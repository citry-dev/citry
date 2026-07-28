# Citry - Project Status Report (June 2026)

This document captures the full state of the Citry project as of June 2, 2026,
after approximately 4 months of inactivity (last code work: Feb 5–6, 2026).
Its purpose is to allow anyone (including future-you) to resume work without
re-reading the entire codebase.

> **Refreshed 2026-06-22.** The snapshot above is June 2; the three weeks since
> built the entire Python runtime and moved the active work to it. Shipped in
> that window: slots/fills, provide/inject, the dependencies system (JS/CSS,
> per-instance vars, the cache API, `Script`/`Style`, `<c-js>`/`<c-css>`, the
> browser client), dynamic `<c-component>`/`<c-element>`, Vue-like class/style
> attributes, the Const optimization, `on_render` + error bubbling,
> `Component.ancestors`, and web integrations (Django, FastAPI, Flask,
> Starlette, WSGI, ASGI). The V3 parser is wired to Python and stable; 1,126
> Python tests pass; the benchmark renders the full suite at ~1.29x a bare
> Django template. Sections 5, 8, and 9 are refreshed below, and 9.5 covers
> performance; the live detail lives in `docs/design/`. Some older sub-sections
> (4, 6) still describe the parser-frontier era and lag behind this.

---

## 1. What is Citry

Citry is a **universal, cross-language HTML templating engine**. It brings
Vue/React-style component syntax to Python, JS/TS, PHP, Go, and Rust - all
powered by a single Rust core. The name stands for "Component tree."

Citry was forked from
[django-components/djc-core](https://github.com/django-components/djc-core) on
Dec 19, 2025 (commit `49e20dc`). The goal is to evolve djc-core's template
parser into a standalone, Django-independent templating engine.

**Key design principles:**

- **Rust as source of truth** - all parsing, AST, compilation lives in Rust
- **Thin language bindings** - Python via PyO3/maturin, future: JS via
  wasm-bindgen, PHP/Go via C FFI
- **13 built-in tags** - `<c-if>`, `<c-elif>`, `<c-else>`, `<c-for>`,
  `<c-empty>`, `<c-slot>`, `<c-fill>`, `<c-component>`, `<c-element>`,
  `<c-provide>`, `<c-css>`, `<c-js>`, `<c-raw>`
- **2 simple rules** - `<c-*>` tags are components, `c-*` attributes are dynamic

The root `README.md` is the **north star specification** for what Citry should do.

---

## 2. Template syntax versions (V1/V2/V3)

These are **template syntax versions**, not project versions. They describe how
templates are parsed and what syntax is allowed. Defined in
`crates/citry_template_parser/README.md` and upstream django-components issues
[#1499](https://github.com/django-components/django-components/issues/1499),
[#1141](https://github.com/django-components/django-components/issues/1141),
[#1004](https://github.com/django-components/django-components/issues/1004).

| Version | Syntax | Status in Citry |
|---------|--------|-----------------|
| **V1** | Django-compatible. Only `{% component %}` tags use extended syntax (lists, dicts, spreads, Python expressions). Everything else is standard Django. | Fully implemented in djc-core (upstream). Code exists in citry as `old_tag_parser_string.rs`, `old_tag_compiler.rs` tests. |
| **V2** | Entire template uses extended syntax, but keeps `{% %}` delimiters. All tags must be `BaseNode` subclasses. Enables linting, variable tracking, static section detection. | Partially implemented in djc-core. Citry has the V1→V2 tag parser/compiler (commented out in Python bindings). |
| **V3** | Drops Django syntax entirely. Uses HTML-like `<c-*>` tags, `c-*` attributes, `{{ expr }}`, `{# comments #}`. No filters, no translations, no `{% %}`. | **This is what Citry is building.** Active implementation in `citry_template_parser`. |

**Migration path** (from upstream issue #1499):
`djc_v1 → djc_v2 → djc_v3 → citry_v1`

### About the `v2_*.md` files

The files prefixed `v2_` in `crates/citry_template_parser/` are **working
notes and brainstorming docs** for "the next version," NOT specifications tied
to V2 specifically. They contain a mix of:

- Confirmed decisions (e.g., `v2_spec.md` on `c-*` attribute semantics)
- Design explorations (e.g., `v2_jsx.md` on PYX/JSX-in-Python)
- Research notes (e.g., `v2_cross_lang.md` on FFI patterns)
- Rejected ideas (e.g., `v2_rejected_ideas.md`)

**Not everything in these docs should be implemented.** Use the root `README.md`
and the staged code as the source of truth.

---

## 3. Repository structure

```
citry/
├── crates/                          # Rust workspace crates
│   ├── citry_core_py/               # PyO3 glue - exposes Rust to Python
│   ├── citry_html_transform/        # HTML attribute transformer (quick-xml)
│   ├── citry_template_parser/       # V3 template parser (stable; frontier moved to the runtime)
│   └── python_safe_eval/            # Sandboxed Python expression transformer (ruff)
├── packages/
│   └── py/
│       └── citry_core/              # Python package (PyPI: citry_core v1.3.0)
│           ├── citry_core/
│           │   ├── html_transform/  # Python wrapper for HTML transformer
│           │   ├── safe_eval/       # Python sandboxed eval (420 lines)
│           │   └── template_parser/ # Python wrapper for template parser (WIP)
│           └── tests/
├── third_party/rust/ruff/           # Git submodule - ruff Python parser
├── docs/                            # Project documentation
├── scripts/                         # check.py, validate.py, validators/
├── .github/workflows/               # CI: repo--check, rust--tests, py--tests, publish
├── Cargo.toml                       # Rust workspace config
├── pyproject.toml                   # Root tooling config (NOT releasable)
└── README.md                        # THE NORTH STAR SPECIFICATION
```

---

## 4. Crate-by-crate status

### 4.1 `python_safe_eval` - Stable

Transforms Python expressions into sandboxed form by rewriting the AST.
Uses ruff's Python parser internally. ~400 lines of Rust, 3 test files.

- `foo(1)` → `call(foo, 1)`
- `obj.attr` → `attribute(obj, "attr")`
- `obj[key]` → `subscript(obj, key)`

No pending work. Used by both `safe_eval` Python module and `citry_template_parser`.

### 4.2 `citry_html_transform` - Stable

Adds/modifies attributes on HTML root/all elements using quick-xml.
~200 lines of Rust, 1 test file.

No pending work. Thin wrapper exposed to Python.

### 4.3 `citry_template_parser` - stable and feature-complete

(2026-06-22: this was "THE MAIN WIP" at the snapshot; the parser is now
feature-complete and stable, and the active work has moved to the Python
runtime and performance. The file-level detail below is still accurate.)
It implements the V3 template parser: Pest grammar -> AST -> Compiler (code
generation).

**Source code stats:**

| Component | Lines | Status |
|-----------|-------|--------|
| `grammar.pest` | 389 | Complete for current feature set |
| `ast.rs` | 843 | Complete - Token, Node, HtmlStartTag/EndTag, Template, Expr, Comment, etc. |
| `parser.rs` | 2,560 | Complete - `parse_template()` with tag stack, components, control flow, slots, fills |
| `compiler.rs` | 1,651 | Complete - generates language-specific source code from AST |
| `constants.rs` | 286 | Complete - tag names, validation rules, void elements |
| `error.rs` | 61 | Complete - ParseError enum |
| `parser_context.rs` | 242 | Complete - ParserContext with configurable tag rules |
| `lang/*.rs` | 1,442 total | Python (314), JS (176), PHP (147), Go (278), Rust (338), trait (189) |
| `utils/pest.rs` | 26 | Complete |
| **Tests** | 5,847 | 16 test files + common helpers (447 lines) |

### 4.4 `citry_core_py` - Glue crate

This is the PyO3 module that exposes Rust to Python. It registers three
submodules of `_rust`, all active and wired to Python:

- `template_parser` - `parse_template` / `compile_template`, the V3 AST classes,
  and `TagRules`. Returns a `Template` AST (`Node`, `HtmlStartTag`, `Expr`, ...).
- `html_transform` - `mark_html` and `transform_html`.
- `safe_eval` - the sandboxed expression evaluator.

Keep this list in step with the
[`_rust.pyi`](../packages/py/citry_core/citry_core/_rust.pyi) stub.

---

## 5. Python package status

Two Python packages live under `packages/py/` (this section was rewritten on
the 2026-06-22 refresh; the old text described the V3 parser as not yet wired,
which is obsolete).

### `citry_core` (the Rust bindings) - v1.3.0 on PyPI

Thin Python over the Rust crates, built with maturin as `citry_core._rust`:

- `citry_core.template_parser` - `parse_template` / `compile_template` plus the
  V3 AST classes. Wired and stable (the PyO3 glue registers it; the earlier
  "commented out" note and the CLAUDE.md gotcha about it are both stale).
- `citry_core.html_transform` - `mark_html` (the serialize-time marker scan) and
  `transform_html`.
- `citry_core.safe_eval` - the sandboxed expression evaluator (`safe_eval`
  transforms an expression into safe code in Rust via the `python_safe_eval`
  crate; the per-eval intercepted ops and error context are Python).

### `citry` (the runtime) - v0.1.0 on PyPI, the live frontier

Published to PyPI as `citry` 0.1.0, versioned and released independently of
`citry_core` (see the release process in
[`docs/codebase.md`](../docs/codebase.md)). Still the live frontier: this is
where active development continues.

The high-level engine that consumes the compiler output. Public surface includes
`Citry`, `Component`, `Const`, `Extension`, and the compiled node classes
(`ComponentNode`, `ExprNode`, `IfNode`, `ForNode`, `FillNode`,
`ElementAttrsNode`, ...). Shipped: the full render + serialize pipeline,
slots/fills with compile-time validation (Pydantic-aware), provide/inject, the
dependencies system (JS/CSS, per-instance vars, the cache API, `Script`/`Style`,
`<c-js>`/`<c-css>`, the browser client, render strategies), dynamic
`<c-component>`/`<c-element>`, Vue-like class/style attributes, the `Const`
render-caching optimization ([`docs/design/component_constness.md`](../docs/design/component_constness.md)),
`on_render` + error bubbling + `ErrorFallback`, `Component.ancestors`, and web
integrations (`citry.contrib.{django,fastapi,flask,asgi,wsgi}`).

**1,126 Python tests pass** across both packages (was 310 at the June 2
snapshot). The old V1/V2 `_test_template_parser__*` files have been superseded
by the V3 suite.

---

## 6. What the V3 parser implements

### 6.1 Grammar (`grammar.pest`)

The Pest grammar handles these template elements (in precedence order):

1. HTML comments (`<!-- ... -->`)
2. HTML directives (`<!DOCTYPE ...>`, `<![CDATA[...]]>`)
3. Processing instructions (`<?...?>`)
4. Raw blocks (`<c-raw>...</c-raw>`)
5. HTML tags (start, end, self-closing)
6. Template expressions (`{{ ... }}`)
7. Template comments (`{# ... #}`)
8. Plain text

HTML attributes support:
- Static: `class="foo"`, `class='foo'`, `disabled`
- Unquoted: `class=foo`
- Double and single quoted values

### 6.2 Parser (`parser.rs`)

`parse_template()` builds a tree using a tag stack. Key features:

- **Component detection** - Any tag starting with `c-` (except reserved names)
  is treated as a component
- **Control flow grouping** - `<c-if>/<c-elif>/<c-else>` and
  `<c-for>/<c-empty>` must form valid groups (validated)
- **Control flow as attributes** - `<div c-if="x">` is syntactic sugar for
  `<c-if cond="x"><div>...</div></c-if>`
- **`c-*` attribute classification:**
  - `c-bind="expr"` → spread attributes (HtmlAttrKind::Expression)
  - `c-class="expr"` → dynamic attribute (HtmlAttrKind::Expression)
  - `c-body="<div>...</div>"` → nested template (HtmlAttrKind::Template)
  - Heuristic: if value starts with `<tag...` and ends with `</tag>`, it's a
    template; otherwise it's an expression
- **Fragment support** - `<>...</>` for multi-root nested templates
- **Variable tracking** - `used_variables` and `introduced_variables` tracked at
  every level (tag, section, template)
- **Slot detection** - `<c-slot>` tags with static names are collected in
  `template.slots`
- **Fill validation** - `<c-fill>` only inside components, no mixing with
  non-fill siblings, unique names enforced
- **Void element handling** - `<br>`, `<img>`, etc. auto-close
- **Multi-language expressions** - `Lang` trait with Python, JS, PHP, Go, Rust
  implementations. Python uses `python_safe_eval`'s ruff integration for
  variable extraction.

### 6.3 Compiler (`compiler.rs`)

`compile_template()` converts the AST into language-specific source code.
It generates a function body that returns a list of node objects:

| Node type | Rust constant | What it compiles to |
|-----------|--------------|-------------------|
| Plain text | (inline string) | `"""Hello, world!"""` |
| `{{ expr }}` | `EXPR_NODE` | `ExprNode(source, (start, end), """expr""", ("var1",))` |
| `<div>` | `HTML_NODE` | Opening/closing tags with attributes |
| `<c-MyComp>` | `COMPONENT_NODE` | `ComponentNode(source, (start, end), attrs, body)` |
| `<c-if>` | `IF_NODE` | `IfNode(source, (start, end), branches)` |
| `<c-for>` | `FOR_NODE` | `ForNode(source, (start, end), targets, iterable, body, empty_body)` |
| `<c-slot>` | `SLOT_NODE` | `SlotNode(source, (start, end), name, attrs, body)` |
| `<c-fill>` | `FILL_NODE` | `FillNode(source, (start, end), name, data_var, default_var, body)` |
| Static attr | `STATIC_ATTR_NODE` | `StaticHtmlAttr(key, value)` |
| Expr attr | `EXPR_ATTR_NODE` | `ExprHtmlAttr(key, source, (start, end), expr, vars)` |
| Template attr | `TEMPLATE_ATTR_NODE` | `TemplateHtmlAttr(key, body)` |

The compiler also handles:
- **Control flow attribute unwrapping** - `<div c-if="x" c-for="y in z">` is
  first expanded to nested `<c-if>` / `<c-for>` nodes before compilation
- **Priority ordering** - IF group has higher priority than FOR group
- **Boolean normalization** - `key=""` and `key=''` compile as boolean `True`
- **Void element rendering** - `<br>` stays as `<br/>`, `<div/>` expands to
  `<div></div>`

### 6.4 Multi-language support

The `Lang` trait (`lang/lang.rs`) defines the interface for language-specific
expression handling. Each implementation provides:

- `parse_expression()` - Parse an expression string and return used/assigned
  variables
- `parse_forloop_expression()` - Parse `<c-for each="x in items">` syntax
- `compile()` - Convert `LangSpecArgument` list into source code string

| Language | File | Expression parsing | Code generation |
|----------|------|-------------------|-----------------|
| Python | `lang/python.rs` | Via `python_safe_eval` (ruff) - full variable tracking | Generates Python function source |
| JavaScript | `lang/js.rs` | Stub - regex-based variable extraction | Stub |
| PHP | `lang/php.rs` | Stub - regex-based variable extraction | Stub |
| Go | `lang/go.rs` | Stub - regex-based variable extraction | Stub |
| Rust | `lang/rust.rs` | Stub - regex-based variable extraction | Stub |

Only Python has full implementation. Other languages have structural stubs that
extract variables via regex heuristics but don't do real parsing.

---

## 7. Test infrastructure

### 7.1 Rust tests

Located in `crates/citry_template_parser/tests/`. **16 test files, 5,847
lines.**

All tests use a shared `common/mod.rs` (447 lines) that provides builder
helpers for constructing expected AST trees:

```rust
// Token helper - auto-computes end_index
token("c-my-tag", 1, 1, 2)

// Attribute helpers
static_attr(key_token, value_token)    // class="foo"
bool_attr(key_token)                   // disabled
expr_attr(key_token, value_token)      // c-class="expr"
template_attr(key_token, value_token)  // c-body="<div>...</div>"

// Node helpers
self_closing_node(start_tag)
body_node(start_tag, end_tag, body_template)

// Template helpers
template(elements)
template_with_vars(elements, used_variables)

// Parse helpers
parse_first_node(input)     // Parse and extract first Node
parse_should_fail(input)    // Assert parsing fails
assert_parse_error(input, expected_msg_substring)  // Assert specific error
```

**Test file organization:**

| File | What it tests |
|------|-------------|
| `tag_parser_structure.rs` | Opening/closing tags, self-closing, end tag validation |
| `tag_parser_html.rs` | Regular HTML elements, void elements, nesting |
| `tag_parser_kwargs.rs` | Key-value attributes, quoted/unquoted values |
| `tag_parser_boolean_attrs.rs` | Boolean attributes, `key=""` normalization |
| `tag_parser_dynamic_attrs.rs` | `c-*` expression and template attributes |
| `tag_parser_expressions.rs` | `{{ expr }}` template expressions |
| `tag_parser_comments.rs` | HTML comments, template comments `{# #}` |
| `tag_parser_nested_templates.rs` | Nested templates in `c-*` attributes, fragments |
| `tag_parser_spreads.rs` | `c-bind` spread attributes |
| `tag_parser_control_flow_if.rs` | `<c-if>/<c-elif>/<c-else>` grouping and validation |
| `tag_parser_control_flow_for.rs` | `<c-for>/<c-empty>`, loop variable extraction |
| `tag_parser_fills.rs` | `<c-fill>/<c-slot>`, fill-inside-component validation |
| `tag_parser_composition.rs` | Multiple control flow attrs on same tag |
| `tag_parser_raw.rs` | `<c-raw>` verbatim blocks |
| `tag_parser_user_rules.rs` | Custom tag validation rules via `ParserContext` |
| `tag_compiler.rs` | **V3 compiler** - `compile_template` output for every node type (39 tests) |

> The legacy `old_tag_parser_string.rs` and `old_tag_compiler.rs` (44 V1/V2 tests)
> were **deleted** in session 9.1.1 - they tested `GenericTag`/`compile_tag_attrs`
> APIs that no longer exist in V3. Their concepts (string args, filters, spreads,
> lists/dicts as values, positional args) were intentionally dropped in V3; the
> carryover concepts (static attrs, boolean attrs, `c-bind` spread) are already
> covered by the `tag_parser_*` files above.

**Parser test style:** Full tree assertions - every test constructs the complete
expected AST tree and asserts equality with `assert_eq!(result, expected)`.
Token positions (start_index, line, col) are manually computed and verified.

**Compiler test style** (`tag_compiler.rs`): exact-string assertions on the
generated Python source. A `wrap()` helper supplies the `generate_template()`
boilerplate; `assert_compile(input, expected_body_list)` parses + compiles and
compares. Expected strings were authored by observing actual compiler output
(a throwaway `_explore_compiler.rs` harness, since deleted) - the same
observe-then-lock approach used for the parser tests. Covers: text, expressions,
static HTML, void/self-closing elements, dynamic attrs on HTML, all component
forms (name normalization, static/expr/template attrs, body, nesting),
if/elif/else, for/empty, control-flow-as-attributes (incl. nested if+for),
slot, fill, raw, string coalescing, and whitespace behavior.

**Total Rust tests:** 226 unit tests + 5 ignored doctests (illustrative code
examples in `lang/rust.rs` and `parser_context.rs`, marked ```` ```ignore ````).

**Findings from session 9.1.1:**
- **Non-determinism bug (FIXED):** `compile_control_flow_node` aggregated a
  node's `used_variables` via a `HashSet`, so the emitted tuple order varied
  between runs (breaking reproducible output / stable cache keys). Fixed in
  `compiler.rs` to dedupe while preserving first-seen (source) order, matching
  how attribute-level vars are already handled.
- **Whitespace-drop bug (FIXED):** whitespace immediately following an HTML
  closing tag was being dropped (`</div> Bye` → `</div>Bye`, `</div> <span>` →
  `</div><span>`). Root cause: the special `WHITESPACE` rule makes Pest insert
  implicit whitespace between elements in *non-atomic* rules, and `template = {
  template_element* ~ EOI }` was non-atomic - so the inter-element implicit
  whitespace silently consumed the space before the next `text` element. (Text
  *before* a tag was kept because the atomic `text` rule greedily eats its own
  trailing space first.) Fix: made `template` compound-atomic (`${ ... }`) in
  `grammar.pest` so no implicit whitespace is inserted between elements.
  - **Cascade effects (both resolved, both improvements):**
    1. HTML comment values now include the leading space symmetrically
       (`<!-- x -->` value is ` x ` not `x `). The old asymmetric value was the
       same implicit-whitespace bug. Updated 3 comment tests.
    2. The old grammar *accidentally* rejected `<c-raw attr>` (implicit
       whitespace ate the separator `spacing_with_whitespace` needed, so the
       raw rule fail-matched). The fix makes the grammar correctly match raw
       tags with attributes - which is the documented design intent (grammar
       allows them, Rust rejects them). This exposed that `process_html_raw`
       bypassed `validate_node` and never validated attributes. Added a
       `validate_attributes_present` call in `process_html_raw`; updated the
       `test_c_raw_with_attrs` expected error. Now c-raw attr rejection uses the
       same path/message as `<c-else>`/`<c-empty>`.

### 7.2 Python tests

- `test_html_transformer.py` - Working, run in CI
- `test_safe_eval.py` (2,265 lines) - Working, run in CI
- `_test_template_parser__tag.py` (5,098 lines) - **Disabled** (prefixed `_`).
  Tests for V1/V2 `parse_tag` / `compile_tag` API. Will need rewriting for V3.
- `_test_template_parser__value.py` (345 lines) - **Disabled**. Same situation.

### 7.3 Running tests

```bash
# Rust tests (from repo root)
cargo test

# Python tests (from repo root)
cd packages/py/citry_core && uv run maturin develop  # Build first
cd ../../.. && uv run pytest

# Both
cargo test && uv run pytest
```

---

## 8. Where we left off

### 8.1 Last commits

Most recent first (the Feb commits in the original snapshot are long superseded):

| Date | Commit | What |
|------|--------|------|
| 2026-06-22 | `f02154c` | Django, FastAPI, Flask, Starlette, WSGI, ASGI integrations |
| 2026-06-22 | `9947f05` | JS/CSS deps + vars, cache API, `Script`/`Style`, render strategies, `<c-js>`/`<c-css>`, browser client |
| 2026-06-12 | `b5609fd` | `Component.ancestors` |
| 2026-06-12 | `4f4abcc` | `on_render()`, `ErrorFallback`, component tree path in errors, error bubbling |
| 2026-06-12 | `2292bf5` | benchmarking skeleton |
| 2026-06-12 | `39824bb` | dynamic `<c-component>` / `<c-element>` |
| 2026-06-11 | `8b80c66` | Vue-like class/style attributes |
| 2026-06-11 | `c07f609` | serialize via the Rust `mark_html()` |
| 2026-06-11 | `74aacbe` | Const optimization pt2 |
| 2026-06-10 | `79066c2` | provide/inject |
| 2026-06-10 | `d72475f` | compile-time slots/props validation + Pydantic |
| 2026-06-10 | `980a0cd` / `b392d90` | slots/fills |

### 8.2 Last working session (2026-06-22)

A long benchmarking and performance session (the source of the
`docs/design/performance.md` and `benchmarking.md` refresh):

- Ported the django-components large benchmark to citry (35 components, the full
  `ProjectPage`), plus a separate `Const` variant, and published numbers
  (`benchmarks/`, `docs/design/benchmarking.md`).
- Two optimization passes on the runtime: the O(n*depth) dependency-collection
  fix, batched attribute formatting, escape-to-str, cheaper component ids, lazy
  extension-hook contexts, and a deps class-resolution memo. Repeat render went
  19.63 -> ~13.7 ms (1.85x -> 1.29x a bare Django template), output
  byte-identical, 1,126 tests green.
- Analysed and prototyped (then removed) a render-walk-in-Rust move; the cost
  model, the prototype result, and the verdict are in `performance.md` section
  6, and the open decision is summarized in section 9.5 below.

### 8.3 Git working-tree state

Everything from the benchmark and performance work is **uncommitted** (about 58
changed/new files): the engine optimizations under `packages/py/citry/citry/`,
the benchmark ports and runner under `packages/py/citry/tests/` and
`benchmarks/`, a `c-for`+`c-bind` parser fix under
`crates/citry_template_parser/`, the new `docs/design/performance.md`, and edits
to `benchmarking.md` / `migration_djc.md` / `CHANGELOG.md`. The tree is green
(tests, ruff, and `cargo fmt` all pass) but not checkpointed; one labelled
commit (or a few) would give the next session a clean base.

---

## 9. What needs doing (rough priority order)

### 9.1 Immediate - COMPLETED

~~Finish rewriting Rust tests, commit the template parser crate.~~
Done in sessions 9.1.1 and 9.1.x. 226 Rust unit tests pass. Crate committed.

### 9.2 Near-term - COMPLETED

~~Wire V3 parser to Python.~~
Done in session 9.2. PyO3 glue rewritten for V3: `parse_template`,
`compile_template`, all 12 AST classes, and `TagRules` exposed. Python
wrapper (`template_parser/`), `_rust.pyi` stubs, and stub runtime node
classes all rewritten. 43 new Python tests (parse, compile, round-trip,
errors, lang, TagRules). Old V1/V2 tests deleted. 310 Python tests pass.

### 9.3 Python runtime: built, with one open item

8. ~~Implement Python runtime nodes~~ **Done.** All node classes live in
   `packages/py/citry/citry/nodes/`, and the runtime renders the full
   benchmark suite (slots/fills, control flow, dynamic attributes, components).

9. ~~Implement `<c-provide>`, `<c-js>`, `<c-css>` as Python components~~
   **Done.** provide/inject and the dependencies system (`<c-js>`/`<c-css>`,
   plus the rest of the JS/CSS pipeline) are built.

10. **Python builtins in expressions - decided: no builtins.** `{{ len(items) }}`
    does not resolve `len`, by design: the sandbox exposes no builtins, in both
    sandboxed and unsandboxed modes (`citry_core/safe_eval/eval.py`), so an
    expression reaches only what the render context provides. A template that
    needs `len` / `range` / etc. passes them explicitly from `template_data`, or
    defines them once as `Citry(template_globals={...})`. Not a gap.

### 9.4 Longer-term

11. **Template formatter** - Notes in `v2_template_formatter.rs`. Needs the AST
    with comment association. Tracked in [#22](https://github.com/citry-dev/citry/issues/22).

12. **LSP / linter integration** - Variable tracking is already in the AST. An
    LSP could provide autocomplete, go-to-definition for template variables,
    and error highlighting. Tracked in [#23](https://github.com/citry-dev/citry/issues/23).

13. **Other language bindings** - JS (wasm-bindgen), PHP (FFI), Go (cgo). The
    `lang/*.rs` stubs are structural placeholders. Tracked in [#27](https://github.com/citry-dev/citry/issues/27).

14. **Expression caching** - Per `v2_TODO.md`, static expressions and
    constant-variable expressions could be cached after first render. Tracked in
    [#18](https://github.com/citry-dev/citry/issues/18).

### 9.5 Performance: runtime built, benchmarked, optimized; decision settled

The Python runtime is built and renders the full benchmark suite (so much of
section 9.3 is now done, not pending). Two optimization passes took the
large-page repeat render from 19.63 ms to ~13.7 ms (1.85x -> 1.29x a bare
Django template). The complete record - what changed and why, the per-callback
cost model, the candidates-for-Rust analysis, the Rust prototype that sized the
architectural lever, and the resulting verdict - is in
[`docs/design/performance.md`](../docs/design/performance.md). The benchmark
scaffold and published numbers are in
[`docs/design/benchmarking.md`](../docs/design/benchmarking.md).

**The decision (settled): stay in Python, accept ~1.3x.** Closing the last ~1.3x
to Django parity has no cheap path. The one lever that could reach parity, moving
the render walk into Rust, was built out in full, measured, and archived: it
reached roughly parity on a real construction-bound page and won only modestly
where string work dominates (performance.md section 6.9), not enough to justify
the added complexity and moving the high-risk compiler-output contract. It is
removed from the live code but preserved in git, so a future multi-language port
(the real reason to want a host-agnostic Rust walk) can revive it. The smaller
levers (a security-sensitive runtime sandbox fast path worth ~2-3%, remaining
Python micro-opts) do not add up to parity. Two over-optimistic intermediate claims
were tried and retracted in performance.md (a "~85% Rust-able" estimate, and a
compile-time sandbox fast path); read section 6 for why, so they are not
re-attempted.

---

## 10. Design decisions to remember

### Confirmed (implemented or staged)

- **`key=""` is boolean True** - Normalized at compile time, not parse time.
  AST preserves what user wrote.
- **Void elements** - Parsed as self-closing. Rendered as `<br/>` (compact),
  not expanded to `<br></br>`.
- **Non-void self-closing** - `<div/>` expands to `<div></div>` at compile time.
- **Fragment syntax** - `<>...</>` handled in `parse_html_attribute`, stripped
  before template parsing. NOT part of the grammar.
- **Nested template detection** - Must start with `<tag` and end with `</tag>`.
  Loose patterns like `< THIS IS TEXT >` are treated as text.
- **Control flow grouping** - `<c-if>`/`<c-elif>`/`<c-else>` must be adjacent
  siblings. `<c-for>`/`<c-empty>` same. Validated during parsing.
- **Control flow as attributes** - `<div c-if="x" c-for="y in z">` unwrapped
  at compile time. IF has higher priority than FOR.
- **Variable shadowing forbidden** - `<c-for>` and `<c-fill>` cannot introduce
  variable names that already exist in scope.
- **Fill validation** - `<c-fill>` must eventually be inside a component. No
  mixing fills with non-fill siblings. Unique names enforced.
- **`c-bind` is special** - Multiple `c-bind` attrs allowed on one tag. Not
  subject to duplicate-attribute validation. Does not produce `bind=` attribute.
- **Attribute escaping** - `c-c-foo="expr"` renders as `c-foo="..."` in output.
  First `c-` is stripped; remaining `c-` is literal.
- **Comments tracked but not in AST tree** - Comments collected at every level
  (`Template.comments`, `Node.comments`, etc.) but don't affect the template
  element tree. Formatting can use them later.

### Deferred / open questions

- **JSX-in-Python (PYX)** - Explored in `v2_jsx.md`. Would require forking
  ruff's Python parser. Deferred.
- **Template string parsing in V3** - V2 recursively parses template strings
  (`"Hello {{ name }}"`) to extract nested tags and track variables. The V3
  parser handles this for `c-*` attributes that contain nested templates.
- **Expression caching** - Design exists in `v2_TODO.md` but not implemented.
  Tracked in [#18](https://github.com/citry-dev/citry/issues/18).
- **Builtins in expressions** - Settled: expressions expose no Python builtins.
  Pass what a template needs from `template_data`, or set `template_globals`. See
  section 9.3 item 10.
- **`{% %}` support in V3** - The grammar does NOT parse Django-style template
  tags. V3 only recognizes `{{ }}`, `{# #}`, and HTML tags.

---

## 11. CI/CD and tooling

### Workflows

| File | Trigger | What it does |
|------|---------|-------------|
| `repo--check.yml` | All pushes/PRs | Full check suite (`python scripts/check.py`) |
| `rust--tests.yml` | Changes to `crates/`, `third_party/`, `.github/` | `cargo test` on ubuntu + windows |
| `py--tests.yml` | Changes to `packages/py/`, `crates/`, `third_party/` | `uv sync --all-packages` + `pytest` on Python 3.10–3.14, ubuntu + windows + macOS smoke |
| `py--citry-core--publish.yml` | Tag push `py@citry-core@*` | Build wheels + publish to PyPI |

### Custom validators

4 auto-discovered validators in `scripts/validators/` (run by `python scripts/check.py`):
- `toolchain.py` - Ensures Rust toolchain consistency
- `crate_member.py` - Ensures new crates are in workspace
- `bindings.py` - Validates Python/Rust binding consistency
- `dependabot.py` - Ensures new Python packages have dependabot
  entries

### Build commands

```bash
# Install dev dependencies
uv sync --extra dev

# Build Python extension
cd packages/py/citry_core && uv run maturin develop && cd ../../..

# Run linters
uv run ruff format . && uv run ruff check .
cargo fmt && cargo clippy

# Run tests
cargo test && uv run pytest
```

---

## 12. Key files quick reference

| What | Path |
|------|------|
| **North star spec** | `README.md` |
| **V3 grammar** | `crates/citry_template_parser/src/grammar.pest` |
| **V3 AST types** | `crates/citry_template_parser/src/ast.rs` |
| **V3 parser** | `crates/citry_template_parser/src/parser.rs` |
| **V3 compiler** | `crates/citry_template_parser/src/compiler.rs` |
| **Language trait** | `crates/citry_template_parser/src/lang/lang.rs` |
| **Python lang impl** | `crates/citry_template_parser/src/lang/python.rs` |
| **Tag constants/rules** | `crates/citry_template_parser/src/constants.rs` |
| **Test helpers** | `crates/citry_template_parser/tests/common/mod.rs` |
| **PyO3 glue** | `crates/citry_core_py/src/lib.rs` |
| **Python package config** | `packages/py/citry_core/pyproject.toml` |
| **Python type stubs** | `packages/py/citry_core/citry_core/_rust.pyi` |
| **Codebase docs** | `docs/codebase.md` |
| **Attribute spec** | `crates/citry_template_parser/v2_spec.md` |
| **Grammar commentary** | `crates/citry_template_parser/grammar_commentary.md` |
| **Cross-lang FFI notes** | `crates/citry_template_parser/v2_cross_lang.md` |
| **Cursor chat history** | `cursor-chats/INDEX.md` (10 citry chats, 65 djc-core-html-parser chats) |

---

## 13. Upstream relationship

Citry was forked from `django-components/djc-core`. The upstream project
continues active development on django-components (198 cursor chats spanning
Jan 2025–Jun 2025).

Key upstream issues to track:
- [#1499 - Template versions](https://github.com/django-components/django-components/issues/1499) - Defines V1/V2/V3 migration path
- [#1004 - v3: Decoupling from Django](https://github.com/django-components/django-components/issues/1004) - Long-term vision
- [#1141 - v2 Ideas](https://github.com/django-components/django-components/issues/1141) - Features planned for V2
- [#1650 - v3 Cache](https://github.com/django-components/django-components/issues/1650) - Cache should store RenderObject
- [#794 - HTML tag syntax](https://github.com/django-components/django-components/issues/794) - django-cotton-like syntax discussion

The last sync from djc-core was the Feb 5 commit (`905bad2`). Changes in
django-components since then may need to be reviewed for relevant improvements
to port back.
