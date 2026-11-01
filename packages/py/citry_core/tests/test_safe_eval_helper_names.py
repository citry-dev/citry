"""
The sandbox's own helper names cannot be taken over by a lambda or a comprehension.

The generated code calls `variable(...)`, `attribute(...)` and the other helpers by plain
name, and passes the real `context` mapping to them. A lambda parameter or a comprehension
variable with one of those names would replace the helper inside its scope. These tests run
whole expressions through the Rust transformer and the Python runtime together, so they need
the Rust extension built from the current source.
"""

import pytest

from citry_core.safe_eval import SecurityError, compile_expr, safe_eval

# The names the generated code uses. The Rust test
# `test_generated_names_list_matches_what_the_transformer_writes` checks the list there
# against the code the transformer writes; this copy only drives the Python-side cases.
HELPER_NAMES = [
    "variable",
    "attribute",
    "subscript",
    "call",
    "assign",
    "slice",
    "interpolation",
    "template",
    "format",
    "source",
    "context",
]


class Document:
    """A context object with a public and an underscore attribute."""

    public = "public-value"
    _hidden = "hidden-value"


def evaluate(expression: str, /, **context):
    # The expression is positional-only because a context name may be `source`.
    return safe_eval(expression)(context)


class TestLambdaParameters:
    @pytest.mark.parametrize("name", HELPER_NAMES)
    @pytest.mark.parametrize(
        "shape",
        [
            "lambda {name}: 1",
            "lambda a, {name}=1: 1",
            "lambda a, /, {name}: 1",
            "lambda a, *, {name}: 1",
            "lambda *{name}: 1",
            "lambda **{name}: 1",
        ],
    )
    def test_the_name_is_refused(self, name, shape):
        with pytest.raises(SyntaxError, match=rf"'{name}' is a name the sandbox uses.*lambda parameter"):
            safe_eval(shape.format(name=name))

    def test_replacing_the_attribute_check_is_refused(self):
        # With the check replaced, this returned the object whose `__class__` the
        # sandbox hides everywhere else.
        with pytest.raises(SyntaxError, match="lambda parameter"):
            safe_eval("(lambda attribute: obj.__class__)(lambda *a: a[3])")

    def test_reading_the_real_context_through_the_variable_helper_is_refused(self):
        # The replacement function received the real context mapping as its first
        # argument, so `.get("_private")` read a variable the sandbox hides.
        with pytest.raises(SyntaxError, match="lambda parameter"):
            safe_eval("(lambda variable: x)(lambda ctx, *a: ctx).get('_private')")

    def test_writing_into_another_object_through_the_context_name_is_refused(self):
        # `assign` stores into the mapping it receives; with `context` replaced, that
        # was any object the template could reach, such as a session.
        with pytest.raises(SyntaxError, match="lambda parameter"):
            safe_eval("(lambda context: (planted := 'written'))(session)")


class TestComprehensionVariables:
    @pytest.mark.parametrize("name", HELPER_NAMES)
    @pytest.mark.parametrize(
        "shape",
        [
            "[1 for {name} in items]",
            "{{1 for {name} in items}}",
            "{{1: 2 for {name} in items}}",
            "(1 for {name} in items)",
            "[1 for a, {name} in items]",
            "[1 for a in items for {name} in a]",
        ],
    )
    def test_the_name_is_refused(self, name, shape):
        with pytest.raises(SyntaxError, match=rf"'{name}' is a name the sandbox uses.*comprehension variable"):
            safe_eval(shape.format(name=name))

    def test_naming_the_loop_variable_context_to_read_the_real_context_is_refused(self):
        # The first iterable is evaluated outside the comprehension, where `context`
        # is the real mapping.
        with pytest.raises(SyntaxError, match="comprehension variable"):
            safe_eval("[c for c in [context] for context in [0]]")

    def test_a_loop_clause_is_checked_like_a_comprehension(self):
        # `<c-for each="...">` runs its clause as a generator expression.
        with pytest.raises(SyntaxError, match="comprehension variable"):
            safe_eval("((template,) for template in templates)")


class TestOtherSpellingsAndModes:
    def test_the_full_width_spelling_is_refused(self):
        # Python compiles identifiers in NFKC form, so this is the name `attribute`.
        with pytest.raises(SyntaxError, match="'attribute'"):
            safe_eval("lambda \uff41\uff54\uff54\uff52\uff49\uff42\uff55\uff54\uff45: 1")

    @pytest.mark.parametrize("sandboxed", [True, False])
    def test_both_modes_refuse_the_same_text(self, sandboxed):
        # Turning the sandbox off must not change which text is accepted.
        with pytest.raises(SyntaxError, match="lambda parameter"):
            compile_expr("lambda call: call(1)", sandboxed=sandboxed)
        with pytest.raises(SyntaxError, match="comprehension variable"):
            compile_expr("[format for format in formats]", sandboxed=sandboxed)


class TestNamesThatStillWork:
    def test_names_close_to_a_helper_name_are_loop_variables_and_parameters(self):
        assert evaluate("[s for s in sources]", sources=[1, 2]) == [1, 2]
        assert evaluate("[callable for callable in items]", items=[1]) == [1]
        assert evaluate("(lambda variables, _context: variables)(1, 2)") == 1
        assert evaluate("[x for contexts in items for x in contexts]", items=[[1], [2]]) == [1, 2]

    def test_helper_names_are_ordinary_variables_when_read_from_the_context(self):
        # Reading a context variable named `context` is a lookup, not a use of the helper.
        values = {"context": 1, "source": 2, "call": 3, "format": 4, "slice": 5}
        assert evaluate("context + source + call + format + slice", **values) == 15

    def test_a_helper_name_can_be_assigned_with_the_walrus_operator(self):
        # The assignment is written into the context mapping, so it cannot replace a
        # helper, and it stays allowed.
        context = {"obj": Document()}
        assert safe_eval("((variable := 5) and obj.public)")(context) == "public-value"
        assert context["variable"] == 5
        assert safe_eval("variable + 1")(context) == 6

    def test_underscore_variables_and_attributes_stay_hidden(self):
        with pytest.raises(SecurityError):
            evaluate("_private", _private=1)
        with pytest.raises(SecurityError):
            evaluate("obj._hidden", obj=Document())


class TestUnsupportedComprehensionTargets:
    @pytest.mark.parametrize(
        "source",
        [
            "[1 for a.b in items]",
            "[1 for a[0] in items]",
            "[1 for [a, b] in items]",
            "[1 for *a, b in items]",
        ],
    )
    def test_they_raise_a_syntax_error(self, source):
        # These stopped the Rust code with a panic, which Python received as a
        # `BaseException` that `except Exception` does not catch.
        with pytest.raises(SyntaxError, match="comprehension variable must be a name or a tuple of names"):
            safe_eval(source)
