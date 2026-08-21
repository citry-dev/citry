"""Browser evidence for Transfer List interaction, forms, and cleanup."""

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
    raise RuntimeError("Could not locate repository root for Transfer List browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8">
          <title>Transfer List evidence</title><c-css /></head>
          <body x-data>
            <form id="assignment">
              <c-CTransferList
                id="people"
                name="reviewers"
                c-required="True"
                c-value="['locked','grace']"
              >
                <c-CTransferListItem value="ada" label="Ada Lovelace" />
                <c-CTransferListItem value="grace" label="Grace Hopper" />
                <c-CTransferListItem value="katherine" label="Katherine Johnson" />
                <c-CTransferListItem value="locked" label="Policy reviewer" c-disabled="True" />
              </c-CTransferList>
              <button id="reset" type="reset">Reset</button>
            </form>

            <form id="empty-form">
              <c-CTransferList id="required-empty" name="required-reviewer" c-required="True">
                <c-CTransferListItem value="one" label="One" />
              </c-CTransferList>
            </form>

            <c-CTransferList
              id="controlled"
              $c-props="{
                value:$store.transfer.value,
                onValueChange:(next,detail)=>{
                  $store.transfer.events.push({next:[...next],source:detail.source,controlled:detail.controlled});
                  if($store.transfer.accept)$store.transfer.value=[...next];
                },
              }"
            >
              <c-CTransferListItem value="alpha" label="Alpha" />
              <c-CTransferListItem value="beta" label="Beta" />
              <c-CTransferListItem value="gamma" label="Gamma" />
            </c-CTransferList>
          </body></html>
        """
        js = """
          Alpine.store('transfer', {value:['beta'],accept:false,events:[]});
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    for selector in ("#people", "#required-empty", "#controlled"):
        page.wait_for_selector(f"{selector}[data-citry-transfer-list-initialized]")
    return errors


def _pane(root: Any, name: str) -> Any:
    return root.locator(f'[data-citry-transfer-pane="{name}"]')


def _values(root: Any, name: str) -> list[str]:
    return (
        _pane(root, name)
        .locator(':scope [data-citry-ui-part="listbox"] > [data-value]')
        .evaluate_all("elements => elements.map(element => element.dataset.value)")
    )


def test_uncontrolled_transfer_reorder_form_order_and_reset(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#people")
    available = _pane(root, "available")
    chosen = _pane(root, "chosen")

    assert _values(root, "available") == ["ada", "katherine"]
    assert _values(root, "chosen") == ["locked", "grace"]
    assert page.evaluate("[...new FormData(document.querySelector('#assignment')).getAll('reviewers')]") == [
        "locked",
        "grace",
    ]

    available.locator('[data-value="ada"]').click()
    assert available.locator('[data-value="ada"]').get_attribute("aria-selected") == "true"
    root.locator('[data-citry-transfer-action="add"]').click()
    assert _values(root, "chosen") == ["locked", "grace", "ada"]
    assert page.evaluate("[...new FormData(document.querySelector('#assignment')).getAll('reviewers')]") == [
        "locked",
        "grace",
        "ada",
    ]

    root.locator('[data-citry-transfer-action="move-top"]').click()
    assert _values(root, "chosen") == ["ada", "locked", "grace"]
    assert chosen.locator('[data-value="ada"]').evaluate("element => document.activeElement === element.parentElement")

    page.locator("#reset").click()
    page.wait_for_function(
        "[...document.querySelector('#people').querySelectorAll('[data-citry-transfer-pane=chosen] [data-value]')]"
        ".map(element=>element.dataset.value).join(',') === 'locked,grace'"
    )
    assert page.evaluate("[...new FormData(document.querySelector('#assignment')).getAll('reviewers')]") == [
        "locked",
        "grace",
    ]
    assert errors == []


def test_keyboard_selection_typeahead_and_disabled_item(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#people")
    available_list = _pane(root, "available").locator('[data-citry-ui-part="listbox"]')
    chosen = _pane(root, "chosen")

    available_list.focus()
    page.keyboard.press("k")
    assert available_list.get_attribute("aria-activedescendant") == "people-option-2"
    page.keyboard.press("Space")
    assert _pane(root, "available").locator('[data-value="katherine"]').get_attribute("aria-selected") == "true"
    root.locator('[data-citry-transfer-action="add"]').click()
    assert _values(root, "chosen") == ["locked", "grace", "katherine"]

    chosen.locator('[data-value="katherine"]').click()
    locked = chosen.locator('[data-value="locked"]')
    locked.click(force=True)
    assert locked.get_attribute("aria-selected") == "false"
    assert root.locator('[data-citry-transfer-action="remove"]').is_disabled()
    assert errors == []


def test_controlled_requests_wait_for_acceptance_and_required_focuses_chosen(page: Any) -> None:
    errors = _load(page)
    controlled = page.locator("#controlled")
    available = _pane(controlled, "available")

    available.locator('[data-value="alpha"]').click()
    controlled.locator('[data-citry-transfer-action="add"]').click()
    assert _values(controlled, "chosen") == ["beta"]
    assert page.evaluate("Alpine.store('transfer').events") == [
        {"next": ["beta", "alpha"], "source": "add", "controlled": True}
    ]

    page.evaluate(
        "Alpine.store('transfer').accept=true;"
        "Alpine.store('transfer').value=[...Alpine.store('transfer').events[0].next]"
    )
    page.wait_for_function(
        "[...document.querySelector('#controlled').querySelectorAll('[data-citry-transfer-pane=chosen] [data-value]')]"
        ".map(element=>element.dataset.value).join(',') === 'beta,alpha'"
    )

    valid = page.evaluate("document.querySelector('#empty-form').reportValidity()")
    assert valid is False
    required = page.locator("#required-empty")
    assert required.get_attribute("data-invalid") == ""
    assert (
        _pane(required, "chosen")
        .locator('[data-citry-ui-part="listbox"]')
        .evaluate("element => document.activeElement === element")
    )
    assert errors == []


def test_environment_axe_and_cleanup(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#people")
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []

    page.emulate_media(forced_colors="active", reduced_motion="reduce")
    assert root.evaluate("element => getComputedStyle(element).containerType") == "inline-size"

    page.set_viewport_size({"width": 420, "height": 900})
    columns = root.locator(':scope > [data-citry-ui-part="control"]').evaluate(
        "element => getComputedStyle(element).gridTemplateColumns"
    )
    assert columns.count("px") == 1

    root.evaluate("element => element.remove()")
    page.wait_for_timeout(50)
    assert errors == []
