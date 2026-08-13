"""Focused browser contracts for CContextMenu."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cbutton import CButton
from citry_ui.components.ccontext_menu import CContextMenu
from citry_ui.components.cmenu import CMenuItem, CMenuSeparator, CMenuSubmenu
from citry_ui.components.cmenu.cmenu import (
    CInternalMenuCollection,
    CInternalMenuContent,
    CInternalMenuSurface,
)

pytestmark = pytest.mark.e2e

_COMPONENTS = (
    CContextMenu,
    CButton,
    CMenuItem,
    CMenuSeparator,
    CMenuSubmenu,
    CInternalMenuCollection,
    CInternalMenuContent,
    CInternalMenuSurface,
)


def _python_composition_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-context-menu-python-e2e", _COMPONENTS))

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return {
                "python_menu": CContextMenu(
                    aria_label="Invoice actions",
                    slots={
                        "target": lambda data: CButton(
                            variant="outline",
                            attrs=data.target_attrs,
                            slots={"default": "Invoices"},
                        ),
                        "menu": (
                            CMenuItem(value="rename", slots={"default": "Rename"}),
                            CMenuItem(value="duplicate", slots={"default": "Duplicate"}),
                            CMenuSeparator(),
                            CMenuItem(
                                value="delete",
                                intent="danger",
                                slots={"default": "Delete"},
                            ),
                        ),
                    },
                )
            }

        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <title>ContextMenu Python composition contract</title>
            </head>
            <body>
              {{ python_menu }}
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    msg = "Could not find the Citry repository root from the ContextMenu e2e path."
    raise RuntimeError(msg)


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-context-menu-e2e", _COMPONENTS))

    class Page(Component):
        citry = app
        css = """
          body {
            min-height: 50rem;
            margin: 0;
            padding: 2rem;
          }
          .target {
            display: inline-block;
            inline-size: 12rem;
            block-size: 4rem;
          }
          .transform-shell {
            transform: translateX(70px);
            filter: saturate(1);
            perspective: 600px;
            contain: paint;
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <title>ContextMenu browser contract</title>
            </head>
            <body>
              <section
                id="basic-owner"
                x-data="{ events: [], actions: [] }"
              >
                <c-CContextMenu
                  id="basic"
                  aria_label="Document actions"
                  $c-props="{
                    onOpenChange: (open, detail) => events.push({
                      open,
                      reason: detail.reason,
                      controlled: detail.controlled,
                      forced: detail.forced,
                      x: detail.clientX,
                      y: detail.clientY
                    }),
                    onAction: (value, detail) => actions.push({ value, kind: detail.kind })
                  }"
                >
                  <c-fill name="target" data="{ target_attrs }">
                    <button
                      class="target"
                      c-bind="target_attrs"
                      type="button"
                    >Document</button>
                  </c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="rename">Rename</c-CMenuItem>
                    <c-CMenuItem value="duplicate">Duplicate</c-CMenuItem>
                    <c-CMenuSubmenu value="share">
                      <c-fill name="label">Share</c-fill>
                      <c-fill name="default">
                        <c-CMenuItem value="email">Email</c-CMenuItem>
                      </c-fill>
                    </c-CMenuSubmenu>
                  </c-fill>
                </c-CContextMenu>
                <output id="basic-events" x-text="JSON.stringify(events)"></output>
                <output id="basic-actions" x-text="JSON.stringify(actions)"></output>
              </section>

              <section
                id="controlled-owner"
                x-data="{ open: false, accept: false, moveFocusOnClose: false, requests: [] }"
              >
                <c-CContextMenu
                  id="controlled"
                  aria_label="Controlled actions"
                  $c-props="{
                    open,
                    onOpenChange: (next, detail) => {
                      requests.push({ next, reason: detail.reason });
                      if (next) {
                        if (!accept) return false;
                        open = true;
                        return true;
                      }
                      open = false;
                      if (moveFocusOnClose) {
                        document.querySelector('#controlled-focus-b').focus();
                      }
                    }
                  }"
                >
                  <c-fill name="target" data="{ target_attrs }">
                    <div
                      class="target"
                      c-bind="target_attrs"
                      tabindex="0"
                    >
                      <button id="controlled-focus-a" type="button">Controlled A</button>
                      <button id="controlled-focus-b" type="button">Controlled B</button>
                    </div>
                  </c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="inspect">Inspect</c-CMenuItem>
                  </c-fill>
                </c-CContextMenu>
                <button id="accept-controlled" @click="accept = true" type="button">Accept</button>
                <button id="move-controlled-focus" @click="moveFocusOnClose = true" type="button">Move focus</button>
                <output id="controlled-requests" x-text="JSON.stringify(requests)"></output>
              </section>

              <section id="native-owner" x-data="{ events: [] }">
                <c-CContextMenu
                  id="native"
                  aria_label="Native preservation"
                  $c-props="{
                    onOpenChange: (open, detail) => events.push({
                      open,
                      reason: detail.reason,
                      forced: detail.forced
                    })
                  }"
                >
                  <c-fill name="target" data="{ target_attrs }">
                    <div class="target" c-bind="target_attrs" tabindex="0">
                      <span id="native-text">Selectable text</span>
                      <button id="native-custom" type="button">Custom zone</button>
                      <button id="native-second" type="button">Second custom zone</button>
                      <button id="native-built-in" is="x-context-native" type="button">Built-in zone</button>
                      <a id="native-link" href="#native-link-target">Link</a>
                      <input id="native-input" value="Editable" />
                    </div>
                  </c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="custom">Custom</c-CMenuItem>
                  </c-fill>
                </c-CContextMenu>
                <output id="native-events" x-text="JSON.stringify(events)"></output>
              </section>

              <section id="long-owner" x-data="{ clicks: 0, submits: 0 }">
                <form id="long-form" @submit.prevent="submits += 1">
                  <c-CContextMenu id="long" aria_label="Touch actions">
                    <c-fill name="target" data="{ target_attrs }">
                      <button
                        class="target"
                        c-bind="target_attrs"
                        @click="clicks += 1"
                        type="submit"
                      >Touch target</button>
                    </c-fill>
                    <c-fill name="menu">
                      <c-CMenuItem value="touch">Touch action</c-CMenuItem>
                    </c-fill>
                  </c-CContextMenu>
                </form>
                <output id="long-counts" x-text="JSON.stringify({ clicks, submits })"></output>
              </section>

              <section id="disabled-owner" x-data="{ locked: false, events: [] }">
                <button id="toggle-locked" @click="locked = !locked" type="button">Toggle</button>
                <fieldset id="disabled-fieldset" x-bind:disabled="locked">
                  <legend>Context target</legend>
                  <c-CContextMenu
                    id="disabled-context"
                    aria_label="Disabled actions"
                    $c-props="{
                      onOpenChange: (open, detail) => events.push({
                        open,
                        reason: detail.reason,
                        forced: detail.forced
                      })
                    }"
                  >
                    <c-fill name="target" data="{ target_attrs }">
                      <button
                        class="target"
                        c-bind="target_attrs"
                        type="button"
                      >Disable target</button>
                    </c-fill>
                    <c-fill name="menu">
                      <c-CMenuItem value="disable">Disable action</c-CMenuItem>
                    </c-fill>
                  </c-CContextMenu>
                </fieldset>
                <output id="disabled-events" x-text="JSON.stringify(events)"></output>
              </section>

              <section id="reentrant-owner" x-data="{ mutate: false, requests: 0 }">
                <button id="arm-reentrant" @click="mutate = true" type="button">Arm</button>
                <c-CContextMenu
                  id="reentrant"
                  aria_label="Reentrant actions"
                  $c-props="{
                    open: false,
                    onOpenChange: (next) => {
                      requests += 1;
                      if (next && mutate) {
                        document.querySelector('#reentrant-target').remove();
                        return true;
                      }
                      return false;
                    }
                  }"
                >
                  <c-fill name="target" data="{ target_attrs }">
                    <button
                      class="target"
                      c-bind="target_attrs"
                      type="button"
                    >Reentrant target</button>
                  </c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="mutate">Mutate</c-CMenuItem>
                  </c-fill>
                </c-CContextMenu>
                <output id="reentrant-requests" x-text="requests"></output>
              </section>

              <section
                id="throwing-owner"
                x-data="{ calls: 0 }"
              >
                <c-CContextMenu
                  id="throwing"
                  aria_label="Throwing actions"
                  $c-props="{
                    onOpenChange: () => {
                      calls += 1;
                      throw new Error('context callback boom');
                    }
                  }"
                >
                  <c-fill name="target" data="{ target_attrs }">
                    <button
                      class="target"
                      c-bind="target_attrs"
                      type="button"
                    >Throwing target</button>
                  </c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="throw">Throw</c-CMenuItem>
                  </c-fill>
                </c-CContextMenu>
                <output id="throwing-calls" x-text="calls"></output>
              </section>

              <section id="nested-owner" x-data="{ inner: [], outer: [] }">
                <c-CContextMenu
                  id="outer-context"
                  aria_label="Outer actions"
                  $c-props="{
                    onOpenChange: (open, detail) => outer.push({ open, reason: detail.reason })
                  }"
                >
                  <c-fill name="target" data="{ target_attrs as outer_target_attrs }">
                    <div class="target" c-bind="outer_target_attrs" tabindex="0">
                      <button id="outer-zone" type="button">Outer zone</button>
                      <c-CContextMenu
                        id="inner-context"
                        aria_label="Inner actions"
                        $c-props="{
                          onOpenChange: (open, detail) => inner.push({ open, reason: detail.reason })
                        }"
                      >
                        <c-fill name="target" data="{ target_attrs }">
                          <button c-bind="target_attrs" type="button">Inner zone</button>
                        </c-fill>
                        <c-fill name="menu">
                          <c-CMenuItem value="inner">Inner action</c-CMenuItem>
                        </c-fill>
                      </c-CContextMenu>
                    </div>
                  </c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="outer">Outer action</c-CMenuItem>
                  </c-fill>
                </c-CContextMenu>
                <output id="inner-events" x-text="JSON.stringify(inner)"></output>
                <output id="outer-events" x-text="JSON.stringify(outer)"></output>
              </section>

              <c-CContextMenu id="hostile" aria_label="Hostile repair">
                <c-fill name="target" data="{ target_attrs }">
                  <button class="target" c-bind="target_attrs" type="button">Hostile target</button>
                </c-fill>
                <c-fill name="menu">
                  <c-CMenuItem value="repair">Repair</c-CMenuItem>
                </c-fill>
              </c-CContextMenu>

              <div class="transform-shell">
                <c-CContextMenu id="geometry" aria_label="Geometry actions">
                  <c-fill name="target" data="{ target_attrs }">
                    <button
                      class="target"
                      c-bind="target_attrs"
                      type="button"
                    >Geometry</button>
                  </c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="measure">Measure</c-CMenuItem>
                  </c-fill>
                </c-CContextMenu>
              </div>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _load(page) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_function(
        """
          document.querySelectorAll('[data-citry-context-menu-host]').length === 11
          && document.querySelectorAll('[data-citry-context-menu-initialized]').length === 11
        """
    )
    return errors


def _default_prevented(page, selector: str, action) -> bool:
    page.evaluate(
        """
          (selector) => {
            const target = document.querySelector(selector);
            window.__contextDefaultPrevented = null;
            target.addEventListener('contextmenu', (event) => {
              window.__contextDefaultPrevented = event.defaultPrevented;
            }, { once: true });
          }
        """,
        selector,
    )
    action()
    page.wait_for_function("window.__contextDefaultPrevented !== null")
    return page.evaluate("window.__contextDefaultPrevented")


def test_direct_python_button_and_tuple_declarations_initialize(page) -> None:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_python_composition_page(), wait_until="load")

    root = page.locator("[data-citry-context-menu-host]")
    target = page.get_by_role("button", name="Invoices")
    surface = page.get_by_role("menu", name="Invoice actions")
    page.wait_for_function(
        "document.querySelector('[data-citry-context-menu-host]')?.hasAttribute('data-citry-context-menu-initialized')"
    )
    target.click(button="right")
    page.wait_for_function(
        "document.querySelector('[role=menu][aria-label=\"Invoice actions\"]')?.matches(':popover-open')"
    )

    assert root.get_attribute("data-citry-context-menu-initialized") == ""
    assert surface.get_attribute("data-citry-menu-initialized") == ""
    assert errors == []


def test_direct_python_target_component_runtime_markers_remain_owned(page) -> None:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_python_composition_page(), wait_until="load")
    page.wait_for_function(
        "document.querySelector('[data-citry-context-menu-host]')?.hasAttribute('data-citry-context-menu-initialized')"
    )

    page.get_by_role("button", name="Invoices").evaluate(
        "element => element.removeAttribute('data-citry-button-initialized')"
    )
    page.wait_for_function(
        "!document.querySelector('[data-citry-context-menu-host]')?.hasAttribute('data-citry-context-menu-initialized')"
    )
    page.get_by_role("button", name="Invoices").evaluate(
        "element => element.setAttribute('data-citry-button-initialized', '')"
    )
    page.wait_for_function(
        "document.querySelector('[data-citry-context-menu-host]')?.hasAttribute('data-citry-context-menu-initialized')"
    )

    page.get_by_role("button", name="Invoices").evaluate("element => element.setAttribute('data-citry-hostile', 'x')")
    page.wait_for_function(
        "!document.querySelector('[data-citry-context-menu-host]')?.hasAttribute('data-citry-context-menu-initialized')"
    )
    assert not any(error.startswith("[pageerror]") for error in errors)


def test_pointer_keyboard_action_and_controlled_claim_paths(page) -> None:
    errors = _load(page)

    target = page.locator("#basic-target")
    box = target.bounding_box()
    assert box is not None
    prevented = _default_prevented(
        page,
        "#basic-target",
        lambda: target.click(button="right"),
    )
    assert prevented is True
    page.wait_for_function("document.querySelector('#basic-menu')?.matches(':popover-open')")
    assert page.locator("#basic-menu [role='menuitem']").first.evaluate(
        "element => element === document.activeElement"
    )
    point_box = page.locator("#basic-point").bounding_box()
    assert point_box is not None
    assert abs(point_box["x"] - (box["x"] + box["width"] / 2)) <= 2
    assert abs(point_box["y"] - (box["y"] + box["height"] / 2)) <= 2

    page.keyboard.press("ArrowDown")
    assert "Duplicate" in (page.locator("#basic-menu [role='menuitem']").nth(1).text_content() or "")
    page.evaluate("getSelection().removeAllRanges()")
    target.click(button="right", position={"x": 7, "y": 9})
    assert page.locator("#basic-menu [role='menuitem']").first.evaluate(
        "element => element === document.activeElement"
    )
    moved_point = page.locator("#basic-point").bounding_box()
    assert moved_point is not None
    assert abs(moved_point["x"] - (box["x"] + 7)) <= 2
    assert abs(moved_point["y"] - (box["y"] + 9)) <= 2
    assert (page.locator("#basic-events").text_content() or "").count('"open":true') == 1

    page.keyboard.press("Enter")
    page.wait_for_function("!document.querySelector('#basic-menu')?.matches(':popover-open')")
    assert target.evaluate("element => element === document.activeElement")
    assert page.locator("#basic-actions").text_content() == '[{"value":"rename","kind":"command"}]'

    target.focus()
    page.keyboard.press("Shift+F10")
    page.wait_for_function("document.querySelector('#basic-menu')?.matches(':popover-open')")
    assert '"reason":"keyboard"' in (page.locator("#basic-events").text_content() or "")
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#basic-menu')?.matches(':popover-open')")

    requests_before_modifiers = page.locator("#basic-events").text_content()
    for shortcut in (
        "Shift+ContextMenu",
        "Control+ContextMenu",
        "Alt+ContextMenu",
        "Meta+ContextMenu",
        "Control+Shift+F10",
        "Alt+Shift+F10",
        "Meta+Shift+F10",
    ):
        page.keyboard.press(shortcut)
    page.wait_for_timeout(100)
    assert not page.locator("#basic-menu").evaluate("element => element.matches(':popover-open')")
    assert page.locator("#basic-events").text_content() == requests_before_modifiers

    controlled = page.locator("#controlled-target")
    refused = _default_prevented(
        page,
        "#controlled-target",
        lambda: controlled.click(button="right"),
    )
    assert refused is False
    assert not page.locator("#controlled-point").evaluate("element => element.matches(':popover-open')")
    assert not page.locator("#controlled-menu").evaluate("element => element.matches(':popover-open')")

    page.evaluate("getSelection().removeAllRanges()")
    page.locator("#accept-controlled").click()
    accepted = _default_prevented(
        page,
        "#controlled-target",
        lambda: controlled.click(button="right"),
    )
    assert accepted is True
    page.wait_for_function("document.querySelector('#controlled-menu')?.matches(':popover-open')")
    requests = page.locator("#controlled-requests").text_content() or ""
    assert requests.count('"next":true') == 2
    assert errors == []


def test_controlled_close_callback_focus_move_wins_inside_target(page) -> None:
    errors = _load(page)
    page.locator("#accept-controlled").click()
    page.locator("#move-controlled-focus").click()
    page.locator("#controlled-focus-a").focus()
    page.locator("#controlled-focus-a").click(button="right")
    page.wait_for_function("document.querySelector('#controlled-menu')?.matches(':popover-open')")
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#controlled-menu')?.matches(':popover-open')")
    assert page.locator("#controlled-focus-b").evaluate("element => element === document.activeElement")
    assert page.locator("#controlled-requests").text_content() == (
        '[{"next":true,"reason":"contextmenu"},{"next":false,"reason":"escape"}]'
    )
    assert errors == []


def test_native_preservation_shift_escape_and_transformed_point_geometry(page, browser_name) -> None:
    errors = _load(page)

    link = page.locator("#native-link")
    prevented = _default_prevented(
        page,
        "#native-link",
        lambda: link.click(button="right"),
    )
    assert prevented is False
    assert not page.locator("#native-menu").evaluate("element => element.matches(':popover-open')")

    built_in = page.locator("#native-built-in")
    prevented = _default_prevented(
        page,
        "#native-built-in",
        lambda: built_in.click(button="right"),
    )
    assert prevented is False
    assert not page.locator("#native-menu").evaluate("element => element.matches(':popover-open')")

    page.evaluate("document.querySelector('#native-target').setAttribute('contenteditable', 'plaintext-only')")
    prevented = _default_prevented(
        page,
        "#native-text",
        lambda: page.locator("#native-text").click(button="right"),
    )
    assert prevented is False
    page.evaluate("document.querySelector('#native-target').removeAttribute('contenteditable')")

    page.evaluate("getSelection().removeAllRanges()")
    native_target = page.locator("#native-custom")
    native_target.click(button="right")
    page.wait_for_function("document.querySelector('#native-menu')?.matches(':popover-open')")
    page.evaluate(
        """
          () => {
            window.__contextDefaultPrevented = null;
            document.querySelector('#native-custom').addEventListener(
              'contextmenu',
              event => { window.__contextDefaultPrevented = event.defaultPrevented; },
              { once: true }
            );
          }
        """
    )
    native_target.click(button="right", modifiers=["Shift"])
    page.wait_for_timeout(100)
    shifted = page.evaluate("window.__contextDefaultPrevented")
    if browser_name != "firefox":
        assert shifted is False
    else:
        assert shifted in {None, False}
    page.wait_for_function("!document.querySelector('#native-menu')?.matches(':popover-open')")
    assert '"reason":"native","forced":true' in (page.locator("#native-events").text_content() or "")

    page.evaluate("getSelection().removeAllRanges()")
    native_target.click(button="right")
    page.wait_for_function("document.querySelector('#native-menu')?.matches(':popover-open')")
    page.evaluate("getSelection().removeAllRanges()")
    page.locator("#native-second").click(button="right")
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#native-menu')?.matches(':popover-open')")
    assert page.locator("#native-second").evaluate("element => element === document.activeElement")

    if browser_name == "webkit":
        page.evaluate("getSelection().removeAllRanges()")
        basic = page.locator("#basic-target")
        basic.click(button="right")
        page.wait_for_function("document.querySelector('#basic-menu')?.matches(':popover-open')")
        page.keyboard.press("Escape")
        page.wait_for_function("!document.querySelector('#basic-menu')?.matches(':popover-open')")
        assert page.evaluate("Boolean(getSelection().toString())")
        repeated = _default_prevented(
            page,
            "#basic-target",
            lambda: basic.click(button="right"),
        )
        assert repeated is False
        assert not page.locator("#basic-menu").evaluate("element => element.matches(':popover-open')")

    geometry = page.locator("#geometry-target")
    geometry.scroll_into_view_if_needed()
    box = geometry.bounding_box()
    assert box is not None
    geometry.click(button="right", position={"x": 9, "y": 11})
    page.wait_for_function("document.querySelector('#geometry-menu')?.matches(':popover-open')")
    point_box = page.locator("#geometry-point").bounding_box()
    assert point_box is not None
    assert abs(point_box["x"] - (box["x"] + 9)) <= 2
    assert abs(point_box["y"] - (box["y"] + 11)) <= 2
    assert errors == []


def test_open_shadow_selection_preserves_native_context_menu(page) -> None:
    errors = _load(page)

    page.evaluate(
        """
          () => {
            const host = document.createElement('div');
            host.id = 'native-shadow-host';
            document.body.append(host);
            const shadow = host.attachShadow({ mode: 'open' });
            for (const style of document.querySelectorAll('style')) {
              shadow.append(style.cloneNode(true));
            }
            shadow.append(document.querySelector('#native'));
          }
        """
    )
    native_root = page.locator("#native")
    native_root.wait_for(state="attached")
    page.wait_for_function(
        """
          document.querySelector('#native-shadow-host')?.shadowRoot
            ?.querySelector('#native')
            ?.hasAttribute('data-citry-context-menu-initialized')
        """
    )

    text = page.locator("#native-text")
    text.scroll_into_view_if_needed()
    box = text.bounding_box()
    assert box is not None
    y = box["y"] + box["height"] / 2
    page.evaluate("getSelection().removeAllRanges()")
    page.mouse.move(box["x"] + 2, y)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] - 2, y, steps=8)
    page.mouse.up()
    assert page.evaluate(
        """
          () => {
            const root = document.querySelector('#native-shadow-host').shadowRoot;
            const selection = document.getSelection();
            if (typeof selection.getComposedRanges === 'function') {
              return selection.getComposedRanges({ shadowRoots: [root] }).some(range => {
                const live = document.createRange();
                live.setStart(range.startContainer, range.startOffset);
                live.setEnd(range.endContainer, range.endOffset);
                return !live.collapsed && Boolean(live.toString());
              });
            }
            const rootSelection = root.getSelection?.() ?? selection;
            return !rootSelection.isCollapsed && Boolean(rootSelection.toString());
          }
        """
    )

    native_root.evaluate(
        """
          target => {
            window.__shadowSelectionDefaultPrevented = null;
            target.addEventListener('contextmenu', event => {
              window.__shadowSelectionDefaultPrevented = event.defaultPrevented;
            }, { once: true });
          }
        """
    )
    box = text.bounding_box()
    assert box is not None
    y = box["y"] + box["height"] / 2
    page.mouse.click(box["x"] + box["width"] / 2, y, button="right")
    page.wait_for_function("window.__shadowSelectionDefaultPrevented !== null")
    assert page.evaluate("window.__shadowSelectionDefaultPrevented") is False
    assert not page.locator("#native-menu").evaluate("element => element.matches(':popover-open')")
    assert errors == []


def test_long_press_suppresses_only_derived_click_and_fieldset_disables_live(page, browser_name) -> None:
    if browser_name != "chromium":
        pytest.skip("Trusted held-touch synthesis uses Chromium's CDP input domain.")
    errors = _load(page)

    target = page.locator("#long-target")
    box = target.bounding_box()
    assert box is not None
    x = box["x"] + box["width"] / 2
    y = box["y"] + box["height"] / 2
    session = page.context.new_cdp_session(page)
    session.send(
        "Input.dispatchTouchEvent",
        {
            "type": "touchStart",
            "touchPoints": [{"x": x, "y": y, "radiusX": 1, "radiusY": 1}],
        },
    )
    page.wait_for_function("document.querySelector('#long-menu')?.matches(':popover-open')")
    session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    page.wait_for_timeout(100)
    assert page.locator("#long-counts").text_content() == '{"clicks":0,"submits":0}'

    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#long-menu')?.matches(':popover-open')")
    target.click()
    assert page.locator("#long-counts").text_content() == '{"clicks":1,"submits":1}'

    session.send(
        "Input.dispatchTouchEvent",
        {
            "type": "touchStart",
            "touchPoints": [
                {"id": 1, "x": x - 3, "y": y, "radiusX": 1, "radiusY": 1},
                {"id": 2, "x": x + 3, "y": y, "radiusX": 1, "radiusY": 1},
            ],
        },
    )
    page.wait_for_timeout(850)
    assert not page.locator("#long-menu").evaluate("element => element.matches(':popover-open')")
    session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

    session.send(
        "Input.dispatchTouchEvent",
        {
            "type": "touchStart",
            "touchPoints": [
                {"id": 3, "x": x, "y": y, "radiusX": 1, "radiusY": 1},
            ],
        },
    )
    page.wait_for_timeout(200)
    session.send(
        "Input.dispatchTouchEvent",
        {
            "type": "touchStart",
            "touchPoints": [
                {"id": 3, "x": x, "y": y, "radiusX": 1, "radiusY": 1},
                {"id": 4, "x": 5, "y": 5, "radiusX": 1, "radiusY": 1},
            ],
        },
    )
    page.wait_for_timeout(650)
    assert not page.locator("#long-menu").evaluate("element => element.matches(':popover-open')")
    session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

    session.send(
        "Input.dispatchTouchEvent",
        {
            "type": "touchStart",
            "touchPoints": [
                {"id": 5, "x": 5, "y": 5, "radiusX": 1, "radiusY": 1},
            ],
        },
    )
    session.send(
        "Input.dispatchTouchEvent",
        {
            "type": "touchStart",
            "touchPoints": [
                {"id": 5, "x": 5, "y": 5, "radiusX": 1, "radiusY": 1},
                {"id": 6, "x": x, "y": y, "radiusX": 1, "radiusY": 1},
            ],
        },
    )
    page.wait_for_timeout(750)
    assert not page.locator("#long-menu").evaluate("element => element.matches(':popover-open')")
    session.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

    disabled_target = page.locator("#disabled-context-target")
    disabled_target.click(button="right")
    page.wait_for_function("document.querySelector('#disabled-context-menu')?.matches(':popover-open')")
    page.evaluate("Alpine.$data(document.querySelector('#disabled-owner')).locked = true")
    page.wait_for_function(
        """
          !document.querySelector('#disabled-context-menu')?.matches(':popover-open')
          && document.querySelector('#disabled-context')?.hasAttribute('data-disabled')
        """
    )
    prevented = _default_prevented(
        page,
        "#disabled-context-target",
        lambda: disabled_target.click(button="right", force=True),
    )
    assert prevented is False
    assert '"reason":"disabled","forced":true' in (page.locator("#disabled-events").text_content() or "")
    assert errors == []


def test_anchored_parent_is_recomputed_when_open_layer_moves(page) -> None:
    errors = _load(page)

    result = page.evaluate(
        """
          () => {
            const runtime = globalThis[Symbol.for('citry-ui:anchored-layer-runtime')];
            const parentTrigger = document.createElement('button');
            const parentSurface = document.createElement('div');
            const childTrigger = document.createElement('button');
            const childSurface = document.createElement('div');
            for (const element of [parentTrigger, parentSurface, childTrigger, childSurface]) {
              element.textContent = 'layer';
              element.style.cssText = 'display:block;width:20px;height:20px';
            }
            parentSurface.append(childTrigger, childSurface);
            document.body.append(parentTrigger, parentSurface);
            let parentOpen = true;
            let childOpen = true;
            const childForced = [];
            const parent = {
              trigger: parentTrigger,
              surface: parentSurface,
              isOpen: () => parentOpen,
              forceClose: () => { parentOpen = false; },
            };
            const child = {
              trigger: childTrigger,
              surface: childSurface,
              isOpen: () => childOpen,
              forceClose: reason => {
                childOpen = false;
                childForced.push(reason);
              },
            };
            const coordinator = runtime.coordinatorFor(parentSurface);
            const parentRegistered = coordinator.register(parent);
            const childRegistered = coordinator.register(child);
            const inferredBeforeMove = child.__citryAnchoredParent === parent;
            document.body.append(childTrigger, childSurface);
            const refreshed = coordinator.register(child);
            const parentAfterMove = child.__citryAnchoredParent;
            childSurface.append(parentTrigger, parentSurface);
            const inverted = coordinator.register(parent);
            const inversion = {
              childIsRoot: child.__citryAnchoredParent === null,
              parentUnderChild: parent.__citryAnchoredParent === child,
            };
            document.body.append(parentTrigger, parentSurface);
            coordinator.register(parent);
            coordinator.unregister(parent);
            const snapshot = {
              parentRegistered,
              childRegistered,
              inferredBeforeMove,
              refreshed,
              parentCleared: parentAfterMove === null,
              inverted,
              inversion,
              childOpen,
              childForced,
            };
            coordinator.unregister(child);
            parentTrigger.remove();
            parentSurface.remove();
            childTrigger.remove();
            childSurface.remove();
            return snapshot;
          }
        """
    )
    assert result == {
        "parentRegistered": True,
        "childRegistered": True,
        "inferredBeforeMove": True,
        "refreshed": True,
        "parentCleared": True,
        "inverted": True,
        "inversion": {"childIsRoot": True, "parentUnderChild": True},
        "childOpen": True,
        "childForced": [],
    }
    assert errors == []


def test_keyboard_geometry_repairs_on_window_and_shadow_scroll(page) -> None:
    errors = _load(page)

    target = page.locator("#basic-target")
    assert target.get_attribute("style") is None
    pointer_style = page.add_style_tag(content="#basic-target { pointer-events: none; }")
    target.focus()
    page.keyboard.press("Shift+F10")
    page.wait_for_function("document.querySelector('#basic-menu')?.matches(':popover-open')")
    assert target.get_attribute("style") is None
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#basic-menu')?.matches(':popover-open')")
    pointer_style.evaluate("element => element.remove()")

    page.locator("#accept-controlled").click()
    page.evaluate(
        """
          () => {
            const child = document.querySelector('#controlled-focus-a');
            child.removeAttribute('id');
            child.setAttribute('data-idless-focus', '');
            child.setAttribute('style', 'color: red ; pointer-events: none !important');
            child.focus();
          }
        """
    )
    page.keyboard.press("Shift+F10")
    page.wait_for_function("document.querySelector('#controlled-menu')?.matches(':popover-open')")
    assert page.locator("[data-idless-focus]").get_attribute("style") == (
        "color: red ; pointer-events: none !important"
    )
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#controlled-menu')?.matches(':popover-open')")

    target.focus()
    page.keyboard.press("Shift+F10")
    page.wait_for_function("document.querySelector('#basic-menu')?.matches(':popover-open')")
    page.evaluate("scrollTo(0, 300)")
    page.wait_for_function("!document.querySelector('#basic-menu')?.matches(':popover-open')")

    clipped = page.evaluate(
        """
          () => {
            scrollTo(0, 0);
            const wrapper = document.createElement('div');
            wrapper.id = 'border-clip';
            wrapper.style.cssText = [
              'position:fixed', 'left:100px', 'top:100px', 'width:100px', 'height:100px',
              'border:40px solid black', 'overflow:hidden',
            ].join(';');
            wrapper.append(document.querySelector('#hostile'));
            document.body.append(wrapper);
            const target = document.querySelector('#hostile-target');
            target.style.cssText = 'position:absolute;left:-35px;top:0;width:20px;height:20px';
            target.focus();
            return document.elementFromPoint(115, 110) === target;
          }
        """
    )
    assert clipped is False
    page.keyboard.press("Shift+F10")
    assert not page.locator("#hostile-menu").evaluate("element => element.matches(':popover-open')")
    page.evaluate("document.querySelector('#hostile-target').style.left = '-10px'")
    page.locator("#hostile-target").focus()
    page.keyboard.press("Shift+F10")
    page.wait_for_function("document.querySelector('#hostile-menu')?.matches(':popover-open')")
    point = page.locator("#hostile-point").bounding_box()
    assert point is not None
    assert abs(point["x"] - 140) <= 2
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#hostile-menu')?.matches(':popover-open')")
    page.evaluate(
        """
          () => {
            const wrapper = document.querySelector('#border-clip');
            wrapper.style.transform = 'rotate(35deg)';
            wrapper.style.transformOrigin = '0 0';
            const target = document.querySelector('#hostile-target');
            target.style.left = '-5px';
            target.style.top = '0';
            target.focus();
          }
        """
    )
    page.keyboard.press("Shift+F10")
    page.wait_for_function("document.querySelector('#hostile-menu')?.matches(':popover-open')")
    assert page.evaluate(
        """
          () => {
            const target = document.querySelector('#hostile-target');
            const rect = document.querySelector('#hostile-point').getBoundingClientRect();
            return document.elementsFromPoint(rect.left + .5, rect.top + .5)
              .some(element => element === target || target.contains(element));
          }
        """
    )
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#hostile-menu')?.matches(':popover-open')")
    page.evaluate(
        """
          () => {
            const target = document.querySelector('#hostile-target');
            target.style.left = '-60px';
            target.style.top = '10px';
            target.focus();
          }
        """
    )
    page.keyboard.press("Shift+F10")
    assert not page.locator("#hostile-menu").evaluate("element => element.matches(':popover-open')")
    page.evaluate(
        """
          () => {
            const wrapper = document.querySelector('#border-clip');
            wrapper.style.transform = 'perspective(400px) rotateY(45deg)';
            document.querySelector('#hostile-target').focus();
          }
        """
    )
    page.keyboard.press("Shift+F10")
    assert not page.locator("#hostile-menu").evaluate("element => element.matches(':popover-open')")

    page.evaluate(
        """
          () => {
            scrollTo(0, 0);
            const host = document.createElement('div');
            host.id = 'scroll-shadow-host';
            document.body.append(host);
            const shadow = host.attachShadow({ mode: 'open' });
            for (const style of document.querySelectorAll('style')) {
              shadow.append(style.cloneNode(true));
            }
            const scroller = document.createElement('div');
            scroller.id = 'shadow-scroll-container';
            scroller.style.cssText = 'display:block;height:60px;overflow:auto';
            const spacer = document.createElement('div');
            spacer.style.height = '400px';
            scroller.append(document.querySelector('#geometry'), spacer);
            shadow.append(scroller);
          }
        """
    )
    page.wait_for_function(
        """
          document.querySelector('#scroll-shadow-host').shadowRoot
            .querySelector('#geometry')
            .hasAttribute('data-citry-context-menu-initialized')
        """
    )
    geometry = page.locator("#geometry-target")
    geometry.focus()
    page.keyboard.press("Shift+F10")
    page.wait_for_function(
        """
          document.querySelector('#scroll-shadow-host').shadowRoot
            .querySelector('#geometry-menu').matches(':popover-open')
        """
    )
    page.evaluate(
        """
          document.querySelector('#scroll-shadow-host').shadowRoot
            .querySelector('#shadow-scroll-container').scrollTop = 250
        """
    )
    page.wait_for_function(
        """
          !document.querySelector('#scroll-shadow-host').shadowRoot
            .querySelector('#geometry-menu').matches(':popover-open')
        """
    )

    page.evaluate(
        """
          () => {
            const shadow = document.querySelector('#scroll-shadow-host').shadowRoot;
            shadow.append(document.querySelector('#controlled'));
            const child = shadow.querySelector('[data-idless-focus]');
            child.focus();
          }
        """
    )
    page.wait_for_function(
        """
          document.querySelector('#scroll-shadow-host').shadowRoot
            .querySelector('#controlled')
            .hasAttribute('data-citry-context-menu-initialized')
        """
    )
    page.keyboard.press("Shift+F10")
    page.wait_for_function(
        """
          document.querySelector('#scroll-shadow-host').shadowRoot
            .querySelector('#controlled-menu').matches(':popover-open')
        """
    )
    assert (
        page.evaluate(
            """
          document.querySelector('#scroll-shadow-host').shadowRoot
            .querySelector('[data-idless-focus]').getAttribute('style')
        """
        )
        == "color: red ; pointer-events: none !important"
    )
    page.keyboard.press("Escape")
    page.wait_for_function(
        """
          !document.querySelector('#scroll-shadow-host').shadowRoot
            .querySelector('#controlled-menu').matches(':popover-open')
        """
    )
    assert errors == []


def test_callback_reentrancy_cannot_claim_after_target_removal(page) -> None:
    errors = _load(page)
    page.locator("#arm-reentrant").click()
    prevented = _default_prevented(
        page,
        "#reentrant-target",
        lambda: page.locator("#reentrant-target").click(button="right"),
    )
    assert prevented is False
    page.wait_for_function(
        "!document.querySelector('#reentrant')?.hasAttribute('data-citry-context-menu-initialized')"
    )
    assert page.locator("#reentrant-point").evaluate("element => !element.matches(':popover-open')")
    assert page.locator("#reentrant-menu").evaluate("element => !element.matches(':popover-open')")
    assert page.locator("#reentrant-requests").text_content() == "1"
    assert any("external owner structure is invalid" in error for error in errors)
    assert not any(error.startswith("[pageerror]") for error in errors)


def test_callback_exception_rolls_back_before_native_default_continues(page) -> None:
    errors = _load(page)
    prevented = _default_prevented(
        page,
        "#throwing-target",
        lambda: page.locator("#throwing-target").click(button="right"),
    )
    assert prevented is False
    page.wait_for_function(
        """
          !document.querySelector('#throwing-point')?.matches(':popover-open')
          && !document.querySelector('#throwing-menu')?.matches(':popover-open')
          && !document.querySelector('#throwing')?.hasAttribute('data-open')
          && !document.querySelector('#throwing')?.hasAttribute('data-invocation')
        """
    )
    assert sum("context callback boom" in error for error in errors) == 1


def test_nested_boundary_morph_handoff_shadow_move_and_hostile_repair(page) -> None:
    errors = _load(page)

    page.locator("#inner-context-target").click(button="right")
    page.wait_for_function("document.querySelector('#inner-context-menu')?.matches(':popover-open')")
    assert not page.locator("#outer-context-menu").evaluate("element => element.matches(':popover-open')")
    assert (page.locator("#inner-events").text_content() or "").count('"open":true') == 1
    assert '"open":true' not in (page.locator("#outer-events").text_content() or "")

    page.locator("#basic-target").click(button="right", position={"x": 13, "y": 17})
    page.wait_for_function("document.querySelector('#basic-menu')?.matches(':popover-open')")
    before = page.locator("#basic-point").bounding_box()
    assert before is not None
    assert page.locator("#basic").get_attribute("data-invocation") == "pointer"
    page.evaluate(
        """
          () => {
            const root = document.querySelector('#basic');
            Alpine.destroyTree(root);
            Alpine.initTree(root);
          }
        """
    )
    page.wait_for_function(
        """
          document.querySelector('#basic')?.hasAttribute('data-citry-context-menu-initialized')
          && document.querySelector('#basic-menu')?.matches(':popover-open')
          && document.querySelector('#basic-point')?.matches(':popover-open')
        """
    )
    after = page.locator("#basic-point").bounding_box()
    assert after is not None
    assert abs(after["x"] - before["x"]) <= 1
    assert abs(after["y"] - before["y"]) <= 1
    assert page.locator("#basic").get_attribute("data-invocation") == "pointer"

    page.evaluate(
        """
          () => {
            const host = document.createElement('div');
            host.id = 'context-shadow-host';
            document.body.append(host);
            const shadow = host.attachShadow({ mode: 'open' });
            document.querySelectorAll('style').forEach((style) => shadow.append(style.cloneNode(true)));
            shadow.append(document.querySelector('#geometry'));
          }
        """
    )
    page.wait_for_function(
        "document.querySelector('#context-shadow-host').shadowRoot.querySelector('#geometry')"
        ".hasAttribute('data-citry-context-menu-initialized')"
    )
    page.locator("#geometry-target").click(button="right")
    page.wait_for_function(
        "document.querySelector('#context-shadow-host').shadowRoot.querySelector('#geometry-menu')"
        ".matches(':popover-open')"
    )

    page.evaluate(
        """
          () => {
            document.querySelector('#hostile').id = 'changed-root';
            document.querySelector('#hostile-target').id = 'changed-target';
            document.querySelector('#hostile-point').setAttribute('inert', '');
            document.querySelector('#hostile-menu').setAttribute('aria-label', 'Changed');
          }
        """
    )
    page.wait_for_function(
        """
          document.querySelector('#hostile')?.hasAttribute('data-citry-context-menu-initialized')
          && document.querySelector('#hostile-target')
          && !document.querySelector('#hostile-point').hasAttribute('inert')
          && document.querySelector('#hostile-menu').getAttribute('aria-label') === 'Hostile repair'
        """
    )
    page.evaluate(
        """
          () => {
            const root = document.querySelector('#hostile');
            const point = document.querySelector('#hostile-point');
            root.setAttribute('data-open', '');
            root.setAttribute('data-invocation', 'pointer');
            root.setAttribute('data-size', 'lg');
            root.setAttribute('data-disabled', '');
            point.style.removeProperty('anchor-name');
            point.style.position = 'absolute';
            point.style.inset = '0';
            point.style.width = '40px';
          }
        """
    )
    page.wait_for_function(
        """
          (() => {
            const root = document.querySelector('#hostile');
            const point = document.querySelector('#hostile-point');
            return root?.hasAttribute('data-citry-context-menu-initialized')
              && !root.hasAttribute('data-open')
              && !root.hasAttribute('data-invocation')
              && root.dataset.size === 'md'
              && !root.hasAttribute('data-disabled')
              && point.style.getPropertyValue('anchor-name').startsWith('--_cui-menu-anchor-ref-')
              && !point.style.position
              && !point.style.inset
              && !point.style.width;
          })()
        """
    )
    page.evaluate("document.querySelector('#hostile-target').setAttribute('inert', '')")
    page.wait_for_function("!document.querySelector('#hostile')?.hasAttribute('data-citry-context-menu-initialized')")
    page.evaluate("document.querySelector('#hostile-target').removeAttribute('inert')")
    page.wait_for_function("document.querySelector('#hostile')?.hasAttribute('data-citry-context-menu-initialized')")
    page.evaluate("document.querySelector('#hostile').removeAttribute('data-citry-context-menu-initialized')")
    page.wait_for_function("document.querySelector('#hostile')?.hasAttribute('data-citry-context-menu-initialized')")
    page.evaluate("document.querySelector('#hostile').setAttribute('data-citry-hostile', 'x')")
    page.wait_for_function("!document.querySelector('#hostile')?.hasAttribute('data-citry-context-menu-initialized')")

    page.evaluate(
        """
          () => {
            const root = document.querySelector('#outer-context');
            const clone = root.cloneNode(true);
            clone.id = 'outer-clone';
            root.replaceWith(clone);
          }
        """
    )
    page.wait_for_timeout(50)
    assert not page.locator("#outer-clone").get_attribute("data-citry-context-menu-initialized")
    assert not any(error.startswith("[pageerror]") for error in errors)


def test_point_close_capability_loss_and_invalid_target_fail_closed(page) -> None:
    errors = _load(page)

    page.evaluate("document.querySelector('#basic-point').showPopover()")
    page.wait_for_function("!document.querySelector('#basic-point').matches(':popover-open')")
    assert not page.locator("#basic-menu").evaluate("element => element.matches(':popover-open')")
    page.evaluate("document.querySelector('#basic-menu').showPopover()")
    page.wait_for_function("!document.querySelector('#basic-menu').matches(':popover-open')")
    assert '"open":true' not in (page.locator("#basic-events").text_content() or "")

    page.locator("#basic-target").click(button="right")
    page.wait_for_function("document.querySelector('#basic-menu')?.matches(':popover-open')")
    immediate = page.evaluate(
        """
          () => {
            const point = document.querySelector('#basic-point');
            const menu = document.querySelector('#basic-menu');
            point.hidePopover();
            return {
              pointOpen: point.matches(':popover-open'),
              menuOpen: menu.matches(':popover-open'),
            };
          }
        """
    )
    assert immediate == {"pointOpen": False, "menuOpen": False}

    page.locator("#hostile-target").click(button="right")
    page.wait_for_function("document.querySelector('#hostile-menu')?.matches(':popover-open')")
    page.evaluate(
        """
          () => {
            const root = document.querySelector('#hostile');
            const toggle = root.toggleAttribute;
            root.__capabilityMutations = 0;
            root.toggleAttribute = function (...args) {
              root.__capabilityMutations += 1;
              return toggle.apply(this, args);
            };
            document.querySelector('#hostile-point').hidePopover = undefined;
          }
        """
    )
    page.locator("#hostile-target").click(button="right")
    page.wait_for_function(
        """
          !document.querySelector('#hostile')?.hasAttribute('data-citry-context-menu-initialized')
          && !document.querySelector('#hostile-point')?.matches(':popover-open')
          && !document.querySelector('#hostile-menu')?.matches(':popover-open')
        """
    )
    open_loss_count = page.evaluate("document.querySelector('#hostile').__capabilityMutations")
    page.wait_for_timeout(250)
    assert page.evaluate("document.querySelector('#hostile').__capabilityMutations") == open_loss_count

    page.locator("#basic-target").click(button="right")
    page.wait_for_function("document.querySelector('#basic-menu')?.matches(':popover-open')")
    page.evaluate("document.querySelector('#basic-menu').hidePopover = undefined")
    page.locator("#basic-target").click(button="right")
    page.wait_for_function(
        """
          !document.querySelector('#basic')?.hasAttribute('data-citry-context-menu-initialized')
          && !document.querySelector('#basic-point')?.matches(':popover-open')
          && !document.querySelector('#basic-menu')?.matches(':popover-open')
        """
    )

    page.evaluate(
        """
          () => {
            const root = document.querySelector('#geometry');
            const toggle = root.toggleAttribute;
            root.__capabilityMutations = 0;
            root.toggleAttribute = function (...args) {
              root.__capabilityMutations += 1;
              return toggle.apply(this, args);
            };
            document.querySelector('#geometry-point').showPopover = undefined;
          }
        """
    )
    page.locator("#geometry-target").focus()
    page.keyboard.press("Shift+F10")
    assert not page.locator("#geometry").get_attribute("data-citry-context-menu-initialized")
    assert not page.locator("#geometry-menu").evaluate("element => element.matches(':popover-open')")
    closed_loss_count = page.evaluate("document.querySelector('#geometry').__capabilityMutations")
    page.wait_for_timeout(250)
    assert page.evaluate("document.querySelector('#geometry').__capabilityMutations") == closed_loss_count

    page.evaluate("document.querySelector('#native-target').attachShadow({ mode: 'open' })")
    page.locator("#native-target").focus()
    page.keyboard.press("Shift+F10")
    assert not page.locator("#native").get_attribute("data-citry-context-menu-initialized")

    page.evaluate(
        """
          () => {
            const old = document.querySelector('#hostile-target');
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.id = old.id;
            svg.setAttribute('data-citry-context-menu-target', '');
            old.replaceWith(svg);
          }
        """
    )
    page.wait_for_function("!document.querySelector('#hostile')?.hasAttribute('data-citry-context-menu-initialized')")
    assert not any("is not a function" in error for error in errors)


def test_disabled_focus_fallback_removes_temporary_body_tabindex(page) -> None:
    errors = _load(page)

    page.locator("#basic-target").click(button="right")
    page.wait_for_function("document.querySelector('#basic-menu')?.matches(':popover-open')")
    page.evaluate("document.querySelector('#basic-target').disabled = true")
    page.wait_for_function("!document.querySelector('#basic-menu')?.matches(':popover-open')")
    page.wait_for_timeout(100)
    assert page.evaluate(
        """
          () => ({
            activeIsBody: document.activeElement === document.body,
            bodyTabIndex: document.body.getAttribute('tabindex'),
          })
        """
    ) == {"activeIsBody": True, "bodyTabIndex": None}
    assert errors == []


def test_final_cleanup_disconnects_shared_observers_and_clears_readiness(page) -> None:
    page.evaluate(
        """
          () => {
            const NativeMutationObserver = window.MutationObserver;
            window.__contextObserverDisconnects = 0;
            window.MutationObserver = class extends NativeMutationObserver {
              disconnect() {
                window.__contextObserverDisconnects += 1;
                return super.disconnect();
              }
            };
          }
        """
    )
    errors = _load(page)
    baseline_disconnects = page.evaluate("window.__contextObserverDisconnects")

    page.evaluate(
        """
          () => {
            for (const root of document.querySelectorAll('[data-citry-context-menu-host]')) {
              root.remove();
            }
          }
        """
    )
    page.wait_for_function("document.querySelectorAll('[data-citry-context-menu-initialized]').length === 0")
    page.wait_for_function(
        "baseline => window.__contextObserverDisconnects > baseline",
        arg=baseline_disconnects,
    )
    assert errors == []
