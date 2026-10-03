"""
What the browser shows for content that ``Component.on_render`` returns on an interactive page.

A plain ``str`` is text and ``Markup`` is HTML, on the server and after Vue
takes over the page, so hydration finds the same nodes the server sent.
"""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component, Markup

pytest.importorskip("playwright.sync_api")

# User input that would run a script if Citry inserted it as HTML.
USER_INPUT = "<script>window.__pwned = 1</script><b>bold</b> & more"


def _page_with_replacement(value: object) -> type[Component]:
    engine = Citry(secret="on-render-e2e-secret", autodiscover=False)  # noqa: S106 - test signing key
    # Serve the runtime from the route the serve_live fixture mounts.
    engine.set_mounted_prefix("/citry")

    class Replaced(Component):
        citry = engine
        template = """
          <p>unused</p>
        """

        def on_render(self):
            result, _error = yield
            assert result is not None
            return value

    # A component with a Vue listener makes the page interactive.
    class Counter(Component):
        citry = engine
        template = """
          <button id="count" @click="count += 1">{{ count }}</button>
        """

        def template_data(self, kwargs, slots):
            return {"count": 0}

    class Page(Component):
        citry = engine
        template = """
          <!doctype html>
          <html>
            <head></head>
            <body>
              <div id="replaced"><c-Replaced /></div>
              <c-Counter />
            </body>
          </html>
        """

    return Page


def _open(page: Any, serve_live: Any, root: type[Component]) -> list[str]:
    # Vue reports a hydration mismatch through the console, so any warning
    # or error there means the server and browser renders disagreed.
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "console",
        lambda message: faults.append(message.text) if message.type in {"error", "warning"} else None,
    )
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    page.goto(serve_live(root.citry, root().render().serialize(), "") + "/")
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    report = page.evaluate("window.__citryHydrationReport")
    assert report["mountError"] is None, report
    assert report["mismatchCount"] == 0, report
    return faults


@pytest.mark.e2e
def test_plain_str_shows_as_text_after_hydration(page: Any, serve_live: Any) -> None:
    faults = _open(page, serve_live, _page_with_replacement(USER_INPUT))

    assert page.locator("#replaced").text_content().strip() == USER_INPUT
    assert page.locator("#replaced b").count() == 0
    assert page.evaluate("window.__pwned") is None
    assert faults == []


@pytest.mark.e2e
def test_markup_shows_as_html_after_hydration(page: Any, serve_live: Any) -> None:
    faults = _open(page, serve_live, _page_with_replacement(Markup("<b>bold</b>")))

    assert page.locator("#replaced b").text_content() == "bold"
    assert faults == []
