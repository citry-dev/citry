"""Browser acceptance for two live instances produced from one cache artifact."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from citry import Citry, Component
from citry.ext.cache.extension import CacheExtension
from citry.ext.events.renderers import dispatcher_for

pytestmark = pytest.mark.e2e


def test_replayed_events_and_dependencies_have_fresh_browser_identity(
    page: Any,
    serve_live: Any,
    monkeypatch: Any,
) -> None:
    page.set_default_timeout(3000)
    app = Citry(secret="phase-2-browser-secret")  # noqa: S106 - deterministic test signing key
    app.set_mounted_prefix("/citry")
    renders = 0

    class CachedState:
        count: int = 0

        def render(self):
            return Cached(count=self.count)

    class Cached(Component):
        citry = app

        State = CachedState

        class Events:
            def increment(self, state: CachedState):
                state.count += 1
                return state.render()

        css = ".cached { color: rgb(1, 2, 3); }"
        template = '<button class="cached" @c-click="increment">{{ count }}</button>'

        def template_data(self, kwargs, slots=None):
            nonlocal renders
            renders += 1
            return {"count": kwargs.get("count", 0)}

    extension = app.extensions.get_extension("cache")
    assert isinstance(extension, CacheExtension)

    def lookup(component, _context):
        if type(component) is Cached and component.kwargs.get("count", 0) == 0:
            return extension._lookup_physical_key(
                "phase2:browser-replay",
                ttl=None,
                max_entry_bytes=None,
            )
        return None

    monkeypatch.setattr(extension, "_lookup_component", lookup)
    dispatcher_for(app)

    class Page(Component):
        citry = app
        template = """
        <!doctype html>
        <html>
          <head><title>cache replay</title></head>
          <body><c-cached /><c-cached /></body>
        </html>
        """

    html = Page().render().serialize()
    assert renders == 1
    messages: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    calls: list[dict[str, Any]] = []
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json) if request.url.endswith("/ext/events/call") else None,
    )
    page.goto(serve_live(app, html, ""))
    try:
        page.wait_for_function(
            """
            () => {
              const buttons = [...document.querySelectorAll('.cached')];
              return buttons.length === 2 && buttons.every((button) => button.textContent === '0');
            }
            """
        )
    except PlaywrightTimeoutError:
        pytest.fail(f"console={messages!r}; page_errors={page_errors!r}")
    errors = [message for message in messages if message.startswith("error:")]
    assert errors == [], "\n".join(errors)
    assert page_errors == []

    buttons = page.locator(".cached")
    assert buttons.evaluate_all("els => els.map(el => getComputedStyle(el).color)") == ["rgb(1, 2, 3)"] * 2
    for index, expected in ((0, "1"), (0, "2"), (1, "1"), (1, "2")):
        buttons.nth(index).click()
        try:
            page.wait_for_function(
                "([index, expected]) => document.querySelectorAll('.cached')[index]?.textContent === expected",
                arg=[index, expected],
            )
        except PlaywrightTimeoutError:
            pytest.fail(f"calls={calls!r}; console={messages!r}; page_errors={page_errors!r}; html={page.content()!r}")
        sibling = 1 - index
        sibling_expected = "0" if index == 0 else "2"
        assert buttons.nth(sibling).text_content() == sibling_expected
    assert buttons.evaluate_all("els => els.map(el => el.textContent)") == ["2", "2"]
    assert calls[0]["calls"][0]["callerRenderId"] != calls[2]["calls"][0]["callerRenderId"]
    assert all(type(item["calls"][0]["stateToken"]) is str for item in calls)


def test_fragment_cache_replays_events_and_dependencies_with_fresh_browser_identity(
    page: Any,
    serve_live: Any,
) -> None:
    page.set_default_timeout(3000)
    app = Citry(secret="phase-4-browser-secret")  # noqa: S106 - deterministic test signing key
    app.set_mounted_prefix("/citry")
    renders = 0

    class FragmentState:
        count: int = 0

        def render(self):
            return FragmentItem(count=self.count)

    class FragmentItem(Component):
        citry = app
        State = FragmentState

        class Events:
            def increment(self, state: FragmentState):
                state.count += 1
                return state.render()

        css = ".fragment-item { color: rgb(4, 5, 6); }"
        template = '<button class="fragment-item" @c-click="increment">{{ count }}</button>'

        def template_data(self, kwargs, slots=None):
            nonlocal renders
            renders += 1
            return {"count": kwargs.get("count", 0)}

    dispatcher_for(app)

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
    calls: list[dict[str, Any]] = []
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json) if request.url.endswith("/ext/events/call") else None,
    )
    page.goto(serve_live(app, html, ""))
    try:
        page.wait_for_function(
            """
            () => {
              const buttons = [...document.querySelectorAll('.fragment-item')];
              return buttons.length === 2 && buttons.every((button) => button.textContent === '0');
            }
            """
        )
    except PlaywrightTimeoutError:
        pytest.fail(f"console={messages!r}; page_errors={page_errors!r}")
    errors = [message for message in messages if message.startswith("error:")]
    assert errors == [], "\n".join(errors)
    assert page_errors == []

    buttons = page.locator(".fragment-item")
    assert buttons.evaluate_all("els => els.map(el => getComputedStyle(el).color)") == ["rgb(4, 5, 6)"] * 2
    buttons.nth(0).click()
    page.wait_for_function("document.querySelectorAll('.fragment-item')[0]?.textContent === '1'")
    buttons.nth(1).click()
    page.wait_for_function("document.querySelectorAll('.fragment-item')[1]?.textContent === '1'")
    assert calls[0]["calls"][0]["callerRenderId"] != calls[1]["calls"][0]["callerRenderId"]


def test_component_cache_replays_i18n_bindings_with_fresh_occurrences(page: Any) -> None:
    page.set_default_timeout(3000)
    app = Citry(
        autodiscover=False,
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )
    renders = 0

    class CachedMessage(Component):
        citry = app
        messages = "loading = Loading"
        template = '<output class="cached-message" $c-tr:loading>{{ tr("loading") }}</output>'

        class Cache:
            enabled = True

        def template_data(self, kwargs, slots):
            nonlocal renders
            renders += 1
            return {}

    class Page(Component):
        citry = app
        template = (
            '<html><body><c-i18n c-client="True" tag="main">'
            "<c-CachedMessage /><c-CachedMessage />"
            "</c-i18n></body></html>"
        )

    html = Page().render().serialize()
    assert renders == 1
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.route("http://citry.test/", lambda route: route.fulfill(body=html, content_type="text/html"))
    page.goto("http://citry.test/", wait_until="commit")
    try:
        page.wait_for_function(
            "() => [...document.querySelectorAll('.cached-message')]"
            ".map(x => x.textContent).join('|') === 'Loading|Loading'"
        )
    except PlaywrightTimeoutError:
        pytest.fail(f"faults={faults!r}; html={page.content()!r}")
    assert page.locator(".cached-message").count() == 2
    assert faults == []


def test_nested_fragment_cache_replay_preserves_physical_region_ancestry(
    page: Any,
    serve_live: Any,
) -> None:
    app = Citry(secret="phase-4-nested-browser-secret")  # noqa: S106 - deterministic test signing key
    app.set_mounted_prefix("/citry")

    class Page(Component):
        citry = app
        template = """
        <!doctype html>
        <html>
          <head><title>nested fragment cache replay</title></head>
          <body>
            <c-cache key="browser-outer">
                  <c-cache key="browser-inner">
                    <button id="nested-cache">{{ n }}</button>
              </c-cache>
            </c-cache>
          </body>
        </html>
            """

        def template_data(self, kwargs, slots=None):
            return {"n": 9}

    Page().render().serialize()
    html = Page().render().serialize()
    messages: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(serve_live(app, html, ""))
    try:
        page.wait_for_function("() => document.querySelector('#nested-cache')?.textContent === '9'")
    except PlaywrightTimeoutError:
        pytest.fail(f"console={messages!r}; page_errors={page_errors!r}")

    errors = [message for message in messages if message.startswith("error:")]
    assert errors == [], "\n".join(errors)
    assert page_errors == []


def test_cached_on_render_replacement_mounts_as_vue_content(
    page: Any,
    serve_live: Any,
) -> None:
    app = Citry(secret="phase-4-replacement-browser-secret")  # noqa: S106 - deterministic test signing key
    app.set_mounted_prefix("/citry")

    class Replace(Component):
        citry = app
        template = """\
initial\
"""

        def on_render(self):
            yield
            return '<button id="replacement-active">active</button>'

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
    page.goto(serve_live(app, html, ""))
    try:
        page.wait_for_function("() => document.querySelector('#replacement-active')?.textContent === 'active'")
    except PlaywrightTimeoutError:
        pytest.fail(f"console={messages!r}; page_errors={page_errors!r}")

    errors = [message for message in messages if message.startswith("error:")]
    assert errors == [], "\n".join(errors)
    assert page_errors == []
