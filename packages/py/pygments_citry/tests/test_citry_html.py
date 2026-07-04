"""Token-stream tests for the Citry template constructs inside a ``template`` string."""

from pygments.lexers import get_lexer_by_name
from pygments.token import Comment, Name, Operator, Punctuation, String, Text


def lex_template(body):
    """Lex a component whose ``template`` is `body`, returning its non-blank tokens."""
    lexer = get_lexer_by_name("citry")
    src = 'class C(Component):\n    template = """' + body + '"""\n'
    return [(tok, val) for tok, val in lexer.get_tokens(src) if val.strip()]


def lex_html(body):
    """Lex `body` directly with the standalone ``citry-html`` lexer (a bare template)."""
    lexer = get_lexer_by_name("citry-html")
    return [(tok, val) for tok, val in lexer.get_tokens(body) if val.strip()]


def test_interpolation_body_is_python():
    toks = lex_template("<p>{{ count }}</p>")
    assert (Punctuation, "{{") in toks
    assert (Punctuation, "}}") in toks
    assert (Name, "count") in toks


def test_interpolation_boundary_skips_string_literals():
    # the "}}" inside the Python string must not end the block early
    toks = lex_template('{{ "}}" }}')
    # exactly one closing }} punctuation, the real end (not the one in the string)
    assert [v for tok, v in toks if (tok, v) == (Punctuation, "}}")] == ["}}"]
    assert (String.Double, "}}") in toks  # the "}}" is part of a Python string


def test_template_comment():
    toks = lex_template("<i>{# note #}</i>")
    assert (Comment, "{# note #}") in toks


def test_lone_brace_is_text_not_interpolation():
    toks = lex_template("a { b")
    assert (Text, "{") in toks
    assert (Punctuation, "{{") not in toks


def test_builtin_tag_distinct_from_user_component():
    toks = lex_template("<c-slot></c-slot><c-Card></c-Card>")
    assert (Name.Builtin, "c-slot") in toks
    assert (Name.Tag, "c-Card") in toks


def test_dynamic_attribute_value_is_python():
    toks = lex_template('<li c-for="item in items"></li>')
    assert (Name.Attribute, "c-for") in toks
    assert (Operator.Word, "in") in toks  # `in` from the Python expression


def test_dynamic_attribute_single_quoted_and_bare():
    toks = lex_template("<b c-if='a and b' c-x=y></b>")
    assert (Operator.Word, "and") in toks
    assert (Name.Attribute, "c-x") in toks
    assert (Name, "y") in toks


def test_c_raw_body_is_verbatim():
    toks = lex_template("<c-raw>a < b {{ z }}</c-raw>")
    assert (Name.Builtin, "c-raw") in toks
    # nothing inside c-raw is interpreted
    assert (Punctuation, "{{") not in toks
    assert (Name, "z") not in toks


def test_framework_attributes_are_accepted():
    toks = lex_template('<div @click="f" :class="c" [style]="s" (tap)="t"></div>')
    assert (Name.Attribute, "@click") in toks
    assert (Name.Attribute, "[style]") in toks
    assert (Name.Attribute, "(tap)") in toks


def test_boolean_attributes():
    toks = lex_template("<input disabled [hidden]>")
    assert (Name.Attribute, "disabled") in toks
    assert (Name.Attribute, "[hidden]") in toks


def test_interpolation_boundary_counts_nested_braces():
    # the dict's closing }} must not end the block; the real end is the last }}
    toks = lex_template('{{ {"a": {1: 2}} }}')
    assert [v for tok, v in toks if (tok, v) == (Punctuation, "}}")] == ["}}"]
    assert (Punctuation, "{") in toks  # the dict braces are highlighted as Python


def test_builtin_tag_special_attributes_are_python():
    # cond / each / is on a built-in tag hold Python expressions, not strings
    toks = lex_template('<c-if cond="a and b"></c-if><c-for each="x in xs"></c-for><c-component is="widget" />')
    assert (Name.Attribute, "cond") in toks
    assert (Name.Attribute, "each") in toks
    assert (Name.Attribute, "is") in toks
    assert (Operator.Word, "and") in toks  # cond value lexed as Python
    assert (Operator.Word, "in") in toks  # each value lexed as Python
    assert (Name, "widget") in toks  # is value lexed as Python


def test_is_on_an_ordinary_tag_stays_a_string():
    # `is` is a real HTML attribute; on a plain element its value is a string
    toks = lex_template('<button is="my-btn">x</button>')
    assert (Name.Attribute, "is") in toks
    assert (String, '"my-btn"') in toks


def test_interpolation_skips_escaped_quote_in_string():
    # a backslash-escaped quote must not end the string mid-scan
    toks = lex_template(r'{{ "a\"}}b" + c }}')
    assert [v for tok, v in toks if (tok, v) == (Punctuation, "}}")] == ["}}"]
    assert (Name, "c") in toks


def test_interpolation_without_surrounding_whitespace():
    toks = lex_template("{{x}}")
    assert (Punctuation, "{{") in toks
    assert (Punctuation, "}}") in toks
    assert (Name, "x") in toks


def test_unclosed_interpolation_degrades_to_body():
    # no closing }}: the rest is lexed as the expression, and nothing crashes
    toks = lex_html("{{ oops")
    assert (Punctuation, "{{") in toks
    assert (Name, "oops") in toks
    assert (Punctuation, "}}") not in toks


def test_malformed_interpolations_do_not_crash():
    # an unterminated string and a lone trailing } are degenerate but must not
    # raise; the scanner just runs to the end of the text
    for body in ('{{ "unterminated', "{{ a}"):
        toks = lex_html(body)
        assert (Punctuation, "{{") in toks


def test_standalone_citry_html_lexer_on_a_bare_template():
    toks = lex_html('<c-if cond="ok">{# note #}<c-slot />{{ user.name }}</c-if>')
    assert (Name.Builtin, "c-if") in toks
    assert (Name.Builtin, "c-slot") in toks
    assert (Comment, "{# note #}") in toks
    assert (Name.Attribute, "cond") in toks
    assert (Name, "ok") in toks  # cond value is Python
    assert (Name, "user") in toks  # {{ }} body is Python
