# `Dispatch` refuses browser event names (#867)

- **Pull request:** [#867](https://github.com/citry-dev/citry/pull/867),
  merged 2026-11-24 (b565dbc52)
- **Reviewer:** a separate reviewing agent (technical, security,
  versioning and a prose pass, and a check against the maintainers'
  survey of security advisories published for other frameworks, which
  `CLAUDE.md` calls Mechanism 8, then a
  review of its own follow-up fixes), and a separate agent that read the
  docs as a first-time reader would, as the pull request description
  states. The pull request holds no report, comment or
  review thread. This record is built from the description, the merged
  change and its tests.
- **Code:** `Dispatch.__post_init__`, `reserved_event_name_reason` and
  `RESERVED_EVENT_PREFIXES` in
  `packages/py/citry/citry/ext/events/actions.py`; `DOM_EVENT_NAMES` in
  `packages/py/citry/citry/_html_attribute_values.py`, written by
  `scripts/generate_html_attribute_values.py`; `refuseReservedEventName`
  and its copy of the name list in
  `packages/py/citry/citry/_vue/client.js` (the rebuilt `runtime.js`
  carries the same code). Tests:
  `packages/py/citry/tests/test_events_dispatch_names.py`,
  `packages/js/citry-client/test/dispatch-event-names.test.mjs`, and
  `test_the_browser_refuses_a_standard_event_name_on_a_mounted_component`
  in `packages/py/citry/tests/e2e/test_vue_events_default_e2e.py`

## Who controls the input

An Events handler (Python code that the browser calls) can return a
`Dispatch` action. It makes Citry's browser code fire a `CustomEvent`, a
browser event that carries a name and some data, at the calling
component's first element. The event bubbles: it reaches listeners on that
element, its ancestors, `document` and `window`.

- **The `name` of a `Dispatch` action.** The app's Python code chooses it,
  from its own list. The docs say never to copy it from a request. When a
  handler does take it from request data, the request picks which of the
  page's listeners run.
- **The action's `detail`.** It may carry request data as JSON. This change
  does not touch it.
- **The `event` action in the browser.** `Dispatch` reaches the browser as
  an `event` action. Citry's browser code gets it from a server answer,
  through the Events bridge (the browser code that runs an Events call and
  applies its results), or from page code that calls
  `Citry.events.applyActions`.

The change makes `Dispatch` refuse the names of standard browser events
(such as `click`) and names that start with `citry:`, `vue:` or `vnode-`.
Citry's browser code refuses the same names before it fires the event.

A standard name such as `click` runs the page's own listeners for it,
including Vue `@click` handlers and `@c-*` bindings (Citry's bindings that
call the server). What is at risk is which of the app's own listeners run.

The contributor rules in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)
(Mechanism 7) keep a list of the places where a value can reach the
browser. The list now names this place as "Event names in `Dispatch`
actions".
[#874](https://github.com/citry-dev/citry/pull/874) added it after this
change merged.

## How it was checked

- **Review passes.** The reviewer ran a technical pass, a security pass
  (Mechanism 7), the check against the survey of other frameworks'
  advisories (Mechanism 8), a versioning check and a prose pass, then
  reviewed the follow-up fixes. The description does not name the kinds
  picked from the survey. It says the reviewer found no hole in any
  released version, because the name was already documented as app code,
  never request data.
- **The list of names, in three browsers.** The description says the
  reviewer checked browser event names that were missing from the list in
  Chromium, Firefox and WebKit, and that no `on*` handler outside the list
  remains. It names no browser versions.
- **Python tests.** `test_events_dispatch_names.py` (33 tests) covers
  representative refused names, letter case variants, the prefixes,
  accepted custom names (including lookalike letters and spaces around a
  name), the match between the two copies of the list, and the
  generator's marker writer. The focused Events and tooling tests
  passed (3,254 tests).
- **JavaScript tests.** `dispatch-event-names.test.mjs` (22 tests) runs
  against the shipped `runtime.js`: refused and accepted names, actions that
  do not wait for the previous one (`wait: false`), and the runtime's own
  check when the protocol validator (the code that checks the format of a
  call) is bypassed. All 414 `citry-client` tests passed, including the test
  that compares the rebuilt bundle with its source.
- **End to end.** The browser test covers both bridge paths (see "Ruled
  out"). The author confirmed that removing either browser check makes it
  fail. The description does not name the browser.
- **Static checks.** `ruff` and mypy (also with `--platform linux`) and
  `scripts/validate.py` passed. In the local fast check, pytest, the
  validators and the JavaScript packages passed. The Rust phases and some
  pnpm phases did not run in the author's environment. The description
  says CI runs them.
- **Versioning.** The description says Citry 1.3.0 refuses names that
  earlier releases accepted, under the security exception in
  `docs/codebase.md` ("Breaking changes"). The changelog entry is marked
  Security. It lists the refused names, including common words such as
  `close` and `message`, and shows the fix: prefix the name with the
  component's name.

## Ruled out

- **A standard event name in another letter case.** `Click`, `KEYDOWN`,
  `DOMContentLoaded` and `Citry:ready` are refused. Browsers match event
  names exactly, but some code treats `Click` and `click` as the same name:
  HTML reads an `onClick` attribute as `onclick`, and Vue reads `@Click` on
  a component tag as `click`. No app needs a custom event that differs from
  a standard one only in case.
- **A lookalike letter or spaces around a name.** Both checks lowercase
  only the ASCII letters `A` to `Z`. A name with a Cyrillic `с` or the
  Kelvin sign (U+212A, which looks like `K`) matches no standard
  listener, and Python and JavaScript disagree on how to lowercase some
  non-ASCII letters, so lowercasing them would let the two checks
  disagree. Spaces around a name are not
  trimmed, because a browser matches no listener for ` click`.
- **A name that reaches the browser without the server check.** One
  function, `refuseReservedEventName`, runs before any listener on every
  browser path:
  - `applyActions` on a page with no mounted component, including
    `wait: false` and delayed actions;
  - the Events bridge's `dispatchEvent`, for a result that targets a
    mounted component, before the `onEvent` listeners as well as the DOM
    event;
  - the bridge's `dispatchEventGlobal`, for an event with no target.
- **The prefixes.** Names that start with `citry:`, `vue:` or `vnode-` are
  refused, on the server and in the browser.
- **The two copies of the list disagreeing.** A test compares the block
  in `client.js` with the Python table, and the prefix lists.
- **Regenerating the list from its upstream sources, and dropping a common
  name.** The generator script's `REQUIRED_NAMES` now also requires
  `submit`, `input`, `change`, `keydown` and `message`.

## Fixed during the review

- Browser event names missing from the list. The description says the
  reviewer checked them in three browsers and that no `on*` handler
  outside the list remains. It also says the pull request adds 44 names
  that browsers fire at `document` and `window`, or still fire without a
  current standard, for 175 in all. It does not say how many of the 44
  came from the review.
- A browser test that did not reach either bridge path. The end-to-end
  test now covers both.
- The findings of the agent that read the docs as a first-time reader,
  which the description says were applied. It does not list them.

## Not tested

- **The Rust and some pnpm phases of the local check.** They did not run
  locally. The description says CI runs them.

## Follow-ups

- **Refresh the generated tables.** The author edited the
  `DOM_EVENT_NAMES` line by hand, in the format the generator writes,
  because the author's environment could not download the sources. The
  module header still says the tables were generated on 2026-10-21. The
  description asks for a run of
  `scripts/generate_html_attribute_values.py` online before the release,
  to refresh all tables together. It does not say whether that has
  happened.
- **The protocol's reference validators still accept these names.** The
  validators (Python, JavaScript and JSON Schema) check the format of the
  JSON a call carries. The Events v1 spec row says the refusal is Citry's
  own rule, applied on top of that format.

The pull request closes
[#704](https://github.com/citry-dev/citry/issues/704).
