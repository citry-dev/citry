---
title: TimeInput
description: Collect one canonical wall-clock time with the browser's native time control.
---

# TimeInput

Use `CTimeInput` when a browser-native time editor is the shortest path. It
preserves platform keyboard, touch picker, validation, reset, and Form behavior
while keeping the application value locale-neutral.

## Collect one time

Compose the control in `CField` for its visible label, description, error, and
shared state. A standalone input needs an accessible name through `attrs` or an
external native label.

```citry-html
<c-CField required>
  <c-fill name="label">Start time</c-fill>
  <c-fill name="default"><c-CTimeInput name="start" /></c-fill>
</c-CField>
```

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctime_input/snippets/basic.py" title="Collect one time" />

Python composition accepts an exact zone-free `datetime.time`. Localized text,
offset-aware times, fractional seconds, and noncanonical strings are rejected.

## Constrain a periodic time range

`min`, `max`, and positive integer `step` map to native time constraints. A
minimum later than the maximum deliberately expresses a wrapped interval such
as 23:00 through 02:00.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctime_input/snippets/constraints.py" title="Constrain a native time" />

The server must validate submitted values again; the component never silently
clamps or rounds.

## Use Forms and client control

`name` contributes exactly one canonical value. Disabled inputs are omitted;
readonly inputs remain submitted. Client `value` accepts a canonical string or
`null`, and omission releases control at the latest accepted value.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctime_input/snippets/form.py" title="Submit and reset a time" />

## Understand locale behavior

The DOM value and FormData stay `HH:MM` or `HH:MM:SS`; the browser chooses the
visible segment order, hour cycle, picker, and native validation prose. Use
`CTimePicker` when Citry i18n must own the visible choice labels.

## Compare states and styles

Outline, filled, and plain variants combine with sm, md, and lg sizes. Public
variables style the native control without replacing its semantics.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctime_input/snippets/states.py" title="Compare TimeInput states" />

`CTimeInput` owns no translation keys. Labels and errors belong to the
application; the platform owns the native editor and its prose.

<!-- UI_LIBRARY_API_REFERENCE -->
