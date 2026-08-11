"""Browser evidence for urgent modal decisions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

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
          <body x-data="{controlledOpen: false, accept: false}" x-init="window.__alertEvents = []">
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
                  @click="window.__alertEvents.push('cancel-click')"
                >Keep project</c-CButton>
              </c-fill>
              <c-fill name="action" data="{action_attrs}">
                <c-CButton
                  c-attrs="action_attrs"
                  intent="danger"
                  @click="window.__alertEvents.push('action-click')"
                >Delete</c-CButton>
              </c-fill>
            </c-CAlertDialog>

            <c-CAlertDialog
              id="controlled-alert"
              $c-props="{
                open: controlledOpen,
                onOpenChange: (open, detail) => {
                  window.__alertEvents.push(['open', open, detail.reason, detail.returnValue]);
                  if (accept) controlledOpen = open;
                }
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

    page.evaluate("Alpine.$data(document.body).accept = true")
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
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes: ['violations']})).violations
          .filter((item) => ['serious', 'critical'].includes(item.impact)).map((item) => item.id)"""
    )
    assert violations == []
    assert errors == []
