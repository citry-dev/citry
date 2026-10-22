"""
Read which class names and custom properties a stylesheet declares.

The CSS lint rules compare a template's classes and a stylesheet's
``var(--name)`` reads with what every registered component's CSS declares
(``citry._css_lint`` lists which CSS that is). This module is the one
place that reads selectors and custom property declarations. It is a small
scanner, not a full CSS parser: it follows the parts of CSS syntax that
decide whether a piece of text is a selector (comments, strings, escapes,
``url(...)``, nested blocks, and at-rules) and ignores everything else.

A class counts as declared when a selector names it anywhere: ``.a``,
``.a .b``, ``.a:hover``, ``.a.b``, ``:is(.a)``, ``@scope (.a)``, and rules
nested inside ``@media`` or inside another rule. An attribute selector on
``class`` counts too, such as ``[class~="a"]``; one that matches part of a
value, such as ``[class^="btn-"]``, declares every class that matches it.
Text inside a comment, a string, or a declaration's value, such as the
``.5`` in ``margin: .5em``, is never a class.

The scanner reads malformed CSS close to how a browser does: an unclosed
comment runs to the end of the source, an unclosed string ends at the end
of its line, and an unclosed block ends with the source. Where it differs,
such as after a stray ``}``, it counts more declarations, never fewer, so
the rules that use it report less.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

# The characters, and the `url(` call, that can change how the rest of a
# statement or a value reads. The scanner jumps from one to the next,
# because component stylesheets, such as a UI library's minified CSS, run to
# hundreds of kilobytes.
_STATEMENT_SPECIAL = re.compile(r"""["'/\\()\[\]{};]|(?<![\w-])url\(""", re.IGNORECASE)

# At-rules whose block holds style rules, or declarations and rules mixed when
# nested inside a style rule. Any other at-rule's block, such as `@font-face`
# or `@keyframes`, holds no selector that can name a class.
_GROUPING_AT_RULES = frozenset(
    {
        "media",
        "supports",
        "layer",
        "container",
        "scope",
        "document",
        "-moz-document",
        "starting-style",
        "nest",
        "when",
        "else",
    }
)

# How an attribute selector on `class` compares its value. `~=` is the only
# one that names one whole class; the others match the whole attribute or a
# part of it.
_ClassOperator = Literal["~=", "=", "^=", "$=", "*=", "|="]
_CLASS_OPERATORS = frozenset({"~=", "=", "^=", "$=", "*=", "|="})

# The whitespace HTML splits a class attribute on.
_HTML_WHITESPACE = " \t\n\f\r"


@dataclass(frozen=True, slots=True)
class ClassPattern:
    """
    One ``[class...]`` attribute selector that Citry compares with each class, rather than one class name it records.

    Attributes:
        operator: The comparison: ``^=``, ``$=``, ``*=``, or ``|=``, or
            ``~=`` for one whole class compared without case. A ``~=`` or
            ``=`` selector without the ``i`` flag names whole classes, so it
            is recorded as a class instead.
        value: The value the selector compares with, escapes decoded.
        ignore_case: Whether the selector has the ``i`` flag.

    """

    operator: _ClassOperator
    value: str
    ignore_case: bool

    def matches(self, name: str) -> bool:
        """Return whether a class attribute holding only ``name`` matches this selector."""
        value = self.value
        if self.ignore_case:
            name = name.lower()
            value = value.lower()
        if self.operator == "^=":
            return bool(value) and name.startswith(value)
        if self.operator == "$=":
            return bool(value) and name.endswith(value)
        if self.operator == "*=":
            return bool(value) and value in name
        if self.operator == "~=":
            return name == value
        # `|=` matches the value itself or the value followed by a hyphen.
        return name == value or name.startswith(f"{value}-")


@dataclass(frozen=True, slots=True)
class CssDeclarations:
    """
    What one or more stylesheets declare for templates and other stylesheets to use.

    Attributes:
        classes: Every class name a selector names, escapes decoded.
        class_patterns: The ``[class...]`` selectors that match part of a
            class attribute.
        custom_properties: Every custom property the CSS sets, without the
            leading ``--``: from a ``--name: value`` declaration or an
            ``@property --name`` rule.

    """

    classes: frozenset[str] = frozenset()
    class_patterns: tuple[ClassPattern, ...] = ()
    custom_properties: frozenset[str] = frozenset()

    def declares_class(self, name: str) -> bool:
        """Return whether a selector in these stylesheets can match an element with the class ``name``."""
        return name in self.classes or any(pattern.matches(name) for pattern in self.class_patterns)

    def merged(self, other: CssDeclarations) -> CssDeclarations:
        """Return the declarations of both, as if the stylesheets were one."""
        return CssDeclarations(
            classes=self.classes | other.classes,
            class_patterns=tuple(dict.fromkeys((*self.class_patterns, *other.class_patterns))),
            custom_properties=self.custom_properties | other.custom_properties,
        )


def scan_css(source: str) -> CssDeclarations:
    r"""
    Return the class names and custom properties one stylesheet declares.

    Args:
        source: The stylesheet's text, such as a component's ``css``.

    Returns:
        The declarations, with every CSS escape in a name decoded, so
        ``.md\:flex`` declares the class ``md:flex``.

    """
    scanner = _Scanner(source)
    scanner.scan()
    return CssDeclarations(
        classes=frozenset(scanner.classes),
        class_patterns=tuple(dict.fromkeys(scanner.class_patterns)),
        custom_properties=frozenset(scanner.custom_properties),
    )


def split_class_attribute(value: str) -> list[tuple[str, int, int]]:
    """
    Split a class attribute's text into its class names, the way HTML does.

    Args:
        value: The attribute's text as written, before character references
            are decoded.

    Returns:
        Each name with its start and end index in ``value``.

    """
    names: list[tuple[str, int, int]] = []
    index = 0
    while index < len(value):
        if value[index] in _HTML_WHITESPACE:
            index += 1
            continue
        start = index
        while index < len(value) and value[index] not in _HTML_WHITESPACE:
            index += 1
        names.append((value[start:index], start, index))
    return names


@dataclass(slots=True)
class _Scanner:
    """Walk one stylesheet's statements and record what its selectors and declarations name."""

    source: str
    index: int = 0
    classes: set[str] = field(default_factory=set)
    class_patterns: list[ClassPattern] = field(default_factory=list)
    custom_properties: set[str] = field(default_factory=set)

    def scan(self) -> None:
        """
        Read every statement, entering and leaving blocks with a stack.

        A stack rather than recursion keeps deeply nested or unclosed blocks,
        such as a thousand unclosed `@media` rules, from exhausting Python's
        call stack and stopping the whole check.
        """
        # Whether a statement that opens a block at the current level is a
        # style rule, whose prelude is a selector. The top level holds rules.
        selectors = True
        # The value of `selectors` in each enclosing block, restored when the
        # block closes.
        enclosing: list[bool] = []
        while True:
            self._skip_trivia()
            if self.index >= len(self.source):
                return
            char = self.source[self.index]
            if char == "}":
                self.index += 1
                # A stray `}` at the top level closes nothing. A browser
                # drops the rule after it; counting that rule only makes
                # the rules that use this scanner quieter.
                if enclosing:
                    selectors = enclosing.pop()
                continue
            if char == ";":
                self.index += 1
                continue
            # A custom property's value may hold `{}` blocks, so it is read on
            # its own rather than as a possible nested rule.
            # At the top level, where no declaration belongs, `--x: ...` is
            # an invalid rule that a browser drops alone.
            if enclosing and self.source.startswith("--", self.index) and self._custom_property_declaration():
                continue
            start = self.index
            end, terminator = self._statement_end()
            prelude = self.source[start:end]
            if terminator != "{":
                # A declaration or a block-less at-rule such as `@import` names
                # no selector.
                self.index = end + (1 if terminator == ";" else 0)
                continue
            self.index = end + 1
            enclosing.append(selectors)
            if prelude.lstrip().startswith("@"):
                selectors = self._at_rule(prelude.lstrip())
            elif selectors:
                # A style rule's block holds declarations and, with CSS
                # nesting, more style rules, so `selectors` stays as it is.
                self._selector(prelude)

    def _at_rule(self, prelude: str) -> bool:
        """Record what an at-rule's prelude declares; return whether its block holds style rules."""
        name_end = 1
        while name_end < len(prelude) and _is_name_char(prelude[name_end]):
            name_end += 1
        name = prelude[1:name_end].lower()
        rest = prelude[name_end:]
        if name == "property":
            # `@property --name { ... }` registers a custom property, which
            # counts as setting it: the rule can give an initial value.
            text = rest.strip()
            if text.startswith("--"):
                property_name, _ = _read_name(text, 2)
                if property_name:
                    self.custom_properties.add(property_name)
        if name == "scope":
            # `@scope (.card) to (.content)` matches elements by class.
            self._selector(rest)
        return name in _GROUPING_AT_RULES

    def _custom_property_declaration(self) -> bool:
        """Read a ``--name: value`` declaration at the cursor, or return False when it is not one."""
        name, after_name = _read_name(self.source, self.index + 2)
        cursor = _skip_trivia(self.source, after_name)
        if not name or cursor >= len(self.source) or self.source[cursor] != ":":
            return False
        self.custom_properties.add(name)
        self.index = cursor + 1
        depth = 0
        while (match := _STATEMENT_SPECIAL.search(self.source, self.index)) is not None:
            self.index = match.start()
            char = self.source[self.index]
            if char in "\"'":
                self.index = _skip_string(self.source, self.index)
                continue
            if self.source.startswith("/*", self.index):
                self.index = _skip_comment(self.source, self.index)
                continue
            if char == "\\":
                self.index += 2
                continue
            if _starts_unquoted_url(self.source, self.index):
                self.index = _skip_unquoted_url(self.source, self.index)
                continue
            if char in "([{":
                depth += 1
            elif char in ")]":
                depth = max(0, depth - 1)
            elif char == "}":
                if depth == 0:
                    # The enclosing block ends here; leave the brace for it.
                    return True
                depth -= 1
            elif char == ";" and depth == 0:
                self.index += 1
                return True
            self.index += 1
        self.index = len(self.source)
        return True

    def _statement_end(self) -> tuple[int, str]:
        """
        Find where the statement at the cursor ends: at a ``{``, ``;``, or ``}`` outside any brackets.

        Returns the index of that character and the character, or the end of
        the source and an empty string.
        """
        index = self.index
        depth = 0
        source = self.source
        while (match := _STATEMENT_SPECIAL.search(source, index)) is not None:
            index = match.start()
            char = source[index]
            if char in "\"'":
                index = _skip_string(source, index)
                continue
            if source.startswith("/*", index):
                index = _skip_comment(source, index)
                continue
            if char == "\\":
                index += 2
                continue
            if _starts_unquoted_url(source, index):
                index = _skip_unquoted_url(source, index)
                continue
            if char in "([":
                depth += 1
            elif char in ")]":
                depth = max(0, depth - 1)
            elif depth == 0 and char in "{;}":
                return index, char
            index += 1
        return len(source), ""

    def _selector(self, prelude: str) -> None:
        """Record every class a selector, or an ``@scope`` prelude, names."""
        index = 0
        while index < len(prelude):
            char = prelude[index]
            if char in "\"'":
                index = _skip_string(prelude, index)
                continue
            if prelude.startswith("/*", index):
                index = _skip_comment(prelude, index)
                continue
            if char == "\\":
                # An escaped character outside a class name, such as in a
                # type selector, is never a class.
                index += 2
                continue
            if char == "[":
                index = self._attribute_selector(prelude, index)
                continue
            if prelude.startswith("::", index):
                name, after_name = _read_name(prelude, index + 2)
                if name.lower().startswith("view-transition") and prelude[after_name : after_name + 1] == "(":
                    # `::view-transition-group(.card)` names a view
                    # transition class, which is not a class on an element.
                    index = _skip_parenthesized(prelude, after_name)
                    continue
                index = after_name
                continue
            if char == "." and _starts_identifier(prelude, index + 1):
                name, index = _read_name(prelude, index + 1)
                self.classes.add(name)
                continue
            index += 1

    def _attribute_selector(self, prelude: str, start: int) -> int:
        """Read ``[attr op value flag]`` and record it when it tests ``class``; return the index after ``]``."""
        index = _skip_trivia(prelude, start + 1)
        attribute, index = _read_name(prelude, index)
        # A namespace prefix, as in `[*|class]` or `[svg|class]`, still tests
        # the class attribute.
        if index < len(prelude) and prelude[index] == "|" and prelude[index + 1 : index + 2] != "=":
            attribute, index = _read_name(prelude, index + 1)
        elif prelude[index : index + 1] == "*" and prelude[index + 1 : index + 2] == "|":
            attribute, index = _read_name(prelude, index + 2)
        index = _skip_trivia(prelude, index)
        operator = ""
        if prelude[index : index + 2] in _CLASS_OPERATORS:
            operator = prelude[index : index + 2]
            index += 2
        elif prelude[index : index + 1] == "=":
            operator = "="
            index += 1
        value: str | None = None
        if operator:
            index = _skip_trivia(prelude, index)
            if index < len(prelude) and prelude[index] in "\"'":
                end = _skip_string(prelude, index)
                value = _decode_escapes(prelude[index + 1 : max(index + 1, end - 1)])
                index = end
            else:
                value, index = _read_name(prelude, index)
        index = _skip_trivia(prelude, index)
        ignore_case = False
        if index < len(prelude) and prelude[index] in "iIsS":
            ignore_case = prelude[index] in "iI"
            index += 1
        # Skip to the closing bracket, past anything this reader did not expect.
        while index < len(prelude) and prelude[index] != "]":
            if prelude[index] in "\"'":
                index = _skip_string(prelude, index)
                continue
            index += 1
        if attribute.lower() == "class" and value is not None:
            self._record_class_selector(operator, value, ignore_case=ignore_case)
        return index + 1

    def _record_class_selector(self, operator: str, value: str, *, ignore_case: bool) -> None:
        if operator in {"~=", "="}:
            # `[class="a b"]` matches an element whose class attribute is
            # exactly `a b`, so both names are styled. `[class~="a b"]`
            # compares one class with a value holding a space, which no class
            # equals, so it styles nothing.
            if operator == "~=" and any(char in _HTML_WHITESPACE for char in value):
                return
            for name, _start, _end in split_class_attribute(value):
                if ignore_case:
                    self.class_patterns.append(ClassPattern("~=", name, ignore_case=True))
                else:
                    self.classes.add(name)
            return
        if operator in _CLASS_OPERATORS:
            self.class_patterns.append(ClassPattern(operator, value, ignore_case=ignore_case))  # type: ignore[arg-type]

    def _skip_trivia(self) -> None:
        self.index = _skip_trivia(self.source, self.index)


def _skip_trivia(source: str, index: int) -> int:
    """Skip whitespace and comments."""
    while index < len(source):
        if source[index] in " \t\r\n\f":
            index += 1
        elif source.startswith("/*", index):
            index = _skip_comment(source, index)
        else:
            return index
    return index


def _skip_comment(source: str, start: int) -> int:
    """Return the index after the comment at ``start``; an unclosed comment runs to the end."""
    closing = source.find("*/", start + 2)
    return len(source) if closing < 0 else closing + 2


def _skip_string(source: str, start: int) -> int:
    """Return the index after the string at ``start``; an unclosed string ends at its line's end."""
    quote = source[start]
    index = start + 1
    while index < len(source):
        char = source[index]
        if char == "\\":
            index += 2
            continue
        if char == quote:
            return index + 1
        if char in "\n\r\f":
            return index
        index += 1
    return len(source)


def _starts_unquoted_url(source: str, index: int) -> bool:
    """Return whether ``url(`` with an unquoted argument starts at ``index``."""
    if source[index : index + 4].lower() != "url(":
        return False
    if index > 0 and _is_name_char(source[index - 1]):
        return False
    after = _skip_whitespace(source, index + 4)
    return after >= len(source) or source[after] not in "\"'"


def _skip_unquoted_url(source: str, start: int) -> int:
    """Return the index after ``url(...)``; its text may hold ``;`` or ``{`` that end nothing."""
    index = start + 4
    while index < len(source):
        if source[index] == "\\":
            index += 2
            continue
        if source[index] == ")":
            return index + 1
        index += 1
    return len(source)


def _skip_whitespace(source: str, index: int) -> int:
    while index < len(source) and source[index] in " \t\r\n\f":
        index += 1
    return index


def _is_name_char(char: str) -> bool:
    """Return whether ``char`` may continue a CSS identifier without an escape."""
    return (char.isascii() and (char.isalnum() or char in "-_")) or ord(char) >= 0x80


def _is_name_start(char: str) -> bool:
    return (char.isascii() and (char.isalpha() or char == "_")) or ord(char) >= 0x80


def _is_valid_escape(source: str, index: int) -> bool:
    """Return whether a backslash at ``index`` starts an escape; one before a newline does not."""
    return source[index : index + 1] == "\\" and source[index + 1 : index + 2] not in {"\n", "\r", "\f"}


def _starts_identifier(source: str, index: int) -> bool:
    """Return whether a CSS identifier starts at ``index``, so ``.5`` in a number is not a class."""
    if index >= len(source):
        return False
    char = source[index]
    if char == "-":
        following = source[index + 1 : index + 2]
        return bool(following) and (
            following == "-" or _is_name_start(following) or _is_valid_escape(source, index + 1)
        )
    return _is_name_start(char) or _is_valid_escape(source, index)


def _read_name(source: str, index: int) -> tuple[str, int]:
    """Read a CSS name at ``index`` with its escapes decoded; return it and the index after it."""
    parts: list[str] = []
    while index < len(source):
        char = source[index]
        if _is_name_char(char):
            parts.append(char)
            index += 1
            continue
        if _is_valid_escape(source, index):
            decoded, index = _read_escape(source, index)
            parts.append(decoded)
            continue
        break
    return "".join(parts), index


def _read_escape(source: str, index: int) -> tuple[str, int]:
    """Decode the escape whose backslash is at ``index``; return the character and the index after it."""
    index += 1
    if index >= len(source):
        return "�", index
    digits = 0
    while digits < 6 and index + digits < len(source) and source[index + digits] in "0123456789abcdefABCDEF":
        digits += 1
    if digits == 0:
        return source[index], index + 1
    codepoint = int(source[index : index + digits], 16)
    index += digits
    # One whitespace character after a hex escape belongs to the escape.
    if source[index : index + 2] == "\r\n":
        index += 2
    elif index < len(source) and source[index] in " \t\n\r\f":
        index += 1
    if codepoint == 0 or 0xD800 <= codepoint <= 0xDFFF or codepoint > 0x10FFFF:
        return "�", index
    return chr(codepoint), index


def _decode_escapes(text: str) -> str:
    """Decode every escape in a string's contents; an escaped newline is removed, as CSS does."""
    if "\\" not in text:
        return text
    parts: list[str] = []
    index = 0
    while index < len(text):
        if text[index] != "\\":
            parts.append(text[index])
            index += 1
            continue
        if text[index + 1 : index + 2] in {"\n", "\f"}:
            index += 2
            continue
        if text[index + 1 : index + 3] == "\r\n":
            index += 3
            continue
        decoded, index = _read_escape(text, index)
        parts.append(decoded)
    return "".join(parts)


def _skip_parenthesized(source: str, start: int) -> int:
    """Return the index after the parenthesized group that opens at ``start``, counting nested groups."""
    depth = 0
    index = start
    while index < len(source):
        char = source[index]
        if char in "\"'":
            index = _skip_string(source, index)
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return len(source)
