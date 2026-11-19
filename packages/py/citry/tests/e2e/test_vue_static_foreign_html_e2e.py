"""
HTML that Citry did not compile, inside a Vue app, in a real browser.

A template with foreign spans (tags another engine renders, such as Django's
`{% %}` tags) writes plain HTML. Inside a Vue app that HTML becomes one
static node: Vue adopts the server's nodes when it hydrates, never compiles
the HTML, and keeps working when an Events handler renders the component
again.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from citry import Citry, Component, Extension, ForeignSpan, ForeignSpanSet
from citry._vue.serialization import hydration_admission
from citry.ext.events.renderers import dispatcher_for
from citry.nodes import ForeignNode

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e

# What each foreign span renders to. The Vue syntax would run, or show 49,
# if Vue compiled the HTML.
_FOREIGN_HTML = {
    "{% fill %}": (
        '<p id="fill">{{ 7*7 }} <b id="directive" v-html="\'<i id=injected>x</i>\'"'
        ' @click="globalThis.__ran = true" :title="1">kept</b></p>'
    ),
    "{% link %}": '<a id="link" href="/home">Home &amp; away</a>',
}


class _Foreign(Extension):
    name = "e2e_static_foreign_html"

    def on_template_foreign_spans(self, ctx: Any) -> ForeignSpanSet:
        content = ctx.content.encode()
        return ForeignSpanSet(
            tuple(
                ForeignSpan(match.start(), match.end(), may_control_body=True)
                for match in re.finditer(rb"\{%.*?%\}", content)
            )
        )

    def on_template_foreign_compiled(self, ctx: Any) -> None:
        ctx.nodes[:] = [_FOREIGN_HTML[node.text] if isinstance(node, ForeignNode) else node for node in ctx.nodes]
        ctx.mark_resolved(*ctx.claims)


def test_static_foreign_html_hydrates_and_survives_an_events_render(
    page: Any, serve_live: Any, wait_for_citry_ready: Any
) -> None:
    engine = Citry(
        secret="static-foreign-html-e2e-secret",  # noqa: S106
        autodiscover=False,
        extensions=[_Foreign],
    )
    engine.set_mounted_prefix("/citry")

    class StaticLink(Component):
        citry = engine
        template = """
<span class="link">{% link %}</span>
"""

    class Box(Component):
        citry = engine

        class Kwargs:
            n: int = 0

        class State(Kwargs):
            pass

        class Events:
            def inc(self, state: Any) -> Any:
                return Box(n=state.n + 1)

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"n": kwargs.n}

        template = """
<section id="box">
  <button id="inc" @c-click="inc">{{ n }}</button>
  <c-slot />
  <c-static-link />
</section>
"""

    class Page(Component):
        citry = engine
        template = """
<c-box>{% fill %}</c-box>
"""

    assert StaticLink
    dispatcher_for(engine)
    faults: list[str] = []
    warnings: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: warnings.append(message.text) if message.type == "warning" else None)
    rendered = Page().render()
    html = rendered.serialize()
    assert '"hydrate":true' in html
    admission = hydration_admission(rendered)
    assert admission is not None
    assert admission.declines == ()

    base = serve_live(engine, html, "")
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    page.add_init_script(
        "document.addEventListener('DOMContentLoaded', () => {"
        " globalThis.__servedFill = document.querySelector('#fill');"
        " globalThis.__servedLink = document.querySelector('#link'); });"
    )
    page.goto(base + "/")
    wait_for_citry_ready()
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    report = page.evaluate("window.__citryHydrationReport")
    assert report["mountError"] is None, report
    assert report["mismatchCount"] == 0, report
    assert report["replacedElementCount"] == 0, report

    # Vue adopted the server's nodes for both blocks.
    assert page.evaluate("globalThis.__servedFill === document.querySelector('#fill')") is True
    assert page.evaluate("globalThis.__servedLink === document.querySelector('#link')") is True
    # The Vue syntax in the HTML stayed text and plain attributes.
    assert page.text_content("#fill") == "{{ 7*7 }} kept"
    assert page.locator("#injected").count() == 0
    assert page.get_attribute("#directive", "v-html") == "'<i id=injected>x</i>'"
    page.click("#directive")
    assert page.evaluate("globalThis.__ran") is None

    # An Events render of the box renders the foreign child again. The
    # caller's fill is not part of that render, as for any caller fill.
    page.click("#inc")
    page.wait_for_function("document.querySelector('#inc').textContent === '1'")
    assert page.text_content("#link") == "Home & away"
    page.click("#inc")
    page.wait_for_function("document.querySelector('#inc').textContent === '2'")
    assert page.text_content("#link") == "Home & away"
    assert page.locator("#injected").count() == 0
    assert page.evaluate("globalThis.__ran") is None
    assert faults == []
    assert warnings == []
