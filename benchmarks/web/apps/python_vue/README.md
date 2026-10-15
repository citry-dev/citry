# Python JSON API + Vue project board

This adapter uses Vue 3.5.42 to render a browser application against the same
Starlette 1.6.0 JSON backend as its React counterpart. The server first returns
an HTML shell and signed session cookie. The client loads its local production
bundle, fetches `/initial`, and renders the returned board. Initial readiness
includes that JSON fetch, browser rendering and lifecycle completion. There is
no server-rendered board or hydration of pre-rendered HTML.

`scenario/json_api.py` owns both adapters' shell, JSON projection, state
operations, CSRF checks, signed sessions, asset delivery and timing middleware.
Its domain data and CSS come from the shared project-board scenario. The initial
JSON response supplies a CSRF token stored in the signed session cookie. Action
requests must carry that token,
match the browser session and pass the same-origin check when Origin is present.
The secret is fixed for isolated synthetic benchmark data, not deployment use.

Forms send their current values as JSON only when submitted. Editing a field
sends no request. Each successful mutation returns one complete canonical page snapshot,
including the new operation and revision. Business validation errors also return
a completed revision and preserve the attempted input value. The response headers
and body carry the submitted operation key and server-assigned revision.

Vue uses `createApp`, reactive state, provide/inject and native render functions
(`h`). Native components compose the project shell, five mounted tab bodies,
phase and output expansion panels, notes, comments, roles, bookmarks, output
forms, dependencies and attachments. The Outputs tab is initially active; tab,
panel, disclosure and output display-control interactions stay local.
After assigning each response to the reactive board, the adapter awaits
`nextTick` before signaling that the new elements and handlers are ready.
The observer counts outstanding application fetches and emits readiness only
after JSON parsing and framework commit. Network failures log an error and emit
no completion mark. Local disclosure state and the sibling draft input remain
inside the browser framework and survive updates. Newly inserted controls are
qualified with a real selection action. Concurrent actions, asynchronous custom
callbacks and lifecycle behavior beyond the canonical filter, insert and remove
updates remain outside this scenario's qualification. Dirty-input and focus
preservation inside server-updated content are also outside it.

## Build and run

Python dependencies have an independent frozen `uv.lock`. Browser dependencies
have a separate `bun.lock` with exact Vue pins. `build.py` verifies the
archive and executable hashes for Bun 1.3.14, installs the frozen dependencies
without package scripts, and builds a minified browser bundle with production
flags. The native compiler pin currently supports macOS ARM64. Its binary,
package installation and output live under excluded `generated/`; preparation
records these bytes separately. No global installation or runtime build is used.

```sh
uv sync --frozen --no-build --python 3.12.13
uv run --no-sync python build.py
uv run --no-sync python -m unittest test_app -q
uv run --no-sync uvicorn app:application --host 127.0.0.1 --port 8000
```

Open `/?count=14&session=manual`; 140 outputs exercise the linear 10x cohort,
and the optional 1400-output case exercises the 100x cohort. All browser assets are local; page, JSON and
asset responses use `Cache-Control: no-store`. The ASGI `Server-Timing` duration
runs through response start, including middleware, domain work and JSON
serialization; it excludes body transmission. This is a local diagnostic
comparison. Instrumentation can affect timings; semantic snapshot cost is
reported separately, while residual event-loop effects are not calibrated.
The adapter makes no publication ranking claim.

Successful `/initial` and `/action` responses also emit `Server-Timing: prepare`.
That narrower span starts with the post-mutation domain snapshot and includes
the browser projection, response envelope and Starlette JSON serialization. It
excludes request parsing, validation, the domain mutation and body transmission.

Sources checked on 10 September 2026: [Vue lifecycle and nextTick](https://vuejs.org/api/general.html#nexttick)
and [render functions](https://vuejs.org/guide/extras/render-function.html).
