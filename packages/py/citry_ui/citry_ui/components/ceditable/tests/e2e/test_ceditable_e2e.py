"""Browser evidence for Editable state, forms, and styling."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate the repository root for Editable browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = ".primary-editable, .outside-editable, .required-editable { inline-size: 20rem; }"
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8">
          <title>Editable evidence</title><c-css /></head><body x-data>
            <form
              id="title-form"
              @submit.prevent="$store.editable.submits = Array.from(new FormData($event.target).entries())"
            >
              <c-CEditable
                class_="primary-editable"
                value="Project Atlas"
                name="title"
                $c-props="{
                  value:$store.editable.value,
                  editing:$store.editable.editing,
                  disabled:$store.editable.disabled,
                  readonly:$store.editable.readonly,
                  submitMode:$store.editable.submitMode,
                  actionPosition:$store.editable.actionPosition,
                  variant:$store.editable.variant,
                  size:$store.editable.size,
                  onValueChange:(next, detail) => {
                    $store.editable.values.push([next, detail.previousValue, detail.source, detail.controlled]);
                    if ($store.editable.acceptValue) $store.editable.value = next;
                  },
                  onEditChange:(next, detail) => {
                    $store.editable.edits.push([next, detail.reason, detail.controlled, detail.forced]);
                    if ($store.editable.acceptEdit) $store.editable.editing = next;
                  },
                }"
              />
              <button id="submit" type="submit">Submit</button>
              <button id="reset" type="reset">Reset</button>
            </form>
            <c-CEditable
              class_="outside-editable" value="Outside actions"
              action_position="outside" submit_mode="explicit"
            />
            <form id="required-form">
              <c-CEditable class_="required-editable" name="required-title" required />
              <button id="required-submit" type="submit">Validate</button>
            </form>
            <fieldset id="locked" disabled>
              <c-CEditable class_="locked-editable" value="Locked title" />
            </fieldset>
            <button id="after" type="button">After</button>
          </body></html>
        """
        js = """
          Alpine.store('editable', {
            value:'Project Atlas', editing:undefined, disabled:false, readonly:false,
            submitMode:'both', actionPosition:'inside', variant:'outline', size:'md',
            acceptValue:false, acceptEdit:false, values:[], edits:[], submits:[],
          });
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector(".primary-editable[data-citry-editable-initialized]")
    return errors


def _editable(page: Any, selector: str = ".primary-editable") -> Any:
    return page.locator(selector)


def test_default_inside_edit_submit_cancel_and_controlled_value(page: Any) -> None:
    errors = _load(page)
    root = _editable(page)
    edit = root.get_by_role("button", name="Edit")
    input_ = root.get_by_role("textbox")
    edit.click()
    assert root.get_attribute("data-editing") == ""
    assert input_.evaluate("element => element === document.activeElement") is True
    input_.fill("Project Aurora")
    root.get_by_role("button", name="Save").click()
    assert root.get_attribute("data-editing") is None
    assert root.locator('[data-citry-ui-part="preview-value"]').text_content() == "Project Atlas"
    assert page.evaluate("Alpine.store('editable').values.at(-1)") == [
        "Project Aurora",
        "Project Atlas",
        "submit",
        True,
    ]

    page.evaluate("Alpine.store('editable').acceptValue = true")
    edit.click()
    input_.fill("Project Aurora")
    input_.press("Enter")
    page.wait_for_function(
        "document.querySelector('.primary-editable "
        "[data-citry-ui-part=preview-value]').textContent === 'Project Aurora'"
    )
    edit.click()
    input_.fill("Discard me")
    input_.press("Escape")
    assert root.locator('[data-citry-ui-part="preview-value"]').text_content() == "Project Aurora"
    assert errors == []


def test_controlled_edit_reject_accept_release_and_blur(page: Any) -> None:
    errors = _load(page)
    root = _editable(page)
    edit = root.get_by_role("button", name="Edit")
    page.evaluate("Alpine.store('editable').editing = false")
    edit.click()
    assert root.get_attribute("data-editing") is None
    assert page.evaluate("Alpine.store('editable').edits.at(-1).slice(0,3)") == [True, "edit", True]

    page.evaluate("Alpine.store('editable').acceptEdit = true")
    edit.click()
    page.wait_for_function("document.querySelector('.primary-editable').hasAttribute('data-editing')")
    page.evaluate("Alpine.store('editable').editing = null")
    page.evaluate("Alpine.store('editable').value = undefined")
    page.wait_for_function("document.querySelector('.primary-editable').hasAttribute('data-editing')")
    input_ = root.get_by_role("textbox")
    input_.fill("Blur committed")
    page.locator("#after").focus()
    page.wait_for_function("!document.querySelector('.primary-editable').hasAttribute('data-editing')")
    assert root.locator('[data-citry-ui-part="preview-value"]').text_content() == "Blur committed"
    assert page.evaluate("Alpine.store('editable').values.at(-1)[2]") == "blur"
    assert errors == []


def test_native_form_reset_required_invalid_fieldset_and_outside_geometry(page: Any) -> None:
    errors = _load(page)
    root = _editable(page)
    page.evaluate("Alpine.store('editable').value = undefined")
    root.get_by_role("button", name="Edit").click()
    root.get_by_role("textbox").fill("Submitted title")
    root.get_by_role("button", name="Save").click()
    page.locator("#submit").click()
    assert page.evaluate("Alpine.store('editable').submits") == [["title", "Submitted title"]]
    page.locator("#reset").click()
    page.wait_for_function(
        "document.querySelector('.primary-editable "
        "[data-citry-ui-part=preview-value]').textContent === 'Project Atlas'"
    )

    page.locator("#required-submit").click()
    required = _editable(page, ".required-editable")
    assert required.get_attribute("data-editing") == ""
    assert required.get_attribute("data-invalid") == ""
    assert required.get_by_role("textbox").evaluate("element => element === document.activeElement") is True
    required.get_by_role("textbox").fill("Resolved")
    required.get_by_role("button", name="Save").click()

    locked = _editable(page, ".locked-editable")
    assert locked.get_attribute("data-disabled") == ""
    assert locked.get_by_role("button", name="Edit").is_disabled()
    page.locator("#locked").evaluate("element => element.disabled = false")
    page.wait_for_function("!document.querySelector('.locked-editable').hasAttribute('data-disabled')")
    assert locked.get_by_role("button", name="Edit").is_enabled()
    locked.get_by_role("button", name="Edit").click()
    page.wait_for_function("document.querySelector('.locked-editable').hasAttribute('data-editing')")

    outside = _editable(page, ".outside-editable")
    outside.get_by_role("button", name="Edit").click()
    input_box = outside.get_by_role("textbox").bounding_box()
    actions_box = outside.locator('[data-citry-ui-part="actions"]').bounding_box()
    assert actions_box["x"] >= input_box["x"] + input_box["width"] - 1
    assert errors == []


def test_inside_geometry_rtl_theme_forced_colors_print_and_axe(page: Any) -> None:
    errors = _load(page)
    root = _editable(page)
    root.get_by_role("button", name="Edit").click()
    input_box = root.get_by_role("textbox").bounding_box()
    actions_box = root.locator('[data-citry-ui-part="actions"]').bounding_box()
    assert actions_box["x"] + actions_box["width"] <= input_box["x"] + input_box["width"] + 1

    root.evaluate("element => element.dir = 'rtl'")
    rtl_input = root.get_by_role("textbox").bounding_box()
    rtl_actions = root.locator('[data-citry-ui-part="actions"]').bounding_box()
    assert rtl_actions["x"] - rtl_input["x"] < (
        rtl_input["x"] + rtl_input["width"] - (rtl_actions["x"] + rtl_actions["width"])
    )

    page.emulate_media(forced_colors="active")
    assert root.get_by_role("textbox").evaluate("element => getComputedStyle(element).borderStyle") == "solid"
    page.emulate_media(media="print")
    assert (
        root.locator('[data-citry-ui-part="preview"]').evaluate("element => getComputedStyle(element).display")
        == "block"
    )

    page.emulate_media(media="screen", forced_colors="none")
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
    assert errors == []
