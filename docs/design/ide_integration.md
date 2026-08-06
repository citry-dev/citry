# Design: IDE integration (editor tooling for citry)

**Status (2026-08-05): refreshed after maintainer review and accepted for
implementation.** Steps 1 through 9 at the end of this document are complete.
The portable syntax corpus drives the aligned Pygments lexers and declarative
VS Code highlighting, `citry check` provides parser-grade batch validation
with an explicitly bounded static fallback, and the companion language server
plus VS Code client provide the implemented editor intelligence. The VS Code
extension and `citry-lsp` 0.1.0 remain release-prepared rather than published
until they can be cut from a clean release commit. `pygments-citry` 0.1.1 is
published. The original design is the
synthesis of a research and design-panel process: five recon reports,
three competing design drafts, and two adversarial judge verdicts, all in
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
with [#22](https://github.com/citry-dev/citry/issues/22) (formatter), now
specified in [`template_formatter.md`](template_formatter.md),
the implemented [#26](https://github.com/citry-dev/citry/issues/26)
(component introspection), and
[#27](https://github.com/citry-dev/citry/issues/27)
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
set citry's parser accepts (allowed and required attributes and slots, plus
slot-data fields, per tag), defined in
`crates/citry_template_parser/src/parser_context.rs:31-101`
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
citations. Repo facts were refreshed against the tree on 2026-07-30; external
research remains the dated 2026-07-07 corpus unless stated otherwise.

### 1.1 In this repo (verified against source)

**The parser already provides the core of a language server for valid
templates.** The AST exposes exact UTF-8 byte positions through tokens and
node start/end tokens (`Token`: start/end index, line/col,
`crates/citry_template_parser/src/ast.rs:23-35`); used and
introduced variables are tracked per scope as tokens with positions, kept on
the node specifically for def/use linking (`ast.rs:641-740`;
[`template_grammar.md`](template_grammar.md) records the intent); slots are collected with
required-ness; and `TagRules` (`parser_context.rs:36-101`, a `#[pyclass]`)
lets a caller feed per-tag validation into `parse_template`, which is exactly
the hook component-aware diagnostics need: derive rules from each
component's `Kwargs` / `Slots` and the parser itself reports unknown or
missing attributes and slot violations for every component in the rule map.
A tag with no entry in the map is allowed through unvalidated (the rule
lookup falls through to allow-anything, `parser.rs:2595-2598`; same shape
for slots, `parser.rs:2979-2989`), so unknown-component detection is a
small tool-side check against the registry, not a parser feature
(section 3.2). Full sweep:
[`ide_research/recon-citry-tooling-surface.md`](ide_research/recon-citry-tooling-surface.md).

**The gaps are all about invalid or changing input.** The Pest parser is
fail-fast: one error, no partial AST (`parser.rs:141-153`). Parser context now
rebases a Pest grammar failure to its actual root-source position through
`ParserContext::error_from_pest`.
Errors still flatten to exception strings at the PyO3 boundary
(`crates/citry_core_py/src/template_parser.rs:33-38`). `HtmlAttr.kind` has no
Python getter (`ast.rs:374`). The parser crate depends on pyo3
unconditionally (`crates/citry_template_parser/Cargo.toml:12`), which blocks
standalone-binary and wasm reuse until feature-gated. The recon distills
these into a seven-item engine punch list; this design consumes two of them
now (section 3.5) and sequences the rest (sections 3.5 and 10).

**Templates live primarily inside Python files.** A component's template,
JS, and CSS are class attributes, inline multiline strings or `*_file` paths
(`packages/py/citry/citry/component.py:576-612`), and house style mandates
the inline form. So the defining constraint versus Vue or Svelte is that an
editor tool must first locate embedded regions in a `.py` file the Python
tooling already owns.

**Existing assets.** `pygments-citry` 0.1.1 is published on PyPI
(`packages/py/pygments_citry/`): two Pygments lexers
whose embedded-region detection is useful highlighting prior art and whose
behavior is updated through normal package releases. The `citry` console script
exists
(`packages/py/citry/pyproject.toml:51-52`), and `citry inspect --json` already
emits the versioned runtime catalog. The catalog provides registered names,
schemas, asset declarations, and source paths without exposing source bodies.
The live component registry remains the completeness boundary for registry
mode (`packages/py/citry/citry/component_registry.py`).

**Standing decisions this design does not reopen.**
[`source_languages.md`](source_languages.md) decided (sections 2, 4.3-4.5,
and 6.1): no highlight-only marker stopgaps (no typed aliases, no
third-party fork adoption, no `# language=` convention shipped as the
official story); the `*_lang` declaration attributes; a curated
rich-editing set; and a staged build path (extension skeleton, then
grammar, then server) where each layer ships on its own. [`extensions_roadmap.md`](extensions_roadmap.md) files the
LSP, formatter, and highlighting as standalone tooling on the Rust parser,
not extensions. The implemented CLI locates an explicit `Citry` instance with
`--app module:attribute`. A `[tool.citry]` table or `CITRY_APP` variable remains
a later ergonomics decision, not a current discovery contract.

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
   `css` strings get real highlighting in VS Code with zero configuration and
   zero binaries. Standalone template files get the same grammar through an
   explicit file association or a path learned from the project.
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

The formatter (#22) is outside this design and is now governed by
[`template_formatter.md`](template_formatter.md). Type-aware template
expressions were originally deferred, but direct user testing fired their
reopening condition on 2026-08-06 and moved them into the accepted order in
section 14. The remaining deliberate deferrals with reopening triggers in
section 10 are a Rust language server; a tree-sitter grammar; error-tolerant or
multi-error parsing in the engine; a JetBrains-native (PSI) plugin; web-types
emission; wasm builds; semantic tokens; and embedded CSS/JS language services
in the server (delegation to existing tools is documented instead, e.g. pointing
`tailwindCSS.includeLanguages` at citry template regions).

---

## 3. The chosen architecture

The plan contains five editor-tooling artifacts, of which the checker and
server reuse the shipped runtime catalog, plus two small engine changes. No new
binaries are distributed in the committed scope.

```
packages/py/pygments_citry/        0.1.1 published                     (Python)
packages/editors/syntax-fixtures/  exists; portable conformance data  (JSON)
packages/editors/vscode/           0.0.1 release-prepared              (JSON at v0; TypeScript with LSP)
packages/py/citry/                 existing `citry inspect`;          (Python, reuses citry_core)
                                     new `citry check`
package home decided before v1     new: pygls server, `citry-lsp`     (Python, reuses citry_core + citry)
crates/citry_template_parser/ +    two small additive changes         (Rust; Mechanism 2 + 4
crates/citry_core_py/                (structured diagnostics, kind)     when implemented)
```

### 3.1 The VS Code extension (`packages/editors/vscode/`)

One extension, named `citry`, that owns all three layers over time (the
staged path `source_languages.md` section 4.5 records). At v0 it contains no
server client, only:

- A **language contribution** `citry-html` for standalone template files
  (`{# #}` comment config and bracket pairs). Citry accepts arbitrary
  `template_file` names, so the extension must not claim every `.html` file.
  Projects opt into file globs, or a later registry-aware client associates
  paths the catalog identifies.
- A **TextMate grammar** for citry-HTML: HTML base, the built-in `<c-*>`
  tags and user components scoped distinctly, `{{ ... }}` bodies handed to
  Python scopes, `{# ... #}` as comments, and `<script>` / `<style>` bodies
  handed to JS / CSS. Its fixtures cover the current authored channels:
  `c-*` expression and nested-template attributes, `$c-props` client
  expressions, `c-$c-props` server expressions, `#c-key`, `#c-ignore`, Events
  `@c-*` and `:c-*` bindings, Alpine-style attributes, slot-data
  destructuring, raw blocks, comments, and malformed input.
- An **injection grammar** into `source.python` that matches the component
  string attributes (`template`, `js`, `css` followed by `= """`), marks
  the bodies with `meta.embedded` scopes, and maps them through
  `embeddedLanguages` so bracket matching and comment toggling behave.
  Detection keys on the **exact attribute names**, not on annotation text;
  textual annotation matching is precisely the brittleness the
  `python-inline-source` lineage and Tailwind's `classRegex` never escaped.
  TextMate cannot prove that the surrounding class inherits from `Component`,
  so v0 treats exact `template`, `js`, and `css` assignments as best-effort
  highlighting and may color an unrelated class attribute with one of those
  names. Parser-backed region discovery replaces that approximation with the
  language-server rung.

Known and accepted limitation: a TextMate grammar cannot count braces, so a
brace-heavy expression like `{{ {'a': {}} }}` can mis-detect the expression
boundary (`source_languages.md` documents the case). The grammar gets
recursive brace-and-string sub-rules that push this to rare inputs; the
remainder is documented best-effort coloring and will arrive as low-grade
issue traffic indefinitely (judge 2 named this cost; it is accepted
knowingly, with the tree-sitter grammar as the named upgrade path).

The desktop extension now adds a request-forwarding layer over those scopes.
For exact `template`, `js`, and `css` triple-string assignments, it builds a
same-length virtual HTML, JavaScript, or CSS document by retaining embedded
text and line breaks while replacing other Python text with spaces. It then
asks VS Code's installed language providers for completion, hover, and
definitions. `citry-html` documents forward directly to the HTML provider.
This client behavior does not require an app or server. A missing or failing
provider contributes no result. Diagnostics are not forwarded because VS Code
does not expose them as a provider request. Formatting is implemented through
the parser-backed formatter and the VS Code client's document/cursor commands;
[`template_formatter.md`](template_formatter.md) owns that cross-surface
contract, including how embedded templates coexist with the host document's
selected formatter.

One HTML-delegation gap remains in the current epic. On a native element,
Citry's dynamic-attribute spelling should retain the editor intelligence of the
underlying HTML attribute: hovering `c-class` in
`<form c-class="classes">` should produce the same native `class` description
and MDN link as hovering `class` in `<form class="classes">`. The VS Code
client can provide this without teaching the LSP an HTML catalog: project a
recognized native-element `c-<attribute>` name to `<attribute>` in the virtual
HTML document, ask the installed HTML provider at the corresponding position,
then map returned ranges back to the complete Citry attribute name. The mapping
must be parser/context aware: it applies only to dynamic native HTML attributes,
not Citry control directives, component inputs, or arbitrary `c-*` names. The
first acceptance case is hover (including the provider's documentation link),
with completion or other forwarded requests added only where their range and
edit mappings are equally exact. Provider absence remains a silent no-result.

Citry currently has 15 built-in tags from two authoritative sources. The Rust
parser owns eight structural names (`if`, `elif`, `else`, `for`, `empty`,
`raw`, `fill`, and `slot`); the Python registry owns seven built-in component
names (`provide`, `cache`, `component`, `element`, `error-fallback`, `js`, and
`css`). The shared corpus at
`packages/editors/syntax-fixtures/template.json` exercises those tags and the
attribute channels above through Pygments and TextMate. The check gate verifies
that the authoritative union remains represented in the corpus. It does not
pretend that either lexer is a second component registry or require a generic
highlighter to enumerate every user-facing tag internally.

### 3.2 The batch checker (`citry check`)

The implemented subcommand on the existing `citry` console script discovers
authored template sources, parses them with the real parser, and prints
diagnostics with the parser's annotated snippets. It has no positional path,
configuration-file, environment-variable, JSON, or fix surface in this first
rung. Its one mode flag is `--static`. Two discovery modes will be shared with
the server:

- **Registry mode**: import the project's `Citry` instance via the
  same `module:attribute` app spec accepted by the CLI's current `--app`
  option, derive `TagRules` from each registered component's `Kwargs`, `Slots`,
  and slot-data fields, and pass them to `parse_template`, so unknown or
  missing attributes and slot violations on registered components are
  diagnosed by the parser itself. A first editor setting or initialization
  option carries the app spec; an invalid spec, import failure, wrong object
  type, or discovery failure is reported in tooling status and degrades to
  syntax-only analysis. No new parser machinery is needed for the rule checks.
  The parser lets a tag with no rules pass unvalidated, so
  unknown-component detection is one extra tool-side check, shared with
  the server: compare the parsed component tag names against the registry
  and report the tags it does not know. Per decision D9 (section 11),
  that check fires in registry mode only. The v0 checker walks ordinary
  retained template bodies. Unknown tags inside template-valued attributes
  remain suppressed until step 4 exposes `HtmlAttr.kind`, because reparsing
  every `c-*` value would mistake expression strings for template source.
- **Static syntax mode**: `citry check --static` selects this limited mode
  explicitly. It is also the automatic fallback after an explicitly selected
  app fails to import or complete discovery. It conservatively locates definite
  literal `template` assignments and parses them without `TagRules`. Python AST
  is one source of regions for a valid file, not a complete or error-tolerant
  project model. This mode makes no registry-completeness claim, emits no
  unknown-component diagnostic, and does not serialize guessed records as
  `ComponentInfo`. Rich static component knowledge waits for the separate
  partially known record and join contract.

This is the `svelte-check` / `vue-tsc` pattern: the CLI twin ships before
the live server and shares its engine. It works in CI and pre-commit, in
every editor, with no editor integration at all.

The command exits 0 after a clean explicitly selected mode and 1 for source or
template findings. Bare `citry check` and combining `--app` with `--static`
exit 2 without importing project code or scanning source. An explicitly
selected app that fails to import or initialize also exits 2 after static
syntax checking finishes, with no partial registry names or rules retained.
Existing engine-backed commands remain fail-fast.

The first checker validates authored base Citry syntax. An extension may
transform source through `on_template_loaded`; Events already validates and
rewrites literal `@c-*` and `:c-*` bindings before the Rust parser runs. The
checker must not place a diagnostic from transformed text onto authored text
without a source mapping. Until a tooling analysis callback or mapping
contract exists, it reports extension-transform validation as unavailable and
continues with the authored base syntax it can confidently identify.

### 3.3 The shipped registry dump (`citry inspect --json`)

The implemented command emits the versioned runtime `ComponentCatalog` after
successfully importing the selected `Citry` instance. It uses the API defaults:
built-ins excluded, assets unresolved, default values omitted, and no extension
inspector invoked. It is independently useful to scripts, CI, and other
consumers of the component-introspection API (#26, including docs tooling and
Storybook-style galleries).

The command is deliberately runtime-only. It has no static scan after import or
discovery failure. The static syntax fallback described elsewhere uses a
separate tooling record, not the runtime catalog schema. Before any combined
output is proposed, a later design must define that record, source-root
discovery, its runtime join key, ambiguity handling, and failure behavior.
Static absence never proves that a component is unknown.

### 3.4 The thin language server (`citry-lsp` companion package)

A pygls server, started through a `citry-lsp` console script and distributed as
the pure-Python companion package in `packages/py/citry_lsp/`. The companion
boundary was selected at step 5 so pygls does not enter Citry's runtime
dependency tree and the server owns its protocol version, release, and
changelog. Install it in the project environment for registry mode; an
isolated invocation remains explicitly syntax-only. "Thin" is a design
commitment:

- **It answers only citry questions.** Diagnostics for template regions,
  completion and hover from the component registry and the parsed AST,
  go-to-definition for lexical loop/fill locals and catalog-backed components
  and inputs, and document symbols. Exact component-input fields use additive
  runtime provenance plus a conservative Python AST join; other schema roles
  consume that same join only when their feature is implemented.
  It never analyzes Python, never embeds a CSS or JS analyzer, never
  mirrors the user's project. Pyright / Pylance own the `.py` file; the
  citry server is a second, coexisting server registered for `python`
  documents plus the `citry-html` file type (the proven Ruff / Tailwind
  pattern).
- **Region discovery is conservative and recoverable.** On valid Python, the
  server combines the standard `ast` and source tokens to find literal class
  attributes and their authored string bodies. AST alone is insufficient:
  parsing fails on incomplete Python, string values can be escaped or
  concatenated, and its columns are UTF-8 byte offsets. On broken Python, a
  small lexical scanner recovers only regions it can identify unambiguously;
  the last-good region map supplies context without allowing stale squiggles
  to move onto new text. One coordinate adapter converts Python and parser byte
  ranges through the authored source to LSP UTF-16 positions, with non-ASCII,
  escapes, prefixes, quote styles, concatenation, and incomplete files covered
  by tests.
- **Component knowledge has two tiers**, the same two modes as
  `citry check`, sharing that code. Interpreter discovery (which Python
  owns this workspace) is answered in VS Code by the
  `@vscode/python-extension` environments API and elsewhere by an explicit
  setting; the current `module:attribute` app spec resolves the app instance.
  The environments API is treated as an adapter, with an explicit executable
  setting retained because the extension API can change. This is
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
  diagnostics). The implemented component and contract completion and hover
  can answer from the copied catalog plus a small hand-rolled
  **cursor-context scanner** over
  the current text ("am I inside a tag name? an attribute? a fill?"),
  because the moment a user wants tag completion (`<c-Ca`) is exactly when
  the buffer does not parse. The server retains last-good trees but does not
  project their stale token ranges onto edited source; lexical navigation and
  document symbols wait for a current valid parse. This removes the originally
  budgeted position-adjustment risk without weakening completion or catalog
  hover. Judge 1 identified this as design A's weakest unbudgeted spot; the v1
  implementation resolves it by keeping current-text context and stale-range
  features separate.

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

Implemented 2026-07-30 and extended within formatter protocol v1 on 2026-08-04.
The server supports the Citry 0.3.x and component-catalog v1 contracts and
rejects an incompatible client protocol during initialize. A one-shot worker
subprocess imports the configured app, captures Python and file-descriptor
output, and returns only portable `TemplateAnalysis` and `ComponentCatalog`
data. Startup is bounded at
five seconds; `SystemExit`, invalid specs, hangs, crashes, and malformed worker
responses all produce one reported syntax-only degradation. File changes and
the explicit reload request replace the complete copied project generation.
No project module enters the LSP stdio process.

#### 3.4.1 Capability and degradation contract

Tooling reports its active mode so partial facts are never presented as
complete. These are the minimum guarantees for `citry check` and the server:

| Source and project state | Available behavior | Deliberately suppressed or reported limitation |
|---|---|---|
| Definite template region; configured app imports and discovery completes | Base parser diagnostics, registered component and input checks, schema-free Citry structural/directive completion, lexical loop/fill completion and hover, registry component/attribute/slot completion, catalog hover, exact component/input definitions when source is provable, and unknown-component diagnostics | Extension-transformed diagnostics unless that extension supplies an authored-source mapping |
| Definite template region; no app configured | `citry check --static` and the server provide base parser diagnostics in their explicit syntax-only modes; the server still offers Citry structural/directive completion and parser-proven lexical loop/fill completion, hover, and navigation; the VS Code client independently forwards HTML, CSS, and JavaScript completion, hover, and definitions | Registry component completion and hover, interface checks, unknown-component diagnostics, and delegated web-language diagnostics |
| Configured app spec is invalid, imports the wrong object, or import/discovery fails | The same syntax-only analysis as an explicit `citry check --static` run | Registry-derived features; one actionable project-status error carries the underlying failure |
| Python file parses and contains a definite literal component asset | AST-decoded source, base syntax analysis, and exact authored host ranges through the shipped byte-to-UTF-16 source map | Computed, inherited, file-backed, concatenated, or otherwise nonliteral inline asset values unless registry-backed source discovery identifies a separate file |
| Python file is incomplete | `citry check` reports that the source cannot be analyzed; the server uses lexically proven current regions plus last-good semantic data and recovers active bindings only from complete current-text start tags | A last-good diagnostic whose range cannot be proven against current text; ambiguous regions are skipped |
| Static scan sees a possible component but no complete runtime registry exists | Syntax-only facts with explicit partial confidence | Any conclusion that the component set is complete, especially unknown-component errors |
| Template uses extension rewrites | Authored base-syntax analysis | Transformed-source diagnostics unless the extension supplies a mapping; status names the unsupported capability |
| Template declares an unsupported non-`None` `template_lang` value | The source is skipped with an explicit finding | Base-language guessing and alternate dialect semantics |
| Standalone template path is explicitly associated or learned from a loaded project | `citry-html` highlighting; checker/server analysis when registry ownership is known | Automatic ownership of arbitrary `.html` files and a positional path surface in the v0 checker |

Wrong setting values do not fall back to a different app. Unsupported catalog,
extension-introspection, or server protocol versions produce one version-skew
status and disable only the features that depend on that data.

### 3.5 Engine-side prerequisites (small, additive, one pass)

From the punch list in
[`ide_research/recon-citry-tooling-surface.md`](ide_research/recon-citry-tooling-surface.md)
section 6, the committed scope needs exactly one plan-mode pass over the
PyO3 surface, containing:

1. **Structured diagnostics across the PyO3 boundary** (punch item 2): an
   error type carrying span indices and line/col plus a stable code alongside
   the existing exception text
   (`citry_core_py/src/template_parser.rs:33-38`). The CLI can live with
   rendered strings; an LSP mapping squiggles, and `citry check
   --format json` for CI annotations, should not regex positions out of
   prose. `ParserContext::error_from_pest` already preserves the actual
   root-source position for a top-level grammar failure, so this pass exposes
   that position rather than repairing it again.
2. **Expose `HtmlAttr.kind` to Python** (punch item 1): one `#[pyo3(get)]`
   plus a stub line (`ast.rs:374`), so the server does not re-derive attribute
   classification. The stale `Template.comments` docstring at `ast.rs:944-946`
   gets corrected in the same touch (punch item 7).

Implemented 2026-07-30. `ParseDiagnostic` is attached to the existing Python
exception and reached through the typed `parse_diagnostic()` helper;
`HtmlAttr.kind` is readable and comparable; `Citry.template_analysis()`
publishes a complete engine-owned snapshot; and `PythonTemplateSourceMap`
maps complete or conservatively recovered Python string regions to LSP
coordinates.

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

- **Planned pre-publication semantics route: an LSP4IJ user-defined server
  template.** LSP4IJ
  supports declaring a language server with no plugin code (command plus
  file mappings), and definitions can be exported and imported as
  templates. Step 14 tests this route and, if the attach spike succeeds,
  publishes an importable JSON template with the editor documentation. The
  JetBrains
  **native** LSP API is not a documented route here: it is a plugin API (an
  `LspServerDescriptor` lives in plugin code), so "config docs" cannot
  reach it; design A's contrary claim was judged factually wrong and is
  corrected in this synthesis. A thin official plugin (descriptor plus
  bundled server plus TextMate bundle) on the JetBrains Marketplace is a
  named later rung, once the server is stable.
- **The attach question is open and gets the language-server rung's first
  spike.**
  Whether any second LSP client (LSP4IJ or the native API) surfaces
  features on `.py` documents PyCharm's Python plugin already owns is
  unverified across the entire corpus, and both judges flagged it. The
  spike (days, testing both routes on `.py` documents) remains step 21 before
  PyCharm support is promised anywhere user-facing. It does not block the
  already implemented editor-independent or VS Code rungs.
- **No inline coloring in PyCharm under this plan, and the docs say so.**
  JetBrains' TextMate bundle mechanism only applies to file types no native
  plugin owns; `.py` belongs to PyCharm's Python plugin, so no bundle can
  color inside Python strings. LSP diagnostics and completion are provisional
  pending the spike, and inline templates have no Citry coloring
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
The JetBrains semantics cells are provisional on the pre-server attach spike.

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

This table preserves the research estimate and marks work that landed while
Citry itself was being completed. Section 14 is the accepted implementation
sequence and controls ordering from 2026-07-30 onward.

### v0: visible value with no server (~3.5 to 5 weeks)

| Milestone | Deliverable | Effort | What it buys |
|---|---|---|---|
| v0.0 | `pygments-citry` 0.1.0 published on 2026-07-27 | Done | ```` ```citry ```` fences render everywhere Pygments runs (docs site, Sphinx, PyPI READMEs; GitHub fences unaffected) |
| v0.1 | Shared syntax conformance corpus; current Pygments behavior; VS Code `citry-html` language + TextMate grammar + injection grammar into Python strings; **measure parse latency** on representative components and record the numbers | Highlighting implemented; Pygments 0.1.1 published; VS Code publication and latency measurement remain | Color where citry users live, inline and in explicitly associated files; shared evidence across the two highlighting implementations; the latency numbers that decide falsifier 1 before any server is committed |
| v0.2 | `citry check` (registry mode + conservative static syntax fallback, text output; versioned JSON added with v1.0) | Implemented 2026-07-30 | Parser-grade base validation in CI and pre-commit, with component-aware validation only when runtime completeness is known; the discovery and `TagRules`-derivation code the server reuses |
| v0.3 | `citry inspect --json` (implemented 2026-07-22) | Done | A scripting and CI usable runtime component inventory, independent of any editor |

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
| v1.0 | Engine pass and shared coordinate adapter; `citry-lsp` diagnostics for inline, explicit `citry-html`, and catalog-resolved file templates; VS Code client; `citry check --format json` | Implemented 2026-07-30 | Red squiggles from the real parser as you type, component-aware when the registry imports; first-in-family for a Python component framework |
| v1.1 | Component/input/slot/slot-data completion, catalog hover, schema-free structural/directive completion, lexical loop/fill completion and navigation, exact component-class and component-input navigation where provable, document symbols, conservative incomplete-region recovery, complete catalog retention, and VS Code web-language request forwarding | Implemented through 2026-08-05 | "My editor knows my components" even before app setup for parser-owned syntax, then adds registry contracts, exact authored fields, slot-data shapes, and ordinary HTML, CSS, and JavaScript assistance inside asset strings |
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
injection (PSI) plugin for inline coloring, and semantic tokens. Typed template
expressions have moved to the accepted implementation order after the
2026-08-06 user-testing evidence; they still require their named batch-first
design and source-mapping contract. The formatter has moved to the accepted
implementation plan in
[`template_formatter.md`](template_formatter.md).

---

## 6. Distribution and packaging

- **`pygments-citry`**: published on PyPI; subsequent syntax-alignment changes
  use its normal package-specific version, changelog, tag, and trusted-publish
  workflow. The package already registers the `pygments.lexers` entry points.
- **`citry check` / `citry inspect`**: ride the existing `citry` package
  and console script; nothing new to distribute.
- **`citry-lsp`**: a pure-Python console command with no platform matrix. Its
  implementation is the companion distribution in `packages/py/citry_lsp/`.
  A project-environment install can import the user's registry while keeping
  pygls out of applications that do not install editor tooling. The documented
  isolated `uvx --from citry-lsp citry-lsp` invocation provides syntax-only
  behavior because it cannot import the project app.
  The server declares its supported Citry, catalog, and protocol versions; the
  skew-refusal behavior in section 3.4 handles versions outside that range.
- **VS Code extension**: one **universal** vsix (it bundles no binaries),
  prepared locally at v0.0.1 and, when released, published to both the
  Microsoft Marketplace and Open VSX. Open VSX is not
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

This table records the implemented and proposed locations.

| Artifact | Location | Language | Status |
|---|---|---|---|
| Pygments lexers | `packages/py/pygments_citry/` | Python | aligned 0.1.1 package published |
| Shared syntax corpus | `packages/editors/syntax-fixtures/` | JSON | exists; consumed by each highlighter's tests |
| `citry inspect` and `citry check` subcommands | `packages/py/citry/` (CLI + the #26 introspection API) | Python | implemented, including `check --format json` schema v1 |
| Language server | `packages/py/citry_lsp/` | Python | v0.1.0 implemented and locally install-tested; not yet published |
| VS Code extension + grammars | `packages/editors/vscode/` | JSON + TypeScript | v0.1.0 client and universal VSIX implemented; not yet published |
| Structured diagnostics and `kind` getter | `crates/citry_template_parser/` + `crates/citry_core_py/` + `_rust.pyi` + Python wrapper | Rust + stubs | implemented 2026-07-30 through the required prior-art, plan, and cross-binding audit |
| Syntax corpus and authoritative-set validator | Highlighting tests plus `scripts/validators/` if cross-package validation needs it | Fixtures + Python | implemented with v0.1 highlighting |
| Editor setup docs, LSP4IJ template JSON, troubleshooting page | docs site (`docs_site/`) | Markdown/JSON | VS Code setup and troubleshooting implemented; long-tail editor snippets and LSP4IJ template remain v1.2 |

The engine changes touch two high-risk surfaces named in CLAUDE.md (the
`#[pyclass]` contract and the PyO3 glue), so each goes through the
prior-art header, plan mode, and the cross-binding audit (the five
`LangImpl` files are unaffected by these two changes, but the audit
enumerates that explicitly rather than assuming it).

---

## 8. Relationship to tracked issues and the bindings roadmap

- **#23 (LSP / linter): this document is the design for it.** It uses the
  implemented `module:attribute` app spec and refines the issue's
  variable-linking notes into lexical-local, schema-field, and component
  navigation capabilities; `citry check` and `citry-lsp` are the two
  deliverables that issue anticipated.
- **#24 (syntax highlighting): v0.0 + v0.1 deliver it** (Pygments publication,
  the TextMate and injection grammars). The tree-sitter
  grammar remains a v2 candidate, not part of #24's resolution.
- **#22 (formatter): the development vertical path is implemented.**
  [`template_formatter.md`](template_formatter.md) defines the staged
  Citry/HTML formatter, internal comment-association and whitespace passes,
  later embedded-language providers, `citry format`, LSP protocol, and VS Code
  integration. The Rust core, Python host rewrite, CLI, protocol v1 LSP routes,
  and VS Code formatting commands now exercise the opening-tag preview. The
  structural formatter remains the first public formatter release, and
  `citry check` does not grow `--fix`.
- **#26 (component introspection API): implemented, including `citry inspect
  --json`.** The command's runtime JSON is the versioned soft contract from
  [`component_introspection.md`](component_introspection.md), shared with other
  planned consumers such as docs tooling and component galleries. Effective
  fields now retain conservative per-field authoring provenance for exact
  editor joins. The separate partially known static-analysis record remains an
  IDE design task.
- **#27 (JS bindings via wasm): independent, and deliberately untouched.**
  This design needs no wasm and no pyo3 feature gate; the gate
  (`crates/citry_template_parser/Cargo.toml:12` and every `#[pyclass]`
  site) remains #27's prerequisite and doubles as the Rust-server pivot's
  prerequisite, so it is scheduled by whichever of those fires first. If
  the pivot fires, the same gating work serves both consumers; nothing in
  the committed scope preempts or blocks it.
- **Typed component interfaces now exist.** `Kwargs`, `Slots`,
  `TemplateData`, `JsData`, `CssData`, State, and Events metadata provide
  useful declared types. A shadow-file checker (the checker that type-checks a
  generated Python stand-in for the template, section 10) can consume those
  interfaces, but the transform, authored-source mapping, and demand case still
  require their own batch-first design.

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
- **The syntax-corpus tax**: Rust structural names and Python built-in
  component names are authoritative, while Pygments and TextMate keep behavior
  rules for the constructs they highlight. Shared fixtures and one
  authoritative-union check make drift visible without inventing another
  registry.
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

- **Full Python semantic checking beyond direct schema joins** (shadow Python
  for Pyright/mypy, svelte2tsx-style) was originally deferred, then reopened by
  direct user testing on 2026-08-06. The smaller `TemplateData` schema join in
  step 10 proved the value of declared root completion, hover, and definitions,
  while also exposing the boundary: the catalog's display-only type strings do
  not prove members, and components without a duplicated `TemplateData` class
  still receive no roots from their `template_data()` return. The accepted
  order now separates a conservative source-level returned-dict shape pass from
  the larger batch-first transform. Name resolution across arbitrary Python,
  call signatures, inferred member types, unions, narrowing, and semantic
  diagnostics still require that dedicated design and source-map maintenance
  line; they must not be approximated by parsing display strings or executing
  `template_data()` during discovery.
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
  likely a C scanner), another highlighting behavior implementation, and
  per-editor query files, serving editors whose users still get the LSP's
  substance here.
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
- **The formatter (#22)** is governed by the cross-surface implementation plan
  in [`template_formatter.md`](template_formatter.md). Its development
  vertical path now uses protocol v1 without changing the broader IDE roadmap.
  **Semantic tokens** remain
  an upgrade channel to revisit if the grammar's best-effort coloring
  demonstrably misleads in practice.
- **Implementing HTML, CSS, or JavaScript language services inside
  `citry-lsp`, and any takeover, fork, or patch of host tooling.** The VS Code
  client forwards supported requests to the providers already installed in
  the editor. Other clients may provide equivalent delegation. Citry keeps
  host-language analysis owned by those tools.

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
  rungs, and B's attach spike moved to the start of the language-server rung,
  before any user-facing PyCharm semantic-coverage promise (judge 2: "no draft
  should ship its coverage matrix before this answer exists"). Syntax-only
  artifacts do not depend on that result.
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
  when that design starts, its **first**
  change is an optional, additive side-table the compiler can emit
  (generated range back to template offset), designed so existing
  consumers are untouched. Recording the intention now is the cheap part
  of judge 2's point; deferring the contract change is judge 1's. If an
  intermediate compiler-contract change ever threatens to foreclose an
  additive side-table, that change must weigh this recorded requirement.
  Timing was contested the same way: judge 2 asked for the engine
  contract items as an early workstream running parallel to v0, and
  judge 1 attacked design B's engine-first ordering. The synthesis
  schedules the whole engine pass at v1.0, after the pause review, so
  holding at v0 spends zero engine work, per judge 1's economics;
  judge 2's early-parallel preference is noted and rejected for that
  reason.
- **D6: `citry inspect --json` is an independent artifact.** Grafted from
  design C (judge 1 graft 6), then implemented on 2026-07-22. It remains useful
  to scripts and CI with no editor anywhere. Section 14 starts from this
  completed foundation.
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
   the explicit app spec and first-class status reporting,
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
6. **Typing is the adoption driver. Fired 2026-08-06.** Direct editor testing
   identified inferred `template_data()` roots and Python member completion as
   the largest remaining authoring win. Deferring type-aware features is now
   the wrong bet, so the accepted order schedules a conservative returned-dict
   pass followed by the shadow-file design, using the typed schemas and Events
   metadata that now exist.
7. **pygls stalls.** Currently healthy (v2.1.1, 2026-03-25). A stall is
   survivable (the LSP surface used is small) but advances the pivot
   timeline.

---

## 13. Open questions for the maintainer

1. **The pause-review evidence bar.** What counts as adoption evidence for
   citry at its current stage (extension installs? issue traffic? PyPI
   downloads? direct user asks?), and who weighs it against judge 2's
   counterpoint that the gated features generate the evidence.
2. **What is the richer static-analysis record and join contract?** The runtime
   catalog is versioned from day one. Static component knowledge needs its own
   partially known record, source-root discovery, join key, ambiguity rules,
   and confidence rules before it can go beyond syntax-only fallback.
3. **PyCharm launch messaging.** Given the django-components audience
   skews PyCharm, is "diagnostics and completion via LSP4IJ, no inline
   color yet" acceptable at v1 launch, or does that gap re-rank the thin
   JetBrains plugin (or even the PSI plugin) ahead of parts of v1?
4. **Name claims and identifiers.** Confirm `citry-lsp` (PyPI package and
   console script), the `citry` extension id, and the target publisher accounts
   (Marketplace, Open VSX, Package Control, crates.io) immediately before each
   artifact is ready to publish.

---

## Sources

Repo sources are cited inline as `file:line`; the load-bearing current-state
claims were refreshed against the tree on 2026-08-05:
`crates/citry_template_parser/src/{parser_context.rs,ast.rs,parser.rs}`,
`crates/citry_template_parser/Cargo.toml`,
`crates/citry_core_py/src/template_parser.rs`,
`packages/py/citry/pyproject.toml`, `packages/py/citry/citry/component.py`,
`packages/py/citry/citry/component_registry.py`,
`packages/py/citry/citry/{__main__.py,commands/inspect.py,tag_rules.py}`,
`packages/py/citry/citry/ext/events/bindings.py`,
`packages/py/pygments_citry/`, `packages/editors/syntax-fixtures/`,
`docs/design/source_languages.md`,
`docs/design/component_introspection.md`, `docs/design/extensions_commands.md`,
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

---

## 14. Accepted implementation order (2026-07-30)

This sequence supersedes the dated ordering assumptions in the research
corpus. Each step ships a usable result and keeps the capability and
degradation contract in section 3.4.1.

1. **Refresh the design and issue contracts.** Bring this document and issues
   #23, #24, and #26 into line with the shipped catalog, CLI app selection,
   parser spans, current template syntax, and the registry/static confidence
   boundary.
2. **Ship the shared syntax and highlighting rung.** Establish one syntax
   conformance corpus, bring Pygments up to the current authored syntax,
   publish `pygments-citry`, then build the VS Code inline injection and
   `citry-html` TextMate grammar. The corpus covers valid, nested, malformed,
   and non-ASCII examples across both highlighters. Standalone file association
   is explicit or project-derived, never a blanket claim on `.html`.
3. **Add a conservative `citry check`.** Validate base syntax everywhere the
   tool can prove a template region. Require either explicit `--static` mode or
   an app spec so a clean result cannot hide which level of analysis ran. Add
   registered component checks only when the selected `--app`-shaped spec
   imports and discovery completes. On import failure, continue syntax-only,
   show the failure once in project status, and never infer an unknown component
   from static absence. Report extension transforms and alternate source
   languages as unsupported until they provide an authored-source analysis
   contract.
4. **Add the small engine and analysis contracts.** Implemented 2026-07-30.
   Preserve the existing
   Python exception classes and messages while exposing a stable diagnostic
   code and byte range. Add one tested UTF-8-byte to host-source to UTF-16
   coordinate adapter, expose `HtmlAttr.kind`, keep stubs in sync, and provide
   a supported analysis bridge that gives tooling a complete engine-owned
   snapshot. The existing root-source grammar-error position becomes the
   structured diagnostic range.
5. **Build diagnostics-first pygls support.** Implemented 2026-07-30. Reuse the
   checker engine for inline and associated file templates. The public
   `discover_python_templates()` contract is the shared conservative inline
   discovery path; the editor alone opts into narrow unfinished-literal
   recovery. Import trusted project code outside the LSP stdio process, with
   bounded startup and clear handling for stdout, `SystemExit`, hangs, reloads,
   and crashes. The client reports the selected interpreter, app spec, registry
   state, server protocol version, and active degradation mode.
6. **Add narrow editor intelligence.** Implemented 2026-07-30. Add component,
   attribute, and slot completion; catalog-backed hover; lexical loop/fill
   navigation; component navigation at the precision the catalog exposes; and
   document symbols. Root variables produced by arbitrary `template_data()`
   code are not presented as lexical def/use links.
7. **Complete the first editor-usability follow-up.** Implemented 2026-08-01.
   Offer both registered and valid class-name component spellings and rank
   them from the typed casing. Join `python_file` and `qualname` to an
   unambiguous Python AST class and otherwise retain file-start navigation.
   Surface the existing authoritative slot-data field sets in completion and
   hover, including known empty shapes. In VS Code, forward completion, hover,
   and definition requests from exact asset strings and `citry-html` documents
   to installed HTML, CSS, and JavaScript providers. Provider absence or
   failure contributes no result, and no app is required for this delegation.
8. **Add schema-free template quality of life.** Implemented 2026-08-05.
   Offer the parser-owned structural tags and host-specific Citry directive
   snippets even in syntax-only mode. Complete and hover parser-proven lexical
   names introduced by `c-for` and `c-fill`, including shorthand loops,
   destructuring, aliases, rest/fallback bindings, nested template values, and
   conservatively recovered incomplete expressions. These features never infer
   that an unregistered user component exists.
9. **Preserve the semantic inputs needed by later schema work.** Implemented
   2026-08-05. Keep the complete component-catalog v1 envelope, all five schema
   roles, all three assets, extensions, and shared asset ownership in the LSP
   instead of reducing them to the first editor feature set. Add conservative
   per-field declaration provenance to `FieldInfo`, including the distinct
   authored owners of C3-composed fields, and join it to exact annotated Python
   assignments for component-input and static fill-slot definitions. Local,
   generated, unreadable, invalid, and ambiguous declarations produce no field
   target. Open files use synchronized editor text and closed files use the
   current disk AST; v1 does not claim generation freshness without a source
   fingerprint. The unreleased catalog and client protocols remain version 1.
10. **Join `TemplateData` to template expressions.** Implemented 2026-08-06.
    For an AST-proven inline declaration or a registry-owned template file,
    intersect the `TemplateData` fields of every effective consumer of that
    physical template. Expose the identical common root fields in expression
    completion and join exact parser-reported free-root tokens to hover and
    annotated-field definitions. Structured asset owner module and qualified
    name provenance makes the physical join work even when the declaring base
    or library component is not itself registered. Lexical `c-for` and
    `c-fill` names remain authoritative in their scopes. Inherited child-only
    fields, conflicting schemas, absent or opaque schemas, unowned files, and
    recovered Python regions contribute no guessed roots. A member such as
    `user.name` can join `user`, but catalog v1 has no structured member graph
    with which to claim `name`, and root completion is withheld at member
    positions. This describes the engine join, not yet a reliable end-to-end
    completion experience: 2026-08-06 VS Code testing found that `CForm` can
    return all twelve declared roots when the engine is explicitly queried at
    a valid identifier, while the initial empty expression at the opening-quote
    trigger returns no items and subsequent client filtering exposes only a
    patchy subset. Step 13 owns empty and partial expression prefixes,
    completion-list lifecycle, exact filter/edit ranges, and applied-client
    tests. The runtime now materializes declared data-schema defaults and
    coercions by using the validated `TemplateData`/`JsData`/`CssData` instance
    as the normalized result, while retaining extras that the schema explicitly
    allows. In the current implementation, unresolved-root diagnostics remain
    disabled; step 17 replaces that temporary state with a Citry-owned rule
    whose default severity is warning:
    instance and per-render template globals, extension mutation, and arbitrary
    extra data keep the applicable root namespace open. No protocol or catalog
    version bump is needed before the first release.
11. **Preserve native HTML intelligence for dynamic attributes.** On native
    elements, project a recognized dynamic attribute such as `c-class` to its
    underlying `class` attribute when forwarding to the installed HTML
    provider. Hovering either spelling must return equivalent documentation,
    including the provider's MDN link, while any returned range maps back to
    the full Citry spelling. Do not rewrite Citry directives, component inputs,
    or unknown `c-*` names, and degrade to no result when no provider responds.
12. **Accept a `ComponentLibrary` as a registry target.** Allow the existing
    `module:attribute` setting to resolve either a `Citry` instance or a
    `ComponentLibrary`. For a library target, the isolated discovery worker
    creates `Citry(autodiscover=False)`, registers that manifest, and publishes
    the resulting built-in-plus-library analysis and catalog. Status and
    documentation must make the boundary explicit: this mode knows no host-app
    components, configuration, or extensions. If the library cannot install
    without host-provided extensions, discovery fails clearly and directs the
    author to expose a configured `Citry` wrapper instead. In particular,
    `"citry.app": "citry_ui:__citry_library__"` should work without a separate
    adapter module.
13. **Repair expression delivery, completion edits, structural snippets, and
    component matching.** Treat completion as an end-to-end LSP/client contract,
    not merely a list of server labels. Empty and partial Python expressions in
    `{{ ... }}`, every Python-valued attribute, loop clauses, and nested
    templates must offer every applicable declared root. The `CForm` acceptance
    case starts at an empty value, then checks one-letter and longer prefixes:
    `action`, `autocomplete`, `aria_busy`, and `attrs` all remain discoverable
    from `a`, and all twelve `TemplateData` fields participate in ordinary VS
    Code typing. Return an incomplete list where the server must be queried as
    the expression evolves, and provide exact expression filter/replacement
    ranges so client-side fuzzy matching behaves like Python and JavaScript
    completion. Every tag or attribute completion likewise replaces the token
    already typed, so selecting `c-for` after `<c-` produces one `<c-for`, never
    `<c-c-for>`. Start-tag completions for structural forms insert their primary
    required syntax and place the cursor in its value: for example
    `<c-for each="">`, `<c-if cond="">`, `<c-elif cond="">`, and
    `<c-fill name="">`; closing-tag completion remains a bare name. Registered
    components remain searchable by class, normalized, and alias spellings.
    Prefix-aware filtering and ranking must keep `c-CForm` visible for
    `<c-form` and rank it above `c-c-form` for `<c-cfo`, because the former is
    the closer separator/casing match. Tests exercise VS Code's requested and
    applied results at the actual trigger positions, not only engine output or
    `sortText` values. The expression-delivery slice was implemented on
    2026-08-06: empty and partial expression requests now return incomplete
    lists with all applicable lexical and `TemplateData` roots, explicit
    `filterText`, and source-mapped UTF-16 insert/replace ranges. Clients that
    do not advertise LSP insert/replace support receive the same full-token
    replacement as a standard `TextEdit`. The structural-tag delivery slice
    was implemented on 2026-08-06: structural and registered component
    items replace the complete partial tag-name token using one atomic,
    source-mapped range and keep the list live as the prefix changes.
    Structural start tags insert their primary syntax without duplicating an
    authored attribute or closing delimiter, while closing tags insert only
    the name. Snippet and insert/replace capability fallbacks preserve usable
    plain text for older clients. The attribute-name and component-matching
    slice was implemented on 2026-08-06. Directive, structural-attribute, and
    component-input completion now replaces the complete current name through
    an exact source-mapped edit, preserves an existing assignment and value,
    ignores lookalike names and quotes inside values and comments, and keeps
    the list incomplete while the name evolves. Registered components are
    filtered and ranked on the server across class, normalized, and alias
    surfaces, including separator-insensitive and conventional leading-`C`
    matches. Query-compatible `filterText` keeps the semantic candidate visible
    to VS Code: `<c-c` prefers `c-c-form`, `<c-C` prefers `c-CForm`, `<c-form`
    retains `c-CForm`, `<c-cfo` ranks `c-CForm` first, and an exact `<c-cform`
    prefers that alias. Attribute-value completions such as fill slot names and
    exposed slot-data fields remain separate value-oriented completion paths.
14. **Add first-party Citry syntax hover.** Provide concise, syntax-only hover
    documentation and canonical `https://citry.dev/` links for every
    parser-owned structural tag, directive, and structural attribute. The
    acceptance corpus includes `c-bind`, `<c-slot>`, `<c-slot required>`, and
    `<c-fill>`. Keep the metadata in one exhaustive table checked against the
    authoritative parser-owned names; registry state and an installed HTML
    provider are not prerequisites.
15. **Infer conservative roots from `template_data()` source.** Without
    executing component methods, inspect the exact owning Python AST and expose
    statically proven string keys from returned dict shapes in the same
    interpolation and expression-attribute contexts as declared
    `TemplateData`. A key can complete and navigate to its literal definition
    even when its value type is unknown; add a type only when Python analysis
    proves one. Track conditional returns, unpacking, aliases, inheritance, and
    shared templates with explicit confidence/completeness rather than treating
    a partial shape as closed. Declared `TemplateData` remains authoritative
    where present. This is the narrow path that makes keys such as `root_class`
    and `root_attrs` useful without forcing authors to duplicate a large return
    dict solely for editor support.
16. **Design and implement type-aware Python template expressions.** Start from
    an editor-independent batch/shadow-Python representation with authored
    source mappings, then reuse it for completion, hover, navigation, and
    diagnostics inside `{{ ... }}`, every Python-valued attribute, loop clauses,
    and nested templates. Cover member and call completion, unions, Optional
    values, narrowing, aliases, and safe-expression restrictions; for example,
    `method.lower()` is offered only where the effective type permits that
    member. Consume structured types or a real Python analyzer rather than
    parsing catalog display strings into an ad hoc type system.
17. **Configure template linting on `Citry`, with unknown roots warning by
    default.** Add one extensible lint-settings surface to the `Citry` instance
    and carry it through portable analysis so `citry check` and the LSP apply
    the same policy; VS Code does not invent a parallel preference. The unknown
    template-variable rule accepts `ignore`, `warning`, or `error` and defaults
    to `warning`. Diagnose only free root names after accounting for lexical
    bindings, declared or inferred component data, and every known global;
    members remain the type checker's concern. Runtime `Citry.template_globals`
    are known automatically, while lint settings independently declare
    additional global names and optional types/descriptions for per-render,
    framework, or extension-provided values without injecting runtime data.
    Extensions may contribute the same portable metadata. Registry mode emits
    the configured diagnostic even when some dynamic source remains open—the
    default warning is deliberately advisory—and authors can declare the name,
    downgrade/ignore the rule, or expose a more complete schema. Syntax-only
    analysis, which cannot associate a component namespace, does not guess.
    Define rule codes, inheritance/override behavior, serialization, and
    component-level escape hatches before implementation.
18. **Join `CssData` to component CSS.** Recognize Citry's generated CSS
    variable spelling, provide field hover and exact definition links back to
    `Component.CssData`, and stay conservative when a stylesheet has multiple
    possible component owners. Global CSS custom-property visibility means
    this is provenance and authoring assistance, not a claim of CSS isolation.
19. **Specify and implement automatic `JsData` scope seeding.** Give each
    component instance an independent client-side value graph, seed its Alpine
    scope from serialized `js_data` immediately before `$component`, and keep
    `$component` as the hook for additional or overridden scope values. Define
    duplicate-name precedence, supported wire types, hydration timing, and
    Alpine activation before changing runtime behavior.
20. **Add Alpine/browser-expression intelligence from that contract.** Parse
    expression and statement contexts for `x-*`, `@*`, and `:*`; offer
    `JsData`-derived names and types; and navigate those names to exact Python
    fields. Alpine magics, Events/State metadata, incoming props, and names
    added imperatively by `$component` remain separate proven sources rather
    than being guessed from JavaScript text.
21. **Complete the PyCharm attach spike.** Verify inline Python-string and
    standalone-template behavior through LSP4IJ, publish an importable template,
    and document the tested capability matrix before release.
22. **Grow the remaining long tail only from evidence.** Richer whole-program
    indexing beyond the scheduled expression work, extension-aware
    authored-source mappings, alternate template dialects,
    tolerant Citry parsing, and native editor plugins keep their reopening
    triggers in sections 10 and 12. Static and runtime records get explicit
    join keys, confidence, ambiguity, and
    version behavior before they are combined.

Step 5 selected the companion `citry_lsp` distribution. It exposes the
`citry-lsp` console command, declares Citry 0.3.2 through 0.3.x, catalog v1,
and client protocol v1 support, and has project-environment plus isolated
syntax-only install coverage. Citry 0.3.2 supplies the first published
portable analysis and coordinate contracts, so it must reach PyPI before
`citry-lsp` 0.1.0 can be published.

Claim each distribution identifier immediately before its artifact is ready to
publish; speculative name claims do not block earlier local work. No local
PyCharm installation was available on 2026-07-30, so the attach spike and any
JetBrains semantic-support matrix remain pre-publication work. This does not
change the implemented editor-agnostic server or VS Code client.
