"""Exercise production i18n payloads in a real browser."""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component

pytest.importorskip("pytest_playwright")

pytestmark = pytest.mark.e2e


def test_serialized_client_provider_delivers_its_message_to_the_live_i18n_runtime(page: Any, serve_live: Any) -> None:
    engine = Citry(
        autodiscover=False,
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )
    engine.set_mounted_prefix("/citry")

    class Page(Component):
        citry = engine
        template = (
            '<c-i18n c-client="True" tag="main"><output id="title" v-text="$i18n.tr(\'title\')"></output></c-i18n>'
        )
        messages = "title = Client title"

    page_errors: list[str] = []
    console_errors: list[str] = []
    page.add_init_script(
        "document.addEventListener('citry:ready', event => ((window.__citryReady ??= []).push(event.detail.appId)));"
    )
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.goto(serve_live(engine, Page().render().serialize(), "") + "/")

    page.wait_for_function("window.__citryReady?.length === 1")
    page.wait_for_function("document.querySelector('#title')?.textContent === 'Client title'")
    assert page.locator("#title").text_content() == "Client title"
    assert page.evaluate("() => CitryStable._apps.size") == 1
    assert page_errors == []
    assert console_errors == []
