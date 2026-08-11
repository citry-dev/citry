"""Browser evidence for native file selection and drop behavior."""

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
    raise RuntimeError("Could not locate repository root for FileInput browser tests.")


def _file_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.file-brand) {
            --cui-file-input-radius: 19px;
            --cui-file-input-active-color: rgb(18 112 72);
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><title>File controls</title><c-css /></head>
            <body x-data>
              <form id="upload-form">
                <c-CField control_id="field-file" required>
                  <c-fill name="label">Primary evidence</c-fill>
                  <c-fill name="default">
                    <c-CFileInput
                      name="primary"
                      accept="application/pdf"
                      class_="file-brand"
                      $c-props="{
                        accept: $store.fileTest.accept,
                        multiple: $store.fileTest.multiple,
                        variant: $store.fileTest.variant,
                      }"
                      @input="$store.fileTest.events.push(['file-input', $event.target.files.length])"
                    />
                  </c-fill>
                  <c-fill name="description">One supporting file.</c-fill>
                  <c-fill name="error">Choose evidence.</c-fill>
                </c-CField>

                <c-CDropTarget
                  label="Supporting evidence"
                  name="supporting"
                  multiple
                  variant="soft"
                  c-input_attrs="{'form': 'upload-form'}"
                  @input="$store.fileTest.events.push([
                    'input', $event.target.files.length, $event.currentTarget.tagName
                  ])"
                  @change="$store.fileTest.events.push([
                    'change', $event.target.files.length, $event.currentTarget.tagName
                  ])"
                >
                  PDF or image files
                </c-CDropTarget>

                <c-CDropTarget
                  label="One attachment"
                  name="single"
                  c-input_attrs="{'form': 'upload-form'}"
                  c-attrs="{'id': 'single-drop'}"
                />
                <button id="reset" type="reset">Reset</button>
              </form>

              <fieldset id="disabled-fieldset" disabled>
                <legend>Disabled files</legend>
                <c-CDropTarget
                  label="Disabled target"
                  name="disabled-file"
                  c-disabled="False"
                  c-attrs="{'id': 'disabled-drop'}"
                />
              </fieldset>
            </body>
          </html>
        """

        def js_data(self, kwargs, slots):
            return {}

        js = """
          Alpine.store('fileTest', {
            accept: 'application/pdf',
            multiple: false,
            variant: 'outline',
            events: [],
          });
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_file_page(), wait_until="load")
    page.wait_for_selector("#field-file[data-citry-file-input-initialized]")
    page.wait_for_selector('[data-citry-ui-part="drop-target"][data-citry-drop-target-initialized]')
    return errors


def _drop_files(page: Any, selector: str, files: list[dict[str, str]]) -> None:
    page.locator(selector).evaluate(
        """(element, files) => {
          const transfer = new DataTransfer();
          files.forEach(file => transfer.items.add(new File([file.body], file.name, {type: file.type})));
          element.dispatchEvent(new DragEvent('dragenter', {bubbles: true, dataTransfer: transfer}));
          element.dispatchEvent(new DragEvent('dragover', {bubbles: true, dataTransfer: transfer}));
          element.dispatchEvent(new DragEvent('drop', {bubbles: true, dataTransfer: transfer}));
        }""",
        files,
    )


def test_native_picker_field_validity_formdata_reset_and_reactive_config(page: Any) -> None:
    errors = _load(page)
    field_input = page.locator("#field-file")
    field_root = page.locator('[data-citry-ui-part="field"]')
    assert field_input.evaluate("element => element.reportValidity()") is False
    assert field_root.get_attribute("data-invalid") == ""

    field_input.set_input_files({"name": "evidence.pdf", "mimeType": "application/pdf", "buffer": b"report"})
    assert field_input.get_attribute("data-has-files") == ""
    assert field_root.get_attribute("data-invalid") is None
    assert page.locator("#upload-form").evaluate("form => new FormData(form).get('primary').name") == "evidence.pdf"

    page.evaluate("Object.assign(Alpine.store('fileTest'), {accept: 'image/*', multiple: true, variant: 'soft'})")
    page.wait_for_function("document.querySelector('#field-file').multiple")
    assert field_input.get_attribute("accept") == "image/*"
    assert field_input.get_attribute("data-variant") == "soft"
    assert field_input.evaluate("element => getComputedStyle(element).borderRadius") == "19px"

    page.locator("#reset").click()
    page.wait_for_function("document.querySelector('#field-file').files.length === 0")
    page.wait_for_function("!document.querySelector('#field-file').hasAttribute('data-has-files')")
    assert field_input.get_attribute("data-has-files") is None
    assert errors == []


def test_drop_assigns_native_filelist_and_dispatches_input_then_change(page: Any) -> None:
    errors = _load(page)
    drop = page.get_by_text("Supporting evidence", exact=True).locator("..")
    _drop_files(
        page,
        '[data-citry-ui-part="drop-target"]:has-text("Supporting evidence")',
        [
            {"name": "first.pdf", "type": "application/pdf", "body": "first"},
            {"name": "second.png", "type": "image/png", "body": "second"},
        ],
    )
    input_element = drop.locator('[data-citry-ui-part="input"]')
    assert input_element.evaluate("element => [...element.files].map(file => file.name)") == [
        "first.pdf",
        "second.png",
    ]
    assert drop.get_attribute("data-has-files") == ""
    assert page.evaluate("Alpine.store('fileTest').events.slice(-2)") == [
        ["input", 2, "LABEL"],
        ["change", 2, "LABEL"],
    ]
    assert page.locator("#upload-form").evaluate(
        "form => new FormData(form).getAll('supporting').map(file => file.name)"
    ) == ["first.pdf", "second.png"]
    assert errors == []


def test_single_drop_disabled_fieldset_and_drag_reflection(page: Any) -> None:
    errors = _load(page)
    single = page.locator("#single-drop")
    single.evaluate(
        """element => {
          const transfer = new DataTransfer();
          transfer.items.add(new File(['a'], 'a.txt', {type: 'text/plain'}));
          element.dispatchEvent(new DragEvent('dragenter', {bubbles: true, dataTransfer: transfer}));
        }"""
    )
    assert single.get_attribute("data-dragging") == ""
    single.evaluate(
        """element => {
          const transfer = new DataTransfer();
          transfer.items.add(new File(['a'], 'a.txt', {type: 'text/plain'}));
          element.dispatchEvent(new DragEvent('dragleave', {bubbles: true, dataTransfer: transfer}));
        }"""
    )
    assert single.get_attribute("data-dragging") is None
    _drop_files(
        page,
        "#single-drop",
        [
            {"name": "a.txt", "type": "text/plain", "body": "a"},
            {"name": "b.txt", "type": "text/plain", "body": "b"},
        ],
    )
    assert single.locator("input").evaluate("element => [...element.files].map(file => file.name)") == ["a.txt"]

    disabled = page.locator("#disabled-drop")
    assert disabled.get_attribute("data-disabled") == ""
    _drop_files(
        page,
        "#disabled-drop",
        [{"name": "ignored.txt", "type": "text/plain", "body": "ignored"}],
    )
    assert disabled.locator("input").evaluate("element => element.files.length") == 0
    page.locator("#disabled-fieldset").evaluate("element => element.disabled = false")
    page.wait_for_function("!document.querySelector('#disabled-drop').hasAttribute('data-disabled')")
    assert errors == []


def test_structure_recovery_focus_environment_and_axe(page: Any) -> None:
    errors = _load(page)
    single = page.locator("#single-drop")
    single.locator("input").focus()
    assert single.evaluate("element => element.matches(':focus-within')") is True
    single.evaluate("element => element.append(document.createElement('button'))")
    page.wait_for_function(
        "!document.querySelector('#single-drop').hasAttribute('data-citry-drop-target-initialized')"
    )
    assert single.locator("input").is_disabled()
    assert any("CDropTarget structure" in error for error in errors)
    single.locator("button").evaluate("element => element.remove()")
    page.wait_for_selector("#single-drop[data-citry-drop-target-initialized]")
    assert single.locator("input").is_enabled()

    page.emulate_media(reduced_motion="reduce")
    assert single.evaluate("element => getComputedStyle(element).transitionDuration") == "0s"
    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe_path))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes: ['violations']})).violations
          .filter(item => ['serious', 'critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
