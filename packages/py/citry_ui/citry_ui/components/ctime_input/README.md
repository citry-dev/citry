# TimeInput

`CTimeInput` collects one wall-clock time through a styled native
`<input type="time">`. Python accepts an exact zone-free `datetime.time` or a
canonical `HH:MM`/`HH:MM:SS` string; the submitted value stays canonical.

The authoritative contract is
[`docs/design/ui_components/time.md`](../../../../../../docs/design/ui_components/time.md).

Use `CTimePicker` when the active Citry locale must determine a finite list of
visible choices. Neither component represents a date, duration, or time zone.
