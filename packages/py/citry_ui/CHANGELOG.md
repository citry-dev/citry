# Changelog

## Unreleased

### Added

- Citry UI now supports Python 3.15.


- A `CCommandPalette` command with a `shortcut` now exposes it to
  assistive technology as `aria-keyshortcuts`, for example `Control+,`
  for "Ctrl ,". A hint that is not one key combination, such as
  `Ctrl K, Ctrl S`, and a disabled command get no `aria-keyshortcuts`.
  Set `shortcut` only for a combination your application handles.

### Changed

- Writing an empty value in a template for a text input, such as
  `<c-CButtonGroup label="">` or `<c-CContextMenu aria_label="">`, raises
  the component's own `ValueError` saying the text is empty, not a
  `TypeError` about a `bool`, because Citry passes `""` for a written
  empty value.
- **Breaking:** in `CCommandPalette`, a command that closes the palette
  now calls `onAction` after the palette closes, and after `onOpenChange`
  and `onQueryChange`, so `onAction` can move focus anywhere on the page
  once the palette has closed. If you pass `open`, set it to `false`
  inside `onOpenChange` itself; when you close it later, `onAction` runs
  while the palette is still open. An error thrown in `onAction` no longer
  keeps the palette open; to keep it open, set `close_on_action=False` on
  the palette or on the command.
- **Breaking:** Citry UI now requires Python 3.11 or newer. On Python
  3.10, pip keeps installing Citry UI 0.3.0.
- The default `change_label` of `CDateRange`, and its
  `citry-ui-date-range-change` message, now read "Change date range,
  {start} – {end}" instead of "… {start} to {end}". The trigger's name
  then contains the dates exactly as the trigger shows them, which voice
  control needs. If you set your own `change_label` or translate the
  message, write the dates as `{start} – {end}`, as the trigger shows
  them.
- Citry UI components work with Citry's new check that raises
  `TypeError` for an input of the wrong type, and accept the same values
  as before, such as `heading_level="2"`. Earlier Citry UI releases
  reject some valid inputs under that check, so upgrade Citry UI and
  Citry together.
- `heading_level` on `CAccordion` and `CDisclosure` now accepts only
  `2` to `6` and the same numbers as text, so `"02"` and `2.0` raise
  `ValueError`.
- **Breaking:** A wrong input to most Citry UI components now raises
  Citry's `TypeError`, which names the input and the expected type. This
  includes a value outside a listed choice, such as `variant="bogus"`,
  which used to raise `ValueError`, so code that catches `ValueError`
  there must catch `TypeError`. `CAccordion`, `CDisclosure`, `CIcon`,
  `CAlert`, `CCalendar`, `CDatePicker`, and `CDateRange` keep Citry UI's
  own errors on all their inputs.

### Fixed

- An open `CMenu`, `CContextMenu`, or `CSplitButton` menu that contains a
  submenu no longer moves focus to its current item again and again, and an
  idle `CSplitButton` or `CTimePicker` no longer rewrites its own markup
  hundreds of times a second. Both loops cost CPU and battery on an idle
  page.
- When a server re-render updates an open `CMenu`, the focused item keeps
  focus.
- `CTooltip` now opens or closes when a re-render changes its server `open`
  input, as the other popups do. Disabling an open tooltip, from the server
  or with the client `disabled` prop, closes it and calls
  `onOpenChange(false, ...)` with reason `"disabled"`. An uncontrolled
  tooltip closed this way stays closed when it is enabled again.
- A component that checks its rendered fills, such as `CDisclosure`'s
  title, now reads a numeric character reference with thousands of digits
  (`&#` followed by 5,000 zeros and `106;`) instead of raising
  `ValueError`.
- A popup inside a `CDialog` or `CDrawer` now calls
  `onOpenChange(false, ...)` with reason `"ancestor"` when the dialog
  closes, as `CMenu` already did. This applies to `CPopover`,
  `CHoverCard`, `CTooltip`, `CSelect`, `CMultiSelect`, `CCombobox`,
  `CCascader`, `CColorPicker`, `CDatePicker`, `CDateRange`, `CTimePicker`
  and `CTour`.
- `CMenu` no longer calls `onOpenChange` on page load when the server
  renders it open inside a closed dialog, which matches the other popups:
  a popup that was never shown reports nothing. If a controlled popup's
  owner asks it to open while the dialog around it is closed, the popup
  calls `onOpenChange(false, ...)` with reason `"ancestor"` once while the
  dialog stays closed, and again after the dialog has been shown and
  closed.
- `citry check --types` and the Citry editor extension no longer
  report an error for `heading_level="2"` on `CAccordion` and
  `CDisclosure`.
- `CCalendar`, `CDatePicker`, and `CDateRange` now accept
  `first_day_of_week="1"`, where they used to raise `TypeError`.
- When a re-render keeps a `CSelect` or `CMultiSelect` open, gives an open
  `CCombobox` new items, or removes the selected tab of a `CTabs` or the
  focused item of a `CTagGroup` or `CToolbar`, the page no longer scrolls
  back to that component. They scroll only their own list, or move focus
  without scrolling.
- While a `CMenu`, `CContextMenu`, or `CSplitButton` menu is open,
  scrolling the page no longer jumps back to the menu, for example when
  the pointer leaves a submenu trigger or the menu re-renders. The menu
  scrolls its own list to show the focused item, and scrolls the page only
  after a key press moves focus to an item that is off screen.
- A `CCascader` trigger's accessible name is now its label followed by
  the path it shows, such as "Place Europe / Slovakia", instead of only
  "Place", so voice control users can say what they see. With
  `aria_label`, the trigger now takes its name through `aria-labelledby`
  from a hidden element and has no `aria-label` attribute, so a selector
  such as `button[aria-label="Place"]` no longer finds it.

## [0.3.0] - 2026-10-19

### Changed

- Citry UI now requires `citry` 0.6.0 or newer, whose Vue runtime its
  components use.
- **Breaking:** pass client inputs and callbacks to a component with Vue
  prop bindings on its tag instead of `$c-props`.

  ```citry-html
  <!-- 0.2.2 -->
  <c-CDialog $c-props="{ open }" />

  <!-- 0.3.0 -->
  <c-CDialog :open="open" />
  ```

- **Breaking:** component `attrs` mappings, and part mappings such as
  `input_attrs` or `trigger_attrs`, reject Vue directive names (those
  starting with `v-`, `:`, `.`, `^`, `@`, or `#`) with an error that names
  the component. Write Vue bindings and listeners on the component tag in
  your template instead, for example `<c-CSplitButton @click="...">`.
- **Breaking:** `CMultiSelect` rejects inline event handler attributes
  such as `onclick` in `attrs`, `trigger_attrs`, and `listbox_attrs` with
  an error that names the input. Use the `onValueChange` callback or a Vue
  listener in your template instead.
- **Breaking:** content with Vue bindings that you write in a separate
  component and pass into Tabs, Repeatable Form Collection, Sortable,
  Splitter, Stepper, Tour, Transfer List, or Virtual List stops the render
  with an error that names the content. Write such content inside the
  group's tag or in a transparent component; there, `v-text`, `@click`,
  `v-model`, and `@c-*` bindings read your component's data.

### Fixed

- `CMenuSubmenu` closes its submenu again when page code or a stray
  `popovertarget` opens it while the submenu is closed. It previously threw
  `hideNativePopover is not defined` and left the submenu open.
- `CScrollArea` no longer calls `onScrollChange` for the scroll event its own
  offset restore causes when the area is moved to another place in the page
  before the next frame; the callback previously received that event with a
  `null` source target.
- `CContextMenu` now calls `onOpenChange` when page code changes the menu's
  markup while the menu is starting up, for example right after a server
  re-render. Previously the callback was not called for that menu until its
  props changed.
- `CContextMenu` now calls `onOpenChange(false)` when a server re-render
  changes the items of an open menu and closes it. Previously the menu
  closed without the callback, so state that follows `onOpenChange` still
  said the menu was open.
- `CContextMenu` no longer keeps the page busy when page code changes its
  markup into a form it cannot use. It now waits for the next change instead
  of rewriting its markup on every timer tick, and logs a single console
  error while the markup stays unusable.
- An open `CDialog`, `CAlertDialog`, `CDrawer`, `CTour`, `CHoverCard`,
  `CSelect`, `CMultiSelect`, `CCombobox`, `CCascader`, `CColorPicker`,
  `CDatePicker`, `CDateRange`, or `CTimePicker` stays open when a server
  event re-renders the component that contains it. Previously it closed
  without calling `onOpenChange`, and a `CDrawer` or `CTour` the user had
  closed could reopen.
- When a server event changes the `open` input you pass to `CPopover`,
  `CMenu`, `CHoverCard`, `CSelect`, `CMultiSelect`, or `CCommandPalette`,
  the component now opens or closes to match; previously it could ignore the
  change. In all of these, and in `CDialog`, `CAlertDialog`, `CDrawer`,
  `CTour`, `CCombobox`, `CCascader`, and `CColorPicker`, a server event that
  leaves `open` unchanged keeps the component open or closed as the user
  left it.
- `CDialog`, `CAlertDialog`, and `CCommandPalette` now call `onOpenChange`
  with reason `"ancestor"` when an enclosing `CDrawer` closes them, as they
  already did inside an enclosing dialog. Previously they reported
  `"native"`.
- The `CMenu` trigger and the `CTimePicker` control no longer stay disabled
  after a server event disables and then re-enables them.
- A `CDialog` or `CAlertDialog` that a server event removes while it is open
  now returns focus to the element that opened it, if that element is still
  on the page.
- An open `CTour` keeps the step the user reached when a server event
  re-renders the component that contains it, and moves to a new step when
  the server changes `active`. Previously such a re-render sent the tour
  back to the server's step. Its dialog also keeps the current step's title
  and description as its accessible name after the user moves between steps.
- `CHoverCard`, `CSelect`, `CMultiSelect`, `CCombobox`, `CCascader`,
  `CColorPicker`, `CDatePicker`, `CDateRange`, and `CTimePicker` now close
  when they are disabled while open, and call `onOpenChange(false)`. Some
  stayed open and others closed without the callback. `CSelect` and
  `CMultiSelect` report reason `"ancestor"`, as they already did when
  disabled from the browser; the others report the new reason `"disabled"`,
  as `CMenu` does. They report the close even when the same server event
  also changes `open`.

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
