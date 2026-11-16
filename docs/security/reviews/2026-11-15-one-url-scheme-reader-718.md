# One Rust reader for URL schemes on the server (#718)

- **Pull request:** [#718](https://github.com/citry-dev/citry/pull/718),
  merged 2026-11-15 (b668c34fa), a follow-up to issue
  [#601](https://github.com/citry-dev/citry/issues/601)
- **Reviewer:** a separate reviewing agent (security and technical, as
  Mechanisms 6, 7 and 8 ask, at high effort), plus a prose pass by a
  separate reviewer. The description says `docs-cold-reader` was not run,
  because no docs page or public docstring changed. This record is built
  from the pull request description, the merged change and its tests.
- **Code:** `crates/citry_html_transform/src/url_scheme.rs` (`url_scheme`,
  `url_scheme_is`); its callers in
  `crates/citry_html_transform/src/output_policy.rs` (`is_javascript_url`,
  `decode_data_url_document`, `refresh_data_url`); the Python function
  `_read_url_scheme` in `crates/citry_core_py/src/html_transform.rs`, which
  calls the Rust reader and is not public API;
  `packages/py/citry/citry/_urls.py`, which wraps it; and the Python
  callers `redirect_url_scheme` in
  `packages/py/citry/citry/ext/events/actions.py`, `_resolve_redirect_url`
  in `packages/py/citry/citry/ext/events/routes.py`, and `check_link_url`
  and `is_image_url_allowed` in
  `packages/py/citry_ui/citry_ui/components/_url.py`. Tests: the shared
  table `crates/citry_html_transform/tests/fixtures/url_schemes.json`, the
  Rust tests in `url_scheme.rs`, `test_url_scheme_readers.py`,
  `test_urls_module.py`, `test_redirect_schemes.py`,
  `test_regex_linear_time.py`, `test_serialize_security.py`,
  `test_output_policy_differential.py` and
  `e2e/test_url_scheme_browser_e2e.py` (all under
  `packages/py/citry/tests/`), `packages/js/citry-client/test/redirect-scheme.test.mjs`,
  `packages/py/citry_ui/tests/test_url_schemes.py` and
  `packages/py/citry_core/tests/test_html_transformer.py`

## Who controls the input

Seven server-side checks each had their own copy of the rule that reads a
URL's scheme (the part before the first `:`, such as `javascript`). Four
copies were in Python and three in Rust. The checks decide what a URL may
do:

- **The output checks** (the `security_csp` and `security_javascript`
  settings, and the `citry check` command) scan a finished page. They
  report `javascript:` URLs in URL attributes, and they read `data:`
  documents and meta refresh URLs (the URL in a
  `<meta http-equiv="refresh">` tag). The template author, the app's
  Python code or request data can write the URLs. The app author turns on
  the settings, which are off by default. These checks use the Rust
  copies.
- **`Redirect`** (the Events action that sends the visitor to a URL) and
  the resolver for the no-JavaScript form path (the code that turns a
  handler's redirect into a `Location` header for a plain HTML form post)
  read the scheme of the URL an event handler asks the visitor to go to. The app's Python code
  chooses it, and it may contain request data.
- **Citry UI's link and image checks** (`check_link_url`,
  `is_image_url_allowed`) read the URL passed to inputs such as
  `CButton(href=)`, `CForm(action=)`, `CAvatar(src=)` and
  `CImage(src=, srcset=, sources=)`. Request data may supply them.

What is at risk is what the browser does with the URL: it navigates to it,
loads an image from it, opens a `data:` document, or runs a `javascript:`
URL. A check that reads a scheme differently from the browser either lets a
URL that runs code through, or reports harmless text. Seven separate copies
of the rule could also disagree with each other.

Now one Rust function reads the scheme the way the browser's URL parser
does:

- It skips leading characters from U+0000 to U+0020.
- It drops tab, line feed and carriage return anywhere in the URL.
- It accepts an ASCII letter followed by ASCII letters, digits, `+`, `-` or
  `.`, up to the `:`.
- It compares letters as ASCII only.

It decodes no character references, and callers keep decoding exactly where
they did before. Python calls it through `_read_url_scheme`, wrapped once in
`citry._urls`.

The one change that users can see: `security_csp`, `security_javascript`
and `citry check` no longer report `javaſcript:`, `javascrıpt:` or
`javascrİpt:`, including when the lookalike letter is written as `&#383;`
or `&#305;` in attribute text. Browsers read these as relative URLs and run
nothing. This makes the check less strict, and the description says the 1.x
rules allow that. No URL that a browser reads as `javascript:` stops being
reported. The changelog has one entry.

Of the places in the list of where values reach the browser (Mechanism 7 in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)),
this change touches "URL attributes", "Navigation" (`Redirect` and the
no-JavaScript form path), "Embedded documents" (the `data:` document and
meta refresh readers), and "The opt-in output checks".

## How it was checked

- **One table, read by every reader.** The shared table holds 93 rows. The
  Rust tests, the binding, every Python caller, the JavaScript redirect
  test, the Citry UI browser image rule and a Playwright test all read it.
  The browser's own JavaScript copies of the rule, `redirectScheme` in
  `client.js` and `isImageUrlAllowed` in `CAvatar` and `CImage`, are not
  edited, so `runtime.js` does not change. They are tested against the same
  table.
- **A second reader as a reference.** The Rust tests compare the reader
  with a separately written reference reader over the table and over
  20,000 strings from a fixed seed. The character set includes `ſ`, `ı`,
  `İ`, U+212A (the Kelvin sign), U+000B, U+007F, U+00A0, U+FEFF and U+200B.
- **The `data:` readers.** A test locks their answers. Before locking
  them, the author ran the same inputs through the code on `origin/main`
  and through the branch, and the answers were identical.
- **Real browsers, by the author.** The new Playwright test ran on
  Chromium, Firefox and WebKit: 24 passed. It clicks links whose schemes
  use the lookalike letters and checks that nothing runs, next to a control
  link that does run. It runs the table against two base URLs. Firefox
  refuses to parse `da\tta:` and `da\nta:` at all, so they load nothing,
  and the test allows that for those two rows only. The test runs in the
  existing PR end-to-end job (Chromium) and in the weekly three-browser
  run.
- **Real browsers, by the reviewer.** The reviewer ran Playwright probes in
  all three browsers: about 110 raw URLs, 33 entity-encoded attribute
  texts, and an iframe run test. It found no case where a browser reads a
  scheme that the reader does not. The description does not record browser
  versions.
- **Old and new Python readers.** The reviewer compared them over 200,000
  strings and found no differences apart from the three lookalike
  spellings.
- **Differential test of the output policy.** The output-policy tests
  compare the Rust checks with a Python reference. The author ran them with
  `CITRY_OUTPUT_POLICY_DIFFERENTIAL=1`, and they passed. The Python
  reference regex there is now ASCII-only. The page generator rarely picks
  the lookalike letters, so most generated URLs still read as
  `javascript:` and the test keeps its positive cases.
- **Timing.** A one-off measurement, not committed: `check_output_html` in
  a release build on a 470 KB page with 10,000 URL attributes took a median
  of 9.57 ms and 9.66 ms after the change, against 9.71 ms and 9.76 ms
  before. The budget was 5%.
- **The author's runs.** `cargo test -p citry_html_transform -p
  citry_core_py`, `cargo clippy` and `cargo fmt` passed.
  `scripts/check.py --profile fast` passed every phase, but it ran before
  the review edits. After them, the author reran the focused Rust, Python
  and JavaScript checks and `mypy` (also with `--platform linux`), which
  were clean.
- **Other frameworks' advisories (Mechanism 8).** The reviewer read the
  maintainers' private survey of security bugs published for other
  frameworks (Mechanism 8 in `CLAUDE.md`) and checked these kinds: script
  from URLs (`xss-url`), script from SVG URLs (`xss-url-svg`), sanitizer
  bypass (`sanitizer-bypass`), open redirects (`open-redirect`), slow
  regular expressions (`redos`), header injection (`header-inj`) and URL
  handling in the browser client (`client-url`). The change introduces
  none of them.
- **Prose pass.** A separate reviewer found six wrong or stale facts and
  eleven wording problems in the change. All were fixed.

## Ruled out

- **Two checks reading one URL differently.** Every server-side check
  named above calls the one reader.
- **A browser reading a scheme that the reader does not.** The reviewer's
  probes and the table run in three browsers found none. For the lookalike
  letters, the browsers read a relative URL and run nothing, and the control
  link in the Playwright test shows the test can see a link that does run.
- **A change in the answers of `Redirect`, the Events redirect resolver,
  Citry UI and the `data:` readers.** The description says they keep
  their exact answers. `decode_data_url_document` and `refresh_data_url`
  keep their own trimming and slicing and ask the reader only whether the
  scheme is `data`.
- **A new slowdown.** `url_scheme_is` stops after it reads the name and the
  character after it, so a long scheme costs no more than the name. The
  timing run showed no slowdown. A Python-level timing test now covers long
  input, because the Redirect regex left the regex timing test.
- **Decoding character references twice, or not at all.** The reader
  decodes none. Callers keep decoding where they did before
  (`decode_html_attribute`, `attribute_text` and
  `_written_attribute_text`).
- **Citry UI relying on a private module that changes.**
  `tests/test_urls_module.py` locks the names and signatures of
  `citry._urls` for 1.x, because Citry UI imports the module.

## Fixed during the review

- `docs/design/trust_boundaries.md` had stale line numbers in rows whose
  files this change moved. They were updated.
- `citry._urls` and `url_scheme.rs` overclaimed "every server-side check".
  They now name the callers.
- The end-to-end test accepted any URL that failed to parse, and its
  `https:` base could hide a relative row. It now runs against two bases and
  allows parse failures only for the two named Firefox rows.
- The Rust table test could skip a row written over several lines without
  noticing. It now counts every row in the file.
- Removing the Redirect regex from the regex timing test left no
  Python-level timing test for long input. One was added.
- The prose pass removed the stale "#697 exception" row from
  `docs/design/trust_boundaries.md`, which #697 asked to delete on merge,
  and fixed the six wrong facts and eleven wording problems.
- The review left one item as it was: Citry UI's table test repeats the
  `data:image/` rule it tests. The scheme and the rest still come from the
  table, so the reader itself is tested.

## Not tested

- **Browser versions and other browsers.** The Playwright runs use
  Chromium, Firefox and WebKit. The description records no versions. No
  other browser was used.
- **The full fast profile after the review edits.** The profile passed
  before them. After them only the focused Rust, Python and JavaScript
  checks and `mypy` ran.
- **The `pyodide-smoke` job.** This CI job runs Citry on Pyodide (a
  Python runtime built for WebAssembly). It builds `citry`
  and `citry-ui` from the checkout but installs the published `citry-core`
  named in `docs_site/static/playground/runtime.json` (2.0.0). `citry._urls`
  imports `_read_url_scheme` at module level, and 2.0.0 lacks it, so the
  job fails on this pull request and on later ones, until the docs release
  after 1.0.0 updates `runtime.json`. It is not a required check. The
  required checks (`check`, `citry-ui-wheel-build`) use the `citry-core`
  wheel built from the checkout.
- **The timing result.** It is a one-off measurement on one page shape, not
  a committed test.

## Follow-ups

- [#601](https://github.com/citry-dev/citry/issues/601): whether Citry
  checks the scheme of link URLs set through `c-bind`. It stays open.
