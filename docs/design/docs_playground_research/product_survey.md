# Docs playground product survey

**Status:** Stage 2 research artifact

**Reviewed:** 2026-07-28
Scope: current official product pages, documentation, source repositories,
release records, and issue trackers

## Purpose

This survey compares a bounded group of browser Python tools and mature
component playgrounds against Citry's first-reader job: edit one Python module
and understand how that module becomes HTML. It is decision input, not a final
execution or UI specification. Stage 3 still owns the execution contract and
Stage 4 still owns the editor choice.

No screenshot was needed to prove a relationship that the official source made
clearer. The source inspections below used exact revisions so that later
changes do not silently rewrite this evidence.

## Evidence labels

- **Documented** means an official user or API document states a behavior as a
  public contract.
- **Observed** means the behavior was inspected in an official live page or in
  the implementation at the named revision. Source inspection proves what the
  inspected revision implements, not how every deployment is configured.
- **Maintainer claim** means a product or project page makes a performance,
  security, or product assertion that this survey did not independently prove.
- **Issue report** means an official tracker report. It identifies a failure
  theme, not its incidence or a guaranteed current defect.
- **Inference** means a Citry conclusion drawn from the preceding evidence.

## Versions and revisions inspected

| Product | Inspected version or revision | Official reference |
| --- | --- | --- |
| Pyodide | 314.0.3, released 2026-07-24 | [release](https://github.com/pyodide/pyodide/releases/tag/314.0.3) |
| PyScript | 2026.7.2, released 2026-07-09 | [release](https://github.com/pyscript/pyscript/releases/tag/2026.7.2) |
| JupyterLite | 0.8.1, released 2026-07-08 | [release](https://github.com/jupyterlite/jupyterlite/releases/tag/v0.8.1) |
| Vue REPL | 4.7.2, revision `9b5bc873`, 2026-04-13 | [release](https://github.com/vuejs/repl/releases/tag/v4.7.2) |
| Svelte playground | revision `996bd63e`, 2026-07-27 | [source](https://github.com/sveltejs/svelte.dev/tree/996bd63e478e199e50d841149965290c358fd735) |
| Sandpack | 2.20.0, revision `7d60a433`, 2025-02-14 | [release](https://github.com/codesandbox/sandpack/releases/tag/v2.20.0) |
| Solid Playground | revision `4d6a22c5`, 2026-04-27 | [source](https://github.com/solidjs/solid-playground/tree/4d6a22c5a338b1689c46dbd130dcb885d4dd286e) |
| Shinylive | 0.10.12, revision `2726fe99`, 2026-06-01 | [release](https://github.com/posit-dev/shinylive/releases/tag/v0.10.12) |

Sandpack has active tracker traffic but no newer tagged release than the one in
the table. This survey does not infer that the project is abandoned.

## Executive findings

1. There is no universal Python playground output contract. Pyodide's low-level
   API and notebook consoles expose a final expression. PyScript teaches
   `print()` or explicit `display()`. Shinylive names an explicit `app` for an
   application but uses interactive final-expression semantics for its plain
   Python terminal. Citry should compare implicit final value and explicit
   `render(value)` in Stage 3. Stdout should not become HTML implicitly.
2. JavaScript component playgrounds favor throttled or debounced automatic
   reruns. The
   maintained Python editors favor an explicit Run action, lazy startup, or one
   automatic initial run followed by explicit reruns. Citry should preserve the
   requested live feel but always expose Run and Stop or Restart. The Stage 3
   prototype should compare default autorun with a hybrid that pauses autorun
   after a timeout or repeated failure.
3. A monotonically increasing run id and latest-result-wins rule are established
   patterns. Svelte also visibly dims an old preview while a new bundle is
   pending or invalid. Citry should never leave a previous result looking
   current.
4. Toast-only errors are weaker than the comparators' durable overlays, output
   panes, and tracebacks. Citry needs a persistent diagnostic surface in the
   owning panel. A toast or live-region message can announce the change, but
   cannot be the only record.
5. A Worker protects responsiveness, not secrets. Pyodide documents that Python
   has browser Web API access. An output iframe is a separate boundary. A
   credential-free runner origin, restrictive network policy, hostile-message
   validation, and an opaque-origin result iframe remain necessary threat-model
   work.
6. Mature component playgrounds switch to one panel at a time on narrow screens.
   Their desktop splitters are often pointer-only even when the editor itself is
   keyboard accessible. Citry should copy the responsive panel switch, not the
   inaccessible splitter.
7. CodeMirror is the common lightweight editor. Vue documents Monaco as the
   heavier choice when language intelligence justifies it. Pygments is useful as
   Citry's existing syntax specification and fixture source, but not as the live
   editor engine.
8. Cold start is product UI, not a spinner implementation detail. PyScript delays
   interpreter loading until Run, Svelte suppresses very short loading flashes,
   JupyterLite exposes kernel startup, and Shinylive publishes approximate
   payload sizes. Citry should name the active phase and distinguish first load
   from a warm rerun.
9. Reset is core recovery. Sharing and download are useful but secondary. A
   shared URL also changes the threat model because it can cause someone else's
   code to be loaded. Citry's initial non-goal of automatically running shared
   code remains justified.

## Decision-oriented comparison

| Product | Run and output model | Errors and stale results | Execution and preview boundary | Citry lesson |
| --- | --- | --- | --- | --- |
| Pyodide | Library API; `runPython` returns the final expression | Exceptions cross the JS/Python boundary; application supplies UI | Python may run in a Worker and has Web API access | Good runtime primitive, not a finished playground contract |
| PyScript editor | Explicit Run; runtime loads on first Run; stdout or explicit `display()` | Output is attached to the editor; Stop refreshes the environment | Editor runs in a Worker by default | Strong explicit-run and lazy-load precedent |
| JupyterLite | Explicit cell execution with retained notebook or REPL outputs | Kernel and cell status remain visible | Kernels use Workers; embedded REPL uses an iframe | Good status, sharing, and recovery patterns, but too much notebook UI for Citry |
| Vue SFC Playground | Debounced live compile and preview | Compile and runtime diagnostics; current revision does not establish a Citry-ready stale label | Sandboxed preview iframe; editor on the page | Lightweight two-panel baseline; its splitter accessibility is insufficient |
| Svelte Playground | Automatic worker bundle; newest bundle id wins | Old preview is visibly dimmed; compile overlay and runtime bar/console | Bundler Worker plus sandboxed iframe | Best stale-result and race-handling precedent |
| React docs with Sandpack | Autorun by default, configurable delay or manual run | Built-in preview error overlay and refresh | External bundler/preview iframe | Useful composable feature set; external runtime availability is a recurring risk |
| Solid Playground | 250 ms throttled automatic worker compile | Persistent expandable compiler error; stale labeling is not established | Compiler Worker plus opaque-origin preview iframe | Useful fourth component comparator for formatting, linting, reset, export, and dockable layout |
| Shinylive | Initial app runs once; edits need explicit app rerun; plain Python supports line/selection execution | Loading, running, errored, and empty viewer states; app start error is prominent | Python Worker, service-worker request proxy, result iframe | Closest maintained Python application editor; strong cold-start and sharing precedent |

### Required-field coverage ledger

This ledger makes unavailable or unverified behavior explicit. "Not
established" means the bounded official-source review found no contract that
should be copied, not that the feature cannot exist.

| Product | Editor, split, mobile, and accessibility | Reset, format, share, download, permalink, and version controls | Cold-start and persistence |
| --- | --- | --- | --- |
| Pyodide | No editor or layout UI; not applicable | Integrator-owned; not applicable | Runtime API exposes loading primitives, not product UI; no UI persistence |
| PyScript editor | CodeMirror; Escape then Tab is documented; full-screen split, mobile mode, and divider persistence are not established | Run and Stop are built in; reset, format, share, download, permalink, and visible version controls are not established for the embedded editor | Interpreter loads on first Run; editor environments may be independent or explicitly shared |
| JupyterLite | JupyterLab editor and keyboard cell commands; embedded REPL can hide chrome; playground splitter and mobile contracts are not established | Shareable REPL link, download settings, and browser storage are documented; a Citry-like restore-starter or format control is not established | Kernel startup is explicit; files persist in browser storage, while service-worker state is a known recovery concern |
| Vue REPL | CodeMirror or Monaco; one-panel mobile toggle; pointer-only 20 to 80 percent splitter; divider persistence not established | URL-hash state is documented; reset, format, download, and version-control behavior were not established strongly enough for a Citry decision | Runtime resource URLs are configurable; no copied cold-start or divider-persistence contract |
| Svelte Playground | CodeMirror; desktop split and one-panel mobile toggle; divider persistence not established | Create, fork, save, hash state, and download are present; format and restore-starter behavior are not established | Bundler status appears after 400 ms; draft state uses session storage |
| Sandpack | CodeMirror with custom languages; responsive columns; preset divider is pointer-only and not persisted by the inspected preset | Reset-file and reset-all hooks, refresh, and Open CodeSandbox are documented; formatting and self-contained permalink versioning depend on the integration | Immediate, lazy, and viewport-visible initialization plus compile delay are configurable |
| Solid Playground | Monaco for TSX, TypeScript, CSS, and JSON; dockable panes; mobile header exists, but a narrow-pane contract and divider persistence are not established | Reset with confirmation, format and lint workers, share or fork, ZIP export, and compile modes are implemented | Suspense and iframe loading states are visible; scratchpad source uses local storage, not divider state |
| Shinylive | CodeMirror plus Pyright; pointer-only resizable grid; 400 px minimum and no complete mobile contract; divider persistence not established | Share, app-only link, gist route, download, static export, and local file controls are present; format exists in source | Explicit loading states and published payload estimates; HTTP cache persists, virtual files do not |

## Browser Python products

### Pyodide

**Reader and first use.** [Documented] Pyodide is a CPython distribution for
the browser and Node, not a complete teaching UI. Its official page offers a
browser REPL and directs integrators to the JavaScript API. Python has access to
browser Web APIs. See the [current project
overview](https://pyodide.org/en/stable/) and [getting-started
guide](https://pyodide.org/en/stable/usage/quickstart.html).
Pyodide does not prescribe a first-loaded module, split layout, reset, sharing,
or download UI; those belong to the integrating application.

**Execution and output.** [Documented] `runPython()` and `runPythonAsync()`
return the value of the final expression. Pyodide also provides console helpers
with Python display-hook behavior, stdout and stderr redirection, and structured
exceptions. This makes Citry's proposed final-expression capture compatible
with the underlying runtime, although normal `.py` module execution still does
not have that contract. See the [JavaScript execution
example](https://pyodide.org/en/stable/usage/quickstart.html), [console
API](https://pyodide.org/en/stable/usage/api/python-api/console.html), and
[stream redirection](https://pyodide.org/en/stable/usage/streams.html).

**Workers and cancellation.** [Documented] Current Pyodide requires a
module-type Worker. The official worker example uses request ids, a separate
globals dictionary, `runPythonAsync()`, and serialized error messages. A Worker
cannot directly manipulate the document. See [Using Pyodide in a web
worker](https://pyodide.org/en/stable/usage/webworker.html). Cooperative
interrupts require a Worker, `SharedArrayBuffer`, and cross-origin isolation;
compiled code must check for signals. See [Interrupting
execution](https://pyodide.org/en/stable/usage/keyboard-interrupts.html).

[Inference] Worker termination remains the reliable hard-stop and recovery
path for Citry. A friendly interrupt may improve the experience when the
deployment headers and executed code permit it, but cannot replace the timeout.

**Packages and assets.** [Documented] `micropip` can install pure-Python wheels
and Emscripten-compatible binary wheels. Binary C, C++, Fortran, or Rust
extensions need a compatible cross-build. `loadPackagesFromImports()` searches
the Pyodide distribution rather than arbitrary PyPI packages. See [Loading
packages](https://pyodide.org/en/stable/usage/loading-packages.html), the
[binary-wheel FAQ](https://pyodide.org/en/stable/usage/faq.html#why-cant-micropip-find-a-pure-python-wheel-for-a-package),
and [bundler guidance](https://pyodide.org/en/stable/usage/working-with-bundlers.html).

**Isolation.** [Documented] Browser Python can use Web APIs, including network
APIs available in its realm. [Inference] A Worker is a scheduling boundary, not
a security sandbox. Loading the exact Citry wheel is a Stage 1 feasibility
question; the existence of other Rust ports is not proof that Citry's PyO3
extension works.

**Official issue themes.** [Issue report] Current reports include an
[interrupt that does not stop `requests` or
`time.sleep()`](https://github.com/pyodide/pyodide/issues/6082), [snapshot
restore failure](https://github.com/pyodide/pyodide/issues/6254), and
[`lockFileURL` resolution failure](https://github.com/pyodide/pyodide/issues/5135).
The recurring decision themes are incomplete interruption, state restoration,
and exact artifact resolution.

### PyScript

**Reader and starter.** [Documented] PyScript's current editor is aimed at
tutorials, demonstrations, and embedded interactive exercises. Its basic sample
prints the Python version. The editor is CodeMirror-based, has a Run control,
and does not load its interpreter until the first Run. See the [2026.7.2 editor
guide](https://docs.pyscript.net/2026.7.2/user-guide/editor/).

**Execution and output.** [Documented] `py-editor` uses explicit Run, with
`Ctrl+Enter`, `Cmd+Enter`, and `Shift+Enter` shortcuts. Each editor gets an
independent environment by default, with an opt-in shared environment and
hidden setup editors. A running editor exposes Stop, asks for confirmation, and
refreshes the editor environment. Output can be sent to a named element.

[Documented] PyScript separates `print()` from rich display. `display()` can
append or replace a target. Plain strings are escaped; trusted raw markup needs
an explicit `HTML()` wrapper. `_repr_*_` methods support rich objects. See
[Display](https://docs.pyscript.net/2026.7.2/user-guide/display/). This is a safer
precedent than treating captured stdout as preview HTML.

**Accessibility and layout.** [Documented] Because CodeMirror uses Tab for
indentation, Escape followed by Tab moves focus out of the editor. The current
guide calls this out explicitly. PyScript supplies an editor component, not a
prescribed two-panel full-screen playground.

**Workers and loading.** [Documented] Editors run in Workers by default. Worker
interpreters, memory, and filesystems are separate, and bridge values must be
serializable. Pyodide worker initialization may be slow, so the official guide
asks applications to show loading feedback. Some synchronous main-thread access
requires `SharedArrayBuffer` headers or a service-worker fallback. See [Web
Workers](https://docs.pyscript.net/2026.7.2/user-guide/workers/) and the
[FAQ](https://docs.pyscript.net/2026.7.2/faq/).

**Sharing.** [Maintainer claim] [PyScript.com](https://pyscript.com/) offers
browser project creation and one-click sharing, with stated project size
limits. This is a hosted product feature, not a contract of the embedded editor.

**Official issue themes.** [Issue report] Representative open reports cover
[improved error reporting](https://github.com/pyscript/pyscript/issues/1596),
[local wheel dependency resolution](https://github.com/pyscript/pyscript/issues/2282),
a [matplotlib editor regression](https://github.com/pyscript/pyscript/issues/2464),
and [worker configuration parsing](https://github.com/pyscript/pyscript/issues/2430).
The recurring themes are error visibility, worker-specific differences, package
resolution, and editor regressions.

### JupyterLite

**Reader and execution contract.** [Documented] JupyterLite brings the
JupyterLab and notebook model into a static site. Code is run explicitly by
cell or REPL prompt, with familiar `Ctrl+Enter`, `Shift+Enter`, and `Alt+Enter`
variants. Outputs and execution history remain attached to cells. See the
[JupyterLite overview](https://jupyterlite.readthedocs.io/en/stable/) and
[JupyterLab execution commands](https://jupyterlab.readthedocs.io/en/stable/user/commands.html).
The deployed files and notebooks are site-configured, so JupyterLite has no
single canonical first-loaded lesson. See [adding files and
content](https://jupyterlite.readthedocs.io/en/stable/howto/content/files.html).

**Embedding and sharing.** [Documented] The embedded REPL can be placed in an
iframe and reduced to one executable cell. Its toolbar can expose Copy
Shareable Link, and the link can either populate or automatically execute the
prompt. Options can clear old cells, hide input, and select a prompt position.
See [Embedding a REPL](https://jupyterlite.readthedocs.io/en/stable/quickstart/embed-repl.html).
JupyterLab [settings](https://jupyterlite.readthedocs.io/en/stable/howto/configure/settings.html)
also support download controls. Browser storage preserves content beneath the
deployment base URL. See [storage
configuration](https://jupyterlite.readthedocs.io/en/stable/howto/configure/storage.html).

**Workers, files, and assets.** [Documented] Pyodide and Xeus kernels run in
Workers. Pyodide kernels use IPython and `piplite`; packages are not all
preinstalled. Kernel access to browser-managed files requires
`SharedArrayBuffer` with cross-origin isolation or a service-worker fallback.
The default Pyodide distribution is fetched from a CDN because a full copy is
large. See [kernel configuration](https://jupyterlite.readthedocs.io/en/stable/howto/configure/kernels.html),
[Python content and files](https://jupyterlite.readthedocs.io/en/stable/howto/content/python.html),
and [Pyodide distribution configuration](https://jupyterlite.readthedocs.io/en/stable/howto/pyodide/pyodide.html).

**Recovery and failure modes.** [Documented] Service workers require HTTPS or
localhost and have private-browsing limitations. The project migration guide
says cache behavior caused enough problems that service-worker use changed.
Troubleshooting may require clearing browser storage, a destructive recovery
action. See [service-worker configuration](https://jupyterlite.readthedocs.io/en/latest/howto/configure/advanced/service-worker.html),
[migration notes](https://jupyterlite.readthedocs.io/en/stable/migration.html),
and [troubleshooting](https://jupyterlite.readthedocs.io/en/stable/troubleshooting.html).

**Official issue themes.** [Issue report] Representative reports cover a
[terminal unavailable without SharedArrayBuffer or a service
worker](https://github.com/jupyterlite/jupyterlite/issues/1939), [Firefox
becoming unresponsive with many kernels](https://github.com/jupyterlite/jupyterlite/issues/1527),
and [content cache busting](https://github.com/jupyterlite/jupyterlite/issues/1706).
The recurring themes are cross-origin headers, service-worker and content cache
state, multiple-kernel resource use, file synchronization, and wheel packaging.

[Inference] JupyterLite offers excellent explicit execution, durable output,
sharing, and status patterns, but its notebook, filesystem, kernel, and settings
surface is much larger than Citry's single-module learning job.

## Component playgrounds

### Vue SFC Playground and `@vue/repl`

**Reader and starter.** [Observed] Vue REPL 4.7.2 opens a small `Hello World!`
single-file component and a live result. See the [welcome template](https://github.com/vuejs/repl/blob/9b5bc873415bbc6fcba6080b9402d140175d5b03/src/template/welcome.vue).
[Inference] That keeps the first edit close to the concept being taught.

**Editor and execution.** [Documented] The project supports CodeMirror and
Monaco. Its README describes CodeMirror as lighter, with fewer requests and
better embedding characteristics, while Monaco adds Volar completion, type
inference, semantic highlighting, and CDN-loaded declarations. It also
documents URL-hash serialization and a mobile output mode. See the [4.7.2
README](https://github.com/vuejs/repl/blob/9b5bc873415bbc6fcba6080b9402d140175d5b03/README.md).

[Observed] Editor changes are debounced by 250 ms before update in the inspected
revision. Compile errors are shown at the editor with a durable show or hide
control. See [EditorContainer.vue](https://github.com/vuejs/repl/blob/9b5bc873415bbc6fcba6080b9402d140175d5b03/src/editor/EditorContainer.vue).

**Preview and diagnostics.** [Observed] The result uses an iframe built from
`srcdoc`. Its bridge reports synchronous errors, unhandled promise rejections,
`console.error`, and Vue warnings. Runtime errors are cleared for a new update,
and changing the import map recreates the iframe. See
[Sandbox.vue](https://github.com/vuejs/repl/blob/9b5bc873415bbc6fcba6080b9402d140175d5b03/src/output/Sandbox.vue)
and the [in-frame bootstrap](https://github.com/vuejs/repl/blob/9b5bc873415bbc6fcba6080b9402d140175d5b03/src/output/srcdoc.html).

[Observed] The iframe permits scripts, forms, modals, pointer lock, popups,
same-origin access, and user-activated top navigation. That policy supports a
general Vue REPL and is much broader than Citry's candidate result policy.

**Split and mobile behavior.** [Observed] The splitter clamps each desktop pane
between 20 and 80 percent. Below 720 px the UI switches between Code and Output
rather than showing a cramped split. The dragger is a mouse-driven `div` with no
keyboard handler, focus target, or separator semantics in the inspected source.
See [SplitPane.vue](https://github.com/vuejs/repl/blob/9b5bc873415bbc6fcba6080b9402d140175d5b03/src/SplitPane.vue).

**Official issue themes.** [Issue report] Reports cover [TypeScript errors that
appear only after refresh](https://github.com/vuejs/repl/issues/321), [splitter
behavior during screen-size switching](https://github.com/vuejs/repl/issues/376),
and [listener accumulation](https://github.com/vuejs/repl/issues/355). The
recurring themes are diagnostic freshness and location, Monaco lifecycle cost,
layout transitions, and resource cleanup.

### Svelte Playground

**Reader and starter.** [Observed] The official playground's basic route is a
small `hello-world` example with examples and create-new controls. It reserves
the viewport beneath the site header for the editor. It also supports saving or
forking with an account and keyboard save. See the [playground page](https://github.com/sveltejs/svelte.dev/blob/996bd63e478e199e50d841149965290c358fd735/apps/svelte.dev/src/routes/%28authed%29/playground/%5Bid%5D/%2Bpage.svelte)
and [app controls](https://github.com/sveltejs/svelte.dev/blob/996bd63e478e199e50d841149965290c358fd735/apps/svelte.dev/src/routes/%28authed%29/playground/%5Bid%5D/AppControls.svelte).

**Execution, races, and cold state.** [Observed] Workspace updates trigger an
automatic bundle in a module Worker. Bundles carry increasing ids; only the
current id is published and older work is superseded. A loading status is
delayed for 400 ms so quick work does not flash a busy indicator. See
[Repl.svelte](https://github.com/sveltejs/svelte.dev/blob/996bd63e478e199e50d841149965290c358fd735/packages/repl/src/lib/Repl.svelte),
[Bundler.svelte.ts](https://github.com/sveltejs/svelte.dev/blob/996bd63e478e199e50d841149965290c358fd735/packages/repl/src/lib/Bundler.svelte.ts),
and the [bundler worker](https://github.com/sveltejs/svelte.dev/blob/996bd63e478e199e50d841149965290c358fd735/packages/repl/src/lib/workers/bundler/index.ts).

**Stale and error behavior.** [Observed] The output iframe catches synchronous
errors, unhandled rejections, and console messages. On a pending or failed
bundle, the prior preview is dimmed and blurred to 25 percent opacity. A compile
error overlays the output with source information; runtime errors get a durable
message bar and console. A successful bundle unmounts the previous app and
clears its body before mounting the new one. See
[Viewer.svelte](https://github.com/sveltejs/svelte.dev/blob/996bd63e478e199e50d841149965290c358fd735/packages/repl/src/lib/Output/Viewer.svelte)
and [ErrorOverlay.svelte](https://github.com/sveltejs/svelte.dev/blob/996bd63e478e199e50d841149965290c358fd735/packages/repl/src/lib/Output/ErrorOverlay.svelte).

**Split, mobile, and isolation.** [Observed] Desktop uses a resizable split.
Below 540 px the layout becomes a one-panel Code or Result view. The result
iframe has a `Result` title. Its default sandbox excludes same-origin permission;
optional relaxed and popup-escape modes broaden it. The default still permits
popups, forms, pointer lock, and modals. Citry should copy the omission of
same-origin permission, but add none of those other tokens without a tested
requirement.

**Share and download.** [Observed] Source can be compressed into the URL hash,
saved in session storage, or downloaded as an app archive. Hash state is updated
at interaction boundaries rather than on every keystroke. Hash-provided
playgrounds restrict sandbox escape. [Inference] This is a useful precedent for
sharing only after the threat model covers externally supplied code.

**Official issue themes.** [Issue report] Reports cover [broken syntax
highlighting](https://github.com/sveltejs/svelte.dev/issues/1896), [stale service
worker content preventing load](https://github.com/sveltejs/svelte.dev/issues/866),
and [missing state in a hash link](https://github.com/sveltejs/svelte.dev/issues/1892).
The recurring themes are language-highlighter drift, actionable compiler
messages, export fidelity, service-worker staleness, and complete permalinks.

### React documentation and Sandpack

**Reader and starter.** [Documented] React documentation embeds task-specific
Sandpack editors and lets the reader Fork them into CodeSandbox. Some exercises
also expose Reset or download through the CodeSandbox handoff. See React's
[installation page](https://react.dev/learn/installation) and [tutorial](https://react.dev/learn/tutorial-tic-tac-toe).
Sandpack itself is a composable library, so it has templates rather than one
canonical first-loaded learning sample.

**Execution and cold state.** [Documented] Sandpack autoruns by default. Its
layout API supports delayed compilation with a 500 ms default debounce,
`autoReload`, manual controls, and immediate, lazy, or viewport-visible
initialization. The docs recommend fixed preview heights to avoid layout shift.
See [layout configuration](https://sandpack.codesandbox.io/docs/getting-started/layout).

**Editor, preview, and recovery.** [Documented] The built-in editor uses
CodeMirror and accepts custom languages and extensions. The preview supplies an
error overlay, refresh, open-in-new-tab, and Open CodeSandbox controls. Hooks can
reset one file or all files and drive a custom editor or console. See [advanced
components](https://sandpack.codesandbox.io/docs/advanced-usage/components) and
[hooks](https://sandpack.codesandbox.io/docs/advanced-usage/hooks). The official
FAQ says the built-in editor does not provide a complete TypeScript language
server. See the [FAQ](https://sandpack.codesandbox.io/docs/resources/faq).

**Split, mobile, and accessibility.** [Documented] The default two-column
layout breaks beneath 700 px and resizable panels are configurable. [Observed]
At revision `7d60a433`, editor tabs have keyboard and ARIA handling, but the
preset resizer is a pointer-driven `div` without separator semantics and is
hidden below 768 px. See [Sandpack.tsx](https://github.com/codesandbox/sandpack/blob/7d60a4334980eef304d53b1c3df371ed6dbcf491/sandpack-react/src/presets/Sandpack.tsx).

**Boundary and assets.** [Maintainer claim] Sandpack says package evaluation and
transpilation occur in a different-subdomain iframe, which protects host cookies,
and that transpilation uses Workers. It can use an externally hosted or
self-hosted bundler. See [hosting the
bundler](https://sandpack.codesandbox.io/docs/guides/hosting-the-bundler). The
FAQ documents required external preview and CDN domains, service-worker browser
issues, and network requirements. [Inference] This architecture offers stronger
origin separation than a same-origin `srcdoc` preview, but adds runtime-service,
package-CDN, CSP, and frame-header dependencies.

**Official issue themes.** [Issue report] Recent reports repeatedly mention
[failure to connect to the runtime](https://github.com/codesandbox/sandpack/issues/1290),
[package installation failure](https://github.com/codesandbox/sandpack/issues/1296),
[lazy initialization flicker](https://github.com/codesandbox/sandpack/issues/1069),
and [custom-domain frame headers](https://github.com/codesandbox/sandpack/issues/1272).
The recurring themes are external runtime availability, dependency CDN failures,
CSP and framing, and lazy lifecycle behavior.

### Solid Playground

**Reader and starter.** [Documented] Solid's current quick start directs readers
to the official interactive playground. [Observed] Revision `4d6a22c5` starts
with one `main.tsx` counter and an explicit `render(..., #app)` call. See the
[quick start](https://docs.solidjs.com/quick-start) and [default
source](https://github.com/solidjs/solid-playground/blob/4d6a22c5a338b1689c46dbd130dcb885d4dd286e/packages/solid-repl/src/index.ts).

**Execution and errors.** [Observed] Source changes trigger compiler work
automatically through a 250 ms throttle. Compilation runs in a Worker and the
result is posted to a preview iframe. Compiler failures appear in a persistent
bottom diagnostic with a summary, expandable stack, and dismiss control. The
inspected protocol does not establish increasing run ids or an explicit stale
preview state. See [repl.tsx](https://github.com/solidjs/solid-playground/blob/4d6a22c5a338b1689c46dbd130dcb885d4dd286e/packages/solid-repl/src/components/repl.tsx)
and [error.tsx](https://github.com/solidjs/solid-playground/blob/4d6a22c5a338b1689c46dbd130dcb885d4dd286e/packages/solid-repl/src/components/error.tsx).

**Editor, layout, and controls.** [Observed] Monaco supplies TSX, TypeScript,
CSS, and JSON support. Separate Workers handle compilation, formatting, and
linting. `Ctrl+S` or `Cmd+S` formats and applies lint fixes. Dockview provides
resizable, movable editor, Preview, and compiled Output panes. Reset asks for
confirmation; the header supports share or fork and ZIP export. Scratchpad
source is saved in local storage. No narrow-screen pane switch, keyboard
divider contract, or divider persistence was established. See [the
editor](https://github.com/solidjs/solid-playground/blob/4d6a22c5a338b1689c46dbd130dcb885d4dd286e/packages/solid-repl/src/components/editor/index.tsx),
[the page state](https://github.com/solidjs/solid-playground/blob/4d6a22c5a338b1689c46dbd130dcb885d4dd286e/packages/playground/src/pages/edit.tsx),
and [header controls](https://github.com/solidjs/solid-playground/blob/4d6a22c5a338b1689c46dbd130dcb885d4dd286e/packages/playground/src/components/header.tsx).

**Preview, assets, and cold start.** [Observed] The result iframe has a stable
title and an opaque origin because its sandbox excludes same-origin permission.
It also permits scripts, popups, popup escape, forms, modals, and pointer lock,
which is broader than Citry needs. The iframe shows a loading message and the
outer page has a Suspense fallback. Preview and developer-tools HTML load pinned
scripts or styles from jsDelivr, unpkg, and JSPM, while user imports default to
esm.sh. See [preview.tsx](https://github.com/solidjs/solid-playground/blob/4d6a22c5a338b1689c46dbd130dcb885d4dd286e/packages/solid-repl/src/components/preview.tsx).

**Official issue themes.** [Issue report] A bounded review of the [official
playground tracker](https://github.com/solidjs/solid-playground/issues) did not
establish a recurring complaint pattern strong enough to use as a Citry
decision. This survey does not manufacture one from isolated reports.

[Inference] Solid reinforces automatic worker compilation, durable diagnostics,
explicit app mounting, and source restore or export. Its general-purpose
dockable layout, Monaco and linting workers, broad iframe permissions, and
external developer-tools assets exceed Citry's first-release learning job.

## Maintained Python application comparator: Shinylive

**Why it belongs in the set.** [Documented] Shinylive is a maintained Python
browser editor for a real application framework, not only a notebook.
[Inference] It is therefore the closest product comparator for Citry even
though a Shiny app is multi-file and long-lived.

**Reader, starter, and output contract.** [Documented] Posit's guide says Python
Shiny runs entirely in the browser through Pyodide. Its default app is a small
slider and text-output example. [Observed] The source also provides a plain
Python script starter ending in `add(1, 2)`. That script is sent to an interactive
terminal, so the final expression is displayed, while an application must
explicitly bind `app = App(...)`. See the [Shinylive guide](https://shiny.posit.co/py/get-started/shinylive.html)
and [current starter templates](https://github.com/posit-dev/shinylive/blob/2726fe99c05ba4516cd002bef8d8f734be125133/src/Components/App.tsx).

**Run behavior.** [Observed] A runnable app executes once after load. Subsequent
edits do not automatically rerun the whole application. `Ctrl+Shift+Enter` or
`Cmd+Shift+Enter` reruns it; `Ctrl+Enter` or `Cmd+Enter` sends the selected text
or current line to the terminal. Rerunning first stops the old app and clears
the result iframe. See [Editor.tsx](https://github.com/posit-dev/shinylive/blob/2726fe99c05ba4516cd002bef8d8f734be125133/src/Components/Editor.tsx).

**Editor and diagnostics.** [Observed] The editor uses CodeMirror plus a
separate Pyright language-server Worker. The viewer has loading, running,
errored, and empty states. An app-start exception replaces the loading view with
a prominent error and traceback. See [Viewer.tsx](https://github.com/posit-dev/shinylive/blob/2726fe99c05ba4516cd002bef8d8f734be125133/src/Components/Viewer.tsx)
and the [Pyright client](https://github.com/posit-dev/shinylive/blob/2726fe99c05ba4516cd002bef8d8f734be125133/src/language-server/pyright-client.ts).

[Documented] The Shiny debugging guide also warns that some Python errors are
visible only in the browser developer console when an application has no visible
Python console. See [Debugging Shiny in the
browser](https://shiny.posit.co/py/get-started/debug.html). [Inference] Citry
should not require developer tools for any runner-owned or caught iframe error.

**Workers, iframe, and service worker.** [Observed] Python runs in a Worker, the
application result runs in an iframe, and a service worker proxies application
requests. These are distinct lifecycle and failure domains. A Pyright Worker is
additional cost and would exceed Citry's initial no-language-server scope.

**Cold load and packages.** [Documented] The guide publishes approximate
downloads: about 13 MB for the base runtime, 7.5 MB for NumPy, 13 MB for pandas,
and 11.5 MB for Matplotlib, with browser caching after first use. Packages can
come from Pyodide or compatible pure wheels. The virtual filesystem is lost on
navigation even though HTTP assets may stay cached. These figures are
Shinylive-specific, not Citry estimates, but the disclosure pattern is useful.

**Sharing, reset, and download.** [Documented] Share creates an editor URL or an
app-only URL with code compressed into the hash, which is not sent in the HTTP
request. The UI displays link length and also offers a gist route with documented
GitHub API rate limits. Apps can be downloaded or exported as static files.
[Observed] The current editor updates share state when an app is run, not on
every keystroke, and warns when compressed state grows too large.

**Split, mobile, and accessibility.** [Observed] Shinylive uses a resizable grid,
but its resize handles are mouse-driven elements without keyboard separator
semantics. The current layout has a 400 px minimum width. See the [resizer
source](https://github.com/posit-dev/shinylive/blob/2726fe99c05ba4516cd002bef8d8f734be125133/src/Components/ResizableGrid/ResizableGrid.tsx)
and [grid styles](https://github.com/posit-dev/shinylive/blob/2726fe99c05ba4516cd002bef8d8f734be125133/src/Components/ResizableGrid/ResizableGrid.css).
[Issue report] The project has an open [mobile-friendliness
issue](https://github.com/posit-dev/shinylive/issues/6).

**Official issue themes.** [Issue report] Representative reports cover [long
loading time](https://github.com/posit-dev/shinylive/issues/192), [missing or
failed service-worker behavior](https://github.com/posit-dev/shinylive/issues/133),
[package version conflicts](https://github.com/posit-dev/shinylive/issues/213),
and the mobile issue above. The recurring themes are cold startup, service-worker
dependency and error visibility, wheel compatibility, and narrow-screen
usability.

## Cross-product decisions for Citry

### Run trigger and cancellation

The products disagree in a meaningful way:

| Pattern | Products | Benefit | Failure mode |
| --- | --- | --- | --- |
| Debounced or throttled autorun | Vue, Svelte, Sandpack, Solid | Immediate cause and effect | Run storms, battery cost, confusing partial code, runaway loops |
| Explicit first Run with lazy runtime | PyScript | Fast shell, user consent before large load | First click feels slow; no result on arrival |
| Automatic initial run, explicit later reruns | Shinylive | Immediate successful example without edit-time churn | Reader may expect edits to be live |
| Explicit cell or prompt | JupyterLite | Clear execution history | Too notebook-like for a live component preview |

**Stage 2 recommendation:** carry two candidates into Stage 3, both with a
visible Run control and shortcut:

1. Debounced autorun after runtime readiness, with latest-wins ids, a Stop
   control, a hard timeout, and automatic pause after a timeout.
2. Automatic initial sample followed by explicit rerun, with an optional
   autorun toggle remembered only for that browser.

Do not queue every edit while the runtime is cold. Keep only the newest source.
When compilation starts, wait long enough before showing a busy indicator to
avoid flicker, but announce a genuinely long bootstrap. Hard timeout must
terminate and recreate the Python Worker even if cooperative interruption is
available.

### Preview value and stdout

The survey does not establish one industry standard:

- Pyodide's API and interactive consoles make a final expression natural.
- JupyterLite and Shinylive's plain Python script use display-hook behavior.
- PyScript uses explicit `print()` or `display()`, and explicit `HTML()` for raw
  markup.
- Application frameworks tend to name an app or mount point explicitly.

**Stage 2 recommendation:** reject `print()` as HTML. Capture stdout and stderr
for diagnostics or an optional console. Carry implicit final expression and an
explicit `render(value)` helper as the two serious Stage 3 candidates. A named
`preview` variable adds ceremony without a clear precedent. Whichever candidate
wins should accept only documented Citry result types and accepted string or
`Markup` results, then still treat the resulting preview HTML as hostile.
Preserve source locations and give an actionable error for no value or `None`.

The canonical starter and the permissive exploratory behavior need not be
identical. For example, Stage 3 may find that the docs should teach
`render(Card(...))` while the runner also accepts a final `Card(...)` expression.
That is a product decision, not something Pyodide's return value settles.

### Current, pending, stale, and failed output

Svelte supplies the clearest precedent. Citry should model preview state
explicitly:

1. `booting`: runtime assets or Citry are loading;
2. `running`: the current source is executing;
3. `current`: preview matches the latest successful source;
4. `stale`: an older preview remains while newer source is pending or failed;
5. `restarting`: a terminated Worker is being rebuilt;
6. `unavailable`: there has never been a successful preview.

Every run needs an increasing id. The parent accepts output only from the
current id and current Worker generation. Preserve the last successful iframe
when feasible, but dim it and label it "Previous result" while stale. A syntax
or runtime error must not silently replace useful output, and old output must
not silently look current.

### Diagnostics

Use a persistent bottom tray in the panel that owns the failure:

- left panel: asset bootstrap, package, syntax, Citry compile/render, timeout,
  result-contract, and runner-protocol errors;
- right panel: synchronous iframe error, unhandled rejection, observed resource
  failure, and deduplicated `console.error`;
- page-level status: browser policy or deployment failure that prevents either
  side from starting.

Show a one-line summary, source location where known, expandable traceback or
details, Copy details, and Dismiss only after the condition has cleared or the
reader deliberately hides it. A live region may announce a new error. A toast
can supplement the tray for Stop, Reset, or "copied", but a traceback should not
expire.

Iframe reports remain best-effort telemetry from hostile visitor code. Validate
the source window, schema, size, rate, Worker generation, and run id. Insert all
messages as text. Absence of a report is not proof that the iframe succeeded.

### Desktop split, mobile mode, and accessibility

Use a two-panel desktop workspace and switch to one panel at a time on narrow
screens. A Code and Result tab or segmented control is more usable than two tall
stacked panes when the software keyboard is open. The switch must preserve the
editor buffer, selection, scroll position, latest preview, and diagnostics.

The divider must improve on the directly inspected Vue, Sandpack, and Shinylive
implementations:

- use separator semantics with an accessible name and current, minimum, and
  maximum values;
- make it focusable;
- support pointer and touch drag;
- support arrows, larger modified-arrow steps, Home, End, and reset;
- maintain visible focus and work in forced colors;
- clamp corrupt persisted values and offer a reset to 50 percent.

Editor focus order must include Run, Stop, Reset, Code or Result switch,
diagnostics, and the iframe. Follow CodeMirror's Escape then Tab convention and
explain it in accessible help. The result iframe needs a stable title.

### Editor and mixed-language highlighting

CodeMirror 6 remains the Stage 4 comparison favorite because Vue, PyScript,
Sandpack, and Shinylive demonstrate its use in embedded tools, while Vue's own
documentation identifies Monaco's extra language intelligence and request
cost. Citry's first release does not need a language server.

Pygments cannot provide the editing surface or incremental parse by itself.
Treat `pygments-citry` as the existing language behavior specification: reuse
its supported-syntax fixtures and expected token boundaries while implementing
the editor's own parser or mixed-language extension. Test Python containing
nested HTML, CSS, and JavaScript as syntax changes on every keystroke. A plain
Python mode is an acceptable temporary fallback only if the UI says nested
highlighting is incomplete and Stage 4 records the upgrade path.

### Workers, iframe, and origin policy

Use the boundaries for separate purposes:

- Python Worker: responsiveness, disposable interpreter, and hard-stop unit;
- result iframe: DOM and script isolation from the documentation shell;
- dedicated credential-free origin, if accepted in the threat model: reduce
  access to Citry-site credentials and sensitive same-origin data;
- restrictive response and network policy: bound runtime and preview asset
  loading where browser policy permits it.

Do not describe a Worker as a sandbox. Do not copy Vue's broad iframe sandbox
tokens simply because they make a general framework REPL convenient. Do not add
`allow-same-origin`, forms, popups, navigation, or downloads without a tested
Citry requirement. External fonts, scripts, stylesheets, images, relative URLs,
`fetch`, and dynamic imports need explicit accepted or rejected behavior.

### Asset and cold-start contract

Pin Pyodide, Python standard-library data, Citry wheels, editor assets, and every
transitive artifact as one compatible manifest. Display phases that correspond
to work the reader can understand:

1. Loading Python;
2. Loading Citry;
3. Preparing the example;
4. Rendering;
5. Restarting after timeout, when applicable.

Do not show a false percentage without byte-level progress. Show Retry and a
specific failure when an asset or policy blocks startup. Measure and publish
cold bootstrap, first render, warm render, transferred bytes, and cached bytes
for the deployment browser matrix. Service-worker caching is not a free win;
JupyterLite, Svelte, Sandpack, and Shinylive trackers all show cache or
service-worker failure as a recurring operational theme.

### Starter, reset, share, and download

The common first-use pattern is a small visible success, with examples or forks
for depth. Citry should start with the proposed self-contained Card-like module:
typed input, a small Python transformation, visibly nested template syntax,
small component CSS, and one preview expression. `components_step9.py` remains
too coupled and advanced for the default. A richer composition or JavaScript
preset can follow only after the initial runtime and payload are understood.

Feature priority from the survey:

1. **Initial release:** Run, Stop or Restart, Reset to starter, durable current
   or stale state, version display, retry, and copyable diagnostics.
2. **Useful after core behavior is reliable:** optional autorun toggle, format,
   copy source, download one `.py` file, and a small preset selector.
3. **Later threat-modelled feature:** share or permalink. Never automatically
   execute URL-provided code on arrival. Show the pinned Citry version and link
   size, and provide an explicit Run action.

Reset should have distinct commands for Reset output and Restore starter so a
reader does not lose edits unexpectedly. Download is safer and more transferable
than account-backed persistence. Formatting must not rewrite invalid mixed
Citry syntax or move diagnostic source positions unexpectedly.

## Recurring issue themes across products

These issue reports are signals for Citry's test plan, not frequency data:

| Theme | Products providing examples | Citry consequence |
| --- | --- | --- |
| Interrupt edge cases | [Pyodide](https://github.com/pyodide/pyodide/issues/6082) | Test infinite loops and terminate the Worker as the final fallback |
| Wheel and dependency resolution | [PyScript](https://github.com/pyscript/pyscript/issues/2282), [Sandpack](https://github.com/codesandbox/sandpack/issues/1296), [Shinylive](https://github.com/posit-dev/shinylive/issues/213) | Build one exact artifact manifest and fail before publishing |
| Service-worker or cache state | [JupyterLite](https://github.com/jupyterlite/jupyterlite/issues/1706), [Svelte](https://github.com/sveltejs/svelte.dev/issues/866), [Shinylive](https://github.com/posit-dev/shinylive/issues/133) | Do not claim offline support; version caches and provide non-destructive recovery |
| Late or hidden diagnostics | [PyScript](https://github.com/pyscript/pyscript/issues/1596), [Vue](https://github.com/vuejs/repl/issues/321) | Persistent source-linked diagnostics are a core contract |
| Splitter and narrow-layout regression | [Vue](https://github.com/vuejs/repl/issues/376), [Shinylive](https://github.com/posit-dev/shinylive/issues/6) | Test pointer, touch, keyboard, zoom, mobile switch, and soft keyboard |
| Incomplete shared state | [Svelte](https://github.com/sveltejs/svelte.dev/issues/1892) | Version serialization and never imply that a link contains unsaved edits |
| Runtime, header, or frame policy blocks startup | [JupyterLite](https://github.com/jupyterlite/jupyterlite/issues/1939), [Sandpack runtime](https://github.com/codesandbox/sandpack/issues/1290), [Sandpack frame headers](https://github.com/codesandbox/sandpack/issues/1272) | Test the production origin, headers, base path, and asset URLs, not only localhost |

## Gate result

Stage 2 identifies stable patterns and real disagreements rather than a product
to clone.

**Patterns to adopt:** latest-wins ids, a disposable Worker, explicit stale
state, persistent panel-owned diagnostics, a one-panel mobile mode, CodeMirror
as the lightweight baseline, staged cold-start feedback, reset and retry, and a
narrow result iframe policy.

**Patterns to reject:** toast-only tracebacks, stdout interpreted as HTML,
pointer-only splitters, an old preview that appears current, a Worker described
as security isolation, unversioned runtime assets, developer-console-only
errors, and automatic execution of shared code.

**Disagreements for Stage 3:** debounced autorun versus initial-auto plus
explicit rerun, and implicit final expression versus explicit `render(value)`.
These are meaningful product choices. The survey narrows the candidates but
does not settle them without a Citry runner prototype and first-reader test.

## Research limits

- Source inspection records implementation at the revisions in this document;
  hosted deployments can use other configuration.
- Official issue trackers overrepresent failures and do not establish how often
  a problem occurs.
- The products solve different jobs. JupyterLite and Shinylive are deliberately
  heavier than Citry's proposed single-module page, while Pyodide is only a
  runtime primitive.
- Accessibility conclusions are limited to documented behavior and obvious
  source semantics. They are not a substitute for keyboard, screen-reader,
  zoom, forced-colors, reduced-motion, touch, and mobile testing of Citry's
  implementation.
- Payload figures from Shinylive do not predict Citry's payload. Stage 1 and
  Stage 6 must measure the exact pinned Citry build.
- This product survey does not prove that Citry's compiled Rust binding can run
  in stock Pyodide. The separate Stage 1 record proves that result for its
  selected tuple and lists the browser-runtime gates that remain open.
