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
            <body
              x-data
              x-init="Alpine.store('scrollAreaTest', {
                axis: 'both',
                scrollbarWidth: 'auto',
                scrollbarGutter: 'auto',
                overscroll: 'auto',
                callbackMode: 'on',
                events: [],
                nativeEvents: 0,
                detailFrozen: false,
              })"
            >
              <button id="before" type="button">Before</button>
              <h2 id="main-title">Operations</h2>
              <c-CScrollArea
                id="main"
                aria_labelledby="main-title"
                axis="both"
                class_="scroll-evidence consumer-smooth"
                style="scroll-behavior: smooth !important"
                c-attrs="{'@scroll': '$store.scrollAreaTest.nativeEvents += 1'}"
                $c-props="{
                  axis: $store.scrollAreaTest.axis,
                  scrollbarWidth: $store.scrollAreaTest.scrollbarWidth,
                  scrollbarGutter: $store.scrollAreaTest.scrollbarGutter,
                  overscroll: $store.scrollAreaTest.overscroll,
                  onScrollChange: $store.scrollAreaTest.callbackMode === 'off'
                    ? null
                    : ($store.scrollAreaTest.callbackMode === 'invalid'
                      ? 7
                      : (detail) => {
                        $store.scrollAreaTest.detailFrozen = Object.isFrozen(detail);
                        $store.scrollAreaTest.events.push({
                          inline: detail.inlineOffset,
                          block: detail.blockOffset,
                          type: detail.source.type,
                          target: detail.source.target.id,
                        });
                      }),
                }"
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
                x-data="{localNative: 0}"
                @scroll-area-native="localNative += $event.detail.amount"
              >
                <output id="listener-count" x-text="localNative"></output>
                <c-CScrollArea
                  id="listener-area"
                  aria_label="Native listener scope"
                  class_="scroll-evidence"
                  c-attrs="{'@scroll': (
                    'window.__scrollAreaAncestorVisible = typeof localNative !== `undefined`; '
                    + '$store.scrollAreaTest.nativeEvents += 1; '
                    + 'window.__scrollAreaNativeType = $event.type; '
                    + '$dispatch(`scroll-area-native`, {amount: 1})'
                  )}"
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
    page.wait_for_function("Alpine.store('scrollAreaTest').events.length === 1")
    event = page.evaluate("Alpine.store('scrollAreaTest').events[0]")
    assert event == {"inline": 140, "block": 90, "type": "scroll", "target": "main"}
    assert page.evaluate("Alpine.store('scrollAreaTest').detailFrozen") is True

    callback_count = page.evaluate("Alpine.store('scrollAreaTest').events.length")
    page.evaluate("Alpine.store('scrollAreaTest').axis = 'block'")
    page.wait_for_function(
        """() => document.querySelector('#main').dataset.axis === 'block'
          && Math.abs(document.querySelector('#main').scrollLeft) <= 1"""
    )
    page.wait_for_timeout(50)
    assert page.evaluate("Alpine.store('scrollAreaTest').events.length") == callback_count

    page.evaluate("Alpine.store('scrollAreaTest').axis = 'both'")
    page.wait_for_function("document.querySelector('#main').dataset.axis === 'both'")
    main.evaluate("root => { root.scrollLeft=120; }")
    page.wait_for_function("Alpine.store('scrollAreaTest').events.length === 2")
    before_direction = page.evaluate("Alpine.store('scrollAreaTest').events.length")
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
    assert page.evaluate("Alpine.store('scrollAreaTest').events.length") == before_direction

    main.evaluate(
        """root => {
          root.scrollTop=180;
          root.parentElement.classList.toggle('unrelated-ancestor-change');
        }"""
    )
    page.wait_for_function("Alpine.store('scrollAreaTest').events.length === 3")
    assert errors == []


def test_native_attrs_use_isolated_scope_but_forward_event_magics_and_store(page: Any) -> None:
    errors = _load(page)
    page.locator("#listener-area").evaluate("root => { root.scrollTop = 40; }")
    page.wait_for_function(
        """() => Number(document.querySelector('#listener-count').textContent) > 0
          && Alpine.store('scrollAreaTest').nativeEvents > 0"""
    )
    assert page.evaluate("window.__scrollAreaAncestorVisible") is False
    assert page.evaluate("window.__scrollAreaNativeType") == "scroll"
    assert page.locator("#listener-count").inner_text() == str(
        page.evaluate("Alpine.store('scrollAreaTest').nativeEvents")
    )
    assert errors == []


def test_client_precedence_invalid_isolation_release_and_callback_revision(page: Any) -> None:
    errors = _load(page)
    store = "Alpine.store('scrollAreaTest')"
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
          window.__citryRootMarkers=Object.fromEntries([...root.attributes]
            .filter(attribute => attribute.name==='data-citry-root' || attribute.name.startsWith('data-cid'))
            .map(attribute => [attribute.name,attribute.value]));
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
            && root.hasAttribute('@scroll')
            && root.dataset.citryUiPart==='scroll-area'
            && Object.entries(window.__citryRootMarkers)
              .every(([name,value]) => root.getAttribute(name)===value)
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
          && window.__scrollRoot.getAttribute('data-cid')===window.__citryRootMarkers['data-cid']"""
    )
    page.evaluate(
        """() => {
          const marker=Object.keys(window.__citryRootMarkers).find(name => name.startsWith('data-cid-'));
          window.__scrollRoot.setAttribute(marker,'hostile');
        }"""
    )
    page.wait_for_function(
        """() => {
          const marker=Object.keys(window.__citryRootMarkers).find(name => name.startsWith('data-cid-'));
          return window.__scrollRoot.hasAttribute('data-citry-scroll-area-initialized')
            && window.__scrollRoot.getAttribute(marker)===window.__citryRootMarkers[marker];
        }"""
    )
    page.evaluate("window.__scrollRoot.removeAttribute('data-citry-root')")
    page.wait_for_function(
        """() => window.__scrollRoot.hasAttribute('data-citry-scroll-area-initialized')
          && window.__scrollRoot.getAttribute('data-citry-root')
            === window.__citryRootMarkers['data-citry-root']"""
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
    assert sum("received invalid client value" in error for error in errors) == 8


def test_retained_root_handoff_focus_offsets_scope_move_and_fresh_clone(page: Any) -> None:
    errors = _load(page)
    main = page.locator("#main")
    main.evaluate("root => { root.scrollLeft=130; root.scrollTop=95; root.focus(); }")
    page.wait_for_function("Alpine.store('scrollAreaTest').events.length===1")
    page.evaluate(
        """() => {
          const root=document.querySelector('#main');
          window.__retainedScrollRoot=root;
          Alpine.destroyTree(root);
          Alpine.initTree(root);
        }"""
    )
    page.wait_for_function("window.__retainedScrollRoot.hasAttribute('data-citry-scroll-area-initialized')")
    assert page.evaluate("document.querySelector('#main')===window.__retainedScrollRoot") is True
    assert page.evaluate("document.activeElement===window.__retainedScrollRoot") is True
    position = _logical(page, "#main")
    assert position["inline"] == pytest.approx(130, abs=1)
    assert position["block"] == pytest.approx(95, abs=1)
    assert page.evaluate("Alpine.store('scrollAreaTest').events.length") == 1

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

    callback_count = page.evaluate("Alpine.store('scrollAreaTest').events.length")
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
    assert page.evaluate("Alpine.store('scrollAreaTest').events.length") == callback_count
    assert page.evaluate("!window.__retainedScrollRoot[Symbol.for('citry-ui:scroll-area-handoff')].owner")
    assert errors == []


def test_nested_content_changes_forms_and_environment_remain_native(page: Any) -> None:
    errors = _load(page)
    inner = page.locator("#inner")
    inner.evaluate("root => { root.scrollLeft=70; root.scrollTop=60; }")
    page.wait_for_timeout(50)
    assert _logical(page, "#inner") == {"inline": 70, "block": 60}
    assert _logical(page, "#outer") == {"inline": 0, "block": 0}

    before = page.evaluate("Alpine.store('scrollAreaTest').events.length")
    page.locator("#main > .scroll-content").evaluate(
        "content => { content.style.inlineSize='60rem'; content.style.blockSize='40rem'; }"
    )
    page.wait_for_timeout(50)
    assert page.evaluate("Alpine.store('scrollAreaTest').events.length") == before

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
