# AGENTS.md - crates/citry_html_transform

Adds or modifies attributes on HTML elements. Two entry points: `mark_html`,
a single-pass scan that splices attributes onto root-level tags and splits the
output around placeholder elements (the serializer's hot path), and
`transform_html`, a `quick-xml` rewrite of every element (the tool for
all-element attribute changes). It also holds the checks that the browser's
HTML parser builds the nodes Vue expects from server HTML before a page
hydrates (`hydration_structure.rs`, `hydration_nesting.rs`, `static_html.rs`).

For repo-level rules see [`/CLAUDE.md`](../../CLAUDE.md). For cross-crate facts
see [`/docs/agent/INDEX.md`](../../docs/agent/INDEX.md).

## Where to look

- `src/lib.rs` - re-exports `mark_html`, `transform_html`, the hydration
  structure and nesting checks, the output scanner and output checks, and
  their types.
- `src/marker.rs` - the root-marking scan.
- `src/transformer.rs` - the every-element rewrite.
- `src/hydration_structure.rs` - checks that the browser builds the nodes Vue
  expects from server HTML before a page hydrates: elements, Vue's anchor
  comments, root whitespace, and shells whose children Vue builds itself.
  `src/output_scanner.rs` supplies the tokenizer it shares with the parse.
- `src/hydration_nesting.rs` - the per-request form of that check: it keeps
  html5ever's answer for each (open elements, token) pair per thread, so a
  page is only parsed in full when the stored answers cannot cover it. The
  module docs list what a stored answer relies on; the random-tree test
  compares it with the full parse.
- `src/output_policy.rs` - runs the strict-CSP and JavaScript-policy rules
  over the HTML `serialize()` returns and reports only what they find; the
  Python validators (`packages/py/citry/citry/_csp_validation.py`,
  `packages/py/citry/citry/_javascript_policy.py`) write the messages and
  decide whether to warn or raise. Its character-reference decoding and
  letter matching copy Python's on purpose.
  `packages/py/citry/tests/_output_policy_reference.py` keeps the Python
  rules, `packages/py/citry/tests/test_output_policy_differential.py`
  compares the two on generated pages, and running any test suite with
  `CITRY_OUTPUT_POLICY_DIFFERENTIAL=1` compares them in every check.
- `src/output_scanner.rs` - reads HTML the way the browser's parser does
  (html5gum with html5ever's tree builder choosing the tokenizer state) and
  returns each start tag's facts; `scan_output_html_with` hands them to a
  callback instead of keeping them.
- `src/html_limits.rs` - the one function every html5gum run goes through
  (`run_tokenizer`). It refuses an input with a tag that holds more than
  `MAX_ATTRIBUTE_RUN` attributes in a row written `name="value"`, and
  keeps the run on enough stack for an input at the limit.
- `src/static_html.rs` - checks that a finished piece of HTML (a `<c-raw>`
  block, or the HTML the server writes inside a shell) keeps its own
  `<template>` parse where the page puts it, and counts the top-level nodes
  Vue's static vnode needs to adopt it.
- `tests/marker.rs`, `tests/transformer.rs` - the tests.
- `tests/attribute_limits.rs` - runs each entry point on a small stack in a
  child process, because a stack overflow cannot be caught.

## Gotchas

- **Start html5gum only through `run_tokenizer`.** html5gum 0.8.4 nests
  several calls for each `name="value"` attribute in a row and has no
  depth limit, so one tag with about 20,000 of them overflows the stack and
  aborts the process. A stack guard around our own code does not help,
  because the calls are inside html5gum. `run_tokenizer` refuses the input
  first, and every function that scans HTML returns that refusal
  (`TooManyAttributes`) as an error, `None`, or `false`, never by reading
  on. A new entry point calls `run_tokenizer` and decides what a refusal
  means for it; a refusal must never read as "nothing found".

## Who depends on it

`crates/citry_core_py` exposes it to Python as the `html_transform` submodule
(wrapped on the Python side in `citry_core/html_transform/`).

## Verifying changes

```bash
cargo test -p citry_html_transform
```
