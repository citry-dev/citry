"""Focused browser evidence for CScrollArea."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cscroll_area import CScrollArea

pytestmark = pytest.mark.e2e


def _root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate repository root.")


def _page_html() -> str:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-scroll-area-e2e", (CScrollArea,)))

    class Page(Component):
        citry = app
        js = """
          $component({data(){const scrollAreaTest=Citry.vue.reactive({
            axis:'both',scrollbarWidth:'auto',scrollbarGutter:'auto',overscroll:'auto',
            callbackMode:'on',events:[],nativeEvents:0,detailFrozen:false,localNative:0,
          }); window.__scrollAreaTest=scrollAreaTest; return {state:{scrollAreaTest},localNative:0};}});
        """
        css = """
          .scroll-evidence {
            inline-size: 18rem;
            max-block-size: 9rem;
          }
          .consumer-smooth {
            scroll-behavior: smooth !important;
          }
          .scroll-content {
            inline-size: 52rem;
            block-size: 32rem;
            background: linear-gradient(135deg, #dbeafe, #dcfce7);
          }
          .block-content {
            inline-size: 44rem;
            block-size: 28rem;
          }
          .nested-outer-content {
            inline-size: 34rem;
            block-size: 25rem;
            padding: 1rem;
          }
          .nested-inner-content {
            inline-size: 28rem;
            block-size: 20rem;
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <title>Scroll Area evidence</title>
              <c-css />
            </head>
            <body>
              <button id="before" type="button">Before</button>
              <h2 id="main-title">Operations</h2>
              <c-CScrollArea
                id="main"
                aria_labelledby="main-title"
                axis="both"
                class_="scroll-evidence consumer-smooth"
                style="scroll-behavior: smooth !important"
                @scroll="state.scrollAreaTest.nativeEvents += 1"
                :axis="state.scrollAreaTest.axis"
                :scrollbarWidth="state.scrollAreaTest.scrollbarWidth"
                :scrollbarGutter="state.scrollAreaTest.scrollbarGutter"
                :overscroll="state.scrollAreaTest.overscroll"
                :onScrollChange="state.scrollAreaTest.callbackMode === 'off'
                    ? null
                    : (state.scrollAreaTest.callbackMode === 'invalid'
                      ? 7
                      : (detail) => {
                        state.scrollAreaTest.detailFrozen = Object.isFrozen(detail);
                        state.scrollAreaTest.events.push({
                          inline: detail.inlineOffset,
                          block: detail.blockOffset,
                          type: detail.source.type,
                          target: detail.source.target.id,
                        });
                      })"
              ><div class="scroll-content"><button id="deep" type="button">Deep action</button></div></c-CScrollArea>

              <c-CScrollArea id="block" aria_label="Block feed" class_="scroll-evidence">
                <div class="block-content">Block content</div>
              </c-CScrollArea>

              <c-CScrollArea id="outer" aria_label="Outer area" axis="both" class_="scroll-evidence">
                <div class="nested-outer-content">
                  <c-CScrollArea id="inner" aria_label="Inner area" axis="both" class_="scroll-evidence">
                    <div class="nested-inner-content">Inner content</div>
                  </c-CScrollArea>
                </div>
              </c-CScrollArea>

              <c-CScrollArea id="generic" class_="scroll-evidence"><p>Unnamed region</p></c-CScrollArea>
              <div
                id="listener-owner"
                @scroll-area-native="localNative += $event.detail.amount"
              >
                <output id="listener-count" :textContent="localNative"></output>
                <c-CScrollArea
                  id="listener-area"
                  aria_label="Native listener scope"
                  class_="scroll-evidence"
                  @scroll="
                    window.__scrollAreaAncestorVisible = typeof localNative !== `undefined`;
                    state.scrollAreaTest.nativeEvents += 1;
                    localNative += 1;
                    window.__scrollAreaNativeType = $event.type;
                  "
                ><div class="block-content">Listener content</div></c-CScrollArea>
              </div>
              <form id="native-form">
                <c-CScrollArea id="form-area" aria_label="Form area" class_="scroll-evidence">
                  <label for="note">Note</label><input id="note" name="note" value="original" />
                </c-CScrollArea>
              </form>
              <button id="after" type="button">After</button>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page_html(), wait_until="load")
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-citry-ui-part="scroll-area"]')]
          .every(root => root.hasAttribute('data-citry-scroll-area-initialized'))"""
    )
    return errors


def _logical(page: Any, selector: str) -> dict[str, float]:
    return page.locator(selector).evaluate(
        """root => {
          const geometry=globalThis[Symbol.for('citry-ui:scroll-geometry')];
          const rtl=getComputedStyle(root).direction==='rtl';
          return {
            inline: geometry.horizontalFromRaw(
              root.scrollLeft,
              geometry.maximum(root.scrollWidth,root.clientWidth),
              rtl,
            ),
            block: geometry.clamp(root.scrollTop,geometry.maximum(root.scrollHeight,root.clientHeight)),
          };
        }"""
    )


def test_incompatible_shared_geometry_generation_fails_closed(page: Any) -> None:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    html = _page_html().replace(
        "<head>",
        """<head><script>
          globalThis[Symbol.for('citry-ui:scroll-geometry')]={generation:2};
        </script>""",
        1,
    )
    page.set_content(html, wait_until="load")
    page.wait_for_timeout(100)
    assert page.evaluate("globalThis[Symbol.for('citry-ui:scroll-geometry')].generation") == 2
    assert page.locator("[data-citry-scroll-area-initialized]").count() == 0
    assert any("incompatible scroll geometry runtime" in error for error in errors)


def test_one_native_viewport_focus_semantics_styles_and_axe(page: Any) -> None:
    errors = _load(page)
    main = page.locator("#main")
    assert main.evaluate("root => root.tagName") == "DIV"
    assert main.locator(":scope > *").count() == 1
    assert main.get_attribute("tabindex") == "0"
    assert main.get_attribute("role") == "region"
    assert main.get_attribute("aria-labelledby") == "main-title"
    generic = page.locator("#generic")
    assert generic.get_attribute("role") is None
    assert generic.get_attribute("aria-label") is None
    assert main.evaluate("root => getComputedStyle(root).scrollBehavior") == "auto"
    geometry = main.evaluate(
        """root => ({
          inline:root.scrollWidth>root.clientWidth,
          block:root.scrollHeight>root.clientHeight,
          overflowInline:getComputedStyle(root).overflowInline,
          overflowBlock:getComputedStyle(root).overflowBlock,
        })"""
    )
    assert geometry == {"inline": True, "block": True, "overflowInline": "auto", "overflowBlock": "auto"}
    main.focus()
    assert main.evaluate("root => root === document.activeElement") is True

    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
    assert errors == []


def test_native_callback_coalescing_axis_reset_and_direction_suppression(page: Any) -> None:
    errors = _load(page)
    main = page.locator("#main")
    main.evaluate("root => { root.scrollLeft=80; root.scrollTop=60; root.scrollLeft=140; root.scrollTop=90; }")
    page.wait_for_function("window.__scrollAreaTest.events.length === 1")
    event = page.evaluate("window.__scrollAreaTest.events[0]")
    assert event == {"inline": 140, "block": 90, "type": "scroll", "target": "main"}
    assert page.evaluate("window.__scrollAreaTest.detailFrozen") is True

    callback_count = page.evaluate("window.__scrollAreaTest.events.length")
    page.evaluate("window.__scrollAreaTest.axis = 'block'")
    page.wait_for_function(
        """() => document.querySelector('#main').dataset.axis === 'block'
          && Math.abs(document.querySelector('#main').scrollLeft) <= 1"""
    )
    page.wait_for_timeout(50)
    assert page.evaluate("window.__scrollAreaTest.events.length") == callback_count

    page.evaluate("window.__scrollAreaTest.axis = 'both'")
    page.wait_for_function("document.querySelector('#main').dataset.axis === 'both'")
    main.evaluate("root => { root.scrollLeft=120; }")
    page.wait_for_function("window.__scrollAreaTest.events.length === 2")
    before_direction = page.evaluate("window.__scrollAreaTest.events.length")
    main.evaluate("root => root.dir='rtl'")
    page.wait_for_function(
        """() => {
          const root=document.querySelector('#main');
          const geometry=globalThis[Symbol.for('citry-ui:scroll-geometry')];
          return root.hasAttribute('data-citry-scroll-area-initialized')
            && getComputedStyle(root).direction==='rtl'
            && Math.abs(geometry.horizontalFromRaw(
              root.scrollLeft,
              geometry.maximum(root.scrollWidth,root.clientWidth),
              true,
            )-120)<=1;
        }"""
    )
    page.wait_for_timeout(50)
    assert page.evaluate("window.__scrollAreaTest.events.length") == before_direction

    main.evaluate(
        """root => {
          root.scrollTop=180;
          root.parentElement.classList.toggle('unrelated-ancestor-change');
        }"""
    )
    page.wait_for_function("window.__scrollAreaTest.events.length === 3")
    assert errors == []


def test_on_scroll_change_callback_prop_is_supported(page: Any) -> None:
    errors = _load(page)
    page.locator("#main").evaluate("root => { root.scrollTop=90; }")
    page.wait_for_function("window.__scrollAreaTest.events.length === 1")
    assert page.evaluate("window.__scrollAreaTest.events[0].target") == "main"
    assert errors == []


def test_authored_native_listener_uses_page_scope_and_event(page: Any) -> None:
    errors = _load(page)
    page.locator("#listener-area").evaluate("root => { root.scrollTop = 40; }")
    page.wait_for_function(
        """() => Number(document.querySelector('#listener-count').textContent) > 0
          && window.__scrollAreaTest.nativeEvents > 0"""
    )
    assert page.evaluate("window.__scrollAreaAncestorVisible") is True
    assert page.evaluate("window.__scrollAreaNativeType") == "scroll"
    assert page.locator("#listener-count").inner_text() == str(page.evaluate("window.__scrollAreaTest.nativeEvents"))
    assert errors == []


def test_client_precedence_invalid_isolation_release_and_callback_revision(page: Any) -> None:
    errors = _load(page)
    store = "window.__scrollAreaTest"
    page.evaluate(
        f"Object.assign({store},{{axis:'inline',scrollbarWidth:'thin',scrollbarGutter:'stable',overscroll:'contain'}})"
    )
    page.wait_for_function(
        """() => {
          const root=document.querySelector('#main');
          return root.dataset.axis==='inline'
            && root.dataset.scrollbarWidth==='thin'
            && root.dataset.scrollbarGutter==='stable'
            && root.dataset.overscroll==='contain';
        }"""
    )
    page.evaluate(f"Object.assign({store},{{axis:'sideways',scrollbarWidth:'auto'}})")
    page.wait_for_function(
        """() => document.querySelector('#main').dataset.axis==='inline'
          && document.querySelector('#main').dataset.scrollbarWidth==='auto'"""
    )
    page.evaluate(f"{store}.axis=null")
    page.wait_for_function("document.querySelector('#main').dataset.axis==='both'")

    page.evaluate(f"{store}.callbackMode='invalid'")
    page.locator("#main").evaluate("root => { root.scrollTop=110; }")
    page.wait_for_function(f"{store}.events.length===1")
    page.evaluate(f"{store}.callbackMode='off'")
    page.locator("#main").evaluate("root => { root.scrollTop=160; }")
    page.wait_for_timeout(50)
    assert page.evaluate(f"{store}.events.length") == 1
    assert sum("received invalid client value" in error for error in errors) == 2


def test_hostile_mutation_duplicate_id_writing_mode_and_recovery(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#main")
    page.evaluate(
        """() => {
          const root=document.querySelector('#main');
          window.__scrollRoot=root;
          root.id='hostile';
          root.setAttribute('role','group');
          root.tabIndex=-1;
          root.setAttribute('aria-hidden','true');
          root.setAttribute('aria-checked','true');
          root.dataset.axis='inline';
          root.dataset.citryUiPart='thumb';
          root.setAttribute('x-show','false');
          root.setAttribute('onclick','window.__hostileClick=true');
          root.style.setProperty('scroll-behavior','smooth','important');
        }"""
    )
    page.wait_for_function(
        """() => {
          const root=window.__scrollRoot;
          return root.id==='main'
            && root.hasAttribute('data-citry-scroll-area-initialized')
            && root.getAttribute('role')==='region'
            && root.tabIndex===0
            && !root.hasAttribute('aria-hidden')
            && !root.hasAttribute('aria-checked')
            && !root.hasAttribute('x-show')
            && !root.hasAttribute('onclick')
            && root.dataset.citryUiPart==='scroll-area'
            && getComputedStyle(root).scrollBehavior==='auto';
        }"""
    )
    assert root.count() == 1

    page.evaluate("window.__scrollRoot.setAttribute('data-citry-hostile','x')")
    page.wait_for_function(
        """() => window.__scrollRoot.hasAttribute('data-citry-scroll-area-initialized')
          && !window.__scrollRoot.hasAttribute('data-citry-hostile')"""
    )
    page.evaluate("window.__scrollRoot.setAttribute('data-cid','hostile')")
    page.wait_for_function(
        """() => window.__scrollRoot.hasAttribute('data-citry-scroll-area-initialized')
          && !window.__scrollRoot.hasAttribute('data-cid')"""
    )
    page.evaluate("window.__scrollRoot.setAttribute('data-citry-ui-part','hostile')")
    page.wait_for_function(
        """() => window.__scrollRoot.hasAttribute('data-citry-scroll-area-initialized')
          && window.__scrollRoot.dataset.citryUiPart==='scroll-area'"""
    )

    page.evaluate(
        """() => {
          const duplicate=document.createElement('div');
          duplicate.id='main';duplicate.dataset.duplicate='';document.body.append(duplicate);
        }"""
    )
    page.wait_for_function("!window.__scrollRoot.hasAttribute('data-citry-scroll-area-initialized')")
    page.evaluate("document.querySelector('[data-duplicate]').remove()")
    page.wait_for_function("window.__scrollRoot.hasAttribute('data-citry-scroll-area-initialized')")

    root.evaluate("element => element.style.writingMode='vertical-rl'")
    page.wait_for_function("!window.__scrollRoot.hasAttribute('data-citry-scroll-area-initialized')")
    root.evaluate("element => element.style.writingMode='horizontal-tb'")
    page.wait_for_function("window.__scrollRoot.hasAttribute('data-citry-scroll-area-initialized')")

    page.evaluate(
        """() => {
          const stylesheet=document.createElement('style');
          stylesheet.id='writing-mode-rule';
          stylesheet.textContent='#main{writing-mode:vertical-rl!important}';
          document.head.append(stylesheet);
          window.__scrollRoot.dispatchEvent(new Event('scroll'));
        }"""
    )
    page.wait_for_function("!window.__scrollRoot.hasAttribute('data-citry-scroll-area-initialized')")
    page.evaluate(
        """() => {
          document.querySelector('#writing-mode-rule').remove();
          window.__scrollRoot.dispatchEvent(new Event('scroll'));
        }"""
    )
    page.wait_for_function("window.__scrollRoot.hasAttribute('data-citry-scroll-area-initialized')")
    assert sum("received invalid client value" in error for error in errors) == 7


def test_retained_root_handoff_focus_offsets_scope_move_and_fresh_clone(page: Any) -> None:
    errors = _load(page)
    main = page.locator("#main")
    main.evaluate("root => { root.scrollLeft=130; root.scrollTop=95; root.focus(); }")
    page.wait_for_function("window.__scrollAreaTest.events.length===1")
    page.evaluate(
        """() => {
          const root=document.querySelector('#main');
          window.__retainedScrollRoot=root;
          root.remove();
          document.body.append(root);
        }"""
    )
    page.wait_for_function("window.__retainedScrollRoot.hasAttribute('data-citry-scroll-area-initialized')")
    assert page.evaluate("document.querySelector('#main')===window.__retainedScrollRoot") is True
    page.wait_for_function(
        """() => {
          const root=window.__retainedScrollRoot;
          return Math.abs(root.scrollLeft-130)<=1 && Math.abs(root.scrollTop-95)<=1;
        }"""
    )
    assert (
        page.evaluate("document.activeElement===window.__retainedScrollRoot || document.activeElement===document.body")
        is True
    )
    position = _logical(page, "#main")
    assert position["inline"] == pytest.approx(130, abs=1)
    assert position["block"] == pytest.approx(95, abs=1)
    assert page.evaluate("window.__scrollAreaTest.events.length") == 1

    page.evaluate(
        """() => {
          const host=document.createElement('div');host.id='shadow-host';document.body.append(host);
          const shadow=host.attachShadow({mode:'open'});shadow.append(window.__retainedScrollRoot);
        }"""
    )
    page.wait_for_function(
        """() => window.__retainedScrollRoot.hasAttribute('data-citry-scroll-area-initialized')
          && window.__retainedScrollRoot.getRootNode() instanceof ShadowRoot"""
    )
    page.evaluate("document.body.append(window.__retainedScrollRoot)")
    page.wait_for_function(
        """() => window.__retainedScrollRoot.hasAttribute('data-citry-scroll-area-initialized')
          && window.__retainedScrollRoot.getRootNode()===document"""
    )
    page.wait_for_timeout(50)

    callback_count = page.evaluate("window.__scrollAreaTest.events.length")
    page.evaluate(
        """() => {
          const old=window.__retainedScrollRoot;
          const clone=old.cloneNode(true);
          window.__freshScrollRoot=clone;
          old.replaceWith(clone);
        }"""
    )
    page.wait_for_function(
        """() => document.querySelector('#main')!==window.__retainedScrollRoot
          && !document.querySelector('#main').hasAttribute('data-citry-scroll-area-initialized')"""
    )
    page.evaluate("window.__freshScrollRoot.scrollTop=120")
    page.wait_for_timeout(50)
    assert page.evaluate("window.__scrollAreaTest.events.length") == callback_count
    assert page.evaluate("!window.__retainedScrollRoot[Symbol.for('citry-ui:scroll-area-handoff')].owner")
    assert errors == []


def test_nested_content_changes_forms_and_environment_remain_native(page: Any) -> None:
    errors = _load(page)
    inner = page.locator("#inner")
    inner.evaluate("root => { root.scrollLeft=70; root.scrollTop=60; }")
    page.wait_for_timeout(50)
    assert _logical(page, "#inner") == {"inline": 70, "block": 60}
    assert _logical(page, "#outer") == {"inline": 0, "block": 0}

    before = page.evaluate("window.__scrollAreaTest.events.length")
    page.locator("#main > .scroll-content").evaluate(
        "content => { content.style.inlineSize='60rem'; content.style.blockSize='40rem'; }"
    )
    page.wait_for_timeout(50)
    assert page.evaluate("window.__scrollAreaTest.events.length") == before

    page.locator("#note").fill("changed")
    form_data = page.evaluate("() => Object.fromEntries(new FormData(document.querySelector('#native-form')))")
    assert form_data == {"note": "changed"}
    page.evaluate("document.querySelector('#native-form').reset()")
    assert page.locator("#note").input_value() == "original"

    page.emulate_media(forced_colors="active")
    assert page.locator("#main").evaluate("root => getComputedStyle(root).scrollbarColor") == "auto"
    page.emulate_media(media="print", forced_colors="none")
    printed = page.locator("#main").evaluate(
        """root => ({
          max:getComputedStyle(root).maxBlockSize,
          overflow:getComputedStyle(root).overflow,
          border:getComputedStyle(root).borderStyle,
        })"""
    )
    assert printed == {"max": "none", "overflow": "visible", "border": "none"}
    page.emulate_media(media="screen")
    assert errors == []
