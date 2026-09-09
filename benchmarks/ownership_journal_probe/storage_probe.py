"""Compare direct native ownership storage with production or the earlier journal."""

from __future__ import annotations

import argparse
import ast
import enum
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
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.ownership_journal_probe.probe import install, load_native, scenario  # noqa: E402

import citry.ownership as own  # noqa: E402
import citry.util.id as ids  # noqa: E402

TABLES = {
    "_logical_instances": own.LogicalInstanceRecord,
    "_init_ancestry": own.InitAncestryRecord,
    "_logical_fills": own.LogicalFillRecord,
    "_physical_regions": own.PhysicalRegionRequestRecord,
}


def transform(original: Any, native: Any) -> Any:
    """Keep control flow while replacing capture constructors and selected copies."""
    factories = {factory.__name__: factory for factory in TABLES.values()}
    tree = ast.parse(textwrap.dedent(inspect.getsource(original)))
    method = tree.body[0]
    tuple_names = {
        item.targets[0].id
        for item in ast.walk(method)
        if isinstance(item, ast.Assign)
        and len(item.targets) == 1
        and isinstance(item.targets[0], ast.Name)
        and isinstance(item.value, ast.Call)
        and isinstance(item.value.func, ast.Name)
        and item.value.func.id in factories
    }

    class Rewrite(ast.NodeTransformer):
        def visit_Call(self, item: ast.Call) -> ast.AST:
            if isinstance(item.func, ast.Name) and item.func.id in factories:
                factory = factories[item.func.id]
                fields = factory._fields
                values = list(item.args)
                if item.keywords:
                    names = [keyword.arg for keyword in item.keywords]
                    if names != list(fields[len(values) : len(values) + len(names)]):
                        raise RuntimeError("Record field evaluation order changed")
                    values.extend(keyword.value for keyword in item.keywords)
                for name in fields[len(values) :]:
                    default = factory._field_defaults[name]
                    values.append(
                        ast.Attribute(
                            value=ast.Name(id=type(default).__name__, ctx=ast.Load()),
                            attr=default.name,
                            ctx=ast.Load(),
                        )
                        if isinstance(default, enum.Enum)
                        else ast.Constant(value=default)
                    )
                return ast.Tuple(elts=values, ctx=ast.Load())
            if (
                isinstance(item.func, ast.Attribute)
                and item.func.attr == "append"
                and isinstance(item.func.value, ast.Attribute)
                and item.func.value.attr in TABLES
                and len(item.args) == 1
                and (
                    (isinstance(item.args[0], ast.Name) and item.args[0].id in tuple_names)
                    or (
                        isinstance(item.args[0], ast.Call)
                        and isinstance(item.args[0].func, ast.Name)
                        and item.args[0].func.id in factories
                    )
                )
            ):
                item.func.attr = "append_values"
            return self.generic_visit(item)

        def visit_Assign(self, item: ast.Assign) -> ast.AST:
            if (
                len(item.targets) != 1
                or not isinstance(item.targets[0], ast.Subscript)
                or not isinstance(item.targets[0].value, ast.Attribute)
                or item.targets[0].value.attr not in TABLES
                or not isinstance(item.value, ast.Call)
                or not isinstance(item.value.func, ast.Attribute)
            ):
                return self.generic_visit(item)
            target = item.targets[0]
            call = item.value
            fields = TABLES[target.value.attr]._fields
            changed = {
                "_with_state": ["state"],
                "_with_source_invocation": ["source_invocation_id"],
                "_with_result_owner": ["result_owner_render_id"],
                "_with_receiver": ["receiver_render_id", "receiver_class_id"],
            }.get(call.func.attr)
            if changed is None or call.keywords or len(call.args) != len(changed):
                raise RuntimeError(f"Unqualified record mutation: {ast.unparse(item)}")
            patches = ast.Tuple(
                elts=[
                    ast.Tuple(elts=[ast.Constant(value=fields.index(name)), value], ctx=ast.Load())
                    for name, value in zip(changed, call.args, strict=True)
                ],
                ctx=ast.Load(),
            )
            patch = ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(value=target.value, attr="patch", ctx=ast.Load()),
                    args=[target.slice, patches],
                    keywords=[],
                )
            )
            # A slot callback can replay into this graph and materialize its
            # tables after entry. Choose storage again at the mutation itself.
            return ast.If(
                test=ast.Call(
                    func=ast.Name(id="isinstance", ctx=ast.Load()),
                    args=[target.value, ast.Name(id="_StorageTable", ctx=ast.Load())],
                    keywords=[],
                ),
                body=[patch],
                orelse=[item],
            )

    method = Rewrite().visit(method)
    # Replay converts tables back to lists; use the untouched implementation
    # from that point onward without changing methods for other live graphs.
    signature = inspect.signature(original)
    positional = []
    keywords = []
    for name, parameter in signature.parameters.items():
        value = ast.Name(id=name, ctx=ast.Load())
        if parameter.kind == parameter.KEYWORD_ONLY:
            keywords.append(ast.keyword(arg=name, value=value))
        else:
            positional.append(value)
    fallback = ast.parse("if not isinstance(self._logical_instances, _StorageTable):\n    pass").body[0]
    fallback.body = [
        ast.Return(
            value=ast.Call(func=ast.Name(id="_storage_original", ctx=ast.Load()), args=positional, keywords=keywords)
        )
    ]
    method.body.insert(1 if isinstance(method.body[0], ast.Expr) else 0, fallback)
    tree.body.insert(0, ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0))
    ast.fix_missing_locations(tree)
    namespace = {**own.__dict__, "_StorageTable": native.RecordTable, "_storage_original": original}
    exec(compile(tree, "ownership-storage-probe", "exec"), namespace)  # noqa: S102
    return namespace[original.__name__]


def install_storage(native: Any, stats: dict[str, int], *, native_ancestors: bool = False) -> tuple[Any, Any]:
    """Install reversible table/capture changes without touching shipped sources."""
    graph = own.OwnershipGraph
    rewritten = (
        "_append_fill",
        "capture_slot_call",
        "bind_template_fill_sources",
        "bind_supplied_slots",
        "rebind_slot_region",
    )
    names = (
        *rewritten,
        "__init__",
        "record_component_invocation",
        "bind_instance",
        "settle_component",
        "import_replayed_snapshot",
        "retire_component_output",
        "_with_ownership_ancestors",
    )
    originals = {name: getattr(graph, name) for name in names}
    base_enable, base_disable = install(native, native_retirement=True)
    base_enable()
    base = {name: getattr(graph, name) for name in names}
    base_disable()
    replacements = {**base, **{name: transform(originals[name], native) for name in rewritten}}

    def initialize(self: Any) -> None:
        base["__init__"](self)
        for name, factory in TABLES.items():
            setattr(self, name, native.RecordTable(factory, len(factory._fields)))

    def bind(self: Any, component: Any, element: Any) -> None:
        if not isinstance(self._logical_instances, native.RecordTable):
            originals["bind_instance"](self, component, element)
            return
        invocation_id = element.ownership_invocation_id
        parent = None
        selector = False
        if invocation_id is not None:
            selector = element.forward_ownership_invocation
            parent = self._component_invocations.journal.bind(
                self._invocation_index[invocation_id],
                component._citry_class_id,
                component.id,
                0 if selector else self._next_order(),
                selector,
            )
            if not selector:
                self._instance_invocation[component.id] = invocation_id
                self._init_ancestry.append_values(
                    (self._next_order(), invocation_id, parent, component.id, own.OwnershipState.ACTIVE)
                )
        self._logical_instances.append_values(
            (
                self._next_order(),
                component.id,
                component._citry_class_id,
                type(component).__name__,
                None if selector else invocation_id,
                parent,
                type(component).transparent,
                own.OwnershipState.ACTIVE,
            )
        )
        self._relation_indexes_current = False

    def replay(self: Any, *args: Any, **kwargs: Any) -> Any:
        for name in TABLES:
            setattr(self, name, list(getattr(self, name)))
        return base["import_replayed_snapshot"](self, *args, **kwargs)

    def retirement(
        self: Any,
        render_id: str,
        *,
        through_order: int,
        descendant_render_ids: Any = None,
        preserved_render_ids: Any = None,
        preserved_region_ids: Any = None,
    ) -> None:
        if isinstance(self._logical_instances, native.RecordTable):
            try:
                changes = self._component_invocations.journal.retire_output(
                    tuple(getattr(self, name) for name in TABLES),
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
                        own.RegionState.RETIRED,
                    ),
                )
            except native.UnsupportedRetirement:
                stats["fallback_calls"] += 1
                if native_ancestors:
                    # Python retirement reads these indexes after ancestry.
                    # Its native helper intentionally did not build them.
                    self._ensure_relation_indexes()
            else:
                stats["native_calls"] += 1
                self._order, receivers, promoted_regions = changes
                for receiver, name, fill_id in receivers:
                    self._receiver_fill[(receiver, name)] = fill_id
                if promoted_regions:
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

    def ancestors(self: Any, render_ids: set[str]) -> set[str]:
        if isinstance(self._logical_instances, native.RecordTable):
            try:
                result = self._component_invocations.journal.ancestors(
                    self._logical_instances, self._init_ancestry, self._physical_regions, render_ids
                )
            except native.UnsupportedRetirement:
                stats["ancestry_fallback_calls"] = stats.get("ancestry_fallback_calls", 0) + 1
            else:
                stats["ancestry_native_calls"] = stats.get("ancestry_native_calls", 0) + 1
                return result
        return originals["_with_ownership_ancestors"](self, render_ids)

    if native_ancestors:
        replacements["_with_ownership_ancestors"] = ancestors
    replacements.update(
        __init__=initialize, bind_instance=bind, import_replayed_snapshot=replay, retire_component_output=retirement
    )

    def switch(methods: dict[str, Any]) -> None:
        for name, method in methods.items():
            setattr(graph, name, method)

    return lambda: switch(replacements), lambda: switch(originals)


def main() -> None:
    """Run focused contracts or compare complete renders with all work timed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", action="store_true")
    parser.add_argument("--compare-native", action="store_true")
    parser.add_argument("--native-ancestors", action="store_true")
    parser.add_argument("--compare-storage", action="store_true")
    parser.add_argument("--pairs", type=int, default=60)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "benchmarks/results/repeat-render/ownership-storage.json"
    )
    args = parser.parse_args()
    if args.pairs < 1:
        parser.error("--pairs must be positive")
    native = load_native()
    stats = {"native_calls": 0, "fallback_calls": 0}
    if args.compare_storage and (not args.native_ancestors or args.compare_native):
        parser.error("--compare-storage requires --native-ancestors and excludes --compare-native")
    enable, restore = install_storage(native, stats, native_ancestors=args.native_ancestors)
    reference = (
        install_storage(native, {"native_calls": 0, "fallback_calls": 0})[0]
        if args.compare_storage
        else install(native, native_retirement=True)[0]
        if args.compare_native
        else restore
    )
    if args.tests:
        enable()
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
            restore()
    module = scenario()
    data = module.gen_render_data()
    snapshot = own.OwnershipGraph.snapshot
    traces = {}
    observations = []
    try:
        for candidate in (False, True):
            # Restore all additional capture methods before enabling the older backend.
            restore()
            (enable if candidate else reference)()
            for _ in range(6):
                module.render(data)
            captured = []

            def capture(graph: Any, _captured: list[Any] = captured) -> Any:
                value = snapshot(graph)
                _captured.append(value)
                return value

            own.OwnershipGraph.snapshot = capture
            ids._id_counter = itertools.count()
            module.render(data)
            own.OwnershipGraph.snapshot = snapshot
            traces[candidate] = captured
        if not traces[False] or traces[False] != traces[True]:
            raise RuntimeError("Missing or unequal ownership snapshots")
        for pair in range(args.pairs):
            outputs = {}
            for candidate in (False, True) if pair % 2 == 0 else (True, False):
                restore()
                (enable if candidate else reference)()
                ids._id_counter = itertools.count()
                start = time.perf_counter_ns()
                outputs[candidate] = module.render(data)
                elapsed = (time.perf_counter_ns() - start) / 1_000_000
                observations.append({"pair": pair, "candidate": candidate, "ms": elapsed})
            if outputs[False] != outputs[True]:
                raise RuntimeError(f"Different HTML for pair {pair}")
    finally:
        own.OwnershipGraph.snapshot = snapshot
        restore()
    savings = []
    for pair in range(args.pairs):
        values = {row["candidate"]: row["ms"] for row in observations if row["pair"] == pair}
        savings.append(values[False] - values[True])
    if args.native_ancestors and (
        stats.get("ancestry_native_calls", 0) == 0 or stats.get("ancestry_fallback_calls", 0)
    ):
        raise RuntimeError(f"Default scenario did not qualify native ancestry: {stats}")
    probe_root = Path(__file__).resolve().parent
    suffix = ".dylib" if sys.platform == "darwin" else ".so"
    paths = [
        Path(__file__),
        probe_root / "probe.py",
        *sorted((probe_root / "src").glob("*.rs")),
        ROOT / "crates/citry_ownership/Cargo.toml",
        ROOT / "crates/citry_ownership/src/lib.rs",
        ROOT / "Cargo.toml",
        ROOT / "Cargo.lock",
        probe_root / f"target/release/libcitry_ownership_journal_probe{suffix}",
        Path(own.__file__),
        Path(module.__file__),
    ]
    report = {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),  # noqa: S607
        "python": sys.version,
        "reference": "native storage with Python ancestry"
        if args.compare_storage
        else "native retirement with Python tables"
        if args.compare_native
        else "production Python ownership",
        "native_ancestors": args.native_ancestors,
        "file_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
        "pairs": args.pairs,
        "all_pairs_html_equal": True,
        "output_bytes": len(outputs[False].encode()),
        "snapshots_compared": len(traces[False]),
        "snapshot_trace_equal": True,
        "retirement": stats,
        "medians_ms": {
            name: statistics.median(row["ms"] for row in observations if row["candidate"] == candidate)
            for name, candidate in (("reference", False), ("candidate", True))
        },
        "median_paired_saving_ms": statistics.median(savings),
        "favorable_pairs": sum(value > 0 for value in savings),
        "observations": observations,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "observations"}, indent=2))


if __name__ == "__main__":
    main()
