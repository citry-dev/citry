from __future__ import annotations

import pytest

from citry.analysis import (
    MarkupLintConsumer,
    browser_expressions,
    lint_invalid_vue_expressions,
    lint_markup,
)
from citry_core.template_parser import parse_template


def _markup(
    source: str,
    consumers: tuple[MarkupLintConsumer, ...] = (),
) -> list[tuple[str, str, str]]:
    """Return (rule code without its family, spanned text, severity) for each finding."""
    encoded = source.encode("utf-8")
    return [
        (
            finding.code.rsplit(".", 1)[1],
            encoded[finding.start_index : finding.end_index].decode("utf-8"),
            finding.severity,
        )
        for finding in lint_markup(parse_template(source), consumers)
    ]


def _codes(source: str, consumers: tuple[MarkupLintConsumer, ...] = ()) -> list[str]:
    return [code for code, _span, _severity in _markup(source, consumers)]


# --- citry.template.misspelled-attribute --------------------------------------


def test_misspelled_attribute_reports_the_benchmark_template():
    source = '<div class="board" id="board" titel="Board">'
    assert _markup(source + "</div>") == [("misspelled-attribute", "titel", "error")]
    (finding,) = lint_markup(parse_template(source + "</div>"), ())
    assert finding.message == "'titel' is not an attribute of <div>, so the browser ignores it. Did you mean 'title'?"


@pytest.mark.parametrize(
    ("source", "span", "suggestion"),
    [
        ('<div clas="a"></div>', "clas", "'class'"),
        ('<a herf="/"></a>', "herf", "'href'"),
        ('<div :titel="t"></div>', ":titel", "':title'"),
        ('<div v-bind:titel="t"></div>', "v-bind:titel", "'v-bind:title'"),
        ('<div c-titel="t"></div>', "c-titel", "'c-title'"),
        # Letter case does not matter, as in HTML.
        ('<img SCR="a.png" alt="">', "SCR", "'src'"),
    ],
)
def test_misspelled_attribute_reports_each_binding_form(source, span, suggestion):
    (finding,) = lint_markup(parse_template(source), ())
    assert source.encode()[finding.start_index : finding.end_index].decode() == span
    assert f"Did you mean {suggestion}?" in finding.message


@pytest.mark.parametrize(
    "source",
    [
        # Open families, Vue's own names, and names far from any attribute.
        '<meta property="og:title" content="x">',
        '<div hx-get="/x" data-x="1" aria-x="2" ref="r" key="k" is="x"></div>',
        '<input capture="user" type="file">',
        # Modifier bindings set DOM properties, and spreads are not names.
        '<div :inner-html.prop="h" .indeterminate="x" c-bind="attrs"></div><div v-bind="attrs"></div>',
        # Custom elements, components, and SVG accept other names.
        '<my-el titel="x"></my-el><c-Card titel="x" /><Card titel="x" /><svg><path strok="1"></path></svg>',
        # A c-* name that looks like a directive belongs to the directive rule.
        '<label c-fro="x"></label>',
        # Two-letter names are too short to read as a typo.
        '<div i="1" dr="2"></div>',
    ],
)
def test_misspelled_attribute_stays_silent(source):
    assert "misspelled-attribute" not in _codes(source)


# --- citry.template.misspelled-element ----------------------------------------


def test_misspelled_element_reports_the_benchmark_template():
    source = '<dvi class="board" id="board" title="Board"></dvi>'
    assert _markup(source) == [("misspelled-element", "dvi", "error")]
    (finding,) = lint_markup(parse_template(source), ())
    assert finding.message == "<dvi> is not an HTML element. Did you mean <div>?"


@pytest.mark.parametrize(("tag", "suggestion"), [("sapn", "span"), ("buton", "button"), ("tabel", "table")])
def test_misspelled_element_suggests_the_html_element(tag, suggestion):
    (finding,) = lint_markup(parse_template(f"<{tag}></{tag}>"), ())
    assert finding.message == f"<{tag}> is not an HTML element. Did you mean <{suggestion}>?"


@pytest.mark.parametrize(
    "source",
    [
        # Obsolete, SVG, MathML, and Vue built-in names are real elements.
        "<frame></frame><marquee></marquee>",
        "<g></g><path></path><foreignObject></foreignObject><mi></mi>",
        "<component :is='x'></component><slot></slot><template v-if='x'></template>",
        # Components, custom elements, and unknown names far from any element.
        "<Card></Card><my-el></my-el><c-card /><widget></widget>",
    ],
)
def test_misspelled_element_stays_silent(source):
    assert "misspelled-element" not in _codes(source)


# --- citry.template.unknown-aria-attribute ------------------------------------


def test_unknown_aria_attribute_reports_the_benchmark_template_with_a_suggestion():
    source = '<button :aria-expandd="open">Menu</button>'
    assert _markup(source) == [("unknown-aria-attribute", ":aria-expandd", "error")]
    (finding,) = lint_markup(parse_template(source), ())
    assert finding.message.endswith("Did you mean 'aria-expanded'?")


def test_unknown_aria_attribute_reports_every_unknown_name_on_every_element():
    source = '<div aria-foo="1"></div><my-el c-aria-labell="x"></my-el><svg aria-hiden="true"></svg>'
    assert _markup(source) == [
        ("unknown-aria-attribute", "aria-foo", "error"),
        ("unknown-aria-attribute", "c-aria-labell", "error"),
        ("unknown-aria-attribute", "aria-hiden", "error"),
    ]
    first = lint_markup(parse_template(source), ())[0]
    assert first.message == "'aria-foo' is not an ARIA attribute, so browsers and screen readers ignore it."


def test_unknown_aria_attribute_accepts_aria_1_2_and_1_3_names_and_component_inputs():
    source = (
        '<div aria-description="d" aria-braillelabel="b" ARIA-LABEL="x" :aria-busy="b"></div>'
        '<c-Card aria-foo="1" /><Card aria-foo="1" />'
    )
    assert _markup(source) == []


# --- citry.template.invalid-nesting -------------------------------------------


def test_invalid_nesting_reports_the_benchmark_template():
    source = "<p>Owner: <div>{{ owner.name }}</div></p>"
    assert _markup(source) == [("invalid-nesting", "div", "error")]
    (finding,) = lint_markup(parse_template(source), ())
    assert finding.message == (
        "<div> cannot be inside <p>. The browser closes the <p> before it, so the page structure differs from the "
        "template."
    )


@pytest.mark.parametrize(
    "source",
    [
        "<p><span><ul><li>a</li></ul></span></p>",
        '<p><c-if cond="x"><div>a</div></c-if></p>',
        '<p><b c-if="x"><h2>a</h2></b></p>',
        "<p><c-slot name='x'><table></table></c-slot></p>",
        "<p><my-el><section></section></my-el></p>",
        "<p><p>a</p></p>",
    ],
)
def test_invalid_nesting_descends_through_inline_elements_and_citry_blocks(source):
    assert _codes(source) == ["invalid-nesting"]


@pytest.mark.parametrize(
    "source",
    [
        # The browser keeps these inside the button, table cell, or template.
        "<p><button><div>a</div></button></p>",
        "<p><template><div>a</div></template></p>",
        # What a component renders is not visible here.
        "<p><c-Card><div>a</div></c-Card></p><p><Card><div>a</div></Card></p>",
        "<p><c-element c-is=\"'span'\"><div>a</div></c-element></p>",
        # Inline content and SVG are fine.
        "<p><span><a href='#'><em>x</em></a></span><svg><g></g></svg></p>",
        # A sibling after the paragraph is not inside it.
        "<p>a</p><div>b</div>",
    ],
)
def test_invalid_nesting_stays_silent(source):
    assert "invalid-nesting" not in _codes(source)


# --- citry.template.duplicate-id ----------------------------------------------


def test_duplicate_id_reports_the_benchmark_template():
    source = '<div class="board" id="board"><h1 id="board">Board</h1></div>'
    assert _markup(source) == [("duplicate-id", "board", "error")]
    (finding,) = lint_markup(parse_template(source), ())
    assert (
        finding.message == "Another element in this template already has id 'board'. An id must be unique in the page."
    )


@pytest.mark.parametrize(
    "source",
    [
        # Conditions and loops, as attributes and as blocks.
        '<div id="a"></div><div c-if="x" id="a"></div>',
        '<c-if cond="x"><div id="a"></div></c-if><c-else><div id="a"></div></c-else>',
        '<div v-if="x" id="a"></div><div v-else id="a"></div>',
        '<c-for each="x in y"><div id="a"></div></c-for>',
        '<li v-for="x in y" id="a"></li><li id="a"></li>',
        # Fills, slot fallbacks, component bodies, and templates.
        '<c-Card><c-fill name="a"><i id="a"></i></c-fill></c-Card><i id="a"></i>',
        '<c-slot name="s"><i id="a"></i></c-slot><i id="a"></i>',
        '<c-Card><i id="a"></i></c-Card><i id="a"></i>',
        '<template><i id="a"></i></template><i id="a"></i>',
        # Bound ids and distinct ids.
        '<i :id="a"></i><i :id="a"></i><i c-id="b"></i><i c-id="b"></i><i id="x"></i><i id="y"></i>',
    ],
)
def test_duplicate_id_stays_silent_when_either_element_may_not_render(source):
    assert "duplicate-id" not in _codes(source)


def test_duplicate_id_counts_v_show_and_svg_elements():
    # A hidden element is still in the page, and SVG ids share the page.
    source = '<div id="a" v-show="x"></div><svg><g id="a"></g></svg>'
    assert _codes(source) == ["duplicate-id"]


# --- citry.template.missing-image-alt -----------------------------------------


def test_missing_image_alt_reports_the_benchmark_template_as_a_warning():
    source = '<div class="board"><img src="/static/avatar.svg" width="32" height="32" /></div>'
    assert _markup(source) == [("missing-image-alt", "img", "warning")]
    (finding,) = lint_markup(parse_template(source), ())
    assert finding.message == (
        '<img> has no alt text. Describe the image in alt, or write alt="" for an image that only decorates the page.'
    )


@pytest.mark.parametrize(
    "source",
    [
        '<i><img src="a" alt=""></i>',
        '<i><img src="a" c-alt="owner.name"></i>',
        '<i><img src="a" :alt="name"></i>',
        '<i><img src="a" v-bind:alt="name"></i>',
        '<i><img src="a" aria-label="Logo"></i>',
        '<i><img src="a" aria-labelledby="l"></i>',
        '<i><img src="a" role="presentation"></i>',
        '<i><img src="a" role="none"></i>',
        '<i><img src="a" :role="r"></i>',
        # A spread may add alt.
        '<i><img src="a" c-bind="attrs"></i>',
        '<i><img src="a" v-bind="attrs"></i>',
        # SVG has its own image element.
        '<svg><image href="a"></image></svg>',
    ],
)
def test_missing_image_alt_stays_silent(source):
    assert _markup(source) == []


def test_missing_image_alt_skips_a_single_root_that_may_receive_a_parents_attributes():
    source = '<img :src="src" width="32">'
    # Vue passes a parent's `alt` to the root of a component with browser
    # code; the default consumer cannot tell, so it stays silent.
    assert _markup(source) == []
    assert _markup(source, (MarkupLintConsumer(root_may_receive_attributes=False),)) == [
        ("missing-image-alt", "img", "warning"),
    ]
    # A shared template stays silent when any owner may forward attributes.
    assert (
        _markup(
            source,
            (MarkupLintConsumer(root_may_receive_attributes=False), MarkupLintConsumer()),
        )
        == []
    )
    # An image that is not the only root is reported either way.
    assert _codes("<img src='a'><p>caption</p>") == ["missing-image-alt"]


# --- citry.browser.invalid-model-target ---------------------------------------


def test_invalid_model_target_reports_the_benchmark_template():
    source = '<form role="search" v-model="query" @c-submit.prevent="search"><input type="search" name="q"/></form>'
    assert _markup(source) == [("invalid-model-target", "v-model", "error")]
    (finding,) = lint_markup(parse_template(source), ())
    assert finding.message == (
        "v-model does not work on <form>, which holds no value. Put it on an <input>, <textarea>, or <select>, "
        "or on a component."
    )


def test_invalid_model_target_reports_other_elements_and_custom_elements():
    source = '<div v-model.lazy="a"></div><my-picker v-model="b"></my-picker>'
    assert _markup(source) == [
        ("invalid-model-target", "v-model.lazy", "error"),
        ("invalid-model-target", "v-model", "error"),
    ]


def test_invalid_model_target_accepts_value_elements_and_components():
    source = (
        '<input v-model="a"><input type="file" v-model="f"><textarea v-model="b"></textarea>'
        '<select v-model="c"></select><c-Field v-model="d" /><Field v-model="e" />'
        '<c-element c-is="\'input\'" v-model="g"></c-element>'
    )
    assert _markup(source) == []


# --- citry.vue.misspelled-event -----------------------------------------------


def test_misspelled_event_reports_the_benchmark_template_as_a_warning():
    source = '<button type="button" @clik="toggle()">Show</button>'
    assert _markup(source) == [("misspelled-event", "@clik", "warning")]
    (finding,) = lint_markup(parse_template(source), ())
    assert finding.message == "'clik' is not a DOM event, so this listener never runs. Did you mean 'click'?"


def test_misspelled_event_reads_v_on_and_modifiers():
    source = '<form v-on:sumbit.prevent="go"></form><div @dbclick="x"></div>'
    assert _markup(source) == [
        ("misspelled-event", "v-on:sumbit.prevent", "warning"),
        ("misspelled-event", "@dbclick", "warning"),
    ]


@pytest.mark.parametrize(
    "source",
    [
        # Real DOM events, including ones only Vue's types list.
        '<div @click="a" @dblclick="b" @scrollend="c" @focusin="d" @compositionstart="e"></div>',
        # Custom event names: hyphen, colon, capital, or a lookalike word.
        '<div @scrolled="a" @touched="b" @my-event="c" @update:x="d" @Clik="e"></div>',
        # Citry server events, dynamic names, and Vue's lifecycle hooks.
        '<button @c-clik="save()" @[name]="x" @vue:mounted="y"></button>',
        # Component tags and custom elements fire their own events.
        '<c-Card @clik="a" /><Card @clik="b" /><my-el @clik="c"></my-el>',
    ],
)
def test_misspelled_event_stays_silent(source):
    assert "misspelled-event" not in _codes(source)


# --- severities, nested templates, and consumers ------------------------------


def test_markup_rules_follow_each_consumers_severity():
    source = '<div titel="x"><img src="a"></div>'
    ignore = MarkupLintConsumer(rule_misspelled_attribute="ignore", rule_missing_image_alt="ignore")
    assert _markup(source, (ignore,)) == []
    raised = MarkupLintConsumer(rule_missing_image_alt="error")
    # One owner that still reports is enough, and "error" wins.
    assert _markup(source, (ignore, raised)) == [
        ("misspelled-attribute", "titel", "error"),
        ("missing-image-alt", "img", "error"),
    ]


@pytest.mark.parametrize("rule_name", ["rule_invalid_nesting", "rule_duplicate_id", "rule_misspelled_element"])
def test_markup_rules_that_every_consumer_ignores_report_nothing(rule_name):
    source = '<p><div id="a"></div><i id="a"></i><dvi></dvi></p>'
    ignore = MarkupLintConsumer(**{rule_name: "ignore"})
    reported = {code for code, _span, _severity in _markup(source, (ignore,))}
    assert rule_name.removeprefix("rule_").replace("_", "-") not in reported
    assert len(reported) == 2


def test_markup_consumer_rejects_an_unknown_severity_or_flag():
    with pytest.raises(ValueError, match="rule_duplicate_id"):
        MarkupLintConsumer(rule_duplicate_id="fatal")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="root_may_receive_attributes"):
        MarkupLintConsumer(root_may_receive_attributes="yes")  # type: ignore[arg-type]


def test_markup_rules_map_nested_template_offsets_into_the_outer_source():
    source = "<c-card c-header=\"<><dvi></dvi><b titel='x'></b></>\" /><p>ok</p>"
    assert _markup(source) == [
        ("misspelled-element", "dvi", "error"),
        ("misspelled-attribute", "titel", "error"),
    ]


def test_markup_rules_do_not_read_ids_or_paragraphs_across_a_nested_template():
    # A nested template renders apart from the element around it, and may
    # render more than once.
    source = "<p><c-card c-header=\"<><div id='a'></div></>\" /></p><i id='a'></i>"
    assert _markup(source) == []


# --- citry.vue.invalid-expression ---------------------------------------------


def _invalid(source: str, consumers: tuple[MarkupLintConsumer, ...] = ()) -> list[tuple[str, str]]:
    template = parse_template(source)
    encoded = source.encode("utf-8")
    return [
        (encoded[finding.start_index : finding.end_index].decode("utf-8"), finding.severity)
        for finding in lint_invalid_vue_expressions(template, browser_expressions(template), consumers)
    ]


def test_invalid_vue_expression_reports_the_benchmark_template():
    source = '<p v-if="open &&">Details are visible</p>'
    assert _invalid(source) == [("open &&", "error")]
    template = parse_template(source)
    (finding,) = lint_invalid_vue_expressions(template, browser_expressions(template), ())
    assert finding.code == "citry.vue.invalid-expression"
    assert finding.message == (
        "The Vue expression in 'v-if' is not valid JavaScript, so Vue cannot compile this template."
    )


def test_invalid_vue_expression_checks_bindings_listeners_loops_and_server_call_arguments():
    source = (
        '<div :title="a +"></div><button @click="go(">x</button>'
        '<li v-for="x in [1,">y</li><button @c-click="save({a: })">s</button>'
    )
    # A loop finding marks the whole `v-for` value.
    assert [span for span, _severity in _invalid(source)] == ["a +", "go(", "x in [1,", "{a: }"]


@pytest.mark.parametrize(
    "source",
    [
        # Same-name shorthand: `:title` reads `title`.
        "<div :title v-bind:alt></div>",
        # Vue never compiles anything under v-pre.
        '<div v-pre><span :title="a &&">{{ x }}</span></div>',
        '<pre v-pre :title="a &&"></pre>',
        # Character references are decoded first, as Vue does.
        '<i v-if="a &gt; b &amp;&amp; c"></i>',
        # A listener may hold statements, a function, or an arrow function.
        '<b @click="a = 1; go()"></b><b @click="function (e) { go(e) }"></b><b @click="(e) => go(e)"></b>',
        # Custom directives are not Vue expressions Citry reads.
        '<i v-tooltip="not js ("></i>',
    ],
)
def test_invalid_vue_expression_stays_silent(source):
    assert _invalid(source) == []


def test_invalid_vue_expression_follows_the_consumers_severity():
    source = '<p v-if="open &&"></p>'
    assert _invalid(source, (MarkupLintConsumer(rule_invalid_vue_expression="ignore"),)) == []
    assert _invalid(source, (MarkupLintConsumer(rule_invalid_vue_expression="warning"),)) == [("open &&", "warning")]


def test_invalid_vue_expression_skips_v_pre_inside_a_nested_template():
    source = '<c-card c-header="<><i v-pre :x=\'a &&\'></i></>" /><p :y="b &&"></p>'
    assert _invalid(source) == [("b &&", "error")]
