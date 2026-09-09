"""Retain concrete compatibility failures of the lazy fallback experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from probe import ORIGINAL, ROOT, LogicalFillKind, Slot, candidate


def make(changed: bool) -> Slot:
    """Create an uninvoked fallback without needing an active ownership graph."""
    factory = candidate if changed else ORIGINAL
    return factory(
        ["body"],
        SimpleNamespace(ownership=None),
        "Card",
        "default",
        None,
        None,
        (0, 4),
        source="body",
        kind=LogicalFillKind.FALLBACK,
    )


def observe(changed: bool, case: str) -> dict[str, Any]:
    """Keep successful values and errors at the same public operation boundary."""
    slot = make(changed)
    try:
        if case == "write_extra":
            slot.extra = {"marker": 1}
            result = slot.extra
        elif case == "write_contents":
            slot.contents = ["replacement"]
            result = slot.contents
        elif case == "delete_extra":
            del slot.extra
            result = "deleted"
        elif case == "static_contents":
            # Direct descriptor access bypasses the experiment's attribute wrapper.
            result = type(Slot.contents.__get__(slot, Slot)).__name__
        else:
            result = type(slot).__name__
        return {"value": result}
    except Exception as error:  # noqa: BLE001 - the errors are the diagnostic result
        return {"error": type(error).__name__, "message": str(error)}


def main() -> None:
    """Record known counterexamples without calling them passing compatibility tests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    observations = {
        case: {"reference": observe(False, case), "candidate": observe(True, case)}  # noqa: FBT003
        for case in ("write_extra", "write_contents", "delete_extra", "static_contents", "type_before_read")
    }
    if any(row["reference"] == row["candidate"] for row in observations.values()):
        raise RuntimeError("An expected counterexample changed; update the experiment's stated limits")
    report = {
        "production_compatible": False,
        "observations": observations,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__).resolve(), Path(__file__).with_name("probe.py"))
        },
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
