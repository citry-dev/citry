"""Browser port of django-components' fragments example through Citry Events."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.events import actions, event

pytestmark = pytest.mark.e2e

READY = "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true"


def test_named_events_load_fragments_with_js_css_and_alpine(page: Any, serve_live: Any) -> None:
    """The three old client choices become named handlers with one fragment lifecycle."""
    engine = Citry(secret="e2e-secret")  # noqa: S106 - deterministic test signing key
    engine.set_mounted_prefix("/citry")

    class LoadedFragment(Component):
        citry = engine

        class Kwargs:
            kind: str

        def template_data(self, kwargs, slots):
            return {"kind": kwargs.kind}

        def js_data(self, kwargs, slots):
            return {"kind": kwargs.kind}

        template = """
          <section
            class="ported-fragment"
            x-data="{ activated: true }"
            c-data-kind="kind"
          >
            <strong>{{ kind }}</strong>
            <span class="alpine-status" x-text="activated ? 'Alpine ready' : 'waiting'"></span>
          </section>
        """

        js = """
          $component(({ els, data }) => {
            els[0].setAttribute("data-component-js", data.kind);
          });
        """

        css = """
          .ported-fragment {
            background-color: rgb(231, 241, 255);
          }
        """

    class FragmentLoader(Component):
        citry = engine

        class Events:
            @event(methods=("GET",))
            def plain(self):
                return actions.Render(LoadedFragment(kind="plain"), target="#fragment-target", swap="inner")

            @event(methods=("GET",))
            def alpine(self):
                return actions.Render(LoadedFragment(kind="alpine"), target="#fragment-target", swap="inner")

            @event(methods=("GET",))
            def htmx(self):
                return actions.Render(LoadedFragment(kind="htmx"), target="#fragment-target", swap="inner")

        template = """
          <nav>
            <button class="load-plain" @c-click="plain">Plain JS</button>
            <button class="load-alpine" @c-click="alpine">AlpineJS</button>
            <button class="load-htmx" @c-click="htmx">HTMX</button>
          </nav>
        """

    class Page(Component):
        citry = engine
        template = """
          <html>
            <head><title>Events fragments port</title></head>
            <body>
              <c-fragment-loader />
              <div id="fragment-target"></div>
            </body>
          </html>
        """

    messages: list[str] = []
    requests: list[Any] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    page.on("request", lambda request: requests.append(request) if "/ext/events/e/" in request.url else None)
    base = serve_live(engine, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)

    for kind in ("plain", "alpine", "htmx"):
        page.locator(f".load-{kind}").click()
        page.wait_for_function(
            "kind => document.querySelector('.ported-fragment')?.dataset.componentJs === kind",
            arg=kind,
        )
        fragment = page.locator(".ported-fragment")
        assert fragment.get_attribute("data-kind") == kind
        assert fragment.locator(".alpine-status").inner_text() == "Alpine ready"
        assert fragment.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(231, 241, 255)"

    assert [request.method for request in requests] == ["GET", "GET", "GET"]
    for request in requests:
        query = parse_qs(urlparse(request.url).query)
        assert query["_citry_caller_render_id"]
        assert query["_citry_send_sequence"]
    assert not [message for message in messages if message.startswith("error:")]
