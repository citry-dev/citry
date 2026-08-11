"""Browser evidence for HoverCard overlay behavior."""

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
    raise RuntimeError("Could not locate repository root.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          .profile-card { --cui-hover-card-duration: 20ms; }
          .profile-layout { display:grid; gap:.5rem; }
          .profile-layout strong { font-size:1.125rem; }
        """
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8"><title>HoverCard evidence</title><c-css /></head>
          <body x-data>
            <main style="display:flex; align-items:center; gap:8rem; padding:14rem; min-block-size:50rem">
              <c-CHoverCard
                id="ada-card" class_="profile-card" c-delay="60" c-close_delay="120"
                $c-props="{
                  open:$store.hoverCard.controlled ? $store.hoverCard.open : undefined,
                  disabled:$store.hoverCard.disabled,
                  placement:$store.hoverCard.placement,
                  arrow:$store.hoverCard.arrow,
                  size:$store.hoverCard.size,
                  onOpenChange:(next, detail) => {
                    $store.hoverCard.requests.push([next, detail.reason, detail.controlled, detail.forced]);
                    if ($store.hoverCard.accept) $store.hoverCard.open = next;
                  },
                }"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <a href="#ada" c-bind="activator_attrs">Ada Lovelace</a>
                </c-fill>
                <c-fill name="default">
                  <article class="profile-layout">
                    <strong>Ada Lovelace</strong>
                    <span>Mathematician and writer</span>
                    <span>Supplementary profile preview.</span>
                  </article>
                </c-fill>
              </c-CHoverCard>
              <c-CHoverCard id="grace-card" c-delay="600" c-close_delay="0" size="sm">
                <c-fill name="activator" data="{ activator_attrs }">
                  <a href="#grace" c-bind="activator_attrs">Grace Hopper</a>
                </c-fill>
                <c-fill name="default"><strong>Grace Hopper</strong><p>Computer scientist.</p></c-fill>
              </c-CHoverCard>
            </main>
            <button id="outside" type="button">Outside</button>
            <dialog id="modal"><button type="button">Modal focus</button></dialog>
            <c-js />
          </body></html>
        """
        js = """
          Alpine.store('hoverCard', {
            controlled:false, open:false, accept:false, disabled:false,
            placement:'bottom-start', arrow:true, size:'md', requests:[],
          });
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_function(
        "[...document.querySelectorAll('[data-citry-hover-card-host]')]"
        ".every(host => host.hasAttribute('data-citry-hover-card-initialized'))"
    )
    return errors


def test_focus_escape_and_hidden_supplementary_semantics(page: Any) -> None:
    errors = _load(page)
    trigger = page.get_by_role("link", name="Ada Lovelace")
    card = page.locator("#ada-card")
    trigger.focus()
    page.wait_for_function("document.querySelector('#ada-card').matches(':popover-open')")

    assert card.get_attribute("aria-hidden") == "true"
    assert trigger.get_attribute("aria-describedby") is None
    assert card.locator("a,button,input,select,textarea,[tabindex]").count() == 0
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#ada-card').matches(':popover-open')")
    assert trigger.evaluate("element => element === document.activeElement") is True
    assert page.evaluate("Alpine.store('hoverCard').requests.at(-1)[1]") == "escape"
    assert errors == []


def test_hover_delay_surface_bridge_peer_and_touch_suppression(page: Any) -> None:
    errors = _load(page)
    first_trigger = page.get_by_role("link", name="Ada Lovelace")
    first = page.locator("#ada-card")
    first_trigger.hover()
    page.wait_for_timeout(20)
    assert first.evaluate("element => element.matches(':popover-open')") is False
    page.wait_for_function("document.querySelector('#ada-card').matches(':popover-open')")

    first.hover()
    page.wait_for_timeout(150)
    assert first.evaluate("element => element.matches(':popover-open')") is True
    second_trigger = page.get_by_role("link", name="Grace Hopper")
    second_trigger.hover()
    page.wait_for_function("document.querySelector('#grace-card').matches(':popover-open')")
    page.wait_for_function("!document.querySelector('#ada-card').matches(':popover-open')")

    second_trigger.dispatch_event("pointerdown", {"pointerType": "touch"})
    page.wait_for_function("!document.querySelector('#grace-card').matches(':popover-open')")
    assert errors == []


def test_controlled_reject_accept_release_and_modal_force_close(page: Any) -> None:
    errors = _load(page)
    trigger = page.get_by_role("link", name="Ada Lovelace")
    page.evaluate("Alpine.store('hoverCard').controlled = true")
    trigger.focus()
    page.wait_for_function("Alpine.store('hoverCard').requests.length > 0")
    assert page.locator("#ada-card").evaluate("element => element.matches(':popover-open')") is False
    assert page.evaluate("Alpine.store('hoverCard').requests.at(-1)") == [True, "focus", True, False]

    page.evaluate("Object.assign(Alpine.store('hoverCard'), {accept:true, open:true, placement:'top-end', size:'lg'})")
    page.wait_for_function("document.querySelector('#ada-card').matches(':popover-open')")
    assert page.locator("#ada-card").get_attribute("data-size") == "lg"
    page.locator("#modal").evaluate("element => element.showModal()")
    page.wait_for_function("!document.querySelector('#ada-card').matches(':popover-open')")
    assert page.evaluate("Alpine.store('hoverCard').requests.at(-1).slice(0,2)") == [False, "modal"]
    assert page.evaluate("Alpine.store('hoverCard').requests.at(-1)[3]") is True
    assert errors == []


def test_geometry_rtl_forced_colors_print_and_axe(page: Any) -> None:
    errors = _load(page)
    trigger = page.get_by_role("link", name="Ada Lovelace")
    trigger.focus()
    page.wait_for_function("document.querySelector('#ada-card').matches(':popover-open')")
    card = page.locator("#ada-card")
    page.wait_for_function("document.querySelector('#ada-card').dataset.side")
    assert card.get_attribute("data-side") in {"top", "bottom"}
    assert card.bounding_box()["width"] <= page.evaluate("visualViewport.width")

    page.locator("main").evaluate("element => element.dir = 'rtl'")
    page.evaluate("Alpine.store('hoverCard').placement = 'bottom-start'")
    page.wait_for_timeout(50)
    assert card.get_attribute("data-placement") == "bottom-start"

    page.emulate_media(forced_colors="active")
    assert card.evaluate("element => getComputedStyle(element).borderStyle") == "solid"
    page.emulate_media(media="print")
    assert card.evaluate("element => getComputedStyle(element).display") == "none"
    page.emulate_media(media="screen", forced_colors="none")

    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
    assert errors == []
