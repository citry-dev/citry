# Design C: ecosystem-first IDE integration

**Date: 2026-07-07. Status: competing draft.** One of three design proposals
for citry's editor integration, feeding the final
[`../ide_integration.md`](../ide_integration.md). This draft argues the
**ecosystem-first** position: maximize the number of editors that get real
citry support per unit of maintainer effort, by shipping artifacts that
existing editor ecosystems already know how to consume, and by integrating
with the tools users already run (Pylance, PyCharm) rather than competing
with them.

Terms used throughout, defined once. **LSP** (Language Server Protocol) is
the editor-agnostic protocol a separate "language server" process speaks to
provide completion, diagnostics, hover, and navigation. **tree-sitter** is an
incremental, error-tolerant parser framework whose grammars Neovim, Zed, and
Helix consume natively for highlighting and structural editing. A **TextMate
grammar** is the older regex-based highlighting format VS Code, Sublime, and
JetBrains consume. An **injection** is a grammar rule that hands a region of
one language (a Python string, a `{{ ... }}` expression) to another
language's grammar. The **project index** is this design's name for the
server's model of which components exist in the user's project and what
inputs and slots each declares.

---

## 1. Prior art

What was searched before writing this proposal, per CLAUDE.md Mechanism 1.

**The research corpus in this directory**, all five reports, all
web-verified 2026-07-07:

- [`recon-citry-tooling-surface.md`](recon-citry-tooling-surface.md): what
  the parser and bindings already provide (spans, variable tracking,
  `TagRules`), the gaps (fail-fast parsing, string-flattened errors, the
  unconditional PyO3 dependency), and the 7-item engine-side punch list.
- [`recon-vue-tooling.md`](recon-vue-tooling.md): the Vetur/Volar/JetBrains
  arc; takeover mode's failure, vue-tsc's fragility, JetBrains abandoning
  its parallel type checker, web-types.
- [`recon-python-template-tooling.md`](recon-python-template-tooling.md):
  djlsp and djls, PyCharm's injection APIs, Pylance's closed surface, the
  second-server coexistence pattern (Ruff, Tailwind), django-components'
  empty baseline.
- [`recon-lsp-architectures.md`](recon-lsp-architectures.md): the four
  server-runtime options with a decision table, the TextMate/tree-sitter
  split of the editor world, semantic-token support per editor,
  distribution channels per editor.
- [`recon-framework-tooling-field.md`](recon-framework-tooling-field.md):
  nine framework tooling stories with maintenance statistics; templ's
  one-maintainer proxy LSP and its four cost clusters; the cost-ordered
  ladder of rungs; the finding that registry completions plus compile-time
  validation deliver most perceived value.

**Repo ground truth read directly for this draft** (spot-checked today, not
only via the recon reports):

- The standing decisions in
  [`../source_languages.md`](../source_languages.md): no highlight-only
  marker stopgaps, `*_lang` declaration attributes, the staged
  skeleton-grammar-server build path, and the explicit endorsement of a
  tree-sitter grammar as the way to get correct highlighting boundaries
  before the server exists (`source_languages.md:367-377`, `:402-417`).
- The tooling issues and their placement:
  `TODO/project_status_june_2026.md:527-537` (formatter #22, LSP #23, other
  bindings #27) and `docs/design/extensions_roadmap.md:110-117` (LSP,
  formatter, and highlighting are standalone tooling, not extensions;
  component introspection is core work, issue #26).
- The existing highlight asset: `packages/py/pygments_citry/`, whose
  builtin-tag list is a hand-kept mirror of `RESERVED_TAG_NAMES`
  (`packages/py/pygments_citry/pygments_citry/citry_html.py:29-33`,
  `crates/citry_template_parser/src/constants.rs:56`).
- The component surface being served: inline `template` / `js` / `css`
  strings or `*_file` paths on `Component` subclasses
  (`packages/py/citry/citry/component.py:263-324`), the component registry
  (`packages/py/citry/citry/component_registry.py:86-112`), the V3 syntax in
  `README.md` (two rules, thirteen built-in tags), and the repo-wide check
  gate with its custom validators (`scripts/check.py`, `scripts/validators/`).
- Parser facts cited below: `Token` spans
  (`crates/citry_template_parser/src/ast.rs:20-35`), `TagRules`
  (`crates/citry_template_parser/src/parser_context.rs:31-62`), the
  unconditional pyo3 dependency
  (`crates/citry_template_parser/Cargo.toml:12`).

**Fresh web checks made for this draft** (2026-07-07, on top of the corpus;
sources in section 10):

- Editor market share among Python developers: the 2024 Python Developers
  Survey (PSF/JetBrains) puts main-editor share at VS Code 48%, PyCharm 25%,
  Neovim 4%, Vim 3%, with a long secondary-editor tail (Vim 16%, Sublime 8%,
  Neovim 6%); JetBrains' 2025 ecosystem survey reports PyCharm 49% and
  VS Code 42% among Python developers counting primary-or-secondary use.
- LSP4IJ (Red Hat's free LSP client for all JetBrains IDEs) supports
  **user-defined language servers with no plugin code**: a server is
  declared by command plus file mappings, and definitions can be exported,
  imported, and shipped as templates.
- Zed extensions declare a tree-sitter grammar by **repository URL plus git
  revision only**; no subdirectory field is documented. Helix's
  `languages.toml` grammar source **does** support `git` + `rev` +
  `subpath`. nvim-treesitter's rewritten main branch discovers parsers from
  a community registry and supports self-contained parser repos that carry
  their own queries.
- JetBrains web-types discovery is keyed off `package.json` (or bundled in
  an IDE plugin); no documented path exists for a Python-only project to
  register a web-types file. This demotes the web-types idea from a rung to
  a gated spike (section 6, rung 6).

Nothing else relevant was found in-tree: `packages/` holds only the Python
packages (`citry`, `citry_core`, `pygments_citry` under `packages/py/`),
there is no existing grammar artifact beyond the Pygments lexers, and no
editor extension code exists anywhere in the repo.

---

## 2. The bet, stated plainly

**Citry's users are spread across many editors, and citry has one
maintainer. Therefore the scarce resource is maintainer attention, and the
correct optimization is coverage per artifact, not depth per editor.**

Three facts drive everything below.

**Fact 1: the audience does not live in one editor.** Among Python
developers, VS Code holds roughly half as a main editor (48% in the 2024
Python Developers Survey), PyCharm a quarter (25%), and the rest is a long
tail (Neovim, Vim, Jupyter, Sublime, Helix, Zed) that sums to over a
quarter, with 80% of developers using more than one editor. A deep
VS Code-only experience writes off half the audience; and the second-largest
chunk, PyCharm, structurally cannot be won by depth at all, because deep
PyCharm integration means a second, JetBrains-native codebase (section 7).

**Fact 2: the field data says solo-maintainable editor tooling is
protocol-shaped and declarative.** Every sustained one-or-two-person tooling
story in the survey (templ, Herb, djls, Tailwind) ships a small number of
artifacts that existing ecosystems consume: a grammar, a server binary, thin
per-editor glue. Every expensive story (svelte2tsx, Volar's hybrid-mode
migration, vue-tsc's internals patching) is expensive precisely in the deep
layer: transforms, source maps, host-checker integration. Those are
permanent cost lines, not one-off builds
([`recon-framework-tooling-field.md`](recon-framework-tooling-field.md),
lessons 1 and 7; [`recon-vue-tooling.md`](recon-vue-tooling.md) 8.2).

**Fact 3: most of the perceived value is in the shallow features.** What
users notice day to day is "my editor colors my templates", "my editor knows
my components", and "typos are caught before render". The field recon's
central finding is that registry-backed completion and compile-time-style
validation deliver most of the perceived value with no type checker and no
deep analysis ([`recon-framework-tooling-field.md`](recon-framework-tooling-field.md),
lesson 2; Vetur delivered years of value on exactly metadata completion plus
structural diagnostics before any reliable type checking existed).

### The coverage-vs-depth trade, argued explicitly

What this design gives up, knowingly:

- **No typed `{{ user.name }}` completion or hover.** That requires the
  shadow-file design (compile templates to typeable Python, run the user's
  checker over it, map positions back). It is the single most expensive line
  item in the field data, it is gated on declared component interfaces (the
  Events typing work), and Python's checker landscape makes it strictly
  harder than the TypeScript version
  ([`recon-lsp-architectures.md`](recon-lsp-architectures.md) section 6;
  [`recon-vue-tooling.md`](recon-vue-tooling.md) 8.3.2).
- **No embedded CSS/JS language services in the server.** Templates' inner
  `<style>` and `<script>` regions get grammar-level coloring everywhere,
  and nothing deeper from citry initially.
- **No JetBrains-native (PSI-level) plugin.** PyCharm users get the LSP
  feature set, which is shallower than what a native plugin could do inside
  string literals.

What it buys with the effort saved:

- **Six-plus editors with real support** (VS Code and forks, PyCharm and
  the JetBrains family, Neovim, Zed, Helix, Sublime, plus any LSP-capable
  editor such as Emacs or Kate) instead of one polished editor.
- **A server small enough that its issue tail stays solo-manageable.**
  Diagnostics and name completion from a project index have no source maps
  to harden, no host checker to chase across releases, and no per-TS-version
  breakage class. templ's issue history shows where a proxy design bleeds
  (source-map robustness, proxied-server quirks); this design simply does
  not have those organs.
- **Forward compatibility with depth.** Every artifact here (the tree-sitter
  grammar, the index, the minimal server, the distribution pipeline) is a
  required substrate for the deeper designs. Depth can be added on top of
  coverage later; coverage cannot be recovered from a deep VS Code-only
  extension without doing this work anyway. The rungs do not have to be
  un-built if the project later chooses depth.

The honest counter-argument: if typed template expressions are the feature
that makes citry adoption tip (the way Volar arguably was for Vue's
TypeScript-era growth), then coverage-first delays the one thing that
matters. Section 9 states what evidence would demonstrate that and kill this
design.

---

## 3. Architecture

Five components. One is the canonical syntax artifact, one is the semantic
authority, one is the knowledge source, and two are thin delivery layers.

```
                 crates/citry_template_parser (exists)
                 Pest grammar, AST, TagRules, spans
                        |                \
                        | (crate link)    \ (taxonomy sync, validated in CI)
                        v                  v
   [2] citry-language-server        [1] tree-sitter-citry grammar
   Rust binary: LSP + `check`       grammar.js + scanner + queries
        |         \                     |         |        |
        |          \ (in-process,       v         v        v
        |           error tolerance)  Neovim     Zed     Helix
        v
   [3] project index
   static scan (ruff_python_parser)
   + optional `citry inspect --json`
        |
        v
   [4] thin editor glue                [5] TextMate + injection grammar
   VS Code ext, Zed ext, Mason,        VS Code base highlighting,
   Helix/Neovim configs, LSP4IJ        Sublime, JetBrains bundle
   template, Sublime package           (best-effort by design)
```

### 3.1 The tree-sitter grammar is the canonical syntax artifact

`tree-sitter-citry` describes citry-HTML (the `<c-*>` / `{{ ... }}` /
`{# ... #}` template language) once, in the format the largest number of
consumers can use directly:

- **Neovim, Zed, and Helix** consume it natively for highlighting,
  indentation, and structural editing; these editors have no other
  highlighting channel (Helix has no semantic tokens at all, Zed ships them
  off by default), so this artifact is the *only* way to reach them
  ([`recon-lsp-architectures.md`](recon-lsp-architectures.md) 4.2-4.3).
- **The language server embeds it in-process** as its error-tolerant parser
  for mid-keystroke documents, the proven pattern of htmx-lsp2 and
  jinja-lsp. This resolves the biggest engine-side gap (the Pest parser
  returns no partial tree,
  `crates/citry_template_parser/src/parser.rs:63-71` per the tooling recon)
  without touching the high-risk Pest grammar: the strict parser stays the
  authority whenever the document parses, and the tree-sitter tree carries
  completion and highlighting through the broken states.
- **GitHub** rendering is a longer-term side effect, not a promise: GitHub's
  highlighting service is tree-sitter-based where a grammar is registered
  with linguist, but linguist registration is traction-gated, and inline
  templates live in `.py` files that GitHub will keep highlighting as Python
  regardless. Filed under "later, if earned" (section 8).

Contents: `grammar.js`, an external scanner in C for raw-text regions
(`<c-raw>`, and robust `{{ ... }}` boundaries where expression values
contain braces, the exact case a TextMate grammar cannot handle,
`source_languages.md:402-409`), and query files (`highlights.scm`,
`injections.scm`, `indents.scm`) with per-editor variants where capture
conventions differ. Injections run both directions: the citry grammar
injects Python into `{{ ... }}` and `c-*` attribute expressions, CSS into
`<style>`, JS into `<script>`; and a shipped injection query for the
*Python* grammar marks `template` / `js` / `css` class-attribute strings as
citry-HTML/JS/CSS regions, which is how inline components light up in
editors that allow extending Python's injections (Neovim's `;; extends`
mechanism does; Zed and Helix are gated, see the coverage matrix and
falsifier F1).

**Where it lives.** Canonical source in the monorepo at
`packages/tree-sitter-citry/`, versioned and reviewed in the same PRs as the
Pest grammar it mirrors (the Astro lesson: tooling in the framework repo, so
the contract cannot drift,
[`recon-framework-tooling-field.md`](recon-framework-tooling-field.md)
lesson 5). Because Zed consumes grammars only as a repository URL plus git
revision (no subdirectory support, verified today), CI pushes a generated
read-only mirror repository (`citry-dev/tree-sitter-citry`, including the
generated `src/parser.c`) on each release; Zed, Helix, and the nvim registry
point at the mirror. Helix could point into the monorepo via `subpath`, but
pointing every consumer at the one mirror is simpler to reason about.

**The taxonomy-drift guard.** This grammar is the third hand-kept mirror of
the built-in tag taxonomy, after the two Pygments lexers
(`citry_html.py:29-33` mirrors `constants.rs:56`). Three mirrors is where
drift becomes a matter of time, so the same PR that adds the grammar adds a
validator to the repo check gate (`scripts/check.py` already runs custom
validators from `scripts/validators/`) that parses the built-in tag list out
of `constants.rs`, the Pygments lexers, and `tree-sitter-citry/grammar.js`
(and later the TextMate grammar) and fails when they disagree. Mechanical,
one afternoon, and it converts "keep the two in step" comments into an
enforced invariant.

### 3.2 The language server is minimal by contract, not by immaturity

A single Rust binary, `citry-language-server` (working name; crate at
`crates/citry_language_server/`), with two subcommands: `serve` (LSP over
stdio) and `check` (batch diagnostics for CI and pre-commit; same engine,
`vue-tsc`-style twin, [`recon-vue-tooling.md`](recon-vue-tooling.md) 8.1.5).

**Runtime choice: Rust, on the `lsp-server` scaffold.** Rationale, in
ecosystem-first terms: it links `citry_template_parser` directly (full AST,
spans, `TagRules`, no serialization boundary and no new binding surface); it
needs no runtime on the user's machine (a Node server is free only inside
VS Code and a real friction everywhere else, which is disqualifying for a
coverage design); Python/pygls would be the cheapest demo but the Django
ecosystem already ran that experiment and rewrote in Rust; and two reference
implementations (`ruff_server`, `ty_server`) are vendored in-tree to crib
document-store and dispatch structure from
([`recon-lsp-architectures.md`](recon-lsp-architectures.md) 3.1-3.5).
`tower-lsp-server` is the acceptable alternative if the async trait API
proves nicer during the spike; this is an ergonomics call, not an
architecture call.

**Feature set, fixed for v1:**

1. **Diagnostics.** Parse errors from the strict parser (its message quality
   and span precision are already good, per the tooling recon), plus
   component-aware validation using the parser's existing `TagRules`
   parameter (`parser_context.rs:31-62`) fed from the project index: unknown
   component tag, unknown attribute, missing required attribute, unknown or
   missing required slot fill. No new parser machinery; the diagnostics hook
   already exists and is data-driven.
2. **Completion.** Component tag names (`<c-Card>` from the index), the
   thirteen built-in tags, attribute names per component (from `Kwargs`),
   slot names inside a component's body (from `Slots`), and template
   variables already visible in scope (the AST's
   `used_variables` / `introduced_variables` tokens). Name completion, not
   type-aware completion.
3. **Navigation.** Go-to-definition from a `<c-*>` tag to the component
   class (the index knows the file and line), and definition/references for
   template variables within a template (the parser already links uses to
   the introducing node, `template_grammar.md` rule notes via the tooling recon).
4. **Document symbols** (components in a file, slots in a template), because
   they fall out of the index and the AST for free.

Explicitly *not* in the server: hover type information, embedded CSS/JS
services, formatting (issue #22 is its own track), rename, semantic tokens
in v1 (a cheap later add, standard token types only, since Helix cannot see
them and Zed defaults them off).

**Document model.** The server registers for citry template files and for
Python files. For Python files it locates embedded regions exactly, not by
regex: the vendored `ruff_python_parser` (already a workspace dependency,
root `Cargo.toml`) finds `Component` subclasses and their
`template` / `js` / `css` string attributes with offsets, the same
information the Tailwind server can only approximate with its
`classRegex` bug tail
([`recon-python-template-tooling.md`](recon-python-template-tooling.md)
section 8). Positions map back through the engine's offset machinery, which
exists internally and needs only a public entry point (punch-list item 4 in
the tooling recon).

**Error tolerance.** Embedded tree-sitter parse (section 3.1) plus the
last-good-tree pattern. The Pest parser is never asked to be something it is
not.

**Engine prerequisite.** Linking `citry_template_parser` into a standalone
binary requires feature-gating its PyO3 dependency
(`crates/citry_template_parser/Cargo.toml:12`, `#[pyclass]` on the AST
types). This is punch-list item 6 from the tooling recon, is also a
prerequisite for the planned JS bindings (#27), touches the repo's
highest-risk surface, and therefore goes through plan mode and the
cross-binding audit when implemented. It is rung 0 here.

### 3.3 The project index: static first, live registry as an upgrade

"What components exist, and what does each accept" is the knowledge that
turns a syntax server into a citry server.

- **Tier 1 (default, zero configuration): static analysis.** The server
  scans the workspace with `ruff_python_parser` for `Component` subclasses,
  reading `Kwargs` / `Slots` fields with types-as-written, template sources,
  and `*_lang` declarations. This covers the common case, needs no Python
  environment, and cannot break when the user's project does not import
  (djlsp's documented operational weakness,
  [`recon-python-template-tooling.md`](recon-python-template-tooling.md)
  2.1).
- **Tier 2 (opt-in): runtime introspection.** A `citry inspect --json`
  CLI command dumps the live registry (names, inputs, slots, file paths)
  by importing the user's `Citry` instance via the `[tool.citry]` pointer
  already designed in issue #23, executed with the project's own
  interpreter. This is the Laravel runtime-introspection trick, and it is
  the only way to see dynamically registered components. The server shells
  out to it when configured and merges results over the static tier,
  degrading gracefully when it fails. The command itself is core Python
  work and the natural first consumer of the component introspection API
  (issue #26); it is useful to scripts and CI independent of any editor.

The Rust-server-plus-thin-Python-agent split is exactly the shape
django-language-server proved
([`recon-lsp-architectures.md`](recon-lsp-architectures.md) section 10.6).

### 3.4 TextMate grammar: mandatory, derived, and deliberately best-effort

VS Code has no native tree-sitter highlighting (the 2018 issue remains
open), so a TextMate grammar is unavoidable for the largest single editor,
and the same artifact serves Sublime and the JetBrains TextMate-bundle
plugin for standalone template files. Two grammars ship in the VS Code
extension: the citry-HTML grammar, and an injection grammar targeting
`source.python` that marks `template` / `js` / `css` string bodies on
component classes and hands them to citry-HTML/JS/CSS scopes.

Policy: the TextMate grammar is a hand-derived transcription of the
tree-sitter grammar, kept intentionally simple. Known-approximate cases
(brace-heavy expressions) are accepted and documented; correctness lives in
the tree-sitter layer and, later, in server semantic tokens. This is the
two-tier highlighting model the Vue stack uses and `source_languages.md`
4.5 already sketches. The taxonomy validator (3.1) covers this grammar too.

This is not the marker-convention stopgap that `source_languages.md:367-377`
rejected: no typed aliases, no third-party fork to teach, no per-string
comments. It is stage two of the staged path that document records
(skeleton, grammar, server), shipped by citry's own extension.

### 3.5 Editor glue, one thin artifact each

- **VS Code:** one extension: language contribution, the two grammars, and
  an LSP client pointing at the bundled server binary. Published to both the
  Microsoft Marketplace and Open VSX (forks like Cursor and Windsurf default
  to Open VSX, and unclaimed names there are an active supply-chain risk, so
  claim early). Platform-specific vsix builds embed the right binary.
- **JetBrains (PyCharm first):** no plugin initially. Ship an **LSP4IJ
  user-defined server template** (a JSON definition: command, file mappings
  for Python files and template files), importable in any JetBrains IDE
  including Community editions, documented on the citry docs site. A thin
  official plugin (`LspServerDescriptor` + bundled binary + TextMate bundle)
  on the JetBrains Marketplace is a later rung once the server is stable,
  now that the native LSP API is free for all users (2025.2+) and
  open-sourced (2026.2 cycle).
- **Neovim:** grammar registered with the nvim-treesitter main-branch
  registry (the mirror repo is self-contained with queries), an
  `injections.scm` extension for Python via the documented `;; extends`
  path, a `vim.lsp.config` server definition upstreamed to nvim-lspconfig,
  and a Mason registry entry pointing at GitHub release archives.
- **Zed:** one small extension in the zed-industries/extensions registry:
  grammar by mirror-repo revision, queries, and a `language_server_command`
  that downloads the server from GitHub releases.
- **Helix:** a documented `languages.toml` snippet immediately; a PR to
  Helix's built-in `languages.toml` once the grammar and server are stable.
- **Sublime:** the TextMate grammar as a syntax package plus an `LSP-citry`
  helper on Package Control. Lowest priority; ships when trivially cheap.

### 3.6 Integration posture toward Pylance and PyCharm

The rule, taken verbatim from the Vue lineage's most expensive lesson: the
citry server **adds to** the host Python tooling and never replaces,
wraps, or patches it
([`recon-vue-tooling.md`](recon-vue-tooling.md) 8.2.1-8.2.2). Concretely:

- In VS Code, the citry server registers for `python` documents *alongside*
  Pylance, answering only citry-shaped requests (regions the index knows).
  This is the proven Ruff/Tailwind coexistence pattern; the two servers
  never coordinate. Interpreter discovery uses the Python extension's
  public environments API instead of home-grown venv probing.
- No Pyright fork, no Pylance feature race, no mypy plugin, no patching of
  any checker's internals.
- In PyCharm, citry arrives as one more LSP server, exactly like Ruff does.
  PyCharm's native Python intelligence is untouched.

---

## 4. Editor coverage matrix

What each editor gets, by milestone rung (section 6). "Inline" means
templates in `.py` strings; "file" means `template_file` templates.
Numbers in the "from rung" column refer to the ladder in section 6.

| Editor | Highlighting (file) | Highlighting (inline) | Diagnostics + completion | Citry ships | Channel | From rung |
|---|---|---|---|---|---|---|
| VS Code + forks (Cursor, Windsurf, VSCodium) | TextMate grammar | Injection grammar into `source.python` | Full v1 server feature set, inline and file | Extension (grammars + LSP client + binary) | Marketplace + Open VSX | R2 (color), R4 (server) |
| PyCharm / JetBrains | TextMate bundle (user-installed or later plugin) | None at first (see note A) | Full v1 server via LSP4IJ template; later thin plugin | LSP4IJ template JSON, TextMate bundle, later plugin | Docs page; JetBrains Marketplace later | R4 |
| Neovim (0.11+) | tree-sitter grammar | Python `injections.scm` extension (`;; extends`) | Full v1 server | Registry entry, queries, lspconfig def, Mason entry | nvim registry + Mason | R1 (color), R4 (server) |
| Zed | tree-sitter grammar via extension | Gated: extending Python's injections from an extension is unproven (falsifier F1) | Full v1 server (extension auto-downloads) | Zed extension | zed-industries/extensions | R1-R2 (color), R4 (server) |
| Helix | tree-sitter grammar | Gated, same as Zed (user-side query overrides exist) | Diagnostics + completion (no semantic tokens exist in Helix at all) | `languages.toml` snippet, later built-in PR | Docs, then Helix PR | R1 (color), R4 (server) |
| Sublime Text | TextMate-derived syntax | No (no injection mechanism worth maintaining) | Full v1 server via LSP package | Syntax package + LSP-citry | Package Control | R5 |
| Emacs, Kate, any LSP editor | Their own tree-sitter/TextMate consumption where available | Varies | Full v1 server (stdio binary on PATH via PyPI) | Nothing editor-specific; docs snippet | PyPI (`uv tool install`) | R4 |
| GitHub.com (read-only) | tree-sitter service after linguist registration (traction-gated) | Never (`.py` files stay Python) | n/a | linguist PR, eventually | github-linguist | R6, if earned |

**Note A (PyCharm inline highlighting).** JetBrains' TextMate bundle
mechanism only applies to file types no native plugin owns; `.py` belongs to
PyCharm's Python plugin, so no bundle can color inside Python strings. Inline
templates in PyCharm therefore get LSP diagnostics and completion but no
citry coloring until an official thin plugin adds injection support (a
deliberate later rung, and the one place this design accepts a visible gap
in its second-largest editor). PyCharm users can meanwhile use the IDE's own
`# language=HTML` injection by hand; citry documents that it exists but does
not ship or promote a marker convention, per the standing decision.

The structural summary: the server is the only write-once-run-everywhere
artifact; the grammar work splits the world into a TextMate half and a
tree-sitter half; and this design ships both halves precisely because
skipping either forfeits whole editors, while depth features benefit only
the editors that already work.

---

## 5. Languages, crates, and packages in the monorepo

| Artifact | Location | Language | New/exists |
|---|---|---|---|
| Template parser, AST, `TagRules` | `crates/citry_template_parser/` | Rust | exists |
| PyO3 feature gate (`python` cargo feature) | same crate | Rust | new, rung 0 |
| tree-sitter grammar + queries + scanner | `packages/tree-sitter-citry/` | JS (grammar DSL) + C | new |
| Grammar mirror repo (generated) | `citry-dev/tree-sitter-citry` (CI-pushed) | generated | new |
| Language server + `check` | `crates/citry_language_server/` | Rust | new |
| Server PyPI package (binary wheel) | `packages/py/citry_language_server/` | packaging only | new |
| `citry inspect --json` + introspection API | `packages/py/citry/` (CLI + core, issue #26) | Python | new |
| VS Code extension (grammars, client) | `packages/editors/vscode/` | TypeScript (thin) + JSON | new |
| Zed extension | `packages/editors/zed/` | Rust (thin, wasm) | new |
| LSP4IJ template, Helix/Neovim snippets | `packages/editors/configs/` + docs site | JSON/TOML/Lua | new |
| Sublime syntax + LSP-citry | `packages/editors/sublime/` | YAML/Python (thin) | new, last |
| Taxonomy validator | `scripts/validators/` | Python | new, with rung 1 |
| Pygments lexers | `packages/py/pygments_citry/` | Python | exists |

Everything is versioned and released in lockstep with citry from the
monorepo (the djls/ruff pattern; also the Astro lesson). The grammar mirror
is the one repository outside the monorepo, and it is generated, never
hand-edited.

---

## 6. Milestone ladder

Efforts are rough solo-maintainer estimates in focused weeks, calibrated
against the field data (templ: one maintainer, production proxy LSP; Herb:
one maintainer, parser-first year). Every rung ships user-visible value on
its own and no rung requires a later rung to be useful.

**R0. Engine prerequisites** (1-2 weeks). Feature-gate PyO3 in
`citry_template_parser` (punch-list item 6; plan mode, cross-binding audit);
expose the offset-aware parse entry (item 4); fix the whole-input-span wrap
on top-level grammar failures (item 3). Also useful to #27 independent of
this design. *Ships: nothing user-visible; unblocks everything.*

**R1. tree-sitter grammar** (3-5 weeks including the C scanner, injection
queries, a test corpus cross-checked against the Pest parser's judgments,
the taxonomy validator, and the mirror-repo CI job). *Ships: Neovim, Zed
(file templates), Helix (file templates) highlighting; the server's future
tolerant parser; a docs "editor setup" page.* The week-one spike inside this
rung is the F1 falsifier test: prove Python-string injection in Neovim, and
establish what Zed/Helix can and cannot do for inline strings.

**R2. VS Code extension, highlight tier** (2-3 weeks). TextMate citry-HTML
grammar transcribed from R1's decisions, the `source.python` injection
grammar, language contribution, publish to Marketplace + Open VSX (claim
names). *Ships: coloring for the single largest audience, inline and file.*

**R3. `citry inspect --json` and the introspection core** (1-2 weeks,
Python). The registry dump command over issue #26's API and issue #23's
`[tool.citry]` discovery. *Ships: a scripting/CI-usable component inventory;
the index's tier 2.*

**R4. The language server** (6-10 weeks). `lsp-server` scaffold cribbed from
the vendored `ruff_server`; document store; embedded-region location via
`ruff_python_parser`; static index; `TagRules`-driven diagnostics;
completions; go-to-component; `check` subcommand; PyPI wheels riding the
existing maturin matrix; GitHub release archives; wire into the VS Code
extension (platform vsix); Mason entry; Zed extension grows
`language_server_command`; LSP4IJ template; Helix and Neovim config
snippets. *Ships: diagnostics and component-aware completion in every
LSP-capable editor, and a CI check command.*

**R5. Long-tail polish** (2-3 weeks, interruptible). Sublime package,
semantic tokens (standard types only), Helix built-in PR, nvim-lspconfig
upstreaming, JetBrains thin plugin decision point. *Ships: the last
editors; better colors where supported.*

**R6. Evidence-gated extras** (spikes, days each, only on demonstrated
demand). Web-types emission (gated on a spike proving PyCharm consumes it in
a Python-only project; today's check says discovery is `package.json`-keyed,
so this likely dies); linguist registration (gated on real-world usage);
vscode.dev via a WASI build of the server (gated on anyone asking).

Total to full coverage (R0-R4): roughly 13-22 focused weeks, or 4-6 months
at solo part-time pace. Value ships from week 4 (R1) onward.

---

## 7. Distribution and packaging

- **Server binary: PyPI wheels first.** citry's audience has Python by
  definition; `uv tool install citry-language-server` (or a `citry[lsp]`
  extra) is the lowest-friction install and rides the maturin platform
  matrix the repo already operates for `citry_core`. This is the djls/ruff
  pattern and it neutralizes the "a Python server would already be in your
  venv" argument without a Python server's ceilings.
- **GitHub Releases archives** (cargo-dist-style) as the canonical URL
  source that the Mason registry, the Zed extension, and any future Homebrew
  formula download from.
- **VS Code: platform-specific vsix** embedding the binary (works offline
  and behind proxies), published to Marketplace and Open VSX on every
  release.
- **JetBrains: docs-first** (LSP4IJ importable template), Marketplace plugin
  later.
- **Version skew policy:** server, grammars, and extensions version in
  lockstep with citry releases from the monorepo tag. The server refuses
  ambiguity politely: if the project's installed citry major.minor is newer
  than the server's, it says so in one diagnostic rather than mis-parsing.
- **Name claims now, regardless of ladder position:** `citry` on Open VSX,
  Marketplace, Package Control, and crates.io are cheap to claim and
  expensive to lose (the January 2026 Open VSX supply-chain reports make
  unclaimed names an actual risk, per the architectures recon).

---

## 8. Maintenance cost, honestly assessed

The steady-state artifact inventory and what each costs a solo maintainer:

| Artifact | Change driver | Steady-state cost |
|---|---|---|
| tree-sitter grammar + queries | V3 syntax changes; editor query-convention drift | The big one. Every syntax change now touches Pest + tree-sitter + TextMate + two Pygments lexers. Mitigated by the CI taxonomy validator and by V3 stabilizing; not mitigated away. |
| TextMate grammar | Same syntax changes | Small; transcription of decisions already made in R1. |
| Language server | Editor LSP quirks, Windows paths/URIs, index edge cases | The templ data says this trickle is real but bounded: 68 LSP issues over a project lifetime, clustering in predictable buckets. This design deletes the two worst buckets (source-map robustness, proxied-server quirks) by not having those organs. Budget: a few issues per month once adopted. |
| VS Code extension | VS Code API drift (slow), marketplace churn | Low; the extension is grammars plus a client. |
| Zed extension, Mason entry, Helix/Neovim configs | Platform migrations (the nvim-treesitter main-branch rewrite is a live example) | Near-zero for months at a time, then an occasional forced migration. |
| LSP4IJ template / JetBrains plugin | JetBrains API evolution (the LSP client API is newly open-sourced and moving) | Near-zero for the template; the thin plugin, if built, adds a yearly-compat tax. |
| `citry inspect` + introspection API | citry's own API evolution | Ordinary core maintenance, shared with #26's other consumers (Storybook, Tailwind extension). |

Honest totals: after the build (section 6), expect **2-6 hours per week**
of tooling maintenance once there is real adoption, spiking around editor
platform migrations and citry syntax changes. The field calibration says
this is sustainable for one person *if and only if* the deep layers stay
out: every surveyed one-maintainer success (templ, Herb, djls) holds the
line at "grammar + server + thin glue", and every cost blowup in the record
(Vetur's duplicated ASTs, vue-tsc's internals patching, hybrid mode's
seven-month migration) lives in the layers this design refuses.

The single most concerning line is the grammar mirror set. Four-going-on-five
hand-synced representations of the token taxonomy is a real drift machine;
the CI validator reduces it to a build failure instead of a user bug report,
but each V3 syntax change still costs a coordinated multi-artifact PR.
That cost argues for the ladder's ordering (grammar work after the syntax
frontier calms) and is falsifier F4.

---

## 9. What this design deliberately does not build, and falsifiers

### 9.1 Not built, with reasons

1. **Shadow-file typed expression checking** (svelte2tsx / templ-proxy
   analogue). The premium feature and the permanent cost center; gated on
   declared component interfaces (the Events typing work) either way. This
   design keeps the door open (the compiler already emits Python; a source
   map slot in the compiler output contract is the one cheap reservation
   the final design should weigh regardless of which draft wins) but builds
   none of it. If depth wins later, it lands as new rungs on top of this
   substrate, not as a rewrite of it.
2. **A Volar.js-based Node server.** Its pull is JS-native embedded-language
   services, which this design does not offer anyway; its price is a Node
   runtime on every non-VS-Code editor (coverage poison) and a dependency on
   a single-digit-maintainer core one ecosystem away.
3. **Pylance/Pyright takeover, wrapping, forking, or patching.** The
   Vue lineage's clearest graves (takeover mode, vue-tsc). Coexistence only.
4. **A JetBrains-native PSI plugin.** A second codebase for one vendor,
   which even JetBrains stopped doing for Vue. The thin LSP plugin is the
   ceiling of planned JetBrains investment; PSI-level string injection is
   explicitly future-maybe.
5. **The formatter.** Separate track (#22), needs comment association in the
   AST, and is not on this design's critical path. `check` deliberately does
   not grow `--fix`.
6. **Error recovery inside the Pest parser.** The tree-sitter grammar is the
   tolerant layer; the strict parser stays strict. No multi-error collection
   work in `citry_template_parser` beyond what diagnostics quality needs.
7. **Embedded CSS/JS language services, Emmet, and Tailwind passthrough
   logic in the server.** Grammar-level coloring only, plus documentation
   for pointing `tailwindCSS.includeLanguages` at citry template files.
   Deeper delegation is a later decision, made once the server exists.
8. **Highlight-only marker conventions** (typed aliases, `# language=`
   shipping, third-party fork adoption). The standing decision in
   `source_languages.md:367-377` holds; everything here is citry's own
   staged grammar-then-server path.
9. **Semantic-token-dependent features.** Helix cannot render them and Zed
   defaults them off; nothing in this design's UX may require them.

### 9.2 Falsifiers: what evidence kills this design

- **F1 (inline injection reach).** If the R1 spike shows that only Neovim
  among the tree-sitter editors can inject citry into Python strings, and
  Zed/Helix additionally cannot get there via user-side query overrides,
  then tree-sitter's coverage dividend shrinks to file templates plus one
  editor, and the "canonical tree-sitter artifact" framing weakens to
  "server-internals plus Neovim". The design survives but the grammar drops
  below the VS Code extension in the ladder; if *additionally* `.py`-inline
  turns out to be the overwhelming authoring mode (it is the documented
  house style), the whole coverage bet loses to a VS Code-plus-PyCharm depth
  bet.
- **F2 (audience concentration).** If citry's actual users (Discord poll,
  extension install counts after R2, docs telemetry) concentrate 80%+ in
  VS Code plus PyCharm, then Neovim/Zed/Helix rungs were effort spent on
  nobody, and a depth design serving those two editors was the right call.
- **F3 (shallow completions rejected).** If post-R4 feedback consistently
  reads "nice, but I expected `{{ }}` to know my types" and adoption stalls
  on it, the minimal-LSP scoping was wrong and the shadow-file work was the
  actual table stakes. Measurable: feature-request issue clustering, users
  comparing citry unfavorably to Volar/svelte in public.
- **F4 (grammar churn).** If V3 syntax keeps changing at its current
  frontier pace into 2027, the multi-mirror grammar tax dominates and every
  grammar artifact should have waited. Measurable from the git log of
  `grammar.pest`: more than a couple of syntax-visible changes per quarter
  after R1 ships means this fired.
- **F5 (PyO3 gating blocked).** If feature-gating PyO3 out of the parser
  crate reveals deep coupling (rung 0 balloons past two weeks), the
  native-binary server premise cracks and the design must re-run the
  server-runtime decision (wasm-in-Node or Python fallback), which erodes
  its distribution story.
- **F6 (grammar fidelity).** If the tree-sitter grammar cannot classify the
  context-dependent cases correctly (a `c-*` attribute value that is an
  expression vs a nested template) and mis-injects Python where a template
  belongs, the "canonical syntax artifact" claim fails its own test corpus
  and the grammar demotes to best-effort coloring, same tier as TextMate.
- **F7 (LSP4IJ friction).** If the LSP4IJ import path proves too fiddly for
  ordinary PyCharm users (measured by setup-help issues), the thin JetBrains
  plugin moves from R5 to the critical path, adding its compat tax early.

---

## 10. Sources

Repo citations appear inline as `file:line`; the load-bearing ones are
`crates/citry_template_parser/src/{ast.rs,parser.rs,parser_context.rs,constants.rs}`,
`crates/citry_template_parser/Cargo.toml`,
`packages/py/citry/citry/{component.py,component_registry.py}`,
`packages/py/pygments_citry/pygments_citry/citry_html.py`,
`docs/design/source_languages.md`, `docs/design/extensions_roadmap.md`,
`TODO/project_status_june_2026.md`, and `scripts/check.py` /
`scripts/validators/`.

The five recon reports in this directory are the primary research base; all
their web claims were verified 2026-07-07 and are relied on here as cited
inline, including: server library status (`lsp-server`, `tower-lsp-server`,
pygls), VS Code's TextMate-only baseline, per-editor semantic-token support,
JetBrains LSP API licensing timeline, Open VSX growth and supply-chain
reports, Mason/Zed/Helix distribution mechanics, djls/djlsp feature sets,
Pyright's no-plugins position, templ/Svelte/Astro/Herb maintenance
statistics, and the Vue lineage history.

Fresh web checks made for this draft, accessed 2026-07-07:

- Python Developers Survey 2024 results (main editor: VS Code 48%, PyCharm
  25%, Neovim 4%, Vim 3%; 80% multi-editor):
  <https://lp.jetbrains.com/python-developers-survey-2024/>
- The State of Python 2025 (JetBrains ecosystem survey: PyCharm 49%,
  VS Code 42% among Python developers, primary-or-secondary):
  <https://blog.jetbrains.com/pycharm/2025/08/the-state-of-python-2025/>
- LSP4IJ user-defined language servers (no plugin required; templates,
  export/import):
  <https://github.com/redhat-developer/lsp4ij/blob/main/docs/UserDefinedLanguageServer.md>
- Zed language extensions (grammar = repository + rev; injections;
  `language_server_command`): <https://zed.dev/docs/extensions/languages>
- Helix languages.toml (grammar `git`/`rev`/`subpath`; language server
  declaration): <https://docs.helix-editor.com/languages.html>
- nvim-treesitter main-branch registry model (registry discovery,
  self-contained parser repos with queries):
  <https://github.com/nvim-treesitter/nvim-treesitter>,
  <https://neovim.io/doc/user/treesitter/>
- JetBrains web-types discovery is `package.json`-linked (basis for gating
  the web-types rung): <https://github.com/JetBrains/web-types>,
  <https://plugins.jetbrains.com/docs/intellij/polysymbols-web-types.html>,
  <https://youtrack.jetbrains.com/issue/WEB-40349>
