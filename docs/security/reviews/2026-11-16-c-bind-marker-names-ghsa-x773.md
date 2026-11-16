# Citry's reserved attribute names as `c-bind` keys (GHSA-x773)

- **Advisory:**
  [GHSA-x773-57wm-phfv](https://github.com/citry-dev/citry/security/advisories/GHSA-x773-57wm-phfv),
  published 2026-11-16, severity medium (CVSS 3.1 score 4.8)
- **Affected and fixed versions:** `citry < 1.0.0`; fixed in 1.0.0
- **Fix:** [#713](https://github.com/citry-dev/citry/pull/713), merged
  2026-11-15 (`a09203a41`), closing issue
  [#699](https://github.com/citry-dev/citry/issues/699). On an HTML
  element, a `c-bind` key may no longer be a name Citry reserves for its
  own elements and placeholders, and a `<c-element>` with `c-is` or
  `c-bind` refuses the same names. The check raises `ValueError`. It
  refuses input that citry 0.9.0 accepted, and the changelog lists it under
  "Upgrading from 0.9.x".
- **Reviewer:** a separate reviewing agent (technical, security and
  advisory survey), then a docs cold reader for the prose. This record is
  built from the pull request description, the merged change and its tests.
- **Code:** `packages/py/citry/citry/attrs.py`
  (`is_citry_marker_attr_name`, `reject_citry_marker_attr_name`), called
  from `citry/nodes/__init__.py` (`ElementAttrsNode`, and the component-tag
  spread in `ComponentNode`), `citry/_vue/leaf_program.py`
  (`_spread_with_source_attrs`, `_root_spread_plan`),
  `citry/ext/i18n/bindings.py` (`I18nBindingElementAttrsNode`) and
  `citry/components/dynamic.py` (`_resolve_element_attrs`); tests in
  `tests/test_attr_names_from_data.py`, `tests/test_component_dynamic.py`
  and `tests/test_simple_vue_row_caches.py` (all under
  `packages/py/citry/`)

## Who controls the input

A `c-bind` spread turns the keys of a dictionary into attribute names.
Citry writes some attribute names into the page and reads them again
later. These names are its markers:

- `c-render-id`: after a render, the server replaces each empty
  `<template c-render-id>` with a child component's HTML.
- `data-cid` and `data-cid-*`: mark component roots and Events instances.
- `data-ccss-*`: scope CSS variables.
- `data-cev-*` and a set of `data-citry-*` names: read by the Events,
  i18n, Vue and stylesheet code in the browser, and by the render cache.

Before the fix, the checks on `c-bind` keys refused names such as `onclick`
and `srcdoc`, and the Events and i18n marker names, but not the rest of
these. A key that came from request or stored data could therefore be one
of them. The advisory reports that a `c-render-id` key made Citry copy
another component's rendered HTML into the element, with and without Vue.

The inputs, by who first supplies them:

- **A `c-bind` key on an HTML element.** The app's Python code supplies it,
  and the app may pass along request or stored data, which counts as the
  data's source. The fix refuses the reserved names here. The risk was that
  Citry's server or browser code acts on the element as if Citry had
  written the marker.
- **Every name on a `<c-element>` with `c-is` or `c-bind`.** A
  `<c-element>` is Citry's tag for an element whose tag name or attributes
  come from data. It cannot tell a name written in the template from one
  passed in as data, so it refuses both. A static
  `<c-element is="div" data-cid-x>` compiles to a plain element and is
  accepted.
- **A name the template author writes on a plain element.** The author
  supplies it, and it is still accepted (for example `<div data-cid-x>`).
  It never reaches the check, because the template is author source.
- **A name an `on_attrs_resolved` hook adds.** The hook is a function an
  extension registers to change an element's attributes after Citry
  resolves them. Extension code supplies the names. Hooks may still add
  these names, and the Events extension adds `data-cev-*` this way.
- **The keys that `format_attrs()` formats.** This public helper writes a
  mapping as HTML attributes. The app's Python code supplies the keys. The
  function is unchanged, and
  [#700](https://github.com/citry-dev/citry/issues/700) tracks whether it
  should refuse the same names.

Of the places in the list of where values reach the browser (Mechanism 7 in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)),
this change touches "Attribute names, not only values" and "Markers for
Citry's browser code".

## How it was checked

The description says a separate reviewer did a technical, security and
advisory-survey pass, and a docs cold reader did a prose pass. It records
no browser versions and no browser run. The routes below are server-side
renders.

- **Reproduction.** On `origin/main` before the change, the reviewer
  reproduced the hole: a `c-bind` key `c-render-id` copied another
  component's HTML, with and without Vue. On the branch it is refused.
- **One check on every path.** `reject_citry_marker_attr_name` runs wherever
  `c-bind` is applied to an element: the node path (the Python code that
  renders a template without Vue), the Vue leaf programs (the generated
  code for a Vue element, in its full form and in the fast form used when a
  spread is the only dynamic part of the root element), elements with a
  `$c-tr` translation binding, and `<c-element>` (the component-tag spread
  and `_resolve_element_attrs`). It compares names after lowercasing ASCII
  letters only, as browsers do.
- **Variants the reviewer tried.** Letter-case variants, `str` subclasses,
  `UserDict` and `MappingProxyType` mappings, and Citry UI `attrs=` are
  refused. Lookalikes that use U+0130, fullwidth letters, the Kelvin sign
  and zero-width characters render as different names.
- **The new tests.** `test_attr_names_from_data.py` sends 15 reserved names
  (two of them in mixed letter case) through six shapes: a plain element
  rendered without Vue, with Vue, and as a Vue-prepared render; a
  `<c-element>` with `c-bind`; and a `<c-element>` with `c-is`, rendered
  plainly and as a Vue-prepared render. Three names go through an element
  with a `$c-tr` binding, and three through the Vue leaf rows
  (`ERROR_CASES` in `test_simple_vue_row_caches.py`). Names that must still
  render (`data-x`, `data-cidr`, `data-ccssx`, `data-citryx`,
  `data-citry-ui-part`, and non-ASCII lookalikes), names written in the
  template, and hooks have tests too. A mutation check (removing a check on
  purpose) showed that the leaf-row tests fail when the leaf-program check
  is removed.
- **An existing test changed.** `test_component_dynamic.py` expected a
  written `data-citry-key` on a `<c-element>` with `c-is` to fail with the
  metadata-conflict message. It now fails earlier, with the reserved-name
  message. The metadata-conflict check still runs after hooks, and a new
  test covers that.
- **The author's runs.** `pytest` over `packages/py/citry/tests` and
  `packages/py/citry_ui/tests`, without the browser and qualification
  tests: 14714 passed and 2 failed. The two failures are Citry UI tests,
  `test_distribution_metadata_and_resources_use_only_the_citry_ui_namespace`
  and `test_the_editor_accepts_digit_inputs_as_text_or_numbers`, and they
  fail the same way on `origin/main` in the shared environment. `ruff
  check`, `ruff format --check`, `mypy` (on macOS and with `--platform
  linux`) and `scripts/validate.py` passed.
- **Other frameworks' advisories (Mechanism 8).** The reviewer read the
  maintainers' private survey of security bugs published for other
  frameworks (Mechanism 8 in `CLAUDE.md`) and checked these kinds: script
  from data-chosen attribute names (`xss-attrname`), attribute spreading
  (`xss-spread`), sanitizer bypass (`sanitizer-bypass`), hydration
  (`hydration`), script from data-chosen tag names (`xss-dyntag`), cache
  entries shared between users and unsafe deserialization
  (`cache-xuser`, `deserialize`), and DOM clobbering (`dom-clobber`). The
  change introduces none of them.

## Ruled out

- **A reserved name reaching an element through one path only.** One
  function does the check, and the tests send names through every path
  listed above.
- **Case and type tricks.** Letter case, `str` subclasses and mapping types
  other than `dict` do not get a name past the check. Names that differ
  only by non-ASCII lookalike letters are different names to Citry's
  readers and to browsers, so they cannot stand in for a reserved one.
- **Refusing too much.** Names close to the reserved ones (`data-x`,
  `data-cidr`, `data-citry-ui-part`) still render, as the controls in the
  tests show. The error message names the attribute, says why, says how to
  fix it, and points to the docs list.
- **Hooks behaving differently with and without Vue.** A hook is extension
  code, so the app author's own setup decides which hooks run. The check
  runs in the same places for both kinds of page, and a test
  (`test_attrs_hook_may_add_a_reserved_name_to_a_dynamic_element`) covers
  a hook that adds a reserved name to a dynamic element.
- **Names the template author writes.** `<div data-cid-x>` and
  `<div c-c-render-id="...">` are accepted on purpose, because the template
  is author input. The new section "Names Citry reserves" on the HTML
  attributes page (`docs_site/content/advanced/html-attributes.md`) lists
  the refused names, says the rule covers `c-bind` on HTML elements and
  not component tags, and says a name written in the template is not
  checked because the author chose it. Short notes on the attributes page
  and the dynamic components page link to it.
- **`data-allow-mismatch`.** It is Vue's own public attribute, so it is not
  refused. `docs/design/trust_boundaries.md` explains why it is left out.
- **The Events and i18n names keeping their own errors.** The Events names
  (`data-cev-*`, `data-citry-runtime-control`, `data-citry-runtime-events`)
  and `data-citry-i18n-binding` on an i18n element still raise the
  `RuntimeError` they raised before, because their checks run first.
  Tests cover both (`test_spread_keys_in_the_events_namespace_keep_their_own_error`
  and the `$c-tr` binding test).

## Fixed during the review

- A first version also checked dynamic elements in the Vue writer (the
  Python code that renders a Vue page's HTML). That refused a name an
  `on_attrs_resolved` hook added on a Vue page but not on a page without
  Vue. The check was removed so hooks behave the same on both, and a test
  was added.
- The leaf-program checks had no test of their own. Reserved names were
  added to `ERROR_CASES` in `test_simple_vue_row_caches.py`, and a mutation
  check confirmed the new cases fail when those checks are removed.
- The docs gave the wrong error type for `data-citry-runtime-*` and for
  `data-citry-i18n-binding`. Both were corrected.
- The docs cold reader asked for changes that were applied: say that the
  rule applies to HTML elements, not component tags; define "reserved
  names" in plain words; point to the docs list from the error message;
  and fix several comments and wordings.

## Not tested

- The docs-site tests did not run in the author's environment, which lacks
  the docs extras. The description says CI runs them.
- The browser end-to-end tests and the qualification tests were not part of
  the author's `pytest` run.
- The description records no browser run. Browser behavior is not
  covered, only the server-side renders and Citry's own checks.
- Citry UI's own `data-citry-<component>-*` names are not in the core list.
  Citry UI refuses them in its own attribute maps, which a separate advisory
  covers ([GHSA-7fjh](2026-11-16-citry-ui-reserved-attr-names-ghsa-7fjh.md)).

## Follow-ups

- `join_frames`, the server step that fills each `<template c-render-id>`
  with its child's HTML, is unchanged. `docs/design/trust_boundaries.md`
  keeps the question of which placeholders it should fill as an open
  question.
- [#700](https://github.com/citry-dev/citry/issues/700): whether
  `format_attrs()` refuses the names `c-bind` refuses, moved to 1.1.0.
