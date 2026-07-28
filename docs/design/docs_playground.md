# Design: Citry docs playground

**Status (2026-07-28): Research in progress. Stages 0, 2, 3, 4, and 5 are
complete; Stage 1 is partially complete. The binding, released-package,
cross-browser Pyodide Worker, combined cross-origin Pyodide broker,
termination, protocol-limit, preview-recovery, and desktop preview-isolation
proofs passed. Deterministic local wheel builds, a single sealed historical
package manifest with no resolver or live fetch, and two cached-desktop
performance repetitions also passed. The preview matrix confirmed that iframe
sandboxing alone does not contain network access, credentials,
self-navigation, downloads, or message floods. Physical-mobile and uncached
network performance, release-CI integration, a production-origin test, the
exact Citry 0.3.0 acceptance run, Stages 6 and 7, and the final
implementation plan remain open.**

This document plans a top-level **Try it** area for the Citry documentation
site. The area will contain one browser playground where a visitor edits a
single Python module and sees its rendered HTML in an isolated iframe.

The plan is deliberately research-first. The largest uncertainty is not the
two-panel interface. It is whether the current Rust-backed Python package can
be built, distributed, and run reliably inside a browser Python runtime. The
editor, execution contract, starter example, error presentation, asset
delivery, and page architecture should be chosen after evidence narrows those
questions.

[`docs_site.md`](docs_site.md) remains the design and history of the docs-site
builder. [`docs_content.md`](docs_content.md) controls the user-documentation
content program. Repository operating and writing rules remain owned by
[`CLAUDE.md`](../../CLAUDE.md).

## Intended outcome

A visitor can open `/playground/`, change a self-contained Citry component,
and see the latest successful HTML result without installing Python or Citry
locally.

On a wide screen, the page keeps the documentation header and replaces the
ordinary sidebar, prose column, and table of contents with a workspace that
fills the remaining viewport:

```text
+-------------------------------------------------------------+
| Citry       Docs  Examples  Reference  Try it  Community    |
+-----------------------------+-------------------------------+
| Python module               | Rendered result               |
|                             |                               |
|                             |          iframe               |
|                             |                               |
|                             |                               |
+-----------------------------+-------------------------------+
```

The middle separator is draggable, touch-operable, and keyboard-operable. On
narrow or short screens, the accepted Stage 4 pattern shows one panel at a
time with explicit Code and Result controls instead of forcing two unreadably
narrow columns.

The expected data flow is:

```text
editor
  -> immediate Run or debounced Auto-run request with an increasing id
  -> cross-origin runner page and validated message broker
  -> disposable same-origin Web Worker running pinned Pyodide and Citry
  -> accepted final value normalized to HTML
  -> sandboxed iframe srcdoc

Python failure -> persistent diagnostic in the editor panel
iframe failure -> persistent diagnostic in the result panel
```

## Why research comes first

The released browser path does not exist today. Published `citry==0.2.0` is
pure Python, but its release metadata declares `citry-core>=1.3.0`. The
resolver can therefore install the newer, incompatible `citry-core==1.4.0`.
The repository has since changed that dependency to an exact
`citry-core==1.4.0` pin, but that correction is not part of the published
0.2.0 artifact. The source manifest still reports version 0.2.0, so 0.3.0 is a
planned release rather than an existing package pair. That release is intended
to provide the compatible public-package pair.

An isolated resolution probe on 2026-07-28 confirmed that installing
`citry==0.2.0` selects `citry-core==1.4.0`. Import and a basic component still
work, so the pair is not universally unusable, but the new core contract can
break the old runtime. Rendering a component tag with `#c-key` fails with
`ComponentNode.__init__() takes 8 positional arguments but 9 were given`.
That is sufficient to exclude this mixed release pair from the playground
proof.

`citry_core` is a mixed Python/Rust package whose `citry_core._rust` module is
built as a native PyO3 extension
(`packages/py/citry_core/pyproject.toml:1-8,46-58` and
`crates/citry_core_py/Cargo.toml:8-16`). Current release automation publishes
native operating-system wheels, not a Pyodide/Emscripten wheel.

Citry needs the complete Rust extension during an ordinary render:

- the parser and compiler turn the template into Python runtime nodes;
- safe evaluation transforms expressions;
- the HTML transformer participates in serialization.

A parser-only browser port would therefore not prove that the playground can
render real Citry components. The first blocking experiment must build and run
the existing PyO3 extension against Pyodide's Emscripten target. Until
`citry==0.3.0` is published, that experiment should exercise parsing,
compilation, safe evaluation, and HTML marking through `citry_core` directly.
It can also exercise the complete released public package by pinning the
historically compatible `citry==0.2.0` and `citry-core==1.3.0` pair explicitly.
The exact published 0.3.0 pair remains the acceptance target for the current
playground.

The current answer to "can Pyodide install the precompiled Rust bindings?" is:

- **Existing native wheels: no.** They target CPython on desktop/server
  operating systems, not the browser.
- **A separately built Pyodide/Emscripten wheel of the same PyO3 binding:
  proven for the selected tuple.** Core 1.3.0 and 1.4.0 built and imported in
  stock Pyodide 314.0.3. The binding rewrite fallback is no longer the next
  path.
- **Published `citry==0.2.0` through live dependency resolution: no.** Its
  open-ended core dependency currently permits an incompatible pair. An exact
  manifest may still use 0.2.0 with the compatible 1.3.0 core as a historical
  public-package proof. Use `citry_core==1.4.0` directly for the future-package
  binding proof, then run the acceptance matrix again after 0.3.0 is
  published.

The WebAssembly build should be another platform wheel in the existing
`citry-core` PyPI project, not a separate package. Its platform tag lets native
`pip` ignore it and lets matching Pyodide installers select it. Although PyPI
would technically allow the unique wheel to be appended to the one-day-old
1.4.0 release during its current 14-day file-addition window, the recommended
release plan is `citry-core==1.4.1` with all native, source, and PyEmscripten
artifacts assembled and tested before one publishing job. Citry 0.3.0 should
then exactly pin 1.4.1. See
[`runtime_feasibility.md`](docs_playground_research/runtime_feasibility.md#distribution-and-release-policy)
for the dated packaging evidence and the required CI changes.

## Local prior art and confirmed constraints

These findings come from the current working tree. They are evidence for the
research plan, not final product choices.

### Navigation and page generation

`docs_site/content/_nav.yml` is the single source for the primary navigation.
Each top-level area becomes a header link in declaration order, and its first
page becomes the link target (`docs_site/README.md:31-64` and
`docs_site/_internal/nav.py:52-69`). A one-page area can therefore be declared
as **Try it** with one `/playground/` item.

The page should have an authored `docs_site/content/playground.md` source. The
static builder and live server already discover Markdown pages, and the nav
guard expects authored nav items to resolve to real pages
(`docs_site/_internal/build.py:165-205`,
`docs_site/_internal/serve.py:65-88`, and
`docs_site/_internal/guards/nav.py:43-76`). A special route without a content
source would fight those conventions and weaken the Markdown and LLM
projections.

Under the current path mapper, that source yields public `/playground/`, static
`playground/index.html`, and Markdown companion `playground/index.md`. The
source and nav entry do not exist yet. They should land together because nav
first fails the missing-page guard while page first is temporarily orphaned.

### Page layout

Every authored page currently goes through one three-pass pipeline and ends in
the monolithic `DocPage` component
(`docs_site/_internal/pipeline.py:202-311`). `DocPage` always owns the head,
fixed header, sidebar, prose article, page navigation, footer, and right table
of contents (`docs_site/_internal/components/doc_page.py:46-88,589-940`).
There is no full-width page mode.

`wrap_in_layout=False` is not that mode. It removes the entire document
wrapper, including the header. The eventual implementation therefore needs an
explicit page layout type and a first-class playground page component. The
preferred hypothesis is to extract the shared document head and header into
reusable components, leave `DocPage` responsible for narrative documentation,
and add a `PlaygroundPage` responsible for the workspace. A smaller conditional
branch inside `DocPage` remains an alternative to evaluate.

The current front matter does not have a layout field. `PageMeta` recognizes
only title, description, canonical URL, indexing and search controls, and the
Open Graph image (`docs_site/_internal/frontmatter.py:47-83`). If research
selects `layout: playground`, the field must accept a closed set of values and
reject an unknown value with the source path and bad value. It must not silently
fall back to the ordinary layout.

The playground component should render as a direct child of the final page
component. Rendering it during the Markdown Citry pass would place its CSS and
JavaScript inside the article and would leak the application markup into the
Markdown companions and LLM exports.

### Responsive header and navigation

On screens below 768 pixels, the desktop primary navigation disappears. The
mobile primary links live inside the sidebar drawer
(`docs_site/_internal/components/doc_page.py:589-600` and
`docs_site/static/css/site.css:1585-1638`). Removing the sidebar without a
replacement would also remove mobile navigation. The playground page must
retain a primary-navigation drawer or supply an equivalent small-screen header
control.

Adding another header link also increases pressure at narrow desktop widths.
The current browser regression checks 769, 800, 900, and 1024 pixels
(`docs_site/tests/e2e/test_docs_e2e.py:115-126`). Blog and UI Kit are already
planned as later top-level areas, so the research must test the likely future
link count as well as the fifth link added now.

### Existing splitter and iframe code

The ordinary docs shell already has draggable sidebar and table-of-contents
handles. Their JavaScript uses mouse events, clamps fixed pixel widths, and
stores them under `djc-panel-widths`
(`docs_site/static/js/site.js:465-529`). The handles are useful visual prior
art, but they have no keyboard or touch contract. The playground splitter must
use Pointer Events, pointer capture, an accessible separator role and values,
keyboard sizing and reset controls, and a playground-specific stored value.

Existing example cards also use iframes, but their content is trusted and the
iframe receives both `allow-scripts` and `allow-same-origin`
(`docs_site/_internal/components/example_card.py:153-159`). Visitor-authored
HTML must not reuse that policy. The initial security hypothesis is an opaque
origin iframe with `sandbox="allow-scripts"` and no same-origin permission.

### Citry highlighting already exists

The `pygments-citry==0.1.0` package is already implemented and loaded by the
docs build. The older pending note in `docs_site.md` is stale.

`CitryPythonLexer` highlights Python and delegates the bodies of triple-quoted
`template`, `js`, and `css` assignments to Citry HTML, JavaScript, and CSS
lexers (`packages/py/pygments_citry/pygments_citry/lexers.py:1-15,49-78`).
`CitryHtmlLexer` also recognizes Citry tags, interpolations, dynamic Python
attributes, JavaScript-valued client props, and raw blocks
(`packages/py/pygments_citry/pygments_citry/citry_html.py:1-13,130-194`).

This is a strong language specification and conformance corpus, but Pygments is
a batch highlighter, not a browser editor grammar. Replacing editable HTML on
each keystroke would not provide a credible editor. Research must determine
whether the selected editor can express the same nested-language regions and
how to share fixtures or generated rules so its behavior does not drift from
`pygments-citry`.

### Renderable return types

Citry already defines the normalization behavior needed by a final-expression
contract:

- `str(CitryElement)` runs render then serialize
  (`packages/py/citry/citry/citry_element.py:127-157`);
- `CitryRender.serialize()` and `str(CitryRender)` produce the final HTML
  (`packages/py/citry/citry/citry_render.py:183-230`).

Repeated execution has one additional constraint. Component classes register
when Python defines them, and a repeated class name collides in a reused
interpreter. `citry.clear()` removes Citry's registrations, class-id lookup,
caches, file indexes, libraries, and tag rules
(`packages/py/citry/citry/citry.py:1530-1562`). A run must use a fresh module
namespace and a clean Citry registry. This cleanup is partial: it does not
reset `sys.modules`, builtins, the in-memory filesystem, JavaScript globals,
class objects that remain referenced, or arbitrary module side effects. A
Worker must remain disposable because those effects cannot all be rolled back
and a blocked Python loop cannot call `clear()`.

### The step 9 tutorial is not a starter playground module

`components_step9.py` is not self-contained. It imports a separately configured
Citry instance and Events actions, binds components to that external instance,
defines server event behavior, and has no final render expression
(`docs_site/snippets/getting_started/components_step9.py:1-5,43-60,116-139`).
It teaches a later server-and-browser stage of the tutorial, not the smallest
browser-only success.

The starter hypothesis is a shorter, self-contained component derived from the
accepted first-component or Card journey. It should demonstrate a typed input,
Python data preparation, a visible template expression, small component CSS,
and a final component expression. A more advanced preset can later demonstrate
composition or client JavaScript after its payload and runtime cost are
measured.

## Product goals

- Let a first-time visitor change a real Citry component and see a visible
  result quickly.
- Execute the supported Citry Python package rather than a simplified template
  imitation.
- Keep all visitor Python execution out of Citry's servers.
- Keep Python execution off the browser main thread.
- Preserve the last successful result while a newer run is pending or fails,
  and make stale state explicit.
- Keep Python and rendered-document errors near the panel that owns them.
- Support keyboard, pointer, touch, zoom, narrow viewports, light/dark/automatic
  themes, reduced motion, and forced colors.
- Pin every runtime artifact to an exact compatible set and make drift fail the
  build or release check.
- Keep the page useful in generated Markdown, search, SEO, and LLM outputs
  without projecting the whole interactive application into those formats.
- Build the browser-hosted Citry runtime as a reusable subsystem. The full-page
  playground is its first consumer; later opt-in live examples must be able to
  use the same loader, runner, editor, preview, lifecycle, and diagnostics
  contracts without embedding the playground layout.

## Initial non-goals

These remain outside the first implementation unless research shows that one
is necessary for the core learning job:

- multiple editable files or a virtual project tree;
- arbitrary third-party package installation;
- a terminal, debugger, language server, or complete notebook;
- accounts, collaborative editing, or server persistence;
- a server-side code runner;
- Citry Events and host-framework simulation in the baseline render-only
  implementation; Events are an explicit follow-on after that baseline works;
- publishing user code or loading untrusted code automatically from a shared
  URL;
- claiming offline support before the asset and cache design proves it;
- supporting historical docs versions with the current playground runtime by
  accident.

Shareable links, presets, console output, formatting, download, and reset are
research candidates, not assumed v1 scope.

## Reusable browser-host architecture

The browser runtime is a product capability, not a page-specific script. Its
consumer-neutral core should own:

- loading and verifying the exact runtime manifest;
- connecting to the credential-free runner and creating, stopping, and
  disposing runtime sessions;
- consumer, session, generation, and run identifiers, including stale-result
  rejection, timeouts, message size/rate limits, and diagnostics;
- AST execution and accepted-value normalization;
- the CodeMirror editor plus Citry language package;
- opaque preview creation, replacement, and client-error reporting;
- the optional Events transport added after baseline rendering;
- a page-level scheduler for the number and lifecycle of active sessions.

The core API should accept source, artifact manifest, consumer id, session id,
generation, run id, and declared capabilities. It must not depend on the
`/playground/` path, splitter markup, fixed DOM ids, or playground storage
keys. Consumer-specific UI remains outside it:

```text
Browser Citry host
  -> PlaygroundWorkspace: full-height Code | Result workspace
  -> InlineLiveCode: opt-in, one-panel Code / Result documentation block
```

One hidden broker page may be shared by one documentation document, but Python
interpreters, Citry registries, event generations, and user drafts must not be
silently shared across consumers. This boundary is a Stage 5 deliverable so
the playground does not accumulate assumptions that later have to be removed
for inline examples.

## Provisional interaction contract

This section records hypotheses to test. It does not settle the product
contract.

### Security boundaries to prove

A Web Worker keeps expensive Python work off the UI thread, but it is not a
sandbox. Pyodide Python can reach JavaScript objects exposed in the Worker and
may be able to call `fetch`, send or flood messages, close the Worker, mutate
JavaScript globals, and use other browser capabilities available there. The
local evidence selects a dedicated credential-free runner origin with a
restrictive network policy. Stage 1 must still prove that deployment on the
real origin preserves that boundary and state the residual capabilities
available to visitor Python. V1 explicitly runs only the built-in trusted
starter or code edited locally by the visitor and makes no claim that arbitrary
Python lacks every network or resource capability.

Hosting only the Worker script or runtime assets on another origin does not
move this boundary. A Worker entry URL must be same-origin with its creator,
and a blob Worker inherits its creator's origin. The current containment
choice is therefore a runner page served from a dedicated credential-free
origin. That cross-origin page owns a Worker from its own origin and brokers a
strict, rate-limited protocol with the docs page. Its iframe retains
same-origin access to its own credential-free origin without gaining access to
the cross-origin documentation parent. A local three-browser proof accepted
the topology and minimum message flow. A production-origin deployment test is
still required because loopback hostnames do not prove real domain, cookie,
CSP, cache, or hosting behavior.

The iframe sandbox is also only one layer. `sandbox="allow-scripts"` blocks
same-origin parent access, but it does not by itself block network requests or
data exfiltration. In the desktop matrix, WebKit 26.5 attached the docs test
cookie to same-origin image, download, and self-navigation requests from the
opaque preview while Chromium 149 and Firefox 151 did not. The result iframe
must therefore load only credential-free resources under a restrictive
network policy. No browser-specific cookie observation may be treated as the
security boundary.

The initial release must not load shared or URL-provided user code
automatically. That non-goal reduces exposure but does not remove the need to
test Worker and iframe capabilities.

### Running code

The run-control shape was accepted on 2026-07-28 as a hybrid: the workspace
always shows an explicit **Run** button and also exposes an **Auto-run** toggle.
The toggle controls debounced execution after edits; it never replaces or
hides the explicit action. Its initial default, debounce interval, persistence,
and pause behavior remain Stage 5 specification candidates and Stage 6
evidence gates.

The candidate lifecycle is:

1. The Run button and `Ctrl+Enter` or `Cmd+Enter` run immediately.
2. When Auto-run is enabled, the editor emits a run after an idle debounce.
3. Each run has an increasing id. A late result from an older run is ignored.
4. A reused Worker clears known Citry-owned state and executes in a fresh module
   namespace. Warm reuse remains a performance hypothesis, not a security or
   determinism guarantee.
5. A timeout terminates the Worker. The next run starts a fresh Worker and
   reloads the pinned runtime.
6. The previous successful iframe stays visible while a run is pending or
   fails, with a clear "showing previous result" state.

Stage 5 must specify testable Auto-run candidates, persistence and failure
rules, and their measurement hooks. Stage 6 must approve or replace those
defaults using browser performance and first-reader evidence. Cold start must
retain only the newest requested source rather than queueing every edit.

### Choosing the preview value

Ordinary Python module execution with `exec()` has no last value. Notebook and
interactive-shell behavior can be implemented by parsing the module with
`ast` and, when the last statement is an `ast.Expr`, replacing it with an
assignment to a collision-safe private result name. Compile that modified tree
once with `ast.copy_location` so future imports, compiler flags, source
positions, and traceback lines keep ordinary module semantics. Research must
explicitly support or reject top-level await.

The candidate accepted values are:

| Final value | Candidate behavior |
| --- | --- |
| `str` or `Markup` | Use as preview HTML. |
| `CitryElement` | Render and serialize with `str(value)`. |
| `CitryRender` | Serialize with `value.serialize()`. |
| No final expression | Show an actionable Python-panel diagnostic. |
| Final expression returns `None` | Show an actionable Python-panel diagnostic. |
| Any other object | Reject with its type and the accepted result forms. Do not turn arbitrary `repr()` output into HTML. |

This would allow all of the following endings:

```python
Welcome(name="Ada")
```

```python
Welcome(name="Ada").render()
```

```python
str(Welcome(name="Ada"))
```

The industry survey must compare this with `print()`, an explicit
`render(value)` helper, a named `preview` variable, and notebook display-hook
behavior. The final choice should optimize for a first-time Python/web reader,
clear tracebacks, copyability into a normal `.py` module, and predictable
reruns. Captured stdout may become an optional console, but it should not
silently become the HTML preview.

### Presenting errors

A short-lived toast is insufficient for a traceback or a repeated client
failure. The working hypothesis is a persistent bottom diagnostic tray within
the relevant panel, with a compact summary and expandable details. A transient
live-region announcement can accompany it without being the only record.

Python-side diagnostics should distinguish at least:

- runtime loading or package installation failure;
- syntax error, with line and column;
- Citry parse, compile, validation, and render errors;
- timeout or Worker restart;
- unsupported or missing final value;
- internal runner/protocol failure.

The result iframe should report at least:

- synchronous `error` events;
- unhandled promise rejections;
- failed script, stylesheet, image, and other resource loads where observable;
- `console.error`, because Citry catches and logs some client failures.

An injected bootstrap can forward those through `postMessage`, tagged with the
run id and a per-run correlation nonce. Visitor JavaScript shares that realm
and can read or spoof the nonce, disable hooks, or send invented diagnostics,
so the nonce is not authentication and the channel is best-effort telemetry.
The parent must validate the sending window, message schema, current run,
message size, and rate; treat every payload as hostile; and insert diagnostic
strings as text, never HTML. Messages from a sandboxed opaque-origin `srcdoc`
frame have a `null` origin, so origin-string comparison alone is not an
authentication mechanism. Parent-owned load and timeout states remain separate,
and silence from the frame never proves successful client execution.

## Research questions and working hypotheses

| Topic | Working hypothesis | What would falsify it |
| --- | --- | --- |
| Python runtime | Pinned Pyodide is the verified host for direct and public-package API proofs; its Worker product model remains under test. | Browser startup is unacceptable, or required interruption and containment controls do not work on the deployment target. |
| Rust binding | Use the existing PyO3 module built for `wasm32-unknown-emscripten`; direct feasibility passed. | The 0.3.0 acceptance matrix fails, behavior diverges in browsers, or its release process proves unsustainable. |
| Alternative binding | Do not pursue a wasm-bindgen core plus Python bridge now. | A later PyO3/Emscripten acceptance gate fails and a thin bridge can preserve the complete Python contract without duplicating the AST or compiler surface. |
| Execution model | Reuse a warm Worker only if tests bound the residual state risk; clear Citry and use a fresh namespace between runs. | Python, filesystem, module, or JavaScript state leaks; memory grows without bound; registry collisions recur; or cleanup cannot restore deterministic behavior. |
| Cancellation | Expose Stop and terminate and recreate the Worker after Stop, timeout, or crash. | Rebootstrap cost makes recovery unusable or deployment policy blocks the necessary Worker behavior. |
| Preview contract | Evaluate and normalize the final expression. | Users consistently misunderstand it, source rewriting harms tracebacks, or explicit rendering is materially more copyable and predictable. |
| Starter | A short Card-like component is better than the tutorial's step 9 module. | It fails to communicate a meaningful Citry advantage or readers cannot transfer it to the getting-started journey. |
| Editor | CodeMirror 6 is the initial comparison favorite because mixed parsing can be extended and its surface is smaller than a full desktop IDE. | Monaco or another editor materially wins on nested languages, accessibility, bundle cost, worker integration, or maintenance. |
| Highlighting | Port the Pygments nested-language rules and share fixtures. | The chosen editor can safely consume Pygments tokens live, or its parser model requires a different source of truth. |
| Runner containment | The locally accepted cross-origin runner page on a dedicated credential-free origin owns the Worker and bounds the host protocol with restrictive policy. | A production-origin test exposes docs credentials or sensitive endpoints, required runtime traffic cannot fit the allowlist, or deployment cannot support the topology. |
| Result isolation | `srcdoc` plus `sandbox="allow-scripts"` is a useful iframe layer for v1. | Required Citry behavior needs same-origin privileges, output can affect the parent, network behavior violates the threat model, or important blind spots make the error contract misleading. |
| Reuse boundary | One consumer-neutral browser host can serve the playground first and opt-in inline examples later. | Page-specific layout, state, asset, or protocol assumptions prevent a second consumer without duplicating the runtime. |
| Events follow-on | A Citry custom Events transport can bridge preview actions directly to the live Python generation without pretending to be an HTTP server. | Core actions require unportable host-framework semantics, render dependencies cannot be represented safely, or lifecycle isolation cannot reject stale event work. |
| Error UI | Persistent per-panel diagnostics are better than toast-only errors. | Usability checks show a smaller presentation retains full traceback access and clear ownership. |
| Assets | Self-host pinned runtime/editor artifacts. | Repository/deploy size becomes unacceptable or a verified immutable CDN provides stronger availability, integrity, and version guarantees. |
| Docs versions | One canonical, site-scoped `/playground/` runs one exactly pinned Citry runtime. It is never emitted below `/v/<version>/`. | This is a fixed product policy, not a hypothesis. A future change requires a new design decision rather than an implicit snapshot build. |

## Research program

Each stage has an expected artifact and a gate. Later stages may run in
parallel only when their claims do not depend on an unsettled earlier result.
All material conclusions require independent adversarial review before they
become final recommendations.

### Stage 0: capture the local baseline

**Status: complete and refreshed on 2026-07-28.**

Record the current docs page pipeline, navigation, responsive header, existing
splitter and iframe behavior, Pygments implementation, package versions,
binding architecture, renderable output types, rerun state, release process,
and current tests. Recheck fingerprints before a later stage relies on a
modified file because the working tree is active.

**Output:** the confirmed constraints and local prior art in this document.

**Gate:** each blocking local claim cites current code or an executable probe;
stale status prose is not used as implementation truth.

The refresh selected the planned canonical route and source at `/playground/` and
`docs_site/content/playground.md`. It also compared the `citry@0.2.0` tag,
current package metadata, and an isolated package-resolution and render probe.
That evidence establishes the published 0.2.0 and 1.4.0 incompatibility and
the two-track released-package and direct-core scope of the next stage.

### Stage 1: prove or reject the browser runtime and containment model

**Status: partially complete.** The binding, package, real Pyodide Worker,
opaque preview, and cross-origin broker tracks ran on 2026-07-28 in Chromium
149, Firefox 151, and WebKit 26.5. The evidence rejects a docs-origin Worker
for credential containment, accepts the dedicated credential-free runner
topology for continued design, and confirms that the preview needs a separate
network and message policy. The local deterministic-build contract, one sealed
manifest, no-resolution historical public loader, cached-desktop timing
matrix, and warm-heap sampling are also complete. Physical-mobile and uncached
network performance, release-workflow enforcement, a real production-origin
test, and the published 0.3.0 acceptance run remain blocking. See
[`runtime_feasibility.md`](docs_playground_research/runtime_feasibility.md) and
the executable [`runtime_proof`](docs_playground_research/runtime_proof/).
The Node and browser loaders use the same manifest and verify every selected
artifact before startup. The historical public track installs five local
wheels directly and rejects HTTP(S) access. Builds from two clean 1.4.0 tag
archives became byte-identical after pinning `SOURCE_DATE_EPOCH`, remapping
Rust paths, and normalizing generated SBOM workspace URLs; release CI still
needs to enforce that proven contract.

1. Write a threat model for the Python Worker, result iframe, parent page,
   network, credentials, storage, messages, locally typed code, and any future
   shared code. State which boundary protects which asset. Compare a direct
   docs-origin Worker with a cross-origin runner page that creates the Worker;
   do not assume that a cross-origin asset URL changes Worker origin.
2. Select one exact Pyodide release and record the complete compatible build
   tuple: `pyodide-build` and xbuild environment, Python, Emscripten, Rust,
   PyO3, maturin, and the resulting wheel ABI tag. The repository's unversioned
   nightly Rust selector must not silently choose an incompatible toolchain.
3. Build `citry_core==1.4.0` for that target from the current binding crate.
   If practical, also build 1.3.0 from its release tag for the released-pair
   public API track.
4. Load each wheel in an otherwise unmodified matching Pyodide runtime and
   import `citry_core._rust`.
5. Against 1.4.0, call template parse and compile, safe evaluation, and HTML
   marking directly.
6. Generate a manifest with exact versions, wheel URLs, and byte hashes for
   each custom core wheel and every Pyodide artifact required by its proof.
   Preinstall the custom core wheel and prove that startup does not depend on
   a live resolver choosing new versions.
7. Install `citry==0.2.0` only over the exact custom 1.3.0 core and with live
   core resolution disabled. Pin its other dependencies. Define and render
   representative components through the public API: static markup,
   expression and control flow, nested component, CSS, plain JavaScript, and
   `$component` JavaScript. Record the fresh 0.2.0 plus 1.4.0 resolution defect
   separately rather than attributing it to Pyodide.
8. After `citry==0.3.0` is published, extend the manifest with its exact wheel
   and every transitive dependency, including `wrapt`, MarkupSafe, and
   typing-extensions, then rerun the public API matrix against its exact core
   pin. The recommended release plan makes that core 1.4.1.
9. Repeat one module at least 100 times, with syntax and render failures between
   successes. Check output determinism, registry cleanup, stale classes, and
   heap growth. Deliberately mutate `sys.modules`, builtins, the in-memory
   filesystem, and Worker JavaScript globals. Compare warm reuse with a fresh
   Worker for every run and record the accepted residual-state risk.
10. Run the proof inside a Worker, then terminate an infinite loop and recover
   by bootstrapping a fresh Worker. Test Python access to Worker APIs, network
   requests, storage where available, message flooding, and Worker shutdown.
11. Exercise the candidate iframe policy against relative and absolute
    resources, `fetch`, navigation, popups, downloads, CSP inheritance, message
    flooding, and attempts to reach the parent. Record diagnostic blind spots.
12. Record compressed bytes, cold bootstrap, first render, warm rerender, and
   edit-to-preview p50/p95 on a current desktop and a representative mid-tier
   mobile device.
13. Produce the exact build command, wheel hash, dependency manifest, and a CI
    sketch. A local one-off binary is not a sufficient proof.

**Output:** `docs/design/docs_playground_research/runtime_feasibility.md`, a
reproducible proof directory, and measured artifacts.

**Gate:** record a direct-core result now and choose one of three explicit
outcomes:

- proceed with a supported PyO3/Emscripten wheel and an accepted containment
  model;
- investigate the wasm-bindgen plus Python-bridge alternative with a newly
  scoped proof;
- stop the browser-only design and decide whether a remote runner is worth its
  security and operations cost.

Failure to build the direct wheel does not authorize a pure-Python fork of core
behavior. Rust remains the source of truth. A successful 1.4.0 direct-core
result and a successful 0.2.0 plus 1.3.0 public-package result prove important
parts of the architecture, but acceptance remains provisional until the exact
published `citry==0.3.0` pair passes the public-package rendering matrix.

**Gate result so far:** continue the PyO3/Emscripten path and use the
credential-free cross-origin runner topology. Pyodide 314.0.3
with Python 3.14.2, Emscripten 5.0.3, Rust 1.93.0, `pyodide-build==0.37.0`,
and ABI `pyemscripten_2026_0_wasm32` produced working core 1.3.0 and 1.4.0
wheels. The 1.4.0 wheel is about 7.1 MB before browser caching. Warm-cache
Node proofs started Pyodide and ran the direct matrix in roughly 1.0 second and
the public-package matrix in roughly 1.5 seconds. The complete sealed
historical track is 20,409,000 fetched bytes.

Two cached-desktop repetitions per engine measured five fresh Workers and 200
warm public-API renders. Worst observed fresh-Worker p95 was 5.92 seconds in
Firefox; worst warm edit-to-result p95 was 10.20 milliseconds. The
61,669,376-byte Wasm heap, Python GC-object count, and loaded-module count did
not grow across either 200-render window. This supports provisional local
guardrails of 6.5 seconds for cached fresh-Worker p95, 15 milliseconds for
warm p95, 64 MiB post-warmup Wasm heap, and at most 8 MiB heap growth over 200
renders. These are desktop regression limits, not final mobile, network, or
Auto-run budgets. The gate remains open for the explicitly unrun tests listed
in the research record.

The earlier wheel hash drift had three causes: cargo-cyclonedx's random SBOM
serial and current timestamp plus transitive `RECORD` entries, absolute paths
in Rust debug information and SBOM workspace URLs, and untracked Python cache
files in a live checkout. The checked-in wrapper requires a clean tag archive,
pins the tagged commit time, remaps Rust paths, normalizes the generated SBOM,
and regenerates `RECORD`. Builds from two different source and target
directories were byte-identical for both core versions and contained none of
the tested local paths. The remaining release task is to put that executable
contract in the publishing workflow.

The real Worker proof loaded core and passed the direct API matrix in all three
desktop engines. Hard termination recovered with a fresh Worker in about 0.88
seconds in Chromium, 4.67 seconds in Firefox, and 1.01 seconds in WebKit on the
local warm-cache host. These are single observations, not budgets. A
same-origin Worker fetch sent the docs test cookie in every engine, so
production must not create the Python Worker directly from the docs page.

The cross-origin protocol proof used a docs parent on one loopback site, a
runner iframe and Worker on another, and an attacker frame on a third.
In all three engines, the runner received no docs cookie, transferred one
validated `MessagePort`, rejected an attacker-origin handshake, applied a
64 KiB source limit, a 2 MiB result limit, rate limiting, increasing run ids,
and a hard timeout, dropped 250 unsolicited Worker messages, recovered after
termination, dropped 150 of a 250-message direct runner-to-parent flood at the
parent boundary, and replaced a self-navigated preview with an inert diagnostic
frame. The same runner then created the real Pyodide Worker, loaded the
manifest-verified core wheel, passed parse, compile, safe evaluation, and HTML
marking, and reached the deliberate docs test endpoint without its cookie.
Those limits are proof constants, not accepted product defaults. Repeating the
result on the production origin remains necessary.

### Stage 2: survey comparable playgrounds

**Status: complete on 2026-07-28.** See
[`product_survey.md`](docs_playground_research/product_survey.md).

Inspect current, official implementations and documentation for a bounded set
of products. The set should cover Python-in-browser behavior and mature
component playground UX rather than collecting many visually similar sites.

Candidate groups:

- Pyodide console and examples, PyScript, and JupyterLite for browser Python,
  output capture, interrupts, package loading, and error behavior;
- Vue SFC Playground, Svelte Playground, React/Sandpack, and another
  single-file component playground for split layout, reruns, diagnostics,
  presets, sharing, and responsive behavior;
- a Python documentation playground that uses explicit `print()` or an
  explicit render function, if a maintained comparable product exists.

For each, record:

- intended reader and first-loaded example;
- run trigger and stale-result behavior;
- final value, stdout, and explicit-render semantics;
- syntax, runtime, and iframe error presentation;
- editor, mixed-language support, keyboard behavior, and mobile mode;
- splitter behavior and persisted state;
- reset, format, share, download, permalink, and version controls;
- Worker and iframe isolation;
- runtime and dependency loading;
- cold-start communication and perceived performance;
- accessibility behavior that can be observed or is documented;
- recurring user complaints in official issue trackers, separated from design
  intent.

Use official product pages, source repositories, documentation, and issue
trackers. Label an observed behavior, documented contract, maintainer claim,
and our inference separately.

**Output:** `docs/design/docs_playground_research/product_survey.md` with a
comparison matrix and screenshots or recordings only where they prove an
interaction that prose cannot.

**Gate:** identify recurring patterns, meaningful disagreements, and which
patterns serve Citry's first-time reader. Popularity alone is not a decision.

**Gate result:** adopt latest-wins run ids, visibly stale prior output,
persistent panel-owned diagnostics, a one-panel mobile mode, staged cold-start
feedback, Reset and Retry, and a narrow iframe policy. Keep CodeMirror as the
Stage 4 lightweight favorite rather than a selection. Reject stdout as
implicit HTML, toast-only tracebacks, pointer-only resize, unversioned assets,
and automatic execution of shared code. The user subsequently selected a
hybrid run-control shape with an always-present Run action and an Auto-run
toggle. Carry the remaining preview-value disagreement into Stage 3: implicit
final expression versus explicit `render(value)`.

### Stage 3: settle the execution and learning contract

**Status: complete on 2026-07-28.** See
[`execution_contract.md`](docs_playground_research/execution_contract.md) and
the executable
[`execution_proof`](docs_playground_research/execution_proof/). The host proof
has 76 passing tests and a clean Ruff run. Repeating it in the exact pinned
Pyodide tuple remains part of Stage 1 acceptance, not an unresolved product
contract.

Prototype the smallest runner independent of final page styling. Compare:

1. implicit final expression;
2. explicit `render(value)`;
3. required `print()` with stdout used as HTML;
4. a named `preview` value.

Test each with a string, `CitryElement`, `CitryRender`, no final expression,
`None`, an unrelated Python object, multiple `print()` calls, a syntax error,
and a render error. Preserve source line numbers and produce tracebacks that
point to `<playground>`. Also test future imports, semicolon endings,
docstring-only modules, private result-name collisions, and the chosen
top-level-await behavior.

Compare at least three starter modules:

- minimal visible component;
- a medium Card-like example with typed input, data, template, and CSS;
- a richer composition or client-JavaScript example.

Evaluate them against the provisional reader model in `docs_content.md`: time
to first meaningful edit, Citry concepts introduced, visible payoff, amount of
unexplained infrastructure, payload, and a clear next link into Docs or
Examples.

**Output:** `docs/design/docs_playground_research/execution_contract.md` with
runner prototypes, example candidates, and a recommendation.

**Gate:** approve one execution contract, one starter, optional presets, and
the exact relationship with the Getting started journey.

**Gate result:** use the module's final expression as its preview value. Accept
only `str` and `Markup`, `CitryElement`, and `CitryRender`; normalize them to
HTML and keep stdout and stderr separate. A visitor who wants an explicit
ending can use the public `Card().render()` or `str(Card())` forms. Do not
inject a playground-only `render(value)`, reserve a `preview` name, or treat
`print()` output as HTML. Reject top-level await in v1 and preserve ordinary
module semantics, future imports, docstrings, and `<playground>` traceback
locations through one AST compilation.

Start with the medium typed welcome card: it gives a first reader one obvious
text edit and one color edit while introducing typed input, template data, and
component-owned CSS. Keep the minimal and composition examples as tested
future presets, but ship no preset selector initially. Link the first success
to **Your first component**, which remains the owner of the step-by-step
learning journey.

Run stays permanently visible and bypasses any Auto-run debounce. Starting
Auto-run enabled, remembering the choice in versioned local storage, beginning
with a 500 ms idle debounce, and disabling Auto-run after a hard timeout or
Worker crash are Stage 5 specification hypotheses, not accepted defaults.
Stage 6 will validate them with measurements and first-reader evidence. Their
resolution will not reopen the preview-value contract.

### Stage 4: select the editor and highlighting strategy

**Status: complete on 2026-07-28, subject to the later release matrix.** See
[`editor_evaluation.md`](docs_playground_research/editor_evaluation.md) and the
static [`editor_proof`](docs_playground_research/editor_proof/). The Chromium
layout and editor probes pass. Real assistive-technology sessions, real 400%
browser zoom, Firefox, WebKit, and combined editor plus runtime performance
remain Stage 6 gates.

Build equivalent small spikes with the strongest two editor candidates. At
minimum compare CodeMirror 6 and Monaco unless Stage 2 identifies a better
fit.

Before choosing the editor, build a layout-only spike with a textarea and
empty result frame. Decide tabs versus stacking on narrow screens, scrolling
ownership, focus order, mobile navigation, soft-keyboard behavior, and minimum
usable pane dimensions. Verify 320 CSS pixels, 400% zoom, dynamic viewport
changes, right-to-left layout, a named `<main>` landmark, one H1, an iframe
title, and diagnostics that do not cover controls. Editor evaluation then uses
those real dimensions rather than a desktop-only mockup.

Measure and verify:

- Python editing, indentation, undo, search, bracket matching, and diagnostics;
- nested HTML, Python expressions, JavaScript, and CSS inside the three Citry
  multiline assignments;
- alignment with `pygments-citry` token fixtures and supported syntax;
- light, dark, and automatic themes;
- keyboard and screen-reader behavior;
- touch and small-screen behavior;
- uncompressed and compressed bundle size;
- number and type of Workers;
- CSP, base-path, and static-site compatibility;
- pinned self-hosted build and update procedure;
- project maintenance cost for a Citry language integration.

Include a plain-textarea fallback decision for runtime or editor load failure.
A fallback that lets readers recover their code may be valuable even if it
cannot execute.

**Output:** `docs/design/docs_playground_research/editor_evaluation.md` plus two
comparable static prototypes.

**Gate:** choose the editor, bundling approach, language integration, and
fallback. Record why the runner cannot directly reuse Pygments, and identify
the fixtures that keep the two implementations aligned.

**Gate result:** choose CodeMirror 6, pin every package exactly in the docs
lockfile, and self-host the resulting route-only assets. In equivalent scoped
proofs, CodeMirror's initial bundle measured 178,063 bytes Brotli. Monaco
measured 571,309 bytes of main-thread assets plus a 74,794-byte editor Worker.
Both passed
the Chromium editing, diagnostics, nested-base-path, and CSP checks, but
Monaco's additional payload and Worker wiring do not buy a first-version
requirement. Reconsider Monaco if the product later expands into language
servers or a broader IDE.

Do not ship the proof's regular-expression decorations as the Citry language
implementation. Build a first-party CodeMirror language package that mounts
official Python, HTML, JavaScript, and CSS parsers and represents Citry
interpolation, dynamic attributes, structural values, comments, and raw
content as real syntax nodes. Pygments remains the static-docs highlighter; its
existing fixtures become the shared compatibility corpus because its
server-oriented token stream cannot drive an incremental browser editor.

On wide screens, use two independently scrolling panels and an accessible
pointer, touch, and keyboard separator. On narrow or short screens, switch to
one panel at a time with explicit Code and Result controls. Keep persistent
diagnostics in flow at the bottom of their owning panel. If CodeMirror fails to
load, preserve the source in a named plain textarea with Copy, Download, Reset,
and Retry editor controls. Disable Auto-run while degraded. Keep Run available
when the textarea is authoritative and the independently loaded Python runner
is healthy; disable it only when the latest source cannot be proven complete
or the runtime is unhealthy. Rich highlighting, inline markers, and editor
search are unavailable in fallback mode.

### Stage 5: design docs-site and release integration

**Status: complete on 2026-07-28.** See
[`docs_integration.md`](docs_playground_research/docs_integration.md).

With runtime and editor choices known, specify:

- `playground.md` front matter and its concise text/LLM projection;
- the closed page-layout schema and invalid-value behavior;
- shared document head/header extraction or the chosen alternative;
- `PlaygroundPage` and playground component boundaries;
- consumer-neutral runtime loader, runner connection, Worker session,
  execution, editor, preview, diagnostic, protocol, and scheduler modules;
- a narrow consumer API carrying consumer, session, generation, and run ids,
  plus declared capabilities, with `PlaygroundWorkspace` as the first UI
  adapter and no dependency on its splitter or storage keys;
- desktop workspace sizing and mobile navigation;
- page-level feature collection and conditional CSS/JavaScript loading so
  ordinary docs pages do not pay for the editor or Pyodide, and future inline
  examples load only a small activator until the visitor opts in;
- self-hosted artifact paths, hashes, caching, compression, and asset guards;
- content-addressed immutable artifact paths, atomic deployment order, and
  retention rules so referring HTML is never published before its Worker,
  wheel, package, and WASM files;
- runtime manifest generation from exact package versions;
- testable candidates and instrumentation for Auto-run default, persistence,
  debounce, timeout, and failure-pause behavior. Stage 5 does not approve the
  final values;
- the user-initiated Stop contract, Worker restart, and their effect on stale
  preview and Auto-run;
- `DOCS_BASE_PATH` behavior for Worker, wheel, package, and WASM URLs, because
  the current HTML rewriter cannot repair URL strings inside JavaScript;
- Pagefind, SEO, social card, Markdown companion, and LLM behavior;
- the canonical unversioned route, its single pinned runtime, and explicit
  exclusion from historical docs snapshots;
- CI ownership and release order for the Pyodide wheel.

The playground is permanently site-scoped. There is one canonical
`/playground/` page and one exactly pinned browser runtime tuple. The **Try it**
navigation area declares `scope: site`, so snapshot builds omit
`docs_site/content/playground.md` and project their header link back to the root
page. They must not emit, redirect, canonicalize, index, or link to
`/v/<version>/playground/`. Build and version guards assert that absence.

Historical inline examples follow the same single-runtime product boundary:
snapshot pages remain static-only and may link to the canonical current
playground with copy that says it runs the current pinned browser release. They
do not activate a current or frozen historical Python runtime in place.

The manifest must bind the complete runtime tuple to exact byte hashes. Script
SRI alone does not cover files dynamically fetched by a Worker or Pyodide, so
the loader and release smoke test must verify the manifest and fetched bytes.

**Output:** `docs/design/docs_playground_research/docs_integration.md` with the
proposed file and artifact graph.

**Gate result:** the static build, live server, domain-root deployment, project
base-path deployment, and version snapshots have explicit contracts. Only the
root `/playground/` exists, it loads one immutable pinned runtime, and no old
page can silently activate another runtime.

### Stage 6: test the complete experience

Assemble one vertical prototype and test the real minified static output, not
only isolated modules.

Required scenarios include:

- first load, slow load, offline load, missing wheel, hash mismatch, package
  import failure, and browser without required WASM features;
- initial sample render, warm edit, rapid edit race, reset, and reload;
- first-reader tasks and performance measurements for explicit Run and the
  Stage 5 Auto-run candidates, including debounce, persistence, and failure
  recovery;
- syntax, template compile, render, unsupported output, and `None` failures;
- infinite loop, timeout, Worker termination, restart, large output, large
  allocation, and traceback truncation;
- synchronous iframe throw, rejected promise, resource failure, and a Citry
  client error that is caught and logged;
- iframe attempts to read or navigate the parent, download, open a popup, use
  storage, fetch data, flood messages, and send malformed diagnostics;
- Python attempts to fetch data, reach same-origin credentials, mutate Worker
  JavaScript state, flood messages, close the Worker, persist filesystem or
  module state, and affect a later run;
- divider pointer drag, touch drag, arrow keys, Home/End, reset, stored size,
  zoom, and right-to-left layout;
- 375-pixel phone flow, tablet, narrow desktop, and the future expected header
  link count;
- light, dark, automatic theme, forced colors, and reduced motion;
- screen-reader names, focus order, live announcements, and recovery without a
  pointer;
- root and non-root base paths, cache update, and no failed asset requests.

Start with Stage 1's provisional cached-desktop guardrails, then add or replace
them with deployed uncached-network and physical-mobile product budgets before
this gate. Report cold and warm behavior separately. A fast shell that hides a
very slow runtime is not a successful first load. Use those measurements and
first-reader results to approve the Auto-run defaults. If Stage 5 proposes a
Stop control, approve its termination, restart, stale-preview, and Auto-run
behavior here as well.

**Output:** `docs/design/docs_playground_research/vertical_prototype.md`,
browser results, accessibility notes, security findings, and performance
measurements.

**Gate:** the maintainer accepts the product behavior and the prototype passes
its agreed budgets and failure scenarios. Unmet requirements are narrowed,
fixed, or recorded as blockers rather than described as complete.

### Stage 7: write the final implementation plan

Replace the hypotheses in this document with accepted decisions. The final
plan must include:

- prior art and research evidence;
- chosen architecture and one or two rejected alternatives;
- runtime, worker, runner, iframe, editor, page, and artifact boundaries;
- exact versions and compatibility policy;
- file-by-file implementation slices;
- all downstream docs, CI, release, guard, and test updates;
- security and privacy model;
- error behavior for every protocol and configuration value;
- rollout, observability, and rollback;
- what would falsify each load-bearing claim.

Implementation should then proceed in review-sized slices. The Pyodide wheel
and its reproducible release path should land before the polished page depends
on it.

### Stage 8: add the Citry Events bridge after baseline rendering

This is planned follow-on work, not part of the first render-only milestone.
It starts only after the production playground passes Stage 6 and the shared
browser host from Stage 5 is in place.

The selected high-level design uses Citry's existing custom transport rather
than overriding global `fetch` or building a dummy WSGI/ASGI server:

```text
preview Citry client
  -> registerTransport("playground", {send})
  -> generation-scoped event envelope
  -> docs host and runner MessagePort
  -> live Python Worker generation
  -> EventsDispatcher.dispatch(synthetic EventRequest, TransportContext)
  -> validated action response
  -> preview Citry client
```

This is closer to the abstraction Citry already exposes. A fake WSGI/ASGI
layer would add HTTP encoding and framework lifecycle without supplying real
authentication, session, CSRF, middleware, file-upload, or host-routing
semantics. ASGI is also a poor first target while the current async dispatch
path can offload synchronous handlers with `asyncio.to_thread`, which needs a
separate browser compatibility proof.

The preview registers a transport named `playground`. The host routes strict
event envelopes over the existing generation-scoped channel. In Python, the
browser adapter constructs a synthetic `EventRequest` and a
`TransportContext(transport="playground", citry=session_citry)`, then invokes
the Events dispatcher directly. The request may expose the relevant path,
method, headers, and body for Citry's own event contract, but it must identify
itself as the playground transport and must not claim ordinary server
middleware behavior.

The Worker, executed module, component registry, session Citry engine, and
event dispatcher stay alive for one rendered generation. A source rerun
creates a new logical generation; reset, close, timeout, crash, or eviction
invalidates every pending event id before disposing its Worker. Switching
between Code and Result without rerunning preserves the generation and its DOM
and Python event state.

Zero-boilerplate Events need one supporting Citry API change. State actions
require a session signing secret, while component classes currently bind to an
immutable default engine when defined. Add a public execution-scoped default
engine override so the browser host can evaluate the user's module against a
private `Citry(secret=...)` instance. Set it up around execution, outside the
user's AST. Do not prefix source text: textual injection would disturb future
imports, module semantics, and traceback locations.

Target the following capability contract first:

| Capability | Initial Events target |
| --- | --- |
| Data | Supported after round-trip and stale-generation tests pass. |
| Dispatch | Supported, including nested event dispatch within declared limits. |
| State and two-way bindings | Supported after signing, token refresh, replay, and generation lifecycle tests pass. |
| Render actions | Supported only after a browser asset adapter can serialize fragments and dependencies without relying on mounted HTTP asset routes. |
| Synchronous handlers | Supported first. |
| Async handlers | Deferred until the browser event-loop policy is explicit and no thread-dependent path is used. |
| Redirect, URL/history actions, Download, and raw route responses | Explicitly unsupported in the browser playground. |
| Host authentication, sessions, CSRF, middleware, uploads, and arbitrary routes | Explicitly not simulated. |

Do not use a broad `fetch` override. It would miss script and stylesheet loads,
change unrelated user code, and falsely imply server completeness. Render
actions instead need a browser-host serialization and asset adapter, likely
using inline or content-addressed blob dependencies governed by the preview
policy. The preview client should receive an explicit supported-action list so
unsupported actions are omitted or rejected with a useful diagnostic.

Required proof cases include Data, Dispatch, State token refresh, a render
swap with CSS and JavaScript dependencies, stale event responses after rerun,
timeout during an event, reset and close cleanup, cross-session isolation,
malformed and oversized envelopes, unsupported actions, synchronous handler
exceptions, and the chosen async policy. An Events-enabled Worker remaining
alive must also pass heap-growth and idle-resource measurements.

**Gate:** the documented action subset works without textual source mutation,
HTTP-framework impersonation, credential access, state crossover, or stale
generation updates. Unsupported server behaviors fail explicitly.

### Stage 9: reuse the browser host for opt-in inline examples

Start this only after the complete production playground, including its Events
lifecycle, passes its containment, release, browser/mobile performance, and
accessibility gates. Inline live code is a second UI consumer, not an embedded
copy of `PlaygroundWorkspace`.

The first authoring contract should be an explicit path-backed Citry tag, for
example:

```html
<c-live-code
  path="docs_site/live_snippets/welcome.py"
  title="Welcome card"
/>
```

The exact allowlisted directory can be settled in Stage 9. Each source is one
complete UTF-8 Python module. The builder reads and highlights it but never
imports it. The general guard rejects traversal, files outside the allowlist,
missing files, invalid UTF-8, excessive size, blank titles, syntax errors,
top-level await or imports outside the accepted browser manifest, and a missing
final expression. Diagnostics name the Markdown source and directive line.

A wrapper around a Markdown fence is not the preferred first contract. The
current docs pipeline protects fences before Citry components run, while the
existing include-file and example-card components already establish
path-backed source patterns. A source file also provides one canonical copy
that can be syntax-checked and projected intentionally.

The default output remains the ordinary static Pygments block. The page loads
only a small activator and exposes **Try live**; CodeMirror, the broker,
Pyodide, wheels, and preview load only after explicit activation. Keep source
in the static code DOM, attach a build-time source hash, and test exact text
round-tripping rather than embedding a second executable source copy. Markdown,
Pagefind, and LLM projections contain the source, not controls, runtime state,
or iframe markup.

Live blocks need a real toolbar above the code because existing Copy and
language controls occupy the top-right corner. On activation, use one panel at
a time at every width with accessible Code and Result tabs. Preserve the
Worker and preview when switching tabs. Always provide Run; Auto-run reuses
the accepted shared controller. Reset restores the authored source into a new
generation. Close disposes the iframe, Worker, and editor, restores the exact
static block and focus, and never loses a dirty draft silently.

For v1, permit one active inline editor/runtime session per document.
Activating another block while the first is dirty must confirm discard or keep
a recoverable in-memory draft. Runtime and Citry state never cross between
examples. One hidden runner page may serve the document, but each live example
gets its own session and generation identities. An activation failure leaves
the static source usable and offers Retry.

Historical `/v/<version>/` pages remain static-only and may link to the
canonical current playground. They never activate a current or frozen
historical runtime in place. The link copy must make clear that `/playground/`
uses the current pinned browser release rather than the snapshot's Citry
version.

The bounded prototype should include a synthetic page with zero, one, and
multiple eligible blocks before converting real Docs or Examples content.
Test JavaScript-disabled static output, source extraction and reset, invalid
directives, dirty activation and close, late loading after close, one example
timing out without corrupting another, Result switching preserving Events
state, narrow layout, 400% zoom, keyboard and screen-reader behavior, forced
colors, reduced motion, soft-keyboard resize, and snapshot pages. Also verify
that pages without live tags load none of the inline-example code.

**Gate:** the inline consumer reuses the accepted browser host without adding
page-wide runtime cost, cross-example state, source duplication, silent draft
loss, or version drift.

## Failure modes that the final design must answer

| Failure | Required behavior to validate |
| --- | --- |
| Pyodide or editor asset cannot load | Preserve editable source where possible, explain which asset failed, offer retry, and do not show an endless spinner. |
| Wheel is incompatible with the selected runtime | Fail during CI/release compatibility smoke tests. At runtime, show the exact pinned pair and a concise load failure. |
| Dependency cannot install | Name the dependency and stage. Do not report every install failure as a Citry render error. |
| Python syntax or runtime error | Keep the previous preview, mark it stale, and show source locations in the left diagnostic. |
| Citry validation or render error | Preserve Citry's useful component path and source context without exposing runner internals. |
| No supported final value | State the accepted endings and point to the last executed line. |
| Infinite loop or runaway work | Terminate the Worker after the accepted limit, report the restart, and allow the next edit to run in a clean Worker. |
| Older run completes late | Ignore it by run id. It must not replace newer HTML or diagnostics. |
| Registry or module state leaks | Use the accepted fresh-Worker or explicitly bounded warm-reuse policy. `citry.clear()` alone is not complete interpreter cleanup. |
| Iframe JavaScript fails | Keep the rendered DOM where safe and show a deduplicated right-panel diagnostic with expandable details. |
| Iframe replaces its own document | Treat an unexpected frame load as a preview-navigation fault, replace it with a fresh inert frame, and show a persistent right-panel diagnostic. The next successful run creates a new preview. The local cross-browser proof passed; repeat on the production origin. CSP is defense in depth, not the only detector. |
| Iframe sends malformed, oversized, flooded, spoofed, or stale messages | Rate-limit or ignore them and record a test-only diagnostic; never treat them as a current trusted error. |
| User HTML attempts parent access or network exfiltration | Apply the accepted sandbox and policy. Tests prove the actual parent, credential, storage, navigation, and network boundaries. |
| Python uses Worker browser capabilities | Apply the accepted origin and capability policy, or state the limitation explicitly. A Worker alone is not a sandbox. |
| Output is too large | Apply a measured limit, preserve the editor, and explain that the preview was not replaced. |
| Stored splitter value is corrupt or out of range | Clamp or reset to the default and update the accessible value. |
| Layout metadata is unknown | Reject the page during build with its source path and accepted values. |
| Base-path URL is wrong | A built-site test fails before deployment. Runtime code derives URLs from injected/base-path data rather than root literals. |
| Runtime deployment is partial or an asset is replaced | Load through one content-addressed manifest, publish assets before referring HTML, and retain old referenced files. |
| A snapshot build tries to emit a playground page | Fail the version build or guard. Only the site-scoped root `/playground/` may exist; do not create a versioned page or redirect. |
| Browser lacks a required feature | Show a supported-browser message and keep source copyable. |
| Event response arrives after rerun or disposal | Reject it by consumer, session, generation, and event id. It must not mutate the current preview or Python state. |
| Unsupported Event action is emitted | Reject it in the browser adapter with the action name and supported subset. Do not approximate server behavior silently. |
| Inline live activation fails or closes late | Leave or restore the exact static code block, terminate the session, reject late messages, and preserve a dirty draft according to the explicit user choice. |

## Verification model

Repository conventions separate machinery tests from assertions about one
user-facing page's wording. Follow that split.

### Unit and render tests

- page-layout parsing, including unknown values;
- shared header rendering and active Try it navigation;
- playground layout has a header but no docs sidebar, breadcrumbs, mobile TOC,
  right TOC, previous/next navigation, or footer;
- concise Markdown and LLM projection;
- runner AST transformation and line-number preservation;
- future imports, semicolons, docstring-only modules, result-name collisions,
  and top-level-await behavior;
- accepted and rejected output types;
- registry reset and fresh namespaces;
- run-id protocol and error-message schema;
- artifact manifest and base-path URL construction;
- hostile message size/rate handling and text-only diagnostic insertion.

### Build and guard checks

- `/playground/` exists in static and live builds;
- no snapshot, alias, sitemap, Pagefind index, Markdown companion, LLM export,
  or redirect exists at `/v/<version>/playground/`;
- every self-hosted runtime asset exists and has the expected hash;
- the content-addressed runtime manifest is complete, atomically deployable,
  and retains every asset referenced by published HTML;
- generated companions and SEO records are intentional;
- the strict nav, link, asset, HTML, heading, JSON-LD, and single-H1 guards
  continue to pass;
- release validation fails on an unsupported Citry, Citry Core, Pyodide, Python,
  or Emscripten combination.

### Browser checks

- the complete Stage 6 matrix;
- no failed requests in a production-equivalent build;
- no header overlap at the existing narrow desktop widths and the future link
  count;
- mobile primary navigation still works without the docs sidebar;
- playground Lighthouse coverage, including the effect of lazy-loading the
  heavy runtime;
- the accepted Chromium, Firefox, and WebKit support matrix, followed by
  representative physical mobile browsers.

### Human checks

- a first-time reader can identify what to edit and reach a changed result;
- the starter teaches one coherent Citry idea without unexplained server setup;
- errors identify the responsible panel and remain available long enough to
  act on;
- keyboard-only and screen-reader review;
- independent technical, security, accessibility, and editorial review.

## Research records and decision log

Create `docs/design/docs_playground_research/` only when Stage 1 begins. Keep
raw measurements and bounded research records there. Keep accepted decisions
and the current stage status in this document so a later session has one entry
point.

Each decision record should contain:

- question and reader impact;
- alternatives;
- evidence and its date/version;
- chosen answer and owner;
- error behavior;
- rejected alternatives and why;
- falsifying condition;
- files and tests affected.

Do not present a benchmark, browser observation, or upstream claim as a general
fact without recording its environment and version.

## Decisions intentionally deferred

The completed stages do not settle:

- the runtime tuple update policy after the verified Pyodide 314.0.3 and direct
  PyO3/Emscripten proof;
- the exact production Citry language grammar implementation and resulting
  bundle composition within the selected private docs frontend package;
- Auto-run default, persistence, debounce timing, and hard timeout;
- production runner origin and network policy, and whether warm Worker reuse
  is acceptable; the local broker topology and bounded protocol are accepted
  for continued design;
- whether a transient toast adds value beyond the accepted persistent panel
  diagnostics and live-region announcement;
- stdout console, formatter, and share links;
- exact production runner hostname and hosting provider;
- final browser support and network/mobile product budgets beyond the
  provisional cached-desktop regression guardrails;
- the execution-scoped default Citry engine API, browser render-dependency
  adapter, and synchronous/async boundary for Stage 8 Events;
- exact live-tag name, allowlisted source directory, draft-confirmation UI, and
  activation thresholds for Stage 9 inline examples.

These are the outputs of the research stages, not implementation details to
guess now.

## Immediate next step

Finish the remaining Stage 1 proof: repeat the accepted cross-origin Pyodide
topology on the intended production runner origin, wire the proven
clean-tag, source-epoch, Rust path-remapping, SBOM-normalization, and
repeated-build comparison contract into release CI,
and measure uncached network, heap pressure, and cold and warm behavior on a
representative physical mid-tier mobile device. Rerun the public-package
matrix against the exact Citry 0.3.0 and compatible core artifacts after they
are published; the recommended release plan uses core 1.4.1.

Stage 5 has completed the docs-site, private frontend package, runtime manifest,
asset, release, and unversioned-route design. Once the remaining runtime gate
closes, Stage 6 can assemble and test the complete production-equivalent
experience. Do not begin production page or editor integration while that gate
is open.
