"""Execute eligible template fills without an unused fallback or generic call context."""

from __future__ import annotations

import ast
import inspect
import textwrap
from typing import Any

from citry import citry_render as renders
from citry import component_render as cr
from citry import nodes, ownership, slots

ORIGINAL = nodes.SlotNode.render
MAKE = nodes._make_body_slot
CONTENT = nodes._TemplateSlotContent
SLOT = slots.Slot
GRAPH = ownership.OwnershipGraph
CONTENT_METHODS = (CONTENT.__call__, CONTENT._render, CONTENT.bind_slot)
SLOT_METHODS = (SLOT.__init__, SLOT.__call__, SLOT.__getattribute__)
CONTEXT_TYPES = (slots.SlotData, slots.SlotContext)
CONTEXT_INITS = (slots.SlotData.__init__, slots.SlotContext.__init__)
GRAPH_METHODS = {
    name: getattr(GRAPH, name)
    for name in (
        "record_template_fill",
        "record_source_location",
        "_append_fill",
        "_next_order",
        "select_supply",
        "supplied_fill_id",
        "capture_slot_call",
    )
}
RECORDS = (ownership.SourceLocationRecord, ownership._SourceSite, ownership.LogicalFillRecord)
RECORD_NEWS = tuple(record.__new__ for record in RECORDS)
CAPTURE = ownership.capture_current_slot_call
COUNTS: dict[str, int] | None = None
OMITTED = object()


def eligible(node: Any, context: Any, fill: Any, name: Any) -> bool:
    """Check initial eligibility for omitting unused call-context values."""
    if type(fill) is not SLOT or type(fill.content_func) is not CONTENT:
        return False
    content = fill.content_func
    if content._fallback_var is not None or content._data_binding is not None:
        return False
    graph = context.ownership
    return not (
        type(graph) is not GRAPH
        or type(node.body) is not list
        or type(node.source) is not str
        or type(name) is not str
        or type(context.component).__getattribute__ is not object.__getattribute__
        or nodes._make_body_slot is not MAKE
        or nodes.Slot is not SLOT
        or nodes._TemplateSlotContent is not CONTENT
        or (CONTENT.__call__, CONTENT._render, CONTENT.bind_slot) != CONTENT_METHODS
        or (SLOT.__init__, SLOT.__call__, SLOT.__getattribute__) != SLOT_METHODS
        or (slots.SlotData, slots.SlotContext) != CONTEXT_TYPES
        or (slots.SlotData.__init__, slots.SlotContext.__init__) != CONTEXT_INITS
        or ownership.capture_current_slot_call is not CAPTURE
        or any(getattr(getattr(graph, key), "__func__", None) is not value for key, value in GRAPH_METHODS.items())
        or (ownership.SourceLocationRecord, ownership._SourceSite, ownership.LogicalFillRecord) != RECORDS
        or any(record.__new__ is not original for record, original in zip(RECORDS, RECORD_NEWS, strict=True))
        or graph._receiver_fill.get((context.component.id, name)) is None
    )


def prepare(node: Any, context: Any, fill: Any, name: str, location: Any, data: Any) -> Any:
    """Capture the same fallback history before an eligible supplied fill executes."""
    if type(data) is not dict or not eligible(node, context, fill, name):
        return nodes._make_body_slot(
            node.body,
            context,
            type(context.component).__name__,
            name,
            None,
            None,
            node.position,
            source=node.source,
            kind=nodes.LogicalFillKind.FALLBACK,
            fallback_slot_site_location_id=location,
        )
    graph = context.ownership
    component = context.component
    source_id = graph.record_source_location(
        context, kind=ownership.SourceLocationKind.FALLBACK_FILL, source=node.source, position=node.position
    )
    graph._append_fill(
        kind=ownership.LogicalFillKind.FALLBACK,
        slot_name=name,
        source_policy=ownership.SourcePolicy.TEMPLATE,
        lexical_owner_render_id=component.id,
        lexical_owner_class_id=component._citry_class_id,
        source_location_id=source_id,
        source_invocation_id=None,
        receiver_render_id=component.id,
        receiver_class_id=component._citry_class_id,
        fallback_slot_site_location_id=location,
    )
    if COUNTS is not None:
        COUNTS["fallbacks_omitted"] = COUNTS.get("fallbacks_omitted", 0) + 1
    return OMITTED


def invoke(fill: Any, data: Any, fallback: Any, provides: Any) -> Any:
    """Retain ordinary calls for observable fallbacks and custom content."""
    if fallback is not OMITTED:
        return fill(data, fallback=fallback, provides=provides)
    if COUNTS is not None:
        COUNTS["direct_calls"] = COUNTS.get("direct_calls", 0) + 1

    def render_content() -> Any:
        content = fill.content_func
        slot_ref = content._slot_ref
        if slot_ref is None or slot_ref() is None:
            raise RuntimeError("A template Slot content callable lost its owning Slot.")
        context = content._context
        effective_provides = context.provides
        if provides is not None and provides is not effective_provides:
            effective_provides = {**effective_provides, **provides} if effective_provides else provides
        if effective_provides is not context.provides:
            render_context = nodes.CitryContext(
                variables={**context.variables},
                extra=context.extra,
                component=context.component,
                provides=effective_provides,
                sandboxed=context.sandboxed,
                ownership=context.ownership,
                template_record=context.template_record,
            )
        else:
            render_context = context
        result = nodes.CitryRender(parts=cr._render_body(content._body, render_context), context=render_context)
        return renders._render_value(result, provides=provides)

    return ownership.capture_current_slot_call(fill, render_content)


def transformed() -> Any:
    """Keep outlet selection, hooks and retirement from the production method."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(ORIGINAL)))
    function = tree.body[0]
    function.decorator_list = []
    changes = []

    class Rewrite(ast.NodeTransformer):
        def visit_Assign(self, node: ast.Assign) -> Any:
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "body_slot":
                changes.append("prepare")
                node.value = ast.parse(
                    "_prepare_template_fill(self, context, fill, name, slot_site_location_id, data)", mode="eval"
                ).body
            elif (
                isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "fill"
            ):
                changes.append("invoke")
                node.value = ast.parse(
                    "_invoke_template_fill(fill, data, body_slot, context.provides)", mode="eval"
                ).body
            return self.generic_visit(node)

    tree = ast.fix_missing_locations(Rewrite().visit(tree))
    if changes != ["prepare", "invoke"]:
        raise RuntimeError(f"The outlet method changed unexpectedly: {changes}")
    nodes.__dict__["_prepare_template_fill"] = prepare
    nodes.__dict__["_invoke_template_fill"] = invoke
    namespace = {}
    exec(compile(tree, "<template-fill-probe>", "exec"), nodes.__dict__, namespace)  # noqa: S102
    return namespace["render"]


CANDIDATE = transformed()


def install(changed: bool) -> None:
    """Select one complete outlet path before fixture construction."""
    nodes.SlotNode.render = CANDIDATE if changed else ORIGINAL
