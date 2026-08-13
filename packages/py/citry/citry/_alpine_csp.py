"""
Pinned static compatibility model for Alpine CSP 3.16.1 expressions.

The tokenizer and recursive-descent grammar mirror the small parser shipped by
``@alpinejs/csp``. This module classifies authored source only. It never runs
application code and deliberately leaves value-dependent evaluator checks to
the browser runtime.

The grammar is a clean Python port of Alpine's MIT-licensed CSP parser at the
exact version named below; its conformance fixture executes that upstream
implementation directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Callable

    from citry._browser_expressions import BrowserExpression

ALPINE_CSP_COMPATIBILITY_VERSION = "3.16.1"

_DANGEROUS_PROPERTIES = frozenset(
    {
        "constructor",
        "prototype",
        "__proto__",
        "__defineGetter__",
        "__defineSetter__",
        "insertAdjacentHTML",
        "setAttribute",
        "setAttributeNS",
        "setAttributeNode",
        "setAttributeNodeNS",
    }
)
_DOM_ROOTS = frozenset({"$el", "$refs", "$root"})
_KEYWORDS = frozenset({"new", "typeof", "void", "delete", "in", "instanceof"})
_GLOBAL_VALUE_NAMES = frozenset(
    {
        "Array",
        "Boolean",
        "Date",
        "Element",
        "Function",
        "Intl",
        "JSON",
        "Map",
        "Math",
        "Number",
        "Object",
        "Promise",
        "Reflect",
        "RegExp",
        "Set",
        "String",
        "Symbol",
        "URL",
        "URLSearchParams",
        "WeakMap",
        "WeakSet",
        "console",
        "document",
        "fetch",
        "globalThis",
        "history",
        "localStorage",
        "location",
        "navigator",
        "performance",
        "queueMicrotask",
        "requestAnimationFrame",
        "sessionStorage",
        "setInterval",
        "setTimeout",
        "structuredClone",
        "window",
    }
)


@dataclass(frozen=True, slots=True)
class AlpineCspClassification:
    """
    One source-level compatibility result and its UTF-8 range.

    ``compatible`` means the pinned grammar and statically knowable evaluator
    restrictions accept the source. Runtime values remain browser-enforced.
    """

    outcome: Literal["compatible", "incompatible", "runtime-dependent"]
    detail: str | None = None
    start_index: int = 0
    end_index: int = 0


@dataclass(frozen=True, slots=True)
class _Token:
    kind: str
    value: object
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class _Node:
    kind: str
    start: int
    end: int
    value: object = None
    children: tuple[_Node, ...] = ()
    computed: bool = False


class _CspError(Exception):
    def __init__(self, detail: str, start: int, end: int) -> None:
        super().__init__(detail)
        self.detail = detail
        self.start = start
        self.end = end


def classify_alpine_csp(expression: BrowserExpression) -> AlpineCspClassification:
    """Classify one extracted browser host against Alpine CSP 3.16.1."""
    attribute = expression.canonical_attribute
    base_attribute = attribute.split(".", 1)[0]
    attribute_start = expression.attribute_start_index
    attribute_end = expression.attribute_end_index

    if base_attribute == "x-html":
        return AlpineCspClassification(
            "incompatible",
            "the x-html directive",
            attribute_start if attribute_start is not None else expression.start_index,
            attribute_end if attribute_end is not None else expression.end_index,
        )

    source = expression.source
    empty_noop = (source == "" and attribute.startswith(("@", "x-on:"))) or (
        base_attribute == "x-init" and all(_js_whitespace(char) for char in source)
    )
    if empty_noop:
        return AlpineCspClassification("compatible")

    if expression.evaluator == "normal" and expression.element in {"iframe", "script"}:
        return AlpineCspClassification(
            "incompatible",
            f"normal expression evaluation on <{expression.element}>",
            attribute_start if attribute_start is not None else expression.start_index,
            attribute_end if attribute_end is not None else expression.end_index,
        )

    if expression.host == "citry-event-args" and not source.strip():
        return AlpineCspClassification("compatible")
    if base_attribute == "x-data" and source == "":
        source = "{}"

    if expression.transform == "x-for":
        items_range = _for_items_range(source)
        if items_range is None:
            return _absolute_issue(expression, "an x-for value without an 'in' or 'of' iterable", 0, len(source))
        items_start, items_end = items_range
        if items_start == items_end:
            return _absolute_issue(expression, "an empty x-for iterable", items_start, items_end)
        return _parse_for_expression(
            expression,
            source[items_start:items_end],
            items_start,
        )

    if expression.transform == "citry-args":
        return _parse_expression(expression, f"({source})", prefix=1)

    first = _parse_expression(expression, source)
    if first.outcome == "incompatible" or expression.transform != "x-model":
        return first
    setter = _parse_expression(expression, f"{source} = __placeholder")
    if setter.outcome != "incompatible":
        return first
    return AlpineCspClassification(
        "incompatible",
        "an x-model expression that cannot be assigned to",
        expression.start_index,
        expression.end_index,
    )


def _parse_for_expression(
    expression: BrowserExpression,
    source: str,
    source_offset: int,
) -> AlpineCspClassification:
    parsed = _parse_source(source)
    if parsed is None:
        runtime_global = _runtime_global_reference(source)
        if runtime_global is None:
            return AlpineCspClassification("compatible")
        start, end = runtime_global
        boundaries = _utf8_boundaries(expression.source)
        return AlpineCspClassification(
            "runtime-dependent",
            "a value that may resolve to a JavaScript global",
            expression.start_index + boundaries[source_offset + start],
            expression.start_index + boundaries[source_offset + end],
        )
    detail, start, end = parsed
    boundaries = _utf8_boundaries(expression.source)
    return AlpineCspClassification(
        "incompatible",
        detail,
        expression.start_index + boundaries[source_offset + start],
        expression.start_index + boundaries[source_offset + end],
    )


def _parse_expression(
    expression: BrowserExpression,
    source: str,
    *,
    prefix: int = 0,
) -> AlpineCspClassification:
    parsed = _parse_source(source)
    if parsed is None:
        runtime_global = _runtime_global_reference(source)
        if runtime_global is None:
            return AlpineCspClassification("compatible")
        start, end = runtime_global
        authored_start = max(0, min(len(expression.source), start - prefix))
        authored_end = max(authored_start, min(len(expression.source), end - prefix))
        boundaries = _utf8_boundaries(expression.source)
        return AlpineCspClassification(
            "runtime-dependent",
            "a value that may resolve to a JavaScript global",
            expression.start_index + boundaries[authored_start],
            expression.start_index + boundaries[authored_end],
        )
    detail, start, end = parsed
    authored_start = max(0, min(len(expression.source), start - prefix))
    authored_end = max(authored_start, min(len(expression.source), end - prefix))
    return _absolute_issue(expression, detail, authored_start, authored_end)


def _parse_source(source: str) -> tuple[str, int, int] | None:
    tokens: tuple[_Token, ...] = ()
    try:
        tokens = _tokenize(source)
        node = _Parser(tokens).parse()
        _validate_node(node)
    except _CspError as exc:
        friendly = _friendly_syntax_issue(tokens)
        if friendly is not None:
            return friendly
        return exc.detail, exc.start, exc.end
    return None


def _absolute_issue(
    expression: BrowserExpression,
    detail: str,
    start: int,
    end: int,
) -> AlpineCspClassification:
    boundaries = _utf8_boundaries(expression.source)
    safe_start = max(0, min(len(expression.source), start))
    safe_end = max(safe_start, min(len(expression.source), end))
    return AlpineCspClassification(
        "incompatible",
        detail,
        expression.start_index + boundaries[safe_start],
        expression.start_index + boundaries[safe_end],
    )


def _runtime_global_reference(source: str) -> tuple[int, int] | None:
    tokens = _tokenize(source)
    for index, token in enumerate(tokens):
        if token.kind != "IDENTIFIER" or token.value not in _GLOBAL_VALUE_NAMES:
            continue
        previous = tokens[index - 1] if index > 0 else None
        following = tokens[index + 1] if index + 1 < len(tokens) else None
        if previous is not None and previous.value == ".":
            continue
        if following is not None and following.value == ":":
            continue
        return token.start, token.end
    return None


def _for_items_range(source: str) -> tuple[int, int] | None:
    """Mirror Alpine's x-for separator regex and JavaScript ``trim()``."""
    for keyword_start in range(1, len(source)):
        keyword = next(
            (candidate for candidate in ("in", "of") if source.startswith(candidate, keyword_start)),
            None,
        )
        if keyword is None or not _js_whitespace(source[keyword_start - 1]):
            continue
        after_keyword = keyword_start + len(keyword)
        if after_keyword >= len(source) or not _js_whitespace(source[after_keyword]):
            continue
        items_start = after_keyword
        while items_start < len(source) and _js_whitespace(source[items_start]):
            items_start += 1
        items_end = len(source)
        while items_end > items_start and _js_whitespace(source[items_end - 1]):
            items_end -= 1
        return items_start, items_end
    return None


def _friendly_syntax_issue(tokens: tuple[_Token, ...]) -> tuple[str, int, int] | None:
    visible = tokens[:-1]
    for index, token in enumerate(visible):
        following = visible[index + 1] if index + 1 < len(visible) else None
        third = visible[index + 2] if index + 2 < len(visible) else None
        if following is not None and token.end == following.start:
            if token.value == "=" and following.value == ">":
                return "arrow functions", token.start, following.end
            if token.value == "?" and following.value == ".":
                return "optional chaining", token.start, following.end
            if token.value in {"+", "-", "*", "/", "%", "&", "|", "?"} and following.value == "=":
                return "compound assignment", token.start, following.end
            if token.value == "/" and following.value == "*":
                return "block comments", token.start, following.end
        if (
            following is not None
            and third is not None
            and token.value == following.value == third.value == "."
            and token.end == following.start
            and following.end == third.start
        ):
            return "spread syntax", token.start, third.end
        if token.value == "`":
            return "template literals", token.start, token.end
        if token.value in {"await", "class", "const", "function", "let", "typeof", "var"}:
            return f"the {token.value!r} syntax", token.start, token.end
        if token.value == ";" and following is not None:
            return "multiple statements", token.start, token.end
    return None


def _tokenize(source: str) -> tuple[_Token, ...]:
    tokens: list[_Token] = []
    position = 0
    while position < len(source):
        if _js_whitespace(source[position]):
            position += 1
            continue
        start = position
        char = source[position]
        if "0" <= char <= "9":
            position += 1
            decimal = False
            while position < len(source):
                current = source[position]
                if "0" <= current <= "9":
                    position += 1
                elif current == "." and not decimal:
                    decimal = True
                    position += 1
                else:
                    break
            tokens.append(_Token("NUMBER", source[start:position], start, position))
            continue
        if _ascii_alpha(char) or char in {"_", "$"}:
            position += 1
            while position < len(source) and (_ascii_alphanumeric(source[position]) or source[position] in {"_", "$"}):
                position += 1
            value = source[start:position]
            if value in {"true", "false"}:
                tokens.append(_Token("BOOLEAN", value == "true", start, position))
            elif value == "null":
                tokens.append(_Token("NULL", None, start, position))
            elif value == "undefined":
                tokens.append(_Token("UNDEFINED", None, start, position))
            elif value in _KEYWORDS:
                tokens.append(_Token("KEYWORD", value, start, position))
            else:
                tokens.append(_Token("IDENTIFIER", value, start, position))
            continue
        if char in {'"', "'"}:
            quote = char
            position += 1
            string_value: list[str] = []
            escaped = False
            while position < len(source):
                current = source[position]
                if escaped:
                    string_value.append(
                        {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", quote: quote}.get(current, current)
                    )
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == quote:
                    position += 1
                    tokens.append(_Token("STRING", "".join(string_value), start, position))
                    break
                else:
                    string_value.append(current)
                position += 1
            else:
                raise _CspError("an unterminated string", start, len(source))
            continue
        if char == "/" and position + 1 < len(source) and source[position + 1] == "/":
            position += 2
            while position < len(source) and source[position] != "\n":
                position += 1
            continue
        three = source[position : position + 3]
        two = source[position : position + 2]
        if three in {"===", "!=="}:
            position += 3
            tokens.append(_Token("OPERATOR", three, start, position))
            continue
        if two in {"==", "!=", "<=", ">=", "&&", "||", "++", "--"}:
            position += 2
            tokens.append(_Token("OPERATOR", two, start, position))
            continue
        position += 1
        kind = "PUNCTUATION" if char in "()[]{},.;:?" else "OPERATOR"
        tokens.append(_Token(kind, char, start, position))
    tokens.append(_Token("EOF", None, position, position))
    return tuple(tokens)


class _Parser:
    def __init__(self, tokens: tuple[_Token, ...]) -> None:
        self.tokens = tokens
        self.position = 0

    def parse(self) -> _Node:
        if self.at_end:
            raise _CspError("an empty expression", 0, 0)
        node = self._assignment()
        self._match("PUNCTUATION", ";")
        if not self.at_end:
            token = self.current
            raise _CspError(f"unsupported token {token.value!r}", token.start, token.end)
        return node

    def _assignment(self) -> _Node:
        left = self._ternary()
        if not self._match("OPERATOR", "="):
            return left
        operator = self.previous
        right = self._assignment()
        if left.kind not in {"identifier", "member"}:
            raise _CspError("an invalid assignment target", left.start, max(left.end, operator.end))
        return _Node("assignment", left.start, right.end, "=", (left, right))

    def _ternary(self) -> _Node:
        test = self._logical_or()
        if not self._match("PUNCTUATION", "?"):
            return test
        consequent = self._assignment()
        self._consume("PUNCTUATION", ":")
        alternate = self._assignment()
        return _Node("conditional", test.start, alternate.end, children=(test, consequent, alternate))

    def _logical_or(self) -> _Node:
        return self._binary(self._logical_and, {"||"})

    def _logical_and(self) -> _Node:
        return self._binary(self._equality, {"&&"})

    def _equality(self) -> _Node:
        return self._binary(self._relational, {"==", "!=", "===", "!=="})

    def _relational(self) -> _Node:
        return self._binary(self._additive, {"<", ">", "<=", ">="})

    def _additive(self) -> _Node:
        return self._binary(self._multiplicative, {"+", "-"})

    def _multiplicative(self) -> _Node:
        return self._binary(self._unary, {"*", "/", "%"})

    def _binary(self, lower: Callable[[], _Node], operators: set[str]) -> _Node:
        left = lower()
        while self.current.kind == "OPERATOR" and self.current.value in operators:
            operator = self._advance()
            right = lower()
            left = _Node("binary", left.start, right.end, operator.value, (left, right))
        return left

    def _unary(self) -> _Node:
        if self.current.kind == "OPERATOR" and self.current.value in {"++", "--", "!", "-", "+"}:
            operator = self._advance()
            argument = self._unary()
            kind = "update" if operator.value in {"++", "--"} else "unary"
            return _Node(kind, operator.start, argument.end, operator.value, (argument,))
        return self._postfix()

    def _postfix(self) -> _Node:
        node = self._member()
        if self.current.kind == "OPERATOR" and self.current.value in {"++", "--"}:
            operator = self._advance()
            return _Node("update", node.start, operator.end, operator.value, (node,))
        return node

    def _member(self) -> _Node:
        node = self._primary()
        while True:
            if self._match("PUNCTUATION", "."):
                property_ = self._consume("IDENTIFIER")
                property_node = _Node("identifier", property_.start, property_.end, property_.value)
                node = _Node("member", node.start, property_.end, children=(node, property_node))
            elif self._match("PUNCTUATION", "["):
                property_node = self._assignment()
                closing = self._consume("PUNCTUATION", "]")
                node = _Node("member", node.start, closing.end, children=(node, property_node), computed=True)
            elif self._match("PUNCTUATION", "("):
                arguments: list[_Node] = []
                if not self._check("PUNCTUATION", ")"):
                    while True:
                        arguments.append(self._assignment())
                        if not self._match("PUNCTUATION", ","):
                            break
                closing = self._consume("PUNCTUATION", ")")
                node = _Node("call", node.start, closing.end, children=(node, *arguments))
            else:
                return node

    def _primary(self) -> _Node:
        token = self.current
        if token.kind in {"NUMBER", "STRING", "BOOLEAN", "NULL", "UNDEFINED"}:
            self._advance()
            return _Node("literal", token.start, token.end, token.value)
        if token.kind == "IDENTIFIER":
            self._advance()
            return _Node("identifier", token.start, token.end, token.value)
        if self._match("PUNCTUATION", "("):
            node = self._assignment()
            self._consume("PUNCTUATION", ")")
            return node
        if self._match("PUNCTUATION", "["):
            opening = self.previous
            children: list[_Node] = []
            while not self._check("PUNCTUATION", "]") and not self.at_end:
                children.append(self._assignment())
                if not self._match("PUNCTUATION", ","):
                    break
                if self._check("PUNCTUATION", "]"):
                    break
            closing = self._consume("PUNCTUATION", "]")
            return _Node("array", opening.start, closing.end, children=tuple(children))
        if self._match("PUNCTUATION", "{"):
            opening = self.previous
            properties: list[_Node] = []
            while not self._check("PUNCTUATION", "}") and not self.at_end:
                computed = False
                if self.current.kind in {"STRING", "IDENTIFIER"}:
                    key_token = self._advance()
                    key = _Node(
                        "literal" if key_token.kind == "STRING" else "identifier",
                        key_token.start,
                        key_token.end,
                        key_token.value,
                    )
                elif self._match("PUNCTUATION", "["):
                    key = self._assignment()
                    self._consume("PUNCTUATION", "]")
                    computed = True
                else:
                    raise _CspError("an unsupported object property key", self.current.start, self.current.end)
                self._consume("PUNCTUATION", ":")
                value = self._assignment()
                properties.append(_Node("property", key.start, value.end, children=(key, value), computed=computed))
                if not self._match("PUNCTUATION", ","):
                    break
                if self._check("PUNCTUATION", "}"):
                    break
            closing = self._consume("PUNCTUATION", "}")
            return _Node("object", opening.start, closing.end, children=tuple(properties))
        raise _CspError(f"unsupported token {token.value!r}", token.start, token.end)

    def _match(self, kind: str, value: object = None) -> bool:
        if not self._check(kind, value):
            return False
        self._advance()
        return True

    def _check(self, kind: str, value: object = None) -> bool:
        if self.at_end:
            return False
        return self.current.kind == kind and (value is None or self.current.value == value)

    def _consume(self, kind: str, value: object = None) -> _Token:
        if self._check(kind, value):
            return self._advance()
        token = self.current
        expected = value if value is not None else kind.lower()
        raise _CspError(f"expected {expected!r}", token.start, token.end)

    def _advance(self) -> _Token:
        if not self.at_end:
            self.position += 1
        return self.previous

    @property
    def current(self) -> _Token:
        return self.tokens[self.position]

    @property
    def previous(self) -> _Token:
        return self.tokens[self.position - 1]

    @property
    def at_end(self) -> bool:
        return self.current.kind == "EOF"


def _validate_node(node: _Node) -> None:
    if node.kind == "member":
        property_node = node.children[1]
        property_name = property_node.value if not node.computed or property_node.kind == "literal" else None
        if type(property_name) is str and property_name in _DANGEROUS_PROPERTIES:
            raise _CspError(f"access to the {property_name!r} property", property_node.start, property_node.end)
    if node.kind in {"assignment", "update"}:
        target = node.children[0]
        if target.kind not in {"identifier", "member"}:
            raise _CspError("an invalid update target", target.start, target.end)
        if target.kind == "member" and _root_identifier(target) in _DOM_ROOTS:
            raise _CspError("a property write through an Alpine DOM magic", target.start, target.end)
    for child in node.children:
        _validate_node(child)


def _root_identifier(node: _Node) -> str | None:
    current = node
    while current.kind in {"member", "group"} and current.children:
        current = current.children[0]
    return current.value if current.kind == "identifier" and type(current.value) is str else None


def _ascii_alpha(char: str) -> bool:
    return "a" <= char <= "z" or "A" <= char <= "Z"


def _ascii_alphanumeric(char: str) -> bool:
    return _ascii_alpha(char) or "0" <= char <= "9"


def _js_whitespace(char: str) -> bool:
    r"""Return whether ECMAScript ``\s`` matches one source character."""
    return char in {
        "\u0009",
        "\u000a",
        "\u000b",
        "\u000c",
        "\u000d",
        "\u0020",
        "\u00a0",
        "\u1680",
        "\u2000",
        "\u2001",
        "\u2002",
        "\u2003",
        "\u2004",
        "\u2005",
        "\u2006",
        "\u2007",
        "\u2008",
        "\u2009",
        "\u200a",
        "\u2028",
        "\u2029",
        "\u202f",
        "\u205f",
        "\u3000",
        "\ufeff",
    }


def _utf8_boundaries(source: str) -> tuple[int, ...]:
    boundaries = [0]
    for char in source:
        boundaries.append(boundaries[-1] + len(char.encode("utf-8")))
    return tuple(boundaries)


__all__ = [
    "ALPINE_CSP_COMPATIBILITY_VERSION",
    "AlpineCspClassification",
    "classify_alpine_csp",
]
