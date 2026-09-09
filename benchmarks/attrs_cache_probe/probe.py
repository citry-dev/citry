"""Compare a bounded final-attribute cache with the production formatter."""

from __future__ import annotations

import argparse
import ast
import gc
import hashlib
import itertools
import json
import random
import statistics
import subprocess
import sys
import textwrap
import time
from functools import lru_cache
from pathlib import Path
from shutil import which
from typing import Any, NamedTuple

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402

import citry.util.id as ids  # noqa: E402
from citry import attrs, nodes  # noqa: E402
from citry.ownership import OwnershipGraph  # noqa: E402
from citry.util import html  # noqa: E402


def reference_node_formatter() -> Any:
    """Load the exact pre-production method against the same live dependencies."""
    git = which("git")
    if git is None:
        raise RuntimeError("The production comparison requires git")
    source = subprocess.check_output(
        [git, "show", "5bad7af8:packages/py/citry/citry/nodes/__init__.py"], cwd=ROOT, text=True
    )
    tree = ast.parse(source)
    cls = next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == "ElementAttrsNode")
    method = next(item for item in cls.body if isinstance(item, ast.FunctionDef) and item.name == "_format")
    method_source = ast.get_source_segment(source, method)
    if method_source is None:
        raise RuntimeError("Cannot extract the original attribute node formatter")
    namespace = {}
    exec(  # noqa: S102 - trusted source from the pinned repository revision
        compile("from __future__ import annotations\n" + textwrap.dedent(method_source), "attrs-reference", "exec"),
        nodes.__dict__,
        namespace,
    )
    return namespace["_format"]


def production_activation(module: Any, data: Any) -> dict[str, int]:
    """Count production cache hits in one separate, untimed render."""
    original = nodes._attrs_output_cache

    class CountedCache(dict):
        hits = 0
        misses = 0

        def get(self, key: Any, default: Any = None) -> Any:
            result = super().get(key, default)
            if result is None:
                self.misses += 1
            else:
                self.hits += 1
            return result

    counted = CountedCache(original)
    nodes._attrs_output_cache = counted
    try:
        module.render(data)
    finally:
        nodes._attrs_output_cache = original
    if counted.hits == 0 or len(counted) > 256:
        raise RuntimeError("Production cache activation or retention check failed")
    return {"hits": counted.hits, "misses": counted.misses, "entries": len(counted), "max_entries": 256}


def candidate_formatter(original: Any) -> tuple[Any, Any]:
    """Keep bounded immutable keys, using the original formatter for misses."""
    helper_names = ("_underlying", "_html_attr_identity", "escape_to_str", "normalize_class", "normalize_style")
    helpers = tuple(getattr(attrs, name) for name in helper_names)
    escape_backend = html._escape_to_str_impl
    escape_public = html.escape

    @lru_cache(maxsize=256)
    def cached(key: tuple[tuple[str, type, Any], ...]) -> str:
        return original({name: value for name, _, value in key})

    def format_cached(values: Any) -> str:
        if (
            type(values) is not dict
            or len(values) > 16
            or attrs._underlying is not helpers[0]
            or attrs._html_attr_identity is not helpers[1]
            or attrs.escape_to_str is not helpers[2]
            or attrs.normalize_class is not helpers[3]
            or attrs.normalize_style is not helpers[4]
            or html._escape_to_str_impl is not escape_backend
            or html.escape is not escape_public
        ):
            return original(values)
        key = []
        chars = 0
        for name, value in values.items():
            if type(name) is not str:
                return original(values)
            chars += len(name)
            kind = type(value)
            if kind is str:
                chars += len(value)
            elif kind is int:
                if value.bit_length() > 256:
                    return original(values)
            elif value is not None and kind is not bool:
                return original(values)
            if chars > 2048:
                return original(values)
            key.append((name, kind, value))
        return cached(tuple(key))

    return format_cached, cached


def candidate_node_formatter(original: Any) -> tuple[Any, Any]:
    """Cache whole node output without retaining nodes, contexts or mutable maps."""
    expected = (
        attrs._underlying,
        attrs._html_attr_identity,
        attrs.escape_to_str,
        attrs.normalize_class,
        attrs.normalize_style,
        html._escape_to_str_impl,
        html.escape,
        nodes.format_attrs,
        nodes._format_resolved_attrs_to_str,
        nodes.validate_html_attr_name,
        attrs.validate_html_attr_name,
        attrs.Markup,
        attrs._format_resolved_attrs_to_str,
    )
    entries: dict[Any, str] = {}
    hits = misses = 0

    class CacheInfo(NamedTuple):
        hits: int
        misses: int
        maxsize: int
        currsize: int

    def format_node(self: Any, resolved: Any, context: Any, *, validate_keys: bool = True) -> Any:
        nonlocal hits, misses
        if (
            type(self) is not nodes.ElementAttrsNode
            or type(resolved) is not dict
            or len(resolved) > 16
            or type(validate_keys) is not bool
            or (validate_keys and type(self._tag_name) is not str)
            or attrs._underlying is not expected[0]
            or attrs._html_attr_identity is not expected[1]
            or attrs.escape_to_str is not expected[2]
            or attrs.normalize_class is not expected[3]
            or attrs.normalize_style is not expected[4]
            or html._escape_to_str_impl is not expected[5]
            or html.escape is not expected[6]
            or nodes.format_attrs is not expected[7]
            or nodes._format_resolved_attrs_to_str is not expected[8]
            or nodes.validate_html_attr_name is not expected[9]
            or attrs.validate_html_attr_name is not expected[10]
            or attrs.Markup is not expected[11]
            or attrs._format_resolved_attrs_to_str is not expected[12]
        ):
            return original(self, resolved, context, validate_keys=validate_keys)
        items = []
        chars = 0
        for name, value in resolved.items():
            if type(name) is not str:
                return original(self, resolved, context, validate_keys=validate_keys)
            chars += len(name)
            kind = type(value)
            if kind is str:
                chars += len(value)
            elif kind is int:
                if value.bit_length() > 256:
                    return original(self, resolved, context, validate_keys=validate_keys)
            elif value is not None and kind is not bool:
                return original(self, resolved, context, validate_keys=validate_keys)
            if chars > 2048:
                return original(self, resolved, context, validate_keys=validate_keys)
            items.append((name, kind, value))
        key = (validate_keys, tuple(items))
        result = entries.get(key)
        if result is not None:
            hits += 1
            return result
        misses += 1
        result = original(self, resolved, context, validate_keys=validate_keys)
        if type(result) not in (str, attrs.Markup):
            raise RuntimeError("Eligible node formatting unexpectedly returned a structural value")
        if len(entries) >= 256:
            entries.pop(next(iter(entries)))
        entries[key] = result
        return result

    class CacheView:
        @staticmethod
        def cache_info() -> Any:
            return CacheInfo(hits, misses, 256, len(entries))

    return format_node, CacheView


def main() -> None:
    """Retain complete-render timings, equality checks and cache activation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundary", choices=("formatter", "node", "production"), default="formatter")
    parser.add_argument("--pairs", type=int, default=60)
    parser.add_argument("--tests", action="store_true")
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--order", choices=("alternating", "balanced-random"), default="alternating")
    parser.add_argument("--seed", type=int, default=20260909)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.pairs < 1:
        parser.error("--pairs must be positive")
    original = attrs._format_resolved_attrs_to_str
    original_node = nodes._format_resolved_attrs_to_str
    if original_node is not original:
        raise RuntimeError("The formatter aliases must match before this comparison")
    original_node_method = nodes.ElementAttrsNode._format
    reference_node = reference_node_formatter() if args.boundary == "production" else original_node_method
    changed, cache = (
        (original_node_method, None)
        if args.boundary == "production"
        else candidate_node_formatter(original_node_method)
        if args.boundary == "node"
        else candidate_formatter(original)
    )

    def switch(candidate: bool) -> None:
        if args.boundary in ("node", "production"):
            nodes.ElementAttrsNode._format = changed if candidate else reference_node
        else:
            attrs._format_resolved_attrs_to_str = changed if candidate else original
            nodes._format_resolved_attrs_to_str = changed if candidate else original_node

    if args.tests:
        import pytest  # noqa: PLC0415

        switch(candidate=True)
        try:
            raise SystemExit(
                pytest.main(
                    [
                        "packages/py/citry/tests/test_attrs.py",
                        "packages/py/citry/tests/test_attrs_template.py",
                        "packages/py/citry/tests/test_ownership.py",
                        "-q",
                        "--no-cov",
                    ]
                )
            )
        finally:
            attrs._format_resolved_attrs_to_str = original
            nodes._format_resolved_attrs_to_str = original_node
            nodes.ElementAttrsNode._format = original_node_method

    module = scenario()
    data = module.gen_render_data()
    snapshot = OwnershipGraph.snapshot
    traces: dict[bool, list[Any]] = {}
    observations = []
    orders = [bool(pair % 2) for pair in range(args.pairs)]
    if args.order == "balanced-random":
        random.Random(args.seed).shuffle(orders)  # noqa: S311 - reproducible execution order
    gc_events: list[dict[str, int]] = []
    gc_starts: dict[int, int] = {}
    record_gc = False

    def observe_gc(phase: str, info: dict[str, Any]) -> None:
        if not record_gc:
            return
        generation = info["generation"]
        if phase == "start":
            gc_starts[generation] = time.perf_counter_ns()
        else:
            gc_events.append(
                {
                    "generation": generation,
                    "ns": time.perf_counter_ns() - gc_starts.pop(generation),
                    "collected": info["collected"],
                    "uncollectable": info["uncollectable"],
                }
            )

    if args.diagnostic:
        gc.callbacks.append(observe_gc)
    try:
        for candidate in (False, True):
            switch(candidate)
            for _ in range(6):
                module.render(data)
            captured = []

            def capture(graph: Any, _captured: list[Any] = captured) -> Any:
                result = snapshot(graph)
                _captured.append(result)
                return result

            OwnershipGraph.snapshot = capture
            ids._id_counter = itertools.count()
            module.render(data)
            traces[candidate] = captured
            OwnershipGraph.snapshot = snapshot
        if not traces[False] or traces[False] != traces[True]:
            raise RuntimeError("Missing or unequal ownership snapshots")
        switch(candidate=True)
        if args.boundary == "production":
            activation = production_activation(module, data)
        else:
            before = cache.cache_info()
            module.render(data)
            after = cache.cache_info()
            activation = {
                "hits": after.hits - before.hits,
                "misses": after.misses - before.misses,
                "entries": after.currsize,
                "max_entries": after.maxsize,
            }
            if not activation["hits"] or after.currsize > 256:
                raise RuntimeError("Cache is inactive or exceeds its entry bound")
        for pair in range(args.pairs):
            outputs = {}
            for candidate in (True, False) if orders[pair] else (False, True):
                switch(candidate)
                ids._id_counter = itertools.count((pair + 1) * 1_000_000)
                if args.diagnostic:
                    gc_events.clear()
                    cpu_start = time.process_time_ns()
                    record_gc = True
                start = time.perf_counter_ns()
                outputs[candidate] = module.render(data)
                finished = time.perf_counter_ns()
                record_gc = False
                cpu_finished = time.process_time_ns() if args.diagnostic else 0
                elapsed = (finished - start) / 1_000_000
                record = {"pair": pair, "candidate": candidate, "candidate_first": orders[pair], "ms": elapsed}
                if args.diagnostic:
                    record["cpu_ms"] = (cpu_finished - cpu_start) / 1_000_000
                    record["gc_events"] = list(gc_events)
                observations.append(record)
            if outputs[False] != outputs[True]:
                raise RuntimeError(f"HTML differs in pair {pair}")
    finally:
        OwnershipGraph.snapshot = snapshot
        attrs._format_resolved_attrs_to_str = original
        nodes._format_resolved_attrs_to_str = original_node
        nodes.ElementAttrsNode._format = original_node_method
        if args.diagnostic:
            gc.callbacks.remove(observe_gc)
    savings = []
    for pair in range(args.pairs):
        values = {row["candidate"]: row["ms"] for row in observations if row["pair"] == pair}
        savings.append(values[False] - values[True])
    git = which("git")
    report = {
        "revision": subprocess.check_output([git, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() if git else None,
        "python": sys.version,
        "boundary": args.boundary,
        "reference": "5bad7af8 ElementAttrsNode._format" if args.boundary == "production" else "imported runtime",
        "id_schedule": "distinct start per pair; same start within each pair",
        "order": args.order,
        "order_seed": args.seed if args.order == "balanced-random" else None,
        "diagnostic": args.diagnostic,
        "hashes": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (Path(__file__), Path(attrs.__file__), Path(nodes.__file__), Path(html.__file__))
        },
        "pairs": args.pairs,
        "all_pairs_html_equal": True,
        "snapshot_trace_equal": True,
        "snapshots_compared": len(traces[True]),
        "activation": activation,
        "medians_ms": {
            name: statistics.median(row["ms"] for row in observations if row["candidate"] == candidate)
            for name, candidate in (("reference", False), ("candidate", True))
        },
        "median_paired_saving_ms": statistics.median(savings),
        "favorable_pairs": sum(value > 0 for value in savings),
        "observations": observations,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "observations"}, indent=2))


if __name__ == "__main__":
    main()
