# Async guards, `_context` and `_csrf` (GHSA-gj9m)

- **Advisory:**
  [GHSA-gj9m-wwqx-m37j](https://github.com/citry-dev/citry/security/advisories/GHSA-gj9m-wwqx-m37j),
  published 2026-11-25, severity high (CVSS 3.1 score 7.4)
- **Affected and fixed versions:** `citry >= 0.3.0, < 1.3.0`; fixed in
  1.3.0
- **Fix:** the commits from `907883ff8` to `a2692cb95`, merged to `main`
  2026-11-25 with the other 1.3.0 security fixes in `31bc11ef5`
  ([#881](https://github.com/citry-dev/citry/pull/881)). Citry refuses an
  `async def` guard, `_context` or `_csrf` function with a `ValueError`
  when the component class is defined. If a guard or `_csrf` function
  still returns a coroutine, another awaitable, a generator or an async
  generator when it is called, Citry refuses the call. `_context` may
  return awaitables as data, so Citry refuses only a coroutine from it.
- **Reviewer:** separate reviewing agents, in five rounds on the fix
- **Code:** `defers_its_body` and `refuse_deferred_result` in
  `packages/py/citry/citry/ext/events/handlers.py`, used for `_guard`,
  `_context`, `_csrf`, `@event(guard=..., csrf=...)`, the app-wide
  defaults in `extensions_defaults["events"]`, `_csp_nonce` and
  `_render_inputs`; the guard block of `_prepare_call` in
  `packages/py/citry/citry/ext/events/dispatcher.py`; tests in
  `packages/py/citry/tests/test_events_dispatch.py`

## Who controls the input

Events is Citry's feature for calling Python from the browser: an event
handler is a Python function on a component that the browser calls. A
guard is a function that decides who may call an event handler. The
app author writes the guards, the `_context` function that builds a
call's context, and the `_csrf` function that runs the app's own CSRF
check (a check that a request really comes from the app's own page,
not from another site). The request that the guard should refuse comes from anyone who
can reach the event route.

Citry called these functions without awaiting them. An `async def` one
only created a coroutine, and its code never ran. So an async guard
refused nothing, an async `_csrf` checked nothing (Citry's own header
and origin checks still ran), and an async `_context` handed handlers a
coroutine in place of the context.

What was at risk is the app's data and actions behind the handler: any
visitor could call a handler that an async guard was meant to protect.
No value reaches the browser by a new route.

Of the places in the Mechanism 7 list in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser),
this change touches "Responses Citry serves": the error bodies of the
refused calls.

## How it was checked

- **Releases.** 0.3.0 and 1.2.0 were run from their published wheels,
  over ASGI and WSGI routes, with guards that always refuse.
- **Routes.** The batch route (sync and async dispatch), the per-event
  `POST` and `GET` routes, the form post without JavaScript, the
  `ViewEvents` verb route, and detached handlers.
- **Kinds of function.** `async def` functions, async generators and
  generators, each behind a `staticmethod`, a `classmethod`, a
  `functools.partial`, a bound method, or an object with an async
  `__call__`; and, at call time, functions that return a coroutine,
  another awaitable, a generator or an async generator, including ones
  that only register as `collections.abc` types, as compiled Cython
  objects do.
- **Answers.** Each refused call answers with an error, `handler_error`
  for a guard or `_context` and `csrf_failed` for `_csrf`, and the
  handler does not run.
- **Tests.** The new tests fail on the code before the fix. The events
  test files and the whole `citry` package suite passed, apart from
  failures that came from the reviewers' local environments and fail the
  same way without the fix.
- **CI.** Nothing ran in the private fork, because GitHub Actions does
  not run there. CI ran on the public pull request
  ([#881](https://github.com/citry-dev/citry/pull/881)) before it
  merged.
- **Other frameworks' advisories (Mechanism 8).** The reviewers read the
  maintainers' private survey of security bugs published for other
  frameworks and checked these kinds: CSRF (`csrf`), names that pick
  code (`name-to-code`), a second path that skips a check
  (`sanitizer-bypass`), error pages (`error-page`) and log injection
  (`log-inj`). This advisory added a kind to the survey: an
  authorization check written async but called without awaiting it
  (`async-authz`).

## Ruled out

- **The siblings of these functions.** `_csp_nonce` and
  `_render_inputs` already refused `async def`. They now use the same
  check, which also catches an object with an async `__call__`.
- **Async event handlers.** They stay supported on ASGI servers. A check
  that needs `await` can run at the start of the handler.
- **A decorator that wraps an async function in a plain one.** A wrapper
  that runs the async function to the end, such as
  `asgiref.sync.async_to_sync`, is a valid plain function, so Citry does
  not follow `__wrapped__` to refuse it.
- **`on_event` and `on_event_error` hooks, and async result resolvers.**
  They already failed closed with an error.
- **Author-only by design.** A plain decorator that starts an async
  check and drops its result refuses nothing, and Citry cannot see
  inside it. `docs_site/content/security.md` ("Authorize every event")
  tells authors to run any async function to the end.

## Fixed during the review

- `_context` first refused any awaitable, which refused legitimate data;
  it now refuses only a coroutine.
- A compiled coroutine from `_context`, and a compiled generator or
  async generator from a guard or `_csrf`, went through the first
  checks.
- Citry also closed a coroutine or generator that the app had already
  started; it now closes only one that has not started.
- The refusal messages, the advice about decorators, and rows and line
  references in `docs/design/trust_boundaries.md`.

## Not tested

- Django, Flask and FastAPI end to end, and a real browser. The routes
  were run through Citry's own ASGI and WSGI apps and the dispatcher.
- Real Cython and mypyc objects; imitations stood in for them.
- PyPy and free-threaded Python.

## Follow-ups

None. `docs_site/content/security.md` ("Authorize every event" and "Use
your own token"), the `@event` docstring and `docs/design/events.md` say
that guards, `_context` and `_csrf` must be plain `def` functions.
