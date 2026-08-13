"""Public ScrollArea evidence through its reusable quality scenario."""

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
    msg = "Could not find the Citry repository root from the ScrollArea quality test."
    raise RuntimeError(msg)


def _wait_for_all_ready(page: Any) -> None:
    page.wait_for_function(
        """() => {
          const roots = document.querySelectorAll('[data-citry-ui-part="scroll-area"]');
          const ready = document.querySelectorAll(
            '[data-citry-ui-part="scroll-area"][data-citry-scroll-area-initialized]',
          );
          return roots.length > 0 && ready.length === roots.length;
        }"""
    )


def test_scroll_area_quality_native_semantics_callback_style_and_axe(page: Any) -> None:
    page.set_content(render_scenario("scroll-area.states"), wait_until="load")
    _wait_for_all_ready(page)

    generic = page.locator("#quality-scroll-area-generic")
    named = page.locator("#quality-scroll-area-block")
    assert generic.get_attribute("tabindex") == "0"
    assert generic.get_attribute("role") is None
    assert generic.get_attribute("aria-label") is None
    assert named.get_attribute("role") == "region"
    assert named.get_attribute("aria-label") == "Quality activity"
    assert named.locator('[data-citry-ui-part="scroll-area"]').count() == 0

    named.focus()
    assert named.evaluate("element => element === document.activeElement") is True

    subject = page.locator("#quality-scroll-area-configuration")
    subject.evaluate("element => element.scrollTo(160, 120)")
    page.get_by_role("button", name="Block", exact=True).click()
    page.wait_for_function(
        """() => {
          const root = document.querySelector('#quality-scroll-area-configuration');
          return root.dataset.axis === 'block'
            && Math.abs(root.scrollLeft) <= 1
            && getComputedStyle(root).scrollBehavior === 'auto';
        }"""
    )

    callback_root = page.locator("#quality-scroll-area-callback")
    callback_root.evaluate("element => element.scrollTo(120, 90)")
    page.wait_for_function(
        """() => Number(document.querySelector('[data-quality-callbacks]').textContent) >= 1
          && Number(document.querySelector('[data-quality-native-scrolls]').textContent) >= 1
          && Number(document.querySelector('[data-quality-inline-offset]').textContent) > 0
          && Number(document.querySelector('[data-quality-block-offset]').textContent) > 0"""
    )

    # Owned semantics fail closed for the invalid frame, then return exactly.
    named.evaluate(
        """element => {
          element.setAttribute('tabindex', '-1');
          element.setAttribute('role', 'button');
          element.dataset.axis = 'invalid';
          element.style.removeProperty('scroll-behavior');
        }"""
    )
    page.wait_for_function(
        """() => {
          const root = document.querySelector('#quality-scroll-area-block');
          return root.hasAttribute('data-citry-scroll-area-initialized')
            && root.getAttribute('tabindex') === '0'
            && root.getAttribute('role') === 'region'
            && root.dataset.axis === 'block'
            && root.style.getPropertyValue('scroll-behavior').trim() === 'auto'
            && root.style.getPropertyPriority('scroll-behavior') === 'important';
        }"""
    )

    named.evaluate("element => element.style.setProperty('writing-mode', 'vertical-rl')")
    page.wait_for_function(
        "!document.querySelector('#quality-scroll-area-block').hasAttribute('data-citry-scroll-area-initialized')"
    )
    named.evaluate("element => element.style.setProperty('writing-mode', 'horizontal-tb')")
    page.wait_for_selector(
        "#quality-scroll-area-block[data-citry-scroll-area-initialized]",
        state="attached",
    )

    page.evaluate(
        """() => {
          const root = document.querySelector('#quality-scroll-area-generic');
          const host = document.querySelector('#quality-scroll-area-shadow-host');
          host.attachShadow({mode:'open'}).append(root);
        }"""
    )
    page.wait_for_function(
        """() => document.querySelector('#quality-scroll-area-shadow-host')
          .shadowRoot.querySelector('#quality-scroll-area-generic')
          .hasAttribute('data-citry-scroll-area-initialized')"""
    )
    assert (
        page.evaluate(
            """() => {
          const root = document.querySelector('#quality-scroll-area-shadow-host')
            .shadowRoot.querySelector('#quality-scroll-area-generic');
          root.focus();
          return root.tabIndex === 0 && root === root.getRootNode().activeElement;
        }"""
        )
        is True
    )
    page.evaluate(
        """() => {
          const host = document.querySelector('#quality-scroll-area-shadow-host');
          host.before(host.shadowRoot.querySelector('#quality-scroll-area-generic'));
        }"""
    )
    page.wait_for_selector(
        "#quality-scroll-area-generic[data-citry-scroll-area-initialized]",
        state="attached",
    )

    page.emulate_media(media="print")
    assert named.evaluate(
        """element => {
          const style = getComputedStyle(element);
          return style.maxBlockSize === 'none'
            && style.overflowX === 'visible'
            && style.overflowY === 'visible';
        }"""
    )
    page.emulate_media(media="screen")

    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file(), "run `pnpm install` before the ScrollArea quality axe test"
    page.add_script_tag(path=str(axe_path))
    findings = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter((finding) => ['serious','critical'].includes(finding.impact))"""
    )
    assert findings == []


def test_scroll_area_signed_retained_replacement_removal_and_restore(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page_errors.append(str(error)))

    rendered = build_scenario(
        "scroll-area.states",
        configure_app=lambda app: app.set_mounted_prefix("/citry"),
    )
    base_url = serve_citry_ui_live(rendered.app, rendered.html)
    page.goto(base_url + "/", wait_until="load")
    _wait_for_all_ready(page)

    lifecycle = page.locator("#quality-scroll-area-lifecycle")
    lifecycle.evaluate("element => element.scrollTo(180, 140)")
    page.wait_for_function(
        """() => {
          const root = document.querySelector('#quality-scroll-area-lifecycle');
          return root.scrollLeft > 0 && root.scrollTop > 0;
        }"""
    )
    lifecycle.focus()
    page.evaluate(
        """() => {
          window.__scrollAreaRetainedRoot = document.querySelector(
            '#quality-scroll-area-lifecycle',
          );
          window.__scrollAreaRetainedPosition = {
            left: window.__scrollAreaRetainedRoot.scrollLeft,
            top: window.__scrollAreaRetainedRoot.scrollTop,
          };
        }"""
    )
    page.wait_for_timeout(50)
    callback_baseline = int(page.locator("[data-quality-lifecycle-callbacks]").text_content())

    def refresh(step: int) -> None:
        page.evaluate(
            """() => Citry.events.send(
              document.querySelector('.scroll-area-quality'),
              'refresh',
              {},
            )"""
        )
        page.wait_for_function(
            "step => Number(document.querySelector('[data-quality-morph-step]').textContent) === step",
            arg=step,
            timeout=10_000,
        )
        page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")

    refresh(1)
    page.wait_for_selector("#quality-scroll-area-lifecycle[data-citry-scroll-area-initialized]")
    retained = page.evaluate(
        """() => {
          const root = document.querySelector('#quality-scroll-area-lifecycle');
          return {
            same: root === window.__scrollAreaRetainedRoot,
            left: root.scrollLeft,
            top: root.scrollTop,
            focused: root === document.activeElement,
          };
        }"""
    )
    assert retained["same"] is True
    assert retained["focused"] is True
    assert abs(retained["left"] - 180) <= 1
    assert abs(retained["top"] - 140) <= 1
    assert int(page.locator("[data-quality-lifecycle-callbacks]").text_content()) == callback_baseline

    refresh(2)
    page.wait_for_selector("#quality-scroll-area-lifecycle[data-citry-scroll-area-initialized]")
    replaced = page.evaluate(
        """() => {
          const root = document.querySelector('#quality-scroll-area-lifecycle');
          window.__scrollAreaReplacementRoot = root;
          return {
            same: root === window.__scrollAreaRetainedRoot,
            left: root.scrollLeft,
            top: root.scrollTop,
          };
        }"""
    )
    assert replaced == {"same": False, "left": 0, "top": 0}

    refresh(3)
    assert page.locator("#quality-scroll-area-lifecycle").count() == 0

    refresh(4)
    page.wait_for_selector("#quality-scroll-area-lifecycle[data-citry-scroll-area-initialized]")
    restored = page.evaluate(
        """() => {
          const root = document.querySelector('#quality-scroll-area-lifecycle');
          window.__scrollAreaRestoredRoot = root;
          return {
            differsFromReplacement: root !== window.__scrollAreaReplacementRoot,
            left: root.scrollLeft,
            top: root.scrollTop,
          };
        }"""
    )
    assert restored == {"differsFromReplacement": True, "left": 0, "top": 0}

    page.locator("#quality-scroll-area-lifecycle").evaluate("element => element.scrollTo(90, 80)")
    page.wait_for_function(
        """() => {
          const root = document.querySelector('#quality-scroll-area-lifecycle');
          return root.scrollLeft > 0 && root.scrollTop > 0;
        }"""
    )
    page.locator("#quality-scroll-area-lifecycle").focus()
    page.wait_for_timeout(50)
    callback_before_final_retain = int(page.locator("[data-quality-lifecycle-callbacks]").text_content())

    refresh(5)
    page.wait_for_selector("#quality-scroll-area-lifecycle[data-citry-scroll-area-initialized]")
    final_retained = page.evaluate(
        """() => {
          const root = document.querySelector('#quality-scroll-area-lifecycle');
          return {
            same: root === window.__scrollAreaRestoredRoot,
            left: root.scrollLeft,
            top: root.scrollTop,
            focused: root === document.activeElement,
          };
        }"""
    )
    assert final_retained["same"] is True
    assert final_retained["focused"] is True
    assert abs(final_retained["left"] - 90) <= 1
    assert abs(final_retained["top"] - 80) <= 1
    assert int(page.locator("[data-quality-lifecycle-callbacks]").text_content()) == callback_before_final_retain
    assert console_errors == []
    assert page_errors == []
