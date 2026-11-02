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
- `src/tokenizer.rs` - the one function every html5gum run goes through
  (`run_tokenizer`). It keeps the run on enough stack, whatever thread
  calls it, and returns whether the run stayed within the size limits.
- `src/html_limits.rs` - the size limits every parse applies before
  html5ever builds a tree: 1,024 attributes on one tag, 16 start tags of
  each of `html`, `head` and `body`, 512 elements held open at once, and
  250,000 formatting elements and attributes reopened. html5ever's cost
  grows with the square of an attribute count, of a repeated `<html>` or
  `<body>` count, and of the nesting depth. When formatting tags such as
  `<b>` are closed out of order, html5ever keeps them on a list and opens
  a copy of each at the next text or tag, so the tree grows by the input
  size times the length of that list. After each token, `after_token`
  counts the elements the tree builder holds (it lists them through
  `trace_handles`) and compares the formatting elements the scan's tree
  sink saw created (`TrackingSink`, the DOM every scan builds into) with
  the formatting start tags it was given.
- `src/static_html.rs` - checks that a finished piece of HTML (a `<c-raw>`
  block, or the HTML the server writes inside a shell) keeps its own
  `<template>` parse where the page puts it, and counts the top-level nodes
  Vue's static vnode needs to adopt it.
- `tests/marker.rs`, `tests/transformer.rs` - the tests.
- `tests/attribute_runs.rs` - runs each entry point on a tag with 100,000
  attributes on a 128 KiB and an 8 MiB stack, in a child process, because a stack overflow
  cannot be caught. Each entry point refuses the tag, but html5gum still
  reads all of it.
- `tests/html_limits.rs` - each entry point at and just over each size
  limit, and the inputs that were slow before the limits.

## Gotchas

- **html5gum is a patched copy.** The workspace builds
  `third_party/rust/html5gum` (0.8.4 with one line changed; its
  `README.citry.md` says which and why). Upstream 0.8.4 nests a few calls
  for each `name="value"` attribute in a row, so one tag with about 50,000
  of them overflows the 8 MiB main-thread stack in a release build (about
  3,000 on a 512 KiB thread) and aborts the process. A stack guard around
  our own code cannot stop that, because the calls are inside html5gum.
  When you upgrade html5gum, carry the change over unless upstream has
  fixed it; `tests/attribute_runs.rs` fails if it is lost.
- **Start html5gum only through `run_tokenizer`** (test helpers aside), so
  every run gets the same stack reserve and the same size limits. Build a
  fragment's tree with `output_scanner::parse_fragment_in`, not
  html5ever's own `parse_fragment`, so the limits count in the context the
  tree is built in.
- **Build every scan's tree into `TrackingSink`.** It counts the formatting
  elements the parser makes, and the limit on reopened ones reads that
  count after each token. A scan that built into another sink would never
  refuse a page for reopening.
- **The nesting limit counts the parser's own elements.** It is 512
  elements held at once. A page scan holds `<html>`, `<body>` and the
  `<head>` pointer, so it fits 509 nested elements; a `<template>`
  fragment holds the root `<html>` and the context element, so it fits 510
  (`tests/html_limits.rs` locks both). `tests/deep_nesting.rs` runs the
  recursive checks over the deepest tree these limits allow.
- **The Python wrappers pick a hint by the start of each limit's message**
  (`packages/py/citry/citry/_vue/opaque_html.py`). Give a new limit a
  message that starts with words no other limit's message starts with, and
  add its hint there.

## Who depends on it

`crates/citry_core_py` exposes it to Python as the `html_transform` submodule
(wrapped on the Python side in `citry_core/html_transform/`).

## Verifying changes

```bash
cargo test -p citry_html_transform
```
