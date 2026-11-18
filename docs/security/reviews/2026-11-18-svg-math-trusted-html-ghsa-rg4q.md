# Trusted HTML in SVG, MathML and Vue blocks (GHSA-rg4q)

- **Advisory:**
  [GHSA-rg4q-c67p-vp27](https://github.com/citry-dev/citry/security/advisories/GHSA-rg4q-c67p-vp27),
  published 2026-11-18, severity medium (CVSS 3.1 score 4.7)
- **Affected and fixed versions:** `citry >= 0.1.0, < 1.0.1`, fixed in
  1.0.1; `citry-ui < 0.6.1`, fixed in 0.6.1
- **Fix:** two commits on `main`, committed 2026-11-18. `ec2b4f782`
  still accepts `svg` and `math` as a tag from data, but raises
  `ValueError` when the element's body holds a `Markup` value with a
  tag, a `<c-raw>` block, a child component, a `<c-slot>` or a
  `<script>`; the same applies to `mglyph` and `malignmark`. The same
  commit makes `citry-ui` 0.6.1 refuse `is` and `key` as attribute names
  in the data-item maps of its table, grid, select and breadcrumb
  components. `7139005ad` raises `ValueError` for a `Markup` value that
  holds a `<noscript>` in a component with `js` and in an Events
  `Render`. Citry's browser code repeats part of both checks.
- **Reviewer:** separate reviewing agents: a review of the finding, a
  second audit that found one more way to choose the tag, reviews of
  four versions of the fix, reviews of a Citry UI follow-up
  and of a correction for the node path, and a review of the whole
  release candidate
- **Code:** in `packages/py/citry/citry/`, `components/dynamic.py`
  (`reject_trusted_html_in_selected_foreign_element`,
  `_check_foreign_body_after_render`), `util/html.py`
  (`FOREIGN_CONTENT_TAGS`), `_vue/opaque_html.py`
  (`reject_noscript_in_opaque_html`), `_vue/direct_capture.py` and
  `_vue/client.js` (`refuseOpaqueHtmlUnderForeignElement`,
  `opaqueHtmlHoldsNoscript`); `citry_ui/components/_attrs.py`
  (`reject_data_item_vue_name`) and the components that call it; tests
  in `packages/py/citry/tests/test_c_element_foreign_body.py` and
  `test_vue_opaque_noscript.py`, `packages/js/citry-client/test/`
  (`dynamic-element-tags.test.mjs`, `opaque-noscript.test.mjs`), and
  `packages/py/citry_ui/tests/` (`test_foreign_is_from_attrs.py`,
  `test_data_item_vue_names.py`, `e2e/test_data_item_vue_names_e2e.py`)

## Who controls the input

Citry writes a `Markup` value (HTML the app trusts) as written. Inside an
ordinary element, HTML keeps the contents of some elements as plain text
or inert, such as `<style>`, `<title>`, `<textarea>`, `<noscript>` and
`<template>`. The advisory describes two places where the browser read
that HTML another way:

- **A data-chosen `svg` or `math` tag.** `<c-element>` renders an element
  whose tag is chosen while the page renders. Under `svg` or `math`, the
  browser reads the body as SVG or MathML, where those elements are
  ordinary and their contents are markup. `mglyph` and `malignmark`
  inside a MathML text element written in the template do the same.
- **`<noscript>` in a block that Vue builds.** In a component with `js`,
  and in the HTML that an Events `Render` action (a handler's reply that
  updates the page) inserts, Vue builds a
  `Markup` value inside a `<template>`. Chromium and WebKit (the engine
  Safari uses) read `<noscript>` contents there as markup.

The inputs, by who first supplies them:

- **The tag name.** The template author decides where a tag may come
  from: `c-is`, a `c-bind` key `is` (in any letter case), or
  `<c-i18n tag>`. The app's Python code can also pass `is` in the
  `attrs=` input of the `citry-ui` components `CCard`, `CContainer`,
  `CGrid`, `CRow` and `CCol`. The value itself can come from request
  data, which counts as its source.
- **The body.** The app marks the HTML as trusted, most often the output
  of a sanitizer that allows `<style>`, `<noscript>` or a similar element.
  When that HTML holds user content, the user supplies it. Text that
  Citry escapes stays text in both cases.

Of the places in the Mechanism 7 list in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser),
this change touches "Text and markup", "Tag names" and "Parser rules
browsers differ on". The same pull request as this record adds the
SVG and MathML case to "Tag names".

## How it was checked

- **Browsers.** Chromium 159, Firefox 159 and WebKit 27.2 through
  Playwright 1.65.2 (1.65.0 for the last node-path runs). A page counted
  as a hit when a marker handler in it ran.
- **Releases.** `citry` 0.5.1, 0.6.0, 0.7.0, 0.9.0 and 1.0.0 were run in
  the browsers; 0.1.0 to 0.5.0 were read from the release tags. The
  `<noscript>` case was run on 0.5.1 (Events only) and on 0.6.0, 0.7.0,
  0.9.0 and 1.0.0.
- **Ways of choosing the tag.** `c-is`, a `c-bind` key `is` in any letter
  case, `<c-component>` selecting the `element` built-in, `<c-i18n tag>`,
  Citry UI `attrs={"is": ...}`, and a Python call of the `element`
  built-in.
- **Routes.** The ordinary render, a loop, `simple=True`,
  `simple="vue"`, a Vue component alone and in a loop, the component
  cache with and without Vue, an Events `Render`, and the node path (the
  renders that run the template's Python nodes directly: `str(slot)`
  after the page render, a worker thread, a component class that has
  rendered before, `reset_template()`, and an extension that holds
  another template language).
- **Kinds of body.** Trusted HTML holding each HTML element that keeps
  its contents as text or inert; SVG and MathML elements that hold HTML;
  comments and CDATA sections; escaped data inside raw-text elements the
  template wrote; `Markup` subclasses and other objects with
  `__html__`; and Python slot values.
- **Other tags.** 16 bodies under 17 other tags that data may choose:
  816 loads, no hits. A sweep of the browser calls that insert HTML found
  no other call that changes the reading.
- **Size.** The finding ran 4,764 page loads and its review 2,214 more.
  The fixes for this advisory and GHSA-mfvc were checked together with
  1,170 loads and 720 loads for sibling cases. 180 loads with the server
  checks turned off showed that the browser checks alone stop the cases
  they cover; 324 more with the old browser code showed the cases still
  run there. The last run used 130 pages per engine.
- **Tests.** 390 new Python tests in this advisory's files and 10 Node
  tests, 5 of which fail on 1.0.0; 145 more for the node-path
  correction; 241 Citry UI tests and 12 Citry UI browser tests per
  engine. Full runs with the fixes for this advisory and GHSA-mfvc:
  14,680 Python tests without browser tests, 3,870 Citry UI tests, 167
  browser end-to-end tests, and `mypy` on macOS and with `--platform
  linux`.
- **Other frameworks' advisories (Mechanism 8).** The reviewers read the
  maintainers' private survey of security bugs published for other
  frameworks and checked these kinds: data-chosen tag names
  (`xss-dyntag`), HTML that changes meaning when read again (`mxss`),
  raw-text elements (`xss-rawtext`), attribute spreading and names
  (`xss-spread`, `xss-attrname`), sanitizer bypass (`sanitizer-bypass`),
  data accepted as trusted because of its shape (`trusted-shape`),
  hydration (`hydration`), server data written into the page
  (`ssr-serialize`), cache keys (`cache-key`), unsafe deserialization
  (`deserialize`), prototype pollution (`proto`), missing escaping
  (`xss-escape`), State shared between requests (`xreq-state`) and
  template injection (`template-inj`).

## Ruled out

- **Escaped data becoming markup under `svg` or `math`.** Text that
  Citry escapes stays text. A `<script>` the template wrote is refused
  under these tags
  (`test_a_script_the_template_wrote_is_refused_under_a_data_chosen_foreign_tag`).
- **Other tags.** None of the other tags data may choose changed how the
  browser read the body.
- **Getting a refused tag past the check through `is`.** It is refused on
  every path
  (`test_an_is_key_from_data_naming_a_refused_tag_is_refused`), and in
  any letter case
  (`test_the_refusal_covers_svg_and_math_in_any_letter_case`).
- **An old cache entry.** The render cache key includes the Citry
  version, so a render cached by an affected release is not replayed.
- **A data-chosen `is` in Citry UI data-item maps.** It had no effect in
  three engines over 1,152 loads. `citry-ui` 0.6.1 refuses it anyway.
- **The server and browser lists drifting apart.** Tests compare the tag
  lists in Python and in the browser code
  (`test_the_browser_runtime_lists_the_same_*`).

## Fixed during the review

- A `Markup` value inside `#c-ignore` or `v-pre` got past the
  `<noscript>` check.
- On the node path, a `<script>` the template wrote was not refused.
- `mglyph` and `malignmark` inside a MathML text element were found and
  added.
- The first version refused plain bodies on the node path, and a
  component class that had rendered before still failed after the first
  correction. Both were fixed.
- A nested-element check trusted any component. It now trusts only the
  classes of the `element` built-in.
- Wording in the changelog, docs and error messages.

## Not tested

- Real Safari, and a page sent with a Content Security Policy header.
- Releases before 0.5.1 in a browser.
- The browser check alone against a child component's slot; this rests
  on reading the code.
- After the node-path correction, the browser runs on Vue, `simple`, the
  cache and Events were not repeated, and `<c-i18n tag>`, Citry UI and
  the Python `element` call were not run on the node path.

## Follow-ups

- Author-only by design: on the node path, a `<c-raw>` body and the
  template text of an unfilled `<c-slot>` fallback are not refused under
  a data-chosen `svg`, because only the template author writes them.
  `docs/design/trust_boundaries.md` records this.
- `docs_site/content/advanced/dynamic-components.md` says which bodies
  `svg` and `math` accept, and `docs_site/content/security.md` covers
  `<noscript>` in a `Markup` value.
- No issue is open yet for further hardening: having the browser check
  `<noscript>` in blocks that come from `<c-raw>`, refusing `is` in every
  Citry UI map, and deciding how to treat a `<noscript>` the template
  writes inside `<c-raw>` or `#c-ignore`.
