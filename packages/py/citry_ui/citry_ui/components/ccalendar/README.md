# Calendar

`CCalendar` selects one canonical calendar date through an inline,
locale-aware grid while retaining a native Date input as its Form, reset,
validity, and no-JavaScript transport.

The authoritative contract is
[`docs/design/ui_components/calendar.md`](../../../../../../docs/design/ui_components/calendar.md).

Use `CDateInput` when browser-owned date editing is enough. Use `CDatePicker`
for the composed popup field and `CDateRange` for an ordered start/end value.
