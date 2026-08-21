"""Browser coverage for static-first inline Citry examples."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

_WELCOME_SOURCE = Path(__file__).parents[2] / "live_snippets" / "welcome.py"
_ACTIVE_PREVIEW = ".citry-live-code__preview:not(.citry-playground__preview--candidate)"


def test_inline_example_loads_lazily_runs_events_and_recovers_a_draft(
    page: Any,
    docs_site_url: str,
) -> None:
    requests: list[str] = []
    page.on("request", lambda request: requests.append(request.url))
    page.goto(docs_site_url + "/examples/", wait_until="networkidle")

    root = page.locator("[data-citry-live-code]")
    static_source = root.locator("[data-live-static] .highlight")
    expect(root).to_be_visible()
    assert static_source.text_content() == _WELCOME_SOURCE.read_text(encoding="utf-8")
    assert root.locator(".cm-editor").count() == 0
    assert root.locator("iframe").count() == 0
    assert not any("live_code_runtime.js" in url for url in requests)
    assert not any("worker.js" in url for url in requests)
    assert not any("pyodide" in url for url in requests)

    root.locator("[data-live-activate]").click()
    expect(root.locator(".cm-editor")).to_be_attached(timeout=15_000)
    assert any("live_code_runtime.js" in url for url in requests)
    expect(root.locator("iframe")).to_be_attached()
    assert set(root.locator("iframe").get_attribute("sandbox").split()) == {"allow-forms", "allow-scripts"}

    card = root.frame_locator(_ACTIVE_PREVIEW).locator(".welcome-card")
    expect(card).to_contain_text("Welcome, Ada Lovelace.", timeout=120_000)
    expect(root.locator('[data-live-tab="code"]')).to_have_attribute("aria-selected", "true")
    expect(root.locator('[data-live-panel="code"]')).to_be_visible()
    expect(root.locator('[data-live-panel="result"]')).to_be_hidden()
    announcer_style = root.locator("[data-live-announcer]").evaluate(
        """element => {
          const style = getComputedStyle(element);
          return {
            clipPath: style.clipPath,
            height: style.height,
            overflow: style.overflow,
            position: style.position,
            width: style.width,
          };
        }"""
    )
    assert announcer_style == {
        "clipPath": "inset(50%)",
        "height": "1px",
        "overflow": "hidden",
        "position": "absolute",
        "width": "1px",
    }
    root.locator('[data-live-tab="result"]').click()
    card.locator("button").click()
    expect(card.locator("output")).to_have_text("1", timeout=10_000)

    root.locator('[data-live-tab="code"]').click()
    root.locator('[data-live-tab="result"]').click()
    expect(card.locator("output")).to_have_text("1")
    root.locator("[data-live-run]").click()
    expect(root.locator("[data-live-run]")).to_be_enabled(timeout=120_000)
    expect(root.locator('[data-live-tab="result"]')).to_have_attribute("aria-selected", "true")
    expect(root.locator('[data-live-panel="result"]')).to_be_visible()
    expect(card.locator("output")).to_have_text("0")
    root.locator('[data-live-tab="code"]').click()
    root.locator("[data-live-auto-run]").uncheck()
    editor = root.locator(".cm-content")
    editor.click()
    page.keyboard.press("ControlOrMeta+End")
    page.keyboard.insert_text("\n# saved draft")
    expect(editor).to_contain_text("saved draft")
    expect(root.locator("[data-live-stale]")).to_be_visible()
    root.locator('[data-live-tab="result"]').click()

    root.locator("[data-live-close]").click()
    expect(static_source).to_be_visible()
    expect(root.locator("iframe")).to_have_count(0)
    expect(root.locator("[data-live-draft]")).to_be_visible()
    expect(root.locator("[data-live-activate]")).to_have_text("Resume live")
    expect(root.locator("[data-live-activate]")).to_be_focused()

    root.locator("[data-live-activate]").click()
    expect(root.locator('[data-live-tab="result"]')).to_have_attribute("aria-selected", "true")
    expect(root.locator('[data-live-panel="result"]')).to_be_visible()
    expect(root.locator('[data-live-tab="result"]')).to_be_focused()
    root.locator('[data-live-tab="code"]').click()
    root.locator(".cm-content").click()
    page.keyboard.press("ControlOrMeta+End")
    expect(root.locator(".cm-content")).to_contain_text("saved draft", timeout=15_000)
    root.locator('[data-live-tab="result"]').click()
    root.locator("[data-live-reset]").click()
    expect(root.locator('[data-live-tab="result"]')).to_have_attribute("aria-selected", "true")
    expect(root.locator('[data-live-panel="result"]')).to_be_visible()
    expect(root.locator('[data-live-panel="code"]')).to_be_hidden()
    root.locator('[data-live-tab="code"]').click()
    expect(root.locator(".cm-content")).not_to_contain_text("saved draft")
    expect(root.locator(".cm-content")).to_contain_text("class WelcomeCard")
    root.locator("[data-live-close]").click()
    expect(root.locator("[data-live-activate]")).to_have_text("Try live")


def test_page_without_live_code_emits_no_inline_assets(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/about/philosophy/", wait_until="domcontentloaded")

    assert page.locator("[data-citry-live-code]").count() == 0
    assert page.locator('link[href$="/playground/live_code.css"]').count() == 0
    assert page.locator('script[src$="/playground/live_code.js"]').count() == 0


def test_multiple_inline_examples_share_one_active_browser_runtime(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/__tests__/live-code-multiple/", wait_until="domcontentloaded")
    blocks = page.locator("[data-citry-live-code]")
    expect(blocks).to_have_count(2)
    first = blocks.nth(0)
    second = blocks.nth(1)

    full_height = first.locator("[data-live-static] pre").evaluate(
        """element => ({
          clientHeight: element.clientHeight,
          maxHeight: getComputedStyle(element).maxHeight,
          scrollHeight: element.scrollHeight,
        })"""
    )
    default_height = second.locator("[data-live-static] pre").evaluate(
        """element => ({
          clientHeight: element.clientHeight,
          maxHeight: getComputedStyle(element).maxHeight,
          scrollHeight: element.scrollHeight,
        })"""
    )
    assert full_height["maxHeight"] == "none"
    assert full_height["scrollHeight"] == full_height["clientHeight"]
    assert default_height["maxHeight"] != "none"
    assert default_height["scrollHeight"] > default_height["clientHeight"]

    first.locator("[data-live-activate]").click()
    expect(first.locator(".cm-content")).to_be_attached(timeout=15_000)
    assert (
        first.locator(".citry-live-code__editor-shell").evaluate("element => element.clientHeight")
        < full_height["clientHeight"]
    )
    first.locator('[data-live-tab="result"]').click()
    assert (
        first.locator(".citry-live-code__preview-shell").evaluate("element => element.clientHeight")
        < full_height["clientHeight"]
    )
    first.locator('[data-live-tab="code"]').click()
    first.locator(".cm-content").click()
    page.keyboard.press("ControlOrMeta+End")
    page.keyboard.insert_text("\n# first draft")

    second.locator("[data-live-activate]").click()
    expect(second.locator(".cm-content")).to_be_attached(timeout=15_000)
    expect(first.locator("[data-live-activate]")).to_have_text("Resume live")
    expect(first.locator("[data-live-draft]")).to_be_visible()
    assert page.locator(".cm-editor").count() == 1
    assert page.locator(_ACTIVE_PREVIEW).count() == 1

    first.locator("[data-live-activate]").click()
    first.locator('[data-live-tab="code"]').click()
    first.locator(".cm-content").click()
    page.keyboard.press("ControlOrMeta+End")
    expect(first.locator(".cm-content")).to_contain_text("first draft")
    assert page.locator(".cm-editor").count() == 1
    assert page.locator(_ACTIVE_PREVIEW).count() == 1
    expect(second.locator("[data-live-activate]")).to_have_text("Try live")


def test_incomplete_inline_example_can_be_edited_into_a_renderable_module(
    page: Any,
    docs_site_url: str,
) -> None:
    page.goto(docs_site_url + "/__tests__/live-code-incomplete/", wait_until="domcontentloaded")
    root = page.locator("[data-citry-live-code]")

    expect(root.locator("[data-live-static]")).to_contain_text("class DraftCard")
    root.locator("[data-live-activate]").click()
    expect(root.locator(".cm-content")).to_be_attached(timeout=15_000)
    expect(root.locator("[data-live-python-summary]")).to_have_text(
        "No preview value was found. End the module with HTML, a CitryElement, a ComponentLike, or a CitryRender.",
        timeout=120_000,
    )

    editor = root.locator(".cm-content")
    editor.click()
    page.keyboard.press("ControlOrMeta+End")
    page.keyboard.insert_text('\n\nDraftCard(text="Finish the example")\n')

    expect(root.locator("[data-live-status]")).to_contain_text("Rendered in", timeout=120_000)
    preview = root.frame_locator(_ACTIVE_PREVIEW)
    expect(preview.locator(".draft-card")).to_contain_text("Finish the example")
    expect(root.locator("[data-live-python-diagnostic]")).to_be_hidden()


def test_getting_started_live_examples_run_the_behavior_the_lesson_describes(
    page: Any,
    docs_site_url: str,
) -> None:
    page.goto(docs_site_url + "/getting-started/browser-interactivity/", wait_until="domcontentloaded")
    runtime_version = page.evaluate(
        "async () => (await (await fetch('/static/playground/runtime.json')).json()).citry.version"
    )
    assert runtime_version == "0.4.2"
    examples = page.locator("[data-citry-live-code]")
    expect(examples).to_have_count(1)

    counters = examples.nth(0)
    counters.locator("[data-live-activate]").click()
    expect(counters.locator(".cm-content")).to_be_attached(timeout=15_000)
    expect(counters.locator("[data-live-status]")).to_contain_text("Rendered in", timeout=120_000)
    counter_preview = counters.frame_locator(_ACTIVE_PREVIEW)
    ada = counter_preview.locator(".counter").nth(0)
    grace = counter_preview.locator(".counter").nth(1)
    expect(ada).to_be_attached()
    counters.locator('[data-live-tab="result"]').click()
    expect(ada).to_contain_text("Ada")
    expect(grace).to_contain_text("Grace")
    ada.click()
    expect(ada).to_contain_text("clicked 1 times")
    expect(grace).to_contain_text("clicked 0 times")

    page.goto(docs_site_url + "/getting-started/client-props-and-handlers/", wait_until="domcontentloaded")
    connected = page.locator("[data-citry-live-code]")
    connected.locator("[data-live-activate]").click()
    expect(connected.locator(".cm-content")).to_be_attached(timeout=15_000)
    expect(connected.locator("[data-live-status]")).to_contain_text("Rendered in", timeout=120_000)
    connected_preview = connected.frame_locator(_ACTIVE_PREVIEW)
    choice = connected_preview.locator(".choice-picker__value")
    expect(choice).to_have_text("Ocean")
    connected.locator('[data-live-tab="result"]').click()
    connected_preview.locator(".choice-button").click()
    expect(choice).to_have_text("Forest")


def test_inline_example_remains_useful_without_javascript(browser: Any, docs_site_url: str) -> None:
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    try:
        page.goto(docs_site_url + "/examples/", wait_until="domcontentloaded")
        root = page.locator("[data-citry-live-code]")
        expect(root.locator("[data-live-static]")).to_be_visible()
        expect(root.locator("[data-live-activate]")).to_be_hidden()
        assert root.locator("iframe").count() == 0
        assert "class WelcomeCard" in root.locator("[data-live-static]").text_content()
    finally:
        context.close()


def test_inline_runtime_activation_failure_keeps_source_and_retries(page: Any, docs_site_url: str) -> None:
    runtime_pattern = "**/static/playground/live_code_runtime.js?attempt=*"
    page.route(runtime_pattern, lambda route: route.abort())
    page.goto(docs_site_url + "/examples/", wait_until="domcontentloaded")
    root = page.locator("[data-citry-live-code]")

    root.locator("[data-live-activate]").click()
    expect(root.locator("[data-live-activate]")).to_have_text("Retry live")
    expect(root.locator("[data-live-static]")).to_be_visible()
    assert root.locator("iframe").count() == 0

    page.unroute(runtime_pattern)
    root.locator("[data-live-activate]").click()
    expect(root.locator(".cm-editor")).to_be_attached(timeout=15_000)
    root.locator("[data-live-close]").click()
    expect(root.locator("[data-live-static]")).to_be_visible()


def test_rapid_activation_restores_the_superseded_block(page: Any, docs_site_url: str) -> None:
    page.goto(docs_site_url + "/__tests__/live-code-multiple/", wait_until="domcontentloaded")
    blocks = page.locator("[data-citry-live-code]")

    page.evaluate(
        """() => {
          const buttons = [...document.querySelectorAll('[data-live-activate]')];
          buttons[0].click();
          buttons[1].click();
        }"""
    )

    expect(blocks.nth(1).locator(".cm-editor")).to_be_attached(timeout=15_000)
    first_button = blocks.nth(0).locator("[data-live-activate]")
    expect(first_button).to_have_text("Try live")
    expect(first_button).to_be_enabled()
    expect(first_button).to_be_visible()
    assert page.locator(".cm-editor").count() == 1
