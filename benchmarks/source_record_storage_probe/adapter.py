"""Opt-in source-record storage using the existing native ownership table."""

from __future__ import annotations

import ast
import copy
import inspect
import textwrap
from typing import Any

from citry import ownership

GRAPH = ownership.OwnershipGraph
ORIGINALS = {name: getattr(GRAPH, name) for name in ("_initialize_native_storage", "record_source_location")}
RECORD = ownership.SourceLocationRecord
CONSTRUCTOR = RECORD.__new__


def compile_method(name: str) -> Any:
    """Change only source-table creation and the occurrence append operation."""
    original = ORIGINALS[name]
    lines, first = inspect.getsourcelines(original)
    tree = ast.parse(textwrap.dedent("".join(lines)))
    function = tree.body[0]
    if not isinstance(function, ast.FunctionDef):
        raise TypeError("Expected an ordinary ownership method")
    if name == "_initialize_native_storage":
        # Allocate and fill the source table before publishing any native table.
        first_publish = next(
            index
            for index, node in enumerate(function.body)
            if isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Attribute)
            and node.targets[0].attr == "_component_invocations"
        )
        statements = ast.parse(
            "sources = _RecordTable(_probe_source_record, 8)\n"
            "sources.set_tuple_constructor(tuple.__new__)\n"
            "for record in self._source_locations:\n"
            "    sources.append(record)\n"
            "self._source_locations = sources\n"
        ).body
        function.body[first_publish:first_publish] = statements
    else:
        candidates = [
            (index, node)
            for index, node in enumerate(function.body)
            if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "append"
        ]
        if len(candidates) != 1:
            raise RuntimeError("Expected exactly one source-record append")
        index, original_append = candidates[0]
        constructor = original_append.value.args[0]
        if not isinstance(constructor, ast.Call) or constructor.args or len(constructor.keywords) != 8:
            raise RuntimeError("Unexpected source-record construction")
        values = ast.Tuple(elts=[copy.deepcopy(item.value) for item in constructor.keywords], ctx=ast.Load())
        replacement = ast.parse(
            "if (isinstance(self._source_locations, _RecordTable)\n"
            "    and SourceLocationRecord is _probe_source_record\n"
            "    and SourceLocationRecord.__new__ is _probe_source_constructor):\n"
            "    self._source_locations.append_values(())\n"
            "else:\n"
            "    pass\n"
        ).body[0]
        replacement.body[0].value.args[0] = values
        replacement.orelse = [original_append]
        function.body[index] = replacement
    ast.fix_missing_locations(tree)
    ast.increment_lineno(tree, first - 1)
    namespace: dict[str, Any] = {}
    exec(compile(tree, inspect.getsourcefile(original), "exec"), vars(ownership), namespace)  # noqa: S102
    result = namespace[name]
    result.__qualname__ = original.__qualname__
    return result


CANDIDATES = {name: compile_method(name) for name in ORIGINALS}


def install(changed: bool) -> None:
    """Select candidate methods without changing production source or binaries."""
    ownership._probe_source_record = RECORD
    ownership._probe_source_constructor = CONSTRUCTOR
    for name, method in (CANDIDATES if changed else ORIGINALS).items():
        setattr(GRAPH, name, method)
