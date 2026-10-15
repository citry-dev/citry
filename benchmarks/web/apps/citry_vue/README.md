# Citry + Vue

This adapter serves the canonical project board with Citry's public default Vue
implementation. The app uses ordinary components and default engine settings: no
research flags, server wrappers or browser startup flags. Actions travel through
Citry's normal signed, CSRF-protected Events POST route.

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
output as HTML and every action response as JSON (`server_prepare_kinds`). `test_app.py` renders each board size and
fails if one of them stops hydrating.

## What the server timing covers

The adapter reports every measured server span as `Server-Timing: prepare`. On
a page load the span covers Citry rendering, the Vue payload and definitions,
the server HTML when Citry writes it, and serialization of the document. On an
action it also covers the final Events envelope validation and serialization.
Asset serving, shared model updates, transport, Vue work and browser callbacks
stay outside the span. Because the adapter reports no separate `render` span,
the raw data marks the 1,400-output page's `server_render_status` as
`missing`; `summary.json` keeps the `prepare` value as `server_prepare_median_ms`.

An action that introduces a new compiled definition can make a later script
request after the main Events exchange. The runner still reports the correct
total time and summed payload bytes, but it classifies that action's latency
phases as unclassified rather than presenting the script load as browser time.

## Wheels

A profile that selects this adapter supplies repo-relative paths under
`.benchmarks/wheels/` for locally built `citry` and `citry-core` wheels. Build
those wheels before `citry-bench prepare`; the runner hashes their bytes into
the prepared-build identity and installs them only into this adapter's
environment.
