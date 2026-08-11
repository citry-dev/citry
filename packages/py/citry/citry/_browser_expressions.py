"""Portable extraction and lexical scanning for Citry browser expressions."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from citry._json_wire import JsonWireType
from citry_core.template_parser import (
    HtmlAttrKind,
    TemplateElement,
    parse_template,
)
from citry_core.template_parser import (
    analyze_browser_source as analyze_browser_source_rust,
)
from citry_core.template_parser import (
    analyze_component_scope_writes as analyze_component_scope_writes_rust,
)
from citry_core.template_parser import (
    analyze_component_source as analyze_component_source_rust,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from citry_core.template_parser import Template


BrowserExpressionMode = Literal["expression", "statement", "loop"]
SERVER_EVENT_CALL_NAMES = frozenset({"$error", "$loading", "$sendEvent", "error", "loading", "sendEvent"})


@dataclass(frozen=True, slots=True)
class BrowserExpression:
    """One exact Alpine/Citry browser-expression host in template source."""

    source: str
    start_index: int
    end_index: int
    mode: BrowserExpressionMode
    attribute: str
    bindings: tuple[str, ...] = ()
    binding_details: tuple[BrowserBinding, ...] = ()


@dataclass(frozen=True, slots=True)
class BrowserBinding:
    """One parser-scoped Alpine binding and its source expression."""

    name: str
    start_index: int
    end_index: int
    kind: Literal["x-data", "x-for"]
    position: int
    source: str
    source_start_index: int
    source_end_index: int


@dataclass(frozen=True, slots=True)
class BrowserCompletion:
    """The identifier prefix and exact UTF-8 replacement span at a cursor."""

    prefix: str
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class BrowserIdentifier:
    """One JavaScript identifier token and whether it is unqualified."""

    name: str
    start_index: int
    end_index: int
    root: bool


@dataclass(frozen=True, slots=True)
class BrowserMember:
    """One simple ``owner.member`` reference in authored JavaScript."""

    owner: str
    name: str
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class BrowserLiteralCall:
    """One literal first argument to a named browser call."""

    function: str
    value: str
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class BrowserDeclarativeEvent:
    """One literal handler name authored in an ``@c-*`` binding."""

    name: str
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class BrowserScopeWrite:
    """One direct synchronous `$component` scope-property assignment."""

    name: str
    start_index: int
    end_index: int
    value_start_index: int
    value_end_index: int
    value_source: str


@dataclass(frozen=True, slots=True)
class BrowserComponentBinding:
    """One local name destructured from the `$component` context."""

    name: str
    local_name: str
    start_index: int
    end_index: int
    references: tuple[tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class BrowserComponentSourceAnalysis:
    """Portable OXC facts for runtime `$component` initializers."""

    valid: bool
    references: tuple[BrowserFreeReference, ...]
    bindings: tuple[BrowserComponentBinding, ...]
    scope_writes: tuple[BrowserScopeWrite, ...]


@dataclass(frozen=True, slots=True)
class BrowserProp:
    """One conservatively parsed `$component` client-prop declaration."""

    name: str
    javascript: str
    required: bool
    has_default: bool
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class BrowserObjectProperty:
    """One static key and value in an authored JavaScript object literal."""

    name: str
    start_index: int
    end_index: int
    value_source: str
    value_start_index: int
    value_end_index: int


@dataclass(frozen=True, slots=True)
class BrowserComponentPropsUse:
    """One direct `$c-props` object passed to a statically named child tag."""

    tag_name: str
    start_index: int
    end_index: int
    properties: tuple[BrowserObjectProperty, ...]
    has_dynamic_keys: bool


@dataclass(frozen=True, slots=True)
class BrowserFreeReference:
    """One OXC-proven free identifier mapped to template source."""

    name: str
    start_index: int
    end_index: int


@dataclass(frozen=True, slots=True)
class BrowserSourceAnalysis:
    """Portable syntax and free-reference result for one browser host."""

    valid: bool
    references: tuple[BrowserFreeReference, ...]


_EXPRESSION_ATTRIBUTES = frozenset(
    {
        "$c-props",
        "x-bind",
        "x-data",
        "x-html",
        "x-id",
        "x-if",
        "x-model",
        "x-modelable",
        "x-on",
        "x-show",
        "x-text",
    }
)
_STATEMENT_ATTRIBUTES = frozenset({"x-effect", "x-init", "x-intersect"})
_JS_KEYWORDS = frozenset(
    {
        "await",
        "break",
        "case",
        "catch",
        "class",
        "const",
        "continue",
        "debugger",
        "default",
        "delete",
        "do",
        "else",
        "export",
        "extends",
        "false",
        "finally",
        "for",
        "function",
        "if",
        "import",
        "in",
        "instanceof",
        "let",
        "new",
        "null",
        "of",
        "return",
        "static",
        "super",
        "switch",
        "this",
        "throw",
        "true",
        "try",
        "typeof",
        "undefined",
        "var",
        "void",
        "while",
        "with",
        "yield",
    }
)


@dataclass(frozen=True, slots=True)
class _Token:
    kind: Literal["identifier", "string", "punctuation"]
    source: str
    start: int
    end: int
    value: str | None = None


def browser_expressions(
    template: Template,
    *,
    parse_nested: Callable[[str], Template] = parse_template,
) -> tuple[BrowserExpression, ...]:
    """Extract supported Alpine/Citry browser hosts, including nested templates."""
    found: list[BrowserExpression] = []
    _collect_browser_expressions(template, found, parse_nested=parse_nested, base_index=0, bindings=())
    return tuple(sorted(found, key=lambda item: (item.start_index, item.end_index)))


def browser_declarative_events(
    template: Template,
    known_names: frozenset[str] = frozenset(),
    *,
    parse_nested: Callable[[str], Template] = parse_template,
) -> tuple[BrowserDeclarativeEvent, ...]:
    """Extract literal server handlers from parser-proven ``@c-*`` bindings."""
    found: list[BrowserDeclarativeEvent] = []
    _collect_declarative_events(
        template,
        found,
        known_names=known_names,
        parse_nested=parse_nested,
        base_index=0,
    )
    return tuple(sorted(found, key=lambda item: (item.start_index, item.end_index)))


def browser_bindings(
    template: Template,
    *,
    parse_nested: Callable[[str], Template] = parse_template,
) -> tuple[BrowserBinding, ...]:
    """Return every exact Alpine binding declaration, including nested templates."""
    found: list[BrowserBinding] = []
    _collect_browser_bindings(
        template,
        found,
        parse_nested=parse_nested,
        base_index=0,
    )
    return tuple(sorted(found, key=lambda item: (item.start_index, item.end_index)))


def browser_component_scope_writes(source: str) -> tuple[BrowserScopeWrite, ...]:
    """Return OXC-proven synchronous scope writes from component JavaScript."""
    encoded = source.encode("utf-8")
    return tuple(
        BrowserScopeWrite(
            name,
            name_start,
            name_end,
            value_start,
            value_end,
            encoded[value_start:value_end].decode("utf-8"),
        )
        for name, name_start, name_end, value_start, value_end in analyze_component_scope_writes_rust(source)
        if 0 <= name_start < name_end <= len(encoded) and 0 <= value_start <= value_end <= len(encoded)
    )


def analyze_browser_component_source(source: str) -> BrowserComponentSourceAnalysis:
    """Return source-proven bindings, free names, and scope writes for `$component`."""
    valid, references, bindings, writes = analyze_component_source_rust(source)
    encoded = source.encode("utf-8")
    return BrowserComponentSourceAnalysis(
        valid=valid,
        references=tuple(
            BrowserFreeReference(name, start, end)
            for name, start, end in references
            if 0 <= start < end <= len(encoded)
        ),
        bindings=tuple(
            BrowserComponentBinding(
                name,
                local_name,
                start,
                end,
                tuple(
                    (reference_start, reference_end)
                    for reference_start, reference_end in references
                    if 0 <= reference_start < reference_end <= len(encoded)
                ),
            )
            for name, local_name, start, end, references in bindings
            if 0 <= start < end <= len(encoded)
        ),
        scope_writes=tuple(
            BrowserScopeWrite(
                name,
                name_start,
                name_end,
                value_start,
                value_end,
                encoded[value_start:value_end].decode("utf-8"),
            )
            for name, name_start, name_end, value_start, value_end in writes
            if 0 <= name_start < name_end <= len(encoded) and 0 <= value_start <= value_end <= len(encoded)
        ),
    )


def browser_literal_wire_type(source: str) -> JsonWireType:
    """Infer broad JSON types from direct JavaScript literals only."""
    value = source.strip()
    if value in {"true", "false"}:
        return JsonWireType("boolean", literal=value == "true")
    if value == "null":
        return JsonWireType("null")
    if _javascript_number(value):
        return JsonWireType("number")
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'", "`"}:
        return JsonWireType("string")
    if value.startswith("[") and value.endswith("]"):
        return JsonWireType("array", (JsonWireType("unknown"),))
    if value.startswith("{") and value.endswith("}"):
        return JsonWireType("object", additional=JsonWireType("unknown"))
    return JsonWireType("unknown")


def browser_client_prop_accepts(expected: str, actual: JsonWireType) -> bool:
    """Compare the broad JSON kinds proven by static prop declarations."""
    if actual.kind == "union":
        return all(browser_client_prop_accepts(expected, item) for item in actual.items)
    alternatives = {item.strip() for item in expected.split("|")}
    if "unknown" in alternatives:
        return True
    if actual.kind in {"string", "number", "boolean", "null"}:
        return actual.kind in alternatives
    if actual.kind == "array":
        return any(item.startswith("Array<") for item in alternatives)
    if actual.kind == "object":
        return any(item == "Record<string, unknown>" or item.startswith("{") for item in alternatives)
    return True


def browser_component_prop_uses(
    template: Template,
    *,
    parse_nested: Callable[[str], Template] = parse_template,
) -> tuple[BrowserComponentPropsUse, ...]:
    """Return direct object literals passed through `$c-props`."""
    found: list[BrowserComponentPropsUse] = []
    _collect_component_prop_uses(
        template,
        found,
        parse_nested=parse_nested,
        base_index=0,
    )
    return tuple(found)


def analyze_browser_expression(expression: BrowserExpression) -> BrowserSourceAnalysis:
    """Analyze one host with OXC and preserve authored UTF-8 coordinates."""
    source = expression.source
    relative_start = 0
    mode = expression.mode
    if mode == "loop":
        split = _loop_separator(source)
        if split is None:
            return BrowserSourceAnalysis(valid=False, references=())
        relative_start = split[1]
        while relative_start < len(source) and source[relative_start].isspace():
            relative_start += 1
        source = source[relative_start:]
        mode = "expression"
    valid, raw_references = analyze_browser_source_rust(source, mode)
    if not valid:
        return BrowserSourceAnalysis(valid=False, references=())
    base = expression.start_index + len(expression.source[:relative_start].encode("utf-8"))
    references = tuple(BrowserFreeReference(name, base + start, base + end) for name, start, end in raw_references)
    return BrowserSourceAnalysis(valid=True, references=references)


def browser_expression_at(
    template: Template,
    index: int,
    *,
    parse_nested: Callable[[str], Template] = parse_template,
) -> BrowserExpression | None:
    """Return the innermost supported browser host at one UTF-8 index."""
    matches = [
        expression
        for expression in browser_expressions(template, parse_nested=parse_nested)
        if expression.start_index <= index <= expression.end_index
    ]
    return min(matches, key=lambda item: item.end_index - item.start_index) if matches else None


def browser_completion_at(expression: BrowserExpression, index: int) -> BrowserCompletion | None:
    """Locate an unqualified identifier prefix in browser expression source."""
    relative = index - expression.start_index
    boundaries = _utf8_boundaries(expression.source)
    if relative not in boundaries:
        return None
    cursor = boundaries.index(relative)
    if not _cursor_is_code(expression.source, cursor):
        return None
    start = cursor
    while start > 0 and _identifier_continue(expression.source[start - 1]):
        start -= 1
    prefix = expression.source[start:cursor]
    if prefix and not _identifier_start(prefix[0]):
        return None
    before = expression.source[:start].rstrip()
    if before.endswith((".", "?.")):
        return None
    if prefix in _JS_KEYWORDS:
        return None
    loop_split = _loop_separator(expression.source) if expression.mode == "loop" else None
    if loop_split is not None and cursor <= loop_split[1]:
        return None
    end = cursor
    while end < len(expression.source) and _identifier_continue(expression.source[end]):
        end += 1
    return BrowserCompletion(
        prefix,
        expression.start_index + boundaries[start],
        expression.start_index + boundaries[end],
    )


def browser_identifier_at(expression: BrowserExpression, index: int) -> BrowserIdentifier | None:
    """Resolve one exact identifier token while excluding comments and strings."""
    relative = index - expression.start_index
    tokens = _tokens(expression.source)
    for token_index, token in enumerate(tokens):
        if token.kind != "identifier":
            continue
        start = len(expression.source[: token.start].encode("utf-8"))
        end = len(expression.source[: token.end].encode("utf-8"))
        if start <= relative < end or (relative == end and start < end):
            previous = _previous_token(tokens, token_index)
            root = previous is None or previous.source not in {".", "?."}
            if token.source in expression.bindings:
                root = False
            loop_split = _loop_separator(expression.source) if expression.mode == "loop" else None
            if loop_split is not None and token.end <= loop_split[1]:
                root = False
            return BrowserIdentifier(
                token.source,
                expression.start_index + start,
                expression.start_index + end,
                root,
            )
    return None


def browser_identifiers(expression: BrowserExpression) -> tuple[BrowserIdentifier, ...]:
    """Return every code identifier with root/binding classification."""
    found: list[BrowserIdentifier] = []
    seen: set[tuple[int, int]] = set()
    for token in _tokens(expression.source):
        if token.kind != "identifier":
            continue
        start = expression.start_index + len(expression.source[: token.start].encode("utf-8"))
        identifier = browser_identifier_at(expression, start)
        if identifier is not None and (identifier.start_index, identifier.end_index) not in seen:
            seen.add((identifier.start_index, identifier.end_index))
            found.append(identifier)
    return tuple(found)


def browser_member_at(expression: BrowserExpression, index: int) -> BrowserMember | None:
    """Resolve a simple member without guessing through calls or computed keys."""
    relative = index - expression.start_index
    tokens = _tokens(expression.source)
    boundaries = _utf8_boundaries(expression.source)
    for token_index, token in enumerate(tokens):
        if token.kind != "identifier":
            continue
        start = boundaries[token.start]
        end = boundaries[token.end]
        if not (start <= relative < end or (relative == end and start < end)):
            continue
        separator = _previous_token(tokens, token_index)
        if separator is None or separator.source not in {".", "?."}:
            return None
        owner = _previous_token(tokens, token_index - 1)
        if owner is None or owner.kind != "identifier":
            return None
        before_owner = _previous_token(tokens, token_index - 2)
        if before_owner is not None and before_owner.source in {".", "?."}:
            return None
        return BrowserMember(
            owner.source,
            token.source,
            expression.start_index + start,
            expression.start_index + end,
        )
    return None


def browser_literal_calls(
    expression: BrowserExpression,
    names: frozenset[str],
) -> tuple[BrowserLiteralCall, ...]:
    """Return exact literal first arguments for unqualified named calls."""
    tokens = _tokens(expression.source)
    boundaries = _utf8_boundaries(expression.source)
    found: list[BrowserLiteralCall] = []
    for index, token in enumerate(tokens):
        if token.kind != "identifier" or token.source not in names:
            continue
        previous = _previous_token(tokens, index)
        if previous is not None and previous.source in {".", "?."}:
            continue
        opening = _next_token(tokens, index)
        argument = _next_token(tokens, index + 1)
        if opening is None or opening.source != "(" or argument is None or argument.kind != "string":
            continue
        if argument.value is None:
            continue
        content_start = argument.start + 1
        content_end = max(content_start, argument.end - 1)
        found.append(
            BrowserLiteralCall(
                token.source,
                argument.value,
                expression.start_index + boundaries[content_start],
                expression.start_index + boundaries[content_end],
            )
        )
    return tuple(found)


def python_event_handler_coordinates(
    source: str,
    function_qualname: str,
    method_name: str,
    wire_name: str,
) -> tuple[int, int, int, int] | None:
    """Locate an effective event method only while its authored wire name agrees."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, TypeError, MemoryError, RecursionError):
        return None
    if not function_qualname or "<locals>" in function_qualname:
        return None
    body: list[ast.stmt] = tree.body
    parts = function_qualname.split(".")
    for part in parts[:-1]:
        class_matches = [
            statement for statement in body if isinstance(statement, ast.ClassDef) and statement.name == part
        ]
        if len(class_matches) != 1:
            return None
        body = class_matches[0].body
    method_matches = [
        statement
        for statement in body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)) and statement.name == parts[-1]
    ]
    if len(method_matches) != 1 or parts[-1] != method_name:
        return None
    method = method_matches[0]
    current_wire = method_name
    for decorator in method.decorator_list:
        if not isinstance(decorator, ast.Call) or _qualified_tail(decorator.func) != "event":
            continue
        names = [keyword.value for keyword in decorator.keywords if keyword.arg == "name"]
        if len(names) > 1:
            return None
        if names:
            name = names[0]
            if not isinstance(name, ast.Constant) or type(name.value) is not str or not name.value:
                return None
            current_wire = name.value
    if current_wire != wire_name:
        return None
    line = source.splitlines(keepends=True)[method.lineno - 1]
    declaration_start = len(line.encode("utf-8")[: method.col_offset].decode("utf-8"))
    name_start = line.find(method.name, declaration_start)
    if name_start < 0:
        return None
    return (
        method.lineno - 1,
        len(line[:name_start].encode("utf-16-le")) // 2,
        method.lineno - 1,
        len(line[: name_start + len(method.name)].encode("utf-16-le")) // 2,
    )


def browser_component_props(source: str) -> tuple[BrowserProp, ...] | None:
    """Parse the supported `$component({props, init})` declaration subset."""
    tokens = _tokens(source)
    for index, token in enumerate(tokens):
        if token.kind != "identifier" or token.source != "$component":
            continue
        opening = _next_token(tokens, index)
        config = _next_token(tokens, index + 1)
        if opening is None or opening.source != "(" or config is None:
            continue
        if config.source != "{":
            return ()
        config_end = _matching_token(tokens, index + 2, "{", "}")
        if config_end is None:
            return None
        props_value = _object_property_value(tokens, index + 2, config_end, "props")
        if props_value is None:
            return ()
        if tokens[props_value].source != "{":
            return None
        props_end = _matching_token(tokens, props_value, "{", "}")
        if props_end is None:
            return None
        return _prop_definitions(source, tokens, props_value + 1, props_end)
    return ()


def _prop_definitions(
    source: str,
    tokens: tuple[_Token, ...],
    start: int,
    end: int,
) -> tuple[BrowserProp, ...] | None:
    fields: list[BrowserProp] = []
    index = start
    while index < end:
        token = tokens[index]
        if token.source == ",":
            index += 1
            continue
        name = token.source if token.kind == "identifier" else token.value
        if name is None or index + 2 >= end or tokens[index + 1].source != ":" or tokens[index + 2].source != "{":
            return None
        definition_start = index + 2
        definition_end = _matching_token(tokens, definition_start, "{", "}")
        if definition_end is None or definition_end > end:
            return None
        type_index = _object_property_value(tokens, definition_start, definition_end, "type")
        required_index = _object_property_value(tokens, definition_start, definition_end, "required")
        default_index = _object_property_value(tokens, definition_start, definition_end, "default")
        constructors = _prop_constructors(tokens, type_index, definition_end)
        javascript = _prop_javascript(constructors)
        required = required_index is not None and tokens[required_index].source == "true"
        has_default = default_index is not None
        if default_index is not None and tokens[default_index].source == "null":
            javascript = f"{javascript} | null"
        elif not required and not has_default:
            javascript = f"{javascript} | undefined"
        fields.append(
            BrowserProp(
                name,
                javascript,
                required,
                has_default,
                len(source[: token.start].encode("utf-8")),
                len(source[: token.end].encode("utf-8")),
            )
        )
        index = definition_end + 1
    return tuple(fields)


def _browser_object_literal(source: str, *, base_index: int) -> tuple[tuple[BrowserObjectProperty, ...], bool] | None:
    """Parse static top-level keys while remembering whether dynamic keys remain."""
    tokens = _tokens(source)
    if not tokens or tokens[0].source != "{":
        return None
    closing = _matching_token(tokens, 0, "{", "}")
    if closing is None or closing != len(tokens) - 1:
        return None
    properties: list[BrowserObjectProperty] = []
    has_dynamic_keys = False
    index = 1
    while index < closing:
        if tokens[index].source == ",":
            index += 1
            continue
        if tokens[index].source == "..." or tokens[index].source == "[":
            # A spread or computed key can add any property, but later direct
            # keys remain useful for unknown-key and type checks.
            has_dynamic_keys = True
            index = _object_entry_end(tokens, index + 1, closing)
            continue
        key = tokens[index]
        name = key.source if key.kind == "identifier" else key.value
        if name is None:
            return None
        next_index = index + 1
        if next_index >= closing or tokens[next_index].source in {",", "}"}:
            if key.kind != "identifier":
                return None
            value_start = key.start
            value_end = key.end
            index = next_index
        elif tokens[next_index].source == ":":
            value_index = next_index + 1
            if value_index >= closing:
                return None
            entry_end = _object_entry_end(tokens, value_index, closing)
            last_value = entry_end - 1
            if last_value < value_index:
                return None
            value_start = tokens[value_index].start
            value_end = tokens[last_value].end
            index = entry_end
        else:
            return None
        properties.append(
            BrowserObjectProperty(
                name,
                base_index + len(source[: key.start].encode("utf-8")),
                base_index + len(source[: key.end].encode("utf-8")),
                source[value_start:value_end],
                base_index + len(source[:value_start].encode("utf-8")),
                base_index + len(source[:value_end].encode("utf-8")),
            )
        )
    return tuple(properties), has_dynamic_keys


def _object_entry_end(tokens: tuple[_Token, ...], start: int, closing: int) -> int:
    """Return the comma after one object entry without entering nested values."""
    depth = 0
    index = start
    while index < closing:
        source = tokens[index].source
        if source in {"{", "[", "("}:
            depth += 1
        elif source in {"}", "]", ")"}:
            depth = max(0, depth - 1)
        elif source == "," and depth == 0:
            return index
        index += 1
    return closing


def _object_property_value(
    tokens: tuple[_Token, ...],
    start: int,
    end: int,
    name: str,
) -> int | None:
    depth = 0
    index = start + 1
    while index < end:
        token = tokens[index]
        if token.source in {"{", "[", "("}:
            depth += 1
        elif token.source in {"}", "]", ")"}:
            depth = max(0, depth - 1)
        if (
            depth == 0
            and token.kind in {"identifier", "string"}
            and (token.value or token.source) == name
            and index + 2 < end
            and tokens[index + 1].source == ":"
        ):
            return index + 2
        index += 1
    return None


def _prop_constructors(tokens: tuple[_Token, ...], index: int | None, limit: int) -> tuple[str, ...]:
    if index is None:
        return ()
    if tokens[index].source != "[":
        return (tokens[index].source,) if tokens[index].kind == "identifier" else ()
    closing = _matching_token(tokens, index, "[", "]")
    if closing is None or closing > limit:
        return ()
    return tuple(token.source for token in tokens[index + 1 : closing] if token.kind == "identifier")


def _prop_javascript(constructors: tuple[str, ...]) -> str:
    mapped = {
        "String": "string",
        "Number": "number",
        "Boolean": "boolean",
        "Object": "Record<string, unknown>",
        "Array": "Array<unknown>",
        "Function": "Function",
        "BigInt": "bigint",
        "Symbol": "symbol",
    }
    retained = tuple(dict.fromkeys(mapped.get(constructor, "unknown") for constructor in constructors))
    return " | ".join(retained) if retained else "unknown"


def _matching_token(
    tokens: tuple[_Token, ...],
    start: int,
    opening: str,
    closing: str,
) -> int | None:
    if start >= len(tokens) or tokens[start].source != opening:
        return None
    depth = 0
    for index in range(start, len(tokens)):
        if tokens[index].source == opening:
            depth += 1
        elif tokens[index].source == closing:
            depth -= 1
            if depth == 0:
                return index
    return None


def _collect_browser_expressions(
    template: Template,
    found: list[BrowserExpression],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
    bindings: tuple[BrowserBinding, ...],
) -> None:
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        introduced = _node_browser_bindings(node, base_index)
        for attr in node.start_tag.attrs:
            inner = attr.inner_value
            if inner is None:
                continue
            if attr.kind == HtmlAttrKind.Template:
                nested = _nested_template(inner.content, parse_nested)
                if nested is not None:
                    parsed, nested_start = nested
                    _collect_browser_expressions(
                        parsed,
                        found,
                        parse_nested=parse_nested,
                        base_index=base_index + inner.start_index + nested_start,
                        bindings=(*bindings, *introduced),
                    )
                continue
            classified = _browser_attribute(attr.key.content, inner.content)
            if classified is None:
                continue
            mode, relative_start, relative_end = classified
            start = base_index + inner.start_index + len(inner.content[:relative_start].encode("utf-8"))
            end = base_index + inner.start_index + len(inner.content[:relative_end].encode("utf-8"))
            base_name = attr.key.content.split(".", 1)[0]
            active = bindings if mode == "loop" or base_name == "x-data" else (*bindings, *introduced)
            found.append(
                BrowserExpression(
                    inner.content[relative_start:relative_end],
                    start,
                    end,
                    mode,
                    attr.key.content,
                    tuple(binding.name for binding in active),
                    active,
                )
            )
        body = getattr(node, "body", None)
        if body is not None:
            _collect_browser_expressions(
                body,
                found,
                parse_nested=parse_nested,
                base_index=base_index,
                bindings=(*bindings, *introduced),
            )


def _collect_declarative_events(
    template: Template,
    found: list[BrowserDeclarativeEvent],
    *,
    known_names: frozenset[str],
    parse_nested: Callable[[str], Template],
    base_index: int,
) -> None:
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        for attr in node.start_tag.attrs:
            inner = attr.inner_value
            if inner is None:
                continue
            if attr.kind == HtmlAttrKind.Template:
                nested = _nested_template(inner.content, parse_nested)
                if nested is not None:
                    parsed, nested_start = nested
                    _collect_declarative_events(
                        parsed,
                        found,
                        known_names=known_names,
                        parse_nested=parse_nested,
                        base_index=base_index + inner.start_index + nested_start,
                    )
                continue
            if not attr.key.content.startswith("@c-"):
                continue
            resolved = _declarative_handler(inner.content, known_names)
            if resolved is None:
                continue
            name, start, end = resolved
            found.append(
                BrowserDeclarativeEvent(
                    name,
                    base_index + inner.start_index + len(inner.content[:start].encode("utf-8")),
                    base_index + inner.start_index + len(inner.content[:end].encode("utf-8")),
                )
            )
        body = getattr(node, "body", None)
        if body is not None:
            _collect_declarative_events(
                body,
                found,
                known_names=known_names,
                parse_nested=parse_nested,
                base_index=base_index,
            )


def _collect_browser_bindings(
    template: Template,
    found: list[BrowserBinding],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
) -> None:
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        found.extend(_node_browser_bindings(node, base_index))
        for attr in node.start_tag.attrs:
            inner = attr.inner_value
            if inner is None or attr.kind != HtmlAttrKind.Template:
                continue
            nested = _nested_template(inner.content, parse_nested)
            if nested is None:
                continue
            parsed, nested_start = nested
            _collect_browser_bindings(
                parsed,
                found,
                parse_nested=parse_nested,
                base_index=base_index + inner.start_index + nested_start,
            )
        body = getattr(node, "body", None)
        if body is not None:
            _collect_browser_bindings(
                body,
                found,
                parse_nested=parse_nested,
                base_index=base_index,
            )


def _collect_component_prop_uses(
    template: Template,
    found: list[BrowserComponentPropsUse],
    *,
    parse_nested: Callable[[str], Template],
    base_index: int,
) -> None:
    for element in template.elements:
        if not isinstance(element, TemplateElement.Node):
            continue
        node = element._0
        for attr in node.start_tag.attrs:
            inner = attr.inner_value
            if inner is None:
                continue
            if attr.kind == HtmlAttrKind.Template:
                nested = _nested_template(inner.content, parse_nested)
                if nested is not None:
                    parsed, nested_start = nested
                    _collect_component_prop_uses(
                        parsed,
                        found,
                        parse_nested=parse_nested,
                        base_index=base_index + inner.start_index + nested_start,
                    )
                continue
            if attr.key.content != "$c-props":
                continue
            expression_start = base_index + inner.start_index
            parsed_object = _browser_object_literal(inner.content, base_index=expression_start)
            if parsed_object is None:
                continue
            properties, has_dynamic_keys = parsed_object
            target_name = node.start_tag.name.content
            if target_name == "c-component":
                target = next(
                    (
                        candidate.inner_value.content.strip()
                        for candidate in node.start_tag.attrs
                        if candidate.key.content == "is" and candidate.inner_value is not None
                    ),
                    "",
                )
                if not target or any(char.isspace() for char in target):
                    continue
                target_name = target if target.startswith("c-") else f"c-{target}"
            found.append(
                BrowserComponentPropsUse(
                    target_name,
                    expression_start,
                    expression_start + len(inner.content.encode("utf-8")),
                    properties,
                    has_dynamic_keys,
                )
            )
        body = getattr(node, "body", None)
        if body is not None:
            _collect_component_prop_uses(
                body,
                found,
                parse_nested=parse_nested,
                base_index=base_index,
            )


def _declarative_handler(source: str, known_names: frozenset[str]) -> tuple[str, int, int] | None:
    leading = len(source) - len(source.lstrip())
    trailing = len(source.rstrip())
    text = source[leading:trailing]
    if not text:
        return None
    if text in known_names:
        return text, leading, trailing
    opening = text.find("(")
    if opening >= 0 and text.endswith(")"):
        handler = text[:opening].rstrip()
        if not handler:
            return None
        return handler, leading, leading + len(handler)
    return text, leading, trailing


def _node_browser_bindings(node: object, base_index: int) -> tuple[BrowserBinding, ...]:
    introduced: list[BrowserBinding] = []
    start_tag = getattr(node, "start_tag", None)
    for attr in getattr(start_tag, "attrs", ()):
        if attr.inner_value is None:
            continue
        if attr.key.content == "x-for":
            split = _loop_separator(attr.inner_value.content)
            if split is None:
                continue
            source = attr.inner_value.content
            left = source[: split[0]]
            binding_tokens = _simple_loop_binding_tokens(left)
            if binding_tokens is None:
                continue
            source_start = split[1]
            while source_start < len(source) and source[source_start].isspace():
                source_start += 1
            source_end = len(source.rstrip())
            iterable = source[source_start:source_end]
            for position, binding_token in enumerate(binding_tokens):
                introduced.append(
                    BrowserBinding(
                        binding_token.source,
                        base_index + attr.inner_value.start_index + len(source[: binding_token.start].encode("utf-8")),
                        base_index + attr.inner_value.start_index + len(source[: binding_token.end].encode("utf-8")),
                        "x-for",
                        position,
                        iterable,
                        base_index + attr.inner_value.start_index + len(source[:source_start].encode("utf-8")),
                        base_index + attr.inner_value.start_index + len(source[:source_end].encode("utf-8")),
                    )
                )
        elif attr.key.content.split(".", 1)[0] == "x-data":
            source = attr.inner_value.content
            tokens = _tokens(source)
            for name in _object_literal_names(source):
                name_token = next(
                    (
                        candidate
                        for candidate in tokens
                        if (candidate.source if candidate.kind == "identifier" else candidate.value) == name
                    ),
                    None,
                )
                if name_token is None:
                    continue
                introduced.append(
                    BrowserBinding(
                        name,
                        base_index + attr.inner_value.start_index + len(source[: name_token.start].encode("utf-8")),
                        base_index + attr.inner_value.start_index + len(source[: name_token.end].encode("utf-8")),
                        "x-data",
                        0,
                        source,
                        base_index + attr.inner_value.start_index,
                        base_index + attr.inner_value.end_index,
                    )
                )
    return tuple({binding.name: binding for binding in introduced}.values())


def _simple_loop_binding_tokens(source: str) -> tuple[_Token, ...] | None:
    """Accept direct and positional Alpine bindings without guessing object keys."""
    tokens = _tokens(source)
    identifiers = tuple(token for token in tokens if token.kind == "identifier")
    if not identifiers or any(
        token.kind != "identifier" and token.source not in {"(", ")", "[", "]", ","} for token in tokens
    ):
        return None
    return identifiers


def _object_literal_names(source: str) -> tuple[str, ...]:
    """Return static top-level keys from one direct JavaScript object literal."""
    tokens = _tokens(source)
    if not tokens or tokens[0].source != "{":
        return ()
    closing = _matching_token(tokens, 0, "{", "}")
    if closing is None or closing != len(tokens) - 1:
        return ()
    names: list[str] = []
    index = 1
    while index < closing:
        if tokens[index].source == ",":
            index += 1
            continue
        if tokens[index].source == "...":
            return ()
        token = tokens[index]
        name = token.source if token.kind == "identifier" else token.value
        next_token = tokens[index + 1] if index + 1 < closing else None
        if name is not None and (next_token is None or next_token.source in {":", "(", ",", "}"}):
            names.append(name)
        depth = 0
        index += 1
        while index < closing:
            punctuation = tokens[index].source
            if punctuation in {"{", "[", "("}:
                depth += 1
            elif punctuation in {"}", "]", ")"}:
                depth = max(0, depth - 1)
            elif punctuation == "," and depth == 0:
                index += 1
                break
            index += 1
    return tuple(dict.fromkeys(name for name in names if _js_identifier(name)))


def _loop_separator(source: str) -> tuple[int, int] | None:
    """Find Alpine's top-level ``in``/``of`` separator outside strings."""
    depth = 0
    for token in _tokens(source):
        if token.kind == "punctuation":
            if token.source in {"(", "[", "{"}:
                depth += 1
            elif token.source in {")", "]", "}"}:
                depth = max(0, depth - 1)
        if depth == 0 and token.kind == "identifier" and token.source in {"in", "of"}:
            return token.start, token.end
    return None


def _js_identifier(value: str) -> bool:
    return bool(value) and _identifier_start(value[0]) and all(_identifier_continue(char) for char in value[1:])


def _browser_attribute(name: str, source: str) -> tuple[BrowserExpressionMode, int, int] | None:
    if name.startswith("@c-"):
        opening = source.find("(")
        closing = source.rfind(")")
        if opening >= 0 and closing > opening and not source[closing + 1 :].strip():
            return "expression", opening + 1, closing
        return None
    base_name = name.split(".", 1)[0]
    if name.startswith(("@", "x-on:")):
        return "statement", 0, len(source)
    if name.startswith((":", "x-bind:")):
        return "expression", 0, len(source)
    if base_name == "x-for":
        return "loop", 0, len(source)
    if base_name in _EXPRESSION_ATTRIBUTES:
        return "expression", 0, len(source)
    if base_name in _STATEMENT_ATTRIBUTES or base_name.startswith("x-intersect:"):
        return "statement", 0, len(source)
    return None


def _nested_template(source: str, parser: Callable[[str], Template]) -> tuple[Template, int] | None:
    leading_chars = len(source) - len(source.lstrip())
    trailing_chars = len(source.rstrip())
    trimmed = source[leading_chars:trailing_chars]
    if not (trimmed.startswith("<>") and trimmed.endswith("</>")):
        return None
    nested = trimmed[2:-3]
    try:
        parsed = parser(nested)
    except (SyntaxError, ValueError):
        return None
    return parsed, len(source[:leading_chars].encode("utf-8")) + 2


def _tokens(source: str) -> tuple[_Token, ...]:
    tokens: list[_Token] = []
    index = 0
    while index < len(source):
        char = source[index]
        if char.isspace():
            index += 1
            continue
        if source.startswith("//", index):
            newline = source.find("\n", index + 2)
            index = len(source) if newline < 0 else newline + 1
            continue
        if source.startswith("/*", index):
            closing = source.find("*/", index + 2)
            index = len(source) if closing < 0 else closing + 2
            continue
        if char in {"'", '"', "`"}:
            end = _skip_string(source, index, char)
            raw = source[index:end]
            value = _decode_string(raw) if char != "`" else None
            tokens.append(_Token("string", raw, index, end, value))
            index = end
            continue
        if _identifier_start(char):
            end = index + 1
            while end < len(source) and _identifier_continue(source[end]):
                end += 1
            tokens.append(_Token("identifier", source[index:end], index, end))
            index = end
            continue
        punctuation = "..." if source.startswith("...", index) else "?." if source.startswith("?.", index) else char
        tokens.append(_Token("punctuation", punctuation, index, index + len(punctuation)))
        index += len(punctuation)
    return tuple(tokens)


def _cursor_is_code(source: str, cursor: int) -> bool:
    for token in _tokens(source):
        if token.start < cursor < token.end and token.kind == "string":
            return False
    prefix = source[:cursor]
    if prefix.rfind("//") > prefix.rfind("\n"):
        return False
    opening = prefix.rfind("/*")
    return opening < 0 or opening < prefix.rfind("*/")


def _skip_string(source: str, start: int, quote: str) -> int:
    index = start + 1
    while index < len(source):
        if source[index] == "\\":
            index += 2
            continue
        if source[index] == quote:
            return index + 1
        index += 1
    return len(source)


def _decode_string(source: str) -> str | None:
    if len(source) < 2 or source[-1] != source[0]:
        return None
    result: list[str] = []
    index = 1
    while index < len(source) - 1:
        char = source[index]
        if char != "\\":
            result.append(char)
            index += 1
            continue
        index += 1
        if index >= len(source) - 1:
            return None
        escaped = source[index]
        simple = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}
        result.append(simple.get(escaped, escaped))
        index += 1
    return "".join(result)


def _previous_token(tokens: tuple[_Token, ...], index: int) -> _Token | None:
    return tokens[index - 1] if index > 0 else None


def _next_token(tokens: tuple[_Token, ...], index: int) -> _Token | None:
    return tokens[index + 1] if index + 1 < len(tokens) else None


def _identifier_start(char: str) -> bool:
    return char in {"$", "_"} or char.isalpha() or (ord(char) >= 128 and char.isidentifier())


def _identifier_continue(char: str) -> bool:
    return _identifier_start(char) or char.isdigit()


def _javascript_number(source: str) -> bool:
    """Recognize ordinary decimal literals without evaluating JavaScript."""
    if not source:
        return False
    value = source.removeprefix("+").removeprefix("-")
    if not value:
        return False
    lower = value.lower()
    if "e" in lower:
        mantissa, exponent = lower.split("e", 1)
        if not exponent.removeprefix("+").removeprefix("-").isdigit():
            return False
    else:
        mantissa = lower
    if "." in mantissa:
        whole, fraction = mantissa.split(".", 1)
        return bool(whole or fraction) and (not whole or whole.isdigit()) and (not fraction or fraction.isdigit())
    return mantissa.isdigit()


def _utf8_boundaries(source: str) -> list[int]:
    boundaries = [0]
    total = 0
    for char in source:
        total += len(char.encode("utf-8"))
        boundaries.append(total)
    return boundaries


def _qualified_tail(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


__all__ = [
    "SERVER_EVENT_CALL_NAMES",
    "BrowserBinding",
    "BrowserCompletion",
    "BrowserComponentBinding",
    "BrowserComponentPropsUse",
    "BrowserComponentSourceAnalysis",
    "BrowserDeclarativeEvent",
    "BrowserExpression",
    "BrowserExpressionMode",
    "BrowserFreeReference",
    "BrowserIdentifier",
    "BrowserLiteralCall",
    "BrowserMember",
    "BrowserObjectProperty",
    "BrowserProp",
    "BrowserScopeWrite",
    "BrowserSourceAnalysis",
    "analyze_browser_component_source",
    "analyze_browser_expression",
    "browser_bindings",
    "browser_client_prop_accepts",
    "browser_completion_at",
    "browser_component_prop_uses",
    "browser_component_props",
    "browser_component_scope_writes",
    "browser_declarative_events",
    "browser_expression_at",
    "browser_expressions",
    "browser_identifier_at",
    "browser_identifiers",
    "browser_literal_calls",
    "browser_literal_wire_type",
    "browser_member_at",
    "python_event_handler_coordinates",
]
