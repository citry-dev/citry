# Design: Citry docs playground

**Status (2026-08-05):** The playground is implemented at the
canonical, unversioned `/playground/` route. The shipped baseline includes the
mixed-language editor, pinned Pyodide runtime, Citry 0.3.1 and Citry Core 1.4.0,
final-expression execution, automatic and manual runs, isolated previews,
responsive layout, diagnostics, browser coverage, and the custom Events
transport for Data, Dispatch, Render, and signed State. Stage 9 reuses the
browser host for opt-in live examples. Deferred
hardening and rollout work is collected in the final appendix.

[`docs_site.md`](docs_site.md) remains the design and history of the docs-site
builder. [`docs_content.md`](docs_content.md) owns the documentation content
program. Dated research and prototypes live in
[`docs_playground_research/`](docs_playground_research/).

## Shipped baseline

### Reader experience

A visitor opens `/playground/` and sees a complete Citry Python module beside
its rendered result. The normal docs header remains. The docs sidebar,
breadcrumbs, prose column, table of contents, previous and next links, footer,
and version picker are absent so the workspace can fill the remaining
viewport.

Auto-run starts enabled. The starter renders as soon as the browser application
initializes, and an edit runs after a 500 ms idle delay. A saved explicit choice
to turn Auto-run off is respected. Run is always available as an immediate
action and through `Ctrl+Enter` or `Cmd+Enter`.

Run, Stop, Copy, Download, Reset, and Help are compact icon buttons with
accessible names and native tooltips. Stop remains visible and is disabled when
there is no active run. Reset restores the authored starter, disposes runtime
state, and lets the enabled Auto-run policy render it again.

On wide screens the workspace has two resizable panels:

```text
+-------------------------------------------------------------+
| Citry       Docs  Examples  Reference  Try it  Community    |
+-----------------------------+-------------------------------+
| Python module               | Rendered result               |
|                             |                               |
|                             |          iframe               |
|                             |                               |
+-----------------------------+-------------------------------+
```

On narrow or short screens, Code and Result tabs show one panel at a time.

### Page and navigation

The authored page is `docs_site/content/playground.md`. The top-level **Try it**
area in `docs_site/content/_nav.yml` points to `/playground/`.

The page uses `layout: playground`. Front matter accepts only known layout
values, and the guard rejects an unknown value. The build emits the playground
only at the site root. It never emits `/v/<version>/playground/`; historical
documentation may link to the canonical current playground instead.

The page loads its frontend and runtime files only for the playground layout.
Ordinary docs pages do not pay the CodeMirror or Pyodide cost.

### Editor and controls

The editor is CodeMirror 6, bundled from exactly pinned dependencies in the
private `docs_site/_internal/frontend` package. It uses the CodeMirror Python parser and
mixed official HTML, CSS, and JavaScript parsers for Citry's `template`, `css`,
and `js` class attributes. Lightweight decorations emphasize Citry component
names, Citry attributes, and `{{ ... }}` interpolation markers.

The editor follows the docs theme. Function definitions use a dedicated
high-contrast token in light and dark modes. Selection uses an explicitly
translucent overlay so selected syntax remains readable. Playground type is
slightly denser than narrative prose and matches ordinary docs code blocks and
controls. The preview shell starts at the docs site's 90 percent root density;
rendered HTML can override it with its own styles.

If CodeMirror construction fails after the application loads, the authored
textarea remains editable. The same Run, Copy, Download, Reset, and Help
controls continue to operate on it.

Copy places the complete module on the clipboard. Download produces
`citry_playground.py`. Reset restores the exact contents of
`docs_site/live_snippets/welcome.py`. Help is authored in
`docs_site/content/playground.md` and rendered with the shared docs prose
styles in a dialog. The dialog closes from its header icon, bottom action,
Escape key, or a click on the backdrop.

### Python execution contract

The editor contains one complete Python module. The executor parses it with
`ast`, preserves ordinary module semantics, and evaluates a final expression
separately. It does not prepend source text, so future imports, docstrings, and
traceback line numbers retain their normal meaning.

The final expression accepts:

| Value | Preview behavior |
| --- | --- |
| `str` or `Markup` | Use it as rendered HTML. |
| `CitryElement` | Serialize with `str(value)`. |
| `CitryRender` | Serialize with `value.serialize()`. |
| Missing or unsupported value | Return an actionable Python diagnostic. |

This keeps playground examples copyable as normal `.py` modules while giving
the concise final-value behavior readers expect from an interactive shell.
Explicit `print()` output is captured as stdout and shown in the left
diagnostic; it is never treated as preview HTML.

Each run executes in a fresh module namespace. The executor registers that
module in `sys.modules` and keeps its in-memory source in `linecache` for the
active run, matching imported-module introspection on Python 3.14 without
evaluating deferred annotations. It clears Citry-owned registries before reuse
and protects its internal result names from user-source collisions. Syntax,
runtime, Citry validation, normalization, stdout, and stderr information use
one structured result contract.

### Runtime loading and lifecycle

The browser data flow is:

```text
CodeMirror or textarea
  -> immediate Run or debounced Auto-run
  -> same-origin Web Worker
  -> pinned Pyodide CDN files and exact wheel URLs
  -> executor.py and a fresh Python module namespace
  -> normalized HTML result
  -> fresh sandboxed preview candidate
  -> atomic commit after preview acknowledgement
```

`docs_site/static/playground/runtime.json` is the runtime manifest. It pins:

- Pyodide 314.0.3;
- `citry==0.3.1`;
- `citry_core==1.4.0` using the published PyEmscripten wheel;
- exact compatible browser dependency URLs.

The Worker installs those exact files directly and verifies the imported Citry
and Citry Core versions. It does not ask a live resolver to select package
versions. Runtime initialization is lazy: it starts with the first automatic or
manual run rather than blocking the page shell. Each new Worker revalidates the
first-party runtime manifest and executor so a docs deployment does not reuse
an older browser-cached adapter with a newer Worker.

Citry 0.3.1 includes its generated Events browser runtime. The docs runtime
uses that package-owned file, keeping Python emission and client behavior on
one pinned release. The Citry 0.3.0 adapter that overwrote the installed
package's Events client was removed when the runtime advanced to 0.3.1.

The page keeps a successfully initialized Worker warm for subsequent ordinary
runs. Reset, an execution timeout, a Worker crash, a fatal initialization
failure, or Stop while Python is active terminates it. The next run creates a
fresh Worker and reloads the pinned runtime. Stop after Python has returned but
while a preview candidate is still loading discards only that candidate,
preserves the displayed result, and leaves the idle Worker warm. Python
execution has a five-second limit; runtime
preparation has its own bounded timeout.

Every Worker has a generation identity. Every run has an increasing id and the
source has an independent revision. Messages from retired Workers and inactive
run ids are ignored. A successful active run may commit after its source has
been edited, but the result stays visibly stale. If Auto-run is enabled, only
the newest pending source runs next and replaces it.

### Preview and diagnostics

Visitor HTML runs in an iframe with `sandbox="allow-forms allow-scripts"` and
no `allow-same-origin`. Browsers otherwise suppress the native `submit` event
before Citry's `@c-submit.prevent` listener can intercept it. The static
`preview.html` shell and its parent communicate through a private `MessagePort`
scoped by session, run id, and nonce.

Every accepted result starts in a fresh hidden candidate iframe. The candidate
parses the HTML, activates scripts, and acknowledges the result. Only then does
the host replace the displayed iframe. This gives each result a fresh
JavaScript realm, so timers, globals, listeners, promises, and prototype changes
from an older result cannot affect the next one. If candidate loading,
handshaking, or rendering fails, the previously displayed frame and its live
diagnostic channel remain intact.

Script activation recreates only browser-processed classic scripts, modules,
import maps, and speculation rules. Authored non-async external scripts are put
back into ordered mode and awaited through load or error. Before inserting
visitor HTML, the preview temporarily withholds Citry's ownership graph,
Events, and dependency JSON manifests. When the core manager activates, the
preview holds Alpine startup. After supported ordered executable activation
completes, it restores the exact original manifest nodes at their source
positions in one observer batch, lets the graph-linked dependency task attach
component and Events scopes, and releases Alpine in a `finally` block. Other
data-block scripts remain in place. This preserves manifest adjacency, lets the
installed Citry runtime process graph, Events, and dependency transactions in
its defined order, and avoids replaying a transaction by replacing an inert
manifest node.

Python errors belong to the Code panel. Client JavaScript, rejected promises,
resource failures, unexpected preview navigation, and preview protocol errors
belong to the Result panel. Diagnostics are persistent, copyable, dismissible,
inserted as text, size-limited, and announced through a live region. Their copy
and close actions use icon buttons with accessible names and native tooltips;
copy completion is announced. A successful preview commit clears diagnostics
from the retired frame and then shows only diagnostics produced by the accepted
candidate.

The last successful result remains visible while Python is running and when a
later Python run fails. A stale label explains that the displayed output does
not match current source.

### Responsive and accessible layout

The splitter supports pointer capture, touch, keyboard arrows, Home, End,
Enter, double-click reset, right-to-left direction, and persisted sizing. It is
an accessible vertical separator with a 30 to 70 percent range. The grid uses
the same range, so its announced value matches panel geometry.

At `56rem` width or `28rem` height, the interface switches to Code and Result
tabs. The same breakpoint is used by CSS and JavaScript. Tabs expose selected
state, keyboard movement, panel relationships, and focus behavior. Controls
have visible focus styles, icon-only buttons have accessible names, and status
changes use polite or assertive live regions according to urgency.

### Implementation ownership

| Responsibility | Current files |
| --- | --- |
| Authored page and navigation | `docs_site/content/playground.md`, `docs_site/content/_nav.yml` |
| Layout parsing and pipeline | `docs_site/_internal/frontmatter.py`, `docs_site/_internal/guards/frontmatter.py`, `docs_site/_internal/pipeline.py` |
| Shared page shell | `docs_site/_internal/components/doc_page.py` |
| Workspace markup | `docs_site/_internal/components/playground_workspace.py` |
| Page controller | `docs_site/_internal/frontend/src/playground.js` |
| Editor integration | `docs_site/_internal/frontend/src/citry_editor.js` |
| Worker lifecycle | `docs_site/_internal/frontend/src/worker_session.js` |
| Atomic preview lifecycle | `docs_site/_internal/frontend/src/preview_bridge.js` |
| Starter and runtime manifest | `docs_site/live_snippets/welcome.py`, `docs_site/static/playground/runtime.json` |
| Worker and Python executor | `docs_site/static/playground/worker.js`, `docs_site/static/playground/executor.py` |
| Preview shell and styles | `docs_site/static/playground/preview.html`, `docs_site/static/playground/playground.css` |
| Generated browser bundle | `docs_site/static/playground/playground.js` |
| Bundle generation check | `docs_site/_internal/frontend/scripts/build.mjs`, `scripts/check.py` |
| Browser coverage | `docs_site/tests/e2e/test_playground_e2e.py` |

The source modules are consumer-oriented rather than one monolithic page
implementation. Stage 9 can reuse the editor, Worker session, executor, and
preview bridge without embedding `PlaygroundWorkspace`. The page controller
and diagnostics are currently bound to the full-page workspace and need a
reusable host extraction as part of Stage 9.

### Baseline failure behavior

| Failure | Shipped behavior |
| --- | --- |
| Pyodide, wheel, or dependency cannot load | Name the preparation stage, stop the Worker, preserve source, and allow a fresh retry. |
| Source exceeds 64 KiB | Reject the run before posting it to the Worker and show the limit in the Code panel. |
| Python syntax, runtime, or Citry render error | Keep the prior result, mark it stale, and show line-aware details in the Code panel. |
| Missing or unsupported final value | Explain the accepted final-expression values. |
| Serialized result exceeds 2 MiB | Reject the result in the Worker, keep the prior result, and show the limit in the Code panel. |
| Infinite Python work | Terminate after five seconds and start a clean Worker on the next run. |
| Retired Worker or inactive run completes late | Ignore it without changing current status, HTML, or diagnostics. |
| Active run completes after its source was edited | Commit it as visibly stale; with Auto-run enabled, immediately follow it with only the newest queued source. |
| Stop during Python work | Terminate the active Worker generation and leave Stop disabled when idle. |
| Stop during preview work after Python returned | Discard the preview candidate while preserving the displayed result and the warm, idle Worker. |
| Preview candidate fails | Keep the prior iframe and its diagnostic channel; do not commit the candidate. |
| Preview JavaScript fails | Keep the rendered DOM and show the Result-panel diagnostic. |
| Preview navigates itself | Replace it with a clean shell and report the navigation fault. |
| Malformed, oversized, flooded, spoofed, or stale preview message | Ignore it according to protocol limits. |
| Program writes stdout or stderr | Show captured output details in the Code panel; never reinterpret it as HTML. |
| Stored settings are invalid | Restore Auto-run on and a 50 percent split, then clamp future values. |
| Unknown page layout or a versioned playground is requested | Fail a build or guard before deployment. |

### Verification

The implemented baseline is covered by:

- executor tests for final-expression transformation, supported values,
  tracebacks, future imports, semicolons, collisions, stdout, and stderr;
- front-matter, layout, navigation, root-only build, live-server, and static
  asset tests;
- a generated-bundle freshness check in the normal repository gate;
- Chromium, Firefox, and WebKit end-to-end runs using the published package
  bytes;
- browser regressions for Auto-run, Stop and fresh-Worker recovery, queued source,
  reset races, stale results, fresh preview realms, atomic preview failure and
  success, client diagnostics, syntax colors, selection opacity, splitter
  geometry, and compact tabs;
- the full repository Rust, Python, type-checking, frontend, coverage, and
  validator gate.

## Stage 8: Citry Events bridge

Stage 8 makes the main Citry interaction model available without asking
playground authors to construct an application or server framework.

### Selected transport model

Use Citry's custom transport abstraction rather than overriding global `fetch`
or pretending to host WSGI or ASGI:

```text
preview Citry client
  -> registerTransport("playground", {send})
  -> generation-scoped outer bridge message
     containing an unchanged Citry call envelope
  -> preview MessagePort and docs host
  -> live Python Worker generation
  -> EventsDispatcher.dispatch(envelope, context, request=synthetic_request)
  -> validated action response
  -> preview Citry client
```

The browser adapter constructs a synthetic `EventRequest` containing the path,
method, headers, and body needed by Citry's event contract. Its
`TransportContext` identifies `transport="playground"` and uses the current
generation's Citry engine. It must not claim authentication, session,
middleware, CSRF, upload, arbitrary route, or framework behavior that the
browser host does not provide.

A broad `fetch` override is the wrong boundary. It would affect unrelated user
code, miss non-fetch resource loading, and suggest more HTTP compatibility than
exists. The Citry client already has the narrower extension point.

### Generation lifecycle

The Worker, module namespace, component registry, Citry engine, and dispatcher
remain alive for the displayed rendered generation. Source rerun, Reset, Stop,
timeout, crash, or eviction invalidates every pending event id before disposing
that generation. Code and Result tab switches preserve it.

Every outer bridge message needs consumer, Worker generation, render
generation, event id, and payload limits. Its nested Citry call envelope
remains the closed protocol record accepted by the dispatcher; bridge metadata
must not be added to that envelope. A response for an older render must never
update current DOM or Python state.

The default Citry engine exists only inside the disposable Worker. The executor
configures it with a per-Worker random secret and disables autodiscovery before
visitor code runs. This gives ordinary `from citry import Component` classes
zero-boilerplate signed State without changing the visitor's source text or
sharing a process-global engine with another visitor.

### Initial capability target

| Capability | Implemented Stage 8 behavior |
| --- | --- |
| Data | Supported through the normal Citry result envelope. |
| Dispatch | Supported through the normal Citry action applier. |
| State and two-way bindings | Supported with per-Worker signing, token refresh, cross-generation rejection, and cleanup. Signed tokens are not single-use within one live generation. |
| Render actions | Supported. The preview resolves Citry-owned JavaScript and CSS through the active Python Worker before applying the action. |
| Synchronous handlers | Supported with a five-second event limit. |
| Async handlers | Rejected by the synchronous dispatcher until a browser-safe event-loop policy is selected. |
| Redirect and URL or history actions | Rejected explicitly. |
| Download and raw route responses | Rejected explicitly. |
| Host authentication, sessions, CSRF, middleware, uploads, and arbitrary routes | Do not simulate. |

The Python executor inside the Worker applies its fixed supported-action policy
before the preview client can apply a response. Unsupported behavior fails with
an actionable Result-panel diagnostic rather than silently approximating a
server.

### Stage 8 proof and gate

The lower-level proof covers Data, Dispatch, Render, signed State token refresh,
the synthetic request contract, and unsupported action rejection. The browser
gate uses the published wheels in Chromium, Firefox, and WebKit and covers the
starter's live State and Dispatch round trip, a Data promise, rendered
fragments with JavaScript, CSS, nested State and Events, handler errors, reruns,
reset, Stop, fresh Worker recovery, and iframe generation isolation.

### Render asset protocol

Citry keeps its normal dependency manifests and stable logical asset paths.
The preview extracts new Citry asset paths from an initial document or Render
action, then asks the active Worker generation to resolve a bounded batch. The
Python executor accepts only Citry's named JavaScript and CSS routes under the
playground-owned prefix. It does not expose visitor-defined routes or a general
HTTP adapter.

The preview converts returned UTF-8 JavaScript and CSS into stable Blob URLs
scoped to that iframe. It reuses each Blob URL for later fragments. JavaScript
and persistent CSS already emitted by the initial document remain recorded
under their logical Citry paths, so a later Render action does not execute them
again. Citry may collect class CSS after its last instance leaves; the preview
then resolves that class sheet once so a later instance is styled again.

All Render actions in one event response are prepared before Citry applies any
of them. If any required asset is missing, invalid, stale, oversized, or times
out, the whole event fails and the existing DOM remains unchanged. Stop can
cancel asset preparation for a candidate result while that run is active.
Reset, a newer run, and Worker replacement cancel every pending asset request;
iframe replacement makes a late response inert. Event-triggered asset requests
otherwise use their bounded timeout because Stop is disabled after a run has
finished. The iframe request ID and Worker request ID are deliberately
separate, and both sides validate the current run and preview identity.

The accepted subset works without textual source mutation, HTTP-framework
impersonation, state crossover, or stale-generation updates. Pending events are
bounded and rejected when their Worker or preview retires; a hung synchronous
handler terminates its Worker after five seconds.

## Stage 9: reuse the browser host for opt-in inline examples

Stage 9 makes eligible examples in Docs and Examples editable without turning
every documentation page into an application by default.

### Authoring contract

Use an explicit path-backed Citry tag, for example:

```html
<c-live-code
  path="docs_site/live_snippets/welcome.py"
  title="Welcome card"
/>
```

Add the value-less `full_height` kwarg when the static source should contribute
its complete height to the page:

```html
<c-live-code
  path="docs_site/live_snippets/welcome.py"
  title="Welcome card"
  full_height
/>
```

The default static block remains capped at 32rem. `full_height` removes that
cap for the selected block while preserving horizontal scrolling and the
bounded Code and Result panels after activation.

Each source is one complete UTF-8 Python module anywhere under `docs_site/`.
`docs_site/live_snippets/` remains the convention for reusable reader-facing
modules, not a hard boundary. The builder reads and highlights the source but
never imports it. The source guard rejects path traversal, files outside
`docs_site/` including symlink escapes, missing files, invalid UTF-8, excessive
size, blank titles, syntax errors, unsupported imports, and top-level await. It
also requires LF line endings so the highlighted DOM remains the byte-exact
source loaded into the editor. A module without a final preview value remains a
valid static example. When a reader activates it, auto-run reports the missing
value in the editor, and a later edit can add the value and render successfully.
Diagnostics from source guards name the Markdown source and directive line.
Source guards run before rendering, so a bad directive cannot fail first with a
component-schema traceback.

A source file is preferable to wrapping a Markdown fence. The existing docs
pipeline protects fences before Citry components run, while path-backed source
already has precedent in include and example components. It also provides one
canonical copy that tests and projections can consume.

### Static-first interaction

The default is a normal Citry-aware Pygments block. A 1.7 KiB activator adds
**Try live**. CodeMirror, Pyodide, wheels, Worker code, and preview load only
after activation. Markdown, Pagefind, and LLM projections contain the source,
not live controls or runtime state.

The narrow narrative column uses one panel at a time with accessible Code and
Result tabs. Activation preserves the exact authored source. Run and Stop stay
available above both panels. Auto-run starts enabled. Reset restores the
authored module in a new Worker and preview generation. Activation, Auto-run,
Run, and Reset preserve the reader's selected Code or Result tab. A render
never moves the reader to Result without an explicit tab action. Close disposes
the editor, Worker, pending Events calls, preview ports, and iframe before
restoring the static block and focus. Editing marks the last successful result
as stale and disables its Events bridge until current code renders
successfully. Status is visible once in the toolbar and repeated through a
visually clipped live region for assistive technology.

The document coordinator allows one active inline runtime. Each activation has
independent Worker, preview, run, and operation identities. Closing or replacing
a dirty block stores an in-memory draft, labels it **Draft saved**, and
offers **Resume live**. Reset clears that draft. Activation failure leaves the
static source usable and offers **Retry live** with a fresh module request.

Historical `/v/<version>/` pages stay static-only. They may link to the current
`/playground/` with copy that clearly identifies it as the current pinned Citry
version.

### Implementation and proof

`LiveCode` owns the static component markup. The render-scoped context records
static styling and interactive activation separately. Historical builds load
the live-code stylesheet but omit the activation script. `live_code.js` is the
small document coordinator, while `live_code_runtime.js` is the deferred
consumer of the shared Citry editor, Worker session, executor, and preview
bridge. Pages without live tags emit neither asset. The Worker and Events wire
protocols are the same ones accepted by the full-page playground.

The first opted-in module is `docs_site/live_snippets/welcome.py` on the Examples
overview. That same module is the full-page starter and demonstrates State plus
a Python Events handler, so the two learning surfaces cannot drift.

The first selective content rollout also replaces compatible self-contained
fences with canonical modules in `docs_site/live_snippets/`:

- the small example on the Docs overview;
- the reading list and slots lessons;
- the component-owned JavaScript example; and
- the reactive parent and child lesson immediately before FastAPI.

These are useful in place because a reader can observe the concept without
leaving its explanation. Each module remains runnable from a normal Python
shell: its `__main__` block prints the example, while its final expression
provides the browser preview. Installation remains a local-environment check,
so running it in Pyodide would teach the wrong success condition. The Card and
composed ReadingPage lessons remain multi-file on purpose. Flattening either
would duplicate source or contradict the import lesson.

The existing recipe pages also remain unchanged. Their `<c-example>` views
already combine multiple source files with a hosted result, and a second
single-file editor would duplicate those sources. A later editable mode inside
`<c-example>` is a better extension. The Fragments recipe additionally depends
on hosted routes and assets that the inline browser runtime does not model.

The live authoring server also adds a universal workspace Citry UI wheel to
the committed Citry and Citry Core runtime. Keeping the released framework
tuple makes component docs a compatibility check against their supported
floor, while the library itself remains editable. The published Citry wheel
supplies its matching Events client. The local manifest verifies Citry, Citry
Core, and Citry UI as one compatible tuple. This capability is explicit in the
page render context, so local interactive snippets may import
`citry_ui`. Component snippets marked `static` for publication gain local
activation controls automatically. Static builds, guards, `serve-built`, CI,
and deployment keep the committed published runtime and import allowlist.

The earlier plain-Alpine Disclosure lesson was not made live. Browser
validation showed that the pinned runtime tuple preserves its Alpine
attributes but does not emit the owned runtime without another client-graph
trigger, so the standalone lesson did not work as written. The public journey
now starts with the component-owned JavaScript example. Automatic plain-Alpine
activation remains owned by the separate
[`alpine_activation_plan.md`](alpine_activation_plan.md).

Unit coverage includes exact source recovery, zero and multiple tags, unique
tab relationships, historical static-only rendering, text projection, every
authoring boundary, and directive-line diagnostics outside code regions.
Playwright coverage includes the no-JavaScript view, pre-activation request
boundary, the real pinned Pyodide and wheel path, State and Dispatch, activation
failure and retry, dirty close and replacement, draft resume, Reset, focus
restoration, rapid competing activations, stale-result signaling, and the
one-active-runtime rule. Chromium, Firefox, and WebKit run the inline suite; the
existing full-page browser suite remains a regression gate.

Stage 9 is accepted without page-wide runtime cost, cross-example state,
executable source duplication, silent draft loss, or documentation-version
drift. Physical-device, long-session, and deeper assistive-technology rollout
remain in the deferred appendix.

## Appendix: deferred hardening, rollout, and optional additions

The baseline is a minor learning feature on a static, unauthenticated site. It
runs the built-in example and code typed locally by the visitor. The following
work is intentionally outside the shipped baseline and stages 8 and 9.

### Revisit triggers

Reopen containment and artifact delivery before the playground:

- loads shared, URL-provided, or remotely stored user code automatically;
- runs on a site with accounts, private data, credentials, or state-changing
  endpoints;
- shares one runtime across visitors or documents;
- gains enough use that the accepted operational risk is no longer
  proportionate;
- cannot meet support or reliability goals with public CDN and PyPI delivery.

### Stronger runtime isolation

A hardened topology can move Python execution to a credential-free,
different-site runner page that owns the Worker and brokers a strict protocol
to the docs page. That design needs a separately deployed origin, explicit CSP
and permissions policy, production cookie and storage probes, request and
message limits, rollback ownership, and a real failure UI for runner outages.

The current same-origin Worker is not a security sandbox. Pyodide Python can use
Worker network and storage capabilities. The opaque preview blocks direct
same-origin DOM access but does not by itself prevent every network request,
self-navigation attempt, download activation, CPU loop, or URL log entry.
Future isolation work must test those capabilities rather than claiming that
iframe sandbox flags solve them.

The preview grants `allow-forms` because browsers otherwise suppress native
`submit` events before `@c-submit.prevent` can intercept them. An unhandled form
can therefore issue a request and navigate its iframe before the preview bridge
restores it. Later hardening can test a `form-action 'none'` CSP across Chromium,
Firefox, and WebKit, but it must preserve cancelable submit delivery to Citry.

### Mirrored and verified runtime artifacts

The shipped runtime fetches pinned Pyodide and exact wheel URLs from public
CDN and PyPI hosts. A later reliability or supply-chain program can mirror
those files under project control, verify hashes in the browser, publish a
content-addressed manifest, retain every referenced runtime generation, and
promote assets before referring HTML.

That program also needs deterministic native, source, and PyEmscripten wheel
assembly before a release is published. It is not required to serve the small
first-party JSON, HTML, Python, CSS, and JavaScript files, which already use the
normal docs static-file path.

### Release and rollback automation

Potential release work includes:

- permanent PyEmscripten wheel jobs in the normal Citry Core release workflow;
- tuple compatibility checks for Python, Pyodide, Emscripten, Citry, and Citry
  Core;
- immutable runtime manifests and retained rollback generations;
- deployment ordering checks and production smoke tests;
- repository and PyPI environment policies beyond the current sole-developer
  setup.

### Events transport extensions

Potential later additions include a browser-safe asynchronous dispatcher
boundary and longer-run heap-growth and idle-resource measurement. Redirect,
history, download, raw route-response, upload, authentication, session,
middleware, and arbitrary-route behavior remains intentionally outside the
playground transport.

### Preview delivery extensions

Current Citry output uses inline classic scripts. The preview also preserves
authored order for non-async external scripts. Inline module completion and a
broader module matrix still need explicit activation barriers and browser
coverage for evaluation, top-level await, and failure ordering. Authored
`async` scripts remain intentionally outside the ordered barrier.

The document detector currently requires a doctype or `<html>` start. A Citry
component that wraps a complete document places an ownership-cap comment before
its doctype and therefore follows the fragment path. Supporting document-level
`html` and `body` attributes in that form also requires preserving the outer
ownership comments that `DOMParser` does not place inside the extracted head or
body. This can be added with a dedicated parser-delivery contract and tests.

### Published Citry UI runtime

Local authoring already builds the workspace Citry UI wheel against the pinned
published Citry runtime so component examples can be tested before
publication. Once `citry-ui` is published as a
universal pure-Python wheel compatible with
the playground's pinned Citry, Citry Core, and Pyodide tuple, the playground
and live-component Worker should include it by default. This is a pinned
runtime capability, not an unconstrained package installer:

1. Add the exact `citry-ui` version and wheel URL to `runtime.json`, load it
   with the existing package sequence, and verify
   `importlib.metadata.version("citry-ui")` alongside Citry and Citry Core.
2. Allow `citry_ui` imports in authored live-code modules.
3. After every `citry.clear()`, import `citry_ui` and call
   `citry.register_library(citry_ui)`. Clearing Citry removes the installed
   library classes, so registration must happen for every run rather than only
   during Worker startup.
4. Extend final-expression normalization to accept a Citry `ComponentLike`
   and resolve it against the Worker's exact Citry instance. This makes a final
   expression such as `CButton(content="Save")` work as naturally as direct
   `<c-CButton>` use inside an authored component.
5. Keep component CSS and JavaScript on Citry's ordinary dependency path so
   direct invocations and registered template tags activate the same assets.

The browser suite must cover a direct `citry_ui` import, final-expression
composition, registered `C*` tags, library assets, and two consecutive runs.
The second run is essential because it proves registration after `clear()`.
Live-code validation must accept `citry_ui` without broadening the import
allowlist to arbitrary packages.

A missing, incompatible, or incorrectly versioned wheel is a Worker runtime
initialization failure with the normal Retry action. A registration or render
failure is reported for that run and must not replace the last successful
preview. The runtime manifest, worker version checks, library registration,
allowed imports, and browser tests land together so the docs never advertise a
partially available built-in library.

### Production, device, and accessibility rollout

Additional rollout evidence may include uncached and throttled network timing,
physical mobile browsers, soft keyboards, memory growth over long sessions,
Lighthouse checks, assistive-technology sessions, production-origin cookie and
storage probes, and CSP reporting. The current automated matrix covers desktop
Chromium, Firefox, and WebKit plus responsive viewport behavior.

### Optional product additions

The baseline does not include shareable URLs, source history, presets,
formatting, a full stdout console, collaborative storage, automatic remote-code
loading, or a toast layer in addition to persistent diagnostics. Each can be
designed if reader behavior shows that it improves the learning task enough to
justify its lifecycle and security surface.
