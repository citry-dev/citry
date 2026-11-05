# Move to html5gum 0.9.1 (#614)

- **Pull request:** [#614](https://github.com/citry-dev/citry/pull/614),
  merged 2026-11-05 (68079171c)
- **Reviewer:** a separate reviewing agent
- **Code:** the HTML reader in `crates/citry_html_transform/src/`:
  `tokenizer.rs` (`run_tokenizer`, where every html5gum run starts),
  `output_scanner.rs`, `html_limits.rs` and `static_html.rs`; tests in
  `crates/citry_html_transform/tests/attribute_runs.rs`,
  `crates/citry_html_transform/tests/html_limits.rs`,
  `packages/py/citry/tests/test_html_attribute_runs.py`,
  `packages/py/citry/tests/test_output_policy.py` and
  `packages/py/citry/tests/test_output_policy_differential.py`

## Who controls the input

html5gum is the library that splits HTML text into tags, attributes and
text. Citry runs it over three kinds of HTML:

- the HTML of a rendered page, for the opt-in output checks
  (`security_csp` and `security_javascript`);
- each `Markup` or `<c-raw>` fragment;
- the server HTML that Citry checks before Vue's browser code takes it over
  (hydration).

The template author writes most of that HTML. But request data and stored
data can reach it too, for example as HTML an app marks safe with `Markup`.
So anyone whose text reaches a page can control what html5gum reads,
including a tag with a very long run of attributes.

This change moves Citry from a patched copy of html5gum 0.8.4 to the
released 0.9.1. Two things could go wrong:

- html5gum 0.9.1 could read some HTML differently from the old copy. The
  output checks must read HTML the way the browser does, so a different
  reading could let code through or refuse harmless text.
- A start tag with a very long run of `name="value"` attributes could
  overflow the stack and stop the whole process. Citry 0.7.0 carried a copy
  of html5gum with one line changed to prevent that
  ([GHSA-vgc3-4q38-q7vf](https://github.com/citry-dev/citry/security/advisories/GHSA-vgc3-4q38-q7vf)).
  With the copy deleted, html5gum 0.9.1 itself has to prevent it.

## How it was checked

The change was compared with the old build, not only checked by the tests.
Comparisons 2, 4 and 5 give the old build (the patched copy) and html5gum
0.9.1 the same inputs. Comparisons 1 and 3 run the existing tests, and
comparison 6 tests the stack. The pull request description lists all six,
and an independent review added comparison 4.

1. **Crate tests.** `cargo test -p citry_html_transform` before and after,
   with the same counts, including `attribute_runs` and `html_limits`. The
   cases in `attribute_runs.rs` are unchanged (only its comments changed),
   and no assertion was edited to fit.
2. **Citry's own functions.** The same crate source was built once against
   each version and read 24,584 HTML-looking strings taken from this
   repository, plus 200,000 random strings built from tag-like pieces. For
   each string the test program compared `scan_output_html`,
   `validate_html_fragment_boundary`, `static_html_node_count`,
   `static_html_in_context` (3 contexts, 2 uses) and `check_output_html`
   (4 sets of options).
3. **Python tests.** The pytest phase of
   `scripts/check.py --profile fast` (`-m "not e2e and not qualification"`)
   ran against an extension built from the branch: 17,894 passed, 238
   skipped, 1 expected failure. That includes `test_html_attribute_runs.py`
   and `test_output_policy.py`. It also includes
   `test_output_policy_differential.py`, which runs with
   `CITRY_OUTPUT_POLICY_DIFFERENTIAL=1` and compares the Rust rules with
   the Python copy of them.
4. **Trees and text runs.** About 1.1 million cases compared the DOM trees
   (the element trees the browser builds from HTML) built for the hydration
   and static HTML checks, the text runs, and the `<template>` fragment
   parse. They covered every raw-text tag (a tag whose content the browser
   reads as plain text, such as `<script>` and `<style>`) crossed with
   about 40 tag endings, comment forms, CDATA, `<svg>` and `<math>`, and
   tags of up to 100,000 attributes.
5. **html5gum's own events.** The test program compared every event
   html5gum reports (kind, bytes, errors and spans, the byte positions of
   the event in the input) in all six states html5gum's tokenizer can
   start in. The tokenizer is the part that splits the text into tokens. It
   covered 15,681,960 cases, one for every string up to 5 characters over a
   19-character alphabet, and 6,000,000 random cases.
6. **Stack use.** A thread with a 128 KiB stack read 20,000 repeats of each
   of 22,641 short units (every string of 1 to 4 characters over 12
   tag-related characters, plus hand-picked ones) and of each of 7,056
   pairs of realistic fragments, behind 11 different prefixes. None
   overflowed. The same sweep against unpatched html5gum 0.8.4 overflows on
   5 of the units, so the sweep can detect the problem.

## Ruled out

- **A different reading of HTML:** comparisons 2 and 4 found no difference
  in anything Citry returns or in the trees it builds. In comparison 5 the
  events and errors were identical in all cases; only two spans differed
  (see below). So on every input tried, the output checks, the fragment
  check and the hydration checks gave the same results as before. The size
  limits in `html_limits.rs` are untouched, and the `html_limits` tests give
  the same results.
- **The stack overflow:** since 0.9.1
  ([html5gum#158](https://github.com/untitaker/html5gum/pull/158)),
  html5gum returns to its main loop between two attributes, so the stack a
  run needs should not grow with the tag. Two checks test that.
  `attribute_runs.rs` reads a tag with 100,000 attributes on a 128 KiB and
  an 8 MiB stack, and it fails with a crash if a release nests again.
  Comparison 6 repeats short pieces of HTML 20,000 times on a 128 KiB
  stack. Both pass. The root `Cargo.toml` pins html5gum to exactly
  `=0.9.1`, so a later release enters only through a deliberate upgrade.
- **Two span differences:** the spans differ in two cases, and both are
  span fixes in the html5gum 0.9.0 changelog:
  - an unquoted attribute value, as in `<a b=xyz>`, now starts at its
    first byte; it used to start one byte late
    ([html5gum#146](https://github.com/untitaker/html5gum/pull/146));
  - text that runs to the end of the input in a character reference, or
    inside a tag read as plain text such as `<textarea>`, `<style>` or
    `<script>` (html5gum calls these the RCDATA, RAWTEXT and script data
    states), now ends at the last byte; it used to end one byte early
    ([html5gum#148](https://github.com/untitaker/html5gum/pull/148)).

  Citry reads neither span. `output_scanner.rs` works out every attribute
  value span again from the source text (`repair_attribute_value_spans`),
  and it ignores the span of a text event.
- **Slower reading of large pages:** a slower reader would cost the server
  time on every page when the output checks are on. On a 1.87 MB page in a
  release build on an Apple M-series Mac, best of 15 runs,
  `scan_output_html` took 33.0 ms before and 30.8 ms after,
  `check_output_html` about 35 ms and 32.5 ms, and `static_html_node_count`
  30.0 ms and 27.8 ms. That is one machine and one page; other machines
  are under "Not tested".
- **Advisory checks on html5gum:** html5gum is now an ordinary crates.io
  crate, so the cargo-deny advisory check (the CI step that fails on a
  known advisory in a locked Rust crate) covers it. The old copy was a path
  dependency, which that check skips. The wheel's `LICENSE-html5gum` is the
  0.9.1 crate's own `LICENSE`. A test compares its SHA-256 with a recorded
  digest for the locked version, so a version change fails that test until
  someone checks the new license.

## Fixed during the review

Nothing recorded.

## Not tested

- Speed on x86_64, where html5gum 0.8.4 searched bytes with the `jetscii`
  crate, which uses SSE4.2 instructions. html5gum 0.9.1 uses a portable
  search and Citry does not enable `jetscii`. That search was not tested on
  a big-endian target either (the release wheels include s390x).
- Behavior against a real browser. No comparison used a browser. They
  compare the new build with the old one, run existing tests, or test the
  stack.
- The rest of the fast profile of `scripts/check.py` (its pnpm,
  JavaScript, pyright and Vue render parity phases), `cargo test` for
  crates that do not depend on html5gum, the browser and qualification
  tests, and the release workflows. The local disk was nearly full, so
  only `cargo test` for `citry_html_transform` and `citry_vue_compiler`,
  and the Python tests, ran.

## Follow-ups

None.
