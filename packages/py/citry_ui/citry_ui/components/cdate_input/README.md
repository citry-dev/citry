# DateInput

`CDateInput` collects one calendar date through a styled native
`<input type="date">`. Python accepts an exact `date` or canonical ISO string;
the browser and native Form always use `YYYY-MM-DD`.

The authoritative contract is
[`docs/design/ui_components/date-input.md`](../../../../../../docs/design/ui_components/date-input.md).

Use `CCalendar` for an inline custom calendar, `CDatePicker` for a composed
custom popup picker, and DateRange for an ordered start/end value.
