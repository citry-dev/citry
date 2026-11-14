# Output checks that read pages unlike browsers (GHSA-7qpw)

- **Advisory:**
  [GHSA-7qpw-hm7q-pvfx](https://github.com/citry-dev/citry/security/advisories/GHSA-7qpw-hm7q-pvfx),
  published 2026-11-14, severity medium (CVSS 3.1 score 6.1)
- **Affected and fixed versions:** `citry >= 0.1.0, < 0.8.0`, fixed in
  0.8.0; `citry-core >= 1.8.0, < 1.9.1`, fixed in 1.9.1
- **Fix:** `f96d4f5f7`. Citry writes the ESC character in an escaped
  value as a character reference. The `security_javascript` and
  `security_csp` output checks read a page the ways that browsers are
  known to differ on (each way is a "reading": one scan of the page under
  one set of browser parsing rules), and keep all their readings within
  one work budget (a cap on how much work one page may cost to check).
  The advisory says the checks cover only the differences found so far.
  Under `security_javascript` only, the check also reports text that
  depends on the page's encoding.
- **Reviewer:** separate reviewing agents, in repeated rounds (this record
  rests mainly on the last two, the fix author's runs and the advisory)
- **Code:** in `crates/citry_html_transform/src/`, `output_policy.rs` (the
  rules), `output_scanner.rs` (the readings) and `html_limits.rs` (the
  work budget); `escape_text`, `static_text` and `escape_attribute` in
  `crates/citry_vue_compiler/src/server_render.rs`; in
  `packages/py/citry/citry/`, `util/html.py` (`escape`, `escape_to_str`),
  `_javascript_policy.py`, `_output_policy.py`, `_csp_validation.py` and
  `ext/preview/host.py`; tests in the Rust files above,
  `packages/py/citry/tests/` and
  `packages/py/citry_core/tests/test_html_transformer.py`; and the scope
  statement in `docs_site/content/security.md`.

## Who controls the input

Citry's escaping and its opt-in output checks read some pages differently
from browsers. The output checks (the `security_javascript` and
`security_csp` settings) read the HTML Citry renders and report code in
it, such as scripts, event handlers and `javascript:` URLs; with
`security_javascript="forbid"`, such a page raises `ValueError`. The
first case below needs no setting; the second affects an app that relies
on a check.

- **Escaped values.** Citry's escaping left the ESC control character
  (U+001B) in place. On a page that a browser reads as ISO-2022-JP (a
  Japanese encoding), ESC bytes switch how later bytes are read, so a
  closing quote can stop being a quote. Anyone whose text reaches an
  escaped value can supply the ESC: the template author, the app's Python
  code, or data from a request or storage. The page must name
  ISO-2022-JP, so an app that serves UTF-8 is not affected.
- **Gaps in the checks.** The HTML can come from `Markup` (a string Citry
  writes as HTML without escaping it), a `<c-raw>` block (a template
  block Citry writes as written), or an extension that edits the HTML.
  Several cases can also arrive through an escaped value that a template
  binds to a `<meta http-equiv="refresh">`, a `<script>` type, a frame, a
  link or a form, or through a `Script` type the app sets.

In both cases the browser runs the code. The advisory sorts the gaps in
the checks into five groups: characters that browsers skip, the page's
own encoding, `<select>`, other differences in how the page is built,
and where the browser puts the HTML. It says which check each group
affects. The fix adds the report for the encoding group under
`security_javascript` only, so `security_csp` is unchanged for that group.

The change touches these places in the Mechanism 7 list (the list in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)
of places where a value reaches the browser): text and markup, URL
attributes, embedded documents, the output checks, and the responses
Citry serves (the preview server). The list has two entries from this
review: "Parser rules browsers differ on" and "The page's declared
encoding".

## How it was checked

Each round read the fix, ran its own pages in real browsers (Chromium
156.0.8078.4 and Firefox 157.0), and tried to defeat the new checks. A
page counted as a hit when a marker handler in it ran. Each run had a
control with no check, to show that the harness sees code that runs.

1. **Known pages in nine placements.** 56 pages found by earlier probing
   were each placed nine ways: as a whole document, as a host page's body
   in standards and quirks mode (the way a browser reads a page, set by
   its doctype), as `innerHTML` (the browser call that sets an element's
   HTML) of a `<div>` and of a `<template>` in both modes, as a `srcdoc`
   document (an iframe's own HTML), and as a `data:` document. Of the 504
   combinations, 57 passed `security_javascript="forbid"` and none ran.
   With no check, 420 ran in at least one browser.
2. **Generated pages.** Generators built pages from about 330 tag names,
   about 20 doctypes and several script-running snippets. The strings
   that `forbid` passed ran in six placements in both browsers: the
   author's 57,359 strings found 0 hits, and so did a reviewer's about
   38,000 more and a run through `DOMParser` (the browser's own HTML
   parser). The author's generator found many hits against an earlier
   version of the fix.
3. **Other places that take HTML.** Strings that `forbid` passes were set
   as `innerHTML` of 20 kinds of element (10,374 strings in each browser):
   129 hits in all. Eight of the 20 kinds had hits and the other twelve
   had none. The docs still list `<table>`, `<select>` and `<form>` as
   not read, because the check does not follow their parsing rules.
4. **Nested documents.** 220 cases of a `srcdoc` document inside a
   `data:` document and the other nestings: 30 passed the check and none
   of those ran in either browser.
5. **Tests.** On the last reviewed code, the crate's 107 unit tests and
   61 more in its other test targets passed, as did 968 focused Python
   tests and 597 more with `CITRY_OUTPUT_POLICY_DIFFERENTIAL=1`, which
   compares the Rust rules with a Python reference copy.
6. **Reused open-element lists.** To save work, the scanner reuses its
   list of open elements (tags opened and not yet closed) between tokens.
   A debug build compared every reused list with one built from scratch,
   on 8 runs of 2.5 million random pages: 0 differences. With the fix for
   out-of-date lists switched off, the same harness reported 252
   differences in 4.5 million pages, and the new test
   `a_kept_read_is_dropped_once_four_equal_copies_are_made` fails with
   the fix reverted.
7. **Ordinary pages and code reads.** Builds of the check from before and
   after the new readings checked 26,174 HTML blocks from the
   repository's examples, docs and components. Two differed, both for one
   Markdown page and its archived copy (an unclosed `<noscript>` in the
   prose); the new reading is right for it. The reviewers also read
   html5ever 0.29.0 (the HTML parser behind the check) and followed every
   work budget limit to its caller.

## Ruled out

- **An escaped value that keeps ESC:** `escape` and `escape_to_str` in
  `util/html.py` and the three Vue server renderer writers write ESC as
  `&#27;`, which a browser reads only after it has decoded the page in
  its encoding (`test_python_render_paths_write_no_raw_esc`). Values that
  pass through `Markup.format()`, `%`, `+` and `join` belong to MarkupSafe
  (the Python library behind `Markup`) and keep ESC, and the check reports
  such text (`test_markup_format_keeps_esc_for_the_check_to_find`).
- **Characters browsers skip in a script type or refresh:** the browsers
  skip different sets, so the check follows neither. A script type that
  still holds anything but printable ASCII or ASCII whitespace after
  trimming counts as running code, and the refresh check reads past any
  such character
  (`test_forbid_rejects_a_script_type_padded_with_a_character_a_browser_may_skip`).
- **A page that changes meaning with its encoding:** the rule
  `js-page-encoding` reports `ESC $`, `ESC (`, non-ASCII text in a
  `<![CDATA[` section (a block of raw text inside SVG or MathML) and a `<`
  followed by a NUL byte, in every embedded document too. A `data:` HTML
  document that is not plain ASCII counts as running code
  (`a_data_document_that_is_not_plain_ascii_counts_as_running`).
- **A page read only as a whole document:** the check now also reads a
  page as a host page's body and as a `<template>`'s contents when its
  markup builds differently there
  (`markup_put_into_another_page_builds_the_tree_it_builds_there`).
- **A limit that lets a page through:** every limit returns an error, so
  `forbid` refuses the page, as it does a nested document it cannot read.
- **Cost:** in a release build on one macOS machine, the slowest refused
  page tried took about 2.6 seconds per megabyte, and the slowest page
  tried that passes about 2.0. Both grow in proportion to the page size.
  A flat 1 MB page took about 39 ms, and about 289 ms with markup that
  calls for extra readings (`<select>`, `<noscript>`, SVG and others).
- **Citry's own browser code:** a Vue `v-html` binding counts as needing
  JavaScript, so `forbid` refuses it, and Vue builds a block it does not
  read itself (`Markup`, `<c-raw>`) inside a `<template>`, which the check
  reads.

## Fixed during the review

The reviews found these problems in the fix, and each was corrected
before the fix merged.

- **A wrong `srcdoc` reading.** The first version read a `srcdoc`
  document in one mode, but the browsers pick different modes. The check
  reads it in both (`a_srcdoc_document_is_read_in_both_modes`).
- **A cost estimate about 10 times too low.** A page with many open
  formatting elements and several readings took 10 times longer than
  estimated. One work budget now covers all readings
  (`a_page_that_needs_every_reading_while_deep_is_refused`).
- **A tag name written raw into an error message.** The tag name comes
  from the page; the message now quotes it
  (`test_a_tag_name_in_the_message_is_quoted`).
- **Fix text that named the wrong problem.** Each case now has its own
  fix text, chosen by a `case` code
  (`noted_tags_carry_the_case_that_names_the_fix`). The code first shared
  the field that holds an attribute name; a reviewer recommended its own
  field, so each ordinary finding that the Rust check returns to Python
  has eight fields (an `element` finding has ten), which the Python code
  reads
  (`test_check_output_html_returns_only_what_the_rules_report`).
- **A doctype rule wider than needed.** It refused a `<table>` inside a
  `<p>` under doctypes on which the parsers agree. It now covers only
  those where they differ
  (`a_table_in_a_paragraph_is_noted_only_where_html5ever_picks_another_mode`).
- **A reused list with an out-of-date flag.** The reused list of open
  elements could keep an out-of-date flag, so one refusal could be missed
  at an end tag. The list is now dropped when the flag changes. No missed
  script was found.
- **Smaller problems.** A tag found by two readings was listed twice
  (`a_tag_two_readings_find_is_reported_once`), and some docs did not
  match the code.

## Not tested

- WebKit and other browsers (only Chromium and Firefox were used), and a
  browser in a Japanese locale.
- Real integrations: a real htmx page (htmx swaps server HTML into an
  open page), an Events `Render` response (an answer to an event call
  that inserts HTML into the open page) end to end, hydration (Vue
  attaching to a server-rendered page), and render caches. Whether any
  Vue page that carries the runtime can pass `forbid` is also untested;
  the reviewers tried `v-html`, `v-text` and `Markup`.
- Bulk and unusual inputs: `data:` documents in bulk or opened by
  navigation (only the known pages ran there), a 4 MB page timed end to
  end (the timings are for 1 MB pages and the Rust crate alone),
  element kinds beyond the 20 in the placement test (one random seed),
  other `v-html` targets such as `<option>`, html5gum (the tokenizer
  behind the check) against the HTML standard's tokenizer, and
  declarative shadow roots beyond the known pages.
- The effect on `security_csp` of the skipped-character and encoding
  groups, which the advisory reasons from the code, and of the cases in
  the "other differences" group that the fix only reports under
  `security_javascript`. No browser run tested them.
- The last edits before the merge: docs, comments, the text of two
  messages and a few test changes. They did not change which pages are
  reported, and no browser run covered them.

## Follow-ups

None open. The checks do not read HTML that an app's own script sets as
`innerHTML` of an `<svg>`, `<math>`, `<table>` or table part, `<select>`
or `<form>` element, and they do not replace a Content Security Policy or
an HTML sanitizer. `docs_site/content/security.md` ("Pages read several
ways") documents both.
