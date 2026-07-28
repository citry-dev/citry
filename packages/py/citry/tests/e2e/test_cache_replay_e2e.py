"""Browser acceptance for two live instances produced from one cache artifact."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from citry import Citry, Component
from citry.ext.cache.extension import CacheExtension

pytestmark = pytest.mark.e2e


def test_replayed_events_and_dependencies_have_fresh_browser_identity(
    page: Any,
    serve_document: Any,
    monkeypatch: Any,
) -> None:
    app = Citry(secret="phase-2-browser-secret")  # noqa: S106 - deterministic test signing key
    renders = 0

    class Cached(Component):
        citry = app

        class State:
            count: int = 3
            _public = ("count",)

        class Events:
            def increment(self, state):
                state.count += 1

        js = """
        $component(({ els, id, data }) => {
          els.forEach((el) => {
            el.dataset.callbackId = id;
            el.dataset.callbackValue = String(data.value);
          });
        });
        """
        css = """
        .cached { color: rgb(1, 2, 3); }
        """
        template = """
        <button class="cached" x-data @c-click="increment"><c-slot /></button>
        """

        def template_data(self, kwargs, slots=None):
            nonlocal renders
            renders += 1
            return {}

        def js_data(self, kwargs, slots=None):
            return {"value": 7}

    extension = app.extensions.get_extension("cache")
    assert isinstance(extension, CacheExtension)

    def lookup(component, _context):
        if type(component) is Cached:
            return extension._lookup_physical_key(
                "phase2:browser-replay",
                ttl=None,
                max_entry_bytes=None,
            )
        return None

    monkeypatch.setattr(extension, "_lookup_component", lookup)

    class Page(Component):
        citry = app
        template = """
        <!doctype html>
        <html>
          <head><title>cache replay</title></head>
          <body><c-cached>first</c-cached><c-cached>second</c-cached></body>
        </html>
        """

    html = Page().render().serialize()
    assert renders == 1
    messages: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(serve_document(html))
    page.wait_for_function(
        """
        () => {
          const buttons = [...document.querySelectorAll('.cached')];
          return buttons.length === 2 && buttons.every(
            (button) => button.dataset.callbackId &&
              Citry.events._internal.getAnchor(button.getAttribute('data-cid'))
          );
        }
        """
    )
    errors = [message for message in messages if message.startswith("error:")]
    assert errors == [], "\n".join(errors)
    assert page_errors == []

    result = page.locator(".cached").evaluate_all(
        """
        (buttons) => buttons.map((button) => ({
          callbackId: button.dataset.callbackId,
          callbackValue: button.dataset.callbackValue,
          componentId: button.getAttribute('data-cid'),
          eventBinding: button.hasAttribute('data-cev-on'),
          eventAnchor: !!Citry.events._internal.getAnchor(button.getAttribute('data-cid')),
          color: getComputedStyle(button).color,
        }))
        """
    )
    assert len({item["componentId"] for item in result}) == 2
    assert all(item["callbackId"] == item["componentId"] for item in result)
    assert all(item["callbackValue"] == "7" for item in result)
    assert all(item["eventBinding"] for item in result)
    assert all(item["eventAnchor"] for item in result)
    assert all(item["color"] == "rgb(1, 2, 3)" for item in result)


def test_fragment_cache_replays_events_and_dependencies_with_fresh_browser_identity(
    page: Any,
    serve_document: Any,
) -> None:
    app = Citry(secret="phase-4-browser-secret")  # noqa: S106 - deterministic test signing key
    renders = 0

    class FragmentItem(Component):
        citry = app

        class State:
            count: int = 3
            _public = ("count",)

        class Events:
            def increment(self, state):
                state.count += 1

        js = """
        $component(({ els, id, data }) => {
          els.forEach((el) => {
            el.dataset.callbackId = id;
            el.dataset.callbackValue = String(data.value);
          });
        });
        """
        css = """
        .fragment-item { color: rgb(4, 5, 6); }
        """
        template = """
        <button class="fragment-item" x-data @c-click="increment">fragment</button>
        """

        def template_data(self, kwargs, slots=None):
            nonlocal renders
            renders += 1
            return {}

        def js_data(self, kwargs, slots=None):
            return {"value": 9}

    class Page(Component):
        citry = app
        template = """
        <!doctype html>
        <html>
          <head><title>fragment cache replay</title></head>
          <body>
            <c-cache key="browser-fragment"><c-fragment-item /></c-cache>
            <c-cache key="browser-fragment"><c-fragment-item /></c-cache>
          </body>
        </html>
        """

    html = Page().render().serialize()
    assert renders == 1
    messages: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(serve_document(html))
    try:
        page.wait_for_function(
            """
            () => {
              const buttons = [...document.querySelectorAll('.fragment-item')];
              return buttons.length === 2 && buttons.every(
                (button) => button.dataset.callbackId &&
                  Citry.events._internal.getAnchor(button.getAttribute('data-cid'))
              );
            }
            """
        )
    except PlaywrightTimeoutError:
        pytest.fail(f"console={messages!r}; page_errors={page_errors!r}")
    errors = [message for message in messages if message.startswith("error:")]
    assert errors == [], "\n".join(errors)
    assert page_errors == []

    result = page.locator(".fragment-item").evaluate_all(
        """
        (buttons) => buttons.map((button) => ({
          callbackId: button.dataset.callbackId,
          callbackValue: button.dataset.callbackValue,
          componentId: button.getAttribute('data-cid'),
          eventBinding: button.hasAttribute('data-cev-on'),
          eventAnchor: !!Citry.events._internal.getAnchor(button.getAttribute('data-cid')),
          color: getComputedStyle(button).color,
        }))
        """
    )
    assert len({item["componentId"] for item in result}) == 2
    assert all(item["callbackId"] == item["componentId"] for item in result)
    assert all(item["callbackValue"] == "9" for item in result)
    assert all(item["eventBinding"] for item in result)
    assert all(item["eventAnchor"] for item in result)
    assert all(item["color"] == "rgb(4, 5, 6)" for item in result)


def test_nested_fragment_cache_replay_preserves_physical_region_ancestry(
    page: Any,
    serve_document: Any,
) -> None:
    app = Citry(secret="phase-4-nested-browser-secret")  # noqa: S106 - deterministic test signing key

    class Page(Component):
        citry = app
        template = """
        <!doctype html>
        <html>
          <head><title>nested fragment cache replay</title></head>
          <body>
            <c-cache key="browser-outer">
              <c-cache key="browser-inner">
                <button id="nested-cache" x-data="{ n: 9 }" x-text="n"></button>
              </c-cache>
            </c-cache>
          </body>
        </html>
        """

    Page().render().serialize()
    html = Page().render().serialize()
    messages: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(serve_document(html))
    try:
        page.wait_for_function("() => document.querySelector('#nested-cache')?.textContent === '9'")
    except PlaywrightTimeoutError:
        pytest.fail(f"console={messages!r}; page_errors={page_errors!r}")

    errors = [message for message in messages if message.startswith("error:")]
    assert errors == [], "\n".join(errors)
    assert page_errors == []


def test_cached_on_render_replacement_preserves_physical_region_ancestry(
    page: Any,
    serve_document: Any,
) -> None:
    app = Citry(secret="phase-4-replacement-browser-secret")  # noqa: S106 - deterministic test signing key

    class Active(Component):
        citry = app
        js = """
        $component(({ els }) => {
          els.forEach((el) => { el.dataset.ready = "yes"; });
        });
        """
        template = """\
<button id="replacement-active">active</button>\
"""

    class Outlet(Component):
        citry = app
        template = """\
<c-slot />\
"""

    class Replace(Component):
        citry = app
        template = """\
initial\
"""

        def on_render(self):
            yield
            return Outlet(slots={"default": Active()})

    class Page(Component):
        citry = app
        template = """
        <!doctype html>
        <html>
          <head><title>cached replacement ancestry</title></head>
          <body><c-cache key="replacement-outer"><c-replace /></c-cache></body>
        </html>
        """

    Page().render().serialize()
    html = Page().render().serialize()
    messages: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(serve_document(html))
    try:
        page.wait_for_function("() => document.querySelector('#replacement-active')?.dataset.ready === 'yes'")
    except PlaywrightTimeoutError:
        pytest.fail(f"console={messages!r}; page_errors={page_errors!r}")

    errors = [message for message in messages if message.startswith("error:")]
    assert errors == [], "\n".join(errors)
    assert page_errors == []
