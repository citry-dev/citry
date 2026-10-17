"""
Browser checks for a Render that replaces components a caller passed in as fills.

A component written between another component's tags, such as ``<c-Badge />``
inside ``<c-mark name="summary">``, belongs to the template that wrote it: the
browser keeps its binding in that caller's call table, not in the table of the
component that shows it. A Render into the mark, or into the component that
received the fill, replaces the fill while the caller stays on the page. The
test reaches the target through a mark, through ``render:<id>``, and through
the filled-in component's own Render, each with a replacement of the same
component type and of a different type.
"""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for

_PlaywrightTimeoutError = pytest.importorskip("playwright.sync_api").TimeoutError

_TARGETS = ("mark", "render-id", "calling-instance")


def _collect_errors(page: Any) -> list[str]:
    # A rejected revision surfaces as an unhandled rejection, not as a pageerror.
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.add_init_script("addEventListener('unhandledrejection', event => console.error(String(event.reason)));")
    page.add_init_script(
        """
        window.__citryReadyApps = [];
        document.addEventListener('citry:ready', event => window.__citryReadyApps.push(event.detail.appId));
        """
    )
    return errors


def _open(page: Any, serve_live: Any, engine: Citry, html: str, errors: list[str]) -> None:
    page.goto(serve_live(engine, html, "") + "/")
    _wait(page, "window.__citryReadyApps?.length === 1", errors)


def _wait(page: Any, expression: str, errors: list[str]) -> None:
    # A rejected revision leaves the page unchanged, so report the browser
    # error rather than a bare timeout.
    try:
        page.wait_for_function(expression, timeout=10_000)
    except _PlaywrightTimeoutError:
        pytest.fail(f"the page never reached {expression!r}; browser errors: {errors}")


def _app_revision(page: Any) -> int:
    return page.evaluate("[...__citryRuntime._apps.values()][0].revision")


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("target", "replacement"),
    [
        *((target, replacement) for target in _TARGETS for replacement in ("same-type", "different-type")),
        # The replacement Card receives the Badge through its own slot, so the
        # slot the caller filled renders again, now with the Render's content.
        ("render-id", "supplied-slot"),
        ("calling-instance", "supplied-slot"),
    ],
)
def test_render_replaces_components_a_caller_filled_in(
    page: Any, serve_live: Any, target: str, replacement: str
) -> None:
    engine = Citry(secret="vue-fill-replacement-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    card_render_id = ""

    class Badge(Component):
        citry = engine
        template = """
          <b id="badge">{{ label }}</b>
        """

        def template_data(self, kwargs, slots):
            return {"label": kwargs.get("label", "initial")}

    class Notice(Component):
        citry = engine
        template = """
          <i id="notice">notice</i>
        """

    class CardState:
        count: int = 0

    class Card(Component):
        citry = engine
        State = CardState
        template = """
          <section id="card">
            <button id="card-refresh" type="button" @c-click="refresh">card</button>
            <c-slot name="default">{{ fallback }}</c-slot>
          </section>
        """

        def template_data(self, kwargs, slots):
            # The next Render addresses whichever Card the page shows now.
            nonlocal card_render_id
            card_render_id = self.id
            child = kwargs.get("child")
            return {"fallback": child if child is not None else "empty"}

        class Events:
            def refresh(self, state: CardState):
                state.count += 1
                return actions.Render(_card())

    renders = 0

    def _replacement() -> Component:
        # Each Render replaces the Card and its State, so count the Renders here.
        nonlocal renders
        renders += 1
        return Notice() if replacement == "different-type" else Badge(label=f"badge-{renders}")

    def _card() -> Component:
        if replacement == "supplied-slot":
            return Card(slots={"default": _replacement()})
        return Card(child=_replacement())

    class CallerState:
        count: int = 0

    class Caller(Component):
        citry = engine
        State = CallerState
        # The mark case fills a mark; the other two fill a Card. Both fills
        # are written here, so this template's call table names the Badge.
        template = (
            """
          <main>
            <button id="refresh" type="button" @c-click="refresh">refresh</button>
            <button id="local" type="button" @click="local += 1" v-text="local"></button>
            <div id="holder"><c-mark name="summary"><c-Badge /></c-mark></div>
          </main>
        """
            if target == "mark"
            else """
          <main>
            <button id="refresh" type="button" @c-click="refresh">refresh</button>
            <button id="local" type="button" @click="local += 1" v-text="local"></button>
            <div id="holder"><c-Card><c-Badge /></c-Card></div>
          </main>
        """
        )

        js = """
          $component({
            data() {
              return { local: 0 };
            },
          });
        """

        class Events:
            def refresh(self, state: CallerState):
                state.count += 1
                if target == "mark":
                    return actions.Render(_replacement(), target="mark:summary")
                return actions.Render(_card(), target=f"render:{card_render_id}")

    dispatcher_for(engine)
    errors = _collect_errors(page)
    _open(page, serve_live, engine, Caller().render().serialize(), errors)
    assert page.locator("#holder #badge").text_content() == "initial"
    revision = _app_revision(page)
    trigger = "#card-refresh" if target == "calling-instance" else "#refresh"

    for count in (1, 2):
        # The second Render starts from content the first one replaced, so an
        # entry the first one left in the caller's call table must not reject it.
        page.locator(trigger).click()
        _wait(page, f"[...__citryRuntime._apps.values()][0].revision === {revision + count}", errors)
        if replacement != "different-type":
            assert page.locator("#holder #badge").text_content() == f"badge-{count}"
        else:
            assert page.locator("#holder #notice").count() == 1
            assert page.locator("#holder #badge").count() == 0

    # The caller renders again in the browser. Its fill still names the
    # removed Badge, and the replaced content must not show it.
    page.locator("#local").click()
    _wait(page, "document.querySelector('#local')?.textContent === '1'", errors)
    expected = "#holder #notice" if replacement == "different-type" else "#holder #badge"
    assert page.locator(expected).count() == 1
    if replacement == "different-type":
        assert page.locator("#holder #badge").count() == 0
    assert errors == []
