---
title: Pin input
description: Capture fixed-length verification and recovery codes without losing native input behavior.
---

# Pin input

Use `CPinInput` for one-time codes, PINs, and short recovery tokens. Its value
is always a string, so a leading zero is preserved.

## Enter a verification code

Give a standalone PinInput an accessible `label`, or place it in `CField` for a
visible label, help, error, and shared state.

```citry-html
<c-CField required>
  <c-fill name="label">Verification code</c-fill>
  <c-fill name="description">Enter the six digits from your message.</c-fill>
  <c-fill name="default"><c-CPinInput name="code" /></c-fill>
</c-CField>
```

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpin_input/snippets/basic.py" title="Enter a verification code" />

One native text input owns focus, selection, paste, autofill, validation, and
submission. The separate cells are visual only and create neither extra Tab
stops nor separate Form values. Without JavaScript the native input remains a
normal usable text box.

## Accept recovery-code letters

The default `type="numeric"` accepts ASCII digits. Use `alphabetic` or
`alphanumeric` for protocol tokens containing ASCII letters. These values are
opaque identifiers, not localized numbers.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpin_input/snippets/alphanumeric.py" title="Enter an alphanumeric recovery code" />

Invalid characters are discarded and reported through `onValueInvalid`.
`length` is structural and supports 1 through 32 characters.

## Control the value

Client `value` controls the exact string. An edit is a request: the displayed
cells and Form value remain owner-controlled until the Alpine expression
returns the requested value.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpin_input/snippets/controlled.py" title="Control a PinInput" />

`onValueChange` reports accepted edits. `onComplete` reports a transition to a
full value and never submits the Form automatically. Paste and autofill remain
available.

## Preserve native Form behavior

`required` combines with an exact-length native pattern, so an empty or partial
required code blocks submission. Readonly values remain focusable and submit;
disabled values do not submit.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpin_input/snippets/forms.py" title="Submit and reset codes" />

`one_time_code=True` emits `autocomplete="one-time-code"`. Set an explicit
`input_attrs={"autocomplete": "..."}` when another autocomplete policy is
required. Citry never invokes WebOTP or reads SMS messages.

## Mask or group the visual cells

`mask=True` replaces filled visual cells with bullets without changing the
submitted string. It reduces shoulder surfing but is not encryption and does
not hide the accessible text-field value from assistive software.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpin_input/snippets/masked.py" title="Mask a code" />

Use `attached=True` to join cells. For a 3–3 presentation, provide
`separator_after=(2,)` and the `separator` slot. Separator output is visual;
put instructions in Field description text.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpin_input/snippets/separator.py" title="Group code cells" />

## Keep code direction and locale ownership clear

PinInput renders protocol tokens left-to-right by default, including inside an
RTL page. ASCII digits are not localized. Labels, Field text, placeholders,
and separators belong to the application and stay in its locale.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpin_input/snippets/locales.py" title="Use PinInput in RTL content" />

## Choose states and public styles

Outline and subtle variants combine with sm, md, and lg sizes. Public
`--cui-pin-input-*` variables and documented part selectors customize cells,
focus, separators, and state treatment.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpin_input/snippets/states.py" title="Compare PinInput states" />

Tab enters the component once. Native text editing and clipboard shortcuts
continue to work; Home, End, and pointer selection move the active visual cell.

<!-- UI_LIBRARY_API_REFERENCE -->
