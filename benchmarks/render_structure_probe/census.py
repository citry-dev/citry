"""Count rebuilt records and repeated discovery without making timing claims."""

from __future__ import annotations

import dataclasses
import hashlib
import itertools
import json
import subprocess
import sys
from collections import Counter
from enum import Enum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402


def canonical(value: Any) -> Any:
    """Retain record fields, enum type names and values, and sequence ordering across processes."""
    if isinstance(value, Enum):
        return {"enum": f"{type(value).__module__}.{type(value).__qualname__}", "value": canonical(value.value)}
    if dataclasses.is_dataclass(value):
        return {
            "record": f"{type(value).__module__}.{type(value).__qualname__}",
            "fields": [[field.name, canonical(getattr(value, field.name))] for field in dataclasses.fields(value)],
        }
    if isinstance(value, tuple) and hasattr(type(value), "_fields"):
        return {
            "record": f"{type(value).__module__}.{type(value).__qualname__}",
            "fields": [[key, canonical(item)] for key, item in zip(value._fields, value, strict=True)],
        }
    if type(value) in (tuple, list):
        return {type(value).__name__: [canonical(item) for item in value]}
    if type(value) is dict:
        return {"dict": [[canonical(key), canonical(item)] for key, item in value.items()]}
    if value is None or type(value) in (str, int, bool, float):
        return value
    raise TypeError(f"Unqualified snapshot value: {type(value)!r}")


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    """Keep topology observations local to three controlled input cases."""
    import citry.component_render as rendering  # noqa: PLC0415
    import citry.util.id as ids  # noqa: PLC0415
    import citry_core._rust as native  # noqa: PLC0415
    from citry.citry_render import CitryRender, RenderFrame  # noqa: PLC0415
    from citry.ownership import OwnershipGraph  # noqa: PLC0415

    module = scenario()
    data = module.gen_render_data()
    for _ in range(6):
        module.render(data)
    counts: Counter[str] = Counter()
    sites: Counter[str] = Counter()
    scan_code = rendering._scan_deferred_parts.__code__
    body_code = rendering._render_body.__code__
    contains_code = rendering._contains_deferred.__code__

    def profile(frame: Any, event: str, _arg: Any) -> None:
        if event != "call":
            return
        code = frame.f_code
        if code is scan_code:
            counts["deferred_scan_calls"] += 1
            counts["deferred_scan_part_entries"] += len(frame.f_locals["parts"])
        elif code is body_code:
            counts["body_calls"] += 1
            counts["body_input_entries"] += len(frame.f_locals["body"])
        elif code is contains_code:
            counts["contains_deferred_calls"] += 1
        elif code.co_name == "__init__":
            instance = frame.f_locals.get("self")
            if isinstance(instance, (CitryRender, RenderFrame)) and code is type(instance).__init__.__code__:
                counts[f"created_{type(instance).__name__}"] += 1
                caller = frame.f_back
                if caller is not None:
                    sites[f"{Path(caller.f_code.co_filename).name}:{caller.f_code.co_name}"] += 1

    snapshots = []
    original = OwnershipGraph.snapshot

    def snapshot(graph: OwnershipGraph) -> Any:
        result = original(graph)
        snapshots.append(result)
        return result

    rows = []
    OwnershipGraph.snapshot = snapshot
    try:
        for label, inputs in (
            ("same_1", data),
            ("same_2", data),
            ("shorter_outputs", {**data, "outputs": data["outputs"][:1]}),
        ):
            counts.clear()
            sites.clear()
            snapshots.clear()
            ids._id_base = 123456
            ids._id_counter = itertools.count()
            sys.setprofile(profile)
            try:
                output = module.render(inputs)
            finally:
                sys.setprofile(None)
            rows.append(
                {
                    "case": label,
                    "counts": dict(counts),
                    "construction_callers": dict(sites),
                    "output_bytes": len(output.encode()),
                    "html_digest": hashlib.sha256(output.encode()).hexdigest(),
                    "snapshots": [
                        {
                            "digest": digest(canonical(item)),
                            "rows": {field.name: len(getattr(item, field.name)) for field in dataclasses.fields(item)},
                            "distinct_source_sites": len({id(row.site) for row in item.source_locations}),
                        }
                        for item in snapshots
                    ],
                }
            )
    finally:
        OwnershipGraph.snapshot = original
    report = {
        "diagnostic_only": True,
        "python": sys.version,
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),  # noqa: S607
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "cases": rows,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [
                Path(__file__),
                Path(__file__).with_name("plan.md"),
                *sorted((ROOT / "packages/py/citry/citry").rglob("*.py")),
                ROOT / "packages/py/citry/tests/test_benchmark_citry.py",
                ROOT / "benchmarks/ownership_journal_probe/probe.py",
                ROOT / "benchmarks/utils.py",
            ]
        },
    }
    path = ROOT / "benchmarks/results/performance-render/render-structure-census.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
