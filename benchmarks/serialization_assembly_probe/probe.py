"""Compare joined child strings with child references during HTML assembly."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import itertools
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402
from benchmarks.repeated_work_probe import compile_function  # noqa: E402

import citry.serialize as ser  # noqa: E402
import citry.util.id as ids  # noqa: E402
import citry_core._rust as native  # noqa: E402
from citry.ownership import OwnershipGraph  # noqa: E402

REFERENCE = """    finished: dict[str, str] = {}
    for key in reversed(order):
        segments, placeholders = frame_by_key[key]
        parts = [segments[0]]
        for (child_id, placeholder_html, _), segment in zip(placeholders, segments[1:], strict=True):
            parts.append(finished.get(child_id, placeholder_html))
            parts.append(segment)
        finished[key] = "".join(parts)

    html = finished[root_key]"""

CANDIDATE = """    finished = {}
    for key in reversed(order):
        segments, placeholders = frame_by_key[key]
        if not placeholders and len(segments) == 1:
            finished[key] = segments[0]
            continue
        parts = [segments[0]]
        for (child_id, placeholder_html, _), segment in zip(placeholders, segments[1:], strict=True):
            parts.append(finished.get(child_id, placeholder_html))
            parts.append(segment)
        finished[key] = parts

    # Only references to earlier entries were stored, so this walk is acyclic.
    chunks = []
    pending = [finished[root_key]]
    while pending:
        part = pending.pop()
        if isinstance(part, str):
            chunks.append(part)
        else:
            pending.extend(reversed(part))
    html = "".join(chunks)"""


def synthetic_checks() -> dict[str, Any]:
    """Check assembly order and expose copying costs without rendering components."""
    reference = compile_function(
        "def assemble(frame_by_key, order, root_key):\n" + REFERENCE + "\n    return html\n", {}, "assemble"
    )
    candidate = compile_function(
        "def assemble(frame_by_key, order, root_key):\n" + CANDIDATE + "\n    return html\n", {}, "assemble"
    )
    cases: dict[str, tuple[Any, Any, str]] = {
        "empty": ({"": ([""], [])}, [""], ""),
        "unresolved": ({"": (["before", "after"], [("missing", "literal", [])])}, [""], ""),
        # A reference to a later bottom-up entry must remain literal, even if
        # that entry exists. A self reference has the same rule.
        "forward_and_self": (
            {"": (["", ""], [("b", "B", [])]), "b": (["", "", ""], [("", "ROOT", []), ("b", "SELF", [])])},
            ["", "b"],
            "",
        ),
    }
    deep = {str(index): (["<i>", "</i>"], [(str(index + 1), "?", [])]) for index in range(400)}
    deep["400"] = (["x" * 100_000], [])
    cases["deep_large_leaf"] = (deep, list(deep), "0")
    wide = {"": ([""] * 1001, [(str(index), "?", []) for index in range(1000)])}
    wide.update({str(index): (["x" * 100], []) for index in range(1000)})
    cases["wide"] = (wide, list(wide), "")
    reports = {}
    for name, arguments in cases.items():
        expected = reference(*arguments)
        if candidate(*arguments) != expected:
            raise RuntimeError(f"Assembly differs for {name}")
        observations = []
        for pair in range(20):
            for changed in (False, True) if pair % 2 == 0 else (True, False):
                function = candidate if changed else reference
                start = time.perf_counter_ns()
                result = function(*arguments)
                elapsed = (time.perf_counter_ns() - start) / 1_000_000
                if result != expected:
                    raise RuntimeError(f"Assembly changed during {name}")
                observations.append({"pair": pair, "candidate": changed, "ms": elapsed})
        reports[name] = {"output_chars": len(expected), "all_equal": True, "observations": observations}
    return reports


def main() -> None:
    """Measure complete renders; keep inspection and all switches outside timers."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=int, default=60)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.pairs < 1:
        parser.error("--pairs must be positive")
    reference = ser.serialize_render_result
    source = inspect.getsource(reference)
    if source.count(REFERENCE) != 1:
        raise RuntimeError("Serializer assembly changed; inspect before comparing")
    candidate = compile_function(source.replace(REFERENCE, CANDIDATE), ser.__dict__, reference.__name__)
    volume: list[Any] = []
    measured_source = source.replace(
        "    html = finished[root_key]",
        """    _probe_volume.append({
        "frames": len(finished),
        "root_chars": len(finished[root_key]),
        "joined_frame_chars": sum(len(value) for value in finished.values()),
        "multi_part_join_chars": sum(len(finished[key]) for key in order if frame_by_key[key][1]),
    })
    html = finished[root_key]""",
    )
    measured = compile_function(measured_source, {**ser.__dict__, "_probe_volume": volume}, reference.__name__)
    synthetic = synthetic_checks()
    module = scenario()
    data = module.gen_render_data()
    snapshot = OwnershipGraph.snapshot
    traces: dict[bool, list[Any]] = {}
    observations = []
    try:
        for changed in (False, True):
            ser.serialize_render_result = candidate if changed else reference
            for _ in range(6):
                module.render(data)
            captured: list[Any] = []

            def capture(graph: Any, _captured: list[Any] = captured) -> Any:
                value = snapshot(graph)
                _captured.append(value)
                return value

            OwnershipGraph.snapshot = capture
            ids._id_counter = itertools.count()
            module.render(data)
            OwnershipGraph.snapshot = snapshot
            traces[changed] = captured
        if not traces[False] or traces[False] != traces[True]:
            raise RuntimeError("Missing or unequal ownership snapshot traces")
        ser.serialize_render_result = measured
        ids._id_counter = itertools.count()
        measured_html = module.render(data)
        for pair in range(args.pairs):
            outputs = {}
            for changed in (False, True) if pair % 2 == 0 else (True, False):
                ser.serialize_render_result = candidate if changed else reference
                ids._id_counter = itertools.count()
                start = time.perf_counter_ns()
                outputs[changed] = module.render(data)
                elapsed = (time.perf_counter_ns() - start) / 1_000_000
                observations.append({"pair": pair, "candidate": changed, "ms": elapsed})
            if outputs[False] != outputs[True] or outputs[False] != measured_html:
                raise RuntimeError(f"HTML differs in pair {pair}")
    finally:
        ser.serialize_render_result = reference
        OwnershipGraph.snapshot = snapshot
    savings = []
    for pair in range(args.pairs):
        values = {row["candidate"]: row["ms"] for row in observations if row["pair"] == pair}
        savings.append(values[False] - values[True])
    report = {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),  # noqa: S607
        "python": sys.version,
        "platform": platform.platform(),
        "serializer_sha256": hashlib.sha256(Path(ser.__file__).read_bytes()).hexdigest(),
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "scenario_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "candidate_assembly_sha256": hashlib.sha256(CANDIDATE.encode()).hexdigest(),
        "pairs": args.pairs,
        "all_pairs_html_equal": True,
        "output_bytes": len(measured_html.encode()),
        "snapshots_compared": len(traces[True]),
        "snapshot_trace_equal": True,
        "medians_ms": {
            name: statistics.median(row["ms"] for row in observations if row["candidate"] == changed)
            for name, changed in (("reference", False), ("candidate", True))
        },
        "median_paired_saving_ms": statistics.median(savings),
        "favorable_pairs": sum(value > 0 for value in savings),
        "assembly_volume": volume,
        "synthetic": synthetic,
        "observations": observations,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps({key: value for key, value in report.items() if key not in {"observations", "synthetic"}}, indent=2)
    )


if __name__ == "__main__":
    main()
