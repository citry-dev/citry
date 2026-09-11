"""Render explicitly simple templates with their surrounding component as owner."""

from __future__ import annotations

from dataclasses import dataclass
from inspect import isasyncgen, isawaitable, isgenerator
from typing import TYPE_CHECKING, Any, cast

from citry._pure import pure_body_lookup, store_pure_body
from citry.citry_context import CitryContext
from citry.citry_element import CitryElement
from citry.citry_render import CitryRender, DeferredComponent, _render_slot_value, _render_value
from citry.constness import (
    _const_mapping,
    _construct_data_schema,
    _merge_const_mappings,
    _restore_const_identities,
)
from citry.nodes import (
    ComponentNode,
    ElementAttrsNode,
    ElementKeyNode,
    ExprHtmlAttr,
    ExprNode,
    FillNode,
    ForNode,
    IfNode,
    SlotNode,
    StaticHtmlAttr,
    TemplateHtmlAttr,
    TemplateNode,
)
from citry.slots import Slot, normalize_slot_fills
from citry.util.misc import to_dict

if TYPE_CHECKING:
    from citry._simple_declarations import SimpleDeclaration
    from citry.citry_render import RenderPart
    from citry.citry_template import CitryTemplate
    from citry.component import Component
    from citry.nodes import BodyItem
    from citry.slots import SlotFunc


class SimpleRender(CitryRender):
    """Keep an interior simple result separate from its owner's finalization."""

    __slots__ = ()


class SimpleElement(CitryElement):
    """Carry the actual insertion context through deferred scheduling."""

    __slots__ = ("caller", "content")

    def __init__(self, element: CitryElement, caller: CitryContext, content: SimpleContent | None) -> None:
        super().__init__(element.comp_cls, element.kwargs, ownership_graph=caller.ownership)
        self.caller = caller
        self.content = content


@dataclass(slots=True)
class SimpleContent:
    """Retain the source context or Python slot supplying default content."""

    caller: CitryContext
    body: list[BodyItem] | None = None
    slot: Slot | None = None

    def render(self, provides: dict[str, Any] | None = None) -> RenderPart:
        # component_render imports this module only at simple entry points;
        # importing it here avoids the nodes/render pipeline import cycle.
        from citry.component_render import _render_body  # noqa: PLC0415

        context = self.caller
        if provides is not None and provides is not context.provides:
            context = CitryContext(
                variables=context.variables,
                extra=context.extra,
                component=context.component,
                provides={**context.provides, **provides},
                sandboxed=context.sandboxed,
                ownership=context.ownership,
                template_record=context.template_record,
                _simple_scope=context._simple_scope,
            )
        if self.body is not None:
            return CitryRender(_render_body(self.body, context), context)
        if self.slot is None:
            return ""
        return _render_slot_value(self.slot, None, None, context)

    def as_slot(self) -> Slot:
        """Expose default content as a lazy Slot that keeps the caller as owner."""
        # Internal content may already carry a physical-region wrapper; the
        # render-value dispatcher accepts it alongside ordinary slot results.
        callback = cast("SlotFunc[Any]", lambda context: self.render(context.provides))
        return Slot("", content_func=callback, slot_name="default")


@dataclass(frozen=True, slots=True)
class SimpleScope:
    """Select the default outlet belonging to this lexical simple template."""

    component_class: type[Component]
    content: SimpleContent | None


def prepare_simple_element(
    element: CitryElement,
    caller: CitryContext,
    *,
    body: list[BodyItem] | None = None,
) -> SimpleElement:
    """Check a simple call before it can record an independent component boundary."""
    name = element.comp_cls.__name__
    if (
        element.component_tag_client_bindings
        or element.element_morph_metadata is not None
        or element.ownership_invocation_id is not None
        or element.forward_ownership_invocation
    ):
        msg = (
            f"Component {name} uses simple=True; component bindings, range metadata"
            " and forwarded invocations are unsupported."
        )
        raise TypeError(msg)
    if caller.component is None:
        raise RuntimeError("A simple call requires an insertion owner.")
    if caller.component.citry is not element.comp_cls.citry:
        raise ValueError("A simple call and its insertion owner must belong to the same Citry instance.")
    content: SimpleContent | None = None
    if body is not None:
        if element.slots:
            raise TypeError("A simple call cannot combine a template body and Python slots.")
        if not all(isinstance(item, str) and not item.strip() for item in body):
            content = SimpleContent(caller, body=body)
    elif element.slots:
        if set(element.slots) != {"default"}:
            msg = f"Component {name} uses simple=True; only default content is supported."
            raise TypeError(msg)
        normalized = normalize_slot_fills(element.slots, component_name=name)
        if "default" in normalized:
            content = SimpleContent(caller, slot=normalized["default"])
    return SimpleElement(element, caller, content)


def simple_deferred(
    element: CitryElement, caller: CitryContext, *, body: list[BodyItem] | None = None
) -> DeferredComponent:
    """Queue a checked simple call at its current physical insertion region."""
    prepared = prepare_simple_element(element, caller, body=body)
    return DeferredComponent(
        prepared,
        cast("Component", caller.component),
        caller.provides,
        physical_parent_region_id=caller.ownership.current_region_id() if caller.ownership is not None else None,
    )


def _validate_body(body: list[BodyItem], cls: type[Component]) -> bool:
    """Check every authored branch and nested template before inputs prune any work."""
    from citry._i18n_directives import looks_like_i18n_binding  # noqa: PLC0415
    from citry.component_render import _compile_nested_template  # noqa: PLC0415

    pending: list[Any] = list(body)
    has_outlet = False
    while pending:
        item = pending.pop()
        kind = type(item)
        if kind in (str, ExprNode):
            continue
        if kind in (ExprHtmlAttr, StaticHtmlAttr, TemplateHtmlAttr) and looks_like_i18n_binding(
            item.key.removeprefix("c-")
        ):
            msg = f"Component {cls.__name__} uses simple=True; $c-tr bindings are unsupported."
            raise TypeError(msg)
        if kind in (ExprHtmlAttr, StaticHtmlAttr):
            continue
        if kind is SlotNode:
            if item.attrs or item.body or item.introduced_vars:
                msg = f"Component {cls.__name__} uses simple=True; only an empty default slot outlet is supported."
                raise TypeError(msg)
            has_outlet = True
        elif kind in (ComponentNode, FillNode):
            pending.extend(item.attrs)
            pending.extend(item.body)
        elif kind in (IfNode, ForNode):
            for branch in item.branches:
                pending.extend(branch[1])
                pending.extend(branch[2])
        elif kind is ElementAttrsNode:
            pending.extend(item.attrs)
        elif kind is ElementKeyNode:
            pending.append(item.attr)
        elif kind in (TemplateNode, TemplateHtmlAttr):
            if kind is TemplateHtmlAttr and item.foreign_spans:
                msg = f"Component {cls.__name__} uses simple=True; foreign template attributes are unsupported."
                raise TypeError(msg)
            source = item.expr if kind is TemplateNode else item.template
            if item._generator is None:
                item._generator = _compile_nested_template(source, cls.citry._tag_rules(), cls)
            pending.extend(item._generator())
        else:
            msg = f"Component {cls.__name__} uses simple=True; template node {kind.__name__} is unsupported."
            raise TypeError(msg)
    return has_outlet


def _prepared_template(cls: type[Component]) -> tuple[CitryTemplate | None, list[BodyItem], bool]:
    """Retain checked nodes only while their loaded template record is current."""
    from citry.component_render import _get_compiled_template  # noqa: PLC0415

    compiled = _get_compiled_template(cls)
    cached = cls.__dict__.get("_citry_simple_template")
    if cached is not None and cached[0] is compiled:
        return cached
    if compiled is None or compiled.generate is None:
        return None, [], False
    with compiled.compile_lock:
        cached = cls.__dict__.get("_citry_simple_template")
        if cached is not None and cached[0] is compiled:
            return cached
        extensions = cls.citry.extensions
        body = extensions.on_template_foreign_compiled(
            cls,
            compiled.generate(),
            provider_metadata=compiled.foreign_provider_metadata,
            template_id=compiled.template_id,
            origin=compiled.origin,
            template_kind=compiled.kind,
        )
        body = extensions.on_template_compiled(
            cls,
            body,
            template_id=compiled.template_id,
            origin=compiled.origin,
            template_kind=compiled.kind,
        )
        cached = compiled, body, _validate_body(body, cls)
        cls._citry_simple_template = cached
        return cached


def render_simple(element: SimpleElement) -> SimpleRender:
    """Run current inputs through a checked template without creating its own instance."""
    from citry.component_render import (  # noqa: PLC0415
        _normalize_data,
        _render_and_capture_pure_body,
        _render_body,
        _render_globals,
        _replay_pure_body,
    )

    cls = element.comp_cls
    declaration: SimpleDeclaration = cls._citry_simple_declaration
    compiled, body, has_outlet = _prepared_template(cls)
    element_kwargs = to_dict(element.kwargs)
    raw_kwargs = _const_mapping(element_kwargs, preserve=element_kwargs)
    const_candidates = dict(raw_kwargs._const_values)
    kwargs, kwargs_const = _construct_data_schema(
        raw_kwargs,
        declaration.kwargs_schema,
        provenance_only=True,
    )
    const_candidates.update(kwargs_const._const_values)
    _restore_const_identities(kwargs_const, const_candidates)
    raw_slots = {"default": element.content.as_slot()} if element.content is not None else {}
    # Template hooks and kwargs adapters can execute Python. Check after them,
    # immediately before calling the constrained slot constructor.
    declaration.check_slots_unchanged()
    slots = declaration.slots_schema(**raw_slots) if declaration.slots_schema is not None else raw_slots
    data = declaration.callback(kwargs, slots) if declaration.callback is not None else kwargs
    if isawaitable(data) or isgenerator(data) or isasyncgen(data):
        raise TypeError(f"Component {cls.__name__} uses simple=True; template_data must return synchronous data.")
    data = _normalize_data(
        data,
        declaration.data_schema,
        preserve=kwargs_const if declaration.callback is None else None,
    )
    _restore_const_identities(data, const_candidates)
    if cls.citry.template_globals or _render_globals.get():
        data = _merge_const_mappings(
            _const_mapping(cls.citry.template_globals),
            _const_mapping(_render_globals.get() or {}),
            data,
        )
    caller = element.caller
    context = CitryContext(
        variables=data,
        component=caller.component,
        provides=caller.provides,
        ownership=caller.ownership,
        sandboxed=caller.sandboxed,
        template_record=compiled,
        _simple_scope=SimpleScope(cls, element.content),
    )
    # Default content is not part of the data key. In particular an absent
    # outlet emits text, which an ordinary pure capture would incorrectly keep
    # for a later filled invocation. Keep outlet-bearing bodies live.
    lookup = (
        pure_body_lookup(cls, body, data, compiled.used_vars)
        if cls.pure and compiled is not None and not has_outlet
        else None
    )
    if lookup is not None and lookup[1] is not None:
        parts = _replay_pure_body(lookup[1], context)
    elif lookup is not None:
        parts, plan, cached_count = _render_and_capture_pure_body(body, context, cast("Component", caller.component))
        if cached_count and not context._error_tainted and not context.extra:
            store_pure_body(lookup[0], plan)
    else:
        parts = _render_body(body, context)
    return SimpleRender(parts, context)


def render_simple_value(element: CitryElement, caller: CitryContext, provides: dict[str, Any] | None) -> CitryRender:
    """Settle an expression value at the ordinary immediate expression stage."""
    from citry.component_render import _render_one_traced, _settle_render  # noqa: PLC0415

    caller = caller._with_provides(provides)
    initial = _render_one_traced(prepare_simple_element(element, caller), caller.component, caller.provides)
    return _settle_render(initial.render)


def render_simple_outlet(context: CitryContext) -> RenderPart:
    """Insert content with its source variables and the provides active at this outlet."""
    scope = context._simple_scope
    if scope is None or scope.content is None:
        return ""
    part = scope.content.render(context.provides)
    component = cast("Component", context.component)
    return _render_value(part, provides=context.provides, citry=component.citry, context=context)
