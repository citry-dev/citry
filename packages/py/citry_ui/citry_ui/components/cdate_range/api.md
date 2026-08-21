---
title: DateRange
description: Choose two ordered canonical dates as one localized range.
---

# DateRange

Use `CDateRange` when users choose a start and end date together. It renders
two usable native Date inputs first, then enhances them into one localized
Popover and Calendar when JavaScript activates.

## Choose one range

Use a fieldset and legend because DateRange submits two controls. It rejects
composition inside `CField` rather than giving two Form fields one field-owned
identity.

```citry-html
<fieldset>
  <legend>Travel dates</legend>
  <c-CDateRange start_name="arrival" end_name="departure" />
</fieldset>
```

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_range/snippets/basic.py" title="Choose one date range" />

The first Calendar selection starts a draft and the second commits an ordered
range. Selecting the same date twice commits a one-day range. Hover and focus
preview a draft without changing submitted values.

## Submit and reset both endpoints

`start_name` and `end_name` create separate canonical `YYYY-MM-DD` FormData
entries. Both endpoints are empty or both are committed. Native `input` and
`change` events fire only after an uncontrolled range commit.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_range/snippets/form.py" title="Submit and reset a date range" />

Without JavaScript the two labeled native Date inputs remain fully usable.
Reset restores both initial endpoints and closes the enhanced surface.

## Bound the whole interval

`min` and `max` are inclusive. `unavailable_dates` accepts at most 4096 unique
dates, and a committed range may not cross any unavailable date. Recheck the
same business rules on the server when processing a submission.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_range/snippets/constraints.py" title="Constrain a date range" />

## Control value and popup visibility

Client `value` is either `{start, end}` or `null`. `value` and `open` are
independent controlled channels; while supplied, requests call
`onValueChange` or `onOpenChange` and wait for the owner to return accepted
state through `$c-props`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_range/snippets/controlled.py" title="Control DateRange" />

Omitting a client prop releases only that channel at its latest committed
state.

## Follow the active locale

The visible range, Calendar labels, endpoint descriptions, trigger name, and
validation text follow the active i18n provider. The canonical Form values do
not change when the locale changes.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_range/snippets/locales.py" title="Localize DateRange" />

`first_day_of_week` overrides only the week start. Generic browser parsing of
localized date text is not part of this family; its transport always uses
native canonical Date controls.

## Compare states and presentation

Readonly keeps the range submitted and lets users inspect the Calendar but
blocks commits. Disabled blocks interaction and Form participation. Required
ranges cannot be cleared.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_range/snippets/states.py" title="Compare DateRange states" />

Use `variant`, `size`, the documented `--cui-date-range-*` variables, and
stable `data-citry-ui-part` selectors for styling. Nested Calendar and Popover
variables keep their own public contracts.

The Calendar uses its complete grid keyboard model. Manual screen-reader
review remains important for range grids, especially on mobile.

<!-- UI_LIBRARY_API_REFERENCE -->
