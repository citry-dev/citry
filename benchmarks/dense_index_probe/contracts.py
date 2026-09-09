"""Record invalid-ID behavior that direct ownership positions must preserve."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from probe import ROOT, OwnershipGraph, install


def observe(changed: bool, invocation_id: Any) -> dict[str, Any]:
    """Attempt retirement on a graph containing one unrendered invocation."""
    install(changed)
    try:
        graph = OwnershipGraph()
        context = SimpleNamespace(component=SimpleNamespace(id="owner", _citry_class_id="Owner"))
        graph.record_component_invocation(
            context,
            authored_tag="child",
            target_class_id="Child",
            morph_key=None,
            morph_mode=None,
            source="child",
            position=(0, 5),
            client_bindings=(),
        )
        try:
            graph.retire_invocation(invocation_id)
            outcome = {"returned": True}
        except Exception as error:  # noqa: BLE001 - the error is part of the observation
            outcome = {"error": type(error).__name__, "message": str(error)}
        outcome["record_states"] = [row.state.value for row in graph.snapshot().component_invocations]
        return outcome
    finally:
        install(changed=False)


def main() -> None:
    """Keep counterexamples distinct from production compatibility tests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = {
        label: {"reference": observe(False, value), "candidate": observe(True, value)}  # noqa: FBT003
        for label, value in (("zero", 0), ("past_end", 2), ("equal_float", 1.0))
    }
    if any(row["reference"] == row["candidate"] for row in rows.values()):
        raise RuntimeError("A stated direct-position counterexample changed; review the candidate")
    report = {
        "production_compatible": False,
        "observations": rows,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__).resolve(), Path(__file__).with_name("probe.py"))
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
