"""Browser evidence for Infinite Scroll requests and cleanup."""

# ruff: noqa: E501 - embedded templates and browser expressions remain readable

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component
from citry import citry as default_citry

pytestmark = pytest.mark.e2e


def _root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate repository root for Infinite Scroll browser tests.")


_SNIPPETS = _root() / "packages/py/citry_ui/citry_ui/components/cinfinite_scroll/snippets"
_PREVIEW_NAMES = tuple(sorted(path.stem for path in _SNIPPETS.glob("*.py") if path.stem != "__init__"))


class InfiniteScrollPreviewDocument(Component):
    citry = default_citry

    class Kwargs:
        title: str
        content: object

    class Slots:
        pass

    template = """
      <!doctype html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <title>{{ title }}</title>
          <c-css />
        </head>
        <body>
          <main>{{ content }}</main>
          <c-js />
        </body>
      </html>
    """

    def template_data(self, kwargs: Kwargs, _slots: Slots) -> dict[str, object]:
        return {"title": kwargs.title, "content": kwargs.content}


def _preview_document(name: str) -> str:
    # Family tests execute each shipped snippet without coupling docs tests to
    # the public page's authored example membership or order.
    module = importlib.import_module(f"citry_ui.components.cinfinite_scroll.snippets.{name}")
    return (
        InfiniteScrollPreviewDocument(
            title=name.replace("_", " ").title(),
            content=module.preview,
        )
        .render()
        .serialize()
    )


def _open_preview(page: Any, serve_citry_ui_live: Any, name: str) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    base = serve_citry_ui_live(default_citry, _preview_document(name))
    page.goto(base + "/", wait_until="networkidle")
    page.wait_for_selector("[data-citry-infinite-scroll-initialized]")
    return errors


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8"><title>Infinite Scroll evidence</title><c-css /></head>
          <body x-data>
            <form @submit.prevent="$store.more.submits.push($event.submitter.value)">
              <c-CInfiniteScroll id="native" aria_label="Feed" action_name="feed_action" c-auto="False"
                $c-props="{loading:$store.more.loading,error:$store.more.error,hasMore:$store.more.hasMore,onLoadMore:(detail)=>$store.more.requests.push(detail.reason)}">
                <ol><li>Result one</li></ol>
              </c-CInfiniteScroll>
            </form>
            <c-CInfiniteScroll id="automatic" aria_label="Automatic feed"
              $c-props="{error:$store.more.automaticError,onLoadMore:(detail)=>$store.more.automatic.push(detail.reason)}"><p>Visible result</p></c-CInfiniteScroll>
          </body></html>
        """
        js = "Alpine.store('more',{loading:false,error:false,hasMore:true,requests:[],automatic:[],automaticError:false,submits:[]});"

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector("#native[data-citry-infinite-scroll-initialized]")
    page.wait_for_selector("#automatic[data-citry-infinite-scroll-initialized]")
    return errors


def test_button_reactive_states_native_submit_and_cleanup(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#native")
    root.locator('[data-citry-ui-part="action"]').click()
    assert page.evaluate("Alpine.store('more').requests") == ["button"]
    assert page.evaluate("Alpine.store('more').submits") == ["load-more"]
    root.locator("ol").evaluate("list => list.append(document.createElement('li'))")
    page.wait_for_timeout(0)
    root.locator('[data-citry-ui-part="action"]').click()
    assert page.evaluate("Alpine.store('more').requests") == ["button", "button"]
    assert page.evaluate("Alpine.store('more').submits") == ["load-more", "load-more"]
    page.evaluate("Alpine.store('more').error=true")
    page.wait_for_function("document.querySelector('#native').hasAttribute('data-error')")
    root.locator('[data-citry-ui-part="action"]').click()
    assert page.evaluate("Alpine.store('more').requests") == ["button", "button", "retry"]
    page.evaluate("Alpine.store('more').loading=true")
    page.wait_for_function(
        "document.querySelector('#native [data-citry-ui-part=content]').getAttribute('aria-busy')==='true'"
    )
    assert root.locator('[data-citry-ui-part="action"]').is_hidden()
    page.evaluate("Object.assign(Alpine.store('more'),{loading:false,error:false,hasMore:false})")
    page.wait_for_function("document.querySelector('#native').hasAttribute('data-end')")
    root.evaluate("element => element.remove()")
    page.wait_for_timeout(30)
    assert errors == []


def test_intersection_environment_and_axe(page: Any) -> None:
    errors = _load(page)
    page.wait_for_function("Alpine.store('more').automatic.length > 0")
    assert page.evaluate("Alpine.store('more').automatic") == ["intersection"]
    page.evaluate("Alpine.store('more').automaticError=true")
    page.wait_for_function("document.querySelector('#automatic').hasAttribute('data-error')")
    page.wait_for_timeout(100)
    assert page.evaluate("Alpine.store('more').automatic") == ["intersection"]
    page.locator("#automatic [data-citry-ui-part=action]").click()
    assert page.evaluate("Alpine.store('more').automatic") == ["intersection", "retry"]
    page.emulate_media(forced_colors="active", reduced_motion="reduce")
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
    assert errors == []


def test_at_a_glance_loads_two_dummy_pages_without_navigating(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, "at_a_glance")
    root = page.locator('[data-citry-ui-part="infinite-scroll"]')
    action = root.locator('[data-citry-ui-part="action"]')
    activities = root.locator("li")
    initial_url = page.url
    assert activities.count() == 3

    action.click()
    page.wait_for_function("document.querySelectorAll('[data-citry-ui-part=content] li').length === 5")
    assert page.url == initial_url
    assert action.is_visible()

    action.click()
    page.wait_for_function("document.querySelectorAll('[data-citry-ui-part=content] li').length === 7")
    page.wait_for_function("document.querySelector('[data-citry-ui-part=infinite-scroll]').hasAttribute('data-end')")
    assert page.url == initial_url
    assert action.is_hidden()
    assert page.get_by_text("Collected the first responses").is_visible()
    assert errors == []


def test_automatic_preview_keeps_loading_each_time_its_feed_reaches_the_end(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, "automatic")
    root = page.locator('[data-citry-ui-part="infinite-scroll"]')
    assert root.locator("li").count() == 8
    page.wait_for_timeout(400)
    assert root.locator("li").count() == 8

    for expected_count in (12, 16, 20, 24):
        root.evaluate("element => { element.scrollTop = element.scrollHeight; }")
        page.wait_for_function(
            "expected => document.querySelectorAll('[data-citry-ui-part=content] li').length === expected",
            arg=expected_count,
        )
        page.wait_for_function(
            "document.querySelector('[data-citry-ui-part=content]').getAttribute('aria-busy') === 'false'"
        )
        page.wait_for_timeout(400)
        assert root.locator("li").count() == expected_count

    assert root.evaluate("element => element.hasAttribute('data-end')") is False
    action = root.locator('[data-citry-ui-part="action"]')
    assert action.is_visible()
    assert action.is_enabled()

    root.evaluate("element => { element.scrollTop = element.scrollHeight; }")
    page.wait_for_function("document.querySelectorAll('[data-citry-ui-part=content] li').length === 28")
    assert page.get_by_text("Search result 28").is_visible()
    assert errors == []


def test_retry_preview_recovers_and_appends_the_retained_page(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, "error_retry")
    root = page.locator('[data-citry-ui-part="infinite-scroll"]')
    assert root.evaluate("element => element.hasAttribute('data-error')") is True
    root.locator('[data-citry-ui-part="action"]').click()
    page.wait_for_function("document.querySelectorAll('[data-citry-ui-part=content] li').length === 4")
    page.wait_for_function("document.querySelector('[data-citry-ui-part=infinite-scroll]').hasAttribute('data-end')")
    assert page.get_by_text("Order #1039").is_visible()
    assert page.get_by_text("Orders recovered").is_visible()
    assert errors == []


def test_named_server_action_accepts_its_submitter_and_appends_a_dummy_response(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, "server_action")
    root = page.locator('[data-citry-ui-part="infinite-scroll"]')
    initial_url = page.url
    assert page.get_by_role("textbox", name="Search query").input_value() == ""
    root.locator('[data-citry-ui-part="action"]').click()
    page.wait_for_function("document.querySelectorAll('[data-citry-ui-part=content] li').length === 4")
    assert page.url == initial_url
    assert page.get_by_text("result_action=next:2").is_visible()
    assert page.get_by_text("Low-light autofocus test").is_visible()
    assert root.evaluate("element => element.hasAttribute('data-end')") is True
    assert errors == []


def test_virtual_list_preview_replaces_its_server_snapshot(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, "virtual_list")
    root = page.locator('[data-citry-ui-part="infinite-scroll"]')
    assert root.locator('[role="listitem"]:visible').count() == 3
    root.locator('[data-citry-ui-part="action"]').click()
    page.wait_for_function(
        "[...document.querySelectorAll('[data-citry-ui-part=content] [role=listitem]')]"
        ".filter(item => item.getClientRects().length).length === 6"
    )
    assert root.locator('[role="listitem"]:visible').count() == 6
    assert page.get_by_text("Invited a reviewer").is_visible()
    assert root.evaluate("element => element.hasAttribute('data-end')") is True
    assert errors == []


def test_completed_accessibility_preview_has_no_request_action(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, "accessibility")
    root = page.locator('[data-citry-ui-part="infinite-scroll"]')
    assert root.evaluate("element => element.hasAttribute('data-end')") is True
    assert root.locator('[data-citry-ui-part="action"]').is_hidden()
    assert errors == []


@pytest.mark.parametrize("preview_name", _PREVIEW_NAMES)
def test_shipped_previews_have_no_high_impact_axe_findings(
    page: Any,
    serve_citry_ui_live: Any,
    preview_name: str,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, preview_name)
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => {
          const result = await axe.run(document, {resultTypes: ['violations']});
          return result.violations.filter(
            finding => finding.impact === 'serious' || finding.impact === 'critical'
          );
        }"""
    )
    assert violations == [], f"Infinite Scroll preview {preview_name} has high-impact axe findings"
    assert errors == []
