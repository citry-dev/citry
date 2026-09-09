"""Check exact record types, field identity, cached views and constructor cycles."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import weakref
from pathlib import Path
from typing import Any

from probe import NATIVE, PROBE_ARTIFACT, ROOT
from probe import ownership as own


def journal() -> Any:
    """Build a journal with the production record classes and states."""
    return NATIVE.Journal(
        own.ComponentInvocationRecord,
        own.RenderQueueRecord,
        own.OwnershipState.ACTIVE,
        own.QueueState.ENQUEUED,
        own.QueueState.RENDERED,
    )


def seed(value: Any) -> None:
    """Capture one invocation containing a retained string object."""
    value.capture((1, 1, "source", "Parent", 1, "child", "Child", None, None, None, None, ()), 2)


def main() -> None:
    """Retain direct-export identity, cache, failure and GC observations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    marker = object()
    records = (
        own.LogicalInstanceRecord(1, marker, "Class", "Class", None, None, transparent=False),
        own.InitAncestryRecord(1, 1, marker, "child"),
        own.LogicalFillRecord(
            1,
            1,
            own.LogicalFillKind.NAMED,
            "default",
            own.SourcePolicy.TEMPLATE,
            marker,
            "Owner",
            None,
            None,
            None,
            None,
        ),
        own.PhysicalRegionRequestRecord(
            1, 2, 1, marker, None, marker, None, None, marker, None, own.RegionState.CAPTURED
        ),
    )
    checks = {}
    for record in records:
        table = NATIVE.RecordTable(type(record), len(record))
        table.set_tuple_constructor(tuple.__new__)
        table.append_values(tuple(record))
        exported = table[0]
        if (
            type(exported) is not type(record)
            or exported != record
            or any(a is not b for a, b in zip(exported, record, strict=True))
        ):
            raise AssertionError("Direct export changed the type, value or field identity")
        if table[0] is not exported:
            raise AssertionError("Direct export did not cache the immutable view")
        table.patch(0, ((0, 55),))
        patched = table[0]
        if exported[0] != 1 or patched[0] != 55 or patched is exported:
            raise AssertionError("A patch changed a retained view or reused stale state")
        checks[type(record).__name__] = {"type_value_identity_equal": True, "retained_view_preserved": True}
    value = journal()
    seed(value)
    before = (value.invocation(0), value.queue(0))
    value.set_tuple_constructor(tuple.__new__)
    if value.invocation(0) is not before[0] or value.queue(0) is not before[1]:
        raise AssertionError("Configuring a constructor invalidated cached views")
    value.bind(0, "Target", "target", 3, selector=False)
    after = (value.invocation(0), value.queue(0))
    for old, new, factory in zip(before, after, (own.ComponentInvocationRecord, own.RenderQueueRecord), strict=True):
        if type(new) is not factory or new == old or new is old:
            raise AssertionError("Journal export type/cache invalidation differs")
        checks[factory.__name__] = {"exact_type": True, "retained_view_preserved": True}
    if after[0].source_render_id is not before[0].source_render_id:
        raise AssertionError("Journal export copied a retained source field")

    failed = []
    for kind in ("table", "journal"):
        target = NATIVE.RecordTable(type(records[0]), len(records[0])) if kind == "table" else journal()
        if kind == "table":
            target.append_values(tuple(records[0]))
        else:
            seed(target)
        target.set_tuple_constructor(17)
        get = (
            (lambda _target=target: _target[0]) if kind == "table" else (lambda _target=target: _target.invocation(0))
        )
        try:
            get()
        except TypeError:
            pass
        else:
            raise AssertionError("A non-callable constructor did not fail on export")
        target.set_tuple_constructor(None)
        if type(get()) is not (type(records[0]) if kind == "table" else own.ComponentInvocationRecord):
            raise AssertionError("A failed construction polluted the cache")
        failed.append(kind)

    class Constructor:
        def __init__(self, owner: Any) -> None:
            self.owner = owner

        def __call__(self, factory: Any, fields: Any) -> Any:
            return tuple.__new__(factory, fields)

    cycles = []
    for kind in ("table", "journal"):
        for exported in (False, True):
            target = NATIVE.RecordTable(type(records[0]), len(records[0])) if kind == "table" else journal()
            if kind == "table":
                target.append_values(tuple(records[0]))
            else:
                seed(target)
            constructor = Constructor(target)
            reference = weakref.ref(constructor)
            target.set_tuple_constructor(constructor)
            if exported:
                target[0] if kind == "table" else target.invocation(0)
            del target, constructor
            gc.collect()
            if reference() is not None:
                raise AssertionError("Native constructor reference leaked a cycle")
            cycles.append({"kind": kind, "exported": exported, "collected": True})
    report = {
        "records": checks,
        "constructor_error_recovery": failed,
        "constructor_cycles": cycles,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__).resolve(), PROBE_ARTIFACT)
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
