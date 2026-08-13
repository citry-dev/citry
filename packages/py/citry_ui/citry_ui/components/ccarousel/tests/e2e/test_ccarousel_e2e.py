"""Browser evidence for Carousel behavior."""

# ruff: noqa: E501

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
          .evidence-carousel { inline-size:32rem; --cui-carousel-duration:20ms; }
          .evidence-slide { box-sizing:border-box; min-block-size:12rem; padding:2rem; border-radius:.75rem; background:light-dark(#eef2ff,#1e1b4b); }
        """
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8"><title>Carousel evidence</title><c-css /></head>
          <body x-data>
            <c-CCarousel
              id="stories" label="Featured stories" class_="evidence-carousel"
              $c-props="{
                index:$store.carousel.controlled ? $store.carousel.index : undefined,
                disabled:$store.carousel.disabled,
                loop:$store.carousel.loop,
                controls:$store.carousel.controls,
                indicators:$store.carousel.indicators,
                draggable:$store.carousel.draggable,
                orientation:$store.carousel.orientation,
                variant:$store.carousel.variant,
                size:$store.carousel.size,
                onIndexChange:(next, detail) => {
                  $store.carousel.requests.push([next, detail.reason, detail.controlled, detail.forced, detail.value]);
                  if ($store.carousel.accept) $store.carousel.index = next;
                },
              }"
            >
              <c-CCarouselSlide value="aurora" label="Aurora field report"><article class="evidence-slide"><h2>Aurora</h2><a href="#aurora">Read Aurora</a></article></c-CCarouselSlide>
              <c-CCarouselSlide value="tide" label="Tide field report"><article class="evidence-slide"><h2>Tide</h2><button type="button">Open Tide</button></article></c-CCarouselSlide>
              <c-CCarouselSlide value="forest" label="Forest field report"><article class="evidence-slide"><h2>Forest</h2><p>Canopy observations.</p></article></c-CCarouselSlide>
            </c-CCarousel>
            <c-js />
          </body></html>
        """
        js = """
          Alpine.store('carousel', {
            controlled:false, index:0, accept:false, disabled:false, loop:false,
            controls:true, indicators:true, draggable:true, orientation:'horizontal',
            variant:'plain', size:'md', requests:[],
          });
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector("#stories[data-citry-carousel-initialized]")
    return errors


def test_next_previous_picker_and_focus_stability(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#stories")
    next_button = page.get_by_role("button", name="Next slide")
    next_button.focus()
    next_button.press("Enter")
    page.wait_for_function("document.querySelector('#stories').dataset.index === '1'")
    assert next_button.evaluate("element => element === document.activeElement") is True
    assert root.locator('[data-citry-ui-part="slide"][data-active]').get_attribute("data-value") == "tide"
    page.get_by_role("button", name="Aurora field report").click()
    page.wait_for_function("document.querySelector('#stories').dataset.index === '0'")
    assert page.get_by_role("button", name="Previous slide").is_disabled()
    assert errors == []


def test_controlled_reject_accept_release_and_loop(page: Any) -> None:
    errors = _load(page)
    page.evaluate("Alpine.store('carousel').controlled = true")
    page.get_by_role("button", name="Next slide").click()
    assert page.locator("#stories").get_attribute("data-index") == "0"
    assert page.evaluate("Alpine.store('carousel').requests.at(-1)") == [1, "next", True, False, "tide"]
    page.evaluate("Object.assign(Alpine.store('carousel'), {accept:true, index:1})")
    page.wait_for_function("document.querySelector('#stories').dataset.index === '1'")
    page.evaluate("Object.assign(Alpine.store('carousel'), {controlled:false, loop:true})")
    page.get_by_role("button", name="Previous slide").click()
    page.wait_for_function("document.querySelector('#stories').dataset.index === '0'")
    page.get_by_role("button", name="Previous slide").click()
    page.wait_for_function("document.querySelector('#stories').dataset.index === '2'")
    assert errors == []


def test_native_scroll_orientation_and_drag_state(page: Any) -> None:
    errors = _load(page)
    viewport = page.locator('[data-citry-ui-part="viewport"]')
    page.evaluate("Alpine.store('carousel').orientation = 'vertical'")
    page.wait_for_function("document.querySelector('#stories').dataset.orientation === 'vertical'")
    viewport.evaluate(
        "element => { element.scrollTop = element.scrollHeight; element.dispatchEvent(new Event('scroll')); }"
    )
    page.wait_for_function("document.querySelector('#stories').dataset.index === '2'")
    page.evaluate("Alpine.store('carousel').orientation = 'horizontal'")
    page.wait_for_function("document.querySelector('#stories').dataset.orientation === 'horizontal'")
    box = viewport.bounding_box()
    page.mouse.move(box["x"] + 250, box["y"] + 30)
    page.mouse.down()
    assert viewport.get_attribute("data-dragging") == ""
    page.mouse.up()
    assert viewport.get_attribute("data-dragging") is None
    assert errors == []


def test_shared_geometry_keeps_rtl_picker_and_native_position_correlated(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#stories")
    viewport = root.locator('[data-citry-ui-part="viewport"]')
    root.evaluate("element => { element.dir='rtl'; element.querySelector('[data-citry-carousel-next]').click(); }")
    page.wait_for_function(
        """() => {
          const root=document.querySelector('#stories');
          const viewport=root.querySelector('[data-citry-ui-part="viewport"]');
          const track=viewport.firstElementChild;
          const geometry=globalThis[Symbol.for('citry-ui:scroll-geometry')];
          const maximum=geometry.maximum(viewport.scrollWidth,viewport.clientWidth);
          const position=geometry.horizontalFromRaw(viewport.scrollLeft,maximum,true);
          const target=Math.abs(track.children[1].offsetLeft-track.offsetLeft);
          return root.dataset.index==='1' && Math.abs(position-target)<=1;
        }"""
    )
    root.evaluate("element => element.querySelector('[data-citry-carousel-next]').click()")
    page.wait_for_function(
        """() => {
          const root=document.querySelector('#stories');
          const viewport=root.querySelector('[data-citry-ui-part="viewport"]');
          const geometry=globalThis[Symbol.for('citry-ui:scroll-geometry')];
          const maximum=geometry.maximum(viewport.scrollWidth,viewport.clientWidth);
          return root.dataset.index==='2'
            && Math.abs(geometry.horizontalFromRaw(viewport.scrollLeft,maximum,true)-maximum)<=1;
        }"""
    )
    maximum = viewport.evaluate("element => element.scrollWidth - element.clientWidth")
    position = viewport.evaluate(
        """element => globalThis[Symbol.for('citry-ui:scroll-geometry')]
          .horizontalFromRaw(element.scrollLeft,element.scrollWidth-element.clientWidth,true)"""
    )
    assert position == pytest.approx(maximum, abs=1)
    assert errors == []


def test_reactive_presentation_disabled_reduced_forced_print_and_axe(page: Any) -> None:
    errors = _load(page)
    page.evaluate(
        "Object.assign(Alpine.store('carousel'), {variant:'surface', size:'lg', controls:false, indicators:false, disabled:true})"
    )
    root = page.locator("#stories")
    page.wait_for_function("document.querySelector('#stories').dataset.size === 'lg'")
    assert root.get_attribute("data-variant") == "surface"
    assert page.locator('[data-citry-ui-part="controls"]').is_hidden()
    assert page.locator('[data-citry-ui-part="indicators"]').is_hidden()
    page.emulate_media(reduced_motion="reduce")
    assert (
        page.locator('[data-citry-ui-part="viewport"]').evaluate("element => getComputedStyle(element).scrollBehavior")
        == "auto"
    )
    page.emulate_media(forced_colors="active")
    assert root.evaluate("element => getComputedStyle(element).borderStyle") == "solid"
    page.emulate_media(media="print")
    assert (
        page.locator('[data-citry-ui-part="track"]').evaluate("element => getComputedStyle(element).display") == "grid"
    )
    page.emulate_media(media="screen", forced_colors="none", reduced_motion="no-preference")

    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
    assert errors == []
