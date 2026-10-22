"""
Explain a render failure caused by a server expression that reads a Vue ``v-for`` variable.

Citry evaluates ``{{ }}``, ``c-*`` attributes, and component inputs on the
server while it renders the page. A variable that a Vue ``v-for`` declares
exists only later, in the browser, so a server expression that reads one
fails with a ``KeyError`` that only names the variable. When a render error
reaches the template that failed, this module checks whether a
``KeyError`` is that mistake and, if so, builds the error raised in its
place, which says why and how to fix it.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from citry._browser_expressions import enclosing_vue_loops
from citry._source_lines import line_break_count
from citry.nodes import ComponentNode, ExprNode
from citry_core.template_parser import parse_template

# The name right after a `<`, such as `c-if` in `<c-if cond="...">`.
_TAG_NAME = re.compile(r"<([A-Za-z][\w:.-]*)")
# How safe_eval reports a failed variable lookup, such as
# "Error in variable: KeyError: 'member'". Only that failure is about a name.
_FAILED_LOOKUP = re.compile(r"Error in variable: KeyError: '([^'\n]+)'")
# A name or a dotted path, such as `member.name`, which reads the same in
# Python and JavaScript, so a suggestion can quote it for either side.
_PLAIN_PATH = re.compile(r"[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*")
# Citry's own tags that are not component calls, so they may sit in a v-for.
_SERVER_TAGS = frozenset({"c-if", "c-elif", "c-else", "c-for", "c-empty", "c-raw"})
# The left side of a v-for, up to its `in` or `of`.
_LOOP_TARGETS = re.compile(r"\s*(.*?)\s+(?:in|of)\s")

if TYPE_CHECKING:
    from collections.abc import Container, Iterable

    from citry._browser_expressions import EnclosingVueLoop


class VueLoopVariableError(KeyError):
    """
    A server expression reads a variable that only a Vue ``v-for`` declares.

    It is a ``KeyError``, as the failed variable lookup was, so code that
    already catches the lookup failure keeps catching it.
    """

    def __str__(self) -> str:
        # KeyError prints its message through repr(), which would show this
        # several-line message as one quoted line with escaped line breaks.
        return str(self.args[0]) if self.args else ""


def vue_loop_variable_error(
    error: BaseException,
    node: object,
    variables: Container[str],
    origin: str | None,
) -> tuple[VueLoopVariableError, tuple[int, int]] | None:
    """
    Return the error to raise in place of ``error`` when ``node`` failed because it reads a Vue ``v-for`` variable.

    The error comes with the byte span of the template to show under it.
    ``variables`` are the names the server had while rendering ``node``, and
    ``origin`` names the template for the message. Only a plain ``KeyError``
    for a name that the node reads, that the server lacks, and that an
    enclosing ``v-for`` declares is replaced. Any other error gets ``None``
    and stays as it is.
    """
    # A KeyError subclass is someone's own error, not a failed variable lookup.
    if type(error) is not KeyError or len(error.args) != 1:
        return None
    lookup = _FAILED_LOOKUP.search(str(error.args[0]))
    source = getattr(node, "source", None)
    # Only the name whose lookup failed can be blamed: another missing name
    # in the same expression, or a failed lookup inside a value the server
    # has, is a different mistake.
    if lookup is None or not isinstance(source, str):
        return None
    name = lookup.group(1)
    if name in variables or name not in (getattr(node, "used_vars", None) or ()):
        return None
    site = _reading_site(node, name)
    if site is None:
        return None
    position, attr = site
    try:
        template = parse_template(source)
    except (SyntaxError, ValueError):
        # A template only an extension or custom tag rules can parse gives
        # nothing to search, so the original error stands.
        return None
    # The innermost loop that declares the name is the one in scope.
    loop = next(
        (loop for loop in reversed(enclosing_vue_loops(template, *position)) if loop.binding.name == name),
        None,
    )
    if loop is None:
        return None
    message = _message(node, attr, source, position, name, loop, origin, variables)
    return VueLoopVariableError(message), position


def _reading_site(node: object, name: str) -> tuple[tuple[int, int], Any] | None:
    """
    Return the byte span of ``node`` to blame for reading ``name``, and the attribute that reads it, if any.

    Most nodes carry their own span. A ``<c-if>`` or ``<c-for>`` node does
    not, so the span of the branch whose ``cond`` or ``each`` reads the
    name stands in for it.
    """
    position = getattr(node, "position", None)
    if isinstance(position, tuple) and len(position) == 2:
        return position, _attribute_reading(getattr(node, "attrs", ()), name)
    for branch in getattr(node, "branches", ()):
        branch_position, attrs = branch[0], branch[1]
        attr = _attribute_reading(attrs, name)
        if attr is not None:
            return branch_position, attr
    return None


def _message(
    node: object,
    attr: Any,
    source: str,
    position: tuple[int, int],
    name: str,
    loop: EnclosingVueLoop,
    origin: str | None,
    variables: Container[str],
) -> str:
    """Write what went wrong, where, and the server-side or browser-side way to fix it."""
    line = _line(source, position[0])
    where = f"in template {origin}, line {line}" if origin else f"on line {line} of its template"
    declared = f"the Vue v-for on <{loop.tag}> (line {_line(source, loop.tag_start_index)}) declares it"
    repeat = _server_loop(name, loop, variables)
    # The Vue compiler rejects a component call inside a v-for, so when one
    # sits between the loop and the failing expression, only the server
    # loop fixes it and no browser-side alternative is offered.
    browser_fix_works = not any(_is_component_tag(tag) for tag in loop.inner_tags)
    attr_key = getattr(attr, "key", None)
    attr_expr = getattr(attr, "expr", None)
    plain_expr = isinstance(attr_expr, str) and _PLAIN_PATH.fullmatch(attr_expr) is not None
    if isinstance(node, ComponentNode):
        tag = node._authored_tag()
        reads = f"<{tag}> {where} reads '{name}'" + (f" in {_quote(source, attr)}" if attr is not None else "")
        happens = (
            "Citry evaluates component inputs on the server while it renders the page, so an input cannot"
            " read a browser variable."
        )
        fix = f"Repeat <{tag}> on the server instead, with {repeat} in place of the v-for."
        browser = None
    elif isinstance(node, ExprNode):
        expression = node.expr.strip()
        reads = f"{{{{ {expression} }}}} {where} reads '{name}'"
        happens = "Citry evaluates {{ }} on the server while it renders the page."
        browser = (
            f'Let Vue show the value in the browser with <span v-text="{expression}"></span>'
            f" in place of {{{{ {expression} }}}}"
            if _PLAIN_PATH.fullmatch(expression)
            else "Let Vue show the value in the browser with a v-text binding"
        )
        fix = f"repeat on the server with {repeat}."
    elif isinstance(attr_key, str) and attr_key.startswith("c-"):
        # A `c-<name>` attribute has a Vue twin, `:<name>`, that the browser
        # evaluates; `c-bind` has `v-bind`.
        vue_key = "v-bind" if attr_key == "c-bind" else f":{attr_key.removeprefix('c-')}"
        reads = f"{_quote(source, attr)} {where} reads '{name}'"
        happens = f"Citry evaluates {attr_key} on the server while it renders the page."
        browser = (
            f'Let Vue set it in the browser with {vue_key}="{attr_expr}"'
            if plain_expr
            else f"Let Vue set it in the browser with a {vue_key} binding"
        )
        fix = f"repeat on the server with {repeat}."
    elif hasattr(node, "branches") and attr is not None and (branch_tag := _tag_at(source, position[0])) is not None:
        # A `<c-if cond>` or `<c-for each>`: the branch's span starts at its tag.
        reads = f"<{branch_tag} {_quote(source, attr)}> {where} reads '{name}'"
        happens = f"Citry evaluates <{branch_tag}> on the server while it renders the page."
        browser = (
            "Use a nested v-for in the browser instead"
            if branch_tag.lower() == "c-for"
            else "Use v-if in the browser instead"
        )
        fix = f"repeat on the server with {repeat}."
    else:
        reads = f"{_quote(source, attr) if attr is not None else 'A server expression'} {where} reads '{name}'"
        happens = "Citry evaluates it on the server while it renders the page."
        browser = None
        fix = f"Repeat this part on the server with {repeat}."
    if browser is not None:
        fix = f"{browser}, or {fix}" if browser_fix_works else f"Repeat this part on the server with {repeat}."
    if not repeat.startswith("<"):
        # The v-for's list lives in the browser too, so the server needs it.
        fix += " The <c-for> needs that list as a template variable, for example from template_data()."
    return f"{reads}, but '{name}' exists only in the browser: {declared}. {happens} {fix}"


def _is_component_tag(tag: str) -> bool:
    """Return whether a tag calls a component, rather than Citry's own server tags such as ``<c-if>``."""
    lowered = tag.lower()
    return lowered.startswith("c-") and lowered not in _SERVER_TAGS


def _server_loop(name: str, loop: EnclosingVueLoop, variables: Container[str]) -> str:
    """Return the `<c-for>` that repeats on the server what the v-for repeats in the browser."""
    targets = _LOOP_TARGETS.match(loop.expression)
    # Only a loop whose item is `name`, with at most an index beside it, over
    # a list the server already has, reads the same as a `<c-for>`. A third
    # target means Vue loops over an object's values, which Python does not.
    item = re.fullmatch(rf"\(?\s*{re.escape(name)}\s*(?:,\s*\w+\s*)?\)?", targets.group(1)) if targets else None
    iterable = loop.binding.source
    if item is not None and _PLAIN_PATH.fullmatch(iterable) and iterable.split(".")[0] in variables:
        return f'<c-for each="{name} in {iterable}">'
    return "a <c-for> over the same list"


def _attribute_reading(attrs: Iterable[object], name: str) -> Any:
    """Return the first of ``attrs`` whose expression reads ``name``, if any."""
    return next((attr for attr in attrs if name in getattr(attr, "used_vars", ())), None)


def _tag_at(source: str, byte_offset: int) -> str | None:
    """Return the name of the tag that starts at ``byte_offset``, as the template spells it, if one does."""
    match = _TAG_NAME.match(source.encode()[byte_offset:].decode(errors="replace"))
    return match.group(1) if match is not None else None


def _quote(source: str, attr: Any) -> str:
    """Quote an attribute as the template spells it, from its byte position."""
    start, end = attr.position
    return source.encode()[start:end].decode(errors="replace")


def _line(source: str, byte_offset: int) -> int:
    """Return the line of a byte offset, counted from 1 as an editor shows it."""
    return line_break_count(source.encode()[:byte_offset].decode(errors="replace")) + 1


__all__ = ["VueLoopVariableError", "vue_loop_variable_error"]
