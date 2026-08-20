# Design: IDE integration (editor tooling for citry)

**Status (2026-08-05): refreshed after maintainer review and accepted for
implementation.** Steps 1 through 9 at the end of this document are complete.
The portable syntax corpus drives the aligned Pygments lexers and declarative
VS Code highlighting, `citry check` provides parser-grade batch validation
with an explicitly bounded static fallback, and the companion language server
plus VS Code client provide the implemented editor intelligence. The VS Code
extension remains release-prepared rather than published. `citry-lsp` 0.1.0
is published and 0.1.1 is release-prepared. `pygments-citry` 0.1.2 is
published, with 0.2.0 release-prepared. The original design is the
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
The reusable implementation contract for adding another embedded component
language is [`embedded_language_ide.md`](embedded_language_ide.md); feature
work follows that vertical checklist instead of reconstructing the Template,
JavaScript, and CSS implementation history from this document.
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

**Existing assets.** `pygments-citry` 0.1.2 is published on PyPI
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
packages/py/pygments_citry/        0.1.2 published; 0.2.0 prepared    (Python)
packages/editors/syntax-fixtures/  exists; portable conformance data  (JSON)
packages/editors/vscode/           0.1.0 release-prepared              (JSON at v0; TypeScript with LSP)
packages/py/citry/                 existing `citry inspect`;          (Python, reuses citry_core)
                                     new `citry check`
packages/py/citry_lsp/             0.1.0 published; pygls server      (Python, reuses citry_core + citry)
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

One HTML-delegation slice is implemented in the current epic. On a native element,
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
edit mappings are equally exact. The implemented VS Code path scans direct
ordinary start-tag attributes, projects one `c-` prefix without changing UTF-16
coordinates, and accepts only provider hovers whose range exactly identifies
the projected lowercase suffix. Citry directives and every `c-*` tag boundary
    are excluded. Comments, expressions, raw-text bodies, end tags, and quoted
    nested templates cannot produce candidates in this direct-tag path. Step 22
    adds a separate parser-backed projection for nested templates and
    `<c-element>`. Provider absence remains a silent no-result.

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
  diagnosed by the parser itself. The editor setting additionally accepts a
  `ComponentLibrary`; its isolated worker installs that library into
  `Citry(autodiscover=False)` and reports that the registry excludes host-app
  state. An invalid spec, import failure, wrong object type, missing required
  host extension, or discovery failure is reported in tooling status and
  degrades to syntax-only analysis. The batch checker's `--app` remains a
  `Citry` instance because its other CLI commands need a runnable engine. No
  new parser machinery is needed for the rule checks.
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
  Its Python work is limited to conservative source-AST joins and mapped
  shadow documents for Citry-owned declarations, regions, and expressions. A
  pinned Python analyzer child answers only those mapped expression requests;
  Citry never attempts general Python semantic analysis or embeds a CSS or JS
  analyzer.
  Pyright / Pylance own the `.py` file; the citry server is a second,
  coexisting server registered for `python` documents plus the `citry-html`
  file type (the proven Ruff / Tailwind pattern).
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
  setting; the current `module:attribute` registry target resolves either the
  app instance or an isolated `ComponentLibrary` registry.
  The environments API is treated as an adapter, with an explicit executable
  setting retained because the extension API can change. This is
  the classic failure mode of Python-resident servers and gets first-class
  status reporting ("which Python, which registry target, registry or static
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

Implemented 2026-07-30 and extended within formatter protocol v1 on 2026-08-04
and library registry targets on 2026-08-08.
The server supports the Citry 0.4.x and component-catalog v1 contracts and
rejects an incompatible client protocol during initialize. A one-shot worker
subprocess imports the configured target, captures Python and file-descriptor
output, and returns only portable `TemplateAnalysis` and `ComponentCatalog`
data. A `ComponentLibrary` target is installed into a fresh
`Citry(autodiscover=False)` whose status names the library-only scope. Startup
is bounded at five seconds; `SystemExit`, invalid specs, hangs, crashes, and
malformed worker responses all produce one reported syntax-only degradation.
File changes and the explicit reload request replace the complete copied
project generation. No project module enters the LSP stdio process.

#### 3.4.1 Capability and degradation contract

Tooling reports its active mode so partial facts are never presented as
complete. These are the minimum guarantees for `citry check` and the server:

| Source and project state | Available behavior | Deliberately suppressed or reported limitation |
|---|---|---|
| Definite template region; configured app or library target imports and discovery completes | Base parser diagnostics, registered component and input checks, schema-free Citry structural/directive completion, lexical loop/fill completion and hover, registry component/attribute/slot completion, catalog hover, declared or conservatively source-inferred template-root completion/hover/navigation, type-aware member and call features for proven roots, exact component/input definitions when source is provable, unknown-component diagnostics, and application-configured unknown-root linting | Extension-transformed diagnostics unless that extension supplies an authored-source mapping; a library target explicitly excludes host-app components, configuration, and host-provided extensions |
| Definite template region; no app configured | `citry check --static` and the server provide base parser diagnostics in their explicit syntax-only modes; the server still offers Citry structural/directive completion and parser-proven lexical loop/fill completion, hover, and navigation; the VS Code client independently forwards HTML, CSS, and JavaScript completion, hover, and definitions | Registry component completion and hover, interface checks, unknown-component diagnostics, and delegated web-language diagnostics |
| Configured registry target is invalid, imports the wrong object, requires unavailable host extensions, or import/discovery fails | The same syntax-only analysis as an explicit `citry check --static` run | Registry-derived features; one actionable project-status error carries the underlying failure |
| Python file parses and contains a definite literal component asset | AST-decoded source, base syntax analysis, and exact authored host ranges through the shipped byte-to-UTF-16 source map | Computed, inherited, file-backed, concatenated, or otherwise nonliteral inline asset values unless registry-backed source discovery identifies a separate file |
| Python file is incomplete | `citry check` reports that the source cannot be analyzed; the server uses lexically proven current regions, recovers active bindings only from complete current-text start tags, and narrowly repairs a trailing member access or unfinished call only for the active completion/signature request | Stale semantic answers and diagnostics from an earlier source generation; ambiguous regions are skipped |
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

- **The first PyCharm semantics route is an LSP4IJ user-defined server
  template.** LSP4IJ
  supports declaring a language server with no plugin code (command plus
  file mappings), and definitions can be exported and imported as
  templates. The attach spike succeeded on 2026-08-11, and the repository
  publishes an importable template under `packages/editors/jetbrains/lsp4ij/`
  with the editor documentation. The
  JetBrains
  **native** LSP API is not a documented route here: it is a plugin API (an
  `LspClientDescriptor` lives in plugin code), so "config docs" cannot
  reach it; design A's contrary claim was judged factually wrong and is
  corrected in this synthesis. A thin official plugin (descriptor plus
  bundled server plus TextMate bundle) on the JetBrains Marketplace is a
  named later rung, once the server is stable.
- **The attach question is closed.** PyCharm 2026.2.0.1 with LSP4IJ 0.20.1
  attached one Citry server to both an inline `.py` component and a standalone
  `.citry-html` template while PyCharm's Python support remained active.
  Completion, hover, Definition, References, Declaration, Type Definition,
  push diagnostics, an unsaved diagnostic edit/clear, and standalone
  formatting all reached the IDE through LSP4IJ's feature adapters. A
  disposable native-API plugin also attached one project-wide Citry client to
  both files, so attachment alone is not a reason to maintain an official
  plugin. The exact environment, timings, falsifiers, and limitations are in
  `ide_research/pycharm_attach_spike.md`.
- **No inline coloring in PyCharm under this plan, and the docs say so.**
  JetBrains' TextMate bundle mechanism only applies to file types no native
  plugin owns; `.py` belongs to PyCharm's Python plugin, so no bundle can
  color inside Python strings. LSP diagnostics and completion work through
  the tested template, but inline templates have no Citry coloring
  until an official plugin adds native injection support, which is a named,
  triggered future rung (section 10), not an implicit never. PyCharm users
  can meanwhile use the IDE's own `# language=HTML` injection by hand;
  citry documents that it exists but does not ship or promote a marker
  convention, per the standing decision in `source_languages.md`. This
  framing is carried into user-facing docs verbatim (grafted from design
  C's "Note A", at both judges' direction).

#### Deferred first-party JetBrains plugin

The completed attach spike removes attachment as a reason to build a plugin,
but it does not make the LSP4IJ route equivalent to the VS Code client. The
remaining work is parked in
[GitHub issue #78](https://github.com/citry-dev/citry/issues/78) and has two
deliberately separate rungs.

The first rung tests the smallest editor-neutral coloring path. `citry-lsp`
would publish standard `textDocument/semanticTokens`, deriving token identity
and coordinates from the existing parser, Python/nested-template source maps,
and shared syntax fixtures. LSP4IJ 0.20.1 contains semantic-token support, but
Citry must still prove in a real PyCharm session that those tokens paint inline
regions cleanly over Python's ordinary string highlighting. The existing
TextMate grammar can separately supply baseline coloring for standalone
`*.citry-html`; a TextMate bundle cannot color a region inside the Python file
type PyCharm already owns.

The second rung is a first-party Kotlin plugin using JetBrains'
`LspIntegrationProvider` and one project-wide Citry client. It owns one-click
project-interpreter and `module:attribute` app selection, status/degradation
UI, restart/troubleshooting, and Marketplace packaging. Native language
injections are preferred for Citry/HTML in `template` strings, JavaScript in
`js` strings and Alpine expressions, and CSS in `css` strings. Injection
prefixes/suffixes seed `$component`, magics, `JsData`, props, event names,
Alpine scope, and `CssData` without copying those analyzers into Kotlin.

Ordinary injection is not sufficient for every surface. `<c-element is="...">`
must adopt the selected native element's contract; nested templates require
recursive source mapping; and Alpine/child-component behavior depends on
registry-backed projections. For those positions the plugin consumes Citry's
existing private HTML/browser projections, presents mapped virtual documents
to the installed JetBrains HTML/JavaScript/CSS services, and maps completion,
hover, edits, and navigation back to authored source. Generated locations must
never escape into the UI. Missing optional host-language services, indexing,
stale generations, cancellation, restart, and multiple workspaces all degrade
conservatively. Local PyCharm is proven first; JetBrains Remote Development
gets its own placement/interpreter matrix before documentation claims it.

Recommended order: semantic-token spike; standalone TextMate packaging; thin
native client/status plugin; native injections; then the specialized
`<c-element>`, nested-template, Alpine, props, events, and CSS projection
adapters. Semantic tokens may eliminate the coloring-only reason for a plugin,
but they cannot replace the editor-side provider bridge.

---

## 4. Editor coverage matrix

What this design delivers per editor at the end of v1 (section 5). "Inline"
means templates in `.py` strings; "file" means `template_file` templates.
The JetBrains semantics cells reflect the completed 2026-08-11 attach spike.

| Editor | Highlighting (inline) | Highlighting (file) | Diagnostics + completion + hover + go-to | Citry ships | Channel |
|---|---|---|---|---|---|
| VS Code + forks (Cursor, Windsurf, VSCodium) | Yes (injection grammar) | Yes (grammar) | Yes (bundled LSP client) | Extension | Marketplace + Open VSX |
| PyCharm / JetBrains | No (named future rung; section 3.6) | No in the current LSP4IJ route (`*.citry-html` remains plain text) | Yes for Citry's standard LSP features through the tested LSP4IJ template; VS Code-private HTML/JS/CSS delegation is absent | LSP4IJ template JSON + docs; thin plugin later | Docs site; JetBrains Marketplace later |
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
| v1.1 | Component/input/slot/slot-data completion, catalog hover, schema-free structural/directive completion, lexical loop/fill completion and navigation, declared and conservative source-inferred template roots, exact component-class/input/root navigation where provable, document symbols, conservative incomplete-region recovery, complete catalog retention, and VS Code web-language request forwarding | Implemented through 2026-08-08 | "My editor knows my components" even before app setup for parser-owned syntax, then adds registry contracts, exact authored fields and returned keys, slot-data shapes, and ordinary HTML, CSS, and JavaScript assistance inside asset strings |
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
  prepared locally at v0.1.0 and, when released, published to both the
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
| Language server | `packages/py/citry_lsp/` | Python | v0.1.0 published on 2026-08-19 |
| VS Code extension + grammars | `packages/editors/vscode/` | JSON + TypeScript | v0.1.0 client and universal VSIX implemented; not yet published |
| Structured diagnostics and `kind` getter | `crates/citry_template_parser/` + `crates/citry_core_py/` + `_rust.pyi` + Python wrapper | Rust + stubs | implemented 2026-07-30 through the required prior-art, plan, and cross-binding audit |
| Syntax corpus and authoritative-set validator | Highlighting tests plus `scripts/validators/` if cross-package validation needs it | Fixtures + Python | implemented with v0.1 highlighting |
| Editor setup docs, LSP4IJ template JSON, troubleshooting page | docs site (`docs_site/`) + `packages/editors/jetbrains/lsp4ij/` | Markdown/JSON | VS Code setup/troubleshooting and the tested PyCharm LSP4IJ template are implemented; remaining long-tail editor snippets stay in v1.2 |

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

- **General Python checking outside mapped template expressions.** Step 16 now
  uses shadow Python and a pinned `ty` child for member and call completion,
  hover, navigation, signatures, and diagnostics on proven template roots. It
  deliberately does not analyze arbitrary `.py` code or replace the user's
  Python extension. Citry owns only the template namespace, lexical controls,
  source mapping, and conservative result filtering. The analyzer owns Python
  names, types, calls, unions, and narrowing. Reopen this boundary only if a
  template feature requires an analyzer fact that cannot be requested through
  the supported child protocol.
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
- **A JetBrains-native plugin.** Parked in
  [#78](https://github.com/citry-dev/citry/issues/78), with the implementation
  and acceptance contract in section 3.6. Test standard semantic tokens and
  standalone TextMate coloring first. The **thin native LSP/status plugin**
  reopens when the LSP4IJ route proves too fiddly or first-party setup/status
  is itself valuable; the **native injection and projection bridge** reopens
  on demand for inline coloring or VS Code-parity HTML/JavaScript/CSS
  intelligence. Neither is needed merely to attach Citry alongside Python.
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
2. **PyCharm attachment regresses on both tested routes.** The 2026-08-11
   spike did not fire this falsifier: both LSP4IJ and the native API attached
   Citry alongside Python support. If a future supported PyCharm/LSP4IJ
   combination breaks both routes, correct the published coverage matrix and
   reopen the native-plugin question before claiming that version.
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
   fingerprint. Effective schema construction snapshots each field's authored
   owner across both eager annotations on Python 3.10 through 3.13 and deferred
   annotations on Python 3.14. C3-composed `TemplateData` and `Kwargs` therefore
   retain every distinct source owner without asking the LSP process to evaluate
   project annotations. The unreleased catalog and client protocols remain
   version 1.
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
    allows. Step 17 now owns unresolved-root diagnostics through a Citry rule
    whose default severity is error. Runtime globals, lint-only declarations,
    extension metadata, and explicit extra-preserving policies participate
    without pretending that unknown or absent schemas are closed. No protocol
    or catalog version bump is needed before the first release.
11. **Preserve native HTML intelligence for dynamic attributes.** Implemented
    2026-08-06 for direct-attribute hover in VS Code. On native
    elements, project a recognized dynamic attribute such as `c-class` to its
    underlying `class` attribute when forwarding to the installed HTML
    provider. Hovering either spelling must return equivalent documentation,
    including the provider's MDN link, while any returned range maps back to
    the full Citry spelling. Do not rewrite Citry directives, component inputs,
    or unknown `c-*` names, and degrade to no result when no provider responds.
    The same-length client projection lowercases the native suffix for HTML
    identity and maps only an exact provider-owned suffix range back to the
    complete Citry spelling. It excludes every `c-*` tag boundary, raw-text
    body, comment, expression, end tag, and quoted nested template. Completion
    remains outside this direct dynamic-attribute slice. Step 22 implements
    nested-template and `<c-element>` forwarding through a distinct parser-backed
    projection rather than loosening this hover contract.
12. **Accept a `ComponentLibrary` as a registry target.** Implemented
    2026-08-08. Allow the existing
    `module:attribute` setting to resolve either a `Citry` instance or a
    `ComponentLibrary`. For a library target, the isolated discovery worker
    creates `Citry(autodiscover=False)`, registers that manifest, and publishes
    the resulting built-in-plus-library analysis and catalog. Status and
    documentation must make the boundary explicit: this mode knows no host-app
    components, configuration, or host-provided extensions. If the library
    cannot install without host-provided extensions, discovery fails clearly
    and directs the author to expose a configured `Citry` wrapper instead. In
    particular, `"citry.app": "citry_ui:__citry_library__"` works as the direct
    manifest target.
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
    The no-whitespace activation slice was implemented on 2026-08-08. VS Code
    retriggers once when the first Unicode identifier character is typed in a
    lexically plausible Citry Python or structural-value host, including
    directly after `{{`, an attribute quote, or an operator. It uses the same
    deletion and history recovery as tag completion. Identifier characters
    remain absent from the global LSP trigger list so ordinary Python typing
    does not wake Citry; the server remains authoritative for exact parsed
    regions, expression token context, and replacement ranges. Strings,
    comments, mapping string keys, and raw-text bodies are declined, while
    f-string replacements and static `c-fill` `name`/`data` values retain their
    applicable completion paths. Automatic word retriggering is limited to
    conventional direct Python `template` literals and documents explicitly in
    `citry-html` mode. Registry-owned files left in ordinary `html` mode still
    support manual completion and native punctuation/whitespace triggers, but
    the client cannot prove their ownership before waking every HTML provider.
14. **Add first-party Citry syntax hover.** Implemented 2026-08-08. Concise,
    syntax-only hover documentation and canonical `https://citry.dev/` links
    cover every parser-owned structural tag, fixed directive, and contextual
    structural attribute. The acceptance corpus includes `c-bind`,
    `<c-slot>`, `<c-slot required>`, and `<c-fill>`, along with closing tags,
    nested templates, inline Python strings, and invalid structural placement.
    One context-qualified table drives both completion and hover. Its tag,
    directive, and per-structural-tag attribute keys are checked against
    immutable inventories exported by the Rust parser through `citry_core`.
    Exact AST token ranges handle valid templates; a parser-shaped scan keeps
    tag and attribute help available when semantic placement fails, while
    comments, raw bodies, values, dynamic `c-*` attributes, and split Python
    literal tokens produce no false hover. Registry state and an installed HTML
    provider are not prerequisites. Existing lexical and `TemplateData` hover
    wins inside expression values, and catalog hover still owns registered
    components and component inputs that are not fixed Citry syntax.
15. **Infer conservative roots from `template_data()` source.** Implemented
    2026-08-08. Use the
    selected project interpreter's CPython `ast`, not Ruff's `ty` analyzer, for
    this source-shape pass. The isolated app worker statically walks the loaded
    component class MRO to copy the concrete-to-owner resolution chain, files,
    and qualified names without invoking the method or arbitrary descriptors.
    An engine-owned `ComponentLibrary` materialization wrapper is collapsed
    only from its positive runtime marker, and the effective function's code
    file and first line must match the exact direct AST method it claims as
    provenance.
    The private worker metadata is keyed by catalog `definition_id`; it does not
    expand catalog v1 or the client protocol. A shared, pure source-analysis
    function under `citry.analysis` then analyzes that exact method without
    importing project code. The LSP supplies synchronized editor text for every
    open Python file in the chain and disk source otherwise. The checker now
    supplies disk source to the shared step-17 root policy; step 15 itself did
    not add a new `citry check` finding or report field. Direct returned dicts
    and only explicitly modelled local aliases, mutations, branches, and `**`
    unpacks contribute literal string keys. A direct return of the method's
    `kwargs` parameter, or a simple untouched alias of it, instead joins the
    component's proven effective `Kwargs` fields. This includes the inherited
    base implementation, whose runtime contract makes component inputs
    available as template roots without an override. Typed `Kwargs` is a
    structural carrier rather than an ordinary dict, so calls, subscript
    operations, unpacking, and other mutations on it withhold those roots;
    returning any other unknown parameter or name leaves the shape open.
    Literal-dict roots carry their key range and an optional
    value-expression range, while kwargs-derived roots reuse the effective
    `Kwargs` field's existing declaration provenance. Every result also carries
    whether the key is always or conditionally present and whether the complete
    shape is closed or remains open with a reason. The source pass does not
    infer value types; kwargs-derived roots reuse their existing structured
    schema type when all consumers agree. Repeated literal keys follow Python's last-write order within
    one mapping. When several reachable branches define the same key, retain
    every definition and return every distinct standard LSP location; never
    choose one arbitrarily. Unknown unpacking preserves proven key existence
    while discarding any value definition it may overwrite. Passing a tracked
    mapping to unsupported code or referencing it from unmodelled control flow
    withholds that affected mapping's roots rather than guessing. Invalid or
    unreadable source, an unsaved class or method
    rename that no longer matches runtime provenance, or anything other than
    one exact owning AST node contributes no inferred roots for that owner and
    never reuses stale definition ranges. A key can complete and navigate to
    its literal definition even when its value type is unknown. Literal keys
    are accepted only when their exact runtime string is also the exact Python
    identifier identity, so normalization-changing strings are not suggested.
    This pass does
    not grow its own general Python type system. Declared `TemplateData` remains
    authoritative where present, and a physical template shared by several
    components exposes only compatible proven roots shared by every consumer.
    This is the narrow path that makes keys such as `root_class` and
    `root_attrs` useful without forcing authors to duplicate a large return
    dict solely for editor support.
16. **Design and implement type-aware Python template expressions.**
    Implemented 2026-08-08. The accepted analyzer and source-mapping contract
    is specified in
    [`python_template_expressions.md`](python_template_expressions.md). A
    portable `citry.analysis` builder finds every Python-valued host and emits
    virtual Python that binds declared or source-inferred roots, recreates
    template conditions, lowers loop clauses to comprehensions, carries nested
    template and fill scope, and maps exact expression and unchanged Python
    source ranges. Inferred methods are copied so their concrete return value
    types remain visible even through a broad public return annotation; the
    inherited `return kwargs` path imports only static type information for the
    effective `Kwargs` schema. The schema catalog supplies per-field authored
    owners from its version-neutral annotation snapshot, including Python 3.14
    deferred declarations; missing owner provenance withholds that typed binding
    rather than falling back to the generated effective class.
    `citry-lsp` runs the exactly pinned published `ty` language server from the
    selected environment as one child per workspace. Standard structured LSP
    records provide member and call completion, hover, definition, signature
    help, and pull diagnostics without linking Ruff's unpublished internal
    crates or importing project code in the stdio process. Results are retained
    only inside mapped authored expressions, shared consumers and return paths
    are joined conservatively, Citry owns unknown-root findings independently,
    and private, `str.format`, and receiver-proven sandbox-internal members are
    filtered. Missing, mismatched, failed, and timed-out analyzers produce
    one degradation notice while parser and root features continue. The client
    protocol remains version 1 because all editor operations use standard LSP
    capabilities. Variable hover composes a Python-highlighted declaration
    from the analyzer's current type with Citry's root or lexical provenance;
    declared catalog text remains the fallback when semantic analysis cannot
    prove one complete answer across every consumer and return path.
17. **Configure template linting on `Citry`, with strict unknown roots by
    default.** Implemented 2026-08-08. The contract is specified in
    [`template_linting.md`](template_linting.md). Add one extensible
    lint-settings surface to the `Citry` instance and carry it through portable
    analysis so `citry check` and the LSP apply the same policy; VS Code does
    not invent a parallel preference. `rule_unknown_template_variable` accepts
    `ignore`, `warning`, or `error` and defaults to `error`. Diagnose only free
    root names after accounting for lexical bindings, declared or inferred
    component data, runtime globals, lint-only variables, and extension
    contributions. Portable schema metadata records `closed`, explicit
    `allow-extra`, or `unknown` namespace policy rather than treating a field
    list as exhaustive. Explicitly extra-allowing schemas cap the diagnostic at
    warning; unknown and absent schemas remain strict unless the author declares
    the name or overrides the rule. Members remain the Python analyzer's
    concern. Components configure inherited overrides through `Component.Lint`.
    Syntax-only analysis, which cannot associate a component namespace, does
    not guess. Runtime globals and lint-only declarations also participate in
    root completion, Python-style hover, and conservative member intelligence;
    qualified forward annotations resolve in the selected project environment.
    Direct application and component `template_variables` mappings also carry
    exact, synchronized source provenance for Definition and Declaration;
    dynamic or ambiguous construction produces no guessed target.
    Citry-owned diagnostic identifiers, message templates, trigger conditions,
    examples, default severities, reporting surfaces, and help links come from
    the versioned diagnostics-v1 catalog. The LSP retains `citry` as the
    standard source label and attaches catalog documentation through
    `Diagnostic.codeDescription`; provider-owned `citry.python.*` details
    remain external.
18. **Join CSS data sources to component CSS.** Implemented 2026-08-09. This
    step covers both declared
    `Component.CssData` fields and exact string keys inferred conservatively
    from `css_data()` when no schema is declared. A Python field name maps to
    its exact runtime custom-property spelling: `chart_height` becomes
    `--chart_height`; Citry does not convert underscores to dashes or normalize
    case. An inferred key such as `"row-color"` becomes `--row-color`.

    The first supported authoring surfaces are direct `Component.css` string
    literals and registry-owned `css_file` files, including inherited and
    shared assets with source-proven owners. CSS selected dynamically,
    dependency or extension CSS without an authored source map, compiled CSS
    dialects, arbitrary stylesheets, inline `style` attributes, and template
    `<style>` bodies remain outside this step. A template `<style>` element is
    not itself the component CSS asset that causes `css_data()` to be emitted,
    so it needs a separate delivery and ownership contract before Citry joins
    data to it.

    Citry recognizes a data reference only as the custom-property argument of
    `var()`, including incomplete `var(--` and `var(--cha` authoring states.
    Custom-property declarations, `@property`, strings, comments, selectors,
    and lookalike text are not data references. The scanner handles CSS
    comments, strings, nested functions, fallbacks, CRLF, Unicode, UTF-16
    editor coordinates, and incomplete input. Completion emits the exact
    unescaped runtime spelling; escaped identifier spellings conservatively
    receive no Citry result in this step.

    Completion, hover, Definition, Declaration, and References are additive to
    the editor's ordinary CSS service. Hover leads with the CSS property and
    then names every proven Python producer, its annotation, and description.
    A Python annotation describes the value before CSS serialization, not the
    CSS grammar accepted where `var()` is used, so Citry does not present it as
    a CSS value type. Definition and Declaration point to exact `CssData`
    fields or inferred dictionary keys. References list each exact use in the
    same physical CSS asset once; `includeDeclaration` adds every exact Python
    origin. Reverse Python-field-to-workspace-CSS references, Type Definition,
    rename, and workspace-wide CSS indexing remain outside this slice.

    A shared stylesheet gets Citry assistance only for a name available from
    every currently proven consumer. Hover lists each producer separately when
    annotations or descriptions disagree, and navigation returns every exact
    origin. A name present on only some consumers produces no Citry result.
    Syntax-only analysis has no component owners and therefore leaves the
    stylesheet entirely to the ordinary CSS provider.

    `css_data()` source inference reuses the portable, batch-capable mapping
    analysis developed for `template_data()`, with a CSS string-key policy and
    without the default `return kwargs` rule. It accepts direct dictionary
    returns, simple aliases, modeled updates, exact string keys, and multiple
    reachable return paths. Conditional keys remain available but are marked
    conditional. Computed keys, escaped mappings, unsupported mutation,
    ambiguous method ownership, and stale source open the shape or withhold it
    rather than manufacturing provenance. A declared `CssData` schema remains
    authoritative; open-schema extras are not guessed from source in this
    first implementation.

    Source freshness follows the template-variable contract. The worker copies
    CSS asset and `css_data()` resolution chains from its isolated project
    process. The long-lived LSP validates effective MRO, direct string or
    `pathlib.Path(...)` asset ownership, schema fields, and inferred-key ranges
    against synchronized source. Imported constants, factories, decorators,
    metaclasses, other dynamic asset selection, conflicting source aliases,
    or a changed request generation degrade to no Citry result. Shared
    consumers are filtered independently, so one stale component does not
    invalidate an unrelated proven owner.

    This feature deliberately emits no unknown-property or unused-field
    diagnostics. A custom property can come from an ancestor, the host page, a
    theme, an external stylesheet, JavaScript, or an extension. Likewise, an
    apparently unused `CssData` field can be consumed outside the component's
    primary authored stylesheet. The join proves known producer provenance;
    it never claims CSS namespace closure or selector isolation.
19. **Specify and implement automatic `JsData` scope seeding.** Implemented
    2026-08-09. The runtime
    keeps content-addressed JSON delivery, but parses a fresh value graph for
    every component invocation so siblings never share mutable arrays or
    objects. It seeds every top-level `js_data()` entry into the component's
    stable Alpine scope before `$component` runs. A callback may overwrite a
    seeded name or add another name; on a correlated rerender Citry refreshes
    current seeded names, removes seeded names absent from the new payload,
    and preserves callback-owned names outside that set. Inner Alpine scopes
    retain their ordinary lexical precedence, component boundaries stay
    isolated, and fill content retains its recorded lexical source.

    The wire contract remains strict JSON: null, booleans, finite numbers,
    strings, arrays, and objects with exact string keys. Seeding does not
    flatten nested objects or rename keys. Property writes must be safe even
    for names such as `__proto__`; only JavaScript-identifier keys later
    participate in bare-name editor completion. The callback receives the
    same invocation-local snapshot as `data`, while `scope` remains the
    mutable Alpine surface.

    A component with `$component` always receives the seed before its
    callback. A rendered component that declares `JsData` or overrides
    `js_data()` and has Alpine expressions receives an explicit seed-only
    lifecycle call even when it has no component JavaScript or its current
    data is empty; the empty call also clears keys owned by an earlier render.
    A component that inherits the framework's always-empty default needs no
    seed call. The manifest states whether a call initializes or only seeds;
    the client never guesses from a registration that may still be loading.
    `js_data()` alone does not ship Alpine or a payload when the rendered
    instance has neither `$component` nor browser expressions. For initial
    documents and inserted fragments, scope attachment and seeding finish
    before Alpine evaluates the instance or dependent children run. Missing
    or malformed data cancels that call with a pointed client error rather
    than exposing a partially seeded scope.
20. **Add Alpine/browser-expression intelligence from that contract.**
    Implemented 2026-08-09. Parse
    expression and statement contexts for `x-*`, `@*`, and `:*`; offer
    `JsData`-derived names and their JSON wire types; and navigate those names
    to exact Python fields or conservatively inferred `js_data()` keys.
    Declared `JsData` is authoritative. Without it, source inference follows
    the same current-source and shared-consumer confidence rules as template
    and CSS data. A direct value such as `kwargs.submitting` joins to the
    effective `Kwargs.submitting` annotation through the method's actual
    second parameter name. Python annotations map to a structured JSON type
    model, not copied display strings. A field whose type cannot be converted
    cleanly to the strict JSON wire contract produces a warning at its
    declaration and degrades to `unknown` for editor typing; runtime
    serialization remains the final check for actual values.

    Component JavaScript receives a mapped virtual declaration for
    `$component`. Its `data` and initial `scope` shapes come from `JsData`; its
    read-only `props` shape comes from the authored `props` declaration,
    including constructor unions, required/default presence, and the
    runtime's null policy. Empty or dynamic prop definitions remain unknown
    instead of borrowing types from similarly named JS data. Generated ranges
    never escape into authored edits or navigation.

    Events, State, props, Alpine magics, and names added imperatively by
    `$component` remain separate proven sources. A string literal passed to
    `sendEvent` or `$sendEvent` is checked against the owning component's
    effective Events handler wire names and navigates to the exact Python
    method. Dynamic names remain unchecked. `onEvent` and `$onEvent` listen
    for open browser-event names produced by `actions.Dispatch` or other DOM
    code, so they accept any string and do not use the server-handler
    diagnostic.

    The portable analysis locates expression, statement, and loop hosts in
    supported Alpine attributes, including nested templates, without
    importing project code. It also identifies root names, simple
    `owner.member` uses, `$component` prop declarations, and literal server
    event calls while declining strings, comments, computed members, and
    dynamic event names. `citry check` and the LSP share the same structured
    Python-to-JSON type mapping and diagnostics.

    In VS Code, a version-bound virtual JavaScript document delegates ordinary
    JavaScript completion, hover, and definition to the installed JavaScript
    provider. Citry adds exact `JsData` roots, component `data` and `scope`
    members, public Events `State` members through `$state` and callback
    `state`, static client props, and server-event origins. Shared assets keep
    only contracts proven for every owner, and synchronized Python source is
    revalidated before a result is returned. Citry-owned names suppress a
    duplicate delegated hover or definition. Citry owns linked hover help for
    its Alpine magics and `$component` context, while ordinary JavaScript
    remains provider-owned. Generated projection ranges, stale
    document versions, invalid source, ambiguous ownership, unsupported data
    shapes, and partial provenance degrade to no mapped result. This slice
    does not claim a standalone JavaScript diagnostic service. Citry owns its
    JSON-wire warning, Alpine and component-initializer namespace rules,
    literal server-event contract, and static child-prop contract; ordinary
    JavaScript diagnostics remain provider-owned.

    **Accepted browser-intelligence expansion.** User testing after the first
    Step 20 delivery established that browser expressions need the same strict
    namespace policy as Python template expressions. Citry therefore owns a
    portable Alpine-expression analyzer, backed by OXC and shared by
    `citry check` and the LSP. It distinguishes declarations, local bindings,
    property names, and free root references instead of promoting the earlier
    lexical scanner into a linter. A free Alpine root absent from every proven
    source is an error by default. `LintSettings.rule_unknown_alpine_variable`
    and the matching `Component.Lint` field accept `"error"`, `"warning"`, or
    `"ignore"`; `alpine_variables` declares additional analysis-only browser
    globals or custom Alpine magics using the same annotation and
    `Annotated[T, description]` convention as template lint variables.
    `JsData`, inferred `js_data()`, Alpine/Citry magics, ordinary browser
    globals, `x-data`, `x-for`, and proven synchronous `$component` scope writes
    are joined automatically and are never repeated in that setting.

    Component JavaScript has a separate strict namespace rule for proven
    `$component` initializers. OXC resolves local declarations and the exact
    callback or configuration-`init` context destructuring, then reports free
    initializer references without scanning unrelated file-level JavaScript.
    A missing name is an error by default, so `scope.value = ...` is rejected
    when the callback destructured only `data`. The application and inheritable
    `Component.Lint` declaration expose
    `rule_unknown_component_js_variable = "error" | "warning" | "ignore"`
    and `component_js_globals`, whose values use the same annotation and
    `Annotated[T, description]` convention. ECMAScript and browser globals are
    built in; callback context names must be destructured and are not implicit
    globals. Invalid severities or JavaScript identifiers are rejected when
    settings are constructed. Invalid or unsupported initializer source
    produces no partial namespace diagnostic and leaves ordinary JavaScript
    diagnostics to the installed provider.

    `$component` exposes the complete runtime callback context, including
    `id`, `els`, typed `data`, initial `scope`, read-only `props`, Events
    `state`, `loading`, `error`, `effect`, `reactive`, `graph`,
    `provide`/`inject`/`unprovide`, `sendEvent`, and `onEvent`. Callback and
    configuration-object forms use separate contextual overloads, and the
    callback result is `void | (() => void)` because a returned function is
    cleanup while async initialization is unsupported. Direct synchronous
    initialization writes such as `scope.name = value`, `scope["name"] =
    value`, and a static `Object.assign(scope, {...})` add proven variables to
    the component's Alpine subtree. Conditional writes are optional; computed
    keys, escaped aliases, async/later writes, and arbitrary dynamic mutation
    remain unproven. Rebinding the local `scope` parameter does not replace the
    Alpine scope.

    `x-for` separates its declaration pattern from its iterable expression.
    The iterable is checked in the outer scope; declared value/key/index names
    are typed, navigable, and visible on the `<template>` and its single-root
    descendant subtree, with nested scopes and shadowing resolved by binding
    identity. The provider projection models Alpine value iteration rather than
    copying JavaScript `for...in` semantics.

    Literal server-handler checks cover all equivalent spellings: `sendEvent`
    and `$sendEvent` calls, declarative `@c-*` bindings, and the handler names
    passed to `$loading(...)` and `$error(...)`. They share
    `citry.browser.unknown-server-event`, completion, hover, and exact Python
    handler navigation. `onEvent` and `$onEvent` remain open browser-event
    listeners. Declarative handler argument expressions are analyzed in the
    source component's Alpine scope.

    Citry-owned browser APIs have first-party hover records with their
    JavaScript signature, a concise explanation, and a canonical documentation
    link. This covers `$component`, each proven destructured context binding,
    and Citry Alpine magics such as `$sendEvent`, `$loading`, and `$error`.
    Literal server-event completion works from an empty or partial string in
    `sendEvent`, `$sendEvent`, `$loading`, and `$error`, using the same handler
    contract as diagnostics and navigation.

    The VS Code adapter keeps one virtual JavaScript document per authored
    browser host and refreshes it as the source changes. Requests for the same
    document version and cursor position share one LSP projection. When the
    registry-backed projection exists, the generic embedded-JavaScript path
    does not invoke a second provider. This keeps the installed JavaScript
    service warm, avoids duplicate work, and prevents generated `document.js`
    targets from escaping through fallback navigation. Cancellation, stale
    source versions, failed providers, or a missing registry return no result.

    For a statically resolved child component, `$c-props` is checked against
    the child's effective static `$component({props})` contract. Citry reports
    unknown keys, missing required keys, and incompatible proven value types,
    and navigates an authored key to the child prop declaration. Explicit keys
    remain checkable beside a spread, but a dynamic spread prevents a
    missing-required conclusion; computed keys, dynamic component targets,
    ambiguous shared targets, and unproven `c-$c-props` results degrade without
    a speculative diagnostic.

    The accepted expansion was implemented on 2026-08-10. The portable OXC
    analysis, shared lint policy, event contract, `$component` declarations,
    scope-write discovery, `x-for` bindings, and static `$c-props` checks are
    consumed by batch and editor surfaces from the same source records.

21. **Complete the PyCharm attach spike.** Verify inline Python-string and
    standalone-template behavior through LSP4IJ, publish an importable template,
    and document the tested capability matrix before release.

    Implemented 2026-08-11. PyCharm 2026.2.0.1 and LSP4IJ 0.20.1 attached one
    Citry server to both document shapes alongside native Python support. The
    standard completion, hover, Definition, References, Declaration, Type
    Definition, push-diagnostic, unsaved-edit, and standalone-formatting paths
    passed through LSP4IJ. A disposable native `LspIntegrationProvider` reached
    `Running` and attached to both files as well. The first public route is the
    importable definition in `packages/editors/jetbrains/lsp4ij/citry/`; a
    maintained native plugin remains triggered by setup/status/coloring or
    private-provider needs, not by an attach blocker. The spike also narrowed
    dynamic formatting registration to a language-only selector accepted by
    both JetBrains clients without exposing Citry formatting on Python files.
    See `ide_research/pycharm_attach_spike.md` for the evidence matrix and
    limitations. The intentionally deferred coloring, native-client, and
    HTML/JavaScript/CSS bridge work is tracked in
    [#78](https://github.com/citry-dev/citry/issues/78) with its staged
    acceptance contract.
22. **Grow the remaining long tail only from evidence.** Richer whole-program
    indexing beyond the scheduled expression work, extension-aware
    authored-source mappings, alternate template dialects,
    tolerant Citry parsing, and native editor plugins keep their reopening
    triggers in sections 10 and 12. Static and runtime records get explicit
    join keys, confidence, ambiguity, and
    version behavior before they are combined.
    The two concrete HTML-provider follow-ups were implemented on 2026-08-10.
    Nested templates stored in `c-*` attribute values receive HTML completion,
    hover, and definition through a parser-proven virtual fragment. The LSP
    strips the `<>...</>` envelope, selects the deepest containing nested
    template, and returns an exact version-bound source range. The VS Code
    client asks the installed HTML provider against that fragment and maps
    only ranges and edits contained by the returned source map. For example,
    a double-quoted nested-template attribute uses single quotes for HTML
    attributes inside it: `c-body="<><input type='email' /></>"`.

    `<c-element>` start-tag intelligence uses the same parser-backed request.
    A statically proven literal target such as `is="form"` is projected to a
    same-length `<form>` start tag, so tag-specific attributes such as
    `action` and `method` are available. A dynamic `c-is`, `c-bind`, an
    unproven target, or a literal tag name too long for exact same-length
    mapping is projected to a custom-element placeholder, which preserves
    generic global HTML attributes without claiming a tag-specific contract.
    Citry's `is`, `c-is`, and `c-bind` selection attributes are masked from the
    HTML provider. Dynamic native attributes such as `c-action` still use the
    exact suffix projection from step 11 and map hover back to the complete
    authored name.

    Both paths require the current parser tree, one contiguous literal range,
    and a linear authored-source mapping. Host-only multiline indentation is
    retained in the virtual fragment. Invalid/recovered syntax, Python escapes
    or literal joins that need a richer map, stale versions, provider
    failure, and out-of-range provider edits return no result. A cheap lexical
    client filter only decides whether to ask for the parser-backed projection;
    it never establishes eligibility. This additive private request keeps the
    unreleased protocol at version 1.

    **Performance follow-up, implemented 2026-08-10.** The VS Code adapter
    rejects irrelevant browser-provider routes before contacting the LSP,
    coalesces Python watcher bursts, keeps stable generic virtual-document
    identities, caches HTML projections by document generation and containing
    source range, and requests no eager completion-item resolution. Custom
    projections and delegated providers have bounded waits and propagate
    cancellation where the public provider API permits it. Opt-in
    `citry.trace.performance` output records projection, virtual-document,
    delegated-provider, and total elapsed time as structured JSON without
    changing protocol v1.

    Project discovery runs asynchronously. Reload requests are serialized,
    debounced, and latest-wins; a catalog refresh preserves the one incremental
    `ty` process. Child requests keep late protocol responses consumable after
    cancellation, and shutdown retains ownership through bounded terminate and
    kill escalation. Semantic diagnostics wait for a short idle period, cancel
    obsolete generations, reuse one proven component/source join per template
    generation, and batch compatible expression copies into one analyzer
    document per consumer. Direct Python dependencies are refreshed first;
    analysis with an incomplete transitive-import graph retains the broader
    freshness fallback.

    On the 2026-08-10 development machine, constructing shadows for 60 Python
    expressions fell from 475.64 ms to 12.87 ms on the first generation and
    below 0.01 ms for an unchanged generation. Thirty mapped `ty` diagnostics
    used one request instead of 30 and measured 64.51 ms cold and 15.41 ms
    warm. On a 17.4 KB template, the client-side browser route measured about
    0.22 ms median / 0.24 ms p95, and deepest HTML-host selection measured
    about 0.28 ms median / 0.37 ms p95. These are focused implementation
    benchmarks, not end-to-end editor latency; the performance trace is the
    supported way to separate provider stages in a real Extension Host.
23. **Complete variable navigation with standard LSP meanings.** Implemented
    2026-08-08. References operate only on a proven template root or exact
    parser-owned `c-for` or `c-fill` binding. They list authored uses inside the
    same physical template, including nested templates, without crossing sibling
    bindings that reuse a name. `includeDeclaration` adds the lexical
    introduction or every exact `TemplateData`, `Kwargs`, or inferred-dict-key
    origin. Definition and Declaration share that Citry-owned origin resolver.
    Type Definition is a separate `ty` request: it points to the actual Python
    class or typeshed type, maps copied source back to the authored file, and
    returns no result when any proven consumer or return path lacks a safe
    target. Untyped `c-fill` bindings point to their current neutral `Any`
    contract even when they have no authored use. Python-local lambda,
    comprehension, and walrus variables, member references, and references in
    other physical templates remain outside this first slice. Invalid parses,
    ambiguous ownership, a stale synchronized schema or asset-resolution chain,
    analyzer failure, or a generated-only target degrade to no result rather
    than a partial answer.
    Asset freshness is source-proven only for direct string literals and
    direct `pathlib.Path(...)` declarations. Imported constants, factories,
    decorators, metaclasses, and other dynamic asset selection keep their
    loaded registry behavior, but any synchronized Python buffer makes this
    navigation slice fail closed until discovery runs again.
24. **Keep template literals from being changed into f-strings by Pylance.**
    Implemented 2026-08-08. Pylance owns this edit through
    `python.analysis.autoFormatStrings`; its default is `false`. Citry documents
    a workspace override of `false` and uses it in this repository. The setting
    is window-scoped, so one workspace value applies to every Python file in
    that VS Code window, not one template literal or workspace folder. Citry
    does not intercept typing or reverse document changes because those events
    cannot prove whether an f-string edit came from Pylance or was authored
    deliberately. Editors without Pylance need no setting.

Step 5 selected the companion `citry_lsp` distribution. It exposes the
`citry-lsp` console command, declares Citry 0.4.0 through 0.4.x, catalog v1,
and client protocol v1 support, and has project-environment plus isolated
syntax-only install coverage. Citry 0.4.0 supplies the first published
portable analysis and coordinate contracts, and reached PyPI before
`citry-lsp` 0.1.0 was published on 2026-08-19.

Claim each distribution identifier immediately before its artifact is ready to
publish; speculative name claims do not block earlier local work. The PyCharm
attach spike completed on 2026-08-11. Its checked-in LSP4IJ definition and
tested semantic-support matrix cover the editor-neutral server;
Citry-specific JetBrains coloring and VS Code-private provider delegation
remain separate future plugin work.
