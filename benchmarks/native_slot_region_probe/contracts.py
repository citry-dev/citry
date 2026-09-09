"""Compare slot-region preparation, callback state and native rejection behavior."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from probe import ENABLE, NATIVE, PROBE_ARTIFACT, PROBE_ROOT, RESTORE, ROOT
from probe import ownership as own

import citry.citry_render as renders
from citry.slots import Slot


def observe(*, changed: bool, case: str) -> tuple[Any, ...]:
    """Compare graph state observed inside and after the slot callback."""
    (ENABLE if changed else RESTORE)()
    graph = own.OwnershipGraph()
    slot = Slot("body")
    fill_id = graph._append_fill(
        kind=own.LogicalFillKind.NAMED,
        slot_name="default",
        source_policy=own.SourcePolicy.TEMPLATE,
        lexical_owner_render_id="owner",
        lexical_owner_class_id="Owner",
        source_location_id=None,
        source_invocation_id=None,
        receiver_render_id="receiver",
        receiver_class_id="Receiver",
    )
    graph._template_fill_by_slot_object[slot] = fill_id
    if case == "retired":
        graph._logical_fills[0] = graph._logical_fills[0]._with_state(own.OwnershipState.RETIRED)
    if case == "untracked":
        del graph._template_fill_by_slot_object[slot]
    observations = []
    original_wrapper = renders.PhysicalRegionPart

    def callback() -> Any:
        observations.append((graph._order, graph._region_id, tuple(graph._region_index.items()), graph.snapshot()))
        if case == "nested":
            return graph.capture_slot_call(slot, lambda: "inner")
        if case == "error":
            raise ValueError("slot callback failed")
        if case == "wrapper-alias":
            renders.PhysicalRegionPart = lambda _graph, region_id, _result: SimpleNamespace(region_id=region_id)
        return "body"

    token = None
    if case == "outlet":
        token = own._SLOT_SITE.set(own._SlotSite(graph=graph, receiver_render_id="outlet", source_location_id=17))
    try:
        try:
            result = graph.capture_slot_call(slot, callback)
        except ValueError as error:
            outcome = (type(error).__name__, str(error))
        else:
            outcome = (type(result).__name__, getattr(result, "region_id", None))
    finally:
        renders.PhysicalRegionPart = original_wrapper
        if token is not None:
            own._SLOT_SITE.reset(token)
    return outcome, observations, graph.snapshot(), own._ACTIVE_REGION.get()


def main() -> None:
    """Retain differential slot cases and verify rejection before native append."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = {}
    try:
        for case in ("standalone", "outlet", "nested", "retired", "untracked", "error", "wrapper-alias"):
            reference = observe(changed=False, case=case)
            candidate = observe(changed=True, case=case)
            if reference != candidate:
                raise AssertionError((case, reference, candidate))
            cases[case] = {"equal": True, "outcome": reference[0], "callback_observations": len(reference[1])}
        sys.path.insert(0, str(PROBE_ROOT))
        import check_storage  # noqa: PLC0415

        old_install = check_storage.install_storage
        check_storage.install_storage = lambda *_args, **_kwargs: (ENABLE, RESTORE)
        try:
            check_storage.check_mid_callback_replay(NATIVE)
        finally:
            check_storage.install_storage = old_install

        invalid = []
        fill = own.LogicalFillRecord(
            1,
            1,
            own.LogicalFillKind.NAMED,
            "default",
            own.SourcePolicy.TEMPLATE,
            "owner",
            "Owner",
            None,
            None,
            "receiver",
            "Receiver",
        )
        for case in ("region-width", "fill-width", "fill-index", "parent-index", "ids", "site"):
            regions = NATIVE.RecordTable(own.PhysicalRegionRequestRecord, 10 if case == "region-width" else 11)
            fills = NATIVE.RecordTable(own.LogicalFillRecord, 12 if case == "fill-width" else 13)
            if case != "fill-width":
                fills.append_values(tuple(fill))
            expected = IndexError if case in {"fill-index", "parent-index"} else ValueError
            try:
                regions.begin_slot_region(
                    fills,
                    8 if case == "fill-index" else 0,
                    0 if case == "parent-index" else None,
                    (1,) if case == "ids" else (1, 2, 1, None),
                    ("receiver",) if case == "site" else None,
                    own.OwnershipState.ACTIVE,
                    own.RegionState.CAPTURED,
                )
            except expected:
                if len(regions) != 0:
                    raise AssertionError("Invalid preparation appended a region") from None
                invalid.append(case)
            else:
                raise AssertionError("Invalid native preparation did not raise")
        fills = NATIVE.RecordTable(own.LogicalFillRecord, 13)
        fills.append_values(tuple(fill._with_state(own.OwnershipState.RETIRED)))
        regions = NATIVE.RecordTable(own.PhysicalRegionRequestRecord, 11)
        declined = regions.begin_slot_region(
            fills, 0, 99, (1, 2, 1, 99), None, own.OwnershipState.ACTIVE, own.RegionState.CAPTURED
        )
        if declined is not None or len(regions) != 0:
            raise AssertionError("Inactive fill must decline before parent lookup or mutation")
        report = {
            "cases": cases,
            "mid_callback_replay": {"success_and_error_equal": True},
            "invalid_without_append": invalid,
            "inactive_before_parent_lookup": True,
            "hashes": {
                str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (
                    Path(__file__).resolve(),
                    Path(__file__).with_name("adapter.py"),
                    PROBE_ROOT / "check_storage.py",
                    PROBE_ARTIFACT,
                )
            },
        }
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    finally:
        RESTORE()


if __name__ == "__main__":
    main()
