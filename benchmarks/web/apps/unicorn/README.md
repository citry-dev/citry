# Django Unicorn project board

This app renders the shared project board through django-unicorn 0.67.0,
Django 6.1.1 and Uvicorn 0.52.4 on Python 3.12.13. Unicorn renders a normal
Django component template and uses its native JSON action protocol, state
checksum, request queue and bundled morphdom implementation for updates.
All runtime assets are served locally from the pinned wheel or the licensed
Alpine 3.17.2 files in `assets/`.

`BoardView` keeps the editable query, title input, operation and board session
in Unicorn's serialized state. Its template context derives rows and revision
from the same in-memory model as the other apps. Derived rows are not
additional editable component state. Unicorn's normal component caches remain
enabled; no application response or rendered-board cache is added.

One stateful Unicorn Board renders three Django template partials for project
info, note panels and grouped outputs. At 14 outputs, the mounted DOM has five
tab panels, five open phase groups, 14 output forms, 4 notes, 8 comments, 2
roles, 1 bookmark, 1 attachment and 2 dependencies. The 140/1400 output sizes
replicate those nested cohorts by 10x/100x while retaining one shell and five
groups; the duplicated flat snapshot rows are not serialized into component
state.

Forms use `unicorn:submit.prevent` and `unicorn:model.defer`. Typing updates
Unicorn's local deferred state without a separate server request; submitting
sends those changes and the action in one native request. The runner writes
its operation ID into a hidden input. A capturing submit listener calls the
public `Unicorn.trigger()` API to synchronize that deferred model before
Unicorn handles the form. Action timing still begins at the trusted UI click.
The independent Alpine disclosure and draft input are outside the component.

Django's CSRF middleware and signed-cookie session middleware stay enabled.
The component checks its board session against the signed browser session
before hydration, mutation and rendering. This adds session middleware to the
shared Django host. The fixed secret is only for isolated synthetic benchmark
data. Tests exercise missing CSRF, wrong origin, cross-session component reuse
and tampered state. Unicorn reports a checksum failure as HTTP 200 with a JSON
`error`; the test verifies that response and absence of a model mutation.

## Readiness and measurement limits

Initial readiness follows Unicorn's completed synchronous initialization and
Alpine's `alpine:initialized` event. On updates, Unicorn's `updated` callback
runs after morphing but before its synchronous handler refresh. The observer
waits for Alpine's next tick, then checks Unicorn's action queue, current
request queue and debounce timer. Only an idle component emits the marker.
The complete action sequence and negative lifecycle checks must pass before
interpreting these markers as readiness.

Queue inspection uses fields from the pinned Unicorn browser implementation.
Its duration is recorded as `observer_ms` inside the measured endpoint and
is not subtracted. It is not calibrated across frameworks. The checks cover
this component's synchronous handlers and the sibling Alpine UI; asynchronous
application callbacks, nested components, polling and concurrent requests are
outside this app's qualification.

The shared Django middleware records `Server-Timing: application` through
synchronous middleware, component processing and rendering. It excludes ASGI
scheduling, socket transport and response-body transmission. All page and
asset responses use `Cache-Control: no-store`. This entry targets the local
HTTP/1.1 identity-encoding diagnostic profile.

## Run locally

```sh
uv sync --frozen --no-build --python 3.12.13
uv run --no-sync python -m unittest test_app -q
uv run --no-sync uvicorn app:application --host 127.0.0.1 --port 8000
```

Open `/?count=14&session=manual`. The runner supplies unique operation IDs;
manual form submissions use the current hidden operation value.

API sources checked on 10 September 2026: [release dependency metadata](https://pypi.org/pypi/django-unicorn/0.67.0/json),
[component installation](https://www.django-unicorn.com/docs/installation/)
and [JavaScript integration](https://www.django-unicorn.com/docs/javascript/).
The installed `static/unicorn/js/messageSender.js` and `component.js` define
the callback ordering and queue fields used by the readiness observer.

## Server HTML render timing

The render span covers `UnicornView.render` and Django template rendering, counting nested
calls once. Component context callbacks and HTML generation are included; outer action
hydration and JSON response encoding are excluded.

A request-scoped `Server-Timing: render` metric reports the sum of these spans. It excludes
action mutation, CSRF checks, network transfer and browser work. Static responses and failed
responses have no render metric. The existing `application` metric remains a broader, separate
measurement. These hooks are benchmark instrumentation against the pinned release, not
framework changes.
