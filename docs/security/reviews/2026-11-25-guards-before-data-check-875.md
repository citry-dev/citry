# Guards run before the data check (#875)

- **Pull request:** [#875](https://github.com/citry-dev/citry/pull/875),
  merged 2026-11-25 (0a77df467); closes
  [#861](https://github.com/citry-dev/citry/issues/861)
- **Reviewer:** none is named, and the pull request holds no report,
  comment or review thread. This record is built from the description,
  the merged change and its tests.
- **Code:** `EventsDispatcher._prepare_call` in
  `packages/py/citry/citry/ext/events/dispatcher.py`; tests
  `TestGuardsBeforeDataCheck` and `TestGuardsSeeStateWrites` in
  `packages/py/citry/tests/test_events_dispatch.py`,
  `TestGuardsBeforeDataCheckOverHttp` in
  `packages/py/citry/tests/test_events_routes.py`, and
  `TestVerbRouteGuardOrder` in
  `packages/py/citry/tests/test_events_view_events.py`

## Who controls the input

An event handler is a Python function that the browser calls. A guard
is a function that the app author writes to decide who may call it. Each
call carries args, which anyone who can reach the event route supplies,
and Citry checks them against the handler's `data` class (the class
that declares the call's data).

Before this change, Citry checked the args before it ran the guards. A
caller that a guard would refuse still had its whole payload checked,
which is the costly step of a call, and got a 422 that listed what was
wrong with its own args before it got the guard's 403. Citry now runs
the `on_event` hook (an extension hook that sees each call), `_context`
(the app's function that builds a call's context) and the guards first,
and checks the args last.

The inputs, by who first supplies them:

- **The args.** Request data. The guards now read them before Citry has
  checked them, through `self.event.args`, so a key can be missing or
  hold a value of another type or size. The guards get a copy, so a
  guard that changes it cannot change what the `data` class checks.
- **State writes.** State is data that a component keeps between
  calls, and the browser may write the fields listed in `State._model`.
  These writes are request data too. As before, a guard sees State
  after them, and a
  State write that fails its check answers 422 before any guard runs.
- **The guards, `_context` and `on_event`.** App code. They now also run,
  with any side effects, for calls whose args are invalid.

What is at risk is not what the browser shows. It is what a refused
caller learns and costs: before the change it could make the server
check a large payload, and read field errors about it, without passing
the guard.

Of the places in the Mechanism 7 list in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser),
this change touches "Responses Citry serves": which error body a refused
call gets.

## How it was checked

- **Dispatcher tests.** `TestGuardsBeforeDataCheck`, sync and async:
  a refused caller with invalid args gets 403 with no field errors; an
  allowed caller with invalid args still gets 422; `_context` and the
  guard each run once; each call of a batch gets its own answer; a
  handler's own guard; a handler without `data`; a guard that changes
  the args; and a guard that fails on invalid args (500).
- **State tests.** `TestGuardsSeeStateWrites`: a guard sees the written
  State value, and a refused State write answers 422 before the guard.
- **Routes.** `TestGuardsBeforeDataCheckOverHttp` covers the per-event
  route, the batch route, a form post without JavaScript, and a `GET`
  handler. `TestVerbRouteGuardOrder` covers the `ViewEvents` verb route.
- **The old order.** The description says the new order tests fail
  against the old dispatcher. Two existing tests that encoded the old
  order were updated.
- **Checks run locally.** ruff, mypy on macOS and with `--platform
  linux`, the protocol contract checks, `scripts/validate.py`, and the
  `citry` Python tests without the end-to-end tests (15,898 passed before
  the review fixes, and every events test passed after them).
- **Versioning.** No call that 1.2.x accepted is refused. A call that a
  guard refuses gets the guard's error where 1.2.x answered 422, and
  a guard that indexes `self.event.args` and fails on a missing key now
  answers 500. The changelog lists both under "Security:" in 1.3.0. The
  `on_event` hook is experimental. No wire format changes.
- **Other frameworks' advisories (Mechanism 8).** The description
  records no check against the maintainers' survey.

## Ruled out

- **A guard trusting a value the caller chose.** For State writes this
  is not new: guards already saw the browser's writes to `_model`
  fields. For args it is new: guards now run before the check, so
  `self.event.args` can hold values the check would have refused. A
  guard that fails on one answers 500, not 200, so the call is still
  refused. `docs_site/content/security.md` ("Authorize every event") and
  `docs_site/content/events/state.md` tell authors to read args with
  `.get()`, check their type, and leave the fields a guard decides on
  out of `_model`.
- **A guard changing what the handler receives.** The guards get a copy
  of the args, and a test covers a guard that changes them.
- **The order of error codes in the protocol.** The
  [Events v1 spec](../../../packages/protocol/events/v1/spec.md) does not
  say whether a guard's error or `invalid_args` comes first, so it is
  unchanged.

## Fixed during the review

Nothing recorded. The description does not list the review's findings.
The pull request's second commit gives the guards a copy of the args
and adds tests for a guard that fails on invalid args, a guard that
sees the browser's State writes, and a refused State write that answers
before the guards, but the record does not say which of these the review
asked for.

## Not tested

- A real browser. The description lists no end-to-end test.
- The full repository gate before merge. The description lists the
  package tests and checks above.

## Follow-ups

- The 1.3.0 security fixes in
  [#881](https://github.com/citry-dev/citry/pull/881) build on this
  order: the guards that now run first are the ones those fixes changed.
  See
  [`2026-11-25-guards-run-together-ghsa-2jch.md`](2026-11-25-guards-run-together-ghsa-2jch.md)
  and
  [`2026-11-25-async-guards-ghsa-gj9m.md`](2026-11-25-async-guards-ghsa-gj9m.md).
