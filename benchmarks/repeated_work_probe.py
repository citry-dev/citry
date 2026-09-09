"""Compare repeated-render optimizations and exploratory caches."""

from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import itertools
import json
import statistics
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from shutil import which
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

import citry.component_render as runtime  # noqa: E402
import citry.util.id as ids  # noqa: E402
from benchmarks.ownership_journal_probe.probe import load_native, scenario  # noqa: E402
from benchmarks.ownership_journal_probe.storage_probe import install_storage  # noqa: E402
from citry import extension, nodes  # noqa: E402
from citry.ownership import OwnershipGraph  # noqa: E402

BASELINE = "8afbea56"


def compile_function(source: str, namespace: dict[str, Any], name: str) -> Any:
    """Compile a comparison function against the same runtime dependencies."""
    scope: dict[str, Any] = {}
    exec(compile("from __future__ import annotations\n" + source, "repeated-work-probe", "exec"), namespace, scope)  # noqa: S102
    return scope[name]


def prepare(case: str) -> tuple[list[tuple[Any, str, Any, Any]], dict[str, Any]]:
    """Describe reversible switches; the cache experiments are not production code."""
    if case == "empty-retirement":
        git = which("git")
        if git is None:
            raise RuntimeError("The empty-retirement comparison requires git")
        source = subprocess.check_output(
            [git, "show", "2412f7b0:packages/py/citry/citry/component_render.py"], cwd=ROOT, text=True
        )
        tree = ast.parse(source)
        function = next(
            item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "_settle_render"
        )
        source = ast.get_source_segment(source, function)
        if source is None:
            raise RuntimeError("Cannot extract reference settlement function")
        call = """            ownership.retire_unselected_after(
                hook_checkpoint,
                through_order=hook_through_order,
                preserved_render_ids=selected_render_ids,
                preserved_region_ids=selected_region_ids,
            )"""
        if source.count(call) != 1:
            raise RuntimeError("Hook retirement call changed; inspect before comparing")
        guarded = "            if hook_checkpoint != hook_through_order:\n" + textwrap.indent(call, "    ")
        reference = compile_function(source, runtime.__dict__, function.name)
        candidate = compile_function(source.replace(call, guarded), runtime.__dict__, function.name)
        return [(runtime, function.name, reference, candidate)], {}
    if case == "input-constness":
        git = which("git")
        if git is None:
            raise RuntimeError("The input-constness comparison requires git")
        completed = subprocess.run(
            [git, "show", "c8da9e03:packages/py/citry/citry/nodes/__init__.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        tree = ast.parse(completed.stdout)
        function = next(
            item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "_kwarg_is_const"
        )
        source = ast.get_source_segment(completed.stdout, function)
        if source is None:
            raise RuntimeError("Cannot extract baseline input constness helper")
        reference = compile_function(source, nodes.__dict__, function.name)
        return [(nodes, function.name, reference, nodes._kwarg_is_const)], {}
    if case == "source-sites":
        original = OwnershipGraph.__init__
        cache: dict[Any, Any] = {}

        def initialize(graph: Any) -> None:
            original(graph)
            graph._source_site_cache = cache

        return [(OwnershipGraph, "__init__", original, initialize)], {"source_cache": cache}
    if case == "graph-scope":
        # Retain the exact old wrapper, including error handling. Loading it
        # from git avoids adding extra Python attribute lookups to the reference.
        git = which("git")
        if git is None:
            raise RuntimeError("The graph-scope comparison requires git")
        completed = subprocess.run(
            [git, "show", f"{BASELINE}:packages/py/citry/citry/component_render.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        tree = ast.parse(completed.stdout)
        node = next(
            item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == "_render_one_traced"
        )
        source = ast.get_source_segment(completed.stdout, node)
        if source is None:
            raise RuntimeError("Cannot extract baseline graph wrapper")
        reference = compile_function(source, runtime.__dict__, node.name)
        return [(runtime, node.name, reference, runtime._render_one_traced)], {}

    edits = {
        "on_component_data": (
            """    ordered = [extension for extension in extensions if extension is not i18n]
    if i18n in extensions:
        ordered.append(i18n)""",
            """    ordered = getattr(self, '_probe_ordered', None)
    if ordered is None:
        ordered = tuple(extension for extension in extensions if extension is not i18n)
        if i18n in extensions:
            ordered += (i18n,)
        self._probe_ordered = ordered""",
        ),
        "on_component_rendered": (
            "        extensions = tuple(extension for extension in extensions if extension is not i18n)",
            """        filtered = getattr(self, '_probe_rendered', None)
        if filtered is None:
            filtered = tuple(extension for extension in extensions if extension is not i18n)
            self._probe_rendered = filtered
        extensions = filtered""",
        ),
        "_attrs_resolved_extensions": (
            "    return tuple(extension for extension in extensions "
            "if not extension._attrs_resolved_requires_runtime_candidate)",
            """    filtered = getattr(self, '_probe_attrs', None)
    if filtered is None:
        filtered = tuple(
            extension for extension in extensions if not extension._attrs_resolved_requires_runtime_candidate
        )
        self._probe_attrs = filtered
    return filtered""",
        ),
    }
    switches = []
    for name, (old, new) in edits.items():
        original = getattr(extension.ExtensionManager, name)
        source = textwrap.dedent(inspect.getsource(original))
        if source.count(old) != 1:
            raise RuntimeError(f"Hook implementation changed: {name}")
        candidate = compile_function(source.replace(old, new), extension.__dict__, name)
        switches.append((extension.ExtensionManager, name, original, candidate))
    return switches, {}


def main() -> None:
    """Alternate complete renders and retain every observation and equality check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        choices=("source-sites", "hook-subsets", "graph-scope", "input-constness", "empty-retirement"),
        required=True,
    )
    parser.add_argument("--pairs", type=int, default=60)
    parser.add_argument("--backend", choices=("production", "native-storage"), default="production")
    parser.add_argument("--tests", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.pairs < 1:
        parser.error("--pairs must be positive")
    if (args.backend != "production" or args.tests) and args.case != "empty-retirement":
        parser.error("Backend and test options require --case empty-retirement")
    switches, details = prepare(args.case)
    backend_stats = {"native_calls": 0, "fallback_calls": 0}
    restore_backend = None
    native = None
    if args.backend == "native-storage":
        native = load_native()
        enable_backend, restore_backend = install_storage(native, backend_stats)
        enable_backend()
    restores = [(owner, name, getattr(owner, name)) for owner, name, _, _ in switches]

    def switch(candidate: bool) -> None:
        for owner, name, reference, changed in switches:
            setattr(owner, name, changed if candidate else reference)

    if args.tests:
        switch(candidate=True)
        import pytest  # noqa: PLC0415

        try:
            raise SystemExit(
                pytest.main(
                    [
                        "packages/py/citry/tests/test_ownership.py",
                        "packages/py/citry/tests/test_ownership_manifest.py",
                        "packages/py/citry/tests/test_ext_cache_replay.py",
                        "-q",
                        "--no-cov",
                    ]
                )
            )
        finally:
            for owner, name, original in restores:
                setattr(owner, name, original)
            if restore_backend is not None:
                restore_backend()
    module = scenario()
    data = module.gen_render_data()
    observations = []
    snapshot = OwnershipGraph.snapshot
    traces: dict[bool, list[Any]] = {}
    windows: dict[bool, list[Any]] = {}
    retirement = OwnershipGraph.retire_unselected_after
    try:
        for candidate in (False, True):
            switch(candidate)
            for _ in range(6):
                module.render(data)
            captured: list[Any] = []

            def capture(graph: Any, _captured: list[Any] = captured) -> Any:
                value = snapshot(graph)
                _captured.append(value)
                return value

            if args.case == "empty-retirement":
                reached: list[Any] = []

                def capture_window(
                    graph: Any,
                    checkpoint: int,
                    *,
                    through_order: int,
                    preserved_render_ids: Any,
                    preserved_region_ids: Any = None,
                    _reached: list[Any] = reached,
                ) -> None:
                    _reached.append(
                        {
                            "checkpoint": checkpoint,
                            "through_order": through_order,
                            "preserved_render_ids": sorted(preserved_render_ids),
                            "preserved_region_ids": sorted(preserved_region_ids or ()),
                            "rows_in_interval": {
                                name: len(
                                    graph._ordered_indexes_between(getattr(graph, name), checkpoint, through_order)
                                )
                                for name in (
                                    "_component_invocations",
                                    "_logical_instances",
                                    "_init_ancestry",
                                    "_logical_fills",
                                    "_physical_regions",
                                )
                            },
                        }
                    )
                    retirement(
                        graph,
                        checkpoint,
                        through_order=through_order,
                        preserved_render_ids=preserved_render_ids,
                        preserved_region_ids=preserved_region_ids,
                    )

                OwnershipGraph.retire_unselected_after = capture_window
                windows[candidate] = reached
            OwnershipGraph.snapshot = capture
            ids._id_counter = itertools.count()
            module.render(data)
            OwnershipGraph.snapshot = snapshot
            OwnershipGraph.retire_unselected_after = retirement
            traces[candidate] = captured
        if not traces[False] or traces[False] != traces[True]:
            raise RuntimeError("Experiment has missing or unequal ownership snapshots")
        if args.case == "empty-retirement":
            empty = [row for row in windows[False] if row["checkpoint"] == row["through_order"]]
            remaining = [row for row in windows[False] if row["checkpoint"] != row["through_order"]]
            if not empty or windows[True] != remaining or any(any(row["rows_in_interval"].values()) for row in empty):
                raise RuntimeError("The empty retirement window was not removed as expected")
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
                raise RuntimeError(f"Experiment changed HTML in pair {pair}")
    finally:
        OwnershipGraph.snapshot = snapshot
        OwnershipGraph.retire_unselected_after = retirement
        if restore_backend is not None:
            restore_backend()
        # Restore the exact imported functions even when the reference came from git.
        for owner, name, original in restores:
            setattr(owner, name, original)
    medians = {
        name: statistics.median(row["ms"] for row in observations if row["candidate"] == candidate)
        for name, candidate in (("reference", False), ("candidate", True))
    }
    savings = []
    for pair in range(args.pairs):
        values = {row["candidate"]: row["ms"] for row in observations if row["pair"] == pair}
        savings.append(values[False] - values[True])
    cache = details.get("source_cache", {})
    report = {
        "case": args.case,
        "backend": args.backend,
        "backend_stats": backend_stats,
        "retirement_windows": windows,
        "storage_adapter_sha256": hashlib.sha256(
            (ROOT / "benchmarks/ownership_journal_probe/storage_probe.py").read_bytes()
        ).hexdigest()
        if native is not None
        else None,
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest()
        if native is not None
        else None,
        "reference": (
            "2412f7b0 settlement function"
            if args.case == "empty-retirement"
            else "c8da9e03 input constness helper"
            if args.case == "input-constness"
            else BASELINE + " wrapper"
            if args.case == "graph-scope"
            else "current runtime"
        ),
        "nodes_sha256": hashlib.sha256(Path(nodes.__file__).read_bytes()).hexdigest(),
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "runtime_sha256": hashlib.sha256(Path(runtime.__file__).read_bytes()).hexdigest(),
        "python": sys.version,
        "pairs": args.pairs,
        "all_pairs_html_equal": True,
        "snapshots_compared": len(traces[True]),
        "snapshot_trace_equal": True,
        "medians_ms": medians,
        "median_paired_saving_ms": statistics.median(savings),
        "favorable_pairs": sum(value > 0 for value in savings),
        "shared_source_sites": len(cache),
        "shared_distinct_source_bytes": sum(len(source.encode()) for source in {key[0] for key in cache}),
        "observations": observations,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "observations"}, indent=2))


if __name__ == "__main__":
    main()
