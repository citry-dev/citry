"""
HTML escaping and the trusted-markup type.

Citry autoescapes the result of template expressions before placing it in the
output, so user data cannot inject markup. A value that is already trusted HTML
(for example the result of rendering a subtree) carries that trust as
``Markup`` and is passed through unescaped.

Citry's rendering modules import their escaping tools from this thin wrapper so
backend-specific behavior stays in one place. The public package re-exports the
same ``Markup`` class directly.

- ``escape(value)`` returns ``Markup``. It respects the ``__html__``
  protocol, so a value that is already ``Markup`` (or any object with
  ``__html__``) passes through without double-escaping.
- ``escape`` escapes ``& < > ' "``. Escaping all five means the same output is
  safe in both HTML body text and double- or single-quoted attribute values,
  which matters because a template expression can land in either position.
- ``Markup`` is exactly ``markupsafe.Markup``, imported unchanged.
  ``Markup(value)`` marks the complete value as trusted HTML; it does not
  sanitize, validate, or escape anything. See
  https://markupsafe.palletsprojects.com/en/stable/escaping/#markupsafe.Markup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from markupsafe import Markup, escape

if TYPE_CHECKING:
    from collections.abc import Callable

# markupsafe's escaper that returns a plain ``str`` (the same function that
# ``escape`` runs internally before wrapping the result in a ``Markup``).
# it lives in the C ``_speedups`` module, with a pure-Python ``_native`` twin;
# we resolve whichever is present and fall back to the public ``escape`` if a
# future markupsafe drops the name, so this stays a one-line behaviour change.
_escape_to_str_impl: Callable[[str], str] | None
try:
    from markupsafe._speedups import _escape_inner as _escape_to_str_impl
except ImportError:  # pragma: no cover - depends on the installed wheel
    try:
        from markupsafe._native import _escape_inner as _escape_to_str_impl
    except ImportError:  # pragma: no cover - very old markupsafe
        _escape_to_str_impl = None


def escape_to_str(value: Any) -> str:
    """
    Escape ``value`` to a plain ``str`` (not ``Markup``).

    Same character escaping as :func:`escape`, including the ``__html__``
    pass-through, but it skips allocating a ``Markup`` for the result. Use it
    only where the escaped text is concatenated into a larger string that is
    marked safe as a whole (so the unmarked piece is never re-escaped); for a
    value that becomes output on its own, use :func:`escape`.
    """
    if hasattr(value, "__html__"):
        return str(value.__html__())
    text = str(value)

    # IMPORTANT: we don't use ``escape(text)`` here because that creates a Markup
    # object, which is unnecessary overhead / performance penalty, when the caller
    # is just going to concatenate the result into a larger string.
    # Instead, we call the internal escape function that returns a plain string.
    if _escape_to_str_impl is None:
        return str(escape(text))
    return _escape_to_str_impl(text)


__all__ = ["Markup", "escape", "escape_to_str"]
