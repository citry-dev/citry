---
title: Calendar
description: Select one canonical date in an inline locale-aware calendar grid.
---

# Calendar

Use `CCalendar` when the active Citry locale must determine an inline calendar's
month heading, weekday order, day names, and accessible date labels. The public
value remains a canonical `YYYY-MM-DD` date regardless of display locale or
calendar system.

## Select one date

Compose Calendar in `CField` for a visible label, description, error, and shared
state. A standalone Calendar uses its localized `label` by default.

```citry-html
<c-CField required>
  <c-fill name="label">Arrival date</c-fill>
  <c-fill name="default"><c-CCalendar name="arrival" /></c-fill>
</c-CField>
```

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccalendar/snippets/basic.py" title="Select one date" />

The enhanced grid uses one roving tab stop. Arrow keys move by day or week,
Home and End move within the locale week, Page Up/Down move by calendar month,
and Shift+Page Up/Down move by calendar year. Enter or Space selects the
focused date.

## Submit and reset a canonical value

`name` contributes exactly one canonical date through the owned native Date
input. Disabled Calendar is omitted; readonly Calendar remains submitted. An
uncanceled reset restores the server value and visible month.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccalendar/snippets/form.py" title="Submit and reset Calendar" />

Without JavaScript, that Date input remains visible and usable. After
enhancement it becomes the visually hidden Form, validity, and reset transport;
the browser-generated grid is the interaction surface.

## Bound and block dates

`min` and `max` are inclusive. Dates outside them are disabled and leave the
focus sequence. `unavailable_dates` accepts up to 4096 unique exact dates;
those dates stay focusable so keyboard users can inspect the calendar, but
selection is rejected.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccalendar/snippets/constraints.py" title="Constrain available dates" />

This bounded exact list is for known application dates such as booked days.
The server must validate submitted availability again.

## Control selection and the visible month

Client `value` and `visibleDate` are independent controlled channels. A
controlled request invokes `onValueChange` or `onVisibleDateChange` without
claiming the selection or page changed; return the accepted canonical value to
commit it. Omitting a prop releases that channel at its latest accepted state.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccalendar/snippets/controlled.py" title="Control selection and month" />

Uncontrolled selection emits bubbling native `input` followed by `change` from
the fallback input. Controlled requests do not emit those transport events.

## Follow the active locale

Under a client-enabled `<c-i18n>` provider, Calendar rebuilds its heading,
weekday order, day numbers, and full accessible date labels immediately when
the locale changes. `first_day_of_week` can override only the week start; leave
it as `None` to follow locale week data.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccalendar/snippets/locales.py" title="Configure locale-sensitive weeks" />

Calendar navigates locale calendar months while retaining ISO Gregorian domain
dates for callbacks and FormData. The provider time zone determines today's
marker when explicit; otherwise Calendar uses the browser's local date.

## Choose stable or natural rows

`fixed_weeks=True` keeps six rows so surrounding layout does not jump between
months. Set it to `False` for the month's natural row count. Hide neighboring
month dates with `show_adjacent_days=False` when they should not be selectable
from the current page.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccalendar/snippets/natural_weeks.py" title="Compare calendar row layouts" />

## Compare states and sizes

Outline and plain variants combine with sm, md, and lg sizes. Readonly Calendar
allows focus and navigation but blocks selection. Disabled Calendar removes all
day tab stops and disables navigation.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccalendar/snippets/states.py" title="Compare Calendar states" />

## Customize documented anatomy

Public `--cui-calendar-*` variables style the root, navigation, dates, selected
day, today, and unavailable dates. Stable `data-citry-ui-part` selectors expose
the documented anatomy without making generated classes or arrow markup public.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccalendar/snippets/styling.py" title="Customize Calendar" />

Use `CDateInput` when browser-owned editing and picker UI are preferable. Use
`CDatePicker` for a popup field composed from DateInput and Calendar, and
`CDateRange` when the application value is an ordered start/end pair.

<!-- UI_LIBRARY_API_REFERENCE -->
