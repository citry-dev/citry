"""Cross-browser behavior tests for CToastRegion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component, ComponentLibrary

pytestmark = pytest.mark.e2e


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body x-data="{
              notices: [
                {id: 'saved', title: 'Saved', description: 'Field note synchronized.',
                 intent: 'success', durationMs: 0},
                {id: 'retry', title: 'Upload paused', actionLabel: 'Retry',
                 intent: 'warn', durationMs: 0},
                {id: 'queued', title: 'Queued observation', durationMs: 0},
              ],
              placement: 'block-end-end', limit: 2, durationMs: 1000,
              pauseOnHover: true, pauseOnFocus: true, pauseOnHidden: true,
              removeOnDismiss: true, dismissals: [], actions: []
            }">
              <button id="before" type="button">Before notices</button>
              <form id="toast-form" @submit.prevent="$el.dataset.submitted = 'yes'">
                <c-CToastRegion
                  id="notices"
                  $c-props="{
                    items: notices, placement, limit, durationMs,
                    pauseOnHover, pauseOnFocus, pauseOnHidden,
                    onDismiss: (id, detail) => {
                      dismissals.push([id, detail.reason, detail.message.title,
                        Object.hasOwn(detail.message, 'fingerprint')]);
                      if (removeOnDismiss) notices = notices.filter(item => item.id !== id);
                    },
                    onAction: (id, detail) => actions.push([
                      id, detail.message.title, Object.hasOwn(detail.message, 'fingerprint')
                    ]),
                  }"
                />
                <button id="submit" type="submit">Submit form</button>
              </form>
              <button id="after" type="button">After notices</button>
              <dialog id="blocking-dialog"><button type="button">Modal task</button></dialog>
              <output id="dismissals" x-text="JSON.stringify(dismissals)"></output>
              <output id="actions" x-text="JSON.stringify(actions)"></output>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _morph_page() -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-toast-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(ComponentLibrary("citry-ui-toast-e2e", (citry_ui.CToastRegion,)))

    class ToastHost(Component):
        citry = app

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def advance(self, state):
                state.step += 1
                return ToastHost(step=state.step)

        template = """
          <section data-toast-host>
            <button class="advance-toast" type="button" @c-click="advance">Advance</button>
            <c-CToastRegion
              #c-key="'retained-toast'"
              id="retained-toast"
              c-items="items"
              c-placement="placement"
              c-duration_ms="0"
            />
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            return {
                "items": (citry_ui.CToastMessage(id="retained", title="Retained notice"),),
                "placement": "block-end-end" if kwargs.step == 0 else "block-start-start",
            }

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body><c-toast-host /><c-js /></body>
          </html>
        """

    return app, str(Page())


@pytest.fixture
def toast_page(page: Any):
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector("#notices[data-citry-toast-initialized]")
    return page, console_errors, page_errors


def _toasts(page: Any):
    return page.locator('#notices > [data-citry-toast-list] > [data-citry-ui-part="toast"]')


def _dismiss_button(toast: Any, title: str):
    button = toast.locator("[data-citry-toast-dismiss]")
    label = button.get_attribute("aria-label")
    assert label is not None
    assert label.replace("\u2068", "").replace("\u2069", "") == f"Dismiss {title}"
    return button


def test_queue_limit_semantics_announcers_and_form_safety(toast_page) -> None:
    page, console_errors, page_errors = toast_page
    region = page.locator("#notices")
    toasts = _toasts(page)

    assert region.get_attribute("role") == "region"
    assert region.get_attribute("aria-label") == "Notifications"
    assert toasts.count() == 2
    assert toasts.nth(0).get_attribute("data-citry-toast-id") == "saved"
    assert toasts.nth(1).get_attribute("data-citry-toast-id") == "retry"
    assert region.locator('[aria-live="polite"]').count() == 1
    assert region.locator('[aria-live="assertive"]').count() == 1
    assert toasts.nth(0).get_attribute("aria-labelledby")
    assert toasts.nth(0).get_attribute("aria-describedby")

    _dismiss_button(toasts.nth(0), "Saved").click()
    page.wait_for_function("document.querySelectorAll('#notices [data-citry-ui-part=toast]').length === 2")
    assert _toasts(page).nth(1).get_attribute("data-citry-toast-id") == "queued"
    assert page.locator("#toast-form").get_attribute("data-submitted") is None
    assert page.locator("#dismissals").text_content() == '[["saved","dismiss","Saved",false]]'
    assert console_errors == []
    assert page_errors == []


def test_action_order_close_policy_and_suppression_until_producer_removal(toast_page) -> None:
    page, console_errors, page_errors = toast_page
    retry = page.locator('[data-citry-toast-id="retry"]')
    retry.get_by_role("button", name="Retry").click()
    page.wait_for_function("!document.querySelector('[data-citry-toast-id=retry]')")

    assert page.locator("#actions").text_content() == '[["retry","Upload paused",false]]'
    assert page.locator("#dismissals").text_content() == ('[["retry","action","Upload paused",false]]')

    page.evaluate("Alpine.$data(document.body).removeOnDismiss = false")
    page.evaluate("Alpine.$data(document.body).limit = 3")
    page.evaluate(
        """() => {
          const state = Alpine.$data(document.body);
          state.notices = [...state.notices, {id: 'sticky', title: 'Sticky', durationMs: 0}];
        }"""
    )
    sticky = page.locator('[data-citry-toast-id="sticky"]')
    _dismiss_button(sticky, "Sticky").click()
    page.wait_for_function("!document.querySelector('[data-citry-toast-id=sticky]')")
    page.evaluate("Alpine.$data(document.body).placement = 'block-start-start'")
    page.wait_for_timeout(0)
    assert page.locator('[data-citry-toast-id="sticky"]').count() == 0
    page.evaluate(
        """() => {
          const state = Alpine.$data(document.body);
          state.notices = state.notices.filter(item => item.id !== 'sticky');
        }"""
    )
    page.evaluate(
        """() => {
          const state = Alpine.$data(document.body);
          state.notices = [...state.notices,
            {id: 'sticky', title: 'Fresh sticky', durationMs: 0}];
        }"""
    )
    page.wait_for_selector('[data-citry-toast-id="sticky"]')
    assert page.get_by_text("Fresh sticky", exact=True).count() == 1
    assert console_errors == []
    assert page_errors == []


def test_timeout_pause_and_queued_promotion(toast_page) -> None:
    page, console_errors, page_errors = toast_page
    page.evaluate(
        """() => {
          const state = Alpine.$data(document.body);
          state.limit = 1;
          state.notices = [
            {id: 'timed', title: 'Timed', durationMs: 1000},
            {id: 'later', title: 'Later', durationMs: 0},
          ];
        }"""
    )
    page.wait_for_selector('[data-citry-toast-id="timed"]')
    region = page.locator("#notices")
    region.hover()
    page.wait_for_timeout(1150)
    assert page.locator('[data-citry-toast-id="timed"]').count() == 1
    page.locator("#before").hover()
    page.wait_for_function("!document.querySelector('[data-citry-toast-id=timed]')", timeout=2500)
    assert page.locator('[data-citry-toast-id="later"]').count() == 1
    assert '["timed","timeout","Timed",false]' in page.locator("#dismissals").text_content()
    assert console_errors == []
    assert page_errors == []


def test_f6_focus_route_and_focused_removal_handoff(toast_page) -> None:
    page, console_errors, page_errors = toast_page
    page.locator("#before").focus()
    page.keyboard.press("F6")
    assert page.locator('[data-citry-toast-id="saved"]').evaluate("element => element === document.activeElement")
    page.keyboard.press("F6")
    assert page.locator("#before").evaluate("element => element === document.activeElement")

    first = page.locator('[data-citry-toast-id="saved"]')
    first.focus()
    _dismiss_button(first, "Saved").click()
    page.wait_for_function("document.activeElement?.getAttribute('data-citry-toast-id') === 'retry'")
    assert console_errors == []
    assert page_errors == []


def test_reactive_configuration_invalid_episode_and_logical_geometry(toast_page) -> None:
    page, console_errors, page_errors = toast_page
    region = page.locator("#notices")
    page.evaluate("Object.assign(Alpine.$data(document.body), {placement: 'block-start-start', limit: 3})")
    page.wait_for_function("document.querySelector('#notices').dataset.placement === 'block-start-start'")
    assert _toasts(page).count() == 3
    assert region.evaluate("element => getComputedStyle(element).insetBlockStart !== 'auto'")

    page.evaluate("Alpine.$data(document.body).placement = null")
    page.wait_for_timeout(0)
    page.evaluate("Object.assign(Alpine.$data(document.body), {placement: 42, limit: 'many'})")
    page.wait_for_timeout(0)
    page.evaluate("Object.assign(Alpine.$data(document.body), {durationMs: 99, pauseOnHover: 'yes'})")
    page.wait_for_timeout(0)
    page.evaluate("Object.assign(Alpine.$data(document.body), {limit: -1, placement: 'center'})")
    page.wait_for_timeout(0)
    assert sum("CToastRegion placement received invalid" in item for item in console_errors) == 1
    assert sum("CToastRegion limit received invalid" in item for item in console_errors) == 1
    assert sum("CToastRegion durationMs received invalid" in item for item in console_errors) == 1
    assert sum("CToastRegion pauseOnHover received invalid" in item for item in console_errors) == 1
    assert page_errors == []


def test_unrelated_modal_suppresses_appearance_announcement_and_timers(toast_page) -> None:
    page, console_errors, page_errors = toast_page
    dialog = page.locator("#blocking-dialog")
    page.evaluate(
        """() => {
          document.querySelector('#blocking-dialog').showModal();
          Alpine.$data(document.body).notices = [
            {id: 'modal-wait', title: 'Wait for modal', priority: 'assertive', durationMs: 1000}
          ];
        }"""
    )
    page.wait_for_function("document.querySelector('#notices').inert")
    region = page.locator("#notices")
    assert region.get_attribute("data-citry-toast-modal-paused") == ""
    page.wait_for_timeout(1100)
    assert page.locator('[data-citry-toast-id="modal-wait"]').count() == 1
    assert region.locator('[aria-live="assertive"]').text_content() == ""

    page.evaluate("document.querySelector('#blocking-dialog').close()")
    page.wait_for_function("!document.querySelector('#notices').inert")
    page.wait_for_function(
        "document.querySelector('#notices [aria-live=assertive]').textContent.includes('Wait for modal')"
    )
    page.wait_for_function("!document.querySelector('[data-citry-toast-id=modal-wait]')", timeout=2500)
    assert not dialog.evaluate("element => element.matches(':modal')")
    assert console_errors == []
    assert page_errors == []


def test_plain_text_update_identity_rtl_css_and_accessibility(toast_page) -> None:
    page, console_errors, page_errors = toast_page
    page.evaluate(
        """() => {
          document.documentElement.dir = 'rtl';
          Alpine.$data(document.body).notices = [{
            id: 'saved', title: '<b>Updated safely</b>',
            description: 'observatory'.repeat(40), intent: 'error', durationMs: 0,
          }];
        }"""
    )
    toast = page.locator('[data-citry-toast-id="saved"]')
    page.wait_for_function(
        """document.querySelector(
          '[data-citry-toast-id=saved] [data-citry-ui-part=title]'
        ).textContent.includes('Updated safely')"""
    )
    assert toast.locator("b").count() == 0
    assert toast.get_attribute("data-intent") == "error"
    assert toast.evaluate("element => element.scrollWidth <= element.clientWidth")
    page.evaluate("Alpine.$data(document.body).placement = 'block-end-start'")
    page.wait_for_function("document.querySelector('#notices').dataset.placement === 'block-end-start'")
    assert page.locator("#notices").evaluate("element => getComputedStyle(element).insetInlineStart !== 'auto'")
    axe_path = Path("node_modules/axe-core/axe.min.js").resolve()
    assert axe_path.is_file()
    page.add_script_tag(path=str(axe_path))
    violations = page.evaluate(
        """async () => (await axe.run(document.querySelector('#notices'))).violations.filter(
          item => item.impact === 'serious' || item.impact === 'critical'
        )"""
    )
    assert violations == []
    assert console_errors == []
    assert page_errors == []


def test_correlated_rerender_retains_region_focus_and_does_not_reannounce(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _morph_page()
    base = serve_citry_ui_live(app, html)
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base, wait_until="load")
    page.wait_for_selector("#retained-toast[data-citry-toast-initialized]")
    toast = page.locator('[data-citry-toast-id="retained"]')
    toast.focus()
    page.wait_for_function(
        "document.querySelector('#retained-toast [aria-live=polite]').textContent === 'Retained notice'"
    )
    page.evaluate(
        """() => {
          window.__retainedToastRegion = document.querySelector('#retained-toast');
          window.__retainedToastRuntime = window.__retainedToastRegion.__citryUiToastRuntime;
          window.__retainedToastFingerprints = [
            ...window.__retainedToastRuntime.announcedFingerprints.entries()
          ];
          window.__toastAnnouncements = [];
          const announcers = document.querySelectorAll('#retained-toast [aria-live]');
          window.__toastAnnouncementObserver = new MutationObserver(
            records => window.__toastAnnouncements.push(
              ...records.map(record => record.target.textContent),
            ),
          );
          for (const node of announcers) {
            window.__toastAnnouncementObserver.observe(node, {childList:true, characterData:true, subtree:true});
          }
        }"""
    )
    page.locator(".advance-toast").evaluate("element => element.click()")
    page.wait_for_function(
        """document.querySelector('#retained-toast')?.dataset.placement === 'block-start-start'
          && document.querySelector('#retained-toast')?.hasAttribute('data-citry-toast-initialized')"""
    )
    page.wait_for_function("document.activeElement?.dataset.citryToastId === 'retained'")
    page.wait_for_timeout(350)
    assert page.evaluate("document.querySelector('#retained-toast') === window.__retainedToastRegion")
    assert page.evaluate(
        "document.querySelector('#retained-toast').__citryUiToastRuntime === window.__retainedToastRuntime"
    )
    fingerprints = page.evaluate("window.__retainedToastFingerprints")
    assert len(fingerprints) == 1
    assert fingerprints[0][0] == "retained"
    assert "Retained notice" not in page.evaluate("window.__toastAnnouncements")
    assert page.locator("#retained-toast [aria-live]").evaluate_all(
        "elements => elements.every(element => element.textContent === '')"
    )
    assert errors == []
