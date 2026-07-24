"""The ``<c-docstring />`` tag: render one API symbol's reference card."""

from __future__ import annotations

from typing import Any

from markupsafe import Markup, escape

from citry import Component
from docs_site._internal.components.reference_symbol import ReferenceSymbol
from docs_site._internal.reference import extract_symbol
from docs_site._internal.util import lstrip_outside_pre


class Docstring(Component):
    """``<c-docstring path="citry.X" />`` renders one symbol's API reference."""

    transparent = True
    template = "{{ rendered }}"

    class Kwargs:
        path: str

    def template_data(self, kwargs: Kwargs, slots: Any) -> dict[str, Any]:  # noqa: ARG002
        path = str(kwargs.path)
        data = extract_symbol(path)
        if data is None:
            rendered = Markup(  # noqa: S704
                f'<p class="docs-error">Unknown symbol: {escape(path)}</p>'
            )
        else:
            # Render, flush left (outside <pre>), pad. Trusted: built from citry's own
            # introspected API plus Markdown-rendered docstrings.
            rendered = lstrip_outside_pre(str(ReferenceSymbol(data=data)))
            rendered = Markup(f"\n\n{rendered}\n\n")  # noqa: S704
        return {"rendered": rendered}
