"""Opaque trusted HTML preparation without treating its bytes as Vue source."""

from __future__ import annotations

from html import escape

from citry._output_html import scan_output_html
from citry.attrs import _html_attr_identity
from citry_core.html_transform import mark_html, static_html_node_count, validate_html_fragment_boundary

# How the fragment check starts its message when it refuses a parse error
# rather than the shape of the tags (`validate_html_fragment_boundary`). Keep
# in step with the message in `output_scanner.rs`.
_PARSE_ERROR_PREFIX = "opaque HTML has the HTML parse error "
# The parse errors a '<' that does not start a tag causes.
_STRAY_LESS_THAN_ERRORS = frozenset(
    {"invalid-first-character-of-tag-name", "eof-before-tag-name", "missing-end-tag-name"}
)


def reject_cross_boundary_html(html: str, *, origin: str) -> None:
    """
    Reject opaque markup whose element balance depends on adjacent typed parts.

    Vue inserts the HTML as one block of nodes, so the block cannot open a tag
    that the template closes later, or the other way round. ``origin`` names
    the input for the error message, such as "The <c-raw> block at line 3,
    column 5".
    """
    try:
        validate_html_fragment_boundary(html)
    except ValueError as error:
        preview = html if len(html) <= 80 else f"{html[:77]}..."
        # The check names a parse error it refuses by its name in the HTML
        # standard, so the message can say what to fix in the text itself;
        # the tag rules cover the shape of the tags.
        parse_error = (
            str(error).removeprefix(_PARSE_ERROR_PREFIX) if str(error).startswith(_PARSE_ERROR_PREFIX) else None
        )
        if parse_error is not None:
            hint = (
                " A '<' that does not start a tag must be written as '&lt;'."
                if parse_error in _STRAY_LESS_THAN_ERRORS
                else ""
            )
            msg = (
                f"{origin} is not well-formed HTML: {preview!r} has the HTML parse error {parse_error!r}"
                " (see https://html.spec.whatwg.org/multipage/parsing.html#parse-errors)."
                f"{hint} Inside an interactive component, Vue inserts this HTML as one block, so Citry"
                " accepts only HTML the browser reads without such an error, where it can tell where each"
                " tag starts and ends. Static pages do not need this, because there the HTML is written"
                " into the page as is."
            )
            raise ValueError(msg) from error
        msg = (
            f"{origin} is not a complete HTML fragment: {preview!r}. Inside an interactive component,"
            " Vue inserts this HTML as one block, so every tag it opens must be closed inside it, it must"
            " not close a tag it did not open, and a non-void element such as <iframe> needs its end tag"
            " because the browser ignores a '/' on it. Fix the HTML, or move the tags it shares with the"
            " template into it. Static pages do not have this rule, because there the HTML is written into"
            " the page as is."
        )
        raise ValueError(msg) from error


def mark_opaque_html(html: str, markers: tuple[tuple[str, object], ...]) -> str:
    """Apply validated component-root markers while preserving all other bytes."""
    if type(html) is not str:
        raise TypeError("opaque HTML must be an exact string")
    if not markers or not html:
        return html
    sentinel = "data-citry-opaque-root"
    while sentinel.casefold() in html.casefold():
        sentinel += "x"
    placeholder = "data-citry-opaque-placeholder"
    while placeholder.casefold() in html.casefold():
        placeholder += "x"
    segments, placeholders = mark_html(html, [sentinel], placeholder)
    if placeholders:
        raise ValueError("opaque HTML unexpectedly contained the private placeholder marker")
    marked = segments[0]
    marker_identities = {_html_attr_identity(name) for name, _ in markers}
    sentinel_identity = _html_attr_identity(sentinel)
    for element in scan_output_html(marked).elements:
        identities = {_html_attr_identity(attr.key.content) for attr in element.start_tag.attrs}
        if sentinel_identity in identities and marker_identities & (identities - {sentinel_identity}):
            raise ValueError("opaque HTML root conflicts with a component root marker")
    replacement = "".join(
        f' {name}=""' if value is True else f' {name}="{escape(str(value), quote=True)}"' for name, value in markers
    )
    return marked.replace(f' {sentinel}=""', replacement)


def opaque_html_record(html: str, *, pinned: bool = False) -> dict[str, object]:
    """
    Return the prepared record the browser renders as one static vnode.

    ``nodeCount`` is the number of top-level nodes the browser creates for the
    HTML inside a ``<template>`` element. Vue needs it to adopt those nodes
    when the server wrote the block into a hydrated page; the server checks
    that the page's own parse creates the same nodes before it writes them.

    ``pinned`` marks a `#c-ignore` element's contents: the browser keeps the
    nodes from the first render for the life of the component instance and
    ignores the HTML of later renders, so a library can take them over.
    """
    record: dict[str, object] = {"html": html, "nodeCount": static_html_node_count(html)}
    if pinned:
        record["pinned"] = True
    return record


__all__ = ["mark_opaque_html", "opaque_html_record", "reject_cross_boundary_html"]
