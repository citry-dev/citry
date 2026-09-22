# Playground runtime

This directory contains the browser runtime used by the top-level playground
and by `<c-live-code>` examples. The browser starts Python in a Web Worker,
renders the module's final value into an isolated iframe, and forwards Citry
Events calls back to the same Python process.

Most files here are served directly from `/static/playground/`. Some are
maintained here, while the large JavaScript bundles are generated from smaller
source modules elsewhere in the repository.

## How a run reaches the preview

1. `playground.js` or `live_code_runtime.js` reads source and asks
   `worker_session.js` to run it.
2. `worker.js` loads `runtime.json`, Pyodide, the pinned wheels, and
   `executor.py`. The pinned Citry wheel supplies its matching Events client.
3. `executor.py` runs one Python module in a fresh namespace. It normalizes
   the module's final expression into rendered HTML and retains the Citry
   instance so event handlers remain callable.
4. `preview_bridge.js` loads a fresh `preview.html` iframe and sends it the
   HTML through a private `MessagePort`.
5. `preview.html` installs the HTML, reactivates supported scripts, then
   publishes Citry manifests after Citry's classic scripts are ready. It waits
   for authored non-async external scripts, while async scripts and modules may
   finish later.
6. A Citry event travels from `preview.html` through `preview_bridge.js` and
   `worker_session.js` to `worker.js`. The Worker calls `executor.py`, and the
   response returns along the same path.
7. Before applying a Render action, `preview.html` asks the same Worker for any
   new Citry-owned JavaScript and CSS. `executor.py` resolves only its exact
   built-in asset routes, and the iframe installs the results as reusable Blob
   URLs before Citry changes the DOM.

Each render uses a candidate iframe. The previous result stays visible until
the candidate has loaded, connected, received the new HTML, and acknowledged
the render. Load, connection, protocol, and timeout failures discard the
candidate without replacing the last good result. Visitor-script or manifest
activation errors are different: the candidate reports a client diagnostic
and may commit partially activated HTML so the visitor can inspect the result
beside the error.

## File ownership

| File | Purpose | Where to edit it |
|---|---|---|
| `runtime.json` | Pins Pyodide, Python, Citry, Citry Core, and every browser wheel. | This file. |
| `worker.js` | Owns Pyodide, installs the runtime, runs Python, and dispatches Python event handlers. | This file. |
| `executor.py` | Executes one module, normalizes its final value, reports Python diagnostics, adapts Events requests, and projects an exact-version component catalog. | This file. |
| `analysis_adapter.py` | Converts parser diagnostics, structural and registered-component results, and catalog-backed findings into validated browser records. | This file. |
| `runtime_label.js` | Formats the visible published/workspace runtime provenance label. | [`../../_internal/frontend/src/runtime_label.js`](../../_internal/frontend/src/runtime_label.js). |
| `portable_ide.py` | Generated parser and component-name rules shared with the desktop LSP. | [`../../../packages/py/citry/citry/_portable_ide.py`](../../../packages/py/citry/citry/_portable_ide.py). |
| `preview.html` | Provides the sandboxed result document, ordered script activation, diagnostics, and the Events transport. | This file. |
| `playground.css` | Styles the full-page editor and result workspace. | This file. |
| `live_code.css` | Styles inline `<c-live-code>` blocks and their activated workspace. | This file. |
| `playground.js` | Generated bundle for the full-page playground. | [`../../_internal/frontend/src/playground.js`](../../_internal/frontend/src/playground.js) and its imports. |
| `analysis_worker.js` | Generated Worker for the full-page editor's Citry analysis. | [`../../_internal/frontend/src/analysis_worker.js`](../../_internal/frontend/src/analysis_worker.js). |
| `runtime_packages.js` | Resolves exact package coordinates into URLs when a Worker starts. | [`../../_internal/frontend/src/runtime_packages.js`](../../_internal/frontend/src/runtime_packages.js). |
| `live_code.js` | Generated lightweight activator loaded on pages that contain live examples. | [`../../_internal/frontend/src/live_code.js`](../../_internal/frontend/src/live_code.js). |
| `live_code_runtime.js` | Generated deferred bundle containing the inline editor and runtime. | [`../../_internal/frontend/src/live_code_runtime.js`](../../_internal/frontend/src/live_code_runtime.js) and its imports. |
| `landing_composer.js` | Generated landing-only component collection and sample-board controller. | [`../../_internal/frontend/src/landing_composer.js`](../../_internal/frontend/src/landing_composer.js). |

The shared authored JavaScript modules live in
[`../../_internal/frontend/src/`](../../_internal/frontend/src/):

- `citry_editor.js` configures CodeMirror and nested Citry syntax.
- `browser_ide.js` maps versioned CodeMirror requests and results.
- `citry_regions.js` proves the direct asset ranges shared by both paths.
- `preview_bridge.js` owns the parent side of the iframe protocol.
- `worker_session.js` owns Worker lifetime, timeouts, and run, event, and asset
  request matching.

Do not edit a generated JavaScript file in this directory. Its next build will
replace the change.

## Work on the playground locally

Install the repository's JavaScript dependencies once:

```bash
pnpm install
```

Edit direct files in this directory or authored files under
`docs_site/_internal/frontend/src/`, then rebuild the generated files:

```bash
pnpm --dir docs_site/_internal/frontend build
```

Start the live docs server:

```bash
uv run --no-sync python -m docs_site serve
```

Open `/playground/` for the full workspace. Open any docs page containing
`<c-live-code>` or a component page containing `<c-ui-demo>` to exercise the
inline consumer. Python source changes restart the server. Browser bundle
changes require another frontend build and page refresh.

The live authoring server builds temporary wheels from the workspace `citry`
and `citry-ui` sources and adds one prebuilt PyEmscripten `citry-core` wheel to
its generated copy of `runtime.json`. Build that Core wheel from this checkout
with the repository's pinned Pyodide toolchain, then point
`CITRY_PLAYGROUND_CORE_WHEEL` at the resulting file:

```bash
export CITRY_XBUILDENV=/tmp/citry-pyodide-xbuildenv
uvx --python 3.14.2 --from pyodide-cli==0.5.0 --with pyodide-build==0.37.0 \
  pyodide xbuildenv install 314.0.3 --path "$CITRY_XBUILDENV"
uvx --python 3.14.2 --from pyodide-cli==0.5.0 --with pyodide-build==0.37.0 \
  pyodide xbuildenv install-emscripten --path "$CITRY_XBUILDENV"
uv run --no-sync python scripts/build_citry_core_pyodide_wheel.py \
  --source packages/py/citry_core \
  --out-dir /tmp/citry-playground-core \
  --xbuildenv-path "$CITRY_XBUILDENV" \
  --cargo-target-dir /tmp/citry-playground-cargo \
  --cargo-home "$HOME/.cargo" \
  --source-date-epoch "$(git show -s --format=%ct HEAD)"
core_wheels=(/tmp/citry-playground-core/citry_core-*.whl)
if [[ ${#core_wheels[@]} -ne 1 || ! -f ${core_wheels[0]} ]]; then
  echo "Expected exactly one workspace Core wheel." >&2
  exit 1
fi
export CITRY_PLAYGROUND_CORE_WHEEL="${core_wheels[0]}"
uv run --no-sync python -m docs_site serve
```

The build script and the matching toolchain versions in
[`repo--docs-check.yml`](https://github.com/citry-dev/citry/blob/main/.github/workflows/repo--docs-check.yml)
are the provenance boundary. A filename, version, and ABI match only prove
compatibility; they cannot prove that an arbitrary wheel came from this
checkout. Do not use a downloaded or published wheel as the workspace Core
artifact. The Core build is deliberately outside the server factory: reloads
can recreate the app and the two pure-Python wheels without recompiling Rust.

The generated manifest labels this complete three-package tuple as
`source: "workspace"`. If the core artifact is missing or does not match the
workspace package versions, the server prints the reason and serves the
committed `source: "published"` runtime. A local-runtime E2E fixture treats
that fallback as a setup failure, so a published browser run cannot be
mistaken for workspace coverage. Static builds, CI's published-runtime tests,
and deployed docs use only the exact published versions in the committed
`runtime.json`.

## Update the pinned Python runtime

Treat `runtime.json` as one compatible tuple. When any runtime package changes:

1. Pin the full Pyodide and Python versions.
2. Pin PyPI packages by version, filename, and lowercase SHA-256. Pin CDN
   packages by their direct URL; published direct URLs must use the pinned
   Pyodide CDN `/pyodide/v<version>/full/` tree, while workspace manifests may
   use their generated `./local/` wheel paths.
3. Confirm compiled wheels match the Pyodide Python and PyEmscripten ABI.
4. Keep `citry.version`, `citry.core_version`, and `citry.ui_version` equal to
   their package entries.
5. Run the real browser tests. Import success alone does not prove that
   rendering, scripts, Events, and interaction work together.

The Worker verifies installed Python, Citry, Citry Core, and Citry UI versions
before it accepts a run. For a PyPI package, it resolves the registry-assigned
storage URL at startup and rejects any artifact whose filename or SHA-256 does
not match `runtime.json`. This means the release candidate can contain the
complete runtime entry before publication. A local runtime updates all three
`citry.version`, `citry.core_version`, and `citry.ui_version` fields while
replacing the published Citry Core, Citry, and Citry UI entries with the
compatible workspace builds.

## Keep the protocols synchronized

The runtime uses three small internal protocols:

- `worker_session.js` and `worker.js` pair Worker generations with run IDs.
- `browser_ide.js` and `analysis_worker.js` pair source versions with parser
  diagnostics, completion, and hover requests.
- `preview_bridge.js` and `preview.html` pair protocol version, session, run ID,
  and nonce before accepting a message.

Events and Render asset requests cross all four JavaScript modules and
`executor.py`. Asset calls have separate iframe-local and Worker-local IDs,
while both layers bind them to the current run. `preview.html` keeps one Blob
URL per logical Citry asset and remembers assets already emitted by the initial
document so later fragments do not execute them twice while they remain
usable. If Citry collects class CSS after its last instance leaves, the next
instance reuses the browser asset path to restore that sheet. The preview
prepares every Render action in an event response before applying any action.

When changing a message shape, timeout, byte limit, or lifecycle rule, update
both sender and receiver and extend the corresponding browser test. Stale
messages must remain harmless after Stop, Reset, a newer run, iframe
replacement, or Worker restart. Asset preparation failure must leave the last
good candidate or displayed DOM unchanged.

The result iframe intentionally uses only `allow-forms` and `allow-scripts`.
Keep it on an opaque origin, communicate through the transferred
`MessagePort`, and validate identity and size before acting on a message.

## Checks before committing

Run the generated-file check and focused unit tests:

```bash
pnpm --dir docs_site/_internal/frontend check
uv run --no-sync pytest \
  docs_site/tests/test_playground_executor.py \
  docs_site/tests/test_playground_analysis.py \
  docs_site/tests/test_local_playground_runtime.py \
  docs_site/tests/test_live_code.py \
  docs_site/tests/test_serve.py
```

Exercise the parent/iframe protocol and the complete playground in Chromium:

```bash
uv run --no-sync pytest \
  docs_site/tests/e2e/test_live_code_e2e.py \
  docs_site/tests/e2e/test_preview_bridge_e2e.py \
  docs_site/tests/e2e/test_playground_e2e.py
```

Finish with the repository gate:

```bash
python scripts/check.py
```

The browser tests should cover a successful render, Python and client errors,
Stop and Reset, stale-result handling, form submission, Citry Events, a Render
action with JavaScript, CSS, nested State and Events, asset deduplication, and
at least one client-active Citry UI component.
