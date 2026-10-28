r"""
Turn a call run's loop into the paths the Rust loop walk reads (level C2 of the native render path).

A call run is the rows one ``<c-for>`` places at one component call site,
such as ``<c-Row c-for="row in phase['outputs']" #c-key="row['id']" c-row="row" />``.
On the native render path, ``ForNode`` asks Rust
(``native_render._CallRunWalkPlan``) to read every row of such a loop in one
call, instead of walking the loop in Python. Rust can do that only when the
loop's iterable, the call's inputs and its key are plain paths: a name
followed by constant subscripts (``row``, ``row['id']``, ``groups[0]``).
This module turns the template's expression text into those paths, which
this file calls lowering, and refuses everything else, so the loop keeps
Python's walk. ``docs/design/native_render.md`` describes the walk and its
error modes.

An expression reaches two evaluators: Python's own parser reads it when the
expression sandbox is off, and the sandbox's rewriter reads it when it is on.
Both read a plain path's names and keys alike, so the path is lowered from
Python's parse of the text. The lowering asks the sandbox to compile the
text first.

The lowering also refuses:

- names and string keys that start with ``_``, which the sandbox refuses
  when the expression runs, and names that are not ASCII identifiers
  (Python applies NFKC normalization to other identifiers);
- string keys holding a surrogate code point, which no Rust string can hold;
- negative, bool or above-i64 indexes, and float, bytes and other constants
  as subscripts;
- any other expression: calls, attributes, slices, operators, comprehension
  filters (``if``), several loop targets or several ``for`` clauses;
- an expression the sandbox cannot compile, so a template error is always
  raised by Python's walk.
"""

from __future__ import annotations

import ast
from keyword import iskeyword
from typing import TypeAlias, TypeGuard

from citry._authored_expression import parse_authored_expression
from citry_core.safe_eval import compile_expr

PathSteps: TypeAlias = tuple[str | int, ...]
Path: TypeAlias = tuple[str, PathSteps]

# The largest index Rust accepts; a constant beyond it cannot index a real list anyway.
_I64_MAX = 2**63 - 1


def _plain_name(name: str) -> bool:
    """Whether a name reads the same in Python and in Rust: ASCII, not starting with ``_``, not a keyword."""
    return name.isascii() and name.isidentifier() and not iskeyword(name) and not name.startswith("_")


def _plain_step(value: object) -> TypeGuard[str | int]:
    """Whether a constant subscript is one Rust reads exactly as Python does."""
    # Exact types only, so `x[True]` is refused (bool is an int subclass).
    if type(value) is str:
        return not value.startswith("_") and not any("\ud800" <= char <= "\udfff" for char in value)
    if type(value) is int:
        return 0 <= value <= _I64_MAX
    return False


def _lower_parsed(node: ast.expr) -> Path | None:
    """Lower Python's parse of an expression to ``(name, steps)``, or None when it is not a plain path."""
    steps: list[str | int] = []
    while isinstance(node, ast.Subscript):
        index = node.slice
        if not isinstance(index, ast.Constant) or not _plain_step(index.value):
            return None
        steps.append(index.value)
        node = node.value
    if not isinstance(node, ast.Name) or not _plain_name(node.id):
        return None
    steps.reverse()
    return node.id, tuple(steps)


def _sandbox_compiles(source: str) -> bool:
    """
    Whether the expression sandbox compiles ``source``.

    When it does not, the loop keeps Python's walk, which raises the template's error.
    """
    try:
        compile_expr(source, sandboxed=True)
    except Exception:  # noqa: BLE001 - Python's walk raises the template's own error
        return False
    return True


def _parsed_body(source: str) -> ast.expr | None:
    """Return Python's parse of ``source``, wrapped as the unsandboxed evaluator wraps it, or None."""
    try:
        # compile_expr wraps the text the same way, so a trailing comment parses alike.
        return parse_authored_expression(source).body
    except (SyntaxError, ValueError):
        # ValueError covers text Python cannot encode, such as a lone surrogate.
        return None


def lower_path(expr: str) -> Path | None:
    """Return ``(name, steps)`` for a plain path, or None when it is not one or the sandbox cannot compile it."""
    parsed = _parsed_body(expr)
    if parsed is None or not _sandbox_compiles(expr):
        return None
    return _lower_parsed(parsed)


def _loop_iterable(node: ast.expr, target: str) -> ast.expr | None:
    """Return the iterable of ``((target,) for target in <iterable>)``, or None for any other shape."""
    if not isinstance(node, ast.GeneratorExp) or len(node.generators) != 1:
        return None
    element = node.elt
    if not (
        isinstance(element, ast.Tuple)
        and len(element.elts) == 1
        and isinstance(element.elts[0], ast.Name)
        and element.elts[0].id == target
    ):
        return None
    loop = node.generators[0]
    if loop.ifs or loop.is_async or not isinstance(loop.target, ast.Name) or loop.target.id != target:
        return None
    return loop.iter


def lower_loop(targets: tuple[str, ...], clause: str) -> tuple[str, Path] | None:
    """
    Return ``(target, iterable path)`` for ``<target> in <plain path>``, or None.

    The text lowered is the generator expression ``ForNode.iter_bodies``
    compiles, so the clause means here what it means there.
    """
    if len(targets) != 1 or not _plain_name(targets[0]):
        return None
    target = targets[0]
    # The newline keeps a trailing `# comment` in the clause from hiding the
    # closing parenthesis, as in `ForNode.iter_bodies`.
    source = f"(({target},) for {clause}\n)"
    parsed = _parsed_body(source)
    if parsed is None or not _sandbox_compiles(source):
        return None
    parsed_iterable = _loop_iterable(parsed, target)
    if parsed_iterable is None:
        return None
    iterable = _lower_parsed(parsed_iterable)
    # The iterable is read before the loop variable exists.
    if iterable is None or iterable[0] == target:
        return None
    return target, iterable
