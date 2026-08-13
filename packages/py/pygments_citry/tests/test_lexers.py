"""Token-stream tests for the top-level ``citry`` lexer (Python plus the embeds)."""

from pygments.lexers import get_lexer_by_name
from pygments.token import Comment, Keyword, Name, String


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


def test_messages_opener_embeds_fluent():
    toks = lex(
        'class C(Component):\n    messages = """# @param {str} $name - User name.\nhello = Welcome, { $name }."""\n'
    )
    assert (Name.Variable, "messages") in toks
    assert (Comment.Multiline, "# @param {str} $name - User name.") in toks
    assert (Name.Constant, "hello") in toks
    assert (Name.Variable, "$name") in toks


def test_indented_messages_keep_exact_python_offsets():
    lexer = get_lexer_by_name("citry")
    source = (
        'class C(Component):\n    messages = """\n'
        "      # @param {str} $name - User name.\n"
        "      hello = Welcome, { $name }.\n"
        '    """\n'
    )
    stream = list(lexer.get_tokens_unprocessed(source))

    assert any(
        offset == source.index("hello") and token is Name.Constant and value == "hello"
        for offset, token, value in stream
    )
    assert any(
        offset == source.index("$name", source.index("hello")) and token is Name.Variable and value == "$name"
        for offset, token, value in stream
    )


def test_typed_opener_keeps_annotation_and_embeds_html():
    toks = lex("class C(Component):\n    template: types.html = '''<br/>'''\n")
    assert (Name.Variable, "template") in toks
    assert (Name.Class, "types.html") in toks
    assert (Name.Tag, "br") in toks


def test_triple_single_quote_body():
    toks = lex("class C(Component):\n    css = '''a{}'''\n")
    assert (String.Doc, "'''") in toks
    assert (Name.Tag, "a") in toks


def test_full_component_highlights_all_assets_and_stays_python():
    src = (
        "class Card(Component):\n"
        '    template = """<c-slot></c-slot>{{ title }}"""\n'
        '    js = """const n = 1;"""\n'
        '    css = """.card { color: red; }"""\n'
        '    messages = """card-title = Account"""\n'
    )
    toks = lex(src)
    assert (Name.Variable, "template") in toks
    assert (Name.Variable, "js") in toks
    assert (Name.Variable, "css") in toks
    assert (Name.Variable, "messages") in toks
    assert (Name.Constant, "card-title") in toks
    # the class itself is still ordinary Python
    assert (Name.Class, "Card") in toks


def test_embeds_close_only_with_their_opening_quote_family():
    cases = (
        ("template", '"""', "'''", "<p>''' {{ after }}</p>", (Name, "after")),
        ("template", "'''", '"""', '<p>""" {{ after }}</p>', (Name, "after")),
        ("js", '"""', "'''", "const before = 1; /* ''' */ const after = 2;", (Name.Other, "after")),
        ("js", "'''", '"""', 'const before = 1; /* """ */ const after = 2;', (Name.Other, "after")),
        ("css", '"""', "'''", "a { /* ''' */ border-color: red; }", (Keyword, "border-color")),
        ("css", "'''", '"""', 'a { /* """ */ border-color: red; }', (Keyword, "border-color")),
        ("messages", '"""', "'''", "hello = ''' { $after }", (Name.Variable, "$after")),
        ("messages", "'''", '"""', 'hello = """ { $after }', (Name.Variable, "$after")),
    )

    for attribute, opener, other, body, expected in cases:
        source = f"class C(Component):\n    {attribute} = {opener}{body}{opener}\n    sentinel = 1\n"
        toks = lex(source)
        assert other in body
        assert expected in toks
        assert toks.count((String.Doc, opener)) == 2
        assert (Name, "sentinel") in toks


def test_escaped_matching_delimiter_stays_inside_template_with_exact_offsets():
    lexer = get_lexer_by_name("citry")
    for opener in ('"""', "'''"):
        body = f"<p>\\{opener} {{{{ after }}}}</p>"
        source = f"class C(Component):\n    template = {opener}{body}{opener}\n    sentinel = 1\n"
        stream = list(lexer.get_tokens_unprocessed(source))
        quotes = [(offset, value) for offset, token, value in stream if token is String.Doc and value == opener]

        assert quotes == [(source.index(opener), opener), (source.rindex(opener), opener)]
        assert any(token is Name and value == "after" for _, token, value in stream)
        assert any(token is Name and value == "sentinel" for _, token, value in stream)
