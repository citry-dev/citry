# Rendered markup in attributes on the node path (GHSA-gv5c)

- **Advisory:**
  [GHSA-gv5c-rm2r-mvp5](https://github.com/citry-dev/citry/security/advisories/GHSA-gv5c-rm2r-mvp5),
  published 2026-11-18, severity medium (CVSS 3.1 score 4.7)
- **Affected and fixed versions:** `citry >= 0.1.0, < 1.0.1`; fixed in
  1.0.1
- **Fix:** `5d07a7de7`, committed to `main` 2026-11-18, for issue
  [#702](https://github.com/citry-dev/citry/issues/702). Citry escapes
  rendered markup that a template writes into an HTML attribute the same
  way in every render. In the renders the advisory lists, a component
  inside such markup now raises the error it already raised in an
  ordinary render.
- **Reviewer:** separate reviewing agents, one after each of three rounds
  of the fix, each with a technical, security, advisory-survey and prose
  pass
- **Code:** `ElementAttrsNode._format` in
  `packages/py/citry/citry/nodes/__init__.py`, which the translation
  binding element (`I18nBindingElementAttrsNode`) also calls; tests in
  `packages/py/citry/tests/test_node_path_attribute_values.py`; the
  node-path section of `docs/design/trust_boundaries.md`

## Who controls the input

A template can write rendered markup into an attribute, such as
`c-title="<>{{ value }}</>"`, or pass a component input that holds such
markup to `c-title`. Citry escapes that markup as attribute text, so a
`"` inside it stays inside the attribute.

Citry renders a template in one of two ways. Most renders collect the
output first and then write it (the capture path). A few renders run the
template's Python nodes directly (the node path). Before the fix, the
node path wrote rendered markup between the quotes without the attribute
escape. In 0.1.0 to 0.5.1 every render took the node path. In 0.6.0 to
1.0.0 these renders did:

- a template that holds another template language's syntax through an
  extension that uses the experimental `on_template_foreign_spans` hook;
- a slot rendered with `str(slot)` after the page render;
- a slot rendered in a worker thread that does not copy context
  variables.

The inputs, by who first supplies them:

- **The attribute and the markup around the value.** The template author
  writes them.
- **The value inside the markup.** Plain text in `{{ }}` is escaped
  before it reaches the attribute, so data alone cannot add a `"`. A `"`
  reaches the attribute only through HTML the app marked as safe: a
  `Markup` value, a Python slot holding one, or the output of an HTML
  sanitizer. A sanitizer may keep a quoted attribute, so when that HTML
  holds user content, the user supplies the quote. The browser then reads
  the rest as a new attribute, such as an event handler, and runs it.

Of the places in the list of where values reach the browser (Mechanism 7
in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)),
this change touches "Text and markup" and "Attribute names, not only
values".

## How it was checked

- **Browsers.** Chromium, Firefox and WebKit through Playwright 1.65.2
  (1.65.0 in the last round), with Python 3.13 on macOS. A page counted as a hit when a marker
  handler in it ran.
- **Releases.** The reviewers installed `citry` 0.1.0, 0.2.0, 0.3.0,
  0.4.2, 0.4.6, 0.5.0, 0.5.1, 0.6.0, 0.7.0, 0.8.0, 0.9.0 and 1.0.0 from
  PyPI and ran the pages on them. The fix was checked on `main` with the
  released `citry-core` 2.1.0.
- **Kinds of value.** `Markup`, a Python slot holding it, sanitizer
  output, a `<c-raw>` block, and a component input holding markup, with
  plain text and a plain `str` as controls. They were placed in a plain
  element, an SVG element, a `<c-element>`, a `c-bind` mapping and an
  element with a translation binding.
- **Routes.** The ordinary render, and five node-path routes: an
  extension using `on_template_foreign_spans` (a test extension and a
  real third-party one), `str(slot)` on a kept slot, a worker thread,
  markup nested inside a component class that has rendered before, and a
  render after `Component.reset_template()`. The reviewers also showed
  that `asyncio.to_thread`, `render()`, `render_template`, `pure`,
  `simple=True` and the cache extension stay on the capture path.
- **A sweep.** 85 cases compared the output of the capture path with
  four node-path routes, value kind by value kind.
- **Browser runs.** In the last review round, 372 of 588 page loads ran
  the marker handler on 1.0.0 and 0 of 810 loads ran it with the fix.
- **Tests.** 16 of the 20 new tests fail on the 1.0.0 code. The last
  round ran the whole Python suite without browser tests (14,152
  passed), 529 browser end-to-end tests in Chromium, 3,848 Citry UI
  tests, `ruff`, and `mypy` on macOS and with `--platform linux`.
- **Other frameworks' advisories (Mechanism 8).** The reviewers read the
  maintainers' private survey of security bugs published for other
  frameworks and checked these kinds: missing escaping (`xss-escape`),
  sanitizer bypass (`sanitizer-bypass`), data accepted as trusted markup
  because of its shape (`trusted-shape`), HTML that changes meaning when
  written again (`mxss`), data-chosen attribute names (`xss-attrname`),
  attribute spreading (`xss-spread`), hydration (`hydration`), server
  data written into the page (`ssr-serialize`), cache keys and cache
  entries shared between users (`cache-key`, `cache-xuser`), error pages
  (`error-page`), crashes (`dos-crash`), translated messages
  (`i18n-xss`), URLs (`xss-url`) and raw-text elements (`xss-rawtext`).

## Ruled out

- **A route that keeps the old writer.** The branch that wrote rendered
  markup without the escape is gone. Every value on the node path now
  goes through the same formatter as on the capture path, and the tests
  send each value kind through each node-path route
  (`TestRoutesReachingTheNodePath`, `TestValueKindsOnTheNodePath`).
- **Other checks behaving differently on the node path.** Attribute-name
  refusals, text and raw-text elements, URL attributes and the CSP nonce
  give the same output as on the capture path. Vue syntax is inert there
  and Events bindings are refused.
- **A cached render.** The render cache refuses a render that did not use
  the capture path, and its key includes the Citry version. The
  attribute output cache never stores a rendered markup value.
- **`c-class` and `c-style`.** Both refuse a rendered markup value with
  `TypeError`.
- **Breaking documented use.** A component inside markup printed with
  `{{ }}` still renders
  (`test_markup_input_printed_as_content_renders_its_component`). Only a
  component inside markup written into an attribute raises, as it already
  did on the capture path
  (`test_component_inside_an_attribute_value_raises_as_on_the_ordinary_path`).
- **The opt-in output checks.** `security_csp="strict"` and
  `security_javascript="forbid"` refuse the added event handler on every
  route.

## Fixed during the review

- The first round found the problem only through an extension. The first
  review showed that a kept slot and a worker thread reach it with no
  extension in 0.6.0 to 1.0.0, and that every rendered markup value was
  affected, not only an inline nested template. The tests, the changelog
  and the design doc were widened to match.
- The design doc's paragraph about the node path was wrong and was
  rewritten. The changelog names the new error for a component inside
  such markup.
- The second review found that the `#c-key` writer and the
  `reset_template()` route were missing from the analysis, and that a
  code comment and a lint exemption gave the wrong reason. All were
  corrected.

## Not tested

- Real Safari and Edge (only Playwright's browser builds were used), and
  page encodings other than UTF-8.
- `citry` 0.4.0, 0.4.1 and 0.4.3 to 0.4.5, which were not installed.
- The worker-thread route on free-threaded Python 3.14t, gevent and
  eventlet.
- An Events `Render` built from a kept slot, in a browser.
- Citry UI components on the node-path routes.
- The browser end-to-end tests in Firefox and WebKit, `scripts/check.py`
  and the docs build.

## Follow-ups

- Render `str(slot)` and worker-thread slots through the capture path, so
  the node path is used less. No issue is open yet.
- A Django `SafeString` in an attribute has its own advisory, published
  the same day
  ([GHSA-v7q5](2026-11-18-safestring-in-attributes-ghsa-v7q5.md)). Its
  `#c-key` part applies only in the renders listed above.
