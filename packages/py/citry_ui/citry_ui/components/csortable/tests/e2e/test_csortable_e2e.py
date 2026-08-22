"""Browser evidence for Sortable interaction, control, forms, and cleanup."""

# ruff: noqa: E501 - embedded templates and browser expressions remain readable

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
    raise RuntimeError("Could not locate repository root for Sortable browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8">
          <title>Sortable evidence</title><c-css /></head><body x-data>
            <form id="uncontrolled-form">
              <c-CSortable id="uncontrolled" name="priority">
                <c-CSortableItem value="alpha" label="Alpha" />
                <c-CSortableItem value="fixed" label="Fixed" c-disabled="True" />
                <c-CSortableItem value="beta" label="Beta" />
                <c-CSortableItem value="gamma" label="Gamma" />
              </c-CSortable>
              <button id="reset" type="reset">Reset</button>
            </form>
            <c-CSortable id="controlled" $c-props="{
              order:$store.sortable.order,
              onOrderChange:(next,detail)=>{
                $store.sortable.events.push({next:[...next],source:detail.source,controlled:detail.controlled});
                if($store.sortable.accept)$store.sortable.order=[...next];
              },
            }">
              <c-CSortableItem value="one" label="One" />
              <c-CSortableItem value="two" label="Two" />
              <c-CSortableItem value="three" label="Three" />
            </c-CSortable>
            <div dir="rtl"><c-CSortable id="grid" layout="grid">
              <c-CSortableItem value="r1" label="RTL one" />
              <c-CSortableItem value="r2" label="RTL two" />
              <c-CSortableItem value="r3" label="RTL three" />
            </c-CSortable></div>
          </body></html>
        """
        js = "Alpine.store('sortable',{order:['one','two','three'],accept:false,events:[]});"

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    for selector in ("#uncontrolled", "#controlled", "#grid"):
        page.wait_for_selector(f"{selector}[data-citry-sortable-initialized]")
    return errors


def _values(root: Any) -> list[str]:
    return root.locator(":scope > [data-citry-sortable-items] > [data-value]").evaluate_all(
        "elements => elements.map(element => element.dataset.value)"
    )


def test_keyboard_commit_cancel_disabled_form_order_and_reset(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#uncontrolled")
    alpha = root.locator('[data-value="alpha"] [data-citry-sortable-handle]')
    alpha.focus()
    alpha.press("Space")
    alpha.press("ArrowDown")
    alpha.press("ArrowDown")
    alpha.press("Space")
    assert _values(root) == ["fixed", "beta", "alpha", "gamma"]
    assert page.evaluate("[...new FormData(document.querySelector('#uncontrolled-form')).getAll('priority')]") == [
        "fixed",
        "beta",
        "alpha",
        "gamma",
    ]
    assert "Dropped Alpha" in root.locator('[data-citry-ui-part="status"]').text_content()

    alpha.press("Space")
    alpha.press("End")
    alpha.press("Escape")
    assert _values(root) == ["fixed", "beta", "alpha", "gamma"]
    assert root.locator('[data-value="fixed"] button').is_disabled()

    page.locator("#reset").click()
    page.wait_for_function(
        "[...document.querySelectorAll('#uncontrolled > ol > [data-value]')].map(e=>e.dataset.value).join(',') === 'alpha,fixed,beta,gamma'"
    )
    assert errors == []


def test_controlled_keyboard_request_waits_then_accepts(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#controlled")
    handle = root.locator('[data-value="one"] [data-citry-sortable-handle]')
    handle.focus()
    handle.press("Enter")
    handle.press("End")
    handle.press("Enter")
    assert _values(root) == ["one", "two", "three"]
    assert page.evaluate("Alpine.store('sortable').events") == [
        {"next": ["two", "three", "one"], "source": "keyboard", "controlled": True}
    ]
    page.evaluate(
        "Alpine.store('sortable').accept=true;"
        "Alpine.store('sortable').order=[...Alpine.store('sortable').events[0].next]"
    )
    page.wait_for_function(
        "[...document.querySelectorAll('#controlled > ol > [data-value]')].map(e=>e.dataset.value).join(',') === 'two,three,one'"
    )
    assert "Dropped One" in root.locator('[data-citry-ui-part="status"]').text_content()
    assert errors == []


def test_pointer_grid_environment_axe_and_cleanup(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#uncontrolled")
    alpha = root.locator('[data-value="alpha"] [data-citry-sortable-handle]')
    gamma = root.locator('[data-value="gamma"]')
    start = alpha.bounding_box()
    end = gamma.bounding_box()
    assert start is not None
    assert end is not None
    page.mouse.move(start["x"] + start["width"] / 2, start["y"] + start["height"] / 2)
    page.mouse.down()
    page.mouse.move(end["x"] + end["width"] / 2, end["y"] + end["height"] - 2, steps=4)
    page.mouse.up()
    assert _values(root)[-1] == "alpha"

    grid = page.locator("#grid")
    assert grid.evaluate("element => getComputedStyle(element).direction") == "rtl"
    page.emulate_media(forced_colors="active", reduced_motion="reduce")
    assert alpha.evaluate("element => parseFloat(getComputedStyle(element).transitionDuration) || 0") <= 0.001
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
