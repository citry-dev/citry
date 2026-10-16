# Tetra project board

This app uses Tetra 0.8.5's ordinary `Component`, public Python methods,
encrypted component state and HTTP update protocol. Alpine submits form values
to `act`; Tetra sends and applies its normal response. The shared domain model,
visible board, controls and sibling disclosure match the other apps.

At 14 outputs, rendering creates one stateful Board plus 24 native
BasicComponent instances: ProjectLayout, ProjectInfo, 3 NotePanels, 5
PhaseGroups and 14 ProjectOutputs. Native blocks fill the layout sidebar,
header and content. All five tab panels and five phase groups remain mounted.
The 14/140/1400 output sizes replicate the canonical cohorts to 4/40/400 notes,
8/80/800 comments, 2/20/200 roles, 1/10/100 bookmarks, 1/10/100 attachments
and 2/20/200 dependencies.

The version was selected for packaging feasibility before timing comparisons.
On 2026-09-10, the latest published release was 0.9.2. Its wheel and source
distribution omit `tetra/components/default/link/link.html`, which its built-in
`Link` imports during `django.setup()`. A normal installation fails with
`ComponentError` before application initialization. The 0.9.0 and 0.9.1 wheels
also lack that template. Version 0.8.5 defines these built-ins inline and starts
without repairing the framework. This app represents 0.8.5, not the latest
Tetra release. Exact distribution identities are retained in `provenance.json`.

The Django host runs with `DEBUG=False`, active CSRF protection and one Uvicorn
worker. Tetra requires an authenticated-session interface for encrypted state;
standard session and authentication middleware provide an anonymous user and
cache-backed session keys. Django's default in-process session cache adds no
database, but its storage and processing remain part of Tetra's measured work.
`channels` is pinned because Tetra imports it during app initialization. No
channel layer, WebSocket router, Redis service or reactive component is enabled.

The documented `tetra_scripts include_alpine=True` tag emits the component
library, stock Tetra runtime and bundled Alpine 3.15.4 with morph. Its default
template selects unminified assets even with `DEBUG=False`; this app retains
that behavior. An explicit minified Alpine configuration was rejected during
qualification: the wheel's `alpinejs.cdn.min.js` has a stray final `c` expression
that raises `ReferenceError`. No framework asset is repaired or error suppressed.
All files are served locally. The generated component library is minified by
Tetra's normal `tetrabuild` command. These asset choices must remain visible in
any comparison; this is not a claim of identical frontend optimization.

The initial signal follows `alpine:initialized` and Alpine's next tick. Update
readiness requires `tetra:component-updated`, no outstanding request IDs and
Alpine's next tick. `tetra:after-request` alone is insufficient: in this version
it fires after fetch resolves, before response parsing and DOM morphing. The
observer never replaces the transport or advances the server revision. Concurrent
requests, reactive subscriptions and asynchronous component assets are outside
this app's qualification scope.

From this directory:

```sh
uv sync --frozen --no-build --python 3.12.13
uv run --no-sync python build.py
uv run --no-sync python -m unittest test_app
uv run --no-sync python -m uvicorn app:application --host 127.0.0.1 --port 8000 --workers 1
```

Open `/?count=14&session=manual`. The runner sets hidden operation IDs for real
control clicks. `build.py` downloads esbuild 0.27.2 only during preparation,
checks the platform archive against the pinned SHA512 digest in `esbuild.json`,
and extracts only its executable. The public `TETRA_ESBUILD_PATH` setting prevents
an implicit compiler download. Compiler provenance is written under `generated/`;
the runner records generated files and rejects changes after preparation.
Nothing is compiled or installed by an application request.

Sources: [Tetra components](https://tetra.readthedocs.io/v0.8.5/components/),
[installation and builds](https://tetra.readthedocs.io/v0.8.5/install/),
[script tags](https://tetra.readthedocs.io/v0.8.5/include-js-css/),
[client lifecycle](https://tetra.readthedocs.io/v0.8.5/events/).
The installed wheel is authoritative where current documentation differs.
See the shared scenario README for the common semantics and remaining limits.

## Server HTML render timing

The render span covers Tetra `Component.render` and Django template rendering, counting nested
calls once. Component initialization triggered by template tags and state data embedded during
rendering are included.

A request-scoped `Server-Timing: render` metric reports the sum of these spans. It excludes
action mutation, CSRF checks, network transfer and browser work. Static responses and failed
responses have no render metric. The existing `application` metric remains a broader, separate
measurement. These hooks are benchmark instrumentation against the pinned release, not
framework changes.
