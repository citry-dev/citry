"""Development-only component and slot boundary highlighting."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import TYPE_CHECKING, ClassVar, Literal, cast
from weakref import WeakSet

from citry.citry_context import CitryContext
from citry.citry_render import CitryRender, RenderDecoration
from citry.extension import Extension, ExtensionConfig

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.citry_render import RenderPart
    from citry.component import Component
    from citry.extension import (
        OnComponentRegisteredContext,
        OnComponentRenderedContext,
        OnComponentUnregisteredContext,
        OnRenderCacheExportContext,
        OnRenderContextMergeContext,
        OnSlotRenderedContext,
    )


_CACHE_ACTIVE_KEY = "debug:render-cache-active"
_CONFIG_FIELDS = frozenset(("highlight_components", "highlight_slots"))

_BoundaryKind = Literal["component", "slot"]


@dataclass(frozen=True, slots=True)
class _Palette:
    text: str
    border: str


_PALETTES: dict[_BoundaryKind, _Palette] = {
    "component": _Palette(text="#2f14bb", border="blue"),
    "slot": _Palette(text="#bb1414", border="#e40c0c"),
}


def _wrap_result(result: RenderPart, *, kind: _BoundaryKind, label: str, source: str) -> RenderDecoration:
    from citry._vue.capture import (  # noqa: PLC0415
        PreparedAttribute,
        PreparedElementClose,
        PreparedElementOpen,
        PreparedTextValue,
    )

    palette = _PALETTES[kind]
    context = result.context if isinstance(result, CitryRender) else CitryContext()
    parts = list(result.parts) if type(result) is CitryRender else [result]
    return RenderDecoration(
        parts=parts,
        context=context,
        opening=(
            PreparedElementOpen(
                source,
                (0, len(source.encode())),
                "div",
                (
                    PreparedAttribute("class", "data", (0, 0), f"citry-debug citry-debug-{kind}"),
                    PreparedAttribute("style", "data", (0, 0), f"border: 1px solid {palette.border}"),
                ),
                is_void=False,
                is_self_closing=False,
                element_metadata=(),
            ),
            PreparedElementOpen(
                source,
                (0, len(source.encode())),
                "span",
                (
                    PreparedAttribute("class", "data", (0, 0), "citry-debug-label"),
                    PreparedAttribute("style", "data", (0, 0), f"font-weight: bold; color: {palette.text}"),
                    PreparedAttribute("aria-hidden", "data", (0, 0), "true"),
                ),
                is_void=False,
                is_self_closing=False,
                element_metadata=(),
            ),
            PreparedTextValue(source, (0, len(source.encode())), label),
            PreparedTextValue(source + ":suffix", (0, len((source + ":suffix").encode())), ": "),
            PreparedElementClose(source, (0, len(source.encode())), "span"),
        ),
        closing=(PreparedElementClose(source, (0, len(source.encode())), "div"),),
        omit_around_document=True,
        frame=result.frame if isinstance(result, CitryRender) else None,
    )


class Debug(Extension):
    """
    Draw development-only boundaries around component and slot output.

    Install this extension explicitly with ``Citry(extensions=[Debug])``.
    Its per-component config has two exact boolean fields,
    ``highlight_components`` and ``highlight_slots``. Set them globally in
    ``extensions_defaults["debug"]`` or override them in a component's nested
    ``class Debug``.

    The visual boundaries are real ``div`` elements. They are useful for
    inspecting ordinary page structure, but can affect layout, direct-child
    selectors, and restricted table or select content models. Do not enable
    them in production or use them for layout-sensitive verification.

    Example:
        Enable both boundary types for one engine:

        ```python
        from citry import Citry
        from citry.ext.debug import Debug

        app = Citry(
            extensions=[Debug],
            extensions_defaults={
                "debug": {
                    "highlight_components": True,
                    "highlight_slots": True,
                },
            },
        )
        ```

    """

    name = "debug"

    def __init__(self) -> None:
        self._registered_components: WeakSet[type[Component]] = WeakSet()
        self._registered_components_lock = RLock()

    class Config(ExtensionConfig):
        """Per-component Debug switches."""

        highlight_components: ClassVar[bool] = False
        highlight_slots: ClassVar[bool] = False

        def __init__(self, component: Component | None) -> None:
            super().__init__(component)
            self._slot_occurrence = 0

        def _next_slot_occurrence(self) -> int:
            self._slot_occurrence += 1
            return self._slot_occurrence

    def validate_config_fields(
        self,
        fields: Mapping[str, object],
        *,
        component: type[Component] | None = None,  # noqa: ARG002 - required extension hook signature
    ) -> None:
        for name, value in fields.items():
            if name not in _CONFIG_FIELDS:
                expected = ", ".join(repr(field) for field in sorted(_CONFIG_FIELDS))
                msg = f"unknown config field {name!r}; expected one of {expected}"
                raise ValueError(msg)
            if type(value) is not bool:
                msg = f"config field {name!r} must be a bool; got {value!r}"
                raise ValueError(msg)

    def on_component_registered(self, ctx: OnComponentRegisteredContext) -> None:
        with self._registered_components_lock:
            self._registered_components.add(ctx.component_class)

    def on_component_unregistered(self, ctx: OnComponentUnregisteredContext) -> None:
        with self._registered_components_lock:
            if not ctx.citry._has_component_class(ctx.component_class):
                self._registered_components.discard(ctx.component_class)

    def render_cache_bypass_reason(self) -> str | None:
        """Require live rendering while debug highlighting is enabled."""
        with self._registered_components_lock:
            component_classes = tuple(self._registered_components)
        active = any(
            (config := getattr(component_class, self.class_name, None)) is not None
            and (config.highlight_components or config.highlight_slots)
            for component_class in component_classes
        )
        return "debug-active" if active else None

    def on_component_rendered(self, ctx: OnComponentRenderedContext) -> CitryRender | None:
        config = cast("Debug.Config", getattr(ctx.component, self.name))
        if (
            ctx.error is not None
            or ctx.render is None
            or type(ctx.component).transparent
            or not config.highlight_components
        ):
            return None
        label = f"{type(ctx.component).__name__} ({ctx.component.id})"
        wrapped = _wrap_result(
            ctx.render,
            kind="component",
            label=label,
            source=f"debug:component:{type(ctx.component).__name__}",
        )
        wrapped.context.extra[_CACHE_ACTIVE_KEY] = True
        return wrapped

    def on_slot_rendered(self, ctx: OnSlotRenderedContext) -> CitryRender | None:
        config = cast("Debug.Config", getattr(ctx.component, self.name))
        if type(ctx.component).transparent or not config.highlight_slots:
            return None
        occurrence = config._next_slot_occurrence()
        label = f"{type(ctx.component).__name__} - {ctx.slot_name}"
        wrapped = _wrap_result(
            ctx.result,
            kind="slot",
            label=label,
            source=f"debug:slot:{type(ctx.component).__name__}:{ctx.slot_name}:{occurrence}",
        )
        wrapped.context.extra[_CACHE_ACTIVE_KEY] = True
        return wrapped

    def on_render_context_merge(self, ctx: OnRenderContextMergeContext) -> None:
        if ctx.child_context.extra.get(_CACHE_ACTIVE_KEY):
            ctx.parent_context.extra[_CACHE_ACTIVE_KEY] = True

    def _render_cache_participates(self, ctx: OnRenderCacheExportContext) -> bool:
        return bool(ctx.root_context.extra.get(_CACHE_ACTIVE_KEY))


__all__ = ["Debug"]
