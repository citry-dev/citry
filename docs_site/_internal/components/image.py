"""
The ``<c-image />`` tag: an image with an optional width or CSS class. It is sugar
over markdown's own ``![alt](src)``, which still handles the simple case.
"""

from __future__ import annotations

from typing import Any

from markupsafe import Markup, escape

from citry import Component


class Image(Component):
    """``<c-image src="..." alt="..." width="..." css_class="..." />`` renders an image tag."""

    name = "image"
    transparent = True
    template = "{{ img }}"

    class Kwargs:
        src: str
        alt: str = ""
        width: str = ""
        css_class: str = ""

    def template_data(self, kwargs: Kwargs, slots: Any) -> dict[str, Any]:  # noqa: ARG002
        attrs = [f'src="{escape(str(kwargs.src))}"', f'alt="{escape(str(kwargs.alt))}"']
        width = str(kwargs.width)
        if width:
            attrs.append(f'width="{escape(width)}"')
        css_class = str(kwargs.css_class)
        if css_class:
            attrs.append(f'class="{escape(css_class)}"')
        # Markup so the <img> reaches the markdown pass as literal HTML; every
        # attribute value is escaped above. Trusted: the page author names the src.
        return {
            "img": Markup(f"<img {' '.join(attrs)} />"),  # noqa: S704
        }
