# AlpineJS ecosystem survey, mid-2026

Research for the citry Events extension: is Alpine (or a fork or alternative)
the right delegated client-side reactivity layer for server-rendered
component state?

All facts below were verified against live sources on **2026-07-05** (GitHub
API, npm registry, jsdelivr CDN, project docs). Bundle sizes were measured by
downloading the published CDN builds and gzipping them locally, not taken
from third-party size sites.

## TL;DR

- The TypeScript fork is **`ekwoka/Alpine-TS`** ("alpinets") by Eric Kwoka.
  It is **not viable as a dependency**: no license file, never published to
  npm, last commit August 2024, 9 stars, tracks upstream Alpine 3.14.1
  (mid-2024). Kwoka's real performance work went into upstream Alpine
  instead, and he has since moved on to other projects.
- **Upstream Alpine 3 is healthy**: v3.15.12 (April 30, 2026), roughly
  monthly patch releases, Caleb Porzio still merging (June 2026), Josh
  Hanley (Livewire team) doing much of the day-to-day. MIT. Core is 16.7 KB
  gzipped. The long-requested x-for performance work landed in v3.15.9
  (March 2026). Deferred / non-blocking initialization never landed;
  `Alpine.start()` is still one synchronous DOM walk.
- **No Alpine 4 roadmap exists publicly** as of July 2026. Signals were
  explored in a 2023 branch and a 2024 discussion and went nowhere visible;
  Caleb's energy has gone into Livewire 4 (August 2025), the Blaze compiler,
  islands, and Flux UI.
- Alternatives do not displace Alpine for "attach reactive scopes to
  server-rendered DOM": petite-vue is dead (last release January 2022),
  `@vue/reactivity` and preact signals are reactivity cores without a DOM
  binding layer (you would rebuild Alpine's directive half yourself), and
  datastar is a whole competing framework loop, not an embeddable substrate.
- The proven embedding playbook is Livewire's: compile a pinned Alpine into
  your own bundle, claim `window.Alpine`, warn on a second instance, fire
  your own init event for plugin registration, then call `Alpine.start()`
  yourself on `DOMContentLoaded`, with a documented manual-bundle escape
  hatch.

---

## 1. The TypeScript fork: ekwoka/Alpine-TS

### Identification

- Repo: <https://github.com/ekwoka/Alpine-TS>, package name in the monorepo:
  `alpinets` / `@alpinets/alpinets`. Description: "Alpine JS, but TS."
  Created 2022-10-08.
- Author: Eric Kwoka (github `ekwoka`, npm `ekwoka`). The identification as
  "active community maintainer" checks out: he has filed **46 PRs against
  `alpinejs/alpine`**, at least 35 merged, spanning 2023-2024 (bug fixes in
  the reactivity proxies, mutation handling, x-model, morph, teleport, plus
  the x-for performance rewrite, PR
  [#4361](https://github.com/alpinejs/alpine/pull/4361)). He also maintains
  the `@types/alpinejs` DefinitelyTyped packages (latest 3.13.11,
  November 2024).
- Stated goal (the README is two sentences): "This Project will attempt to
  rewrite all of AlpineJS in TypeScript, with an improved DX system and
  hopefully other optimizations and improvements."

### Status as of 2026-07-05 (GitHub API)

| Fact | Value |
|---|---|
| Last commit to main | **2024-08-25** ("Adds Sort Plugin"), ~22 months stale |
| Stars / forks | 9 / 1 |
| Open issues | 10 |
| Releases / tags | **none** |
| npm | **never published** (`@alpinets/alpinets` returns "Not found" on the registry; the name exists only as a pnpm `workspace:*` reference) |
| License | **none** (GitHub API reports `license: null`; no LICENSE file). Legally all-rights-reserved |
| Upstream parity | root `package.json` says `"name": "alpinejs", "version": "3.14.1"`, i.e. it tracks upstream as of mid-2024 and has missed the entire 3.15.x line |

### What it actually contains

The monorepo mirrors Alpine's package layout: `alpinets` (core) plus
`anchor`, `collapse`, `focus`, `intersect`, `mask`, `morph`, `persist`,
`sort`. The merged-PR history is mostly TypeScript conversion, typing of the
plugins, a vitest-based test suite replacing Alpine's Cypress tests, and
periodic "fast-forward upstream" merges, plus a few genuine fixes (magics
injection memory leak, template-directive memory cleanup, nested setter
regression). It is a faithful TS port with tests, not a re-architecture.

The interesting performance work happened *outside* the fork:

- His x-for rewrite was submitted upstream (September 2024) and merged into
  **upstream v3.15.9 in March 2026**, so the fork no longer has a perf story
  upstream lacks; if anything the reverse is now true.
- He built a signals-based drop-in reactivity engine,
  `@timberts/reactivity`, claiming "about 30% faster than vue reactivity,
  and about 70% smaller", pluggable through Alpine's public
  `Alpine.setReactivityEngine` API (see the TC39 signals discussion,
  [alpine#4179](https://github.com/alpinejs/alpine/discussions/4179)). It
  was published once, **v0.0.1 in September 2023**, and never updated.

### Author activity

Kwoka's public GitHub activity in July 2026 is Rust work on
`bevyengine/bevy` and personal repos. His last upstream Alpine PR was
November 2024. He has, by every observable signal, moved on from the Alpine
ecosystem.

### Verdict

**Do not adopt Alpine-TS as a dependency.** Concretely:

1. **No license.** Using or vendoring it is legally unsafe until a license
   file appears.
2. **No artifact.** Nothing on npm, no releases, no published bundle to pin
   or measure. You would be building from a stale source tree.
3. **Dormant and behind.** Two years without a commit, frozen at upstream
   3.14.1, so it lacks the 2025-2026 fixes (including the CSP evaluator
   work, morph fixes, and, ironically, its own author's x-for optimization,
   which only shipped in upstream 3.15.9).
4. **Zero adoption.** 9 stars, no downstream users to share maintenance
   risk with.

The one durable thing the fork proves is that Alpine's internals *can* be
typed and ported cleanly, and that Alpine's `setReactivityEngine` hook is
real. If citry ever needs a custom engine, that public hook on upstream
Alpine is the place to plug in, not the fork.

## 2. Upstream Alpine status, mid-2026

### Version and cadence

- Latest release: **v3.15.12, 2026-04-30**
  (<https://github.com/alpinejs/alpine/releases>).
- Cadence: v3.15.0 shipped 2025-09-03, then twelve patch releases through
  April 2026 (roughly monthly). Commits on `main` continue through
  **2026-07-01** (verified via the GitHub commits API), so the gap since
  April is unreleased work, not abandonment.
- License: **MIT** (GitHub API). ~31.7k stars. Open issue count is in the
  single digits; the project triages aggressively and routes questions to
  discussions.

### Who maintains it

Caleb Porzio still merges PRs personally (merge commits dated June 27,
2026). The bulk of day-to-day fixing in 2025-2026 is by **Josh Hanley**
(`joshhanley`, Livewire core team), with a ring of recurring community
contributors (SimoTod, willrowe, ganyicz, nicolagianelli). Practical
reading: Alpine is maintained as critical infrastructure for Livewire, which
is also its funding story. It is not a one-person bus-factor project, but it
is a two-organization one (Caleb + the Livewire/Laravel orbit).

### Did the long-standing performance work land?

- **x-for optimization: yes.** ekwoka's PR
  [#4361](https://github.com/alpinejs/alpine/pull/4361) merged in
  **v3.15.9 (2026-03-27)**, about 18 months after submission.
- **Scheduler/reactivity: partially.** "Add reactive effect transactions"
  ([#4731](https://github.com/alpinejs/alpine/pull/4731), v3.15.6,
  January 2026) batches effect runs; "Improve evaluator"
  ([#4711](https://github.com/alpinejs/alpine/pull/4711), v3.15.3) cleaned
  up expression evaluation. v3.15.12 added minified ESM builds per package
  ([#4820](https://github.com/alpinejs/alpine/pull/4820)).
- **Non-blocking / deferrable initialization: no.** `Alpine.start()` today
  (source:
  <https://github.com/alpinejs/alpine/blob/main/packages/alpinejs/src/lifecycle.js>)
  synchronously dispatches `alpine:init`, starts the MutationObserver, then
  querySelectors all roots and walks each tree, all on the main thread. No
  requestIdleCallback, no chunking. The 2023 experiments
  (`improve-performance` and `explore-signals` branches, last commits
  December 2023) were never merged. The community fills the gap with
  third-party lazy loading:
  [Async Alpine](https://github.com/Accudio/async-alpine) (225 stars, active
  as of June 2026).

### Official plugin set and measured sizes

Sizes are the published `dist/cdn.min.js` of each package at the `@3` tag
(resolves to 3.15.12), downloaded from jsdelivr and gzipped locally on
2026-07-05:

| Package | min | gzip | Note |
|---|---|---|---|
| `alpinejs` (core) | 46.3 KB | **16.7 KB** | includes `@vue/reactivity` |
| `@alpinejs/morph` | 5.4 KB | 2.1 KB | |
| `@alpinejs/persist` | 0.8 KB | 0.5 KB | |
| `@alpinejs/focus` | 26.1 KB | 9.0 KB | bundles focus-trap + tabbable |
| `@alpinejs/csp` (alt core build) | 61.5 KB | 20.3 KB | ships its own CSP-safe expression evaluator, hence larger than core |
| `@alpinejs/collapse` | 1.4 KB | 0.7 KB | |
| `@alpinejs/intersect` | 0.9 KB | 0.6 KB | |
| `@alpinejs/mask` | 2.0 KB | 1.1 KB | |
| `@alpinejs/anchor` | 15.7 KB | 6.3 KB | bundles floating-ui |
| `@alpinejs/sort` | 38.9 KB | 13.6 KB | bundles SortableJS |
| `@alpinejs/resize` | 0.7 KB | 0.5 KB | |

A realistic citry payload (core + morph + persist) is about **19.3 KB
gzipped**. Adoption context: `alpinejs` gets ~2.38M npm downloads/month
(api.npmjs.org, last month as of 2026-07-05), which understates real usage
since Alpine is predominantly consumed via CDN script tags and bundled
inside Livewire.

### Morph maturity specifically

`@alpinejs/morph` has shipped since 2022 and is the DOM-diffing backbone of
Livewire 3/4, so it is exercised at scale in production. It is still
receiving correctness fixes in 2026, which cuts both ways: v3.15.0 added
`Alpine.morphBetween()`
([#4629](https://github.com/alpinejs/alpine/pull/4629)); v3.15.9 fixed
dialog handling during morph; v3.15.11 fixed a v3.15.9 regression where
`$refs` was unavailable during morph
([#4793](https://github.com/alpinejs/alpine/pull/4793)); a May 2026 commit
fixed x-if/x-for content duplicating during morph
([#4785](https://github.com/alpinejs/alpine/pull/4785)). Read: mature and
actively hardened, but treat plugin upgrades as something to test, not
rubber-stamp. If citry re-renders server HTML into live components, morph is
the piece you want, and also the piece to pin tightly.

### Alpine 4

No public roadmap, milestone, branch, or announcement as of 2026-07-05.
Searches of the repo (branches, releases), discussions, and the web turn up
only: the archived `alpinejs/alpine-next` repo (that was the v3 rewrite,
archived 2021), the `explore-signals` branch (December 2023), and the TC39
signals discussion
([#4179](https://github.com/alpinejs/alpine/discussions/4179), April 2024)
which no maintainer answered. Caleb's 2025-2026 output went to **Livewire
4** (released at Laracon US, August 2025, with the Blaze compile-time
optimizer and islands rendering,
<https://laravel.com/blog/livewire-4-is-here-the-artisan-of-the-day-is-caleb-porzio>)
and Flux UI. Planning assumption for citry: **Alpine 3.15.x semantics are
what you get for the foreseeable future**, which is actually good for a
framework embedding it (stable contract, no breaking major on the horizon).

## 3. Alternatives in the same weight class

**petite-vue: abandoned, not an option.** 6 KB Vue subset by Evan You aimed
at exactly citry's use case (progressive enhancement of server HTML). Last
npm release 0.4.1 (January 2022, npm registry timestamps); last substantive
commit January 2022; 20 open issues; still labeled a Vue org side project.
Downloads ~12k/month. Four and a half years without a release means you
would be adopting an unmaintained codebase, full stop.
(<https://github.com/vuejs/petite-vue>)

**@vue/reactivity standalone: excellent core, no DOM half.** 7.2 KB gzipped
(measured, `reactivity.esm-browser.prod.js` @3.5), 51M downloads/month,
actively developed (3.5.39 June 2026; a 3.6 line with the alien-signals
based reactivity rewrite is at beta.17 on npm, which will eventually make
this core faster still). It gives you `reactive()`/`effect()` and nothing
else: no directive scanning, no scope inheritance, no x-model/x-on, no
lifecycle, no morph. Worth noting: **Alpine's engine is literally
`@vue/reactivity`** (imported in
`packages/alpinejs/src/index.js`), so embedding Alpine is embedding this
library plus the DOM binding layer citry would otherwise have to write and
maintain itself. Only choose bare `@vue/reactivity` if citry wants to own
its own directive/binding DSL long-term.

**preact signals (`@preact/signals-core`): tiny, different shape.** 2.0 KB
gzipped (measured), 22M downloads/month, active (1.14.3, June 2026).
Fine-grained signal objects rather than proxied plain objects, which means
component state does not stay "a plain dict that happens to be reactive";
mirroring a server-side State dict would need a translation layer, and there
is still no DOM binding layer. Great engine if citry compiles bindings
itself; not a drop-in "reactive scopes on server HTML" tool.

**datastar: a competitor, not a substrate.** v1.0.0 April 2026, v1.0.2 June
2026, MIT, ~4.6k stars, active (<https://github.com/starfederation/datastar>).
~12.2 KB gzipped bundle (measured from its published bundle). It does
signals-in-attributes plus server-driven patches over SSE as one opinionated
loop: the server owns state transitions and streams DOM/signal patches.
Embedding it would mean adopting its transport and update model, which
overlaps with (and would fight) citry's own Events design. Right way to use
it: study it as design input for the events/transport layer, not as a
dependency.

**Bottom line for Q3:** in 2026 Alpine is still the only maintained,
widely-deployed library whose whole job is "attach reactive scopes and
declarative bindings to HTML you already rendered on the server". The
alternatives are either dead (petite-vue), engines without the DOM half
(@vue/reactivity, preact signals), or whole frameworks (datastar). Alpine
remains the right default, with bare `@vue/reactivity` as the fallback if
citry decides to own the binding layer.

## 4. Risks of embedding Alpine in a framework, and the Livewire playbook

### One global, no multi-instance story

Alpine assumes it is the only Alpine on the page. The CDN build does
`window.Alpine = Alpine` unconditionally; `Alpine.start()` keeps a
module-local `started` flag and only warns ("Alpine has already been
initialized on this page") on a double start of the *same* copy
(`src/lifecycle.js`). Two different copies (citry's bundled one plus a
user's own CDN tag, or citry inside a Livewire app) will both walk the DOM
and double-initialize every `x-data` island; nothing prevents it. Livewire's
defense is detection plus convention: at bundle-eval time it warns
`"Detected multiple instances of Alpine running"` if `window.Alpine`
already exists, tags its own copy with `window.Alpine.__fromLivewire =
true`, and re-checks the tag on DOMContentLoaded to catch a later foreign
bundle clobbering the global
(<https://github.com/livewire/livewire/blob/main/js/index.js>). citry should
copy this exactly, including documenting "do not add your own Alpine script
tag; import ours".

### Init order and timing control

- The npm/ESM build does nothing until you call `Alpine.start()`
  (`builds/module.js`), which is the right build for a framework: you fully
  own boot timing.
- The CDN build auto-starts in a `queueMicrotask` after script evaluation
  (`builds/cdn.js`), i.e. right after DOM parse when loaded with `defer`.
- `window.deferLoadingAlpine` is an **Alpine v2 API that no longer exists in
  v3**; the v3 upgrade guide replaces it with lifecycle events
  (<https://alpinejs.dev/upgrade-guide>). Anything (or any LLM) suggesting it
  for v3 is stale.
- All registration (plugins, `Alpine.data()`, custom directives, magics)
  must happen before `start()`, either literally before the call or inside
  an `alpine:init` listener. A framework that owns `start()` should also
  expose its own pre-start event, as Livewire does with `livewire:init`.

### Blocking initialization on large pages

This is the real, documented weakness. `start()` synchronously initializes
every root tree; cost scales with DOM size and directive count, on the main
thread, before the page is interactive. Evidence trail:

- [alpine#566](https://github.com/alpinejs/alpine/issues/566) (v2 era):
  measurable slowdown just from Alpine being present on element-heavy pages.
- [Discussion #2837](https://github.com/alpinejs/alpine/discussions/2837):
  ~200 ms reported to initialize a large x-for list; advice given is to
  server-render the items instead.
- Ryan Carniato's js-framework-benchmark commentary
  (<https://dev.to/ryansolid/comment/1712l>): Alpine is among the slowest
  libraries for keyed list updates; fine at "sprinkle" scale, visible when
  scaled up.
- The existence of [Async Alpine](https://async-alpine.dev/docs/strategies/)
  (load/init components on visible/idle/media triggers) is itself evidence
  that stock Alpine has no built-in answer.
- After boot, a global MutationObserver walks every added subtree looking
  for directives, so large DOM swaps (exactly what a server-driven framework
  does) pay a per-node scan. Livewire's own source comments on this: its
  `interceptInit` callback early-returns on elements without `wire:`
  attributes "to prevent Livewire from causing general slowness for other
  Alpine elements on the page"
  (<https://github.com/livewire/livewire/blob/main/js/lifecycle.js>).

Implications for citry: keep Alpine scopes shallow (one `x-data` per
interactive component root, not per-element sprinkles), render content
server-side rather than via large client x-for loops, and consider
lazy-initializing below-the-fold components (Async Alpine's strategies, or
citry-controlled `initTree()` calls) if profiling shows boot cost on big
pages. Budget expectation from community numbers: hundreds of components is
fine on desktop, low hundreds of milliseconds territory on mid-range mobile;
thousands of directive-bearing elements is where it visibly hurts.

### How Livewire version-locks and boots Alpine (the pattern to copy)

Verified from `livewire/livewire@main` on 2026-07-05:

1. **Version lock by compilation.** `package.json` pins `alpinejs:
   ^3.15.12` and every official plugin at `^3.15.12`; esbuild compiles all
   of it into Livewire's own shipped bundle. Users never install Alpine; the
   Alpine version is a build-time fact of the Livewire release, updated by
   the Livewire team in lockstep (Josh Hanley maintains both sides).
2. **Auto-inject, auto-boot.** The PHP side injects the bundle; on
   `DOMContentLoaded` it runs `Livewire.start()`, which fires
   `livewire:init` (user extension point), registers all Alpine plugins,
   adds a root selector for its own components
   (`Alpine.addRootSelector('[wire\\:id]')`), installs `interceptInit`
   hooks, and only then calls `Alpine.start()`.
3. **Escape hatch.** Setting `window.livewireScriptConfig` (via the
   `@livewireScriptConfig` Blade directive) suppresses auto-boot so apps
   that bundle their own JS can `import { Livewire, Alpine } from
   '.../livewire.esm'`, register plugins, and call `Livewire.start()`
   themselves (<https://livewire.laravel.com/docs/alpine>).
4. **Re-export Alpine.** The ESM bundle exports its Alpine so userland
   plugins attach to the *bundled* copy instead of a second install.

This maps one-to-one onto citry: ship `citry.js` with Alpine compiled in and
pinned, expose `window.Alpine` and an ESM export, fire `citry:init` before
starting, use `Alpine.addRootSelector()` (a public API) to make citry
component roots first-class Alpine roots, and document the "bring your own
bundle" path.

### Residual risks worth naming

- **Coexistence with Livewire/other Alpine hosts is unsolved upstream.** If
  a user embeds a citry page in an app that already ships Alpine (Livewire,
  Statamic, Filament...), one copy must win. Detection and a clear error is
  the state of the art.
- **Expression evaluation uses `new Function`**, which violates strict CSP.
  The `@alpinejs/csp` build fixes that but costs 20.3 KB gzipped and
  restricts expressions; it received active fixes through 3.15.12, so it is
  a real option, but decide early which build citry standardizes on.
- **Single-ecosystem gravity.** Alpine's health is entangled with
  Livewire/Laravel funding and attention. That has been a stabilizing force
  for five years, and there is no current signal of trouble, but it is the
  honest dependency-risk shape: you are betting on Caleb's companies, not on
  a foundation.

## Sources

Accessed 2026-07-05:

- Alpine-TS repo and README: <https://github.com/ekwoka/Alpine-TS>; GitHub API repo object (license null, pushed_at 2024-08-25); root `package.json` (name `alpinejs`, version 3.14.1); npm registry 404 for `@alpinets/alpinets`
- ekwoka upstream PRs: GitHub search API `repo:alpinejs/alpine author:ekwoka type:pr` (46 results); x-for perf PR <https://github.com/alpinejs/alpine/pull/4361>
- ekwoka signals engine: <https://github.com/alpinejs/alpine/discussions/4179>; npm `@timberts/reactivity` (0.0.1, 2023-09-09)
- Alpine releases and bodies: <https://github.com/alpinejs/alpine/releases> via GitHub API (v3.15.0 2025-09-03 through v3.15.12 2026-04-30)
- Alpine commits/maintainers: GitHub commits API for `alpinejs/alpine` (through 2026-07-01)
- Alpine source: `packages/alpinejs/src/lifecycle.js`, `src/index.js`, `builds/cdn.js`, `builds/module.js` on `main`; upgrade guide `packages/docs/src/en/upgrade-guide.md` (deferLoadingAlpine removal)
- Bundle sizes: downloaded from `https://cdn.jsdelivr.net/npm/<pkg>@3/dist/cdn.min.js`, gzipped locally; jsdelivr resolved `alpinejs@3` to 3.15.12
- npm downloads: api.npmjs.org last-month points for alpinejs, petite-vue, @vue/reactivity, @preact/signals-core, @alpinejs/morph
- Livewire: <https://livewire.laravel.com/docs/alpine>; `js/index.js`, `js/lifecycle.js`, `package.json` on `livewire/livewire@main`; Livewire 4 announcement <https://laravel.com/blog/livewire-4-is-here-the-artisan-of-the-day-is-caleb-porzio>
- petite-vue: GitHub API for `vuejs/petite-vue`; npm registry (0.4.1, 2022)
- Vue/preact/datastar: npm registry dist-tags (vue 3.5.39 latest, 3.6.0-beta.17; @preact/signals-core 1.14.3); GitHub API for `starfederation/datastar` (v1.0.0 2026-04-16, v1.0.2 2026-06-02)
- Init cost evidence: <https://github.com/alpinejs/alpine/issues/566>; <https://github.com/alpinejs/alpine/discussions/2837>; <https://dev.to/ryansolid/comment/1712l>; <https://async-alpine.dev/docs/strategies/>; <https://github.com/Accudio/async-alpine>
