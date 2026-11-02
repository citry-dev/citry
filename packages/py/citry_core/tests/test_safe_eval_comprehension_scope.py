"""
Each part of a comprehension sees only the loop variables Python has bound when it runs.

Python evaluates the first iterable in the enclosing scope, before any loop variable
exists, and each later iterable once the earlier `for` clauses have bound theirs. The
sandbox reads every name that is not bound yet from the context through its variable
check. Python's builtins are not reachable from an expression, and the evaluation
namespace holds an empty `__builtins__` as a second layer. These tests run whole
expressions through the Rust transformer and the Python runtime together, so they need the
Rust extension built from the current source.
"""

import builtins
import platform
import types

import pytest

from citry_core.safe_eval import SecurityError, compile_expr, safe_eval
from citry_core.safe_eval import eval as evaluator

# PyPy adds the builtins to every namespace it evaluates in, so the unsandboxed mode reaches
# them there by design (`compile_expr(sandboxed=False)` is for trusted templates only).
IS_PYPY = platform.python_implementation() == "PyPy"


def evaluate(expression: str, /, **context):
    return safe_eval(expression)(context)


class TestTheFirstIterableReadsTheContext:
    def test_a_name_shared_with_the_loop_variable_is_read_from_the_context(self):
        assert evaluate("[x * 2 for x in x]", x=[1, 2]) == [2, 4]
        assert evaluate("{x for x in x}", x=[1]) == {1}
        assert evaluate("{x: 1 for x in x}", x=["a"]) == {"a": 1}
        assert list(evaluate("(x for x in x)", x=[3])) == [3]

    @pytest.mark.parametrize("name", ["len", "getattr", "map", "repr", "type"])
    def test_a_builtin_is_not_reachable(self, name):
        # The name is a context lookup, so it fails when the context lacks it, and returns
        # the context's value when it has one.
        with pytest.raises(KeyError):
            evaluate(f"[{name} for {name} in [{name}]]")
        assert evaluate(f"[{name} for {name} in [{name}]]", **{name: "mine"}) == ["mine"]

    def test_the_builtins_name_is_refused_like_any_underscore_name(self):
        with pytest.raises(SecurityError):
            evaluate("[b for __builtins__ in [__builtins__] for b in [__builtins__]]")

    def test_a_later_iterable_reads_an_earlier_loop_variable(self):
        assert evaluate("[b for a in xs for b in a]", xs=[[1, 2], [3]]) == [1, 2, 3]

    def test_a_later_iterable_reads_its_own_name_from_the_context(self):
        assert evaluate("[b for a in xs for b in b]", xs=[0, 0], b=[7]) == [7, 7]

    def test_a_lambda_in_the_first_iterable_reads_the_context(self):
        assert evaluate("[a for a in (lambda: a)()]", a=[5]) == [5]

    @pytest.mark.skipif(IS_PYPY, reason="PyPy adds the builtins to every namespace")
    def test_the_unsandboxed_mode_reaches_no_builtin_either(self):
        with pytest.raises(NameError):
            compile_expr("[len for len in [len]]", sandboxed=False)({})
        assert compile_expr("[x for x in x]", sandboxed=False)({"x": [1]}) == [1]


class TestTheEvaluationNamespaceHasNoBuiltins:
    @pytest.mark.skipif(IS_PYPY, reason="PyPy adds the builtins to every namespace")
    def test_a_plain_name_the_transformer_let_through_finds_no_builtin(self, monkeypatch):
        # Stand in for a transformer that leaves a name unchecked. The empty `__builtins__`
        # must still stop it.
        class Transformer:
            @staticmethod
            def safe_eval(source):
                return source

        monkeypatch.setattr(evaluator._rust, "safe_eval", Transformer)
        assert hasattr(builtins, "len")
        with pytest.raises(NameError):
            safe_eval("len")({})

    def test_the_generated_function_has_an_empty_builtins_mapping(self):
        compiled = safe_eval("[x for x in x]")
        generated = next(
            cell.cell_contents for cell in compiled.__closure__ if isinstance(cell.cell_contents, types.FunctionType)
        )
        assert dict(generated.__globals__["__builtins__"]) == {}
