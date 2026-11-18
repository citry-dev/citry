# Vue `ref` names from data (GHSA-mfvc)

- **Advisory:**
  [GHSA-mfvc-9w4x-jmh7](https://github.com/citry-dev/citry/security/advisories/GHSA-mfvc-9w4x-jmh7),
  published 2026-11-18, severity medium (CVSS 3.1 score 4.7)
- **Affected and fixed versions:** `citry >= 0.6.0, < 1.0.1`; fixed in
  1.0.1
- **Fix:** `f8b306c5e`, committed to `main` 2026-11-18. Citry refuses
  `ref`, `ref_for` and `ref_key`, in any letter case, as a `c-bind` key,
  as a name that an `on_attrs_resolved` hook adds, as any `c-ref`
  attribute whatever its value, and as an input of a `<c-element>` whose
  tag comes from data, including a Python call of the `element`
  built-in. It raises `ValueError`, as it does for `onclick`. A
  `ref="name"` written as plain text in the template keeps working.
- **Reviewer:** separate reviewing agents: the audit that found it, a
  review that showed it could run script, a review of the fix, a review
  of the Citry UI follow-up, and a review of the whole release candidate
- **Code:** in `packages/py/citry/citry/`, `attrs.py`
  (`is_script_capable_attr_name`, `reject_script_capable_attr_name`),
  `nodes/__init__.py` (`ElementAttrsNode._reject_vue_ref_attr`),
  `components/dynamic.py` (`_resolve_element_attrs`),
  `_vue/leaf_program.py`, `citry_element.py`, `ext/i18n/bindings.py` and
  `extension.py`; tests in
  `packages/py/citry/tests/test_attr_names_vue_ref.py` and, for Citry
  UI, `packages/py/citry_ui/tests/test_data_item_vue_ref.py` and
  `e2e/test_data_item_vue_ref_e2e.py`

## Who controls the input

Citry refuses attribute names from data that the browser reads as code,
such as `onclick`. In a component with `js`, Citry passes an element's
other attributes to Vue as one object. Vue reads a `ref`, `ref_for` or
`ref_key` attribute itself instead of writing it: it stores the element
in the component's own value of that name. A key chosen by request data
could therefore replace a value that the component's `setup()` returns.

The inputs, by who first supplies them:

- **A `c-bind` key, or a Citry UI `attrs=` key.** The app's Python code
  supplies it and may pass along request data, which counts as the
  data's source.
- **A `c-ref` value.** The template author writes the attribute, and the
  value can come from data.
- **The `setup()` value and its use.** The app author writes the Vue
  code. When the component shows that value with `v-html`, or uses it in
  a condition around `v-html`, the replaced value can run script in the
  browser. Without `v-html`, the effect is limited to changing the
  component's state.

Pages without Vue are not affected: there the name is written as an
ordinary attribute.

Of the places in the Mechanism 7 list in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser),
this change touches "Attribute names, not only values" and "Text and
markup" (through `v-html`). The same pull request as this record adds
Vue's reserved names to "Attribute names, not only values".

## How it was checked

- **Browsers.** Chromium 159, Firefox 159 and WebKit 27.2 through
  Playwright 1.65.2. A page counted as a hit when a marker handler in it
  ran or the component's value changed.
- **Releases.** `citry` 0.6.0, 0.7.0, 0.9.0 and 1.0.0 were run, inside
  and outside `<c-for>`, with controls. The lower bound was read from
  the tags: no release before 0.6.0 sends attributes to Vue.
- **Kinds of effect.** Replacing a value that the component shows with
  `v-html`, and changing a flag that guards `v-html`.
- **Routes.** `c-bind` on plain elements and on `<c-element>` in the
  ordinary render, `simple=True`, the cache, a loop, a Vue loop, the Vue
  cache and list rows; `c-ref` in letter-case variants; a Python call of
  the `element` built-in; `on_attrs_resolved` hooks; Citry UI `attrs=`
  and the row, cell, column, option and item maps of Citry UI
  components (17 maps); and `<c-i18n>` with `c-bind`.
- **Tests.** 202 new Python tests at the fix stage; 168 Citry UI tests
  and 12 Citry UI browser tests per engine.
- **Other frameworks' advisories (Mechanism 8).** The reviewers read the
  maintainers' private survey of security bugs published for other
  frameworks and checked attribute spreading (`xss-spread`), data-chosen
  attribute names (`xss-attrname`) and sanitizer bypass
  (`sanitizer-bypass`), with the same further kinds as for
  [GHSA-rg4q](2026-11-18-svg-math-trusted-html-ghsa-rg4q.md).

## Ruled out

- **One route left open.** The tests send the three names through each
  route above
  (`test_spread_keys_may_not_be_vue_ref_names`,
  `test_a_c_ref_attribute_may_not_take_its_value_from_data`,
  `test_a_python_call_of_the_element_builtin_may_not_pass_a_ref`,
  `test_attrs_hooks_may_not_add_vue_ref_names`,
  `test_root_spread_plans_refuse_vue_ref_names_like_the_full_merge`).
- **Other spellings.** Vue reads only the exact three names, and Citry's
  letter-case folding maps no non-ASCII letter onto them.
- **Vue's element lifecycle hook names.** They start with `on`, so the
  existing `on*` rule already refuses them.
- **Refusing too much.** `key` and `is` from data still render, because
  they give no way to markup or script
  (`test_spread_keys_that_only_look_like_ref_still_render`,
  `test_an_is_key_in_a_spread_still_renders`). A `ref` written as plain
  text in the template still works
  (`test_a_ref_written_in_the_template_on_a_*_still_renders`); the Citry
  UI sidebar relies on it.

## Fixed during the review

- A `c-ref` whose value came from data got past the first version of the
  check.
- After an exception was added for the Citry UI sidebar, a Python call of
  the `element` built-in with `ref` got past the check. It is refused
  now.
- Wording in the docs, docstrings and changelog.

## Not tested

- Real Safari, and a page sent with a Content Security Policy header.
- `simple="vue"` with `c-ref`, because the reviewer's harness for it did
  not work.
- Releases before 0.6.0, which have no Vue components.

## Follow-ups

None open. `docs_site/content/advanced/html-attributes.md`,
`syntax/attributes.md`, `advanced/dynamic-components.md` and
`advanced/extensions.md` (all under `docs_site/content/`) list the
refused names and say that a plain-text `ref` keeps working.
