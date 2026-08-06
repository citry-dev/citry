# Playground docs-site and release integration

**Date:** 2026-07-28

**Shipping override (2026-07-29):** The separate-origin immutable-bundle plan
in this research record is deferred hardening. V1 serves its first-party files
through the existing docs static deployment and loads pinned Pyodide and exact
package files from their current CDN/PyPI URLs. See the current Stage 7 plan in
[`docs_playground.md`](../docs_playground.md#current-shipping-plan).

**Status:** Stage 5 design accepted for iterative implementation. The tested
core 1.4.0 PyEmscripten wheel is public and passed the package smoke from its
PyPI bytes. Local implementation can proceed, and production activation is no
longer conditional on a separate runner deployment.

**Scope:** the authored page, docs builder, browser package, indexing,
cancellation, and the originally researched hardened release contracts.

## Outcome

The docs site should expose one top-level **Try it** link to one canonical,
site-scoped `/playground/` page. The page runs one exactly pinned Citry browser
runtime. It is not a documentation-version feature:

- `/playground/` is the only playground route;
- `docs_site/content/playground.md` is `scope: site` through navigation;
- snapshot builds do not write `/v/<version>/playground/` or a redirect there;
- snapshot header links point directly to the root `/playground/`;
- the page has no docs version picker and shows the pinned browser package
  version in its own workspace status;
- changing the pinned Citry version is an explicit runtime promotion and docs
  deployment, not a docs snapshot rebuild.

The page uses a first-class `playground` layout. A shared document shell keeps
the existing head, header, search, theme controls, responsive primary
navigation, and common assets. `DocPage` continues to own narrative docs chrome.
`PlaygroundPage` owns a viewport-filling application surface with no docs
sidebar, breadcrumbs, table of contents, previous or next links, or docs footer.

The browser implementation lives in a private docs frontend package. Its core
session, runner, protocol, execution, preview, diagnostic, and scheduling
modules do not know about the playground splitter or browser storage keys. The
full-page `PlaygroundWorkspace` is the first consumer. A later inline live-code
consumer can reuse the same host without copying the page application.

CodeMirror and the small playground application are route-only, self-hosted
assets. Pyodide, Python packages, wheels, WebAssembly, and the execution Worker
live in a content-addressed bundle on the separately deployed, credential-free,
different-site runner origin accepted in Stage 1. Ordinary docs pages load
none of them.

## Evidence from the current builder

This design follows mechanisms that already exist in the repository:

- [`docs_site/content/_nav.yml`](../../../docs_site/content/_nav.yml) defines
  top-level header order and page scope. `scope: site` pages are omitted from
  snapshots, and snapshot links to them stay at the root.
- [`build.py`](../../../docs_site/_internal/build.py) discovers flat Markdown
  sources, writes clean HTML and Markdown companion routes, excludes site-scoped
  content in version mode, then produces Pagefind, SEO, LLM, social-card, and
  base-path outputs for the root build.
- [`frontmatter.py`](../../../docs_site/_internal/frontmatter.py) has no layout
  field today. Its guard derives the known schema from `PageMeta`, so adding a
  typed field can keep parsing and validation aligned.
- [`pipeline.py`](../../../docs_site/_internal/pipeline.py) always wraps authored
  content in the monolithic `DocPage`. `wrap_in_layout=False` removes the whole
  document and therefore cannot implement a full-width page with the header.
- [`doc_page.py`](../../../docs_site/_internal/components/doc_page.py) currently
  owns the common document head and header as well as narrative-only chrome.
  Its mobile primary navigation is inside the docs sidebar, so merely hiding
  that sidebar would remove small-screen navigation.
- [`base_path.py`](../../../docs_site/_internal/base_path.py) rewrites URL-bearing
  HTML attributes only. It cannot repair root paths embedded in JavaScript or
  JSON configuration.
- [`assemble.py`](../../../docs_site/_internal/assemble.py) builds the root site
  and copies committed snapshots below `/v/`. It does not need to copy the
  site-scoped playground into snapshots.
- [`repo--docs-deploy.yml`](../../../.github/workflows/repo--docs-deploy.yml)
  deploys the Pages artifact atomically, while the package publish workflows
  already collect platform artifacts before their single Trusted Publishing
  jobs.

The Stage 3 and Stage 4 decisions remain authoritative: final-expression
preview semantics come from
[`execution_contract.md`](execution_contract.md), and CodeMirror 6 plus the
responsive layout comes from
[`editor_evaluation.md`](editor_evaluation.md).

## Alternatives rejected at this stage

- A special Python route with no authored Markdown source would bypass current
  navigation, companion, LLM, git-metadata, and guard conventions.
- A `full_width: true` collection of unrelated booleans would permit invalid
  combinations and would not establish a reusable page type. Use the closed
  layout value.
- A large `if playground` branch inside the current monolithic `DocPage` would
  retain narrative-only coupling and leave mobile primary navigation attached
  to a sidebar the page does not have. Extract the shared shell.
- Loading CodeMirror or the runner bootstrap on every docs page would impose
  application cost on readers who never use live code. Use typed page features.
- Serving the Python Worker from the docs origin would expose docs-origin
  credentials in the tested browsers. Keep the accepted separate runner origin.
- Resolving Citry from PyPI or Pyodide at page startup would make the same page
  change according to registry and cache state. Promote exact bytes first.
- Adding `/v/<version>/playground/`, even as a redirect, would create a
  versioned route identity for a product that intentionally has only one
  current runtime. Snapshot navigation should link to the root directly.

## Canonical route and navigation

Add the area after Reference and before Community:

```yaml
  - label: Try it
    scope: site
    items:
      - { title: Playground, path: /playground/ }
```

The resulting progression is Docs, Examples, Reference, Try it, Community, and
Blog. The navigation label is the short call to action. The page title can be
the clearer `Try Citry`.

`scope: site` is the publication rule. The current `NavTree.project_path()`
keeps a site-scoped path at the root even while rendering a snapshot. The
current version build's Markdown file selection omits site-scoped routes before
rendering. Its build stamp also records `/playground/` and the site-scoped
`/playground/*` namespace as root-owned route patterns.

The following are required invariants:

1. A root build writes `playground/index.html` and
   `playground/index.md`.
2. A live server request for `/playground/` renders the same layout and config.
3. A snapshot build writes neither of those paths below its output directory.
4. A newly built snapshot's Try it link is `/playground/`, or
   `<DOCS_BASE_PATH>/playground/` after the final base-path pass.
5. No version alias mirrors a playground page because the target snapshot has
   no such page.
6. `/v/<version>/playground/` is not emitted, redirected, canonicalized,
   indexed, or added to a sitemap or LLM file. A direct request may reach the
   site's ordinary 404 behavior.
7. Existing committed snapshots remain immutable. They do not acquire a new
   header link until rebuilt under normal snapshot policy.

This is a product policy, not an initial rollout choice. Historical playground
support is not left as an implicit future mode.

## Authored page and text projections

Create [`docs_site/content/playground.md`](../../../docs_site/content) with the
following shape:

```markdown
---
title: Try Citry
description: Edit and run a self-contained Citry component in your browser.
layout: playground
---

Edit one self-contained Python module and see its rendered HTML without setting
up a local project.

The final expression becomes the preview. End with a component, a rendered
Citry value, or an HTML string. In a normal Python script, use `str(...)` or
`print(...)` when you want terminal output.

Use **Run** at any time, or turn on **Auto-run** to update after edits. The
playground uses one pinned current Citry browser release and does not represent
the version selected in historical documentation.

When you are ready to build a project, continue with [Your first
component](getting-started/your-first-component.md).
```

The exact editorial wording remains reviewable, but the content contract is
fixed:

- the browser page renders the title and short description in its application
  header and exposes the remaining prose in an accessible Help surface;
- the same authored body becomes the Markdown companion and LLM full-text
  projection;
- the text projection explains final-expression behavior and the single pinned
  current runtime without hardcoding a package version in prose;
- the runtime version shown in browser chrome comes from the machine-readable
  runtime lock, so it cannot drift from the loaded artifacts;
- edited source, stdout, diagnostics, iframe markup, and transient runtime state
  never enter generated Markdown or LLM files.

The starter module has one source of truth at
`docs_site/playground/starter.py`. The builder reads it as UTF-8 text and places
it in the server-rendered fallback `<textarea>`. JavaScript upgrades that same
control into CodeMirror. Reset restores the originally rendered text. Do not
embed a second copy in a script tag or frontend bundle.

The first release does not persist the source draft across a full reload. This
keeps initial behavior deterministic and avoids silently restoring and running
old code. Source remains in memory through panel switches and runtime restarts.
Reset, Copy, and Download preserve recovery. Draft persistence can be designed
later if reader testing establishes a need.

## Closed layout schema

Add a closed layout type to `PageMeta`:

```python
class PageLayout(str, Enum):
    DOCS = "docs"
    PLAYGROUND = "playground"
```

Omitted `layout` means `docs`. `layout: playground` selects
`PlaygroundPage`. Empty or any other value is a build error. The error names the
source and accepted values, for example:

```text
playground.md: invalid layout 'playgound'; expected one of: docs, playground
```

This validation must run in `parse_page()` or immediately after it, not only in
`build-check`, because an ordinary `build` or live render must not silently
choose the wrong chrome. Pass a source label to parsing so errors remain useful.
The front-matter guard should also understand string-backed `Enum` values and report the
same accepted set before a post-build pass.

Blog catalog pages construct `PageMeta` programmatically and keep the default
`docs` layout. Generated Reference, release, 404, and redirect pages also stay
on their current layouts.

Layout selection is not a generic component name and does not accept arbitrary
imports. Adding another layout requires a source change, renderer branch, and
tests.

## Document shell and page components

Extract shared chrome instead of adding a large conditional inside `DocPage`.
The intended component hierarchy is:

```text
DocumentShell
  head metadata and common CSS
  SiteHeader
  MobilePrimaryNav
    optional page-specific secondary navigation slot
  page body slot
    DocPageBody
      docs sidebar, prose, TOC, page nav, footer
    or
    PlaygroundWorkspace
      application toolbar, editor panel, preview panel, diagnostics
  SearchModal
  common site scripts and collected feature assets
```

`DocumentShell` owns the doctype, `<html>`, head metadata, theme bootstrap,
favicons, common styles, header, mobile primary drawer, search modal, common
scripts, and `<c-css>` or `<c-js>` placement. It accepts a page-kind value so
metadata can differ without duplicating the whole head.

`SiteHeader` owns the desktop primary navigation and existing search, theme,
social, and overflow controls. Its hamburger targets the shared mobile drawer,
not `djc-sidebar`. `MobilePrimaryNav` always renders the primary links. `DocPage`
supplies its section navigation into the drawer; `PlaygroundPage` leaves that
slot empty. This preserves mobile navigation without rendering a fake docs
sidebar.

`DocPage` keeps all narrative-only behavior: breadcrumbs, title injection,
mobile and desktop TOC, previous and next cards, blog metadata, version picker,
and footer. Its rendered output should remain structurally compatible except
for the extracted component boundaries.

`PlaygroundPage`:

- has one visible H1, `Try Citry`, in the application header;
- has one named `<main>` landmark;
- renders no documentation version picker because the route is site-scoped;
- renders the pinned Citry and Pyodide versions from build configuration;
- supplies the authored explanatory HTML to Help and a small Pagefind region;
- supplies the starter source and a SHA-256 source fingerprint;
- renders a non-JavaScript source fallback and a clear execution-unavailable
  message;
- references only the page features collected for this route.

Keep component composition inside one Citry render tree so nested component CSS
and JavaScript still reach the document dependency placeholders. Do not
pre-render an inner component to an unrelated string and then insert it into the
shell.

## Page feature collection and conditional assets

Introduce a typed page-feature collector rather than placing playground asset
paths directly in `PlaygroundPage`:

```text
PLAYGROUND_WORKSPACE
INLINE_LIVE_ACTIVATOR   (reserved for Stage 9)
```

The layout automatically requires `PLAYGROUND_WORKSPACE`. A future
`<c-live-code>` component can require `INLINE_LIVE_ACTIVATOR` during the Citry
content pass. Authors do not set features in front matter.

A feature registry resolves each feature to hashed, self-hosted styles and
module scripts from `docs_site/static/generated/asset-manifest.json`.
`DocumentShell` emits the deduplicated resources after the content and layout
passes have completed. Missing entries, duplicate logical names, unsafe paths,
or hash mismatches fail the build.

The loading contract is:

| Page | Initial extra assets | Deferred assets |
| --- | --- | --- |
| Ordinary Docs, Examples, Reference, Community, Blog | None | None |
| `/playground/` | Workspace CSS and the small application entry, which then loads CodeMirror chunks | Cross-origin runner broker, Pyodide, wheels, and WASM according to the Stage 6 loading candidate |
| Future page with static live-code tags | Small inline activator only | Editor and runtime after explicit **Try live** |

The generated same-origin application files use content-hashed filenames. The
page may carry SRI for those ordinary `<script>` and `<link>` requests. SRI is
not treated as verification for Worker-fetched runtime files.

## Private frontend package and module boundaries

Add `docs_site/_internal/frontend` as a private pnpm workspace member. Pin all direct and
transitive packages in the root `pnpm-lock.yaml`. Use the selected CodeMirror
versions from Stage 4 and the repository's existing esbuild version unless an
implementation proof establishes a reason to change it.

Proposed source graph:

```text
docs_site/_internal/frontend/
  package.json
  tsconfig.json
  build.mjs
  src/
    entries/
      playground.ts
      inline-live-activator.ts
      runner-page.ts
      preview-page.ts
      runtime-worker.ts
    host/
      browser-session.ts
      runtime-descriptor.ts
      runner-connection.ts
      protocol.ts
      scheduler.ts
      state-machine.ts
      limits.ts
      diagnostics.ts
      preview-frame.ts
    editor/
      editor.ts
      citry-language.ts
      citry-language-data.ts
      themes.ts
    consumers/
      playground-workspace.ts
      inline-live-code.ts
    runner/
      broker.ts
      worker-session.ts
      runtime-loader.ts
      preview-shell.ts
      executor.py
  tests/
    ...
```

The names can be adjusted during implementation, but the dependency direction
is required:

```text
consumer adapter -> browser host -> bounded protocol
                                  -> runner broker -> Worker -> Python executor
consumer adapter -> editor adapter
consumer adapter -> preview and diagnostics views
```

Host modules do not query playground DOM ids, write splitter values, choose a
storage key, or assume that code and result are simultaneously visible. The
consumer supplies source and view callbacks. Host modules also fetch no
Pyodide or wheel bytes; the verified loader executes inside the runner-owned
Worker, where those artifacts are same-origin.

The narrow public interface within the private package should resemble:

```ts
type BrowserSessionOptions = {
  consumerId: string;
  runtime: RuntimeDescriptor;
  capabilities: readonly Capability[];
  limits: SessionLimits;
  onState(state: SessionState): void;
  onResult(result: RenderResult): void;
  onDiagnostic(diagnostic: Diagnostic): void;
};

interface BrowserSession {
  prepare(): Promise<void>;
  run(source: string, reason: "initial" | "manual" | "auto" | "reset"): Promise<void>;
  stop(reason: "user" | "timeout" | "dispose"): Promise<void>;
  dispose(): Promise<void>;
}
```

Every protocol envelope carries protocol version, runtime bundle id, consumer
id, session id, generation id, run id, message type, and bounded payload. The
Stage 8 Events extension adds capability-specific event ids without changing
those identities.

The Python executor implements the accepted AST algorithm and output
normalization from Stage 3. It is loaded as a hashed runtime artifact, not
constructed by prefixing text to visitor source.

## Workspace and diagnostics contract

The application body fills the viewport below the existing fixed 4rem header.
Use a dynamic viewport CSS variable based on `visualViewport.height` with
`100dvh` and `100vh` fallbacks. The document body does not scroll; each editor,
preview, Help surface, and diagnostic tray owns its own overflow.

At wide and sufficiently tall viewports:

- code and result panels start at 50/50;
- the separator clamps the code panel to 30 through 70 percent;
- pointer and touch dragging use pointer capture;
- the focusable separator uses `role="separator"`, orientation, current value,
  text value, and min and max values;
- Arrow keys move one percent, Shift plus Arrow moves ten percent, Home and End
  reach the limits, and Enter or double-click restores 50/50;
- the saved split uses a schema-versioned local key, clamps corrupt values, and
  falls back to 50.

At widths at or below 56rem, heights at or below 28rem, or when zoom makes both
panels unusable, show one panel at a time with explicit Code and Result
controls. Switching panels does not rerun Python or dispose the live generation.
The small-screen header drawer contains all primary navigation even though the
docs sidebar is absent.

Run is always visible. `Ctrl+Enter` or `Cmd+Enter` invokes it. Auto-run is a
separate labelled toggle. Copy, Download, Reset, Help, an equal-panes control,
runtime state, and the pinned version badge are first-release toolbar controls.
Share, format, and a general file system remain out of scope.

Use persistent, in-flow panel diagnostics rather than toast-only errors:

- Python parse, execution, render, output-type, loading, and Worker failures
  belong to the code panel;
- stdout and stderr remain separate protocol fields; when either is nonempty,
  the code tray shows a non-error captured-output notice with counts and
  truncation state even while the expandable console is deferred;
- preview script, promise, resource, navigation, and protocol failures belong
  to the result panel;
- each tray has a concise summary, expandable sanitized details, Copy, and
  dismissal when dismissal is safe;
- a short `aria-live` announcement may accompany a change, but it never replaces
  the tray;
- the last successful preview remains visible and is labelled stale while a
  run is pending, stopped, timed out, or failed;
- a successful current run clears superseded diagnostics for its owning panel.

Stage 6 rejects host-owned `srcdoc` for production because it inherits the docs
response CSP and cannot relax that policy for visitor inline CSS and
JavaScript. The preview is instead a fixed content-addressed document on the
credential-free, different-site runner origin, still embedded with `sandbox="allow-scripts"`
without `allow-same-origin` and with a title. The immutable page contains its
small trusted bootstrap inline; no external script origin is allowed. The
bootstrap transfers a private MessagePort, accepts bounded HTML, activates
visitor content under a preview-specific restrictive CSP, and forwards the
bounded error classes accepted in Stage 1. A runner-origin script-source probe
must produce no server request. It cannot promise to observe every possible
browser failure. Unexpected navigation
disconnects the port and replaces the document with an inert frame; the next
successful run creates a new preview session. See
[`vertical_prototype.md`](vertical_prototype.md#preview-architecture-correction).
Self-navigation and download activation can still issue docs-origin requests,
and visitor Python can retain visitor-created runner-origin IndexedDB or Cache
Storage data across Worker restarts and tabs. V1 accepts and discloses these
residuals only for locally edited code; production tests exercise them with the
real origins, cookies, request logs, and storage cleanup.

## Auto-run policy and local instrumentation

Stage 5 defined two complete, testable candidates while preserving an explicit
Run control in both:

| Behavior | Candidate A: guided live | Candidate B: run on demand |
| --- | --- | --- |
| First visit | Prepare after first paint, run starter when ready | Do not load the heavy runtime until Run |
| Auto-run default | On | Off |
| Edit debounce candidates | 500 ms, with the newest source replacing queued work | 800 ms after the visitor turns it on |
| Explicit Run | Immediate and bypasses debounce | Immediate and bypasses debounce |
| Returning visitor | Honor only an explicit stored Auto-run choice | Honor only an explicit stored Auto-run choice |
| Syntax or render failure | Keep Auto-run selected and show stale result | Same |
| Timeout, crash, or user Stop | Pause scheduling until explicit Run | Same |

The persistence key is a settings-schema version, not a Citry or docs version,
for example `citry.playground.settings.v1`. Store only the explicit Auto-run
choice and splitter value. Storage failure uses the active candidate default
and does not block editing or Run.

Stage 6 selected Candidate B for the initial implementation, with Auto-run off,
an always-visible Run control, a persisted explicit Auto-run choice, a 500 ms
latest-source debounce after opt-in, and a five-second execution timeout.
These values are rollout-tunable defaults rather than architectural contracts.

Instrumentation uses browser Performance marks, measures, and a test-only
`CustomEvent` stream. Record phase, duration, candidate, cache state, reason,
and normalized outcome code. Do not record source, rendered HTML, stdout,
stderr, exception messages, tracebacks, or user identifiers. Production
telemetry remains off until a separate privacy review defines a destination,
retention, disclosure, and opt-out. The test harness can collect local events
without a network request.

## Stop, timeout, and restart

Version 1 should expose Stop. While a run is active, Run remains visible but is
disabled and Stop is visible and enabled. Stop is a hard lifecycle operation:

1. The host invalidates the current generation and run ids.
2. The runner terminates the Python Worker. It does not rely on a cooperative
   Python exception.
3. Late messages from the old Worker are ignored.
4. The last successful preview remains visible and is marked stale with a
   `Stopped` status.
5. The runner creates a clean Worker lazily for the next explicit Run.
6. Auto-run retains the visitor's toggle choice but enters a paused state. One
   explicit Run clears the pause; later edits may auto-run again.

The hard timeout and Worker crash use the same termination and stale-preview
path, with different diagnostic codes. Syntax, validation, and normal render
failures do not terminate a healthy Worker or pause Auto-run. Reset during a run
first stops the generation, restores the authored starter, and follows the
selected initial-run policy. Reset while idle also terminates the warm Worker,
so the restored starter runs in a clean interpreter.

This contract is more understandable than a timeout-only interface and matches
the hard-cancellation mechanism the Pyodide proof can actually guarantee.

## Build configuration and base paths

Add a playground config object loaded by `DocsConfig`:

```text
runtime lock path       docs_site/playground/runtime-lock.json
runner origin           committed canonical origin, with DOCS_PLAYGROUND_RUNNER_ORIGIN override
application asset map   docs_site/static/generated/asset-manifest.json
starter path            docs_site/playground/starter.py
```

After the Stage 1 deployed-origin gate passes, `DocsConfig` records that
canonical origin as its default so an ordinary static build and live server
remain usable without extra setup. `DOCS_PLAYGROUND_RUNNER_ORIGIN` is an
absolute-origin override for local development and preview builds; it allows no
credentials, query, fragment, or unexpected path. The production workflows
assert the canonical value and cannot silently deploy against a developer
override. Before the canonical origin is accepted and configured, enabling the
playground layout is a build error rather than a fallback to the docs origin.
The runtime lock, bundle id, protocol version, package tuple, and hashes are
committed inputs, not environment overrides.

The builder produces one escaped `application/json` configuration block for
the page containing:

```json
{
  "schemaVersion": 1,
  "docsBasePath": "/citry",
  "assetBaseUrl": "/citry/static/generated/playground/",
  "runnerUrl": "https://runner.example/runtime/<bundle-id>/runner.html",
  "previewUrl": "https://runner.example/runtime/<bundle-id>/preview.html",
  "runtimeManifestUrl": "https://runner.example/runtime/<bundle-id>/manifest.json",
  "runtimeBundleId": "<bundle-id>",
  "protocolVersion": 1,
  "packages": {"citry": "<exact>", "citry-core": "<exact>", "pyodide": "314.0.3"}
}
```

All same-origin URLs are constructed in Python from the normalized
`DOCS_BASE_PATH` before serialization. The final HTML base-path pass remains
idempotent for ordinary attributes. Runtime JavaScript resolves relative
resources from the injected URLs or `import.meta.url`, never from a root literal
or `location.pathname` guess. The cross-origin runner URL is absolute and is
not prefixed by the docs base path.

Serialize JSON with `<`, `>`, `&`, and line-separator characters escaped so
visitor-controlled or authored text cannot end the script element. Parse and
validate once during startup. A missing field, wrong bundle id, unsupported
schema or protocol, or invalid URL produces a persistent code-panel
configuration diagnostic and no runner handshake.

For local development, run the docs server and the compiled runner on distinct
ports, for example:

```sh
pnpm --dir docs_site/_internal/frontend dev:runner --port 8011
DOCS_PLAYGROUND_RUNNER_ORIGIN=http://127.0.0.1:8011 \
  uv run --no-sync python -m docs_site serve
```

The docs server does not silently switch the runner onto its own origin.

## Immutable runtime lock and artifact graph

`docs_site/playground/runtime-lock.json` replaces the research manifest as the
production input. The research file remains evidence and is not loaded by the
site. The production lock records:

- schema and protocol versions;
- bundle id algorithm and resulting bundle id;
- canonical docs and runner origins, their private-PSL-aware schemeful sites,
  and exact `frame-ancestors` values;
- exact Citry, Citry Core, Pyodide, Python, Emscripten, Rust, Maturin,
  `pyodide-build`, and supporting package versions;
- source tag and peeled commit for built Citry artifacts;
- filename, byte size, SHA-256, media type, and source URL for every artifact;
- license identifier, notice source, and required license text for every
  redistributed artifact;
- deterministic install order with dependency resolution disabled;
- runner page, broker, preview page and bootstrap, Worker, Python executor,
  Pyodide JavaScript, lock file, standard library, WASM, and wheel inventory;
- required response headers and Content Security Policy;
- the acceptance smoke-test digest and timestamp.

The bundle id is SHA-256 over a canonical serialization of the lock's immutable
inputs, excluding the bundle-id field itself. The generated manifest includes
that id and a complete file inventory. The remote directory is:

```text
https://<runner-origin>/runtime/<bundle-id>/
  manifest.json
  runner.html
  preview.html
  assets/
    broker.<hash>.mjs
    worker.<hash>.mjs
    executor.<hash>.py
  pyodide/
    pyodide.mjs
    pyodide.asm.mjs
    pyodide.asm.wasm
    python_stdlib.zip
    pyodide-lock.json
  wheels/
    citry-<exact>-py3-none-any.whl
    citry_core-<exact>-cp314-cp314-pyemscripten_2026_0_wasm32.whl
    <exact transitive wheels>
  THIRD_PARTY_NOTICES.txt
  licenses/
    <artifact-specific license files>
```

No `latest`, floating PyPI URL, live dependency resolver, or mutable file path is
part of page startup. The production loader must consume the bodies whose sizes
and SHA-256 values it verified, not let Pyodide re-fetch their URLs. A
mutation-between-fetches test enforces that boundary. The release smoke test
repeats verification through the public origin. Browser caching uses:

- immutable bundle files: `Cache-Control: public, max-age=31536000, immutable`;
- the content-addressed manifest: the same immutable policy;
- no cookies, authentication, personalized responses, or state-changing routes
  on the runner origin;
- explicit MIME types, `nosniff`, no referrer, the accepted runner and preview
  CSPs, and exact docs-origin `frame-ancestors`. The lock stores the complete
  policy for every response class. Runner HTML permits only its same-origin
  script and Worker; the Worker policy retains the tested `blob:`,
  `'unsafe-eval'`, and `'wasm-unsafe-eval'` script sources plus same-origin
  connect while verified-buffer startup needs them. Runtime files remain
  runner-to-runner same-origin resources rather than receiving broad CORS.

Selecting the production provider and canonical different-site origin is the
entry gate for implementation slice 5. Its deployment record owns credentials,
staging, atomic promotion, headers, and rollback. The earlier page, editor, and
local host slices do not depend on that provider.

## Release and deployment order

The PyEmscripten build is another wheel in the existing `citry-core` PyPI
release. It is not a separate package or a docs-only wheel. Matching Pyodide
installers can select its platform tag; native installers ignore it.

The accepted first release plan is now:

1. Completed on 2026-07-28: upload the reproducible,
   stock-Pyodide-tested 1.4.0 PyEmscripten wheel to the existing
   `citry-core==1.4.0` release. Citry 0.3.0 already exactly pins that core
   version.
2. Completed on 2026-07-28: verify the expected core filename, size, and hash
   from PyPI, then rerun the exact 0.3.0/1.4.0 package smoke from those public
   bytes. The public file is byte-identical to the three-browser matrix input.
3. The fallback was not needed. If a comparable late file cannot be added in
   the future, publish a new core version and a new Citry patch that pins it,
   then repeat the acceptance matrix.
4. Assemble a runtime bundle only from the exact published wheel bytes and the
   pinned Pyodide files. Build it twice and require identical manifests and
   content hashes.
5. Upload the complete bundle to a staging content-addressed path. Verify every
   byte through the public staging endpoint.
6. Promote the exact immutable directory to the production runner origin.
   Promotion must not rewrite bytes.
7. Run the deployed cross-origin broker, containment, browser, package, and
   header matrix against that exact bundle.
8. Emit the verified runtime lock as a workflow artifact after steps 1 through
   7 pass. Apply it through an ordinary maintainer branch and reviewed merge,
   or an explicitly configured GitHub App token. Do not rely on a default
   `GITHUB_TOKEN` commit to trigger downstream checks or deployment.
9. Build the root docs artifact, verify that its configured bundle already
   exists publicly, then deploy the Pages artifact atomically.

The docs page is therefore always the last artifact published. A failed runner
promotion cannot produce HTML that references missing files. A normal docs
redeploy does not rebuild or mutate the runtime bundle.

Suggested CI ownership:

- `.github/workflows/py--citry-core--publish.yml` owns the PyEmscripten wheel,
  reproducibility, inventory, stock-Pyodide core smoke, attestations, and PyPI
  upload with the other core artifacts;
- `.github/workflows/py--citry--publish.yml` owns the exact public Citry package
  browser matrix after core is available;
- a new `.github/workflows/repo--playground-runtime.yml` owns bundle assembly,
  immutable upload, public verification, and the protected
  `playground-runtime` deployment environment;
- `repo--docs-check.yml` owns frontend generated-output checks, manifest schema,
  page build, guards, and browser tests without publishing;
- `repo--docs-deploy.yml` and `repo--docs-release.yml` verify that the committed
  bundle is already public, then deploy root docs and snapshots. A docs release
  still does not create a versioned playground.

The frontend build writes content-hashed application assets and
`asset-manifest.json` under `docs_site/static/generated/`. Commit those generated
files, as the repository already does for the Citry client build output, so an
ordinary Python docs build remains reproducible. `pnpm ... check:generated`
rebuilds into a temporary directory and fails on drift. Docs check and deploy
workflows install the pinned pnpm workspace and run that check before Python
build steps.

Production runtime bundles have no automatic deletion. Removal requires an
explicit inventory proving that no current page, rollback artifact, cached
release artifact, or supported deployment references the bundle. Keeping all
promoted bundles is the default. This turns a docs rollback into an HTML deploy,
not an emergency runtime rebuild.

## Search, SEO, social, and machine-readable output

The root playground is an ordinary recorded page with layout-specific
projection rules:

| Output | Contract |
| --- | --- |
| Canonical | Exactly `<site-root>/playground/`; never a `/v/` URL. |
| Robots and sitemap | `index,follow` and one root sitemap entry unless editorial review explicitly changes it. |
| Open Graph | `og:type=website`, title and description from front matter, and the normal generated Citry social card. Social-card rendering uses `OgCard` directly and never loads the editor or runtime. |
| Structured data | No docs `Article` JSON-LD. Add no application schema until the shipped feature and claims can satisfy it accurately. |
| Pagefind | Index title, description, and authored Help copy. Mark editor source, controls, status, diagnostics, and iframe with `data-pagefind-ignore`. |
| Markdown companion | `/playground/index.md` with front matter and the concise authored body. No application markup or starter duplication. |
| `llms.txt` | One **Try it** link in navigation order with the page description. |
| `llms-full.txt` | The concise authored body, not runtime state. |
| Docs version picker | Hidden because the page is site-scoped. |

Snapshot builds produce none of these for a versioned playground. Root
Pagefind and LLM files contain the one current page only.

## Failure contracts at the integration boundary

| Failure | Required result |
| --- | --- |
| Generated application asset absent or hash mismatched | Fail docs build or guard before deployment. |
| Runtime lock malformed or contains a floating dependency | Fail lock validation before frontend or docs build. |
| Config contains an invalid runner origin or base path | Fail page rendering with a source-located configuration error. |
| Public runtime bundle is absent during docs deploy | Stop before Pages artifact upload. |
| Runtime manifest or file hash fails in browser | Do not start Python. Keep source copyable, name the failed phase, and offer Retry. |
| Protocol or bundle id differs during handshake | Reject the runner, dispose it, and show a persistent code-panel diagnostic. |
| User presses Stop, run times out, or Worker crashes | Invalidate the generation, terminate the Worker, preserve stale output, pause Auto-run until explicit Run, and create a clean Worker next time. |
| CodeMirror fails | Keep the authoritative named textarea, Copy, Download, Reset, and Retry editor controls. Run remains available only if the full latest source and runner health are known. |
| Preview reports a client failure | Preserve the safe DOM where possible and show the persistent right-panel diagnostic. |
| Preview JavaScript loops forever | The Python timeout does not contain it. Attempt replacement only if the parent event loop remains responsive; otherwise document tab reload as the v1 recovery. |
| Preview self-navigation or download activation issues a request | The parent cannot prevent the first request. Keep docs static and credential-free, test cookie and log behavior in all engines, disclose the residual, and reopen the design before docs gains sensitive GET endpoints. |
| Python uses runner-origin IndexedDB or Cache Storage | Application code stores nothing there. Test persistence and cross-tab visibility with real operations, clean up test keys, disclose the residual, and require a new decision before shared code. |
| Python writes stdout or stderr | Return both fields and show a left-tray notice with counts and truncation state; never use either as preview HTML. |
| Snapshot build contains `playground/index.html` | Fail the snapshot test or version guard and do not commit the snapshot. |
| Historical page links to a versioned playground | Fail link or version guards. Link to the canonical current page with current-runtime wording instead. |

## Proposed repository changes

The implementation should be reviewable in slices. The complete expected graph
is:

```text
docs_site/content/playground.md
docs_site/content/_nav.yml
docs_site/playground/starter.py
docs_site/playground/runtime-lock.json
docs_site/playground/DEPLOYMENT.md
docs_site/playground/THIRD_PARTY_NOTICES.md
docs_site/_internal/frontend/**
docs_site/static/generated/asset-manifest.json
docs_site/static/generated/playground/*

docs_site/_internal/frontmatter.py
docs_site/_internal/config.py
docs_site/_internal/features.py
docs_site/_internal/assets.py
docs_site/_internal/pipeline.py
docs_site/_internal/build.py
docs_site/_internal/serve.py
docs_site/_internal/components/document_shell.py
docs_site/_internal/components/site_header.py
docs_site/_internal/components/mobile_primary_nav.py
docs_site/_internal/components/doc_page.py
docs_site/_internal/components/playground_page.py
docs_site/_internal/guards/playground.py
docs_site/_internal/guards/__init__.py

docs_site/tests/test_frontmatter.py
docs_site/tests/test_pipeline.py
docs_site/tests/test_chrome.py
docs_site/tests/test_build.py
docs_site/tests/test_assemble.py
docs_site/tests/test_assets.py
docs_site/tests/test_base_path.py
docs_site/tests/test_playground.py
docs_site/tests/e2e/test_playground_e2e.py

pnpm-workspace.yaml
pnpm-lock.yaml
scripts/check.py
.github/workflows/py--citry-core--publish.yml
.github/workflows/py--citry--publish.yml
.github/workflows/repo--check.yml
.github/workflows/repo--playground-runtime.yml
.github/workflows/repo--docs-check.yml
.github/workflows/repo--docs-cross-browser.yml
.github/workflows/repo--docs-deploy.yml
.github/workflows/repo--docs-release.yml
```

Not every file must land in one change. The preferred sequence is:

1. typed layout, shell extraction, page render, site scope, and snapshot
   absence tests with a textarea-only workspace;
2. private frontend package, generated asset manifest, CodeMirror, responsive
   panels, and fallback;
3. consumer-neutral host and the Stage 3 Python executor against a local
   immutable bundle;
4. runner-origin deployment workflow and exact public package lock;
5. page connection, diagnostics, Stop, reset, base paths, projections, and full
   static e2e coverage;
6. Stage 7 activation checks, including the public bundle, all three engines,
   final navigation, and one physical-phone smoke, before production rollout.

## Verification matrix

### Unit and render

- omitted, `docs`, `playground`, empty, misspelled, and unknown layout values;
- source-located invalid-layout errors in ordinary build and live render;
- common head and header parity after extraction;
- active Try it state in desktop and mobile primary navigation;
- playground H1 and main landmark, with no docs sidebar, breadcrumb, TOC,
  page navigation, footer, or version picker;
- help, starter, fallback textarea, config JSON escaping, and pinned version
  badge;
- feature deduplication and no playground features on ordinary pages;
- consumer-neutral API, state transitions, identities, limits, and stale-run
  rejection;
- AST execution and normalized result matrix from Stage 3 inside the pinned
  Pyodide Worker;
- Stop, timeout, crash, restart, queued edit, and Auto-run pause behavior;
- persistent panel diagnostics and sanitized traceback projection.

### Build, version, and assets

- root build emits HTML and Markdown companion at `/playground/`;
- live server renders the page and route-only asset URLs;
- domain-root and non-empty `DOCS_BASE_PATH` builds resolve every application,
  runner, manifest, Worker, Pyodide, wheel, and WASM URL;
- snapshot build emits no playground HTML, companion, content asset, redirect,
  Pagefind record, sitemap URL, social card, or LLM section below `/v/`;
- new snapshot top navigation links to the root playground;
- version aliases do not mirror a playground route;
- application asset manifest filenames, sizes, hashes, SRI, and generated-output
  drift checks;
- runtime lock canonicalization, bundle id, exact install order, no floating
  URLs, and public-byte verification;
- docs deployment preflight fails before upload when a runtime artifact is
  absent or different.

### Browser, accessibility, and product

- complete Stage 6 matrix in Chromium, Firefox, and WebKit against minified
  static output and the deployed runner origin;
- no failed requests, no docs-origin credentials at the runner, and expected
  CSP and cache headers;
- first load, warm run, rapid edits, old-run rejection, Stop, timeout, reset,
  reload, offline, missing file, and hash substitution;
- pointer, touch, keyboard, RTL, 320 CSS pixels, 400 percent zoom, forced
  colors, reduced motion, soft keyboard, and visual viewport changes;
- one-panel switching preserves source, preview, focus, and live generation;
- screen-reader review of editor escape behavior, separator values, states,
  diagnostics, and live announcements;
- moderated comparison of Auto-run candidates and first-reader success;
- uncached physical mid-tier mobile timings, heap pressure, termination
  recovery, and the accepted product budgets.

## Iterative rollout work and falsifying conditions

Stage 5 is complete because the repository, page, artifact, version, release,
and failure behavior are now specified. The following work belongs to release
and rollout rather than blocking the first implementation.

Release and rollout should:

- repeat the broker and preview proof on the real runner origin and headers;
- put deterministic PyEmscripten builds and comparison into release CI;
- measure uncached and physical mid-tier mobile behavior;
- promote and verify the first immutable public runtime bundle.

Reopen this integration design if any of the following occurs:

- the real host cannot provide immutable paths, exact headers, or a
  credential-free origin;
- page-specific assumptions are required inside the browser host to support the
  full-page consumer;
- the runtime bundle cannot be verified before the docs deployment references
  it;
- shell extraction materially changes ordinary docs behavior and a smaller
  composition model preserves reuse more safely;
- site scope does not exclude every snapshot artifact in the production build;
- Stage 6 shows that Stop and clean restart cannot recover within an acceptable
  time;
- CodeMirror or the route-only application cost exceeds the accepted budgets.

None of those conditions changes the fixed route policy. There remains one
unversioned `/playground/` with one pinned current runtime.
