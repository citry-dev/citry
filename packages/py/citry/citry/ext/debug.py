"""Development-only component and slot boundary highlighting."""

from __future__ import annotations

import re
from dataclasses import dataclass
from threading import RLock
from typing import TYPE_CHECKING, ClassVar, Literal, cast
from weakref import WeakSet

from citry.citry_context import CitryContext
from citry.citry_render import CitryRender, Placeholder
from citry.extension import Extension, ExtensionConfig
from citry.util.html import escape_to_str

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
        OnSerializeContext,
        OnSlotRenderedContext,
    )


_KEY_PREFIX = "citry-debug-boundary"
_CACHE_ACTIVE_KEY = "debug:render-cache-active"
_CONFIG_FIELDS = frozenset(("highlight_components", "highlight_slots"))
_DOCUMENT_ROOT_RE = re.compile(
    r"\A\s*(?:\ufeff\s*)?(?:(?:<!--.*?-->)\s*)*(?:<!doctype\s+html(?:\s[^>]*)?>|<html(?:\s|>))",
    flags=re.IGNORECASE | re.DOTALL,
)
_HEX_RE = re.compile(r"[0-9a-f]*\Z")

_BoundaryKind = Literal["component", "slot"]
_BoundarySide = Literal["open", "close"]


@dataclass(frozen=True, slots=True)
class _Palette:
    text: str
    border: str


@dataclass(frozen=True, slots=True)
class _Occurrence:
    boundary_id: tuple[_BoundaryKind, str, str]
    side: _BoundarySide
    placeholder_html: str
    position: int


_PALETTES: dict[_BoundaryKind, _Palette] = {
    "component": _Palette(text="#2f14bb", border="blue"),
    "slot": _Palette(text="#bb1414", border="#e40c0c"),
}


def _encode(value: str) -> str:
    """Encode a variable key field into characters safe inside c-render-id."""
    return value.encode().hex()


def _decode(value: str) -> str | None:
    """Decode one key field, returning None for a key not produced by Debug."""
    if len(value) % 2 or _HEX_RE.fullmatch(value) is None:
        return None
    try:
        return bytes.fromhex(value).decode()
    except (UnicodeDecodeError, ValueError):
        return None


def _key(side: _BoundarySide, kind: _BoundaryKind, token: str, label: str) -> str:
    return f"{_KEY_PREFIX}:{side}:{kind}:{_encode(token)}:{_encode(label)}"


def _parse_occurrence(placeholder_id: str, placeholder_html: str, html: str) -> _Occurrence | None:
    """Read a serialized Debug placeholder ID and locate its exact marker."""
    fields = placeholder_id.split(":")
    if len(fields) != 7 or fields[0] != _KEY_PREFIX:
        return None
    _, side, kind, token_hex, label_hex, counter, nonce = fields
    if (
        side not in ("open", "close")
        or kind not in ("component", "slot")
        or not counter.isdecimal()
        or len(nonce) != 32
        or _HEX_RE.fullmatch(nonce) is None
    ):
        return None
    if _decode(token_hex) is None or _decode(label_hex) is None:
        return None
    position = html.find(placeholder_html)
    if position < 0:
        return None
    return _Occurrence(
        boundary_id=(cast("_BoundaryKind", kind), token_hex, label_hex),
        side=cast("_BoundarySide", side),
        placeholder_html=placeholder_html,
        position=position,
    )


def _open_wrapper(kind: _BoundaryKind, label_hex: str) -> str:
    label = _decode(label_hex)
    if label is None:  # Defensive: parsing already validated the field.
        return ""
    palette = _PALETTES[kind]
    escaped_label = escape_to_str(label)
    return (
        f'<div class="citry-debug citry-debug-{kind}" style="border: 1px solid {palette.border}">'
        f'<span class="citry-debug-label" style="font-weight: bold; color: {palette.text}"'
        f' aria-hidden="true">{escaped_label}: </span>'
    )


def _wrap_result(result: RenderPart, *, kind: _BoundaryKind, token: str, label: str) -> CitryRender:
    context = result.context if isinstance(result, CitryRender) else CitryContext()
    return CitryRender(
        parts=[
            Placeholder(_key("open", kind, token, label)),
            result,
            Placeholder(_key("close", kind, token, label)),
        ],
        context=context,
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
        if isinstance(ctx.render, CitryRender):
            wrapped = CitryRender(
                parts=[
                    Placeholder(_key("open", "component", ctx.component.id, label)),
                    *ctx.render.parts,
                    Placeholder(_key("close", "component", ctx.component.id, label)),
                ],
                context=ctx.render.context,
            )
        else:
            wrapped = _wrap_result(ctx.render, kind="component", token=ctx.component.id, label=label)
        wrapped.context.extra[_CACHE_ACTIVE_KEY] = True
        return wrapped

    def on_slot_rendered(self, ctx: OnSlotRenderedContext) -> CitryRender | None:
        config = cast("Debug.Config", getattr(ctx.component, self.name))
        if type(ctx.component).transparent or not config.highlight_slots:
            return None
        occurrence = config._next_slot_occurrence()
        token = f"{ctx.component.id}:{occurrence}"
        label = f"{type(ctx.component).__name__} - {ctx.slot_name}"
        wrapped = _wrap_result(ctx.result, kind="slot", token=token, label=label)
        wrapped.context.extra[_CACHE_ACTIVE_KEY] = True
        return wrapped

    def on_render_context_merge(self, ctx: OnRenderContextMergeContext) -> None:
        if ctx.child_context.extra.get(_CACHE_ACTIVE_KEY):
            ctx.parent_context.extra[_CACHE_ACTIVE_KEY] = True

    def _render_cache_participates(self, ctx: OnRenderCacheExportContext) -> bool:
        return bool(ctx.root_context.extra.get(_CACHE_ACTIVE_KEY))

    def on_serialize(self, ctx: OnSerializeContext) -> str:
        occurrences = [
            occurrence
            for placeholder_id, placeholder_html in ctx.placeholders.items()
            if (occurrence := _parse_occurrence(placeholder_id, placeholder_html, ctx.html)) is not None
        ]
        occurrences.sort(key=lambda occurrence: occurrence.position)

        # Pair only properly nested markers. An extension that ran after Debug
        # during rendering may have discarded or rearranged one side; such
        # remnants are removed below instead of producing malformed wrappers.
        stack: list[_Occurrence] = []
        pairs: list[tuple[_Occurrence, _Occurrence]] = []
        for occurrence in occurrences:
            if occurrence.side == "open":
                stack.append(occurrence)
            elif stack and stack[-1].boundary_id == occurrence.boundary_id:
                pairs.append((stack.pop(), occurrence))

        html = ctx.html
        for opening, closing in sorted(pairs, key=lambda pair: pair[0].position, reverse=True):
            open_at = html.find(opening.placeholder_html)
            close_at = html.find(closing.placeholder_html, open_at + len(opening.placeholder_html))
            if open_at < 0 or close_at < 0:
                continue
            body_start = open_at + len(opening.placeholder_html)
            body = html[body_start:close_at]
            kind, _, label_hex = opening.boundary_id
            omit_boundary = _DOCUMENT_ROOT_RE.match(body) is not None
            open_html = "" if omit_boundary else _open_wrapper(kind, label_hex)
            close_html = "" if omit_boundary else "</div>"
            html = html[:open_at] + open_html + body + close_html + html[close_at + len(closing.placeholder_html) :]

        # Remove every surviving Debug marker, including unmatched halves and
        # markers deliberately omitted around a full document.
        for occurrence in occurrences:
            html = html.replace(occurrence.placeholder_html, "", 1)
        return html


__all__ = ["Debug"]
