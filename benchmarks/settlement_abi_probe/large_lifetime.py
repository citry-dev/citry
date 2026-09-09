"""Check whether the complete benchmark retains its ownership graph after rendering."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path
from typing import Any
from weakref import ref

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks.settlement_abi_probe.adapter import install  # noqa: E402


def worker(changed: bool) -> dict[str, object]:
    """Observe one discarded render after six warmups without holding its graph."""
    install(changed)
    from benchmarks.utils import get_benchmark_script  # noqa: PLC0415

    from citry import ownership  # noqa: PLC0415

    path = ROOT / "packages/py/citry/tests/test_benchmark_citry.py"
    module = types.ModuleType("lifetime_scenario")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(get_benchmark_script(path), str(path), "exec"), module.__dict__)  # noqa: S102
    data = module.gen_render_data()
    for _ in range(6):
        module.render(data)
    gc.collect()
    gc.disable()
    snapshot = ownership.OwnershipGraph.snapshot
    graphs = []

    def observe(graph: Any) -> Any:
        graphs.append(ref(graph))
        return snapshot(graph)

    try:
        ownership.OwnershipGraph.snapshot = observe
        output = module.render(data)
    finally:
        ownership.OwnershipGraph.snapshot = snapshot
    if len(graphs) != 4:
        raise RuntimeError("Expected four ownership snapshot observations")
    live_before = sum(graph() is not None for graph in graphs)
    gc.set_debug(gc.DEBUG_SAVEALL)
    collected = gc.collect()
    counts = Counter(f"{type(item).__module__}.{type(item).__qualname__}" for item in gc.garbage)
    return {
        "candidate": changed,
        "snapshot_observations": len(graphs),
        "live_graph_observations_before_gc": live_before,
        "live_graph_observations_after_gc": sum(graph() is not None for graph in graphs),
        "collected": collected,
        "unreachable_types": dict(sorted(counts.items())),
        "output_bytes": len(output.encode()),
    }


def main() -> None:
    """Keep full-page lifetime evidence separate from throughput samples."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("reference", "candidate"))
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker == "candidate")))
        return
    report = {}
    for variant in ("reference", "candidate"):
        completed = subprocess.run(
            [sys.executable, __file__, "--worker", variant], cwd=ROOT, capture_output=True, text=True, check=True
        )
        report[variant] = json.loads(completed.stdout)
    report["hashes"] = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (
            Path(__file__),
            Path(__file__).with_name("adapter.py"),
            ROOT / "packages/py/citry/tests/test_benchmark_citry.py",
        )
    }
    report["build"] = json.loads((ROOT / "benchmarks/results/repeat-render/settlement-abi310-build.json").read_text())
    (ROOT / "benchmarks/results/repeat-render/settlement-abi310-large-lifetime.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps({variant: report[variant] for variant in ("reference", "candidate")}, indent=2))


if __name__ == "__main__":
    main()
