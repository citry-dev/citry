---
title: Slider and RangeSlider
url: https://citry.dev/v/0.4.4/ui-library/components/slider/
description: "Use CSlider to choose one value from a bounded exact-decimal scale. Use\nCRangeSlider when the user chooses an ordered lower and upper value."
---
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



### Choose one value

[Open the rendered preview](/v/0.4.4/ui-library/components/slider/_previews/basic/)

````citry
from decimal import Decimal
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CSlider

citry.register_library(citry_ui)


class BasicSlider(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "python_slider": CSlider(
                value=Decimal("0.5"),
                min=Decimal(0),
                max=Decimal(1),
                step=Decimal("0.1"),
                input_attrs={"aria-label": "Python opacity"},
            )
        }

    template = """
      <section class="slider-example-grid">
        <c-CField>
          <c-fill name="label">Volume</c-fill>
          <c-fill name="description">Use arrow keys for one-percent steps.</c-fill>
          <c-fill name="default"><c-CSlider name="volume" value="40" /></c-fill>
        </c-CField>
        <article><h3>Python composition</h3>{{ python_slider }}</article>
      </section>
    """
    css = """
      :where(.slider-example-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:1.5rem}
      :where(.slider-example-grid article){display:grid;gap:.75rem}:where(.slider-example-grid h3){margin:0}
    """


preview = BasicSlider()
preview  # noqa: B018
````



### Choose a value range

[Open the rendered preview](/v/0.4.4/ui-library/components/slider/_previews/range/)

````citry
from citry import Component


class RangeSliderExample(Component):
    template = """
      <c-CField>
        <c-fill name="label">Price range</c-fill>
        <c-fill name="description">Lower and upper values stay at least 10 apart.</c-fill>
        <c-fill name="default">
          <c-CRangeSlider name="price" c-value="(20, 80)" c-min_steps_between_thumbs="10" />
        </c-fill>
      </c-CField>
    """


preview = RangeSliderExample()
preview  # noqa: B018
````


## Choose exact values

Server inputs accept `int`, `Decimal`, or a canonical plain-decimal string.
Floats and exponent notation are rejected. The difference between `min` and
`max` must contain a whole number of `step` intervals, capped at one million.
Form submission and callbacks use canonical ASCII strings, so values such as
`Decimal("0.300")` submit as `0.3` without binary-float drift.

`large_step` controls Page Up and Page Down. It defaults to ten steps. Marks
label selected grid positions; they do not add selectable values or alter the
step grid.


### Use an exact decimal scale

[Open the rendered preview](/v/0.4.4/ui-library/components/slider/_previews/exact-decimals/)

````citry
from decimal import Decimal
from typing import Any

from citry import Component


class ExactDecimalSlider(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:  # noqa: ARG002
        return {
            "value": Decimal("0.30"),
            "marks": {Decimal("0.1"): "Low", Decimal("0.3"): "Target", Decimal("0.5"): "High"},
        }

    template = """
      <c-CField>
        <c-fill name="label">Opacity</c-fill>
        <c-fill name="description">Exact 0.05 steps avoid binary floating-point drift.</c-fill>
        <c-fill name="default">
          <c-CSlider c-value="value" min="0.1" max="0.5" step="0.05" c-marks="marks" show_value="always" />
        </c-fill>
      </c-CField>
    """


preview = ExactDecimalSlider()
preview  # noqa: B018
````



### Label selected values

[Open the rendered preview](/v/0.4.4/ui-library/components/slider/_previews/marks/)

````citry
from typing import Any

from citry import Component


class SliderMarks(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:  # noqa: ARG002
        return {"marks": {0: "Silent", 25: "Quiet", 50: "Medium", 75: "Loud", 100: "Maximum"}}

    template = """
      <c-CField>
        <c-fill name="label">Playback volume</c-fill>
        <c-fill name="default"><c-CSlider value="50" c-marks="marks" show_value="always" /></c-fill>
      </c-CField>
    """


preview = SliderMarks()
preview  # noqa: B018
````


## Pick one value or an interval

`CSlider` contributes one form entry. `CRangeSlider name="price"` contributes
two ordered entries with the same name. Use `lower_name` and `upper_name`
together when the server expects distinct field names.

Range thumbs keep their lower and upper identities, remain in the same Tab
order, and do not cross, swap, or push each other. `min_steps_between_thumbs`
sets a grid-step gap between them.


### Submit Slider values

[Open the rendered preview](/v/0.4.4/ui-library/components/slider/_previews/forms/)

````citry
from citry import Component


class SliderForm(Component):
    template = """
      <form
        x-data="{result:'Submit to inspect values'}"
        @submit.prevent="result=JSON.stringify(Array.from(new FormData($event.target).entries()))"
        class="slider-example-stack"
      >
        <c-CField>
          <c-fill name="label">Budget</c-fill>
          <c-fill name="default">
            <c-CRangeSlider lower_name="minimum" upper_name="maximum" c-value="(25, 75)" />
          </c-fill>
        </c-CField>
        <div><button type="submit">Submit</button> <button type="reset">Reset</button></div>
        <output x-text="result">Submit to inspect values</output>
      </form>
    """
    css = ":where(.slider-example-stack){display:grid;gap:1rem;max-inline-size:32rem}"


preview = SliderForm()
preview  # noqa: B018
````


## Keyboard and pointer behavior

Arrow Right and Arrow Up add one step; Arrow Left and Arrow Down subtract one.
Page Up and Page Down use `large_step`; Home and End move to the current
thumb's allowed bounds. For a range, Tab visits lower then upper. Horizontal
pointer geometry mirrors in RTL while keyboard value direction stays stable.

The no-JavaScript fallback is one native range input for `CSlider` and two
clearly labeled native range inputs for `CRangeSlider`. Once enhanced, the
styled thumbs take over interaction while the native controls continue to own
form submission and reset.


### Use vertical Sliders

[Open the rendered preview](/v/0.4.4/ui-library/components/slider/_previews/vertical/)

````citry
from citry import Component


class VerticalSliders(Component):
    template = """
      <section class="vertical-slider-row">
        <c-CSlider value="30" orientation="vertical" c-input_attrs="{'aria-label':'Level'}" />
        <c-CRangeSlider c-value="(20, 70)" orientation="vertical" lower_label="Floor" upper_label="Ceiling" />
      </section>
    """
    css = ":where(.vertical-slider-row){display:flex;gap:3rem;min-block-size:14rem;align-items:center}"


preview = VerticalSliders()
preview  # noqa: B018
````


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



### Control Slider values

[Open the rendered preview](/v/0.4.4/ui-library/components/slider/_previews/controlled/)

````citry
from citry import Component


class ControlledRangeSlider(Component):
    template = """
      <section x-data="{range:['20','80']}" class="slider-example-stack">
        <c-CRangeSlider
          c-value="(20, 80)"
          $c-props="{value:range,onValueChange:(next)=>range=next}"
        />
        <output x-text="`Selected ${range[0]} through ${range[1]}`">Selected 20 through 80</output>
      </section>
    """
    css = ":where(.slider-example-stack){display:grid;gap:1rem;max-inline-size:32rem}"


preview = ControlledRangeSlider()
preview  # noqa: B018
````


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


### Format localized Slider values

[Open the rendered preview](/v/0.4.4/ui-library/components/slider/_previews/locales/)

````citry
from citry import Component


class LocalizedSlider(Component):
    template = """
      <section class="slider-example-stack">
        <p>Inside a client-enabled <code>&lt;c-i18n&gt;</code>, labels and formatted values switch locale in place.</p>
        <c-CRangeSlider c-value="('1234.5', '5678.5')" min="0" max="10000" step="0.5" show_value="always" />
        <p>Canonical Form values remain <code>1234.5</code> and <code>5678.5</code>.</p>
      </section>
    """
    css = ":where(.slider-example-stack){display:grid;gap:1rem;max-inline-size:36rem}"


preview = LocalizedSlider()
preview  # noqa: B018
````


## State and customization

`readonly` preserves a submitted value and focusable slider semantics while
blocking mutation. `disabled` removes interaction and form participation.
Choose `solid` or `subtle`, three sizes, horizontal or vertical orientation,
and `never`, `interaction`, or `always` value bubbles. Use the documented CSS
variables and part selectors for styling; `attrs` and input-attribute mappings
cannot replace state, form, identity, or accessibility attributes owned by the
component.


### Compare Slider states

[Open the rendered preview](/v/0.4.4/ui-library/components/slider/_previews/states/)

````citry
from citry import Component


class SliderStates(Component):
    template = """
      <section class="slider-state-grid">
        <c-CSlider value="30" variant="solid" size="sm" c-input_attrs="{'aria-label':'Small solid'}" />
        <c-CSlider value="50" variant="subtle" show_value="always" c-input_attrs="{'aria-label':'Subtle'}" />
        <c-CSlider value="70" size="lg" readonly c-input_attrs="{'aria-label':'Readonly'}" />
        <c-CSlider value="90" disabled invalid c-input_attrs="{'aria-label':'Disabled invalid'}" />
      </section>
    """
    css = ":where(.slider-state-grid){display:grid;gap:1.5rem;max-inline-size:36rem}"


preview = SliderStates()
preview  # noqa: B018
````


## API reference

### Inputs

#### CSlider server inputs

Server inputs are passed in a template through `<c-CSlider ... />` or in Python through
`CSlider(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 17rem; --ui-api-column-3-width: 13rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="slider-input-cslider-server-inputs-value"></span>`value` | `CSliderExact | None` ([`CSliderExact`](#slider-interface-exact)) | `None` | Sets the initial exact value; None uses min. |
| <span id="slider-input-cslider-server-inputs-name"></span>`name` | `str | None` | `None` | Names the progressive native Form entry. |
| <span id="slider-input-cslider-server-inputs-form"></span>`form` | `str | None` | `None` | Associates the Form entry with an external Form ID. |
| <span id="slider-input-cslider-server-inputs-id"></span>`id` | `str | None` | generated | Sets the public native input ID and enhanced label target. |
| <span id="slider-input-cslider-server-inputs-min"></span>`min` | `CSliderExact` ([`CSliderExact`](#slider-interface-exact)) | `0` | Sets the inclusive exact minimum and step-grid origin. |
| <span id="slider-input-cslider-server-inputs-max"></span>`max` | `CSliderExact` ([`CSliderExact`](#slider-interface-exact)) | `100` | Sets the inclusive exact maximum. |
| <span id="slider-input-cslider-server-inputs-step"></span>`step` | `CSliderExact` ([`CSliderExact`](#slider-interface-exact)) | `1` | Sets the positive exact grid interval. |
| <span id="slider-input-cslider-server-inputs-large-step"></span>`large_step` | `CSliderExact | None` ([`CSliderExact`](#slider-interface-exact)) | Ten steps. | Sets the positive whole-step Page Up and Page Down interval. |
| <span id="slider-input-cslider-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Blocks focus mutation and Form participation outside Field. |
| <span id="slider-input-cslider-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Preserves focus and submission while blocking mutation outside Field. |
| <span id="slider-input-cslider-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Reflects application invalid state outside Field. |
| <span id="slider-input-cslider-server-inputs-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CSliderOrientation`](#slider-interface-orientation)) | `"horizontal"` | Selects track orientation. |
| <span id="slider-input-cslider-server-inputs-variant"></span>`variant` | `"solid" | "subtle"` ([`CSliderVariant`](#slider-interface-variant)) | `"solid"` | Selects visual treatment. |
| <span id="slider-input-cslider-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CSliderSize`](#slider-interface-size)) | `"md"` | Selects track and thumb sizing. |
| <span id="slider-input-cslider-server-inputs-show-value"></span>`show_value` | `"never" | "interaction" | "always"` ([`CSliderShowValue`](#slider-interface-show-value)) | `"interaction"` | Controls localized value bubbles. |
| <span id="slider-input-cslider-server-inputs-show-marks"></span>`show_marks` | `bool | None` | True when marks exist. | Shows or hides mark dots and labels. |
| <span id="slider-input-cslider-server-inputs-marks"></span>`marks` | `Mapping[CSliderExact, str] | Sequence[CSliderExact] | None` | `None` | Adds up to 101 bounded step-grid marks. |
| <span id="slider-input-cslider-server-inputs-format"></span>`format` | `str` | `"citry-ui-slider"` | Selects the named i18n number format profile for visible and accessible values. |
| <span id="slider-input-cslider-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#slider-interface-class-value)) | `None` | Adds classes to the documented root and merges with attrs. |
| <span id="slider-input-cslider-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#slider-interface-style-value)) | `None` | Adds styles to the documented root and merges with attrs. |
| <span id="slider-input-cslider-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes without replacing owned state or identity. |
| <span id="slider-input-cslider-server-inputs-input-attrs"></span>`input_attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed native-input attributes including standalone accessible naming. |

</div>

#### CRangeSlider server inputs

Server inputs are passed in a template through `<c-CRangeSlider ... />` or in Python through
`CRangeSlider(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 17rem; --ui-api-column-3-width: 13rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="slider-input-crange-slider-server-inputs-value"></span>`value` | `tuple[CSliderExact, CSliderExact] | None` ([`CSliderExact`](#slider-interface-exact)) | (min, max) | Sets the initial ordered lower and upper exact values. |
| <span id="slider-input-crange-slider-server-inputs-name"></span>`name` | `str | None` | `None` | Names both ordered Form entries when separate names are omitted. |
| <span id="slider-input-crange-slider-server-inputs-lower-name"></span>`lower_name` | `str | None` | `None` | Names the lower Form entry when supplied together with upper_name. |
| <span id="slider-input-crange-slider-server-inputs-upper-name"></span>`upper_name` | `str | None` | `None` | Names the upper Form entry when supplied together with lower_name. |
| <span id="slider-input-crange-slider-server-inputs-form"></span>`form` | `str | None` | `None` | Associates both Form entries with an external Form ID. |
| <span id="slider-input-crange-slider-server-inputs-id"></span>`id` | `str | None` | generated | Sets the lower native input ID and bases the generated upper and root IDs. |
| <span id="slider-input-crange-slider-server-inputs-min"></span>`min` | `CSliderExact` ([`CSliderExact`](#slider-interface-exact)) | `0` | Sets the inclusive exact minimum and step-grid origin. |
| <span id="slider-input-crange-slider-server-inputs-max"></span>`max` | `CSliderExact` ([`CSliderExact`](#slider-interface-exact)) | `100` | Sets the inclusive exact maximum. |
| <span id="slider-input-crange-slider-server-inputs-step"></span>`step` | `CSliderExact` ([`CSliderExact`](#slider-interface-exact)) | `1` | Sets the positive exact grid interval. |
| <span id="slider-input-crange-slider-server-inputs-large-step"></span>`large_step` | `CSliderExact | None` ([`CSliderExact`](#slider-interface-exact)) | Ten steps. | Sets the positive whole-step Page Up and Page Down interval. |
| <span id="slider-input-crange-slider-server-inputs-min-steps-between-thumbs"></span>`min_steps_between_thumbs` | `int` | `0` | Keeps this many grid intervals between fixed lower and upper thumbs. |
| <span id="slider-input-crange-slider-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Blocks focus mutation and Form participation outside Field. |
| <span id="slider-input-crange-slider-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Preserves focus and ordered submission while blocking mutation outside Field. |
| <span id="slider-input-crange-slider-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Reflects application invalid state outside Field. |
| <span id="slider-input-crange-slider-server-inputs-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CSliderOrientation`](#slider-interface-orientation)) | `"horizontal"` | Selects track orientation. |
| <span id="slider-input-crange-slider-server-inputs-variant"></span>`variant` | `"solid" | "subtle"` ([`CSliderVariant`](#slider-interface-variant)) | `"solid"` | Selects visual treatment. |
| <span id="slider-input-crange-slider-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CSliderSize`](#slider-interface-size)) | `"md"` | Selects track and thumb sizing. |
| <span id="slider-input-crange-slider-server-inputs-show-value"></span>`show_value` | `"never" | "interaction" | "always"` ([`CSliderShowValue`](#slider-interface-show-value)) | `"interaction"` | Controls both localized value bubbles. |
| <span id="slider-input-crange-slider-server-inputs-show-marks"></span>`show_marks` | `bool | None` | True when marks exist. | Shows or hides mark dots and labels. |
| <span id="slider-input-crange-slider-server-inputs-marks"></span>`marks` | `Mapping[CSliderExact, str] | Sequence[CSliderExact] | None` | `None` | Adds up to 101 bounded step-grid marks. |
| <span id="slider-input-crange-slider-server-inputs-format"></span>`format` | `str` | `"citry-ui-slider"` | Selects the named i18n number format profile for both values. |
| <span id="slider-input-crange-slider-server-inputs-lower-label"></span>`lower_label` | `str` | `"Lower value"` | Overrides the catalog-backed lower-thumb accessible name. |
| <span id="slider-input-crange-slider-server-inputs-upper-label"></span>`upper_label` | `str` | `"Upper value"` | Overrides the catalog-backed upper-thumb accessible name. |
| <span id="slider-input-crange-slider-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#slider-interface-class-value)) | `None` | Adds classes to the documented root and merges with attrs. |
| <span id="slider-input-crange-slider-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#slider-interface-style-value)) | `None` | Adds styles to the documented root and merges with attrs. |
| <span id="slider-input-crange-slider-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes without replacing owned state or identity. |
| <span id="slider-input-crange-slider-server-inputs-lower-input-attrs"></span>`lower_input_attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed attributes to the lower native input. |
| <span id="slider-input-crange-slider-server-inputs-upper-input-attrs"></span>`upper_input_attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed attributes to the upper native input. |

</div>

#### CSlider client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CSlider />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="slider-input-cslider-client-inputs-value"></span>`value` | `canonical decimal string` | Releases control to the last uncontrolled value. | Controls the exact value while supplied. |
| <span id="slider-input-cslider-client-inputs-min"></span>`min` | `canonical decimal string` | Uses the server value. | Replaces the minimum when the resulting grid is valid. |
| <span id="slider-input-cslider-client-inputs-max"></span>`max` | `canonical decimal string` | Uses the server value. | Replaces the maximum when the resulting grid is valid. |
| <span id="slider-input-cslider-client-inputs-step"></span>`step` | `positive canonical decimal string` | Uses the server value. | Replaces the grid interval when min and max contain whole steps. |
| <span id="slider-input-cslider-client-inputs-large-step"></span>`largeStep` | `positive canonical decimal string` | Uses the server value. | Replaces the Page Up and Page Down interval. |
| <span id="slider-input-cslider-client-inputs-disabled"></span>`disabled` | `boolean` | Uses server or owner state. | Controls mutation and Form participation. |
| <span id="slider-input-cslider-client-inputs-readonly"></span>`readonly` | `boolean` | Uses server or owner state. | Controls focusable nonmutable state. |
| <span id="slider-input-cslider-client-inputs-invalid"></span>`invalid` | `boolean` | Uses server or Field state. | Controls application invalid state. |
| <span id="slider-input-cslider-client-inputs-orientation"></span>`orientation` | `CSliderOrientation` ([`CSliderOrientation`](#slider-interface-orientation)) | Uses the server value. | Controls track orientation. |
| <span id="slider-input-cslider-client-inputs-variant"></span>`variant` | `CSliderVariant` ([`CSliderVariant`](#slider-interface-variant)) | Uses the server value. | Controls visual treatment. |
| <span id="slider-input-cslider-client-inputs-size"></span>`size` | `CSliderSize` ([`CSliderSize`](#slider-interface-size)) | Uses the server value. | Controls coordinated sizing. |
| <span id="slider-input-cslider-client-inputs-show-value"></span>`showValue` | `CSliderShowValue` ([`CSliderShowValue`](#slider-interface-show-value)) | Uses the server value. | Controls value-bubble visibility. |
| <span id="slider-input-cslider-client-inputs-format"></span>`format` | `string` | Uses the server profile. | Controls locale-aware visible and accessible value formatting. |
| <span id="slider-input-cslider-client-inputs-on-value-change"></span>`onValueChange` | `function` | No live value callback. | Receives each user value request. |
| <span id="slider-input-cslider-client-inputs-on-value-change-end"></span>`onValueChangeEnd` | `function` | No completed-interaction callback. | Receives each keyboard request and completed pointer gesture. |

</div>

#### CRangeSlider client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CRangeSlider />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="slider-input-crange-slider-client-inputs-value"></span>`value` | `[canonical decimal string, canonical decimal string]` | Releases control to the last uncontrolled pair. | Controls the ordered exact pair while supplied. |
| <span id="slider-input-crange-slider-client-inputs-min"></span>`min` | `canonical decimal string` | Uses the server value. | Replaces the minimum when the resulting grid is valid. |
| <span id="slider-input-crange-slider-client-inputs-max"></span>`max` | `canonical decimal string` | Uses the server value. | Replaces the maximum when the resulting grid is valid. |
| <span id="slider-input-crange-slider-client-inputs-step"></span>`step` | `positive canonical decimal string` | Uses the server value. | Replaces the grid interval when min and max contain whole steps. |
| <span id="slider-input-crange-slider-client-inputs-large-step"></span>`largeStep` | `positive canonical decimal string` | Uses the server value. | Replaces the Page Up and Page Down interval. |
| <span id="slider-input-crange-slider-client-inputs-min-steps-between-thumbs"></span>`minStepsBetweenThumbs` | `nonnegative integer` | Uses the server value. | Controls the minimum lower-to-upper grid gap. |
| <span id="slider-input-crange-slider-client-inputs-disabled"></span>`disabled` | `boolean` | Uses server or owner state. | Controls mutation and Form participation. |
| <span id="slider-input-crange-slider-client-inputs-readonly"></span>`readonly` | `boolean` | Uses server or owner state. | Controls focusable nonmutable state. |
| <span id="slider-input-crange-slider-client-inputs-invalid"></span>`invalid` | `boolean` | Uses server or Field state. | Controls application invalid state. |
| <span id="slider-input-crange-slider-client-inputs-orientation"></span>`orientation` | `CSliderOrientation` ([`CSliderOrientation`](#slider-interface-orientation)) | Uses the server value. | Controls track orientation. |
| <span id="slider-input-crange-slider-client-inputs-variant"></span>`variant` | `CSliderVariant` ([`CSliderVariant`](#slider-interface-variant)) | Uses the server value. | Controls visual treatment. |
| <span id="slider-input-crange-slider-client-inputs-size"></span>`size` | `CSliderSize` ([`CSliderSize`](#slider-interface-size)) | Uses the server value. | Controls coordinated sizing. |
| <span id="slider-input-crange-slider-client-inputs-show-value"></span>`showValue` | `CSliderShowValue` ([`CSliderShowValue`](#slider-interface-show-value)) | Uses the server value. | Controls both value bubbles. |
| <span id="slider-input-crange-slider-client-inputs-format"></span>`format` | `string` | Uses the server profile. | Controls locale-aware visible and accessible value formatting. |
| <span id="slider-input-crange-slider-client-inputs-on-value-change"></span>`onValueChange` | `function` | No live value callback. | Receives each ordered-pair request. |
| <span id="slider-input-crange-slider-client-inputs-on-value-change-end"></span>`onValueChangeEnd` | `function` | No completed-interaction callback. | Receives each keyboard request and completed pointer gesture. |

</div>

### Slots

-

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CSlider events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="slider-event-cslider-events-on-value-change"></span>`onValueChange` | `(value: string, detail: CSliderValueChangeDetail) => void` ([`CSliderValueChangeDetail`](#slider-interface-cslider-value-change-detail)) | Each pointer-drag or keyboard value request. | `{value, previousValue, controlled, source, sourceEvent, phase}` ([`CSliderValueChangeDetail`](#slider-interface-cslider-value-change-detail)) | Uncontrolled state and native Form value update before notification; controlled state is request-only. |
| <span id="slider-event-cslider-events-on-value-change-end"></span>`onValueChangeEnd` | `(value: string, detail: CSliderValueChangeDetail) => void` ([`CSliderValueChangeDetail`](#slider-interface-cslider-value-change-detail)) | A keyboard request or completed changed pointer gesture. | `{value, previousValue, controlled, source, sourceEvent, phase}` ([`CSliderValueChangeDetail`](#slider-interface-cslider-value-change-detail)) | Reports the final requested value once per completed interaction. |

</div>

#### CRangeSlider events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="slider-event-crange-slider-events-on-value-change"></span>`onValueChange` | `(value: tuple[str, str], detail: CRangeSliderValueChangeDetail) => void` ([`CRangeSliderValueChangeDetail`](#slider-interface-crange-slider-value-change-detail)) | Each lower or upper pointer-drag or keyboard pair request. | `{value, previousValue, controlled, source, sourceEvent, phase, activeThumb}` ([`CRangeSliderValueChangeDetail`](#slider-interface-crange-slider-value-change-detail)) | Preserves ordered stable thumb identity; controlled state is request-only. |
| <span id="slider-event-crange-slider-events-on-value-change-end"></span>`onValueChangeEnd` | `(value: tuple[str, str], detail: CRangeSliderValueChangeDetail) => void` ([`CRangeSliderValueChangeDetail`](#slider-interface-crange-slider-value-change-detail)) | A keyboard request or completed changed pointer gesture. | `{value, previousValue, controlled, source, sourceEvent, phase, activeThumb}` ([`CRangeSliderValueChangeDetail`](#slider-interface-crange-slider-value-change-detail)) | Reports the final requested ordered pair once per completed interaction. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CSlider CSS variables

Apply these variables to `CSlider` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="slider-css-cslider-css-variables-track-color"></span>`--cui-slider-track-color` | `color` | Unfilled rail color. | `Mixed CanvasText.` |
| <span id="slider-css-cslider-css-variables-fill-color"></span>`--cui-slider-fill-color` | `color` | Selected rail color. | `AccentColor` |
| <span id="slider-css-cslider-css-variables-thumb-color"></span>`--cui-slider-thumb-color` | `color` | Thumb fill. | `Canvas` |
| <span id="slider-css-cslider-css-variables-thumb-border-color"></span>`--cui-slider-thumb-border-color` | `color` | Thumb outline. | `AccentColor` |
| <span id="slider-css-cslider-css-variables-focus-color"></span>`--cui-slider-focus-color` | `color` | Keyboard focus ring. | `Highlight` |
| <span id="slider-css-cslider-css-variables-mark-color"></span>`--cui-slider-mark-color` | `color` | Mark dots. | `CanvasText` |
| <span id="slider-css-cslider-css-variables-value-background"></span>`--cui-slider-value-background` | `color` | Value-bubble background. | `High-contrast ink.` |
| <span id="slider-css-cslider-css-variables-value-foreground"></span>`--cui-slider-value-foreground` | `color` | Value-bubble text. | `High-contrast surface.` |
| <span id="slider-css-cslider-css-variables-track-size"></span>`--cui-slider-track-size` | `length` | Rail thickness. | `0.375rem` |
| <span id="slider-css-cslider-css-variables-thumb-size"></span>`--cui-slider-thumb-size` | `length` | Thumb diameter. | `1.25rem` |
| <span id="slider-css-cslider-css-variables-control-size"></span>`--cui-slider-control-size` | `length` | Minimum interaction block size. | `2.75rem` |
| <span id="slider-css-cslider-css-variables-radius"></span>`--cui-slider-radius` | `length` | Rail and thumb rounding. | `999px` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CSlider attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="slider-attribute-cslider-root-attributes-data-disabled"></span>`data-disabled` | Root div | `present | absent` | Mirrors effective disabledness. |
| <span id="slider-attribute-cslider-root-attributes-data-readonly"></span>`data-readonly` | Root div | `present | absent` | Mirrors effective readonly state. |
| <span id="slider-attribute-cslider-root-attributes-data-invalid"></span>`data-invalid` | Root div | `present | absent` | Mirrors effective invalid state. |
| <span id="slider-attribute-cslider-root-attributes-data-dragging"></span>`data-dragging` | Root div | `present | absent` | Marks an active pointer gesture. |
| <span id="slider-attribute-cslider-root-attributes-data-orientation"></span>`data-orientation` | Root div | `CSliderOrientation` ([`CSliderOrientation`](#slider-interface-orientation)) | Mirrors track orientation. |
| <span id="slider-attribute-cslider-root-attributes-data-variant"></span>`data-variant` | Root div | `CSliderVariant` ([`CSliderVariant`](#slider-interface-variant)) | Mirrors visual treatment. |
| <span id="slider-attribute-cslider-root-attributes-data-size"></span>`data-size` | Root div | `CSliderSize` ([`CSliderSize`](#slider-interface-size)) | Mirrors coordinated sizing. |
| <span id="slider-attribute-cslider-root-attributes-data-show-value"></span>`data-show-value` | Root div | `CSliderShowValue` ([`CSliderShowValue`](#slider-interface-show-value)) | Mirrors value-bubble policy. |

</div>

#### CSlider attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="slider-attribute-cslider-thumb-attributes-role"></span>`role` | Enhanced thumb Button | `"slider"` | Exposes slider interaction semantics. |
| <span id="slider-attribute-cslider-thumb-attributes-aria-valuenow"></span>`aria-valuenow` | Enhanced thumb Button | `canonical decimal` | Exposes the exact current value. |
| <span id="slider-attribute-cslider-thumb-attributes-aria-valuetext"></span>`aria-valuetext` | Enhanced thumb Button | `localized string` | Exposes the locale-formatted current value. |
| <span id="slider-attribute-cslider-thumb-attributes-aria-valuemin"></span>`aria-valuemin` | Enhanced thumb Button | `canonical decimal` | Exposes the current inclusive lower bound. |
| <span id="slider-attribute-cslider-thumb-attributes-aria-valuemax"></span>`aria-valuemax` | Enhanced thumb Button | `canonical decimal` | Exposes the current inclusive upper bound. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CSlider selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="slider-selector-cslider-selectors-slider"></span>`[data-citry-ui-part="slider"]` | CSlider root div | State reflections and root customization destination. |
| <span id="slider-selector-cslider-selectors-range-slider"></span>`[data-citry-ui-part="range-slider"]` | CRangeSlider root div | State reflections and root customization destination. |
| <span id="slider-selector-cslider-selectors-native-input"></span>`[data-citry-ui-part="native-input"]` | Native range input | No-JavaScript fallback and enhanced Form transport. |
| <span id="slider-selector-cslider-selectors-control"></span>`[data-citry-ui-part="control"]` | Enhanced control div | Pointer interaction surface. |
| <span id="slider-selector-cslider-selectors-track"></span>`[data-citry-ui-part="track"]` | Track div | Positions fill marks and thumbs. |
| <span id="slider-selector-cslider-selectors-fill"></span>`[data-citry-ui-part="fill"]` | Fill span | Shows the selected value or interval. |
| <span id="slider-selector-cslider-selectors-mark"></span>`[data-citry-ui-part="mark"]` | Mark span | Shows a configured grid position. |
| <span id="slider-selector-cslider-selectors-mark-label"></span>`[data-citry-ui-part="mark-label"]` | Mark label span | Shows application-owned mark text. |
| <span id="slider-selector-cslider-selectors-thumb"></span>`[data-citry-ui-part="thumb"]` | Enhanced slider Button | Keyboard focus target and draggable value owner. |
| <span id="slider-selector-cslider-selectors-value"></span>`[data-citry-ui-part="value"]` | Value span | Shows the locale-formatted current value. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="slider-interface-exact"></span>`CSliderExact` | `int | Decimal | str` |
| <span id="slider-interface-orientation"></span>`CSliderOrientation` | `Literal["horizontal", "vertical"]` |
| <span id="slider-interface-variant"></span>`CSliderVariant` | `Literal["solid", "subtle"]` |
| <span id="slider-interface-size"></span>`CSliderSize` | `Literal["sm", "md", "lg"]` |
| <span id="slider-interface-show-value"></span>`CSliderShowValue` | `Literal["never", "interaction", "always"]` |
| <span id="slider-interface-change-source"></span>`CSliderChangeSource` | `Literal["pointer", "keyboard", "reset"]` |
| <span id="slider-interface-change-phase"></span>`CSliderChangePhase` | `Literal["change", "end"]` |
| <span id="slider-interface-range-thumb"></span>`CRangeSliderThumb` | `Literal["lower", "upper"]` |
| <span id="slider-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="slider-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="slider-interface-cslider-value-change-detail"></span>

#### `CSliderValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="slider-interface-cslider-value-change-detail-value"></span>`value` | `canonical decimal string` | - | Requested exact value. |
| <span id="slider-interface-cslider-value-change-detail-previous-value"></span>`previousValue` | `canonical decimal string` | - | Effective exact value before the interaction. |
| <span id="slider-interface-cslider-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client value owns state. |
| <span id="slider-interface-cslider-value-change-detail-source"></span>`source` | `CSliderChangeSource` ([`CSliderChangeSource`](#slider-interface-change-source)) | - | Pointer keyboard or reset cause. |
| <span id="slider-interface-cslider-value-change-detail-source-event"></span>`sourceEvent` | `object | null` | - | Native interaction event when one exists. |
| <span id="slider-interface-cslider-value-change-detail-phase"></span>`phase` | `CSliderChangePhase` ([`CSliderChangePhase`](#slider-interface-change-phase)) | - | Live change or completed interaction. |

</div>

<span id="slider-interface-crange-slider-value-change-detail"></span>

#### `CRangeSliderValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="slider-interface-crange-slider-value-change-detail-value"></span>`value` | `[canonical decimal string, canonical decimal string]` | - | Requested ordered exact pair. |
| <span id="slider-interface-crange-slider-value-change-detail-previous-value"></span>`previousValue` | `[canonical decimal string, canonical decimal string]` | - | Effective ordered pair before the interaction. |
| <span id="slider-interface-crange-slider-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client value owns state. |
| <span id="slider-interface-crange-slider-value-change-detail-source"></span>`source` | `CSliderChangeSource` ([`CSliderChangeSource`](#slider-interface-change-source)) | - | Pointer keyboard or reset cause. |
| <span id="slider-interface-crange-slider-value-change-detail-source-event"></span>`sourceEvent` | `object | null` | - | Native interaction event when one exists. |
| <span id="slider-interface-crange-slider-value-change-detail-phase"></span>`phase` | `CSliderChangePhase` ([`CSliderChangePhase`](#slider-interface-change-phase)) | - | Live change or completed interaction. |
| <span id="slider-interface-crange-slider-value-change-detail-active-thumb"></span>`activeThumb` | `CRangeSliderThumb` ([`CRangeSliderThumb`](#slider-interface-range-thumb)) | - | Stable lower or upper thumb that requested the change. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CRangeSlider translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="slider-translation-crange-slider-translations-lower"></span>`citry-ui-range-slider-lower` | Distinguishes the lower thumb and native fallback input. | `None` | `lower_label` | $c-tr updates the stable hidden label; both controls reference it. |
| <span id="slider-translation-crange-slider-translations-upper"></span>`citry-ui-range-slider-upper` | Distinguishes the upper thumb and native fallback input. | `None` | `upper_label` | $c-tr updates the stable hidden label; both controls reference it. |

</div>
