# A Django `SafeString` in attributes and `#c-key` (GHSA-v7q5)

- **Advisory:**
  [GHSA-v7q5-qfrw-rhqc](https://github.com/citry-dev/citry/security/advisories/GHSA-v7q5-qfrw-rhqc),
  published 2026-11-18, severity medium (CVSS 3.1 score 4.7)
- **Affected and fixed versions:** `citry >= 0.1.0, < 1.0.1`; fixed in
  1.0.1
- **Fix:** `e5a191a2a`, committed to `main` 2026-11-18. Citry escapes a
  `SafeString` in every attribute, as it already escaped `Markup`, and
  writes a `SafeString` `#c-key` value (the key Citry uses to track a
  repeated element) as escaped text. A component with Vue bindings now
  renders such a value, where it raised `TypeError` before.
- **Reviewer:** two separate reviewing agents, each with a technical,
  security, advisory-survey and prose pass; the second also ran the
  browser pages again
- **Code:** in `packages/py/citry/citry/`, `util/html.py` (`exact_str`,
  `decode_attribute_entities`, `escape_attribute_value`), `attrs.py`,
  `nodes/__init__.py` (`ElementKeyNode.render` and the key paths in
  `ComponentNode`), `_vue/capture.py` and `_vue/leaf_program.py` (the
  element key); tests in
  `packages/py/citry/tests/test_attribute_safe_string_subclass.py`

## Who controls the input

A Django `SafeString` is the value that `mark_safe()` and
`format_html()` return. Like `Markup`, it has an `__html__` method, the
marker for HTML that may be written as it is. Citry escapes every value
that a template writes into an attribute, trusted HTML included, so a
`"` in it cannot end the attribute.

The escape first turned a trusted value into plain text with `str()`.
But `str()` of a `SafeString` returns the same `SafeString`, so the
value kept its marker and passed the escape. The same held for any value
whose `str()` keeps `__html__`, such as a lazy translation wrapped in
`mark_safe()`. In 0.1.0 to 0.5.1, every value with `__html__`,
`Markup` included, was written into attributes as it was.

The inputs, by who first supplies them:

- **The attribute.** The template author writes `c-<name>`, `c-bind`
  or `<c-element>`; the app's Python code calls `format_attrs()`; an
  extension adds attributes through `on_attrs_resolved`; or the app
  passes Citry UI `attrs=`. In 0.6.0 to 1.0.0 all of these wrote the
  value unescaped. `#c-key` on an HTML element did so only in the
  renders that
  [GHSA-gv5c](2026-11-18-node-path-attribute-markup-ghsa-gv5c.md)
  lists: the renders that run the template's Python nodes directly (the
  node path), such as `str(slot)` after the page render.
- **The value.** The app's Python code marks it safe. `format_html()`
  escapes its arguments and plain text is escaped, so data alone cannot
  add a `"`. When the app marks user content safe, most often sanitizer
  output that keeps a quoted attribute, the user supplies the quote, and
  the browser reads the rest as a new attribute, such as an event
  handler.

Of the places in the Mechanism 7 list in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser),
this change touches "Text and markup" and "Attribute names, not only
values".

## How it was checked

- **Browsers.** Chromium, Firefox and WebKit through Playwright 1.65.2,
  with Python 3.13 on macOS and Django 6.0.6 and 6.1.3. A page counted
  as a hit when a marker handler in it ran.
- **Releases.** 1.0.0 was run in the browsers. The range back to 0.1.0
  was read from the release tags (0.1.0, 0.4.0, 0.5.1 and 0.6.0), and
  follows the same rule as GHSA-gv5c. The first analysis named 0.6.0 as
  the lower bound; the reviewers widened it after reading the older
  tags.
- **Kinds of value.** `mark_safe()`, `format_html()`, a lazy translation
  wrapped in `mark_safe()`, an object whose `__html__` returns a
  `SafeString`, and `Markup` as a control.
- **Places.** `c-<name>` (including URL attributes), `c-bind`,
  `<c-element>`, SVG elements, loop rows, `simple=True` components,
  `format_attrs()`, `on_attrs_resolved`, Citry UI `attrs=`, `c-class`
  keys, elements with Vue bindings, and `#c-key` on an element, in a
  loop, on a `<c-element>`, on SVG and on a component. Each went through
  the ordinary render and the node-path routes of GHSA-gv5c, including a
  real third-party extension that uses `on_template_foreign_spans`.
- **Browser runs.** With the fix, no page ran the marker handler; the
  last round's pages were part of 810 loads with 0 hits. Before the key
  fix, the `#c-key` pages ran it in every load.
- **Tests.** All 19 new tests fail on the 1.0.0 code. The full-suite
  runs are the ones listed for GHSA-gv5c.
- **Other frameworks' advisories (Mechanism 8).** The reviewers checked
  the same kinds as for GHSA-gv5c: `xss-escape`, `sanitizer-bypass`,
  `trusted-shape`, `mxss`, `xss-attrname`, `xss-spread`, `hydration`,
  `ssr-serialize`, `cache-key`, `cache-xuser`, `error-page`,
  `dos-crash`, `xss-url`, `xss-rawtext` and `i18n-xss`.

## Ruled out

- **A value that keeps its marker after the conversion.** `exact_str`
  drops any `str` subclass, and `decode_attribute_entities` now always
  returns an exact `str`, so `escape_attribute_value` escapes it
  (`test_exact_str_of_str_drops_the_subclass`,
  `test_django_safestring_is_escaped_in_an_attribute`).
- **One writer left out.** The tests cover `escape_attribute_value`,
  `format_attrs()`, rendered `c-<name>`, `c-bind` and `<c-element>`,
  Vue-bound attributes and every `#c-key` path (`TestElementKey`).
- **Changing text output.** A `SafeString` printed with `{{ }}` is
  still written as trusted HTML; only attributes and keys changed.
- **Other places that take values.** `css_data()` and `js_data()`
  already refuse trusted HTML. `c-class` and `c-style` were already
  escaped, and Jinja2's `Markup` already took the escape.
- **Sibling bugs.** A sweep of every `str()`, `escape()` and `__html__`
  call in the package found no other place that writes such a value
  unescaped.

## Fixed during the review

- The first review found that `#c-key` still wrote a `SafeString`
  unescaped on the node-path routes after the first version of the fix.
  It was fixed in the same commit.
- A sweep after the key fix found five places in the Vue element and
  component key code that failed with `TypeError` on such a value. All
  five were fixed.

## Not tested

- Releases before 0.6.0, in a browser.
- Real Safari and Edge, page encodings other than UTF-8, the
  worker-thread route on free-threaded Python, gevent and eventlet, and
  Citry UI components on the node-path routes.

## Follow-ups

These are crashes and two double-escaping problems, none of them an
escaping hole, left for a later public pull request. No issue is open
yet.

- A lazy value used as a `c-class` mapping key.
- `Markup` or a `SafeString` as a Citry UI `CButton` `href` (a crash).
- `Markup` in Citry UI `CAvatar` `img_attrs`, whose character references
  reach the browser data escaped twice.
- A key in `c-class` that is escaped twice.
