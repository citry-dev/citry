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
  - `animation_sets_href`, `is_url_value`, and `is_javascript_url_value`
    are the one rule for "this attribute holds a `javascript:` URL". The
    page check and the embedded-document check both call them. They cover
    the `to`, `from`, `by`, and `values` of an SVG `<animate>` or `<set>`
    that sets `href`. The Python reference keeps a matching copy.
  - `data_url_requires_javascript` is the one rule for a `data:` URL the
    page loads or opens as a document: `iframe src`, `frame src`,
    `object data`, `embed src` (`loads_document_url`), a link or form URL
    or the value of an SVG animation of a link (`opens_document_url`), and
    a `<meta http-equiv="refresh">` (`meta_refreshes`, `refresh_data_url`).
    `attribute_document_requires_javascript` routes each attribute to it,
    at the top level and inside embedded documents. A `text/html` document
    is read as the browser reads the URL: tabs and line breaks dropped,
    `; base64` accepted, and any payload that is not plain ASCII, or that
    holds 0x00, 0x0E, 0x0F, or 0x1B, counted as running code
    (`payload_may_hide_markup`). A type in
    `is_inert_media_type` (text, images, media, fonts, PDF, downloads) runs
    nothing. Every other type, SVG and the other XML types included, counts
    as running code without being read. The Python reference keeps a
    matching copy.
  - `may_be_skipped_by_browser` is the one rule for a character a browser
    might skip in a `<script type>` or a refresh `content`: anything but
    printable ASCII. Browsers differ here, so `script_type_is_executable`
    counts a type that still holds such a character, ASCII whitespace
    aside, as running, and `refresh_data_url` skips such characters in every
    gap. Another encoding could spell such a character in a `data:`
    document, which `payload_may_hide_markup` covers. The Python reference
    keeps a matching copy.
  - `BrowserRules` (in `src/output_scanner.rs`) names the tree-building
    rules browsers differ on, the mode (`Mode`), and where the markup ends
    up (`Placement`: a whole document, another page's body, or a
    `<template>`, which is how Citry's browser runtime (through Vue) builds
    an opaque HTML block, a piece of HTML that Vue does not read itself). No
    reading follows `innerHTML` set on an element with special parsing
    rules, such as an SVG or MathML element, a `<table>` or table part, a
    `<select>` or a `<form>`, which browsers build differently from the
    three placements. The check can scan a page more than once, each time
    under one set of these rules; one such scan is a reading of the page.
    `for_each_reading` (in `src/output_policy.rs`) runs the rules of this
    check once per reading, at the top level and in embedded documents, so
    code any reading finds counts. Its doc comment lists what adds a
    reading: the text `<select` or `<frameset`, a `<noscript>` that may
    hold a tag (Chromium reads
    `template.innerHTML` with scripting off, see `noscript_as_markup`), an
    end tag `EndTagRule` changes, a `<table>` start tag inside an open `<p>`
    (the one step quirks mode changes), and a table part that html5ever
    ignored. A page with none of these gets one reading. html5ever 0.29.0
    keeps its old `<select>` rule and has neither browser's own end-tag
    rule, so `feed` changes the tags it hands over and `VisibleNames`
    changes the names `elem_name` gives. For markup that goes into another
    page, `tree_builder_for` feeds the tags of an empty host page first, and
    the `<noscript>` reading turns html5ever's scripting option off. Only this
    check departs from html5ever: `scan_output_html` and the page parses
    keep its rules. An `iframe srcdoc` document is read in standards mode
    and, when the mode matters, in the mode its doctype picks, because
    Firefox 157 reads it in standards mode and Chromium 156 picks the mode
    from its doctype, with no doctype meaning quirks mode.
    `EmbeddedDocuments` keeps each embedded document's answer for the whole
    check, so the readings of the outer page do not multiply the readings of
    the documents inside it.
  - `ParserDifference` (in `src/output_scanner.rs`) records one tag where
    browsers may build a different tree from every reading, and its doc
    comment is the one list of the cases. The check does not try to build
    the browser's tree there: it reports the tag under
    `Rule::JsParserDifference` on the page, with the `DifferenceKind` code
    in the finding's `case` field so Python can name the fix, and counts
    an embedded document with one as running code.
    `DifferenceKind::UnclearFormatting` arises on its own for an end tag
    inside an SVG or MathML element that holds HTML (`<desc>`, `<mi>`) or a
    `<search>`. A `<b>` start tag closes any other SVG or MathML element it
    is inside, so `<svg><b><b><b><b>` never reaches it. The one other route,
    an `<svg>` start tag after a closed formatting element, is reported as
    `ReopenedFormatting`, and end tags after it can report both.
    `note_parser_difference` and `end_tag_is_ignored` notice them from
    `held_elements`, which reads html5ever's open elements and formatting
    list apart (see `read_held`). It keeps a read while html5ever reports
    the same handles, and brings it up to date when only the newest open
    elements changed (`update_held`), so a tag costs at most a few passes
    over what html5ever holds.
  - The Python reference cannot read a page these ways, so
    `rust_only_adds_findings` lets the comparison pass when Rust reports
    every finding the copy reports and more, except after a tag Rust
    reports as a parser difference, where the copy's later findings may be
    missing. `select_rule_changes_tags` leaves a generated page with an
    omit marker out when the `<select>` rule moves its tags, and
    `noscript_rule_changes_tags` leaves a generated page out when reading
    `<noscript>` contents as markup changes its tags.
  - `encoding_dependent_span` is the one rule for text whose tags depend on
    the encoding the browser picks. The check runs it on the settled page
    (`Rule::JsPageEncoding`) and on every embedded document. Its doc comment
    lists what was tested. The Python reference keeps a matching
    copy. Escaped values write ESC as `&#27;`
    (`packages/py/citry/citry/util/html.py` and the Vue server renderer's
    `ESC_REFERENCE`), so this rule fires on text Citry did not escape,
    including `Markup.format()` output.
  - `classify_dependency_attribute` (in `citry_core_py`) reads only
    structured `Script` and `Style` attributes, so it keeps calling
    `is_url_attribute` and `is_javascript_url` directly.
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
  the formatting start tags it was given. The output check also spends that
  count from one budget for all its readings of a page
  (`MAX_CHECK_WORK_PER_BYTE` and `CHECK_WORK_FLOOR`, refused as
  `HtmlTooLarge::CheckWork`), so the number of readings cannot multiply
  the cost of a deep page without bound.
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

- **html5gum must not nest for each attribute.** Since 0.9.1
  ([pull request 158](https://github.com/untitaker/html5gum/pull/158)) it
  returns to its main loop between two attributes, so a tag with any number
  of attributes needs the same stack. A stack overflow aborts the
  whole process, and a stack guard around our own code cannot stop it,
  because the calls are inside html5gum. The workspace pins html5gum to an
  exact version, so an upgrade is a deliberate step. Run
  `tests/attribute_runs.rs` when you take it: it fails with a crash if a
  release nests for each `name="value"` attribute again.
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
  (`tests/html_limits.rs` locks both). The output check's reading of a
  page inside a `<template>` (see `Placement::Template`) holds that
  `<template>` too, so it fits 508. The test
  `each_placement_fits_the_nesting_its_host_elements_leave` locks all
  three numbers. `tests/deep_nesting.rs` runs the recursive checks over
  the deepest tree these limits allow.
- **html5ever 0.29.0 does not read every page the way browsers do.** It
  keeps the old `<select>` rule, which html5ever 0.40.1 has dropped. It
  also leaves the SVG and MathML elements that hold HTML off its list of
  special elements, in 0.40.1 too, which `end_tag_is_ignored` and
  `FedTag::ListItem` make up for in the output check. The other gaps
  found so far are listed on `ParserDifference`, and the check refuses a
  page at them instead of building the browser's tree. Add a new gap there
  the same way: notice the tag and refuse it. The hydration checks and the
  Vue HTML scan still read such a page html5ever's way. An upgrade has to
  keep the tree tests in `src/output_scanner.rs` passing, which pin these
  rules to trees Chromium and Firefox built, and a change to these rules
  needs a new look at what real browsers build.
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
