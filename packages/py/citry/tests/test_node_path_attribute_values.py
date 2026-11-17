"""
Tests for rendered markup written into an HTML attribute on the node path.

A `CitryRender` is the result of rendering markup, such as the nested template
in `c-title="<>{{ value }}</>"` or a component input that holds one. Written
into an HTML attribute, its HTML must be escaped as attribute text, so a `"`
from `Markup` or a Python slot inside it cannot end the attribute.

The node path is the set of node classes in `citry.nodes` that render a
template compiled without the capture step. Each test renders the same markup
on the ordinary path and on a route that reaches the node path, and checks
that both write the same attribute:

- an extension that claims part of the template as another template language
  (a foreign span), as an extension that embeds Django template syntax does;
- `str(slot)` on a fill slot that a component kept after its render;
- a fill slot rendered in a worker thread, which does not carry the render's
  context variables;
- a kept slot whose classes already rendered once, when the element sits inside
  a nested template that a component receives as an input.
"""

from __future__ import annotations

import concurrent.futures
from html.parser import HTMLParser

import pytest

from citry import Citry, Component, Extension, ForeignSpan, ForeignSpanSet, Markup, Slot
from citry.nodes import ElementAttrsNode, ForeignNode

# A `"` here ends the attribute if the node path writes the value unescaped,
# and the rest becomes an `onmouseover` attribute.
_BREAKOUT = 'x" onmouseover="alert(1)" y="'
_BREAKOUT_MARKUP = Markup('x" onmouseover="alert(1)" y="')
# Sanitizer output: the quoted `title` is harmless between tags, but its quotes
# would end the outer attribute if written unescaped.
_SANITIZED = '<a title="x onmouseover=alert(1) y">t</a>'
_SANITIZED_MARKUP = Markup('<a title="x onmouseover=alert(1) y">t</a>')

_HOST_TAG = "{% host %}"


class _HostSpans(Extension):
    """Claim `{% host %}` as a foreign span, as an extension for another template language does."""

    name = "test_node_path_host_spans"

    def on_template_foreign_spans(self, ctx):
        start = ctx.content.encode().find(_HOST_TAG.encode())
        if start < 0:
            return None
        return ForeignSpanSet((ForeignSpan(start, start + len(_HOST_TAG)),))

    def on_template_foreign_compiled(self, ctx):
        # The host engine would render its own tag here; the test drops it.
        ctx.nodes[:] = ["" if isinstance(item, ForeignNode) else item for item in ctx.nodes]
        ctx.mark_resolved(*ctx.claims)


def _target_attributes(rendered: str) -> dict[str, str | None]:
    """Return the attributes of the element with `id="t"`, as a browser's HTML parser reads them."""

    class TargetParser(HTMLParser):
        found: dict[str, str | None] | None = None

        def handle_starttag(self, tag, attrs):
            if self.found is None and ("id", "t") in attrs:
                self.found = dict(attrs)

    parser = TargetParser(convert_charrefs=True)
    parser.feed(rendered)
    assert parser.found is not None, rendered
    return {key: value for key, value in parser.found.items() if not key.startswith("data-cid-")}


def _render(route, template, data, *, setup=None, messages=None, citry_kwargs=None):
    """
    Render `template` as the body of a fresh component `Inner` through `route`; return the HTML.

    Every call makes a new `Citry` and new classes, so no class has rendered
    before, which is the state a process is in after it starts.
    """
    app = Citry(extensions=[_HostSpans] if route == "foreign-span" else [], **(citry_kwargs or {}))
    if setup is not None:
        setup(app)

    def template_data(self, kwargs, slots):
        return dict(data)

    members = {
        "citry": app,
        "template": (_HOST_TAG if route == "foreign-span" else "") + template,
        "template_data": template_data,
    }
    if messages is not None:
        members["messages"] = messages
    Inner = type("Inner", (Component,), members)
    kept: list[Slot] = []

    class Holder(Component):
        citry = app
        template = """
            <section>{{ printed }}</section>
        """

        def template_data(self, kwargs, slots):
            if route == "worker-thread":
                # A plain executor does not copy context variables into the worker.
                with concurrent.futures.ThreadPoolExecutor(1) as pool:
                    printed = pool.submit(str, slots["default"]).result()
                return {"printed": Markup(printed)}  # noqa: S704 - Citry rendered and escaped it
            kept.append(slots["default"])
            return {"printed": ""}

    class Page(Component):
        citry = app
        template = """
            <c-Holder><c-Inner /></c-Holder>
        """

    if route in {"capture", "foreign-span"}:
        return Inner().render().serialize()
    if route == "kept-slot-warm":
        # Both classes render once normally first, so they hold the compiled
        # form that the ordinary path uses.
        Inner().render().serialize()
        Page().render().serialize()
        kept.clear()
    html = Page().render().serialize()
    return str(kept[-1]) if kept else html


_NODE_ROUTES = ["foreign-span", "kept-slot", "worker-thread"]


@pytest.fixture
def node_path_calls(monkeypatch):
    """Record each render that formats attributes on a plain node-path element, so a test can show it ran there."""
    calls: list[str] = []
    original = ElementAttrsNode._format

    def recording_format(self, resolved, context, *, validate_keys=True):
        if type(self) is ElementAttrsNode:
            calls.append(self.tag_name)
        return original(self, resolved, context, validate_keys=validate_keys)

    monkeypatch.setattr(ElementAttrsNode, "_format", recording_format)
    return calls


def _assert_same_attribute(route, template, data, attr="title", **kwargs):
    """Render on the ordinary path and on `route`; both must give the target the same attributes."""
    ordinary = _target_attributes(_render("capture", template, data, **kwargs))
    node = _target_attributes(_render(route, template, data, **kwargs))
    assert "onmouseover" not in node
    assert node == ordinary
    assert attr in node
    return node


class TestRoutesReachingTheNodePath:
    """Each route writes the markup as escaped attribute text, as the ordinary path does."""

    @pytest.mark.parametrize("route", [*_NODE_ROUTES, "kept-slot-warm"])
    def test_markup_in_nested_template_stays_in_its_attribute(self, route, node_path_calls):
        # The warm route needs the element inside a nested template that a
        # component receives as an input; the others use a plain element.
        def setup(app):
            class Box(Component):
                citry = app
                template = """
                    <div>{{ body }}</div>
                """

                def template_data(self, kwargs, slots):
                    return {"body": kwargs["body"]}

        template = (
            """<c-Box c-body="<><span id='t' c-title='<>{{ v }}</>'>i</span></>" />"""
            if route == "kept-slot-warm"
            else '<div id="t" c-title="<>{{ v }}</>">x</div>'
        )

        node = _assert_same_attribute(route, template, {"v": _BREAKOUT_MARKUP}, setup=setup)

        assert node["title"] == _BREAKOUT
        # Shows the route really rendered the element on the node path.
        assert node_path_calls

    def test_host_template_extension_with_sanitizer_output(self, node_path_calls):
        # The shape an app using an extension for Django template syntax has:
        # sanitized HTML, marked safe, passed into a nested-template attribute.
        node = _assert_same_attribute(
            "foreign-span",
            '<div id="t" c-title="<>{{ v }}</>">x</div>',
            {"v": _SANITIZED_MARKUP},
        )

        assert node["title"] == _SANITIZED
        assert node_path_calls


def _receiver(template):
    """Return a `setup` that defines `Leaf`, which writes its input `r` into the given template."""

    def setup(app):
        class Leaf(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"r": kwargs["r"]}

        Leaf.template = template

    return setup


_I18N = {"extensions_defaults": {"i18n": {"source_locale": "en-US", "locales": ("en-US",)}}}


class TestValueKindsOnTheNodePath:
    """Every way a `CitryRender` reaches a plain element's attribute, on the extension-free kept-slot route."""

    @pytest.mark.parametrize(
        ("template", "data", "kwargs"),
        [
            pytest.param(
                '<div id="t" c-title="<>{{ v }}</>">x</div>',
                {"v": _BREAKOUT_MARKUP},
                {},
                id="nested-markup",
            ),
            pytest.param(
                '<div id="t" c-title="<>{{ v }}</>">x</div>', {"v": _SANITIZED_MARKUP}, {}, id="nested-sanitized"
            ),
            pytest.param(
                '<div id="t" c-title="<>{{ s() }}</>">x</div>',
                {"s": Slot(_BREAKOUT_MARKUP)},
                {},
                id="nested-python-slot",
            ),
            pytest.param(
                '<c-Leaf c-r="<>{{ v }}</>" />',
                {"v": _BREAKOUT_MARKUP},
                {"setup": _receiver('<div id="t" c-title="r">x</div>')},
                id="component-input-in-c-attribute",
            ),
            pytest.param(
                '<c-Leaf c-r="<>{{ v }}</>" />',
                {"v": _BREAKOUT_MARKUP},
                {"setup": _receiver("""<div id="t" c-bind="{'title': r}">x</div>""")},
                id="component-input-in-c-bind",
            ),
            pytest.param(
                '<c-element is="div" id="t" c-title="<>{{ v }}</>">x</c-element>',
                {"v": _BREAKOUT_MARKUP},
                {},
                id="c-element-static-is",
            ),
            pytest.param(
                '<svg><a id="t" c-title="<>{{ v }}</>">x</a></svg>', {"v": _BREAKOUT_MARKUP}, {}, id="svg-element"
            ),
            pytest.param(
                """
                <div
                  id="t"
                  c-title="<>{{ v }}</>"
                  c-aria-label="tr('save')"
                  $c-tr:save[aria-label]
                >x</div>
                """,
                {"v": _BREAKOUT_MARKUP},
                {"citry_kwargs": _I18N, "messages": "save = Save"},
                id="translation-binding",
            ),
        ],
    )
    def test_value_is_escaped_as_attribute_text(self, template, data, kwargs):
        node = _assert_same_attribute("kept-slot", template, data, **kwargs)

        assert node["title"] in {_BREAKOUT, _SANITIZED}


def _child(app):
    class Child(Component):
        citry = app
        template = """
            <b>child</b>
        """


class TestComponentsInsideTheMarkup:
    """A component inside rendered markup works where the docs show it, on every route."""

    @pytest.mark.parametrize("route", ["capture", *_NODE_ROUTES])
    def test_markup_input_printed_as_content_renders_its_component(self, route):
        # The documented use: a component input given as `<>...</>` and
        # printed with `{{ }}`. The component inside it renders on every route.
        def setup(app):
            _child(app)

            class Card(Component):
                citry = app
                template = """
                    <article id="t" title="card">{{ footer }}</article>
                """

                def template_data(self, kwargs, slots):
                    return {"footer": kwargs["footer"]}

        html = _render(route, '<c-Card c-footer="<><c-Child /></>" />', {}, setup=setup)

        assert "<b" in html
        assert "child</b>" in html

    @pytest.mark.parametrize("route", _NODE_ROUTES)
    def test_component_inside_an_attribute_value_raises_as_on_the_ordinary_path(self, route):
        # An attribute holds text, so a component inside one has no place to
        # render; the ordinary path refuses it, and every route must too.
        template = '<div id="t" c-title="<><c-Child /></>">x</div>'
        with pytest.raises(RuntimeError, match="unresolved DeferredComponent") as ordinary:
            _render("capture", template, {}, setup=_child)
        with pytest.raises(RuntimeError, match="unresolved DeferredComponent") as node:
            _render(route, template, {}, setup=_child)

        assert type(node.value) is type(ordinary.value)
