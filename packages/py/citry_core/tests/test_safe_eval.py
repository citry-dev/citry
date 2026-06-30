# ruff: noqa: E731
import re
from dataclasses import dataclass, field
from typing import Any, NamedTuple

import pytest

from citry_core.safe_eval import SecurityError, safe_eval, unsafe

# Check if t-strings are supported (Python 3.14+)
try:
    from string.templatelib import Template  # type: ignore[import-untyped]

    TSTRINGS_SUPPORTED = True
except ImportError:
    TSTRINGS_SUPPORTED = False


class Value(NamedTuple):
    value: int


@dataclass
class Nested:
    inner: str = field(default="inner_val")


@dataclass
class Obj:
    attr: str = field(default="value")
    name: str = field(default="test")
    value: int = field(default=42)
    start: int = 1
    end: int = 5
    nested: Nested = field(default_factory=Nested)
    items: dict[Any, Value] = field(default_factory=lambda: {"test": Value(value=42), 0: Value(value=10)})

    _private = "secret"

    def method(self, a: int, b: int) -> int:
        return a + b


class TestSyntax:
    def test_allow_multiline(self):
        compiled = safe_eval("[\n  1,\n  2,\n  3\n]")
        context = {}
        result = compiled(context)
        assert result == [1, 2, 3]
        assert context == {}

    def test_allow_multiline_with_variables(self):
        compiled = safe_eval("[\n  x,\n  y,\n  z\n]")
        context = {"x": 10, "y": 20, "z": 30}
        result = compiled(context)
        assert result == [10, 20, 30]
        assert context == {"x": 10, "y": 20, "z": 30}

    # === LITERALS ===

    def test_allow_literal_string(self):
        compiled = safe_eval("'hello'")
        context = {}
        result = compiled(context)
        assert result == "hello"
        assert context == {}

    def test_allow_literal_bytes(self):
        compiled = safe_eval("b'hello'")
        context = {}
        result = compiled(context)
        assert result == b"hello"
        assert context == {}

    def test_allow_literal_integer(self):
        compiled = safe_eval("42")
        context = {}
        result = compiled(context)
        assert result == 42
        assert context == {}

    def test_allow_literal_integer_negative(self):
        compiled = safe_eval("-42")
        context = {}
        result = compiled(context)
        assert result == -42
        assert context == {}

    def test_allow_literal_float(self):
        compiled = safe_eval("3.14")
        context = {}
        result = compiled(context)
        assert result == 3.14
        assert context == {}

    def test_allow_literal_float_negative(self):
        compiled = safe_eval("-3.14")
        context = {}
        result = compiled(context)
        assert result == -3.14
        assert context == {}

    def test_allow_literal_float_scientific(self):
        compiled = safe_eval("-1e10")
        context = {}
        result = compiled(context)
        assert result == -10000000000.0
        assert context == {}

    def test_allow_literal_boolean_true(self):
        compiled = safe_eval("True")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_literal_boolean_false(self):
        compiled = safe_eval("False")
        context = {}
        result = compiled(context)
        assert result is False
        assert context == {}

    def test_allow_literal_none(self):
        compiled = safe_eval("None")
        context = {}
        result = compiled(context)
        assert result is None
        assert context == {}

    def test_allow_literal_ellipsis(self):
        compiled = safe_eval("...")
        context = {}
        result = compiled(context)
        assert result is ...
        assert context == {}

    def test_allow_list_with_literals(self):
        compiled = safe_eval("[1, 2, 3]")
        context = {}
        result = compiled(context)
        assert result == [1, 2, 3]
        assert context == {}

    def test_allow_tuple_with_literals(self):
        compiled = safe_eval("(1, 2, 3)")
        context = {}
        result = compiled(context)
        assert result == (1, 2, 3)
        assert context == {}

    def test_allow_set_literal(self):
        compiled = safe_eval("{1, 2, 3}")
        context = {}
        result = compiled(context)
        assert result == {1, 2, 3}
        assert context == {}

    def test_allow_dict_with_literals(self):
        compiled = safe_eval("{'a': 1, 'b': 2}")
        context = {}
        result = compiled(context)
        assert result == {"a": 1, "b": 2}
        assert context == {}

    # === DATA STRUCTURES ===

    def test_allow_list_empty(self):
        compiled = safe_eval("[]")
        context = {}
        result = compiled(context)
        assert result == []

    def test_allow_tuple_empty(self):
        compiled = safe_eval("()")
        context = {}
        result = compiled(context)
        assert result == ()

    def test_allow_set_empty(self):
        compiled = safe_eval("set()")
        # NOTE: `set()`, `list()`, etc. must exposed to be able to call it as a function
        context = {"set": None}
        with pytest.raises(TypeError, match=r"'NoneType' object is not callable"):
            result = compiled(context)

        context = {"set": set}
        result = compiled(context)
        assert result == set()

    def test_allow_dict_empty(self):
        compiled = safe_eval("{}")
        context = {}
        result = compiled(context)
        assert result == {}

    def test_allow_nested_data_structures(self):
        compiled = safe_eval("[1, [2, 3], {'a': 4}]")
        context = {}
        result = compiled(context)
        assert result == [1, [2, 3], {"a": 4}]

    def test_allow_list_comprehension(self):
        compiled = safe_eval("[x for x in items]")
        context = {"items": [1, 2, 3]}
        result = compiled(context)
        assert result == [1, 2, 3]

    def test_allow_list_comprehension_with_condition(self):
        compiled = safe_eval("[x for x in items if x > 1]")
        context = {"items": [1, 2, 3]}
        result = compiled(context)
        assert result == [2, 3]

    def test_allow_list_comprehension_complex(self):
        compiled = safe_eval("[x[0] * y * multiplier for x in items for y in x[1] if x[0] > min_val if y < max_val]")
        context = {
            "items": [(1, [2.1, 2.2]), (2, [3.1, 3.2]), (4, [4.1, 4.2])],
            "max_val": 5,
            "min_val": 1,
            "multiplier": 2,
        }
        result = compiled(context)
        assert result == [12.4, 12.8, 32.8, 33.6]

    def test_allow_set_comprehension(self):
        compiled = safe_eval("{x for x in items}")
        context = {"items": [1, 2, 2, 3]}
        result = compiled(context)
        assert result == {1, 2, 3}  # Sets remove duplicates
        assert context == {"items": [1, 2, 2, 3]}

    def test_allow_dict_comprehension(self):
        compiled = safe_eval("{x: x*2 for x in items}")
        context = {"items": [1, 2, 3]}
        result = compiled(context)
        assert result == {1: 2, 2: 4, 3: 6}
        assert context == {"items": [1, 2, 3]}

    # === UNARY OPERATORS ===

    def test_allow_unary_plus(self):
        compiled = safe_eval("+42")
        context = {}
        result = compiled(context)
        assert result == 42
        assert context == {}

    def test_allow_unary_minus(self):
        compiled = safe_eval("-42")
        context = {}
        result = compiled(context)
        assert result == -42
        assert context == {}

    def test_allow_unary_not(self):
        compiled = safe_eval("not True")
        context = {}
        result = compiled(context)
        assert result is False
        assert context == {}

    def test_allow_unary_invert(self):
        compiled = safe_eval("~42")
        context = {}
        result = compiled(context)
        assert result == -43  # Bitwise NOT: ~42 = -(42 + 1) = -43
        assert context == {}

    def test_allow_nested_unary_operators(self):
        compiled = safe_eval("--42")
        context = {}
        result = compiled(context)
        assert result == 42  # Double negation: -(-42) = 42
        assert context == {}

    def test_transform_variable_in_unary_operation(self):
        compiled = safe_eval("-x")
        context = {"x": 10}
        result = compiled(context)
        assert result == -10
        assert context == {"x": 10}

    # === BINARY OPERATORS ===

    def test_allow_binary_add(self):
        compiled = safe_eval("1 + 2")
        context = {}
        result = compiled(context)
        assert result == 3
        assert context == {}

    def test_allow_binary_subtract(self):
        compiled = safe_eval("5 - 3")
        context = {}
        result = compiled(context)
        assert result == 2
        assert context == {}

    def test_allow_binary_multiply(self):
        compiled = safe_eval("4 * 5")
        context = {}
        result = compiled(context)
        assert result == 20
        assert context == {}

    def test_allow_binary_divide(self):
        compiled = safe_eval("10 / 2")
        context = {}
        result = compiled(context)
        assert result == 5.0
        assert context == {}

    def test_allow_binary_modulo(self):
        compiled = safe_eval("10 % 3")
        context = {}
        result = compiled(context)
        assert result == 1
        assert context == {}

    def test_allow_binary_power(self):
        compiled = safe_eval("2 ** 3")
        context = {}
        result = compiled(context)
        assert result == 8
        assert context == {}

    def test_allow_binary_equality(self):
        compiled = safe_eval("1 == 1")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_binary_inequality(self):
        compiled = safe_eval("1 != 2")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_binary_less_than(self):
        compiled = safe_eval("1 < 2")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_binary_greater_than(self):
        compiled = safe_eval("3 > 2")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_binary_less_equal(self):
        compiled = safe_eval("2 <= 3")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_binary_greater_equal(self):
        compiled = safe_eval("3 >= 2")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_nested_binary_operations(self):
        compiled = safe_eval("1 + 2 * 3")
        context = {}
        result = compiled(context)
        assert result == 7  # Multiplication has precedence: 1 + (2 * 3) = 1 + 6 = 7
        assert context == {}

    def test_transform_variable_in_binary_operation(self):
        compiled = safe_eval("x + y")
        context = {"x": 10, "y": 20}
        result = compiled(context)
        assert result == 30
        assert context == {"x": 10, "y": 20}

    # === BOOLEAN OPERATORS ===

    def test_allow_boolean_and(self):
        compiled = safe_eval("True and False")
        context = {}
        result = compiled(context)
        assert result is False
        assert context == {}

    def test_allow_boolean_or(self):
        compiled = safe_eval("True or False")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_boolean_chained_and(self):
        compiled = safe_eval("True and False and True")
        context = {}
        result = compiled(context)
        assert result is False  # Short-circuits on first False
        assert context == {}

    def test_allow_boolean_chained_or(self):
        compiled = safe_eval("False or True or False")
        context = {}
        result = compiled(context)
        assert result is True  # Short-circuits on first True
        assert context == {}

    def test_allow_boolean_mixed_operators(self):
        compiled = safe_eval("True and False or True")
        context = {}
        result = compiled(context)
        assert result is True  # (True and False) or True = False or True = True
        assert context == {}

    def test_allow_boolean_with_comparisons(self):
        compiled = safe_eval("1 < 2 and 3 > 4")
        context = {}
        result = compiled(context)
        assert result is False  # True and False = False
        assert context == {}

    def test_transform_variable_in_boolean_operation(self):
        compiled = safe_eval("x and y")
        context = {"x": 10, "y": 20}
        result = compiled(context)
        assert result == 20  # In Python, 'and' returns the last truthy value or first falsy value
        assert context == {"x": 10, "y": 20}

    # === COMPARISONS ===

    def test_allow_comparison_less_than(self):
        compiled = safe_eval("1 < 2")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_comparison_less_equal(self):
        compiled = safe_eval("1 <= 2")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_comparison_greater_than(self):
        compiled = safe_eval("3 > 2")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_comparison_greater_equal(self):
        compiled = safe_eval("3 >= 2")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_comparison_equality(self):
        compiled = safe_eval("1 == 1")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_comparison_inequality(self):
        compiled = safe_eval("1 != 2")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_comparison_in(self):
        compiled = safe_eval("1 in [1, 2, 3]")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_comparison_not_in(self):
        compiled = safe_eval("4 not in [1, 2, 3]")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_comparison_is(self):
        compiled = safe_eval("x is None")
        context = {"x": 10}
        result = compiled(context)
        assert result is False
        assert context == {"x": 10}

        # Test when x is actually None
        context = {"x": None}
        result = compiled(context)
        assert result is True
        assert context == {"x": None}

    def test_allow_comparison_is_not(self):
        compiled = safe_eval("x is not None")
        context = {"x": 10}
        result = compiled(context)
        assert result is True
        assert context == {"x": 10}

        # Test when x is actually None
        context = {"x": None}
        result = compiled(context)
        assert result is False
        assert context == {"x": None}

    def test_allow_comparison_chained(self):
        compiled = safe_eval("1 < 2 < 3")
        context = {}
        result = compiled(context)
        assert result is True
        assert context == {}

    def test_allow_comparison_mixed_types(self):
        compiled = safe_eval("'hello' == 'world'")
        context = {}
        result = compiled(context)
        assert result is False
        assert context == {}

    def test_transform_variable_in_comparison(self):
        compiled = safe_eval("x > 5")
        context = {"x": 10}
        result = compiled(context)
        assert result is True
        assert context == {"x": 10}

        # Test when x is less than 5
        context = {"x": 3}
        result = compiled(context)
        assert result is False
        assert context == {"x": 3}

    # === COMPREHENSIONS ===

    def test_allow_multiple_comprehensions(self):
        compiled = safe_eval("[(x.name, y) for x in items for y in x.children]")

        @dataclass
        class Item:
            name: str
            children: list[int]

        items = [Item("a", [1, 2]), Item("b", [3, 4])]
        context = {"items": items}
        result = compiled(context)
        assert result == [("a", 1), ("a", 2), ("b", 3), ("b", 4)]
        assert context == {"items": items}

    def test_allow_comprehension_with_multiple_conditions(self):
        compiled = safe_eval("[x for x in items if x > 0 if x < 10]")
        context = {"items": [-5, 1, 5, 15, 20]}
        result = compiled(context)
        assert result == [1, 5]
        assert context == {"items": [-5, 1, 5, 15, 20]}

    def test_allow_nested_comprehension(self):
        compiled = safe_eval("[[x+1 for x in row] for row in matrix]")
        context = {"matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}
        result = compiled(context)
        assert result == [[2, 3, 4], [5, 6, 7], [8, 9, 10]]
        assert context == {"matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}

    def test_transform_attribute_in_comprehension(self):
        compiled = safe_eval("[item.name for item in items]")
        items = [Obj() for _ in range(3)]
        context = {"items": items}
        result = compiled(context)
        assert result == ["test", "test", "test"]
        assert context == {"items": items}

    def test_transform_subscript_access_in_comprehension(self):
        compiled = safe_eval("[item[0] for item in items]")
        context = {"items": [[10, 20], [30, 40], [50, 60]]}
        result = compiled(context)
        assert result == [10, 30, 50]
        assert context == {"items": [[10, 20], [30, 40], [50, 60]]}

    def test_transform_walrus_in_comprehension(self):
        compiled = safe_eval("[y for x in items if (y := x.value)]")
        items = [Obj() for _ in range(3)]
        context = {"items": items, "y": 10}
        result = compiled(context)
        assert result == [42, 42, 42]
        assert context == {"items": items, "y": 42}

    def test_transform_walrus_before_comprehension(self):
        compiled = safe_eval("(limit := 10) and [x for x in items if x < limit]")
        context = {"items": [1, 2, 15, 20]}
        result = compiled(context)
        assert result == [1, 2]
        assert context == {"items": [1, 2, 15, 20], "limit": 10}

        # Also check what happens when we don't set the limit - should fail
        compiled = safe_eval("[x for x in items if x < limit]")
        context = {"items": [1, 2, 15, 20]}
        with pytest.raises(KeyError, match="'limit'"):
            compiled(context)

        # Or when we set it AFTER - also should fail
        compiled = safe_eval("[x for x in items if x < limit] and (limit := 10)")
        context = {"items": [1, 2, 15, 20]}
        with pytest.raises(KeyError, match="'limit'"):
            compiled(context)

    def test_local_variable_tracking_in_comprehensions(self):
        compiled = safe_eval("[x for x in items]")
        context = {"items": [1, 2, 3], "x": 100}
        result = compiled(context)
        assert result == [1, 2, 3]
        # x in comprehension is local, so outer x should remain unchanged
        assert context == {"items": [1, 2, 3], "x": 100}

    def test_local_variable_tracking_in_nested_comprehensions(self):
        compiled = safe_eval("[[x for x in row] for row in matrix]")
        context = {"matrix": [[1, 2, 3], [4, 5, 6]], "x": 100, "row": 200}
        result = compiled(context)
        assert result == [[1, 2, 3], [4, 5, 6]]
        # x and row in comprehensions are local, so outer values should remain unchanged
        assert context == {"matrix": [[1, 2, 3], [4, 5, 6]], "x": 100, "row": 200}

    def test_local_variable_tracking_in_multiple_comprehensions(self):
        compiled = safe_eval("[(x.name, y) for x in items for y in x.children]")

        @dataclass
        class Item:
            name: str
            children: list[int]

        items = [Item("a", [1]), Item("b", [2])]
        context = {"items": items, "x": 100, "y": 200}
        result = compiled(context)
        assert result == [("a", 1), ("b", 2)]
        # x and y in comprehensions are local, so outer values should remain unchanged
        assert context == {"items": items, "x": 100, "y": 200}

    def test_local_variable_tracking_in_comprehension_conditions(self):
        compiled = safe_eval("[x for x in items if x > 0]")
        context = {"items": [-5, 1, 2, 3], "x": 100}
        result = compiled(context)
        assert result == [1, 2, 3]
        # x in comprehension is local, so outer x should remain unchanged
        assert context == {"items": [-5, 1, 2, 3], "x": 100}

    def test_local_variable_tracking_in_multiple_comprehension_conditions(self):
        compiled = safe_eval("[(x.name, y) for x in items for y in x.children if y > 0]")

        @dataclass
        class Item:
            name: str
            children: list[int]

        items = [Item("a", [-1, 1]), Item("b", [-2, 2])]
        context = {"items": items, "x": 100, "y": 200}
        result = compiled(context)
        assert result == [("a", 1), ("b", 2)]
        # x and y in comprehensions are local, so outer values should remain unchanged
        assert context == {"items": items, "x": 100, "y": 200}

    # === FUNCTION CALLS ===

    def test_transform_function_call_simple(self):
        compiled = safe_eval("foo()")
        foo = lambda: 42
        context = {"foo": foo}
        result = compiled(context)
        assert result == 42
        assert context == {"foo": foo}

    def test_transform_function_call_with_positional_args(self):
        compiled = safe_eval("foo(x, 2, 3)")
        foo = lambda a, b, c: (a, b, c)
        context = {"foo": foo, "x": 10}
        result = compiled(context)
        assert result == (10, 2, 3)
        assert context == {"foo": foo, "x": 10}

    def test_transform_function_call_with_keyword_args(self):
        compiled = safe_eval("foo(a=1, b=x)")
        foo = lambda a, b: (a, b)
        context = {"foo": foo, "x": 10}
        result = compiled(context)
        assert result == (1, 10)
        assert context == {"foo": foo, "x": 10}

    def test_transform_function_call_with_mixed_args(self):
        compiled = safe_eval("foo(1, x, a=y, b=4)")
        foo = lambda pos1, pos2, a, b: (pos1, pos2, a, b)
        context = {"foo": foo, "x": 10, "y": 5}
        result = compiled(context)
        assert result == (1, 10, 5, 4)
        assert context == {"foo": foo, "x": 10, "y": 5}

    def test_transform_nested_function_calls(self):
        compiled = safe_eval("foo(bar(1, x))")
        bar = lambda a, b: a + b
        foo = lambda x: x * 2
        context = {"bar": bar, "foo": foo, "x": 10}
        result = compiled(context)
        assert result == 22
        assert context == {"bar": bar, "foo": foo, "x": 10}

    def test_transform_method_call(self):
        compiled = safe_eval("obj.method(1, 2)")
        context = {"obj": Obj()}
        result = compiled(context)
        assert result == 3
        assert context == {"obj": Obj()}

    def test_transform_function_call_with_variable_args(self):
        compiled = safe_eval("foo(x, y, z)")
        foo = lambda *args: args
        context = {"foo": foo, "x": 10, "y": 20, "z": 30}
        result = compiled(context)
        assert result == (10, 20, 30)
        assert context == {"foo": foo, "x": 10, "y": 20, "z": 30}

    def test_transform_function_call_with_variable_kwargs(self):
        compiled = safe_eval("foo(a=x, b=y)")
        foo = lambda **kwargs: kwargs
        context = {"foo": foo, "x": 10, "y": 20}
        result = compiled(context)
        assert result == {"a": 10, "b": 20}
        assert context == {"foo": foo, "x": 10, "y": 20}

    def test_transform_function_call_with_spread_args(self):
        compiled = safe_eval("foo(*args)")
        foo = lambda *args: args
        context = {"args": [1, 2, 3], "foo": foo}
        result = compiled(context)
        assert result == (1, 2, 3)
        assert context == {"args": [1, 2, 3], "foo": foo}

    def test_transform_function_call_with_spread_kwargs(self):
        compiled = safe_eval("foo(**kwargs)")
        foo = lambda **kwargs: kwargs
        context = {"foo": foo, "kwargs": {"a": 10, "b": 20}}
        result = compiled(context)
        assert result == {"a": 10, "b": 20}
        assert context == {"foo": foo, "kwargs": {"a": 10, "b": 20}}

    def test_transform_function_call_with_mixed_spreads(self):
        compiled = safe_eval("foo(1, *args, a=2, **kwargs)")
        foo = lambda *args, **kwargs: (args, kwargs)
        context = {"args": [10, 20], "foo": foo, "kwargs": {"c": 30}}
        result = compiled(context)
        assert result == ((1, 10, 20), {"a": 2, "c": 30})
        assert context == {"args": [10, 20], "foo": foo, "kwargs": {"c": 30}}

    def test_transform_function_call_with_nested_call_as_arg(self):
        compiled = safe_eval("foo(a=get_item())")
        get_item = lambda: 42
        foo = lambda **kwargs: kwargs
        context = {"foo": foo, "get_item": get_item}
        result = compiled(context)
        assert result == {"a": 42}
        assert context == {"foo": foo, "get_item": get_item}

    def test_transform_function_call_complex_signature(self):
        compiled = safe_eval("foo(x, y, 3, *args, a=get_item(), b=5, **kwargs)")
        get_item = lambda: 10
        foo = lambda *args, **kwargs: (args, kwargs)
        context = {
            "args": [1, 2],
            "foo": foo,
            "get_item": get_item,
            "kwargs": {"c": 100},
            "x": 10,
            "y": 20,
        }
        result = compiled(context)
        assert result == ((10, 20, 3, 1, 2), {"a": 10, "b": 5, "c": 100})
        assert context == {
            "args": [1, 2],
            "foo": foo,
            "get_item": get_item,
            "kwargs": {"c": 100},
            "x": 10,
            "y": 20,
        }

    def test_transform_subscript_with_method_call(self):
        compiled = safe_eval("obj[0](1, 2)")
        obj = [lambda a, b: (a, b)]
        context = {"obj": obj}
        result = compiled(context)
        assert result == (1, 2)
        assert context == {"obj": obj}

    def test_transform_slice_with_function_call(self):
        compiled = safe_eval("list[get_start():get_end()]")
        get_start = lambda: 1
        get_end = lambda: 5
        context = {
            "get_end": get_end,
            "get_start": get_start,
            "list": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        }
        result = compiled(context)
        assert result == [1, 2, 3, 4]
        assert context == {
            "get_end": get_end,
            "get_start": get_start,
            "list": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        }

    def test_transform_walrus_with_function_call(self):
        compiled = safe_eval("(result := get_value())")
        get_value = lambda: 42
        context = {"get_value": get_value}
        result = compiled(context)
        assert result == 42
        assert context == {"get_value": get_value, "result": 42}

    def test_transform_walrus_in_function_call(self):
        compiled = safe_eval("foo(x := get_value())")
        get_value = lambda: 42
        foo = lambda x: x * 2
        context = {"foo": foo, "get_value": get_value, "x": 10}
        result = compiled(context)
        assert result == 84
        assert context == {"foo": foo, "get_value": get_value, "x": 42}

    def test_transform_fstring_with_function_call(self):
        compiled = safe_eval("f'Value: {get_value()}'")
        get_value = lambda: 42
        context = {"get_value": get_value}
        result = compiled(context)
        assert result == "Value: 42"
        assert context == {"get_value": get_value}

    # === ATTRIBUTE ACCESS ===

    def test_transform_attribute_access_simple(self):
        compiled = safe_eval("obj.attr")

        context = {"obj": Obj()}
        result = compiled(context)
        assert result == "value"
        assert context == {"obj": Obj()}

    def test_transform_attribute_access_chained(self):
        compiled = safe_eval("obj.nested.inner")
        context = {"obj": Obj()}
        result = compiled(context)
        assert result == "inner_val"
        assert context == {"obj": Obj()}

    def test_transform_attribute_access_with_args(self):
        compiled = safe_eval("obj.method(1, x)")
        context = {"obj": Obj(), "x": 10}
        result = compiled(context)
        assert result == 11
        assert context == {"obj": Obj(), "x": 10}

    def test_transform_attribute_in_expression(self):
        compiled = safe_eval("obj.value + 10")
        context = {"obj": Obj()}
        result = compiled(context)
        assert result == 52
        assert context == {"obj": Obj()}

    def test_transform_attribute_with_underscore(self):
        compiled = safe_eval("obj._private")
        context = {"obj": Obj()}
        with pytest.raises(
            SecurityError,
            match=r"attribute '_private' on object '<class 'test_safe_eval.Obj'>' is unsafe",
        ):
            compiled(context)
        assert context == {"obj": Obj()}

    def test_transform_attribute_with_dunder(self):
        compiled = safe_eval("obj.__class__")
        context = {"obj": Obj()}
        with pytest.raises(
            SecurityError,
            match=r"attribute '__class__' on object '<class 'test_safe_eval.Obj'>' is unsafe",
        ):
            compiled(context)
        assert context == {"obj": Obj()}

    def test_transform_mixed_attribute_and_subscript(self):
        compiled = safe_eval("obj.items[0]")
        context = {"obj": Obj()}
        result = compiled(context)
        assert result == Value(value=10)
        assert context == {"obj": Obj()}

    def test_transform_subscript_then_attribute(self):
        compiled = safe_eval("obj[0].name")
        context = {"obj": [Obj()]}
        result = compiled(context)
        assert result == "test"
        assert context == {"obj": [Obj()]}

    def test_transform_slice_with_attribute_access(self):
        compiled = safe_eval("list[obj.start:obj.end]")
        context = {
            "list": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "obj": Obj(),
        }
        result = compiled(context)
        assert result == [1, 2, 3, 4]
        assert context == {"list": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "obj": Obj()}

    def test_transform_walrus_with_attribute_access(self):
        compiled = safe_eval("(x := obj.value)")
        context = {"obj": Obj(), "x": 10}
        result = compiled(context)
        assert result == 42
        assert context == {"obj": Obj(), "x": 42}

    def test_transform_fstring_with_attribute(self):
        compiled = safe_eval("f'Name: {obj.name}'")
        context = {"obj": Obj()}
        result = compiled(context)
        assert result == "Name: test"
        assert context == {"obj": Obj()}

    # === SUBSCRIPT ACCESS ===

    def test_transform_subscript_access_simple(self):
        compiled = safe_eval("obj[2]")
        context = {"obj": [10, 20, 30, 40]}
        result = compiled(context)
        assert result == 30
        assert context == {"obj": [10, 20, 30, 40]}

    def test_transform_subscript_access_with_variable_key(self):
        compiled = safe_eval("obj[key]")
        context = {"key": "name", "obj": {"attr": "value", "name": "test", "value": 42}}
        result = compiled(context)
        assert result == "test"
        assert context == {
            "key": "name",
            "obj": {"attr": "value", "name": "test", "value": 42},
        }

    def test_transform_subscript_access_with_string_key(self):
        compiled = safe_eval("obj['name']")
        context = {"obj": {"attr": "value", "name": "test", "value": 42}}
        result = compiled(context)
        assert result == "test"
        assert context == {"obj": {"attr": "value", "name": "test", "value": 42}}

    def test_transform_subscript_access_chained(self):
        compiled = safe_eval("obj[0][1]")
        context = {"obj": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}
        result = compiled(context)
        assert result == 2
        assert context == {"obj": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}

    def test_transform_subscript_access_with_expression_key(self):
        compiled = safe_eval("obj[x + 1]")
        context = {"obj": [0, 5, 10, 15], "x": 1}
        result = compiled(context)
        assert result == 10
        assert context == {"obj": [0, 5, 10, 15], "x": 1}

    def test_transform_subscript_access_in_expression(self):
        compiled = safe_eval("obj[0] + 10")
        context = {"obj": [5, 15, 25]}
        result = compiled(context)
        assert result == 15
        assert context == {"obj": [5, 15, 25]}

    # === SLICES ===

    def test_transform_slice_start_stop(self):
        compiled = safe_eval("list[1:x]")
        context = {"list": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "x": 5}
        result = compiled(context)
        assert result == [1, 2, 3, 4]

    def test_transform_slice_stop_only(self):
        compiled = safe_eval("list[:x]")
        context = {"list": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "x": 5}
        result = compiled(context)
        assert result == [0, 1, 2, 3, 4]

    def test_transform_slice_start_only(self):
        compiled = safe_eval("list[1:]")
        context = {"list": [0, 1, 2, 3, 4, 5]}
        result = compiled(context)
        assert result == [1, 2, 3, 4, 5]

    def test_transform_slice_all(self):
        compiled = safe_eval("list[:]")
        context = {"list": [0, 1, 2, 3, 4, 5]}
        result = compiled(context)
        assert result == [0, 1, 2, 3, 4, 5]
        # Ensure it's a copy, not the same object
        assert result is not context["list"]

    def test_transform_slice_with_step(self):
        compiled = safe_eval("list[::]")
        context = {"list": [0, 1, 2, 3, 4, 5]}
        result = compiled(context)
        assert result == [0, 1, 2, 3, 4, 5]
        # Ensure it's a copy, not the same object
        assert result is not context["list"]

    def test_transform_slice_reverse(self):
        compiled = safe_eval("list[::-1]")
        context = {"list": [0, 1, 2, 3, 4, 5]}
        result = compiled(context)
        assert result == [5, 4, 3, 2, 1, 0]

    def test_transform_slice_full(self):
        compiled = safe_eval("list[1:-2:1]")
        context = {"list": [0, 1, 2, 3, 4, 5]}
        result = compiled(context)
        assert result == [1, 2, 3]

    def test_transform_slice_start_with_step(self):
        compiled = safe_eval("list[1::]")
        context = {"list": [0, 1, 2, 3, 4, 5]}
        result = compiled(context)
        assert result == [1, 2, 3, 4, 5]

    def test_transform_slice_start_stop_with_step(self):
        compiled = safe_eval("list[1:2:]")
        context = {"list": [0, 1, 2, 3, 4, 5]}
        result = compiled(context)
        assert result == [1]

    def test_transform_slice_with_variables(self):
        compiled = safe_eval("list[start:end:step]")
        context = {"end": 4, "list": [0, 1, 2, 3, 4, 5], "start": 1, "step": 2}
        result = compiled(context)
        assert result == [1, 3]

    def test_transform_slice_with_expressions(self):
        compiled = safe_eval("list[x + 1:y - 1]")
        context = {"list": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "x": 1, "y": 5}
        result = compiled(context)
        assert result == [2, 3]

    # === WALRUS OPERATOR ===

    def test_transform_walrus_simple(self):
        compiled = safe_eval("(x := 5)")

        context = {"x": 10}
        result = compiled(context)
        assert result == 5
        assert context == {"x": 5}

        context = {"y": "a"}
        result = compiled(context)
        assert result == 5
        assert context == {"y": "a", "x": 5}

    def test_transform_walrus_with_variable(self):
        compiled = safe_eval("(x := y)")
        context = {"y": 5}
        result = compiled(context)
        assert result == 5
        assert context == {"x": 5, "y": 5}

        context = {"x": 10, "y": "a"}
        result = compiled(context)
        assert result == "a"
        assert context == {"x": "a", "y": "a"}

    def test_transform_walrus_with_expression(self):
        compiled = safe_eval("(x := y + 1)")

        context = {"x": 10, "y": 5}
        result = compiled(context)
        assert result == 6
        assert context == {"x": 6, "y": 5}

        context = {"y": "a"}
        with pytest.raises(TypeError):
            _ = compiled(context)

    def test_transform_walrus_in_if_expression(self):
        compiled = safe_eval("(x := get_value()) if (x := get_value()) else -1")

        # Hit the truthy branch
        items = [1, 2]
        items_iter = iter(items)
        get_value = lambda: next(items_iter)
        context = {"get_value": get_value}
        result = compiled(context)
        assert result == 2
        # x assigned from left-most `x := get_value()`
        assert context == {"x": 2, "get_value": get_value}

        # Hit the falsy branch
        items = [0, 1]
        items_iter = iter(items)
        get_value = lambda: next(items_iter)
        context = {"get_value": get_value}
        result = compiled(context)
        assert result == -1
        # x assigned from right-most `x := get_value()`
        assert context == {"x": 0, "get_value": get_value}

    def test_transform_walrus_chained(self):
        compiled = safe_eval("(x := (y := 5))")
        context = {}
        result = compiled(context)
        assert result == 5
        assert context == {"x": 5, "y": 5}

    def test_transform_walrus_remains_accessible_after_scope(self):
        compiled = safe_eval("foo([(a := i + 1) for i in items], a)")
        foo = lambda lst, a: [*lst, a]
        context = {"foo": foo, "items": [1, 2, 3]}
        result = compiled(context)
        assert result == [2, 3, 4, 4]
        assert context == {"foo": foo, "items": [1, 2, 3], "a": 4}

    def test_transform_walrus_multiple_assignments(self):
        compiled = safe_eval("[(x := i, y := i*2) for i in items] + [(x, y)]")
        context = {"items": [1, 2, 3]}
        result = compiled(context)
        assert result == [(1, 2), (2, 4), (3, 6), (3, 6)]
        assert context == {"items": [1, 2, 3], "x": 3, "y": 6}

    def test_transform_walrus_sequential_usage(self):
        compiled = safe_eval("(x := 5) + x")
        context = {}
        result = compiled(context)
        assert result == 10
        assert context == {"x": 5}

    def test_transform_walrus_nested_scopes(self):
        compiled = safe_eval(
            "[(y, x, a, b, i) for x in [(a := i) for i in items] if (b := a + 1)] + [(y, x, a, b, i)]"
        )
        context = {"i": -1, "a": -1, "b": -1, "items": [1, 2, 3], "x": 5, "y": 10}
        result = compiled(context)
        assert result == [
            # x as loop var
            (10, 1, 3, 4, -1),
            (10, 2, 3, 4, -1),
            (10, 3, 3, 4, -1),
            # x=5 from outside context
            (10, 5, 3, 4, -1),
        ]
        assert context == {
            # Unchanged
            "i": -1,
            "items": [1, 2, 3],
            "x": 5,
            "y": 10,
            # a and b are set by walrus op in the last loop
            "a": 3,
            "b": 4,
        }

    def test_transform_walrus_in_comprehension_leaks(self):
        compiled = safe_eval("[(x := y) for y in items]")
        context = {"items": [1, 2, 3]}
        result = compiled(context)
        assert result == [1, 2, 3]
        # x should be accessible outside the comprehension (matches Python behavior)
        assert context == {"items": [1, 2, 3], "x": 3}

    def test_transform_walrus_in_comprehension_conflicts_with_variable(self):
        with pytest.raises(
            SyntaxError,
            match="assignment expression cannot rebind comprehension iteration variable 'n'",
        ):
            safe_eval("[(n := n + 1) + n for n in items]")

    def test_transform_walrus_in_comprehension_conflicts_with_variable_nested(self):
        with pytest.raises(
            SyntaxError,
            match="assignment expression cannot rebind comprehension iteration variable 'x'",
        ):
            safe_eval("[[(x := x + 1) for y in inner] for x in outer]")

    # NOTE: This diverges from Python, which allows overwriting function args by walrus
    def test_transform_walrus_in_lambda_leaks(self):
        compiled = safe_eval("lambda x: (y := x + 1) + y")
        context = {}
        fn = compiled(context)
        result = fn(5)
        assert result == 12  # (y := 5 + 1) + y = 6 + 6 = 12

        # The important part: y SHOULD be in the context
        assert context == {"y": 6}

        # And should change again after another call
        result2 = fn(10)
        assert result2 == 22  # (y := 10 + 1) + y = 11 + 11 = 22
        assert context == {"y": 11}

    # NOTE: This diverges from Python, which allows overwriting function args by walrus
    def test_transform_walrus_in_lambda_conflicts_with_variable(self):
        with pytest.raises(
            SyntaxError,
            match="assignment expression cannot rebind lambda parameter 'x'",
        ):
            safe_eval("(lambda x: (x := 3) and x**2)")

    # NOTE: This diverges from Python, which allows overwriting function args by walrus
    def test_transform_walrus_in_lambda_conflicts_with_variable_nested_outer(self):
        with pytest.raises(
            SyntaxError,
            match="assignment expression cannot rebind lambda parameter 'x'",
        ):
            safe_eval("(lambda x: lambda y: (x := 3))")

    # NOTE: This diverges from Python, which allows overwriting function args by walrus
    def test_transform_walrus_in_lambda_conflicts_with_variable_nested_inner(self):
        with pytest.raises(
            SyntaxError,
            match="assignment expression cannot rebind lambda parameter 'y'",
        ):
            safe_eval("(lambda x: lambda y: (y := 3))")

    # === F-STRINGS ===

    def test_transform_fstring_simple(self):
        compiled = safe_eval("f'Hello {name}'")
        context = {"name": "test"}
        result = compiled(context)
        assert result == "Hello test"
        assert context == {"name": "test"}

    def test_transform_fstring_with_expression(self):
        compiled = safe_eval("f'Result: {x + 1}'")
        context = {"x": 10}
        result = compiled(context)
        assert result == "Result: 11"
        assert context == {"x": 10}

        context = {"x": "a"}
        with pytest.raises(TypeError):
            compiled(context)

    def test_transform_fstring_multiple_interpolations(self):
        compiled = safe_eval("f'{x} and {y}'")
        context = {"x": 10, "y": 11}
        result = compiled(context)
        assert result == "10 and 11"
        assert context == {"x": 10, "y": 11}

    def test_transform_fstring_nested_expression(self):
        compiled = safe_eval("f'start {obj.method(x, y)} end'")

        context = {
            "obj": Obj(),
            "x": 10,
            "y": 11,
        }
        result = compiled(context)
        assert result == "start 21 end"
        assert context == {"obj": Obj(), "x": 10, "y": 11}

    def test_transform_fstring_with_format_spec(self):
        compiled = safe_eval("f'start {value:.2f} end'")
        context = {"value": 100}
        result = compiled(context)
        assert result == "start 100.00 end"
        assert context == {"value": 100}

    def test_transform_fstring_with_format_spec_alignment(self):
        compiled = safe_eval("f'start {name:>10} end'")
        context = {"name": "test"}
        result = compiled(context)
        assert result == "start       test end"
        assert context == {"name": "test"}

    def test_transform_fstring_with_conversion(self):
        compiled = safe_eval("f'start {value!r} end'")

        class Value:
            def __repr__(self):
                return "<Value: 100>"

            def __eq__(self, other):
                return isinstance(other, Value)

        context = {"value": Value()}
        result = compiled(context)
        assert result == "start <Value: 100> end"
        assert context == {"value": Value()}

    def test_transform_fstring_with_conversion_str(self):
        compiled = safe_eval("f'start {value!s} end'")

        class Value:
            def __str__(self):
                return "<Value: 100>"

            def __eq__(self, other):
                return isinstance(other, Value)

        context = {"value": Value()}
        result = compiled(context)
        assert result == "start <Value: 100> end"
        assert context == {"value": Value()}

    def test_transform_fstring_with_conversion_and_format(self):
        compiled = safe_eval("f'start {value!r:>20} end'")

        class Value:
            def __repr__(self):
                return "<Value: 100>"

            def __eq__(self, other):
                return isinstance(other, Value)

        context = {"value": Value()}
        result = compiled(context)
        assert result == "start         <Value: 100> end"
        assert context == {"value": Value()}

    # === T-STRINGS ===

    def test_transform_tstring_simple(self):
        compiled = safe_eval("t'Hello {name}'")
        context = {"name": "test"}
        if TSTRINGS_SUPPORTED:
            # On Python 3.14+, t-strings are supported and return Template objects
            result = compiled(context)
            assert isinstance(result, Template)
        else:
            with pytest.raises(NotImplementedError):
                compiled(context)

    def test_transform_tstring_with_expression(self):
        compiled = safe_eval("t'Result: {x + 1}'")
        context = {"x": 10}
        if TSTRINGS_SUPPORTED:
            result = compiled(context)
            assert isinstance(result, Template)
        else:
            with pytest.raises(NotImplementedError):
                compiled(context)

    def test_transform_tstring_multiple_interpolations(self):
        compiled = safe_eval("t'{x} and {y}'")
        context = {"x": 10, "y": 10}
        if TSTRINGS_SUPPORTED:
            result = compiled(context)
            assert isinstance(result, Template)
        else:
            with pytest.raises(NotImplementedError):
                compiled(context)

    def test_transform_tstring_with_format_spec(self):
        compiled = safe_eval("t'start {value:.2f} end'")
        context = {"value": 100}
        if TSTRINGS_SUPPORTED:
            result = compiled(context)
            assert isinstance(result, Template)
        else:
            with pytest.raises(NotImplementedError):
                compiled(context)

    def test_transform_tstring_with_conversion(self):
        compiled = safe_eval("t'start {value!r} end'")
        context = {"value": 100}
        if TSTRINGS_SUPPORTED:
            result = compiled(context)
            assert isinstance(result, Template)
        else:
            with pytest.raises(NotImplementedError):
                compiled(context)

    def test_transform_tstring_with_conversion_and_format(self):
        compiled = safe_eval("t'start {value!r:>20} end'")
        context = {"value": 100}
        if TSTRINGS_SUPPORTED:
            result = compiled(context)
            assert isinstance(result, Template)
        else:
            with pytest.raises(NotImplementedError):
                compiled(context)

    # === VARIABLES ===

    def test_transform_variable_as_callable(self):
        compiled = safe_eval("my_func(1, 2)")

        context = {"my_func": None}
        with pytest.raises(TypeError):
            result = compiled(context)

        context = {"my_func": lambda x, y: x + y}
        result = compiled(context)
        assert result == 3

    def test_allow_simple_variable(self):
        compiled = safe_eval("x")
        context = {"x": 10}
        result = compiled(context)
        assert result == 10

    def test_transform_variable_in_list(self):
        compiled = safe_eval("[x, y, z]")
        context = {"x": 10, "y": 11, "z": 12}
        result = compiled(context)
        assert result == [10, 11, 12]

    def test_transform_variable_in_dict(self):
        compiled = safe_eval("{'key': x}")
        context = {"x": 10}
        result = compiled(context)
        assert result == {"key": 10}

    def test_transform_variable_in_complex_expression(self):
        compiled = safe_eval("x + y * z > 10")
        context = {"x": 10, "y": 11, "z": 12}
        result = compiled(context)
        assert result == (10 + 11 * 12 > 10)

    def test_transform_variable_names_with_underscores(self):
        compiled = safe_eval("my_variable")
        context = {"my_variable": None}
        result = compiled(context)
        assert result is None

        context = {"my_variable": 10}
        result = compiled(context)
        assert result == 10

    def test_transform_variable_names_with_numbers(self):
        compiled = safe_eval("var123")
        context = {"var123": None}
        result = compiled(context)
        assert result is None

        context = {"var123": 10}
        result = compiled(context)
        assert result == 10

    # === LAMBDAS ===

    def test_lambda_simple(self):
        compiled = safe_eval("lambda x: x + 1 + y")

        context = {"y": 10}
        fn = compiled(context)
        assert callable(fn)
        result = fn(1)
        assert result == 12
        assert context == {"y": 10}  # Should be unchanged

        # Make the lambda raise an error
        context2 = {"y": "a"}
        fn2 = compiled(context2)
        assert callable(fn2)
        with pytest.raises(TypeError):
            fn2(1)
        assert context2 == {"y": "a"}  # Should be unchanged

    def test_lambda_no_params(self):
        compiled = safe_eval("lambda: 42 + y")

        context = {"y": 10}
        fn = compiled(context)
        assert callable(fn)
        result = fn()
        assert result == 52
        assert context == {"y": 10}  # Should be unchanged

        # Make the lambda raise an error
        with pytest.raises(TypeError):
            result = fn(1)
        assert context == {"y": 10}  # Should be unchanged

    def test_lambda_multiple_params(self):
        compiled = safe_eval("lambda x, y: x + y + z")
        context = {"z": 10}
        fn = compiled(context)
        result = fn(1, 2)
        assert result == 13
        assert context == {"z": 10}  # Should be unchanged

    def test_lambda_with_varargs(self):
        compiled = safe_eval("lambda *args: len(args)")
        context = {"len": len}
        fn = compiled(context)

        result = fn(1, 2)
        assert result == 2
        assert context == {"len": len}  # Should be unchanged

        result = fn(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
        assert result == 10
        assert context == {"len": len}  # Should be unchanged

    def test_lambda_with_kwargs(self):
        compiled = safe_eval("lambda **kwargs: len(kwargs)")
        context = {"len": len}
        fn = compiled(context)

        result = fn(a=1, b=2, c=3)
        assert result == 3
        assert context == {"len": len}  # Should be unchanged

        result = fn(a=1, b=2, c=3, d=4, e=5, f=6, g=7, h=8, i=9, j=10)
        assert result == 10
        assert context == {"len": len}  # Should be unchanged

    # === FORBIDDEN SYNTAX ===

    def test_forbid_assignment(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("x = 1")

    def test_forbid_augmented_assignment(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("x += 1")

    def test_forbid_annotated_assignment(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("x: int = 1")

    def test_forbid_delete(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("del x")

    def test_forbid_multiple_delete(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("del x, y, z")

    def test_forbid_raise(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("raise ValueError('error')")

    def test_forbid_raise_bare(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("raise 'Oops'")

    def test_forbid_assert(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("assert x > 0")

    def test_forbid_assert_with_message(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("assert x > 0, 'x must be positive'")

    def test_forbid_pass(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("pass")

    def test_forbid_type_alias(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("type Point = tuple[float, float]")

    def test_forbid_for(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("for i in range(10): print(i")

    def test_forbid_while(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("while i < 10: print(i)")

    def test_forbid_break(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("for i in range(10): break")

    def test_forbid_continue(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("for i in range(10): continue")

    def test_forbid_if(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("if x > 0: print(1)")

    def test_forbid_if_else(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("if x > 0: print(1)\nelif 2: print(2)\nelse: print(3)")

    def test_forbid_try_except(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("try: x\nexcept: pass")

    def test_forbid_try_except_specific(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("try: x\nexcept ValueError: pass")

    def test_forbid_try_except_finally(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("try: x\nexcept: pass\nfinally: pass")

    def test_forbid_except_star(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("try: x\nexcept* ValueError: pass")

    def test_forbid_with(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("with open('f') as f: pass")

    def test_forbid_with_multiple(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("with open('f1') as f1, open('f2') as f2: pass")

    def test_forbid_async_with_in_async_fn(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("async def fn():\n    async with x as y: pass")

    def test_forbid_import(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("import os")

    def test_forbid_import_from(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("from os import path")

    def test_forbid_import_from_as(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("from os import path as p")

    def test_forbid_class(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("class MyClass: pass")

    def test_forbid_fn(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("def fn(): 1")

    def test_forbid_return(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("def fn(): return 42")

    def test_forbid_global(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("def fn(): global x")

    def test_forbid_nonlocal(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("def fn(): nonlocal x")

    def test_forbid_yield(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("def fn(): yield x")

    def test_forbid_yield_from(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("def fn(): yield from x")

    def test_forbid_decorator(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("@decorator\ndef fn(): pass")

    def test_forbid_async_fn(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("async def fn(): await x")

    def test_forbid_async_for(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("async for x in y")

    def test_forbid_async_with(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("async with x as y: pass")

    def test_forbid_match(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("match x:\n    case 1: pass")

    def test_forbid_match_singleton(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("match x:\n    case None: pass\n    case True: pass")

    def test_forbid_match_sequence(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("match x:\n    case [1, 2, 3]: pass")

    def test_forbid_match_star(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("match x:\n    case [1, *rest]: pass")

    def test_forbid_match_mapping(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("match x:\n    case {'key': value}: pass")

    def test_forbid_match_class(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("match x:\n    case Point(x=0, y=0): pass")

    def test_forbid_match_as(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("match x:\n    case [1, 2] as pair: pass")

    def test_forbid_match_or(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("match x:\n    case 1 | 2 | 3: pass")

    def test_forbid_match_wildcard(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("match x:\n    case _: pass")

    def test_forbid_match_guard(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("match x:\n    case n if n > 0: pass")

    def test_forbid_typevar(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("type T = int")

    def test_forbid_typevar_union(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("type StringOrInt = str | int")

    def test_forbid_generic_function(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("def func[T](x: T) -> T: return x")

    def test_forbid_typevartuple(self):
        with pytest.raises((SyntaxError, ValueError)):
            safe_eval("def func[*Ts](*args: *Ts) -> tuple[*Ts]: return args")

    # === OTHER ===

    def test_allow_comments(self):
        compiled = safe_eval("1 # comment")
        context = {}
        result = compiled(context)
        assert result == 1

    def test_allow_generator_expression(self):
        compiled = safe_eval("(x for x in items)")
        context = {"items": [1, 2, 3]}
        result = compiled(context)
        assert isinstance(result, type(x for x in []))
        assert list(result) == [1, 2, 3]

    def test_transform_complex_nested_access(self):
        compiled = safe_eval("obj.items[key].value")

        context1 = {
            "key": "test",
            "obj": {"attr": "value", "name": "test", "value": 42},
        }
        with pytest.raises(TypeError):
            compiled(context1)

        context2 = {"key": "test", "obj": Obj()}
        result = compiled(context2)
        assert result == 42

    def test_transform_percent_formatting(self):
        compiled = safe_eval("'text %s' % var")
        context = {"var": None}
        result = compiled(context)
        assert result == "text None"

    def test_transform_percent_formatting_tuple(self):
        compiled = safe_eval("'%s and %s' % (x, y)")
        context = {"x": 10, "y": 11}
        result = compiled(context)
        assert result == "10 and 11"


class TestUsage:
    def test_allow_multiple_evaluations(self):
        compiled = safe_eval("1")
        context = {}
        result = compiled(context)
        assert result == 1
        assert context == {}

    def test_missing_variable(self):
        compiled = safe_eval("x")
        context = {}
        with pytest.raises(KeyError, match="'x'"):
            compiled(context)

    def test_variable_none(self):
        compiled = safe_eval("x")
        context = {"x": None}
        result = compiled(context)
        assert result is None

    def test_syntax_error(self):
        with pytest.raises(
            SyntaxError,
            match=re.escape("Parse error: Expected an expression or a ']' at byte range 7..8: ')'"),
        ):
            safe_eval("x := [1)")


class TestSecurity:
    def test_block_unsafe_builtin_eval(self):
        compiled = safe_eval("eval('1+1')")
        context = {"eval": eval}
        with pytest.raises(SecurityError, match="function '<built-in function eval>' is unsafe"):
            compiled(context)

    def test_block_unsafe_builtin_passed_as_variable(self):
        compiled = safe_eval("totally_no_e_val('1+1')")
        context = {"totally_no_e_val": eval}
        with pytest.raises(SecurityError, match="function '<built-in function eval>' is unsafe"):
            compiled(context)

    def test_block_unsafe_decorated_function(self):
        @unsafe
        def dangerous_function():
            return "dangerous"

        compiled = safe_eval("dangerous_function()")
        context = {"dangerous_function": dangerous_function}
        with pytest.raises(SecurityError, match=r"function '.*dangerous_function.*' is unsafe"):
            compiled(context)

    def test_block_django_alters_data_function(self):
        class DjangoModel:
            def delete(self):
                pass

            delete.alters_data = True

        obj = DjangoModel()
        compiled = safe_eval("obj.delete()")
        context = {"obj": obj}
        with pytest.raises(SecurityError, match=r"function '.*delete.*' is unsafe"):
            compiled(context)

    def test_block_private_attribute(self):
        compiled = safe_eval("obj._private")
        context = {"obj": Obj()}
        with pytest.raises(
            SecurityError,
            match=r"attribute '_private' on object '<class 'test_safe_eval.Obj'>' is unsafe",
        ):
            compiled(context)

    def test_block_dunder_attribute(self):
        compiled = safe_eval("obj.__class__")
        context = {"obj": object()}
        with pytest.raises(
            SecurityError,
            match="attribute '__class__' on object '<class 'object'>' is unsafe",
        ):
            compiled(context)

    def test_block_internal_mro_attribute(self):
        compiled = safe_eval("str.mro")
        context = {"str": str}
        with pytest.raises(SecurityError, match="attribute 'mro' on object '<class 'type'>' is unsafe"):
            compiled(context)

    def test_block_generator_internal_attributes(self):
        def gen():
            yield 1

        g = gen()
        compiled = safe_eval("g.gi_frame")
        context = {"g": g}
        with pytest.raises(
            SecurityError,
            match="attribute 'gi_frame' on object '<class 'generator'>' is unsafe",
        ):
            compiled(context)

    def test_block_code_type_access(self):
        compiled = safe_eval("func.__code__")

        def func():
            pass

        context = {"func": func}
        with pytest.raises(
            SecurityError,
            match="attribute '__code__' on object '<class 'function'>' is unsafe",
        ):
            compiled(context)

    def test_block_unsafe_variable_access(self):
        compiled = safe_eval("_private_var")
        context = {"_private_var": 42}
        with pytest.raises(SecurityError, match="variable '_private_var' is unsafe"):
            compiled(context)

    def test_block_unsafe_variable_assignment(self):
        compiled = safe_eval("(_private := 42)")
        context = {}
        with pytest.raises(SecurityError, match="variable '_private' is unsafe"):
            compiled(context)


# These tests were based on Jinja2s `test_security.py` file, Jinja v3.1.6
# https://github.com/pallets/jinja/blob/5ef70112a1ff19c05324ff889dd30405b1002044/tests/test_security.py
class TestSecurityJinjaCompat:
    def test_subclasses_method(self):
        compiled = safe_eval("obj.__class__.__subclasses__()")
        context = {"obj": 42}
        # Should be blocked at __class__ access, not at __subclasses__
        with pytest.raises(
            SecurityError,
            match=r"attribute '__class__' on object.*is unsafe",
        ):
            compiled(context)

    def test_private_method_call(self):
        class ObjWithPrivate:
            def _foo(self):
                return "secret"

            def public(self):
                return "public"

        obj = ObjWithPrivate()
        # Private method call should be blocked
        compiled = safe_eval("obj._foo()")
        context = {"obj": obj}
        with pytest.raises(
            SecurityError,
            match=r"attribute '_foo' on object.*is unsafe",
        ):
            compiled(context)

        # Public method should work
        compiled = safe_eval("obj.public()")
        context = {"obj": obj}
        result = compiled(context)
        assert result == "public"

    # Unlike Jinja, we allow to call methods that mutate objects in place.
    # If we want to add immutable sandbox support, these should be blocked
    def test_mutable_operations(self):
        compiled = safe_eval("lst.append(42)")
        context = {"lst": [1, 2, 3]}
        result = compiled(context)
        assert result is None  # append returns None
        assert context["lst"] == [1, 2, 3, 42]  # Modified

        compiled = safe_eval("lst.pop()")
        context = {"lst": [1, 2, 3]}
        result = compiled(context)
        assert result == 3
        assert context["lst"] == [1, 2]  # Modified

        compiled = safe_eval("dct.clear()")
        context = {"dct": {"a": 1, "b": 2}}
        result = compiled(context)
        assert result is None  # clear returns None
        assert context["dct"] == {}  # Modified

    # Unlike Jinja, we do NOT block access to func_code attribute.
    # Because we support only Python 3.
    # func_code is an attribute of a function object in Python 2.
    def test_func_code_attribute(self):
        compiled = safe_eval("func.func_code")

        def func():
            pass

        context = {"func": func}
        with pytest.raises(
            AttributeError,
            match="'function' object has no attribute 'func_code'",
        ):
            compiled(context)

    # `str.format()` and `str.format_map()` can be used to expose unsafe variables,
    # e.g. `"{a.__class__}".format(a=42)` returns `"<class 'int'>"`
    # While Jinja allows to use `str.format()` and `str.format_map()`,
    # we simply block them instead and ask users to use f-strings instead,
    # which is handled by our transformer instead.
    def test_format_method(self):
        compiled = safe_eval('"a{0[\'b\']}b".format({"b": 42})')
        context = {}
        with pytest.raises(
            SecurityError,
            match=r"function '.*format.*' is unsafe. Use f-strings instead.",
        ):
            compiled(context)

    def test_format_map_method(self):
        compiled = safe_eval('"a{x.__class__}b".format_map({"x": {"b": 42}})')
        context = {}
        with pytest.raises(
            SecurityError,
            match=r"function '.*format_map.*' is unsafe. Use f-strings instead.",
        ):
            compiled(context)

    def test_indirect_call_via_attr(self):
        # Mimic the exploit - first get the str.format and assign to a variable
        compiled = safe_eval("(format_func := str.format)")
        context = {"str": str}
        compiled(context)
        assert context == {"str": str, "format_func": str.format}

        # Reusing the context object (what would happen in the template),
        # use `format_func` to call `str.format`
        compiled = safe_eval('format_func("{b.__class__}", b=42)')
        with pytest.raises(
            SecurityError,
            match=r"function '.*format.*' is unsafe. Use f-strings instead.",
        ):
            compiled(context)

        # Same for format_map
        compiled = safe_eval("(format_func := str.format_map)")
        context = {"str": str}
        compiled(context)
        assert context == {"str": str, "format_func": str.format_map}

        # Reusing the context object (what would happen in the template),
        # use `format_func` to call `str.format`
        compiled = safe_eval('format_func("{b.__class__}", {"b": 42})')
        with pytest.raises(
            SecurityError,
            match=r"function '.*format_map.*' is unsafe. Use f-strings instead.",
        ):
            compiled(context)


class TestCustomValidators:
    def test_validate_callable(self):
        # Create a function that blocks functions with "danger" in their name
        def is_safe_callable(func):
            func_name = getattr(func, "__name__", "")
            return not func_name.lower().startswith("danger")

        # Success case
        def safe_func(x):
            return x + 1

        compiled = safe_eval("safe_func(5)", validate_callable=is_safe_callable)
        context = {"safe_func": safe_func}
        result = compiled(context)
        assert result == 6

        # Failure case
        def danger_func(x):
            return x * 2

        compiled = safe_eval("danger_func(5)", validate_callable=is_safe_callable)
        context = {"danger_func": danger_func}
        with pytest.raises(SecurityError, match=r"function '.*danger_func.*' is unsafe"):
            compiled(context)

    def test_validate_attribute(self):
        # Create a validator that blocks attributes starting with "secret"
        def is_safe_attr(obj, attr_name):
            return not attr_name.lower().startswith("secret")

        class DataClass:
            def __init__(self):
                self.public = "public_data"
                self.secret_data = "secret_info"  # noqa: S105

        obj = DataClass()

        # Success case
        compiled = safe_eval("obj.public", validate_attribute=is_safe_attr)
        context = {"obj": obj}
        result = compiled(context)
        assert result == "public_data"

        # Failure case
        compiled = safe_eval("obj.secret_data", validate_attribute=is_safe_attr)
        context = {"obj": obj}
        with pytest.raises(
            SecurityError,
            match=r"attribute 'secret_data' on object '.*DataClass.*' is unsafe",
        ):
            compiled(context)

    def test_validate_subscript(self):
        # Create a validator that blocks integer keys >= 100
        def is_safe_subscript(obj, key):
            if isinstance(key, int):
                return key < 100
            return True

        data = {1: "one", 2: "two", 100: "hundred", 200: "two_hundred"}

        # Success case
        compiled = safe_eval("data[1]", validate_subscript=is_safe_subscript)
        context = {"data": data}
        result = compiled(context)
        assert result == "one"

        # Failure case
        compiled = safe_eval("data[100]", validate_subscript=is_safe_subscript)
        context = {"data": data}
        with pytest.raises(SecurityError, match=r"key '100' on object '.*dict.*' is unsafe"):
            compiled(context)

        # String keys are allowed
        data_str = {"a": "alpha", "b": "beta"}
        compiled = safe_eval("data_str['a']", validate_subscript=is_safe_subscript)
        context = {"data_str": data_str}
        result = compiled(context)
        assert result == "alpha"

    def test_validate_assign(self):
        # Create a validator that blocks assignments to variables ending with "_config"
        def is_safe_assign(var_name, value):
            return not var_name.endswith("_config")

        # Success case
        compiled = safe_eval("(user_id := 42)", validate_assign=is_safe_assign)
        context = {}
        result = compiled(context)
        assert result == 42
        assert context == {"user_id": 42}

        # Failure case
        compiled = safe_eval("(app_config := {'key': 'value'})", validate_assign=is_safe_assign)
        context = {}
        with pytest.raises(SecurityError, match="assignment to variable 'app_config' is unsafe"):
            compiled(context)
        assert context == {}

    def test_validate_variable(self):
        # Create a validator that blocks variables containing "internal"
        def is_safe_variable(var_name):
            return "internal" not in var_name.lower()

        # Success cases
        compiled = safe_eval("public_var", validate_variable=is_safe_variable)
        context = {"public_var": "public_value"}
        result = compiled(context)
        assert result == "public_value"

        compiled = safe_eval("inter_nal_data", validate_variable=is_safe_variable)
        context = {"inter_nal_data": "internal_value"}
        result = compiled(context)
        assert result == "internal_value"

        # Failure cases
        compiled = safe_eval("internal_var", validate_variable=is_safe_variable)
        context = {"internal_var": "secret"}
        with pytest.raises(SecurityError, match="variable 'internal_var' is unsafe"):
            compiled(context)

        compiled = safe_eval("my_internal_data", validate_variable=is_safe_variable)
        context = {"my_internal_data": "data"}
        with pytest.raises(SecurityError, match="variable 'my_internal_data' is unsafe"):
            compiled(context)


class TestErrorReporting:
    def test_error_variable(self):
        compiled = safe_eval("1 + _unsafe_var + 1")
        context = {"_unsafe_var": 42}
        with pytest.raises(
            SecurityError,
            match=re.escape(
                "Error in variable: SecurityError: variable '_unsafe_var' is unsafe\n\n"
                "     1 | 1 + _unsafe_var + 1\n"
                "             ^^^^^^^^^^^"
            ),
        ):
            compiled(context)

    def test_error_attribute(self):
        compiled = safe_eval("1 + obj._private + 1")
        context = {"obj": Obj()}
        with pytest.raises(
            SecurityError,
            match=re.escape(
                "Error in attribute: SecurityError: attribute '_private' on object '<class 'test_safe_eval.Obj'>' is unsafe\n\n"  # noqa: E501
                "     1 | 1 + obj._private + 1\n"
                "             ^^^^^^^^^^^"
            ),
        ):
            compiled(context)

    def test_error_subscript(self):
        def is_safe_subscript(obj, key):
            return False

        compiled = safe_eval("1 + data['key'] + 1", validate_subscript=is_safe_subscript)
        context = {"data": {"key": "value"}}
        with pytest.raises(
            SecurityError,
            match=re.escape(
                "Error in subscript: SecurityError: key 'key' on object '<class 'dict'>' is unsafe\n\n"
                "     1 | 1 + data['key'] + 1\n"
                "             ^^^^^^^^^^^"
            ),
        ):
            compiled(context)

    def test_error_call(self):
        compiled = safe_eval("1 + eval('1+1') + 1")
        context = {"eval": eval}
        with pytest.raises(
            SecurityError,
            match=re.escape(
                "Error in call: SecurityError: function '<built-in function eval>' is unsafe\n\n"
                "     1 | 1 + eval('1+1') + 1\n"
                "             ^^^^^^^^^^^"
            ),
        ):
            compiled(context)

    def test_error_assign(self):
        compiled = safe_eval("1 + (_unsafe := 42) + 1")
        context = {}
        with pytest.raises(
            SecurityError,
            match=re.escape(
                "Error in assign: SecurityError: variable '_unsafe' is unsafe\n\n"
                "     1 | 1 + (_unsafe := 42) + 1\n"
                "              ^^^^^^^^^^^^^"
            ),
        ):
            compiled(context)

    def test_error_slice(self):
        compiled = safe_eval("1 + list[x + 1:y - 1] + 1")
        context = {"list": [1, 2, 3, 4, 5], "x": None, "y": None}
        with pytest.raises(
            TypeError,
            match=re.escape(
                "unsupported operand type(s) for +: 'NoneType' and 'int'\n\n     1 | 1 + list[x + 1:y - 1] + 1\n"
            ),
        ):
            compiled(context)

    def test_error_fstring(self):
        compiled = safe_eval("1 + f'{a + 2}' + 1")
        context = {"a": "a"}
        with pytest.raises(
            TypeError,
            match=re.escape(
                'can only concatenate str (not "int") to str\n\n'
                "     1 | 1 + f'{a + 2}' + 1\n"
                "         ^^^^^^^^^^^^^^^^^^"
            ),
        ):
            compiled(context)

    def test_error_multi_line(self):
        source = "1 + fn([\n    1,\n    2,\n    3,\n]) + 1"
        compiled = safe_eval(source)
        context = {"fn": eval}
        with pytest.raises(
            SecurityError,
            match=re.escape(
                "Error in call: SecurityError: function '<built-in function eval>' is unsafe\n\n"
                "     1 | 1 + fn([\n"
                "             ^^^^\n"
                "     2 |     1,\n"
                "         ^^^^^^\n"
                "     3 |     2,\n"
                "         ^^^^^^\n"
                "     4 |     3,\n"
                "         ^^^^^^\n"
                "     5 | ]) + 1\n"
                "         ^^"
            ),
        ):
            compiled(context)
