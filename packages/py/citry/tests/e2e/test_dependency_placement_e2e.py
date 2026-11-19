"""
A browser must read an attribute value with end-tag text as text after Citry places its tags.

An interactive page writes ``<`` and ``>`` raw in attribute values. Citry
must place its CSS and JS at the page's real ``</head>`` and ``</body>``, so a
value such as ``X</head><img onerror=...>`` stays inside its attribute and the
handler never runs.
"""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component

pytest.importorskip("playwright.sync_api")

# Markup that sets window.__pwn if it ever becomes a real element.
PAYLOAD = "<img id=pwn src=x onerror=window.__pwn=1>"


def _serialize(value: str, *, route: str, shell: str) -> str:
    engine = Citry(autodiscover=False)
    engine.set_mounted_prefix("/citry")

    class Widget(Component):
        citry = engine
        # c-title writes the value on the server; :title binds it in Vue.
        template = (
            """
            <div id="target" c-title="value">x</div>
            """
            if route == "server"
            else """
            <div id="target" :title="value">x</div>
            """
        )
        css = """
            .a { color: red; }
        """

        def template_data(self, kwargs, slots):
            return {"value": value}

        def js_data(self, kwargs, slots):
            return {"value": value}

    class Page(Component):
        citry = engine
        template = shell

    return Page().render().serialize()


@pytest.mark.e2e
@pytest.mark.parametrize("decoy", ["</head>", "</body>"])
@pytest.mark.parametrize("route", ["server", "vue"])
@pytest.mark.parametrize(
    ("shell", "wrap"),
    [
        # A fragment the app puts into its own page.
        ("<c-Widget />", True),
        ("<!DOCTYPE html><HTML><HEAD></HEAD><BODY><c-Widget /></BODY></HTML>", False),
    ],
    ids=["fragment", "uppercase-document"],
)
def test_end_tag_text_in_an_attribute_stays_text(page: Any, decoy: str, route: str, shell: str, wrap: bool) -> None:
    value = f"X{decoy}Y{PAYLOAD}"
    html = _serialize(value, route=route, shell=shell)
    if wrap:
        html = f"<!DOCTYPE html><html><head></head><body>{html}</body></html>"
    # The runtime and stylesheet URLs are not served; only the markup matters.
    page.route("**/*", lambda route: route.fulfill(status=404, body=""))

    page.set_content(html)
    # An <img> with a missing source fires onerror right after it loads.
    page.wait_for_timeout(300)

    assert page.evaluate("window.__pwn") is None
    assert page.locator("#pwn").count() == 0
    assert page.locator("#target").get_attribute("title") == value
