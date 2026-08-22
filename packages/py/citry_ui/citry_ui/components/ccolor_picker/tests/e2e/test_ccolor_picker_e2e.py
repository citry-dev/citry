"""Browser evidence for Color Picker formats, forms, keyboard, and cleanup."""

# ruff: noqa: E501 - embedded templates and browser expressions remain readable

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component
from citry_ui import CColorSwatch

pytestmark = pytest.mark.e2e


def _root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate repository root for Color Picker browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app

        def template_data(self, _kwargs, _slots):
            return {"swatches": [CColorSwatch("#7f56d9", "Violet"), CColorSwatch("#12b76a", "Green")]}

        template = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Color Picker evidence</title><c-css /></head><body x-data><form><c-CColorPicker id="picker" label="Brand color" name="brand" value="#7f56d9" c-swatches="swatches" $c-props="{onValueChange:(value,detail)=>$store.color.changes.push([value,detail.source]),onOpenChange:(open)=>$store.color.opens.push(open)}" /><button type="reset">Reset</button></form></body></html>"""
        js = "Alpine.store('color',{changes:[],opens:[]});"

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector("#picker[data-citry-color-picker-initialized]")
    return errors


def test_keyboard_text_swatch_and_form_value(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#picker")
    root.locator('[data-citry-ui-part="trigger"]').click()
    area = root.locator('[data-citry-ui-part="area"]')
    area.focus()
    area.press("Home")
    assert page.evaluate("Alpine.store('color').changes.at(-1)[1]") == "area"
    format_select = root.locator('[data-citry-ui-part="format"]')
    format_select.select_option("rgb")
    text_input = root.locator('[data-citry-ui-part="input"]')
    text_input.fill("18, 183, 106")
    text_input.press("Enter")
    assert root.locator('input[type="color"]').input_value() == "#12b76a"
    root.locator('[data-citry-color-swatch][data-value="#7f56d9"]').click()
    assert root.locator('input[name="brand"]').input_value() == "#7f56d9"
    assert page.evaluate("Alpine.store('color').changes.at(-1)") == ["#7f56d9", "swatch"]
    assert errors == []


def test_invalid_edit_environment_axe_and_cleanup(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#picker")
    root.locator('[data-citry-ui-part="trigger"]').click()
    text_input = root.locator('[data-citry-ui-part="input"]')
    text_input.fill("not a color")
    text_input.press("Enter")
    assert text_input.get_attribute("aria-invalid") == "true"
    assert root.locator('[data-citry-ui-part="status"]').inner_text() == "Enter a valid color value"
    page.emulate_media(forced_colors="active", reduced_motion="reduce")
    page.add_script_tag(path=str(_root() / "node_modules" / "axe-core" / "axe.min.js"))
    violations = page.evaluate(
        """async()=> (await axe.run(document,{resultTypes:['violations']})).violations.filter(x=>['serious','critical'].includes(x.impact)).map(x=>x.id)"""
    )
    assert violations == []
    root.evaluate("element=>element.remove()")
    page.wait_for_timeout(30)
    assert errors == []
