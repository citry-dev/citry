"""Compare guarded result conversion with the unchanged production renderer."""

from __future__ import annotations

import argparse
import ast
import gc
import hashlib
import inspect
import itertools
import json
import os
import random
import statistics
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402

import citry.citry_render as renders  # noqa: E402
import citry.util.id as ids  # noqa: E402
import citry_core._rust as native  # noqa: E402
from citry import nodes  # noqa: E402
from citry.ext.i18n import bindings  # noqa: E402
from citry.ownership import OwnershipGraph  # noqa: E402

ORIGINAL = renders._render_value
TRUSTED_RENDER = renders.CitryRender
TRUSTED_PROTOCOL = renders.ComponentLike
TRUSTED_ELEMENT = renders.CitryElement
TRUSTED_REGION_PART = renders.PhysicalRegionPart
ALIASES = (renders, nodes, bindings)
SNIPPET = """    kind = type(value)
    if (
        ComponentLike is _probe_component_like
        and CitryElement is _probe_element
        and CitryRender is _probe_render
        and PhysicalRegionPart is _probe_region_part
    ):
        if kind is str and not issubclass(str, ComponentLike):
            return escape(value)
        if (
            kind is _probe_render
            and kind.__bases__ == (object,)
            and "__citry_element__" not in kind.__dict__
            and "__getattribute__" not in kind.__dict__
            and "__getattr__" not in kind.__dict__
            and "__class__" not in kind.__dict__
            and not issubclass(kind, ComponentLike)
        ):
            return value
"""


def candidate(*, counted: bool = False) -> Any:
    """Insert only the guarded branches; keep the reference body and live globals."""
    renders.__dict__.update(
        _probe_component_like=TRUSTED_PROTOCOL,
        _probe_element=TRUSTED_ELEMENT,
        _probe_render=TRUSTED_RENDER,
        _probe_region_part=TRUSTED_REGION_PART,
    )
    snippet = SNIPPET
    if counted:
        renders.__dict__["_probe_hits"] = Counter()
        snippet = snippet.replace(
            "            return escape(value)", '            _probe_hits["str"] += 1\n            return escape(value)'
        )
        snippet = snippet.replace(
            "            return value", '            _probe_hits["CitryRender"] += 1\n            return value'
        )
    anchor = "    if isinstance(value, ComponentLike):"
    source = inspect.getsource(ORIGINAL)
    if "_DEFAULT_VALUE_TYPES" in source:
        raise RuntimeError("Prototype mode requires a pre-production checkout; use --production for current code")
    if source.count(anchor) != 1:
        raise RuntimeError("Result-conversion source no longer has the expected boundary")
    source = source.replace(anchor, snippet + anchor)
    namespace = {}
    exec(  # noqa: S102 - insert the experiment into trusted local source
        compile("from __future__ import annotations\n" + source, "render-value-candidate", "exec"),
        renders.__dict__,
        namespace,
    )
    return namespace["_render_value"]


def install(function: Any) -> None:
    """Use the same implementation at each imported runtime alias."""
    for module in ALIASES:
        module._render_value = function


def reference() -> Any:
    """Load the pinned pre-production body against the same live dependencies."""
    source = subprocess.check_output(
        ["git", "show", "49852e7:packages/py/citry/citry/citry_render.py"],  # noqa: S607
        cwd=ROOT,
        text=True,
    )
    tree = ast.parse(source)
    node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "_render_value")
    function_source = ast.get_source_segment(source, node)
    namespace = {}
    exec("from __future__ import annotations\n" + function_source, renders.__dict__, namespace)  # noqa: S102
    return namespace["_render_value"]


def counted_production() -> Any:
    """Count the actual production branches in a separate untimed render."""
    tree = ast.parse(inspect.getsource(ORIGINAL))
    function = tree.body[0]
    guard = next(
        node
        for node in function.body
        if isinstance(node, ast.If) and ast.unparse(node.test).startswith("ComponentLike is _DEFAULT_VALUE_TYPES[0]")
    )
    if len(guard.body) != 2 or not all(isinstance(node, ast.If) for node in guard.body):
        raise RuntimeError("The production branch layout no longer matches the activation counter")
    renders.__dict__["_probe_hits"] = Counter()
    for node, name in zip(guard.body, ("str", "CitryRender"), strict=True):
        node.body.insert(0, ast.parse(f"_probe_hits[{name!r}] += 1").body[0])
    ast.fix_missing_locations(tree)
    namespace = {}
    exec(  # noqa: S102 - only this untimed copy receives activation counters
        "from __future__ import annotations\n" + ast.unparse(tree), renders.__dict__, namespace
    )
    return namespace["_render_value"]


def equivalence(*, production: bool) -> dict[str, Any]:
    """Compare every reached ownership snapshot as well as serialized output."""
    module = scenario()
    data = module.gen_render_data()
    baseline = reference() if production else ORIGINAL
    changed = ORIGINAL if production else candidate()
    snapshot = OwnershipGraph.snapshot
    traces, outputs = [], []
    try:
        for function in (baseline, changed):
            install(function)
            for _ in range(6):
                module.render(data)
            trace = []

            def capture(graph: Any, _trace: list[Any] = trace) -> Any:
                result = snapshot(graph)
                _trace.append(result)
                return result

            OwnershipGraph.snapshot = capture
            ids._id_counter = itertools.count()
            outputs.append(module.render(data))
            OwnershipGraph.snapshot = snapshot
            traces.append(trace)
        if not traces[0] or traces[0] != traces[1] or outputs[0] != outputs[1]:
            raise RuntimeError("Candidate changed reached snapshots or HTML")
    finally:
        OwnershipGraph.snapshot = snapshot
        install(ORIGINAL)
    return {"snapshots_equal": True, "snapshots_compared": len(traces[0]), "html_equal": True}


def worker(changed: bool, samples: int, id_base: int, *, production: bool) -> dict[str, Any]:
    """Time complete renders on a private heap with normal collection enabled."""
    ids._id_base = id_base
    ids._id_counter = itertools.count()
    if production:
        function = ORIGINAL if changed else reference()
    else:
        function = candidate() if changed else ORIGINAL
    install(function)
    module = scenario()
    data = module.gen_render_data()
    for _ in range(6):
        module.render(data)
    before = gc.get_stats()
    observations, digests = [], []
    for index in range(samples):
        ids._id_counter = itertools.count((index + 1) * 1_000_000)
        cpu_start = time.process_time_ns()
        start = time.perf_counter_ns()
        output = module.render(data)
        end = time.perf_counter_ns()
        cpu_end = time.process_time_ns()
        observations.append({"ms": (end - start) / 1_000_000, "cpu_ms": (cpu_end - cpu_start) / 1_000_000})
        digests.append(hashlib.sha256(output.encode()).hexdigest())
        del output
    after = gc.get_stats()
    hits = None
    if changed:
        install(counted_production() if production else candidate(counted=True))
        module.render(data)
        hits = dict(renders.__dict__["_probe_hits"])
        if not hits:
            raise RuntimeError("The candidate branches were never reached")
    install(ORIGINAL)
    return {
        "candidate": changed,
        "python": sys.version,
        "hash_seed": os.environ.get("PYTHONHASHSEED"),
        "id_base": id_base,
        "gc_enabled": gc.isenabled(),
        "gc_thresholds": gc.get_threshold(),
        "gc_before": before,
        "gc_after": after,
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
        "activation": hits,
        "means_ms": {key: statistics.mean(row[key] for row in observations) for key in ("ms", "cpu_ms")},
        "observations": observations,
        "html_digests": digests,
    }


def main() -> None:
    """Keep every preselected process pair and its complete sample distribution."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("reference", "candidate"))
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--pairs", type=int, default=8)
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--seed", type=int, default=20260909)
    parser.add_argument("--id-base", type=int, default=123456)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if min(args.samples, args.pairs) < 1:
        parser.error("Sample and pair counts must be positive")
    if not args.production and "_DEFAULT_VALUE_TYPES" in inspect.getsource(ORIGINAL):
        parser.error("Prototype mode requires a pre-production checkout; use --production for current code")
    if args.worker:
        print(json.dumps(worker(args.worker == "candidate", args.samples, args.id_base, production=args.production)))
        return
    if args.output is None:
        parser.error("The parent requires --output")
    semantic_check = equivalence(production=args.production)
    orders = [bool(pair % 2) for pair in range(args.pairs)]
    random.Random(args.seed).shuffle(orders)  # noqa: S311 - reproducible execution order
    pairs = []
    for pair, candidate_first in enumerate(orders):
        variants = {}
        for name in ("candidate", "reference") if candidate_first else ("reference", "candidate"):
            result = subprocess.run(
                [
                    sys.executable,
                    __file__,
                    "--worker",
                    name,
                    "--samples",
                    str(args.samples),
                    "--id-base",
                    str(args.id_base + pair * 10_000_000),
                    *(["--production"] if args.production else []),
                ],
                cwd=ROOT,
                env={**os.environ, "PYTHONHASHSEED": str(args.seed + pair)},
                capture_output=True,
                text=True,
                check=True,
            )
            variants[name] = json.loads(result.stdout)
        if variants["reference"]["html_digests"] != variants["candidate"]["html_digests"]:
            raise RuntimeError(f"HTML differs in process pair {pair}")
        if variants["reference"]["native_sha256"] != variants["candidate"]["native_sha256"]:
            raise RuntimeError("The paired processes loaded different native artifacts")
        saving = {
            key: variants["reference"]["means_ms"][key] - variants["candidate"]["means_ms"][key]
            for key in ("ms", "cpu_ms")
        }
        pairs.append({"pair": pair, "candidate_first": candidate_first, "mean_savings_ms": saving, **variants})
        print(json.dumps({"pair": pair, "mean_savings_ms": saving}), flush=True)
    report = {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),  # noqa: S607
        "production": args.production,
        "reference": "49852e7 _render_value" if args.production else "imported production _render_value",
        "order_seed": args.seed,
        "order": "balanced-random",
        "samples_per_process": args.samples,
        "warmups_per_process": 6,
        "equivalence": semantic_check,
        "all_pair_html_digests_equal": True,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__).resolve(),
                Path(renders.__file__),
                ROOT / "packages/py/citry/citry/citry_element.py",
                ROOT / "packages/py/citry/citry/component_like.py",
                ROOT / "packages/py/citry/tests/test_benchmark_citry.py",
            )
        },
        "median_process_pair_mean_savings_ms": {
            key: statistics.median(pair["mean_savings_ms"][key] for pair in pairs) for key in ("ms", "cpu_ms")
        },
        "joint_favorable_process_pairs": sum(
            all(value > 0 for value in pair["mean_savings_ms"].values()) for pair in pairs
        ),
        "pairs": pairs,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "pairs"}, indent=2))


if __name__ == "__main__":
    main()
