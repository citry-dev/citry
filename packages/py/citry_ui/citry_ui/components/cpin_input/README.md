# PinInput

`CPinInput` captures a short fixed-length code as one exact string. It keeps a
single native text input for paste, autofill, accessibility, validation,
reset, and Form submission while JavaScript adds the segmented visual cells.

The authoritative contract is
[`docs/design/ui_components/pin-input.md`](../../../../../../docs/design/ui_components/pin-input.md).

Use `CInput` for passwords and unrestricted identifiers. Use `CNumberInput`
only for values that have numeric formatting and stepping semantics.
