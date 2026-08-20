---
title: DateInput
description: Collect one canonical calendar date with the browser's native date control.
---

# DateInput

Use `CDateInput` when one native calendar date is the application value. It
preserves browser keyboard, touch picker, autofill, validation, reset, and Form
behavior while keeping the submitted value locale-neutral.

## Collect one date

Compose the input in `CField` for a visible label, description, error, and
shared state. A standalone input needs an accessible name supplied through
`attrs` or an external native label.

```citry-html
<c-CField required>
  <c-fill name="label">Arrival date</c-fill>
  <c-fill name="default"><c-CDateInput name="arrival" /></c-fill>
</c-CField>
```

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_input/snippets/basic.py" title="Collect one date" />

Python composition accepts an exact `datetime.date`; a `datetime`, localized
text, or noncanonical string is rejected.

## Set exact bounds

`min`, `max`, and positive integer `step` map directly to native date
constraints. The server must validate submitted values again.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_input/snippets/bounds.py" title="Constrain a native date" />

The component does not clamp or round. Browser constraint validity remains
observable through the native input.

## Use native Forms and reset

`name` contributes exactly one canonical value. Disabled inputs are omitted;
readonly inputs remain submitted. `CForm` and `CField` own their shared state.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_input/snippets/form.py" title="Submit and reset a date" />

## Control a date in Alpine

Client `value` accepts a canonical string or `null`. Native `input` and
`change` events remain the observation surface; a supplied client value is
restored after event listeners run until its owner accepts another value.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_input/snippets/controlled.py" title="Control a date" />

Omitting client `value` releases control at the last accepted value.

## Hint birthday autofill

The ordinary native `autocomplete` input can request browser-managed birthday
autofill without changing the canonical value contract.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_input/snippets/birthday.py" title="Request birthday autofill" />

## Understand locale behavior

The DOM value and FormData stay `YYYY-MM-DD`; the browser chooses the visible
segment spelling and native picker UI. That UI may follow browser or platform
locale rather than the nearest Citry i18n provider.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_input/snippets/locales.py" title="Compare native locale contexts" />

Use the custom Calendar/DatePicker family when the active Citry locale must
determine the exact calendar UI.

## Compare states and styles

Outline, filled, and plain variants combine with sm, md, and lg sizes. Public
variables customize the outer native control without hiding its picker
indicator or replacing its internal semantics.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_input/snippets/states.py" title="Compare DateInput states" />

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdate_input/snippets/styling.py" title="Customize DateInput" />

`CDateInput` owns no translation key: labels and errors belong to the
application, while native picker and validation prose belong to the browser.

<!-- UI_LIBRARY_API_REFERENCE -->
