# AGENTS.md - crates/python_safe_eval

Transforms a Python expression into a sandboxed form by rewriting its AST, so
the host can intercept variable access, calls, attribute access, and subscripts
at runtime. Built on Ruff's Python parser (`ruff_python_ast`,
`ruff_python_parser`). Stable; few open questions.

For repo-level rules see [`/CLAUDE.md`](../../CLAUDE.md). For cross-crate facts
see [`/docs/agent/INDEX.md`](../../docs/agent/INDEX.md).

## What it does

It parses the expression, validates that the AST contains only allowed node
kinds, rewrites unsafe patterns into interceptable calls (for example
`foo(1)` -> `call(foo, 1)`, `obj.attr` -> `attribute(obj, "attr")`,
`obj[k]` -> `subscript(obj, k)`), regenerates Python source from the modified
AST, and returns it along with the variables it uses.

## Where to look

- `src/lib.rs` - public API re-exports: `transform_expression_string`,
  `parse_expression_with_adjusted_error_ranges`, `generate_python_code`,
  `extract_comments`, and the `Comment`, `Token`, `TransformResult` types.
- `src/transformer.rs` - the AST validation and rewriting.
- `src/codegen.rs` - regenerating Python source from the AST.
- `src/comments.rs` - comment extraction.
- `src/utils/python_ast.rs` - AST helpers.
- `src/utils/literal_source.rs` - writing a string literal from its source
  text when the parser's decoded value cannot reproduce it (a lone surrogate
  escape), and the helpers that write f-string text into the `str.format`
  template the transformer builds.

## Who depends on it

- `crates/citry_core_py` exposes it to Python as the `safe_eval` submodule
  (the Python side wraps it in `citry_core/safe_eval/`).
- `crates/citry_template_parser` uses it (via the Python `LangImpl`) to extract
  used / assigned variables and comments from `{{ }}` expressions and from
  `<c-for>` loop expressions.

## Gotchas

- After the transformer runs, a name node can hold a literal's source text
  (`literal_source::source_text`), which the generator writes as it is. A
  step added after the transformer must not read name ids as variable names.

## Verifying changes

```bash
cargo test -p python_safe_eval
```
