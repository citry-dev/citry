"""Check retained queue-order objects, collection and numeric retirement fallback."""

from __future__ import annotations

import gc
import hashlib
import json
import sys
import weakref
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmarks/native_combined_capture_probe"))

from probe import ENABLE, NATIVE, PROBE_ARTIFACT, RESTORE, STATS  # noqa: E402
from probe import ownership as own  # noqa: E402


def journal() -> Any:
    """Create a journal using the production factories and states."""
    return NATIVE.Journal(
        own.ComponentInvocationRecord,
        own.RenderQueueRecord,
        own.OwnershipState.ACTIVE,
        own.QueueState.ENQUEUED,
        own.QueueState.RENDERED,
    )


def capture(value: Any, order: Any, invocation_id: int = 1) -> None:
    """Record one call before its receiver is bound."""
    value.capture((invocation_id, 1, "owner", "Owner", 1, "child", "Child", None, None, None, None, ()), order)


def graph_case(*, changed: bool, case: str) -> tuple[Any, dict[str, int]]:
    """Retire the same graph through production or a numeric native fallback."""
    (ENABLE if changed else RESTORE)()
    graph = own.OwnershipGraph()
    invocation_id = 2**64 if case == "large-id" else -1 if case == "negative-id" else 1
    call = own.ComponentInvocationRecord(
        invocation_id, 1, "owner", "Owner", 1, "child", "Child", None, None, "child", None, ()
    )
    queue = own.RenderQueueRecord(invocation_id, 2, "child", 3, None, own.QueueState.RENDERED)
    if changed:
        capture(graph._component_invocations.journal, 2, invocation_id)
        graph._component_invocations.journal.bind(0, "Child", "child", 3, selector=False)
    else:
        graph._component_invocations.append(call)
        graph._render_queue.append(queue)
    graph._invocation_index[invocation_id] = 0
    graph._queue_index[invocation_id] = 0
    graph._logical_instances.append(
        own.LogicalInstanceRecord(4, "child", "Child", "Child", invocation_id, "owner", transparent=False)
    )
    graph._order = 2**64 if case == "large-order" else 4
    through = 2**64 if case == "large-through" else -1 if case == "negative-through" else graph._order
    before = STATS.copy()
    graph.retire_component_output("owner", through_order=through, descendant_render_ids={"child"})
    return graph.snapshot(), {key: STATS[key] - before[key] for key in STATS}


def main() -> None:
    """Retain boundary values, exact object identity, fallback and cycle evidence."""
    orders = [int(str(2**64 + offset)) for offset in range(1, 5)]
    value = journal()
    capture(value, orders[0])
    enqueued = value.queue(0)
    value.bind(0, "Child", "child", orders[1], selector=False)
    rendered = value.queue(0)
    value.settle(0, orders[2], own.QueueState.SETTLED)
    settled = value.queue(0)
    if (
        enqueued.enqueued_order is not orders[0]
        or rendered.rendered_order is not orders[1]
        or settled.settled_order is not orders[2]
    ):
        raise AssertionError("Journal did not preserve input queue-order objects")
    replacement = own.RenderQueueRecord(1, orders[3], "child", orders[1], orders[2], own.QueueState.SETTLED)
    value.set_queue(0, replacement)
    assigned = value.queue(0)
    if any(a is not b for a, b in zip(assigned, replacement, strict=True)):
        raise AssertionError("Queue assignment changed field identity")
    result = value.retire_many(
        [0], 2**64 - 1, own.OwnershipState.RETIRED, own.QueueState.RETIRED, own.QueueState.FAILED
    )
    retired = value.queue(0)
    if retired.enqueued_order is not orders[3] or retired.rendered_order is not orders[1]:
        raise AssertionError("Fresh export did not preserve assigned queue-order objects")
    if (
        result != 2**64
        or retired.settled_order is not result
        or value.invocation(0).state != own.OwnershipState.RETIRED
    ):
        raise AssertionError("Retirement did not cross the integer boundary consistently")
    if enqueued.state != own.QueueState.ENQUEUED or settled.state != own.QueueState.SETTLED:
        raise AssertionError("Later queue updates changed retained views")
    value.settle(0, orders[2], own.QueueState.FAILED)
    failed = value.queue(0)
    result = value.retire_many(
        [0], orders[3], own.OwnershipState.RETIRED, own.QueueState.RETIRED, own.QueueState.FAILED
    )
    if result is not orders[3] or value.queue(0) is not failed:
        raise AssertionError("Failed queues must retain state, order and cached view")

    class Order:
        def __init__(self, owner: Any) -> None:
            self.owner = owner

    cycles = []
    for field in ("enqueued", "rendered", "settled"):
        for exported in (False, True):
            target = journal()
            order = Order(target)
            capture(target, order if field == "enqueued" else 2)
            if field == "rendered":
                target.bind(0, "Child", "child", order, selector=False)
            elif field == "settled":
                target.settle(0, order, own.QueueState.SETTLED)
            if exported:
                target.queue(0)
            reference = weakref.ref(order)
            del target, order
            gc.collect()
            if reference() is not None:
                raise AssertionError("Queue-order reference leaked a native cycle")
            cycles.append({"field": field, "exported": exported, "collected": True})
    fallbacks = {}
    try:
        for case in ("large-id", "negative-id", "large-order", "large-through", "negative-through"):
            reference, _ = graph_case(changed=False, case=case)
            candidate, counts = graph_case(changed=True, case=case)
            if reference != candidate or counts != {"native_calls": 0, "fallback_calls": 1}:
                raise AssertionError((case, reference, candidate, counts))
            fallbacks[case] = {"snapshots_equal": True, **counts}
    finally:
        RESTORE()
    print(
        json.dumps(
            {
                "input_orders": orders,
                "queue_order_identity": True,
                "retained_views": True,
                "crossed_u64": True,
                "failed_queue_preserved": True,
                "cycles": cycles,
                "retirement_fallbacks": fallbacks,
                "hashes": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (Path(__file__).resolve(), PROBE_ARTIFACT)
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
