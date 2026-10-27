"""
Run Vue's compiler over a template, as a render would, and report what it rejects.

When a component that uses Vue renders, Citry compiles its template to a Vue
render function, and the render fails if the compiler reports anything: a
`<div>` the browser moves out of a `<table>`, a `<button>` inside a
`<button>`, a `v-else` with no `v-if` right before it (an orphan `v-else`),
a broken expression. This rule writes the Vue template the render would
compile (`citry._vue.static_template`), runs the same compiler on it, and
reports each error at the authored text it points at.

It needs only the template, so `citry check --static` and an editor that has
not loaded the application run it too; only a component inside a Vue `v-for`
needs the application, to tell an ordinary call from a component that renders
in place.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from citry._browser_expressions import browser_expressions
from citry._diagnostic_catalog import TEMPLATE_INVALID_NESTING, VUE_COMPILE_ERROR, VUE_INVALID_EXPRESSION
from citry._diagnostics import render_diagnostic
from citry._markup_lint import (
    MarkupLintConsumer,
    MarkupLintFinding,
    _active_severities,
    lint_invalid_vue_expressions,
    lint_markup,
)
from citry._vue.static_template import (
    RendersInPlace,
    StaticVueTemplate,
    UnsupportedStaticTemplate,
    static_vue_template,
)
from citry.component_render import _exec_template_code
from citry_core import _rust
from citry_core.template_parser.compile import _compile_prepared_template

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from citry._vue.static_template import ElseDirective
    from citry_core.template_parser import Template


# Compiler codes for the browser rebuilding the element tree differently from
# the template: an element moved out of a table, a nested button or form, an
# end tag with nothing left to close.
_TREE_CODES = frozenset({"ExtendPoint", "InvalidEndTag", "MissingEndTag"})
# The compiler also checks the records Citry passes about component calls.
# One of those checks finds the author's mistake: a component inside a Vue
# `v-for`, which only `<c-for>` can repeat.
_COMPONENT_IN_V_FOR = "CITRY_COMPONENT_IN_V_FOR"
# The compiler's code for an orphan `v-else`, which it reports without a position.
_ORPHAN_ELSE = "VElseNoAdjacentIf"
# Same-length replacements that take a `v-else` or `v-else-if` out of its
# chain without moving any other byte of the template. `v-else-if` becomes a
# `v-if` with spaces before its `=`, so a `v-else` after it still has a chain
# to join and no valid `v-else` turns into an orphan.
_ELSE_STAND_INS = {"v-else": "data-z", "v-else-if": "v-if     "}
# Plain wordings for the compiler's messages about the element tree, keyed by
# how each message starts. `{tag}` is the tag the finding points at.
_TREE_MESSAGES = (
    (
        "Foster parenting moved this element",
        "a <{tag}> inside a table must sit in a <td> or <th>, so the browser moves it out of the table."
        " Put rows in <tr> and cells in <td> or <th>.",
    ),
    (
        "Nested button start tag closed the previous button",
        "this <button> holds another <button>, so the browser ends it where the inner one starts."
        " Close this <button> before the next one.",
    ),
    (
        "Nested anchor start tag closed the previous anchor",
        "this <a> holds another <a>, so the browser ends the link where the inner one starts."
        " Close this <a> before the next one.",
    ),
    (
        "HTML tree construction ignored this start tag because an equivalent element is already open",
        "this <{tag}> is inside another <{tag}>, so the browser ignores this start tag."
        " Close the outer <{tag}> first.",
    ),
    (
        "HTML tree construction ignored this end tag",
        "the browser already closed this element, so this end tag closes nothing.",
    ),
)
_TAG_NAME = re.compile(rb"</?([A-Za-z][^\s/>]*)")


@dataclass(frozen=True, slots=True)
class _CompilerError:
    code: str
    message: str
    start: int | None
    end: int | None


def lint_vue_compile(
    source: str,
    template: Template,
    consumers: Sequence[MarkupLintConsumer],
    *,
    renders_in_place: RendersInPlace | None = None,
) -> tuple[MarkupLintFinding, ...]:
    """
    Report what Vue's compiler rejects in a template, at the place the author wrote it.

    A broken Vue expression has its own rule (`citry.vue.invalid-expression`),
    and so does a block element inside a `<p>` (`citry.template.invalid-nesting`).
    A compiler error those rules explain is left out, whatever severity they
    have, so each mistake has one message and one setting.

    Args:
        source: The template text that ``template`` was parsed from. Finding
            positions are UTF-8 byte offsets into it.
        template: The parsed template.
        consumers: Every component known to render this template.
        renders_in_place: Says whether a component tag (its name without
            `c-`) renders in place, as a `transparent` or `simple` component
            does, or returns `None` when the caller cannot tell. A component
            inside a Vue `v-for` is reported only when this says it does not.

    Returns:
        Findings in source order. A template this rule cannot turn into the
        Vue template a render would compile is skipped, with no findings.

    """
    severity = _active_severities(tuple(consumers) or (MarkupLintConsumer(),)).get("rule_vue_compile_error")
    if severity is None:
        return ()
    try:
        nodes = _exec_template_code(_compile_prepared_template(template), source, prepared=True)()
    except (ValueError, TypeError, RuntimeError, SyntaxError):
        # Citry does not compile every template for Vue: one that uses an
        # extension's template syntax is rejected here, and building the
        # nodes rejects a few that the parser accepts, such as `#c-ignore`
        # on a component tag, which a render reports itself.
        return ()
    try:
        written = static_vue_template(source, nodes, renders_in_place=renders_in_place)
    except UnsupportedStaticTemplate:
        # A node with no Vue form a render would write: report nothing
        # rather than a guess.
        return ()
    errors = _compile_errors(written)
    if not errors and not written.scoped_fill_refusals:
        return ()
    found: dict[tuple[int, int, str], MarkupLintFinding] = {}
    # Vue's compiler accepts these, because the template written for Vue
    # leaves the pattern out, as a render does, but every render fails on them.
    for start, end, message in written.scoped_fill_refusals:
        found[start, end, message] = MarkupLintFinding(
            name="CITRY_SCOPED_FILL_IN_PLACE",
            message=render_diagnostic(VUE_COMPILE_ERROR, detail=message),
            code=VUE_COMPILE_ERROR,
            severity=severity,
            start_index=start,
            end_index=end,
        )
    explained: tuple[MarkupLintFinding, ...] | None = None
    without_paragraphs: set[tuple[str, str, int | None, int | None]] | None = None

    def errors_without_paragraphs() -> set[tuple[str, str, int | None, int | None]]:
        # One extra compile serves every tree error of this template.
        nonlocal without_paragraphs
        if without_paragraphs is None:
            nesting = [item for item in explained or () if item.code == TEMPLATE_INVALID_NESTING]
            without_paragraphs = _errors_without_paragraphs(written, nesting)
        return without_paragraphs

    for error in errors:
        located = _locate(written, error)
        if located is None:
            continue
        if _is_expression_error(error) or error.code in _TREE_CODES:
            # Run the two specific rules only when the compiler found
            # something they may explain, which is rare.
            if explained is None:
                explained = _specific_findings(template)
            if _already_reported(error, located, explained, errors_without_paragraphs):
                continue
        start, end = located
        found.setdefault(
            (start, end, error.message),
            MarkupLintFinding(
                name=error.code,
                message=render_diagnostic(VUE_COMPILE_ERROR, detail=_detail(written, error, located)),
                code=VUE_COMPILE_ERROR,
                severity=severity,
                start_index=start,
                end_index=end,
            ),
        )
    return tuple(sorted(found.values(), key=lambda item: (item.start_index, item.end_index)))


def _compile_errors(written: StaticVueTemplate) -> list[_CompilerError]:
    """Compile the Vue template and return its errors, each once, with positionless orphan `v-else`s located."""
    response = _compile(written, written.compile_input.template)
    errors: list[_CompilerError] = []
    seen: set[tuple[str, str, int | None, int | None]] = set()
    orphan_count = 0
    for item in response:
        stage = str(item.get("stage"))
        code = str(item.get("code"))
        if code == _ORPHAN_ELSE and item.get("start") is None:
            orphan_count += 1
            continue
        # The other errors from the compiler's checks of Citry's call
        # records and of its own generated code describe this module's
        # output, not the author's template.
        if stage in {"metadata", "audit"} and code != _COMPONENT_IN_V_FOR:
            continue
        start, end = item.get("start"), item.get("end")
        error = _CompilerError(
            code,
            str(item.get("message", "")),
            start if isinstance(start, int) else None,
            end if isinstance(end, int) else None,
        )
        # The parser and the compiler both report a tree error.
        key = (error.code, error.message, error.start, error.end)
        if key not in seen:
            seen.add(key)
            errors.append(error)
    if orphan_count:
        errors.extend(_orphan_else_errors(written, orphan_count))
    return errors


def _orphan_else_errors(written: StaticVueTemplate, orphan_count: int) -> list[_CompilerError]:
    """
    Find which `v-else` or `v-else-if` the compiler rejected.

    The compiler reports an orphan `v-else` without a position. Taking a
    group of them out of their chains (see `_ELSE_STAND_INS`) and compiling
    again shows whether the group held an orphan, because taking one out
    never makes another an orphan. A group that held none is dropped, and one
    that did is split in half, so a long template needs a few compiles per
    orphan rather than one per `v-else`. Each orphan is reported, including a
    `v-else` that follows an orphan `v-else-if`.
    """
    template = written.compile_input.template.encode()
    candidates = [
        directive
        for directive in written.else_directives
        if template[directive.vue_start : directive.vue_end].decode() in _ELSE_STAND_INS
    ]
    errors: list[_CompilerError] = []

    def orphans_in(group: list[ElseDirective]) -> int:
        changed = bytearray(template)
        for directive in group:
            name = template[directive.vue_start : directive.vue_end].decode()
            changed[directive.vue_start : directive.vue_end] = _ELSE_STAND_INS[name].encode()
        remaining = sum(
            1
            for item in _compile(written, changed.decode())
            if item.get("code") == _ORPHAN_ELSE and item.get("start") is None
        )
        return orphan_count - remaining

    def search(group: list[ElseDirective], held: int) -> None:
        if held <= 0:
            return
        if len(group) == 1:
            (directive,) = group
            name = template[directive.vue_start : directive.vue_end].decode()
            errors.append(
                _CompilerError(
                    _ORPHAN_ELSE,
                    f"'{name}' has no element with 'v-if' or 'v-else-if' right before it.",
                    directive.vue_start,
                    directive.vue_end,
                )
            )
            return
        if held >= len(group) and all(_is_plain_else(template, directive) for directive in group):
            # Taking a plain `v-else` out of its chain changes only its own
            # count, so a group that held as many orphans as it has members
            # is all orphans.
            for directive in group:
                search([directive], 1)
            return
        first, second = group[: len(group) // 2], group[len(group) // 2 :]
        # Each half is compiled on its own: taking a `v-else-if` out of its
        # chain also mends the orphan `v-else` after it, so one half's count
        # says nothing exact about the other's.
        search(first, orphans_in(first))
        search(second, orphans_in(second))

    search(candidates, orphans_in(candidates))
    return errors


def _is_plain_else(template: bytes, directive: ElseDirective) -> bool:
    return template[directive.vue_start : directive.vue_end] == b"v-else"


def _compile(written: StaticVueTemplate, template: str) -> list[dict[str, object]]:
    compile_input = written.compile_input
    response = json.loads(
        _rust.vue._compile_vue(
            template,
            json.dumps(compile_input.local_calls, separators=(",", ":")),
            json.dumps(compile_input.element_bindings, separators=(",", ":")),
        )
    )
    diagnostics = response.get("diagnostics", [])
    return [item for item in diagnostics if isinstance(item, dict)]


def _locate(written: StaticVueTemplate, error: _CompilerError) -> tuple[int, int] | None:
    """Map a compiler error to the authored bytes it is about, or `None` when it points at no authored text."""
    if error.start is None or error.end is None:
        return None
    located = written.authored_range(error.start, error.end)
    if located is not None or error.code != _COMPONENT_IN_V_FOR:
        return located
    # This error points at the generated tag of a component call, which maps
    # to the authored call as a whole; report it on the call's tag name.
    call = written.generated_source(error.start)
    # Only a call known to be an ordinary call counts: a component that
    # renders in place may sit inside a Vue `v-for`.
    if call is None or error.start not in written.ordinary_calls:
        return None
    return call[0] + 1, call[0] + 1 + _tag_name_length(written, call[0] + 1)


def _tag_name_length(written: StaticVueTemplate, start: int) -> int:
    name = written.source[start:]
    length = 0
    while length < len(name) and name[length : length + 1] not in b" \t\n\r\f/>":
        length += 1
    return length


def _specific_findings(template: Template) -> tuple[MarkupLintFinding, ...]:
    """
    Run the expression and paragraph-nesting rules with both turned on, to see what they explain.

    The rules' own severities do not matter here: a mistake they find
    belongs to them even when a project turns them off.
    """
    consumer = MarkupLintConsumer(rule_invalid_nesting="error", rule_invalid_vue_expression="error")
    return (
        *lint_markup(template, (consumer,)),
        *lint_invalid_vue_expressions(template, browser_expressions(template), (consumer,)),
    )


def _context_start(finding: MarkupLintFinding) -> int:
    return finding.start_index if finding.context_start_index is None else finding.context_start_index


def _context_end(finding: MarkupLintFinding) -> int:
    return finding.end_index if finding.context_end_index is None else finding.context_end_index


def _already_reported(
    error: _CompilerError,
    located: tuple[int, int],
    reported: Sequence[MarkupLintFinding],
    errors_without_paragraphs: Callable[[], set[tuple[str, str, int | None, int | None]]],
) -> bool:
    """Whether another rule's more specific finding already explains this compiler error."""
    start, end = located
    if _is_expression_error(error):
        # The expression finding may span only the token the parser stopped
        # at, while Vue's compiler points elsewhere in the same expression,
        # so compare with the whole expression it was found in.
        return any(
            finding.code == VUE_INVALID_EXPRESSION
            and _context_start(finding) < max(end, start + 1)
            and start < _context_end(finding)
            for finding in reported
        )
    nesting = [finding for finding in reported if finding.code == TEMPLATE_INVALID_NESTING]
    if error.code not in _TREE_CODES or not nesting:
        return False
    # The browser closes a `<p>` before a block inside it, and the compiler
    # then reports every tag that closing leaves behind, such as the `</a>`
    # around the block or the `</p>` itself. The same template with each such
    # `<p>` renamed to `<q>`, which a block does not close, shows which
    # errors the paragraph caused.
    return (error.code, error.message, error.start, error.end) not in errors_without_paragraphs()


def _errors_without_paragraphs(
    written: StaticVueTemplate,
    nesting: Sequence[MarkupLintFinding],
) -> set[tuple[str, str, int | None, int | None]]:
    """Compile the template with the `<p>` around each nesting finding renamed, and return the errors left."""
    template = bytearray(written.compile_input.template.encode())
    for finding in nesting:
        for start, close_start, _end in written.paragraphs_around(finding.start_index):
            # `<p` and `</p` become `<q` and `</q`, so no other byte moves.
            for name_at in (start + 1, close_start + 2):
                position = written.vue_offset(name_at)
                if position is not None and template[position] in b"pP":
                    template[position] = ord("q") if template[position] == ord("p") else ord("Q")
    return {
        (str(item.get("code")), str(item.get("message", "")), item.get("start"), item.get("end"))  # type: ignore[misc]
        for item in _compile(written, template.decode())
    }


def _is_expression_error(error: _CompilerError) -> bool:
    """Whether the compiler rejected an expression, as in `InvalidExpression` or `VForMalformedExpression`."""
    return "Expression" in error.code


def _detail(written: StaticVueTemplate, error: _CompilerError, located: tuple[int, int]) -> str:
    """Return what the compiler found as one sentence, in plain words for the messages authors meet most."""
    if error.code == "InvalidEndTag":
        return "the browser already closed this element, so this end tag closes nothing."
    if error.code == _COMPONENT_IN_V_FOR:
        return "a component cannot be inside a Vue 'v-for'. Repeat it with '<c-for>'."
    tag_match = _TAG_NAME.match(written.source, located[0])
    tag = tag_match.group(1).decode() if tag_match is not None else "element"
    for start, wording in _TREE_MESSAGES:
        if error.message.startswith(start):
            return wording.format(tag=tag)
    message = error.message.strip()
    if not message:
        return error.code
    # Keep a leading acronym such as "HTML" as written.
    return message[:1].lower() + message[1:] if message[1:2].islower() else message
