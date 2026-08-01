# Playground runtime

This directory contains the browser runtime used by the top-level playground
and by `<c-live-code>` examples. The browser starts Python in a Web Worker,
renders the module's final value into an isolated iframe, and forwards Citry
Events calls back to the same Python process.

Most files here are served directly from `/static/playground/`. Some are
maintained here, while the large JavaScript bundles are generated from smaller
source modules elsewhere in the repository.

## How a run reaches the preview

1. `playground.js` or `live_code_runtime.js` reads the editor and asks
   `worker_session.js` to run it.
2. `worker.js` loads `runtime.json`, Pyodide, the pinned wheels,
   `executor.py`, and `citry-events.js`.
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
| `executor.py` | Executes one module, normalizes its final value, reports Python diagnostics, and adapts Events requests. | This file. |
| `preview.html` | Provides the sandboxed result document, ordered script activation, diagnostics, and the Events transport. | This file. |
| `playground.css` | Styles the full-page editor and result workspace. | This file. |
| `live_code.css` | Styles inline `<c-live-code>` blocks and their activated workspace. | This file. |
| `playground.js` | Generated bundle for the full-page playground. | [`../../frontend/src/playground.js`](../../frontend/src/playground.js) and its imports. |
| `live_code.js` | Generated lightweight activator loaded on pages that contain live examples. | [`../../frontend/src/live_code.js`](../../frontend/src/live_code.js). |
| `live_code_runtime.js` | Generated deferred bundle containing the inline editor and runtime. | [`../../frontend/src/live_code_runtime.js`](../../frontend/src/live_code_runtime.js) and its imports. |
| `citry-events.js` | Generated Citry Events client, including pinned Alpine and morph builds. | [`../../../packages/js/citry-client/src/citry-events.ts`](../../../packages/js/citry-client/src/citry-events.ts). |

The shared authored JavaScript modules live in
[`../../frontend/src/`](../../frontend/src/):

- `citry_editor.js` configures CodeMirror and nested Citry syntax.
- `preview_bridge.js` owns the parent side of the iframe protocol.
- `worker_session.js` owns Worker lifetime, timeouts, and request matching.

Do not edit a generated JavaScript file in this directory. Its next build will
replace the change.

## Work on the playground locally

Install the repository's JavaScript dependencies once:

```bash
pnpm install
```

Edit direct files in this directory or authored files under
`docs_site/frontend/src/`, then rebuild the generated files:

```bash
pnpm --dir docs_site/frontend build
```

Start the live docs server:

```bash
uv run --no-sync python -m docs_site serve
```

Open `/playground/` for the full workspace. Open any docs page containing
`<c-live-code>` to exercise the inline consumer. Python source changes restart
the server. Browser bundle changes require another frontend build and page
refresh.

The live server builds temporary wheels from the workspace `citry` and
`citry-ui` sources. It serves a local `runtime.json`, local wheels, and the
matching Events client without changing this committed directory. Static
builds, CI, and deployed docs use the exact versions in the committed
`runtime.json`.

## Regenerate the Events client

The Events client has two generated copies. Build its TypeScript source first,
then rebuild the docs frontend so this directory receives the same bytes:

```bash
pnpm --dir packages/js/citry-client build
pnpm --dir docs_site/frontend build
```

The docs frontend check compares `citry-events.js` byte for byte with the
Python package copy. This prevents the playground and installed Citry package
from using different client runtimes.

## Update the pinned Python runtime

Treat `runtime.json` as one compatible tuple. When any runtime package changes:

1. Pin the full Pyodide and Python versions.
2. Pin each package version and immutable wheel URL.
3. Confirm compiled wheels match the Pyodide Python and PyEmscripten ABI.
4. Keep `citry.version` and `citry.core_version` equal to their package entries.
5. Run the real browser tests. Import success alone does not prove that
   rendering, scripts, Events, and interaction work together.

The Worker verifies installed Python, Citry, and Citry Core versions before it
accepts a run. A local runtime may also add `citry.ui_version`, which makes the
Worker verify Citry UI.

## Keep the protocols synchronized

The runtime uses two small internal protocols:

- `worker_session.js` and `worker.js` pair Worker generations with run IDs.
- `preview_bridge.js` and `preview.html` pair protocol version, session, run ID,
  and nonce before accepting a message.

Events cross all four JavaScript modules and `executor.py`. When changing a
message shape, timeout, byte limit, or lifecycle rule, update both sender and
receiver and extend the corresponding browser test. Stale messages must remain
harmless after Stop, Reset, a newer run, iframe replacement, or Worker restart.

The result iframe intentionally uses only `allow-forms` and `allow-scripts`.
Keep it on an opaque origin, communicate through the transferred
`MessagePort`, and validate identity and size before acting on a message.

## Checks before committing

Run the generated-file check and focused unit tests:

```bash
pnpm --dir docs_site/frontend check
uv run --no-sync pytest \
  docs_site/tests/test_playground_executor.py \
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
uv run --no-sync python scripts/check.py
```

The browser tests should cover a successful render, Python and client errors,
Stop and Reset, stale-result handling, form submission, Citry Events, and at
least one client-active Citry UI component.
