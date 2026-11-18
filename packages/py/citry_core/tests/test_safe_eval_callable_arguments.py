"""
The sandbox refuses a call that hands it a function the sandbox would not call itself.

The call check runs for each call that the expression text writes. A function that takes
another function and calls it, such as `list.sort` with `key=`, makes that inner call in
C code, without the check. Two rules close that route:

- Reading `format` or `format_map` from any string is refused, exact `str` included, so
  template text alone has no refused function to hand over.
- A call whose arguments include a refused function is refused, so a refused function
  that the app put in the context cannot be handed over either.

Each test records whether the private attribute or the refused method actually ran, so a
test fails if the call went through, even when the result is thrown away.
"""

import functools
import sys
import types
from typing import Any

import pytest

from citry_core.safe_eval import SecurityError, safe_eval, unsafe
from citry_core.safe_eval.sandbox import find_unsafe_callable_argument

CALLED: list[str] = []


@pytest.fixture(autouse=True)
def _clear_calls() -> None:
    CALLED.clear()


class Holder:
    """A context object that records when the template reaches what it must not reach."""

    @property
    def _trigger(self) -> str:
        CALLED.append("read")
        return "CALL-MARKER"

    @unsafe
    def remove(self, item: Any) -> None:
        CALLED.append("remove")

    def drop(self, item: Any) -> None:
        CALLED.append("drop")

    drop.alters_data = True  # type: ignore[attr-defined]

    def delete(self, using: Any = None) -> None:
        """Shaped like Django's `Model.delete`, which a sort key can call with one argument."""
        CALLED.append("delete")

    delete.alters_data = True  # type: ignore[attr-defined]

    def label(self, item: Any) -> str:
        return f"label-{item}"


class RaisingLookup:
    """A callable whose own attribute lookup raises something other than `AttributeError`."""

    def __getattr__(self, name: str) -> Any:
        raise KeyError(name)

    def __call__(self, item: Any) -> Any:
        CALLED.append("raising-lookup")
        return item


class UnhashableCallable:
    """A callable instance that defines `__eq__` without `__hash__`, so it cannot be hashed."""

    def __eq__(self, other: object) -> bool:
        return self is other

    __hash__ = None  # type: ignore[assignment]

    def __call__(self, item: Any) -> Any:
        return item


def assert_refused(source: str, **context: Any) -> SecurityError:
    with pytest.raises(SecurityError) as error:
        safe_eval(source)(context)
    assert CALLED == []
    assert "CALL-MARKER" not in str(error.value)
    return error.value


class TestStringFormatHandedToBuiltins:
    """Template text alone: a format method read from a string literal."""

    def test_sort_key_with_str_format(self):
        assert_refused("[obj].sort(key='{0._trigger}'.format)", obj=Holder())

    def test_sort_key_with_str_format_map(self):
        assert_refused("[{'o': obj}].sort(key='{o._trigger}'.format_map)", obj=Holder())

    def test_sort_key_inside_a_comprehension(self):
        assert_refused("[[o].sort(key='{0._trigger}'.format) for o in objs]", objs=[Holder()])

    def test_sort_key_from_a_lambda_result(self):
        # The lambda body is checked, so the read is refused inside it.
        assert_refused("[obj].sort(key=(lambda: '{0._trigger}'.format)())", obj=Holder())

    def test_sort_key_with_a_string_from_the_context(self):
        assert_refused("[obj].sort(key=text.format)", obj=Holder(), text="{0._trigger}")


class TestRefusedFunctionsAsArguments:
    """Refused functions that the app put in the context, or that its objects carry."""

    def test_bound_format_method_in_the_context(self):
        assert_refused("[obj].sort(key=fmt)", obj=Holder(), fmt="{0._trigger}".format)

    def test_unsafe_method(self):
        error = assert_refused("[1].sort(key=obj.remove)", obj=Holder())
        assert "cannot be passed to" in str(error)

    def test_alters_data_method(self):
        assert_refused("[1].sort(key=obj.drop)", obj=Holder())

    def test_django_style_delete_from_template_text(self):
        # Template text alone, with an ordinary model-like object in the context: this
        # route changes data, not only reads it.
        assert_refused("[None].sort(key=user.delete)", user=Holder())

    def test_partial_of_a_refused_function(self):
        assert_refused("[obj].sort(key=fmt)", obj=Holder(), fmt=functools.partial(str.format, "{0._trigger}"))

    def test_passed_by_position_to_an_app_helper(self):
        assert_refused("apply(fmt, obj)", apply=lambda f, x: f(x), fmt="{0._trigger}".format, obj=Holder())

    def test_passed_by_keyword_to_an_app_helper(self):
        assert_refused("apply(f=fmt, x=obj)", apply=lambda f, x: f(x), fmt="{0._trigger}".format, obj=Holder())

    def test_passed_through_star_arguments(self):
        assert_refused("apply(*[fmt, obj])", apply=lambda f, x: f(x), fmt="{0._trigger}".format, obj=Holder())

    def test_passed_through_double_star_arguments(self):
        assert_refused(
            "apply(**{'f': fmt, 'x': obj})", apply=lambda f, x: f(x), fmt="{0._trigger}".format, obj=Holder()
        )

    def test_refused_builtin(self):
        assert_refused("[obj].sort(key=v)", obj=Holder(), v=vars)


class TestSafeFunctionsStillWork:
    """The argument check must leave ordinary functions alone."""

    def test_sort_key_with_a_lambda(self):
        items = [3, 1, 2]
        safe_eval("items.sort(key=lambda x: -x)")({"items": items})
        assert items == [3, 2, 1]

    def test_sort_key_with_a_public_method(self):
        items = [2, 1]
        safe_eval("items.sort(key=obj.label)")({"items": items, "obj": Holder()})
        assert items == [1, 2]

    def test_unhashable_callable_argument(self):
        assert safe_eval("apply(f, 5)")({"apply": lambda f, x: f(x), "f": UnhashableCallable()}) == 5

    def test_class_as_argument(self):
        assert safe_eval("check(1, kind)")({"check": isinstance, "kind": int}) is True

    def test_policy_function(self):
        assert find_unsafe_callable_argument((1, "x", len), {"key": str.upper}) is None
        refused = find_unsafe_callable_argument((1,), {"key": "{0}".format})
        assert refused is not None
        assert refused[1] == "Use f-strings instead."


class FakePromise:
    """Stands in for Django's lazy string: not a `str`, but with a `format` that follows paths."""

    def __init__(self, text: str) -> None:
        self.text = text

    def format(self, *args: Any, **kwargs: Any) -> str:
        return self.text.format(*args, **kwargs)

    def format_map(self, mapping: Any) -> str:
        return self.text.format_map(mapping)


class TestDjangoLazyStrings:
    """A lazy-string function in the context lets the template choose the format text."""

    @pytest.fixture
    def fake_django(self, monkeypatch: pytest.MonkeyPatch) -> None:
        module = types.ModuleType("django.utils.functional")
        module.Promise = FakePromise  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "django.utils.functional", module)

    @pytest.mark.usefixtures("fake_django")
    @pytest.mark.parametrize(
        "source",
        [
            "lazy('{0._trigger}').format(obj)",
            "[obj].sort(key=lazy('{0._trigger}').format)",
            "lazy('{o._trigger}').format_map({'o': obj})",
        ],
    )
    def test_format_on_a_lazy_string_is_refused(self, source):
        assert_refused(source, lazy=FakePromise, obj=Holder())

    @pytest.mark.usefixtures("fake_django")
    def test_a_bound_lazy_format_from_the_context_is_refused(self):
        assert_refused("[obj].sort(key=fmt)", fmt=FakePromise("{0._trigger}").format, obj=Holder())

    def test_with_real_django(self):
        functional = pytest.importorskip("django.utils.functional")
        assert_refused("[obj].sort(key=lazy('{0._trigger}').format)", lazy=functional.lazystr, obj=Holder())


class TestArgumentsTheCheckCannotRead:
    def test_an_argument_whose_lookup_raises_is_refused(self):
        error = assert_refused("apply(f, 1)", apply=lambda f, x: f(x), f=RaisingLookup())
        # The object's own error stays attached, so the reason is not lost.
        assert isinstance(error.__cause__, KeyError)


class TestValidateCallableHook:
    def test_the_hook_sees_functions_passed_as_arguments(self):
        def refuse_label(func: Any) -> bool:
            return getattr(func, "__name__", "") != "label"

        with pytest.raises(SecurityError, match="cannot be passed to"):
            safe_eval("[1].sort(key=obj.label)", validate_callable=refuse_label)({"obj": Holder()})

    def test_the_hook_allows_what_it_allows(self):
        items = [2, 1]
        safe_eval("items.sort(key=obj.label)", validate_callable=lambda _func: True)({"items": items, "obj": Holder()})
        assert items == [1, 2]
