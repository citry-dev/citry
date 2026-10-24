"""
Citry reads a class's or module's namespace whole only through a copy.

Any render thread can store a computed value on a component class at any
moment, and an import can add names to a module. Reading the live namespace
whole (a loop over it in Python, or one C call such as ``dict.update`` or a
set operation, which another thread can interrupt on free-threaded Python)
then raises "dictionary changed size during iteration".
``_static_class_namespace_copy`` and ``vars(module).copy()`` copy in one call
that another thread cannot interrupt.

The failure shows only under contention, mostly on free-threaded Python,
which ordinary test runs cannot reproduce on demand. So this test reads the
shipped sources instead: it finds each live namespace (``vars(x)``,
``_static_class_dict(x)``, ``x.__dict__`` other than ``self.__dict__``, and
any name assigned one of these in the same function) and reports the common
ways of reading one whole. Single lookups (``in``, ``[]``, ``.get``) stay
allowed. It cannot follow a namespace passed to another function or read
through ``getattr(x, "__dict__")``, which also reads instance dicts.
"""

from __future__ import annotations

import ast
from pathlib import Path

_PACKAGES = Path(__file__).resolve().parents[2]
_SOURCES = [
    path
    for package in ("citry/citry", "citry_ui/citry_ui", "citry_lsp/citry_lsp")
    for path in sorted((_PACKAGES / package).rglob("*.py"))
    if "tests" not in path.parts and "quality" not in path.parts
]
# Calls that read their first argument whole.
_WHOLE_READ_CALLS = frozenset({"dict", "list", "tuple", "set", "frozenset", "sorted"})
# Methods that read their argument whole, such as `x.update(namespace)`.
_WHOLE_READ_METHODS = frozenset(
    {"update", "isdisjoint", "issubset", "issuperset", "union", "intersection", "difference"}
)
# Methods that, called on a namespace, read it whole.
_VIEW_METHODS = frozenset({"keys", "values", "items"})
_SET_OPERATORS = (ast.BitAnd, ast.BitOr, ast.Sub, ast.BitXor)


def _is_live_namespace_call(node: ast.AST) -> bool:
    """Whether ``node`` produces a live namespace: ``vars(x)``, ``_static_class_dict(x)`` or ``x.__dict__``."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id not in {"vars", "_static_class_dict"} or len(node.args) != 1:
            return False
        # `vars(parser.parse_args(...))` reads the fresh Namespace argparse
        # just built, which no other thread holds.
        argument = node.args[0]
        return not (
            isinstance(argument, ast.Call)
            and isinstance(argument.func, ast.Attribute)
            and argument.func.attr == "parse_args"
        )
    # An instance's own __dict__ is not shared with render threads.
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "__dict__"
        and not (isinstance(node.value, ast.Name) and node.value.id == "self")
    )


class _Finder(ast.NodeVisitor):
    def __init__(self) -> None:
        self.found: list[int] = []
        # Names holding a live namespace, one set per function being visited.
        self.scopes: list[set[str]] = [set()]

    def _live(self, node: ast.AST | None) -> bool:
        if node is None:
            return False
        if isinstance(node, ast.Name):
            return node.id in self.scopes[-1]
        # `namespace.keys()` is as live as `namespace`.
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _VIEW_METHODS
            and self._live(node.func.value)
        ):
            return True
        return _is_live_namespace_call(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda) -> None:
        self.scopes.append(set())
        self.generic_visit(node)
        self.scopes.pop()

    visit_FunctionDef = _visit_function  # noqa: N815 - ast.NodeVisitor naming
    visit_AsyncFunctionDef = _visit_function  # noqa: N815 - ast.NodeVisitor naming
    visit_Lambda = _visit_function  # noqa: N815 - ast.NodeVisitor naming

    def _bind(self, target: ast.AST, value: ast.AST | None) -> None:
        if isinstance(target, ast.Name):
            if value is not None and self._live(value):
                self.scopes[-1].add(target.id)
            else:
                self.scopes[-1].discard(target.id)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._bind(target, node.value)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._bind(node.target, node.value)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        # `names |= namespace` reads the namespace whole.
        if isinstance(node.op, _SET_OPERATORS) and self._live(node.value):
            self.found.append(node.lineno)
        self.generic_visit(node)

    def visit_Starred(self, node: ast.Starred) -> None:
        # `[*namespace]` and `f(*namespace)` loop over it.
        if self._live(node.value):
            self.found.append(node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        function = node.func
        whole = (isinstance(function, ast.Name) and function.id in _WHOLE_READ_CALLS) or (
            isinstance(function, ast.Attribute) and function.attr in _WHOLE_READ_METHODS
        )
        if whole and any(self._live(argument) for argument in node.args):
            self.found.append(node.lineno)
        if isinstance(function, ast.Attribute) and function.attr in _VIEW_METHODS and self._live(function.value):
            self.found.append(node.lineno)
        if any(keyword.arg is None and self._live(keyword.value) for keyword in node.keywords):
            self.found.append(node.lineno)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        if self._live(node.iter):
            self.found.append(node.lineno)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        if self._live(node.iter):
            self.found.append(node.iter.lineno)
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        if isinstance(node.op, _SET_OPERATORS) and (self._live(node.left) or self._live(node.right)):
            self.found.append(node.lineno)
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        # `{**namespace}` copies it key by key.
        if any(key is None and self._live(value) for key, value in zip(node.keys, node.values, strict=True)):
            self.found.append(node.lineno)
        self.generic_visit(node)


def _whole_reads(source: str) -> list[int]:
    finder = _Finder()
    finder.visit(ast.parse(source))
    return sorted(set(finder.found))


def test_the_finder_reports_whole_reads_and_allows_lookups_and_copies() -> None:
    reported = """
def f(cls, module, other):
    a = dict(vars(cls))
    b = {}.update(_static_class_dict(cls))
    for name in vars(module):
        pass
    namespace = _static_class_dict(cls)
    c = namespace.keys() - {"x"}
    d = frozenset({"x"}).isdisjoint(namespace)
    e = {**cls.__dict__}
    g = [value for value in vars(cls).values()]
    h = list(vars(type(other)))
    ns: dict = vars(cls)
    for name in ns:
        pass
    i = [*vars(cls)]
    names = set()
    names |= vars(cls).keys()
    k = list(vars(cast("type", cls)))
"""
    assert _whole_reads(reported) == [3, 4, 5, 8, 9, 10, 11, 12, 14, 16, 18, 19]
    allowed = """
def f(self, cls, module):
    a = vars(module).copy()
    b = _static_class_namespace_copy(cls)
    for name in b:
        pass
    c = "x" in vars(cls)
    d = cls.__dict__.get("x")
    e = self.__dict__.items()
    namespace = vars(cls)
    namespace = {}
    f = namespace.keys() - {"x"}
    g = dict(vars(parser.parse_args([])))
    h = getattr(instance, "__dict__", None)
    h.update({})
"""
    assert _whole_reads(allowed) == []


def test_no_shipped_source_reads_a_live_namespace_whole() -> None:
    found = [
        f"{path.relative_to(_PACKAGES)}:{line}"
        for path in _SOURCES
        for line in _whole_reads(path.read_text(encoding="utf-8"))
    ]
    assert found == [], "read through _static_class_namespace_copy() or vars(module).copy():\n" + "\n".join(found)
