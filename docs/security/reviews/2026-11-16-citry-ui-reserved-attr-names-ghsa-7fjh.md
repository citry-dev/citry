# Reserved `data-*` names in Citry UI attribute maps (GHSA-7fjh)

- **Advisory:**
  [GHSA-7fjh-88q2-h966](https://github.com/citry-dev/citry/security/advisories/GHSA-7fjh-88q2-h966),
  published 2026-11-16, severity low (CVSS 3.1 score 3.7)
- **Affected and fixed versions:** `citry-ui < 0.6.0`; fixed in 0.6.0
- **Fix:** [#722](https://github.com/citry-dev/citry/pull/722), merged
  2026-11-15 (`e5b57c65f`), closing issue
  [#716](https://github.com/citry-dev/citry/issues/716). Every Citry UI
  `attrs=` and `*_attrs=` input raises `ValueError` for a name that starts
  with `data-citry-`, `data-cui-`, `data-cev` or `data-cid`. Names that a
  component hands out in slot data keep working.
- **Reviewer:** a separate reviewing agent (technical review, a Mechanism 7
  brief on attribute names and markers for Citry's browser code, and the
  advisory survey), then `docs-cold-reader` for the prose. This record is
  built from the pull request description, the merged change and its
  tests.
- **Code:** `packages/py/citry_ui/citry_ui/components/_attrs.py`
  (`reject_citry_ui_reserved_attr`, `reject_citry_ui_reserved_attrs`,
  `CitryUiOwnedValue`, `citry_ui_owned_value`) and
  `components/_validation.py` (`reject_owned_attrs`), called from each
  component module under `packages/py/citry_ui/citry_ui/components/` that
  takes an `attrs` input; tests in
  `packages/py/citry_ui/tests/test_reserved_attr_names.py` and in the
  per-component test files

## Who controls the input

Citry UI components accept extra attributes through `attrs=` and the other
`*_attrs=` arguments. Citry UI's browser code finds its elements by
`data-citry-*` and `data-cui-*` names, and builds some of those names at
run time from a part or action name. Core Citry's browser code reads
`data-cev*` and `data-cid*` names.

Before the fix, the components differed in what they refused. Most refused
`data-citry-`, `data-cev` and `data-cid` with their own copy of the loop,
some refused only the names they set themselves, some did not refuse
`data-cev`, and none refused `data-cui-`. So a name from request or stored
data could make Citry UI's browser code act on an element, for example by
closing a dialog or making a list option behave as disabled. The advisory
names such cases.

The inputs, by who first supplies them:

- **The attribute names in an `attrs=` or `*_attrs=` map.** The app's
  Python code supplies them, and may pass along request or stored data,
  which counts as the data's source. The browser code reads them as
  markers for the elements it manages.
- **The attrs a component hands out in slot data.** Slot data is what a
  component passes to the content placed in its slot. `CDialog`'s
  `activator_attrs`, for example, holds `data-citry-dialog-trigger`. Citry
  UI supplies these, and the documented pattern spreads them onto a
  button: `<c-CButton c-attrs="activator_attrs">`. A plain list of allowed
  names would have let request data use another component's name too, so
  these values are written as `CitryUiOwnedValue`, a `str` subclass. The
  check accepts a `data-citry-*` name only with such a value. Request data
  and JSON give only a plain `str`, and string operations drop the
  subclass. Adding your own keys (`{**activator_attrs, 'title': 'More'}`)
  keeps it.
- **`CContextMenu(target_attrs=)`.** The app's code may set
  `data-citry-context-menu-native`, a documented escape that only turns the
  custom menu off. Citry UI wraps the value as a `CitryUiOwnedValue` so it
  can reach a `<c-CButton>` in the target slot.
- **A `CitryUiOwnedValue` moved to another key.** App code could move such
  a value to a key that data chooses, because the value is not tied to its
  name. That is author-only. `docs/design/trust_boundaries.md` records it.

Of the places in the list of where values reach the browser (Mechanism 7 in
[`CLAUDE.md`](../../../CLAUDE.md#mechanism-7---a-security-pass-for-anything-that-reaches-the-browser)),
this change touches "Attribute names, not only values" and "Markers for
Citry's browser code".

## How it was checked

The description records no browser versions and no browser run for the
review.

- **A probe through every input.** The reviewer ran a harness that
  injected a probe name into every `attrs` and `*_attrs` input of every
  scenario in Citry UI's quality catalog
  (`packages/py/citry_ui/citry_ui/quality`). All 171 public inputs reached
  the check with the real value. The description does not say whether the
  harness was kept.
- **Whole prefixes, found by a scan.** The browser code builds some names
  at run time (`dataset[...]`, names made from a part or action), so a list
  read from the source would miss names and go stale with the next
  component. The fix reserves the prefixes, which also covers names a later
  release starts reading. A test scans the shipped source (component `js`,
  `runtime.source.js`, templates, CSS and `dataset.citryX` properties) for
  every `data-citry-*` and `data-cui-*` name and fails if the check stops
  refusing one. The test also requires the scan to find four named names,
  one of them a `data-cui-` name, and more than 100 names in all, so a
  broken scan cannot pass with an empty list.
- **The new tests** in `test_reserved_attr_names.py` cover:
  - the shared check: prefixes, ASCII letter case, a non-ASCII lookalike
    that passes, `None` and `False`, a `CitryUiOwnedValue`, `data-cid`
    never unlocked by one, and extra prefixes;
  - the source scan;
  - `CButton` with the issue's case;
  - the `CDialog` and `CPopover` slot attrs on a `CButton`, also with keys
    added;
  - the `CContextMenu` escape;
  - one render case each for `CDialog`, `CDrawer`, `CForm`, `CField`,
    `CSidebar`, `CTabs` (`attrs` and `tab_list_attrs`), `CCombobox`
    (`input_attrs`), a `CTable` cell and a `CListboxOption` `data-cui-*`
    name;
  - a source check that every component module with an `attrs` input calls
    the shared check.
- **Slot attrs through the page.** The author checked that a
  `CitryUiOwnedValue` survives slot data into `CButton` on a static page
  and on a page whose component has State, which renders through Vue.
- **Existing tests.** About 40 component tests matched the old per-component
  messages. They now match the shared message. The behavior they test is
  unchanged.
- **The author's runs.** The Citry UI unit suite: 3761 passed and 2
  failed. The two failures,
  `test_distribution_metadata_and_resources_use_only_the_citry_ui_namespace`
  and `test_the_editor_accepts_digit_inputs_as_text_or_numbers`, fail the
  same way on `main` in the author's environment. `ruff check`,
  `ruff format --check` (the repository), `scripts/validate.py`, and `mypy`
  on `citry_ui` (also with `--platform linux`) passed.
- **Other frameworks' advisories (Mechanism 8).** The reviewer read the
  maintainers' private survey of security bugs published for other
  frameworks (Mechanism 8 in `CLAUDE.md`). The kinds that apply are script
  from attribute names, attribute spreading, hydration markers, trust
  decided by a value's type, and cache keys. The change introduces none of
  them. For the last two, the cache key encoder refuses a `str` subclass,
  so a `CitryUiOwnedValue` cannot collide with a plain string in a cache
  key.

## Ruled out

- **A reserved name reaching the page through one input only.** The probe
  reached all 171 public inputs, and the source check requires every
  component module with an `attrs` input to call the shared check.
- **Request data carrying a `CitryUiOwnedValue`.** Request data and JSON
  produce only a plain `str`. The exception in the check covers
  `data-citry-` names only, so other reserved names are refused even with
  such a value. A test pins this for `data-cid`
  (`test_core_citry_names_stay_refused_even_with_an_owned_value`).
- **Case and lookalike tricks.** The match lowercases ASCII letters only,
  as browsers compare names, so `DATA-CITRY-X` is refused and a name with
  non-ASCII lookalike letters is a different name.
- **A name that writes no attribute.** A reserved name with the value
  `None` or `False` passes because it writes nothing
  (`test_button_renders_nothing_for_a_reserved_name_set_to_none`).
- **The context menu escape widening.** `CContextMenu(target_attrs=)`
  accepts only `data-citry-context-menu-native`. Other reserved names are
  still refused there (`test_context_menu_target_refuses_other_reserved_names`).
- **Names that browser code builds later.** The check reserves the
  prefixes, not a list, so a name that a later release starts reading is
  already covered.
- **Extra component prefixes.** A few components also refuse a prefix of
  their own, such as `data-cni`. The review found that no browser code
  reads these today, and they stay as they were.
- **Names outside these prefixes.** Citry UI does not check what other
  attribute names mean, and the docs tell app authors what to do. The "Pass
  request data safely" section of `docs_site/content/ui-library/index.md`
  says to build `attrs=` and `*_attrs=` maps in your own code, lists the
  refused prefixes, and shows how to pass slot attrs on.
  `docs/design/trust_boundaries.md` records the limit.

## Fixed during the review

- The first version did not reserve `data-cui-*`. The review found that a
  `data-cui-*` name from data on a `CListboxOption` reached the browser
  code. The prefix was added with a test. The advisory covers this name.
- The source scan covered only `data-citry-`. It now covers `data-cui-` as
  well, and the test names one `data-cui-` name that the scan must find.
- `CField`, `CSidebar`, `CTabs`, the `CContextMenu` refusal and the `None`
  case had no component-level test. Each has one now.
- Docs and comments missed `data-cui-`, and one comment said "storage
  cannot produce one", which was too strong. The wording was fixed, along
  with a doubled word in a test label.
- The `docs-cold-reader` pass asked for changes that were applied: move the
  `CButton` rule under "Configure Button", say how to add keys to slot
  attrs, put "rename the key" first in the error message, add an upgrade
  action to the changelog, and fix several comments and docstrings.

## Not tested

- The full gate, `docs_site/tests` and the browser end-to-end tests did not
  run in the author's environment. The gate builds Rust, which the change
  does not touch, and the environment lacks `lxml` for the docs tests. The
  description says CI covers them.
- No browser run of the names after the fix is recorded.
- The source check passes when a module calls the shared check for one of
  its maps and not for another. The description keeps it as a cheap guard
  for new components. A check that renders each component would need a hook
  into Citry's private input handling, so it was left out. For a component
  added later, only the source check applies.

## Follow-ups

None.
