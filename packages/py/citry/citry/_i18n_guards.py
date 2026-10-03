"""Find Python i18n calls that run only when the app configures i18n."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def i18n_configured_guarded_calls(tree: ast.AST) -> frozenset[int]:
    """
    Return the ``id()`` of each call that runs only when ``i18n.configured`` is true.

    Without i18n settings an app has no format profiles, so a formatter call
    such as ``self.i18n.format.number(value, format="price")`` fails when it
    runs. A component that also works without i18n guards the call, and
    ``citry check`` and the language server then leave its profile name
    unchecked. These guards are recognized, with ``self.i18n`` or any other
    ``<name>.i18n`` or bare ``i18n`` owner:

    - ``x if self.i18n.configured else y`` and ``if self.i18n.configured:``,
      including when the test is an ``and`` chain that contains the guard;
    - ``self.i18n.configured and x``, for the operands after the guard;
    - ``if not self.i18n.configured: return ...`` (or ``raise``), for the
      statements after it in the same block.

    Any other call, such as one guarded through a local variable, is not in
    the result and is still checked.
    """
    guarded: set[int] = set()
    _visit(tree, guarded)
    return frozenset(guarded)


def _visit(node: ast.AST, guarded: set[int]) -> None:
    if isinstance(node, (ast.If, ast.IfExp)):
        polarity = _guard_polarity(node.test)
        body: list[ast.AST] = list(node.body) if isinstance(node.body, list) else [node.body]
        orelse: list[ast.AST] = list(node.orelse) if isinstance(node.orelse, list) else [node.orelse]
        if polarity is True:
            _mark(body, guarded)
        elif polarity is False:
            _mark(orelse, guarded)
    elif isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
        # `self.i18n.configured and x` evaluates `x` only once the guard holds.
        for index, operand in enumerate(node.values):
            if _guard_polarity(operand) is True:
                _mark(node.values[index + 1 :], guarded)
                break
    for field in ("body", "orelse", "finalbody"):
        statements = getattr(node, field, None)
        if isinstance(statements, list):
            _mark_after_early_exit(statements, guarded)
    for child in ast.iter_child_nodes(node):
        _visit(child, guarded)


def _mark_after_early_exit(statements: list[ast.stmt], guarded: set[int]) -> None:
    """Mark the statements after ``if not ...configured: return`` in one block."""
    for index, statement in enumerate(statements):
        if (
            isinstance(statement, ast.If)
            and not statement.orelse
            and _guard_polarity(statement.test) is False
            and statement.body
            and isinstance(statement.body[-1], (ast.Return, ast.Raise))
        ):
            _mark(statements[index + 1 :], guarded)
            return


def _mark(nodes: Sequence[ast.AST], guarded: set[int]) -> None:
    for node in nodes:
        guarded.update(id(call) for call in ast.walk(node) if isinstance(call, ast.Call))


def _guard_polarity(test: ast.expr) -> bool | None:
    """Return ``True`` when ``test`` proves i18n is configured, ``False`` when it proves the opposite."""
    if _is_configured_read(test):
        return True
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not) and _is_configured_read(test.operand):
        return False
    # Every operand of an `and` must hold, so one guard among them is enough.
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
        return True if any(_is_configured_read(value) for value in test.values) else None
    return None


def _is_configured_read(node: ast.expr) -> bool:
    """Recognize ``self.i18n.configured``, ``component.i18n.configured``, and ``i18n.configured``."""
    if not isinstance(node, ast.Attribute) or node.attr != "configured":
        return False
    owner = node.value
    return (isinstance(owner, ast.Attribute) and owner.attr == "i18n") or (
        isinstance(owner, ast.Name) and owner.id == "i18n"
    )


__all__ = ["i18n_configured_guarded_calls"]
