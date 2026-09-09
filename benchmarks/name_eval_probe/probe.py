"""Compare direct simple-name evaluation with the existing expression pipeline."""

from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import itertools
import json
import keyword
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from shutil import which
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402

import citry.util.id as ids  # noqa: E402
import citry_core.safe_eval.eval as evaluator  # noqa: E402
from citry import nodes  # noqa: E402
from citry.ownership import OwnershipGraph  # noqa: E402


def load_reference() -> Any:
    """Use the pre-change compiler with the same live runtime dependencies."""
    git = which("git")
    if git is None:
        raise RuntimeError("The name evaluation comparison requires git")
    completed = subprocess.run(
        [git, "show", "26312d08:packages/py/citry_core/citry_core/safe_eval/eval.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    tree = ast.parse(completed.stdout)
    function = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "safe_eval")
    source = ast.get_source_segment(completed.stdout, function)
    if source is None:
        raise RuntimeError("Cannot extract reference safe_eval function")
    scope = {}
    exec(source, evaluator.__dict__, scope)  # noqa: S102
    return scope["safe_eval"]


def main() -> None:
    """Swap already compiled node evaluators outside complete render timings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=int, default=60)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.pairs < 1:
        parser.error("--pairs must be positive")
    if not hasattr(evaluator, "_simple_name_evaluator"):
        parser.error("The current evaluator does not provide the simple-name shortcut")
    original_compile = nodes.compile_expr
    reference_compile = load_reference()
    switches = []

    def compile_expr(source: str, **kwargs: Any) -> Any:
        changed = original_compile(source, **kwargs)
        if type(source) is str and source.isascii() and source.isidentifier() and not keyword.iskeyword(source):
            if not kwargs.get("sandboxed", True):
                raise RuntimeError("The simple-name comparison requires sandboxed evaluation")
            if changed.__qualname__ != "_simple_name_evaluator.<locals>.evaluate":
                raise RuntimeError("The interpreter did not select the candidate evaluator")
            reference = reference_compile(source)
            frame = inspect.currentframe()
            try:
                owner = frame.f_back.f_locals["self"]
            finally:
                del frame
            if type(owner) not in (nodes.ExprNode, nodes.ExprHtmlAttr):
                raise TypeError(f"Unexpected simple-name compiler caller: {type(owner)}")
            switches.append((owner, reference, changed, source))
            return reference
        return changed

    module = scenario()
    data = module.gen_render_data()
    nodes.compile_expr = compile_expr
    try:
        for _ in range(6):
            module.render(data)
    finally:
        nodes.compile_expr = original_compile
    for owner, reference, _, _ in switches:
        if owner._eval is not reference:
            raise RuntimeError("Captured evaluator was not stored on its node")

    def switch(candidate: bool) -> None:
        for owner, reference, changed, _ in switches:
            owner._eval = changed if candidate else reference

    snapshot = OwnershipGraph.snapshot
    traces = {}
    counts: Counter[str] = Counter()
    observations = []
    try:
        for candidate in (False, True):
            switch(candidate)
            captured = []

            def capture(graph: Any, _captured: list[Any] = captured) -> Any:
                value = snapshot(graph)
                _captured.append(value)
                return value

            OwnershipGraph.snapshot = capture
            ids._id_counter = itertools.count()
            module.render(data)
            OwnershipGraph.snapshot = snapshot
            traces[candidate] = captured
        if traces[False] != traces[True]:
            raise RuntimeError("Candidate changed ownership snapshots")
        # Count actual candidate use separately from timing.
        for owner, _, changed, source in switches:

            def count(*values: Any, _fn: Any = changed, _source: str = source) -> Any:
                counts[_source] += 1
                return _fn(*values)

            owner._eval = count
        module.render(data)
        for pair in range(args.pairs):
            outputs = {}
            for candidate in (False, True) if pair % 2 == 0 else (True, False):
                switch(candidate)
                ids._id_counter = itertools.count()
                start = time.perf_counter_ns()
                outputs[candidate] = module.render(data)
                elapsed = (time.perf_counter_ns() - start) / 1_000_000
                observations.append({"pair": pair, "candidate": candidate, "ms": elapsed})
            if outputs[False] != outputs[True]:
                raise RuntimeError(f"Candidate changed HTML in pair {pair}")
    finally:
        OwnershipGraph.snapshot = snapshot
        switch(candidate=False)
    savings = []
    for pair in range(args.pairs):
        values = {row["candidate"]: row["ms"] for row in observations if row["pair"] == pair}
        savings.append(values[False] - values[True])
    report = {
        "reference": "26312d08 safe_eval compiler",
        "python": sys.version,
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "eval_sha256": hashlib.sha256(Path(evaluator.__file__).read_bytes()).hexdigest(),
        "nodes_sha256": hashlib.sha256(Path(nodes.__file__).read_bytes()).hexdigest(),
        "pairs": args.pairs,
        "all_pairs_html_equal": True,
        "output_bytes": len(outputs[True].encode()),
        "snapshot_trace_equal": True,
        "snapshots_compared": len(traces[True]),
        "candidate_nodes": len(switches),
        "candidate_calls_per_render": sum(counts.values()),
        "candidate_calls_by_source": dict(counts),
        "medians_ms": {
            name: statistics.median(row["ms"] for row in observations if row["candidate"] == candidate)
            for name, candidate in (("reference", False), ("candidate", True))
        },
        "median_paired_saving_ms": statistics.median(savings),
        "favorable_pairs": sum(value > 0 for value in savings),
        "observations": observations,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if key not in ("observations", "candidate_calls_by_source")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
