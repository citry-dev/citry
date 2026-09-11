# Changelog

## [0.2.2] - 2026-09-11

### Fixed

- Grid column counts and spans, Textarea rows and columns, and TagsInput
  maximums now accept ASCII decimal strings consistently from static and
  dynamic component inputs and Python composition
  ([#107](https://github.com/citry-dev/citry/issues/107)).

## [0.2.1] - 2026-09-09

### Changed

- Accept Citry 0.4.2 and newer without a dependency upper bound, including Citry 0.5.

### Fixed

- Dialogs and command palettes stay open when a delayed browser close event
  arrives after a rerender.
- Avatars without an initial image source now render valid HTML and preserve
  custom image attributes when the browser creates the image.
- Radio groups inside a Field now associate its label with the first radio
  without assigning the same ID to the group.
- Corrected markup in Calendar, Command Palette, Data Grid, Tree Grid,
  Repeatable Form Collection, and Transfer List, including native table
  semantics and labels for hidden selected options.
- Restored drawer backdrops, listbox checkmarks, tree expand indicators,
  carousel scrollbar styling, and pin-input selection styling by correcting
  their CSS selectors. Tour actions now stay together on narrow screens.

## [0.2.0] - 2026-08-22

### Added

- Added Timeline, Sidebar, Tour, Data Grid, Virtual List (including the
  `VirtualWindow` definition), and Transfer List component families with
  public guides, structured API references, examples, localization keys, and
  browser coverage.
- Added Sortable, Repeatable Form Collection, Infinite Scroll, Cascader,
  Tree Grid, and Color Picker component families with the same documentation,
  localization, quality-scenario, and browser-test coverage.
- Added Calendar, Date Input, Date Picker, Date Range, Number Input, Pin Input,
  Rating, Slider, Time Input, and Time Picker component families with public
  guides, structured API references, examples, and browser coverage.

### Breaking changes

- **Breaking:** 0.2.0 removes `CStack` and `CGroup`; use the
  direction-explicit `CCol` and `CRow`. No compatibility aliases are provided.
  Update each public surface as follows:
  - Python imports: `CStack` to `CCol`, `CGroup` to `CRow`,
    `CStackDefaultSlotData` to `CColDefaultSlotData`, and
    `CGroupDefaultSlotData` to `CRowDefaultSlotData`.
  - Template tags: `<c-CStack>` to `<c-CCol>` and `<c-CGroup>` to `<c-CRow>`,
    including their closing tags.
  - CSS part selectors: `[data-citry-ui-part="stack"]` to
    `[data-citry-ui-part="col"]` and `[data-citry-ui-part="group"]` to
    `[data-citry-ui-part="row"]`.
  - CSS variables: `--cui-stack-gap` to `--cui-col-gap` and
    `--cui-group-gap` to `--cui-row-gap`.

### Changed

- Citry UI now requires `citry>=0.4.2` for component-owned source messages and
  checked browser translation bindings.
- Production component styles and the largest new interaction runtimes ship as
  deterministic checked-in minified assets while readable sources remain next
  to each component.
- Data Grid cells can opt into text, number, checkbox, or select editing while
  preserving server ownership through explicit edit-request callbacks.

## [0.1.0] - 2026-08-19

### Added

- Build application interfaces from 55 styled component families by registering `citry_ui` once with a Citry instance.
- Use the same components in Citry templates or compose them from typed Python invocations.
- Customize light and dark themes through documented CSS variables, parts, variants, sizes, slots, and attributes.
- Render accessible server HTML, add keyboard and pointer interaction through
  Citry's client runtime, and localize built-in labels through the bundled
  catalog.

[0.2.2]: https://github.com/citry-dev/citry/releases/tag/citry-ui%400.2.2
[0.2.1]: https://github.com/citry-dev/citry/releases/tag/citry-ui%400.2.1
[0.2.0]: https://github.com/citry-dev/citry/releases/tag/citry-ui%400.2.0
[0.1.0]: https://github.com/citry-dev/citry/releases/tag/citry-ui%400.1.0
