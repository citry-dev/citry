"""Measure an experimental combined invocation/queue journal in real renders."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import itertools
import json
import statistics
import subprocess
import sys
import time
import types
from importlib.machinery import ExtensionFileLoader
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.utils import get_benchmark_script  # noqa: E402

import citry.ownership as own  # noqa: E402
import citry.util.id as ids  # noqa: E402


class Table:
    """Materialize immutable rows only when existing Python readers need them."""

    def __init__(self, journal: Any, *, queue: bool) -> None:
        self.journal = journal
        self.read = journal.queue if queue else journal.invocation
        self.read_all = journal.queues if queue else journal.invocations
        self.write = journal.set_queue if queue else journal.set_invocation

    def __len__(self) -> int:
        return len(self.journal)

    def __iter__(self) -> Any:
        return iter(self.read_all())

    def __getitem__(self, index: int) -> Any:
        return self.read(index)

    def __setitem__(self, index: int, value: Any) -> None:
        self.write(index, value)


def install(
    native: Any,
    *,
    bulk_retirement: bool = False,
    native_retirement: bool = False,
    retirement_stats: dict[str, int] | None = None,
) -> tuple[Any, Any]:
    """Return switches for the native experiment and unchanged Python reference."""
    graph = own.OwnershipGraph
    names = (
        "__init__",
        "record_component_invocation",
        "bind_instance",
        "settle_component",
        "import_replayed_snapshot",
        "retire_component_output",
    )
    originals = {name: getattr(graph, name) for name in names}

    def initialize(self: Any) -> None:
        originals["__init__"](self)
        journal = native.Journal(
            own.ComponentInvocationRecord,
            own.RenderQueueRecord,
            own.OwnershipState.ACTIVE,
            own.QueueState.ENQUEUED,
            own.QueueState.RENDERED,
        )
        self._component_invocations = Table(journal, queue=False)
        self._render_queue = Table(journal, queue=True)

    def capture(
        self: Any,
        context: Any,
        *,
        authored_tag: str,
        target_class_id: str,
        morph_key: Any,
        morph_mode: Any,
        source: Any,
        position: Any,
        client_bindings: Any,
    ) -> Any:
        table = self._component_invocations
        if not isinstance(table, Table):
            return originals["record_component_invocation"](
                self,
                context,
                authored_tag=authored_tag,
                target_class_id=target_class_id,
                morph_key=morph_key,
                morph_mode=morph_mode,
                source=source,
                position=position,
                client_bindings=client_bindings,
            )
        component = context.component
        if component is None:
            raise RuntimeError("A component invocation requires a component-owned render context.")
        source_id = self.record_source_location(
            context,
            kind=own.SourceLocationKind.COMPONENT_CALL,
            source=source,
            position=position,
        )
        self._invocation_id += 1
        invocation_id = own.ComponentInvocationId(self._invocation_id)
        values = (
            invocation_id,
            self._next_order(),
            component.id,
            component._citry_class_id,
            source_id,
            authored_tag,
            target_class_id,
            morph_key,
            morph_mode,
            None,
            self.current_region_id(),
            client_bindings,
        )
        index = table.journal.capture(values, self._next_order())
        self._invocation_index[invocation_id] = index
        self._queue_index[invocation_id] = index
        self._relation_indexes_current = False
        return invocation_id

    def bind(self: Any, component: Any, element: Any) -> None:
        table = self._component_invocations
        invocation_id = element.ownership_invocation_id
        if not isinstance(table, Table) or invocation_id is None:
            originals["bind_instance"](self, component, element)
            return
        selector = element.forward_ownership_invocation
        parent = table.journal.bind(
            self._invocation_index[invocation_id],
            component._citry_class_id,
            component.id,
            0 if selector else self._next_order(),
            selector,
        )
        if not selector:
            self._instance_invocation[component.id] = invocation_id
            self._init_ancestry.append(
                own.InitAncestryRecord(self._next_order(), invocation_id, parent, component.id),
            )
        self._logical_instances.append(
            own.LogicalInstanceRecord(
                self._next_order(),
                component.id,
                component._citry_class_id,
                type(component).__name__,
                None if selector else invocation_id,
                parent,
                type(component).transparent,
            ),
        )
        self._relation_indexes_current = False

    def settle(self: Any, render_id: str, *, failed: bool = False) -> None:
        table = self._render_queue
        if not isinstance(table, Table) or failed:
            originals["settle_component"](self, render_id, failed=failed)
            return
        invocation_id = self._instance_invocation.get(render_id)
        if invocation_id is not None:
            table.journal.settle(self._queue_index[invocation_id], self._next_order(), own.QueueState.SETTLED)

    def replay(self: Any, *args: Any, **kwargs: Any) -> Any:
        # Replay imports have more general relationships than this prototype.
        # Include conversion cost and let the proven Python path own the rest.
        self._component_invocations = list(self._component_invocations)
        self._render_queue = list(self._render_queue)
        return originals["import_replayed_snapshot"](self, *args, **kwargs)

    retirement = originals["retire_component_output"]
    if bulk_retirement:
        # Keep closure semantics identical and move only the final paired
        # invocation/queue mutations into one call. The reference is executable.
        tree = ast.parse(Path(own.__file__).read_text())
        owner = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "OwnershipGraph")
        method = next(
            node for node in owner.body if isinstance(node, ast.FunctionDef) and node.name == "retire_component_output"
        )
        loop = next(
            node
            for node in method.body
            if isinstance(node, ast.For)
            and isinstance(node.iter, ast.Name)
            and node.iter.id == "retired_invocation_ids"
        )
        replacement = ast.parse("""
if isinstance(self._component_invocations, _ProbeTable):
    self._order = self._component_invocations.journal.retire_many(
        [self._invocation_index[key] for key in retired_invocation_ids],
        self._order, OwnershipState.RETIRED, QueueState.RETIRED, QueueState.FAILED,
    )
else:
    for invocation_id in retired_invocation_ids:
        self.retire_invocation(invocation_id)
""").body[0]
        method.body[method.body.index(loop)] = replacement
        module = ast.Module(
            body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), method],
            type_ignores=[],
        )
        ast.fix_missing_locations(module)
        own._ProbeTable = Table
        scope: dict[str, Any] = {}
        exec(compile(module, "ownership-journal-retirement-probe", "exec"), own.__dict__, scope)  # noqa: S102
        retirement = scope["retire_component_output"]
    if native_retirement:

        def retirement(
            self: Any,
            render_id: str,
            *,
            through_order: int,
            descendant_render_ids: Any = None,
            preserved_render_ids: Any = None,
            preserved_region_ids: Any = None,
        ) -> None:
            table = self._component_invocations
            if isinstance(table, Table):
                try:
                    changes = table.journal.retire_output(
                        (self._logical_instances, self._init_ancestry, self._logical_fills, self._physical_regions),
                        (
                            render_id,
                            through_order,
                            set(descendant_render_ids or ()),
                            set(preserved_render_ids or ()),
                            set(preserved_region_ids or ()),
                        ),
                        self._order,
                        (
                            own.RegionState.CAPTURED,
                            own.OwnershipState.RETIRED,
                            own.QueueState.RETIRED,
                            own.QueueState.FAILED,
                        ),
                    )
                except native.UnsupportedRetirement:
                    # Only rejected input types may fall back; execution failures
                    # must propagate because a native update may have begun.
                    if retirement_stats is not None:
                        retirement_stats["fallback_calls"] += 1
                else:
                    if retirement_stats is not None:
                        retirement_stats["native_calls"] += 1
                    (self._order, instances, edges, fills, regions, promotions, region_promotions) = changes
                    for index in instances:
                        self._logical_instances[index] = self._logical_instances[index]._with_state(
                            own.OwnershipState.RETIRED
                        )
                    for index in edges:
                        self._init_ancestry[index] = self._init_ancestry[index]._with_state(own.OwnershipState.RETIRED)
                    for index, receiver, class_id in promotions:
                        fill = self._logical_fills[index]
                        self._logical_fills[index] = fill._with_receiver(
                            receiver, class_id, state=own.OwnershipState.ACTIVE
                        )
                        self._receiver_fill[(receiver, fill.slot_name)] = fill.id
                    for index, receiver in region_promotions:
                        self._physical_regions[index] = self._physical_regions[index]._with_receiver(receiver)
                    for index in fills:
                        self._logical_fills[index] = self._logical_fills[index]._with_state(own.OwnershipState.RETIRED)
                    for index in regions:
                        self._physical_regions[index] = self._physical_regions[index]._with_state(
                            own.RegionState.RETIRED
                        )
                    # Existing Python readers rebuild their own indexes on demand.
                    if region_promotions:
                        self._relation_indexes_current = False
                    return
            originals["retire_component_output"](
                self,
                render_id,
                through_order=through_order,
                descendant_render_ids=descendant_render_ids,
                preserved_render_ids=preserved_render_ids,
                preserved_region_ids=preserved_region_ids,
            )

    replacements = dict(zip(names, (initialize, capture, bind, settle, replay, retirement), strict=True))

    def switch(methods: dict[str, Any]) -> None:
        for name, method in methods.items():
            setattr(graph, name, method)

    return lambda: switch(replacements), lambda: switch(originals)


def load_native() -> Any:
    """Load this experiment's release artifact without replacing citry_core."""
    folder = Path(__file__).resolve().parent / "target/release"
    suffix = ".dylib" if sys.platform == "darwin" else ".so"
    path = folder / f"libcitry_ownership_journal_probe{suffix}"
    name = "citry_ownership_journal_probe"
    spec = importlib.util.spec_from_file_location(name, path, loader=ExtensionFileLoader(name, str(path)))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load native journal probe at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scenario() -> types.ModuleType:
    """Build the existing large scenario, excluding only its pytest wrapper."""
    path = ROOT / "packages/py/citry/tests/test_benchmark_citry.py"
    module = types.ModuleType("ownership_journal_scenario")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(get_benchmark_script(path), str(path), "exec"), module.__dict__)  # noqa: S102
    return module


def check_journal_contracts(native: Any) -> None:
    """Check retained snapshots and failed-queue ordering before the suite."""

    def check_equal(actual: Any, expected: Any) -> None:
        if actual != expected:
            raise AssertionError(f"Expected {expected!r}, got {actual!r}")

    journal = native.Journal(
        own.ComponentInvocationRecord,
        own.RenderQueueRecord,
        own.OwnershipState.ACTIVE,
        own.QueueState.ENQUEUED,
        own.QueueState.RENDERED,
    )
    index = journal.capture((1, 1, "parent", "Parent", 1, "child", "Child", None, None, None, None, ()), 2)
    initial_invocation = journal.invocation(index)
    initial_queue = journal.queue(index)
    check_equal(journal.bind(index, "Child", "child", 3, selector=False), "parent")
    bound_invocation = journal.invocation(index)
    bound_queue = journal.queue(index)
    check_equal(initial_invocation.target_render_id, None)
    check_equal(initial_queue.target_render_id, None)
    check_equal(bound_invocation.target_render_id, "child")
    check_equal(bound_queue.rendered_order, 3)
    check_equal(
        journal.retire_many([index], 3, own.OwnershipState.RETIRED, own.QueueState.RETIRED, own.QueueState.FAILED), 4
    )
    check_equal(bound_invocation.state, own.OwnershipState.ACTIVE)
    check_equal(bound_queue.state, own.QueueState.RENDERED)
    check_equal(journal.queue(index).settled_order, 4)
    journal.settle(index, 5, own.QueueState.FAILED)
    failed_queue = journal.queue(index)
    check_equal(
        journal.retire_many([index], 5, own.OwnershipState.RETIRED, own.QueueState.RETIRED, own.QueueState.FAILED), 5
    )
    check_equal(journal.queue(index), failed_queue)
    journal.settle(index, 6, own.QueueState.SETTLED)
    order = journal.retire_many(
        [index], 2**64 - 1, own.OwnershipState.RETIRED, own.QueueState.RETIRED, own.QueueState.FAILED
    )
    check_equal(order, 2**64)
    if journal.queue(index).settled_order is not order:
        raise AssertionError("Retirement must retain the resulting Python order object")


def main() -> None:
    """Compare complete renders or run focused contracts with the experiment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", action="store_true")
    parser.add_argument("--pairs", type=int, default=40)
    parser.add_argument("--bulk-retirement", action="store_true")
    parser.add_argument("--native-retirement", action="store_true")
    parser.add_argument("--reference-bulk", action="store_true")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "benchmarks/results/performance-render/combined-journal-probe.json"
    )
    args = parser.parse_args()
    native = load_native()
    retirement_stats = {"native_calls": 0, "fallback_calls": 0}
    enable, disable = install(
        native,
        bulk_retirement=args.bulk_retirement,
        native_retirement=args.native_retirement,
        retirement_stats=retirement_stats,
    )
    if args.reference_bulk:
        disable, _ = install(native, bulk_retirement=True)
    if args.tests:
        check_journal_contracts(native)
        enable()
        import pytest  # noqa: PLC0415

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
    module = scenario()
    data = module.gen_render_data()
    for _ in range(6):
        module.render(data)
    # Compare every snapshot reached by a complete render outside the timer.
    # Equal HTML alone cannot establish that retired history stayed identical.
    snapshot = own.OwnershipGraph.snapshot
    traces: dict[bool, list[Any]] = {}
    for candidate in (False, True):
        (enable if candidate else disable)()
        captured: list[Any] = []

        def capture_snapshot(graph: Any, _captured: list[Any] = captured) -> Any:
            value = snapshot(graph)
            _captured.append(value)
            return value

        own.OwnershipGraph.snapshot = capture_snapshot
        try:
            ids._id_counter = itertools.count()
            module.render(data)
        finally:
            own.OwnershipGraph.snapshot = snapshot
        traces[candidate] = captured
    if traces[False] != traces[True]:
        raise RuntimeError("Journal changed captured ownership snapshots")
    observations = []
    outputs = {}
    for pair in range(args.pairs):
        for candidate in (False, True) if pair % 2 == 0 else (True, False):
            (enable if candidate else disable)()
            ids._id_counter = itertools.count()
            start = time.perf_counter_ns()
            html = module.render(data)
            elapsed = (time.perf_counter_ns() - start) / 1_000_000
            outputs[candidate] = html
            observations.append({"pair": pair, "candidate": candidate, "ms": elapsed})
        if outputs[False] != outputs[True]:
            raise RuntimeError(f"Journal changed HTML in pair {pair}")
    probe_root = Path(__file__).resolve().parent
    suffix = ".dylib" if sys.platform == "darwin" else ".so"
    recorded_paths = [
        probe_root / "probe.py",
        probe_root / "src/lib.rs",
        ROOT / "crates/citry_ownership/src/lib.rs",
        ROOT / "crates/citry_ownership/Cargo.toml",
        ROOT / "Cargo.toml",
        ROOT / "Cargo.lock",
        probe_root / "src/retirement.rs",
        probe_root / f"target/release/libcitry_ownership_journal_probe{suffix}",
        Path(own.__file__),
    ]
    report = {
        "git_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"],  # noqa: S607 - Developer-shell repository tool.
            cwd=ROOT,
            text=True,
        ).strip(),
        "file_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in recorded_paths
        },
        "reference_mode": "combined journal with bulk retirement" if args.reference_bulk else "production Python",
        "python": sys.version,
        "pairs": args.pairs,
        "all_pairs_html_equal": True,
        "snapshot_trace_equal": True,
        "snapshots_compared": len(traces[True]),
        "output_bytes": len(outputs[True].encode()),
        "replay_implementation": "materialize tables and use Python reference",
        "bulk_retirement": args.bulk_retirement,
        "native_retirement": args.native_retirement,
        "retirement_counts": retirement_stats,
        "observations": observations,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    for candidate in (False, True):
        median = statistics.median(row["ms"] for row in observations if row["candidate"] == candidate)
        print(f"candidate={candidate}: {median:.4f} ms")


if __name__ == "__main__":
    main()
