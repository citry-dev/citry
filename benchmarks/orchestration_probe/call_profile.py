"""Retain a full-call diagnostic to choose component orchestration experiments."""

from __future__ import annotations

import cProfile
import hashlib
import json
import pstats
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402

from citry import component_render  # noqa: E402

module = scenario()
data = module.gen_render_data()
for _ in range(6):
    module.render(data)
profiler = cProfile.Profile()
profiler.enable()
for _ in range(20):
    module.render(data)
profiler.disable()
stats = pstats.Stats(profiler)
rows = []
for (filename, line, name), (primitive, total, own, cumulative, _callers) in stats.stats.items():
    rows.append(
        {
            "file": filename,
            "line": line,
            "function": name,
            "calls_per_render": total / 20,
            "primitive_calls_per_render": primitive / 20,
            "instrumented_self_ms": own * 50,
            "instrumented_cumulative_ms": cumulative * 50,
        }
    )
rows.sort(key=lambda row: row["instrumented_self_ms"], reverse=True)
report = {
    "diagnostic_only": True,
    "samples": 20,
    "warmups": 6,
    "note": "cProfile changes call costs; cumulative rows overlap and must not be added.",
    "source_sha256": hashlib.sha256(Path(component_render.__file__).read_bytes()).hexdigest(),
    "rows": rows,
}
path = ROOT / "benchmarks/results/performance-render/orchestration-profile.json"
path.write_text(json.dumps(report, indent=2) + "\n")
for row in rows[:35]:
    print(json.dumps(row))
