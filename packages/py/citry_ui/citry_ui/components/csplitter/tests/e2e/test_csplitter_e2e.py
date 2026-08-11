"""Browser evidence for Splitter resizing and accessibility."""

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
    raise RuntimeError("Could not locate repository root for Splitter browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = ".brand-splitter { --cui-splitter-radius: 19px; --cui-splitter-handle-active-color: rgb(127 86 217); }"
        template = """
          <!doctype html>
          <html lang="en"><head><meta charset="utf-8"><title>Splitter evidence</title><c-css /></head>
          <body x-data>
            <form @submit.prevent="$store.splitter.submits += 1">
              <c-CSplitter
                c-sizes="[30, 70]"
                class_="brand-splitter"
                variant="outline"
                c-keyboard_step="5"
                $c-props="{
                  sizes: $store.splitter.sizes,
                  orientation: $store.splitter.orientation,
                  disabled: $store.splitter.disabled,
                  onResizeStart: (detail) => $store.splitter.events.push(['start', detail.source]),
                  onResize: (next, detail) => {
                    $store.splitter.events.push(['resize', detail.source, ...next]);
                    if ($store.splitter.accept) $store.splitter.sizes = next;
                  },
                  onResizeEnd: (next, detail) => $store.splitter.events.push(['end', detail.source, ...next]),
                }"
              >
                <c-CSplitterPanel id="nav" label="Navigation" c-min_size="20" c-max_size="50">
                  <button id="inside" type="submit">Inside</button>
                </c-CSplitterPanel>
                <c-CSplitterPanel id="main" label="Main" c-min_size="40">Main</c-CSplitterPanel>
              </c-CSplitter>
              <button id="submit" type="submit">Submit</button>
            </form>

            <fieldset id="fieldset" disabled>
              <legend>Locked</legend>
              <c-CSplitter>
                <c-CSplitterPanel id="fa" label="Field A">A</c-CSplitterPanel>
                <c-CSplitterPanel id="fb" label="Field B">B</c-CSplitterPanel>
              </c-CSplitter>
            </fieldset>

            <div dir="rtl" style="inline-size:320px">
              <c-CSplitter c-sizes="[40, 60]" variant="soft">
                <c-CSplitterPanel id="rtl-a" label="RTL A">A</c-CSplitterPanel>
                <c-CSplitterPanel id="rtl-b" label="RTL B">B</c-CSplitterPanel>
              </c-CSplitter>
            </div>
          </body></html>
        """
        js = """
          Alpine.store('splitter', {
            sizes: [30, 70], orientation: 'horizontal', disabled: false,
            accept: false, events: [], submits: 0,
          });
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector(".brand-splitter[data-citry-splitter-initialized]")
    return errors


def test_controlled_keyboard_callbacks_constraints_and_form_safety(page: Any) -> None:
    errors = _load(page)
    root = page.locator(".brand-splitter")
    handle = root.locator('[data-citry-ui-part="handle"]')
    handle.focus()
    handle.press("ArrowRight")
    assert handle.get_attribute("aria-valuenow") == "30"
    assert page.evaluate("Alpine.store('splitter').events")[:3] == [
        ["start", "keyboard"],
        ["resize", "keyboard", 35, 65],
        ["end", "keyboard", 35, 65],
    ]
    page.evaluate("Alpine.store('splitter').accept = true")
    handle.press("Shift+ArrowRight")
    page.wait_for_function(
        "document.querySelector('.brand-splitter [role=separator]').getAttribute('aria-valuenow') === '50'"
    )
    handle.press("End")
    assert handle.get_attribute("aria-valuenow") == "50"
    assert page.evaluate("Alpine.store('splitter').submits") == 0
    page.locator("#inside").click()
    assert page.evaluate("Alpine.store('splitter').submits") == 1
    assert errors == []


def test_pointer_drag_reactive_orientation_fieldset_rtl_and_css(page: Any) -> None:
    errors = _load(page)
    root = page.locator(".brand-splitter")
    handle = root.locator('[data-citry-ui-part="handle"]')
    page.evaluate("Alpine.store('splitter').accept = true")
    box = handle.bounding_box()
    assert box is not None
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] / 2 + 30, box["y"] + box["height"] / 2)
    page.mouse.up()
    page.wait_for_function(
        "Number(document.querySelector('.brand-splitter [role=separator]').getAttribute('aria-valuenow')) > 30"
    )
    assert any(event[:2] == ["start", "pointer"] for event in page.evaluate("Alpine.store('splitter').events"))
    assert any(event[:2] == ["end", "pointer"] for event in page.evaluate("Alpine.store('splitter').events"))

    page.evaluate("Alpine.store('splitter').orientation = 'vertical'")
    page.wait_for_function("document.querySelector('.brand-splitter').dataset.orientation === 'vertical'")
    assert handle.get_attribute("aria-orientation") == "horizontal"
    assert root.evaluate("element => getComputedStyle(element).borderRadius") == "19px"

    field = page.locator("#fieldset [data-citry-ui-part=splitter]")
    field_handle = field.locator("[role=separator]")
    assert field_handle.get_attribute("aria-disabled") == "true"
    assert field_handle.get_attribute("tabindex") == "-1"
    page.locator("#fieldset").evaluate("element => element.disabled = false")
    page.wait_for_function("document.querySelector('#fieldset [role=separator]').getAttribute('tabindex') === '0'")

    rtl_handle = page.locator("[dir=rtl] [role=separator]")
    before = float(rtl_handle.get_attribute("aria-valuenow"))
    rtl_handle.focus()
    rtl_handle.press("ArrowRight")
    page.wait_for_timeout(20)
    assert float(rtl_handle.get_attribute("aria-valuenow")) < before
    assert errors == []


def test_structure_recovery_environment_cleanup_and_axe(page: Any) -> None:
    errors = _load(page)
    root = page.locator(".brand-splitter")
    root.evaluate("element => element.append(document.createElement('div'))")
    page.wait_for_function(
        "!document.querySelector('.brand-splitter').hasAttribute('data-citry-splitter-initialized')"
    )
    assert any("CSplitter structure" in error for error in errors)
    root.locator(":scope > div:last-child").evaluate("element => element.remove()")
    page.wait_for_selector(".brand-splitter[data-citry-splitter-initialized]")

    page.emulate_media(reduced_motion="reduce")
    assert (
        root.locator("[role=separator]").evaluate(
            "element => parseFloat(getComputedStyle(element).transitionDuration) || 0"
        )
        <= 0.001
    )
    assert root.evaluate("element => element.scrollWidth <= element.clientWidth")
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
    assert [error for error in errors if "CSplitter structure" not in error] == []
