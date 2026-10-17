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
5. `preview.html` asks the Worker for every Vue component definition and
   stylesheet the HTML names, and swaps each path for a Blob URL, because
   those files exist only inside the Worker. It then installs the HTML,
   reactivates supported scripts, and publishes Citry manifests once
   Citry's classic scripts are ready. It waits for authored non-async external
   scripts, while async scripts and modules may finish later.
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

The live server builds a temporary wheel from the workspace `citry-ui` source
and replaces the published Citry UI entry in its generated copy of
`runtime.json`. It serves that local wheel without changing this committed
directory or installing two UI copies. Deployed docs, CI, and static builds
without `CITRY_PLAYGROUND_CORE_WHEEL` use only the exact published versions in
the committed `runtime.json`. The pinned
Citry wheel owns the Events client in both cases.

The workspace `citry-ui` usually requires a Citry that is newer than the pinned
release, for the whole stretch between releases. The server then prints which
pair it rejected and serves this committed runtime unchanged, so every page
still renders and Citry UI examples show their code without a live preview.
Pinning a Citry release that the workspace `citry-ui` accepts brings the local
wheel back, or set `CITRY_PLAYGROUND_CORE_WHEEL` (see below) to run this
checkout's Citry.

## Run the playground with this checkout's Citry

Between releases, the workspace Citry often changes what the browser receives,
while the committed `runtime.json` still installs the last published Citry.
The browser tests then check the published code, not your change. The
workspace Citry also needs the workspace Citry Core, which contains compiled
Rust code, so the browser needs a Citry Core wheel compiled for Pyodide.

Build that wheel with the release build script. The script needs the Pyodide
cross-build environment (the Emscripten compiler and the Python headers that
Pyodide publishes). It also needs a copy of the source without compiled
extensions or Python caches, because it rejects a source tree that contains
them. Run these commands from the repository root:

```bash
cache=~/Library/Caches/citry  # any directory outside the repository
rustup toolchain install 1.96.0 --target wasm32-unknown-emscripten
export PYODIDE_XBUILDENV_PATH=$cache/pyodide-xbuildenv
uvx --python 3.14.2 --from pyodide-cli==0.5.0 \
  --with pyodide-build==0.37.0 \
  pyodide xbuildenv install 314.0.3 --path $PYODIDE_XBUILDENV_PATH
uvx --python 3.14.2 --from pyodide-cli==0.5.0 \
  --with pyodide-build==0.37.0 \
  pyodide xbuildenv install-emscripten --path $PYODIDE_XBUILDENV_PATH

rm -rf $cache/core-src && mkdir -p $cache/core-src/packages/py
rsync -a --exclude .git --exclude target --exclude __pycache__ \
  --exclude '*.so' --exclude '*.pyc' \
  Cargo.toml Cargo.lock crates third_party $cache/core-src/
rsync -a --exclude __pycache__ --exclude '*.so' --exclude '*.pyc' \
  packages/py/citry_core $cache/core-src/packages/py/
rm -rf $cache/core-wheel
uv run --no-sync python scripts/build_citry_core_pyodide_wheel.py \
  --source $cache/core-src/packages/py/citry_core \
  --out-dir $cache/core-wheel \
  --xbuildenv-path $cache/pyodide-xbuildenv \
  --cargo-target-dir $cache/cargo-pyemscripten \
  --source-date-epoch "$(date +%s)"
```

The versions in these commands come from
[`packages/py/citry_core/pyodide-build.json`](../../../packages/py/citry_core/pyodide-build.json).
The first run downloads about 2 GB of tools and takes a few minutes. A cold
Rust build took about three minutes on an Apple Silicon laptop. Later builds
reuse the Cargo target directory. Rebuild the wheel whenever the Rust crates
change.

Point `CITRY_PLAYGROUND_CORE_WHEEL` at the result:

```bash
export CITRY_PLAYGROUND_CORE_WHEEL=$(ls $cache/core-wheel/citry_core-*.whl)
```

With the variable set, the local docs server and the browser tests build
wheels from `packages/py/citry` and `packages/py/citry_ui` (a few seconds),
and the playground installs them with your Citry Core wheel in place of the
published ones.
The generated `runtime.json` says `source: "workspace"` in place of the
committed `source: "published"`, and the playground shows that label next to
the versions it runs. Build the Core wheel from this checkout with the script
above; a matching file name, version, and ABI show that a wheel fits, not that
it was built from your source, so do not use a downloaded wheel here.
The committed directory never changes. If the variable names a missing file, a
wheel built for another platform, or a Citry Core version that the workspace
Citry rejects, the server and the tests stop with the reason rather than fall
back to the published Citry.

## Which browser tests run against the pinned release

Without `CITRY_PLAYGROUND_CORE_WHEEL`, the playground and `<c-live-code>`
browser tests run against the release that `runtime.json` pins, because that
is what the deployed docs serve. The docs check workflow
([`repo--docs-check.yml`](https://github.com/citry-dev/citry/blob/main/.github/workflows/repo--docs-check.yml))
runs them this way too: it does not set the variable, so CI checks the
playground the deployed docs serve and skips the tests below with their
reason. Running them against this checkout's Citry is a local step: build the
Core wheel above and set the variable.

Some tests click through code from this checkout: the docs snippets, the
Citry UI snippets, or the workspace Citry UI wheel. Between releases that code
can use Citry features the pinned release lacks, so these tests carry the
`workspace_citry` marker. Without `CITRY_PLAYGROUND_CORE_WHEEL`, pytest skips
them and prints the reason, which names the variable. With it set, they run
against this checkout's Citry. Every other playground and live-code test runs
unconditionally.

Mark a new browser test `workspace_citry` when it checks what this checkout's
example code or Citry UI does in the browser. Leave it unmarked when it checks
the runtime itself (loading, Stop and Reset, diagnostics, the iframe protocol)
or code that the pinned release already supports.

The release docs workflow sets `CITRY_PLAYGROUND_PINS_MATCH_CHECKOUT=1` when it
tests the pins it has just updated. Right after publication, `main` normally
still holds the released source, so the marked tests describe the pinned
wheels and run. Set it yourself only when your checkout matches the pinned
release; otherwise the marked tests fail on features that release lacks.

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
complete runtime entry before publication. A local runtime rewrites the
`citry` version fields to match the workspace wheels it serves.

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

When your change touches what the browser receives from Citry, set
`CITRY_PLAYGROUND_CORE_WHEEL` for this run so the skipped `workspace_citry`
tests run too.

Finish with the repository gate:

```bash
python scripts/check.py
```

The browser tests should cover a successful render, Python and client errors,
Stop and Reset, stale-result handling, form submission, Citry Events, a Render
action with JavaScript, CSS, nested State and Events, asset deduplication, and
at least one client-active Citry UI component.
