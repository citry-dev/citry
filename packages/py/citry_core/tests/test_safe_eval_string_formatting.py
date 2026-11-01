"""
The sandbox refuses every string method that reads attribute paths named inside the string.

`"{0.name}".format(obj)` reads `obj.name`, and `"{0.__class__}"` reads what the sandbox
hides everywhere else, because the format methods look up each field with the real
`getattr`. The sandbox refuses `str.format` and `str.format_map`. These tests cover the
other classes with the same behavior: `str` subclasses that define their own methods
(`markupsafe.Markup` is one), `collections.UserString`, and `string.Formatter`.
"""

import collections
import functools
import operator
import string
from typing import Any, SupportsIndex

import pytest

from citry_core.safe_eval import SecurityError, safe_eval
from citry_core.safe_eval.sandbox import is_safe_attribute, is_safe_callable

SECRET = "SECRET-MARKER"  # noqa: S105 - a marker value that tests look for, not a password


class Holder:
    """A context object whose public attribute holds data the template must not format out."""

    secret = SECRET
    _hidden = "HIDDEN-MARKER"

    def format(self, currency: str) -> str:
        """A method that is called `format` but formats nothing from a template string."""
        return f"12 {currency}"


class PathFormatter(string.Formatter):
    """Reads each `{field}` with the real `getattr`, like markupsafe's formatter."""


class EscapingStr(str):
    """
    A `str` subclass with its own `format` and `format_map`, built the way `Markup` builds them.

    `replace` returns the subclass as `Markup.replace` does, so an expression can write
    the format text itself, e.g. `value.replace("x", "{0.secret}").format(obj)`.
    """

    __slots__ = ()

    def format(self, *args: Any, **kwargs: Any) -> "EscapingStr":
        return self.__class__(PathFormatter().vformat(self, args, kwargs))

    def format_map(self, mapping: Any) -> "EscapingStr":
        return self.__class__(PathFormatter().vformat(self, (), mapping))

    def replace(self, old: str, new: str, count: SupportsIndex = -1) -> "EscapingStr":
        return self.__class__(super().replace(old, new, count))


class InheritingStr(str):
    """A `str` subclass that defines no format methods of its own."""

    __slots__ = ()


class SubclassedUserString(collections.UserString):
    """A subclass of `UserString`, which is not a `str` subclass."""


def evaluate(source: str, **context: Any) -> Any:
    return safe_eval(source)(context)


def assert_refused_without_leaking(source: str, **context: Any) -> None:
    with pytest.raises(SecurityError) as error:
        evaluate(source, **context)
    # The refusal comes before any formatting, so the data never reaches the message.
    assert SECRET not in str(error.value)


# Each value is a string the template author controls the text of. The text asks for
# the attribute `secret` of the first argument.
FORMAT_TEXT = "{0.secret}"
FORMAT_MAP_TEXT = "{o.secret}"


@pytest.fixture(
    params=[
        pytest.param(EscapingStr, id="str-subclass-with-own-methods"),
        pytest.param(InheritingStr, id="str-subclass-inheriting-methods"),
        pytest.param(collections.UserString, id="UserString"),
        pytest.param(str, id="str"),
    ]
)
def string_type(request: pytest.FixtureRequest) -> type:
    return request.param


class TestStringTypes:
    def test_format_is_refused(self, string_type):
        assert_refused_without_leaking("value.format(holder)", value=string_type(FORMAT_TEXT), holder=Holder())

    def test_format_map_is_refused(self, string_type):
        assert_refused_without_leaking(
            "value.format_map({'o': holder})", value=string_type(FORMAT_MAP_TEXT), holder=Holder()
        )

    def test_the_format_text_can_be_built_inside_the_expression(self):
        # The author controls the text through `replace`, so the value the app passes in does
        # not have to contain a replacement field for the hole to matter.
        assert_refused_without_leaking(
            "value.replace('x', '{0.secret}').format(holder)", value=EscapingStr("x"), holder=Holder()
        )

    @pytest.mark.parametrize("method", ["format", "format_map"])
    def test_a_bound_method_passed_in_by_the_app_is_refused(self, string_type, method):
        text = FORMAT_TEXT if method == "format" else FORMAT_MAP_TEXT
        bound = getattr(string_type(text), method)
        argument = "holder" if method == "format" else "{'o': holder}"
        assert_refused_without_leaking(f"fn({argument})", fn=bound, holder=Holder())

    @pytest.mark.parametrize("method", ["format", "format_map"])
    def test_a_method_taken_from_the_class_is_refused(self, string_type, method):
        # An app that passes the class (to build values) also hands out its unbound functions.
        text = FORMAT_TEXT if method == "format" else FORMAT_MAP_TEXT
        argument = "holder" if method == "format" else "{'o': holder}"
        assert_refused_without_leaking(
            f"cls.{method}(value, {argument})", cls=string_type, value=string_type(text), holder=Holder()
        )

    @pytest.mark.parametrize("method", ["format", "format_map"])
    def test_a_user_string_function_stored_first_is_refused_when_called(self, method):
        # `UserString.format` is a plain function that is not the one on `str`, so the
        # call check must know it by itself.
        text = FORMAT_TEXT if method == "format" else FORMAT_MAP_TEXT
        argument = "holder" if method == "format" else "{'o': holder}"
        context: dict[str, Any] = {
            "cls": collections.UserString,
            "value": collections.UserString(text),
            "holder": Holder(),
        }
        safe_eval(f"(fn := cls.{method})")(context)
        with pytest.raises(SecurityError) as error:
            safe_eval(f"fn(value, {argument})")(context)
        assert SECRET not in str(error.value)

    def test_the_error_names_the_replacement_for_every_string_type(self, string_type):
        with pytest.raises(SecurityError, match=r"Use f-strings instead\."):
            evaluate("value.format(holder)", value=string_type(FORMAT_TEXT), holder=Holder())


class TestFormatter:
    FORMATTER_METHODS = [
        ("format", "'{0.secret}', holder"),
        ("vformat", "'{0.secret}', (holder,), {}"),
        ("get_field", "'0.secret', (holder,), {}"),
        ("get_value", "0, (holder,), {}"),
        ("parse", "'{0.secret}'"),
        ("convert_field", "holder, 's'"),
        ("format_field", "holder, ''"),
        ("check_unused_args", "set(), (), {}"),
    ]

    @pytest.mark.parametrize(("method", "arguments"), FORMATTER_METHODS)
    def test_every_method_of_a_formatter_instance_is_refused(self, method, arguments):
        # `set` and `Holder` are passed in only so the arguments can be written; the
        # refusal happens before any of them runs.
        assert_refused_without_leaking(
            f"formatter.{method}({arguments})", formatter=string.Formatter(), holder=Holder(), set=set
        )

    @pytest.mark.parametrize(("method", "arguments"), FORMATTER_METHODS)
    def test_every_method_of_a_formatter_subclass_instance_is_refused(self, method, arguments):
        assert_refused_without_leaking(
            f"formatter.{method}({arguments})", formatter=PathFormatter(), holder=Holder(), set=set
        )

    def test_a_formatter_built_inside_the_expression_is_refused(self):
        # The app passes the class (or a module that holds it); the author builds the instance.
        assert_refused_without_leaking(
            "Formatter().format('{0.secret}', holder)", Formatter=PathFormatter, holder=Holder()
        )

    def test_a_bound_method_passed_in_by_the_app_is_refused(self):
        assert_refused_without_leaking("fn('{0.secret}', holder)", fn=PathFormatter().format, holder=Holder())

    def test_a_function_taken_from_the_class_is_refused(self):
        assert_refused_without_leaking(
            "Formatter.format(formatter, '{0.secret}', holder)",
            Formatter=string.Formatter,
            formatter=PathFormatter(),
            holder=Holder(),
        )

    def test_a_subclass_override_taken_from_the_class_is_refused(self):
        assert_refused_without_leaking(
            "Formatter.get_field(formatter, '0.secret', (holder,), {})",
            Formatter=PathFormatter,
            formatter=PathFormatter(),
            holder=Holder(),
        )


class TestWrappers:
    def test_partial_does_not_hide_a_refused_method(self):
        value = EscapingStr(FORMAT_TEXT)
        assert_refused_without_leaking(
            "partial(value.format)(holder)", partial=functools.partial, value=value, holder=Holder()
        )

    def test_partial_does_not_hide_a_refused_function(self):
        # `getattr` is refused when called directly; wrapping it must not change that.
        assert_refused_without_leaking(
            "partial(read, holder)('secret')", partial=functools.partial, read=getattr, holder=Holder()
        )

    def test_nested_partials_do_not_hide_a_refused_function(self):
        assert_refused_without_leaking(
            "partial(partial(read, holder), 'secret')()", partial=functools.partial, read=getattr, holder=Holder()
        )

    def test_partial_of_a_safe_function_still_works(self):
        assert evaluate("partial(add, 1)(2)", partial=functools.partial, add=operator.add) == 3

    @pytest.mark.parametrize("factory", [operator.attrgetter, operator.methodcaller])
    def test_building_a_reader_for_a_path_the_template_names_is_refused(self, factory):
        # `attrgetter("__class__")(obj)` reads what the sandbox hides, so the author may
        # not build one. A reader the app builds with its own path is a different case.
        assert_refused_without_leaking("factory('secret')(holder)", factory=factory, holder=Holder())

    def test_a_reader_the_app_built_is_still_callable(self):
        assert evaluate("read(holder)", read=operator.attrgetter("secret"), holder=Holder()) == SECRET


class TestUnrelatedCodeKeepsWorking:
    """A method called `format` is refused only when it formats a string."""

    def test_a_method_named_format_on_an_ordinary_class(self):
        assert evaluate("holder.format('EUR')", holder=Holder()) == "12 EUR"

    def test_f_strings(self):
        assert evaluate("f'{holder.secret} {n:03d}'", holder=Holder(), n=7) == f"{SECRET} 007"

    def test_other_methods_of_a_str_subclass(self):
        value = EscapingStr("a-b")
        assert evaluate("value.upper()", value=value) == "A-B"
        assert evaluate("value.replace('-', '+')", value=value) == "a+b"
        assert evaluate("'-'.join(parts)", parts=["a", "b"]) == "a-b"
        assert evaluate("value + '!'", value=value) == "a-b!"

    def test_percent_formatting(self):
        assert evaluate("'%s-%d' % (name, n)", name="x", n=3) == "x-3"
        assert evaluate("'%(name)s' % mapping", mapping={"name": "x"}) == "x"

    def test_an_item_named_format_in_a_dict(self):
        assert evaluate("d['format']", d={"format": "yes"}) == "yes"
        assert evaluate("d.format", d=type("Bag", (), {"format": "yes"})()) == "yes"

    def test_a_method_named_like_a_formatter_method_on_another_class(self):
        class Parser:
            def parse(self, text: str) -> str:
                return text.upper()

        assert evaluate("parser.parse('a')", parser=Parser()) == "A"

    def test_formatter_attributes_that_are_not_methods_of_the_formatter(self):
        class Tagged(string.Formatter):
            label = "tag"

        assert evaluate("formatter.label", formatter=Tagged()) == "tag"


class TestPolicyFunctions:
    """The rules, checked on their own so a change shows up without a full expression."""

    @pytest.mark.parametrize("name", ["format", "format_map"])
    def test_attribute_policy_for_string_subclasses(self, name):
        assert is_safe_attribute(EscapingStr("x"), name) is False
        assert is_safe_attribute(InheritingStr("x"), name) is False
        assert is_safe_attribute(SubclassedUserString("x"), name) is False
        assert is_safe_attribute(EscapingStr, name) is False
        assert is_safe_attribute(InheritingStr, name) is False
        assert is_safe_attribute(SubclassedUserString, name) is False

    @pytest.mark.parametrize("name", ["format", "format_map"])
    def test_attribute_policy_leaves_exact_str_to_the_call_check(self, name):
        # `str.format` stays readable so the refusal comes from the call, with its message.
        for exact in (str, collections.UserString):
            assert is_safe_attribute(exact("x"), name) is True
            assert is_safe_attribute(exact, name) is True
            assert is_safe_callable(getattr(exact("x"), name)) == (False, "Use f-strings instead.")
            assert is_safe_callable(getattr(exact, name)) == (False, "Use f-strings instead.")

    @pytest.mark.parametrize("name", ["upper", "replace", "join", "strip"])
    def test_attribute_policy_leaves_other_string_methods_alone(self, name):
        assert is_safe_attribute(EscapingStr("x"), name) is True
        assert is_safe_attribute(EscapingStr, name) is True

    def test_attribute_policy_for_formatters(self):
        formatter = PathFormatter()
        for name in ("format", "vformat", "get_field", "get_value", "parse", "convert_field", "format_field"):
            assert is_safe_attribute(formatter, name) is False
            assert is_safe_attribute(PathFormatter, name) is False
            assert is_safe_attribute(string.Formatter, name) is False
        assert is_safe_attribute(formatter, "unrelated") is True

    def test_callable_policy_looks_at_the_owner_not_the_function(self):
        for value in (EscapingStr("x"), InheritingStr("x"), collections.UserString("x"), SubclassedUserString("x")):
            assert is_safe_callable(value.format)[0] is False
            assert is_safe_callable(value.format_map)[0] is False
        for name in ("format", "vformat", "get_field", "parse"):
            assert is_safe_callable(getattr(PathFormatter(), name))[0] is False
        # Other methods of the same objects are fine.
        assert is_safe_callable(EscapingStr("x").upper) == (True, None)
        assert is_safe_callable(Holder().format) == (True, None)

    def test_callable_policy_for_plain_functions_is_unchanged(self):
        assert is_safe_callable(len) == (True, None)
        assert is_safe_callable(getattr)[0] is False
        assert is_safe_callable(print) == (True, None)
