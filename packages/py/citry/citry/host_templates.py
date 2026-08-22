"""Stable services for host-template extensions rendering compiled Citry bodies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from citry.citry_context import CitryContext
from citry.citry_render import CitryRender

if TYPE_CHECKING:
    from collections.abc import Mapping

    from citry.nodes import BodyItem, FillSink


_COMPILED_BODY_TOKEN = object()


@dataclass(frozen=True, slots=True, init=False)
class CompiledBody:
    """Opaque handle to one already-compiled independent Citry body list."""

    _items: tuple[BodyItem, ...]
    _engine_id: str
    _template_id: str

    def __init__(
        self,
        items: list[BodyItem],
        *,
        engine_id: str,
        template_id: str,
        _token: object | None = None,
    ) -> None:
        if _token is not _COMPILED_BODY_TOKEN:
            raise TypeError("CompiledBody handles are created by a foreign compiled-hook context.")
        object.__setattr__(self, "_items", tuple(items))
        object.__setattr__(self, "_engine_id", engine_id)
        object.__setattr__(self, "_template_id", template_id)

    @classmethod
    def _from_items(
        cls,
        items: list[BodyItem],
        *,
        engine_id: str,
        template_id: str,
    ) -> CompiledBody:
        return cls(
            items,
            engine_id=engine_id,
            template_id=template_id,
            _token=_COMPILED_BODY_TOKEN,
        )


def _validate_context(body: CompiledBody, context: CitryContext) -> None:
    component = context.component
    if component is None or component.citry.engine_id != body._engine_id:
        raise ValueError("CompiledBody belongs to a different Citry instance.")
    template = context.template_record
    if template is None or template.template_id != body._template_id:
        active_id = template.template_id if template is not None else None
        raise ValueError(
            "CompiledBody belongs to a different active template record "
            f"(body={body._template_id!r}, active={active_id!r})."
        )


def render_compiled_body(
    body: CompiledBody,
    context: CitryContext,
    *,
    variables_overlay: Mapping[str, Any] | None = None,
) -> CitryRender:
    """Render a protected compiled body with a live host-variable overlay."""
    from citry.component_render import _render_body, _settle_render  # noqa: PLC0415

    if not isinstance(body, CompiledBody):
        raise TypeError("render_compiled_body() requires a CompiledBody handle.")
    _validate_context(body, context)
    variables = dict(context.variables)
    if variables_overlay is not None:
        variables.update(variables_overlay)
    child_context = CitryContext(
        variables=variables,
        extra=context.extra,
        component=context.component,
        provides=context.provides,
        sandboxed=context.sandboxed,
        ownership=context.ownership,
        template_record=context.template_record,
    )
    parts = _render_body(body._items, child_context)
    return _settle_render(CitryRender(parts=parts, context=child_context), finalize_root=False)


def collect_compiled_body_fills(
    body: CompiledBody,
    context: CitryContext,
    sink: FillSink,
    *,
    variables_overlay: Mapping[str, Any] | None = None,
) -> None:
    """Collect fills from a host-selected compiled body against a live overlay."""
    from citry.nodes import collect_fills_from_body  # noqa: PLC0415

    if not isinstance(body, CompiledBody):
        raise TypeError("collect_compiled_body_fills() requires a CompiledBody handle.")
    _validate_context(body, context)
    variables = dict(context.variables)
    if variables_overlay is not None:
        variables.update(variables_overlay)
    child_context = CitryContext(
        variables=variables,
        extra=context.extra,
        component=context.component,
        provides=context.provides,
        sandboxed=context.sandboxed,
        ownership=context.ownership,
        template_record=context.template_record,
    )
    collect_fills_from_body(body._items, child_context, sink)
