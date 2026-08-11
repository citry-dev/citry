"""Compile and link authored Fluent catalogs into three runtime candidates."""

# This is an executable design probe, not production code.
# ruff: noqa: ANN001, ANN201, ANN202, ANN204, S607

from __future__ import annotations

import ast as py_ast
import copy
import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from fluent.runtime import FluentBundle, FluentResource
from fluent.syntax import FluentParser, FluentSerializer
from fluent.syntax import ast as fluent_ast

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
TOPOLOGY = FIXTURES / "topology.json"
REQUIREMENTS = ROOT / "python-requirements.txt"
BROWSER_RUNNER = ROOT / "browser" / "runner.mjs"
BROWSER_PACKAGE = ROOT.parent / "runtime_backend" / "browser" / "package.json"
BROWSER_LOCK = ROOT.parent / "runtime_backend" / "browser" / "pnpm-lock.yaml"
RUST_MANIFEST = ROOT / "rust" / "Cargo.toml"
FSI = "\u2068"
PDI = "\u2069"
SLOT_MARKER = "__CITRY_SLOT_COMPILER_LINKER_TERMS_LINK__"
PARAM_RE = re.compile(
    r"^@param\s+\{(?P<type>[A-Za-z][A-Za-z0-9_.]*)\}\s+"
    r"\$(?P<name>[A-Za-z][A-Za-z0-9_-]*)"
    r"(?:\s+-\s+(?P<description>.+))?$"
)
ALLOWED_TYPES = {"str", "int", "float", "Decimal", "Slot"}
NUMERIC_TYPES = {"int", "float", "Decimal"}


class CompilerError(RuntimeError):
    def __init__(self, code: str, message: str, positions: list[dict[str, Any]] | None = None):
        super().__init__(message)
        self.code = code
        self.positions = positions or []


class CandidateMissing(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_digest(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:length]


def output_token(key: OutputKey) -> str:
    return key.message_id if key.attribute is None else f"{key.message_id}.{key.attribute}"


@dataclass(frozen=True, order=True)
class OutputKey:
    message_id: str
    attribute: str | None = None


@dataclass(frozen=True)
class Layer:
    name: str
    package: str
    precedence: int


@dataclass
class Definition:
    layer: Layer
    locale: str
    path: Path
    source: str
    entry: Any
    params: dict[str, str] = field(default_factory=dict)

    def pattern(self, key: OutputKey):
        if key.attribute is None:
            return self.entry.value
        for attribute in self.entry.attributes:
            if attribute.id.name == key.attribute:
                return attribute.value
        return None

    def position(self, node=None) -> dict[str, Any]:
        target = node or self.entry
        start = target.span.start
        prefix = self.source[:start]
        return {
            "file": str(self.path.relative_to(ROOT)),
            "line": prefix.count("\n") + 1,
            "column": start - prefix.rfind("\n"),
            "start": start,
            "end": target.span.end,
        }


@dataclass(frozen=True)
class Contract:
    types: tuple[tuple[str, str], ...]

    def as_dict(self) -> dict[str, str]:
        return dict(self.types)

    @property
    def slots(self) -> frozenset[str]:
        return frozenset(name for name, type_name in self.types if type_name == "Slot")


@dataclass
class Graph:
    locale: str
    messages: dict[OutputKey, Definition] = field(default_factory=dict)
    terms: dict[tuple[str, str], Definition] = field(default_factory=dict)


@dataclass(frozen=True)
class Resolution:
    active_locale: str
    key: OutputKey
    selected_locale: str
    graph: Graph


@dataclass
class MapOperation:
    internal_id: str
    kind: str
    authored: dict[str, Any]
    detail: str | None = None


def walk_expression(expression):
    yield expression
    if isinstance(expression, fluent_ast.Placeable):
        yield from walk_expression(expression.expression)
    elif isinstance(expression, fluent_ast.SelectExpression):
        yield from walk_expression(expression.selector)
        for variant in expression.variants:
            yield from walk_pattern(variant.value)
    elif isinstance(expression, fluent_ast.FunctionReference) or (
        isinstance(expression, fluent_ast.TermReference) and expression.arguments is not None
    ):
        for positional in expression.arguments.positional:
            yield from walk_expression(positional)


def walk_pattern(pattern):
    if pattern is None:
        return
    for element in pattern.elements:
        if isinstance(element, fluent_ast.Placeable):
            yield from walk_expression(element.expression)


def direct_variables(pattern) -> set[str]:
    return {node.id.name for node in walk_pattern(pattern) if isinstance(node, fluent_ast.VariableReference)}


def message_references(pattern) -> list[tuple[OutputKey, Any]]:
    return [
        (
            OutputKey(
                node.id.name,
                node.attribute.name if node.attribute is not None else None,
            ),
            node,
        )
        for node in walk_pattern(pattern)
        if isinstance(node, fluent_ast.MessageReference)
    ]


def term_references(pattern) -> list[tuple[str, Any]]:
    return [(node.id.name, node) for node in walk_pattern(pattern) if isinstance(node, fluent_ast.TermReference)]


def parse_params(entry) -> dict[str, str]:
    if entry.comment is None:
        return {}
    params = {}
    for raw_line in entry.comment.content.splitlines():
        line = raw_line.strip()
        if not line.startswith("@param"):
            continue
        match = PARAM_RE.fullmatch(line)
        if match is None:
            raise CompilerError("malformed-param", f"malformed @param: {line}")
        name = match.group("name")
        type_name = match.group("type")
        if type_name not in ALLOWED_TYPES:
            raise CompilerError("unsupported-param-type", f"unsupported type {type_name}")
        if name in params:
            raise CompilerError("duplicate-param", f"duplicate @param ${name}")
        params[name] = type_name
    return params


def merge_types(
    target: dict[str, str],
    incoming: dict[str, str],
    *,
    positions: list[dict[str, Any]] | None = None,
) -> None:
    for name, type_name in incoming.items():
        previous = target.get(name)
        if previous is not None and previous != type_name:
            raise CompilerError(
                "transitive-type-conflict",
                f"${name} is both {previous} and {type_name}",
                positions,
            )
        target[name] = type_name


def validate_declared_variables(
    allowed: dict[str, str],
    actual: set[str],
    *,
    positions: list[dict[str, Any]] | None = None,
) -> dict[str, str]:
    introduced = actual - set(allowed)
    if introduced:
        name = sorted(introduced)[0]
        raise CompilerError(
            "translation-added-variable",
            f"translation introduces undeclared ${name}",
            positions,
        )
    return {name: allowed[name] for name in sorted(actual)}


def validate_required_slot_paths(
    required_slots: frozenset[str],
    paths: list[Counter[str]],
    *,
    output: str,
    positions: list[dict[str, Any]] | None = None,
) -> None:
    for slot in sorted(required_slots):
        if any(path[slot] == 0 for path in paths):
            raise CompilerError(
                "required-slot-omitted",
                f"{output} omits required Slot ${slot} on a reachable path",
                positions,
            )


class Linker:
    def __init__(self, topology_path: Path, *, reverse_catalog_order: bool = False):
        self.topology_path = topology_path
        self.topology = json.loads(topology_path.read_text())
        self.packages = self.topology["packages"]
        self.layers = {
            item["name"]: Layer(item["name"], item["package"], item["precedence"]) for item in self.topology["layers"]
        }
        self.owner_by_id: dict[str, str] = {}
        for package, config in self.packages.items():
            for message_id in config["exports"]:
                if message_id in self.owner_by_id:
                    raise CompilerError("duplicate-owner", f"duplicate owner for {message_id}")
                self.owner_by_id[message_id] = package
        self.message_definitions: dict[tuple[str, str], list[Definition]] = defaultdict(list)
        self.term_definitions: dict[tuple[str, str, str], Definition] = {}
        self.catalog_paths: list[Path] = []
        catalog_specs = [
            (self.layers[item["name"]], locale, FIXTURES / relative)
            for item in self.topology["layers"]
            for locale, relative in item["catalogs"].items()
        ]
        if reverse_catalog_order:
            catalog_specs.reverse()
        for layer, locale, path in catalog_specs:
            self._load_catalog(layer, locale, path)
        for definitions in self.message_definitions.values():
            definitions.sort(key=lambda definition: definition.layer.precedence, reverse=True)
        self._contract_cache: dict[OutputKey, Contract] = {}
        self._validate_owner_sources()

    def _load_catalog(self, layer: Layer, locale: str, path: Path) -> None:
        source = path.read_text()
        resource = FluentParser(with_spans=True).parse(source)
        junk = [entry for entry in resource.body if isinstance(entry, fluent_ast.Junk)]
        if junk:
            raise CompilerError("catalog-junk", f"{path} contains Fluent Junk")
        seen_messages = set()
        seen_terms = set()
        self.catalog_paths.append(path)
        for entry in resource.body:
            if isinstance(entry, fluent_ast.Message):
                message_id = entry.id.name
                if message_id in seen_messages:
                    raise CompilerError("duplicate-message", f"duplicate {message_id} in {path}")
                seen_messages.add(message_id)
                definition = Definition(layer, locale, path, source, entry, parse_params(entry))
                self.message_definitions[(locale, message_id)].append(definition)
            elif isinstance(entry, fluent_ast.Term):
                term_id = entry.id.name
                if term_id in seen_terms:
                    raise CompilerError("duplicate-term", f"duplicate -{term_id} in {path}")
                seen_terms.add(term_id)
                key = (locale, layer.name, term_id)
                if key in self.term_definitions:
                    raise CompilerError("duplicate-term", f"duplicate -{term_id} in layer")
                self.term_definitions[key] = Definition(layer, locale, path, source, entry)

    def _owner_definition(self, key: OutputKey) -> Definition:
        owner = self.owner_by_id.get(key.message_id)
        if owner is None:
            raise CompilerError("unknown-owner", f"no owner for {key.message_id}")
        source_locale = self.packages[owner]["source_locale"]
        candidates = [
            definition
            for definition in self.message_definitions.get((source_locale, key.message_id), [])
            if definition.layer.package == owner and definition.pattern(key) is not None
        ]
        if len(candidates) != 1:
            raise CompilerError(
                "owner-source-definition",
                f"expected one {owner}/{source_locale} definition for {output_token(key)}",
            )
        return candidates[0]

    def _validate_owner_sources(self) -> None:
        for message_id, owner in sorted(self.owner_by_id.items()):
            definition = self._owner_definition(OutputKey(message_id))
            all_variables = set()
            if definition.entry.value is not None:
                all_variables.update(direct_variables(definition.entry.value))
            for attribute in definition.entry.attributes:
                all_variables.update(direct_variables(attribute.value))
            if all_variables != set(definition.params):
                raise CompilerError(
                    "source-param-mismatch",
                    f"{message_id} params differ: variables={sorted(all_variables)}, "
                    f"params={sorted(definition.params)}",
                    [definition.position()],
                )
            source_locale = self.packages[owner]["source_locale"]
            for candidate in self.message_definitions.get((source_locale, message_id), []):
                if candidate is definition:
                    continue
                if candidate.params:
                    raise CompilerError(
                        "override-param",
                        f"override {message_id} must not redeclare @param",
                        [candidate.position()],
                    )
        for definitions in self.message_definitions.values():
            for definition in definitions:
                owner = self.owner_by_id.get(definition.entry.id.name)
                if owner is None and definition.params:
                    raise CompilerError("unknown-owner", "@param message has no declared owner")
                if owner is None:
                    continue
                source_locale = self.packages[owner]["source_locale"]
                is_owner_source = definition.layer.package == owner and definition.locale == source_locale
                if not is_owner_source and definition.params:
                    raise CompilerError(
                        "translation-param",
                        f"translation/override {definition.entry.id.name} redeclares @param",
                        [definition.position()],
                    )

    def public_outputs(self) -> list[OutputKey]:
        outputs = []
        for message_id in sorted(self.owner_by_id):
            definition = self._owner_definition(OutputKey(message_id))
            if definition.entry.value is not None:
                outputs.append(OutputKey(message_id))
            outputs.extend(OutputKey(message_id, attribute.id.name) for attribute in definition.entry.attributes)
        return outputs

    def source_contract(self, key: OutputKey, stack: tuple[OutputKey, ...] = ()) -> Contract:
        if key in self._contract_cache:
            return self._contract_cache[key]
        if key in stack:
            positions = [self._owner_definition(item).position() for item in (*stack, key)]
            raise CompilerError("source-reference-cycle", "source message reference cycle", positions)
        definition = self._owner_definition(key)
        pattern = definition.pattern(key)
        types = {}
        for name in direct_variables(pattern):
            type_name = definition.params.get(name)
            if type_name is None:
                raise CompilerError("missing-param", f"missing source @param ${name}")
            types[name] = type_name
        for reference, _node in message_references(pattern):
            referenced = self.source_contract(reference, (*stack, key))
            positions = [definition.position(), self._owner_definition(reference).position()]
            merge_types(types, referenced.as_dict(), positions=positions)
        contract = Contract(tuple(sorted(types.items())))
        self._contract_cache[key] = contract
        return contract

    def _select_definition(self, locale: str, key: OutputKey) -> Definition:
        for definition in self.message_definitions.get((locale, key.message_id), []):
            if definition.pattern(key) is not None:
                return definition
        raise CandidateMissing(f"missing {output_token(key)} at {locale}")

    def _add_term(
        self,
        graph: Graph,
        definition: Definition,
        term_id: str,
        stack: tuple[tuple[str, str], ...],
    ) -> None:
        term_key = (definition.layer.name, term_id)
        if term_key in graph.terms:
            return
        if term_key in stack:
            raise CompilerError("term-cycle", f"private term cycle at -{term_id}")
        term_definition = self.term_definitions.get((graph.locale, definition.layer.name, term_id))
        if term_definition is None:
            raise CandidateMissing(f"missing private -{term_id} in {definition.layer.name}/{graph.locale}")
        graph.terms[term_key] = term_definition
        for nested_term, _node in term_references(term_definition.entry.value):
            self._add_term(graph, term_definition, nested_term, (*stack, term_key))

    def _add_message(
        self,
        graph: Graph,
        key: OutputKey,
        stack: tuple[OutputKey, ...],
    ) -> None:
        if key in graph.messages:
            return
        if key in stack:
            positions = [graph.messages[item].position() for item in stack if item in graph.messages]
            raise CompilerError("selected-reference-cycle", "selected message reference cycle", positions)
        definition = self._select_definition(graph.locale, key)
        graph.messages[key] = definition
        pattern = definition.pattern(key)
        for reference, _node in message_references(pattern):
            self._add_message(graph, reference, (*stack, key))
        for term_id, _node in term_references(pattern):
            self._add_term(graph, definition, term_id, ())

    def _selected_interface(
        self,
        key: OutputKey,
        graph: Graph,
        stack: tuple[OutputKey, ...] = (),
    ) -> dict[str, str]:
        if key in stack:
            raise CompilerError("selected-reference-cycle", "selected message reference cycle")
        definition = graph.messages[key]
        pattern = definition.pattern(key)
        allowed = self.source_contract(key).as_dict()
        types = validate_declared_variables(
            allowed,
            direct_variables(pattern),
            positions=[definition.position()],
        )
        for reference, _node in message_references(pattern):
            incoming = self._selected_interface(reference, graph, (*stack, key))
            merge_types(
                types,
                incoming,
                positions=[definition.position(), graph.messages[reference].position()],
            )
        for name, type_name in types.items():
            if allowed.get(name) != type_name:
                raise CompilerError(
                    "translation-interface-mismatch",
                    f"{output_token(key)} receives incompatible ${name}: {type_name}",
                    [definition.position()],
                )
        return types

    def _slot_paths(
        self,
        key: OutputKey,
        graph: Graph,
        stack: tuple[OutputKey, ...] = (),
    ) -> list[Counter[str]]:
        if key in stack:
            raise CompilerError("selected-reference-cycle", "selected message reference cycle")
        definition = graph.messages[key]
        pattern = definition.pattern(key)
        types = self.source_contract(key).as_dict()
        return self._pattern_slot_paths(pattern, types, graph, (*stack, key), definition)

    def _pattern_slot_paths(self, pattern, types, graph, stack, definition):
        paths = [Counter()]
        for element in pattern.elements:
            if not isinstance(element, fluent_ast.Placeable):
                continue
            expression_paths = self._expression_slot_paths(element.expression, types, graph, stack, definition)
            paths = [left + right for left in paths for right in expression_paths]
        return paths

    def _expression_slot_paths(self, expression, types, graph, stack, definition):
        if isinstance(expression, fluent_ast.VariableReference):
            if types.get(expression.id.name) == "Slot":
                return [Counter({expression.id.name: 1})]
            return [Counter()]
        if isinstance(expression, fluent_ast.MessageReference):
            key = OutputKey(
                expression.id.name,
                expression.attribute.name if expression.attribute is not None else None,
            )
            return self._slot_paths(key, graph, stack)
        if isinstance(expression, fluent_ast.SelectExpression):
            selector_slots = [
                node
                for node in walk_expression(expression.selector)
                if isinstance(node, fluent_ast.VariableReference) and types.get(node.id.name) == "Slot"
            ]
            if selector_slots:
                raise CompilerError(
                    "slot-selector",
                    "Slot cannot be used as a selector",
                    [definition.position(selector_slots[0])],
                )
            return [
                path
                for variant in expression.variants
                for path in self._pattern_slot_paths(variant.value, types, graph, stack, definition)
            ]
        if isinstance(expression, fluent_ast.FunctionReference):
            for node in expression.arguments.positional:
                if isinstance(node, fluent_ast.VariableReference) and types.get(node.id.name) == "Slot":
                    raise CompilerError(
                        "slot-function",
                        "Slot cannot be passed to an authored function",
                        [definition.position(node)],
                    )
            return [Counter()]
        return [Counter()]

    def resolve(self, active_locale: str, key: OutputKey) -> Resolution:
        owner = self.owner_by_id[key.message_id]
        source_locale = self.packages[owner]["source_locale"]
        attempts = []
        for locale in dict.fromkeys((active_locale, source_locale)):
            graph = Graph(locale)
            try:
                self._add_message(graph, key, ())
            except CandidateMissing as error:
                attempts.append(str(error))
                continue
            selected = self._selected_interface(key, graph)
            allowed = self.source_contract(key).as_dict()
            for name, type_name in selected.items():
                if allowed.get(name) != type_name:
                    raise CompilerError(
                        "translation-interface-mismatch",
                        f"{output_token(key)} has incompatible ${name}",
                    )
            required_slots = self.source_contract(key).slots
            slot_paths = self._slot_paths(key, graph)
            validate_required_slot_paths(
                required_slots,
                slot_paths,
                output=output_token(key),
                positions=[graph.messages[key].position()],
            )
            return Resolution(active_locale, key, locale, graph)
        raise CompilerError(
            "unresolved-output",
            f"could not resolve {output_token(key)}: {'; '.join(attempts)}",
        )

    def compile(self) -> dict[str, Any]:
        resolutions = [
            self.resolve(locale, output)
            for locale in self.topology["active_locales"]
            for output in self.public_outputs()
        ]
        bundle_messages: dict[str, dict[OutputKey, Definition]] = defaultdict(dict)
        bundle_terms: dict[str, dict[tuple[str, str], Definition]] = defaultdict(dict)
        for resolution in resolutions:
            for key, definition in resolution.graph.messages.items():
                previous = bundle_messages[resolution.selected_locale].get(key)
                if previous is not None and previous is not definition:
                    raise CompilerError("nondeterministic-selection", output_token(key))
                bundle_messages[resolution.selected_locale][key] = definition
            bundle_terms[resolution.selected_locale].update(resolution.graph.terms)

        artifacts = {}
        source_maps = []
        internal_by_locale: dict[str, dict[OutputKey, str]] = {}
        for locale in sorted(bundle_messages):
            artifact, maps, internal = self._compile_bundle(
                locale,
                bundle_messages[locale],
                bundle_terms[locale],
            )
            artifacts[locale] = artifact
            source_maps.extend(maps)
            internal_by_locale[locale] = internal

        manifest: dict[str, dict[str, Any]] = defaultdict(dict)
        for resolution in resolutions:
            definition = resolution.graph.messages[resolution.key]
            owner = self.owner_by_id[resolution.key.message_id]
            manifest[resolution.active_locale][output_token(resolution.key)] = {
                "owner": owner,
                "bundle_locale": resolution.selected_locale,
                "selected_layer": definition.layer.name,
                "internal_id": internal_by_locale[resolution.selected_locale][resolution.key],
                "contract": self.source_contract(resolution.key).as_dict(),
                "selected_source": definition.position(),
            }
        return {
            "artifacts": artifacts,
            "manifest": {locale: dict(sorted(items.items())) for locale, items in manifest.items()},
            "source_maps": source_maps,
        }

    def _message_internal(self, locale: str, key: OutputKey, definition: Definition) -> str:
        identity = f"message\0{locale}\0{definition.layer.name}\0{key.message_id}\0{key.attribute or 'value'}"
        return f"cmsg-{stable_digest(identity)}"

    def _term_internal(self, locale: str, term_key, definition: Definition) -> str:
        layer_name, term_id = term_key
        identity = f"term\0{locale}\0{layer_name}\0{term_id}\0{definition.path}"
        return f"cterm-{stable_digest(identity)}"

    def _compile_bundle(self, locale, messages, terms):
        internal = {key: self._message_internal(locale, key, definition) for key, definition in messages.items()}
        term_internal = {key: self._term_internal(locale, key, definition) for key, definition in terms.items()}
        identifiers = [*internal.values(), *term_internal.values()]
        if len(set(identifiers)) != len(identifiers):
            raise CompilerError("internal-id-collision", f"internal ID collision in {locale}")
        body = []
        operations: list[MapOperation] = []
        for term_key, definition in sorted(terms.items()):
            entry = copy.deepcopy(definition.entry)
            entry.id.name = term_internal[term_key]
            entry.comment = None
            self._transform_pattern(
                entry.value,
                None,
                definition,
                internal,
                term_internal,
                operations,
                term_internal[term_key],
            )
            body.append(entry)
        for key, definition in sorted(messages.items(), key=lambda item: internal[item[0]]):
            pattern = copy.deepcopy(definition.pattern(key))
            internal_id = internal[key]
            self._transform_pattern(
                pattern,
                key,
                definition,
                internal,
                term_internal,
                operations,
                internal_id,
            )
            body.append(
                fluent_ast.Message(
                    fluent_ast.Identifier(internal_id),
                    pattern,
                    attributes=[],
                    comment=None,
                )
            )
        artifact = FluentSerializer().serialize(fluent_ast.Resource(body))
        maps = self._attach_generated_positions(locale, artifact, operations)
        return artifact, maps, internal

    def _transform_pattern(
        self,
        pattern,
        key,
        definition,
        internal,
        term_internal,
        operations,
        internal_id,
    ) -> None:
        if pattern is None:
            return
        types = self.source_contract(key).as_dict() if key is not None else {}
        for element in pattern.elements:
            if isinstance(element, fluent_ast.Placeable):
                element.expression = self._transform_expression(
                    element.expression,
                    key,
                    types,
                    definition,
                    internal,
                    term_internal,
                    operations,
                    internal_id,
                    displayed=True,
                )

    def _transform_expression(
        self,
        expression,
        key,
        types,
        definition,
        internal,
        term_internal,
        operations,
        internal_id,
        *,
        displayed,
    ):
        if isinstance(expression, fluent_ast.VariableReference) and displayed:
            type_name = types.get(expression.id.name)
            if type_name is None:
                raise CompilerError("generation-type-missing", f"no type for ${expression.id.name}")
            function = "SLOT" if type_name == "Slot" else "CITRY_TEXT"
            kind = "slot" if type_name == "Slot" else "scalar"
            operations.append(MapOperation(internal_id, kind, definition.position(expression), expression.id.name))
            return fluent_ast.FunctionReference(
                fluent_ast.Identifier(function),
                fluent_ast.CallArguments(positional=[expression], named=[]),
            )
        if isinstance(expression, fluent_ast.MessageReference):
            reference = OutputKey(
                expression.id.name,
                expression.attribute.name if expression.attribute is not None else None,
            )
            operations.append(
                MapOperation(
                    internal_id,
                    "public-reference",
                    definition.position(expression),
                    output_token(reference),
                )
            )
            expression.id.name = internal[reference]
            expression.attribute = None
            return expression
        if isinstance(expression, fluent_ast.TermReference):
            term_key = (definition.layer.name, expression.id.name)
            operations.append(
                MapOperation(
                    internal_id,
                    "private-term",
                    definition.position(expression),
                    f"-{expression.id.name}",
                )
            )
            expression.id.name = term_internal[term_key]
            return expression
        if isinstance(expression, fluent_ast.SelectExpression):
            selector = expression.selector
            mode = "cardinal"
            variable = None
            authored_selector = selector
            if isinstance(selector, fluent_ast.VariableReference):
                variable = selector
                if types.get(variable.id.name) not in NUMERIC_TYPES:
                    raise CompilerError(
                        "unsupported-selector",
                        f"selector ${variable.id.name} is not numeric",
                        [definition.position(variable)],
                    )
            elif isinstance(selector, fluent_ast.FunctionReference) and selector.id.name == "NUMBER":
                if len(selector.arguments.positional) != 1 or not isinstance(
                    selector.arguments.positional[0], fluent_ast.VariableReference
                ):
                    raise CompilerError("unsupported-ordinal", "ordinal selector must use one variable")
                type_option = next(
                    (
                        item
                        for item in selector.arguments.named
                        if item.name.name == "type" and isinstance(item.value, fluent_ast.StringLiteral)
                    ),
                    None,
                )
                if type_option is None or type_option.value.value != "ordinal":
                    raise CompilerError("unsupported-selector", "NUMBER selector must be ordinal")
                variable = selector.arguments.positional[0]
                mode = "ordinal"
            else:
                raise CompilerError("unsupported-selector", "selector shape is not lowerable")
            exact_values = [
                variant.key.value
                for variant in expression.variants
                if isinstance(variant.key, fluent_ast.NumberLiteral)
            ]
            named = []
            if exact_values:
                named.append(
                    fluent_ast.NamedArgument(
                        fluent_ast.Identifier("exact"),
                        fluent_ast.StringLiteral(",".join(exact_values)),
                    )
                )
            if mode == "ordinal":
                named.append(
                    fluent_ast.NamedArgument(
                        fluent_ast.Identifier("mode"),
                        fluent_ast.StringLiteral("ordinal"),
                    )
                )
            expression.selector = fluent_ast.FunctionReference(
                fluent_ast.Identifier("CITRY_PLURAL"),
                fluent_ast.CallArguments(positional=[variable], named=named),
            )
            operations.append(
                MapOperation(
                    internal_id,
                    "ordinal-selector" if mode == "ordinal" else "plural-selector",
                    definition.position(authored_selector),
                    ",".join(exact_values) or None,
                )
            )
            for variant in expression.variants:
                if isinstance(variant.key, fluent_ast.NumberLiteral):
                    variant.key = fluent_ast.Identifier(f"exact-{variant.key.value}")
                self._transform_pattern(
                    variant.value,
                    key,
                    definition,
                    internal,
                    term_internal,
                    operations,
                    internal_id,
                )
            return expression
        if isinstance(expression, fluent_ast.FunctionReference):
            if expression.id.name not in {"NUMBER", "DATETIME"}:
                raise CompilerError(
                    "unsupported-function",
                    f"unsupported authored function {expression.id.name}",
                    [definition.position(expression)],
                )
            profile = next(
                (
                    item
                    for item in expression.arguments.named
                    if item.name.name == "profile" and isinstance(item.value, fluent_ast.StringLiteral)
                ),
                None,
            )
            if profile is None:
                raise CompilerError(
                    "missing-format-profile",
                    f"{expression.id.name} requires a literal profile",
                    [definition.position(expression)],
                )
            operations.append(
                MapOperation(
                    internal_id,
                    "number" if expression.id.name == "NUMBER" else "datetime",
                    definition.position(expression),
                    profile.value.value,
                )
            )
            return expression
        return expression

    def _attach_generated_positions(self, locale, artifact, operations):
        resource = FluentParser(with_spans=True).parse(artifact)
        generated_by_id = {}
        for entry in resource.body:
            if not isinstance(entry, fluent_ast.Message):
                continue
            generated = []
            for node in walk_pattern(entry.value):
                kind = None
                if isinstance(node, fluent_ast.FunctionReference):
                    if node.id.name == "CITRY_TEXT":
                        kind = "scalar"
                    elif node.id.name == "SLOT":
                        kind = "slot"
                    elif node.id.name == "NUMBER":
                        kind = "number"
                    elif node.id.name == "DATETIME":
                        kind = "datetime"
                    elif node.id.name == "CITRY_PLURAL":
                        ordinal = any(
                            item.name.name == "mode"
                            and isinstance(item.value, fluent_ast.StringLiteral)
                            and item.value.value == "ordinal"
                            for item in node.arguments.named
                        )
                        kind = "ordinal-selector" if ordinal else "plural-selector"
                elif isinstance(node, fluent_ast.MessageReference):
                    kind = "public-reference"
                elif isinstance(node, fluent_ast.TermReference):
                    kind = "private-term"
                if kind is not None:
                    generated.append((kind, node))
            generated_by_id[entry.id.name] = generated
        maps = []
        for internal_id in sorted({operation.internal_id for operation in operations}):
            authored = [operation for operation in operations if operation.internal_id == internal_id]
            generated = generated_by_id.get(internal_id, [])
            if [operation.kind for operation in authored] != [kind for kind, _node in generated]:
                raise CompilerError(
                    "source-map-order",
                    f"source map order mismatch for {internal_id}: "
                    f"{[item.kind for item in authored]} vs {[item[0] for item in generated]}",
                )
            for operation, (_kind, node) in zip(authored, generated, strict=True):
                prefix = artifact[: node.span.start]
                maps.append(
                    {
                        "bundle_locale": locale,
                        "internal_id": internal_id,
                        "kind": operation.kind,
                        "detail": operation.detail,
                        "authored": operation.authored,
                        "generated": {
                            "line": prefix.count("\n") + 1,
                            "column": node.span.start - prefix.rfind("\n"),
                            "start": node.span.start,
                            "end": node.span.end,
                        },
                    }
                )
        return maps


def negative_evidence() -> dict[str, Any]:
    parser = FluentParser(with_spans=True)
    evidence = {}

    conflict_path = FIXTURES / "negative" / "type-conflict.ftl"
    conflict_source = conflict_path.read_text()
    conflict_resource = parser.parse(conflict_source)
    messages = {entry.id.name: entry for entry in conflict_resource.body if isinstance(entry, fluent_ast.Message)}
    params = {name: parse_params(entry) for name, entry in messages.items()}

    def conflict_contract(name, stack=()):
        if name in stack:
            raise CompilerError("source-reference-cycle", "cycle")
        types = {variable: params[name][variable] for variable in direct_variables(messages[name].value)}
        for reference, _node in message_references(messages[name].value):
            merge_types(types, conflict_contract(reference.message_id, (*stack, name)))
        return types

    try:
        conflict_contract("conflict-wrapper")
    except CompilerError as error:
        evidence["transitive_type_conflict"] = error.code
    else:
        raise RuntimeError("type conflict fixture passed")

    missing_path = FIXTURES / "negative" / "missing-slot.ftl"
    missing_source = missing_path.read_text()
    missing_entry = next(entry for entry in parser.parse(missing_source).body if isinstance(entry, fluent_ast.Message))
    missing_params = parse_params(missing_entry)
    variants = missing_entry.value.elements[0].expression.variants
    counts = []
    for variant in variants:
        count = sum(
            1
            for node in walk_pattern(variant.value)
            if isinstance(node, fluent_ast.VariableReference) and missing_params.get(node.id.name) == "Slot"
        )
        counts.append(count)
    require(counts == [1, 0], f"missing-slot fixture shape changed: {counts}")
    try:
        validate_required_slot_paths(
            frozenset({"terms_link"}),
            [Counter({"terms_link": count}) for count in counts],
            output="missing-slot",
        )
    except CompilerError as error:
        evidence["required_slot_omitted"] = error.code
    else:
        raise RuntimeError("missing Slot fixture passed")

    cycle_path = FIXTURES / "negative" / "reference-cycle.ftl"
    cycle_messages = {
        entry.id.name: entry
        for entry in parser.parse(cycle_path.read_text()).body
        if isinstance(entry, fluent_ast.Message)
    }

    def visit_cycle(name, stack=()):
        if name in stack:
            raise CompilerError("source-reference-cycle", "cycle")
        for reference, _node in message_references(cycle_messages[name].value):
            visit_cycle(reference.message_id, (*stack, name))

    try:
        visit_cycle("cycle-a")
    except CompilerError as error:
        evidence["reference_cycle"] = error.code
    else:
        raise RuntimeError("cycle fixture passed")

    unknown_path = FIXTURES / "negative" / "unknown-variable.ftl"
    unknown_messages = [
        entry for entry in parser.parse(unknown_path.read_text()).body if isinstance(entry, fluent_ast.Message)
    ]
    allowed = parse_params(unknown_messages[0])
    try:
        validate_declared_variables(allowed, direct_variables(unknown_messages[1].value))
    except CompilerError as error:
        evidence["translation_added_variable"] = error.code
    else:
        raise RuntimeError("unknown-variable fixture passed")
    return evidence


def scalar_text(value) -> str:
    value = getattr(value, "value", value)
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    return str(value)


def keep_slot(value) -> str:
    marker = scalar_text(value)
    if not marker.startswith("__CITRY_SLOT_"):
        raise TypeError("SLOT accepts only an opaque Citry Slot marker")
    return marker


def plural_category(locale, value, *, exact=None, mode="cardinal"):
    value = Decimal(str(getattr(value, "value", value)))
    mode = scalar_text(mode)
    if mode == "ordinal":
        if locale != "en-US" or value != value.to_integral_value():
            return "other"
        integer = int(value)
        if integer % 100 in {11, 12, 13}:
            return "other"
        return {1: "one", 2: "two", 3: "few"}.get(integer % 10, "other")
    if mode != "cardinal":
        raise ValueError(f"unknown plural mode: {mode}")
    if exact is not None:
        for item in scalar_text(exact).split(","):
            if value == Decimal(item):
                return f"exact-{item}"
    if locale == "cs-CZ":
        if value != value.to_integral_value():
            return "many"
        return "one" if value == 1 else "few" if 2 <= value <= 4 else "other"
    return "one" if value == 1 else "other"


def python_candidate(payload):
    bundles = {}
    for locale, source in payload["artifacts"].items():
        bundle = FluentBundle(
            [locale],
            functions={
                "CITRY_TEXT": lambda value: f"{FSI}{scalar_text(value)}{PDI}",
                "SLOT": keep_slot,
                "CITRY_PLURAL": lambda value, _locale=locale, **named: plural_category(_locale, value, **named),
                "NUMBER": lambda value, *, profile: (
                    f"{FSI}NUM[value={scalar_text(value)},profile={scalar_text(profile)}]{PDI}"
                ),
            },
            use_isolating=False,
        )
        bundle.add_resource(FluentResource(source))
        bundles[locale] = bundle
    results = {}
    for case in payload["cases"]:
        bundle = bundles[case["bundle_locale"]]
        message = bundle.get_message(case["internal_id"])
        require(message is not None and message.value is not None, "Python message missing")
        value, errors = bundle.format_pattern(message.value, case["args"])
        require(not errors, f"Python format errors: {errors}")
        results[case["name"]] = {
            "bundle_locale": case["bundle_locale"],
            "value": value,
        }
    return {"candidate": "python", "results": results}


def json_command(command: list[str]) -> dict[str, Any]:
    process = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(process.stdout)


def build_cases(compiled) -> list[dict[str, Any]]:
    manifest = compiled["manifest"]
    cases = []

    def add(name, active, output, args):
        resolution = manifest[active][output]
        cases.append(
            {
                "name": name,
                "active_locale": active,
                "output": output,
                "bundle_locale": resolution["bundle_locale"],
                "internal_id": resolution["internal_id"],
                "args": args,
            }
        )

    rich_args = {"name": "Ada", "terms_link": SLOT_MARKER}
    add("account_cs", "cs-CZ", "citry-ui-account", rich_args)
    add("account_en", "en-US", "citry-ui-account", rich_args)
    add("account_aria_cs", "cs-CZ", "citry-ui-account.aria-label", {"name": "Ada"})
    add("wrapper_cs", "cs-CZ", "my-app-wrapper", rich_args)
    add("wrapper_en", "en-US", "my-app-wrapper", rich_args)
    add("reference_candidate_fallback", "cs-CZ", "citry-ui-ref-wrapper", {})
    add("library_source_fallback", "cs-CZ", "citry-ui-fallback-only", {})
    add("application_source_fallback", "en-US", "my-app-fallback-only", {})
    for value in (0, 1, 2, 2.5, 5):
        add(f"count_cs_{str(value).replace('.', '_')}", "cs-CZ", "citry-ui-count", {"count": value})
    for value in (1, 2, 3, 4, 11, 21):
        add(f"ordinal_en_{value}", "en-US", "my-app-ordinal", {"position": value})
    return cases


def main() -> None:
    parsed_source = py_ast.parse(Path(__file__).read_text())
    assertion_count = sum(isinstance(node, py_ast.Assert) for node in py_ast.walk(parsed_source))
    require(assertion_count == 0, "compiler/linker harness contains load-bearing Python assert statements")

    expected_packages = {
        line.split("==", 1)[0]: line.split("==", 1)[1]
        for line in REQUIREMENTS.read_text().splitlines()
        if line.strip()
    }
    for package, version in expected_packages.items():
        require(importlib.metadata.version(package) == version, f"unexpected {package}")
    normalized_expected = {name.lower().replace("_", "-"): version for name, version in expected_packages.items()}
    installed_packages = {
        distribution.metadata["Name"].lower().replace("_", "-"): distribution.version
        for distribution in importlib.metadata.distributions()
    }
    require(installed_packages == normalized_expected, f"unexpected Python environment: {installed_packages}")

    linker = Linker(TOPOLOGY)
    compiled = linker.compile()
    reversed_compiled = Linker(TOPOLOGY, reverse_catalog_order=True).compile()
    require(compiled == reversed_compiled, "catalog discovery order changed compiler output")
    require(
        all("CITRY_" not in path.read_text() and "SLOT" not in path.read_text() for path in linker.catalog_paths),
        "authored fixtures contain internal functions",
    )
    require(
        all("CITRY_PLURAL" in source for source in compiled["artifacts"].values()),
        "compiled artifact omitted generated plural handling",
    )
    require(
        all("CITRY_TEXT" in source and "SLOT" in source for source in compiled["artifacts"].values()),
        "compiled artifact omitted generated scalar/Slot handling",
    )

    cases = build_cases(compiled)
    payload = {"artifacts": compiled["artifacts"], "cases": cases}
    python = python_candidate(payload)
    with tempfile.TemporaryDirectory(prefix="citry-i18n-linker-") as temporary:
        payload_path = Path(temporary) / "payload.json"
        payload_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        browser = json_command(["node", str(BROWSER_RUNNER), str(payload_path)])
        rust = json_command(
            [
                "cargo",
                "run",
                "--quiet",
                "--manifest-path",
                str(RUST_MANIFEST),
                "--locked",
                "--",
                str(payload_path),
            ]
        )
    require(
        python["results"] == browser["results"] == rust["results"],
        "compiled artifacts differ across runtimes",
    )
    require(browser["runtime_versions"] == {"@fluent/bundle": "0.19.1"}, "browser runtime version changed")
    results = python["results"]
    require(
        "APPLICATION-CS" in results["account_cs"]["value"],
        "application private term did not remain layer-local",
    )
    require(
        results["account_cs"]["value"].count(SLOT_MARKER) == 2
        and results["account_en"]["value"].count(SLOT_MARKER) == 2,
        "repeated Slot markers were not preserved",
    )
    require(
        results["reference_candidate_fallback"]["bundle_locale"] == "en-US"
        and "English wrapper" in results["reference_candidate_fallback"]["value"],
        "same-locale reference failure did not continue owner fallback",
    )
    require(
        results["library_source_fallback"]["bundle_locale"] == "en-US"
        and results["application_source_fallback"]["bundle_locale"] == "cs-CZ",
        "per-owner source fallback failed",
    )
    require(
        compiled["manifest"]["cs-CZ"]["citry-ui-account"]["owner"] == "citry_ui"
        and compiled["manifest"]["cs-CZ"]["citry-ui-account"]["selected_layer"] == "application",
        "override changed ownership or failed precedence",
    )
    require(
        compiled["manifest"]["cs-CZ"]["citry-ui-account.aria-label"]["selected_layer"] == "citry_ui",
        "partial attribute fallback did not select the lower layer",
    )

    negative = negative_evidence()
    require(
        negative
        == {
            "transitive_type_conflict": "transitive-type-conflict",
            "required_slot_omitted": "required-slot-omitted",
            "reference_cycle": "source-reference-cycle",
            "translation_added_variable": "translation-added-variable",
        },
        "negative compiler evidence changed",
    )
    source_map_kinds = {item["kind"] for item in compiled["source_maps"]}
    require(
        {
            "scalar",
            "slot",
            "plural-selector",
            "ordinal-selector",
            "number",
            "public-reference",
            "private-term",
        }
        <= source_map_kinds,
        f"source maps are incomplete: {source_map_kinds}",
    )

    input_paths = sorted(
        {
            Path(__file__).resolve(),
            REQUIREMENTS,
            TOPOLOGY,
            BROWSER_RUNNER,
            BROWSER_PACKAGE,
            BROWSER_LOCK,
            RUST_MANIFEST,
            ROOT / "rust" / "Cargo.lock",
            ROOT / "rust" / "src" / "main.rs",
            *FIXTURES.rglob("*.ftl"),
        }
    )
    output = {
        "result": "PASS_BOUNDED",
        "environment": {
            "python": platform.python_version(),
            "uv": subprocess.run(["uv", "--version"], check=True, capture_output=True, text=True).stdout.strip(),
            "node": subprocess.run(["node", "--version"], check=True, capture_output=True, text=True).stdout.strip(),
            "pnpm": subprocess.run(["pnpm", "--version"], check=True, capture_output=True, text=True).stdout.strip(),
            "rustc": subprocess.run(["rustc", "--version"], check=True, capture_output=True, text=True).stdout.strip(),
            "cargo": subprocess.run(["cargo", "--version"], check=True, capture_output=True, text=True).stdout.strip(),
            "platform": platform.platform(),
            "packages": expected_packages,
        },
        "inputs": {str(path.relative_to(ROOT.parent)): sha256(path) for path in input_paths},
        "compiled": compiled,
        "cases": cases,
        "runtime_results": {
            "python": python["results"],
            "browser": browser["results"],
            "rust": rust["results"],
        },
        "negative": negative,
        "evidence_integrity": {
            "python_assert_statements": assertion_count,
            "browser_runtime_versions": browser["runtime_versions"],
        },
        "gates": {
            "authored_internal_functions_absent": True,
            "catalog_order_deterministic": True,
            "per_owner_source_fallback": True,
            "same_locale_reference_candidate_fallback": True,
            "application_override_preserves_owner": True,
            "private_terms_remain_layer_local": True,
            "partial_attribute_fallback": True,
            "transitive_typed_interface": True,
            "transitive_type_conflict_rejected": True,
            "required_slot_omission_rejected": True,
            "repeated_slot_markers_preserved": True,
            "authored_plural_and_ordinal_lowered": True,
            "displayed_scalars_lowered": True,
            "source_maps_cover_lowered_operations": True,
            "python_browser_rust_outputs_equal": True,
            "real_pyo3_binding_proved": False,
            "production_linker_ratified": False,
        },
        "bounded_conclusion": {
            "fluent_compiler_linker": "viable",
            "backend_ratified": False,
        },
    }
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
