# A handler's own guard skipped `_guard` (GHSA-2jch)

- **Advisory:**
  [GHSA-2jch-pr4c-gf9m](https://github.com/citry-dev/citry/security/advisories/GHSA-2jch-pr4c-gf9m),
  published 2026-11-25, severity medium (CVSS 3.1 score 6.8)
- **Affected and fixed versions:** `citry >= 0.3.0, < 1.3.0`; fixed in
  1.3.0
- **Fix:** the commits from `2835e4ba4` to `123dd8644` (the range also
  holds three async-guard commits of GHSA-gj9m, merged in), merged to
  `main` 2026-11-25 with the other 1.3.0 security fixes in `31bc11ef5`
  ([#881](https://github.com/citry-dev/citry/pull/881)):
  - **Order.** The component's `_guard` (or the app-wide `_guard` when
    the component sets none) runs first, then the handler's own
    `@event(guard=...)`, and either one refusing refuses the call. A
    handler skips the component's guard only with
    `@event(component_guard=False)`.
  - **Return values.** A returned `EventError`, any other returned
    exception, or a false value other than `None` refuses the call, and
    a returned function fails it with a 500.
  - **Class definition.** Citry raises an error when a second
    `@event(...)` decorates a function that already has settings, and
    each handler keeps the settings it had when its class was created.
- **Reviewer:** separate reviewing agents, in six rounds on the fix,
  plus a read of the docs as a first-time reader
- **Code:** the guard block of `_prepare_call` and `_apply_guard_result`
  in `packages/py/citry/citry/ext/events/dispatcher.py`;
  `refuse_stacked_event`, `refuse_hidden_event_settings` and `event` in
  `packages/py/citry/citry/ext/events/handlers.py`;
  `verb_handler_methods` in
  `packages/py/citry/citry/ext/events/view_events.py`; tests in
  `packages/py/citry/tests/test_events_dispatch.py`,
  `test_events.py`, `test_events_routes.py` and
  `test_events_view_events.py` in the same folder

## Who controls the input

An event handler is a Python function on a component that the browser
calls, and a guard decides who may call it. The app author writes the
guards: a component's `_guard`, an app-wide
`_guard` in `extensions_defaults["events"]`, and a handler's own
`@event(guard=...)`. The request that a guard should refuse comes from
anyone who can reach the event route.

In affected versions, a handler's own guard replaced the component's
`_guard` instead of running beside it. The guides said that `_guard`
runs before every handler, so an author who added an owner check to one
handler removed the component's login check from it. A caller who
passed the handler's check could then call it. In the same versions, a
guard that returned `False` or an exception, in place of raising,
refused nothing, and a `guard=` in the inner one of two stacked
`@event(...)` decorators did not run.

The review also found these in affected versions, and the fix closes
them: a guard that returned a function, as `return self.can_edit` does
without the `()`, let the call through; a decorator above `@event(...)`
that kept `__wrapped__` but not the settings dropped the guard without
an error; and one function decorated for two classes, or used as a
`ViewEvents` verb in two classes, let the later class change the
earlier one's settings, which in one case could make a handler accept
`GET` and so skip the CSRF checks. (`ViewEvents` maps HTTP verbs such
as `get` and `post` to handlers.)

What was at risk is the app's data and actions behind the handler. No
value reaches the browser by a new route.

Of the places in the Mechanism 7 list in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser),
this change touches "Responses Citry serves": the error bodies of the
refused calls, which may carry the message of an `EventError` that a
guard returns.

## How it was checked

- **Releases.** 0.3.0 and 1.2.0 were run from their published wheels,
  over the ASGI batch route and the WSGI per-event route.
- **Routes.** The batch route (sync and async dispatch), the per-event
  `POST` and `GET` routes, the form post without JavaScript, the
  `ViewEvents` verb route, detached handlers, `dispatch`,
  `dispatch_async` and custom transports. Every route runs the guards
  in one place, `_prepare_call`.
- **Where the guards are set.** On the component, on a mixin or a parent
  class, as a `staticmethod`, as the app-wide default only, and with the
  same function at both levels.
- **Return values.** At each guard level, sync and async dispatch: true
  and false values of many types, returned `EventError` instances and
  subclasses, other returned exceptions and exception classes, functions
  and other callables, values whose truth test raises, and objects that
  imitate a NumPy boolean, a Django QuerySet, `AnonymousUser` and
  `HttpResponseForbidden`. Django 6.0.6 objects were checked for the
  callable rule.
- **Answers.** A refused call answers 403 with a fixed message, or the
  returned `EventError`'s own status and message. On the form post
  without JavaScript the 403 is `text/plain; charset=utf-8` with
  `X-Content-Type-Options: nosniff`. A returned error whose message holds
  markup or line breaks reached only JSON and plain-text answers, added
  no header, and the text of any other returned exception was never
  sent. The warning that Citry logs names the guard's type and name, not
  the value.
- **Tests.** Each round added tests that fail on the code before it. The
  events test files and the `citry` package suite passed, apart from
  failures that came from the reviewers' local environments and fail the
  same way without the fix.
- **Versioning.** The fix refuses calls and code that 1.2.0 accepted. It
  ships under the security exception in the 1.3.0 minor release, and the
  changelog names each case. `component_guard` is a new optional
  argument.
- **CI.** Nothing ran in the private fork, because GitHub Actions does
  not run there. CI ran on the public pull request
  ([#881](https://github.com/citry-dev/citry/pull/881)) before it
  merged.
- **Other frameworks' advisories (Mechanism 8).** The reviewers read the
  maintainers' private survey of security bugs published for other
  frameworks and checked these kinds: an authorization check written
  async (`async-authz`), names that pick code (`name-to-code`), CSRF
  (`csrf`, `xsrf-leak`), State from another request (`xreq-state`), a
  second path that skips a check (`sanitizer-bypass`), error pages
  (`error-page`), log injection (`log-inj`), header injection
  (`header-inj`), server data reaching the client (`source-exposure`),
  path authorization (`path-authz`) and island hydration (`island`).
  This advisory added a kind to the survey: a per-route authorization
  check that replaces the global one (`authz-replace`).

## Ruled out

- **A request that skips the component's guard.** None of the routes
  above let a call through that either guard refuses. `self.event.name`
  comes from the same string Citry uses to find the handler, so a
  request cannot make it name another handler.
- **Other settings that replace the component's.** `@event(csrf=...)`
  replaces `_csrf` and `@event(methods=...)` replaces `_methods`. One
  call carries one CSRF scheme and Citry's own checks still run, so
  these are safe, and the docs say they replace. `_debounce` and
  `_throttle` are browser timing hints, not limits.
- **Author-only by design.** `@event(component_guard=False)`,
  `_guard = None` on a component (it replaces the app-wide guard), and
  an `on_event` hook that answers a call itself all skip guards on
  purpose; `docs_site/content/security.md` ("Authorize every event")
  says so. A truthy value such as `request.user` lets the call go ahead
  with a logged warning, as `security.md` documents.

## Fixed during the review

- The first version of the fix refused only a guard that returned
  `False`. A returned `EventError`, another exception or an empty value
  still let the call through; each now refuses it.
- Handler settings built in code with `component_guard=0` skipped the
  component's guard; only `False` skips it now, and `@event` accepts
  only `True` or `False`.
- A returned exception kept the traceback of the last call, with its
  request and State; Citry now clears it, down the exception's chain,
  without touching the exception the server was already handling.
- The lead `_guard` example in the docs called the shared check without
  returning its result.
- Wording of the warning, the docs, the changelog and the advisory, and
  line references in `docs/design/trust_boundaries.md`.

## Not tested

- Django, Flask and FastAPI end to end, and a real browser. The routes
  were run through Citry's own ASGI and WSGI apps and the dispatcher.
- Real NumPy, pandas and Cython objects; imitations stood in for them.
- PyPy and free-threaded Python.

## Follow-ups

- Reloading a module with `importlib.reload`, or with an editor or
  notebook tool such as Jupyter's `%autoreload`, raises the error for
  a function that already has `@event(...)` settings when the module applies `@event(...)` to a
  function imported from another module. `docs_site/content/security.md`
  ("Authorize every event") says so.
- [#875](https://github.com/citry-dev/citry/pull/875) runs the guards
  before Citry checks a call's data; see its own record,
  [`2026-11-25-guards-before-data-check-875.md`](2026-11-25-guards-before-data-check-875.md).
