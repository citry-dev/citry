# Django Components, HTMX and Alpine project board

This app uses django-components 0.152.0 and djc-core 1.3.1 with Django 6.1.1,
HTMX 2.0.10 and Alpine 3.17.2. Uvicorn 0.52.4 serves the production Django ASGI
application with `DEBUG=False`. The independent lockfile pins published packages;
it does not import the repository's Citry implementation.

## Component and interaction model

The initial request renders a Page component containing a Board through the
native `{% component %}` tag. Actions render that same Board directly with
`Component.render_to_response()`. Components use the public
`get_template_data()` lifecycle and preserve generated component IDs and normal
HTML processing. Each request reads the shared in-memory board model.

At 14 outputs, native rendering creates 27 component instances: Page, Board,
ProjectLayout, ProjectTabs and ProjectInfo; 3 NotePanels; 5 PhaseGroups; and 14
ProjectOutputs. The layout receives real sidebar, header and content slots. The
fixed shell has five mounted tab panels and five open phase groups. The
14/140/1400 output sizes replicate the canonical nested cohorts to 4/40/400
notes, 8/80/800 comments, 2/20/200 roles, 1/10/100 bookmarks, 1/10/100
attachments and 2/20/200 dependencies.

Django Components supplies rendering and dependency management. HTMX supplies
form submission and `outerHTML` board replacement with its default settle delay;
Alpine owns the independent local disclosure and draft input. Django CSRF
middleware remains active, including token and same-origin checks. Initial and
replacement forms include tokens. Unknown protocol actions fail with HTTP 400;
business validation errors render the next revision normally. This isolated
synthetic-data scenario has no authentication or database.

## Native dependencies and readiness

Page uses `deps_strategy="document"`; Board updates use `"fragment"`. The app
retains the framework's dependency manager, generated fragment loader and native
dependency processing. It does not strip framework attributes or bypass rendering
dependencies. The manager is served from the pinned wheel through Django's static
file finder on the local origin, with identity encoding and `Cache-Control:
no-store`. These components declare no additional component JS or CSS; the shared
stylesheet, HTMX and Alpine are ordinary page assets.

Readiness follows initial Alpine initialization and, after server actions, HTMX
settlement followed by Alpine's next tick with zero pending HTTP requests. The
initial dependency manager is a normal parser-blocking script before the deferred
Alpine script runs. No component-specific asynchronous initialization is declared.
This boundary qualifies this composition; dynamically introduced component
dependencies, asynchronous component callbacks and concurrent actions need
separate qualification. Shared scenario assertions check the complete visible
state and working controls after every update. The ready timestamp precedes the
synchronous semantic capture, whose separately reported cost can still perturb
the event loop. This app alone establishes no publication ranking.

`Server-Timing: application` covers synchronous Django middleware, the view,
shared action and native component rendering. It excludes ASGI scheduling and
body transmission. Health requests do not render the board.

## Assets and local use

HTMX, Alpine and their licenses are vendored under `assets/`. `assets/sources.json`
records upstream URLs, package integrity and file hashes. `provenance.json`
identifies the selected Django Components wheel and the manager served from it.
The manager's MIT license is retained as `assets/django_components.LICENSE`.
All browser assets are served locally; no CDN or build step is required.

Run from this directory:

```sh
uv sync --frozen --no-build --python 3.12.13
uv run --no-sync uvicorn app:application --host 127.0.0.1 --port 8000
uv run --no-sync python -m unittest test_app
```

Open `/?count=14&session=manual`; 140 and 1400 outputs use the same implementation.
The runner supplies unique sessions and operation IDs, and `/health` returns its
process nonce. The fixed secret is for isolated benchmark data; this is not a
deployment template.

Sources checked on 10 September 2026:
[release metadata](https://pypi.org/pypi/django-components/0.152.0/json),
[public rendering API](https://django-components.github.io/django-components/latest/concepts/fundamentals/rendering_components/),
[HTML fragment integration](https://django-components.github.io/django-components/latest/concepts/advanced/html_fragments/),
and the installed release's `component.py`, `dependencies.py` and static manager.

## Server HTML render timing

The render span covers `Component.render` and Django template rendering, counting nested calls
once. Component context callbacks and dependency emission inside these methods are included.

A request-scoped `Server-Timing: render` metric reports the sum of these spans. It excludes
action mutation, CSRF checks, network transfer and browser work. Static responses and failed
responses have no render metric. The existing `application` metric remains a broader, separate
measurement. These hooks are benchmark instrumentation against the pinned release, not
framework changes.
