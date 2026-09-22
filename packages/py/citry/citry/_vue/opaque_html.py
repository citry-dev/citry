"""Opaque trusted HTML preparation without treating its bytes as Vue source."""

from __future__ import annotations

from html import escape

from citry._output_html import scan_output_html
from citry.attrs import _html_attr_identity
from citry_core.html_transform import mark_html, validate_html_fragment_boundary


def reject_cross_boundary_html(html: str) -> None:
    """Reject opaque markup whose element balance depends on adjacent typed parts."""
    validate_html_fragment_boundary(html)


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


__all__ = ["mark_opaque_html", "reject_cross_boundary_html"]
