"""Lifecycle checks for the landing page's component callback."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

pytestmark = pytest.mark.e2e


def test_landing_callback_removes_listeners_and_pending_work(page: Any) -> None:
    from docs_site._internal.components.landing import LandingPage

    page.set_content(
        """
        <div id="landing-root">
          <button data-copy-install>Copy</button>
          <section data-landing-picker>
            <button data-picker-case="first"></button>
            <div data-picker-panel="first"></div>
          </section>
          <section data-landing-tour data-tour-source="">
            <button data-tour="first"></button>
            <div data-tour-note="first"></div>
            <div class="landing-tour__notes"></div>
          </section>
          <section data-editor-showcase>
            <div data-editor-code><div class="landing-editor__bar"></div></div>
            <div class="highlight"><pre></pre></div>
            <button data-editor-symbol="member-chip-use">member-chip-use</button>
            <div data-editor-hover hidden>
              <div data-editor-hover-signature></div>
              <div data-editor-hover-provenance></div>
              <div data-editor-hover-description></div>
              <a data-editor-hover-docs></a>
              <a data-editor-jump></a>
              <span data-editor-jump-hint></span>
              <span data-editor-status></span>
            </div>
          </section>
        </div>
        """
    )

    result = page.evaluate(
        """async source => {
          const root = document.querySelector('#landing-root');
          const button = root.querySelector('[data-copy-install]');
          const tourRoot = root.querySelector('[data-landing-tour]');
          const registrations = [];
          const originalAdd = EventTarget.prototype.addEventListener;
          EventTarget.prototype.addEventListener = function(type, listener, options) {
            if (options && typeof options === 'object' && options.signal) {
              registrations.push({
                target: this,
                type,
                signal: options.signal,
                capture: Boolean(options.capture),
                passive: Boolean(options.passive),
              });
            }
            return originalAdd.call(this, type, listener, options);
          };

          const timers = new Map();
          let nextTimer = 0;
          const originalSetTimeout = window.setTimeout;
          const originalClearTimeout = window.clearTimeout;
          window.setTimeout = (callback, delay) => {
            const id = ++nextTimer;
            timers.set(id, { callback, delay });
            return id;
          };
          window.clearTimeout = id => timers.delete(id);

          const frames = new Map();
          let nextFrame = 0;
          const originalRequestAnimationFrame = window.requestAnimationFrame;
          const originalCancelAnimationFrame = window.cancelAnimationFrame;
          window.requestAnimationFrame = callback => {
            const id = ++nextFrame;
            frames.set(id, callback);
            return id;
          };
          window.cancelAnimationFrame = id => frames.delete(id);

          let pendingWrite;
          const writes = [];
          Object.defineProperty(navigator, 'clipboard', {
            configurable: true,
            value: {
              writeText(text) {
                writes.push(text);
                if (writes.length === 1) {
                  return new Promise(resolve => { pendingWrite = resolve; });
                }
                return Promise.resolve();
              },
            },
          });

          try {
            let callback;
            new Function('$component', source)(register => { callback = register; });

            const firstStart = registrations.length;
            const firstCleanup = callback({ component: { $el: root } });
            const firstRegistrations = registrations.slice(firstStart);
            const firstSignal = firstRegistrations[0].signal;
            button.click();
            firstCleanup();
            pendingWrite();
            await Promise.resolve();

            const afterFirstCleanup = {
              isCleanup: typeof firstCleanup === 'function',
              allListenersUseOneSignal: firstRegistrations.every(item => item.signal === firstSignal),
              signalAborted: firstSignal.aborted,
              capturePreserved: firstRegistrations.some(
                item => item.target === tourRoot && item.type === 'click' && item.capture,
              ),
              passivePreserved: firstRegistrations.some(
                item => item.type === 'scroll' && item.passive,
              ),
              copyTextAfterLateClipboard: button.textContent,
              pendingTimers: timers.size,
              pendingFrames: frames.size,
              hasGlobalListeners: firstRegistrations.some(item => item.target === document)
                && firstRegistrations.some(item => item.target === window),
            };

            const secondStart = registrations.length;
            const secondCleanup = callback({ component: { $el: root } });
            const secondRegistrations = registrations.slice(secondStart);
            const secondSignal = secondRegistrations[0].signal;
            button.click();
            await Promise.resolve();
            await Promise.resolve();
            const copiedText = button.textContent;
            const timersBeforeCleanup = timers.size;
            const framesBeforeCleanup = frames.size;
            secondCleanup();
            button.click();

            return {
              afterFirstCleanup,
              secondSignalIsFresh: secondSignal !== firstSignal,
              secondSignalAborted: secondSignal.aborted,
              writes,
              copiedText,
              textAfterPostCleanupClick: button.textContent,
              timersBeforeCleanup,
              timersAfterCleanup: timers.size,
              framesBeforeCleanup,
              framesAfterCleanup: frames.size,
            };
          } finally {
            EventTarget.prototype.addEventListener = originalAdd;
            window.setTimeout = originalSetTimeout;
            window.clearTimeout = originalClearTimeout;
            window.requestAnimationFrame = originalRequestAnimationFrame;
            window.cancelAnimationFrame = originalCancelAnimationFrame;
          }
        }""",
        LandingPage.js,
    )

    assert result == {
        "afterFirstCleanup": {
            "isCleanup": True,
            "allListenersUseOneSignal": True,
            "signalAborted": True,
            "capturePreserved": True,
            "passivePreserved": True,
            "copyTextAfterLateClipboard": "Copy",
            "pendingTimers": 0,
            "pendingFrames": 0,
            "hasGlobalListeners": True,
        },
        "secondSignalIsFresh": True,
        "secondSignalAborted": True,
        "writes": ["pip install citry", "pip install citry"],
        "copiedText": "Copied",
        "textAfterPostCleanupClick": "Copied",
        "timersBeforeCleanup": 1,
        "timersAfterCleanup": 0,
        "framesBeforeCleanup": 1,
        "framesAfterCleanup": 0,
    }
