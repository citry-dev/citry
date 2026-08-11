# Recon: what citry already offers for IDE tooling

**Date: 2026-07-07.** Ground-truth sweep of citry's own tooling surface,
read from the actual source, feeding the IDE-integration design
([`../ide_integration.md`](../ide_integration.md)). Part of the
`ide_research/` corpus, which mirrors the structure of
[`../events_research/`](../events_research/README.md). Repo claims cite
`file:line`; web claims are listed in Sources with access dates.

Terms used throughout, defined once: **LSP** (Language Server Protocol) is
the editor-agnostic protocol a language server speaks to provide completion,
hover, go-to-definition, and diagnostics. **Pest** is the Rust parser
generator citry's template grammar is written in. **wasm** (WebAssembly) is
the portable binary format that lets Rust code run in browsers and Node.
**tree-sitter** is an incremental, error-tolerant parser framework editors
use for highlighting. **TextMate grammar** is the regex-based highlighting
format VS Code uses by default.

---

## 1. Summary of findings

- The Rust parser already produces almost everything a language server needs
  for a *valid* template: every AST node carries exact source spans, used and
  introduced variables are tracked per scope with positions, slots are
  collected with their required-ness, comments are collected at every level,
  and per-tag validation is user-configurable (`TagRules`), which is the
  natural hook for component-aware diagnostics.
- The big gaps are all about *invalid* or *changing* input: the parser is
  fail-fast (one error, no partial AST), has no error recovery for
  half-typed templates, no incremental reparse, and errors cross the Python
  boundary as flattened exception strings rather than structured positions.
- Templates live primarily *inside Python files* as multiline string class
  attributes. That is the defining constraint versus Vue/Svelte single-file
  components: an editor extension must first locate the embedded region in a
  `.py` file, then analyze it, then map positions back. The repo has already
  made the key decisions here (no highlight-only stopgap, `*_lang`
  declaration attributes, a curated rich-editing set) in
  [`source_languages.md`](../source_languages.md).
- The wasm/JS route to reusing the Rust parser is real but has one concrete
  blocker: the parser crate depends on PyO3 unconditionally, with `#[pyclass]`
  inline on every AST struct, and PyO3 does not build for the wasm target
  that `wasm-bindgen` uses. Feature-gating PyO3 is a mechanical but
  cross-cutting prerequisite. The other dependencies (Pest, Ruff's Python
  parser) are wasm-proven.

---

## 2. What the parser and AST can power today

### 2.1 Position data on every node

`Token` is the shared span type: `content`, `start_index`, `end_index`, and
`line_col` (`crates/citry_template_parser/src/ast.rs:20-35`). Every AST type
carries tokens for both its full span and its meaningful parts:

- `HtmlStartTag` / `HtmlEndTag`: whole-tag token plus a separate `name` token
  (`ast.rs:328-344`, `ast.rs:383-394`).
- `HtmlAttr`: whole-attribute token, `key` token, `value` (with quotes) and
  `inner_value` (without quotes) tokens, plus `quote_char`
  (`ast.rs:251-275`).
- `Expr` (a `{{ ... }}` expression): whole-expression token plus a `value`
  token for the inside (`ast.rs:426-439`).
- `Comment`: whole-comment token plus a delimiter-stripped `value` token
  (`ast.rs:182-189`).

This is enough to compute highlight ranges, hover targets, selection ranges,
and document symbols for any parsed template without re-lexing.

Two sharp edges for tooling:

- `line_col` is the *start* position only. An end line/col must be computed
  from `end_index` against the source text. Mechanical, but every consumer
  does it.
- Positions inside nested constructs are already in root-template
  coordinates: a nested template in a `c-*` attribute is parsed with a child
  context that accumulates line/col/index offsets
  (`crates/citry_template_parser/src/parser.rs:520-547`), and variable tokens
  found inside expressions are shifted the same way
  (`parser.rs:493-505`). So a tool never has to stitch coordinate systems
  together *within* one template string. (Mapping template coordinates into
  the enclosing `.py` file is a separate problem; section 4.)

### 2.2 Variable tracking, ready for go-to-definition

Each node records `used_variables` (free variables its subtree reads) and
`introduced_variables` (names it binds: `<c-for>` loop targets, `<c-fill>`
`data`/`fallback` handles), both as `Vec<Token>` with source positions
(`ast.rs:508-539`). Used variables are collected in source order in a `Vec`,
so ordering is stable (crate agent INDEX,
`crates/citry_template_parser/docs/agent/INDEX.md:89-93`). A node's own
introduced names are subtracted from its used set, so `Template.used_variables`
at the root is exactly "the inputs the caller must supply"
(`ast.rs:700-715`).

Crucially, the introduced names are *kept* on the node rather than discarded
after subtraction, precisely so a linter or language server can link a use of
a loop variable back to the `each` that defines it
([`template_grammar.md:399-405`](../template_grammar.md)). For Python expressions this
resolution is real parsing, not regex: the `LangImpl` for Python delegates to
`python_safe_eval`, which uses Ruff's Python parser and returns variable
tokens with adjusted ranges
(`crates/citry_template_parser/src/lang/python.rs:18-72`; pipeline summary in
the crate agent INDEX). Variable shadowing is forbidden at parse time
(template_grammar.md rule 10), which makes "same name means same variable" sound
within a template. Together this powers, today: go-to-definition and
find-references for template variables, "undeclared input" analysis, and
hover showing where a name comes from.

The GitHub issue for the LSP ([#23](https://github.com/citry-dev/citry/issues/23))
already records this design note, plus the config story for resolving
components (a `[tool.citry]` section in `pyproject.toml` pointing at the
project's `Citry` instance, the same `module:attribute` spec the CLI accepts).

### 2.3 Slots and component-shape data

`Template.slots` collects every statically-named `<c-slot>` with its name
token and a three-state `required` flag (`ast.rs:775-804`). At parse time,
`<c-fill>` names are checked for uniqueness, and against allowed/required
slot rules when the parser is given them (template_grammar.md rules 6 and 7). This is
the raw material for "missing required slot" and "unknown slot" diagnostics
in the parent template.

### 2.4 User-configurable validation: the diagnostics hook

`TagRules` is a per-tag rule set the caller passes into `parse_template`:
allowed attributes (with mutually-exclusive groups), required attributes,
allowed slot names, required slot names
(`crates/citry_template_parser/src/parser_context.rs:31-62`). It is exposed
to Python (`packages/py/citry_core/citry_core/_rust.pyi:364-377`) and
accepted as a `dict[str, TagRules]` by the Python `parse_template`
(`_rust.pyi:207-212`).

This is exactly the shape a language server needs: derive `TagRules` from
each registered component's `Kwargs`/`Slots` classes and the parser itself
validates `<c-Table bogus="1">` (unknown input) or a missing required input
at parse time (template_grammar.md rule 8). The engine-side rules for built-in tags
are data-driven in `constants.rs` the same way (crate agent INDEX,
`docs/agent/INDEX.md:100-102`), so component-aware diagnostics do not require
new parser machinery, only feeding the registry's knowledge into the
existing parameter.

### 2.5 Comments, collected but not associated

Comments (`{# ... #}` and `<!-- ... -->`) are collected with spans at every
level (`Template.comments`, `Node.comments`, `HtmlAttr.comments`,
`Expr.comments`), and template comments do not appear in the element tree
(`ast.rs:813-830`). That flat collection is sufficient for highlighting. The
*formatter* additionally needs a comment
association pass (attaching each comment to a neighboring node), which is
identified as the hard part of the formatter and does not exist yet
([#22](https://github.com/citry-dev/citry/issues/22)).

One stale doc to ignore: the `Template.comments` docstring says comments are
populated "only if comment collection is enabled during parsing"
(`ast.rs:818-819`), but no such flag exists anywhere in the parser
(`ParserContext` has no toggle, `parser_context.rs:92-103`). Collection is
always on. The implementation is authoritative here.

### 2.6 What Python sees today

The PyO3 surface registers `parse_template`, `compile_template`, all the AST
classes, `TagRules`, and the `HTML_VOID_ELEMENTS` constant under
`citry_core._rust.template_parser`
(`crates/citry_core_py/src/lib.rs:45-72`), mirrored in
`packages/py/citry_core/citry_core/_rust.pyi` and wrapped by thin Python
modules (`packages/py/citry_core/citry_core/template_parser/parse.py`,
`compile.py`). So Python-side tooling gets the full structured AST with
positions today, with no serialization step.

One exposure gap found: `HtmlAttr.kind` (the Static / Expression / Template
classification) has no `#[pyo3(get)]` (`ast.rs:267-268`), and accordingly
does not appear in the stub (`_rust.pyi:250-259`), even though the
`HtmlAttrKind` enum class itself is registered
(`citry_core_py/src/lib.rs:54`). Python tooling that needs to know whether an
attribute value is an expression or a nested template must currently
re-derive it (key starts with `c-`, value shape), duplicating parser logic.
A one-line getter would fix this.

### 2.7 Highlighting that already exists: the Pygments lexer

`pygments-citry` is built (unpublished): a Pygments lexer that highlights a
citry component *inside a Python file*, handing the `template` / `js` / `css`
triple-quoted bodies to HTML/JS/CSS sub-lexers, following the upstream
`pygments-djc` pattern ([`pygments_citry.md:1-12`](../pygments_citry.md)).
It is docs-oriented (code fences), not an editor foundation, but it is
working prior art for the "find the embedded region in Python source"
problem: it does so with token-level rules matching
`template|js|css = ("""...` at the start of the string body.

---

## 3. Diagnostics quality today, and what is missing for an editor

### 3.1 What an error looks like

`ParseError` is either `Syntax(pest::error::Error<Rule>)` or a plain
`Value(String)`; the helper `ParseError::from_span` builds a pest error from
any span plus a message (`crates/citry_template_parser/src/error.rs:26-41`).
Pest's error display renders the classic annotated snippet (line/col, the
offending line, a caret). All semantic validation errors are built this way
from accurate spans: unexpected or mismatched close tag
(`parser.rs:298-317`), unclosed
tag at end of input pointing at the *opening* tag (`parser.rs:173-188`),
expression parse failures pointing at the expression's span in the template
(`parser.rs:488-491`), attribute/fill/control-flow violations throughout the
validation functions (`parser.rs:1056-1500`). So message quality and
location precision are genuinely good for a batch compiler.

Two structural problems for an editor, though:

1. **A top-level grammar failure loses its structured position.** When the
   Pest grammar itself rejects the input, the error is re-wrapped with a span
   covering the *entire input*, and the real location survives only inside
   the formatted message text (`parser.rs:125-130`). The grammar is
   permissive (unmatched text falls through to the `text` rule), so this
   path is rarer than in most parsers, but it exists.
2. **The Python boundary flattens everything to a string.** `parse_error_to_py`
   maps errors to `SyntaxError` / `ValueError` with `e.to_string()`
   (`crates/citry_core_py/src/template_parser.rs:33-38`). No structured
   `start_index` / `end_index` / line / col fields cross the boundary. An LSP
   consuming the Python surface today would have to regex the position back
   out of the rendered message. A structured diagnostic type (span + message
   + a stable code) is a small, additive change to the contract, but it is a
   `#[pyclass]`-surface change and therefore goes through the cross-binding
   audit (CLAUDE.md Mechanism 4).

`CompileError` carries no position at all (`error.rs:5-11`); acceptable,
since compilation runs on an already-validated AST.

### 3.2 Fail-fast: one error, no partial AST

`parse_template` returns `Result<Template, ParseError>`
(`parser.rs:63-71`): the first error aborts, there is no error list, and no
AST is produced for a broken template. Validation is interleaved with tree
construction, so it also stops at the first violation. For a batch compile
this is fine; for an editor it means that while the user is mid-edit
(an unclosed `<div`, a half-typed `{{ expr`), the language server gets
*nothing*: no tree to highlight from, no variables to resolve, and exactly
one diagnostic. Editors expect the opposite: most of the time the buffer is
broken, and tooling must degrade gracefully.

### 3.3 No incremental parsing

Every parse is a full parse of the input string. Pest generates
non-incremental, non-error-recovering parsers by design; there is no
tree-edit or reuse machinery. In practice citry templates are
component-sized (a class attribute, not a 5000-line document), so a full
reparse per keystroke is very likely affordable; but no parse-latency
numbers exist in the repo, so this should be measured, not assumed, in the
design doc.

The already-recorded mitigation direction: ship a **tree-sitter grammar**
for citry-HTML alongside (or instead of) a TextMate grammar. Tree-sitter is
incremental and error-tolerant, and `source_languages.md` explicitly
identifies it as the natural way to get correct highlighting boundaries
(the `{{ {'a': {}} }}` brace problem) without waiting for the language
server ([`source_languages.md:402-417`](../source_languages.md)). The
division of labor that falls out: tree-sitter for the always-on,
error-tolerant syntax layer; the Pest parser as the authority for semantic
analysis and diagnostics when the template parses.

### 3.4 No serialized AST dump

The AST types derive only `Debug, PartialEq, Clone` (`ast.rs:21`,
throughout); `serde` is pinned in the workspace (`Cargo.toml:74`) but the
parser crate does not use it (`crates/citry_template_parser/Cargo.toml:7-18`).
So there is no JSON (or other) AST serialization: the only structured
consumer surface is the PyO3 object graph. A TypeScript extension host or a
non-Python tool has no way to read the AST today except by embedding the
parser (wasm, section 5) or shelling out to Python. If a stable dump format
is wanted, it must be designed (and versioned) deliberately, since the
compiler-output and `#[pyclass]` surfaces are already treated as high-risk
contracts (CLAUDE.md).

### 3.5 No public offset-aware parse entry point

The offset machinery for parsing a string that lives at an offset inside a
larger source exists and is exercised internally (child contexts for nested
templates, `parser_context.rs:117-135`; `Token::offset`, `ast.rs:149-169`),
but the public entry points always start from a zeroed context
(`parser.rs:91-109`); `parse_template_inner` is private (`parser.rs:114`).
For the embedded-in-Python case (section 4), a tool wants "parse this
template, reporting all positions in `.py`-file coordinates". Today it must
shift every token itself afterwards, or the crate exposes the offsets
publicly, a small additive API.

### 3.6 Missing tools, tracked

- **Formatter** ([#22](https://github.com/citry-dev/citry/issues/22)): not
  built; needs the comment-association pass (section 2.5); the old
  `v2_template_formatter.rs` notes are harvested into the issue, and the file
  itself is no longer in the tree.
- **LSP / linter** ([#23](https://github.com/citry-dev/citry/issues/23)):
  not built; issue carries the variable-inference notes and the
  `[tool.citry]` config design.
- **Syntax highlighting grammar / editor plugin**
  ([#24](https://github.com/citry-dev/citry/issues/24)): not built; scoped
  to a TextMate or tree-sitter grammar for citry-HTML plus the embedded
  blocks, shipped by the citry editor extension.

---

## 4. Templates inside Python files: the defining constraint

### 4.1 How components declare their sources

A component's three source bodies are class attributes, each inline or a
file path: `template` / `template_file`, `js` / `js_file`, `css` /
`css_file` (`packages/py/citry/citry/component.py:295-324`; setting both
members of a pair is a class-definition error, `component.py:142-145`).
House style mandates the inline form be a triple-quoted multiline string
(CLAUDE.md, "Component template / js / css are multiline strings"), and the
docs and examples are written that way. So, unlike Vue or Svelte where the
unit the editor opens *is* the component file, citry's primary authoring
surface is a Python file with up to three embedded foreign-language regions
per class, plus the file-based variant where the template is a sibling file
(the `table.py` + `table.html` layout, issue #23).

Consequences for an extension, in order of difficulty:

1. **`template_file` case, easy:** ordinary file association. The design
   docs use `.html` for templates in examples; nothing constrains the
   suffix (`assets.py` resolves any path,
   `packages/py/citry/citry/assets.py:134-147`).
2. **Inline case, the real work:** the extension must find the regions.
   Static analysis of the Python AST is sufficient (find `template = "..."`
   string assignments on classes; `pygments-citry` already does a
   token-level version of this), and the `*_lang` attribute (see below) is
   readable from the same AST. The editor-side model for this is the
   virtual-document / embedded-language approach (Volar.js-style: map the
   string body to a virtual template document, forward LSP requests, map
   positions back), already identified in
   [`source_languages.md:334-338, 379-441`](../source_languages.md).
3. **Semantic layer:** resolving `<c-table>` to its component class needs
   the project's component registry, which is runtime state; issue #23's
   answer is the `[tool.citry]` pointer to the `Citry` instance plus
   directory scanning.

### 4.2 Decisions already taken (do not re-litigate in the design doc)

`source_languages.md` (status 2026-07-01, "design agreed") settles several
questions this research would otherwise reopen:

- **Language declaration** is `template_lang` / `js_lang` / `css_lang`
  string attributes, default `None` = infer; the django-components
  `Annotated[str, types.html]` alias approach was examined and rejected
  (never read at runtime upstream, import-heavy, not a portable highlight
  key) (`source_languages.md:65-137`).
- **No interim highlight-only stopgap.** citry will not teach the
  `python-inline-source` fork (the maintainer's own
  `jurooravec.python-inline-source-2`) to recognize components, and ships no
  typed aliases; the editor investment goes directly into the full
  extension + language server (`source_languages.md:367-377`). PyCharm's
  injection mechanism (`# language=HTML` comments) is likewise noted as
  non-portable (`source_languages.md:288-301`).
- **The rich-editing set is curated and smaller than the compile set:**
  citry-HTML (citry's own service), delegated CSS and JS services, plus
  deliberate per-dialect plugins; a custom `*_lang` gets highlighting at
  most (`source_languages.md:340-346, 471-484`).
- **The build path is staged:** extension skeleton, then grammar
  (highlighting), then language server (intelligence), each layer shipping
  on its own (`source_languages.md:425-441`).

The IDE design doc should treat these as inputs and go deeper only where
`source_languages.md` stops: the concrete LSP architecture (process model,
parser reuse, the Python-registry bridge), which that doc leaves open
("VS Code first, and whether to build the language server on Volar.js ...",
`source_languages.md:565-568`).

### 4.3 Adjacent infrastructure worth knowing about

- **Hot reload is built:** a host-neutral pluggable watcher
  (`citry.reload`, `watchfiles` / `watchdog` / poller backends), the
  `citry watch` command, and the `Citry.invalidate_file` /
  `invalidate_all` primitives over a reverse index mapping resolved file
  paths to the component classes that loaded them
  ([`hot_reload.md:1-18, 43-56`](../hot_reload.md)). An LSP normally relies
  on editor file events rather than its own watcher, but the reverse index
  is a ready-made "which components does this file belong to" map for a dev
  server or for cross-file invalidation of analysis caches.
- **The compiler output format is a documented contract** (module docstring
  of `compiler.rs`, summarized in the crate agent INDEX): tooling like a
  formatter must be built on the *AST*, not the compiled string, and the
  crate's test style for exact-output assertions (observe-then-lock,
  `crates/citry_template_parser/AGENTS.md:40-41`) applies to formatter
  tests too.

---

## 5. The wasm / JS-binding angle for an LSP

### 5.1 What is planned

JS/TS bindings are planned but not started: issue
[#27](https://github.com/citry-dev/citry/issues/27) records the mechanism
survey (JS/TS via `wasm-bindgen` + `wasm-pack`, with `--target web` vs
`--target nodejs` builds; PHP/Go via C ABI). `packages/` contains only `py`.
Note the two distinct roles a JS binding could play:
(a) a *host binding* for rendering citry in JS apps (issue #27's framing,
which also needs real `LangImpl` expression parsing for JS), and (b) a
*tooling vehicle*: running the existing parser, with the Python `LangImpl`,
inside an editor extension or language server. Role (b) does not need any
`lang/js.rs` work at all; it parses Python-flavored templates for Python
projects, just from a JS process.

### 5.2 The one concrete blocker: PyO3 in the parser crate

`citry_template_parser` depends on `pyo3` unconditionally
(`crates/citry_template_parser/Cargo.toml:12`), and the `#[pyclass]` /
`#[pymethods]` attributes sit directly on the AST structs
(`ast.rs:8, 20, 37`, throughout) and on `TagRules`
(`parser_context.rs:31, 64`). PyO3 supports the
`wasm32-unknown-emscripten` target (the Pyodide use case) but not
`wasm32-unknown-unknown`, which is what `wasm-bindgen` / `wasm-pack`
compile for (see Sources; the pyodide/PyO3 material is explicit that
emscripten is the supported wasm story). The workspace also pins pyo3 with
`features = ["extension-module"]` (`Cargo.toml:20`), i.e. the crate is
built to live inside a Python process.

So the prerequisite for any wasm build (and, likely, for linking the crate
into a standalone native LSP binary) is making the Python surface optional:
a `python` cargo feature gating the pyo3 dependency and turning every
`#[pyclass]` into `#[cfg_attr(feature = "python", pyclass)]` plus gating the
`#[pymethods]` blocks. Mechanical, but it touches every AST type, which is
the repo's highest-risk surface (CLAUDE.md high-risk areas), so it needs the
prior-art header and plan-mode treatment when it happens.

The rest of the dependency tree is wasm-friendly: Pest is pure Rust;
`ruff_python_parser` and `ruff_python_ast` (the expression layer, vendored
as workspace path deps, `Cargo.toml:29-38`) demonstrably compile to wasm,
since Astral ships `ruff_wasm` to npm (`@astral-sh/ruff-wasm-web`) and the
Ruff playground runs the same parser in the browser; `quick-xml`, `regex`,
`thiserror`, `lazy_static` are all wasm-clean pure Rust.

### 5.3 Delivery options for the language server, with what each costs

Laying out the option space (recon, not a recommendation):

1. **Native Rust LSP binary** (rust-analyzer model): reuses the parser crate
   directly at full speed; requires the pyo3 feature-gating above, plus
   per-platform binary distribution. The Python-side registry bridge
   (resolving components, Kwargs/Slots schemas) still needs a channel to a
   Python process or a static-analysis fallback.
2. **wasm language server inside the VS Code extension:** VS Code officially
   supports LSP servers compiled to WASI Preview 1 via the
   `ms-vscode.wasm-wasi-core` extension and the `@vscode/wasm-wasi-lsp`
   module (GA'd via the 2024 VS Code wasm blog series; see Sources). Same
   pyo3 prerequisite; distribution is trivial (the wasm file ships in the
   extension) and it works in vscode.dev, at some performance cost and with
   WASI sandbox constraints.
3. **wasm-bindgen npm package** consumed by a Node-based LSP written in
   TypeScript: the parser becomes a library call; the server logic
   (documents, virtual docs for Python embedding, config) lives in TS, which
   is the most natural language for VS Code extension authors. Same pyo3
   prerequisite. This doubles as the seed of the eventual JS host binding's
   tooling story (#27).
4. **Python LSP (pygls-style) on the existing `citry_core` binding:** zero
   Rust work today; full structured AST already available (section 2.6);
   trivially reuses the live component registry (import the user's `Citry`
   instance, derive `TagRules`). Costs: requires a Python environment for
   the editor tooling (users of the framework have one by definition), and
   the structured-diagnostics gap (section 3.1) plus the `HtmlAttr.kind`
   gap (section 2.6) must be fixed in the PyO3 surface first.

A hybrid is common in practice (tree-sitter grammar for the syntax layer in
any case; the semantic server in whichever runtime wins the registry-access
argument). The design doc should decide primarily on: where the component
registry lives (Python), how much of the analysis needs it, and whether the
first shipped milestone is grammar-only (per `source_languages.md` staging).

---

## 6. Punch list distilled for the design doc

Parser/AST work that IDE tooling would need from the engine side, smallest
first:

1. Expose `HtmlAttr.kind` to Python (one `#[pyo3(get)]`, plus stub line)
   (`ast.rs:267-268`).
2. Structured diagnostics across the PyO3 boundary: error class carrying
   span indices and line/col, not just a formatted string
   (`citry_core_py/src/template_parser.rs:33-38`).
3. Fix the whole-input-span wrap on top-level grammar failures so the
   structured position survives (`parser.rs:125-130`).
4. Public offset-aware parse entry (expose the existing `ParserContext`
   offsets) for parsing templates embedded in `.py` files in host-file
   coordinates (`parser.rs:114`, `parser_context.rs:117-135`).
5. Multi-error collection and/or error-tolerant parsing (a real design
   problem under Pest; the pragmatic split is tree-sitter for the tolerant
   syntax layer, Pest parser for authoritative diagnostics).
6. Feature-gate pyo3 in `citry_template_parser` to unlock wasm and native
   binary reuse (`Cargo.toml:12`, all `#[pyclass]` sites).
7. Correct the stale `Template.comments` docstring while touching the AST
   (`ast.rs:818-819`).

None of these are speculative: each maps to a specific LSP feature
(diagnostics, embedded documents, editor-cadence reparse, distribution).

---

## Sources

Repo sources are cited inline as `file:line` above; the load-bearing ones:
`crates/citry_template_parser/src/{ast.rs,parser.rs,parser_context.rs,error.rs,lib.rs}`,
`crates/citry_template_parser/{Cargo.toml,AGENTS.md,docs/agent/INDEX.md}`,
`crates/citry_core_py/src/{lib.rs,template_parser.rs}`,
`packages/py/citry_core/citry_core/_rust.pyi`,
`packages/py/citry/citry/{component.py,assets.py}`,
`docs/design/{template_grammar.md,source_languages.md,hot_reload.md,pygments_citry.md}`,
and GitHub issues
[#22](https://github.com/citry-dev/citry/issues/22),
[#23](https://github.com/citry-dev/citry/issues/23),
[#24](https://github.com/citry-dev/citry/issues/24),
[#27](https://github.com/citry-dev/citry/issues/27) (read via `gh`,
2026-07-07).

Web sources (all accessed 2026-07-07):

- PyO3 wasm support is emscripten-targeted (Pyodide), not
  `wasm32-unknown-unknown`:
  [PyO3 issue #2412, wasm32-emscripten support](https://github.com/PyO3/pyo3/issues/2412);
  [Pyodide blog: Rust/PyO3 support in Pyodide](https://blog.pyodide.org/posts/rust-pyo3-support-in-pyodide/);
  [maturin PR #974, add wasm32-unknown-emscripten target](https://github.com/PyO3/maturin/pull/974).
- Ruff's parser runs in the browser via wasm (so citry's expression layer is
  wasm-proven):
  [ruff_wasm crate](https://github.com/astral-sh/ruff/blob/main/crates/ruff_wasm/src/lib.rs);
  [@astral-sh/ruff-wasm-web on npm](https://www.npmjs.com/package/@astral-sh/ruff-wasm-web);
  [Ruff contributing docs (playground architecture)](https://docs.astral.sh/ruff/contributing/).
- VS Code supports language servers compiled to WASI:
  [VS Code blog: Using WebAssembly for extension development, part two (wasm LSP)](https://code.visualstudio.com/blogs/2024/06/07/wasm-part2);
  [ms-vscode.wasm-wasi-core extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode.wasm-wasi-core);
  [microsoft/vscode-wasm](https://github.com/microsoft/vscode-wasm).
- Referenced from `source_languages.md` (surveyed there, dates as of that
  doc, 2026-07-01): Volar.js embedded languages, tree-sitter, VS Code
  TextMate/semantic-token guides; URLs listed in
  [`../source_languages.md`](../source_languages.md) section 9.
