"""
Run the disposable browser probes for Citry UI overlay foundations.

The probes intentionally use platform HTML/CSS/JavaScript rather than a
candidate public component API.  They answer the decision questions in
``docs/design/ui_overlay_foundations.md`` without turning the spike into a
supported runtime.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING, Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import BrowserType, Page, Playwright


BROWSER_NAMES = ("chromium", "firefox", "webkit")


def _document(*, body: str, css: str = "", script: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>{css}</style>
  </head>
  <body>
    {body}
    <script>{script}</script>
  </body>
</html>"""


def _round_geometry(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _round_geometry(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_round_geometry(item) for item in value]
    if isinstance(value, float):
        return round(value, 2)
    return value


def _platform_and_positioning(page: Page) -> dict[str, Any]:
    page.set_content(
        _document(
            body="""
              <section id="theme" style="--probe-color: rgb(18 92 132)">
                <div id="clip">
                  <button id="anchor" popovertarget="surface">Anchor</button>
                  <div id="surface" popover="auto">Anchored surface</div>
                </div>
              </section>
              <button id="edge-anchor" popovertarget="edge-surface">Edge</button>
              <div id="edge-surface" popover="auto">Fallback surface</div>
            """,
            css="""
              body {
                margin: 0;
                min-block-size: 720px;
              }

              #theme {
                position: absolute;
                inset: 40px auto auto 48px;
              }

              #clip {
                inline-size: 220px;
                block-size: 72px;
                overflow: hidden;
                border: 1px solid;
              }

              #anchor {
                anchor-name: --probe-anchor;
                inline-size: 148px;
                margin: 42px 0 0 20px;
              }

              #surface {
                position-anchor: --probe-anchor;
                position-area: block-end span-inline-end;
                position-try-fallbacks: flip-block;
                inline-size: anchor-size(width);
                box-sizing: border-box;
                margin: 0;
                padding: 8px;
                color: var(--probe-color);
              }

              #edge-anchor {
                position: absolute;
                inset: auto auto 4px 420px;
                anchor-name: --edge-anchor;
              }

              #edge-surface {
                position-anchor: --edge-anchor;
                position-area: block-end span-inline-end;
                position-try-fallbacks: flip-block;
                margin: 0;
                padding: 8px;
              }
            """,
        ),
        wait_until="load",
    )
    page.locator("#anchor").click()
    ordinary = page.evaluate(
        """() => {
          const anchor = document.querySelector('#anchor');
          const surface = document.querySelector('#surface');
          const clip = document.querySelector('#clip');
          const a = anchor.getBoundingClientRect();
          const s = surface.getBoundingClientRect();
          const c = clip.getBoundingClientRect();
          const probeX = Math.min(s.right - 2, innerWidth - 2);
          const probeY = Math.min(s.bottom - 2, innerHeight - 2);
          return {
            anchor: {x: a.x, y: a.y, width: a.width, height: a.height, bottom: a.bottom},
            surface: {x: s.x, y: s.y, width: s.width, height: s.height, bottom: s.bottom},
            clip: {x: c.x, y: c.y, width: c.width, height: c.height, bottom: c.bottom},
            open: surface.matches(':popover-open'),
            escapedClip: s.bottom > c.bottom,
            hitOutsideClip: surface.contains(document.elementFromPoint(probeX, probeY)),
            inheritedColor: getComputedStyle(surface).color,
            parentPreserved: surface.parentElement === clip,
            widthMatches: Math.abs(s.width - a.width) < 1,
            blockEndPlaced: s.top >= a.bottom - 1,
          };
        }"""
    )
    page.keyboard.press("Escape")
    page.locator("#edge-anchor").click()
    edge = page.evaluate(
        """() => {
          const anchor = document.querySelector('#edge-anchor').getBoundingClientRect();
          const surface = document.querySelector('#edge-surface').getBoundingClientRect();
          return {
            anchor: {top: anchor.top, bottom: anchor.bottom},
            surface: {top: surface.top, bottom: surface.bottom},
            flippedAbove: surface.bottom <= anchor.top + 1,
            insideViewport: surface.top >= 0 && surface.bottom <= innerHeight,
          };
        }"""
    )
    support = page.evaluate(
        """() => ({
          popover: typeof HTMLElement.prototype.showPopover === 'function',
          anchorName: CSS.supports('anchor-name: --probe'),
          positionAnchor: CSS.supports('position-anchor: --probe'),
          positionArea: CSS.supports('position-area: block-end span-inline-end'),
          anchorSize: CSS.supports('width: anchor-size(width)'),
          flipBlock: CSS.supports('position-try-fallbacks: flip-block'),
          positionVisibility: CSS.supports('position-visibility: anchors-visible'),
          hintPopover: (() => {
            const node = document.createElement('div');
            node.setAttribute('popover', 'hint');
            return node.popover === 'hint';
          })(),
        })"""
    )
    return _round_geometry({"support": support, "ordinary": ordinary, "edge": edge})


def _layering_and_dismissal(page: Page) -> dict[str, Any]:
    page.set_content(
        _document(
            body="""
              <button id="outer-trigger" popovertarget="outer">Outer</button>
              <div id="outer" popover="auto">
                <button id="inner-trigger" popovertarget="inner">Inner</button>
                <div id="inner" popover="auto">Inner surface</div>
              </div>
              <button id="manual-trigger">Manual</button>
              <div id="manual" popover="manual">Manual surface</div>
              <button id="dialog-trigger">Dialog</button>
              <dialog id="dialog">
                <button id="dialog-popover-trigger" popovertarget="dialog-popover">Details</button>
                <div id="dialog-popover" popover="auto">Dialog popover</div>
                <button id="dialog-close">Close</button>
              </dialog>
              <button id="outside">Outside</button>
            """,
            script="""
              window.__toggles = [];
              for (const node of document.querySelectorAll('[popover]')) {
                node.addEventListener('beforetoggle', (event) => {
                  window.__toggles.push({
                    id: node.id,
                    event: 'beforetoggle',
                    oldState: event.oldState,
                    newState: event.newState,
                    cancelable: event.cancelable,
                  });
                });
                node.addEventListener('toggle', (event) => {
                  window.__toggles.push({
                    id: node.id,
                    event: 'toggle',
                    oldState: event.oldState,
                    newState: event.newState,
                    cancelable: event.cancelable,
                  });
                });
              }
              document.querySelector('#manual-trigger').addEventListener('click', () => {
                document.querySelector('#manual').showPopover();
              });
              document.querySelector('#dialog-trigger').addEventListener('click', () => {
                document.querySelector('#dialog').showModal();
              });
              document.querySelector('#dialog-close').addEventListener('click', () => {
                document.querySelector('#dialog').close();
              });
            """,
        ),
        wait_until="load",
    )
    page.locator("#outer-trigger").click()
    page.locator("#inner-trigger").click()
    nested_open = page.evaluate(
        """() => ({
          outer: document.querySelector('#outer').matches(':popover-open'),
          inner: document.querySelector('#inner').matches(':popover-open'),
        })"""
    )
    page.keyboard.press("Escape")
    first_escape = page.evaluate(
        """() => ({
          outer: document.querySelector('#outer').matches(':popover-open'),
          inner: document.querySelector('#inner').matches(':popover-open'),
        })"""
    )
    page.keyboard.press("Escape")
    second_escape = page.evaluate(
        """() => ({
          outer: document.querySelector('#outer').matches(':popover-open'),
          inner: document.querySelector('#inner').matches(':popover-open'),
        })"""
    )

    page.locator("#manual-trigger").click()
    page.locator("#outside").click()
    manual_after_outside = page.locator("#manual").evaluate("node => node.matches(':popover-open')")
    page.keyboard.press("Escape")
    manual_after_escape = page.locator("#manual").evaluate("node => node.matches(':popover-open')")
    page.locator("#manual").evaluate("node => node.hidePopover()")

    page.locator("#dialog-trigger").click()
    page.locator("#dialog-popover-trigger").click()
    dialog_open = page.evaluate(
        """() => ({
          dialog: document.querySelector('#dialog').open,
          popover: document.querySelector('#dialog-popover').matches(':popover-open'),
        })"""
    )
    page.keyboard.press("Escape")
    dialog_first_escape = page.evaluate(
        """() => ({
          dialog: document.querySelector('#dialog').open,
          popover: document.querySelector('#dialog-popover').matches(':popover-open'),
        })"""
    )
    page.keyboard.press("Escape")
    dialog_second_escape = page.evaluate(
        """() => ({
          dialog: document.querySelector('#dialog').open,
          popover: document.querySelector('#dialog-popover').matches(':popover-open'),
        })"""
    )
    toggle_events = page.evaluate("window.__toggles")
    return {
        "nestedOpen": nested_open,
        "firstEscape": first_escape,
        "secondEscape": second_escape,
        "manualAfterOutside": manual_after_outside,
        "manualAfterEscape": manual_after_escape,
        "dialogOpen": dialog_open,
        "dialogFirstEscape": dialog_first_escape,
        "dialogSecondEscape": dialog_second_escape,
        "toggleEvents": {
            "count": len(toggle_events),
            "openingBeforeToggleCancelable": all(
                event["cancelable"]
                for event in toggle_events
                if event["event"] == "beforetoggle" and event["newState"] == "open"
            ),
            "closingBeforeToggleCancelable": any(
                event["cancelable"]
                for event in toggle_events
                if event["event"] == "beforetoggle" and event["newState"] == "closed"
            ),
        },
    }


def _physical_context(page: Page) -> dict[str, Any]:
    page.set_content(
        _document(
            body="""
              <div id="provider" style="--context-color: rgb(77 42 130)">
                <button id="native-trigger" popovertarget="native">Native</button>
                <div id="native" popover="auto">Native surface</div>
                <button id="moved">Moved surface</button>
              </div>
              <div id="portal"></div>
            """,
            css="""
              #native,
              #moved {
                color: var(--context-color, rgb(1 2 3));
              }
            """,
            script="""
              window.__contextEvents = [];
              document.querySelector('#provider').addEventListener('click', (event) => {
                window.__contextEvents.push(event.target.id);
              });
            """,
        ),
        wait_until="load",
    )
    page.locator("#native-trigger").click()
    native = page.locator("#native").evaluate(
        """node => ({
          parent: node.parentElement.id,
          color: getComputedStyle(node).color,
          closestProvider: node.closest('#provider')?.id ?? null,
        })"""
    )
    page.locator("#native").click()
    native_events = page.evaluate("window.__contextEvents.slice()")
    page.locator("#moved").evaluate("node => document.querySelector('#portal').append(node)")
    moved = page.locator("#moved").evaluate(
        """node => ({
          parent: node.parentElement.id,
          color: getComputedStyle(node).color,
          closestProvider: node.closest('#provider')?.id ?? null,
        })"""
    )
    page.locator("#moved").click()
    moved_events = page.evaluate("window.__contextEvents.slice()")
    return {
        "nativeTopLayer": native,
        "nativeEvents": native_events,
        "physicallyMoved": moved,
        "eventsAfterMove": moved_events,
        "citryTeleportContract": (
            "Lexical Citry/Alpine context follows the authored x-teleport origin; "
            "CSS inheritance, native containment, currentTarget, and bubbling follow the physical placement."
        ),
    }


def _controlled_layer_and_presence(page: Page) -> dict[str, Any]:
    page.set_content(
        _document(
            body="""
              <button id="outer-trigger">Outer</button>
              <div id="outer" popover="manual">
                <button id="inner-trigger">Inner</button>
                <div id="inner" popover="manual">Inner surface</div>
              </div>
            """,
            css="""
              [popover] {
                margin: 0;
                opacity: 1;
              }
            """,
            script="""
              window.__layerLog = [];
              window.__declineInner = true;
              window.__layerStack = [];
              window.__layerStates = new Map();

              const stateFor = (id) => {
                let state = window.__layerStates.get(id);
                if (state) return state;
                state = {
                  id,
                  surface: document.querySelector(`#${id}`),
                  trigger: document.querySelector(`#${id}-trigger`),
                  animation: null,
                  generation: 0,
                  registered: false,
                };
                window.__layerStates.set(id, state);
                return state;
              };

              window.openLayer = (id) => {
                const state = stateFor(id);
                state.generation += 1;
                state.animation?.cancel();
                state.animation = null;
                state.surface.inert = false;
                state.surface.style.opacity = '';
                if (!state.surface.matches(':popover-open')) state.surface.showPopover();
                window.__layerStack = window.__layerStack.filter((item) => item !== state);
                window.__layerStack.push(state);
                state.registered = true;
                window.__layerLog.push(`open:${id}`);
              };

              window.requestLayerClose = (state, reason) => {
                window.__layerLog.push(`request:${state.id}:${reason}`);
                if (state.id === 'inner' && window.__declineInner) {
                  window.__layerLog.push('decline:inner');
                  return false;
                }
                state.generation += 1;
                const generation = state.generation;
                window.__layerStack = window.__layerStack.filter((item) => item !== state);
                state.registered = false;
                state.surface.inert = true;
                state.animation?.cancel();
                state.animation = state.surface.animate(
                  [{opacity: 1}, {opacity: 0}],
                  {duration: 160, easing: 'linear', fill: 'forwards'},
                );
                state.animation.finished.then(() => {
                  if (state.generation !== generation || state.registered) return;
                  if (state.surface.matches(':popover-open')) state.surface.hidePopover();
                  state.surface.inert = false;
                  state.animation = null;
                  window.__layerLog.push(`settled:${state.id}`);
                }).catch(() => {});
                return true;
              };

              window.disposeLayers = () => {
                for (const state of window.__layerStates.values()) {
                  state.generation += 1;
                  state.animation?.cancel();
                  state.animation = null;
                  state.registered = false;
                  state.surface.inert = false;
                  if (state.surface.matches(':popover-open')) state.surface.hidePopover();
                }
                window.__layerStack = [];
                window.__layerLog.push('dispose');
              };

              document.querySelector('#outer-trigger').addEventListener('click', () => openLayer('outer'));
              document.querySelector('#inner-trigger').addEventListener('click', () => openLayer('inner'));
              document.addEventListener('keydown', (event) => {
                if (event.key !== 'Escape') return;
                const top = window.__layerStack.at(-1);
                if (!top) return;
                event.preventDefault();
                event.stopImmediatePropagation();
                requestLayerClose(top, 'escape');
              }, true);
              document.addEventListener('pointerdown', (event) => {
                const top = window.__layerStack.at(-1);
                if (!top || top.surface.contains(event.target) || top.trigger.contains(event.target)) return;
                requestLayerClose(top, 'outside');
              }, true);
            """,
        ),
        wait_until="load",
    )
    page.locator("#outer-trigger").click()
    page.locator("#inner-trigger").click()
    page.keyboard.press("Escape")
    declined = page.evaluate(
        """() => ({
          stack: window.__layerStack.map((state) => state.id),
          outerOpen: document.querySelector('#outer').matches(':popover-open'),
          innerOpen: document.querySelector('#inner').matches(':popover-open'),
          innerInert: document.querySelector('#inner').inert,
        })"""
    )
    page.evaluate("window.__declineInner = false")
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
    during_exit = page.evaluate(
        """() => ({
          stack: window.__layerStack.map((state) => state.id),
          outerOpen: document.querySelector('#outer').matches(':popover-open'),
          innerOpen: document.querySelector('#inner').matches(':popover-open'),
          outerInert: document.querySelector('#outer').inert,
          innerInert: document.querySelector('#inner').inert,
          activeAnimations: [...window.__layerStates.values()].filter((state) => state.animation).length,
        })"""
    )
    page.wait_for_timeout(190)
    settled = page.evaluate(
        """() => ({
          stack: window.__layerStack.map((state) => state.id),
          outerOpen: document.querySelector('#outer').matches(':popover-open'),
          innerOpen: document.querySelector('#inner').matches(':popover-open'),
          activeAnimations: [...window.__layerStates.values()].filter((state) => state.animation).length,
        })"""
    )

    page.locator("#outer-trigger").click()
    page.keyboard.press("Escape")
    page.wait_for_timeout(40)
    page.locator("#outer-trigger").click()
    page.wait_for_timeout(170)
    rapid_reopen = page.evaluate(
        """() => ({
          stack: window.__layerStack.map((state) => state.id),
          open: document.querySelector('#outer').matches(':popover-open'),
          inert: document.querySelector('#outer').inert,
          activeAnimations: [...window.__layerStates.values()].filter((state) => state.animation).length,
        })"""
    )
    page.evaluate("window.disposeLayers()")
    cleanup = page.evaluate(
        """() => ({
          stack: window.__layerStack.length,
          open: document.querySelectorAll(':popover-open').length,
          activeAnimations: [...window.__layerStates.values()].filter((state) => state.animation).length,
        })"""
    )
    return {
        "declinedControlledClose": declined,
        "ownershipReleasedDuringExit": during_exit,
        "settled": settled,
        "rapidReopen": rapid_reopen,
        "cleanup": cleanup,
        "log": page.evaluate("window.__layerLog"),
    }


def _presence(page: Page) -> dict[str, Any]:
    page.set_content(
        _document(
            body="""
              <button id="parent-trigger" popovertarget="parent">Parent</button>
              <div id="parent" popover="auto">
                <button id="child-trigger" popovertarget="child">Child</button>
                <div id="child" popover="auto">Animated child</div>
              </div>
            """,
            css="""
              [popover] {
                opacity: 0;
                transform: translateY(-8px);
                transition:
                  opacity 160ms linear,
                  transform 160ms linear,
                  display 160ms allow-discrete,
                  overlay 160ms allow-discrete;
              }

              [popover]:popover-open {
                opacity: 1;
                transform: translateY(0);
              }

              @starting-style {
                [popover]:popover-open {
                  opacity: 0;
                  transform: translateY(-8px);
                }
              }
            """,
        ),
        wait_until="load",
    )
    page.locator("#parent-trigger").click()
    page.wait_for_timeout(200)
    page.locator("#child-trigger").click()
    page.wait_for_timeout(200)
    page.locator("#child").evaluate("node => node.hidePopover()")
    immediate = page.locator("#child").evaluate(
        """node => ({
          open: node.matches(':popover-open'),
          display: getComputedStyle(node).display,
          opacity: getComputedStyle(node).opacity,
          height: node.getBoundingClientRect().height,
        })"""
    )
    page.keyboard.press("Escape")
    ownership_after_escape = page.evaluate(
        """() => ({
          parent: document.querySelector('#parent').matches(':popover-open'),
          child: document.querySelector('#child').matches(':popover-open'),
        })"""
    )
    page.wait_for_timeout(80)
    middle = page.locator("#child").evaluate(
        """node => ({
          open: node.matches(':popover-open'),
          display: getComputedStyle(node).display,
          opacity: getComputedStyle(node).opacity,
          height: node.getBoundingClientRect().height,
        })"""
    )
    page.wait_for_timeout(140)
    settled = page.locator("#child").evaluate(
        """node => ({
          open: node.matches(':popover-open'),
          display: getComputedStyle(node).display,
          opacity: getComputedStyle(node).opacity,
          height: node.getBoundingClientRect().height,
        })"""
    )
    support = page.evaluate(
        """() => ({
          allowDiscrete: CSS.supports('transition-behavior: allow-discrete'),
          overlay: CSS.supports('overlay: auto'),
          startingStyle: CSS.supports('selector(:popover-open)'),
        })"""
    )
    return _round_geometry(
        {
            "support": support,
            "immediateAfterHide": immediate,
            "middleOfExit": middle,
            "settled": settled,
            "ownershipAfterImmediateEscape": ownership_after_escape,
        }
    )


def _drawer_boundary(page: Page) -> dict[str, Any]:
    page.set_content(
        _document(
            body="""
              <button id="before">Before</button>
              <aside id="persistent">
                <button id="persistent-action">Persistent action</button>
              </aside>
              <main id="main"><button id="main-action">Main action</button></main>
              <button id="open-task">Open task drawer</button>
              <dialog id="task">
                <button id="task-anchor" popovertarget="task-popover">More</button>
                <div id="task-popover" popover="auto">Nested overlay</div>
                <button id="task-close">Close</button>
              </dialog>
            """,
            css="""
              #persistent {
                inline-size: 14rem;
                float: inline-start;
              }

              #task {
                inset: 0 0 0 auto;
                block-size: 100dvb;
                inline-size: min(24rem, 90dvi);
                max-block-size: none;
                max-inline-size: none;
                margin: 0;
                padding: 1rem;
                box-sizing: border-box;
              }

              #task-anchor {
                anchor-name: --task-anchor;
              }

              #task-popover {
                position-anchor: --task-anchor;
                position-area: block-end span-inline-end;
                margin: 0;
              }
            """,
            script="""
              document.querySelector('#open-task').addEventListener('click', () => {
                document.querySelector('#task').showModal();
              });
              document.querySelector('#task-close').addEventListener('click', () => {
                document.querySelector('#task').close();
              });
            """,
        ),
        wait_until="load",
    )
    page.locator("#main-action").focus()
    persistent = page.evaluate(
        """() => ({
          mainInert: document.querySelector('#main').matches(':modal') || document.querySelector('#main').inert,
          mainFocusable: document.activeElement === document.querySelector('#main-action'),
          persistentInTopLayer: document.querySelector('#persistent').matches(':modal'),
        })"""
    )
    page.locator("#open-task").click()
    page.locator("#task-anchor").click()
    modal = page.evaluate(
        """() => {
          const dialog = document.querySelector('#task');
          const popover = document.querySelector('#task-popover');
          const d = dialog.getBoundingClientRect();
          const p = popover.getBoundingClientRect();
          document.querySelector('#main-action').focus();
          return {
            dialogOpen: dialog.open,
            dialogModal: dialog.matches(':modal'),
            nestedPopoverOpen: popover.matches(':popover-open'),
            nestedPopoverInsideViewport: p.top >= 0 && p.right <= innerWidth && p.bottom <= innerHeight,
            focusContained: dialog.contains(document.activeElement),
            sideGeometry: {
              right: innerWidth - d.right,
              top: d.top,
              heightDelta: innerHeight - d.height,
            },
          };
        }"""
    )
    page.keyboard.press("Escape")
    first_escape = page.evaluate(
        """() => ({
          dialog: document.querySelector('#task').open,
          popover: document.querySelector('#task-popover').matches(':popover-open'),
        })"""
    )
    page.keyboard.press("Escape")
    second_escape = page.evaluate(
        """() => ({
          dialog: document.querySelector('#task').open,
          popover: document.querySelector('#task-popover').matches(':popover-open'),
        })"""
    )
    return _round_geometry(
        {
            "persistentLayout": persistent,
            "modalTaskDrawer": modal,
            "firstEscape": first_escape,
            "secondEscape": second_escape,
        }
    )


def _toast_host(page: Page) -> dict[str, Any]:
    page.set_content(
        _document(
            body="""
              <button id="before">Before</button>
              <div id="producer"></div>
              <div id="toast-host" aria-live="polite" aria-atomic="false"></div>
              <div id="manual-host" popover="manual"></div>
              <dialog id="modal"><button id="modal-action">Modal action</button></dialog>
            """,
            css="""
              #toast-host,
              #manual-host {
                position: fixed;
                inset: 1rem 1rem auto auto;
                display: grid;
                gap: 0.5rem;
                max-inline-size: 20rem;
              }

              .toast {
                padding: 0.5rem;
                border: 1px solid;
                background: Canvas;
                color: CanvasText;
              }
            """,
            script="""
              window.__toastLog = [];
              window.__toastStates = new Map();
              window.addToast = ({id, text, timeout = 120}) => {
                const host = document.querySelector('#toast-host');
                let state = window.__toastStates.get(id);
                if (!state) {
                  const toast = document.createElement('div');
                  toast.className = 'toast';
                  toast.dataset.toastId = id;
                  toast.tabIndex = -1;
                  host.append(toast);
                  state = {toast, remaining: timeout, started: 0, timer: null, paused: false};
                  const pause = () => {
                    if (state.paused) return;
                    state.paused = true;
                    clearTimeout(state.timer);
                    state.remaining -= performance.now() - state.started;
                    window.__toastLog.push(`pause:${id}`);
                  };
                  const resume = () => {
                    if (!state.paused) return;
                    state.paused = false;
                    state.started = performance.now();
                    state.timer = setTimeout(state.remove, Math.max(state.remaining, 0));
                    window.__toastLog.push(`resume:${id}`);
                  };
                  state.remove = () => {
                    toast.remove();
                    window.__toastStates.delete(id);
                    window.__toastLog.push(`remove:${id}`);
                  };
                  toast.addEventListener('pointerenter', pause);
                  toast.addEventListener('pointerleave', resume);
                  toast.addEventListener('focusin', pause);
                  toast.addEventListener('focusout', resume);
                  window.__toastStates.set(id, state);
                }
                state.toast.textContent = text;
                window.__toastLog.push(`show:${id}`);
                clearTimeout(state.timer);
                state.remaining = timeout;
                state.started = performance.now();
                state.paused = state.toast.matches(':hover') || state.toast.contains(document.activeElement);
                if (!state.paused) state.timer = setTimeout(state.remove, timeout);
                return state.toast;
              };
              window.addEventListener('keydown', (event) => {
                if (event.key !== 'F6') return;
                document.querySelector('#toast-host .toast')?.focus();
              });
            """,
        ),
        wait_until="load",
    )
    page.evaluate(
        """() => {
          window.addToast({id: 'one', text: 'First'});
          window.addToast({id: 'one', text: 'Updated'});
          window.addToast({id: 'two', text: 'Second'});
        }"""
    )
    dedupe = page.evaluate(
        """() => ({
          count: document.querySelectorAll('#toast-host .toast').length,
          firstText: document.querySelector('[data-toast-id="one"]').textContent,
          liveHostIdentity: document.querySelector('#toast-host') === document.querySelector('[aria-live]'),
          producerIndependent: !document.querySelector('#producer').contains(document.querySelector('#toast-host')),
        })"""
    )
    page.locator('[data-toast-id="one"]').hover()
    page.wait_for_timeout(160)
    paused = page.evaluate(
        """() => ({
          onePresent: Boolean(document.querySelector('[data-toast-id="one"]')),
          twoPresent: Boolean(document.querySelector('[data-toast-id="two"]')),
        })"""
    )
    page.locator("#before").focus()
    page.keyboard.press("F6")
    f6 = page.evaluate(
        """() => ({
          focusedToast: document.activeElement?.dataset.toastId ?? null,
          hostStillConnected: document.querySelector('#toast-host').isConnected,
        })"""
    )
    before_modal = page.evaluate(
        """() => {
          const manual = document.querySelector('#manual-host');
          manual.replaceChildren(Object.assign(document.createElement('div'), {textContent: 'Manual toast'}));
          manual.showPopover();
          document.querySelector('#modal').showModal();
          const point = manual.getBoundingClientRect();
          const hit = document.elementFromPoint(point.left + 2, point.top + 2);
          return {
            manualOpen: manual.matches(':popover-open'),
            modalOpen: document.querySelector('#modal').open,
            manualPaintedAboveModal: manual.contains(hit),
          };
        }"""
    )
    page.evaluate(
        """() => {
          document.querySelector('#modal').close();
          document.querySelector('#manual-host').hidePopover();
          document.querySelector('#modal').showModal();
          document.querySelector('#manual-host').showPopover();
        }"""
    )
    after_modal = page.evaluate(
        """() => {
          const manual = document.querySelector('#manual-host');
          const modal = document.querySelector('#modal');
          const point = manual.getBoundingClientRect();
          const hit = document.elementFromPoint(point.left + 2, point.top + 2);
          return {
            manualOpen: manual.matches(':popover-open'),
            modalOpen: modal.open,
            manualPaintedAboveModal: manual.contains(hit),
          };
        }"""
    )
    page.keyboard.press("Escape")
    after_escape = page.evaluate(
        """() => ({
          manualOpen: document.querySelector('#manual-host').matches(':popover-open'),
          modalOpen: document.querySelector('#modal').open,
        })"""
    )
    return {
        "persistentHost": dedupe,
        "pause": paused,
        "focusHandoff": f6,
        "manualPopoverShownBeforeModal": before_modal,
        "manualPopoverShownAfterModal": after_modal,
        "afterEscape": after_escape,
        "log": page.evaluate("window.__toastLog"),
    }


PROBES: tuple[tuple[str, Callable[[Page], dict[str, Any]]], ...] = (
    ("platformAndPositioning", _platform_and_positioning),
    ("layeringAndDismissal", _layering_and_dismissal),
    ("controlledLayerAndPresence", _controlled_layer_and_presence),
    ("physicalContext", _physical_context),
    ("presence", _presence),
    ("drawerBoundary", _drawer_boundary),
    ("toastHost", _toast_host),
)


def _run_browser(browser_type: BrowserType) -> dict[str, Any]:
    browser = browser_type.launch(headless=True)
    try:
        context = browser.new_context(viewport={"width": 960, "height": 720})
        page = context.new_page()
        console_errors: list[str] = []
        page_errors: list[str] = []
        page.on(
            "console",
            lambda message: console_errors.append(message.text) if message.type == "error" else None,
        )
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        results: dict[str, Any] = {}
        for name, probe in PROBES:
            results[name] = probe(page)
        results["runtimeHealth"] = {
            "consoleErrors": console_errors,
            "pageErrors": page_errors,
        }
        return {
            "version": browser.version,
            "probes": results,
        }
    finally:
        browser.close()


def run(playwright: Playwright) -> dict[str, Any]:
    results: dict[str, Any] = {
        "recordedAt": datetime.now(UTC).isoformat(),
        "playwright": version("playwright"),
        "viewport": {"width": 960, "height": 720},
        "browsers": {},
    }
    for browser_name in BROWSER_NAMES:
        browser_type = getattr(playwright, browser_name)
        try:
            results["browsers"][browser_name] = _run_browser(browser_type)
        except PlaywrightError as exc:  # pragma: no cover - records unavailable engines
            results["browsers"][browser_name] = {
                "error": f"{type(exc).__name__}: {exc}",
            }
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with sync_playwright() as playwright:
        results = run(playwright)
    payload = json.dumps(results, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.write_text(payload)
    sys.stdout.write(payload)


if __name__ == "__main__":
    main()
