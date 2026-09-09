"""Move settlement callbacks onto an explicit state object in a temporary source copy."""

from __future__ import annotations

import ast
import copy

METHODS = {"commit", "requeue", "settle", "settle_in_invocation_region", "bubble"}
FIELDS = {"stack", "root_result"}


class References(ast.NodeTransformer):
    """Redirect only the known shared bindings; keep all other operations intact."""

    def __init__(self, receiver: str, names: set[str]) -> None:
        self.receiver = receiver
        self.names = names
        self.count = 0

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id not in self.names:
            return node
        self.count += 1
        return ast.copy_location(
            ast.Attribute(value=ast.Name(id=self.receiver, ctx=ast.Load()), attr=node.id, ctx=node.ctx), node
        )

    def visit_Nonlocal(self, node: ast.Nonlocal) -> ast.AST | None:
        if node.names != ["root_result"]:
            raise RuntimeError("Unexpected settlement nonlocal binding")
        return None


def transform(source: str) -> tuple[str, dict[str, object]]:
    """Reject unfamiliar callback structure before generating the new representation."""
    tree = ast.parse(source)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_settle_render")
    callbacks = [node for node in function.body if isinstance(node, ast.FunctionDef)]
    if {node.name for node in callbacks} != METHODS:
        raise RuntimeError("Settlement callbacks changed")
    if any(arg.arg in ("self", "state") for node in callbacks for arg in node.args.args):
        raise RuntimeError("State name collides with a callback argument")
    state = ast.parse('''class _SettlementState:
    """Own pending tasks and the current root without retaining callbacks."""
    __slots__ = ("stack", "root_result")

    def __init__(self, stack, root_result):
        self.stack = stack
        self.root_result = root_result
''').body[0]
    references = References("self", METHODS | FIELDS)
    for node in callbacks:
        method = references.visit(copy.deepcopy(node))
        method.args.args.insert(0, ast.arg(arg="self"))
        state.body.append(method)
    outer = References("state", METHODS | {"root_result"})
    body = []
    initialized = 0
    for node in function.body:
        if isinstance(node, ast.FunctionDef):
            continue
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "root_result"
        ):
            if ast.dump(node.value) != ast.dump(ast.Name(id="root_render", ctx=ast.Load())):
                raise RuntimeError("Unexpected root initialization")
            body.append(ast.parse("state = _SettlementState(stack, root_render)").body[0])
            initialized += 1
        else:
            body.append(outer.visit(node))
    if initialized != 1:
        raise RuntimeError("Missing unique state initialization")
    function.body = body
    tree.body.insert(tree.body.index(function), state)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n", {
        "methods": sorted(METHODS),
        "fields": sorted(FIELDS),
        "method_shared_references": references.count,
        "outer_state_references": outer.count,
    }
