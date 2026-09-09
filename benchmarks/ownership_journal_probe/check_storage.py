"""Check cached record lifetimes and replay during an active slot callback."""

from __future__ import annotations

import bisect
import gc
import weakref
from typing import Any

from storage_probe import TABLES, install_storage, load_native, own

from citry.slots import Slot


def check_tables(native: Any) -> None:
    """Retain exported records across native mutation and collect reference cycles."""
    record = own.LogicalInstanceRecord(1, "id", "Class", "Class", None, None, transparent=False)
    table = native.RecordTable(type(record), len(record))
    table.append_values(tuple(record))
    before = table[0]
    if before is not table[0] or before != record:
        raise AssertionError("Initial immutable view was not cached")
    table.patch(0, ((7, own.OwnershipState.RETIRED),))
    after = table[0]
    if before.state != own.OwnershipState.ACTIVE or after.state != own.OwnershipState.RETIRED:
        raise AssertionError("Native patch changed a retained immutable record")
    if bisect.bisect_right(table, 1, key=lambda value: value.order) != 1:
        raise AssertionError("Record table does not support the runtime's ordered lookup")
    saved = tuple(table)
    try:
        table.patch(0, ((7, own.OwnershipState.ACTIVE), (99, None)))
    except IndexError:
        pass
    else:
        raise AssertionError("Invalid patch field must raise")
    if tuple(table) != saved:
        raise AssertionError("Invalid patch changed fields before validation")

    class Name(str):  # noqa: SLOT000 - Deliberate user object with a back-reference.
        owner: Any

    # Fields may point back through user values, even before any public view
    # exists. Check both raw storage and already exported record caches.
    for exported in (False, True):
        name = Name("cycle")
        table = native.RecordTable(type(record), len(record))
        name.owner = table
        table.append_values(tuple(record._replace(render_id=name)))
        if exported:
            table[0]
        reference = weakref.ref(name)
        del name, table
        gc.collect()
        if reference() is not None:
            raise AssertionError("Native record table leaked a Python reference cycle")

        name = Name("cycle")
        journal = native.Journal(
            own.ComponentInvocationRecord,
            own.RenderQueueRecord,
            own.OwnershipState.ACTIVE,
            own.QueueState.ENQUEUED,
            own.QueueState.RENDERED,
        )
        name.owner = journal
        journal.capture((1, 1, name, "Parent", 1, "child", "Child", None, None, None, None, ()), 2)
        if exported:
            journal.invocation(0)
            journal.queue(0)
        reference = weakref.ref(name)
        del name, journal
        gc.collect()
        if reference() is not None:
            raise AssertionError("Native invocation journal leaked a Python reference cycle")


def check_mid_callback_replay(native: Any) -> None:
    """Replay may replace the tables before a slot callback returns or raises."""
    enable, disable = install_storage(native, {"native_calls": 0, "fallback_calls": 0})
    try:
        for fail in (False, True):
            observations = []
            for changed in (False, True):
                (enable if changed else disable)()
                empty = own.OwnershipGraph().snapshot()
                graph = own.OwnershipGraph()
                if changed and isinstance(graph._component_invocations, list):
                    graph._initialize_native_storage()
                slot = Slot("x")
                fill = graph._append_fill(
                    kind=own.LogicalFillKind.PYTHON,
                    slot_name="default",
                    source_policy=own.SourcePolicy.PYTHON,
                    lexical_owner_render_id=None,
                    lexical_owner_class_id=None,
                    source_location_id=None,
                    source_invocation_id=None,
                    receiver_render_id=None,
                    receiver_class_id=None,
                )
                graph._template_fill_by_slot_object[slot] = fill
                error = ValueError("slot failed after replay")

                def callback(
                    _graph: Any = graph, _empty: Any = empty, *, _fail: bool = fail, _error: Exception = error
                ) -> str:
                    _graph.import_replayed_snapshot(_empty)
                    if _fail:
                        raise _error
                    return "x"

                try:
                    result = graph.capture_slot_call(slot, callback)
                except ValueError as caught:
                    if not fail or caught is not error:
                        raise
                    value = None
                else:
                    if fail or result.part != "x":
                        raise AssertionError("Unexpected replay callback result")
                    value = (result.region_id, result.part)
                if changed and any(isinstance(getattr(graph, name), native.RecordTable) for name in TABLES):
                    raise AssertionError("Replay did not materialize native tables")
                observations.append((value, graph.snapshot()))
            if observations[0] != observations[1]:
                raise AssertionError("Replay during slot callback differs from production")
    finally:
        disable()


def main() -> None:
    """Run the opt-in storage contract checks without starting repository gates."""
    native = load_native()
    check_tables(native)
    check_mid_callback_replay(native)
    print(
        "Cached snapshots, ordered lookup, patch validation, four GC cycles and two mid-callback replay cases passed"
    )


if __name__ == "__main__":
    main()
