# Jinja + HTMX + Alpine project board

This adapter renders the shared project board with Jinja2 3.1.6 through
Starlette 1.6.0's `Jinja2Templates` and `TemplateResponse`. Uvicorn 0.52.4 serves
one production process. This is a Starlette-hosted HTML template entry;
comparison with Django includes the different hosts' request processing.
The template integration follows
[Starlette's documented Jinja API](https://starlette.dev/templates/).

The full page includes `board.html` through Jinja's native template include.
An action renders that same template as an HTML fragment. HTML autoescaping
stays enabled for text and attribute values. The environment keeps Jinja's
normal compiled-template cache and disables source-file reload checks for
production. It does not cache rendered HTML or action results. The first
page request compiles templates as needed; later requests use their compiled
code. See [Jinja's environment API](https://jinja.palletsprojects.com/en/stable/api/).

The native page include renders one canonical shell, five mounted tab panels,
three note panels, five open phase groups and repeated output structures. At 14
outputs it contains 4 notes, 8 comments, 2 roles, 1 bookmark, 1 attachment and
2 dependencies. The 140/1400 output sizes replicate those nested cohorts by
10x/100x while keeping one shell and five groups.

HTMX 2.0.10 submits forms and replaces the board with its normal `outerHTML`
swap and settle delay. Alpine 3.17.2 owns the independent local disclosure.
Both files, licenses and source hashes are copied from the existing HTMX
adapters into `assets/`. All browser resources are served locally; the CSS
comes from the shared scenario. Browser readiness uses `alpine:initialized`
or `htmx:afterSettle`, followed by Alpine's next tick, with no pending HTMX
request. The observer is identical to the other HTMX adapters.

Starlette's signed-cookie session middleware stays enabled. The initial
request creates a random CSRF token and stores it with the board session in
the signed cookie. Every form submits that token. POSTs require the matching
token and board session, and a matching Origin when the browser supplies it.
Trusted-host middleware rejects unexpected hosts. These checks remain in the
measured request path. The fixed signing secret belongs only to this isolated
synthetic benchmark. See [Starlette's session middleware](https://starlette.dev/middleware/#sessionmiddleware).

`Server-Timing: application` covers ASGI entry through response start, including
routing, session handling, domain actions, Jinja rendering and scheduling.
It excludes body transmission. The synchronous initial route uses Starlette's
normal thread pool; the action route asynchronously reads the form and then
renders synchronously. The headers and rendered board carry the same operation
and revision. These are host-specific diagnostics, not an isolated measurement
of template rendering.

The shared exact-state oracle checks all actions, including invalid input,
insertion, removal and reordering. Untimed qualification also selects the
newly inserted row. The shared limits on preservation inside replaced content,
asynchronous assets, nested lifecycle behavior and concurrent actions apply.
The ready timestamp precedes synchronous semantic capture. Its separately
reported cost can still perturb the event loop, so this adapter alone does not
establish a public performance comparison.

## Run locally

From this directory:

```sh
uv sync --frozen --no-build --python 3.12.13
uv run --no-sync python -m unittest test_app -q
uv run --no-sync uvicorn app:application --host 127.0.0.1 --port 8000
```

Open `/?count=14&session=manual`; counts 140 and 1400 are also supported.
The runner supplies unique operation keys; manual forms use `manual`.
`/health` returns the runner's nonce without rendering or resetting a board.
Page, fragment and asset responses use `Cache-Control: no-store` and identity
encoding. Dependencies are pinned in the independent `uv.lock`; HTTPX is a
test-only dependency. No frontend build or global package installation is needed.

Versions and APIs were checked on 10 September 2026 against the documentation
above and the packages' published PyPI metadata:
[Jinja2](https://pypi.org/pypi/Jinja2/3.1.6/json),
[Starlette](https://pypi.org/pypi/starlette/1.6.0/json), and
[Uvicorn](https://pypi.org/pypi/uvicorn/0.52.4/json).

## Server HTML render timing

The render span covers `jinja2.Template.render`, counting nested calls once. The board snapshot
is prepared before this boundary and is excluded.

A request-scoped `Server-Timing: render` metric reports the sum of these spans. It excludes
action mutation, CSRF checks, network transfer and browser work. Static responses and failed
responses have no render metric. The existing `application` metric remains a broader, separate
measurement. These hooks are benchmark instrumentation against the pinned release, not
framework changes.
