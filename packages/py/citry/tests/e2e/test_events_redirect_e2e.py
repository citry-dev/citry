"""A relative `actions.Redirect` lands on the same page with and without JavaScript."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.events import actions

pytestmark = pytest.mark.e2e

# The form page sits two folders deep with a query, so each relative form
# resolves somewhere different from the handler URL under /citry/ext/events/.
_PAGE_PATH = "/shop/list?x=1"

# The handler picks its URL by key so the test never redirects to raw
# request data.
_TARGETS = {
    "query": "?page=2",
    "sibling": "next",
    "parent": "../x",
    "absolute": "/abs",
    # Non-ASCII URLs go out percent-encoded in the 303 Location header.
    "unicode-path": "/café/ñ?q=ü#ß",
    "unicode-relative": "é?q=ü",
}


# Module level, so the handler's string annotation resolves.
class GoIn:
    to: str


def _redirect_page() -> tuple[Citry, str]:
    engine = Citry(secret="e2e-secret")  # noqa: S106 - deterministic test signing key
    # The page renders before serve_live mounts the routes, so name the prefix now.
    engine.set_mounted_prefix("/citry")

    class Jumper(Component):
        citry = engine

        class Events:
            def go(self, data: GoIn):
                return actions.Redirect(_TARGETS[data.to])

        def template_data(self, kwargs, slots):
            return {"go_url": self.events.url("go")}

        template = """
          <section>
            <form class="runtime-form" @c-submit.prevent="go">
              <select name="to">
                <option value="query">query</option>
                <option value="sibling">sibling</option>
                <option value="parent">parent</option>
                <option value="absolute">absolute</option>
                <option value="unicode-path">unicode-path</option>
                <option value="unicode-relative">unicode-relative</option>
              </select>
              <button type="submit">Go with JavaScript</button>
            </form>
            <form
              class="native-form"
              method="post"
              c-action="go_url"
            >
              <select name="to">
                <option value="query">query</option>
                <option value="sibling">sibling</option>
                <option value="parent">parent</option>
                <option value="absolute">absolute</option>
                <option value="unicode-path">unicode-path</option>
                <option value="unicode-relative">unicode-relative</option>
              </select>
              <button type="submit">Go without JavaScript</button>
            </form>
          </section>
        """

    class Page(Component):
        citry = engine
        template = """
          <html>
            <head><title>Redirect</title></head>
            <body><c-jumper /></body>
          </html>
        """

    return engine, str(Page())


@pytest.mark.parametrize(
    ("key", "landing"),
    [
        ("query", "/shop/list?page=2"),
        ("sibling", "/shop/next"),
        ("parent", "/x"),
        ("absolute", "/abs"),
        ("unicode-path", "/caf%C3%A9/%C3%B1?q=%C3%BC#%C3%9F"),
        ("unicode-relative", "/shop/%C3%A9?q=%C3%BC"),
    ],
)
def test_relative_redirect_lands_on_the_same_page_without_javascript(
    browser: Any,
    page: Any,
    serve_live: Any,
    wait_for_citry_ready: Any,
    key: str,
    landing: str,
) -> None:
    """The no-JS 303 resolves against the form's page, as `location.assign()` does."""
    engine, html = _redirect_page()
    # serve_live answers every path outside /citry with the page, so the
    # landing page loads too and its URL is what the test reads.
    base = serve_live(engine, html, "")

    # With JavaScript: the runtime posts the call and applies the redirect.
    page.goto(base + _PAGE_PATH)
    wait_for_citry_ready()
    page.select_option(".runtime-form select", key)
    page.click(".runtime-form button[type=submit]")
    page.wait_for_url(base + landing)

    # Without JavaScript: the browser posts the form and follows the 303.
    context = browser.new_context(java_script_enabled=False)
    try:
        no_js = context.new_page()
        no_js.goto(base + _PAGE_PATH)
        no_js.select_option(".native-form select", key)
        with no_js.expect_navigation():
            no_js.click(".native-form button[type=submit]")
        assert no_js.url == base + landing
        assert no_js.url == page.url
    finally:
        context.close()
