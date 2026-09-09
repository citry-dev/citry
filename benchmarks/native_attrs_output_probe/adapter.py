"""Measure native construction of one flat attribute-output cache key."""

from __future__ import annotations
import __future__

import ast
import importlib.machinery
import importlib.util
import inspect
import textwrap
from pathlib import Path

from citry import nodes

ROOT = Path(__file__).resolve().parent
ARTIFACT = ROOT / "target/release/libcitry_native_attrs_output_probe.dylib"
spec = importlib.util.spec_from_file_location(
    "citry_native_attrs_output_probe",
    ARTIFACT,
    loader=importlib.machinery.ExtensionFileLoader("citry_native_attrs_output_probe", str(ARTIFACT)),
)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot load the attribute-output probe")
NATIVE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(NATIVE)
ORIGINAL = nodes.ElementAttrsNode._format
source, line = inspect.getsourcelines(ORIGINAL)
tree = ast.parse(textwrap.dedent("".join(source)))
outer = tree.body[0]
cache_branch = outer.body[2]
if not isinstance(cache_branch, ast.If) or not isinstance(cache_branch.body[0], ast.AnnAssign):
    raise TypeError("The inspected formatter's cache branch has changed")
cache_branch.body = ast.parse("""
cache_key = _native_attrs_output_key(resolved)
if cache_key is not None:
    cached = _attrs_output_cache.get(cache_key)
    if cached is not None:
        return cached
    resolved = {cache_key[index]: cache_key[index + 2] for index in range(0, len(cache_key), 3)}
""").body
ast.fix_missing_locations(tree)
ast.increment_lineno(tree, line - 1)
nodes._native_attrs_output_key = NATIVE.cache_key
# Run against the actual module dictionary so changed runtime globals stay visible.
exec(  # noqa: S102 - benchmark-only AST rewrite of the inspected runtime method
    compile(tree, ORIGINAL.__code__.co_filename, "exec", flags=__future__.annotations.compiler_flag),
    nodes.__dict__,
)
CANDIDATE = nodes.__dict__.pop("_format")


def install(changed: bool) -> None:
    """Start each variant with an empty cache under its own private key format."""
    nodes._attrs_output_cache.clear()
    nodes.ElementAttrsNode._format = CANDIDATE if changed else ORIGINAL
