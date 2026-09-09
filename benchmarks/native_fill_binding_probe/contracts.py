"""Compare fill binding errors, retained records and receiver fallback behavior."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from probe import ENABLE, NATIVE, RESTORE, ROOT
from probe import ownership as own

from citry.slots import Slot


def observe(changed: bool, case: str) -> tuple[Any, ...]:
    """Run the same graph binding operations with production or grouped storage."""
    (ENABLE if changed else RESTORE)()
    graph = own.OwnershipGraph()
    slot = Slot("body")
    receiver = SimpleNamespace(id="receiver", _citry_class_id="Receiver", raw_slots={"default": slot})
    fill_id = graph._append_fill(
        kind=own.LogicalFillKind.FALLBACK if case == "fallback" else own.LogicalFillKind.NAMED,
        slot_name="default",
        source_policy=own.SourcePolicy.PYTHON if case == "python" else own.SourcePolicy.TEMPLATE,
        lexical_owner_render_id="owner",
        lexical_owner_class_id="Owner",
        source_location_id=None,
        source_invocation_id=2 if case == "rebind" else None,
        receiver_render_id="other" if case == "forward" else None,
        receiver_class_id=None,
    )
    graph._template_fill_by_slot_object[slot] = fill_id
    if case == "retired":
        graph._logical_fills[0] = graph._logical_fills[0]._with_state(own.OwnershipState.RETIRED)
    # The narrow invocation reader only requires the lexical owner. Use the
    # same structural boundary in both variants, leaving fill storage real.
    graph._component_invocations = [SimpleNamespace(source_render_id="wrong" if case == "wrong-owner" else "owner")]
    graph._invocation_index[1] = 0
    retained = graph._logical_fills[0]
    error = None
    visits = []

    class Supplies:
        def values(self) -> Any:
            visits.append("first")
            yield slot
            graph._logical_fills = list(graph._logical_fills)
            visits.append("second")
            yield slot

    try:
        graph.bind_template_fill_sources(Supplies() if case == "materialize" else {"default": slot}, 1)
        graph.bind_supplied_slots(receiver)
        if case == "repeat":
            graph.bind_supplied_slots(receiver)
    except RuntimeError as exc:
        error = (type(exc).__name__, str(exc))
    return (
        error,
        retained,
        tuple(graph._logical_fills),
        tuple(graph._receiver_fill.items()),
        graph._template_fill_by_slot_object[slot],
        tuple(visits),
    )


def main() -> None:
    """Retain differential outcomes and native validation observations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = ("normal", "repeat", "fallback", "python", "wrong-owner", "rebind", "forward", "retired", "materialize")
    outcomes = {}
    try:
        for case in cases:
            reference = observe(changed=False, case=case)
            candidate = observe(changed=True, case=case)
            if reference != candidate:
                raise AssertionError((case, reference, candidate))
            outcomes[case] = {"equal": True, "error": reference[0], "fills": len(reference[2]), "visits": reference[5]}
        invalid = []
        for width, index, expected in ((12, 0, ValueError), (13, 0, IndexError), (13, -1, IndexError)):
            for operation in ("bind_fill_source", "attach_active_fill"):
                table = NATIVE.RecordTable(tuple, width)
                arguments = (
                    (index, "owner", 1, own.SourcePolicy.TEMPLATE, own.LogicalFillKind.FALLBACK)
                    if operation == "bind_fill_source"
                    else (index, "receiver", "Receiver", own.OwnershipState.ACTIVE)
                )
                try:
                    getattr(table, operation)(*arguments)
                except expected:
                    invalid.append(
                        {"operation": operation, "width": width, "index": index, "unchanged": len(table) == 0}
                    )
                else:
                    raise AssertionError("Invalid native fill operation did not raise")
        report = {
            "cases": outcomes,
            "invalid": invalid,
            "scope": "Production/grouped-native graph binding, retained rows, errors and forwarding/revival fallback.",
            "hashes": {
                str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (Path(__file__).resolve(), Path(__file__).with_name("adapter.py"))
            },
        }
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    finally:
        RESTORE()


if __name__ == "__main__":
    main()
