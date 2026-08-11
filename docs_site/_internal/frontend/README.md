# Docs playground frontend

This private pnpm package contains the authored JavaScript for Citry's
full-page playground, inline `<c-live-code>` examples, the opt-in editor in
`<c-ui-demo>` component previews, and the landing-page component showcase. It
bundles the browser controllers into static files served by the docs site.

The browser runtime files that are maintained directly under
`docs_site/static/playground/` have their own
[`README.md`](../../static/playground/README.md). Read that guide for the complete
Python, iframe, and Citry Events flow. This guide covers the frontend source
package and its build outputs.

## How the modules fit together

```text
playground.js
├── citry_editor.js
├── preview_bridge.js
└── worker_session.js

live_code.js
└── loads live_code_runtime.js after Try live
    ├── citry_editor.js
    ├── preview_bridge.js
    └── worker_session.js

landing_composer.js
```

The full-page playground loads its complete bundle immediately. A narrative
docs page loads the small `live_code.js` activator only when it contains an
interactive live example or a locally editable UI preview. Ordinary pages,
publication-static examples, and historical pages omit it. The landing page
loads only its small component showcase controller.

Both consumers share the editor and protocol coordinators. A change to one of
those shared modules must be exercised in both the full-page and inline browser
tests.

## Source files

| File | Responsibility |
|---|---|
| [`src/playground.js`](src/playground.js) | Coordinates the full-page toolbar, editor, run state, responsive panels, divider, diagnostics, help dialog, and saved settings. |
| [`src/live_code.js`](src/live_code.js) | Finds live examples, keeps one active, saves per-example drafts, and loads the larger runtime on demand. |
| [`src/live_code_runtime.js`](src/live_code_runtime.js) | Coordinates one activated inline editor, its Python session, preview, tabs, diagnostics, Reset, and disposal. |
| [`src/landing_composer.js`](src/landing_composer.js) | Places pre-rendered Citry UI recipes into the landing page canvas through a lightweight drag-and-drop interaction. |
| [`src/citry_editor.js`](src/citry_editor.js) | Configures CodeMirror for Python with nested HTML, JavaScript, CSS, and Citry-specific highlighting. |
| [`src/worker_session.js`](src/worker_session.js) | Owns Worker generations, Python run IDs, timeouts, size limits, Stop, and pending Events and asset calls. |
| [`src/preview_bridge.js`](src/preview_bridge.js) | Creates candidate result iframes, authenticates their `MessagePort`, commits acknowledged renders, and forwards diagnostics, Events, and Citry asset requests. |
| [`scripts/build.mjs`](scripts/build.mjs) | Builds the four docs bundles and checks their committed output. |
| [`package.json`](package.json) | Owns the package commands and exact CodeMirror, Lezer, and esbuild versions. |

Outside this package,
[`doc_page.py`](../components/doc_page.py) conditionally includes the
playground or live-code styles and entry scripts in rendered pages.

Each JavaScript file uses short comments at lifecycle boundaries and for guards
whose intent is not obvious from the condition. Keep comments focused on why a
state check, ordering rule, or fallback exists. Generated bundles are minified,
so maintain detailed comments in `src/` rather than editing their output.

## Generated outputs

The build writes these files under `docs_site/static/playground/`:

| Output | Source | Build form |
|---|---|---|
| [`playground.js`](../../static/playground/playground.js) | `src/playground.js` and all three shared modules | Bundled and minified |
| [`live_code.js`](../../static/playground/live_code.js) | `src/live_code.js` | Minified, not bundled |
| [`live_code_runtime.js`](../../static/playground/live_code_runtime.js) | `src/live_code_runtime.js` and all three shared modules | Bundled and minified |
| [`landing_composer.js`](../../static/playground/landing_composer.js) | `src/landing_composer.js` | Bundled and minified |

`live_code.js` remains unbundled because its dynamic import must continue to
load `live_code_runtime.js` only after activation. The three bundled entry
points keep their imports together so the static docs server does not need to
resolve package dependencies in the browser.

Every generated docs bundle starts with the authored source path and a warning
not to edit it. Keep these outputs beside `worker.js` and `preview.html`
because the generated modules resolve both runtime files relative to their own
URL.

## Set up the workspace

Install JavaScript dependencies from the repository root:

```bash
pnpm install
```

This package is a member of the root pnpm workspace. Add runtime or development
dependencies to this package's `package.json`, pin them exactly, and refresh
`pnpm-lock.yaml` with the root install. Do not duplicate these dependencies in
the root package merely to make this build work.

## Edit and preview changes

Edit files under `src/`, then regenerate the static outputs:

```bash
pnpm --dir docs_site/_internal/frontend build
```

Start the docs authoring server from the repository root:

```bash
uv run --no-sync python -m docs_site serve
```

Open `/playground/` to exercise `playground.js`. Open a docs page containing
`<c-live-code>` to exercise lazy activation and `live_code_runtime.js`. Open `/`
to exercise `landing_composer.js`.
Rebuild and refresh after each frontend source change. The docs server serves
the generated static files and does not compile this package on request.

## Maintain the DOM contracts

`playground.js` queries IDs emitted by
[`playground_workspace.py`](../components/playground_workspace.py).
The live-code modules query data attributes emitted by
[`live_code.py`](../components/live_code.py).
The landing showcase queries data attributes emitted by
[`landing_composer.py`](../components/landing_composer.py). The server validates
and renders every catalog recipe through the real Citry UI component classes;
the page carries that trusted HTML as escaped application data so Markdown
cannot reinterpret component internals. The browser reconstructs detached
templates, restores their shared CSS, clones recipes into the chosen drop area,
and keeps collapsed sequence gaps around each insertion for the next drag. Only
the gap near the held pointer expands; the bounded sample board scrolls faster
as that pointer approaches its top or bottom edge. Native wheel scrolling chains
back to the page when the board reaches either boundary.
`doc_page.py` uses the render context to include the matching CSS and entry
script only when the page needs them. When changing an ID, data attribute,
panel relationship, control, or asset condition:

1. Update the Python component and JavaScript consumer together.
2. Preserve keyboard behavior, focus movement, labels, and live-region output.
3. Update the applicable browser test.
4. Rebuild the generated files.

A missing required element currently fails during module initialization. Test
rendered markup and JavaScript together rather than treating either side as an
independent interface.

## Coordinate runtime changes

`worker_session.js` pairs with
[`worker.js`](../../static/playground/worker.js). `preview_bridge.js` pairs with
the inline script in
[View `preview.html`](../../static/playground/preview.html). Changes to either
frontend coordinator may alter its paired runtime protocol. Follow
[the runtime protocol maintenance guide](../../static/playground/README.md#keep-the-protocols-synchronized)
and update the direct runtime counterpart in the same change. Render actions
add a round trip from the iframe through both coordinators to the active Python
Worker. Preserve the independent iframe and Worker asset IDs, current-run
checks, cancellation behavior, and response-size limits when changing it.

## Run the checks

Confirm the committed bundles match their sources:

```bash
pnpm --dir docs_site/_internal/frontend check
```

If `check` reports a stale or missing bundle, run `build` and inspect the
generated diff. Then follow
[the runtime verification matrix](../../static/playground/README.md#checks-before-committing)
for Python, browser, and repository-wide checks.
