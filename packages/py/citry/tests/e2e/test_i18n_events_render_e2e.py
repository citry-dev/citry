"""Browser e2e: an Events Render of a region with a client i18n provider (#660)."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component, FormatRegistry, NumberFormat, NumberInput, PercentFormat
from citry.ext.events import actions

pytestmark = pytest.mark.e2e


def test_a_render_of_a_client_i18n_region_keeps_its_configuration(
    page: Any, serve_live: Any, wait_for_citry_ready: Any
) -> None:
    # Several profiles in each kind, so the formats and parsers hold more than one key and the
    # server's Render response can list them in another order than the page did.
    formats = FormatRegistry(
        number={
            "measurement": NumberFormat(),
            "scientific-edit": NumberFormat(input=NumberInput(notation="decimal_or_scientific")),
        },
        percent={"completion": PercentFormat()},
    )
    app = Citry(
        autodiscover=False,
        secret="s" * 40,
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US", "cs"), "formats": formats}},
    )
    app.set_mounted_prefix("/citry")

    calls: list[int] = []

    class Region(Component):
        citry = app

        class Kwargs:
            count: int = 0

        class Events:
            def refresh(self) -> Any:
                calls.append(1)
                return actions.Render(Region(count=len(calls)))

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"count": kwargs.count}

        template = """
            <c-i18n
              c-client="True"
              locale="en-US"
              tag="main"
            >
              <button
                id="refresh"
                @c-click="refresh"
              >
                {{ count }}
              </button>
              <output
                id="number"
                v-text="$i18n.format.number('1234.5', { format: 'measurement' })"
              ></output>
            </c-i18n>
        """

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script(
        "window.__eventErrors = [];"
        "document.addEventListener('citry:events:error', (event) =>"
        " window.__eventErrors.push(String(event.detail?.error?.message ?? event.detail?.error)));"
    )
    page.set_default_timeout(5000)
    page.goto(serve_live(app, Region().render().serialize(), "") + "/")
    wait_for_citry_ready()
    for expected in ("1", "2"):
        page.click("#refresh")
        page.wait_for_function(
            f"() => document.querySelector('#refresh')?.textContent.trim() === '{expected}'"
            " || window.__eventErrors.length > 0"
        )
        assert page.evaluate("window.__eventErrors") == []
    assert page.locator("#number").text_content() == "1,234.5"
    assert errors == []
