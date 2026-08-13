# Résumé observations - django-components / Citry (2024–2026)

Working notes mined from: GitHub (django-components/django-components +
JuroOravec repos), the local upstream clone (`~/repos/django-components`,
incl. CHANGELOG), the Citry repo (design docs and cited source files), and
642 archived Cursor chats. Every number below has a cited source.

---

## 1. Headline scale & impact (verifiable metrics)

- **Core maintainer of django-components** - Vue/React-style component
  framework for Django/Python. **1,515 GitHub stars, 101 forks** (as of
  2026-06).
- **459 commits, 397 merged PRs** (of 403 opened), **141 issues authored**
  on the main repo (GitHub API, JuroOravec). Sustained ~18 months of
  near-daily activity (Cursor chat archive spans Jan 2025 → Jun 2026).
- **~70 releases shipped** in the window (v0.117 → v0.151), including two
  flagged major releases (v0.136, v0.140 "biggest step toward v1").
- **PyPI adoption** (pypistats, 2026-06): django-components **~109,000
  downloads/month** (~22,700/week, ~4,800/day). Companion packages:
  `pygments-djc` ~3,640/mo, `djc-ext-pydantic` ~1,490/mo. (Rust parser and
  `citry-core` not retrieved, rate-limited; the parser ships as a
  django-components dependency so its volume tracks the core package.)
- **Authored & maintains an ecosystem of companion packages**, not just the
  core: `djc-core-html-parser` (Rust), `djc-ext-pydantic`, `djc-storybook`,
  `djc-heroicons`, `pygments-djc`, plus `citry_core` on PyPI.

## 2. The Rust migration (the "4x / critical parts to Rust" story)

- **Designed and built a Rust core** exposed to Python via **PyO3 / maturin**,
  replacing hot-path Python. Two concrete, changelog-cited wins:
  - **Component input validation made 6–7x faster** on both CPython and PyPI
    (PyPy) - this had been **10–30% of total render time** (v0.128, PR #945).
  - **Whole-render ~20% faster** by moving **template-tag parsing into Rust**
    (v0.145).
- **`djc-core-html-parser`** - standalone Rust HTML parser (own repo, Rust),
  the reusable primitive extracted from this work. Origin chats:
  "Refactoring HTML Parser for Performance" (325 msgs), "Optimizing HTML
  Transformation with Rust" (94 msgs), "Optimizing Vue Component Parser with
  Rust" (670 msgs).
- **Fixed memory leaks** in component caching and request context-processor
  data reuse (changelog, multiple releases).
- Note on the screenshot's "4x" / "Version 2": the *documented* upstream
  numbers are 6–7x (validation) and ~20% (end-to-end); the 3–4x figures are
  cleanest for **Citry** (next section). Worth aligning the CV wording to
  whichever number we can cite - see §6.

## 3. Citry - the ground-up Rust rewrite (architecture leadership)

- **Conceived and is building Citry**: a **universal, cross-language HTML
  templating engine** (one Rust core → Python, JS, PHP, Go, Rust bindings).
  Forked from django-components' core Dec 2025; "Rust as single source of
  truth, thin language bindings."
- **Full compiler pipeline in Rust**: Pest grammar (389 lines) → AST
  (843) → parser (2,560) → code-generating compiler (1,651), plus a
  multi-language codegen trait (`LangImpl`, 5 language impls). ~226 Rust
  unit tests + 310 Python tests.
- **Sandboxed Python expression evaluator** (`python_safe_eval`) built on
  **ruff's** Python parser - AST-rewrites user template expressions into a
  safe call form. Security-conscious design.
- **Performance engineering as a first-class concern**:
  - **Const-folding optimization** ("pre-render the constant parts") - design
    in `docs/design/component_constness.md`.
  - **Deferred rendering**, **infinite-depth rendering**, **HTML
    serialization fast path** (`mark_html()`).
  - **Built a benchmarking harness** (asv-style) comparing Citry vs
    django-components vs vanilla Django. First published numbers:
    **~3x faster startup/import, ~3.5x faster repeat renders** vs DJC.
- Deep design docs authored for each subsystem (slots, provide/inject,
  extensions, dependencies, asset loading, dynamic components, on_render).

## 4. Framework features designed & shipped (the "fully fledged framework" story)

Big-ticket capabilities that moved DJC from "utility" to "framework
comparable to Pydantic/FastAPI in DX":

- **Type system overhaul** (v0.140) - class-attribute-based typed component
  inputs (args/kwargs/slots), `{{ component_vars.* }}`, IDE autocomplete;
  Pydantic validation via the `djc-ext-pydantic` extension. This is the
  "Pydantic/FastAPI-comparable" hook.
- **Extension / plugin system** - `ComponentExtension` API with a rich hook
  surface: `on_extension_created`, `on_slot_rendered`, `on_template_loaded/
  compiled`, `on_js_loaded`, `on_css_loaded`, `on_dependencies`. Extensions
  can register **custom CLI commands** and **URL routes**. Enabled
  third-party preprocessing (Markdown, Pug) and integrations.
- **JS/CSS dependency management** - automatic dependency rendering (removed
  the old middleware), **scoped-by-default JS**, `get_js_data()`/
  `get_css_data()` reactive variables, pluggable deps strategies
  (`document`/`fragment`/`simple`/`prepend`/`append`/`ignore`).
- **HTML fragments** for **HTMX / AlpineJS / vanilla JS** partial rendering.
- **Slots & fills** system (Vue-like), prepared for v1.
- **provide / inject** (dependency injection across the component tree).
- **Component tree navigation** - `parent`, `root`, `ancestors`.
- **Hot reload** of component templates/JS/CSS without server restart.
- **Python expressions inside template tags**; error traces that preserve the
  original Python traceback.

## 4b. Design leadership / written technical vision (RFCs)

A distinct strength, not just "features shipped." Juro drives the project's
direction through long-form written proposals, then implements them.

- **141 issues authored**, ~35 of them roadmap/proposal/design RFCs; repo has
  **85 discussion threads**, several started by Juro.
- **Multi-version product roadmap** authored as connected RFCs:
  - **#1499 "Template versions"**: a staged V1->V2->V3 migration strategy to
    make Django templates "safer, faster, and lintable" without breaking
    users, via a per-component `version` opt-in (incremental, not a flag day).
  - **#1004 "v3: Decoupling from Django"**: the plan to turn a Django library
    into a standalone, framework-agnostic templating engine (the seed of
    Citry). Enumerates every Django coupling point and how to abstract it.
  - **#1141 "[v2] Ideas"**: the V2 feature slate (Python expressions in
    templates, marking constant vars for ~50% render savings, slot caching),
    each tracked as proposed / accepted / rejected.
- **API-redesign RFCs** that shaped the public API: phasing out the component
  registry (#1195), "Python-less" template-only components sourced from user
  feedback (#1240), scoped slots (#494), middleware-free dependency rendering
  (#478), first-class HTML fragments (#635), component caching (#992),
  `on_render` (#1085), tree navigation (#1252). Mostly written as proposals
  first, debated, then shipped.
- **~71,000 words of design specs in Citry** across 14 documents
  (`docs/design/`), each with prior-art survey, chosen design, alternatives,
  and falsification criteria (`migration_djc.md` 2,941 lines,
  `dependencies.md` 889, `component_slots.md` 811). Distinctive practice: write the
  design doc *before* touching high-risk code.
- Decisions **grounded in user feedback**: proposals cite Reddit threads,
  issues, and real migration blockers, not just personal preference.

## 5. Engineering rigor / cross-cutting

- **CI matrix**: Python 3.10–3.14 on Ubuntu + Windows; **cross-browser E2E**
  (Chromium, Firefox, WebKit, via Playwright). Made the test matrix **10x
  faster** (v0.149).
- **Custom tooling**: bespoke pre-commit linters enforcing Rust/Python
  binding consistency, workspace membership, dependabot coverage; asv
  benchmark suite that posts **per-PR performance comparisons** as comments.
- **Monorepo** with Rust workspace + per-language Python packages; maturin
  module mapping; PyO3 glue as an explicit cross-language contract.
- **Community / maintainer work**: triaged 141 issues, onboarded
  contributors, wrote extensive docs (mkdocs site). Notable adopters in the
  Django ecosystem.

## 6. Decisions locked for the prose

- **Performance number: the Citry benchmark** (~3x faster startup,
  ~3.5x faster repeat renders vs django-components, our own harness). Backup
  figures: 6-7x validation (PR #945), ~20% end-to-end (v0.145).
- Frame Citry as "**led design and built the core**" (pre-1.0, not shipped).
