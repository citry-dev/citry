# Citry UI link checks on `Markup` URLs (GHSA-gg8q)

- **Advisory:**
  [GHSA-gg8q-qfwj-j6p4](https://github.com/citry-dev/citry/security/advisories/GHSA-gg8q-qfwj-j6p4),
  published 2026-11-16, severity medium (CVSS 3.1 score 4.7)
- **Affected and fixed versions:** `citry-ui >= 0.4.0, < 0.6.0`; fixed in
  `citry-ui` 0.6.0
- **Fix:** [#697](https://github.com/citry-dev/citry/pull/697), merged
  2026-11-15 (`aed98a905`). Every Citry UI URL check reads the value
  through Citry's own attribute writer, so a `Markup` URL is checked as the
  text the page gets. The same pull request makes `citry`'s
  `security_javascript="omit"` setting read `Script` and `Style` URLs the
  same way.
- **Reviewer:** a separate reviewing agent (a security pass in Chromium and
  the advisory survey). This record is built from the pull request
  description, the merged change and its tests.
- **Code:** `packages/py/citry_ui/citry_ui/components/_url.py`
  (`attribute_text`, called from `check_link_url` and
  `is_image_url_allowed`), `components/cbutton/cbutton.py` (the
  `formaction` check in `attrs`), and
  `packages/py/citry/citry/_javascript_policy.py`
  (`_written_attribute_text`); tests in
  `packages/py/citry_ui/tests/test_url_schemes.py` and
  `packages/py/citry/tests/test_serialize_security.py`

## Who controls the input

Since 0.4.0, Citry UI checks the URLs passed to its link and form inputs,
such as `CButton` `href`, and allows only a relative URL or an `http:`,
`https:`, `mailto:`, `sms:` or `tel:` URL. A `Markup` value says that its
text is already HTML, so when Citry writes it into an attribute it decodes
the character references in it (codes such as `&amp;` that stand for a
character). Before the fix, the check read the text
before that decoding. So a URL whose scheme was spelled with character
references was read as a relative URL, and the page got the decoded
scheme. The advisory names the inputs that wrote the decoded text.

The inputs, by who first supplies them:

- **A `Markup` URL passed to `CForm` `action`, to `formaction` in `CButton`
  `attrs` or `CSplitButton` `primary_attrs`, or to `CButton` `href`.**
  The app's Python code supplies the URL, and may pass along request or
  stored data, which counts as the data's source. This happens when an app
  marks a stored URL as safe, for example with `Markup(value)` or Django's
  `mark_safe(value)`. The browser navigates to the URL when a visitor
  clicks the link or submits the form. `CButton` `href` was affected only
  on a page rendered with `deps_strategy="simple"` or `"ignore"`; with the
  default strategy a `Markup` `href` already raised `TypeError`.
- **A plain `str` URL.** It is written as typed, so the check always read
  the same text as the page.
- **The other Citry UI URL inputs** (`CListItem`, `CMenuItem`,
  `CPagination`, `CBreadcrumbItem`, `CNavigationMenuLink`, `CAvatar` and
  `CImage`). They copy a `Markup` value to a plain string before they check
  and write it, so the page shows the text as typed.
- **A `Script` or `Style` dependency URL in `citry`.** The app's code
  writes it. With `security_javascript="omit"`, a `Markup` URL was reported
  but left on the page (`warn` and `forbid` already caught it through
  the whole-page check). Browsers do not run a `javascript:` URL in
  `<script src>` or `<link href>`, so this was fixed without an advisory.

Of the places in the list of where values reach the browser (Mechanism 7 in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)),
this change touches "URL attributes" and "The opt-in output checks".

## How it was checked

- **The check reads what the writer writes.** `attribute_text` runs
  Citry's own attribute writer and undoes only its escaping, so the check
  reads the text the page gets and follows the writer when the writer
  changes.
- **A real browser.** The reviewer rendered each affected input in
  Chromium with about 38 spellings of a scheme, and read the URL the
  browser built from the element's `href`, `action` or `formAction`
  property. Before the fix a refused scheme reached the page on all four
  inputs; after it, on none.
- **Every route to the page.** The reviewer followed each URL through the
  server-rendered HTML, the data Citry sends to Vue on an interactive
  page, `attrs=` arguments and cached renders.
- **The new tests.** `test_url_schemes.py` sends schemes spelled with
  decimal, hexadecimal and named character references, letters written as
  character references, and mixed letter case through every link and image
  input. It also checks that an ordinary `Markup` URL is still accepted and
  written with the exact text expected, and that the other URL inputs write
  a `Markup` value as typed. `test_serialize_security.py` covers `Script`
  and `Style` dependencies with `security_javascript="omit"`. The tests for
  spelled schemes and for `Script` and `Style` in `omit` mode fail on the
  code before the fix.
- **The author's runs.** The focused suites passed (`test_url_schemes`,
  `test_serialize_security`, `test_output_policy`, and the `CButton`,
  `CForm`, `CSplitButton`, `CImage` and `CAvatar` tests). The `citry` and
  `citry_ui` suites without the browser tests passed, apart from a type
  check test that fails the same way on `main` in the author's
  environment, and a package metadata test that read an out-of-date
  install in the shared environment. `ruff`, `mypy` (also with `--platform
  linux`) and `rustfmt` on the one changed Rust doc comment passed.
- **Other frameworks' advisories (Mechanism 8).** The reviewer read the
  maintainers' private survey of security bugs published for other
  frameworks (Mechanism 8 in `CLAUDE.md`) and checked these kinds: URL
  schemes that run code, a second render path that skips a check,
  `srcset`, and a check that decodes text differently from the browser.
  The change introduces none of them.

## Ruled out

- **A spelling the check reads differently from the browser.** The check
  reads the text Citry's writer produces, with its escaping undone. The
  browser also turns NUL into U+FFFD and a carriage return into a line
  feed, and neither change can make a refused scheme read as an allowed
  one.
- **The Vue path.** For `CForm` `action` and `formaction`, Citry also
  decodes `Markup` in the data it sends to Vue. The check reads the same
  decoded text, so both paths get the same answer.
- **Refusing too much.** Ordinary `Markup` URLs are still accepted, and the
  tests check the exact URL written.
- **Image inputs.** `is_image_url_allowed` reads the URL the same way. An
  `<img>` runs no script, so the image inputs were not part of the
  advisory.
- **URLs written by the template author or the app's own code.** Those are
  not at risk. The advisory tells apps to pass a plain `str`, since a URL
  is not HTML.

## Fixed during the review

- A `Script` attribute holding an object other than `str` with an
  `__html__` method skipped the decoding. It is now read the same way.
- A comment said the unescaped text is exactly what the browser reads,
  which was too strong. It now says how the browser's reading differs and
  why that cannot let a scheme through.
- The tests that an ordinary `Markup` URL is accepted only proved that
  nothing raised. They now check the exact URL written. A test for
  `Script(url=Markup(...))` was added.
- The Rust doc comment of `_classify_dependency_attribute` and the
  changelog entries were reworded.

## Not tested

- Firefox and WebKit. The browser run used Chromium only, and the
  description records neither the Chromium nor the Python version.
- The full repository gate and the browser end-to-end tests were not part
  of the author's runs.

## Follow-ups

- [#718](https://github.com/citry-dev/citry/pull/718) later moved the
  server's scheme reading into one Rust function, and Citry UI's checks
  build on this change
  ([its record](2026-11-15-one-url-scheme-reader-718.md)).
- The review noted three places with the same cause that are not security
  problems: `validate_html_id` reads a `Markup` id before decoding, which
  can give a broken id; the check that reads a `<script>`'s `type` to
  decide whether Citry wraps its code reads a `Markup` `type` before
  decoding; and the copy of `CAvatar`'s `img_attrs` that Citry UI's
  browser code uses does not decode `Markup`, while the server HTML
  does. No public issue tracks them yet.
