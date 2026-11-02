"""
A template cannot take over the sandbox's own helpers through a name it binds.

The generated code calls `_sx_variable(...)`, `_sx_attribute(...)` and the other helpers by
name, and passes the real context mapping to them as `_sx_context`. Every one of those names
starts with `_sx_`. A template reads a free name through `_sx_variable()`, which refuses `_`
names, and the Rust transformer refuses a lambda parameter or comprehension variable that
starts with `_sx_`. Every other name, including the words the helpers are named after, works
as an ordinary name. These tests run whole expressions through the Rust transformer and the
Python runtime together, so they need the Rust extension built from the current source.
"""

import types

import pytest

from citry_core.safe_eval import SecurityError, compile_expr, safe_eval

# The words the helpers are named after. Templates use them as ordinary names, such as
# `<source c-for="source in sources">`.
HELPER_WORDS = [
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

# The names the generated code reads. The Rust test
# `test_generated_names_list_matches_what_the_transformer_writes` checks this list against
# the code the transformer writes; this copy only drives the Python-side cases.
GENERATED_NAMES = [f"_sx_{word}" for word in HELPER_WORDS]


class Document:
    """A context object with a public and an underscore attribute."""

    public = "public-value"
    _hidden = "hidden-value"


def evaluate(expression: str, /, **context):
    # The expression is positional-only because a context name may be `source`.
    return safe_eval(expression)(context)


class TestHelperWordsAreOrdinaryNames:
    @pytest.mark.parametrize("word", HELPER_WORDS)
    def test_a_lambda_parameter(self, word):
        assert evaluate(f"(lambda {word}: {word} + 1)(1)") == 2
        assert evaluate(f"(lambda *{word}: len({word}))(1, 2)", len=len) == 2

    @pytest.mark.parametrize("word", HELPER_WORDS)
    def test_a_comprehension_variable(self, word):
        assert evaluate(f"[{word} * 2 for {word} in items]", items=[1, 2]) == [2, 4]
        assert evaluate(f"{{{word}: 1 for {word} in items}}", items=["a"]) == {"a": 1}

    @pytest.mark.parametrize("word", HELPER_WORDS)
    def test_the_checks_still_run_inside_the_scope(self, word):
        # The helper calls inside the scope keep their own names, so attribute, item,
        # and variable checks still apply next to a parameter with a helper's word.
        assert evaluate(f"(lambda {word}: obj.public)(1)", obj=Document()) == "public-value"
        with pytest.raises(SecurityError):
            evaluate(f"(lambda {word}: obj._hidden)(1)", obj=Document())
        with pytest.raises(SecurityError):
            evaluate(f"[_private for {word} in items]", items=[1], _private=1)

    def test_a_c_for_style_loop_over_sources(self):
        # The loop Citry UI's `CImage` writes, run as the generator a `<c-for>` uses.
        sources = [{"src": "a.webp"}, {"src": "b.avif"}]
        assert evaluate("[source['src'] for source in sources]", sources=sources) == ["a.webp", "b.avif"]

    def test_expressions_that_once_replaced_a_helper_now_run_the_check(self):
        # The parameter named `attribute` is the template's own value, and `obj.__class__`
        # still goes through the real attribute check.
        with pytest.raises(SecurityError):
            evaluate("(lambda attribute: obj.__class__)(lambda *a: a[3])", obj=Document())
        # `x` is read from the context through the real variable helper.
        assert evaluate("(lambda variable: x)(lambda ctx, *a: ctx)", x=7) == 7
        # The walrus writes into the real context mapping, not into `session`.
        context = {"session": {}}
        safe_eval("(lambda context: (planted := 'written'))(session)")(context)
        assert context["planted"] == "written"
        assert context["session"] == {}

    @pytest.mark.parametrize("sandboxed", [True, False])
    def test_both_modes_accept_the_same_text(self, sandboxed):
        # Turning the sandbox off must not change which text is accepted.
        assert compile_expr("(lambda call: call + 1)(1)", sandboxed=sandboxed)({}) == 2
        assert compile_expr("[format for format in formats]", sandboxed=sandboxed)({"formats": [1]}) == [1]

    def test_helper_words_are_ordinary_context_variables(self):
        values = {"context": 1, "source": 2, "call": 3, "format": 4, "slice": 5}
        assert evaluate("context + source + call + format + slice", **values) == 15


class TestTheGeneratedPrefixIsReserved:
    @pytest.mark.parametrize("name", [*GENERATED_NAMES, "_sx_other"])
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
    def test_a_lambda_parameter_is_refused(self, name, shape):
        with pytest.raises(SyntaxError, match=rf"'{name}' starts with '_sx_'.*lambda parameter"):
            safe_eval(shape.format(name=name))

    @pytest.mark.parametrize("name", [*GENERATED_NAMES, "_sx_other"])
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
    def test_a_comprehension_variable_is_refused(self, name, shape):
        with pytest.raises(SyntaxError, match=rf"'{name}' starts with '_sx_'.*comprehension variable"):
            safe_eval(shape.format(name=name))

    def test_replacing_the_variable_helper_is_refused(self):
        # Without the refusal, the template's lambda would receive the real context
        # mapping as its first argument, and `.get("_private")` would read a hidden name.
        with pytest.raises(SyntaxError, match="lambda parameter"):
            safe_eval("(lambda _sx_variable: x)(lambda ctx, *a: ctx).get('_private')")

    def test_reading_the_real_context_through_a_loop_name_is_refused(self):
        with pytest.raises(SyntaxError, match="comprehension variable"):
            safe_eval("[c for c in [1] for _sx_context in [0]]")

    def test_the_full_width_spelling_is_refused(self):
        # Python compiles identifiers in NFKC form, so this is the name `_sx_variable`.
        with pytest.raises(SyntaxError, match="'_sx_variable'"):
            safe_eval("lambda _\uff53\uff58_variable: 1")

    @pytest.mark.parametrize("sandboxed", [True, False])
    def test_both_modes_refuse_the_same_text(self, sandboxed):
        with pytest.raises(SyntaxError, match="lambda parameter"):
            compile_expr("lambda _sx_call: _sx_call(1)", sandboxed=sandboxed)
        with pytest.raises(SyntaxError, match="comprehension variable"):
            compile_expr("[_sx_format for _sx_format in formats]", sandboxed=sandboxed)

    @pytest.mark.parametrize("name", GENERATED_NAMES)
    def test_a_generated_name_cannot_be_read(self, name):
        # A free name goes through the variable helper, which refuses `_` names.
        with pytest.raises(SecurityError):
            evaluate(name)

    def test_names_close_to_the_prefix_still_work(self):
        assert evaluate("(lambda _: 1)(0)") == 1
        assert evaluate("(lambda _context, sx_call: sx_call)(1, 2)") == 2
        assert evaluate("[1 for _ in items]", items=[0, 0]) == [1, 1]


def _names_read(code: types.CodeType) -> set[str]:
    # Global names the code reads, including inside nested comprehensions and lambdas.
    names = set(code.co_names)
    for constant in code.co_consts:
        if isinstance(constant, types.CodeType):
            names |= _names_read(constant)
    return names


def test_the_runtime_defines_every_name_the_generated_code_reads():
    # One expression that makes the transformer write every helper. The runtime's
    # evaluation namespace is the generated function's globals, so a helper the Rust
    # side writes but the runtime does not define would fail here, not on first use.
    evaluate = safe_eval("[(w := a.b[1:2](c)) for a in d if f'{a!r:{w}}'] or t'{x}'")
    generated = next(
        cell.cell_contents for cell in evaluate.__closure__ if isinstance(cell.cell_contents, types.FunctionType)
    )
    read = {name for name in _names_read(generated.__code__) if name.startswith("_sx_")}
    # `_sx_context` is the function's own local, so it is not a global read.
    assert read == set(GENERATED_NAMES) - {"_sx_context"}
    assert read <= set(generated.__globals__)
    # Python 3.11 runs the comprehension as its own function, so the value it reads
    # becomes a shared cell; 3.12 and later inline it as a plain local.
    code = generated.__code__
    assert "_sx_context" in code.co_varnames + code.co_cellvars


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
