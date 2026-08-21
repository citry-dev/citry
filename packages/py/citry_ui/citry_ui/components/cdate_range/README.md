# DateRange

`CDateRange` combines two canonical native Date inputs with an enhanced
`CPopover` and `CCalendar`. The native pair remains the no-JavaScript, Form,
reset, and constraint transport; the enhanced control commits both endpoints
as one range.

The authoritative contract is
[`docs/design/ui_components/date-range.md`](../../../../../../docs/design/ui_components/date-range.md).

DateRange deliberately does not compose inside `CField`, because a field owns
one submitted control. Use a `fieldset` and `legend` for its two endpoints.
