"""Ownership storage activation and replay transitions in ordinary rendering."""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from citry import Citry, Component, Slot, ownership


@pytest.mark.skipif(ownership._native_ownership is None, reason="The installed core has Python ownership storage")
def test_ordinary_render_uses_native_storage():
    c = Citry()

    class Child(Component):
        citry = c
        template = """
        <c-slot />
        """

    class Page(Component):
        citry = c
        template = """
        <c-child>body</c-child>
        """

    render = Page().render()
    graph = render.context.ownership
    assert isinstance(graph._component_invocations, ownership._JournalRecords)
    assert isinstance(graph._logical_instances, ownership._RecordTable)
    snapshot = graph.snapshot()
    assert snapshot.component_invocations
    assert snapshot.physical_regions
    assert all(isinstance(row, ownership.ComponentInvocationRecord) for row in snapshot.component_invocations)
    assert all(row.state == ownership.QueueState.SETTLED for row in snapshot.render_queue)


def test_core_without_ownership_capability_renders_in_fresh_interpreter():
    # A released core may lack both the native namespace and its Python wrapper.
    code = textwrap.dedent('''\
        import sys
        from citry_core import _rust
        if hasattr(_rust, "ownership"):
            del _rust.ownership
        sys.modules["citry_core._ownership"] = None
        from citry import Citry, Component, ownership
        c = Citry()
        class Child(Component):
            citry = c
            template = """
            <c-slot />
            """
        class Page(Component):
            citry = c
            template = """
            <c-child>body</c-child>
            """
        rendered = Page().render()
        graph = rendered.context.ownership
        assert isinstance(graph._component_invocations, list)
        assert isinstance(graph._physical_regions, list)
        assert graph.snapshot().physical_regions
        assert "body" in str(rendered)
    ''')
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("fail", [False, True])
@pytest.mark.parametrize("native", [False, True])
def test_replay_during_slot_callback_keeps_region_and_exception(monkeypatch, *, fail, native):
    if native and ownership._native_ownership is None:
        pytest.skip("The installed core has Python ownership storage")
    if not native:
        monkeypatch.setattr(ownership, "_native_ownership", None)
    graph = ownership.OwnershipGraph()
    if native:
        # Keep this a native-to-Python replay test even without a nested component.
        graph._initialize_native_storage()
    empty = ownership.OwnershipGraph().snapshot()
    slot = Slot("body")
    fill_id = graph._append_fill(
        kind=ownership.LogicalFillKind.PYTHON,
        slot_name="default",
        source_policy=ownership.SourcePolicy.PYTHON,
        lexical_owner_render_id=None,
        lexical_owner_class_id=None,
        source_location_id=None,
        source_invocation_id=None,
        receiver_render_id=None,
        receiver_class_id=None,
    )
    graph._template_fill_by_slot_object[slot] = fill_id
    error = ValueError("slot failed after replay")
    retained = []

    def callback():
        retained.append(graph.snapshot())
        graph.import_replayed_snapshot(empty)
        assert isinstance(graph._physical_regions, list)
        if fail:
            raise error
        return "body"

    if fail:
        with pytest.raises(ValueError, match="slot failed after replay") as caught:
            graph.capture_slot_call(slot, callback)
        assert caught.value is error
    else:
        result = graph.capture_slot_call(slot, callback)
        assert result.part == "body"
        assert result.region_id == 1
    assert ownership._ACTIVE_REGION.get() is None
    snapshot = graph.snapshot()
    assert retained[0].physical_regions[0].state == ownership.RegionState.CAPTURED
    assert snapshot.physical_regions[0].state == (
        ownership.RegionState.FAILED if fail else ownership.RegionState.CAPTURED
    )
    assert len(snapshot.logical_fills) == len(snapshot.physical_regions) == 1
