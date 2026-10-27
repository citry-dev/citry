"""Browser evidence for urgent modal decisions."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component
from citry import citry as default_citry
from citry_ui.quality.accessibility import axe_rule_exclusions_script

pytestmark = pytest.mark.e2e


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate repository root for AlertDialog tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en"><head><meta charset="utf-8" /><title>AlertDialog contract</title><c-css /></head>
          <body>
            <c-CAlertDialog id="uncontrolled">
              <c-fill name="activator" data="{activator_attrs}">
                <c-CButton c-attrs="activator_attrs">Delete project</c-CButton>
              </c-fill>
              <c-fill name="title">Delete project?</c-fill>
              <c-fill name="description">This permanently removes project data.</c-fill>
              <c-fill name="cancel" data="{cancel_attrs}">
                <c-CButton
                  c-attrs="cancel_attrs"
                  variant="outline"
                  @click="alertEvents.push('cancel-click')"
                >Keep project</c-CButton>
              </c-fill>
              <c-fill name="action" data="{action_attrs}">
                <c-CButton
                  c-attrs="action_attrs"
                  intent="danger"
                  @click="alertEvents.push('action-click')"
                >Delete</c-CButton>
              </c-fill>
            </c-CAlertDialog>

            <c-CAlertDialog
              id="controlled-alert"
              :open="controlledOpen"
              :onOpenChange="(open, detail) => {
                  alertEvents.push(['open', open, detail.reason, detail.returnValue]);
                  if (accept) controlledOpen = open;
                }"
            >
              <c-fill name="activator" data="{activator_attrs}">
                <c-CButton c-attrs="activator_attrs">Open controlled</c-CButton>
              </c-fill>
              <c-fill name="title">End session?</c-fill>
              <c-fill name="description">Unsaved work will be discarded.</c-fill>
              <c-fill name="cancel" data="{cancel_attrs}">
                <c-CButton c-attrs="cancel_attrs">Continue session</c-CButton>
              </c-fill>
              <c-fill name="action" data="{action_attrs}">
                <c-CButton c-attrs="action_attrs" intent="danger">End session</c-CButton>
              </c-fill>
            </c-CAlertDialog>
            <button id="after" type="button">After</button>
          </body></html>
        """
        js = """
          $component({
            data() {
              return { controlledOpen: false, accept: false, alertEvents: [] };
            },
            mounted() {
              window.__alertEvents = this.alertEvents;
              window.__state = this;
            },
            beforeUnmount() {
              delete window.__alertEvents;
              delete window.__state;
            },
          });
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector("[data-citry-alert-dialog-initialized]")
    return errors


def test_open_focus_outside_refusal_cancel_and_action_order(page: Any) -> None:
    errors = _load(page)
    trigger = page.get_by_role("button", name="Delete project")
    trigger.click()
    dialog = page.get_by_role("alertdialog", name="Delete project?")
    assert dialog.evaluate("element => element.matches(':modal')")
    cancel = dialog.get_by_role("button", name="Keep project")
    assert cancel.evaluate("element => element === document.activeElement")

    box = dialog.bounding_box()
    assert box is not None
    page.mouse.click(2, 2)
    assert dialog.evaluate("element => element.open")

    cancel.click()
    page.wait_for_function("!document.querySelector('#uncontrolled').open")
    assert page.evaluate("window.__alertEvents") == ["cancel-click"]
    assert trigger.evaluate("element => element === document.activeElement")

    trigger.click()
    dialog.get_by_role("button", name="Delete").click()
    page.wait_for_function("!document.querySelector('#uncontrolled').open")
    assert page.evaluate("window.__alertEvents.at(-1)") == "action-click"
    assert errors == []


def test_controlled_rejection_acceptance_escape_and_return_value(page: Any) -> None:
    errors = _load(page)
    trigger = page.get_by_role("button", name="Open controlled")
    trigger.click()
    page.wait_for_function("window.__alertEvents.length === 1")
    assert page.evaluate("window.__alertEvents[0]") == ["open", True, "trigger", ""]
    assert not page.locator("#controlled-alert").evaluate("element => element.open")

    page.evaluate("window.__state.accept = true")
    trigger.click()
    page.wait_for_function("document.querySelector('#controlled-alert').open")
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#controlled-alert').open")
    assert page.evaluate("window.__alertEvents.at(-1).slice(0, 3)") == ["open", False, "escape"]

    trigger.click()
    page.wait_for_function("document.querySelector('#controlled-alert').open")
    page.get_by_role("alertdialog", name="End session?").get_by_role("button", name="End session").click()
    page.wait_for_function("!document.querySelector('#controlled-alert').open")
    assert page.evaluate("window.__alertEvents.at(-1)") == ["open", False, "action", "action"]
    assert errors == []


def test_focus_loop_role_description_variables_and_axe(page: Any) -> None:
    errors = _load(page)
    page.get_by_role("button", name="Delete project").click()
    dialog = page.get_by_role("alertdialog", name="Delete project?")
    assert dialog.get_attribute("aria-describedby") == "uncontrolled-description"
    action = dialog.get_by_role("button", name="Delete")
    action.focus()
    page.keyboard.press("Tab")
    assert dialog.get_by_role("button", name="Keep project").evaluate("element => element === document.activeElement")
    dialog.evaluate("element => element.style.setProperty('--cui-alert-dialog-radius', '19px')")
    assert dialog.evaluate("element => getComputedStyle(element).borderRadius") == "19px"

    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe_path))
    page.evaluate(axe_rule_exclusions_script())
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes: ['violations']})).violations
          .filter((item) => ['serious', 'critical'].includes(item.impact)).map((item) => item.id)"""
    )
    assert violations == []
    assert errors == []


class AlertDialogPreviewDocument(Component):
    citry = default_citry

    class Kwargs:
        content: object

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, _slots: Slots) -> dict[str, object]:
        return {"content": kwargs.content}

    template = """
      <!doctype html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>AlertDialog snippet</title>
          <c-css />
        </head>
        <body>
          <main>{{ content }}</main>
          <c-js />
        </body>
      </html>
    """


def _open_snippet(page: Any, serve_citry_ui_live: Any, name: str) -> list[str]:
    # Snippets register Citry UI on the default instance when imported, so the
    # docs preview and this test render the same component.
    module = importlib.import_module(f"citry_ui.components.calert_dialog.snippets.{name}")
    html = AlertDialogPreviewDocument(content=module.preview).render().serialize()
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(serve_citry_ui_live(default_citry, html) + "/", wait_until="networkidle")
    page.wait_for_selector("[data-citry-alert-dialog-initialized]")
    return errors


def test_quality_scenario_records_the_latest_open_change(page: Any, open_scenario: Any) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    open_scenario("alert-dialog.states")
    page.wait_for_selector("[data-citry-alert-dialog-initialized]")

    page.get_by_role("button", name="Delete project").click()
    page.wait_for_function("document.querySelector('#quality-delete-project').open")
    assert page.evaluate("window.__qualityAlertDialogChange") == {
        "open": True,
        "reason": "trigger",
        "returnValue": "",
    }

    page.get_by_role("alertdialog", name="Delete this project?").get_by_role("button", name="Keep project").click()
    page.wait_for_function("!document.querySelector('#quality-delete-project').open")
    assert page.evaluate("window.__qualityAlertDialogChange") == {
        "open": False,
        "reason": "action",
        "returnValue": "cancel",
    }
    assert errors == []


def test_controlled_action_snippet_keeps_the_dialog_open_until_archiving_finishes(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_snippet(page, serve_citry_ui_live, "controlled_action")
    trigger = page.get_by_role("button", name="Archive record")
    result = page.locator("p[aria-live=polite]")

    trigger.click()
    page.wait_for_function("document.querySelector('#archive-record').open")
    page.get_by_role("alertdialog", name="Archive this record?").get_by_role("button", name="Cancel").click()
    page.wait_for_function("!document.querySelector('#archive-record').open")
    assert result.text_content() == "Archive cancelled"

    trigger.click()
    page.wait_for_function("document.querySelector('#archive-record').open")
    alert = page.get_by_role("alertdialog", name="Archive this record?")
    alert.get_by_role("button", name="Archive").click()
    # The owner keeps the controlled dialog open while the action runs. Read
    # all three in one check, because the work finishes after 500 ms.
    page.wait_for_function(
        """() => document.querySelector('p[aria-live=polite]').textContent === 'Archiving...'
          && document.querySelector('#archive-record').open
          && [...document.querySelectorAll('#archive-record button')]
            .find(button => button.textContent.trim() === 'Cancel').disabled"""
    )
    page.wait_for_function("!document.querySelector('#archive-record').open")
    assert result.text_content() == "Record archived"
    assert errors == []


def test_controlled_action_snippet_ignores_escape_while_archiving(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    # Escape during the archive work must not report a cancel for a record
    # that is archived a moment later.
    errors = _open_snippet(page, serve_citry_ui_live, "controlled_action")
    page.get_by_role("button", name="Archive record").click()
    page.wait_for_function("document.querySelector('#archive-record').open")
    page.get_by_role("alertdialog", name="Archive this record?").get_by_role("button", name="Archive").click()
    page.wait_for_function("document.querySelector('p[aria-live=polite]').textContent === 'Archiving...'")

    page.keyboard.press("Escape")
    # Two frames give the dialog time to apply a close it accepted.
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
    assert page.evaluate("document.querySelector('#archive-record').open") is True
    assert page.locator("p[aria-live=polite]").text_content() == "Archiving..."

    page.wait_for_function("!document.querySelector('#archive-record').open")
    assert page.locator("p[aria-live=polite]").text_content() == "Record archived"
    assert errors == []
