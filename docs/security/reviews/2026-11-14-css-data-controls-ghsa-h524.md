# Control characters in `css_data()` values (GHSA-h524)

- **Advisory:**
  [GHSA-h524-84qp-7xv2](https://github.com/citry-dev/citry/security/advisories/GHSA-h524-84qp-7xv2),
  published 2026-11-14, severity medium (CVSS 3.1 score 6.1)
- **Affected and fixed versions:** `citry >= 0.7.0, < 0.8.0`, fixed in
  0.8.0
- **Fix:** `680daf87d`. The `css_data()` check refuses a control
  character outside a quoted string, and a stored `css_data()` stylesheet
  is built again from its values with the current check each time it is
  served.
- **Reviewer:** a separate reviewing agent
- **Code:** `packages/py/citry/citry/util/css.py`
  (`validate_css_var_value`, `_is_css_control`,
  `_escape_beyond_printable_ascii`, `serialize_css_var_value`),
  `packages/py/citry/citry/ext/dependencies/scripts.py` (`get_script`,
  `_rebuild_css_data_stylesheet`, `_css_vars_capture`) and
  `packages/py/citry/citry/ext/dependencies/emission.py`
  (`_resolve_records`); tests in
  `packages/py/citry/tests/test_css_data_refusals.py` and
  `packages/py/citry/tests/e2e/test_css_data_tokens_e2e.py`

## Who controls the input

A component's `css_data()` method returns values that Citry writes into
a stylesheet as CSS custom properties (for example `--color: red;`). Citry
checks each value so that it stays inside its own declaration. Before the
fix, the check read the text as the app passed it. Citry then wrote
control characters as CSS hex escapes (a backslash and hex digits, such as
`\1 `, that CSS reads as one character). The browser reads such an escape
as part of an identifier (a name, such as a property or function name).
For some values the check's reading and the browser's reading split the
text into different pieces, so text the check had accepted inside a URL
was CSS to the browser. That could add a page-wide rule.

Request or stored data that the app passes to `css_data()` is the first
source of the value. A value that only the template author or the app's
own code writes is not at risk. The
browser applies the value as CSS, so the risk is restyling the page,
hiding content, or loading images from another site. The advisory reports
that the rule did not run JavaScript in the tested browsers and that a
value cannot end the `<style>` element.

Of the places in the list of where values reach the browser (Mechanism 7
in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)),
this change touches "CSS", and it also covers a stylesheet that Citry
reads back from a cache.

## How it was checked

The review compared what the check reads with what a browser reads, and
tests cover the linked and inline paths by which a stylesheet reaches the
page, with and without a configured cache. A few terms first. The
serializer is the function that turns a Python value into CSS text. A
token is one piece CSS is cut into, such as a name, a string or a URL. A
fuzz is a script that loads many generated values, and its harness is the
program that loads them into the browsers.

1. **Reproduction.** A probe printed the serializer's output for a value
   made of one control character in front of a URL-like text, for six
   control characters. On the code before the fix the check accepted each
   and wrote an escape. After the fix it refuses each, with a
   `ValueError` that names the character and its offset. The advisory
   reports that Chromium 156 and Firefox 157 applied the added rule from
   the unfixed output.
2. **Property test.** A test that feeds many random inputs,
   `test_css_data_escape_leaves_the_browser_reading_the_tokens_the_check_read`,
   gives 60,000 random values to the serializer. It records the exact text
   the check read, splits that text and the escaped text into tokens with
   a reference CSS tokenizer written in the test file, and requires equal
   lists. It also requires that more than 1,000 of the values changed when
   escaped, so the comparison is not empty.
3. **Browser fuzz.** A harness built 97,799 values
   that the fixed check accepts. Each puts one of 40 boundary
   prefixes (ASCII and Unicode spaces, control characters,
   non-ASCII letters and symbols, name and number starts) in front of
   `url(`, `var(`, `calc(`, a bracket or nothing, followed by bodies with
   comment, brace, quote and escape text, and tails that would end a
   declaration. Each value was loaded as one custom property in its own
   rule, in Chromium and Firefox. The harness flags a sheet that holds
   anything other than that one rule with the next property intact, and a
   changed page background. Result: 0 mismatches in each browser. The
   same harness flagged the code before the fix. A further 30,000 random
   values went through the same harness in both browsers, also with 0
   mismatches.
4. **Browser test in the repository.** `test_css_data_tokens_e2e.py`
   serves Citry's own stylesheet route for three accepted values (a
   control character in a string, DEL (U+007F) in a string, a non-ASCII
   letter in front of a function) and requires that the page keeps its
   color and the sheet keeps one rule with the next property intact.
   `test_the_page_turns_green_when_an_escape_changes_the_tokens` is the
   positive control: it writes an unchecked escaped control character by
   hand, and the page does change color. Without the control, a passing
   run could not tell "no break" from "the test cannot see a break".
5. **Refusal and cache tests.** `test_css_data_refusals.py` adds six
   refused values that put a control character in different places
   outside a string (before `url(`, DEL before `url(`, a unit separator
   (U+001F) before `url(`, between two names, after a bracket, and before
   a `url(` that holds comment text). Further tests cover the stored
   stylesheet: it is built again from its values; an entry with no
   stored values, with values the current check refuses, or with values
   that do not match the hash in the URL gives 404; a page inlines the stylesheet its
   own render built, when it has one, not what the cache holds; and a
   stored render-cache entry written by an earlier version is refused.

## Ruled out

- **A control character inside a quoted string:** the escape stays part
  of the string for the browser, so the check still accepts it there.
  Two of the three browser-test values cover this (a control character
  and DEL).
- **A non-ASCII character before a function name:** the check reads it as
  part of a name and so does the browser, so an escape for it cannot move
  a boundary. The third browser-test value covers this.
- **An older stylesheet served from a shared cache** (a cache that
  several server processes read and write): a stylesheet stored
  by 0.7.0 holds only text. The route treats such an entry as missing
  and builds the stylesheet from stored values only, with the current
  check. A page that inlines a stylesheet uses the copy its own render
  built when it has one, so another process rewriting the cache entry
  cannot change what the page inlines. The cache tests in step 5 cover
  each case.
- **Ending the `<style>` element or writing outside the stylesheet:** the
  check already refuses `</style` and `<!--` anywhere in a value, and the
  fix does not change that.

## Fixed during the review

Nothing recorded.

## Not tested

- WebKit and other browsers. The advisory's reproduction used Chromium
  156 and Firefox 157; the fuzz used Chromium and Firefox, and no other
  browser was used.
- The tokenizer in the property test is a re-implementation of the CSS
  rules, not a browser. This review did not test the stylesheet on a page
  that declares a non-UTF-8 encoding. An earlier change's browser test,
  `packages/py/citry/tests/e2e/test_css_data_charset_e2e.py`, covers
  pages in GBK, Big5 and other encodings. The cache tests use the
  in-memory cache, not a shared one such as Redis.
- The fuzz in step 3 loads each value into a hand-written rule. It does
  not render a component. The browser test in step 4 renders and serves
  the linked stylesheet only; the inline path and the stored render cache
  are covered by Python tests. A reviewer's program also loaded inline and
  linked stylesheets in browsers, with and without a cache; it kept no
  output, and the reviewer reported those routes safe. The Vue path was
  checked by reading the code, not in a browser.
- No test replays a stale render-cache entry through a full render. The
  test covers the function that reads the stored stylesheet
  (`_capture_from_wire`).
- A rolling deploy with several processes on different versions. The
  advisory and the changelog tell users to upgrade every process that
  shares the cache; the behavior in that window was not tested.

## Follow-ups

None.
