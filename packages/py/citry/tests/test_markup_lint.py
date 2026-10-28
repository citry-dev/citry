from __future__ import annotations

import re
import warnings

import pytest

from citry import Citry, Component
from citry.analysis import (
    MarkupLintConsumer,
    browser_expressions,
    lint_invalid_vue_expressions,
    lint_markup,
)
from citry_core.template_parser import ForeignSpan, ParseOptions, parse_template


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
        # A binding on Vue's <slot> is a slot prop with any name.
        '<slot :tile="t" v-bind:clas="c"></slot>',
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
        # Obsolete block elements close the paragraph too.
        "<p><center>a</center></p>",
    ],
)
def test_invalid_nesting_descends_through_inline_elements_and_citry_blocks(source):
    assert _codes(source) == ["invalid-nesting"]


@pytest.mark.parametrize(
    "source",
    [
        # The browser keeps these inside the button, table cell, or template,
        # and reads <noscript> content as text when scripts run.
        "<p><button><div>a</div></button></p>",
        "<p><noscript><div>a</div></noscript></p>",
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
        '<li c-for="x in y" id="a"></li><p c-empty id="a"></p><i id="a"></i>',
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
    # A root inside a top-level condition chain is still the only root Vue sees.
    chain = '<c-if cond="a"><img :src="s"></c-if><c-else><img :src="t"></c-else>'
    assert _markup(chain) == []
    assert _codes(chain, (MarkupLintConsumer(root_may_receive_attributes=False),)) == [
        "missing-image-alt",
        "missing-image-alt",
    ]
    assert _codes('<c-if cond="a"><div><img :src="s"></div></c-if>') == ["missing-image-alt"]
    # Two separate conditions can both render, so neither image is the root.
    assert _codes('<c-if cond="a"><img :src="s"></c-if><c-if cond="b"><img :src="t"></c-if>') == [
        "missing-image-alt",
        "missing-image-alt",
    ]


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


def test_vue_only_rules_skip_v_pre_content_and_html_rules_do_not():
    # Vue leaves v-pre content as written, so its v-model and listeners are
    # plain attributes; the browser still parses the HTML.
    source = '<div v-pre v-model="a" @clik="b"><span v-model="x" @clik="y"><dvi></dvi></span></div>'
    assert _codes(source) == ["misspelled-element"]


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


# --- citry.template.csp-incompatible ------------------------------------------

_CSP_NATIVE_EVENT = (
    "A strict Content Security Policy blocks the inline event attribute '{name}'. "
    "Use a Vue listener such as @click instead, or rename a custom attribute, for example to data-{name}."
)
_CSP_JAVASCRIPT_URL = (
    "A strict Content Security Policy blocks the javascript: URL in '{name}'. "
    "Use a real URL, and a Vue listener for the action."
)
_CSP_RAW_TAG = (
    "A strict Content Security Policy blocks this inline <{tag}>. "
    "Move it into the component's js or css, or into a Script or Style dependency."
)


def _csp(source: str, *modes: str) -> list[tuple[int, int, str, str]]:
    """Return (start, end, severity, message) of each strict-CSP finding, for consumers set to ``modes``."""
    consumers = tuple(MarkupLintConsumer(csp=mode) for mode in modes)  # type: ignore[arg-type]
    return [
        (finding.start_index, finding.end_index, finding.severity, finding.message)
        for finding in lint_markup(parse_template(source), consumers)
        if finding.code == "citry.template.csp-incompatible"
    ]


def test_csp_rule_follows_the_consumers_mode():
    source = '<div onclick="go()"></div>'
    message = _CSP_NATIVE_EVENT.format(name="onclick")
    # The engine's default is off, so a consumer that says nothing reports nothing.
    assert lint_markup(parse_template(source), (MarkupLintConsumer(),)) == ()
    assert _csp(source, "off") == []
    assert _csp(source, "warn") == [(5, 12, "warning", message)]
    assert _csp(source, "strict") == [(5, 12, "error", message)]
    # With no consumer at all, no rule is active.
    assert lint_markup(parse_template(source), ()) == ()


def test_csp_rule_takes_the_strictest_consumer_and_ignores_an_off_consumer():
    source = '<div onclick="go()"></div>'
    message = _CSP_NATIVE_EVENT.format(name="onclick")
    # Components of two engines can share one template; the stricter one decides.
    assert _csp(source, "warn", "strict") == [(5, 12, "error", message)]
    assert _csp(source, "strict", "warn") == [(5, 12, "error", message)]
    assert _csp(source, "warn", "off") == [(5, 12, "warning", message)]
    assert _csp(source, "off", "strict") == [(5, 12, "error", message)]
    assert _csp(source, "off", "off") == []


def test_csp_rule_does_not_change_the_other_markup_rules():
    source = '<div titel="x" onclick="go()"></div>'
    codes = {finding.code for finding in lint_markup(parse_template(source), (MarkupLintConsumer(csp="strict"),))}
    assert codes == {"citry.template.misspelled-attribute", "citry.template.csp-incompatible"}
    # An engine that ignores the other rules still gets the CSP rule.
    quiet = MarkupLintConsumer(rule_misspelled_attribute="ignore", csp="warn")
    assert [finding.code for finding in lint_markup(parse_template(source), (quiet,))] == [
        "citry.template.csp-incompatible"
    ]


@pytest.mark.parametrize("mode", ["", "Strict", "on", "error", None, True])
def test_csp_consumer_rejects_an_unknown_mode(mode):
    with pytest.raises(ValueError, match="Unknown csp mode"):
        MarkupLintConsumer(csp=mode)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        # An event handler is reported on the attribute name, as written.
        ('<button onclick="go()">x</button>', [(8, 15, _CSP_NATIVE_EVENT.format(name="onclick"))]),
        ('<button ONCLICK="go()">x</button>', [(8, 15, _CSP_NATIVE_EVENT.format(name="ONCLICK"))]),
        # Any name that starts with "on" is read as a possible handler, as at render time.
        ('<div online="1"></div>', [(5, 11, _CSP_NATIVE_EVENT.format(name="online"))]),
        ('<div onboarding-step="1"></div>', [(5, 20, _CSP_NATIVE_EVENT.format(name="onboarding-step"))]),
        # A name of one or two letters is too short to be a handler.
        ('<div on="1" ono="2"></div>', [(12, 15, _CSP_NATIVE_EVENT.format(name="ono"))]),
        # A name decides, so a handler without a value is still reported.
        ("<button onclick>x</button>", [(8, 15, _CSP_NATIVE_EVENT.format(name="onclick"))]),
        # A javascript: URL is reported on the value, as written.
        ('<a href="javascript:alert(1)">x</a>', [(9, 28, _CSP_JAVASCRIPT_URL.format(name="href"))]),
        ('<a href="JavaScript:x">x</a>', [(9, 21, _CSP_JAVASCRIPT_URL.format(name="href"))]),
        ("<a href=javascript:x>x</a>", [(8, 20, _CSP_JAVASCRIPT_URL.format(name="href"))]),
        # The value is decoded before it is read, as the browser does.
        ('<a href="java&#115;cript:alert(1)">x</a>', [(9, 33, _CSP_JAVASCRIPT_URL.format(name="href"))]),
        ('<a href="java&#x73;cript:x">x</a>', [(9, 26, _CSP_JAVASCRIPT_URL.format(name="href"))]),
        ('<a href="javascript&colon;x">x</a>', [(9, 27, _CSP_JAVASCRIPT_URL.format(name="href"))]),
        ('<a href="java&Tab;script:x">x</a>', [(9, 26, _CSP_JAVASCRIPT_URL.format(name="href"))]),
        # A tab, or leading spaces, do not stop the browser reading the scheme.
        ('<a href="java\tscript:alert(1)">x</a>', [(9, 29, _CSP_JAVASCRIPT_URL.format(name="href"))]),
        ('<a href="  JavaScript:x">x</a>', [(9, 23, _CSP_JAVASCRIPT_URL.format(name="href"))]),
        # Only some attributes hold a URL; "data" is one only on <object>.
        ('<object data="javascript:x"></object>', [(14, 26, _CSP_JAVASCRIPT_URL.format(name="data"))]),
        ('<div data="javascript:x"></div>', []),
        ('<img src="javascript:x" alt="">', [(10, 22, _CSP_JAVASCRIPT_URL.format(name="src"))]),
        ('<form action="javascript:x"></form>', [(14, 26, _CSP_JAVASCRIPT_URL.format(name="action"))]),
        ('<button formaction="javascript:x">x</button>', [(20, 32, _CSP_JAVASCRIPT_URL.format(name="formaction"))]),
        ('<svg><a xlink:href="javascript:x"></a></svg>', [(20, 32, _CSP_JAVASCRIPT_URL.format(name="xlink:href"))]),
        ('<a title="javascript:x">x</a>', []),
        ('<a href="https://example.com/javascript:x">x</a>', []),
        # Both problems on one element are two findings, in source order.
        (
            '<a href="javascript:x"\n   onclick="y">x</a>',
            [
                (9, 21, _CSP_JAVASCRIPT_URL.format(name="href")),
                (26, 33, _CSP_NATIVE_EVENT.format(name="onclick")),
            ],
        ),
        # A raw script or style is reported on the tag name, in any element.
        ("<script>var a = 1</script>", [(1, 7, _CSP_RAW_TAG.format(tag="script"))]),
        ("<style>a { color: red }</style>", [(1, 6, _CSP_RAW_TAG.format(tag="style"))]),
        ("<svg><script>x</script></svg>", [(6, 12, _CSP_RAW_TAG.format(tag="script"))]),
        # A known HTML element is checked in any letter case, as the browser reads it.
        ('<BUTTON onclick="x">y</BUTTON>', [(8, 15, _CSP_NATIVE_EVENT.format(name="onclick"))]),
        ('<A HREF="javascript:x">y</A>', [(9, 21, _CSP_JAVASCRIPT_URL.format(name="HREF"))]),
        ("<Script>a</Script>", [(1, 7, _CSP_RAW_TAG.format(tag="Script"))]),
        ("<SCRIPT>a</SCRIPT>", [(1, 7, _CSP_RAW_TAG.format(tag="SCRIPT"))]),
        ("<STYLE>a { color: red }</STYLE>", [(1, 6, _CSP_RAW_TAG.format(tag="STYLE"))]),
        # An element that Citry renders as a plain element has plain attributes.
        ('<c-element is="div" onclick="x"></c-element>', [(20, 27, _CSP_NATIVE_EVENT.format(name="onclick"))]),
        # A fixed `is` names the element the page gets, so the rules for that element apply.
        (
            '<c-element is="object" data="javascript:x"></c-element>',
            [(29, 41, _CSP_JAVASCRIPT_URL.format(name="data"))],
        ),
        ('<c-element is="div" data="javascript:x"></c-element>', []),
        ('<c-element is="a" href="javascript:x"></c-element>', [(24, 36, _CSP_JAVASCRIPT_URL.format(name="href"))]),
        ('<c-element is="script">a</c-element>', [(1, 10, _CSP_RAW_TAG.format(tag="script"))]),
        ('<c-element is="STYLE"></c-element>', [(1, 10, _CSP_RAW_TAG.format(tag="STYLE"))]),
        # A name with a dot that is not a binding is still the attribute the browser gets.
        ('<div onclick.prevent="x"></div>', [(5, 20, _CSP_NATIVE_EVENT.format(name="onclick.prevent"))]),
        ("<div ONCLICK.once></div>", [(5, 17, _CSP_NATIVE_EVENT.format(name="ONCLICK.once"))]),
        ('<a href.x="javascript:x"></a>', []),
        # The start tag of a text-content element is still HTML.
        ('<plaintext onclick="x">y</plaintext>', [(11, 18, _CSP_NATIVE_EVENT.format(name="onclick"))]),
        # Vue sets the attributes a v-pre region leaves as written, so they are checked.
        ('<div v-pre onclick="x"></div>', [(11, 18, _CSP_NATIVE_EVENT.format(name="onclick"))]),
        ('<div v-pre><span onclick="x"></span></div>', [(17, 24, _CSP_NATIVE_EVENT.format(name="onclick"))]),
        (
            '<div v-pre onclick="x"><script>a</script><a href="javascript:y"></a></div>',
            [
                (11, 18, _CSP_NATIVE_EVENT.format(name="onclick")),
                (24, 30, _CSP_RAW_TAG.format(tag="script")),
                (50, 62, _CSP_JAVASCRIPT_URL.format(name="href")),
            ],
        ),
    ],
)
def test_csp_rule_reports_each_case_with_its_range(source, expected):
    assert [(start, end, message) for start, end, _severity, message in _csp(source, "strict")] == expected


def test_csp_rule_reads_c_raw_content_with_utf8_byte_offsets():
    source = '<c-raw>é <a onclick="x" href="javascript:y">z</a><script>q</script></c-raw>'
    findings = _csp(source, "strict")
    assert findings == [
        (13, 20, "error", _CSP_NATIVE_EVENT.format(name="onclick")),
        (31, 43, "error", _CSP_JAVASCRIPT_URL.format(name="href")),
        (51, 57, "error", _CSP_RAW_TAG.format(tag="script")),
    ]
    # The offsets are bytes into the template, so "é" counts as two.
    encoded = source.encode()
    assert [encoded[start:end] for start, end, _severity, _message in findings] == [
        b"onclick",
        b"javascript:y",
        b"script",
    ]
    assert [(start, end) for start, end, _severity, _message in _csp(source.replace("é", "e"), "strict")] == [
        (12, 19),
        (30, 42),
        (50, 56),
    ]


def test_csp_rule_reads_c_raw_content_beside_other_markup_with_the_modes_severity():
    source = '<p onclick="a"><c-raw><b ONCLICK="y"></b></c-raw></p>'
    assert _csp(source, "warn") == [
        (3, 10, "warning", _CSP_NATIVE_EVENT.format(name="onclick")),
        # <c-raw> content goes through the page check, which reports names in
        # lowercase, but the message shows the name as the content writes it.
        (25, 32, "warning", _CSP_NATIVE_EVENT.format(name="ONCLICK")),
    ]
    assert _csp(source, "off") == []
    assert _csp("<c-raw></c-raw>", "strict") == []


@pytest.mark.parametrize(
    "source",
    [
        # A binding, a Citry or Vue directive, a listener, and a spread are values from data.
        """<a :href="'javascript:x'">x</a>""",
        """<a c-href="'javascript:x'">x</a>""",
        """<a v-bind:href="'javascript:x'">x</a>""",
        """<a v-bind="{ href: 'javascript:x' }">x</a>""",
        '<button @click="go()">x</button>',
        '<button v-on:click="go()">x</button>',
        '<button @click.once="go()" :onclick="x" v-onclick="z">x</button>',
        '<button c-onclick="y">x</button>',
        '<div c-bind="attrs"></div>',
        '<div v-bind="attrs"></div>',
        '<div #default="props"></div>',
        # A component's attributes are inputs, not HTML.
        '<c-Card onclick="x" href="javascript:y" />',
        '<c-card onclick="x" />',
        # A capitalized name that is no HTML element may be a Vue component.
        '<Card onclick="x" href="javascript:y">z</Card>',
        # A name with one of these prefixes is a binding or directive, not an attribute.
        '<div $onclick="x" #onclick="y" [onclick]="z" .onclick="w"></div>',
        '<div @onclick.prevent="x" :onclick.prop="y" v-onclick.z="w" c-onclick.x="q"></div>',
        # The page check reads these elements' content as text, not as tags.
        '<noscript><div onclick="x"></div><script>a</script></noscript>',
        '<xmp><div onclick="x"></div></xmp>',
        '<iframe><div onclick="x"></div></iframe>',
        '<noembed><div onclick="x"></div></noembed>',
        '<noframes><div onclick="x"></div></noframes>',
        '<plaintext><div onclick="x"></div><script>a</script></plaintext>',
        # The HTML of a nested template lands where the code that renders it decides.
        "<c-card c-header=\"<><b onclick='x'></b><script>a</script></>\" />",
        # A bound `is` gives no fixed element, so the c-element name stands.
        """<c-element c-is="'script'"></c-element>""",
        # An empty or missing URL, and a data attribute on a non-object.
        "<a href>x</a>",
        '<a href="">x</a>',
        '<div data-x="javascript:y" data="javascript:y"></div>',
    ],
)
def test_csp_rule_stays_silent(source):
    assert _csp(source, "strict") == []


def test_csp_rule_checks_the_element_that_holds_text_content_but_not_what_is_inside():
    # The browser reads the content as text, but the start tag is still HTML.
    source = '<noscript onclick="x"><i onclick="y"></i></noscript>'
    assert _csp(source, "strict") == [(10, 17, "error", _CSP_NATIVE_EVENT.format(name="onclick"))]


def test_csp_rule_reads_markup_around_a_v_pre_region_and_a_component_tag():
    source = '<c-Card onclick="x"><b onclick="y"></b></c-Card><div v-pre onclick="z"></div><i onclick="w"></i>'
    # The component tag's own attributes are inputs, so only its content is
    # read. The v-pre element is read like any other.
    assert [(start, end) for start, end, _severity, _message in _csp(source, "strict")] == [
        (23, 30),
        (59, 66),
        (80, 87),
    ]


def test_csp_rule_reads_c_raw_content_with_the_names_as_written():
    source = '<c-raw>é <B ONCLICK="x"></B><A HREF=javascript:y>z</A><STYLE>q</STYLE></c-raw>'
    findings = _csp(source, "strict")
    assert findings == [
        (13, 20, "error", _CSP_NATIVE_EVENT.format(name="ONCLICK")),
        (37, 49, "error", _CSP_JAVASCRIPT_URL.format(name="HREF")),
        (56, 61, "error", _CSP_RAW_TAG.format(tag="STYLE")),
    ]
    # A name followed by spaces, or a value of mixed case, is still found.
    spaced = '<c-raw><A\n  HREF = "JaVaScRiPt:x">y</A></c-raw>'
    assert _csp(spaced, "strict") == [(20, 32, "error", _CSP_JAVASCRIPT_URL.format(name="HREF"))]
    # Another attribute that holds the name as a word does not move the finding.
    decoy = '<c-raw><a title="onclick" onclick="x"></a></c-raw>'
    assert _csp(decoy, "strict") == [(26, 33, "error", _CSP_NATIVE_EVENT.format(name="onclick"))]


def test_csp_rule_checks_an_attribute_with_extension_syntax_by_its_name_only():
    # The value is known only after the extension runs, so a javascript: URL
    # that may depend on it is not reported; an on* name never depends on it.
    def findings(source: str, marker: str) -> list[tuple[int, int, str]]:
        start = source.index(marker)
        span = ForeignSpan(start, start + len(marker), "x", 0, may_control_body=False)
        template = parse_template(source, options=ParseOptions([span]))
        consumers = (MarkupLintConsumer(csp="strict"),)
        return [
            (finding.start_index, finding.end_index, finding.message)
            for finding in lint_markup(template, consumers)
            if finding.code == "citry.template.csp-incompatible"
        ]

    assert findings('<a href="javascript:{% x %}">y</a>', "{% x %}") == []
    assert findings('<object data="javascript:{% x %}"></object>', "{% x %}") == []
    assert findings('<div onclick="go({% x %})"></div>', "{% x %}") == [
        (5, 12, _CSP_NATIVE_EVENT.format(name="onclick")),
    ]
    # An attribute beside it is judged as usual.
    assert findings('<a href="javascript:{% x %}" onclick="y">z</a>', "{% x %}") == [
        (29, 36, _CSP_NATIVE_EVENT.format(name="onclick")),
    ]


# The attribute snippets whose render-time result is compared with the template check.
_CSP_AGREEMENT_SNIPPETS = [
    '<button onclick="go()">x</button>',
    '<button ONCLICK="go()">x</button>',
    '<div online="1"></div>',
    '<div on="1" ono="1"></div>',
    "<button onclick>x</button>",
    '<a href="javascript:alert(1)">x</a>',
    '<a href="JavaScript:x">x</a>',
    '<a href="  JavaScript:x">x</a>',
    '<a href="java&#115;cript:alert(1)">x</a>',
    '<a href="java&#x73;cript:x">x</a>',
    '<a href="java&Tab;script:x">x</a>',
    '<a href="java\tscript:x">x</a>',
    '<a href="javascript&colon;x">x</a>',
    '<a href="javascript&#58;x">x</a>',
    '<a href="https://example.com/javascript:x">x</a>',
    '<a href="/javascript:x">x</a>',
    "<a href>x</a>",
    '<a href="">x</a>',
    '<a title="javascript:x">x</a>',
    '<object data="javascript:x"></object>',
    '<div data="javascript:x"></div>',
    '<img src="javascript:x" alt="">',
    '<form action="javascript:x"></form>',
    '<button formaction="javascript:x">x</button>',
    '<svg><a xlink:href="javascript:x"></a></svg>',
    "<a href='javascript:x' onclick='y'>x</a>",
    "<script>var a = 1</script>",
    "<style>a { color: red }</style>",
    "<svg><script>x</script></svg>",
    '<BUTTON onclick="x">y</BUTTON>',
    '<A HREF="javascript:x">y</A>',
    "<Script>a</Script>",
    "<SCRIPT>a</SCRIPT>",
    '<c-raw>é <a onclick="x" href="javascript:y">z</a><script>q</script></c-raw>',
    '<c-raw><B ONCLICK="x"></B><SCRIPT>a</SCRIPT><A HREF=javascript:y>z</A></c-raw>',
    '<c-element is="object" data="javascript:x"></c-element>',
    '<c-element is="div" data="javascript:x"></c-element>',
    '<c-element is="script">a</c-element>',
    '<c-element is="STYLE"></c-element>',
    '<div onclick.prevent="x"></div>',
    "<div ONCLICK.once></div>",
    '<a href.x="javascript:x"></a>',
    '<plaintext onclick="x">y</plaintext>',
    # Vue bindings get their values in the browser, and a listener is not an
    # attribute, so neither check reports these.
    "<a :href=\"'javascript:x'\">x</a>",
    '<button @click="go()">x</button>',
    # The browser reads the content of these elements as text, so neither
    # check reads the tags written inside them.
    '<noscript><div onclick="x"></div></noscript>',
    '<xmp><div onclick="x"></div></xmp>',
    '<iframe><div onclick="x"></div></iframe>',
    '<noembed><div onclick="x"></div></noembed>',
    '<noframes><div onclick="x"></div></noframes>',
    '<plaintext><div onclick="x"></div></plaintext>',
]

# Cases where the two checks differ, as (template, template check, page check), with the reason.
_CSP_DIFFERENCES = [
    # A template with v-pre becomes a Vue page, which the browser builds. When
    # security_csp is not "off", Citry does not server-render a Vue page, so the
    # page check sees an empty mount element. A component with no browser code
    # is server-rendered as HTML and cannot use v-pre. Vue still sets the
    # attributes it leaves as written, so the template check reports them.
    ('<div v-pre onclick="x"></div>', [("native-event", "onclick")], []),
    ('<div v-pre><span onclick="x"></span></div>', [("native-event", "onclick")], []),
    # A bound `is` is a value from data, so the template check keeps the
    # c-element name; the page check knows the element that was rendered.
    ("""<c-element c-is="'script'"></c-element>""", [], [("raw-tag", "script")]),
    # The template check does not read the content of an SVG <title> or <style>
    # as text, as the page check does, so it misses the tags inside. For
    # <style> it still reports the <style> itself.
    ('<svg><title><a onclick="x"></a></title></svg>', [], [("native-event", "onclick")]),
    (
        '<svg><style><a onclick="x"></a></style></svg>',
        [("raw-tag", "style")],
        [("native-event", "onclick"), ("raw-tag", "style")],
    ),
]


_RENDER_CSP_FINDING = re.compile(
    r"^- \S+, (?:attribute '(?P<name>[^']+)', settled HTML bytes \d+:\d+: "
    r"(?:the native inline (?P<event>event) attribute|a (?P<url>javascript): URL in)"
    r"|pre-extension HTML bytes \d+:\d+: a raw <(?P<tag>\w+)> element)",
    re.MULTILINE,
)
_TEMPLATE_CSP_FINDING = re.compile(
    r"inline event attribute '(?P<event>[^']+)'|javascript: URL in '(?P<url>[^']+)'|inline <(?P<tag>\w+)>"
)


def _render_time_csp_findings(template: str) -> list[tuple[str, str]]:
    """Render ``template`` with ``security_csp="warn"`` and return (kind, name) of what the page check found."""
    engine = Citry(autodiscover=False, security_csp="warn")

    # The template is data here, so the class is built from it.
    page = type("Page", (Component,), {"citry": engine, "template": template})
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        page().render().serialize()
    found = []
    for warning in caught:
        if issubclass(warning.category, RuntimeWarning):
            for match in _RENDER_CSP_FINDING.finditer(str(warning.message)):
                if match["event"]:
                    found.append(("native-event", match["name"].lower()))
                elif match["url"]:
                    found.append(("javascript-url", match["name"].lower()))
                else:
                    found.append(("raw-tag", match["tag"].lower()))
    return sorted(found)


def _template_csp_findings(template: str) -> list[tuple[str, str]]:
    found = []
    for _start, _end, _severity, message in _csp(template, "warn"):
        match = _TEMPLATE_CSP_FINDING.search(message)
        assert match is not None, message
        if match["event"]:
            found.append(("native-event", match["event"].lower()))
        elif match["url"]:
            found.append(("javascript-url", match["url"].lower()))
        else:
            found.append(("raw-tag", match["tag"].lower()))
    return sorted(found)


@pytest.mark.parametrize("template", _CSP_AGREEMENT_SNIPPETS)
def test_csp_rule_finds_what_the_page_check_finds_in_literal_markup(template):
    assert _template_csp_findings(template) == _render_time_csp_findings(template)


@pytest.mark.parametrize(("template", "from_template", "from_page"), _CSP_DIFFERENCES)
def test_csp_rule_differs_from_the_page_check_in_these_documented_cases(template, from_template, from_page):
    assert _template_csp_findings(template) == from_template
    assert _render_time_csp_findings(template) == from_page


def test_csp_rule_skips_a_capitalized_name_that_is_no_html_element_though_render_time_reports_it():
    template = '<Card onclick="x">y</Card>'
    # The browser gets <Card> as a plain element, so the page check reports its
    # handler. The template check cannot tell that from a Vue component, whose
    # attributes are inputs, so it stays silent rather than report a false alarm.
    assert _render_time_csp_findings(template) == [("native-event", "onclick")]
    assert _template_csp_findings(template) == []


def test_csp_agreement_list_reports_something_and_covers_the_decode_cases():
    reported = [template for template in _CSP_AGREEMENT_SNIPPETS if _template_csp_findings(template)]
    # A list where neither check reported anything would agree with any rule.
    assert len(reported) >= 20
    assert {'<a href="java&#115;cript:alert(1)">x</a>', '<a href="java\tscript:x">x</a>'} <= set(reported)


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
    # The parser stops at the end of the text, so the finding moves back to
    # the last character written before it.
    assert _invalid(source) == [("&", "error")]
    template = parse_template(source)
    (finding,) = lint_invalid_vue_expressions(template, browser_expressions(template), ())
    assert finding.code == "citry.vue.invalid-expression"
    assert finding.message == (
        "The Vue expression in 'v-if' is not valid JavaScript (Unexpected token), so Vue cannot compile this template."
    )
    # The whole expression stays on the finding for the duplicate filters.
    expression = source.encode("utf-8").index(b"open &&")
    assert (finding.context_start_index, finding.context_end_index) == (expression, expression + len("open &&"))


def test_invalid_vue_expression_checks_bindings_listeners_loops_and_server_call_arguments():
    source = (
        '<div :title="a +"></div><button @click="go(">x</button>'
        '<li v-for="x in [1,">y</li><button @c-click="save({a: })">s</button>'
    )
    # A loop finding points into the part after `in`, and the others at the
    # token where the parser stopped.
    assert [span for span, _severity in _invalid(source)] == ["+", "(", ",", "}"]


@pytest.mark.parametrize(
    ("source", "span", "detail"),
    [
        ('<b @click="go() }">x</b>', "}", "Unexpected token"),
        ('<p :title="a +* b"></p>', "*", "Unexpected token"),
        ('<p :title="foo("></p>', "(", "Expected `)` but found `EOF`"),
        ('<p :title="\'open"></p>', "'open", "Unterminated string"),
        # Text that closes the generated wrapper is still a mistake, at the
        # token that closes it.
        ('<p :title="a); (b"></p>', ")", "Unexpected token"),
        ('<b @click="let a = 1; let a = 2">x</b>', "a", "Identifier `a` has already been declared"),
        # Byte offsets before a multi-byte character map to the right place.
        ('<p :title="café +* b"></p>', "*", "Unexpected token"),
        # A function-expression listener is blamed for its own mistake, not
        # for the name a function declaration would need.
        ('<b @click="function () { a +* b }">x</b>', "*", "Unexpected token"),
        # A trailing comment is skipped when the parser stops at the end.
        ('<p :title="open && // note"></p>', "&", "Unexpected token"),
        # A quote inside a regular expression does not start a string.
        ('<p :title="a.match(/\'/) &&"></p>', "&", "Unexpected token"),
    ],
)
def test_invalid_vue_expression_names_the_parser_error_where_it_points(source, span, detail):
    template = parse_template(source)
    (finding,) = lint_invalid_vue_expressions(template, browser_expressions(template), ())
    encoded = source.encode("utf-8")
    assert encoded[finding.start_index : finding.end_index].decode("utf-8") == span
    assert f"({detail})" in finding.message
    # The second `a` is the one the duplicate declaration points to.
    if "let a" in source:
        assert finding.start_index == encoded.index(b"a = 2")


@pytest.mark.parametrize(
    "source",
    [
        # Positions in decoded text do not match the template, so a
        # character reference keeps the whole expression and no parser text.
        '<p v-if="open &amp;&amp;"></p>',
        # A slot pattern is checked without the parser's message.
        '<MyList><template v-slot:row="{ item:"></template></MyList>',
    ],
)
def test_invalid_vue_expression_keeps_the_whole_range_without_a_parser_position(source):
    template = parse_template(source)
    findings = lint_invalid_vue_expressions(template, browser_expressions(template), ())
    assert len(findings) == 1
    (finding,) = findings
    assert (finding.start_index, finding.end_index) == (finding.context_start_index, finding.context_end_index)
    assert "(" not in finding.message.split("JavaScript", 1)[1].split(",", 1)[0]


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
        # Valueless bindings bind nothing or read the same-name variable.
        '<i v-bind="" v-on=""></i>',
    ],
)
def test_invalid_vue_expression_stays_silent(source):
    assert _invalid(source) == []


def test_invalid_vue_expression_reports_a_value_of_only_spaces():
    # Only a binding with no value at all is Vue's same-name shorthand.
    assert _invalid('<div :title="  "></div>') == [("  ", "error")]


def test_invalid_vue_expression_follows_the_consumers_severity():
    source = '<p v-if="open &&"></p>'
    assert _invalid(source, (MarkupLintConsumer(rule_invalid_vue_expression="ignore"),)) == []
    assert _invalid(source, (MarkupLintConsumer(rule_invalid_vue_expression="warning"),)) == [("&", "warning")]


def test_invalid_vue_expression_skips_v_pre_inside_a_nested_template():
    source = '<c-card c-header="<><i v-pre :x=\'a &&\'></i></>" /><p :y="b &&"></p>'
    assert _invalid(source) == [("&", "error")]
