# FastHTML project board

FastHTML 0.14.13 constructs the page and board fragments with its FastTags API.
Routes return FastTags directly; FastHTML performs the normal response conversion
and HTML serialization. Starlette handles the ASGI application, with one Uvicorn
worker. This is a different server stack from the Django-hosted entries, not an
isolated comparison of serializer speed.

The FastTags tree uses 25 concept-level composition calls at 14 outputs: one
board, tabs and project-info call, 3 note panels, 5 phase groups and 14 output
subtrees, with attachment and dependency helpers nested per output. All five
tab panels and five phase groups are mounted. The 14/140/1400 output sizes
replicate the canonical cohorts to 4/40/400 notes, 8/80/800 comments,
2/20/200 roles, 1/10/100 bookmarks, 1/10/100 attachments and 2/20/200
dependencies while retaining one shell and five groups.

HTMX submits ordinary forms and replaces the board using `outerHTML` with its
default settle delay. Alpine owns the independent local disclosure. Browser
readiness uses `alpine:initialized` or `htmx:afterSettle`, then Alpine's next tick,
with no pending HTMX request. These are the same signals used by the Django HTMX
app. The ready timestamp precedes synchronous semantic capture. Its separately
reported cost can still perturb the event loop. The shared scenario's nested
lifecycle and async-asset limitations also apply here.

FastHTML's default remote headers are disabled through its public `default_hdrs`
option. The document explicitly loads local HTMX 2.0.10 and Alpine 3.17.2, copied
with their licenses and source hashes under `assets/`. The scenario uses ordinary
HTMX attributes and does not need FastHTML's optional Surreal or helper scripts.
All required browser assets are served from the application origin.

The normal FastHTML signed-session middleware stays enabled. Each initial page
creates a random CSRF token in that session, and forms include the token. POSTs
require the matching token, the browser's board session, and a matching Origin
when supplied. Trusted-host middleware rejects unexpected hosts. Session cookie
and CSRF work remain in the measured request path. The submitted CSRF token is
compared with the token stored in FastHTML's signed session cookie. Fixed signing
secrets are only for the isolated synthetic benchmark, not deployment templates.

`Server-Timing: application` measures the outer ASGI call through response start,
including FastHTML routing, session middleware, action and serialization. Unlike
the Django entries' synchronous middleware duration, it also includes ASGI work
and scheduling inside that call. It excludes response-body transmission. Treat
these durations as app-specific diagnostics rather than identical subphases.
The response operation and revision headers use the same model result as the
rendered board. Health checks return the runner's nonce without rendering a board.

From this directory:

```sh
uv sync --frozen --no-build --python 3.12.13
uv run --no-sync python -m unittest test_app -q
uv run --no-sync uvicorn app:application --host 127.0.0.1 --port 8000
```

Open `/?count=14&session=manual`. The runner supplies unique operation IDs for
measurements; manual actions use `manual`. Dependencies are pinned in `uv.lock`,
including Starlette 1.6.0 and Uvicorn 0.52.4. Installation uses published wheels.

API sources checked on 10 September 2026:
[FastHTML core](https://www.fastht.ml/docs/api/core.html),
[FastTags components](https://www.fastht.ml/docs/api/components.html),
[Starlette middleware](https://starlette.dev/middleware/), and
[HTMX documentation](https://htmx.org/docs/).

## Server HTML render timing

The render span sums FastTags board/document construction and FastHTML `_xt_cts` serialization.
Nested construction is counted once. Snapshot preparation is excluded; conversion of the
completed FastTags tree to HTML is included.

A request-scoped `Server-Timing: render` metric reports the sum of these spans. It excludes
action mutation, CSRF checks, network transfer and browser work. Static responses and failed
responses have no render metric. The existing `application` metric remains a broader, separate
measurement. These hooks are benchmark instrumentation against the pinned release, not
framework changes.
