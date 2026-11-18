# Changelog

## [Unreleased]

### Changed

- `CSkeleton` `width`, `height` and `last_line_width` now raise
  `ValueError` unless the value is one positive CSS length or
  percentage, such as `12rem` or `50%`, in `px`, `rem`, `em`, `ch`,
  `vw`, `vh`, `vmin`, `vmax` or `%`, the units `CGrid(min_col=)`
  takes plus `%`. Values such as `auto`, `calc(...)`, `var(...)` and a
  bare `0` now fail; before, any CSS text without `;`, braces or a
  comment was accepted.
- Every `attrs=` and `*_attrs=` map of a Citry UI component now raises
  `ValueError` for the attribute names `is` and `key`, in any letter
  case, as the attrs of table rows and select options already do.
  Citry UI used to accept them: `is` in the `attrs` of `CCard`,
  `CContainer`, `CGrid`, `CGridItem`, `CRow`, `CCol` or `CSidebar`
  replaced the tag the component renders (use `tag=` instead), and
  `key` failed the render of several list items with an unclear error.
  Use a `data-*` name, such as `data-key`, for your own value.
- Labels with placeholders, such as `CTransferList(count_label=)` and
  the labels of `CSortable`, `CFormCollection`, `CTreeGrid`, `CRating`,
  `CCascader`, `CTagsInput` and `CToast`, are now filled on the server
  by replacing each `{name}` as plain text, as the browser code does. A
  format spec such as `{total:>5}`, or a literal `{{x}}`, now stays in
  the label as typed, so the server and the browser show the same text.

### Fixed

- A `Markup` or Django `SafeString` value in `CButton(href=)` or in a
  `tabindex` in `CButton(attrs=)`, and a `SafeString` value in
  `CAvatar(img_attrs=)`, no longer fails the render with a `TypeError`.
- A `Markup` value in `CAvatar(img_attrs=)` now reaches the browser
  code decoded, as the server writes it, so `&amp;` in it reads as `&`
  whether the server or the browser creates the image.

## [0.6.1] - 2026-11-18

### Changed

- The `attrs` of a table row, cell or column (`CTable`, `CDataGrid`,
  `CTreeGrid`), of a `CNativeSelect` option or group, and of a
  `CBreadcrumbItem` now raise `ValueError` for the attribute names `is`
  and `key`, in any letter case. Vue reads both names itself when it
  renders the rows and options of `CDataGrid`, `CTreeGrid` and
  `CNativeSelect`. Before, `key` failed the render with an unclear
  error, and `is` left those rows, cells and options out of the HTML
  the server sent. Use a `data-*` name, such as `data-key`, for your
  own value.

## [0.6.0] - 2026-11-16

### Changed

- **Breaking:** Citry UI now requires Citry 1.0.0 or later and below
  2.0.0 (`citry>=1.0.0,<2`). If you stay on Citry 0.9.x, keep citry-ui
  0.5.x. Citry UI itself stays on 0.x, so pin one minor release, such as
  `citry-ui>=0.6.0,<0.7`.

### Fixed

- `CButton` `href`, `CForm` `action`, and a `formaction` in `CButton`
  `attrs` or `CSplitButton` `primary_attrs` now raise `ValueError` for a
  `Markup` URL whose scheme is spelled with character references, such as
  `Markup("java&#115;cript:alert(1)")`, as they do for the same URL
  written as a plain string. Before, Citry decoded the references when it
  wrote the attribute, so the page got a `javascript:` link.
- Every `attrs=` and `*_attrs=` map now raises `ValueError` for a key
  that starts with `data-citry-`, `data-cui-`, `data-cev` or `data-cid`,
  the names Citry UI's and Citry's browser code finds elements by.
  Before, a key from request data such as `data-citry-dialog-close` on a
  `CButton`, or `data-cui-listbox-option-disabled` on a
  `CListboxOption`, could make that code act on the element. If you
  pass one of these keys, rename it. Attrs a component gives you in
  slot data, such as `activator_attrs`, still work on a `<c-CButton>`,
  as they are or with your own keys added.

## [0.5.0] - 2026-11-14

### Changed

- **Breaking:** Citry UI now requires `citry` 0.9.0 or newer, so upgrade
  both together. Its checks of rendered fills use Citry's HTML parser.
  That parser reads a numeric character reference in an attribute value
  the way the browser does only from Citry 0.9.0. For example,
  `CDisclosure`'s panel now refuses `popover="man&#1;ual"`, because the
  browser reads it as `man`, the character U+0001, and `ual`, which is
  not `manual`.

### Fixed

- When an element in a checked fill repeats an attribute, such as
  `<span tabindex="0" tabindex="-1">`, the check now reads the first
  value, as the browser does. It used to read the last one, so it could
  accept an element that the browser makes focusable, or refuse one that
  is fine.
- Citry 0.9.0 runs `onServerRender` callbacks with children before
  their parent. These components now work with that order when a server
  event re-renders the component around them. Without this fix:
  - an open `CDatePicker`, `CDateRange` or `CTimePicker` popup closed,
    and so did an open `CPopover` inside another open `CPopover`;
  - when one server render opened a `CDialog` or `CDrawer` and a
    `CDialog`, `CDrawer` or `CCommandPalette` inside it, they did not
    both open, or the inner one opened behind the outer one;
  - an open `CDrawer` inside a `CDialog`, or an open `CCommandPalette`
    inside a `CDrawer`, stayed open when the server closed the outer
    one;
  - `CAccordion` did not report, through `onValueChange`, the open
    items that a re-render removed, and did not move focus to the
    nearest item when the focused item was removed.

## [0.4.0] - 2026-11-02

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
- **Breaking:** Citry UI now requires `citry` 0.7.0 or newer. Its
  components accept the same values as before, such as
  `heading_level="2"`, under Citry 0.7.0's check that raises `TypeError`
  for an input of the wrong type. Citry UI 0.3.0 rejects some valid
  inputs under that check, so upgrade both together.
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
- **Breaking:** link inputs now accept only a relative URL or an
  `http:`, `https:`, `mailto:`, `sms:`, or `tel:` URL, and raise
  `ValueError` for any other scheme. Link inputs are `href` on
  `CBreadcrumbItem`, `CButton`, `CListItem`, `CMenuItem`,
  `CNavigationMenuLink`, and `CPagination`; `CForm`'s `action`; and a
  `formaction` attribute on `CButton` or `CSplitButton`. Image inputs
  (`CAvatar`'s `src`, and `CImage`'s `src` and `srcset`, including each
  source's `srcset`) accept only a relative URL or an `http:`,
  `https:`, `blob:`, or `data:image/` URL. To link to another scheme,
  such as an app's own scheme, write the `<a>` in your template.
- Citry UI components work with the next Citry release, which accepts
  `$c-tr` translation bindings only when they are written in the
  template. Earlier Citry UI releases fail to render under that release,
  so upgrade Citry UI and Citry together.

### Fixed

- `CTagsInput` no longer holds up the page for seconds when a typed or
  pasted tag has a long run of spaces inside it, and `CNumberInput`,
  `CSlider`, and `CImage` no longer slow down in Safari on a value with a
  very long run of zeros or commas.
- `CMenu` and `CAccordion` now accept a self-closed element such as
  `<span/>` in an item's label or title, and write it as `<span></span>`,
  as Citry does elsewhere. They used to reject it.
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
- Menus, popovers, dialogs, selects and the other interactive components
  keep working when data puts a `name` on a `form`, `img`, `iframe`,
  `embed` or `object` that matches a `document` member they read, such as
  `<form name="activeElement">`, or when a field inside a form has a `name`
  that matches a form member. This needs Citry 0.7.0 or later; with an
  older Citry the fix does not apply.
- `CImage` now checks a long `srcset` in time proportional to its
  length. A `srcset` with a long run of spaces could keep the server
  busy for minutes or longer during a render, and a client `srcset`
  prop with a long run of spaces or commas could freeze the browser
  tab.
- `CPagination` control labels and `CTable`'s status announcement now
  follow a language switch in the browser.

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
