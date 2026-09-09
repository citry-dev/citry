"""Restore the recorded Python collector for comparisons with ordinary rendering."""

from __future__ import annotations
import __future__

import ast
from pathlib import Path
from typing import Any

from citry import ownership

SOURCE = Path(__file__).with_name("reference_ownership.py.txt")
# Use current record classes and context variables so only the collector changes.
_tree = ast.parse(SOURCE.read_text())
_class = next(node for node in _tree.body if isinstance(node, ast.ClassDef) and node.name == "OwnershipGraph")
_module = ast.Module(body=[_class], type_ignores=[])
_namespace = dict(vars(ownership))
exec(compile(_module, str(SOURCE), "exec", flags=__future__.annotations.compiler_flag), _namespace)  # noqa: S102
_REFERENCE: dict[str, Any] = {
    name: value
    for name, value in vars(_namespace["OwnershipGraph"]).items()
    if callable(value) or isinstance(value, staticmethod)
}
_CANDIDATE = {name: vars(ownership.OwnershipGraph)[name] for name in _REFERENCE}


def install(changed: bool) -> None:
    """Patch the existing class so render entrypoints retain the same graph alias."""
    for name, value in (_CANDIDATE if changed else _REFERENCE).items():
        setattr(ownership.OwnershipGraph, name, value)
