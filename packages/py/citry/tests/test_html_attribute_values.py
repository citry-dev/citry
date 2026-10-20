"""The generator reads closed keyword sets from the HTML Standard's attribute index."""

from __future__ import annotations

from scripts.generate_html_attribute_values import build_attribute_names, build_table, render

# A small copy of the standard's layout. Like the real page, it omits the
# optional </td> and </tr> end tags.
_PAGE = """<!DOCTYPE html>
<p>Last Updated <span class=pubdate>1 January 2030</span>
<table>
 <thead><tr><th>Element<th>Description
 <tbody>
 <tr><th><code>a</code><td>Hyperlink
 <tr><th><code>h1</code>, <code>h2</code><td>Heading
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
    assert elements == ("a", "h1", "h2")
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
    assert global_names == ("draggable", "hidden", "onclick", "role")
    # Only names in the page's element list count, so `img` and `body` are
    # left out here. A note in parentheses names no owner, and owners written
    # without a separator still count.
    assert by_element == {"a": ("form", "width"), "h1": ("width",), "h2": ("width",)}
    assert custom_names == ("form",)


def test_render_writes_an_importable_module():
    namespace: dict[str, object] = {}
    exec(compile(render(_PAGE, retrieved="2030-01-02"), "generated", "exec"), namespace)  # noqa: S102

    assert namespace["HTML_ELEMENTS"] == frozenset({"a", "h1", "h2"})
    assert namespace["CASE_SENSITIVE_KEYWORDS"] == {
        ("ol", "type"): ("1", "a", "A", "i", "I"),
        ("li", "type"): ("1", "a", "A", "i", "I"),
    }
    assert namespace["FRAME_NAME_ELEMENTS"] == ("iframe", "object")
