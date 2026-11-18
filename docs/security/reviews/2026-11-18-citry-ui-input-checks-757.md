# Citry UI input checks: sizes, attribute names, labels (#757)

- **Pull request:** [#757](https://github.com/citry-dev/citry/pull/757),
  merged 2026-11-18 (cb240f3c9)
- **Reviewer:** a separate reviewing agent, in three rounds as the pull
  request description states: one for the first change (security, the
  advisory survey and a prose pass), one for refusing `is` and `key` in
  every attribute map (technical, security and prose), and one for
  `str` subclass names. The pull request holds no report, comment or
  review thread. This record is built from the description, the merged
  change and its tests.
- **Code:** in `packages/py/citry_ui/citry_ui/components/`:
  `_CSS_LENGTH_RE` in `cskeleton/cskeleton.py`;
  `reject_citry_ui_reserved_attr`, `reject_data_item_vue_name` and
  `attr_name_text` in `_attrs.py`; `reject_owned_attrs` in
  `_validation.py`; `fill_label` in `_i18n.py`; `attribute_text` (from
  `_url.py`) as called in `cbutton/cbutton.py` and `cavatar/cavatar.py`;
  and the components that call these. Tests in
  `packages/py/citry_ui/tests/`: `test_root_attrs_vue_names.py`,
  `test_item_attrs_vue_names.py`, `test_data_item_vue_names.py`,
  `test_reserved_attr_names.py`, `test_str_subclass_attr_names.py`,
  `test_markup_browser_data.py`, `test_fill_label.py` and
  `e2e/test_data_item_vue_names_e2e.py`, plus the CSkeleton,
  CTransferList and CContextMenu component tests

## Who controls the input

Every change is in `citry-ui`, which is still 0.x. The app's Python code
passes each of these inputs, and request data may supply them:

- **CSkeleton sizes.** `width`, `height` and `last_line_width` reach a
  CSS custom property. They now take one positive CSS length or
  percentage (the units `CGrid(min_col=)` takes, plus `%`). Anything
  else raises `ValueError`. Before, any text without `;`, braces or a
  comment was accepted. The browser applies the value as CSS.
- **`is` and `key` in attribute maps.** Every `attrs=` and `*_attrs=`
  input, and the attribute map of each list or data item, now refuses
  `is` and `key` in any ASCII letter case and with any value, through
  one shared check. `is` would change the tag a component renders, and
  Vue reads `key` itself. The layout components (`CCard`, `CContainer`,
  `CGrid`, `CGridItem`, `CRow`, `CCol`, `CSidebar`) now take their tag
  only from their fixed `tag=` list. Before, `key` on four item
  components failed the render with an unclear template error.
- **Attribute names that are `str` subclasses.** Each attribute-name
  check now reads a key as the plain text Citry writes
  (`attr_name_text`, or `str` methods called on the class), so a
  subclass gets the same checks as a plain `str`.
- **Trusted strings sent to the browser.** `CButton` sends its `href`
  and a `tabindex` from `attrs` to its browser code, and `CAvatar` sends
  `img_attrs`. They now go through `attribute_text`, so a `Markup` or
  Django `SafeString` value no longer fails the render with a
  `TypeError`, and the browser code gets the same text the server writes
  into the attribute.
- **Label patterns.** `fill_label` fills app-supplied label patterns on
  the server by replacing each exact `{name}` as plain text, the same
  way the browser code fills them. It replaces `str.format` in eight
  components, including `CTransferList` (`count_label`) and `CToast`. A
  format spec such as a field width now stays in the label as typed. The
  browser shows the label as text.

Of the places in the list of where values reach the browser (Mechanism 7
in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)),
this change touches "Attribute names, not only values", "CSS", "URL
attributes" (the `CButton` `href` sent to the browser code), "Tag names"
(the layout components' `tag=`) and "Text and markup" (labels).

## How it was checked

- **Code read.** Each review round read its part of the change. The
  first round had a security brief for attribute names, CSS and URL
  attributes.
- **New tests fail without the fix.** The first change added 133 tests.
  The reviewer ran them against the base commit: 84 failed there and
  `test_fill_label.py` failed at import.
- **The `is` and `key` addition.** `test_root_attrs_vue_names.py` (59
  cases over seven layout components, `CButton` and a non-root
  `CCombobox.input_attrs`, with `data-key` and `tag=` controls) and 16
  new cases in `test_reserved_attr_names.py`. An existing source sweep
  there checks that every component module with an attribute map input
  calls the shared check.
- **`str` subclass names:** 13 new tests in
  `test_str_subclass_attr_names.py`.
- **The whole `citry-ui` suite without the end-to-end tests:** 4,468
  passed, 109 skipped after the last change.
- **Linters.** `ruff check`, `ruff format --check` and `mypy` on the
  touched modules and tests (also with `--platform linux`) were clean.
- **Other frameworks' advisories (Mechanism 8).** The first round
  checked the change against the kinds of bug in the maintainers'
  survey. The description does not list the kinds. No round found a
  hole.

## Ruled out

- **A CSkeleton size that reaches the stylesheet as anything other than
  one length.** The value must match the whole length pattern.
- **An attribute map that skips the `is` and `key` rule.** Every
  `attrs=` and `*_attrs=` input calls the same check, and the source
  sweep test fails when a component module does not.
- **A `str` subclass name answering a check with another spelling than
  the one written to the page.** Every name check reads the plain text.
- **The browser code and the server disagreeing on a trusted value or a
  label.** Both now get the same decoded text, and both fill a label the
  same way.

## Fixed during the review

- A `True` `tabindex` now reaches the browser code as `"true"`, as the
  server writes it.
- End-to-end tests for the `CTreeGrid` and `CSortable` labels.
- Changelog accuracy, comment and docstring wording, and line
  references in `docs/design/trust_boundaries.md`.

## Not tested

- **The end-to-end suites.** They did not run. One end-to-end test
  changed only the message it matches.
- **The docs build and the full repository gate.**

## Follow-ups

- [#764](https://github.com/citry-dev/citry/issues/764): compare
  `str` subclass keys as plain strings in the expression sandbox in
  `citry-core`, as `citry-ui` now does. It is an optional part of the
  release batch in [#776](https://github.com/citry-dev/citry/issues/776).
- The new refusals are listed under "[Unreleased]" in
  `packages/py/citry_ui/CHANGELOG.md` for the next `citry-ui` minor
  release.
