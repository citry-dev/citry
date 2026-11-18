# Output checks, `</form>` and `data:` documents (GHSA-3qv5)

- **Advisory:**
  [GHSA-3qv5-4p87-mxfr](https://github.com/citry-dev/citry/security/advisories/GHSA-3qv5-4p87-mxfr),
  published 2026-11-18, severity medium (CVSS 3.1 score 4.7)
- **Affected and fixed versions:** `citry >= 0.4.0, < 1.0.1`, fixed in
  1.0.1; `citry-core >= 1.8.0, < 2.1.1`, fixed in 2.1.1
- **Fix:** `dff629dfd`, committed to `main` 2026-11-18. The opt-in
  output checks read a page with a `</form>` the way Chromium, Firefox
  and WebKit (the engine Safari uses) each build it, and report a script
  that any of these readings finds. They read an HTML `data:` document
  both with and without the tabs and line breaks written in it, count a
  `data:` document that a frame, link, form or refresh opens as running
  code unless its type is on a short list, and read the `href` of a
  MathML element as a link. `citry` 1.0.1 requires `citry-core` 2.1.1.
- **Reviewer:** separate reviewing agents in four rounds, each with a
  security brief, an advisory-survey check and a prose pass; the fix
  author ran each reviewer's harnesses again on every revision
- **Code:** in `crates/citry_html_transform/src/`, `output_scanner.rs`
  (the readings: `feed_form_end_tag`, `chromium_ignores_form_end`,
  `for_each_reading`, `tree_builder_for`) and `output_policy.rs` (the
  rules: `data_url_requires_javascript`, `decode_data_url_document`,
  `opens_document_url`, `follows_mathml_href`, `declared_type_may_run`,
  `chromium_data_url_document`), with the Rust tests in those files; the
  Python reference copy in
  `packages/py/citry/tests/_output_policy_reference.py`, and
  `test_output_policy_differential.py` and `test_serialize_security.py`
  in `packages/py/citry/tests/`; the scope statement in
  `docs_site/content/security.md`

## Who controls the input

The output checks (the `security_javascript` and `security_csp`
settings) read the HTML a page sends and report scripts, event handlers
and `javascript:` URLs in it. With `security_javascript="forbid"`, such
a page raises `ValueError`. An earlier advisory
([GHSA-7qpw](2026-11-14-output-checks-and-escaping-ghsa-7qpw.md)) made
the checks read a page each way browsers are known to differ on. This
review found more differences:

- **A `</form>` inside a `<template>`.** Chromium handles it differently
  from the HTML standard in a `<template>` written in the page, including
  a declarative shadow root, whose contents show as soon as the page
  loads. WebKit handles it differently in HTML a script sets on a
  `<template>`. Chromium also builds a different tree when a `<noscript>`
  and a `</form>` meet in such HTML. Both checks passed these pages.
- **`data:` documents.** `security_javascript` treated a `data:` document
  as harmless when its type is one browsers show as text, an image,
  media, a font or a download. WebKit renders a `data:` document as HTML
  when it cannot display the type, including a harmless-looking type
  written with a control character. Chromium keeps a tab or line break
  written inside a `data:` URL, which the check removed. WebKit and
  Firefox open the `href` of a MathML element like a link's, and the
  check did not read that URL. A script in such a document runs in a
  separate origin, but it can navigate the page or open windows.

The inputs, by who first supplies them:

- **The HTML.** It comes from `Markup` (a string Citry writes as HTML
  without escaping it), a `<c-raw>` block (a template block Citry writes
  as written), or an HTML sanitizer's output that the app passes through
  one of these. When that HTML holds user content, the user supplies it.
  Escaped values cannot write any of these shapes.
- **The setting.** The app turns the check on and relies on it to refuse
  such HTML. An app that does not set it is not affected by this
  advisory.

Of the places in the Mechanism 7 list in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser),
this change touches "Text and markup", "URL attributes", "Embedded
documents", "The opt-in output checks" and "Parser rules browsers differ
on". The same pull request as this record adds the new cases to "URL
attributes" and "Parser rules browsers differ on".

## How it was checked

- **Browsers.** Playwright 1.65.2 builds of Chromium 159.0.8154.6,
  Firefox 159.0 and WebKit 27.2 on macOS. Each run watched both the tree
  the browser built and whether a marker handler ran, and each batch held
  a sample of pages that 1.0.0 passes and the fix refuses, to show that
  the harness sees a miss.
- **Releases.** `citry` 1.0.0 with `citry-core` 2.1.0 was run end to end
  in the browsers, including served pages with a `Markup` value under
  `forbid`. The check alone, without a browser, ran on `citry` 0.4.0,
  0.4.1, 0.4.6, 0.5.0, 0.5.1 and 0.6.0 to 1.0.0. The range of the
  Chromium `data:` case was read from the release tags.
- **Placements.** A whole document, a host page's body, `innerHTML` of a
  `<div>`, `innerHTML` of a `<template>` whose contents are then added to
  the page, a `<template>` and a declarative shadow root written in the
  page, an `iframe srcdoc` document, and `data:` documents nested up to
  three deep.
- **What opened the `data:` documents.** Frames, `<object>` and
  `<embed>` with and without a declared type, links and forms that target
  a frame (clicked), a refresh inside a `srcdoc` document, SVG link
  animations, and MathML `href` (clicked).
- **Generated pages.** In each round, generators built batches of
  thousands to tens of thousands of strings: shadow-root and template
  pages, table and form pages, SVG and MathML templates and `data:`
  URLs. In the batches run on the last versions of the fix, no string
  that the check passed ran a handler.
- **Hand-built pages.** 1,214 WebKit pages crossing 10 types, 15
  spellings and 35 ways to open a document; 36 types and 2 controls on
  17 ways in all three engines; dozens of Chromium `data:` and
  `<noscript>` pages; and a list of tag names checked against Chromium's
  `</form>` rule.
- **Tests on the final code.** The crate's 115 unit tests and its other
  test targets, with `clippy` and `rustfmt`; 14,123 Python tests with
  `CITRY_OUTPUT_POLICY_DIFFERENTIAL=1`, which compares the Rust rules
  with the Python reference copy; and 529 browser end-to-end tests in
  Chromium.
- **Debug checks.** A debug build compared the output check's shortcuts
  (counting open templates, checking the newest open element first) with
  a full read, on 1.2 million random pages in one round and 400,000 in
  the next. Every result matched.
- **Ordinary pages.** 4,621 pages (the built docs, benchmark apps,
  Django admin templates, and realistic template and shadow-root pages)
  were compared finding by finding. `forbid` changed on two pages, a PDF
  in an `<object>` and an MP4 in an `<embed>`, both on purpose.
  `security_csp` changed on none.
- **Cost.** In a release build on one machine, an ordinary 1 MB page
  still takes about 0.04 seconds. The slowest crafted pages take about 1
  to 1.5 seconds per megabyte, about 3 to 5 times the earlier worst case,
  and the time grows in proportion to page size. Citry's limit on how
  much work one check may do refuses
  one crafted shape from about 200 KB that 1.0.0 passed.
- **Other frameworks' advisories (Mechanism 8).** The reviewers read the
  maintainers' private survey of security bugs published for other
  frameworks and checked these kinds: HTML that changes meaning when read
  again (`mxss`), raw-text elements (`xss-rawtext`), sanitizer bypass
  (`sanitizer-bypass`), URLs and SVG URLs (`xss-url`, `xss-url-svg`), and
  resource use and crashes (`dos-amplify`, `dos-crash`).

## Ruled out

- **Chromium's `</form>` rule in a template or shadow root.** It has its
  own reading
  (`a_script_chromium_builds_after_a_form_end_tag_in_a_template_is_reported`).
- **WebKit's `</form>` rule in HTML set on a `<template>`,** including
  nested forms, forms in tables, and SVG or MathML elements named
  `template`
  (`a_script_hidden_only_in_a_whole_document_is_reported`).
- **`data:` types WebKit renders, and MathML `href`.** Only a short list
  of types counts as inert, with nothing but spaces around the type
  (`a_data_url_webkit_renders_as_html_is_reported`,
  `test_forbid_rejects_an_embedded_document_that_may_run_code`).
- **Tabs and line breaks Chromium keeps.** The check reads the document
  both ways, also through a refresh, character references and nesting
  (`a_data_url_chromium_reads_with_its_line_breaks_is_reported`).
- **The download exception.** `<a download>` and `<area download>` keep
  the longer list of types, also with a frame target and inside a
  sandboxed frame. An SVG link or a link inside `srcdoc` gets the short
  list (`test_forbid_passes_a_data_url_that_runs_no_code`).
- **Routes no browser runs.** Opening a `data:` document at the top
  level, `target=_blank`, `srcset`, `<param>` and a `javascript:`
  refresh ran no code in any engine.
- **Vue and Events `Render`.** `forbid` refuses every page that Vue runs
  on.
- **The Python reference copy.** It reports at most what the Rust check
  reports, so the differential test cannot hide a Rust miss.

## Fixed during the review

The reviewers found these problems in the fix before it merged. The
later rounds also found more cases that 1.0.0 passes; those are part of
the advisory above.

- The first WebKit change looked at the wrong list of open elements, so
  it missed forms that only a template had open. The template reading
  now runs at every `</form>`.
- The first change for Chromium's `<noscript>` case broke the WebKit
  reading, and 34 pages ran a handler. It was split into two readings.
- The first fix was about 9 times slower on crafted pages. Counting open
  templates and checking the newest open element first brought it down.
- The set of ordinary pages had no real template forms, and the
  differential generator never wrote `download`, real `type` values,
  control characters in types, or MathML links. All were added.
- Comments and write-ups said every browser drops tabs and line breaks
  from a URL, overstated what one function checks, and said "Safari"
  where only WebKit was tested. All were corrected.

## Not tested

- Real Chrome and real Safari, WebKit on Linux, and iOS. Only
  Playwright's builds were used, and real Safari may download some
  `data:` types that Playwright's WebKit renders; the fix treats them as
  running code either way.
- The advisory's Content Security Policy workaround was run with a nonce
  policy in Chromium and WebKit only, not Firefox, and not with a
  hash-based policy. The WebKit `<template>` case was not run under a
  nonce policy.
- Chromium HTML set on a `<template>` with a table part and the form
  rule but no `<noscript>`: no hits, but the sample that shows a miss was
  weak, so this stays unproven.
- MathML `href` with the listed types was not clicked, and the last round
  did not click the link and form routes for the Chromium `data:` case.
- Releases before 1.0.0 for the cases the later rounds found, and
  `citry` 0.4.2 to 0.4.5 at all.
- Encodings other than UTF-8, nesting deeper than three documents, real
  file bodies, the cost on another machine, Events `Render` and cached
  renders end to end.
- The last comment edits had no browser run.

## Follow-ups

None open. `docs_site/content/security.md` now lists the short set of
`data:` types and the longer download list, names Chromium and WebKit for
`<noscript>`, and tells authors to close every element inside a form
before its `</form>`. The checks do not replace a Content Security Policy
or an HTML sanitizer.
