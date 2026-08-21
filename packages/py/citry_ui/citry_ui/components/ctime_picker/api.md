---
title: TimePicker
description: Select one canonical wall-clock time from a localized finite popup list.
---

# TimePicker

Use `CTimePicker` when people choose from a bounded schedule and the active
Citry locale should format every visible time. It submits the same canonical
`HH:MM` or `HH:MM:SS` string as a native time input.

## Pick from regular intervals

The default fifteen-minute step produces a finite day list. Bounds limit the
choices; a later minimum than maximum creates a wrapped overnight interval.

```citry-html
<c-CField required>
  <c-fill name="label">Appointment time</c-fill>
  <c-fill name="default"><c-CTimePicker name="appointment" min="09:00" max="17:00" /></c-fill>
</c-CField>
```

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctime_picker/snippets/basic.py" title="Pick an appointment time" />

## Supply exact choices

Use `options` for irregular schedules or second precision. Options are checked,
bounded, unique, and preserve server order. Structural option changes require a
server rerender.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctime_picker/snippets/options.py" title="Supply exact time choices" />

## Submit and reset

The hidden native time control remains the single Form transport and the
no-JavaScript control. `CField` and `CForm` own shared state; the nested Listbox
never becomes another form field.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctime_picker/snippets/form.py" title="Submit and reset a time picker" />

## Control value and visibility

Client `value` and `open` are independently controlled while supplied.
`onValueChange` and `onOpenChange` report requests; omission releases each
channel at its latest committed value.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctime_picker/snippets/controlled.py" title="Control time and popup state" />

## Switch locales in place

The server renders source-locale text first. Under a client-enabled `c-i18n`
provider, the trigger, popup name, clear label, validity message, and generated
option labels update when the locale changes. Canonical Form values do not.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctime_picker/snippets/locales.py" title="Format time choices by locale" />

Literal `placeholder`, `picker_label`, `change_label`, `clear_label`, and
`unavailable_message` overrides remain exactly application-owned and do not
register catalog bindings.

## Compare states and styles

Outline, filled, and plain variants combine with sm, md, and lg sizes. The
picker inherits Popover collision handling, Listbox keyboard behavior, forced
colors, logical direction, and reduced-motion handling.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctime_picker/snippets/states.py" title="Compare TimePicker states" />

<!-- UI_LIBRARY_API_REFERENCE -->
