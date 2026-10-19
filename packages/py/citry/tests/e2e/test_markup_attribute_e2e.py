"""
What the browser reads from a ``Markup`` value written into an HTML attribute.

``Markup`` vouches for HTML, not for attribute text, so Citry escapes it in an
attribute on every page. A static page and an interactive page give the
browser the same attribute value, and a quote in the value cannot end the
attribute and add another one.
"""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component, Markup

pytest.importorskip("playwright.sync_api")

# A value that would add an onmouseover attribute if Citry wrote it raw.
VALUE = Markup('a" onmouseover="window.__pwned = 1" data-x="&amp; <i> &copy=2')
# What the browser reads from that HTML: entities decoded, the rest as typed.
READ = 'a" onmouseover="window.__pwned = 1" data-x="& <i> &copy=2'


def _page(*, interactive: bool) -> type[Component]:
    engine = Citry(secret="markup-attribute-e2e-secret", autodiscover=False)  # noqa: S106 - test signing key
    # Serve the runtime from the route the serve_live fixture mounts.
    engine.set_mounted_prefix("/citry")

    class Target(Component):
        citry = engine
        template = """
          <div id="target" c-title="value">target</div>
          <span id="spread" c-bind="{'title': value}">spread</span>
        """

        def template_data(self, kwargs, slots):
            return {"value": VALUE}

    # A component with a Vue listener makes the page interactive.
    class Counter(Component):
        citry = engine
        template = """
          <button id="count" @click="count += 1">{{ count }}</button>
        """

        def template_data(self, kwargs, slots):
            return {"count": 0}

    counter = "<c-Counter />" if interactive else ""

    class Page(Component):
        citry = engine

    Page.template = f"""
      <!doctype html>
      <html>
        <head></head>
        <body>
          <c-Target />
          {counter}
        </body>
      </html>
    """
    return Page


def _assert_attribute_is_text(page: Any) -> None:
    for selector in ("#target", "#spread"):
        assert page.locator(selector).get_attribute("title") == READ
        assert page.locator(selector).get_attribute("onmouseover") is None
    page.locator("#target").hover()
    assert page.evaluate("window.__pwned") is None


@pytest.mark.e2e
def test_static_page_reads_markup_attribute_as_text(page: Any) -> None:
    page.set_content(str(_page(interactive=False)()))

    _assert_attribute_is_text(page)


@pytest.mark.e2e
def test_interactive_page_reads_the_same_attribute_text(page: Any, serve_live: Any) -> None:
    # Vue reports a hydration mismatch through the console, so any warning
    # or error there means the server and browser renders disagreed.
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "console",
        lambda message: faults.append(message.text) if message.type in {"error", "warning"} else None,
    )
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    root = _page(interactive=True)
    page.goto(serve_live(root.citry, root().render().serialize(), "") + "/")
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    report = page.evaluate("window.__citryHydrationReport")
    assert report["mountError"] is None, report
    assert report["mismatchCount"] == 0, report

    _assert_attribute_is_text(page)
    assert faults == []
