# ruff: noqa: ANN001, ANN202, ARG002, S101, T201
"""
Trace the server identity that a component-first client model would need.

This is research code. It patches Python runtime functions only inside one
context manager, restores them before returning, and never changes Citry's
production modules.

Run from the repository root:

    uv run python \
      docs/design/alpinejs/component_first_server_ownership_harness.py

Pass ``--full`` to print the complete baseline and prototype records.
"""

from __future__ import annotations

import argparse
import json
import re
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

from citry import Citry, CitryContext, CitryRender, Component, Extension, Slot, component_render, nodes
from citry.util.html import Markup

if TYPE_CHECKING:
    from collections.abc import Iterator


_CID_RE = re.compile(r'\bdata-cid-([^\s=]+)=""')
_START_RE = re.compile(r"<!--citry-research-region-start:([^>]+)-->")
_TAG_RE = re.compile(r"<([A-Za-z][^\s/>]*)([^>]*)>")


def _owner(context: CitryContext) -> tuple[str | None, str | None]:
    component = context.component
    if component is None:
        return None, None
    return component.id, type(component).__name__


def _part_tree(part: Any) -> Any:
    if not isinstance(part, CitryRender):
        text = str(part)
        return {"type": type(part).__name__, "text": text if len(text) <= 100 else f"{text[:97]}..."}
    owner_id, owner_class = _owner(part.context)
    return {
        "type": "CitryRender",
        "ownerRenderId": owner_id,
        "ownerClass": owner_class,
        "isComponentRoot": part.is_component_root,
        "parts": [_part_tree(child) for child in part.parts],
    }


def _marker_groups(html: str) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for index, match in enumerate(_TAG_RE.finditer(html)):
        cids = _CID_RE.findall(match.group(2))
        if cids:
            groups.append({"elementIndex": index, "tag": match.group(1), "renderIds": cids})
    return groups


class OwnershipTrace:
    """Research-side records captured before current runtime objects flatten them."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.components: list[dict[str, Any]] = []
        self.invocations: list[dict[str, Any]] = []
        self.logical_fills: list[dict[str, Any]] = []
        self.source_locations: list[dict[str, Any]] = []
        self.gaps: list[dict[str, Any]] = []
        self.root_element_object_id: int | None = None

        self._call_by_element: dict[int, dict[str, Any]] = {}
        self._fill_by_slot: dict[int, dict[str, Any]] = {}
        self._external_fill_by_supply: dict[tuple[int, str | None], dict[str, Any]] = {}
        self._invocation_by_wrapper: dict[int, dict[str, Any]] = {}
        self._slot_object_tokens: dict[int, str] = {}
        self._invocation_by_region: dict[str, dict[str, Any]] = {}
        self._slot_creation: ContextVar[dict[str, Any] | None] = ContextVar(
            "component_first_slot_creation",
            default=None,
        )
        self._slot_site: ContextVar[dict[str, Any] | None] = ContextVar(
            "component_first_slot_site",
            default=None,
        )
        self._active_region: ContextVar[str | None] = ContextVar(
            "component_first_active_region",
            default=None,
        )

    def _next_id(self, prefix: str, collection: list[dict[str, Any]]) -> str:
        return f"{prefix}{len(collection) + 1}"

    def source_location(
        self,
        *,
        kind: str,
        writer_id: str | None,
        writer_class: str | None,
        source: str | None,
        position: tuple[int, int] | None,
    ) -> str | None:
        if writer_id is None or position is None:
            return None
        start, end = position
        record = {
            "sourceLocationId": self._next_id("loc", self.source_locations),
            "kind": kind,
            "writerRenderId": writer_id,
            "writerClass": writer_class,
            "position": [start, end],
            "snippet": source[start:end] if source is not None else None,
        }
        self.source_locations.append(record)
        return record["sourceLocationId"]

    def record_component_call(self, node, context: CitryContext, deferred) -> None:
        writer_id, writer_class = _owner(context)
        location_id = self.source_location(
            kind="component-call",
            writer_id=writer_id,
            writer_class=writer_class,
            source=node.source if isinstance(node.source, str) else None,
            position=node.position,
        )
        record = {
            "callId": self._next_id("call", self.calls),
            "sourceRenderId": writer_id,
            "sourceClass": writer_class,
            "targetRenderId": None,
            "targetClass": deferred.element.comp_cls.__name__,
            "sourceLocationId": location_id,
            "physicalParentRegionId": self._active_region.get(),
        }
        self.calls.append(record)
        self._call_by_element[id(deferred.element)] = record

    def bind_component(self, element, parent, render: CitryRender) -> None:
        component = render.context.component
        assert component is not None
        call = self._call_by_element.get(id(element))
        if call is not None:
            call["targetRenderId"] = component.id
        is_top_root = id(element) == self.root_element_object_id
        record = {
            "renderId": component.id,
            "class": type(component).__name__,
            "isTopRoot": is_top_root,
            "isTransparent": type(component).transparent,
            "callInitEdge": (
                {
                    "callId": call["callId"],
                    "parentRenderId": component.parent.id if component.parent is not None else None,
                }
                if call is not None
                else None
            ),
            "componentParentRenderId": component.parent.id if component.parent is not None else None,
            "renderOneParentArgument": parent.id if parent is not None else None,
            "elementRootIndices": [],
        }
        self.components.append(record)
        if not is_top_root and call is None:
            self.gaps.append(
                {
                    "kind": "missing-call-identity",
                    "renderId": component.id,
                    "class": type(component).__name__,
                    "detail": (
                        "The component was rendered from a Python CitryElement or expression path. "
                        "No ComponentNode call record or source span reached _render_one."
                    ),
                }
            )

    def register_body_slot(
        self,
        slot: Slot,
        context: CitryContext,
        component_name: str,
        slot_name: str,
        position: tuple[int, int] | None,
    ) -> dict[str, Any]:
        creation = self._slot_creation.get() or {}
        writer_id, writer_class = _owner(context)
        kind = creation.get("kind", "template-slot-unknown")
        source = creation.get("source")
        location_id = self.source_location(
            kind=kind,
            writer_id=writer_id,
            writer_class=writer_class,
            source=source if isinstance(source, str) else None,
            position=position,
        )
        slot_object_id = self._slot_object_tokens.setdefault(
            id(slot),
            f"slot-object-{len(self._slot_object_tokens) + 1}",
        )
        record = {
            "logicalFillId": self._next_id("fill", self.logical_fills),
            "kind": kind,
            "slotName": slot_name,
            "debugReceiverName": component_name,
            "writerRenderId": writer_id,
            "writerClass": writer_class,
            "sourceLocationId": location_id,
            "sourcePosition": list(position) if position is not None else None,
            "slotContentObjectId": slot_object_id,
            "invocationRegionIds": [],
            "_writerContext": context,
        }
        self.logical_fills.append(record)
        self._fill_by_slot[id(slot)] = record
        return record

    def external_slot(self, slot: Slot, receiver_id: str | None) -> dict[str, Any]:
        supply_key = (id(slot), receiver_id)
        existing = self._external_fill_by_supply.get(supply_key)
        if existing is not None:
            return existing
        slot_object_id = self._slot_object_tokens.setdefault(
            id(slot),
            f"slot-object-{len(self._slot_object_tokens) + 1}",
        )
        record = {
            "logicalFillId": self._next_id("fill", self.logical_fills),
            "kind": "python-slot",
            "slotName": slot.slot_name,
            "debugReceiverName": slot.component_name,
            "writerRenderId": None,
            "writerClass": None,
            "sourceLocationId": None,
            "sourcePosition": list(slot.source_position) if slot.source_position is not None else None,
            "slotContentObjectId": slot_object_id,
            "invocationRegionIds": [],
            "_writerContext": None,
        }
        self.logical_fills.append(record)
        self._external_fill_by_supply[supply_key] = record
        self.gaps.append(
            {
                "kind": "missing-python-slot-source",
                "logicalFillId": record["logicalFillId"],
                "detail": (
                    "A normalized Python Slot retains optional construction metadata, but no rendered "
                    "component or slot-supply call location."
                ),
            }
        )
        return record

    def invoke_body_slot(self, slot: Slot, original_content, slot_context) -> CitryRender:
        logical = self._fill_by_slot[id(slot)]
        return self._invoke(logical, original_content, slot_context)

    def _invoke(self, logical: dict[str, Any], content, slot_context) -> CitryRender:
        site = self._slot_site.get()
        receiver_context = site.get("context") if site is not None else None
        receiver_id, receiver_class = _owner(receiver_context) if receiver_context is not None else (None, None)
        parent_region_id = self._active_region.get()
        parent_invocation = self._invocation_by_region.get(parent_region_id) if parent_region_id is not None else None
        from_owner_id = parent_invocation["lexicalOwnerRenderId"] if parent_invocation is not None else receiver_id

        region_id = self._next_id("region", self.invocations)
        invocation = {
            "physicalRegionId": region_id,
            "logicalFillId": logical["logicalFillId"],
            "receiverRenderId": receiver_id,
            "receiverClass": receiver_class,
            "slotSitePosition": site.get("position") if site is not None else None,
            "physicalParentRegionId": parent_region_id,
            "transitionFromRenderId": from_owner_id,
            "lexicalOwnerRenderId": logical["writerRenderId"],
            "sourceLocationId": logical["sourceLocationId"],
            "resultOwnerRenderId": None,
        }
        self.invocations.append(invocation)
        self._invocation_by_region[region_id] = invocation
        logical["invocationRegionIds"].append(region_id)

        token = self._active_region.set(region_id)
        try:
            result = content(slot_context)
        finally:
            self._active_region.reset(token)

        if isinstance(result, CitryRender):
            result_owner_id, _ = _owner(result.context)
            wrapper_context = result.context
        else:
            result_owner_id = None
            wrapper_context = logical["_writerContext"] or receiver_context
        invocation["resultOwnerRenderId"] = result_owner_id
        if wrapper_context is None:
            wrapper_context = CitryContext()
        wrapper = CitryRender(
            parts=[
                f"<!--citry-research-region-start:{region_id}-->",
                result,
                f"<!--citry-research-region-end:{region_id}-->",
            ],
            context=wrapper_context,
        )
        self._invocation_by_wrapper[id(wrapper)] = invocation
        return wrapper

    def observe_slot_result(self, ctx) -> CitryRender | None:
        if isinstance(ctx.result, CitryRender) and id(ctx.result) in self._invocation_by_wrapper:
            return None
        logical = self.external_slot(ctx.slot, ctx.component.id)

        def return_result(_slot_context):
            return ctx.result

        return self._invoke(logical, return_result, None)

    def finish(self, html: str) -> dict[str, Any]:
        marker_groups = _marker_groups(html)
        for component in self.components:
            component["elementRootIndices"] = [
                group["elementIndex"] for group in marker_groups if component["renderId"] in group["renderIds"]
            ]
        for logical in self.logical_fills:
            logical.pop("_writerContext", None)
        for invocation in self.invocations:
            region_id = invocation["physicalRegionId"]
            start = f"<!--citry-research-region-start:{region_id}-->"
            end = f"<!--citry-research-region-end:{region_id}-->"
            assert html.count(start) == 1
            assert html.count(end) == 1
            assert html.index(start) < html.index(end)
        return {
            "htmlWithResearchCaps": html,
            "componentInstances": self.components,
            "callEdges": self.calls,
            "sourceLocations": self.source_locations,
            "logicalFills": self.logical_fills,
            "physicalRegionsAndTransitions": self.invocations,
            "elementMarkerGroups": marker_groups,
            "provenGaps": self.gaps,
        }

    def extension_class(self) -> type[Extension]:
        trace = self

        class ComponentFirstServerTrace(Extension):
            name = "component_first_server_trace"

            def on_slot_rendered(self, ctx):
                return trace.observe_slot_result(ctx)

        return ComponentFirstServerTrace

    @contextmanager
    def patches(self) -> Iterator[None]:
        original_component_node_render = nodes.ComponentNode.render
        original_collect_slots = nodes.ComponentNode._collect_slots
        original_make_body_slot = nodes._make_body_slot
        original_slot_node_render = nodes.SlotNode.render
        original_render_one = component_render._render_one
        trace = self

        def traced_component_node_render(node, context):
            deferred = original_component_node_render(node, context)
            trace.record_component_call(node, context, deferred)
            return deferred

        def traced_collect_slots(node, context):
            state = {
                "kind": "named-fill" if node.contains_fills else "implicit-fill",
                "source": node.source,
            }
            token = trace._slot_creation.set(state)
            try:
                return original_collect_slots(node, context)
            finally:
                trace._slot_creation.reset(token)

        def traced_make_body_slot(
            body,
            context,
            component_name,
            slot_name,
            data_var,
            fallback_var,
            position,
            **ownership_kwargs: Any,
        ):
            slot = original_make_body_slot(
                body,
                context,
                component_name,
                slot_name,
                data_var,
                fallback_var,
                position,
                **ownership_kwargs,
            )
            trace.register_body_slot(slot, context, component_name, slot_name, position)
            original_content = slot.content_func

            def traced_content(slot_context):
                return trace.invoke_body_slot(slot, original_content, slot_context)

            slot.content_func = traced_content
            return slot

        def traced_slot_node_render(node, context):
            site_token = trace._slot_site.set(
                {
                    "context": context,
                    "position": list(node.position),
                    "source": node.source,
                }
            )
            creation_token = trace._slot_creation.set({"kind": "fallback", "source": node.source})
            try:
                return original_slot_node_render(node, context)
            finally:
                trace._slot_creation.reset(creation_token)
                trace._slot_site.reset(site_token)

        def traced_render_one(element, parent=None, provides=None):
            initial = original_render_one(element, parent, provides)
            trace.bind_component(element, parent, initial.render)
            return initial

        nodes.ComponentNode.render = traced_component_node_render
        nodes.ComponentNode._collect_slots = traced_collect_slots
        nodes._make_body_slot = traced_make_body_slot
        nodes.SlotNode.render = traced_slot_node_render
        component_render._render_one = traced_render_one
        try:
            yield
        finally:
            component_render._render_one = original_render_one
            nodes.SlotNode.render = original_slot_node_render
            nodes._make_body_slot = original_make_body_slot
            nodes.ComponentNode._collect_slots = original_collect_slots
            nodes.ComponentNode.render = original_component_node_render


def _build_fixture(name: str, extension: type[Extension] | None = None):
    c = Citry(extensions=[extension] if extension is not None else [])

    if name == "ordinary_fill":

        class Outlet(Component):
            citry = c
            template = """
              <section><c-slot name="body" /></section>
            """

        class Page(Component):
            citry = c
            template = """
              <c-outlet>
                <c-fill name="body"><button>ordinary</button></c-fill>
              </c-outlet>
            """

        return Page()

    if name == "implicit_fill":

        class Outlet(Component):
            citry = c
            template = """
              <main><c-slot /></main>
            """

        class Page(Component):
            citry = c
            template = """
              <c-outlet><em>implicit</em></c-outlet>
            """

        return Page()

    if name == "fallback_inside_fill":

        class Card(Component):
            citry = c
            template = """
              <c-slot name="body"><i>child fallback</i></c-slot>
            """

        class Page(Component):
            citry = c
            template = """
              <c-card>
                <c-fill name="body" fallback="fb">
                  <b>parent before {{ fb }} parent after</b>
                </c-fill>
              </c-card>
            """

        return Page()

    if name == "component_inside_fill":

        class Leaf(Component):
            citry = c
            template = """
              <strong>leaf</strong>
            """

        class Host(Component):
            citry = c
            template = """
              <div><c-slot /></div>
            """

        class Page(Component):
            citry = c
            template = """
              <c-host><c-leaf /></c-host>
            """

        return Page()

    if name == "multi_root_fill":

        class Outlet(Component):
            citry = c
            template = """
              <c-slot />
            """

        class Page(Component):
            citry = c
            template = """
              <c-outlet><span>A</span>text<b>B</b></c-outlet>
            """

        return Page()

    if name == "text_only_fill":

        class Outlet(Component):
            citry = c
            template = """
              <c-slot />
            """

        class Page(Component):
            citry = c
            template = """
              <c-outlet>plain text</c-outlet>
            """

        return Page()

    if name == "empty_fill":

        class Outlet(Component):
            citry = c
            template = """
              <c-slot />
            """

        class Page(Component):
            citry = c
            template = """
              <c-outlet><c-fill name="default" /></c-outlet>
            """

        return Page()

    if name == "reused_python_slot":
        reusable = Slot(
            Markup('<small class="reused">python</small>'),
            component_name="Outlet",
            slot_name="default",
        )

        class Outlet(Component):
            citry = c
            template = """
              <div><c-slot /></div>
            """

        class Page(Component):
            citry = c
            template = """
              <section>{{ left }}{{ right }}</section>
            """

            def template_data(self, kwargs, slots):
                return {
                    "left": Outlet(slots={"default": reusable}),
                    "right": Outlet(slots={"default": reusable}),
                }

        return Page()

    if name == "mirrored_outlet":

        class Mirror(Component):
            citry = c
            template = """
              <aside><c-slot name="body" /></aside>
              <aside><c-slot name="body" /></aside>
            """

        class Page(Component):
            citry = c
            template = """
              <c-mirror>
                <c-fill name="body"><mark>mirror</mark></c-fill>
              </c-mirror>
            """

        return Page()

    if name == "dynamic_component":

        class Card(Component):
            citry = c
            template = """
              <article><c-slot /></article>
            """

        class Page(Component):
            citry = c
            template = """
              <c-component c-is="target"><u>dynamic fill</u></c-component>
            """

            def template_data(self, kwargs, slots):
                return {"target": "card"}

        return Page()

    msg = f"Unknown fixture {name!r}"
    raise ValueError(msg)


SCENARIOS = (
    "ordinary_fill",
    "implicit_fill",
    "fallback_inside_fill",
    "component_inside_fill",
    "multi_root_fill",
    "text_only_fill",
    "empty_fill",
    "reused_python_slot",
    "mirrored_outlet",
    "dynamic_component",
)


def _baseline(name: str) -> dict[str, Any]:
    element = _build_fixture(name)
    render = element.render()
    html = render.serialize(deps_strategy="ignore")
    assert "citry-research-region" not in html
    return {
        "html": html,
        "renderTreeBeforeSerialization": _part_tree(render),
        "elementMarkerGroups": _marker_groups(html),
    }


def _prototype(name: str) -> dict[str, Any]:
    trace = OwnershipTrace()
    element = _build_fixture(name, trace.extension_class())
    trace.root_element_object_id = id(element)
    with trace.patches():
        render = element.render()
    html = render.serialize(deps_strategy="ignore")
    evidence = trace.finish(html)
    evidence["renderTreeBeforeSerialization"] = _part_tree(render)
    return evidence


def _assert_findings(evidence: dict[str, Any]) -> None:
    ordinary = evidence["ordinary_fill"]["prototype"]
    assert [fill["kind"] for fill in ordinary["logicalFills"] if fill["invocationRegionIds"]] == ["named-fill"]
    assert (
        ordinary["physicalRegionsAndTransitions"][0]["transitionFromRenderId"]
        != ordinary["physicalRegionsAndTransitions"][0]["lexicalOwnerRenderId"]
    )

    implicit = evidence["implicit_fill"]["prototype"]
    assert [fill["kind"] for fill in implicit["logicalFills"] if fill["invocationRegionIds"]] == ["implicit-fill"]

    fallback = evidence["fallback_inside_fill"]["prototype"]
    invoked_fills = [fill for fill in fallback["logicalFills"] if fill["invocationRegionIds"]]
    assert {fill["kind"] for fill in invoked_fills} == {"named-fill", "fallback"}
    nested = next(region for region in fallback["physicalRegionsAndTransitions"] if region["physicalParentRegionId"])
    outer = next(
        region
        for region in fallback["physicalRegionsAndTransitions"]
        if region["physicalRegionId"] == nested["physicalParentRegionId"]
    )
    assert nested["transitionFromRenderId"] == outer["lexicalOwnerRenderId"]
    assert nested["lexicalOwnerRenderId"] == outer["receiverRenderId"]

    inside = evidence["component_inside_fill"]["prototype"]
    leaf = next(component for component in inside["componentInstances"] if component["class"] == "Leaf")
    leaf_call = next(call for call in inside["callEdges"] if call["targetRenderId"] == leaf["renderId"])
    assert leaf_call["physicalParentRegionId"] is not None
    assert leaf["componentParentRenderId"] == leaf_call["sourceRenderId"]

    multi = evidence["multi_root_fill"]
    assert len(multi["baseline"]["elementMarkerGroups"]) == 2
    assert len(multi["prototype"]["physicalRegionsAndTransitions"]) == 1

    text = evidence["text_only_fill"]
    assert not text["baseline"]["elementMarkerGroups"]
    assert len(text["prototype"]["physicalRegionsAndTransitions"]) == 1

    empty = evidence["empty_fill"]
    assert empty["baseline"]["html"].strip() == ""
    assert len(empty["prototype"]["physicalRegionsAndTransitions"]) == 1

    reused = evidence["reused_python_slot"]["prototype"]
    python_fills = [fill for fill in reused["logicalFills"] if fill["kind"] == "python-slot"]
    assert len(python_fills) == 2
    assert {fill["slotContentObjectId"] for fill in python_fills} == {python_fills[0]["slotContentObjectId"]}
    assert all(len(fill["invocationRegionIds"]) == 1 for fill in python_fills)
    assert all(fill["sourceLocationId"] is None for fill in python_fills)

    mirror = evidence["mirrored_outlet"]["prototype"]
    mirror_fill = next(fill for fill in mirror["logicalFills"] if fill["kind"] == "named-fill")
    assert len(mirror_fill["invocationRegionIds"]) == 2
    assert len(set(mirror_fill["invocationRegionIds"])) == 2

    dynamic = evidence["dynamic_component"]["prototype"]
    card = next(component for component in dynamic["componentInstances"] if component["class"] == "Card")
    assert card["callInitEdge"] is None
    assert card["componentParentRenderId"] is None
    assert any(
        gap["kind"] == "missing-call-identity" and gap["renderId"] == card["renderId"] for gap in dynamic["provenGaps"]
    )


def _summary(evidence: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, case in evidence.items():
        prototype = case["prototype"]
        result[name] = {
            "baselineHtml": case["baseline"]["html"],
            "componentCount": len(prototype["componentInstances"]),
            "callEdgeCount": len(prototype["callEdges"]),
            "logicalFillKinds": [fill["kind"] for fill in prototype["logicalFills"] if fill["invocationRegionIds"]],
            "physicalRegionCount": len(prototype["physicalRegionsAndTransitions"]),
            "gapKinds": [gap["kind"] for gap in prototype["provenGaps"]],
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Print complete trace records")
    args = parser.parse_args()

    evidence = {
        name: {
            "baseline": _baseline(name),
            "prototype": _prototype(name),
        }
        for name in SCENARIOS
    }
    _assert_findings(evidence)
    print(json.dumps(evidence if args.full else _summary(evidence), indent=2, sort_keys=True))
    print("component-first server ownership harness: all assertions passed")


if __name__ == "__main__":
    main()
