"""The generator reads HTML, ARIA, SVG, and DOM event names and values from the standards."""

from __future__ import annotations

import pytest
from scripts.generate_html_attribute_values import (
    OUTPUT_PATH,
    build_aria_attributes,
    build_attribute_names,
    build_boolean_attributes,
    build_event_names,
    build_obsolete_elements,
    build_svg_elements,
    build_table,
    check_required_names,
    render,
)

from citry._html_attribute_values import (
    ARIA_ATTRIBUTES,
    BOOLEAN_ATTRIBUTES,
    DOM_EVENT_NAMES,
    OBSOLETE_ELEMENTS,
    SVG_ELEMENTS,
)

# A small copy of the standard's layout. Like the real page, it omits the
# optional </td> and </tr> end tags.
_PAGE = """<!DOCTYPE html>
<p>Last Updated <span class=pubdate>1 January 2030</span>
<table>
 <thead><tr><th>Element<th>Description
 <tbody>
 <tr><th><code>a</code><td>Hyperlink
 <tr><th><code>h1</code>, <code>h2</code><td>Heading
 <tr><th><code>img</code><td>Image
 <tr><th><code>video</code><td>Video
 <tr><th><code>form</code><td>Form
 <tr><th>SVG <code>svg</code><td>SVG root
 <tr><th>autonomous custom elements<td>Author-defined
</table>
<table id=attributes-1>
 <thead><tr><th>Attribute<th>Element(s)<th>Description<th>Value
 <tbody>
 <tr><th><code>draggable</code><td>HTML elements<td>Drag<td>"<code>true</code>"; "<code>false</code>"
 <tr><th><code>hidden</code>
  <td>HTML elements
  <td>Hidden
  <td>"<code>until-found</code>"; "<code>hidden</code>"; the empty string
 <tr><th><code>step</code>
  <td><code>input</code>
  <td>Step
  <td>Valid floating-point number greater than zero, or "<code>any</code>"
 <tr><th><code>crossorigin</code>
  <td><code>img</code>; <code>video</code>
  <td>CORS
  <td>"<code>anonymous</code>"; "<code>use-credentials</code>"; the empty string
 <tr><th><code>accept-charset</code>
  <td><code>form</code>
  <td>Charset
  <td>ASCII case-insensitive match for "<code>UTF-8</code>"
 <tr><th><code>form</code>
  <td><code>a</code>; form-associated custom elements
  <td>Form owner
  <td>ID
 <tr><th><code>width</code>
  <td><code>h1</code>; <code>source</code> (in <code>a</code>); <code>h2</code> <code>a</code>
  <td>Width
  <td>Number
 <tr><th><code>disabled</code>
  <td><code>a</code>; form-associated custom elements
  <td>Disabled
  <td><a href=common-microsyntaxes.html#boolean-attribute>Boolean attribute</a>
 <tr><th><code>disabled</code><td><code>h1</code><td>Disabled<td>Boolean attribute
 <tr><th><code>inert</code><td>HTML elements<td>Inert<td>Boolean attribute
</table>
<table id=ix-event-handlers>
 <thead><tr><th>Attribute<th>Element(s)<th>Description<th>Value
 <tbody>
 <tr><th><code>onclick</code><td>HTML elements<td>Click<td>Event handler
 <tr><th><code>onunload</code><td><code>body</code><td>Unload<td>Event handler
</table>
"""


def test_build_table_keeps_closed_keyword_sets_only():
    table, elements, updated = build_table(_PAGE)

    assert updated == "1 January 2030"
    # SVG and the custom-element row are not HTML element names.
    assert elements == ("a", "form", "h1", "h2", "img", "video")
    assert table["draggable"] == {"*": ("true", "false")}
    assert table["hidden"] == {"*": ("until-found", "hidden", "")}
    assert table["crossorigin"] == {
        "img": ("anonymous", "use-credentials", ""),
        "video": ("anonymous", "use-credentials", ""),
    }
    assert table["accept-charset"] == {"form": ("UTF-8",)}
    # A value cell that also allows a number is open, so it is left out.
    assert "step" not in table
    # The hand-added sets the index names only in words are present.
    assert "email" in table["type"]["input"]
    assert "no-referrer" in table["referrerpolicy"]["img"]


def test_build_attribute_names_splits_global_element_and_custom_element_names():
    global_names, by_element, custom_names = build_attribute_names(_PAGE)

    # Event handlers count as attributes, and `role` is added by hand.
    assert global_names == ("draggable", "hidden", "inert", "onclick", "role")
    # Only names in the page's element list count, so `input`, `source`, and `body`
    # are left out here. A note in parentheses names no owner, and owners
    # written without a separator still count.
    assert by_element == {
        "a": ("disabled", "form", "width"),
        "form": ("accept-charset",),
        "h1": ("disabled", "width"),
        "h2": ("width",),
        "img": ("crossorigin",),
        "video": ("crossorigin",),
    }
    assert custom_names == ("disabled", "form")


# Small copies of the other sources, each in the markup its real page uses.
_OBSOLETE_PAGE = """<!DOCTYPE html>
<h3 id=non-conforming-features>16.2 Non-conforming features</h3>
<p>Elements in the following list are entirely obsolete:
<dl><dt><dfn id=applet data-dfn-type=element><code>applet</code></dfn><dd><p>Use
 <code id=non-conforming-features:the-embed-element><a href=#embed>embed</a></code>
 instead.<dt><code id=non-conforming-features:frame><a href=#frame>frame</a></code>
 <dt><dfn id=rb data-dfn-type=element><code>rb</code></dfn><dd><p>Use ruby.</dl>
<hr>
<p>The following attributes are obsolete:
<dl><dt><dfn data-dfn-type=element-attr><code>charset</code></dfn> on <code>a</code> elements</dl>
"""

_ARIA_PAGE = """<section id="aria-attributes">
<section class="property notoc" id="aria-label"><p>Defines a string value.</section>
<section class="state deprecated notoc" id="aria-grabbed"><p>Deprecated.</section>
<div class="property-applicability" id="aria-label-used-in">Used in</div>
</section>
"""

_ARIA_DRAFT_PAGE = """<section class="property notoc" id="aria-description"></section>"""

_SVG2_PAGE = """<ul class="element-index">
<li><span class="element-name">\u2018<a href="embedded.html"><span>foreignObject</span></a>\u2019</span></li>
<li><span class="element-name">\u2018<a href="struct.html"><span>g</span></a>\u2019</span></li>
</ul>
"""

_SVG11_PAGE = """<ul><li><a href="text.html"><span class="element-name">\u2018altGlyph\u2019</span></a></li></ul>"""

_VUE_TYPES = """export interface HTMLAttributes {
    onNotAnEvent?: string;
}
export interface Events {
    onCompositionstart: CompositionEvent;
    onDblclick: MouseEvent;
    onClick: MouseEvent;
}
"""


def test_build_boolean_attributes_merges_rows_and_marks_global_ones():
    # `disabled` has two rows, and the form-associated custom element owner
    # is left out because a template cannot tell which custom elements it covers.
    assert build_boolean_attributes(_PAGE) == {"disabled": ("a", "h1"), "inert": ("*",)}


def test_build_aria_attributes_reads_state_and_property_sections():
    # The page's container section and a "property-applicability" block are
    # not definitions, and a deprecated state still counts.
    names = build_aria_attributes(_ARIA_PAGE, _ARIA_DRAFT_PAGE)

    assert names == ("aria-description", "aria-grabbed", "aria-label")


def test_build_aria_attributes_stops_when_no_definition_is_found():
    # An empty table would make the rule report every ARIA attribute, so a
    # changed page layout must stop the generator instead.
    with pytest.raises(SystemExit):
        build_aria_attributes("<section id='aria-attributes'></section>")


def test_build_svg_elements_keeps_the_original_case():
    assert build_svg_elements(_SVG2_PAGE, _SVG11_PAGE) == ("altGlyph", "foreignObject", "g")


def test_build_obsolete_elements_reads_only_the_element_list():
    # An element the list names through a link, such as `frame`, counts,
    # and the obsolete attributes in the next list do not.
    assert build_obsolete_elements(_OBSOLETE_PAGE) == ("applet", "frame", "rb")


def test_build_event_names_unites_html_vue_and_the_hand_added_names():
    names = build_event_names(_PAGE, _VUE_TYPES)

    assert {"click", "unload", "dblclick", "compositionstart", "selectstart"} <= set(names)
    # Only the keys of Vue's `Events` type are event names.
    assert "notanevent" not in names


@pytest.mark.parametrize(
    "build",
    [
        lambda: build_boolean_attributes(_PAGE.replace("Boolean attribute", "Boolean")),
        lambda: build_svg_elements("<p>No index here."),
        lambda: build_svg_elements('<span class="element-name">\u2018two words\u2019</span>'),
        lambda: build_obsolete_elements("<h3 id=non-conforming-features></h3><dl><dt>two words</dl>"),
        lambda: build_event_names(_PAGE, "export interface Other {\n}\n"),
    ],
)
def test_builders_stop_when_the_page_layout_changed(build):
    # A table built from a page the reader no longer understands would turn
    # every real name into a report, so the generator stops instead.
    with pytest.raises(SystemExit):
        build()


_PAGES = {
    "index": _PAGE,
    "obsolete": _OBSOLETE_PAGE,
    "aria": _ARIA_PAGE,
    "aria-draft": _ARIA_DRAFT_PAGE,
    "svg2": _SVG2_PAGE,
    "svg11": _SVG11_PAGE,
}


def test_render_writes_an_importable_module():
    module = render(_PAGES, _VUE_TYPES, retrieved="2030-01-02", vue_source="Vue types, runtime-dom.d.ts")
    namespace: dict[str, object] = {}
    exec(compile(module, "generated", "exec"), namespace)  # noqa: S102

    assert namespace["HTML_ELEMENTS"] == frozenset({"a", "form", "h1", "h2", "img", "video"})
    assert namespace["CASE_SENSITIVE_KEYWORDS"] == {
        ("ol", "type"): ("1", "a", "A", "i", "I"),
        ("li", "type"): ("1", "a", "A", "i", "I"),
    }
    assert namespace["FRAME_NAME_ELEMENTS"] == ("iframe", "object")
    assert namespace["BOOLEAN_ATTRIBUTES"] == {"disabled": ("a", "h1"), "inert": ("*",)}
    assert namespace["OBSOLETE_ELEMENTS"] == frozenset({"applet", "frame", "rb"})
    assert "foreignObject" in namespace["SVG_ELEMENTS"]  # type: ignore[operator]


def test_check_required_names_stops_a_partly_read_source():
    # The small pages above lack names every real table holds, such as
    # `checked`, as a cut-off download would.
    module = render(_PAGES, _VUE_TYPES, retrieved="2030-01-02", vue_source="Vue types, runtime-dom.d.ts")

    with pytest.raises(SystemExit, match="checked"):
        check_required_names(module)


def test_check_required_names_accepts_the_committed_module():
    check_required_names(OUTPUT_PATH.read_text(encoding="utf-8"))


# The tables committed in the generated module, refreshed from the live
# standards, keep the facts the lint rules depend on.


def test_generated_boolean_attributes_leave_enumerated_ones_out():
    assert {"button", "input"} <= set(BOOLEAN_ATTRIBUTES["disabled"])
    # These take "true" and "false" as keywords, so "false" is a real value.
    for name in ("draggable", "spellcheck", "contenteditable"):
        assert name not in BOOLEAN_ATTRIBUTES


def test_generated_aria_attributes_include_draft_names():
    assert {"aria-expanded", "aria-description"} <= ARIA_ATTRIBUTES
    assert "aria-expandd" not in ARIA_ATTRIBUTES


def test_generated_element_sets_cover_svg_and_obsolete_html():
    assert {"path", "foreignObject", "g"} <= SVG_ELEMENTS
    assert {"frame", "marquee"} <= OBSOLETE_ELEMENTS


def test_generated_event_names_include_vue_and_html_events():
    assert {"click", "dblclick", "scrollend", "focusin"} <= DOM_EVENT_NAMES
    assert "clik" not in DOM_EVENT_NAMES
