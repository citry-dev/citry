---
title: DatePicker
description: Choose one canonical date from a localized popup Calendar.
---

# DatePicker

Use `CDatePicker` when an application needs Citry's consistent localized
Calendar in a compact field-like control. Its display follows the active
locale, while its value and Form output remain canonical `YYYY-MM-DD` dates.

## Choose one date

Compose DatePicker in `CField` for a visible label, description, error, and
shared required, disabled, readonly, or invalid state.

```citry-html
<c-CField required>
  <c-fill name="label">Arrival date</c-fill>
  <c-fill name="default"><c-CDatePicker name="arrival" /></c-fill>
</c-CField>
```

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_picker/snippets/basic.py" title="Choose one date" />

The whole visible field is a native Button, not a small detached icon. Opening
moves focus to the selected date or the Calendar's current focus candidate.
Selecting an available date closes the Popover and restores focus to the
field.

## Pick the right date family

Use `CDateInput` when direct native editing, the browser's platform picker, or
the shortest no-JavaScript path is the priority. Use `CCalendar` when dates
must stay visible. DatePicker is the composed popup route and deliberately does
not parse localized typed text.

## Submit and reset a canonical value

One native Date input owns `name`, `form`, required validity, reset, and
FormData. Enhancement hides it visually and gives its public ID to the visible
Button. Without JavaScript it remains the complete usable control.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_picker/snippets/form.py" title="Submit and reset DatePicker" />

Uncontrolled user selection emits bubbling native `input` followed by
`change`. Controlled requests wait for the owner and emit neither transport
event until the owner commits its prop.

## Bound and block dates

`min` and `max` are inclusive. `unavailable_dates` accepts at most 4096 unique
exact dates. Calendar keeps unavailable dates focusable for inspection but
rejects selection. Always validate availability again on the server.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_picker/snippets/constraints.py" title="Constrain available dates" />

## Clear and compare states

An optional non-empty DatePicker shows a clear Button by default. Required
controls never expose it. Readonly permits opening and Calendar navigation but
blocks selection; disabled blocks opening and Form participation.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_picker/snippets/states.py" title="Clear and compare DatePicker states" />

## Control value and open state independently

Client `value` and `open` are separate controlled channels. A controlled
selection or open/close interaction calls `onValueChange` or `onOpenChange`
without claiming it committed. Return the accepted value through `$c-props`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_picker/snippets/controlled.py" title="Control value and popup state" />

Omitting either client prop releases that channel at its latest committed
state. The other channel remains controlled.

## Follow the active locale

Under a client-enabled `<c-i18n>` provider, the display value, trigger name,
popup title, clear name, Calendar heading, weekdays, day numbers, and full date
names switch in place. The ISO value does not change. Non-Gregorian display
calendars remain mapped to the same Gregorian domain date.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_picker/snippets/locales.py" title="Use locale-aware DatePicker output" />

`first_day_of_week` overrides only the week start. Leave it unset to follow
locale data.

## Configure placement

DatePicker uses the existing non-modal Popover contract. Choose one of six
logical placements and use `match_width` when the surface should be at least
the field width. Collision repair may use another rendered side.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_picker/snippets/placement.py" title="Configure logical placement" />

Escape and passive outside or focus-outside interaction close a dismissible
picker. It does not trap focus, lock the page, or make background content inert.

## Customize documented anatomy

Variants, sizes, public `--cui-date-picker-*` variables, and stable
`data-citry-ui-part` selectors style the field. The nested Calendar and Popover
keep their own public variables.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_picker/snippets/styling.py" title="Customize DatePicker" />

The Calendar grid follows its complete roving-focus keyboard contract. Manual
screen-reader review remains important for popup grids, especially on mobile.

<!-- UI_LIBRARY_API_REFERENCE -->
