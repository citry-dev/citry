"""Token-stream tests for the top-level ``citry`` lexer (Python plus the embeds)."""

from pygments.lexers import get_lexer_by_name
from pygments.token import Keyword, Name, String


def lex(src):
    """Lex `src` with the citry lexer, dropping whitespace-only tokens."""
    lexer = get_lexer_by_name("citry")
    return [(tok, val) for tok, val in lexer.get_tokens(src) if val.strip()]


def test_alias_and_name():
    lexer = get_lexer_by_name("citry")
    assert lexer.name == "Citry Python"
    assert "citry" in lexer.aliases


def test_template_opener_and_html_embed():
    toks = lex('class C(Component):\n    template = """<div>{{ x }}</div>"""\n')
    assert (Name.Variable, "template") in toks
    assert (String.Doc, '"""') in toks
    assert (Name.Tag, "div") in toks
    # the {{ }} body is handed to the Python lexer
    assert (Name, "x") in toks


def test_js_opener_embeds_javascript():
    toks = lex('class C(Component):\n    js = """const x = `a`;"""\n')
    assert (Name.Variable, "js") in toks
    # `const` and a backtick template literal are JavaScript, not Python
    assert (Keyword.Declaration, "const") in toks
    assert (String.Backtick, "`") in toks


def test_css_opener_embeds_css():
    toks = lex('class C(Component):\n    css = """a { color: red; }"""\n')
    assert (Name.Variable, "css") in toks
    assert (Keyword, "color") in toks
    assert (Keyword.Constant, "red") in toks


def test_typed_opener_keeps_annotation_and_embeds_html():
    toks = lex("class C(Component):\n    template: types.html = '''<br/>'''\n")
    assert (Name.Variable, "template") in toks
    assert (Name.Class, "types.html") in toks
    assert (Name.Tag, "br") in toks


def test_triple_single_quote_body():
    toks = lex("class C(Component):\n    css = '''a{}'''\n")
    assert (String.Doc, "'''") in toks
    assert (Name.Tag, "a") in toks


def test_full_component_highlights_all_three_and_stays_python():
    src = (
        "class Card(Component):\n"
        '    template = """<c-slot></c-slot>{{ title }}"""\n'
        '    js = """const n = 1;"""\n'
        '    css = """.card { color: red; }"""\n'
    )
    toks = lex(src)
    assert (Name.Variable, "template") in toks
    assert (Name.Variable, "js") in toks
    assert (Name.Variable, "css") in toks
    # the class itself is still ordinary Python
    assert (Name.Class, "Card") in toks
