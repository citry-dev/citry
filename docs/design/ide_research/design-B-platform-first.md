# Design B: platform-first IDE integration

**Date: 2026-07-07. Status: design proposal** (one of three competing drafts
for [`../ide_integration.md`](../ide_integration.md); this one argues the
platform-first angle). Repo claims cite `file:line`; web claims come from the
`ide_research/` recon corpus, all verified against live sources on 2026-07-07
(see Sources). Two claims were re-verified directly for this draft (maturin
binary packaging, JetBrains LSP file targeting); they are marked inline.

Terms used throughout, defined once. **LSP** (Language Server Protocol) is
the editor-agnostic protocol a standalone "language server" process speaks to
give any editor completion, hover, diagnostics, and go-to-definition.
**Pest** is the Rust parser generator citry's template grammar is written in.
**tree-sitter** is an incremental, error-tolerant parsing framework that
Neovim, Zed, and Helix use natively for highlighting, and that Rust programs
can embed as a library. A **TextMate grammar** is a regex-based highlighting
grammar, the format VS Code, Sublime, and JetBrains all consume. A **virtual
file** (or shadow file) is generated code that exists only so an existing
tool can analyze it, with a **source map** recording which generated position
corresponds to which template position.

---

## 1. Prior art

What was searched before designing, per CLAUDE.md Mechanism 1:

- **The full recon corpus in this directory**, all dated and web-verified
  2026-07-07:
  [`recon-citry-tooling-surface.md`](recon-citry-tooling-surface.md) (what
  the parser and bindings offer today, and the 7-item engine punch list),
  [`recon-vue-tooling.md`](recon-vue-tooling.md) (Vetur, Volar, JetBrains
  arc), [`recon-python-template-tooling.md`](recon-python-template-tooling.md)
  (djlsp, djls, PyCharm, Pylance, python-inline-source, tailwind),
  [`recon-lsp-architectures.md`](recon-lsp-architectures.md) (the four
  server-runtime options and the editor coverage table), and
  [`recon-framework-tooling-field.md`](recon-framework-tooling-field.md)
  (templ, Svelte, Astro, HEEx, Blade, Herb, with maintenance statistics).
- **Standing decisions in the tree** that this design builds on and does not
  reopen: [`../source_languages.md`](../source_languages.md) (no
  highlight-only stopgap, `*_lang` attributes, curated rich-editing set, the
  staged extension-grammar-server path, sections cited inline below);
  [`../extensions_roadmap.md`](../extensions_roadmap.md) section 5 (LSP #23,
  formatter #22, highlighting #24 are standalone tooling on the Rust parser,
  not extensions; the component-introspection API is #26);
  [`../template_grammar.md`](../template_grammar.md) (def/use variable linking kept in the AST
  for exactly this purpose, `template_grammar.md:399-405`).
- **The engine source itself**: parser entry and error behavior
  (`crates/citry_template_parser/src/parser.rs:63-71`, `:125-130`), token
  spans (`crates/citry_template_parser/src/ast.rs:20-35`), variable tracking
  (`ast.rs:508-539`), `TagRules`
  (`crates/citry_template_parser/src/parser_context.rs:31-62`), the
  unconditional pyo3 dependency
  (`crates/citry_template_parser/Cargo.toml:12`; workspace pin with
  `extension-module` at `Cargo.toml:19-20`), the PyO3 error flattening
  (`crates/citry_core_py/src/template_parser.rs:33-38`), the compiler entry
  (`crates/citry_template_parser/src/compiler.rs:110`), and the vendored ruff
  crates including `ruff_server`, `ty_server`, and `ruff_python_parser`
  (`Cargo.toml:29-38`,
  `third_party/rust/ruff/crates/ruff_server/Cargo.toml:34-35`).
- **Existing highlight assets**: the two Pygments lexers
  (`packages/py/pygments_citry/pygments_citry/__init__.py:29-43`) and their
  hand-kept mirror of the built-in tag list
  (`crates/citry_template_parser/src/constants.rs:56`,
  `packages/py/pygments_citry/pygments_citry/citry_html.py:31-33`).
- **Tracked issues**: #22 (formatter), #23 (LSP, with the `[tool.citry]`
  registry-discovery design), #24 (highlighting), #26 (component
  introspection), #27 (JS bindings via wasm), read via `gh` in the recon
  pass.
- **Nothing else exists**: no server crate, no grammar artifacts beyond
  Pygments, no editor packages. `packages/` contains only `py`; `crates/`
  contains the four engine crates. Checked the tree directly.

---

## 2. The thesis: build the end state, because citry already paid for most of it

Every framework surveyed in the corpus that shipped serious editor support
converged on the same end state: **the framework's own parser, reused
directly inside a native language server, plus declarative grammars for the
editors that consume those, plus a virtual-file bridge to the host type
checker.** Vue took ten years and three architectures to get there. The
Django ecosystem's first-generation Python server (djlsp) is being lapped by
a second-generation Rust one (djls). templ's one maintainer went straight to
the end state and runs a production proxy LSP with 40 open issues repo-wide.
The interim architectures are not stepping stones; they are things you build
twice.

Citry should skip the interim generation entirely, because it starts where
the others arrived:

1. **The expensive half of a language server is already built and shipping.**
   A language server is, at its core, a parser that keeps exact positions,
   tracks names, and validates structure. Citry's Rust parser produces exact
   spans on every node (`ast.rs:20-35`), tracks used and introduced variables
   per scope with positions kept specifically for def/use linking
   (`ast.rs:508-539`, `template_grammar.md:399-405`), collects slots with
   required-ness, and validates per-tag rules through the caller-supplied
   `TagRules` (`parser_context.rs:31-62`). Herb spent a year building this
   before its server; Svelte maintains svelte2tsx forever; citry has it as a
   sunk cost.
2. **The context problem, the one the whole Python ecosystem punts on, is
   citry's structural advantage.** Django tools cannot know a template's
   variables statically (djlsp resorts to manual `{# type #}` comments), but
   a citry template and the Python that feeds it live on one class, and the
   root template's `used_variables` is exactly "the inputs the caller must
   supply". Only a server with full AST access exploits this; a
   highlight-grade integration wastes the advantage.
3. **The distribution pipeline already exists.** citry ships Rust to PyPI
   through a maturin wheel matrix today. A server binary rides the same
   matrix (maturin packages plain binaries as wheel scripts via its `bin`
   bindings; verified against the maturin docs 2026-07-07). djls and ruff
   prove the pattern end to end.
4. **The assets compound instead of accumulating.** In this design the
   tree-sitter grammar is not a highlighting nicety: it is also the server's
   error-tolerant parser (the htmx-lsp2 / jinja-lsp pattern), and it unlocks
   Neovim, Zed, Helix, and GitHub as side effects. The component
   introspection API (#26) feeds the server, the web-types JSON for
   JetBrains, Storybook, and `Component.Docs`. One platform, many faces.
5. **Vendors adopt platforms; they do not sustain reimplementations.**
   JetBrains, with a paid IDE and a dedicated team, abandoned its own Vue
   template type checker and adopted the framework's server, then donated to
   it. The only assets worth a solo maintainer's time are protocol-level
   ones (a server, grammars, metadata JSON) that editors plug in, which is
   precisely what "platform" means here.

The honest counterargument is opportunity cost: months of platform work is
months not spent on framework features, for a framework that does not yet
have a large user base. Section 9 makes that falsifiable rather than
hand-waved: the ladder has an explicit pause point, and adoption evidence
gates the expensive rungs.

---

## 3. Architecture

### 3.1 Overview

Seven components. Rust is the single source of truth, per repo doctrine; the
server links the parser crate directly, with no binding hop and no
serialization boundary.

```
crates/citry_template_parser        engine: spans, variables, TagRules,
                                    structured diagnostics, offset-aware
                                    parse entry, `python` cargo feature
        |
        | direct crate link (no FFI, no wasm, no PyO3)
        v
crates/citry_language_server        one binary `citry-ls`:
                                    `citry-ls serve` (LSP over stdio)
                                    `citry-ls check` (CI batch diagnostics)
        |                                   uses tree-sitter-citry in-process
        |                                   for broken-input tolerance
        |
        +--> packages/py/citry (sidecar)    `citry inspect --json`: registry
        |                                   dump run with the project's
        |                                   interpreter (optional, enhances
        |                                   static analysis)
        |
editors/vscode                      extension: TextMate grammars (standalone
                                    + Python injection), LSP client,
                                    per-platform vsix
editors/jetbrains                   thin plugin: LspServerDescriptor +
                                    bundled binary + TextMate bundle
editors/zed, editors/sublime,       thin glue; Neovim and Helix are config
  + config snippets                 entries pointing at the binary
grammars/tree-sitter-citry          the tree-sitter grammar + queries,
                                    mirrored to a standalone repo for
                                    editors that fetch by git URL
```

### 3.2 Engine groundwork (the enabling contract changes)

These are small, but four of them touch high-risk surfaces (AST structs, the
PyO3 surface, the compiler output contract), so each goes through the
prior-art header, plan mode, and the cross-binding audit when implemented.
They come first because every later component consumes them, and because
retrofitting contracts after consumers exist is where Volar lost months.

1. **A `python` cargo feature on `citry_template_parser`.** Today pyo3 is
   unconditional (`crates/citry_template_parser/Cargo.toml:12`) with
   `#[pyclass]` inline on every AST struct, and the workspace pins pyo3 with
   `extension-module` (`Cargo.toml:19-20`), meaning the crate expects to live
   inside a Python process. A standalone server binary cannot link that.
   Gate pyo3 behind a feature (`#[cfg_attr(feature = "python", pyclass)]`),
   with `citry_core_py` enabling it. Mechanical but cross-cutting; it also
   unlocks the wasm builds issue #27 wants, as a side effect.
2. **Structured diagnostics.** Parse errors carry accurate spans internally
   but flatten to exception strings at the PyO3 boundary
   (`citry_core_py/src/template_parser.rs:33-38`), and a top-level grammar
   failure is re-wrapped with a whole-input span (`parser.rs:125-130`). Add
   a diagnostic type (span, message, stable code) to the crate's public
   surface and carry it across PyO3. The server, `citry-ls check`, and the
   Python API all consume the same type.
3. **A public offset-aware parse entry.** The offset machinery for parsing a
   string embedded at a position inside a larger file exists and is used
   internally for nested templates (`parser_context.rs:117-135`) but the
   public entry always starts from zero (`parser.rs:114` keeps
   `parse_template_inner` private). Expose it, so a template inside a `.py`
   file parses directly into host-file coordinates.
4. **Reserve the source-map slot in the compiler output contract.** The
   compiler emits Python source as a documented contract
   (`compiler.rs:110`). The virtual-Python milestone (3.7) needs a mapping
   from generated ranges back to template offsets. Reserving the channel now
   (an optional side-table the compiler can emit) is cheap; adding it after
   more consumers exist is a breaking change to a contract CLAUDE.md already
   marks high-risk.
5. Two one-liners from the recon punch list while touching the AST: expose
   `HtmlAttr.kind` to Python (`ast.rs:267-268` has no getter) and correct
   the stale `Template.comments` docstring.

What this design does **not** ask of the engine: error-recovering parsing in
Pest. That is a research project against Pest's design; the tree-sitter
grammar covers broken input instead (3.4).

### 3.3 The language server: `crates/citry_language_server`

A new workspace crate producing one binary, `citry-ls`, built on
**tower-lsp-server** (the maintained community fork, v0.23.0 as of
2025-12-07, used by Biome, Oxc, and django-language-server). The trait-based
async API keeps boilerplate low for a template-scale language; if the fork
ever stalls, the fallback is `lsp-server`, whose reference implementations
(`ruff_server`, `ty_server`) are already vendored in-tree as copyable
structure (`third_party/rust/ruff/crates/`).

Responsibilities, in dependency order:

- **Region location.** For `.py` documents, find the embedded template, js,
  and css regions by parsing the Python source with the vendored
  `ruff_python_parser` (`Cargo.toml:35`): `Component` subclasses, their
  `template` / `js` / `css` string attributes
  (`packages/py/citry/citry/component.py:295-324`), the `*_lang`
  declarations, and `Kwargs` / `Slots` class shapes with field names, types,
  and docstrings. No regex string-finding (the tailwind `classRegex` bug
  tail is the cautionary case); no Python runtime needed for this path. For
  standalone template files, the whole document is one region.
- **Parsing, two-layer.** The strict Pest parser (via the offset-aware
  entry) is the authority: when a region parses, its AST powers everything
  semantic. When it does not (most keystrokes), the embedded
  tree-sitter-citry parse supplies a best-effort tree for highlighting,
  folding, and completion context, and the last good Pest AST answers
  identity questions. Diagnostics always come from the Pest parser, so a
  squiggle is never speculative (the Vetur trust lesson).
- **Component knowledge, static-first.** Derive each component's `TagRules`
  from the statically analyzed `Kwargs` / `Slots` and feed them into
  `parse_template`, which then validates unknown attributes, missing
  required inputs, and slot names natively (`parser_context.rs:31-62`).
  This is the same machinery the engine already uses for built-in tags;
  component-aware diagnostics need no new parser features, only data.
- **Registry sidecar, optional.** Dynamically registered components that
  static analysis cannot see come from `citry inspect --json`, a small
  command in the `citry` package that imports the user's `Citry` instance
  (located via the `[tool.citry]` design from issue #23, the registry at
  `packages/py/citry/citry/component_registry.py:86`) and dumps component
  names, inputs, slots, and file paths. The server invokes it with the
  project's interpreter and degrades gracefully when it fails, because
  running user code must never be load-bearing (djlsp's operational
  weakness).
- **LSP features, v1 set:** diagnostics (parse + component validation),
  completion (`<c-*>` tag names, attribute names from `Kwargs`, slot names,
  closing tags), hover (component and input docs from docstrings),
  go-to-definition and find-references for template variables (directly off
  `used_variables` / `introduced_variables`) and go-to-component (tag to
  class), document symbols, folding, and semantic tokens (standard token
  types with modifiers, since custom types degrade to nothing in stricter
  clients).
- **`citry-ls check`:** the same analysis as a batch run over the project,
  with text and JSON reporters. This is the CLI twin every mature stack
  ships (`vue-tsc`, `astro check`, `svelte-check`), it lands before the
  server (section 5), and it is what CI and pre-commit consume.

### 3.4 Grammars: two artifacts, one of them load-bearing

- **tree-sitter-citry** (`grammars/tree-sitter-citry/`, developed in the
  monorepo so the parser and grammar cannot drift, CI-mirrored to a
  standalone `citry-dev/tree-sitter-citry` repo because Zed, Helix, and
  nvim-treesitter fetch grammars by git reference). Covers citry-HTML with
  injections both ways: Python injected into `{{ ... }}`, and citry injected
  into `template = """..."""` strings via a query file shipped for the
  Python grammar. Includes an external scanner for raw-text elements
  (`<c-raw>`, `<script>`, `<style>`). This grammar is server infrastructure
  first (the tolerant parser in 3.3) and editor reach second (Neovim, Zed,
  Helix, GitHub's highlighting service).
- **TextMate grammars** (inside `editors/vscode/`, reused by the JetBrains
  TextMate bundle and Sublime): a standalone citry-HTML grammar for template
  files, plus an injection grammar into `source.python` scoped to the known
  class attributes, mirroring the region logic the Pygments lexer already
  encodes. Best-effort coloring by design; the documented `{{ {'a': {}} }}`
  brace limitation (`source_languages.md:402-417`) is accepted and corrected
  by semantic tokens where clients paint them.

Both grammars, plus the Pygments lexers, mirror one token taxonomy (built-in
tag names, expression and comment delimiters). That is three hand-kept
mirrors of `constants.rs:56`. The drift guard is a validator in
`scripts/check.py` that extracts the tag list from each artifact and diffs
it against the Rust constants, failing CI on mismatch, the same pattern the
repo already uses for mirrored dependency pins.

### 3.5 Editor glue

Thin per-editor packages, none containing analysis logic:

- **`editors/vscode`**: the extension. Contributes the language id
  (`citry-html`), both TextMate grammars, and an LSP client launching the
  bundled `citry-ls`. Published per-platform (one vsix per OS/arch with the
  right binary) to both the VS Code Marketplace and Open VSX, since Cursor,
  Windsurf, and VSCodium default to Open VSX and unclaimed names there are
  an active supply-chain surface.
- **`editors/jetbrains`**: a thin plugin with an `LspServerDescriptor`
  pointing at the bundled binary plus the TextMate bundle for base
  highlighting. The native LSP API is free for all users since 2025.2/2025.3
  and the client API is open-sourced in the 2026.2 cycle. One real
  uncertainty is called out in section 9: the platform docs do not
  explicitly promise that a second server can attach to `.py` files PyCharm
  already owns (the `isSupportedFile` hook suggests it can; verified against
  the IntelliJ Platform docs 2026-07-07, which state no restriction but
  frame LSP as supplementary). LSP4IJ is the fallback client, and template
  files are the guaranteed path.
- **`editors/zed`**: a small Rust extension referencing the grammar mirror
  and downloading `citry-ls` from GitHub releases.
- **Neovim / Helix / Sublime**: configuration artifacts, not code. A Mason
  registry entry and an lspconfig server definition; a Helix
  `languages.toml` entry (documented snippet first, upstream PR when
  traction justifies); a Sublime syntax package plus `LSP-citry` helper.

### 3.6 Component metadata for IDEs this design does not target

A `web-types.json` generator on the component-introspection API (#26):
web-types is the JetBrains-backed, framework-agnostic JSON format describing
components, attributes, and slots, consumed natively by JetBrains IDEs. It
buys `<c-*>` completion in template files for PyCharm users who install
nothing but citry. Cheap (a serializer over data the introspection API
already holds), and it is the "declarative metadata for the cheap 80%"
channel the Vue/JetBrains history says vendors actually adopt.

### 3.7 Virtual Python: type-aware expressions, deliberately lower priority

The templ/Volar/svelte2tsx move, adapted: for each component, generate a
shadow `.py` in which every template expression appears in a type-checkable
position inside a function whose parameters are typed from the component's
declared interface (`Kwargs` fields, `template_data` return shape), emit the
source map reserved in 3.2, run **Pyright** (open-source, actively
maintained, the checker citry's VS Code audience already runs) over the
shadow files, and map diagnostics back to template positions.

Strictly staged:

- **Stage one, batch (`citry-ls check --types`):** shadow files generated
  into a cache directory, checked in CI. No editor involvement, no
  keystroke-time constraints, works in every editor at once. This is the
  `svelte-check` shape, and it is where the value concentrates.
- **Stage two, live, only if stage one earns trust:** publish shadow files
  on document change and either proxy a Pyright server (templ's model,
  URI/position rewriting both ways) or surface only mapped diagnostics.
  The four predictable cost centers from templ's issue history (tolerant
  parsing, source-map robustness, Windows URIs, the proxied server fighting
  back) are budgeted, not discovered.

Why lower priority is the correct priority and not a hedge: the gating
dependency is not tooling but the component interface contract. Expressions
are evaluated against a dynamic context today
(`compiler.rs:172-195` treats `{{ ... }}` content as Python for
`safe_eval`), so shadow files are only as good as the declared types on the
context, which is the typing work already in flight for Events. Sequencing
typed expressions after structural intelligence also matches the observed
value curve: Vetur proved that metadata completion plus trustworthy
structural diagnostics deliver most of the perceived value, and Vetur also
proved that shipping type diagnostics before they are trustworthy poisons
the whole extension's reputation. Never behind a permanent experimental
flag: batch first, live only when it meets the same bar as everything else.

What is explicitly out: deep inference inside expressions (slot prop
inference, narrowing across template constructs). That is TypeScript-shaped
machinery Python's checkers cannot be driven into from outside; the ceiling
is honest typed-name and attribute checking.

---

## 4. Editor coverage matrix

What the end state delivers per editor, and which milestone (section 5)
turns each cell on.

| Editor | Base highlighting | Semantics (completion, diagnostics, hover, go-to-def) | Typed expressions | citry ships | Milestone |
|---|---|---|---|---|---|
| VS Code + forks (Cursor, Windsurf, VSCodium) | TextMate grammars (standalone + `.py` injection) | Full, via `citry-ls` in the extension | Batch via `check --types`; live in stage two | Extension on Marketplace + Open VSX, per-platform vsix | M1 (color), M3 (semantics), M6 (types) |
| PyCharm / JetBrains | TextMate bundle in the plugin; web-types completion in template files | Full for template files via native LSP API; inline `.py` regions pending the attach question (section 9) | Batch (CI); live undecided | Thin plugin on JetBrains Marketplace; web-types JSON | M4 (+ M5 web-types) |
| Neovim 0.11+ | tree-sitter grammar + queries (incl. Python injection queries) | Full, native LSP client | Batch | Mason entry, lspconfig definition, grammar registration | M1 (color), M4 (wired) |
| Zed | tree-sitter via extension | Full | Batch | Zed extension in the extensions registry | M4 |
| Helix | tree-sitter grammar + queries | Full except semantic tokens (unsupported there) | Batch | `languages.toml` snippet, later upstream PR | M1 (color), M4 (wired) |
| Sublime Text | TextMate-derived syntax | Full via the LSP package, semantic tokens opt-in | Batch | Syntax package + `LSP-citry` on Package Control | M4 |
| GitHub.com (read-only) | tree-sitter service for standalone template files; `.py` stays Python-highlighted | n/a | n/a | linguist registration, traction-gated | Deferred |
| vscode.dev | Same TextMate grammars | Possible later via a WASI build of `citry-ls` (unlocked by the `python` feature gate) | n/a | Nothing extra in the base plan | Deferred |

Two structural facts the matrix encodes: the server is the only
write-once-run-everywhere artifact, and the grammar work splits the editor
world in half (TextMate for VS Code/JetBrains/Sublime, tree-sitter for
Neovim/Zed/Helix), so both grammars are mandatory for full coverage.

---

## 5. Milestone ladder

Each rung ships user-visible value on its own; none is scaffolding-only.
Efforts are focused solo-maintainer time, calibrated against the field data
(templ: one person; Svelte: two people over years; Herb: server one year
after parser, but citry's parser exists).

| Rung | Deliverable | User-visible value | Effort |
|---|---|---|---|
| **M0: engine contracts** | `python` cargo feature; structured diagnostics across PyO3; offset-aware parse entry; whole-input-span fix; source-map slot reserved in the compiler contract; `HtmlAttr.kind` getter | Better parse errors in the Python API immediately; everything else is unblocked | 1.5-2 weeks (small diffs, but four plan-mode passes over high-risk surfaces) |
| **M1: grammars + extension skeleton** | tree-sitter-citry (grammar, scanner, queries, mirror repo); TextMate standalone + Python-injection grammars; VS Code extension shipping color only; taxonomy validator in `scripts/check.py` | Correct highlighting for inline and file templates in VS Code, Neovim, Helix (and Zed once M4 wires it); the first thing every evaluating user sees | 3-4 weeks (the external scanner and the dual injection direction are the hard parts) |
| **M2: `citry-ls check`** | The server crate lands as a binary with the `check` subcommand: parse diagnostics plus component validation (static `TagRules` derivation), text + JSON output; `citry check` in the Python CLI invoking it; wheel packaging proven here | "Typos and missing inputs fail in CI, with exact template positions", in every editor and no editor; the README's reliability promise made mechanical | 2-3 weeks |
| **M3: `citry-ls serve`** | The LSP: document store, region location, two-layer parsing, v1 feature set (3.3), semantic tokens; VS Code extension wires the client | The headline: the editor knows your components, inside `.py` strings, first in the django-components family | 6-10 weeks (the long pole; includes UTF-16 position mapping, incremental document sync, and a beta cycle) |
| **M4: editor rollout** | JetBrains thin plugin (spike the `.py`-attach question in week one), Zed extension, Mason + lspconfig, Helix snippet, Sublime packages, Open VSX publication | PyCharm, Neovim, Zed, Helix, Sublime users get the same server | 2-3 weeks spread out (each glue artifact is days, plus registry review latencies) |
| **M5: registry sidecar + web-types** | `citry inspect --json`; server consumes it with graceful fallback; web-types generator on #26 | Dynamically registered components complete correctly; PyCharm completion with zero plugin installed | 1.5-2 weeks |
| **M6: typed expressions, batch** | Shadow-`.py` generation with source maps; Pyright over the cache dir; diagnostics mapped back; `check --types` | Type errors in `{{ ... }}` caught in CI | 4-6 weeks, **gated on declared component interfaces** (the Events typing work) and on the pause-point review below |
| **M7: typed expressions, live** | Shadow-file publication on change; proxy or diagnostics-only integration with Pyright | Hover types and typed completion inside expressions | 6-10 weeks; only if M6 diagnostics earn trust in the field |

Cumulative to the end of M4: roughly 4 to 5.5 months of focused solo work.
**Pause point:** after M2 (about 7-9 weeks in), the project has grammars,
CI checking, and an extension in the marketplaces, which is already ahead of
every Python component framework. If adoption evidence at that point is
absent (section 9, falsifier 5), M3 onward waits without wasting anything:
M0-M2 artifacts are all things any alternative design needs too.

---

## 6. Distribution and packaging

- **The server binary rides PyPI.** A `citry-lsp` package
  (`packages/py/citry_lsp/`) built with maturin's `bin` bindings, which
  package a plain Rust binary into the wheel as a script on `PATH`
  (verified against maturin docs 2026-07-07). Same CI matrix as the
  existing `citry_core` wheels, so the platform cost is marginal.
  `uv tool install citry-lsp` or `pipx install citry-lsp` serves every
  editor whose glue expects a binary on `PATH`. This is the djls/ruff
  pattern, and it fits an audience that has Python by definition.
- **GitHub release archives** per platform as the canonical download source
  for Zed, Mason, and any future Homebrew formula, generated by
  cargo-dist-style automation from tags.
- **VS Code: per-platform vsix** with the binary embedded (works offline
  and behind proxies), published to the Microsoft Marketplace and Open VSX
  on every release. Claim the `citry` names on both registries at M1, before
  anything valuable exists, as squat protection.
- **JetBrains Marketplace** for the thin plugin, binary bundled as a plugin
  resource.
- **Version skew policy: lockstep.** The server, grammars, extension, and
  `citry` release together from the same monorepo tag; the server refuses
  (with a clear diagnostic, not a crash) to analyze a project whose pinned
  `citry` major.minor is newer than its own. Astro folding its language
  tools back into the monorepo, and templ never separating them, are the
  precedents; separate release trains invite exactly the contract drift
  Mechanism 4 exists to prevent.

---

## 7. Maintenance cost, honestly assessed for one maintainer

The field data says one or two people can carry this; it also says what it
costs. Line items, steady state:

- **The platform tax is a trickle, not a wave.** Once adopted, expect
  weekly-to-monthly patch releases driven by editor quirks, LSP client
  deviations, and Windows path/URI encoding (templ's single largest issue
  cluster). Budget a consistent couple of hours per week indefinitely, more
  in the month after each editor rollout.
- **Three grammar mirrors plus per-editor query variants.** Pygments,
  TextMate, and tree-sitter each restate the token taxonomy, and
  tree-sitter needs slightly different query files per editor. The CI
  validator catches tag-list drift mechanically, but structural grammar
  changes (new template constructs) cost a day or two across all mirrors
  each time. The mitigation is upstream of tooling: V3 syntax is stable,
  and grammar changes are already gated as high-risk.
- **The server is a real codebase.** Realistically 5-10k lines of Rust
  (document store, position mapping, dispatch, feature handlers) that one
  person owns. The vendored `ruff_server`/`ty_server` give copyable
  structure, and templates are component-sized (no whole-project graph in
  memory, none of the Volar memory economics), but it is a second product
  next to the framework.
- **Dependency posture.** tower-lsp-server is a community fork; its trait
  surface is thin enough that migrating to the vendored `lsp-server`
  pattern is a bounded refactor, not a rewrite, if the fork stalls.
  Pyright is a dependency only of M6+, and only as an external process
  whose JSON output is consumed; no internals are patched (the vue-tsc
  lesson is a hard rule here).
- **The virtual-Python transform is a permanent line item once built.**
  svelte2tsx has needed two dedicated maintainers for six years, tracking
  both language ends. Citry's version is smaller (expressions only, not a
  whole component-to-TSX transform), but it still tracks citry syntax,
  Python typing releases, and Pyright behavior. This is exactly why it is
  gated and batch-first: stage one has CI-grade latitude, no
  keystroke-time robustness demands.
- **What keeps the total shape sustainable:** every editor is glue over one
  server (N editors never means N codebases); grammars are data with a
  drift validator; the sidecar is a hundred lines of Python; and the
  lockstep release train means no independent version matrix to test.

The single biggest cost is not any line item: it is that M3 (6-10 weeks) is
a long stretch with no shippable increment in the middle. The ladder
mitigates by making M0-M2 independently valuable, but the M3 trough is real
and should be entered deliberately, after the pause-point review.

---

## 8. What this design deliberately does not build

- **A Python (pygls) language server, even as a prototype.** It is the
  cheapest demo and the only option that sees the live registry natively,
  and the Django ecosystem already ran the experiment: its Python server is
  being superseded by a Rust one. Prototypes of this kind become
  load-bearing and then become the thing you rewrite. The registry access
  it uniquely offers is captured by the sidecar at 2% of the cost.
- **A Node server on volar.js.** Volar's payoff is TypeScript-ecosystem
  machinery (tsserver plugins, TS virtual code) that has no Python
  equivalent, its runtime is free only inside VS Code (every other editor
  must find Node, real friction for a Python audience), and it would put
  the framework's tooling on a second-language stack against the repo's
  Rust-is-the-source-of-truth doctrine. The one thing it would make cheap,
  HTML/CSS assistance inside templates, is deliverable by delegation and
  bundled language data at acceptable cost.
- **A native JetBrains PSI plugin** (the deep injection route that gives
  full in-string semantics in PyCharm). It is a second full codebase in a
  third technology, and the entire Vue/JetBrains history says the durable
  position is "framework ships the server, IDE consumes it". Built only if
  the LSP attach path fails (section 9) *and* PyCharm demand proves large.
- **Highlight-only stopgap conventions** (teaching the python-inline-source
  fork about components, typed string aliases, `# language=` guidance as
  the official story). Decided already (`source_languages.md:367-377`),
  and this recon corpus independently confirmed the decision: those are
  per-editor dead ends maintained by forks.
- **Anything that replaces, forks, or patches host tooling.** No takeover
  of `.py` files from Pylance/Pyright, no mypy plugin as a load-bearing
  channel, no patching checker internals. Volar's takeover mode and
  vue-tsc's string-patching are the two best-documented failure modes in
  the corpus.
- **A public serialized AST dump format (JSON).** The server links the
  crate; Python gets the PyO3 object graph. A serialized AST would be a
  third versioned contract with no consumer in this design. If the planned
  JS binding (#27) needs one later, it is designed then, deliberately.
- **Deep expression type inference** beyond what shadow files plus Pyright
  naturally give (section 3.7). TypeScript-only economics.
- **Error-recovering parsing inside the Pest grammar.** The dual-parser
  split (tree-sitter tolerant layer, Pest authority) buys the behavior
  without redesigning the grammar, whose atomicity rules are the repo's
  most cascade-prone surface.
- **linguist/GitHub registration and a vscode.dev WASI build**, until
  traction justifies them. Both are cheap later and worthless early.

---

## 9. Falsifiers

Evidence that would kill or reroute this design, stated so the judges and
future sessions can actually test them:

1. **The `python` feature gate proves impractical.** If gating pyo3 breaks
   the Python contract, the maturin build, or measurably regresses the
   Python binding (the audit in M0 would show it), the no-binding-hop
   premise dies, and the honest fallback is the Node+wasm server, which
   this design otherwise rejects. This is testable in the first two weeks.
2. **Parse latency fails the keystroke budget.** No parse benchmarks exist
   (render was benchmarked, parsing was not). If a full Pest reparse of a
   realistic component region cannot stay comfortably under ~10ms on
   mid-range hardware, and the tree-sitter layer cannot mask it, the
   two-layer model needs rethinking before M3. Measure during M1, not
   after M3.
3. **JetBrains LSP cannot attach to `.py` documents PyCharm owns.** The
   platform docs place no explicit restriction (verified 2026-07-07;
   `isSupportedFile` is plugin-controlled) but do not promise coexistence
   with native Python support either, and nobody in the corpus has shipped
   exactly this. If the M4 spike fails on both the native API and LSP4IJ,
   PyCharm's inline-template story requires the PSI plugin this design
   refuses, and PyCharm (citry's likely second-largest audience) drops to
   template-file support plus web-types. That would materially weaken the
   platform claim and strengthen a design that prioritizes JetBrains-native
   work.
4. **The dual-parser split produces visible disagreement.** If the
   tree-sitter grammar and the Pest parser diverge often enough that users
   see highlighting that contradicts diagnostics (or completions inside
   regions the authority rejects), and the taxonomy validator plus test
   corpus cannot hold them together, the tolerant layer becomes a liability
   and the design regresses to last-good-tree only, losing Neovim/Zed/Helix
   highlighting quality as collateral.
5. **Adoption evidence is absent at the pause point.** If, when M2 ships,
   citry itself has no meaningful external usage (no marketplace installs
   of the M1 extension, no issue traffic asking for editor support, flat
   PyPI numbers), then months of M3+ platform work is premature relative to
   framework features, and the correct move is to hold at M2 (grammars +
   CI checking are cheap to keep alive) until the framework earns the
   audience. This is the falsifier for the whole platform-first bet, and it
   is deliberately scheduled at the cheapest possible stopping point.
6. **Virtual-Python diagnostics fail the trust bar.** If M6 batch checking
   produces false positives at a rate that makes beta users disable it
   (the Vetur signature), M7 is cancelled and M6 stays CI-only or is
   withdrawn; the structural feature set stands on its own. Measured by:
   defaults kept on in real projects after a month.
7. **The solo-maintainer trickle exceeds budget.** If post-M4 issue load
   sustainably exceeds a few hours a week (tracked honestly across two or
   three months), the editor matrix contracts to VS Code + one grammar
   family rather than silently rotting across six channels.

---

## Sources

Repo sources cited inline as `file:line`; load-bearing ones:
`crates/citry_template_parser/src/{parser.rs,ast.rs,parser_context.rs,compiler.rs}`,
`crates/citry_template_parser/Cargo.toml`, `Cargo.toml` (workspace),
`crates/citry_core_py/src/template_parser.rs`,
`packages/py/citry/citry/{component.py,component_registry.py}`,
`packages/py/pygments_citry/pygments_citry/`,
`docs/design/{source_languages.md,extensions_roadmap.md,template_grammar.md}`,
and issues #22, #23, #24, #26, #27.

Web claims are grounded in the four recon reports in this directory, whose
sources were all accessed and version-checked 2026-07-07:
[`recon-citry-tooling-surface.md`](recon-citry-tooling-surface.md),
[`recon-vue-tooling.md`](recon-vue-tooling.md),
[`recon-python-template-tooling.md`](recon-python-template-tooling.md),
[`recon-lsp-architectures.md`](recon-lsp-architectures.md),
[`recon-framework-tooling-field.md`](recon-framework-tooling-field.md).

Re-verified directly for this draft, 2026-07-07:

- maturin `bin` bindings package plain Rust binaries into wheels as scripts
  on `PATH` (auto-detected without pyo3, or explicit via `-b bin` /
  `pyproject.toml`): <https://www.maturin.rs/bindings.html>
- IntelliJ Platform LSP docs: `isSupportedFile()` controls which files start
  a server, with no stated restriction against natively supported file
  types; the docs frame LSP as supplementary to custom language support:
  <https://plugins.jetbrains.com/docs/intellij/language-server-protocol.html>
  (note this page lags the 2025-09 and 2026-06 JetBrains blog posts on LSP
  availability and open-sourcing, which the LSP-architectures recon cites
  directly).
