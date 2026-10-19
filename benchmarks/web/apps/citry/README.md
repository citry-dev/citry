# Citry

This app serves the canonical project board with Citry 0.6.0 and its default
Vue renderer. It uses ordinary components, Citry's default engine settings
and no browser startup flags. Actions travel through Citry's normal signed,
CSRF-protected Events POST route. For timing only, a small middleware in
`app.py` reports Citry's render span as `Server-Timing: prepare` and marks
compiled Vue definitions as immutable; each page load uses a fresh browser
context, so that cache header does not shorten measured loads.

The page mounts two Vue islands: the `Board` component, which owns every server
action, and a separate plain Vue island for the local disclosure and preserved
draft. The 14 to 1,400 repeated output rows are `ProjectOutput` components with
`simple="vue"`, so each row gets its own Vue state without a Python component
instance. Readiness waits for both Vue islands to finish rendering, the Board
callbacks, and Events setup.

## Server HTML and browser mounting

With Citry's default settings the server writes every board's HTML, and Vue
hydrates it (adopts those nodes instead of building them) at every size, from
14 to 1,400 outputs.

`adapter.toml` states this to the runner as `rendering = "hybrid"` and
`update_payload = "json"`. `summary.json` therefore lists every initial page's
output as HTML and every action response as JSON (`server_prepare_kinds`).
`test_app.py` renders each board size and fails if one of them stops
hydrating.

## What the server timing covers

The app reports every measured server span as `Server-Timing: prepare`. On
a page load the span covers Citry rendering, the Vue payload and definitions,
the server HTML when Citry writes it, and serialization of the document. On an
action it also covers the final Events envelope validation and serialization.
Asset serving, shared model updates, transport, Vue work and browser callbacks
stay outside the span. Because the app reports no separate `render` span,
the raw data marks `server_render_status` as `missing` for every page; `summary.json` keeps the `prepare` value as `server_prepare_median_ms`.

An action that introduces a new compiled definition can make a later script
request after the main Events exchange. The runner still reports the correct
total time and summed payload bytes, but it classifies that action's latency
phases as unclassified rather than presenting the script load as browser time.

## Which Citry it installs

`pyproject.toml` pins `citry==0.6.0` and `citry-core==1.8.0`, the release that
ships the Vue renderer this app uses.

`uv.lock` resolves both packages, like every other dependency, from PyPI.
To move the app to a newer release, change the pins and relock from this
folder:

```bash
uv lock --python 3.12.13 \
  --upgrade-package citry --upgrade-package citry-core
```

A profile can replace both packages with wheels you build, to measure a
change before it is released. The runner hashes those wheels into the
prepared-build identity and installs them only into this app's environment.

## Run the tests

From this folder:

```bash
uv sync --frozen --python 3.12.13
uv run --no-sync python -m unittest test_app -q
uv run --no-sync uvicorn app:application --host 127.0.0.1 --port 8000
```

Open `/?count=14&session=manual` to see the board; 140 and 1400 outputs use
the same app. `test_hydration_e2e.py` is a separate browser test that checks
hydrated pages behave like pages Vue builds itself; it needs pytest and
Playwright, which this app's environment does not install.
