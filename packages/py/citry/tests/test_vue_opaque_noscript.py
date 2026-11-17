"""
Tests for a `Markup` value that holds a `<noscript>` element, in a component with browser code.

Vue builds an opaque HTML block (a `Markup` value, or `<c-raw>`) by parsing it
inside a `<template>`. Chromium and WebKit parse there with scripting off, so
the markup inside a `<noscript>` becomes real elements that load and run once
Vue moves them into the page, while the page's own parse keeps that markup as
inert text. A `Markup` value is the trusted HTML that data can reach, so it is
refused on every Vue path: the first page render, the component cache, a loop,
and an Events `Render`. `<c-raw>` and `#c-ignore` contents are written in the
template, so they stay allowed. The static writer has no such block.
"""

from __future__ import annotations

import itertools
from types import SimpleNamespace
from typing import Any

import pytest
from markupsafe import Markup

from citry import Citry, Component
from citry._vue.events import default_events_producer
from citry.ext.events import actions
from citry.ext.events.renderers import VuePreparedRenderEncoder
from citry.ext.events.results import RenderEncodingContext

REFUSAL = "holds a <noscript> element"

# The image has no handler: the tests only need to see that Citry refuses the value.
NOSCRIPT_BLOCKS = {
    "lowercase": Markup("<noscript><img src=x></noscript>"),
    "uppercase": Markup("<NOSCRIPT><img src=x></NOSCRIPT>"),
    "mixed-case": Markup("<NoScript><img src=x></NoScript>"),
    "nested-in-elements": Markup("<section><p>hi</p><div><noscript><img src=x></noscript></div></section>"),
    "beside-text": Markup("before <noscript>x</noscript> after"),
}

VUE_PATHS = ("vue", "cache-vue", "loop-vue")

_names = itertools.count()


def _template_data(values: dict[str, Any]) -> Any:
    def template_data(self, kwargs, slots):
        return dict(values)

    return template_data


def _component(path: str, body: str, values: dict[str, Any], app: Citry) -> type[Component]:
    """Build the component that holds `body`, wired for one render path."""
    if path == "loop-vue":
        # A <c-for> makes the same value render inside a loop.
        body = '<c-for each="n in one">' + body + "</c-for>"
        values = {**values, "one": [1]}
    attrs: dict[str, Any] = {"citry": app, "template": body, "template_data": _template_data(values)}
    if path != "static":
        # The `js` makes the component a Vue component, so it takes the Vue writer.
        attrs["js"] = """
            $component({});
        """
    if path == "cache-vue":
        attrs["Cache"] = type("Cache", (), {"enabled": True, "ttl": 300, "version": 1})
    return type(f"Inner{next(_names)}", (Component,), attrs)


def _app() -> Citry:
    app = Citry(autodiscover=False, secret="noscript-test-secret" * 2)
    app.set_mounted_prefix("/citry")
    app.initialize()
    return app


def _render_page(path: str, body: str, values: dict[str, Any]) -> str:
    """Render `body` as a child component on one path. A cached component renders twice."""
    app = _app()
    inner = _component(path, body, values, app)
    page = type(
        f"Page{next(_names)}",
        (Component,),
        {"citry": app, "template": f"<main><c-{inner.__name__} /></main>"},
    )
    html = page().render().serialize()
    if path == "cache-vue":
        # The second render replays the first from the cache.
        html = page().render().serialize()
    return html


def _render_events(body: str, values: dict[str, Any]) -> object:
    """Encode an Events `Render` of a Vue component that holds `body`, the way the server answers a handler."""
    app = _app()
    inner = _component("vue", body, values, app)
    producer = default_events_producer(app)
    # The headers name the page's Vue app, the component that called, and the app's revision, which
    # the default producer needs to build the prepared payload.
    context = RenderEncodingContext(
        app,
        None,
        SimpleNamespace(name="save"),
        "http",
        "vue-prepared/1",
        headers={
            "X-Citry-Vue-App": "app",
            "X-Citry-Vue-Occurrence": "citryOccurrenceTest1",
            "X-Citry-Vue-Revision": "0",
        },
    )
    return VuePreparedRenderEncoder(producer).encode(actions.Render(inner()), "render:old", context)


@pytest.mark.parametrize("path", VUE_PATHS)
@pytest.mark.parametrize("html", NOSCRIPT_BLOCKS.values(), ids=NOSCRIPT_BLOCKS)
def test_a_markup_value_with_noscript_is_refused_in_a_vue_component(html: Markup, path: str) -> None:
    # Each Vue path assembles the block itself, so each needs the refusal.
    with pytest.raises(ValueError, match=REFUSAL):
        _render_page(path, "<div>{{ m }}</div>", {"m": html})


@pytest.mark.parametrize("html", NOSCRIPT_BLOCKS.values(), ids=NOSCRIPT_BLOCKS)
def test_an_events_render_refuses_a_markup_value_with_noscript(html: Markup) -> None:
    # An Events response builds its blocks after the page has loaded, through the same Vue writer.
    with pytest.raises(ValueError, match=REFUSAL):
        _render_events("<div>{{ m }}</div>", {"m": html})


def test_an_events_render_without_noscript_encodes() -> None:
    # Control for the refusals above: the same Render with an ordinary Markup value works.
    encoded = _render_events("<div>{{ m }}</div>", {"m": Markup("<b>bold</b>")})

    assert encoded["renderer"] == "vue-prepared/1"  # type: ignore[index]


def test_the_static_writer_keeps_a_markup_value_with_noscript() -> None:
    # Control: a component without browser code writes the value into the page as is, which a
    # <noscript> in the page's own parse keeps inert.
    html = _render_page("static", "<div>{{ m }}</div>", {"m": NOSCRIPT_BLOCKS["lowercase"]})

    assert "<noscript><img src=x></noscript>" in html


@pytest.mark.parametrize("path", VUE_PATHS)
@pytest.mark.parametrize(
    "html",
    [
        pytest.param(Markup('<b title="<noscript>">x</b>'), id="noscript-in-an-attribute-value"),
        pytest.param(Markup("<b>noscript</b>"), id="noscript-as-text"),
        pytest.param(Markup("<!-- <noscript> --><i>x</i>"), id="noscript-in-a-comment"),
    ],
)
def test_a_markup_value_that_only_mentions_noscript_is_still_allowed(html: Markup, path: str) -> None:
    # The refusal reads the markup as the browser does: only an element counts, not the word.
    _render_page(path, "<div>{{ m }}</div>", {"m": html})


@pytest.mark.parametrize("path", VUE_PATHS)
@pytest.mark.parametrize(
    "body",
    [
        pytest.param("<div><c-raw><noscript>x</noscript></c-raw></div>", id="c-raw"),
        pytest.param("<div #c-ignore><noscript>x</noscript></div>", id="c-ignore"),
    ],
)
def test_noscript_written_in_the_template_is_allowed_in_a_vue_component(body: str, path: str) -> None:
    # Only the template author writes `<c-raw>` and `#c-ignore` contents, so they are author-only by design.
    _render_page(path, body, {})


@pytest.mark.parametrize("path", VUE_PATHS)
@pytest.mark.parametrize(
    "body",
    ["<div #c-ignore>{{ m }}</div>", "<div v-pre>{{ m }}</div>"],
    ids=["c-ignore", "v-pre"],
)
def test_a_markup_value_inside_kept_contents_is_refused(body: str, path: str) -> None:
    # The kept contents become one block written in the template, so the
    # Markup value inside is checked on its own before it joins the block.
    with pytest.raises(ValueError, match=REFUSAL):
        _render_page(path, body, {"m": NOSCRIPT_BLOCKS["lowercase"]})


def test_an_events_render_refuses_a_markup_value_inside_kept_contents() -> None:
    with pytest.raises(ValueError, match=REFUSAL):
        _render_events("<div #c-ignore>{{ m }}</div>", {"m": NOSCRIPT_BLOCKS["lowercase"]})
