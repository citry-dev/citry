"""
HTML escaping and the "safe string" type.

Citry autoescapes the result of template expressions before placing it in the
output, so user data cannot inject markup. A value that is already trusted HTML
(for example the result of rendering a subtree) carries that trust as a
``SafeString`` and is passed through unescaped.

This is a thin wrapper over ``markupsafe`` so the rest of citry depends on this
module, not on ``markupsafe`` directly: the escaping backend is isolated to one
place.

- ``escape(value)`` returns a ``SafeString``. It respects the ``__html__``
  protocol, so a value that is already a ``SafeString`` (or any object with
  ``__html__``) passes through without double-escaping.
- ``escape`` escapes ``& < > ' "``. Escaping all five means the same output is
  safe in both HTML body text and double- or single-quoted attribute values,
  which matters because a template expression can land in either position.
- ``SafeString`` is ``markupsafe.Markup``: a ``str`` subclass marking trusted
  HTML. Construct one to opt a value out of escaping.
"""

from __future__ import annotations

from markupsafe import Markup, escape

# Citry-owned name for the trusted-HTML marker (markupsafe.Markup).
SafeString = Markup

__all__ = ["Markup", "SafeString", "escape"]
