"""
The ``<c-js>`` and ``<c-css>`` built-in components.

Each marks the spot where the page's collected dependencies go: ``<c-css />``
the stylesheet tags (typically inside ``<head>``), ``<c-js />`` the script
tags (typically at the end of ``<body>``)::

    <head>
      <c-css />
    </head>
    <body>
      ...
      <c-js />
    </body>

Without these tags the dependencies still land in sensible default locations
(CSS before ``</head>``, JS before ``</body>``); the tags exist for precise
control. When the same tag appears more than once, the first one (in document
order) receives the tags and the rest render nothing.

Each component renders a :class:`~citry.citry_render.Placeholder` part; the
dependencies extension fills it at serialize time
(docs/design/dependencies.md section 7.3).

Each ``Citry`` instance gets its own subclass, created lazily by
``make_builtin_components`` (a Component class binds to one Citry instance at
class-definition time, so the built-ins cannot be shared).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from citry.citry_context import CitryContext
from citry.citry_render import CitryRender, Placeholder
from citry.component import Component
from citry.extensions.dependencies.emission import CSS_PLACEHOLDER_KEY, JS_PLACEHOLDER_KEY

if TYPE_CHECKING:
    from citry.citry import Citry


def _placeholder_render(component: Component, tag_name: str, key: str) -> CitryRender:
    """The shared ``on_render`` body: validate the usage, produce the placeholder part."""
    if component.raw_kwargs:
        msg = f"<{tag_name}> takes no attributes (got {', '.join(component.raw_kwargs)})"
        raise ValueError(msg)
    if component.raw_slots:
        msg = f"<{tag_name}> takes no body; write it self-closing: <{tag_name} />"
        raise ValueError(msg)
    # The placeholder rides a bare component-less render; being transparent,
    # the component's output joins the surrounding frame unmarked.
    return CitryRender(parts=[Placeholder(key)], context=CitryContext())


def make_js_component(citry_instance: Citry) -> type[Component]:
    """Create (and thereby register) the ``<c-js>`` component for one Citry instance."""

    class Js(Component):
        """Marks where the collected ``<script>`` dependency tags are placed."""

        citry = citry_instance
        transparent = True

        def on_render(self) -> CitryRender:
            return _placeholder_render(self, "c-js", JS_PLACEHOLDER_KEY)

    return Js


def make_css_component(citry_instance: Citry) -> type[Component]:
    """Create (and thereby register) the ``<c-css>`` component for one Citry instance."""

    class Css(Component):
        """Marks where the collected stylesheet dependency tags are placed."""

        citry = citry_instance
        transparent = True

        def on_render(self) -> CitryRender:
            return _placeholder_render(self, "c-css", CSS_PLACEHOLDER_KEY)

    return Css
