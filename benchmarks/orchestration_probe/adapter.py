"""Measure builder defaults while retaining the original live runtime globals."""

from __future__ import annotations
import __future__

import ast
import inspect

from citry import component_render

ORIGINAL = component_render._render_one
source, line = inspect.getsourcelines(ORIGINAL)
tree = ast.parse("".join(source))
outer = tree.body[0]
inner = next(node for node in ast.walk(outer) if isinstance(node, ast.FunctionDef) and node.name == "build")
CAPTURED = ORIGINAL.__code__.co_cellvars
if len(CAPTURED) != 7 or inner.args.args or inner.args.kwonlyargs:
    raise RuntimeError("The builder shape differs from the inspected source")
inner.args.args = [ast.arg(arg=name, annotation=ast.Name(id="Any", ctx=ast.Load())) for name in CAPTURED]
inner.args.defaults = [ast.Name(id=name, ctx=ast.Load()) for name in CAPTURED]
ast.fix_missing_locations(tree)
ast.increment_lineno(tree, line - 1)
try:
    exec(  # noqa: S102 - benchmark-only compilation of the inspected runtime function
        compile(tree, ORIGINAL.__code__.co_filename, "exec", flags=__future__.annotations.compiler_flag),
        component_render.__dict__,
    )
    CANDIDATE = component_render._render_one
finally:
    component_render._render_one = ORIGINAL
if CANDIDATE.__code__.co_cellvars:
    raise RuntimeError("The candidate still allocates closure cells")


def install(changed: bool) -> None:
    """Switch the one runtime method used by ordinary render entrypoints."""
    component_render._render_one = CANDIDATE if changed else ORIGINAL
