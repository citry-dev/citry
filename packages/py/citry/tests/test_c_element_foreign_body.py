"""
Tests for the body of a `<c-element>` whose tag name comes from data and is `svg` or `math`.

Inside `<svg>` and `<math>` the browser reads `<style>`, `<title>`, `<noscript>`
and similar elements as markup, so trusted HTML that stays inert inside a
`<div>` can run there. When data chooses the tag (`c-is`, or an `is` key in a
`c-bind` mapping), the body may hold only what the template wrote: text,
escaped `{{ }}` values, plain elements, nested `<c-element>` tags, and the
control flow around them. Every render path must refuse the rest the same way:
the static writer, `simple=True`, the component cache, `<c-for>` loops, and the
Vue writer (a component with `js`).
"""

from __future__ import annotations

import concurrent.futures
import contextvars
import functools
import itertools
import re
from pathlib import Path
from typing import Any

import pytest
from markupsafe import Markup

import citry
import citry.util.html as html_util
from citry import Citry, Component, Extension, ForeignSpan, ForeignSpanSet, Slot
from citry._vue.capture import UnsupportedPreparedView
from citry.nodes import ForeignNode

REFUSAL = "tag name chosen at render time"

# A tag that would run if the browser read it as markup, with a handler that is easy to spot.
STYLE_HTML = Markup("<style><img src=x onerror=window.__ran=1></style>")


class _HtmlObject:
    """A value that is not a `Markup` but writes HTML as is, through `__html__`."""

    def __html__(self) -> str:
        return "<em>o</em>"


_names = itertools.count()


def _data_method(values: dict[str, Any], *, simple: bool = False) -> Any:
    """Return a `template_data` that gives the template `values`, in the form the component kind needs."""
    if simple:

        def simple_data(kwargs, slots):
            return dict(values)

        # A `simple=True` component calls `template_data` without an instance.
        return staticmethod(simple_data)

    def template_data(self, kwargs, slots):
        return dict(values)

    return template_data


@functools.cache
def _world() -> tuple[Citry, type[Component]]:
    """Return one engine, set up for Vue pages, and a small child component it knows."""
    app = Citry(autodiscover=False, secret="foreign-body-test-secret" * 2)
    app.set_mounted_prefix("/citry")
    app.initialize()

    class ForeignKid(Component):
        citry = app
        template = """
            <g>k</g>
        """

    return app, ForeignKid


def _inner_class(path: str, body: str, data: dict[str, Any]) -> type[Component]:
    """Build the component that holds `body`, wired for one render path."""
    app, _kid = _world()
    values = dict(data)
    attrs: dict[str, Any] = {"citry": app}
    if path == "loop":
        # A <c-for> around the element makes its body render inside a loop.
        body = '<c-for each="n in one">' + body + "</c-for>"
        values["one"] = [1]
    attrs["template"] = body
    if path == "simple":
        attrs["simple"] = True
    attrs["template_data"] = _data_method(values, simple=path == "simple")
    if path == "vue":
        # The `js` makes the component a Vue component, so it takes the Vue writer.
        attrs["js"] = """
            $component({});
        """
    if path == "cache":
        attrs["Cache"] = type("Cache", (), {"enabled": True, "ttl": 300, "version": 1})
    return type(f"Inner{next(_names)}", (Component,), attrs)


def _page_around(inner: type[Component]) -> type[Component]:
    """Build a page whose body is the inner component, so every path renders as a child."""
    app, _kid = _world()
    template = f'<!doctype html><html><head><meta charset="utf-8"></head><body><c-{inner.__name__} /></body></html>'
    return type(f"Page{next(_names)}", (Component,), {"citry": app, "template": template})


def _render(path: str, body: str, data: dict[str, Any]) -> str:
    """Render `body` on one path and return the page HTML. A cached component renders twice."""
    page = _page_around(_inner_class(path, body, data))
    html = page().render().serialize()
    if path == "cache":
        # The second render replays the first from the cache.
        html = page().render().serialize()
    return html


PATHS = ("static", "simple", "cache", "loop", "vue")

DATA: dict[str, Any] = {
    "s": "<x>",
    "m": STYLE_HTML,
    "obj": _HtmlObject(),
    "inner": "g",
    "yes": True,
    "items": [1, 2],
    # A Markup value with no tag in it: text and character references only.
    "plain_markup": Markup("a &amp; b"),
}

# Bodies that hold trusted or unreadable HTML. The id says what the body holds.
REFUSED_BODIES = {
    "markup-value": "{{ m }}",
    "html-object": "{{ obj }}",
    "c-raw": "<c-raw><i>r</i></c-raw>",
    "child-component": "<c-ForeignKid />",
    "markup-in-c-if": '<c-if cond="yes"><g>{{ m }}</g></c-if>',
    "markup-in-c-for": '<c-for each="i in items">{{ m }}</c-for>',
    "markup-in-nested-element": '<c-element c-is="inner">{{ m }}</c-element>',
}

# Bodies the template wrote, and the text each must put on the page.
ALLOWED_BODIES = {
    "authored-element": ('<circle id="c"></circle>', '<circle id="c"></circle>'),
    "escaped-value": ("a &amp; b {{ s }}", "a &amp; b &lt;x&gt;"),
    "nested-element-with-authored-children": (
        '<g><c-element c-is="inner">{{ s }}<rect></rect></c-element></g>',
        "<g>&lt;x&gt;<rect></rect></g>",
    ),
    "c-if-around-an-element": ('<c-if cond="yes"><rect>{{ s }}</rect></c-if>', "<rect>&lt;x&gt;</rect>"),
    "c-for-around-an-element": ('<c-for each="i in items"><rect c-id="i"></rect></c-for>', '<rect id="2"></rect>'),
}

# How the tag name reaches the element. Each template wraps one body at BODY.
TAG_SOURCES = {
    "c-is": ('<c-element c-is="t">BODY</c-element>', {"t": "svg"}),
    "c-bind-is": ('<c-element c-bind="battrs">BODY</c-element>', {"battrs": {"is": "svg"}}),
}


def _wrap(source: tuple[str, dict[str, Any]], body: str) -> tuple[str, dict[str, Any]]:
    template, tag_data = source
    # A plain replace, because a body such as `{{ m }}` holds braces that `str.format` would read.
    return template.replace("BODY", body), {**DATA, **tag_data}


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("body", REFUSED_BODIES.values(), ids=REFUSED_BODIES)
@pytest.mark.parametrize("source", TAG_SOURCES.values(), ids=TAG_SOURCES)
def test_data_chosen_svg_refuses_trusted_html_in_its_body(source: tuple[str, dict], body: str, path: str) -> None:
    """
    A body that holds trusted HTML is refused on every path, for either way of choosing the tag.

    Each path writes the body differently, so each needs the refusal; a path that
    skipped it would let `<style>` and `<noscript>` contents run as markup.
    """
    template, data = _wrap(source, body)

    with pytest.raises(ValueError, match=REFUSAL):
        _render(path, template, data)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("tag", ["svg", "SVG", "Svg", "math", "MATH", "mAtH"])
def test_the_refusal_covers_svg_and_math_in_any_letter_case(tag: str, path: str) -> None:
    # The browser reads the tag name without regard to case, so the check must too.
    with pytest.raises(ValueError, match=REFUSAL):
        _render(path, '<c-element c-is="t">{{ m }}</c-element>', {**DATA, "t": tag})


# Like `svg` and `math`, a `mglyph` or `malignmark` inside `<math><mi>` is read as foreign content
# (both are on `FOREIGN_CONTENT_TAGS`), so a `<style>` in its body would be live markup. The Vue
# writer already refuses a Markup value anywhere under `<math>`, so these cases cover the other paths.
@pytest.mark.parametrize("path", ["static", "simple", "cache", "loop"])
@pytest.mark.parametrize("tag", ["mglyph", "MGLYPH", "malignmark", "MAlignMark"])
def test_data_chosen_mathml_text_elements_refuse_trusted_html_in_their_body(tag: str, path: str) -> None:
    template = '<math><mi><c-element c-is="t">{{ m }}</c-element></mi></math>'

    with pytest.raises(ValueError, match=REFUSAL):
        _render(path, template, {**DATA, "t": tag})


@pytest.mark.parametrize("path", ["static", "simple", "cache", "loop"])
def test_a_span_chosen_by_data_inside_math_keeps_a_markup_body(path: str) -> None:
    # Control: an ordinary tag inside <math> does not change how the browser reads its body.
    template = '<math><mi><c-element c-is="t">{{ m }}</c-element></mi></math>'

    html = _render(path, template, {**DATA, "t": "span"})

    assert str(STYLE_HTML) in html


@pytest.mark.parametrize("path", ["static", "simple", "cache", "loop"])
@pytest.mark.parametrize("tag", ["svg", "math"])
def test_a_script_the_template_wrote_is_refused_under_a_data_chosen_foreign_tag(tag: str, path: str) -> None:
    # Inside <svg> the browser decodes `&#34;` in a <script>, so an escaped
    # value could leave the JavaScript string it sits in.
    template = '<c-element c-is="t"><script>var x = "{{ s }}";</script></c-element>'

    with pytest.raises(ValueError, match=REFUSAL):
        _render(path, template, {**DATA, "t": tag, "s": '";x=1;//'})


@pytest.mark.parametrize("path", ["static", "simple", "cache", "loop"])
def test_a_script_the_template_wrote_stays_allowed_under_a_data_chosen_div(path: str) -> None:
    # Control: in HTML the browser keeps `&#34;` in a <script> as written.
    template = '<c-element c-is="t"><script>var x = "{{ s }}";</script></c-element>'

    html = _render(path, template, {**DATA, "t": "div", "s": '";x=1;//'})

    assert 'var x = "&#34;;x=1;//";' in html


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("key", ["is", "Is", "IS", "iS"])
@pytest.mark.parametrize(
    "template",
    [
        '<c-element c-is="t" c-bind="battrs">{{ m }}</c-element>',
        '<c-element is="section" c-bind="battrs">{{ m }}</c-element>',
    ],
    ids=["over-c-is", "over-fixed-is"],
)
def test_an_is_key_in_c_bind_overrides_the_tag_in_any_letter_case(template: str, key: str, path: str) -> None:
    """
    A `c-bind` key `is`, in any case, replaces the tag the template wrote, so the body check follows it.

    The template names a harmless tag, so a check that read only the template's
    tag would let the Markup body through under the `svg` that data picked.
    """
    data = {**DATA, "t": "div", "battrs": {key: "svg"}}

    with pytest.raises(ValueError, match=REFUSAL):
        _render(path, template, data)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("body", REFUSED_BODIES.values(), ids=REFUSED_BODIES)
def test_a_div_chosen_by_data_still_takes_the_same_body(body: str, path: str) -> None:
    # Control: only `svg` and `math` change how the browser reads the body, so `div` keeps working.
    html = _render(path, f'<c-element c-is="t">{body}</c-element>', {**DATA, "t": "div"})

    assert "<div" in html
    assert "</div>" in html


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize(("body", "expected"), ALLOWED_BODIES.values(), ids=ALLOWED_BODIES)
@pytest.mark.parametrize("source", TAG_SOURCES.values(), ids=TAG_SOURCES)
def test_data_chosen_svg_keeps_what_the_template_wrote(
    source: tuple[str, dict], body: str, expected: str, path: str
) -> None:
    # Authored elements, escaped values, nested elements, and control flow are not trusted HTML.
    template, data = _wrap(source, body)

    html = _render(path, template, data)

    assert "<svg" in html
    assert expected in html


@pytest.mark.parametrize("path", ["static", "simple", "cache", "loop"])
def test_a_markup_value_without_a_tag_is_text_under_a_data_chosen_svg(path: str) -> None:
    # Control: HTML with no '<' reads the same inside <svg> as inside a <div>.
    html = _render(path, '<c-element c-is="t">{{ plain_markup }}</c-element>', {**DATA, "t": "svg"})

    assert "a &amp; b" in html


def test_the_vue_writer_refuses_every_markup_value_under_svg() -> None:
    # This rule was there before the body check: Vue inserts a Markup value with the HTML
    # parser, so even text-only Markup cannot sit under an <svg>. It passes with or without the fix.
    with pytest.raises(UnsupportedPreparedView, match="interactive component"):
        _render("vue", '<c-element c-is="t">{{ plain_markup }}</c-element>', {**DATA, "t": "svg"})


def _slot_inner(mode: str, tag: str) -> type[Component]:
    """Build a component whose `<c-element>` body is its default slot, on the static, simple, or Vue path."""
    app, _kid = _world()
    attrs: dict[str, Any] = {
        "citry": app,
        "template": '<c-element c-is="t"><c-slot /></c-element>',
        "template_data": _data_method({"t": tag}, simple=mode == "simple"),
    }
    if mode == "simple":
        attrs["simple"] = True
    if mode == "vue":
        attrs["js"] = """
            $component({});
        """
    return type(f"SlotInner{next(_names)}", (Component,), attrs)


@pytest.mark.parametrize("tag", ["svg", "MATH"])
@pytest.mark.parametrize("mode", ["static", "simple", "vue"])
@pytest.mark.parametrize("fill", ["{{ m }}", "<c-raw><i>r</i></c-raw>", "<c-ForeignKid />"])
def test_slot_content_in_the_body_is_refused(fill: str, mode: str, tag: str) -> None:
    """
    A `<c-slot />` in the body is refused when the caller's content holds trusted HTML.

    The caller writes the slot content, not the component that chose the tag,
    so it can carry trusted HTML that the component never sees.
    """
    app, _kid = _world()
    inner = _slot_inner(mode, tag)
    outer = type(
        f"SlotOuter{next(_names)}",
        (Component,),
        {
            "citry": app,
            "template": f"<main><c-{inner.__name__}>{fill}</c-{inner.__name__}></main>",
            "template_data": _data_method({"m": STYLE_HTML}),
        },
    )

    with pytest.raises(ValueError, match=REFUSAL):
        outer().render().serialize()


def _style_slot(context: object) -> Markup:
    return STYLE_HTML


@pytest.mark.parametrize("mode", ["static", "vue"])
@pytest.mark.parametrize("value", [STYLE_HTML, Slot(_style_slot)], ids=["markup", "slot-function"])
def test_slot_content_passed_from_python_is_refused(value: object, mode: str) -> None:
    # A slot filled from Python, not from a template, reaches the same body.
    inner = _slot_inner(mode, "svg")

    with pytest.raises(ValueError, match=REFUSAL):
        inner(slots={"default": value}).render().serialize()


def test_a_plain_string_slot_from_python_is_escaped_and_allowed() -> None:
    # Control: a `str` slot value is escaped like any `{{ }}` value, so it stays inert.
    html = _slot_inner("static", "svg")(slots={"default": "<x>"}).render().serialize()

    assert "&lt;x&gt;" in html


# The older node classes write a template's own tags as plain strings, which
# an extension that claims part of the template (a foreign span) switches on.
_HOST_SPAN = "{% host %}"


def _host_extension() -> type[Extension]:
    """Return an extension that claims the `{% host %}` span, as a host-template extension does."""

    class Host(Extension):
        name = "foreignbodyhost"

        def on_template_foreign_spans(self, ctx):
            start = ctx.content.encode().find(_HOST_SPAN.encode())
            if start < 0:
                return None
            return ForeignSpanSet((ForeignSpan(start, start + len(_HOST_SPAN)),))

        def on_template_foreign_compiled(self, ctx):
            ctx.nodes[:] = ["" if isinstance(item, ForeignNode) else item for item in ctx.nodes]
            ctx.mark_resolved(*ctx.claims)

    return Host


def _render_with_foreign_span(body: str, data: dict[str, Any]) -> str:
    """Render `body` inside a `<c-element c-is="t">` in a template that an extension claims a span of."""
    app = Citry(autodiscover=False, extensions=[_host_extension()])

    class Kid(Component):
        citry = app
        template = "<g>k</g>"

    class Page(Component):
        citry = app
        template = _HOST_SPAN + f'<c-element c-is="t">{body}</c-element>'

        def template_data(self, kwargs, slots):
            return data

    return str(Page())


@pytest.mark.parametrize("tag", ["svg", "math"])
@pytest.mark.parametrize("body", ["{{ m }}", "<c-Kid />"], ids=["markup-value", "child-component"])
def test_the_node_path_refuses_trusted_html_under_a_data_chosen_foreign_tag(body: str, tag: str) -> None:
    with pytest.raises(ValueError, match=REFUSAL):
        _render_with_foreign_span(body, {**DATA, "t": tag})


@pytest.mark.parametrize("tag", ["svg", "math"])
def test_the_node_path_keeps_authored_elements_and_escaped_values(tag: str) -> None:
    html = _render_with_foreign_span("<circle></circle>{{ s }}", {**DATA, "t": tag})

    assert f"<{tag}" in html
    assert "<circle></circle>&lt;x&gt;" in html


@pytest.mark.parametrize("tag", ["svg", "math"])
def test_the_node_path_refuses_a_script_the_template_wrote(tag: str) -> None:
    # The node path writes template tags as plain text, so the check reads that text for a <script>.
    with pytest.raises(ValueError, match=REFUSAL):
        _render_with_foreign_span('<script>var a = "{{ s }}";</script>', {**DATA, "t": tag})


def test_the_node_path_still_allows_markup_under_a_div() -> None:
    # Control for the refusals above: the same Markup body under `div`.
    html = _render_with_foreign_span("{{ m }}", {**DATA, "t": "div"})

    assert str(STYLE_HTML) in html


# A slot rendered outside the page render, with `str(slot)` after the render
# or in a worker thread, renders its components with the older node classes
# (the node path). There the element writes its own tags as trusted HTML, and
# the check must tell them from the body. The tags are `Markup` while the
# element's own template has not been compiled yet, and prepared parts once it
# has (a "warm" route: any `<c-element>` already rendered in the process). The
# host-template route renders the element itself on the page render, so it
# guards against a regression there rather than testing the node path.
NODE_ROUTES = ("kept-slot", "worker-thread", "warm-kept-slot", "warm-worker-thread", "host-template")


def _render_on_node_route(route: str, body: str, data: dict[str, Any], fill: str = "") -> str:
    """Render `<c-element c-is="t">body</c-element>` in a component reached through one node-path route."""
    app = Citry(autodiscover=False, extensions=[_host_extension()] if route == "host-template" else [])

    class Kid(Component):
        citry = app
        template = """
            <g>k</g>
        """

    class Inner(Component):
        citry = app
        template = (_HOST_SPAN if route == "host-template" else "") + f'<c-element c-is="t">{body}</c-element>'

        def template_data(self, kwargs, slots):
            return data

    if route.startswith("warm-"):
        # Render one ordinary <c-element> first, so the built-in's template is compiled.
        warm_attrs = {"citry": app, "template": '<c-element c-is="w">x</c-element>'}
        warm = type("Warm", (Component,), {**warm_attrs, "template_data": _data_method({"w": "span"})})
        warm().render().serialize()
    kept: list[Slot] = []

    class Holder(Component):
        citry = app
        template = """
            <section>{{ printed }}</section>
        """

        def template_data(self, kwargs, slots):
            if route.endswith("worker-thread"):
                # The slot renders in an empty context, without the page render's
                # context variables. An executor's worker copies them on
                # free-threaded Python 3.14, which would take the ordinary path.
                with concurrent.futures.ThreadPoolExecutor(1) as pool:
                    printed = pool.submit(contextvars.Context().run, str, slots["default"]).result()
                return {"printed": Markup(printed)}  # noqa: S704 - the slot's own rendered HTML
            kept.append(slots["default"])
            return {"printed": ""}

    holder_call = f"<c-Holder><c-Inner>{fill}</c-Inner></c-Holder>"
    page_template = f"<c-Inner>{fill}</c-Inner>" if route == "host-template" else holder_call
    page = type("Page", (Component,), {"citry": app, "template": page_template, "template_data": _data_method(data)})
    html = page().render().serialize()
    # `str(slot)` after the page render has finished.
    return str(kept[-1]) if route.endswith("kept-slot") else html


# Bodies that must render on every node route, and the text each must put on the page.
NODE_ALLOWED_BODIES = {
    "plain-text": ("plain text", "plain text"),
    "escaped-value": ("a {{ s }}", "a &lt;x&gt;"),
    "markup-without-a-tag": ("{{ plain_markup }}", "a &amp; b"),
    "authored-element": ('<circle id="c"></circle>', '<circle id="c"></circle>'),
    "nested-element": (
        '<g><c-element c-is="inner">{{ s }}<rect></rect></c-element></g>',
        "<g><g>&lt;x&gt;<rect></rect></g></g>",
    ),
    "c-for-around-an-element": ('<c-for each="i in items"><rect c-id="i"></rect></c-for>', '<rect id="2"></rect>'),
}

# Bodies that must be refused on every node route: the body, the caller's
# slot fill, and what the error names, which shows the check read the body
# and not the element's own tags.
NODE_REFUSED_BODIES = {
    "markup-value": ("{{ m }}", "", "a Markup value"),
    "html-object": ("{{ obj }}", "", "a Markup value"),
    "markup-in-c-if": ('<c-if cond="yes"><g>{{ m }}</g></c-if>', "", "a Markup value"),
    "markup-in-nested-element": ('<c-element c-is="inner">{{ m }}</c-element>', "", "a Markup value"),
    "child-component": ("<c-Kid />", "", "a child component"),
    "script": ('<script>var a = "{{ s }}";</script>', "", "a <script> element"),
    "slot-with-a-text-fill": ("<c-slot />", "fill text", "slot content"),
    "slot-with-a-markup-fill": ("<c-slot />", "{{ m }}", "slot content"),
}


@pytest.mark.parametrize("route", NODE_ROUTES)
@pytest.mark.parametrize(("body", "expected"), NODE_ALLOWED_BODIES.values(), ids=NODE_ALLOWED_BODIES)
@pytest.mark.parametrize("tag", ["svg", "MATH"])
def test_node_routes_render_what_the_template_wrote_under_a_data_chosen_foreign_tag(
    tag: str, body: str, expected: str, route: str
) -> None:
    html = _render_on_node_route(route, body, {**DATA, "t": tag})

    assert re.search(rf"<{tag}[ >]", html)
    assert expected in html
    assert f"</{tag}>" in html


@pytest.mark.parametrize("route", NODE_ROUTES)
@pytest.mark.parametrize(("body", "fill", "what"), NODE_REFUSED_BODIES.values(), ids=NODE_REFUSED_BODIES)
@pytest.mark.parametrize("tag", ["svg", "MATH"])
def test_node_routes_refuse_trusted_html_under_a_data_chosen_foreign_tag(
    tag: str, body: str, fill: str, what: str, route: str
) -> None:
    with pytest.raises(ValueError, match=REFUSAL) as error:
        _render_on_node_route(route, body, {**DATA, "t": tag}, fill)

    assert f"its body holds {what}" in str(error.value)


@pytest.mark.parametrize("route", NODE_ROUTES)
def test_node_routes_still_allow_markup_under_a_data_chosen_div(route: str) -> None:
    # Control for the refusals above: the same Markup body under `div`.
    html = _render_on_node_route(route, "{{ m }}", {**DATA, "t": "div"})

    assert str(STYLE_HTML) in html


# The browser runtime repeats the server's tag lists, so a definition that
# got past the server is still refused. The two copies must not drift apart.
_CLIENT_JS = Path(citry.__file__).parent / "_vue" / "client.js"


def _client_tag_set(name: str) -> frozenset[str]:
    """Read the `new Set([...])` literal that `client.js` assigns to `name`."""
    source = _CLIENT_JS.read_text(encoding="utf-8")
    match = re.search(rf"const {name} = new Set\(\[(.*?)\]\)", source, re.DOTALL)
    assert match is not None, f"client.js has no {name} set"
    return frozenset(re.findall(r'"([^"]+)"', match.group(1)))


def test_the_browser_runtime_lists_the_same_refused_tags_as_the_server() -> None:
    assert _client_tag_set("REFUSED_DYNAMIC_ELEMENT_TAGS") == html_util._REFUSED_DYNAMIC_ELEMENT_TAGS


def test_the_browser_runtime_lists_the_same_foreign_content_tags_as_the_server() -> None:
    client_tags = _client_tag_set("FOREIGN_CONTENT_TAGS")

    assert client_tags == html_util.FOREIGN_CONTENT_TAGS
    # The two roots that start foreign content are always on the list.
    assert {"svg", "math"} <= client_tags


@pytest.mark.parametrize("path", ["static", "vue"])
@pytest.mark.parametrize("key", ["is", "Is", "IS"])
@pytest.mark.parametrize("tag", ["script", "iframe", "base", "style", "noscript"])
def test_an_is_key_from_data_naming_a_refused_tag_is_refused(tag: str, key: str, path: str) -> None:
    # The tag can come from the `c-bind` mapping rather than from `c-is`, so that route needs the tag check too.
    with pytest.raises(ValueError, match="cannot render a <"):
        _render(path, '<c-element c-bind="battrs">x</c-element>', {"battrs": {key: tag}})
