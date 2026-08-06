# Design A: ship-first, the smallest useful ladder

**Date: 2026-07-07.** One of three competing design drafts for citry's IDE
integration, feeding [`../ide_integration.md`](../ide_integration.md). This
draft optimizes for **time-to-first-value for a solo maintainer**: every rung
ships in days-to-weeks, delivers visible value on its own, and builds an asset
the next rung reuses. Type-aware template intelligence is explicitly deferred
(section 8), not because it lacks value, but because everything before it is
cheaper, is not blocked on other design work, and covers what users notice
first.

Terms used throughout, defined once: **LSP** (Language Server Protocol) is the
editor-agnostic protocol a separate "language server" process speaks to give an
editor diagnostics, completion, hover, and go-to-definition. A **TextMate
grammar** is a regex-based, declarative highlighting grammar (the base
highlighting format in VS Code, also readable by JetBrains and Sublime); an
**injection grammar** is a TextMate grammar that splices its rules into another
language's files, which is how string regions inside Python files get foreign
highlighting. **pygls** is the standard Python library for writing language
servers (v2.1.1, released 2026-03-25, verified on PyPI 2026-07-07). **Pygments**
is the Python syntax highlighter used by docs tooling. **TagRules** is the
per-tag validation rule set citry's parser accepts (allowed and required
attributes and slots per tag), defined in
`crates/citry_template_parser/src/parser_context.rs:31-62` and exposed to
Python.

---

## 1. Prior art

What was searched and read before proposing this design, per CLAUDE.md
Mechanism 1:

- **The full IDE research corpus in this directory**, all dated and
  web-verified 2026-07-07:
  [`recon-citry-tooling-surface.md`](recon-citry-tooling-surface.md) (what the
  parser and bindings already provide, and the 7-item engine punch list),
  [`recon-lsp-architectures.md`](recon-lsp-architectures.md) (the four server
  options and the editor/grammar matrix),
  [`recon-python-template-tooling.md`](recon-python-template-tooling.md)
  (djlsp, djls, PyCharm, Pylance, the in-string highlighting state of the art),
  [`recon-vue-tooling.md`](recon-vue-tooling.md) (Vetur/Volar lineage lessons),
  [`recon-framework-tooling-field.md`](recon-framework-tooling-field.md)
  (templ, Svelte, HEEx, Laravel, and the cost-ordered ladder this design
  adopts).
- **Standing decisions**: [`../source_languages.md`](../source_languages.md)
  sections 4.3-4.5 and 6 (no third-party highlight stopgap; the staged
  skeleton-then-grammar-then-server build path inside one citry extension; the
  curated rich-editing set), and
  [`../extensions_roadmap.md`](../extensions_roadmap.md) (tooling sits outside
  the extension layer; issues [#22](https://github.com/citry-dev/citry/issues/22)
  formatter, [#23](https://github.com/citry-dev/citry/issues/23) LSP/linter,
  [#24](https://github.com/citry-dev/citry/issues/24) syntax highlighting).
- **Status**: `TODO/project_status_june_2026.md:527-537` (section 9.4 files the
  formatter and LSP as longer-term, with variable tracking already in the AST).
- **Existing assets, read from source**: the Pygments package
  `packages/py/pygments_citry/` (two lexers: `citry` for full component files,
  `citry-html` for templates alone; the embedded-region detection in
  `pygments_citry/lexers.py:55-79`; the built-in tag list mirroring
  `RESERVED_TAG_NAMES` in `pygments_citry/citry_html.py:29-47`; packaging in
  `pyproject.toml`, built but unpublished), the `citry` console script
  (`packages/py/citry/pyproject.toml:48-49`), the component source attributes
  (`packages/py/citry/citry/component.py:142-145` and the `template` /
  `template_file` pairs), and `README.md:15-80` for the V3 syntax being served.
- **Spot-verified this pass** (parallel work is active in the tree):
  `TagRules` is `#[pyclass]`-exposed (`parser_context.rs:31`); parse errors
  still cross the PyO3 boundary as flattened strings
  (`crates/citry_core_py/src/template_parser.rs:33-38`).
- **Web checks this pass** (2026-07-07): pygls 2.1.1 on PyPI (actively
  maintained, Python 3.9-3.14); the `@vscode/python-extension` npm package API
  for discovering the selected interpreter
  (`PythonExtension.api()`, `environments.getActiveEnvironmentPath()`,
  `environments.resolveEnvironment()`), verified via the microsoft/vscode-python
  repository (the npmjs page itself returned HTTP 403). All other web claims in
  this draft are carried by the recon corpus, which verified them against live
  sources on the same date.

Nothing here re-litigates `source_languages.md`. In particular, the "no interim
highlighting" decision (section 4.4) forbids stopgap *marker conventions and
third-party forks*; it explicitly endorses the staged build path where citry's
own extension ships its grammar layer first and grows the server later
(section 4.5, "Each layer stands on its own"). Design A is that staging,
executed aggressively.

## 2. The thesis

Citry's editor story today is the django-components status quo: templates
present as inert strings. The recon corpus shows two things about the road out:

1. **The expensive features are not the valuable ones first.** Across the
   surveyed field, what users notice day to day is "my editor colors my
   templates", "typos are caught before render", and "my editor knows my
   components" (recon-framework-tooling-field, lessons 1-2). All three come
   from citry's own parser and registry. None needs a type checker, virtual
   documents, or error-tolerant parsing.
2. **Citry's unfair advantage is already built and already on PyPI.** The Rust
   parser tracks every span, every used and introduced variable, every slot,
   and accepts per-tag validation rules (`TagRules`), all reachable from Python
   through the shipped `citry_core` bindings today
   (recon-citry-tooling-surface, section 2). The cheapest path to real
   diagnostics is a thin Python process that imports what is already
   installed.

So design A ships, in order: the highlighting users see in minute one, a CI
linter that works in every editor at once, and a deliberately thin LSP that
turns the real parser's errors into squiggles and the component registry into
completions. Each rung is independently useful; the ladder can stop or pause at
any rung without stranding work.

## 3. Architecture

Four artifacts, three languages, no new binaries to distribute.

```
packages/py/pygments_citry/        exists; publish to PyPI          (Python)
editors/vscode/                    new: extension + grammars        (TypeScript + JSON grammars)
packages/py/citry/  (citry check)  new CLI subcommand               (Python, reuses citry_core)
packages/py/citry_lsp/             new: pygls server, `citry-lsp`   (Python, reuses citry_core + citry)
crates/citry_core_py/  (+ parser)  two small additive PyO3 changes  (Rust)
```

### 3.1 The VS Code extension (`editors/vscode/`)

One extension, named `citry`, that owns all three layers over time
(`source_languages.md:425-441`). At rung 1 it contains no server client, only:

- A **language contribution** `citry-html` for standalone template files
  (file association, `{# #}` comment config, bracket pairs). This is the
  `template_file` authoring mode, the easy case.
- A **TextMate grammar** for citry-HTML: HTML base, the built-in `<c-*>` tags
  called out (the same 13-tag taxonomy the Pygments lexer encodes,
  `pygments_citry/citry_html.py:29-47`), user components (`<c-Card>`) scoped
  distinctly, `{{ ... }}` bodies handed to Python scopes, `{# ... #}` as
  comments, `<script>` / `<style>` bodies to JS / CSS.
- An **injection grammar** into `source.python` that matches the component
  string attributes (`template`, `js`, `css` followed by `= """`), marks the
  bodies with `meta.embedded` scopes, and maps them through
  `embeddedLanguages` so bracket matching and comment toggling behave. This is
  the editor-side twin of `CitryPythonLexer` (`pygments_citry/lexers.py:55-79`):
  same detection idea, different render target. Detection keys on the exact
  attribute names, not on annotation text, which is precisely the brittleness
  the `python-inline-source` lineage and Tailwind's `classRegex` never escaped
  (recon-python-template-tooling, sections 7.1 and 8).

Known and accepted limitation: a TextMate grammar cannot count braces, so
`{{ {'a': {}} }}` mis-detects the expression boundary under a naive rule
(`source_languages.md:402-417`). The grammar gets the recursive
brace-and-string sub-rules that push this to rare inputs, and the remaining
edge cases are documented as best-effort coloring. Correctness lives in the
parser, which is the next two rungs' job.

### 3.2 The batch linter (`citry check`)

A new subcommand on the existing `citry` CLI
(`packages/py/citry/pyproject.toml:48-49`): discover components, parse every
template with the real parser, print diagnostics with the parser's annotated
snippets (Pest already renders line, column, source line, and caret). Two
discovery modes, both needed later by the server anyway:

- **Registry mode**: import the project's `Citry` instance via the
  `[tool.citry]` pointer in `pyproject.toml` (the design already recorded in
  issue #23), derive `TagRules` from each registered component's `Kwargs` /
  `Slots`, and pass them to `parse_template`, so unknown components, unknown or
  missing attributes, and slot violations are diagnosed by the parser itself
  (`parser_context.rs:31-62`; grammar rules 6-8 per
  recon-citry-tooling-surface, sections 2.3-2.4).
- **Static fallback**: when the project does not import cleanly, walk the
  files with Python's `ast` module, extract `template` strings from `Component`
  subclasses, and parse without `TagRules`. djlsp's introspection breaking on
  unimportable projects is the recorded scar to avoid
  (recon-python-template-tooling, section 10.3).

This is the `svelte-check` / `vue-tsc` pattern: the CLI twin ships before the
live server and shares its engine (recon-vue-tooling, lesson 8.1.5). It works
in CI and pre-commit, in every editor, on day one.

### 3.3 The thin language server (`packages/py/citry_lsp/`)

A pygls server, published as `citry-lsp` on PyPI (pure-Python wheel), installed
into the project's environment (`pip install citry[lsp]` pulls it via an
extra), started as a console script. "Thin" is a design commitment, not a
euphemism:

- **It answers only citry questions.** Diagnostics for template regions,
  completions and hover from the component registry and the parsed AST,
  go-to-definition for template variables. It never analyzes Python, never
  embeds a CSS or JS analyzer, never mirrors the user's project. Pyright /
  Pylance own the `.py` file; the citry server is a second, coexisting server
  registered for `python` documents plus the `citry-html` file type, the
  proven Ruff / Tailwind pattern (recon-python-template-tooling, section 6.2).
- **Region discovery is exact.** The server parses the Python document with
  the standard `ast` module and reads the known class attributes; positions of
  the string bodies come from the AST nodes. Template-relative parser spans are
  shifted into file coordinates by the server (mechanical; the engine-side
  offset-aware entry point, punch-list item 4, is a later nicety, not a
  prerequisite).
- **Registry knowledge is an enhancement with a fallback**, same two modes as
  `citry check`, sharing that code. The interpreter question (which Python owns
  this workspace) is answered in VS Code by the `@vscode/python-extension` API
  and elsewhere by an explicit setting, with the `[tool.citry]` pointer
  resolving the app instance. This is the classic failure mode of Python
  servers (djlsp's venv probing) and gets first-class error reporting instead
  of silent degradation.
- **Fail-fast parsing is accepted for v1.** The parser returns one error and
  no partial tree on invalid input (`parser.rs:63-71` per
  recon-citry-tooling-surface, section 3.2). The server therefore shows one
  precise squiggle per broken template, and holds the last good parse for
  completion and hover while the buffer is broken (the last-good-tree pattern,
  recon-lsp-architectures, section 5). One accurate squiggle from the real
  parser beats zero, and beats a second parser's approximations; multi-error
  recovery is deliberately out of scope (section 8).

### 3.4 Engine-side prerequisites (small, additive)

From the punch list in recon-citry-tooling-surface section 6, design A needs
exactly two items before rung 3, both additive PyO3-surface changes that go
through the Mechanism 4 cross-binding audit:

1. **Structured diagnostics across the PyO3 boundary** (punch-list item 2):
   an error type carrying span indices and line/col instead of only the
   flattened string (`citry_core_py/src/template_parser.rs:33-38`). The CLI
   can live with rendered strings; an LSP mapping squiggles, and a
   `citry check --format json` for CI annotations, should not regex positions
   out of prose. Roughly 2-4 days including the `.pyi` stub, wrapper, and
   tests.
2. **Expose `HtmlAttr.kind` to Python** (punch-list item 1): one
   `#[pyo3(get)]` plus a stub line (`ast.rs:267-268`). Trivial; needed so the
   server does not re-derive attribute classification.

Items 3 (whole-input-span wrap) and 4 (offset-aware parse entry) are
improvements the server can absorb later without design change. Items 5
(error-tolerant parsing) and 6 (feature-gating pyo3 for wasm) are exactly what
design A avoids needing.

## 4. The milestone ladder

Estimates are focused solo-maintainer weeks, not calendar weeks; they assume
the repo conventions (tests with every rung, `python scripts/check.py` green).
Each rung has a gate: ship it, use it on the docs site and example apps, and
only then start the next.

| Rung | Deliverable | Rough effort | What it buys | What it costs later |
|---|---|---|---|---|
| 0 | Publish `pygments-citry` to PyPI | 1-2 days | ```` ```citry ```` fences render everywhere Pygments runs (PyPI READMEs, Sphinx, third-party docs), not just the docs site | Nothing; package is built and tested |
| 1 | VS Code extension: `citry-html` language + TextMate grammar + injection grammar into Python strings | 1-2 weeks | Color in the editor where citry users actually live, for inline strings and template files; the single most visible improvement over django-components | A third mirror of the 13-tag taxonomy (see 7.2); brace edge cases as low-grade issue traffic |
| 2 | `citry check` CLI (registry mode + static fallback) | ~1 week | Parser-grade template validation in CI and pre-commit, in every editor at once; component-aware diagnostics via `TagRules`; builds the discovery code rung 3 reuses | Output format becomes a soft contract; JSON format wants engine item 1 first |
| 3 | `citry-lsp` on pygls: diagnostics for inline and file templates, wired into the VS Code extension | 3-4 weeks (incl. the two engine items and client wiring) | Red squiggles from the real parser as you type, with component-aware checks when the registry imports; the first-in-family semantic tool for a Python component framework | Interpreter-discovery support burden begins; single-diagnostic UX until tolerance work exists |
| 4 | Cheap intelligence: completion (component tags, attributes from `Kwargs`, slot names), hover (component docs, attribute types), go-to-definition (template variables via the used/introduced links; components via the registry), document symbols | 2-4 weeks | "My editor knows my components": the differentiating feature, entirely from existing AST and registry data | Feature surface to keep working per editor quirk |
| 5 | Editor long tail by documentation: Neovim / Zed / Helix / Sublime config snippets for the pip-installed server; JetBrains via LSP4IJ or the native LSP API | ~1 week of docs and testing per editor, no new code | LSP features in every LSP-capable editor without new codebases | Support questions from editors the maintainer does not use |

Cumulative: first visible value inside two weeks (rungs 0-1); the full ladder
to rung 4 is roughly two months of focused work. Everything below the line is
**not committed** by this design and re-evaluated on evidence: the formatter
(#22, needs the comment-association pass), semantic tokens, a tree-sitter
grammar, type-aware expressions (section 8).

Sequencing rationale, made explicit:

- **Rung 1 before any server** because highlighting is what every user sees in
  the first five minutes, it ships as pure data with no process to manage
  (recon-vue-tooling, section 5), and the extension shell it creates is the
  same one that later hosts the LSP client, so nothing is thrown away.
- **Rung 2 before rung 3** because the CLI exercises discovery, `TagRules`
  derivation, and diagnostics rendering with no protocol in the way, in a
  batch context where the strict parser is unconditionally fine. When rung 3
  starts, the risky parts are already tested and shipped.
- **Rung 3 before rung 4** because diagnostics are the trust-building feature
  and the thinnest possible protocol surface. Vetur's lesson is that
  distrusted diagnostics poison an extension's reputation
  (recon-vue-tooling, section 8.2.3); shipping only what the authoritative
  parser says keeps trust high from the start.

## 5. Editor coverage matrix

What design A delivers per editor, at full ladder (rung 5):

| Editor | Highlighting (inline `.py` strings) | Highlighting (template files) | Diagnostics + completion + hover | Citry ships | Channel |
|---|---|---|---|---|---|
| VS Code + forks (Cursor, Windsurf, VSCodium) | Yes (injection grammar) | Yes (grammar) | Yes (bundled LSP client) | Extension | Marketplace + Open VSX |
| PyCharm / JetBrains | No (deferred; needs a native plugin or injection contributor, section 8) | Partial (TextMate bundle for the `citry-html` file type) | Yes, via the native LSP API or LSP4IJ pointed at `citry-lsp` | Config docs now; thin plugin later | Docs; JetBrains Marketplace later |
| Neovim | No (no tree-sitter grammar in design A) | No | Yes (server config snippet; server installs with the project) | Config docs | Docs |
| Zed | No | No | Yes (LSP; extension later if demand) | Config docs | Docs |
| Helix | No | No | Yes, diagnostics-first (Helix has no semantic tokens; design A does not rely on them) | `languages.toml` snippet | Docs |
| Sublime Text | No | Yes (reads TextMate) | Yes (LSP package config) | Config docs | Docs |
| GitHub / docs sites (read-only) | n/a (`.py` files stay Python-highlighted) | Fences via `pygments-citry` on the docs site; GitHub fences unaffected | n/a | Already built | PyPI |

The honest reading: design A is **VS Code-first with LSP reach everywhere**.
The inline-string highlighting gap outside VS Code is the visible cost of not
building a tree-sitter grammar and a JetBrains plugin now; the LSP features
(the substance) still arrive in those editors because the server is a
pip-installed console script speaking a universal protocol. PyCharm is the
most important second target for this audience, and its two LSP routes (the
native API, free since 2025.2, and LSP4IJ) are documented and tested at rung 5;
a JetBrains-native plugin is a later, deliberate second codebase
(recon-python-template-tooling, section 10.3).

## 6. Distribution and packaging

- **`pygments-citry`**: PyPI, as-is (`packages/py/pygments_citry/pyproject.toml`
  already registers the `pygments.lexers` entry points).
- **`citry-lsp`**: PyPI, pure-Python wheel, no platform matrix at all. Declared
  dependencies: `pygls`, `citry-core`, `citry`. Installed into the project's
  environment, which is what lets it import the user's registry; `uvx citry-lsp`
  works for isolated installs at the cost of registry mode. Released in
  lockstep with `citry` from this monorepo (the djls / ruff versioning pattern,
  recon-lsp-architectures section 8.1), because the server's understanding of
  the grammar must track the parser the project renders with.
- **`citry check`**: rides the existing `citry` package and console script;
  nothing new to distribute.
- **VS Code extension**: one **universal** vsix (it bundles no binaries; the
  server lives in the user's environment), published to both the Microsoft
  Marketplace and Open VSX. Publishing to Open VSX is not optional: the fork
  audience (Cursor, Windsurf, VSCodium) defaults to it, and unclaimed names
  there have been an active supply-chain attack surface (January 2026 reports,
  per recon-lsp-architectures section 8.2), so claiming `citry` early is also
  defensive. No download-on-activation, no platform targets, no code signing
  pipeline: this is the cheapest possible extension distribution shape, and it
  is a direct consequence of the server being a PyPI package instead of a
  bundled binary.
- **Everything else is documentation**: config snippets for Neovim, Zed,
  Helix, Sublime, and the two JetBrains LSP routes, shipped on the docs site.

## 7. Maintenance cost, honestly

For one maintainer, the steady-state costs this design signs up for:

### 7.1 The predictable trickle

The field data says production editor tooling at this scope is
one-to-two-person sustainable, with a steady trickle of platform and
editor-quirk issues and weekly-to-monthly patch releases once adopted
(recon-framework-tooling-field, lesson 7: templ, Herb, Tailwind, Svelte).
Design A's shape minimizes the trickle's sources: no per-platform binaries
(no Windows-URI-times-binary-matrix class of bugs), no proxied host server
(no templ-style "gopls fights back" class), no source maps (no nil-map
crashes class). The classes that remain:

- **Interpreter discovery.** The predicted number-one support cost, inherited
  from every Python-resident tool (djlsp's venv/Docker probing tail). Budget
  for it: first-class "which Python, which app instance" status reporting in
  the server and the extension, and a troubleshooting docs page, from day one.
- **Grammar edge cases.** The brace-boundary approximation and quoting quirks
  arrive as small issues indefinitely. Each fix is a regex change plus a
  snapshot test; annoying, cheap, contained.
- **Editor quirks at rung 5.** Each documented editor adds occasional
  config-drift questions (Neovim API churn, LSP4IJ versioning). Docs-only
  surface, but nonzero.

### 7.2 The mirror tax

The TextMate grammar becomes the **third hand-kept mirror** of the built-in
tag taxonomy, after the two Pygments lexers
(`pygments_citry/citry_html.py:31-33` already carries the keep-in-step
comment pointing at `constants.rs`). Mitigation, worth the half day: a repo
validator (the `scripts/check.py` custom-validator slot) that extracts the tag
list from `constants.rs` and asserts the Pygments lexers and the TextMate
grammar JSON agree. That turns silent drift into a CI failure. New built-in
tags are rare (the set is 13 and stable per `README.md:75`), so the tax is
small once guarded.

### 7.3 The rewrite risk, priced in

The Django ecosystem's arc (Python djlsp, then Rust djls) says Python template
servers get rewritten in Rust when they grow (recon-lsp-architectures,
section 10.2). Design A accepts this consciously and prices it: the thin-server
discipline (no embedded analyzers, no virtual-document framework, citry
questions only) keeps the rewritable core small, and everything around it
survives a rewrite untouched: the grammars, the extension client, the
`citry check` UX and its test suite, the LSP feature tests (which are
protocol-level and server-implementation-agnostic), the docs, and the
distribution channels. If the ceiling is hit, the pygls server is the
executable specification for the Rust server, which is exactly the role
Vetur's experiments played for Volar. The bet being made: for
component-sized templates and citry-only questions, the ceiling is years away
or never; the falsifiers in section 9 say what "hit the ceiling" means
concretely.

## 8. What this design deliberately does not build

Each entry names the cost avoided and the trigger that would reopen it.

- **Type-aware template expressions** (virtual/shadow Python for Pyright or
  mypy, svelte2tsx-style). Avoided because: it is gated on declared, typed
  component interfaces (the Events typing work) before it can say anything
  useful (recon-framework-tooling-field, lesson 3); the transform plus source
  maps is a permanent maintenance line item, the single place where Svelte's
  two maintainers spend six years of effort; and no evidence yet says citry
  adoption hinges on it. Reopen when: typed component interfaces land, and
  rung 4 usage shows demand for expression-level intelligence. It then arrives
  as its own design with its own recon, likely CI-batch first.
- **A Rust language server now.** Avoided because: it is the most-code option
  (document store, UTF-16 position mapping, scheduling), it needs a
  per-platform binary pipeline the pure-Python server does not, and its one
  unique strength (performance headroom) solves no problem citry measurably
  has at component scale, while its one unique weakness (no native view of the
  live registry) sits exactly where citry's differentiating feature lives
  (recon-lsp-architectures, section 3.5). Reopen when: falsifier 1 or 3 fires.
- **A tree-sitter grammar.** Avoided because: it is a second full grammar
  (plus likely a C scanner for `<c-raw>`), a fourth taxonomy mirror, and
  per-editor query files, all to serve editors (Neovim, Zed, Helix) whose
  users still get the LSP's substance under design A. Reopen when: demand from
  those communities materializes, or error tolerance becomes load-bearing
  (the grammar then doubles as the server's tolerant parser, per
  recon-lsp-architectures section 4.2, and jumps the queue).
- **Error-tolerant / multi-error parsing in the engine.** Avoided because: it
  is a real design problem under Pest (punch-list item 5), and the
  last-good-tree pattern plus one accurate squiggle is a defensible v1.
  Reopen when: falsifier 3 fires.
- **A JetBrains-native plugin (PSI injection).** Avoided because: it is a
  separate codebase in a fourth language against a large API, and the LSP
  routes now reach JetBrains users for the substance. Reopen when: rung 5
  telemetry (issue traffic, user reports) shows PyCharm users blocked on the
  inline-highlighting gap specifically.
- **web-types emission for JetBrains.** Avoided because: web-types discovery
  is anchored in `package.json`, and no verified path exists for a
  Python-project layout to feed it; speculative work for an unproven channel.
  Reopen when: the JetBrains plugin work starts, where it becomes the cheap
  80% of component completion (recon-vue-tooling, section 6).
- **wasm builds and pyo3 feature-gating.** Not needed by anything above;
  that work belongs to the JS-bindings roadmap (#27), not to editor tooling.
- **The formatter (#22).** Not an IDE-integration deliverable yet; it needs
  the comment-association pass that does not exist, and it earns its own
  design. The LSP reserves the `textDocument/formatting` capability as
  unimplemented until then.
- **Semantic tokens.** An upgrade channel, not a baseline
  (recon-lsp-architectures, section 4.3); deferred until the grammar's
  best-effort coloring demonstrably misleads in practice.

## 9. Falsifiers

Evidence that would kill or materially bend this design:

1. **Parse latency.** No parse-latency numbers exist in the repo (the
   benchmarks measured rendering). Measure at rung 3 start: if parsing a
   representative component through `citry_core` from Python exceeds ~50ms
   p95, keystroke-cadence diagnostics need debouncing tuned; if a debounced
   300ms experience still lags on real projects, the Python-resident server
   premise is wrong and the Rust server (design B territory) is pulled
   forward.
2. **Interpreter discovery dominates.** If, despite the
   `@vscode/python-extension` API, the `[tool.citry]` pointer, and first-class
   status reporting, environment resolution is still the top issue category
   after rung 3 ships, the design's core convenience (living in the user's
   venv) is a liability, and a Rust server with static-analysis-first
   discovery wins.
3. **Fail-fast UX rejection.** If dogfooding shows that one-squiggle-at-a-time
   plus last-good-tree makes the server feel broken while typing (not merely
   modest), error tolerance becomes a prerequisite, which pulls the
   tree-sitter grammar or parser recovery work forward and breaks the
   weeks-not-quarters premise.
4. **JetBrains LSP routes cannot attach to `.py` regions.** The design assumes
   `citry-lsp` diagnostics on Python documents surface correctly through the
   native LSP API or LSP4IJ. If testing shows JetBrains clients will not route
   Python-file requests to a second server usably, PyCharm users get value
   only for `template_file` projects, and the native-plugin question reopens
   much earlier.
5. **Typing is the adoption driver.** If user evidence (issues, interviews,
   comparisons users actually cite) shows teams choose or reject citry on
   typed `{{ }}` intelligence, deferring type-aware features is the wrong
   bet and the shadow-file design (design C territory) deserves the
   investment first.
6. **pygls stalls.** The server bets on pygls staying maintained (currently
   healthy: 2.1.1, 2026-03-25, institutional backing). A stall is survivable
   (the LSP surface used is small) but would advance the Rust rewrite
   timeline.

## Sources

Repo sources are cited inline as `file:line`; the load-bearing ones:
`packages/py/pygments_citry/pygments_citry/{__init__.py,lexers.py,citry_html.py}`,
`packages/py/pygments_citry/pyproject.toml`,
`packages/py/citry/pyproject.toml`, `packages/py/citry/citry/component.py`,
`crates/citry_template_parser/src/{parser_context.rs,ast.rs,parser.rs}`,
`crates/citry_core_py/src/template_parser.rs`, `README.md`,
`docs/design/source_languages.md`, `docs/design/extensions_roadmap.md`,
`TODO/project_status_june_2026.md`, and GitHub issues
[#22](https://github.com/citry-dev/citry/issues/22),
[#23](https://github.com/citry-dev/citry/issues/23),
[#24](https://github.com/citry-dev/citry/issues/24).

Research corpus (all in this directory, dated and web-verified 2026-07-07):
[`recon-citry-tooling-surface.md`](recon-citry-tooling-surface.md),
[`recon-lsp-architectures.md`](recon-lsp-architectures.md),
[`recon-python-template-tooling.md`](recon-python-template-tooling.md),
[`recon-vue-tooling.md`](recon-vue-tooling.md),
[`recon-framework-tooling-field.md`](recon-framework-tooling-field.md).
Web claims attributed to a recon file above were verified there on 2026-07-07;
their source URLs are listed in each recon's Sources section.

Web sources checked directly this pass (accessed 2026-07-07):

- pygls on PyPI (v2.1.1, 2026-03-25, Python 3.9-3.14, actively maintained):
  <https://pypi.org/project/pygls/>
- `@vscode/python-extension` API for interpreter discovery
  (`PythonExtension.api()`, `environments.getActiveEnvironmentPath()`,
  `environments.resolveEnvironment()`), read from the
  microsoft/vscode-python repository (`pythonExtensionApi/`):
  <https://github.com/microsoft/vscode-python/tree/main/pythonExtensionApi>.
  The npmjs.com package page itself returned HTTP 403 during this pass; the
  GitHub source is the verification basis.
