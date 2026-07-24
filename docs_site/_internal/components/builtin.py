"""The ``<c-builtin />`` tag: render a built-in ``<c-*>`` tag's reference card."""

from __future__ import annotations

from typing import Any

from markupsafe import Markup, escape

from citry import Component
from docs_site._internal.components.reference_symbol import ReferenceSymbol
from docs_site._internal.reference import extract_builtin
from docs_site._internal.util import lstrip_outside_pre


class Builtin(Component):
    """``<c-builtin tag="provide" />`` renders a built-in ``<c-*>`` tag's reference."""

    transparent = True
    template = "{{ rendered }}"

    class Kwargs:
        tag: str

    def template_data(self, kwargs: Kwargs, slots: Any) -> dict[str, Any]:  # noqa: ARG002
        tag = str(kwargs.tag)
        data = extract_builtin(tag)
        if data is None:
            rendered = Markup(  # noqa: S704
                f'<p class="docs-error">Unknown built-in: {escape(tag)}</p>'
            )
        else:
            rendered = lstrip_outside_pre(str(ReferenceSymbol(data=data)))
            rendered = Markup(f"\n\n{rendered}\n\n")  # noqa: S704

        return {
            "rendered": rendered,
        }
