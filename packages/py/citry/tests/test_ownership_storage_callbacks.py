"""Preserve ownership mutation order when user values run Python callbacks."""

import sys
from types import SimpleNamespace

import pytest

from citry import Citry, Component, Slot, ownership
from citry.util.id import validate_render_id


@pytest.fixture(params=[False, True], ids=["python", "native"])
def graph(request, monkeypatch):
    if request.param and ownership._native_ownership is None:
        pytest.skip("The installed core does not expose native ownership storage")
    if not request.param:
        monkeypatch.setattr(ownership, "_native_ownership", None)
    result = ownership.OwnershipGraph()
    if request.param:
        # These regressions exercise native rows before the callback changes storage.
        result._initialize_native_storage()
    return result


class _BoundComponent:
    transparent = False

    def __init__(self, render_id):
        self.id = validate_render_id(render_id)
        self._citry_class_id = "Child"


def _invocation(graph):
    context = SimpleNamespace(component=SimpleNamespace(id="owner", _citry_class_id="Owner"))
    return graph.record_component_invocation(
        context,
        authored_tag="child",
        target_class_id="Child",
        morph_key=None,
        morph_mode=None,
        source="x",
        position=(0, 1),
        client_bindings=(),
    )


def _bind(graph, invocation_id, render_id):
    graph.bind_instance(
        _BoundComponent(render_id),
        SimpleNamespace(ownership_invocation_id=invocation_id, forward_ownership_invocation=False),
    )


def _fill(graph, slot, *, owner="owner", receiver=None):
    fill_id = graph._append_fill(
        kind=ownership.LogicalFillKind.NAMED,
        slot_name="default",
        source_policy=ownership.SourcePolicy.TEMPLATE,
        lexical_owner_render_id=owner,
        lexical_owner_class_id="Owner",
        source_location_id=None,
        source_invocation_id=None,
        receiver_render_id=receiver,
        receiver_class_id=None,
    )
    graph._template_fill_by_slot_object[slot] = fill_id
    return fill_id


def test_id_hash_failure_keeps_queue_enqueued(graph):
    error = ValueError("ID hash failed")

    class RenderId(str):
        __slots__ = ()

        def __hash__(self):
            raise error

    invocation_id = _invocation(graph)
    before = graph.checkpoint()
    with pytest.raises(ValueError, match="ID hash failed") as caught:
        _bind(graph, invocation_id, RenderId("child"))

    assert caught.value is error
    snapshot = graph.snapshot()
    assert graph.checkpoint() == before
    assert snapshot.component_invocations[0].target_render_id == "child"
    assert snapshot.render_queue[0].state == ownership.QueueState.ENQUEUED
    assert snapshot.render_queue[0].target_render_id is None
    assert snapshot.render_queue[0].rendered_order is None
    assert snapshot.logical_instances == ()


def test_previous_custom_id_collision_keeps_later_queue_enqueued(graph):
    error = ValueError("Existing ID comparison failed")
    armed = False

    class RenderId(str):
        __slots__ = ()

        def __hash__(self):
            return hash("next")

        def __eq__(self, other):
            if armed:
                raise error
            return str.__eq__(self, other)

    first = _invocation(graph)
    _bind(graph, first, RenderId("previous"))
    second = _invocation(graph)
    before = graph.checkpoint()
    # An exact string can still invoke a previously stored key's comparison.
    armed = True
    with pytest.raises(ValueError, match="Existing ID comparison failed") as caught:
        _bind(graph, second, "next")

    assert caught.value is error
    snapshot = graph.snapshot()
    assert graph.checkpoint() == before
    assert snapshot.component_invocations[1].target_render_id == "next"
    assert snapshot.render_queue[1].state == ownership.QueueState.ENQUEUED
    assert snapshot.render_queue[1].target_render_id is None
    assert snapshot.render_queue[1].rendered_order is None
    assert len(snapshot.logical_instances) == 1


def test_source_comparison_replaces_the_saved_fill_after_callback(graph):
    class Owner(str):
        __slots__ = ()

        def __ne__(self, other):
            graph.retire_range(0, through_order=graph.checkpoint())
            return str.__ne__(self, other)

    invocation_id = _invocation(graph)
    slot = Slot("body")
    _fill(graph, slot, owner=Owner("owner"))
    before = graph.snapshot().logical_fills[0]
    graph.bind_template_fill_sources({"default": slot}, invocation_id)

    fill = graph.snapshot().logical_fills[0]
    assert before.source_invocation_id is None
    assert before.state == ownership.OwnershipState.ACTIVE
    assert fill.source_invocation_id == invocation_id
    assert fill.state == ownership.OwnershipState.ACTIVE


def test_receiver_comparison_replaces_the_saved_fill_after_callback(graph):
    class Receiver(str):
        __slots__ = ()

        __hash__ = str.__hash__

        def __eq__(self, other):
            graph.retire_range(0, through_order=graph.checkpoint())
            return str.__eq__(self, other)

    slot = Slot("body")
    _fill(graph, slot, receiver=Receiver("child"))
    component = _BoundComponent("child")
    component.raw_slots = {"default": slot}
    graph.bind_supplied_slots(component)

    fill = graph.snapshot().logical_fills[0]
    assert fill.receiver_render_id is component.id
    assert fill.receiver_class_id == "Child"
    assert fill.state == ownership.OwnershipState.ACTIVE


def test_result_getter_replaces_the_saved_region_after_callback(graph):
    slot = Slot("body")
    _fill(graph, slot)
    initial = graph.capture_slot_call(slot, lambda: "body")
    before = graph.snapshot().physical_regions[0]

    class Result:
        @property
        def context(self):
            graph.retire_range(0, through_order=graph.checkpoint())

    selected = Result()
    result = graph.rebind_slot_region(initial.region_id, selected)

    assert result.part is selected
    assert before.state == ownership.RegionState.CAPTURED
    region = graph.snapshot().physical_regions[0]
    assert region.state == ownership.RegionState.CAPTURED
    assert region.result_owner_render_id is None


@pytest.mark.usefixtures("graph")
def test_stable_component_id_getter_replay_keeps_binding_visible():
    c = Citry()
    observed = []

    class Child(Component):
        citry = c

        @property
        def id(self):
            # Target the binding boundary while keeping the constructor's validated ID.
            if sys._getframe(1).f_code.co_name == "bind_instance":
                self._bind_reads = getattr(self, "_bind_reads", 0) + 1
                if self._bind_reads == 2:
                    current = ownership.current_ownership_graph()
                    assert current is not None
                    observed.append(current.snapshot())
                    current.import_replayed_snapshot(ownership.OwnershipGraph().snapshot())
                    observed.append(current.snapshot())
            return self._saved_id

        @id.setter
        def id(self, value):
            self._saved_id = value

        template = """
        <p>body</p>
        """

    class Page(Component):
        citry = c
        template = """
        <c-child />
        """

    rendered = Page().render()
    assert "body" in str(rendered)
    assert len(observed) == 2
    assert observed[0] == observed[1]
    child_id = observed[0].component_invocations[0].target_render_id
    assert child_id is not None
    assert observed[0].render_queue[0].state == ownership.QueueState.ENQUEUED
    assert observed[0].render_queue[0].target_render_id is None
    snapshot = rendered.context.ownership.snapshot()
    assert snapshot.component_invocations[0].target_render_id == child_id
    assert snapshot.render_queue[0].target_render_id == child_id
    assert snapshot.render_queue[0].rendered_order is not None
    assert snapshot.render_queue[0].state == ownership.QueueState.SETTLED
