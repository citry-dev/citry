# Design: IDE integration (editor tooling for citry)

**Status (2026-07-07): proposal, not yet maintainer-reviewed.** This document
awaits maintainer review before any implementation planning; nothing in it is
scheduled, and no code exists for it. It is the synthesis of a research and
design-panel process: five recon reports, three competing design drafts, and
two adversarial judge verdicts, all in
[`ide_research/`](ide_research/README.md) and all dated 2026-07-07. Both
judges ranked the ship-first draft
([`ide_research/design-A-ship-first.md`](ide_research/design-A-ship-first.md))
first, so this document builds on that skeleton and grafts the strongest
elements of the platform-first and ecosystem-first drafts onto it; section 11
records every contested decision and why it was resolved the way it was.

Related docs: the standing editor-experience decisions this design builds on
are in [`source_languages.md`](source_languages.md) (no highlight-only
stopgap, the `*_lang` attributes, the staged extension-grammar-server path).
The versioned runtime catalog is specified in
[`component_introspection.md`](component_introspection.md); it represents
classes successfully loaded into a `Citry` instance. Static analysis produces
a separate partially known record and does not serialize that record as
`ComponentInfo`. A later design must define that record plus its join key,
combined-envelope behavior, ambiguity rules, and failure behavior. The tooling
issues this document concretizes are
[#23](https://github.com/citry-dev/citry/issues/23) (language server) and
[#24](https://github.com/citry-dev/citry/issues/24) (syntax highlighting),
with [#22](https://github.com/citry-dev/citry/issues/22) (formatter),
[#26](https://github.com/citry-dev/citry/issues/26) (component
introspection), and [#27](https://github.com/citry-dev/citry/issues/27)
(JS bindings) adjacent (section 8). Operating rules:
[`/CLAUDE.md`](../../CLAUDE.md).

Terms used throughout, defined once. **LSP** (Language Server Protocol) is
the editor-agnostic protocol a separate "language server" process speaks to
give an editor diagnostics, completion, hover, and go-to-definition. A
**TextMate grammar** is a regex-based highlighting grammar (the base
highlighting format in VS Code, also readable by JetBrains and Sublime); an
**injection grammar** is a TextMate grammar that splices its rules into
another language's files, which is how string regions inside Python files get
foreign coloring. **tree-sitter** is an incremental, error-tolerant parser
framework Neovim, Zed, and Helix use natively for highlighting. **pygls** is
the standard Python library for writing language servers (v2.1.1, 2026-03-25,
verified on PyPI by both judges). **Pygments** is the Python syntax
highlighter used by docs tooling. **TagRules** is the per-tag validation rule
set citry's parser accepts (allowed and required attributes and slots per
tag), defined in `crates/citry_template_parser/src/parser_context.rs:31-62`
and already exposed to Python. **LSP4IJ** is Red Hat's free LSP client plugin
for JetBrains IDEs. **PSI** is JetBrains' internal parse-tree API that
native IDE plugins program against. **web-types** is a JSON format
JetBrains IDEs read to learn a project's custom components for completion.
A **vsix** is VS Code's extension package format.
**Registry mode** means citry tooling has imported the user's `Citry`
instance and knows the real component registry; **static mode** means it has
only parsed the project's files without running them.

---

## 1. Prior art (what was searched)

Per CLAUDE.md Mechanism 1. The full survey lives in the five recon reports;
this section carries the load-bearing findings with their strongest
citations, spot-verified against the tree on 2026-07-07 for this synthesis.

### 1.1 In this repo (verified against source)

**The parser already provides the core of a language server for valid
templates.** Every AST node carries exact spans (`Token`: start/end index,
line/col, `crates/citry_template_parser/src/ast.rs:20-35`); used and
introduced variables are tracked per scope as tokens with positions, kept on
the node specifically for def/use linking (`ast.rs:508-539`;
[`template_grammar.md`](template_grammar.md) records the intent); slots are collected with
required-ness; and `TagRules` (`parser_context.rs:31-62`, a `#[pyclass]`)
lets a caller feed per-tag validation into `parse_template`, which is exactly
the hook component-aware diagnostics need: derive rules from each
component's `Kwargs` / `Slots` and the parser itself reports unknown or
missing attributes and slot violations for every component in the rule map.
A tag with no entry in the map is allowed through unvalidated (the rule
lookup falls through to allow-anything, `parser.rs:1723-1733`; same shape
for slots, `parser.rs:2070-2081`), so unknown-component detection is a
small tool-side check against the registry, not a parser feature
(section 3.2). Full sweep:
[`ide_research/recon-citry-tooling-surface.md`](ide_research/recon-citry-tooling-surface.md).

**The gaps are all about invalid or changing input.** The Pest parser is
fail-fast: one error, no partial AST (`parser.rs:63-71`). A top-level grammar
failure is re-wrapped with a whole-input span (`parser.rs:125-130`). Errors
flatten to exception strings at the PyO3 boundary
(`crates/citry_core_py/src/template_parser.rs:33-38`). `HtmlAttr.kind` has no
Python getter (`ast.rs:267-268`). The parser crate depends on pyo3
unconditionally (`crates/citry_template_parser/Cargo.toml:12`), which blocks
standalone-binary and wasm reuse until feature-gated. The recon distills
these into a seven-item engine punch list; this design consumes two of them
now (section 3.5) and sequences the rest (sections 3.5 and 10).

**Templates live primarily inside Python files.** A component's template,
JS, and CSS are class attributes, inline multiline strings or `*_file` paths
(`packages/py/citry/citry/component.py:295-324`), and house style mandates
the inline form. So the defining constraint versus Vue or Svelte is that an
editor tool must first locate embedded regions in a `.py` file the Python
tooling already owns.

**Existing assets.** `pygments-citry` is built and unpublished
(`packages/py/pygments_citry/`): two Pygments lexers whose embedded-region
detection is working prior art for the region-location problem. The `citry`
console script exists (`packages/py/citry/pyproject.toml:48-49`). The
component registry is the knowledge source for registry mode
(`packages/py/citry/citry/component_registry.py:86`).

**Standing decisions this design does not reopen.**
[`source_languages.md`](source_languages.md) decided (sections 2, 4.3-4.5,
and 6.1): no highlight-only marker stopgaps (no typed aliases, no
third-party fork adoption, no `# language=` convention shipped as the
official story); the `*_lang` declaration attributes; a curated
rich-editing set; and a staged build path (extension skeleton, then
grammar, then server) where each layer ships on its own. [`extensions_roadmap.md`](extensions_roadmap.md) files the
LSP, formatter, and highlighting as standalone tooling on the Rust parser,
not extensions. Issue #23 already records the `[tool.citry]` pointer design
for locating the project's `Citry` instance.

### 1.2 The field (from the recon corpus)

- **Vue's ten-year arc**
  ([`ide_research/recon-vue-tooling.md`](ide_research/recon-vue-tooling.md)):
  tooling quality tracks how directly it reuses the framework's own compiler;
  the zero-server tier (a TextMate grammar) is what every user sees in the
  first five minutes and ships as pure data; a CLI checker twin (`vue-tsc`,
  `svelte-check`) shares the editor engine and delivers value in CI first.
  The graves: replacing or subordinating the host language's tooling
  (takeover mode), patching the host checker's internals (`vue-tsc`), and
  shipping diagnostics behind a permanent experimental flag (Vetur's
  distrusted template checking poisoned the whole extension's reputation).
  JetBrains, with a paid IDE and a dedicated team, abandoned its own Vue
  template type checker and adopted the framework's server.
- **Python template land**
  ([`ide_research/recon-python-template-tooling.md`](ide_research/recon-python-template-tooling.md)):
  nobody ships semantic template intelligence inside Python string literals
  today; highlighting-only injection grammars and PyCharm `# language=`
  comments are the state of the art. The proven semantics pattern is a
  second LSP attached to `python` documents alongside Pylance (Ruff,
  tailwindcss-intellisense), which coexists without any coordination.
  Pylance is closed and pyright refuses plugins, so there is no host-server
  integration point to wait for. Two Django template servers exist (djlsp in
  Python, active; djls with a Rust core, early stage); both target template
  files only and punt on context typing. Citry's structural advantage is
  that context resolution, the ecosystem's unsolved hard part, is local
  static analysis here: template and data live on one class, and the parser
  already tracks the variables.
- **Server architectures and editor mechanics**
  ([`ide_research/recon-lsp-architectures.md`](ide_research/recon-lsp-architectures.md)):
  four realistic server runtimes (Rust on `lsp-server`, Rust on
  `tower-lsp-server`, Node consuming a wasm parser, Python on pygls); the
  grammar world splits in half (TextMate for VS Code/JetBrains/Sublime,
  tree-sitter for Neovim/Zed/Helix); semantic tokens upgrade but never
  replace grammars (Helix cannot render them); JetBrains' native LSP API is
  free for all users since 2025.2 but is a **plugin API**, not a
  configuration surface; `ruff_server` and `ty_server` are vendored in-tree
  as reference code; distribution precedents are PyPI wheels (djls, ruff)
  plus per-registry extension artifacts.
- **Nine framework tooling stories**
  ([`ide_research/recon-framework-tooling-field.md`](ide_research/recon-framework-tooling-field.md)):
  templ proves a one-maintainer production proxy LSP is feasible and names
  the four predictable cost clusters: error-tolerant parsing, source-map
  robustness, Windows URIs, and the half the host checker does not cover
  (HTML tags, attributes, component references) being separate work.
  HEEx shows compile-time validation of declared component interfaces
  delivers most day-to-day safety in every editor at once. Registry-backed
  completion plus compile-time-style validation deliver most perceived
  value with no type checker. Declared, typed component interfaces are the
  gating dependency for template typing everywhere. Doing nothing is not
  available to citry: its vocabulary is open (user components plus embedded
  Python), unlike htmx's closed attribute set.

### 1.3 The design panel

Three drafts argued three optimization targets:
[`ide_research/design-A-ship-first.md`](ide_research/design-A-ship-first.md)
(time-to-first-value),
[`ide_research/design-B-platform-first.md`](ide_research/design-B-platform-first.md)
(the end-state platform: a Rust server, both grammar families, bundled
binaries),
[`ide_research/design-C-ecosystem-first.md`](ide_research/design-C-ecosystem-first.md)
(editor coverage per unit of effort, tree-sitter-canonical). Two judges
attacked all three:
[`ide_research/judge-1-maintainer-cost.md`](ide_research/judge-1-maintainer-cost.md)
(verdict A 8.4, C 5.6, B 5.3) and
[`ide_research/judge-2-user-experience.md`](ide_research/judge-2-user-experience.md)
(verdict A 7.45, B 6.88, C 5.99; on undiscounted end-state quality alone the
order flips to B first). Both prescribe the same composite: A's ladder as
the spine, B's destination and safeguards, C's evidence discipline and
JetBrains glue. That composite is this document.

---

## 2. Goals and non-goals

### 2.1 Goals

1. **Color where citry users live, in weeks.** Inline `template` / `js` /
   `css` strings and standalone template files get real highlighting in
   VS Code, with zero configuration and zero binaries.
2. **Parser-grade validation in every editor at once.** A `citry check`
   command runs the real parser (with component-aware `TagRules` checks
   when the registry imports) in CI, pre-commit, and any terminal.
3. **First-in-family editor semantics.** Diagnostics as you type,
   completion of component names, attributes, and slots, hover docs, and
   go-to-definition, from citry's own parser and registry, for inline and
   file templates. django-components ships none of this; citry would be
   first in the family.
4. **Reach every LSP-capable editor without per-editor codebases.** One
   server, thin documented glue elsewhere.
5. **Every stopping point leaves shipped, low-maintenance product.** No
   rung is scaffolding for a later rung; a stall strands nothing.

### 2.2 Non-goals (for this design's committed scope)

Each is a deliberate deferral with a reopening trigger in section 10:
type-aware `{{ ... }}` expressions; a Rust language server; a tree-sitter
grammar; error-tolerant or multi-error parsing in the engine; a
JetBrains-native (PSI) plugin; web-types emission; wasm builds; the
formatter (#22); semantic tokens; embedded CSS/JS language services in the
server (delegation to existing tools is documented instead, e.g. pointing
`tailwindCSS.includeLanguages` at citry template regions).

---

## 3. The chosen architecture

Four shipped artifacts plus two small engine changes. No new binaries to
distribute anywhere in the committed scope.

```
packages/py/pygments_citry/        exists; publish to PyPI            (Python)
editors/vscode/                    new: extension + grammars          (TypeScript + JSON grammars)
packages/py/citry/                 new CLI subcommands:               (Python, reuses citry_core)
                                     `citry check`, `citry inspect`
packages/py/citry_lsp/             new: pygls server, `citry-lsp`     (Python, reuses citry_core + citry)
crates/citry_template_parser/ +    two small additive changes         (Rust; Mechanism 2 + 4
crates/citry_core_py/                (structured diagnostics, kind)     when implemented)
```

### 3.1 The VS Code extension (`editors/vscode/`)

One extension, named `citry`, that owns all three layers over time (the
staged path `source_languages.md` section 4.5 records). At v0 it contains no
server client, only:

- A **language contribution** `citry-html` for standalone template files
  (file association, `{# #}` comment config, bracket pairs). This is the
  `template_file` authoring mode, the easy case.
- A **TextMate grammar** for citry-HTML: HTML base, the built-in `<c-*>`
  tags called out (the same 13-tag taxonomy the Pygments lexer encodes),
  user components scoped distinctly, `{{ ... }}` bodies handed to Python
  scopes, `{# ... #}` as comments, `<script>` / `<style>` bodies to JS /
  CSS.
- An **injection grammar** into `source.python` that matches the component
  string attributes (`template`, `js`, `css` followed by `= """`), marks
  the bodies with `meta.embedded` scopes, and maps them through
  `embeddedLanguages` so bracket matching and comment toggling behave.
  Detection keys on the **exact attribute names**, not on annotation text;
  textual annotation matching is precisely the brittleness the
  `python-inline-source` lineage and Tailwind's `classRegex` never escaped.

Known and accepted limitation: a TextMate grammar cannot count braces, so a
brace-heavy expression like `{{ {'a': {}} }}` can mis-detect the expression
boundary (`source_languages.md` documents the case). The grammar gets
recursive brace-and-string sub-rules that push this to rare inputs; the
remainder is documented best-effort coloring and will arrive as low-grade
issue traffic indefinitely (judge 2 named this cost; it is accepted
knowingly, with the tree-sitter grammar as the named upgrade path).

The TextMate grammar is the **third hand-kept mirror** of the built-in tag
taxonomy, after the two Pygments lexers. The same milestone adds a validator
to the repo check gate (`scripts/check.py` custom-validator slot) that
extracts the tag list from `constants.rs` and asserts the Pygments lexers
and the TextMate grammar agree, turning silent drift into a CI failure.

### 3.2 The batch linter (`citry check`)

A new subcommand on the existing `citry` console script: discover
components, parse every template with the real parser, print diagnostics
with the parser's annotated snippets. Two discovery modes, shared with the
server:

- **Registry mode**: import the project's `Citry` instance via the
  `[tool.citry]` pointer (issue #23's design), derive `TagRules` from each
  registered component's `Kwargs` / `Slots`, and pass them to
  `parse_template`, so unknown or missing attributes and slot violations
  on registered components are diagnosed by the parser itself. No new
  parser machinery; the hook exists and is data-driven. The parser lets a
  tag with no rules pass unvalidated (`parser.rs:1723-1733`), so
  unknown-component detection is one extra tool-side check, shared with
  the server: compare the parsed component tag names against the registry
  and report the tags it does not know. Per decision D9 (section 11),
  that check fires in registry mode only.
- **Static mode (fallback)**: when the project does not import cleanly,
  walk the files with Python's `ast` module, extract `template` strings
  from `Component` subclasses, and parse without `TagRules`. djlsp's
  introspection breaking on unimportable projects is the recorded scar this
  avoids.

This is the `svelte-check` / `vue-tsc` pattern: the CLI twin ships before
the live server and shares its engine. It works in CI and pre-commit, in
every editor, with no editor integration at all.

### 3.3 The registry dump (`citry inspect --json`)

A standalone command that emits the versioned runtime `ComponentCatalog` after
successfully importing the project's configured `Citry` instance. Split out as
its own early artifact (grafted from design C), it is independently useful to
scripts, CI, and the other planned consumers of the component-introspection API
(#26, including docs tooling and Storybook-style galleries). It is the natural
first consumer of that API and survives even if every editor rung dies.

The AST fallback described elsewhere in this document uses a separate IDE
record, not the runtime catalog schema. Before static fallback ships for this
command, the design must define that record, source-root discovery, its runtime
join key, ambiguity handling, and command behavior when application import
fails. Static absence never proves that a component is unknown. `citry check`
and the server may share discovery machinery without pretending their partial
static facts are `ComponentInfo` records.

### 3.4 The thin language server (`packages/py/citry_lsp/`)

A pygls server, published as `citry-lsp` on PyPI (pure-Python wheel),
installed into the project's environment (`pip install citry[lsp]` pulls it
via an extra), started as a console script. "Thin" is a design commitment:

- **It answers only citry questions.** Diagnostics for template regions,
  completion and hover from the component registry and the parsed AST,
  go-to-definition for template variables and components, document symbols.
  It never analyzes Python, never embeds a CSS or JS analyzer, never
  mirrors the user's project. Pyright / Pylance own the `.py` file; the
  citry server is a second, coexisting server registered for `python`
  documents plus the `citry-html` file type (the proven Ruff / Tailwind
  pattern).
- **Region discovery is exact.** The server parses the Python document with
  the standard `ast` module and reads the known class attributes; positions
  of the string bodies come from the AST nodes. Template-relative parser
  spans are shifted into file coordinates by the server (mechanical; an
  engine-side offset-aware parse entry is a later nicety, not a
  prerequisite).
- **Component knowledge has two tiers**, the same two modes as
  `citry check`, sharing that code. Interpreter discovery (which Python
  owns this workspace) is answered in VS Code by the
  `@vscode/python-extension` environments API and elsewhere by an explicit
  setting; the `[tool.citry]` pointer resolves the app instance. This is
  the classic failure mode of Python-resident servers and gets first-class
  status reporting ("which Python, which app instance, registry or static
  mode") plus a troubleshooting docs page from day one, instead of silent
  degradation. Multi-root workspaces (several projects, several venvs, one
  window) mean one server instance per workspace folder; the extension
  manages that explicitly.
- **Fail-fast parsing is accepted for v1, with its costs named.** The
  parser returns one error and no partial tree on invalid input, so the
  server shows one precise squiggle per broken template (all three drafts
  share this property; no plan on the table gives multi-error mid-keystroke
  diagnostics). While a buffer is broken, completion and hover answer from
  the **last good parse**, and the position-adjustment logic that keeps
  that tree usable mid-edit is budgeted work, not assumed free. Completion
  additionally needs a small hand-rolled **cursor-context scanner** over
  the current text ("am I inside a tag name? an attribute? a fill?"),
  because the moment a user wants tag completion (`<c-Ca`) is exactly when
  the buffer does not parse; the last good tree supplies the data, the
  scanner supplies the context. Judge 1 identified this as design A's
  weakest unbudgeted spot; it is priced into v1.1 (section 5).

Two hard behavior rules, adopted as grafts and stated up front:

- **False-positive posture (the Vetur trust lesson in one sentence):**
  unknown-component diagnostics only ever fire in registry mode, never from
  a static or degraded view. A dynamically registered component that static
  analysis cannot see must not produce a squiggle on a valid tag.
- **Version-skew refusal:** the server states, in one clear diagnostic,
  when the project's installed citry is newer (major.minor) than the
  server's own understanding, instead of mis-parsing. This matters doubly
  here because the skew is inverted: the server ships in the user's venv,
  so the user's pin decides which server version runs, and the extension
  must stay compatible with older servers in the field (the extension
  surfaces upgrade guidance when the server reports an older version at
  initialize).

### 3.5 Engine-side prerequisites (small, additive, one pass)

From the punch list in
[`ide_research/recon-citry-tooling-surface.md`](ide_research/recon-citry-tooling-surface.md)
section 6, the committed scope needs exactly one plan-mode pass over the
PyO3 surface, containing:

1. **Structured diagnostics across the PyO3 boundary** (punch item 2): an
   error type carrying span indices and line/col plus a stable code,
   instead of only the flattened string
   (`citry_core_py/src/template_parser.rs:33-38`). The CLI can live with
   rendered strings; an LSP mapping squiggles, and `citry check
   --format json` for CI annotations, should not regex positions out of
   prose. **Bundled into the same pass:** the whole-input-span fix (punch
   item 3, `parser.rs:125-130`), so a top-level grammar failure keeps its
   structured position. It is the same surface, the same plan-mode pass,
   and the same Mechanism 4 cross-binding audit; doing it separately later
   pays the process cost twice (judge 1 graft).
2. **Expose `HtmlAttr.kind` to Python** (punch item 1): one `#[pyo3(get)]`
   plus a stub line (`ast.rs:267-268`), so the server does not re-derive
   attribute classification. The stale `Template.comments` docstring gets
   corrected in the same touch (punch item 7).

Explicitly **not** asked of the engine now, with where each is sequenced:
the offset-aware public parse entry (punch item 4; the server shifts
positions itself, and the entry can be absorbed later without design
change), error-tolerant or multi-error parsing (punch item 5; only if
falsifier 4 fires, and then via the tree-sitter route rather than surgery
on the cascade-prone Pest grammar), the pyo3 feature gate (punch item 6;
it belongs to the JS-bindings work #27 and to the Rust-server pivot, and is
scheduled by whichever fires first), and the compiler source-map slot
(decision D5, section 11).

### 3.6 PyCharm and JetBrains, stated honestly

PyCharm is the second-largest editor among Python developers (25% main
editor to VS Code's 48% in the 2024 Python Developers Survey, verified live
by design C and re-verified by judge 2), and the honest story is the least
flattering part of this design:

- **Semantics route now: an LSP4IJ user-defined server template.** LSP4IJ
  supports declaring a language server with no plugin code (command plus
  file mappings), and definitions can be exported and imported as
  templates. Citry ships an importable JSON template on the docs site the
  same week the server first runs (grafted from design C). The JetBrains
  **native** LSP API is not a documented route here: it is a plugin API (an
  `LspServerDescriptor` lives in plugin code), so "config docs" cannot
  reach it; design A's contrary claim was judged factually wrong and is
  corrected in this synthesis. A thin official plugin (descriptor plus
  bundled server plus TextMate bundle) on the JetBrains Marketplace is a
  named later rung, once the server is stable.
- **The attach question is open and gets the program's first spike.**
  Whether any second LSP client (LSP4IJ or the native API) surfaces
  features on `.py` documents PyCharm's Python plugin already owns is
  unverified across the entire corpus, and both judges flagged it. The
  spike (days, against a stub server, testing both routes on `.py`
  documents) runs in **week one of v0**, before the coverage matrix is
  published anywhere user-facing, because its answer re-prices the
  second-largest audience for every plan.
- **No inline coloring in PyCharm under this plan, and the docs say so.**
  JetBrains' TextMate bundle mechanism only applies to file types no native
  plugin owns; `.py` belongs to PyCharm's Python plugin, so no bundle can
  color inside Python strings. Inline templates in PyCharm therefore get
  LSP diagnostics and completion (pending the spike) but no citry coloring
  until an official plugin adds native injection support, which is a named,
  triggered future rung (section 10), not an implicit never. PyCharm users
  can meanwhile use the IDE's own `# language=HTML` injection by hand;
  citry documents that it exists but does not ship or promote a marker
  convention, per the standing decision in `source_languages.md`. This
  framing is carried into user-facing docs verbatim (grafted from design
  C's "Note A", at both judges' direction).

---

## 4. Editor coverage matrix

What this design delivers per editor at the end of v1 (section 5). "Inline"
means templates in `.py` strings; "file" means `template_file` templates.
The JetBrains semantics cells are provisional on the week-one attach spike.

| Editor | Highlighting (inline) | Highlighting (file) | Diagnostics + completion + hover + go-to | Citry ships | Channel |
|---|---|---|---|---|---|
| VS Code + forks (Cursor, Windsurf, VSCodium) | Yes (injection grammar) | Yes (grammar) | Yes (bundled LSP client) | Extension | Marketplace + Open VSX |
| PyCharm / JetBrains | No (named future rung; section 3.6) | Partial (TextMate bundle for the `citry-html` file type) | Provisional: via the LSP4IJ template pointed at the venv's `citry-lsp`; native-API plugin later | LSP4IJ template JSON + docs; thin plugin later | Docs site; JetBrains Marketplace later |
| Neovim | No (no tree-sitter grammar in committed scope) | No | Yes (config snippet; server installs with the project) | Config docs | Docs |
| Zed | No | No | Yes (config snippet; extension later if demand) | Config docs | Docs |
| Helix | No | No | Yes, diagnostics-first (Helix has no semantic tokens; nothing here relies on them) | `languages.toml` snippet | Docs |
| Sublime Text | No | Yes (reads TextMate) | Yes (LSP package config) | Config docs | Docs |
| Emacs, Kate, any LSP editor | No | Varies | Yes (stdio console script) | Config docs | Docs |
| GitHub / docs sites (read-only) | n/a (`.py` stays Python-highlighted) | Fences via `pygments-citry` on the docs site and anywhere Pygments runs; GitHub fences unaffected (GitHub does not run Pygments) | n/a | Already built | PyPI |

The honest reading: this is **VS Code-first with LSP reach everywhere**.
The inline-highlighting gap outside VS Code is the visible cost of not
building a tree-sitter grammar and a JetBrains plugin now; the LSP features
(the substance) still arrive in those editors because the server is a
pip-installed console script speaking a universal protocol. Two named
support costs: tree-sitter-editor users get LSP features over completely
unhighlighted files, an odd half-experience that will generate "is this
broken?" questions; and every non-VS-Code editor config must name the
venv-specific server path per project (the server is a package in each
project's environment, not a binary on PATH).

---

## 5. Milestone ladder

Estimates are focused solo-maintainer weeks, not calendar weeks; they
assume the repo conventions (tests with every rung, `python
scripts/check.py` green). Each milestone has a gate: ship it, use it on the
docs site and example apps, and only then start the next. Version labels
are tooling milestones, not citry package versions.

### v0: visible value with no server (~3.5 to 5 weeks)

| Milestone | Deliverable | Effort | What it buys |
|---|---|---|---|
| v0.0 | Publish `pygments-citry` to PyPI; claim the `citry` name on the VS Code Marketplace, Open VSX, PyPI (`citry-lsp`), Package Control, and crates.io; run the **PyCharm attach spike** (stub pygls server; LSP4IJ and a scratch native-API descriptor, on `.py` documents) | ~1 week total (publication 1-2 days; claims are hours; spike 2-3 days) | ```` ```citry ```` fences render everywhere Pygments runs (docs site, Sphinx, PyPI READMEs; GitHub fences unaffected); squat protection (unclaimed Open VSX names are an active supply-chain surface); the coverage matrix's biggest unknown resolved before anything is promised |
| v0.1 | VS Code extension: `citry-html` language + TextMate grammar + injection grammar into Python strings; taxonomy validator in `scripts/check.py`; **measure parse latency** on representative components and record the numbers | 1-2 weeks | Color where citry users live, inline and file; the single most visible improvement over django-components; the latency numbers that decide falsifier 1 before any server is committed |
| v0.2 | `citry check` (registry mode + static fallback, text output; JSON output lands with the v1.0 engine work) | ~1 week | Parser-grade validation in CI and pre-commit, in every editor at once; the discovery and `TagRules`-derivation code the server reuses |
| v0.3 | `citry inspect --json` (first consumer of the #26 introspection API) | ~1 week | A scripting/CI-usable component inventory, independent of any editor |

**Pause review (between v0 and v1).** Adapted from design B's falsifier 5
at both judges' direction: if, when v0 ships, citry itself shows no
meaningful external usage (no installs of the v0 extension, no issue
traffic asking for editor support, flat PyPI numbers), then the v1 server
weeks are premature relative to framework features, and the defensible move
is to hold at v0 (grammars, CI checking, and the inspect command are cheap
to keep alive) until the framework earns the audience. The tension is
recorded honestly: judge 2 observed that the v1 features are also what
*generates* adoption and retention, so absent evidence is a prioritization
signal for the maintainer to weigh, not an automatic kill. The evidence bar
needs maintainer calibration (open question 1).

### v1: the language server (~6 to 10 weeks)

| Milestone | Deliverable | Effort | What it buys |
|---|---|---|---|
| v1.0 | The engine pass (structured diagnostics + whole-input-span fix + `HtmlAttr.kind`, section 3.5; one plan-mode pass, one cross-binding audit); `citry-lsp` on pygls serving **diagnostics** for inline and file templates; wired into the VS Code extension; `citry check --format json` | 3-4 weeks | Red squiggles from the real parser as you type, component-aware when the registry imports; first-in-family for a Python component framework |
| v1.1 | Intelligence: completion (component tags, attributes from `Kwargs`, slot names), hover (component and input docs), go-to-definition (template variables via the def/use links; components via the registry), document symbols; the last-good-tree position adjustment and the cursor-context scanner (section 3.4) | 2-4 weeks | "My editor knows my components", entirely from existing AST and registry data |
| v1.2 | Editor long tail by documentation: Neovim / Zed / Helix / Sublime config snippets; the **LSP4IJ importable template JSON** on the docs site; interpreter-troubleshooting page | 1-2 weeks (reads design A's "~1 week of docs and testing per editor" as an overestimate for docs-only config snippets; the LSP4IJ template JSON is the only new artifact) | LSP features in every LSP-capable editor without new codebases |

**Cumulative, stated honestly:** v0 plus v1 is roughly **10 to 15 focused
weeks**. Judge 1 specifically attacked the drafts' optimistic headline
("roughly two months" was the low edge of design A's own arithmetic); the
honest midpoint is closer to three months of focused solo time, and
calendar time is longer because the same person is building the framework.

### v2: evidence-gated, not committed

Nothing below is scheduled by this document; each item lives in section 10
with its trigger. The candidates, in the order the falsifiers would pull
them in: the Rust server pivot (the pre-written plan is design B's M0 + M3
architecture), the tree-sitter grammar (gated on design C's injection-spike
protocol), the thin JetBrains Marketplace plugin, the JetBrains native
injection (PSI) plugin for inline coloring, typed template expressions
(batch-first, gated on declared component interfaces from the Events typing
work), semantic tokens, and the formatter (#22, its own design).

---

## 6. Distribution and packaging

- **`pygments-citry`**: PyPI, as-is (the package already registers the
  `pygments.lexers` entry points).
- **`citry check` / `citry inspect`**: ride the existing `citry` package
  and console script; nothing new to distribute.
- **`citry-lsp`**: PyPI, pure-Python wheel, no platform matrix. Declared
  dependencies: `pygls`, `citry-core`, `citry`. Installed into the
  project's environment via the `citry[lsp]` extra, which is what lets it
  import the user's registry. Two named costs, priced rather than hidden:
  the extra pulls pygls and its dependency tree into the user's project
  environment, which some teams will refuse; and `uvx citry-lsp` works as
  the isolated alternative at the cost of registry mode (static mode still
  works). Released in lockstep with `citry` from this monorepo, because the
  server's understanding of the grammar must track the parser the project
  renders with; the skew-refusal diagnostic (section 3.4) covers the
  inverted case where the user's pin lags.
- **VS Code extension**: one **universal** vsix (it bundles no binaries),
  published to both the Microsoft Marketplace and Open VSX. Open VSX is not
  optional: the fork audience (Cursor, Windsurf, VSCodium) defaults to it.
  No download-on-activation, no platform targets, no signing pipeline; this
  shape is a direct consequence of the server being a PyPI package instead
  of a bundled binary.
- **Everything else is documentation**: config snippets for Neovim, Zed,
  Helix, Sublime, and the LSP4IJ template JSON, shipped on the docs site.
- If the Rust-server pivot ever fires, the distribution shape changes to
  per-platform binaries (wheels via maturin `bin` bindings on the existing
  CI matrix, per-platform vsix, GitHub release archives); that is
  documented in design B sections 5-6 and is also a **user-facing
  migration** (install shape and every editor config snippet churn), so the
  pivot plan includes a migration note for users, not just for the
  codebase.

---

## 7. How this touches the monorepo

No code is being written now; this table records the planned locations so
the maintainer can veto or move them before any implementation planning.

| Artifact | Location | Language | Status |
|---|---|---|---|
| Pygments lexers | `packages/py/pygments_citry/` | Python | exists; publish only |
| `citry check`, `citry inspect` subcommands | `packages/py/citry/` (CLI + the #26 introspection API) | Python | new |
| Language server | `packages/py/citry_lsp/` (`citry-lsp` on PyPI) | Python | new |
| VS Code extension + grammars | `editors/vscode/` (new top-level home for editor glue) | TypeScript + JSON grammars | new |
| Structured diagnostics, span fix, `kind` getter | `crates/citry_template_parser/` + `crates/citry_core_py/` + `_rust.pyi` + Python wrapper | Rust + stubs | new, additive; Mechanisms 1, 2, and 4 apply when implemented |
| Taxonomy validator | `scripts/validators/` | Python | new, with v0.1 |
| Editor setup docs, LSP4IJ template JSON, troubleshooting page | docs site (`docs_site/`) | Markdown/JSON | new |

The engine changes touch two high-risk surfaces named in CLAUDE.md (the
`#[pyclass]` contract and the PyO3 glue), so each goes through the
prior-art header, plan mode, and the cross-binding audit (the five
`LangImpl` files are unaffected by these two changes, but the audit
enumerates that explicitly rather than assuming it).

---

## 8. Relationship to tracked issues and the bindings roadmap

- **#23 (LSP / linter): this document is the design for it.** It consumes
  the issue's `[tool.citry]` discovery design and its variable-linking
  notes verbatim; `citry check` and `citry-lsp` are the two deliverables
  that issue anticipated.
- **#24 (syntax highlighting): discharged by v0.0 + v0.1** (Pygments
  publication, the TextMate and injection grammars). The tree-sitter
  grammar remains a v2 candidate, not part of #24's resolution.
- **#22 (formatter): out of scope, deliberately.** It needs the comment
  association pass the AST does not have (comments are collected but not
  attached to neighboring nodes), and it earns its own design. The LSP
  leaves `textDocument/formatting` unimplemented until then, and
  `citry check` does not grow `--fix`.
- **#26 (component introspection API): `citry inspect --json` is its first
  consumer.** The command's runtime JSON is the versioned soft contract from
  [`component_introspection.md`](component_introspection.md), shared with other
  planned consumers such as docs tooling and component galleries. The separate
  partially known static-analysis record remains an IDE design task.
- **#27 (JS bindings via wasm): independent, and deliberately untouched.**
  This design needs no wasm and no pyo3 feature gate; the gate
  (`crates/citry_template_parser/Cargo.toml:12` and every `#[pyclass]`
  site) remains #27's prerequisite and doubles as the Rust-server pivot's
  prerequisite, so it is scheduled by whichever of those fires first. If
  the pivot fires, the same gating work serves both consumers; nothing in
  the committed scope preempts or blocks it.
- **The Events typing work is the gating dependency for typed template
  expressions** (v2 candidate). Every framework that got real template
  typing has statically declared component interfaces; the shadow-file
  checker (the checker that type-checks a generated Python stand-in for
  the template, section 10) is only as good as the declared types on the
  context. That work is part of the IDE roadmap's future, not adjacent to
  it, and the typed expressions design should start (batch-first,
  `svelte-check`-shaped) only after those interfaces exist.

---

## 9. Maintenance cost, honestly

The field data says production editor tooling at this scope is
one-to-two-person sustainable, with a steady trickle of platform and
editor-quirk issues once adopted. This design's shape minimizes the
trickle's sources: no per-platform binaries (no Windows-URI-times-binary
matrix), no proxied host server, no source maps. What remains:

- **Interpreter discovery is the predicted number-one support cost**,
  inherited from every Python-resident tool. Budgeted mitigations: the
  environments API in VS Code, explicit settings elsewhere, first-class
  status reporting in the server and extension, and a troubleshooting page,
  all from day one. The adjacent first-run tail ("extension cannot find
  citry-lsp in the selected interpreter") is part of the same budget.
- **Grammar edge cases** (brace boundaries, quoting quirks) arrive as small
  issues indefinitely; each fix is a regex change plus a snapshot test.
- **The mirror tax**: three hand-kept encodings of the 13-tag taxonomy
  (two Pygments lexers, one TextMate grammar), guarded by the CI validator;
  new built-in tags are rare, so the tax is small once guarded.
- **Editor-quirk questions at v1.2**, including the named oddity of LSP
  features over unhighlighted files in tree-sitter editors.
- **The rewrite risk, priced in.** The thin-server discipline keeps the
  rewritable core small; the grammars, extension client, `citry check` UX
  and tests, protocol-level LSP feature tests, docs, and distribution
  channels all survive a Rust rewrite untouched, and the pygls server
  becomes the executable specification for it (the role Vetur played for
  Volar). The judges' fact-check matters here: the "Django abandoned the
  Python server path" narrative is overstated (djlsp is active; djls is a
  different author's early-stage project), so this is a priced risk with an
  unknown date, not a scheduled certainty. When it fires it is also a
  user-facing migration (section 6).

---

## 10. What this design deliberately does not build

Each entry names the cost avoided and the trigger that would reopen it.

- **Type-aware template expressions** (shadow Python for Pyright/mypy,
  svelte2tsx-style). Avoided because: gated on declared, typed component
  interfaces before it can say anything useful; the transform plus source
  maps is a permanent maintenance line item (Svelte's two maintainers, six
  years); no evidence yet says citry adoption hinges on it. Reopen when:
  typed component interfaces land **and** v1.1 usage shows demand for
  expression-level intelligence, or falsifier 6 fires. It then arrives as
  its own design, batch-first (CI), never behind a permanent experimental
  flag.
- **A Rust language server now.** Avoided because: most new code of any
  option, a per-platform binary pipeline the pure-Python server does not
  need, and its unique strength (performance headroom) solves no measured
  problem at component scale, while its unique weakness (no native view of
  the live registry) sits where citry's differentiating feature lives.
  Reopen when: falsifier 1, 2, or 3 fires. **The pivot plan is
  pre-written:** design B's M0 (engine contracts: the pyo3 feature gate,
  offset-aware entry) and M3 (the `citry-ls` crate on `tower-lsp-server`,
  with the vendored `ruff_server` / `ty_server` as reference structure),
  with B's distribution section for the packaging.
- **A tree-sitter grammar.** Avoided because: a second full grammar (plus
  likely a C scanner), a fourth taxonomy mirror, and per-editor query
  files, serving editors whose users still get the LSP's substance here.
  Reopen when: demand from those communities materializes, or error
  tolerance becomes load-bearing (falsifier 4), where the grammar doubles
  as the server's tolerant parser and jumps the queue. **The gate when
  reopened:** design C's injection-spike protocol runs first (prove
  Python-string injection editor by editor; C's falsifier F1 established
  that only Neovim's `;; extends` path is documented, Zed and Helix are
  unproven, and the coverage dividend hinges on it). **The mechanics are
  filed:** design C section 3.1 and its sources carry the verified
  distribution facts (Zed fetches grammars by repository URL plus revision
  only, forcing a CI-pushed mirror repo; Helix supports `subpath`; the
  nvim-treesitter registry model). They will be stale by reopening time,
  but the shape of the problem will not be.
- **Error-tolerant / multi-error parsing in the engine.** Avoided because:
  a real design problem under Pest (whose rule atomicity is the repo's most
  cascade-prone surface), and last-good-tree plus one accurate squiggle is
  a defensible v1. Reopen when: falsifier 4 fires; prefer the tree-sitter
  layer over grammar surgery.
- **A JetBrains-native plugin.** Two distinct rungs, both named: the
  **thin LSP plugin** (descriptor + bundled server + TextMate bundle, a
  small codebase) reopens when the LSP4IJ route proves too fiddly for
  ordinary PyCharm users or when the pivot produces a bundlable binary; the
  **native injection (PSI) plugin** that colors inside `.py` strings is a
  second full codebase against a large API and reopens only on evidence
  that PyCharm users are blocked on the inline-highlighting gap
  specifically.
- **web-types emission for JetBrains. Dead, with the verification
  recorded as the standing reason:** design C verified against live
  JetBrains sources that web-types discovery is keyed off `package.json`
  (or bundled in an IDE plugin), with no documented path for a Python-only
  project, and judge 1's own check confirmed it. Reopen only if JetBrains
  documents a non-npm discovery path; "JetBrains plugin work starts" is
  explicitly not the trigger, since a citry plugin would bundle the LSP
  and gain little from web-types.
- **wasm builds and pyo3 feature-gating.** Not needed by anything in the
  committed scope; that work belongs to #27 and to the pivot (section 8).
- **The formatter (#22)** and **semantic tokens**: section 8 and the
  non-goals cover both; semantic tokens are an upgrade channel to revisit
  if the grammar's best-effort coloring demonstrably misleads in practice.
- **Embedded CSS/JS language services, and any takeover, fork, or patch of
  host tooling.** The Vue lineage's clearest graves. Coexistence only,
  always.

---

## 11. Decisions and why (the graft record)

Each entry: what was contested across the drafts, what this synthesis
chose, and why, per the judges.

- **D1: design A's ladder is the spine.** Both judges ranked A first on
  their respective lenses (maintainer economics 8.4 vs 5.6 / 5.3; user
  experience 7.45 vs 6.88 / 5.99). It is the only ladder ordered by what
  users feel, the only plan whose first month is spent on assets that
  already exist, the only one with no binary distribution matrix, and the
  one whose every stopping point leaves shipped product. Judge 2's caveat
  is recorded: on undiscounted end-state quality, design B is better; the
  discount (when features ship, behind what gates) is what flips the
  order, and B's own pause-point logic concedes the expensive rungs should
  wait for adoption evidence that A generates fastest.
- **D2: a thin pygls server, with the Rust pivot pre-written.** Contested
  by design B ("prototypes become load-bearing and then become the thing
  you rewrite") and design C (same runtime choice as B). Resolved for
  Python because: it is the only option that natively sees the live
  registry (citry's differentiating feature), it reuses the shipped
  `citry_core` bindings with zero new binding work, and it makes
  distribution one pure wheel. The judges' fact-check weakened B's
  strongest argument: djlsp (Python) is active and shipping while djls
  (Rust) is early stage, so the evidence supports "the interim generation
  gets rewritten eventually", not "shipping it was a mistake"; users of
  the interim tools were served the whole time. The rewrite is therefore
  priced (section 9), the thin-server rule keeps the rewritable core
  small, and design B's M0 + M3 is documented as the executable pivot so
  the fallback needs no new design work (judge 1's conditional graft).
- **D3: PyCharm via the LSP4IJ template now, native plugin later, inline
  color honestly absent.** Design A's coverage matrix claimed JetBrains
  semantics "via the native LSP API or LSP4IJ" through config docs; judge
  2 convicted the native-API half (it is a plugin API) and both judges
  demanded C's honesty about inline coloring. Adopted: C's importable
  LSP4IJ template as the zero-plugin-code route, C's "Note A" framing in
  user docs, the thin plugin and the PSI plugin as separate named future
  rungs, and B's attach spike moved to week one of the whole program
  (judge 2: "no draft should ship its coverage matrix before this answer
  exists").
- **D4: TextMate injection now, tree-sitter deferred behind a gate.**
  Design C made tree-sitter the canonical first artifact; both judges
  found that ordering contradicted C's own survey data (the first-served
  editors hold a small audience slice, and the inline-injection dividend
  outside Neovim is unproven, C's own falsifier F1). Deferred, with C's
  spike protocol adopted as the mandatory gate when it reopens and C's
  verified distribution mechanics filed as the reopening notes (judge 1
  grafts). The accepted cost is named: best-effort brace boundaries in
  VS Code as permanent low-grade issue traffic.
- **D5: the compiler source-map slot is recorded, not implemented.** The
  judges split: judge 1 attacked B's reservation as prepaid speculative
  work on the repo's highest-risk contract ("a contract change consumed by
  nothing" if typed expressions never ship); judge 2 recommended reserving
  the channel early because retrofitting a mapping channel into the
  compiler output contract later is a breaking change (the Vue recon's
  source-map lesson), while reserving it before more consumers exist is
  cheap. Resolution: no change to the compiler output contract now. The
  requirement is recorded here
  and should be recorded in the typed-expressions issue when one exists:
  when that design starts (gated on the Events typing work), its **first**
  change is an optional, additive side-table the compiler can emit
  (generated range back to template offset), designed so existing
  consumers are untouched. Recording the intention now is the cheap part
  of judge 2's point; deferring the contract change is judge 1's. If an
  intermediate compiler-contract change ever threatens to foreclose an
  additive side-table, that change must weigh this recorded requirement
  (open question 4 asks the maintainer to confirm this resolution).
  Timing was contested the same way: judge 2 asked for the engine
  contract items as an early workstream running parallel to v0, and
  judge 1 attacked design B's engine-first ordering. The synthesis
  schedules the whole engine pass at v1.0, after the pause review, so
  holding at v0 spends zero engine work, per judge 1's economics;
  judge 2's early-parallel preference is noted and rejected for that
  reason.
- **D6: `citry inspect --json` is its own early milestone.** Grafted from
  design C (judge 1 graft 6): days of extra work over embedding discovery
  inside `citry check`, and it creates an independently useful artifact
  plus the natural first consumer of the #26 introspection API, useful to
  scripts and CI with no editor anywhere.
- **D7: a formal pause review sits between v0 and v1.** Grafted from
  design B's falsifier 5 (judge 1 graft 2), with judge 2's counterpoint
  recorded alongside it (section 5): the gated features are also the ones
  that create adoption, so the review is a deliberate maintainer decision
  with the tension stated, not an automatic kill.
- **D8: lockstep releases plus the skew-refusal diagnostic, with the
  inversion named.** Design B's polite-refusal diagnostic is adopted
  (judge 1 graft 4), and judge 1's attack on A is absorbed: because the
  server lives in the user's venv, the user's pin decides which server
  runs, so the extension must tolerate older servers and surface upgrade
  guidance rather than assume lockstep holds in the field.
- **D9: unknown-component diagnostics fire only in registry mode.** The
  Vetur trust lesson turned into one hard rule (judge 1 graft 5): a
  static or degraded view never squiggles a valid tag it merely cannot
  see. Distrusted diagnostics poison an extension's reputation faster
  than missing ones.
- **D10: honest arithmetic and honest degradation.** Judge 1's attacks on
  A's own numbers are absorbed rather than repeated: the committed-scope
  total is stated as 10-15 focused weeks (not "roughly two months"); the
  completion-in-broken-buffers work (cursor-context scanner,
  last-good-tree adjustment) is budgeted by name in v1.1; the venv
  contamination and per-project install friction are stated in
  distribution; the mid-keystroke experience is one squiggle at a time
  and the docs will not imply otherwise; and the "LSP without color"
  oddity in tree-sitter editors is a named support cost, not a surprise.

---

## 12. Falsifiers

Evidence that would kill or materially bend this design, and what happens
then:

1. **Parse latency fails the keystroke budget.** Measured at v0.1 (no
   parse-latency numbers exist in the repo; the benchmarks measured
   rendering). If parsing a representative component through `citry_core`
   from Python exceeds ~50ms p95, keystroke-cadence diagnostics need
   debouncing tuned; if a debounced ~300ms experience still lags on real
   projects, the Python-resident premise is wrong and the Rust pivot
   (section 10) is pulled forward.
2. **The PyCharm attach spike fails on both routes.** Then PyCharm users
   get value only for `template_file` projects, the published coverage
   matrix is corrected before v0.1 ships, and the native-plugin question
   reopens much earlier than planned.
3. **Interpreter discovery dominates.** If, despite the environments API,
   the `[tool.citry]` pointer, and first-class status reporting,
   environment resolution is still the top issue category after v1.0, the
   design's core convenience (living in the user's venv) is a liability
   and the static-first Rust server wins; pivot.
4. **Fail-fast UX rejection.** If dogfooding shows that
   one-squiggle-at-a-time plus last-good-tree makes the server feel broken
   while typing (not merely modest), error tolerance becomes a
   prerequisite: the tree-sitter grammar jumps the queue, behind its
   injection-spike gate.
5. **Adoption evidence is absent at the pause review.** Section 5's
   review; the correct move is to hold at v0, with the recorded tension
   weighed by the maintainer.
6. **Typing is the adoption driver.** If user evidence (issues,
   interviews, public comparisons) shows teams choose or reject citry on
   typed `{{ ... }}` intelligence, deferring type-aware features is the
   wrong bet and the shadow-file design deserves the next investment,
   sequenced behind the Events typing work it needs anyway.
7. **pygls stalls.** Currently healthy (v2.1.1, 2026-03-25). A stall is
   survivable (the LSP surface used is small) but advances the pivot
   timeline.

---

## 13. Open questions for the maintainer

1. **The pause-review evidence bar.** What counts as adoption evidence for
   citry at its current stage (extension installs? issue traffic? PyPI
   downloads? direct user asks?), and who weighs it against judge 2's
   counterpoint that the gated features generate the evidence.
2. **Install posture for the server.** Is `citry[lsp]` (server in the
   project venv, registry mode by default, dependency-tree cost) the right
   default, or should docs lead with `uvx citry-lsp` (isolated, static
   mode) and treat registry mode as opt-in? This decides the top support
   burden's shape.
3. **Home for editor glue.** This doc proposes a new top-level
   `editors/` directory (`editors/vscode/`); the alternative is
   `packages/editors/…` to keep everything under `packages/`. Naming is
   cheap now and annoying to move later.
4. **Confirm D5** (source-map slot recorded, not implemented) or direct
   that the optional side-table land together with the v1.0
   structured-diagnostics pass despite the extra contract review.
5. **What is the static-analysis record and join contract?** The runtime
   catalog is versioned from day one. Static fallback still needs its own
   partially known record, source-root discovery, join key, ambiguity rules,
   and exact CLI behavior after an application import failure.
6. **PyCharm launch messaging.** Given the django-components audience
   skews PyCharm, is "diagnostics and completion via LSP4IJ, no inline
   color yet" acceptable at v1 launch, or does that gap re-rank the thin
   JetBrains plugin (or even the PSI plugin) ahead of parts of v1?
7. **Name claims and identifiers.** Confirm `citry-lsp` (PyPI package and
   console script), the `citry` extension id, and the v0.0 claim list
   (Marketplace, Open VSX, Package Control, crates.io) before anything is
   published under those names.

---

## Sources

Repo sources are cited inline as `file:line`; the load-bearing ones were
spot-verified against the tree for this synthesis on 2026-07-07:
`crates/citry_template_parser/src/{parser_context.rs,ast.rs,parser.rs}`,
`crates/citry_template_parser/Cargo.toml`,
`crates/citry_core_py/src/template_parser.rs`,
`packages/py/citry/pyproject.toml`, `packages/py/citry/citry/component.py`,
`packages/py/citry/citry/component_registry.py`,
`packages/py/pygments_citry/`, `docs/design/source_languages.md`,
`docs/design/extensions_roadmap.md`, `docs/design/template_grammar.md`, and GitHub
issues [#22](https://github.com/citry-dev/citry/issues/22),
[#23](https://github.com/citry-dev/citry/issues/23),
[#24](https://github.com/citry-dev/citry/issues/24),
[#26](https://github.com/citry-dev/citry/issues/26),
[#27](https://github.com/citry-dev/citry/issues/27).

The research corpus (all in [`ide_research/`](ide_research/README.md), all
dated 2026-07-07, with per-report source URLs and access dates in each
file's Sources section):
[`recon-citry-tooling-surface.md`](ide_research/recon-citry-tooling-surface.md),
[`recon-vue-tooling.md`](ide_research/recon-vue-tooling.md),
[`recon-python-template-tooling.md`](ide_research/recon-python-template-tooling.md),
[`recon-lsp-architectures.md`](ide_research/recon-lsp-architectures.md),
[`recon-framework-tooling-field.md`](ide_research/recon-framework-tooling-field.md),
[`design-A-ship-first.md`](ide_research/design-A-ship-first.md),
[`design-B-platform-first.md`](ide_research/design-B-platform-first.md),
[`design-C-ecosystem-first.md`](ide_research/design-C-ecosystem-first.md),
[`judge-1-maintainer-cost.md`](ide_research/judge-1-maintainer-cost.md),
[`judge-2-user-experience.md`](ide_research/judge-2-user-experience.md).
