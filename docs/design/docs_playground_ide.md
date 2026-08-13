# Browser IDE support for the docs playground

**Status:** Phase 1 and the Phase 2A catalog slice are implemented. This
document defines the target architecture and the confidence rules that later
slices must preserve.

The browser playground should explain Citry while the visitor is writing it,
not only after Python runs. It should report Citry parser and lint findings,
complete framework names, explain them on hover, and navigate between authored
declarations and uses. Python type intelligence and ordinary HTML, CSS, and
JavaScript help should follow without turning the playground into a second,
independent implementation of the desktop language server.

The browser can provide this experience locally. Citry's parser and OXC-backed
browser analysis already run as WebAssembly in Pyodide, and Ruff includes a
WebAssembly build of ty. The existing `citry-lsp` process cannot run unchanged:
its app loader and Python type provider launch native child processes, while a
browser Worker has no operating-system process model. The browser and desktop
therefore share analysis behavior below their transports, then use adapters
suited to each environment.

## Prior art

Citry already contains unstable Ruff crates behind its own contracts:

- The workspace points `ruff_python_parser`, `ruff_python_formatter`, and the
  other selected crates at one pinned Ruff submodule (`Cargo.toml:46-63`).
- The template formatter calls those internal Rust APIs directly, then
  reparses and compares their output before accepting it
  (`crates/citry_template_formatter/src/python.rs:14-105`).
- Citry exposes a stable provider identity rather than Ruff's internal types
  (`crates/citry_template_formatter/src/python.rs:34-35`).
- The PyO3 module publishes Citry-owned functions, classes, constants, and
  errors. Ruff values do not cross that boundary
  (`crates/citry_core_py/src/lib.rs:40-150`).

The browser ty integration follows the same rule. Ruff's `ty_wasm` crate owns
an in-memory workspace and exports open, update, diagnostics, completion,
hover, navigation, references, and signature operations
(`third_party/rust/ruff/crates/ty_wasm/src/lib.rs:109-230`). It is an internal,
unpublished crate with version `0.0.0`
(`third_party/rust/ruff/crates/ty_wasm/Cargo.toml:1-4`). CodeMirror and Citry
features must not depend on those raw classes or response shapes.

A small Citry-owned adapter will:

1. create and update the ty workspace;
2. translate Citry's UTF-16 positions and virtual Python documents;
3. validate every response before mapping it to authored source;
4. return a narrow set of Citry records for completion, hover, diagnostics,
   signature help, and navigation;
5. report the pinned Ruff commit as provider identity; and
6. turn startup, panic, invalid response, and stale-generation failures into
   one unavailable provider rather than partial answers.

This is not a different dependency policy from `citry_core`. It applies the
same containment policy to a WebAssembly and JavaScript boundary. A Ruff
upgrade may require changes inside the adapter, while the editor Worker
protocol and CodeMirror integration remain unchanged.

## Product scope

The browser IDE has three independently useful layers.

### Citry-owned analysis

This layer provides parser diagnostics and every result whose meaning Citry
owns:

- structural tags, directives, and nested templates;
- registered components, inputs, slots, slot data, and events;
- template roots and parser-proven loop or fill bindings;
- Alpine scope, Citry browser APIs, `$c-props`, `JsData`, and `CssData`;
- Citry lint rules and their configured severities;
- hover, completion, declaration, definition, references, type definition,
  and signature help where the same source proof exists on desktop.

Portable rules belong in `citry.analysis` or another editor-neutral Citry
module. The desktop pygls adapter and browser Worker call those rules. Neither
adapter reimplements them in TypeScript.

### Python type analysis

The browser builds the same mapped shadow Python documents as the desktop LSP.
A narrow provider interface sends them to native `ty server` on desktop and to
the Citry `ty_wasm` adapter in the browser. Both providers return the same
validated Citry records.

The browser workspace must contain the selected Python target, ty's vendored
typeshed, and typing sources for Citry and any playground package that can be
imported. Installing a package into Pyodide does not automatically add it to
ty's separate in-memory filesystem.

### Ordinary web-language help

VS Code currently asks its installed HTML, CSS, and JavaScript providers about
Citry's mapped virtual documents. A browser does not have those providers.
Close parity requires browser adapters for the HTML and CSS language services
and a JavaScript or TypeScript language service. CodeMirror's existing parsers
remain responsible for immediate syntax highlighting.

This layer is separate from Citry-owned Alpine, event, props, and data checks.
It can be loaded later if its download and memory cost passes the playground's
budgets.

## Runtime architecture

```text
CodeMirror
    |
    | versioned browser IDE requests and results
    v
Citry analysis Worker
    |-- Citry parser and OXC-backed analysis
    |-- current source-only facts
    |-- current successful catalog snapshot
    `-- lazy Python semantic provider
            |-- native ty server on desktop
            `-- Citry ty_wasm adapter in the browser

Existing Pyodide execution Worker
    `-- publishes a validated catalog snapshot after a successful run
```

The execution Worker remains disposable. Stop and runtime recovery may
terminate it without discarding editor diagnostics or analyzer caches. Visitor
code must not share an interpreter with long-lived analyzer state because it
can mutate imported modules and global state.

The first spike may use a second Pyodide Worker because it proves reuse with
the least new Rust surface. Production keeps that choice only if measured
memory is acceptable. The alternative is a direct wasm-bindgen analysis
module that exposes the parser and OXC records needed by the portable engine.
The existing execution runtime measured about 62 MiB of WebAssembly heap, so
duplicating Pyodide is a decision to measure, not an assumed final design.

`ty_wasm` loads only after the first feature that needs Python semantics. The
official hosted playground's current binary is large enough that it should not
join the initial editor bundle.

## Browser Worker protocol

The browser protocol uses LSP-shaped positions and results without requiring a
pygls server inside the page. It remains private to the docs playground.

Every request contains:

- `schemaVersion`, fixed at `1` while the owning package is pre-1.0;
- a request kind from a closed set;
- a non-negative document version;
- an exact UTF-16 position when the request is position-based; and
- a bounded request ID when a response is expected.

Document updates carry the complete source because the playground edits one
small Python module. Results repeat the document version. The client discards
any answer whose version is not current. Missing, extra, or incorrectly typed
fields reject the complete request or response. No handler consumes a partial
record.

Diagnostics are notifications. Completion, hover, declaration, definition,
references, type definition, and signature help use request IDs. Destroying
the editor terminates its Worker and rejects every pending request. A provider
failure clears its diagnostics and contributes no completion, hover, or
navigation result; Python execution remains available.

The Worker accepts at most the playground's existing 64 KiB source limit.
It bounds pending requests and response bytes. It debounces diagnostics but
lets interactive requests run first. A newer document update cancels or makes
harmless every queued result from an older version.

## Source and catalog confidence

The browser maintains two generations of facts:

1. **Source facts** come from conservative analysis of the current editor
   text. Parser syntax, structural names, direct literal regions, and other
   source-proven facts can appear before Python runs.
2. **Runtime facts** come from the last successful execution of the exact same
   document version. The execution Worker serializes a strictly validated
   catalog snapshot containing only the component contracts and source
   provenance the editor needs.

Editing the document immediately detaches the older runtime snapshot. The
browser may retain it for the rendered preview's events, but it cannot use it
for current editor answers. A failed run publishes no catalog. An invalid,
oversized, or wrong-version snapshot is rejected as a whole.

The browser does not execute visitor code merely to answer completion or lint
requests. The playground's existing auto-run policy independently decides
when to execute it.

## Coordinate mapping

The authored Python document is the only user-visible file in the first
release. Every embedded template, JavaScript, CSS, and shadow Python document
therefore carries an exact map back to it.

Mappings must preserve:

- Python string prefixes, quotes, escapes, and common indentation;
- UTF-8 parser offsets and UTF-16 editor positions;
- CRLF source;
- non-BMP characters;
- nested-template base offsets; and
- multiple template regions in one Python module.

Generated-only ranges return no user-facing result. A mapping that cannot
prove exact authored text returns no result. The browser must never navigate
to a synthetic document.

## Performance and loading budgets

Ordinary docs pages continue to load no playground editor or analysis code.
Opening `/playground/` loads CodeMirror immediately and starts Citry parser
analysis in the background. The editor remains responsive while the analyzer
starts.

The first production decision compares two parser-worker candidates:

- a second Pyodide Worker, which maximizes Python reuse; and
- a direct Citry WebAssembly adapter, which should use less memory.

The measurement records compressed bytes, cold initialization, warm update,
hover and completion latency, peak memory where the browser exposes it, and
termination recovery in Chromium, Firefox, and WebKit. The current execution
Worker remains the baseline. A candidate that materially harms mobile memory
or Firefox startup is not accepted merely because its warm requests are fast.

Warm parser diagnostics should arrive within 100 ms after their debounce.
Warm Citry completion and hover should finish within 100 ms at p95 on the
starter module. Python type analysis and ordinary web services receive their
own budgets after their lazy payloads are measured.

## Delivery phases

### Phase 1: prove the local editor path

The first vertical slice connects the full-page CodeMirror editor to a
dedicated analysis Worker. It provides:

- parser diagnostics from the real pinned `citry_core` WebAssembly wheel;
- completion for parser-owned structural `<c-*>` tags; and
- hover for one complete parser-owned structural tag.

The implemented spike reads definite direct triple-quoted `template` fields
from the CodeMirror Python tree and sends each source-exact body with its
authored range. A normal literal with no escapes and a raw literal are exact.
An escaped non-raw literal, formatted string, or bytes literal keeps syntax
highlighting but receives no Phase 1 IDE result. Phase 2 replaces this narrow
guard with the shared Python asset decoder and its escape-aware source map.
This is deliberately narrower than the portable Python asset discovery used
by the desktop server. It proves the expensive boundaries first: Worker
lifecycle, real WASM parsing, asynchronous CodeMirror results, UTF-16 mapping,
and stale-version refusal. The next slice replaces the narrow extraction with
the shared portable discovery API before adding registry facts.

Inline live-code editors do not start an analyzer during this spike. Enabling
one analyzer per live example before measuring memory could multiply the
Pyodide cost on narrative pages. The full-page playground is the acceptance
surface.

### Phase 2: share all Citry-owned analysis

Move document discovery, parser recovery, linting, completion, hover, and
navigation behind an editor-neutral API. Add versioned catalog snapshots from
successful execution. Enable one lazily created analyzer for the currently
active inline live-code example after memory and disposal tests pass.

Phase 2 is split at the hosted package boundary rather than copying newer
Citry rules into the docs frontend.

#### Phase 2A: portable component facts

Implemented:

- `citry.analysis` owns editor-neutral component-name matching, exact tag
  occurrence discovery, and unknown-component discovery. The same functions
  are used by `citry-lsp` and copied byte-for-byte into the browser analyzer's
  isolated Pyodide filesystem.
- Tag discovery covers start and closing tags, ordinary bodies, and recursively
  parsed nested-template attributes. Parser byte offsets remain the source of
  truth.
- A successful execution publishes a bounded private catalog projection for
  every reachable Citry registry. It contains registered names, aliases,
  descriptions, input fields, and slots, but no runtime Python objects.
- The editor accepts that snapshot only for the exact source version that ran.
  It rejects partial, malformed, oversized, stale, and future-schema records as
  complete units. Editing immediately detaches the snapshot, and a stopped or
  failed run clears it.
- An exact-version catalog enriches registered component hover and enables the
  shared unknown-component rule. The adapter also implements component-name
  completion for a proven catalog, although ordinary incomplete-tag edits
  detach a prior runtime catalog before it can be used. Current-source component
  discovery is therefore part of Phase 2B, not a stale-catalog exception.

The browser catalog is private and versioned independently from Citry's public
component-catalog schema. The execution adapter projects only the fields this
editor generation understands. The analysis Worker validates the projection
again before replacing its previous facts.

#### Phase 2B: released full Citry analysis

The hosted playground currently installs `citry==0.3.1` and
`citry-core==1.4.0`. The portable template-variable, Alpine, JavaScript, CSS,
lint, source-map, and Python component-asset APIs used by the desktop IDE are
part of the unreleased local `citry==0.3.2` and `citry-core==1.6.0` sources.
Phase 2B starts when matching wheels are published and pinned by the playground
runtime. It will then:

- replace the Phase 1 direct-triple-quoted extractor with the shared
  escape-aware Python component-asset discovery and source maps;
- analyze current-source component declarations so component completion never
  relies on a catalog from an older document version;
- add the canonical template-variable, component contract, Alpine, JsData,
  CssData, and lint rules with their configured severities;
- expose the Citry-owned hover, completion, references, declaration,
  definition, type-definition, and signature records supported without ty;
- measure one analyzer for an active inline live-code example before enabling
  that surface.

Until those wheels are available, the browser continues to use the public
`citry-core` parser for immediate structural analysis. It does not maintain a
TypeScript copy of unreleased Python rules and does not silently treat a stale
successful catalog as current source.

### Phase 3: add Python semantics

Build the pinned `ty_wasm` artifact and its Citry adapter. Reuse mapped shadow
documents, response joins, safe-eval filtering, and source maps from the
desktop implementation. Load the provider on first semantic request.

### Phase 4: add ordinary web-language providers

Measure and, if accepted, add browser HTML, CSS, and JavaScript language
services. Citry projections and mapping remain shared; only the provider
adapter differs from VS Code.

## Phase 1 acceptance and error matrix

The spike is successful when all of these hold:

- A parser-invalid structural template shows one mapped CodeMirror diagnostic
  from `citry`. It uses the parser's stable code when the pinned wheel exposes
  structured diagnostics, and `citry.parse` for an older parser error.
- Fixing the source clears the diagnostic for the same editor without
  restarting either Worker.
- Typing `<c-i` in a definite template offers `c-if`; ordinary Python, `js`,
  `css`, comments, text, and attribute values do not.
- Hovering a complete `<c-if>` tag returns Citry help and the exact tag range;
  lookalike text and comments return nothing.
- A response for an older document version has no effect.
- An astral character before the result does not shift its range.
- Worker startup, package download, parser configuration, malformed message,
  oversized source, and termination failures leave Python execution and plain
  CodeMirror editing usable.
- Reset updates the existing analyzer generation and clears stale results.
  Editor destruction terminates the analyzer and rejects pending requests.

The spike does not claim registry components, template variables, Python type
analysis, delegated HTML/CSS/JavaScript help, inline live-code support, or
offline availability. Those belong to the named later phases.

The implementation lives in
`docs_site/_internal/frontend/src/browser_ide.js`,
`docs_site/_internal/frontend/src/analysis_worker.js`, and
`docs_site/static/playground/analysis_adapter.py`. The first browser acceptance
test starts the real pinned Pyodide and Citry Core runtime, reports and clears a
parser error, completes `c-if`, and renders its hover help.

## Alternatives considered

### Run pygls in Pyodide

Pygls and the LSP data classes are mostly Python, but app discovery and native
ty still need replacements. Keeping JSON-RPC machinery inside one page would
not preserve the process model and would add another lifecycle layer. The
browser uses a smaller LSP-shaped Worker protocol while sharing the engine
below pygls.

### Host the existing LSP behind WebSocket

This can deliver native ty sooner, but a public playground would add network
latency, source privacy concerns, multi-tenant quotas, and version skew. Rich
registry analysis would also require either executing untrusted visitor code
on the server or accepting a browser-produced catalog. Browser-native analysis
is the default. A hosted service remains an optional future mode for an
authenticated workspace product.

### Replace CodeMirror with Monaco

Monaco has convenient language-service examples, but the existing editor proof
measured a much larger initial payload. CodeMirror now supports asynchronous
completion, hover, diagnostics, and a custom LSP transport. The editor does
not need to change for this architecture.

## What would falsify this design

Revisit the architecture if one of these occurs:

- the real parser cannot return precise browser coordinates without copying
  substantial LSP-only code;
- a second Pyodide analyzer exceeds accepted memory and a direct WebAssembly
  adapter cannot expose the portable rules economically;
- `ty_wasm` cannot preserve the desktop shadow-document behavior or its pinned
  binary makes the playground unusable on supported browsers;
- CodeMirror cannot apply asynchronous results without stale edits or focus
  regressions; or
- catalog serialization cannot distinguish current source from a stale
  successful run.

Each failure narrows one provider choice. It does not justify copying Citry's
analysis rules into the frontend.
