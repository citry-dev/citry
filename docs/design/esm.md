# Exploration brief: ESM and `Component.js`

**Status (2026-07-18): parked research brief, not a proposal.** No ESM
behavior, source-language contract, work package, or implementation is
approved by this document. The current classic-script implementation in
[`dependencies.md`](dependencies.md) and the IIFE output proposed in
[`asset_compiler.md`](asset_compiler.md) remain the baseline until a later
research and ratification round explicitly changes them.

This brief records the questions that round must answer. Its immediate trigger
was the `$component` registration discussion: injecting a class-bound
`$component` by enclosing all of `Component.js` in a function would avoid a
global-name collision, but it could also make otherwise-valid module syntax
invalid and constrain future source-language compilers. Citry should not adopt
that wrapper without first deciding what `Component.js` is allowed to compile
to and how that output is executed.

Related docs: the current asset-compiler proposal
([`asset_compiler.md`](asset_compiler.md)), its implementation plan
([`asset_compiler_plan.md`](asset_compiler_plan.md)), source-language
declarations ([`source_languages.md`](source_languages.md)), dependency
emission and fragment loading ([`dependencies.md`](dependencies.md)), asset
loading ([`asset_loading.md`](asset_loading.md)), hot reload
([`hot_reload.md`](hot_reload.md)), and the client/runtime constraints in
[`events.md`](events.md). For operating rules see
[`/CLAUDE.md`](../../CLAUDE.md).

---

## 1. Scope and boundary

The future exploration must determine whether Citry should support ECMAScript
modules (ESM) for `Component.js`, directly or as compiler output, and what
that would require across loading, compilation, caching, emission, and client
registration.

It must keep these cases separate:

- Plain JavaScript authored as a classic script.
- Plain JavaScript authored as an ESM module (`.mjs`, `js_lang`, or another
  declaration that the exploration may propose).
- TypeScript, TSX, JSX, or a user-defined source language compiled to a
  classic script.
- The same compiled to ESM.
- Inline component source versus a source file with a real resolve directory.
- Initial document emission versus scripts fetched for an inserted fragment.

This brief does **not** choose ESM, change the current esbuild IIFE output,
change `$component`, or approve a function wrapper around component source.
It also does not reopen cross-component bundling or code splitting unless the
research proves that ESM cannot be evaluated coherently without doing so.

### 1.1 Syntax question to settle precisely

"At the top" has two distinct meanings that the research must not conflate:

1. A static `import` declaration must be at a module's top level, rather than
   nested inside a function or block.
2. Whether imports must physically precede every other top-level statement can
   be a language-tool or style constraint rather than the ECMAScript grammar
   rule.

The ECMAScript module grammar admits imports, exports, and statements as
module items; TypeScript recognizes standard ECMAScript module syntax and
adds compiler-mode and module-resolution choices. Starting references are the
[ECMAScript module grammar](https://tc39.es/ecma262/multipage/ecmascript-language-scripts-and-modules.html#sec-modules)
and the
[TypeScript module reference](https://www.typescriptlang.org/docs/handbook/modules/reference).
The later exploration must verify the exact rules against the versions Citry
would support and against every built-in compiler configuration.

One consequence is already clear enough to preserve as a constraint: enclosing
the untouched source in `(function ($component) { ... })` moves any static
imports out of module scope. Such a wrapper cannot be assumed compatible with
future module-capable `Component.js` input or output.

---

## 2. Current constraints to map

The exploration starts by producing an observed execution-order and ownership
map, not by selecting an API. At minimum it must cover:

### 2.1 Dependency emission and browser execution

- How `Script`, its `attrs`, and its current IIFE `wrap` flag distinguish
  classic scripts, modules, and inert data blocks.
- The exact document order of the Citry runtime, extension bootstrap scripts,
  component dependencies, class-level `Component.js`, generated `js_data()`
  scripts, and the page manifest.
- The `document`, `simple`, `fragment`, and `ignore` strategies, including
  inline versus URL-served component scripts.
- How dynamically appended `<script type="module">` elements execute and when
  their `load` promise resolves relative to manifest calls, Alpine startup,
  DOM mutation, and component registration.
- Whether repeated fragment insertion should evaluate a module again. Compare
  native module-map deduplication with Citry's loaded-URL set and current
  per-class registration rule.
- Error propagation, cleanup, pending-call behavior, and observable ordering
  when a module or one of its imports fails.
- CSP, nonces, integrity, cross-origin fetching, MIME types, Blob/data URLs,
  and source-map behavior. Runtime string evaluation must not become an
  accidental requirement.

### 2.2 Component and registration semantics

- Which current top-level side effects in `Component.js` are supported and
  whether module scope, strict mode, deferred execution, and top-level `this`
  would change them.
- How a class-bound registration function receives the class ID without
  rewriting user tokens, relying on a page-global name, or hiding imports
  inside a function.
- Whether `$component(...)` remains the authoring API, becomes an imported
  binding, becomes a compiler-provided binding, or is replaced by a default
  export or explicit namespaced call.
- How one-registration-per-class, `{init, props}`, callback cleanup, `js_data()`
  delivery, context decorators, and fragment re-entry behave in every format.
- Whether registration must be synchronous during module evaluation or may
  happen after an asynchronous boundary.
- How classic and module components coexist on one page and how a useful error
  identifies a format or ordering mismatch.

### 2.3 Compiler and source-language contract

- The asset-compiler proposal's choice to bundle once per component with
  `--format=iife`, including why it was chosen and which assumptions an ESM
  output would invalidate.
- Whether a compiler result needs structured metadata such as
  `format="classic" | "module"`, source map, imports, emitted companion files,
  or execution requirements instead of returning JavaScript text alone.
- How `js_lang`, file-suffix inference, `.js` versus `.mjs`, and explicit user
  overrides select a source grammar and an output format without conflating
  them.
- TypeScript module modes, module resolution, type-only import elision,
  JSX/TSX transforms, compiler-injected helpers, top-level `await`, and
  preservation versus bundling of imports.
- Relative-import resolution for inline source, file source, cached output,
  and component scripts served from Citry's cache route.
- Whether custom compilers may emit ESM, and how Citry validates and safely
  transports their declared output format.
- Cache keys, invalidation dependencies, content-addressed URLs, hot reload,
  and source-map URLs when one source produces multiple output files.
- The boundary between per-component compilation and a module graph. The
  exploration must state what is possible without silently introducing a
  second whole-project build system.

---

## 3. Prior art and evidence to inspect

This is the required research inventory, not a claim that the survey has
already been performed.

### 3.1 Citry

- Runtime code: `citry/ext/dependencies/scripts.py`, `types.py`,
  `emission.py`, `routes.py`, and `client/citry.js`.
- Loading/compiler code that exists when the exploration begins, plus the
  corresponding tests for document order, fragment loading, variables,
  registration, and generated URLs.
- The related design docs linked at the top of this brief, especially the
  asset compiler's prior-art section and its reasons for choosing IIFE output.
- Existing ESM observations in `docs/design/alpinejs/` and
  `docs/design/events_research/`, including the Alpine/morph execution-order
  spike and the old-django-components recon.
- Git history for earlier component-JS, compiler, module, and dependency
  loading experiments.

### 3.2 django-components and preserved projects

- Current django-components source, documentation, changelog, tests, and its
  dependency manager.
- Relevant django-components GitHub issues, pull requests, and discussions,
  including rejected or reverted approaches, not only merged code.
- `old-djc.zip`: the compiler prototype, esbuild metafile, module experiments,
  Vue extension, Blob-module loader, and surrounding TODO/design notes.
- `old-chk.zip`: real application component scripts, Alpine Composition
  registration/load-order defenses, imports, compiled languages, and build
  configuration.
- `old-vuetify.zip`: a large TypeScript/ESM library's source organization,
  package/build formats, import graph, and development/production tooling.
- Existing recon reports may guide the search but do not replace checking the
  preserved source itself.

### 3.3 Standards and toolchains

- The current ECMAScript and HTML module-script specifications and browser
  behavior, including dynamic insertion and the module map.
- TypeScript's supported module and module-resolution modes.
- esbuild's IIFE, ESM, bundling, banner/footer, source-map, and splitting
  behavior; then any other compiler Citry proposes to ship.
- Comparable framework/compiler pipelines where component-local source can
  contain imports: at least Vue, Svelte, Vite/Rollup-based systems, and a
  server-rendered framework that loads fragments dynamically.
- CSP and deployment implications from authoritative browser and standards
  sources.

Every load-bearing conclusion should distinguish specification guarantees,
observed browser behavior, compiler behavior, and Citry policy.

---

## 4. Candidate families to compare

The exploration must compare at least these families without presuming that
one of them wins:

1. **Classic-script lexical wrapper.** A class-bound `$component` is passed
   into a function containing the source. Simple for classic scripts, but the
   module and compiled-language constraints above are its falsifiers.
2. **Module-scope injected binding.** Citry or the compiler emits a top-level
   import/declaration that binds registration to the class while preserving
   the user's own module items. This requires a safe injection point and a
   compiler/output-format contract.
3. **Default-export component definition.** `Component.js` exports one
   callback or `{init, props}` object and the loader registers that value for
   the class. This structurally matches one definition per class but changes
   the authoring and classic-script contracts.
4. **Explicit namespaced registration.** User code calls a stable Citry API
   instead of relying on a magic identifier. This avoids global ambiguity but
   must still associate the call with a class without generated source hacks.
5. **Compiler-owned lowering.** Each source-language compiler receives the
   class context and emits a declared classic/module artifact with the
   registration mechanism already bound. This may be powerful, but risks
   making compilers depend on private runtime details.

Temporary page globals, `document.currentScript` inference, regex replacement,
Blob-module execution, and `eval`/`Function` construction should be assessed as
explicit alternatives with their ordering, CSP, debugging, and collision
costs. They are not acceptable merely because they make a spike short.

---

## 5. Evaluation criteria

An acceptable design must be judged on:

- Correctness across classic JavaScript, ESM JavaScript, TypeScript/TSX/JSX,
  and third-party compiler output.
- Deterministic execution and registration order for documents and fragments.
- No accidental rewriting or capture of identifiers in user source.
- Compatibility with static imports, exports, top-level `await`, relative
  imports, and source maps where the selected format supports them.
- One-registration-per-class enforcement and the full existing component
  lifecycle.
- CSP posture without requiring `unsafe-eval`; a clear policy for inline
  scripts, nonces, Blob/data URLs, and cross-origin modules.
- Cache, deduplication, invalidation, and hot-reload behavior.
- Useful compile-time and runtime errors with paths and source locations.
- Development and deployment complexity, payload/network cost, browser
  compatibility, and the amount of public API Citry must commit to.
- A migration story that does not silently reinterpret existing
  `Component.js` files.

---

## 6. Required outputs before a decision

A future ESM round is not ready for ratification until it produces:

1. A current-state execution-order diagram and a test-backed matrix covering
   source language, classic/module output, inline/URL delivery, and
   document/fragment insertion.
2. A prior-art report covering the repository, django-components and its
   public discussion history, the three preserved archives, and relevant
   standards/toolchains.
3. Two or three concrete Citry designs, each with generated-output examples,
   compiler/runtime changes, compatibility costs, and falsifiers.
4. A browser spike for the leading designs. It must include static imports,
   compiled TypeScript, source-map/error behavior, initial load, repeated
   fragments, registration/data ordering, and failure paths.
5. An adversarial review that specifically looks for execution-order races,
   cache/module-map mismatches, CSP regressions, and source-language lock-in.
6. An explicit maintainer decision followed by a separate implementation
   plan. Research or a spike alone does not authorize changing the current
   script contract.

Until then, ESM support and a universal `$component` injection mechanism are
both open questions.
