"""Internal localization ownership helpers shared by Citry UI families."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from citry import Component, LibraryComponent


def uses_catalog_default(component: Component | LibraryComponent, input_name: str) -> bool:
    """Return whether Citry UI, rather than the caller, owns this default."""
    return input_name not in component.raw_kwargs


_BIDI_CONTROLS = frozenset("\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")
_PARAGRAPH_BOUNDARIES = frozenset("\n\r\u001c\u001d\u001e\u0085\u2029")


def inline_translation_value(value: str) -> str:
    """Make component text safe to interpolate into one Fluent paragraph."""
    return "".join(
        " " if character in _PARAGRAPH_BOUNDARIES else character
        for character in value
        if character not in _BIDI_CONTROLS
    )


def fill_label(pattern: str, **values: object) -> str:
    """
    Put each value in place of its `{name}` in an app-supplied label, such as `"{count} items added"`.

    Where Citry UI's browser code fills a label again, it uses this same
    plain text replacement, one name at a time in the order given, so the
    server and the browser show the same text. `str.format` would read a
    format spec in the label, such as `{total:>99}`, and pad the text or
    look up attributes instead.
    """
    for name, value in values.items():
        pattern = pattern.replace(f"{{{name}}}", str(value))
    return pattern


__all__ = ["fill_label", "inline_translation_value", "uses_catalog_default"]
