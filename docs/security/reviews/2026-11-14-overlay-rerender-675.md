# Open overlays after a server render (#675)

- **Pull request:** [#675](https://github.com/citry-dev/citry/pull/675),
  merged 2026-11-14 (499f4fcfc)
- **Reviewer:** an independent reviewer, as the pull request description
  states. The pull request holds no report, comment or review thread.
- **Code:** the browser code of Citry UI (Citry's component library) in
  `packages/py/citry_ui/citry_ui/components/`: `_dialog_controller.py`
  and one file per component, named after its directory (for example
  `cdialog/cdialog.py`). Tests are in
  `packages/py/citry_ui/tests/e2e/` and
  `cpopover/tests/e2e/test_cpopover_e2e.py`. The change also edits the
  changelog and the size limits, which do not run in the browser.

## Who controls the input

When a server event re-renders part of a page, Citry first calls the
cleanup function that each component's browser code returned last time.
It then runs each component's `onServerRender` callback again (the
browser code that takes over the component's elements). Each call is a
"run". Children run before their parent, an order that
[#651](https://github.com/citry-dev/citry/pull/651) set.

Several Citry UI components were written for parent first: `CDialog`,
`CDrawer`, `CPopover`, `CCommandPalette`, the pickers (`CDatePicker`,
`CDateRange`, `CTimePicker`) and `CAccordion` (a list of items that open
and close). After a server render, an open overlay (a dialog, drawer,
popover or palette that opens over the page) could close, or open below
the overlay around it. `CAccordion` could skip reporting the open items
the render removed, and skip moving focus when the focused item was
removed. The change fixes the components, not the order.

The inputs are the ones these components already read: the `open` and
`disabled` values that the app's Python code passes in, and the nesting
that the template author writes. The pull request says no value from
data reaches a new place in the page. The change adds these pieces of
browser code:

- A cleanup that accepts `{handoff: true}` in the pickers and in
  `CPopover`. In a handoff, the old run leaves its state in place until
  the next run takes it over. An open popover stays showing and stays
  registered as a layer (its entry in the shared list that decides which
  open popover answers Escape and outside clicks).
- A flag in each picker (such as `datePickerAwaitingRun`) that keeps the
  popup closed between the cleanup and the next run, when the server has
  just disabled the picker.
- A timer in `CPopover` that checks a handed-over layer, first after
  0 ms and then every 50 ms.
- A wait of one task (a short delay that lets the other callbacks of the
  same render run first) before a dialog, drawer or palette opens inside
  a dialog that is open but not yet modal. A modal dialog blocks the rest
  of the page and sits in the top layer, above all page content.
- Counters of open and close requests, so a delayed open runs only if
  nothing changed after it.
- A change that makes the drawer's `MutationObserver` (the browser's
  watcher for changes to elements) watch every element from the drawer's
  host up to the document for the attributes that hide it and for
  children added or removed.
- In `CAccordion`, no item state is applied until the accordion has
  compared its registered items with the open and focused ones.
- The palette lists itself in the shared list of open dialogs.

A flaw here would leave an overlay stuck open, hidden behind another
one, or waiting without end. The diff writes no markup or script (see
"How it was checked").

## How it was checked

The pull request says an independent reviewer confirmed that the change
touches only component browser code and sends no value from data to a
new place in the page. No open hole is recorded. The description also
says the reviewer checked four kinds of bug from the maintainers'
advisory survey (Mechanism 8 in `CLAUDE.md`): DOM clobbering (a page
element's `id` or `name` replacing a value the script expects), the
prototype kind (data keys such as `__proto__` that change every object),
hydration (browser code taking over server-written HTML) and denial of
service. No report from the reviewer is attached, so this record cannot
say what inputs it tried.

The author of this record read the merged diff. No changed line of
component code builds HTML, a selector, a URL or a script from a value,
and every `setTimeout` call gets a function, never a string. The shared
state the change uses sits under fixed keys:
`Symbol.for("citry-ui:dialog-runtime")`, which `CDialog`, `CDrawer` and
the dialog controller already use, and
`Symbol.for("citry-ui:popover-handoff")`, which `CPopover` already uses.

The pull request's author reports these checks. The end-to-end tests
drive the components in a real browser.

- With the runtime rebuilt in the old callback order, all 21
  end-to-end tests that fail on `main` before this change passed. The
  order alone caused them.
- Against the published `citry-core==1.9.1`, the Citry UI end-to-end
  suite gave 1085 passed; 17 more are marked as known failures and
  failed as expected. The other Citry UI tests that the author ran, and
  `ruff` (the Python linter), passed.
- New tests cover a `CPopover` inside an open `CPopover` across a server
  render (`test_server_rerender_keeps_a_popover_open_inside_an_open_popover`),
  `CCommandPalette` inside `CDialog` and `CDrawer`, and a check that the
  innermost overlay is on top in every nested case.

## Ruled out

- **A wait that never ends in a dialog, drawer or palette:** a waiting
  open retries once per enclosing dialog, then opens. The cap is
  `Math.max(0, depth - attempts)`, where `depth` counts the enclosing
  dialogs. A dialog left open without being modal never changes, so the
  inner overlay opens once the cap is reached. A later open or close
  cancels a waiting retry through the request counter, and so does the
  cleanup: it raises the counter in `CDialog` and the palette, and sets
  `disposed` in `CDrawer`.
- **A popover timer that never stops (code read, no test):** the timer
  stops when the next run takes the layer over (that run clears it) or
  when the popover leaves the page (the check fails and nothing is
  re-armed).
- **A drawer observer that loops (code read, no test):** the observer
  fires on changes to `class`, `hidden`, `inert`, `open` and `style` on
  every ancestor, and on children added or removed. Its callback
  `reconcileEligibility` closes the drawer (`forceClose`) when it may no
  longer open, or runs `onNativeClose()` when the browser already closed
  it. Both stop the observer (`stopEligibilityWatch`), which discards
  its queued records, so its own writes cannot fire it.
- **Data choosing code, markup or addresses:** the added code reads the
  elements around the component and writes attributes and open state
  that the components already write, such as `data-open` and `inert`.
- **Data-chosen `id` or `name`:** the changed code finds elements by
  their position in the page, by element type (`HTMLDialogElement`) and
  by `:modal` or `:popover-open`, never by `id` or `name`.
- **Data-chosen property names:** the new properties and keys have fixed
  names, so a key such as `__proto__` has no place to land.

## Fixed during the review

Nothing recorded.

## Not tested

- What the independent reviewer tried. No report is on file.
- The browsers. The description does not say which ones ran the
  end-to-end suite.
- The two Tailwind CSS coexistence test files and the type-check test,
  which the author did not run.
- The cap, the 50 ms `CPopover` check and the drawer observer reacting
  to ancestors. The diff adds no test of them.
- A handed-over `CPopover` that stays on the page when no next run
  starts. The timer would then keep re-arming. The diff does not show
  whether Citry always starts a next run after a handoff.
- Cases the description lists as outside this change: a popup that one
  server render opens inside a dialog it also opens (it fails with the
  old order too), and three other components that may have the same bug,
  found by reading code and not reproduced: `CSortable`, a grouped
  `CToggle` and `CFileInput` inside `CField`.

## Follow-ups

No issue is linked. `enclosingDialogWait` exists twice, in the dialog
controller (used by `CDialog` and the palette) and in `CDrawer`, and the
description lists one shared helper as future work. Until then, a change
to the cap in one copy must reach the other.
