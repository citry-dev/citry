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
The two read some literals differently (the rewriter turns a lone surrogate
escape such as ``'\ud800'`` into U+FFFD). So a path is lowered twice, once
from Python's parse of the text and once from the Python code the sandbox
generated for it, and the expression is refused unless both give the same
path. Then Rust reads the same keys whichever evaluator Python's walk would
use.

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

from citry_core.safe_eval import compile_expr

PathSteps: TypeAlias = tuple[str | int, ...]
Path: TypeAlias = tuple[str, PathSteps]

# The largest index Rust accepts; a constant beyond it cannot index a real list anyway.
_I64_MAX = 2**63 - 1
# The names the sandbox's generated code calls for a variable and a subscript
# (`variable` and `subscript` in citry_core/safe_eval/eval.py).
_VARIABLE_CALL = "variable"
_SUBSCRIPT_CALL = "subscript"
# The arguments before the operands in each of those calls: the context, the
# source text and the token's position.
_CALL_PREFIX = 3


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


def _call_operands(node: ast.expr, function: str, count: int) -> list[ast.expr] | None:
    """Return the operands of the sandbox's generated ``function(context, source, token, ...)`` call, or None."""
    if (
        not isinstance(node, ast.Call)
        or not isinstance(node.func, ast.Name)
        or node.func.id != function
        or node.keywords
        or len(node.args) != _CALL_PREFIX + count
    ):
        return None
    return node.args[_CALL_PREFIX:]


def _lower_generated(node: ast.expr) -> Path | None:
    """Lower the sandbox's generated code for an expression to ``(name, steps)``, or None."""
    steps: list[str | int] = []
    while (operands := _call_operands(node, _SUBSCRIPT_CALL, 2)) is not None:
        target, index = operands
        if not isinstance(index, ast.Constant) or not _plain_step(index.value):
            return None
        steps.append(index.value)
        node = target
    operands = _call_operands(node, _VARIABLE_CALL, 1)
    if operands is None:
        return None
    (name,) = operands
    if not isinstance(name, ast.Constant) or type(name.value) is not str or not _plain_name(name.value):
        return None
    steps.reverse()
    return name.value, tuple(steps)


def _generated_body(source: str) -> ast.expr | None:
    """Return the expression the sandbox generated for ``source``, or None when it cannot compile it."""
    try:
        evaluate = compile_expr(source, sandboxed=True)
    except Exception:  # noqa: BLE001 - Python's walk raises the template's own error
        return None
    # The generated code is one assignment of a one-argument lambda, for
    # example `_eval_expr = lambda context: (subscript(...))`. Anything else
    # means the sandbox changed shape, and the expression keeps Python's walk.
    generated = getattr(evaluate, "_source_code", None)
    if type(generated) is not str:
        return None
    try:
        module = ast.parse(generated, mode="exec")
    except (SyntaxError, ValueError):
        return None
    if len(module.body) != 1 or not isinstance(module.body[0], ast.Assign):
        return None
    function = module.body[0].value
    if not isinstance(function, ast.Lambda) or len(function.args.args) != 1:
        return None
    return function.body


def _parsed_body(source: str) -> ast.expr | None:
    """Return Python's parse of ``source``, wrapped as the unsandboxed evaluator wraps it, or None."""
    try:
        # compile_expr wraps the text the same way, so a trailing comment parses alike.
        return ast.parse(f"(\n{source}\n)", mode="eval").body
    except (SyntaxError, ValueError):
        # ValueError covers text Python cannot encode, such as a lone surrogate.
        return None


def _same_path(first: Path | None, second: Path | None) -> bool:
    """Whether two lowerings are the same path, comparing each step's exact type too."""
    if first is None or second is None:
        return False
    return first[0] == second[0] and [(type(step), step) for step in first[1]] == [
        (type(step), step) for step in second[1]
    ]


def lower_path(expr: str) -> Path | None:
    """Return ``(name, steps)`` for a plain path expression that both evaluators read alike, or None."""
    parsed = _parsed_body(expr)
    generated = _generated_body(expr)
    if parsed is None or generated is None:
        return None
    lowered = _lower_parsed(parsed)
    if not _same_path(lowered, _lower_generated(generated)):
        return None
    return lowered


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
    source = f"(({target},) for {clause})"
    parsed = _parsed_body(source)
    generated = _generated_body(source)
    if parsed is None or generated is None:
        return None
    parsed_iterable = _loop_iterable(parsed, target)
    generated_iterable = _loop_iterable(generated, target)
    if parsed_iterable is None or generated_iterable is None:
        return None
    iterable = _lower_parsed(parsed_iterable)
    # The iterable is read before the loop variable exists.
    if not _same_path(iterable, _lower_generated(generated_iterable)) or iterable is None or iterable[0] == target:
        return None
    return target, iterable
