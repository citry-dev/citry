---
title: NumberInput
description: Edit and submit an exact decimal quantity with localized spinbutton behavior.
---

# NumberInput

Use `CNumberInput` for a quantity where incrementing and decrementing make
sense: item counts, measurements, thresholds, or bounded settings. Its public
value is an exact canonical decimal string, so `0.1` stays `0.1` instead of
becoming a JavaScript binary-float approximation.

Use `CPinInput` for one-time codes and identifiers. A credit-card number,
postal code, account number, or phone number is text, not a quantity.

## Edit a quantity

Compose NumberInput inside `CField` for a visible label, description, error,
and shared state.

```citry-html
<c-CField required>
  <c-fill name="label">Crates</c-fill>
  <c-fill name="description">Choose from 1 through 20.</c-fill>
  <c-fill name="default">
    <c-CNumberInput name="crates" value="2" min="1" max="20" />
  </c-fill>
</c-CField>
```

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnumber_input/snippets/basic.py" title="Edit and submit a quantity" />

Standalone use needs an accessible name in `input_attrs`.

## Keep decimals exact

Server inputs accept `int`, `Decimal`, or a plain-decimal string. Floats,
scientific notation, NaN, and infinity are rejected. Client `value` is a
canonical string or `null`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnumber_input/snippets/exact_decimals.py" title="Step exact fractional values" />

`step` sets an exact grid based on `min`, or zero when `min` is omitted. Arrow
keys move one step, Page Up and Page Down move ten, and Home/End use a supplied
minimum/maximum. The adjacent Buttons do not add Tab stops.

## Validate or clamp a committed draft

The default `commit_behavior="validate"` leaves an out-of-range or off-grid
draft visible and invalid. Set `commit_behavior="clamp"` to clamp a parse-valid
out-of-range draft on blur or Enter. Clamp never guesses an incomplete or
malformed value.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnumber_input/snippets/constraints.py" title="Compare validation and clamping" />

`invalid=True` combines application validation with required, parse, minimum,
maximum, and step validity. Inside Field, set `required`, `disabled`,
`readonly`, and `invalid` on Field rather than on NumberInput.

## Control the canonical value

Pass client `value` and `onValueChange` through `$c-props`. A controlled
interaction is a request: the displayed committed value and Form transport do
not change until the owner supplies the requested exact string.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnumber_input/snippets/controlled.py" title="Control exact value ownership" />

`onInputValueChange` reports the literal draft and its `empty`, `incomplete`,
`invalid`, or `valid` parse status. It does not make the draft a second
controlled axis. Native `@input` also remains available through `input_attrs`.

## Hide controls or enable wheel stepping

Set `show_controls=False` for a text-only spinbutton. Keyboard stepping remains
available. Mouse-wheel and trackpad stepping are disabled by default so page
scrolling cannot accidentally change a value; opt in with `wheel=True`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnumber_input/snippets/without_controls.py" title="Use a compact text-only spinbutton" />

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnumber_input/snippets/wheel.py" title="Opt in to focused wheel stepping" />

## Use localized decimal editing

With configured Citry i18n, the server formats the initial value through the
`citry-ui-number-input` number profile. Under a client-enabled `<c-i18n>`
provider, the editor accepts that locale's digits, decimal separator, grouping,
and signs and reformats an idle value after a live locale change.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnumber_input/snippets/locales.py" title="Inspect locale-aware NumberInput composition" />

Without i18n configuration, the exact source format is canonical ASCII. If a
page uses server-only localized i18n, NumberInput keeps the localized SSR text
until focus and then exposes the separately shipped canonical value; it never
guesses which punctuation the server rendered.

An application may override every library-authored label or validity message.
An explicit override stays fixed during locale switches and creates no catalog
binding.

## Preserve native Form behavior

Without JavaScript, the visible text input owns `name` and submits its literal
localized value for server parsing. After enhancement, an owned hidden input
submits the canonical decimal while the visible editor owns native validity.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnumber_input/snippets/forms.py" title="Submit and reset canonical values" />

Readonly values remain focusable and submit. Disabled values do not submit.
An uncanceled reset restores the server value; controlled state receives a
reset request.

## Choose a variant, size, and public style

Outline, filled, and plain variants combine with sm, md, and lg sizes. Public
`--cui-number-input-*` variables and `[data-citry-ui-part="..."]` selectors
customize the stable root, control, editor, and step Buttons.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnumber_input/snippets/states.py" title="Compare NumberInput states and styling" />

Logical CSS supports RTL while plus and minus keep their mathematical meaning.
Coarse pointers receive larger targets; forced colors preserve borders and
focus; print hides the controls.

<!-- UI_LIBRARY_API_REFERENCE -->
