# State entries that a no-JavaScript form never reads (#869)

- **Pull request:** [#869](https://github.com/citry-dev/citry/pull/869),
  merged 2026-11-24 (57776bc29)
- **Reviewer:** a separate reviewing agent (correctness, versioning,
  security, a check against the maintainers' survey of security advisories
  published for other frameworks (Mechanism 8), and prose, each as its own
  pass), as the pull request description states. The pull request holds no
  report, comment or review thread. This record is built from the
  description, the merged change and its tests.
- **Code:** in `packages/py/citry/citry/ext/events/dispatcher.py`:
  `_can_send_state_action`, `_new_state_action`, `_resign_state`,
  `_renew_state` and the signed State size cap in `_prepare_call`; and the
  `prepare_state_token` and `commit_state_token` docstrings in
  `packages/py/citry/citry/ext/events/tokens.py`. Tests:
  `test_events_dispatch.py` and `test_events_routes.py` in
  `packages/py/citry/tests/`

## Who controls the input

The change adds no input. It changes when Citry writes a cache entry for
server-stored State. It also skips the size cap (`_max_bytes`, the State
size limit) on signed State for a browser write that the answer cannot
carry back (see "Follow-ups").

State is data that a component keeps between calls. The browser holds a
State token and sends it back with a call. With signed State, the token
carries the signed data. With server-stored State (`_storage = "server"`),
the data sits in the app's cache and the token names the entry.

Before this change, a call that changed server-stored State wrote the new
entry before Citry built the `state` action (the part of the answer that
hands the browser the new token). A form posted without JavaScript gets an
answer that drops `state` actions, so the entry was written and never
read. It expired after `_max_age` (the State's lifetime setting).

- **The caller instance** (`callerRenderId`) is a value the client sends.
  The number of entries a request can cause therefore stays client-driven.
  The description says the cache's State budget bounds it, as the docs
  describe.
- **The State values and the token** come from the same functions and the
  same values as before.

What is at risk is the cost to the server: cache entries that no browser
will read. Nothing new reaches the browser. The description names these
places: the State tokens the browser stores, Events responses that carry
`publicState`, and server-storage cache writes. The contributor rules in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)
(Mechanism 7) keep a list of the places where a value can reach the
browser. It has no item for cache writes.

## How it was checked

- **A route-by-route review.** The reviewer listed each route a value can
  take and found none that is new or unsafe. The change only removes
  writes, so the token, `publicState` and the error text are built the
  same way as before. The description says the reviewer found no hole in
  a released version.
- **Other frameworks' advisories (Mechanism 8).** The reviewer checked the
  change against the kinds of bug that those advisories describe, and
  the description says none apply. It does not name the kinds.
- **New tests.** The author ran them against `origin/main`'s
  `dispatcher.py`, and all fail there except one test,
  `test_the_new_token_is_the_one_entry_a_live_caller_reads_back`, which
  passed before the change too and checks that the new order still works.
  They cover a form posted without JavaScript that changes server-stored
  State (no entry, and no `state` action in the answer), the same through
  the real route with a 303 answer, a `state` action that cannot be built
  (no entry), signed State that is not capped when the answer cannot carry
  the token, and a live JavaScript caller that still gets one new token and
  reads it back. The existing renewal tests, `TestStateRenewal`, pass
  unchanged.
- **Test runs.** The focused `test_events_*.py` and State tests (2,394
  passed, 1 skipped), then every test under `packages/py/citry/tests`
  (15,497 passed, 75 skipped, 1 expected failure).
- **Static checks.** `ruff check`, `ruff format`, mypy and mypy with
  `--platform linux` on `citry` and the typing contract tests;
  `scripts/validate.py`; and `python -m docs_site build-check --strict`
  (0 errors, 0 warnings). The cargo and pnpm phases did not run locally,
  because no Rust or JavaScript changed.
- **Versioning.** The format of the JSON a call carries and the token
  format are unchanged, and the helpers are private. The description says
  writing fewer cache entries, and checking signed State size less
  strictly in a no-JavaScript answer, are not in the lists of covered
  behavior in `docs/codebase.md` ("Breaking changes"). It targets 1.3.0
  beside
  [#858](https://github.com/citry-dev/citry/pull/858), whose renewal
  path this matches.

## Ruled out


- **An unread entry after a form posted without JavaScript.** The State
  change now follows the order that the renewal path already had: prepare
  the token, build the `state` action, and write the entry last.
  `_can_send_state_action` says whether the answer can carry a `state`
  action. It answers no for the compatibility mode (the mode that answers
  a form posted without JavaScript, or another request that asks for HTML,
  with plain HTML), and otherwise whether the client advertised the kind.
- **An entry left behind by a `state` action that cannot be built.** An
  example is a public value the browser cannot read, such as an integer
  too large for a JavaScript number to hold exactly. The call still answers 500
  `handler_error`, and no entry remains.
- **Changed behavior for JavaScript callers.** None: the same token, the
  same `state` action, and one new entry.

## Fixed during the review

- Three docstrings and comments that claimed more than the code does: the
  shared check is for the dispatcher only, the `prepare_state_token` note
  applies to renewals only, and "form posted without JavaScript" also
  covers any request that asks for HTML.
- The design doc's description of what happens when a State change fails.
- The description of the signed State size cap change, which is now in the
  commit message.

## Not tested

- **A real browser or a real form post.** The tests post through the
  dispatcher and the route. The description lists no browser run.

## Follow-ups

The description leaves two cases out of this change and names no issue for
either:

- **A `Render` action in a no-JavaScript answer.** It still writes an entry
  for a component with server-stored State, and the HTML carries no token
  for it. The entry is written when the component renders
  (`emission.py`, `capture_instance`), before Citry knows whether the HTML
  will reach a client that can use the token. Every page view of such a
  component writes one, and the docs already list "every render" as a
  cost. Fixing it needs a decision about what the render-time token holds
  when the page's manifest (the list of components that the server sends
  with the page) is dropped.
- **A failure after the write.** An `on_event_result` hook that adds an
  action the client did not advertise can still leave the entry until it
  expires. The `_new_state_action` docstring says so.

The description also records a side effect. Signed State is not checked
against the size cap for a browser write in a no-JavaScript answer,
because nothing signs that State there, and a call with no caller instance
was already unchecked. It says only a request built by hand can carry
such a write, because the form codec never sends `stateUpdates`. The
description does not say the reviewer assessed this, and records no other
bound on such a write.

The pull request closes
[#860](https://github.com/citry-dev/citry/issues/860).
