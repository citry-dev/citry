"""Browser evidence for Form Collection requests, native forms, and cleanup."""

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
    raise RuntimeError("Could not locate repository root for Form Collection browser tests.")


_SNIPPETS = _root() / "packages/py/citry_ui/citry_ui/components/cform_collection/snippets"
_PREVIEW_NAMES = tuple(sorted(path.stem for path in _SNIPPETS.glob("*.py") if path.stem != "__init__"))


class FormCollectionPreviewDocument(Component):
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


def _wait_for_focus(locator: Any) -> None:
    locator.evaluate(
        """element => new Promise((resolve, reject) => {
          const deadline = Date.now() + 2_000;
          const check = () => {
            if (element === element.ownerDocument.activeElement) {
              resolve();
            } else if (Date.now() >= deadline) {
              reject(new Error('element did not receive focus'));
            } else {
              requestAnimationFrame(check);
            }
          };
          check();
        })"""
    )


def _preview_document(name: str) -> str:
    # Family tests execute each shipped snippet directly, so preview membership
    # can change without locking the public documentation page into a test.
    module = importlib.import_module(f"citry_ui.components.cform_collection.snippets.{name}")
    preview = module.preview
    return (
        FormCollectionPreviewDocument(
            title=name.replace("_", " ").title(),
            content=preview,
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
    page.wait_for_selector('[data-citry-ui-part="form-collection"]')
    return errors


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8"><title>Form Collection evidence</title><c-css /></head>
          <body x-data>
            <form id="server" @submit.prevent="$store.collection.submits.push($event.submitter.value)">
              <c-CFormCollection id="contacts" label="Contacts" action_name="contact_action" c-min_items="1"
                $c-props="{onAction:(detail)=>$store.collection.actions.push([detail.action,detail.value,detail.index,detail.toIndex])}">
                <c-CFormCollectionItem value="a" label="Primary"><input aria-label="Primary email" name="contacts[a][email]" type="email" required /></c-CFormCollectionItem>
                <c-CFormCollectionItem value="b" label="Backup"><input aria-label="Backup email" name="contacts[b][email]" /></c-CFormCollectionItem>
              </c-CFormCollection>
            </form>
            <c-CFormCollection id="client" label="Client rows" $c-props="{disabled:$store.collection.disabled,onAction:(detail)=>$store.collection.client=detail.action}">
              <c-CFormCollectionItem value="one" label="One"><input aria-label="One value" /></c-CFormCollectionItem>
            </c-CFormCollection>
          </body></html>
        """
        js = "Alpine.store('collection',{actions:[],submits:[],client:'',disabled:false});"

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector("#contacts[data-citry-form-collection-initialized]")
    page.wait_for_selector("#client[data-citry-form-collection-initialized]")
    return errors


def test_named_actions_bypass_validation_and_report_exact_details(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#contacts")
    root.locator('[data-value="a"] [data-citry-form-collection-action="move-down"]').click()
    root.locator('[data-value="b"] [data-citry-form-collection-action="remove"]').click()
    root.locator('[data-citry-ui-part="add"]').click()
    assert page.evaluate("Alpine.store('collection').actions") == [
        ["move-down", "a", 0, 1],
        ["remove", "b", 1, None],
        ["add", None, None, None],
    ]
    assert page.evaluate("Alpine.store('collection').submits") == ["move-down:a", "remove:b", "add"]
    assert page.locator('[name="contacts[a][email]"]').evaluate("element => element.validity.valueMissing") is True
    assert errors == []


def test_client_buttons_reactive_disabled_environment_axe_and_cleanup(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#client")
    add = root.locator('[data-citry-ui-part="add"]')
    assert add.get_attribute("type") == "button"
    add.click()
    assert page.evaluate("Alpine.store('collection').client") == "add"
    page.evaluate("Alpine.store('collection').disabled=true")
    page.wait_for_function("document.querySelector('#client').hasAttribute('data-disabled')")
    assert add.is_disabled()
    assert root.locator("input").is_enabled()

    page.emulate_media(forced_colors="active", reduced_motion="reduce")
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
    root.evaluate("element => element.remove()")
    page.wait_for_timeout(30)
    assert errors == []


def test_client_owned_preview_adds_reorders_parks_and_restores_any_number_of_items(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, "client_actions")
    collection = page.locator('[data-citry-ui-part="form-collection"]')
    item_selector = ':scope > [data-citry-ui-part="items"] > [data-citry-form-collection-item]'
    items = collection.locator(item_selector)
    mobile = collection.locator(f'{item_selector}[data-value="mobile"]')
    office = collection.locator(f'{item_selector}[data-value="office"]')
    add = collection.locator('[data-citry-ui-part="add"]')

    # Five consecutive additions prove that Add is not a one-row restore toggle.
    for _ in range(5):
        assert add.is_enabled()
        add.click()
    assert items.count() == 7
    assert items.evaluate_all("nodes => nodes.map(node => node.dataset.value)") == [
        "mobile",
        "office",
        "phone-3",
        "phone-4",
        "phone-5",
        "phone-6",
        "phone-7",
    ]
    assert page.locator('input[name^="phones["]').count() == 7

    mobile_input = page.locator('input[name="phones[mobile]"]')
    mobile_input.fill("+420 555 0100")
    mobile.evaluate("item => { window.__formCollectionMobile = item; }")
    move_down = mobile.locator('[data-citry-form-collection-action="move-down"]')
    move_down.click()
    assert items.first.get_attribute("data-value") == "office"
    assert mobile.evaluate("item => item === window.__formCollectionMobile") is True
    assert mobile_input.input_value() == "+420 555 0100"
    _wait_for_focus(mobile.locator('[data-citry-form-collection-action="move-up"]'))

    mobile.locator('[data-citry-form-collection-action="move-up"]').click()
    assert items.first.get_attribute("data-value") == "mobile"
    assert mobile.evaluate("item => item === window.__formCollectionMobile") is True
    assert mobile_input.input_value() == "+420 555 0100"
    _wait_for_focus(move_down)

    mobile.locator('[data-citry-form-collection-action="remove"]').click()
    assert items.count() == 6
    assert office.count() == 1
    assert mobile_input.evaluate("input => input.disabled") is False
    assert mobile_input.evaluate("input => input.matches(':disabled')") is True
    _wait_for_focus(add)

    add.click()
    assert items.count() == 7
    assert mobile.evaluate("item => item === window.__formCollectionMobile") is True
    assert mobile_input.input_value() == "+420 555 0100"
    assert mobile_input.evaluate("input => input.disabled") is False
    assert mobile_input.evaluate("input => input.matches(':disabled')") is False
    _wait_for_focus(mobile.locator('[data-citry-form-collection-action="move-up"]'))
    assert add.is_enabled()
    add.click()
    assert items.count() == 8
    assert collection.locator(f'{item_selector}[data-value="phone-8"]').count() == 1
    assert errors == []


def test_server_owned_preview_preserves_native_form_values_while_items_are_parked(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    errors = _open_preview(page, serve_citry_ui_live, "server_actions")
    collection = page.locator('[data-citry-ui-part="form-collection"]')
    item_selector = ':scope > [data-citry-ui-part="items"] > [data-citry-form-collection-item]'
    items = collection.locator(item_selector)
    role = page.locator('input[name="members[member-17][role]"]')
    role.fill("Editor")
    initial_path = page.locator("body").evaluate("() => location.pathname")

    items.first.locator('[data-citry-form-collection-action="remove"]').click()
    assert items.count() == 0
    assert role.evaluate("input => input.disabled") is False
    assert role.evaluate("input => input.matches(':disabled')") is True
    assert page.locator("form").evaluate("form => [...new FormData(form).keys()]") == []

    collection.locator('[data-citry-ui-part="add"]').click()
    assert items.count() == 1
    assert role.evaluate("input => input.disabled") is False
    assert role.evaluate("input => input.matches(':disabled')") is False
    assert role.input_value() == "Editor"
    assert page.locator("form").evaluate("form => [...new FormData(form).keys()]") == [
        "members[member-17][id]",
        "members[member-17][role]",
    ]

    save = page.get_by_role("button", name="Save team")
    save.click()
    assert page.locator("output").inner_text() == "Saved locally"
    assert page.locator("body").evaluate("() => location.pathname") == initial_path
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
          const result = await axe.run(document, { resultTypes: ['violations'] });
          return result.violations.filter(
            violation => violation.impact === 'serious' || violation.impact === 'critical'
          );
        }"""
    )
    assert violations == [], f"Form Collection preview {preview_name} has high-impact axe findings"
    assert errors == []
