"""Keep ownership records and callback state intact when native storage starts later."""

from types import SimpleNamespace

import pytest

from citry import Citry, Component, Slot, ownership

pytestmark = pytest.mark.skipif(
    ownership._native_ownership is None,
    reason="The installed core does not expose native ownership storage",
)


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


def _prefix(graph):
    class Root:
        id = "owner"
        _citry_class_id = "Owner"
        transparent = False

    graph.bind_instance(Root(), SimpleNamespace(ownership_invocation_id=None))
    slot = Slot("body")
    fill_id = graph._append_fill(
        kind=ownership.LogicalFillKind.PYTHON,
        slot_name="default",
        source_policy=ownership.SourcePolicy.PYTHON,
        lexical_owner_render_id=None,
        lexical_owner_class_id=None,
        source_location_id=None,
        source_invocation_id=None,
        receiver_render_id="owner",
        receiver_class_id="Owner",
    )
    graph._template_fill_by_slot_object[slot] = fill_id
    return slot


def _assert_python_tables(graph):
    assert isinstance(graph._component_invocations, list)
    assert isinstance(graph._render_queue, list)
    assert isinstance(graph._logical_instances, list)
    assert isinstance(graph._init_ancestry, list)
    assert isinstance(graph._logical_fills, list)
    assert isinstance(graph._physical_regions, list)


def test_root_only_render_keeps_python_storage():
    c = Citry()

    class Page(Component):
        citry = c
        template = """
        <p><c-slot>body</c-slot></p>
        """

    rendered = Page().render()
    assert "body" in str(rendered)
    graph = rendered.context.ownership
    _assert_python_tables(graph)
    snapshot = graph.snapshot()
    assert snapshot.component_invocations == ()
    assert snapshot.render_queue == ()
    assert len(snapshot.logical_instances) == 1
    assert snapshot.logical_fills
    assert snapshot.physical_regions


@pytest.mark.parametrize("fail", [False, True])
def test_first_invocation_inside_slot_keeps_saved_rows_and_callback_state(*, fail):
    graph = ownership.OwnershipGraph()
    slot = _prefix(graph)
    error = ValueError("slot failed after native conversion")
    retained = []

    def callback():
        _assert_python_tables(graph)
        before = graph.snapshot()
        retained.append(before)
        region_id = graph.current_region_id()
        invocation_id = _invocation(graph)
        assert isinstance(graph._component_invocations, ownership._JournalRecords)
        assert isinstance(graph._physical_regions, ownership._RecordTable)
        after = graph.snapshot()
        assert graph.current_region_id() == region_id
        assert after.component_invocations[0].id == invocation_id
        assert after.component_invocations[0].physical_parent_region_id == region_id
        # Conversion copies containers while keeping every previously exported row.
        for family in ("logical_instances", "init_ancestry", "logical_fills", "physical_regions"):
            assert len(getattr(before, family)) == len(getattr(after, family))
            assert all(a is b for a, b in zip(getattr(before, family), getattr(after, family), strict=True))
        if fail:
            raise error
        return "body"

    if fail:
        with pytest.raises(ValueError, match="slot failed after native conversion") as caught:
            graph.capture_slot_call(slot, callback)
        assert caught.value is error
    else:
        result = graph.capture_slot_call(slot, callback)
        assert result.part == "body"
    assert graph.current_region_id() is None
    assert retained[0].physical_regions[0].state == ownership.RegionState.CAPTURED
    assert graph.snapshot().physical_regions[0].state == (
        ownership.RegionState.FAILED if fail else ownership.RegionState.CAPTURED
    )


def test_empty_replay_still_allows_first_invocation_to_convert_saved_rows():
    graph = ownership.OwnershipGraph()
    _prefix(graph)
    before = graph.snapshot()
    graph.import_replayed_snapshot(ownership.OwnershipGraph().snapshot())
    _assert_python_tables(graph)
    assert _invocation(graph) == 1
    assert isinstance(graph._component_invocations, ownership._JournalRecords)
    after = graph.snapshot()
    assert after.logical_instances[0] is before.logical_instances[0]
    assert after.logical_fills[0] is before.logical_fills[0]
    assert len(after.component_invocations) == len(after.render_queue) == 1


def test_replayed_invocation_keeps_subsequent_capture_on_python_storage():
    source = ownership.OwnershipGraph()
    _invocation(source)
    graph = ownership.OwnershipGraph()
    graph.import_replayed_snapshot(source.snapshot())
    before = graph.snapshot()
    assert _invocation(graph) == 2
    _assert_python_tables(graph)
    after = graph.snapshot()
    assert after.component_invocations[0] is before.component_invocations[0]
    assert after.render_queue[0] is before.render_queue[0]
    assert len(after.component_invocations) == len(after.render_queue) == 2


@pytest.mark.parametrize("convert_before_rollback", [False, True])
def test_replay_rollback_restores_prefix_for_first_native_invocation(*, convert_before_rollback):
    source = ownership.OwnershipGraph()
    if not convert_before_rollback:
        _invocation(source)
    graph = ownership.OwnershipGraph()
    _prefix(graph)
    before = graph.snapshot()
    checkpoint = graph.checkpoint()
    error = ValueError("replay apply failed")

    def apply_replay():
        with graph.replay_transaction():
            graph.import_replayed_snapshot(source.snapshot())
            if convert_before_rollback:
                _invocation(graph)
                assert isinstance(graph._component_invocations, ownership._JournalRecords)
            else:
                _assert_python_tables(graph)
            raise error

    with pytest.raises(ValueError, match="replay apply failed") as caught:
        apply_replay()

    assert caught.value is error
    assert graph.snapshot() == before
    assert graph.checkpoint() == checkpoint
    _assert_python_tables(graph)
    assert _invocation(graph) == 1
    assert isinstance(graph._component_invocations, ownership._JournalRecords)
    after = graph.snapshot()
    assert after.logical_instances[0] is before.logical_instances[0]
    assert after.logical_fills[0] is before.logical_fills[0]


def test_low_level_queue_only_guard_declines_conversion():
    graph = ownership.OwnershipGraph()
    # Isolate the guard with a queue-only state, without claiming a valid rendered graph.
    queued = ownership.RenderQueueRecord(99, 1, None, None, None, ownership.QueueState.ENQUEUED)
    graph._render_queue.append(queued)
    before = graph.snapshot()
    graph._initialize_native_storage()
    _assert_python_tables(graph)
    assert graph.snapshot() == before
    assert graph._render_queue[0] is queued
