# Slider and RangeSlider

Use `CSlider` to choose one value from a bounded exact-decimal scale. Use
`CRangeSlider` when the user chooses an ordered lower and upper value.

```citry
<c-CField>
  <c-fill name="label">Volume</c-fill>
  <c-fill name="default">
    <c-CSlider name="volume" value="40" min="0" max="100" />
  </c-fill>
</c-CField>

<c-CField>
  <c-fill name="label">Price range</c-fill>
  <c-fill name="default">
    <c-CRangeSlider name="price" c-value="(20, 80)" min="0" max="100" />
  </c-fill>
</c-CField>
```

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cslider/snippets/basic.py" title="Choose one value" />

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cslider/snippets/range.py" title="Choose a value range" />

## Choose exact values

Server inputs accept `int`, `Decimal`, or a canonical plain-decimal string.
Floats and exponent notation are rejected. The difference between `min` and
`max` must contain a whole number of `step` intervals, capped at one million.
Form submission and callbacks use canonical ASCII strings, so values such as
`Decimal("0.300")` submit as `0.3` without binary-float drift.

`large_step` controls Page Up and Page Down. It defaults to ten steps. Marks
label selected grid positions; they do not add selectable values or alter the
step grid.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cslider/snippets/exact_decimals.py" title="Use an exact decimal scale" />

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cslider/snippets/marks.py" title="Label selected values" />

## Pick one value or an interval

`CSlider` contributes one form entry. `CRangeSlider name="price"` contributes
two ordered entries with the same name. Use `lower_name` and `upper_name`
together when the server expects distinct field names.

Range thumbs keep their lower and upper identities, remain in the same Tab
order, and do not cross, swap, or push each other. `min_steps_between_thumbs`
sets a grid-step gap between them.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cslider/snippets/forms.py" title="Submit Slider values" />

## Keyboard and pointer behavior

Arrow Right and Arrow Up add one step; Arrow Left and Arrow Down subtract one.
Page Up and Page Down use `large_step`; Home and End move to the current
thumb's allowed bounds. For a range, Tab visits lower then upper. Horizontal
pointer geometry mirrors in RTL while keyboard value direction stays stable.

The no-JavaScript fallback is one native range input for `CSlider` and two
clearly labeled native range inputs for `CRangeSlider`. Once enhanced, the
styled thumbs take over interaction while the native controls continue to own
form submission and reset.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cslider/snippets/vertical.py" title="Use vertical Sliders" />

## Controlled values and callbacks

Omitting client `value` leaves the component uncontrolled. Supplying it through
`$c-props` makes every interaction a request: the thumb moves only after the
owner returns the requested value. `onValueChange` fires during each accepted
pointer or keyboard step. `onValueChangeEnd` fires once at the end of a pointer
gesture and once after a keyboard request.

```citry
<div x-data="{ price: ['20', '80'] }">
  <c-CRangeSlider
    c-value="(20, 80)"
    $c-props="{
      value: price,
      onValueChange: (next) => price = next,
    }"
  />
</div>
```

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cslider/snippets/controlled.py" title="Control Slider values" />

## Labels, fields, and localization

Wrap either component in `CField` for its visible label, description, error,
disabled, readonly, and invalid state. A standalone `CSlider` needs an
accessible name through `input_attrs`. `CRangeSlider` combines the Field label
with localized “Lower value” and “Upper value” labels; override those strings
with `lower_label` and `upper_label` when the application needs domain-specific
names.

Displayed values and `aria-valuetext` use the `number.citry-ui-slider` profile.
Under a client-enabled `c-i18n` provider, thumb labels and formatted values
update after a browser-side locale switch. Canonical form values never change.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cslider/snippets/locales.py" title="Format localized Slider values" />

## State and customization

`readonly` preserves a submitted value and focusable slider semantics while
blocking mutation. `disabled` removes interaction and form participation.
Choose `solid` or `subtle`, three sizes, horizontal or vertical orientation,
and `never`, `interaction`, or `always` value bubbles. Use the documented CSS
variables and part selectors for styling; `attrs` and input-attribute mappings
cannot replace state, form, identity, or accessibility attributes owned by the
component.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cslider/snippets/states.py" title="Compare Slider states" />
