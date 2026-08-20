# NumberInput

`CNumberInput` edits a quantity through an exact canonical decimal, locale-aware
text editing, spinbutton keys, and optional adjacent step controls. It preserves
native Form submission and validation without reducing values to JavaScript
binary floating point.

The authoritative contract is
[`docs/design/ui_components/number-input.md`](../../../../../../docs/design/ui_components/number-input.md).

Use `CPinInput` for numeric-looking codes and identifiers. Currency, percentage,
unit, expression, and scientific-notation editors remain separate jobs.
