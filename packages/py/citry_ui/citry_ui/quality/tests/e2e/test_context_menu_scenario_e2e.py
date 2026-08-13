"""Public ContextMenu evidence through its reusable quality scenario."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry_ui.quality.routes import build_scenario, render_scenario

pytestmark = pytest.mark.e2e


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    msg = "Could not find the Citry repository root from the ContextMenu quality test."
    raise RuntimeError(msg)


def _wait_for_all_ready(page: Any) -> None:
    page.wait_for_function(
        """() => {
          const roots = document.querySelectorAll('[data-citry-ui-part="context-menu"]');
          const ready = document.querySelectorAll(
            '[data-citry-ui-part="context-menu"][data-citry-context-menu-initialized]',
          );
          return roots.length > 0 && ready.length === roots.length;
        }"""
    )


def _record_context_default(page: Any, selector: str, key: str) -> None:
    page.evaluate(
        """([selector, key]) => {
          const target = document.querySelector(selector);
          window[key] = null;
          target.addEventListener('contextmenu', (event) => {
            setTimeout(() => {
              window[key] = {
                defaultPrevented: event.defaultPrevented,
                trusted: event.isTrusted,
              };
            });
          }, {once: true});
        }""",
        [selector, key],
    )


def test_context_menu_quality_invocation_native_paths_layers_and_axe(page: Any) -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.set_content(render_scenario("context-menu.states"), wait_until="load")
    _wait_for_all_ready(page)

    basic = page.locator("#quality-context-menu-basic")
    basic_target = page.locator("#quality-context-menu-basic-target")
    basic_surface = page.locator("#quality-context-menu-basic-menu")
    basic_target.click(button="right", position={"x": 24, "y": 24})
    page.wait_for_function("document.querySelector('#quality-context-menu-basic-menu').matches(':popover-open')")
    assert basic.get_attribute("data-invocation") == "pointer"
    assert basic_surface.get_attribute("role") == "menu"
    assert basic_surface.get_attribute("aria-label") == "Quality document actions"
    assert page.get_by_role("menuitem", name="Rename").evaluate("element => element === document.activeElement")

    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#quality-context-menu-basic-menu').matches(':popover-open')")
    page.wait_for_function("document.querySelector('#quality-context-menu-basic-target') === document.activeElement")

    basic_target.press("Shift+F10")
    page.wait_for_function("document.querySelector('#quality-context-menu-basic-menu').matches(':popover-open')")
    assert basic.get_attribute("data-invocation") == "keyboard"
    page.get_by_role("menuitem", name="Rename").press("Enter")
    page.wait_for_function("!document.querySelector('#quality-context-menu-basic-menu').matches(':popover-open')")
    page.wait_for_function("document.querySelector('#quality-context-menu-basic-target') === document.activeElement")
    assert page.locator("[data-quality-action]").text_content() == "root:rename"

    controlled_target = page.locator("#quality-context-menu-controlled-target")
    controlled_surface = page.locator("#quality-context-menu-controlled-menu")
    page.get_by_role("button", name="Toggle claim acceptance").click()
    _record_context_default(page, "#quality-context-menu-controlled-target", "__contextRefused")
    controlled_target.click(button="right")
    page.wait_for_function("window.__contextRefused !== null")
    assert page.evaluate("window.__contextRefused") == {
        "defaultPrevented": False,
        "trusted": True,
    }
    assert controlled_surface.evaluate("element => element.matches(':popover-open')") is False

    page.get_by_role("button", name="Toggle claim acceptance").click()
    _record_context_default(page, "#quality-context-menu-controlled-target", "__contextClaimed")
    controlled_target.click(button="right")
    page.wait_for_function("window.__contextClaimed !== null")
    page.wait_for_function("document.querySelector('#quality-context-menu-controlled-menu').matches(':popover-open')")
    assert page.evaluate("window.__contextClaimed") == {
        "defaultPrevented": True,
        "trusted": True,
    }
    page.keyboard.press("Escape")

    native_input = page.get_by_role("textbox", name="Native title")
    _record_context_default(page, "#quality-context-menu-native-target input", "__contextNative")
    native_input.click(button="right")
    page.wait_for_function("window.__contextNative !== null")
    assert page.evaluate("window.__contextNative") == {
        "defaultPrevented": False,
        "trusted": True,
    }
    assert (
        page.locator("#quality-context-menu-native-menu").evaluate("element => element.matches(':popover-open')")
        is False
    )

    inner_target = page.locator("#quality-context-menu-inner-target")
    inner_target.click(button="right")
    page.wait_for_function("document.querySelector('#quality-context-menu-inner-menu').matches(':popover-open')")
    assert (
        page.locator("#quality-context-menu-outer-menu").evaluate("element => element.matches(':popover-open')")
        is False
    )
    page.keyboard.press("Escape")

    touch_target = page.get_by_role("button", name="Hold submit target")
    assert touch_target.evaluate("element => getComputedStyle(element).touchAction") != "none"
    touch_target.click()
    page.wait_for_function(
        "document.querySelector('[data-quality-target-clicks]').textContent === '1'"
        " && document.querySelector('[data-quality-submits]').textContent === '1'"
    )

    point = page.locator("#quality-context-menu-positioning-point")
    page.emulate_media(media="print")
    assert point.evaluate("element => getComputedStyle(element).display") == "none"
    page.emulate_media(media="screen")

    basic_target.click(button="right", position={"x": 24, "y": 24})
    page.wait_for_function("document.querySelector('#quality-context-menu-basic-menu').matches(':popover-open')")
    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file(), "run `pnpm install` before the ContextMenu quality axe test"
    page.add_script_tag(path=str(axe_path))
    findings = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter((finding) => ['serious','critical'].includes(finding.impact))"""
    )
    assert findings == []
    assert console_errors == []
    assert page_errors == []


def test_context_menu_signed_retained_replacement_removal_and_restore(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page_errors.append(str(error)))

    rendered = build_scenario(
        "context-menu.states",
        configure_app=lambda app: app.set_mounted_prefix("/citry"),
    )
    base_url = serve_citry_ui_live(rendered.app, rendered.html)
    page.goto(base_url + "/", wait_until="load")
    _wait_for_all_ready(page)
    expected_roots = page.locator('[data-citry-ui-part="context-menu"]').count()
    baseline_layers = page.evaluate("globalThis[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length")

    lifecycle_target = page.locator("#quality-context-menu-lifecycle-target")
    lifecycle_target.click(button="right", position={"x": 20, "y": 20})
    page.wait_for_function("document.querySelector('#quality-context-menu-lifecycle-menu').matches(':popover-open')")
    assert (
        page.evaluate("globalThis[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == baseline_layers + 1
    )
    page.evaluate(
        """() => {
          window.__contextLifecycle = {
            root: document.querySelector('#quality-context-menu-lifecycle'),
            target: document.querySelector('#quality-context-menu-lifecycle-target'),
            point: document.querySelector('#quality-context-menu-lifecycle-point'),
            surface: document.querySelector('#quality-context-menu-lifecycle-menu'),
          };
        }"""
    )
    notice_baseline = int(page.locator("[data-quality-lifecycle-notices]").text_content())

    def refresh(step: int, roots: int) -> None:
        page.evaluate(
            """() => void Citry.events.send(
              document.querySelector('.context-menu-quality__lifecycle'),
              'refresh',
              {},
            )"""
        )
        page.wait_for_function(
            "step => Number(document.querySelector('[data-quality-morph-step]')?.textContent) === step",
            arg=step,
            timeout=10_000,
        )
        page.wait_for_function(
            """roots => {
              const all = document.querySelectorAll('[data-citry-ui-part="context-menu"]');
              const ready = document.querySelectorAll(
                '[data-citry-ui-part="context-menu"][data-citry-context-menu-initialized]',
              );
              return all.length === roots && ready.length === roots;
            }""",
            arg=roots,
            timeout=10_000,
        )
        page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
        page.wait_for_timeout(100)

    refresh(1, expected_roots)
    retained = page.evaluate(
        """() => {
          const prior = window.__contextLifecycle;
          const root = document.querySelector('#quality-context-menu-lifecycle');
          const target = document.querySelector('#quality-context-menu-lifecycle-target');
          const point = document.querySelector('#quality-context-menu-lifecycle-point');
          const surface = document.querySelector('#quality-context-menu-lifecycle-menu');
          return {
            root: root === prior.root,
            target: target === prior.target,
            point: point === prior.point,
            surface: surface === prior.surface,
            active: surface.contains(document.activeElement),
            activeText: document.activeElement?.textContent?.trim() ?? '',
            pointOpen: point.matches(':popover-open'),
            surfaceOpen: surface.matches(':popover-open'),
            invocation: root.dataset.invocation,
          };
        }"""
    )
    assert retained == {
        "root": True,
        "target": True,
        "point": True,
        "surface": True,
        "active": True,
        "activeText": "Retained action",
        "pointOpen": True,
        "surfaceOpen": True,
        "invocation": "pointer",
    }
    assert int(page.locator("[data-quality-lifecycle-notices]").text_content()) == notice_baseline

    refresh(2, expected_roots)
    replaced = page.evaluate(
        """() => {
          const prior = window.__contextLifecycle;
          const root = document.querySelector('#quality-context-menu-lifecycle');
          return {
            rootChanged: root !== prior.root,
            oldConnected: prior.root.isConnected,
            oldPointOpen: prior.point.matches(':popover-open'),
            oldSurfaceOpen: prior.surface.matches(':popover-open'),
            open: root.hasAttribute('data-open'),
            invocation: root.hasAttribute('data-invocation'),
          };
        }"""
    )
    assert replaced == {
        "rootChanged": True,
        "oldConnected": False,
        "oldPointOpen": False,
        "oldSurfaceOpen": False,
        "open": False,
        "invocation": False,
    }
    assert int(page.locator("[data-quality-lifecycle-notices]").text_content()) == notice_baseline

    refresh(3, expected_roots - 1)
    assert page.locator("#quality-context-menu-lifecycle").count() == 0
    assert page.evaluate("globalThis[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == baseline_layers

    refresh(4, expected_roots)
    restored = page.locator("#quality-context-menu-lifecycle")
    assert restored.get_attribute("data-open") is None
    assert page.evaluate("globalThis[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == baseline_layers
    restored_target = page.locator("#quality-context-menu-lifecycle-target")
    restored_target.click(button="right", position={"x": 20, "y": 20})
    page.wait_for_function("document.querySelector('#quality-context-menu-lifecycle-menu').matches(':popover-open')")

    refresh(5, expected_roots - 1)
    assert page.locator("#quality-context-menu-lifecycle").count() == 0
    assert page.locator("[data-citry-context-menu-point]:popover-open").count() == 0
    assert page.evaluate("globalThis[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == baseline_layers

    refresh(6, expected_roots)
    final_root = page.locator("#quality-context-menu-lifecycle")
    assert final_root.get_attribute("data-open") is None
    assert final_root.get_attribute("data-invocation") is None
    assert page.evaluate("globalThis[Symbol.for('citry-ui:anchored-layer-runtime')].layers.length") == baseline_layers
    assert int(page.locator("[data-quality-lifecycle-notices]").text_content()) == notice_baseline + 1
    assert console_errors == []
    assert page_errors == []
