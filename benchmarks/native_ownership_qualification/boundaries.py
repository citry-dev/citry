"""Observe native queue-order limits and partial updates before changing storage."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmarks/native_combined_capture_probe"))

from probe import NATIVE, PROBE_ARTIFACT  # noqa: E402
from probe import ownership as own  # noqa: E402


def journal() -> Any:
    """Create one empty journal with the production record factories."""
    return NATIVE.Journal(
        own.ComponentInvocationRecord,
        own.RenderQueueRecord,
        own.OwnershipState.ACTIVE,
        own.QueueState.ENQUEUED,
        own.QueueState.RENDERED,
    )


def capture(value: Any, order: int) -> int:
    """Append one call with a caller-supplied queue order."""
    return value.capture((1, 1, "source", "Parent", 1, "child", "Child", None, None, None, None, ()), order)


if __name__ == "__main__":
    observations = []
    for operation in ("capture", "bind", "settle", "retire"):
        value = journal()
        if operation != "capture":
            capture(value, 2)
        before = tuple(value.invocations()), tuple(value.queues())
        try:
            if operation == "capture":
                capture(value, 2**64)
            elif operation == "bind":
                value.bind(0, "Target", "target", 2**64, selector=False)
            elif operation == "settle":
                value.settle(0, 2**64, own.QueueState.SETTLED)
            else:
                value.retire_many(
                    [0], 2**64 - 1, own.OwnershipState.RETIRED, own.QueueState.RETIRED, own.QueueState.FAILED
                )
        except OverflowError as error:
            outcome = {"error": type(error).__name__, "message": str(error)}
        else:
            outcome = {"error": None}
        after = tuple(value.invocations()), tuple(value.queues())
        observations.append(
            {
                "operation": operation,
                **outcome,
                "state_changed": before != after,
                "invocation_states": [row.state.value for row in after[0]],
                "queue_states": [row.state.value for row in after[1]],
            }
        )
    print(
        json.dumps(
            {
                "observations": observations,
                "hashes": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (Path(__file__).resolve(), PROBE_ARTIFACT)
                },
            },
            indent=2,
        )
    )
