"""Every browser scenario goes quiet once it has settled."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry_ui.quality.scenarios import SCENARIOS, QualityTool

# Reuse the steps that put each scenario into its active state, so the two
# tests cannot disagree about what "active" means.
from citry_ui.quality.tests.e2e.test_scenario_catalog_e2e import (
    _activate_representative_state,
    _install_image_scenario_routes,
)

# Each browser scenario waits 0.7 s to settle and 0.9 s to measure. With
# about 80 scenarios the file takes about 3 minutes on one worker (measured on
# Chromium). Spread over three workers without `--dist loadfile` it takes
# about 1 minute, but the cross-browser job keeps a whole file on one worker,
# so expect about 3 minutes there. That is too slow for every pull request,
# so only the weekly cross-browser job runs it.
pytestmark = [pytest.mark.e2e, pytest.mark.weekly]

_BROWSER_SCENARIOS = tuple(scenario for scenario in SCENARIOS if QualityTool.BROWSER in scenario.tools)

# A component that repairs its markup from an observer, or two observers that
# answer each other, can run in a loop that keeps the page busy while nobody
# touches it. That burns CPU and battery, and nobody sees it: the page looks
# and works the same, so only a count of what the page does while idle shows
# it. A scenario that fails here names the stack or the mutation that repeats.
#
# The guard counts in three back-to-back windows of 300 ms and fails a key
# only when it reaches the limit in every window. A real loop is busy in each
# window, because it runs hundreds of times a second. Settling work is usually
# busy in the first window only: a smooth scroll that ends late, or a re-render
# that a slow runner delivers after the settle wait. One window would flag
# that work on a slow runner, so a single busy window does not count.
_IDLE_WINDOW_MS = 300
_WINDOW_COUNT = 3
_FOCUS_LIMIT = 5
_REPEAT_LIMIT = 10

# The guard counts timer creations as well as DOM changes, so a component that
# runs a per-frame loop on purpose trips the timer rule. CMenuSubmenu does
# this: it calls requestAnimationFrame on every frame while a submenu is open
# (see `requestAnimationFrame` in cmenu.py). No scenario's active state opens
# a submenu today. A scenario that does must decide whether the loop is
# expected, and then exempt it here on purpose rather than loosen the limit.
#
# The timer rule is a heuristic. A per-frame loop makes about 18 calls in 300
# ms at 60 Hz, so a runner that drops frames can fall under the limit.
#
# The guard cannot see:
# - changes inside shadow roots, because a MutationObserver on the document
#   does not report them;
# - changes inside iframes, which have their own document and timers;
# - a loop that starts only after a popup closes, because a scenario that
#   opens a popup keeps it open for the whole measurement;
# - a timer or interval created before the spy is installed, or a timer
#   function that code saved before then; only its DOM changes and focus()
#   calls show up;
# - loops that run through microtasks, message channels, idle callbacks,
#   resize or intersection observers, or network requests, unless they also
#   change the DOM or call focus().
_IDLE_SPY = """async ({ windowMs, windowCount }) => {
  const state = () => ({ focus: 0, timers: {}, mutations: {} });
  let current = state();
  const count = (table, key) => { table[key] = (table[key] || 0) + 1; };
  // Take the real setTimeout before it is wrapped below, so the windows do
  // not count their own waits.
  const realSetTimeout = window.setTimeout.bind(window);
  const wait = (ms) => new Promise((done) => realSetTimeout(done, ms));
  // The first two frames are this helper and the wrapper below; the next
  // three name who created the timer. Chromium puts "Error" on the first
  // line and Firefox does not, so drop that line before taking frames.
  const caller = () => new Error().stack.split('\\n')
    .filter(line => line.trim() && line.trim() !== 'Error')
    .slice(2, 5).map(line => line.trim()).join(' < ').slice(0, 300);
  const focus = HTMLElement.prototype.focus;
  HTMLElement.prototype.focus = function (...args) {
    current.focus += 1;
    return focus.apply(this, args);
  };
  for (const name of ['setTimeout', 'setInterval', 'requestAnimationFrame']) {
    const original = window[name];
    window[name] = function (...args) {
      count(current.timers, `${name} ${caller()}`);
      return original.apply(this, args);
    };
  }
  new MutationObserver((records) => {
    // One re-render can touch many siblings with the same kind of change.
    // Count each key once per callback, so a loop is measured by how often
    // it runs and not by how many elements one run touches.
    const keys = new Set();
    for (const record of records) {
      const target = record.target;
      const part = target.nodeType === 1
        ? target.getAttribute('data-citry-ui-part') || target.localName
        : '#text';
      keys.add(`${record.type} ${record.attributeName ?? ''} on ${part}`);
    }
    for (const key of keys) count(current.mutations, key);
  }).observe(document, { subtree: true, childList: true, attributes: true, characterData: true });

  // Swap in a fresh table at each window boundary, in page JS, so no call
  // back to the test process delays the start of the next window.
  const windows = [];
  for (let index = 0; index < windowCount; index += 1) {
    await wait(windowMs);
    windows.push(current);
    current = state();
  }
  return windows;
}"""


def _busy_in_every_window(windows: list[dict[str, Any]], table: str, limit: int) -> dict[str, list[int]]:
    """Return keys that reached `limit` in every window, with their count per window."""
    keys = set.intersection(*(set(window[table]) for window in windows))
    busy = {key: [window[table][key] for window in windows] for key in sorted(keys)}
    return {key: counts for key, counts in busy.items() if all(n >= limit for n in counts)}


@pytest.mark.parametrize("scenario", _BROWSER_SCENARIOS, ids=lambda scenario: scenario.id)
def test_scenario_is_idle_in_its_active_state(page: Any, open_scenario: Any, scenario: Any) -> None:
    if scenario.id == "image.states":
        _install_image_scenario_routes(page)
    open_scenario(scenario.id)
    page.wait_for_selector(scenario.ready_selector, state="attached")
    _activate_representative_state(page, scenario.id)
    # Let opening animations, positioning and the first re-render finish
    # before counting, so only repeated work is left.
    page.wait_for_timeout(700)
    windows = page.evaluate(_IDLE_SPY, {"windowMs": _IDLE_WINDOW_MS, "windowCount": _WINDOW_COUNT})

    focus_per_window = [window["focus"] for window in windows]
    hot_timers = _busy_in_every_window(windows, "timers", _REPEAT_LIMIT)
    hot_mutations = _busy_in_every_window(windows, "mutations", _REPEAT_LIMIT)
    span = f"each of {_WINDOW_COUNT} windows of {_IDLE_WINDOW_MS} ms"
    assert not all(n >= _FOCUS_LIMIT for n in focus_per_window), (
        f"{scenario.id}: focus() ran {_FOCUS_LIMIT}+ times in {span}: {focus_per_window}"
    )
    assert not hot_timers, (
        f"{scenario.id}: timers created {_REPEAT_LIMIT}+ times in {span} (counts per window): {hot_timers}"
    )
    assert not hot_mutations, (
        f"{scenario.id}: DOM changes repeated {_REPEAT_LIMIT}+ times in {span} (counts per window): {hot_mutations}"
    )
