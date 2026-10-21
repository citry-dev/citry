from __future__ import annotations

import pytest

from citry import _vue_compile_lint as vue_compile_lint
from citry._markup_lint import MarkupLintConsumer
from citry._vue_compile_lint import lint_vue_compile
from citry_core.template_parser import ForeignSpan, ParseOptions, parse_template


def _compile_errors(
    source: str,
    consumers: tuple[MarkupLintConsumer, ...] = (),
) -> list[tuple[str, str, str]]:
    """Return (compiler code, spanned authored text, severity) for each finding."""
    encoded = source.encode("utf-8")
    findings = lint_vue_compile(source, parse_template(source), consumers)
    assert all(finding.code == "citry.vue.compile-error" for finding in findings)
    return [
        (
            finding.name,
            encoded[finding.start_index : finding.end_index].decode("utf-8"),
            finding.severity,
        )
        for finding in findings
    ]


# --- what the compiler rejects -------------------------------------------------


def test_reports_a_div_the_browser_moves_out_of_a_table():
    source = "<table>\n  <div>Row</div>\n</table>"

    assert _compile_errors(source) == [("ExtendPoint", "<div>", "error")]
    (finding,) = lint_vue_compile(source, parse_template(source), ())
    assert finding.message == (
        "Vue cannot compile this template: a <div> inside a table must sit in a <td> or <th>, so the browser"
        " moves it out of the table. Put rows in <tr> and cells in <td> or <th>."
    )


def test_reports_a_button_inside_a_button():
    source = "<button>a<button>b</button></button>"

    assert _compile_errors(source) == [
        ("ExtendPoint", "<button>", "error"),
        ("ExtendPoint", "</button>", "error"),
    ]
    assert [finding.message for finding in lint_vue_compile(source, parse_template(source), ())] == [
        "Vue cannot compile this template: this <button> holds another <button>, so the browser ends it where"
        " the inner one starts. Close this <button> before the next one.",
        "Vue cannot compile this template: the browser already closed this element, so this end tag closes nothing.",
    ]


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Element nesting is too deep.", "element nesting is too deep."),
        ("HTML tree construction repaired this end tag.", "HTML tree construction repaired this end tag."),
    ],
)
def test_keeps_the_compiler_wording_for_a_message_it_has_no_plain_form_for(message, expected):
    # The compiler's own sentence follows the colon, its first word in
    # lowercase unless that word is an acronym.
    source = "<div>x</div>"
    written = vue_compile_lint.static_vue_template(source, [])
    error = vue_compile_lint._CompilerError("ExtendPoint", message, 0, 5)

    assert vue_compile_lint._detail(written, error, (0, 5)) == expected


def test_reports_a_form_inside_a_form():
    findings = _compile_errors('<form action="/a"><form action="/b"></form></form>')

    assert findings == [
        ("ExtendPoint", '<form action="/b">', "error"),
        ("InvalidEndTag", "</form>", "error"),
    ]
    (_, end_tag) = lint_vue_compile(
        '<form action="/a"><form action="/b"></form></form>',
        parse_template('<form action="/a"><form action="/b"></form></form>'),
        (),
    )
    assert (
        "Close the outer <form> first"
        in lint_vue_compile(
            '<form action="/a"><form action="/b"></form></form>',
            parse_template('<form action="/a"><form action="/b"></form></form>'),
            (),
        )[0].message
    )
    assert end_tag.message.endswith("the browser already closed this element, so this end tag closes nothing.")


def test_reports_a_link_inside_a_link():
    source = '<a href="/a"><a href="/b">b</a></a>'

    assert _compile_errors(source) == [
        ("ExtendPoint", '<a href="/a">', "error"),
        ("ExtendPoint", "</a>", "error"),
    ]
    # The plain wording is chosen by the compiler's message, so this fails
    # when a compiler upgrade rewords it.
    assert "this <a> holds another <a>" in lint_vue_compile(source, parse_template(source), ())[0].message


@pytest.mark.parametrize(
    ("source", "directive"),
    [
        ("<div><p v-else>x</p></div>", "v-else"),
        ('<p v-if="a">x</p>text<b v-else-if="b">y</b>', "v-else-if"),
        ('<p>x</p><c-card v-else :title="t" />', "v-else"),
    ],
)
def test_reports_v_else_with_no_v_if_before_it(source, directive):
    assert _compile_errors(source) == [("VElseNoAdjacentIf", directive, "error")]
    (finding,) = lint_vue_compile(source, parse_template(source), ())
    assert f"'{directive}' has no element with 'v-if' or 'v-else-if' right before it" in finding.message


def test_reports_an_orphan_v_else_after_an_orphan_v_else_if():
    source = '<p>a</p><b v-else-if="x">1</b><i v-else>2</i>'

    assert [text for _code, text, _severity in _compile_errors(source)] == ["v-else-if", "v-else"]


def test_finds_every_orphan_when_all_of_them_are(monkeypatch):
    source = "".join(f"<div><b v-else>{index}</b></div>" for index in range(64))
    compiles = 0
    original = vue_compile_lint._compile

    def counting(*args):
        nonlocal compiles
        compiles += 1
        return original(*args)

    monkeypatch.setattr(vue_compile_lint, "_compile", counting)

    assert len(_compile_errors(source)) == 64
    assert compiles < 70


def test_reports_each_orphan_v_else_and_not_the_chain_that_has_its_v_if():
    source = '<p v-if="a">1</p><p v-else>2</p><div><i v-else>3</i><b v-else-if="c">4</b></div>'
    encoded = source.encode()
    findings = lint_vue_compile(source, parse_template(source), ())

    assert [encoded[item.start_index : item.end_index].decode() for item in findings] == ["v-else", "v-else-if"]
    assert [item.start_index for item in findings] == [source.index("v-else>3"), source.index("v-else-if")]


def test_reports_a_component_inside_a_vue_v_for_on_its_tag_name():
    source = '<ul><template v-for="item in items"><c-row :item="item" /></template></ul>'
    ordinary = lint_vue_compile(source, parse_template(source), (), renders_in_place=lambda _name: False)

    assert [(item.name, source[item.start_index : item.end_index]) for item in ordinary] == [
        ("CITRY_COMPONENT_IN_V_FOR", "c-row"),
    ]
    assert "Repeat it with '<c-for>'" in ordinary[0].message
    # A component that renders in place, as a `transparent` or `simple` one
    # does, may sit inside a Vue `v-for`; without the application the check
    # cannot tell which kind `c-row` is.
    assert lint_vue_compile(source, parse_template(source), (), renders_in_place=lambda _name: True) == ()
    assert _compile_errors(source) == []


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ('<c-element c-is="tag"><table><div>x</div></table></c-element>', "ExtendPoint"),
        ('<p v-if="a">1</p><c-element c-is="tag">x</c-element><p v-else>2</p>', "VElseNoAdjacentIf"),
    ],
)
def test_decides_a_built_in_component_by_its_name_whatever_the_application_says(source, code):
    # A loaded application counts `<c-element>` as transparent; it is still
    # written the way a render writes it.
    findings = lint_vue_compile(source, parse_template(source), (), renders_in_place=lambda _name: True)

    assert [finding.name for finding in findings] == [code]


def test_reports_a_listener_vue_reads_as_an_expression_that_the_expression_rule_accepts():
    # The expression rule accepts statements in a listener, but Vue compiles
    # a listener without `;` as an expression.
    assert _compile_errors('<button @click="if (ok) save()">Save</button>') == [
        ("InvalidExpression", "if (ok) save()", "error"),
    ]
    assert _compile_errors('<button @click="if (ok) save();">Save</button>') == []


def test_reports_a_mistake_inside_every_c_if_branch_a_render_writes_in_place():
    # A component call means a render does not compile this body as a leaf
    # program (a Vue template it reuses for every render), so it writes the
    # branch it picks straight into the table.
    source = (
        '<c-card /><table><c-if cond="wide"><div>wide</div></c-if>'
        "<c-else><tr><td>narrow</td></tr></c-else></table>"
        '<c-for each="row in rows"><button><button>x</button></button></c-for>'
    )

    assert [(code, text) for code, text, _severity in _compile_errors(source)] == [
        ("ExtendPoint", "<div>"),
        ("ExtendPoint", "<button>"),
        ("ExtendPoint", "</button>"),
    ]


def test_follows_the_leaf_program_that_wraps_each_branch_in_a_template():
    # Without a component call, a render compiles the body as a leaf program,
    # which puts each branch in a `<template>`. The compiler then checks a
    # branch on its own, not against the table around it.
    source = (
        '<table><c-if cond="wide"><div>{{ wide }}</div></c-if></table>'
        '<c-for each="row in rows"><button><button>x</button></button></c-for>'
    )

    assert [(code, text) for code, text, _severity in _compile_errors(source)] == [
        ("ExtendPoint", "<button>"),
        ("ExtendPoint", "</button>"),
    ]


@pytest.mark.parametrize(
    "source",
    [
        '<p v-if="a">1</p><c-if cond="ok"><p v-else>2</p></c-if>',
        '<c-if cond="ok"><p v-if="a">1</p></c-if><c-else><p v-else>2</p></c-else>',
    ],
)
def test_reports_a_v_else_that_a_leaf_programs_template_cuts_off_from_its_v_if(source):
    assert _compile_errors(source) == [("VElseNoAdjacentIf", "v-else", "error")]


def test_reports_a_mistake_inside_a_fill_and_a_slot_fallback():
    source = (
        '<c-card><c-fill name="body"><table><div>a</div></table></c-fill></c-card>'
        '<c-slot name="extra"><table><div>b</div></table></c-slot>'
    )
    encoded = source.encode()
    findings = lint_vue_compile(source, parse_template(source), ())

    assert [item.start_index for item in findings] == [source.index("<div>a"), source.index("<div>b")]
    assert {encoded[item.start_index : item.end_index] for item in findings} == {b"<div>"}


def test_maps_positions_past_multibyte_text_and_rewritten_attributes():
    # The writer joins attributes with single spaces and turns Python values
    # into placeholders, so the authored and compiled offsets differ.
    source = '<p   class="č"  c-title="t">{{ name }} ž</p>\n<table   id="x"><div>Row</div></table>'

    assert _compile_errors(source) == [("ExtendPoint", "<div>", "error")]
    (finding,) = lint_vue_compile(source, parse_template(source), ())
    assert finding.start_index == source.encode().index(b"<div>")


def test_reports_the_body_of_a_whole_document_template():
    source = "<!doctype html><html><head><title>x</title></head><body><table><div>Row</div></table></body></html>"

    assert _compile_errors(source) == [("ExtendPoint", "<div>", "error")]


def test_finds_an_orphan_v_else_among_many_with_few_compiles(monkeypatch):
    chains = "".join(f'<p v-if="a{index}">1</p><p v-else>2</p>' for index in range(200))
    source = f"{chains}<div><b v-else>x</b></div>{chains}"
    compiles = 0
    original = vue_compile_lint._compile

    def counting(*args):
        nonlocal compiles
        compiles += 1
        return original(*args)

    monkeypatch.setattr(vue_compile_lint, "_compile", counting)

    assert _compile_errors(source) == [("VElseNoAdjacentIf", "v-else", "error")]
    assert compiles < 40


def test_skips_a_template_whose_python_code_cannot_hold_its_text():
    assert _compile_errors("<div>a\x00b</div>") == []


# --- what another rule already reports ----------------------------------------


@pytest.mark.parametrize("source", ['<p :title="a +">x</p>', '<div v-for="x">y</div>', '<i v-for="(a,) in">z</i>'])
def test_leaves_a_broken_expression_to_the_expression_rule(source):
    assert _compile_errors(source) == []


def test_leaves_a_block_inside_a_paragraph_to_the_nesting_rule_even_when_it_is_off():
    source = "<p>Owner: <div>{{ owner }}</div></p><table><div>Row</div></table>"
    off = (MarkupLintConsumer(rule_invalid_nesting="ignore"),)

    # Only the table's mistake is left; the `</p>` the compiler rejects
    # belongs to the paragraph rule.
    assert _compile_errors(source) == [("ExtendPoint", "<div>", "error")]
    assert _compile_errors(source, off) == [("ExtendPoint", "<div>", "error")]


@pytest.mark.parametrize(
    "source",
    [
        '<p><a href="/x"><div>card</div></a></p>',
        "<p><span><div>a</div></span></p>",
        "<p>Hi <strong><ul><li>x</li></ul></strong></p>",
        "<p><p>a</p></p>",
    ],
)
def test_leaves_every_tag_a_block_inside_a_paragraph_breaks_to_the_nesting_rule(source):
    assert _compile_errors(source) == []


def test_still_reports_another_mistake_inside_the_same_paragraph():
    source = "<p><div>a</div><button>b<button>c</button></button></p>"

    assert [code for code, _text, _severity in _compile_errors(source)] == ["ExtendPoint", "ExtendPoint"]


# --- what compiles ------------------------------------------------------------


@pytest.mark.parametrize(
    "source",
    [
        '<table><thead><tr><th scope="col">A</th></tr></thead><tbody><tr><td>{{ a }}</td></tr></tbody></table>',
        '<p v-if="a">1</p><!-- note --><p v-else-if="b">2</p>\n  <p v-else>3</p>',
        '<c-if cond="a"><p v-if="b">1</p><p v-else>2</p></c-if><c-elif cond="c">x</c-elif><c-else>y</c-else>',
        '<c-for each="item in items"><li>{{ item }}</li></c-for><c-empty><li>none</li></c-empty>',
        '<div v-pre><p v-else>x</p><b :title="a +">y</b></div>',
        '<c-card v-if="open" :title="t" @close="open = false" v-model="value">'
        '<c-fill name="body">B</c-fill><c-fill name="footer" data="d">{{ d }}</c-fill></c-card>'
        "<p v-else>closed</p>",
        '<c-card><c-if cond="a"><c-fill name="body">1</c-fill></c-if><c-else><c-fill name="body">2</c-fill></c-else>'
        "</c-card>",
        '<c-slot name="title">Default <b>title</b></c-slot><c-slot name="other" />',
        # A component call's own tag is Citry's to write, so a row component
        # in a table is not reported.
        "<table><tbody><c-row /></tbody></table>",
        '<c-element c-is="tag"><div>x</div></c-element><c-element is="span">y</c-element>',
        "<div #c-ignore><table><div>kept as HTML</div></table></div><c-raw><table><div>r</div></table></c-raw>",
        '<input v-model="q" c-bind="attrs" #c-key="k"><br/><textarea v-model="t"></textarea>',
        '<button @click="count++; save()" @c-click="rate({ stars: 5 })">Rate</button>',
        '<form v-model="q"></form>',
        "<!doctype html><html><head><title>x</title></head><body><main>{{ a }}</main></body></html>",
        # `<c-provide>` renders its body in place, so the `v-else` follows the `v-if`.
        '<p v-if="a">1</p><c-provide key="k" data="1"><p v-else>2</p></c-provide>',
        '<ul><li v-for="i in items"><c-provide key="k" data="1">x</c-provide></li></ul>',
        "<c-js>if (a < b) { run(); }</c-js>",
        "<div><!-- note --><c-card><!-- only a comment --></c-card></div>",
    ],
)
def test_stays_silent_on_a_template_vue_compiles(source):
    assert _compile_errors(source) == []


def test_skips_a_template_with_source_an_extension_renders():
    # Citry does not compile such a template for Vue, so there is nothing to
    # check it against.
    source = "<table>{% rows %}</table><table><div>x</div></table>"
    start = source.index("{%")
    span = ForeignSpan(start, start + len("{% rows %}"), "rows", 0, may_control_body=False)
    template = parse_template(source, options=ParseOptions([span]))

    assert lint_vue_compile(source, template, ()) == ()


# --- severities ---------------------------------------------------------------


def test_follows_the_consumers_severity():
    source = "<table><div>Row</div></table>"

    assert _compile_errors(source, (MarkupLintConsumer(rule_vue_compile_error="warning"),)) == [
        ("ExtendPoint", "<div>", "warning"),
    ]
    assert _compile_errors(source, (MarkupLintConsumer(rule_vue_compile_error="ignore"),)) == []
    assert _compile_errors(
        source,
        (
            MarkupLintConsumer(rule_vue_compile_error="ignore"),
            MarkupLintConsumer(rule_vue_compile_error="warning"),
        ),
    ) == [("ExtendPoint", "<div>", "warning")]
