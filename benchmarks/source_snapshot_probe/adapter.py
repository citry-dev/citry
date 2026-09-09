"""Keep source fields immutable through internal manifest snapshot reads."""

from __future__ import annotations

import ast
import copy
import importlib.machinery
import importlib.util
import inspect
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from citry import ownership, ownership_manifest, serialize
from citry.ext.events import emission, extension

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "target/release/libcitry_source_snapshot_probe.dylib"
spec = importlib.util.spec_from_file_location(
    "citry_source_snapshot_probe",
    ARTIFACT,
    loader=importlib.machinery.ExtensionFileLoader("citry_source_snapshot_probe", str(ARTIFACT)),
)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot load the source snapshot probe")
NATIVE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(NATIVE)
SourceTable = NATIVE.SourceTable
RECORD = ownership.SourceLocationRecord
NEW = RECORD.__new__
INIT = RECORD.__init__
PUBLIC_SNAPSHOT = ownership.OwnershipGraph.snapshot
GRAPH_ORIGINALS = {
    name: getattr(ownership.OwnershipGraph, name) for name in ("_initialize_native_storage", "record_source_location")
}
READERS = (
    (ownership_manifest, "prepare_ownership_manifest"),
    (ownership_manifest, "ownership_manifest_required"),
    (ownership_manifest.OwnershipManifestArtifact, "assert_unchanged"),
    (emission, "emit_events_dependencies"),
)
ORIGINAL_READERS = {(owner, name): getattr(owner, name) for owner, name in READERS}


@dataclass(frozen=True, slots=True, eq=False)
class SourceView:
    """An immutable ordered sequence of source fields with public records created on demand."""

    rows: tuple[Any, ...]
    cache: dict[int, Any] = field(default_factory=dict, init=False, repr=False)

    def __hash__(self) -> int:
        return hash(self.rows)

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int | slice) -> Any:
        if isinstance(index, slice):
            return tuple(self[i] for i in range(*index.indices(len(self.rows))))
        value = self.rows[index]
        if index < 0:
            index += len(self.rows)
        if type(value) is RECORD:
            return value
        if index not in self.cache:
            self.cache[index] = tuple.__new__(RECORD, value)
        return self.cache[index]

    def __iter__(self) -> Any:
        return (self[index] for index in range(len(self.rows)))

    def __eq__(self, other: object) -> bool:
        if type(other) is SourceView:
            return self.rows == other.rows
        return tuple(self) == other

    def ids(self) -> set[Any]:
        """Read IDs without constructing public source objects."""
        return {row[0] for row in self.rows}


def internal_snapshot(graph: Any) -> Any:
    """Retain source values while preserving ordinary public snapshot overrides."""
    if (
        type(graph._source_locations) is not SourceTable
        or getattr(graph.snapshot, "__func__", None) is not PUBLIC_SNAPSHOT
    ):
        return graph.snapshot()
    return ownership.OwnershipSnapshot(
        source_locations=SourceView(graph._source_locations.raw_snapshot()),
        component_invocations=tuple(graph._component_invocations),
        logical_instances=tuple(graph._logical_instances),
        init_ancestry=tuple(graph._init_ancestry),
        logical_fills=tuple(graph._logical_fills),
        physical_regions=tuple(graph._physical_regions),
        render_queue=tuple(graph._render_queue),
    )


def source_ids(values: Any) -> set[Any]:
    """Validate the same referenced-ID set with either source representation."""
    return values.ids() if type(values) is SourceView else {record.id for record in values}


def tree_for(original: Any) -> tuple[Any, int]:
    lines, first = inspect.getsourcelines(original)
    return ast.parse(textwrap.dedent("".join(lines))), first


def finish(tree: Any, original: Any, first: int) -> Any:
    ast.fix_missing_locations(tree)
    ast.increment_lineno(tree, first - 1)
    namespace: dict[str, Any] = {}
    exec(compile(tree, inspect.getsourcefile(original), "exec"), original.__globals__, namespace)  # noqa: S102
    result = namespace[original.__name__]
    result.__qualname__ = original.__qualname__
    return result


def graph_method(name: str) -> Any:
    original = GRAPH_ORIGINALS[name]
    tree, first = tree_for(original)
    function = tree.body[0]
    if name == "_initialize_native_storage":
        index = next(
            i
            for i, node in enumerate(function.body)
            if isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Attribute)
            and node.targets[0].attr == "_component_invocations"
        )
        function.body[index:index] = ast.parse(
            "sources = _probe_source_table(_probe_source_record, tuple.__new__)\n"
            "for record in self._source_locations:\n"
            "    sources.append(record)\n"
            "self._source_locations = sources\n"
        ).body
    else:
        matches = [
            (i, node)
            for i, node in enumerate(function.body)
            if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "append"
        ]
        if len(matches) != 1:
            raise RuntimeError("Unexpected source append")
        index, append = matches[0]
        constructor = append.value.args[0]
        if not isinstance(constructor, ast.Call) or constructor.args or len(constructor.keywords) != 8:
            raise RuntimeError("Unexpected source constructor")
        replacement = ast.parse(
            "saved_append = self._source_locations.append\n"
            "saved_class = SourceLocationRecord\n"
            "values = ()\n"
            "if (type(getattr(saved_append, '__self__', None)) is _probe_source_table\n"
            "    and saved_class is _probe_source_record\n"
            "    and saved_class.__new__ is _probe_source_new\n"
            "    and saved_class.__init__ is _probe_source_init):\n"
            "    saved_append.__self__.append_values(values)\n"
            "else:\n"
            "    saved_append(saved_class())\n"
        ).body
        replacement[2].value = ast.Tuple(
            elts=[copy.deepcopy(item.value) for item in constructor.keywords], ctx=ast.Load()
        )
        fallback = replacement[3].orelse[0].value.args[0]
        fallback.keywords = [
            ast.keyword(
                arg=item.arg,
                value=ast.Subscript(
                    value=ast.Name(id="values", ctx=ast.Load()), slice=ast.Constant(i), ctx=ast.Load()
                ),
            )
            for i, item in enumerate(constructor.keywords)
        ]
        function.body[index : index + 1] = replacement
    return finish(tree, original, first)


class ReaderChanges(ast.NodeTransformer):
    """Redirect only snapshot calls and source-reference collection."""

    def visit_Call(self, node: ast.Call) -> Any:
        self.generic_visit(node)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "snapshot"
            and not node.args
            and not node.keywords
        ):
            return ast.copy_location(
                ast.Call(
                    func=ast.Name(id="_probe_internal_snapshot", ctx=ast.Load()), args=[node.func.value], keywords=[]
                ),
                node,
            )
        return node

    def visit_Assign(self, node: ast.Assign) -> Any:
        self.generic_visit(node)
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "locations":
            # Validate IDs from raw fields in production; development still exports rows.
            if not isinstance(node.value, ast.ListComp):
                raise RuntimeError("Unexpected manifest source collection")
            return ast.copy_location(
                ast.If(
                    test=ast.Name(id="include_provenance", ctx=ast.Load()),
                    body=[node],
                    orelse=[
                        ast.Assign(
                            targets=[ast.Name(id="locations", ctx=ast.Store())],
                            value=ast.List(elts=[], ctx=ast.Load()),
                        )
                    ],
                ),
                node,
            )
        return node

    def visit_Compare(self, node: ast.Compare) -> Any:
        self.generic_visit(node)
        if (
            isinstance(node.left, ast.SetComp)
            and isinstance(node.comparators[0], ast.Name)
            and node.comparators[0].id == "referenced_locations"
        ):
            node.left = ast.parse(
                "_probe_source_ids(snapshot.source_locations) & referenced_locations", mode="eval"
            ).body
        return node


def reader_method(original: Any) -> Any:
    tree, first = tree_for(original)
    return finish(ReaderChanges().visit(tree), original, first)


GRAPH_CANDIDATES = {name: graph_method(name) for name in GRAPH_ORIGINALS}
CANDIDATE_READERS = {key: reader_method(original) for key, original in ORIGINAL_READERS.items()}


def install(changed: bool) -> None:
    """Select the experiment without replacing the ordinary native extension."""
    ownership._probe_source_table = SourceTable
    ownership._probe_source_record = RECORD
    ownership._probe_source_new = NEW
    ownership._probe_source_init = INIT
    for module in (ownership_manifest, emission):
        module._probe_internal_snapshot = internal_snapshot
        module._probe_source_ids = source_ids
    for name, method in (GRAPH_CANDIDATES if changed else GRAPH_ORIGINALS).items():
        setattr(ownership.OwnershipGraph, name, method)
    for (owner, name), method in (CANDIDATE_READERS if changed else ORIGINAL_READERS).items():
        setattr(owner, name, method)
    serialize.prepare_ownership_manifest = ownership_manifest.prepare_ownership_manifest
    serialize.ownership_manifest_required = ownership_manifest.ownership_manifest_required
    extension.emit_events_dependencies = emission.emit_events_dependencies
