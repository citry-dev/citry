"""
CitryRender - the output of rendering a CitryElement.

The rendering pipeline has three phases, each with its own struct (see
docs/design/rendering.md):

    Component(**kwargs)       -> CitryElement   compose: "what to render"
    CitryElement.render()     -> CitryRender    render: parts + collected metadata
    CitryRender.serialize()   -> str (HTML)     serialize: join + place deps

``CitryRender`` is the middle struct, and on purpose it is NOT a string. Keeping
the render output as an object lets an already-rendered piece be reused. You can
pass a ``CitryRender`` to another component (as a kwarg, inside ``{{ ... }}``, or
in an attribute); the component that receives it pulls in its HTML and copies up
its collected data (JS/CSS dependencies). Turning it into a string
(``str()``/``serialize()``) is the final step that produces the HTML. This is the
citry form of django-components #1650 ("cache the render object, not the string").

A ``CitryRender`` holds:

- ``parts``: an ordered list whose items can be different types. Each part is a
  ``str`` (static or already-rendered text) or a nested ``CitryRender`` (a piece
  not yet joined into text). Joining only at the end keeps reuse cheap and keeps
  the dependencies readable until the final serialize.
- ``context``: the ``CitryContext`` used during the render. For now the whole
  context is kept (the collected data lives in its ``extra``); this can be
  narrowed to specific fields once we know what serialize needs.

Serialization is currently just the recursive join of the parts. Placing
collected dependencies into ``<head>``/``<body>`` (document mode) and the
fragment-mode and injection-strategy choices are future work (see
docs/design/rendering.md sections 5-6).

Example:
    Render and serialize a component::

        from citry import Component

        class Hello(Component):
            template = "<p>Hello!</p>"

        rendered = Hello().render()      # -> CitryRender
        html = rendered.serialize()      # -> "<p>Hello!</p>"
        assert str(rendered) == html     # str() is a convenience for serialize()

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias

from citry.citry_element import CitryElement
from citry.util.html import escape

if TYPE_CHECKING:
    from citry.citry_context import CitryContext
    from citry.component import Component

# One piece of rendered output. It is one of:
#   - str: final text.
#   - CitryRender: a nested render not yet joined into text.
#   - DeferredComponent: a child component not yet rendered (render() renders it
#     before any serialize()).
# A CitryRender's `parts`, and what a node's render() returns, are made of these.
RenderPart: TypeAlias = "str | CitryRender | DeferredComponent"


class CitryRender:
    """
    The result of rendering a ``CitryElement`` (the render-phase output).

    Attributes:
        parts: Ordered list of ``str`` or nested ``CitryRender`` fragments.
        context: The ``CitryContext`` used to produce this render.

    """

    __slots__ = ("context", "parts")

    def __init__(self, parts: list[RenderPart], context: CitryContext) -> None:
        self.parts = parts
        self.context = context

    def serialize(self) -> str:
        """
        Join the parts into a final HTML string.

        Nested ``CitryRender`` parts are serialized recursively. Placement of
        collected dependencies (head/body) and serialization strategies
        (document vs fragment mode) are not implemented yet; see
        docs/design/rendering.md.
        """
        out: list[str] = []
        for part in self.parts:
            if isinstance(part, CitryRender):
                out.append(part.serialize())
            elif isinstance(part, str):
                out.append(part)
            else:
                # The part is a DeferredComponent, so a child component was never
                # rendered. render() renders all of them, so reaching here means
                # serialize() ran on a render that did not come from render()
                # (see docs/design/deferred_rendering.md section 4). It is a
                # RuntimeError, not a TypeError: the render is just unfinished,
                # nothing was given the wrong type.
                msg = "unresolved DeferredComponent at serialize(); render() must process the queue first"
                raise RuntimeError(msg)  # noqa: TRY004
        return "".join(out)

    def __str__(self) -> str:
        return self.serialize()

    def __bytes__(self) -> bytes:
        return self.serialize().encode()

    def __repr__(self) -> str:
        return f"CitryRender(parts={len(self.parts)})"


class DeferredComponent:
    """
    A child component that has not been rendered yet.

    When the parent's template reaches a ``<c-child>`` tag, citry does not render
    the child right there. Doing so would mean one component renders the next,
    which renders the next, so a deeply nested page would hit Python's recursion
    limit. Instead the parent records the child as a ``DeferredComponent`` (with
    its inputs already worked out) and carries on. ``render_impl`` later renders
    the recorded children one at a time, swapping each ``DeferredComponent`` for
    the child's ``CitryRender``. See docs/design/deferred_rendering.md section 4.

    Attributes:
        element: The child to render: its component class plus the inputs
            (kwargs/slots), already worked out. The inputs are read while the
            parent is still rendering, so a loop variable from an enclosing
            ``<c-for>`` keeps the right value.
        parent: The parent ``Component`` instance. Used to set the child's
            ``parent``/``root`` links when it is rendered.

    """

    __slots__ = ("element", "parent")

    def __init__(self, element: CitryElement, parent: Component) -> None:
        self.element = element
        self.parent = parent

    def __repr__(self) -> str:
        return f"DeferredComponent({self.element!r})"


def _render_value(value: Any) -> RenderPart:
    """
    Convert an evaluated expression value into a body part.

    This is the bridge from an arbitrary Python value (the result of evaluating
    a ``{{ ... }}`` expression, or a value handed into an attribute) to a
    ``RenderPart``. The rules (see docs/design/rendering.md section 3.1):

    - ``None`` renders as the empty string (not the literal ``"None"``).
    - A ``CitryElement`` (a composed-but-unrendered element handed into an
      expression) is rendered now, so its output and dependencies flow into the
      surrounding tree.
    - A ``CitryRender`` (an already-rendered subtree) is inlined as-is; it is
      trusted HTML, and the surrounding ``_render_body`` merges its dependencies.
    - Anything else is autoescaped. ``escape`` respects the ``__html__``
      protocol, so a ``SafeString`` (trusted HTML) passes through unescaped.
    """
    if value is None:
        return ""
    if isinstance(value, CitryElement):
        value = value.render()
    if isinstance(value, CitryRender):
        return value
    return escape(value)
