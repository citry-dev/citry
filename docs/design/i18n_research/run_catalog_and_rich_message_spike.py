"""
Executable i18n source-contract and rich-message design probe.

This file intentionally lives outside the production packages. It uses
``fluent.syntax`` only to inspect Fluent source, and it does not select a
production message formatter.
"""

# The executable probe intentionally mirrors Citry's permissive dynamic
# component method signatures. Every proof gate is an always-on runtime check.
# ruff: noqa: ANN001, ANN201, ANN202, ARG002, E402, T201

from __future__ import annotations

import ast as py_ast
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

RESEARCH_DIR = Path(__file__).resolve().parent
REPO_ROOT = RESEARCH_DIR.parents[2]
PY_PACKAGE = REPO_ROOT / "packages" / "py" / "citry"
CORE_PACKAGE = REPO_ROOT / "packages" / "py" / "citry_core"
SOURCE_REQUIREMENTS = RESEARCH_DIR / "source-spike-requirements.txt"
sys.path.insert(0, str(PY_PACKAGE))
sys.path.insert(0, str(CORE_PACKAGE))

from fluent.syntax import FluentParser
from fluent.syntax import ast as fluent_ast

from citry import Citry, Component, Extension, Slot
from citry.assets import _load_pair
from citry_core import _rust as rust_binding
from citry_core.template_parser import parse_template

PARAM_RE = re.compile(
    r"^@param\s+\{(?P<type>[^{}]+)\}\s+\$(?P<name>[A-Za-z][A-Za-z0-9_-]*)"
    r"(?:\s+-\s+(?P<description>.+))?$"
)
ALLOWED_SIMPLE_TYPES = {
    "bool",
    "date",
    "datetime",
    "Decimal",
    "float",
    "int",
    "Slot",
    "str",
    "time",
}
ALLOWED_DOTTED_TYPES = {
    "citry.Slot",
    "datetime.date",
    "datetime.datetime",
    "datetime.time",
    "decimal.Decimal",
}
ALLOWED_CONTAINERS = {"dict", "list", "tuple"}
EXPECTED_DISTRIBUTIONS = {
    "citry": "0.3.2",
    "fluent-syntax": "0.19.0",
    "markupsafe": "3.0.3",
    "typing-extensions": "4.15.0",
    "wrapt": "2.2.2",
}


class ContractError(ValueError):
    """A deliberately pointed source-contract failure."""


def require(condition: bool, message: str) -> None:
    """Enforce a proof gate even when Python optimization is enabled."""
    if not condition:
        raise AssertionError(message)


@dataclass(frozen=True)
class SourceLocation:
    char_start: int
    char_end: int
    byte_start: int
    byte_end: int
    line: int
    column: int


@dataclass(frozen=True)
class ParamSpec:
    name: str
    python_type: str
    description: str | None


@dataclass(frozen=True)
class MessageSpec:
    id: str
    attributes: tuple[str, ...]
    params: tuple[ParamSpec, ...]
    source_slot_occurrences: tuple[tuple[str, int], ...]
    has_selector: bool
    has_term_reference: bool
    location: SourceLocation


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_distribution_name(name: str) -> str:
    """Normalize a distribution name without importing packaging."""
    return re.sub(r"[-_.]+", "-", name).lower()


def distribution_inventory() -> dict[str, str]:
    """Require the complete isolated Python distribution set."""
    inventory: dict[str, str] = {}
    for distribution in importlib.metadata.distributions():
        raw_name = distribution.metadata["Name"]
        name = canonical_distribution_name(raw_name)
        require(name not in inventory, f"duplicate installed distribution {name!r}")
        inventory[name] = distribution.version
    require(
        inventory == EXPECTED_DISTRIBUTIONS,
        f"isolated distribution inventory mismatch: {inventory!r}",
    )
    return dict(sorted(inventory.items()))


def native_repository_state(repository: Path) -> dict[str, Any]:
    git = shutil.which("git")
    require(git is not None, "git executable is required for native repository identity")
    status = subprocess.check_output(
        [git, "-C", str(repository), "status", "--porcelain=v1", "--untracked-files=all"],
        text=True,
    ).strip()
    require(not status, f"native repository must be clean for evidence: {repository}: {status}")
    return {
        "clean": True,
        "head": subprocess.check_output([git, "-C", str(repository), "rev-parse", "HEAD"], text=True).strip(),
        "tree": subprocess.check_output([git, "-C", str(repository), "rev-parse", "HEAD^{tree}"], text=True).strip(),
    }


def native_path_dependency_inputs() -> tuple[list[Path], list[str], dict[str, Any]]:
    """Resolve every local Cargo input reachable from the PyO3 crate."""
    cargo = shutil.which("cargo")
    require(cargo is not None, "cargo executable is required for native dependency metadata")
    metadata = json.loads(
        subprocess.check_output(
            [
                cargo,
                "metadata",
                "--locked",
                "--format-version",
                "1",
                "--manifest-path",
                str(REPO_ROOT / "crates" / "citry_core_py" / "Cargo.toml"),
            ],
            cwd=REPO_ROOT,
            text=True,
        )
    )
    packages = {package["id"]: package for package in metadata["packages"]}
    nodes = {node["id"]: node for node in metadata["resolve"]["nodes"]}
    root_id = metadata["resolve"]["root"]
    require(root_id in nodes, "cargo metadata did not resolve citry_core_py as the root")

    reachable: set[str] = set()
    pending = [root_id]
    while pending:
        package_id = pending.pop()
        if package_id in reachable:
            continue
        reachable.add(package_id)
        pending.extend(nodes[package_id]["dependencies"])

    inputs: list[Path] = []
    package_labels: list[str] = []
    native_repositories: dict[str, Any] = {}
    for package_id in sorted(reachable):
        package = packages[package_id]
        manifest_path = Path(package["manifest_path"]).resolve()
        try:
            manifest_path.relative_to(REPO_ROOT)
        except ValueError:
            continue
        package_dir = manifest_path.parent
        package_labels.append(f"{package['name']}=={package['version']}:{manifest_path.relative_to(REPO_ROOT)}")
        inputs.append(manifest_path)
        source_dir = package_dir / "src"
        if source_dir.is_dir():
            inputs.extend(path.resolve() for path in source_dir.rglob("*") if path.is_file())
        inputs.extend(
            Path(target["src_path"]).resolve()
            for target in package["targets"]
            if "custom-build" in target["kind"] and Path(target["src_path"]).is_file()
        )
        ruff_repository = REPO_ROOT / "third_party" / "rust" / "ruff"
        if manifest_path.is_relative_to(ruff_repository):
            key = ruff_repository.relative_to(REPO_ROOT).as_posix()
            if key not in native_repositories:
                native_repositories[key] = native_repository_state(ruff_repository)
    require(any("third_party/rust/ruff/" in path.as_posix() for path in inputs), "Ruff path inputs missing")
    require(native_repositories, "native submodule identity is missing")
    return sorted(set(inputs)), package_labels, native_repositories


def input_paths(binding_path: Path) -> tuple[list[Path], list[Path], list[str], dict[str, Any]]:
    """Return whitelisted executed inputs and locked native build inputs."""
    native_sources, native_packages, native_repositories = native_path_dependency_inputs()
    binding_sources = [
        REPO_ROOT / "Cargo.lock",
        REPO_ROOT / "Cargo.toml",
        REPO_ROOT / "rust-toolchain.toml",
        *native_sources,
    ]

    python_sources = [
        *(PY_PACKAGE / "citry").rglob("*.py"),
        *(PY_PACKAGE / "citry").rglob("*.pyi"),
        *(CORE_PACKAGE / "citry_core").rglob("*.py"),
        *(CORE_PACKAGE / "citry_core").rglob("*.pyi"),
    ]
    declared_inputs = [
        Path(__file__).resolve(),
        SOURCE_REQUIREMENTS,
        RESEARCH_DIR / "fixtures" / "source.ftl",
        RESEARCH_DIR / "fixtures" / "translation.ftl",
        REPO_ROOT / "pyproject.toml",
        REPO_ROOT / "uv.lock",
        REPO_ROOT / "rust-toolchain.toml",
        PY_PACKAGE / "pyproject.toml",
        CORE_PACKAGE / "pyproject.toml",
        CORE_PACKAGE / "uv.lock",
        binding_path,
        *binding_sources,
        *python_sources,
    ]
    unique_inputs = sorted(set(declared_inputs))
    require(all(path.is_file() for path in unique_inputs), "one or more declared inputs are missing")
    return unique_inputs, sorted(set(binding_sources)), native_packages, native_repositories


def path_digest_manifest(paths: list[Path]) -> dict[str, str]:
    """Record every selected path and digest instead of an opaque tree hash."""
    return {path.relative_to(REPO_ROOT).as_posix(): sha256(path) for path in paths}


def manifest_sha256(manifest: dict[str, str]) -> str:
    payload = json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def command_version(command: list[str]) -> str:
    environment = os.environ.copy()
    environment.pop("VIRTUAL_ENV", None)
    return subprocess.check_output(command, cwd=REPO_ROOT, env=environment, text=True).strip()


def citry_source_evidence() -> dict[str, Any]:
    """Identify the exact Python runtime and rebuilt PyO3 parser under test."""
    binding_path = Path(rust_binding.__file__).resolve()
    declared_inputs, binding_sources, native_packages, native_repositories = input_paths(binding_path)
    newest_binding_source = max(path.stat().st_mtime_ns for path in binding_sources)
    binding_is_fresh = binding_path.stat().st_mtime_ns >= newest_binding_source
    require(
        binding_is_fresh,
        "citry_core._rust is older than its native sources; run the documented frozen maturin develop step",
    )
    manifest = path_digest_manifest(declared_inputs)
    return {
        "input_manifest": manifest,
        "input_manifest_sha256": manifest_sha256(manifest),
        "native_path_packages": native_packages,
        "native_repositories": native_repositories,
        "rust_binding_filename": binding_path.name,
        "rust_binding_sha256": sha256(binding_path),
        "rust_binding_newer_than_sources": binding_is_fresh,
    }


def python_safety_evidence() -> dict[str, Any]:
    source = Path(__file__).read_text(encoding="utf-8")
    assert_count = sum(isinstance(node, py_ast.Assert) for node in py_ast.walk(py_ast.parse(source)))
    require(assert_count == 0, f"the source spike contains {assert_count} removable assert statements")

    environment = os.environ.copy()
    environment["PYTHONOPTIMIZE"] = "1"
    negative = subprocess.run(
        [sys.executable, __file__, "--negative-self-test"],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    require(negative.returncode != 0, "optimized negative self-test unexpectedly succeeded")
    require(
        "intentional always-on failure" in negative.stderr,
        "optimized negative self-test failed for the wrong reason",
    )
    require(
        negative.stdout.strip() == '{"optimization_level": 1}',
        f"optimized negative self-test did not run at level 1: {negative.stdout!r}",
    )
    return {
        "assert_statements": assert_count,
        "negative_self_test_optimization_level": 1,
        "optimized_negative_self_test_rejected": True,
        "run_optimization_level": sys.flags.optimize,
        "source_files_checked": 1,
    }


def source_location(source: str, span: Any) -> SourceLocation:
    """Normalize Fluent character offsets to UTF-8 bytes and line/column."""
    start = int(span.start)
    end = int(span.end)
    prefix = source[:start]
    return SourceLocation(
        char_start=start,
        char_end=end,
        byte_start=len(prefix.encode("utf-8")),
        byte_end=len(source[:end].encode("utf-8")),
        line=prefix.count("\n") + 1,
        column=len(prefix.rsplit("\n", 1)[-1]) + 1,
    )


def walk_fluent(node: Any):
    """Yield a Fluent AST recursively without depending on a visitor helper."""
    if isinstance(node, fluent_ast.BaseNode):
        yield node
        for value in vars(node).values():
            yield from walk_fluent(value)
    elif isinstance(node, (list, tuple)):
        for value in node:
            yield from walk_fluent(value)


def dotted_name(node: py_ast.AST) -> str | None:
    parts: list[str] = []
    current = node
    while isinstance(current, py_ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, py_ast.Name):
        return None
    parts.append(current.id)
    return ".".join(reversed(parts))


def validate_type_node(node: py_ast.AST, *, depth: int = 0) -> None:
    """Validate a closed passive type expression without eval or imports."""
    if depth > 8:
        raise ContractError("@param type nesting exceeds eight levels")

    if isinstance(node, py_ast.Name):
        if node.id not in ALLOWED_SIMPLE_TYPES | ALLOWED_CONTAINERS:
            raise ContractError(f"unsupported @param type name {node.id!r}")
        return

    if isinstance(node, py_ast.Attribute):
        name = dotted_name(node)
        if name not in ALLOWED_DOTTED_TYPES:
            raise ContractError(f"unsupported dotted @param type {name!r}")
        return

    if isinstance(node, py_ast.Subscript):
        if not isinstance(node.value, py_ast.Name) or node.value.id not in ALLOWED_CONTAINERS:
            raise ContractError("only dict, list, and tuple may be parameterized")
        validate_type_node(node.slice, depth=depth + 1)
        return

    if isinstance(node, py_ast.Tuple):
        if not node.elts:
            raise ContractError("an empty type argument tuple is invalid")
        for item in node.elts:
            validate_type_node(item, depth=depth + 1)
        return

    if isinstance(node, py_ast.BinOp) and isinstance(node.op, py_ast.BitOr):
        validate_type_node(node.left, depth=depth + 1)
        validate_type_node(node.right, depth=depth + 1)
        return

    if isinstance(node, py_ast.Constant) and node.value in {None, Ellipsis}:
        return

    raise ContractError(f"unsupported @param type syntax {type(node).__name__}")


def parse_python_type(source: str) -> str:
    if not source or len(source) > 128:
        raise ContractError("@param type must contain 1 to 128 characters")
    try:
        expression = py_ast.parse(source, mode="eval")
    except SyntaxError as error:
        raise ContractError(f"invalid @param Python type syntax: {source!r}") from error
    validate_type_node(expression.body)
    return py_ast.unparse(expression.body)


def parse_param_lines(message: Any) -> tuple[ParamSpec, ...]:
    comment = message.comment
    if comment is None:
        return ()
    result: list[ParamSpec] = []
    seen: set[str] = set()
    for raw_line in comment.content.splitlines():
        line = raw_line.strip()
        if not line.startswith("@param"):
            continue
        match = PARAM_RE.fullmatch(line)
        if match is None:
            raise ContractError(f"malformed @param declaration on {message.id.name!r}: {line!r}")
        name = match.group("name")
        if name in seen:
            raise ContractError(f"duplicate @param declaration for ${name} on {message.id.name!r}")
        seen.add(name)
        result.append(
            ParamSpec(
                name=name,
                python_type=parse_python_type(match.group("type").strip()),
                description=match.group("description"),
            )
        )
    return tuple(result)


def parse_catalog(source: str, *, source_catalog: bool) -> tuple[dict[str, MessageSpec], Any]:
    resource = FluentParser(with_spans=True).parse(source)
    junk = [entry for entry in resource.body if isinstance(entry, fluent_ast.Junk)]
    if junk:
        raise ContractError(f"catalog contains {len(junk)} Fluent Junk entr{'y' if len(junk) == 1 else 'ies'}")

    for entry in resource.body:
        if isinstance(entry, fluent_ast.BaseComment) and "@param" in entry.content:
            raise ContractError("@param must be attached directly to a source message without a blank line")
        if isinstance(entry, fluent_ast.Term) and entry.comment is not None and "@param" in entry.comment.content:
            raise ContractError("@param is allowed only on source messages, not Fluent terms")

    seen_entries: set[tuple[str, str]] = set()
    for entry in resource.body:
        if not isinstance(entry, (fluent_ast.Message, fluent_ast.Term)):
            continue
        kind = "message" if isinstance(entry, fluent_ast.Message) else "term"
        key = (kind, entry.id.name)
        if key in seen_entries:
            raise ContractError(f"duplicate Fluent {kind} ID {entry.id.name!r}")
        seen_entries.add(key)

    specs: dict[str, MessageSpec] = {}
    for entry in resource.body:
        if not isinstance(entry, fluent_ast.Message):
            continue
        params = parse_param_lines(entry)
        if params and not source_catalog:
            raise ContractError(f"translation {entry.id.name!r} must not redeclare @param")

        nodes = tuple(walk_fluent(entry))
        value_nodes = tuple(walk_fluent(entry.value))
        referenced = tuple(
            dict.fromkeys(node.id.name for node in nodes if isinstance(node, fluent_ast.VariableReference))
        )
        declared = tuple(param.name for param in params)
        if source_catalog and set(declared) != set(referenced):
            missing = sorted(set(referenced) - set(declared))
            unused = sorted(set(declared) - set(referenced))
            raise ContractError(f"message {entry.id.name!r} @param mismatch: missing={missing!r}, unused={unused!r}")

        specs[entry.id.name] = MessageSpec(
            id=entry.id.name,
            attributes=tuple(attribute.id.name for attribute in entry.attributes),
            params=params,
            source_slot_occurrences=tuple(
                (
                    param.name,
                    sum(
                        isinstance(node, fluent_ast.VariableReference) and node.id.name == param.name
                        for node in value_nodes
                    ),
                )
                for param in params
                if param.python_type in {"Slot", "citry.Slot"}
            ),
            has_selector=any(isinstance(node, fluent_ast.SelectExpression) for node in nodes),
            has_term_reference=any(isinstance(node, fluent_ast.TermReference) for node in nodes),
            location=source_location(source, entry.span),
        )
    return specs, resource


def message_by_id(resource: Any, message_id: str) -> Any:
    for entry in resource.body:
        if isinstance(entry, fluent_ast.Message) and entry.id.name == message_id:
            return entry
    raise ContractError(f"unknown message {message_id!r}")


def validate_rich_inputs(
    spec: MessageSpec,
    values: dict[str, Any],
    slots: dict[str, Slot],
) -> None:
    slot_names = {param.name for param in spec.params if param.python_type in {"Slot", "citry.Slot"}}
    value_names = {param.name for param in spec.params} - slot_names
    if set(values) & set(slots):
        raise ContractError("a rich-message input cannot be supplied as both a value and a fill")
    if set(values) != value_names:
        raise ContractError(
            f"rich-message values mismatch: expected={sorted(value_names)!r}, actual={sorted(values)!r}"
        )
    if set(slots) != slot_names:
        raise ContractError(f"rich-message fills mismatch: expected={sorted(slot_names)!r}, actual={sorted(slots)!r}")


def render_simple_rich_pattern(
    message: Any,
    spec: MessageSpec,
    values: dict[str, Any],
    slots: dict[str, Slot],
) -> tuple[str | Slot, ...]:
    """Evaluate only direct text and variable placeables for the bounded proof."""
    validate_rich_inputs(spec, values, slots)
    if message.value is None:
        raise ContractError(f"rich message {message.id.name!r} has no value")
    translation_variables = tuple(
        node.id.name for node in walk_fluent(message.value) if isinstance(node, fluent_ast.VariableReference)
    )
    declared_variables = {param.name for param in spec.params}
    undeclared_variables = sorted(set(translation_variables) - declared_variables)
    if undeclared_variables:
        raise ContractError(f"translation introduces undeclared variables {undeclared_variables!r}")
    missing_slots = sorted(name for name in slots if translation_variables.count(name) == 0)
    if missing_slots:
        raise ContractError(f"translation omits required rich placeholders: {missing_slots!r}")
    output: list[str | Slot] = []
    for element in message.value.elements:
        if isinstance(element, fluent_ast.TextElement):
            output.append(element.value)
            continue
        if isinstance(element, fluent_ast.Placeable) and isinstance(element.expression, fluent_ast.VariableReference):
            name = element.expression.id.name
            output.append(slots[name] if name in slots else str(values[name]))
            continue
        raise ContractError(
            f"the spike evaluator supports only direct text and variable placeables; received {type(element).__name__}"
        )
    return tuple(output)


def expect_error(label: str, callback: Any, match: str) -> str:
    try:
        callback()
    except (ContractError, ValueError) as error:
        if match not in str(error):
            raise AssertionError(f"{label}: expected {match!r} in {str(error)!r}") from error
        return str(error)
    raise AssertionError(f"{label}: expected an error")


def validate_declared_message_pair(component: type[Component]) -> None:
    own = vars(component)
    if own.get("messages") is not None and own.get("messages_file") is not None:
        raise ContractError("messages and messages_file are mutually exclusive")


class SpikeI18nExtension(Extension):
    """Small stand-in proving only the nested component config mechanism."""

    name = "i18n"
    render_cache_mode = "stateless"
    render_cache_version = 1

    class Config(Extension.Config):
        client_messages: tuple[str, ...] = ()

    def validate_config_fields(self, fields: dict[str, Any], *, component=None) -> None:
        for field, value in fields.items():
            if field != "client_messages":
                raise ValueError(f"unknown i18n config field {field!r}")
            if component is None:
                raise ValueError("client_messages is component-only")
            if not isinstance(value, tuple) or any(not isinstance(item, str) or not item for item in value):
                raise ValueError("client_messages must be a tuple of non-empty strings")
            if len(value) != len(set(value)):
                raise ValueError("client_messages cannot contain duplicates")


def run() -> dict[str, Any]:
    safety_evidence = python_safety_evidence()
    distributions = distribution_inventory()
    tool_versions = {
        "cargo": command_version(["cargo", "--version"]),
        "maturin": command_version(["uv", "run", "--frozen", "maturin", "--version"]),
        "rustc": command_version(["rustc", "--version"]),
        "uv": command_version(["uv", "--version"]),
    }
    fixture_dir = RESEARCH_DIR / "fixtures"
    source_path = fixture_dir / "source.ftl"
    translation_path = fixture_dir / "translation.ftl"
    source = source_path.read_text(encoding="utf-8")
    translation = translation_path.read_text(encoding="utf-8")
    specs, source_resource = parse_catalog(source, source_catalog=True)
    translation_specs, translation_resource = parse_catalog(translation, source_catalog=False)
    catalog_gates = {
        "source_translation_ids_match": set(specs) == set(translation_specs),
        "attributes_extracted": specs["my-app-account-card-actions"].attributes == ("aria-label",),
        "term_reference_extracted": specs["my-app-account-card-greeting"].has_term_reference,
        "selector_extracted": specs["my-app-inbox-count"].has_selector,
        "unicode_byte_offsets_normalized": specs["my-app-account-card-greeting"].location.byte_start
        > specs["my-app-account-card-greeting"].location.char_start,
    }
    require(all(catalog_gates.values()), f"catalog proof gates failed: {catalog_gates!r}")

    type_examples = {
        expression: parse_python_type(expression)
        for expression in ("str", "Decimal", "date | None", "list[str]", "Slot")
    }
    type_rejections = {
        expression: expect_error(
            f"reject type {expression}",
            lambda expression=expression: parse_python_type(expression),
            "unsupported",
        )
        for expression in ("factory()", "lambda: str", "str + int", "list[[x for x in xs]]")
    }

    malformed_source = "# @param {str} name\nbroken = { $name }\n"
    junk_source = "broken = {\n"
    orphan_source = "# @param {str} $name\n\norphan = { $name }\n"
    translation_param = "# @param {str} $name\ntranslated = { $name }\n"
    duplicate_param = "# @param {str} $name\n# @param {str} $name\nduplicate = { $name }\n"
    duplicate_message = "same = First.\nsame = Second.\n"
    term_param = "# @param {str} $name\n-private = { $name }\n"
    missing_param = "missing = { $name }\n"
    unused_param = "# @param {str} $name\nunused = No variable.\n"
    source_rejections = {
        "malformed_param": expect_error(
            "malformed param", lambda: parse_catalog(malformed_source, source_catalog=True), "malformed"
        ),
        "junk": expect_error("junk", lambda: parse_catalog(junk_source, source_catalog=True), "Junk"),
        "orphan_param": expect_error(
            "orphan param", lambda: parse_catalog(orphan_source, source_catalog=True), "attached directly"
        ),
        "translation_param": expect_error(
            "translation param",
            lambda: parse_catalog(translation_param, source_catalog=False),
            "must not redeclare",
        ),
        "duplicate_param": expect_error(
            "duplicate param",
            lambda: parse_catalog(duplicate_param, source_catalog=True),
            "duplicate",
        ),
        "duplicate_message": expect_error(
            "duplicate message",
            lambda: parse_catalog(duplicate_message, source_catalog=True),
            "duplicate Fluent message ID",
        ),
        "term_param": expect_error(
            "term param",
            lambda: parse_catalog(term_param, source_catalog=True),
            "not Fluent terms",
        ),
        "missing_param": expect_error(
            "missing param",
            lambda: parse_catalog(missing_param, source_catalog=True),
            "missing=['name']",
        ),
        "unused_param": expect_error(
            "unused param",
            lambda: parse_catalog(unused_param, source_catalog=True),
            "unused=['name']",
        ),
    }

    app = Citry(extensions=[SpikeI18nExtension], autodiscover=False)

    class InlineMessages(Component):
        citry = app
        name = "spike-inline-messages"
        messages = """
            inline-message = Inline.
        """

    class FileMessages(Component):
        citry = app
        name = "spike-file-messages"
        messages_file = "fixtures/source.ftl"

    class InheritedFileMessages(FileMessages):
        name = "spike-inherited-file-messages"

    class ClearedMessages(FileMessages):
        name = "spike-cleared-messages"
        messages = None

    class ConflictingMessages(Component):
        citry = app
        name = "spike-conflicting-messages"
        messages = "inline-message = Inline."
        messages_file = "fixtures/source.ftl"

    inline_content, inline_path = _load_pair(InlineMessages, "messages", "messages_file")
    file_content, file_path = _load_pair(FileMessages, "messages", "messages_file")
    inherited_content, inherited_path = _load_pair(InheritedFileMessages, "messages", "messages_file")
    cleared_content, cleared_path = _load_pair(ClearedMessages, "messages", "messages_file")
    asset_gates = {
        "inline_dedented": inline_content == "\ninline-message = Inline.\n",
        "inline_has_no_path": inline_path is None,
        "file_utf8_loaded": file_content == source and file_path == source_path.resolve(),
        "declaration_owner_inherited": inherited_content == source and inherited_path == source_path.resolve(),
        "explicit_none_clears": cleared_content is None and cleared_path is None,
        "file_index_registered": FileMessages in app.get_components_for_file(source_path),
    }
    require(all(asset_gates.values()), f"asset proof gates failed: {asset_gates!r}")
    pair_error = expect_error(
        "message pair conflict",
        lambda: validate_declared_message_pair(ConflictingMessages),
        "mutually exclusive",
    )

    captured_config: list[tuple[str, ...]] = []

    class Configured(Component):
        citry = app
        name = "spike-configured"

        class I18n:
            client_messages = ("my-app-runtime-only",)

        def template_data(self, kwargs, slots):
            configured = self.i18n.client_messages
            captured_config.append(configured)
            return {"configured": configured}

        template = """
          <span>{{ configured[0] }}</span>
        """

    class ConfiguredChild(Configured):
        name = "spike-configured-child"

        class I18n:
            client_messages = ("my-app-child-runtime-only",)

    class ConfiguredReset(Configured):
        name = "spike-configured-reset"
        I18n = None

    configured_render = str(Configured())
    child_render = str(ConfiguredChild())
    component_config_gates = {
        "configured_rendered": "my-app-runtime-only" in configured_render,
        "child_rendered": "my-app-child-runtime-only" in child_render,
        "configured_value": Configured.I18n.client_messages == ("my-app-runtime-only",),
        "child_replacement": ConfiguredChild.I18n.client_messages == ("my-app-child-runtime-only",),
        "reset_to_default": ConfiguredReset.I18n.client_messages == (),
        "render_access_recorded": captured_config == [("my-app-runtime-only",), ("my-app-child-runtime-only",)],
    }
    require(
        all(component_config_gates.values()),
        f"component config proof gates failed: {component_config_gates!r}",
    )

    invalid_config_error = expect_error(
        "invalid nested config",
        lambda: type(
            "InvalidI18nConfig",
            (Component,),
            {
                "citry": app,
                "name": "spike-invalid-i18n-config",
                "I18n": type("I18n", (), {"client_messages": ("same", "same")}),
            },
        ),
        "duplicates",
    )

    rich_id = "my-app-terms-acceptance"
    rich_spec = specs[rich_id]
    rich_message = message_by_id(translation_resource, rich_id)

    class Trans(Component):
        citry = app
        name = "trans"
        transparent = True

        def template_data(self, kwargs, slots):
            message_id = kwargs.get("id")
            if message_id != rich_id:
                raise ContractError(f"spike Trans only knows {rich_id!r}")
            values = kwargs.get("values", {})
            if not isinstance(values, dict):
                raise ContractError("values must be a mapping")
            return {"segments": render_simple_rich_pattern(rich_message, rich_spec, values, slots)}

        template = """
          <c-for each="segment in segments">{{ segment }}</c-for>
        """

    class RichPage(Component):
        citry = app
        name = "spike-rich-page"
        transparent = True

        def template_data(self, kwargs, slots):
            return {"account_name": "<Ada>"}

        template = """
          <c-trans
            id="my-app-terms-acceptance"
            c-values="{'account_name': account_name}"
          >
            <c-fill name="terms_link"><a href="/terms">Terms &amp; conditions</a></c-fill>
          </c-trans>
        """

    rendered = str(RichPage()).strip()
    rich_render_gates = {
        "application_anchor_preserved": rendered.startswith('<a href="/terms">'),
        "catalog_text_escaped": "<unsafe>" not in rendered and rendered.endswith("&lt;unsafe&gt;&amp;"),
        "scalar_value_escaped": "&lt;Ada&gt;" in rendered,
        "translator_reordered_slot": rendered.startswith(
            '<a href="/terms">Terms &amp; conditions</a> was accepted by '
        ),
    }
    require(all(rich_render_gates.values()), f"rich render proof gates failed: {rich_render_gates!r}")

    validation_errors = {
        "missing_fill": expect_error(
            "missing fill",
            lambda: validate_rich_inputs(rich_spec, {"account_name": "Ada"}, {}),
            "fills mismatch",
        ),
        "unknown_fill": expect_error(
            "unknown fill",
            lambda: validate_rich_inputs(
                rich_spec,
                {"account_name": "Ada"},
                {"terms_link": Slot("terms"), "extra": Slot("extra")},
            ),
            "fills mismatch",
        ),
        "value_fill_collision": expect_error(
            "value fill collision",
            lambda: validate_rich_inputs(
                rich_spec,
                {"account_name": "Ada", "terms_link": "wrong"},
                {"terms_link": Slot("terms")},
            ),
            "both a value and a fill",
        ),
    }

    missing_slot_resource = parse_catalog(
        "my-app-terms-acceptance = Accepted by { $account_name }.\n",
        source_catalog=False,
    )[1]
    duplicate_slot_resource = parse_catalog(
        "my-app-terms-acceptance = { $terms_link } then { $terms_link } for { $account_name }.\n",
        source_catalog=False,
    )[1]
    valid_rich_values = {"account_name": "Ada"}
    valid_rich_slots = {"terms_link": Slot("terms")}
    validation_errors["translation_missing_slot"] = expect_error(
        "translation missing slot",
        lambda: render_simple_rich_pattern(
            message_by_id(missing_slot_resource, rich_id),
            rich_spec,
            valid_rich_values,
            valid_rich_slots,
        ),
        "omits required rich placeholders",
    )
    repeated_segments = render_simple_rich_pattern(
        message_by_id(duplicate_slot_resource, rich_id),
        rich_spec,
        valid_rich_values,
        valid_rich_slots,
    )
    repeated_slot_occurrences = sum(segment is valid_rich_slots["terms_link"] for segment in repeated_segments)
    require(repeated_slot_occurrences == 2, "repeated Slot occurrences were not preserved structurally")
    rich_render_gates["translation_repeated_slot_expanded"] = repeated_slot_occurrences == 2

    selector_message = message_by_id(source_resource, "my-app-inbox-count")
    evaluator_limit = expect_error(
        "selector evaluator limit",
        lambda: render_simple_rich_pattern(
            selector_message,
            specs["my-app-inbox-count"],
            {"count": 2},
            {},
        ),
        "direct text and variable",
    )

    template_source = (
        '<c-trans id="my-app-terms-acceptance" '
        "c-values=\"{'account_name': account_name}\">"
        '<c-fill name="terms_link"><a>Terms</a></c-fill></c-trans>'
    )
    parser_debug = repr(parse_template(template_source).elements[0])
    parser_evidence = {
        "ordinary_component_retained": 'content: "c-trans"' in parser_debug,
        "ordinary_fill_retained": 'content: "c-fill"' in parser_debug,
        "source_spans_retained": all(marker in parser_debug for marker in ("start_index:", "end_index:", "line_col:")),
        "contains_fills_retained": "contains_fills: true" in parser_debug,
    }
    require(all(parser_evidence.values()), f"V3 parser proof gates failed: {parser_evidence!r}")

    proof_gates = {
        "assets": all(asset_gates.values()) and bool(pair_error),
        "catalog": all(catalog_gates.values()),
        "component_config": all(component_config_gates.values()) and bool(invalid_config_error),
        "python_safety": safety_evidence["assert_statements"] == 0
        and safety_evidence["optimized_negative_self_test_rejected"],
        "rich_message": all(rich_render_gates.values()) and all(validation_errors.values()) and bool(evaluator_limit),
        "source_rejections": len(source_rejections) == 9 and all(source_rejections.values()),
        "type_rejections": len(type_rejections) == 4 and all(type_rejections.values()),
        "v3_parser": all(parser_evidence.values()),
    }
    passed = all(proof_gates.values())
    require(passed, f"one or more source-spike proof groups failed: {proof_gates!r}")
    citry_evidence = citry_source_evidence()

    return {
        "schema_version": 2,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "fluent_syntax": importlib.metadata.version("fluent.syntax"),
            "distributions": distributions,
            "tools": tool_versions,
            "citry": citry_evidence,
        },
        "fixtures": {
            "source_sha256": sha256(source_path),
            "translation_sha256": sha256(translation_path),
        },
        "catalog": {
            "message_count": len(specs),
            "messages": [asdict(spec) for spec in specs.values()],
            "type_examples": type_examples,
            "type_rejection_count": len(type_rejections),
            "source_rejections": source_rejections,
        },
        "assets": {
            **asset_gates,
            "pair_conflict": pair_error,
            "production_integration_required": True,
        },
        "component_config": {
            "configured": list(Configured.I18n.client_messages),
            "child_replacement": list(ConfiguredChild.I18n.client_messages),
            "reset": list(ConfiguredReset.I18n.client_messages),
            "render_access": [list(item) for item in captured_config],
            "invalid_declaration": invalid_config_error,
            "proof_gates": component_config_gates,
        },
        "python_optimization_safety": safety_evidence,
        "proof_gates": proof_gates,
        "rich_message": {
            "rendered": rendered,
            **rich_render_gates,
            "translation_repeated_slot_occurrences": repeated_slot_occurrences,
            "validation_errors": validation_errors,
            "selector_limit": evaluator_limit,
        },
        "v3_parser": parser_evidence,
        "result": "PASS_BOUNDED" if passed else "FAIL",
    }


if __name__ == "__main__":
    if sys.argv[1:] == ["--negative-self-test"]:
        print(json.dumps({"optimization_level": sys.flags.optimize}, sort_keys=True))
        raise AssertionError("intentional always-on failure")
    require(not sys.argv[1:], f"unexpected arguments: {sys.argv[1:]!r}")
    print(json.dumps(run(), indent=2, sort_keys=True))
