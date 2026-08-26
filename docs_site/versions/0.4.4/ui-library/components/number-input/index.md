---
title: NumberInput
url: https://citry.dev/v/0.4.4/ui-library/components/number-input/
description: "Edit and submit an exact decimal quantity with localized spinbutton behavior."
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



### Edit and submit a quantity

[Open the rendered preview](/v/0.4.4/ui-library/components/number-input/_previews/basic/)

````citry
from decimal import Decimal
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNumberInput

citry.register_library(citry_ui)


class BasicNumberInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "python_control": CNumberInput(
                name="threshold",
                value=Decimal("2.5"),
                min=Decimal(0),
                max=Decimal(10),
                step=Decimal("0.5"),
                input_attrs={"aria-label": "Python threshold"},
            )
        }

    template = """
      <section class="number-input-demo-grid">
        <c-CField required>
          <c-fill name="label">Crates</c-fill>
          <c-fill name="description">Choose from 1 through 20.</c-fill>
          <c-fill name="default">
            <c-CNumberInput name="crates" value="2" min="1" max="20" />
          </c-fill>
        </c-CField>
        <article><h3>Python composition</h3>{{ python_control }}</article>
      </section>
    """

    css = """
      :where(.number-input-demo-grid) {
        display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem;align-items:start
      }
      :where(.number-input-demo-grid article) { display:grid;gap:.75rem }
      :where(.number-input-demo-grid h3) { margin:0 }
    """


preview = BasicNumberInput()
preview  # noqa: B018
````


Standalone use needs an accessible name in `input_attrs`.

## Keep decimals exact

Server inputs accept `int`, `Decimal`, or a plain-decimal string. Floats,
scientific notation, NaN, and infinity are rejected. Client `value` is a
canonical string or `null`.


### Step exact fractional values

[Open the rendered preview](/v/0.4.4/ui-library/components/number-input/_previews/exact-decimals/)

````citry
from citry import Component


class ExactDecimalNumberInput(Component):
    template = """
      <section class="number-input-example-stack">
        <c-CField>
          <c-fill name="label">Calibration offset</c-fill>
          <c-fill name="description">Exact increments of 0.0001.</c-fill>
          <c-fill name="default">
            <c-CNumberInput name="offset" value="0.1001" min="-1" max="1" step="0.0001" />
          </c-fill>
        </c-CField>
        <p>The submitted enhanced value remains the exact string <code>0.1001</code>.</p>
      </section>
    """
    css = ":where(.number-input-example-stack){display:grid;gap:.75rem;max-inline-size:28rem}"


preview = ExactDecimalNumberInput()
preview  # noqa: B018
````


`step` sets an exact grid based on `min`, or zero when `min` is omitted. Arrow
keys move one step, Page Up and Page Down move ten, and Home/End use a supplied
minimum/maximum. The adjacent Buttons do not add Tab stops.

## Validate or clamp a committed draft

The default `commit_behavior="validate"` leaves an out-of-range or off-grid
draft visible and invalid. Set `commit_behavior="clamp"` to clamp a parse-valid
out-of-range draft on blur or Enter. Clamp never guesses an incomplete or
malformed value.


### Compare validation and clamping

[Open the rendered preview](/v/0.4.4/ui-library/components/number-input/_previews/constraints/)

````citry
from citry import Component


class NumberInputConstraints(Component):
    template = """
      <section class="number-input-example-grid">
        <c-CField required>
          <c-fill name="label">Validate the draft</c-fill>
          <c-fill name="description">Enter a quarter step from 0 through 3.</c-fill>
          <c-fill name="default"><c-CNumberInput value="1" min="0" max="3" step="0.25" /></c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">Clamp on commit</c-fill>
          <c-fill name="description">A parse-valid outside value moves to the nearest bound.</c-fill>
          <c-fill name="default"><c-CNumberInput value="1" min="0" max="3" commit_behavior="clamp" /></c-fill>
        </c-CField>
      </section>
    """
    css = """
      :where(.number-input-example-grid) {
        display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem
      }
    """


preview = NumberInputConstraints()
preview  # noqa: B018
````


`invalid=True` combines application validation with required, parse, minimum,
maximum, and step validity. Inside Field, set `required`, `disabled`,
`readonly`, and `invalid` on Field rather than on NumberInput.

## Control the canonical value

Pass client `value` and `onValueChange` through `$c-props`. A controlled
interaction is a request: the displayed committed value and Form transport do
not change until the owner supplies the requested exact string.


### Control exact value ownership

[Open the rendered preview](/v/0.4.4/ui-library/components/number-input/_previews/controlled/)

````citry
from citry import Component


class ControlledNumberInput(Component):
    template = """
      <section x-data="{value:'2',last:'No request yet'}" class="number-input-example-stack">
        <c-CNumberInput
          c-input_attrs="{'aria-label':'Controlled quantity'}"
          $c-props="{
            value,
            onValueChange:(next,detail)=>{value=next;last=`${detail.source}: ${next}`},
          }"
        />
        <output x-text="`Canonical value: ${value}; ${last}`">Canonical value: 2</output>
      </section>
    """
    css = ":where(.number-input-example-stack){display:grid;gap:.75rem;max-inline-size:28rem}"


preview = ControlledNumberInput()
preview  # noqa: B018
````


`onInputValueChange` reports the literal draft and its `empty`, `incomplete`,
`invalid`, or `valid` parse status. It does not make the draft a second
controlled axis. Native `@input` also remains available through `input_attrs`.

## Hide controls or enable wheel stepping

Set `show_controls=False` for a text-only spinbutton. Keyboard stepping remains
available. Mouse-wheel and trackpad stepping are disabled by default so page
scrolling cannot accidentally change a value; opt in with `wheel=True`.


### Use a compact text-only spinbutton

[Open the rendered preview](/v/0.4.4/ui-library/components/number-input/_previews/without-controls/)

````citry
from citry import Component


class NumberInputWithoutControls(Component):
    template = """
      <c-CField>
        <c-fill name="label">Keyboard stepper</c-fill>
        <c-fill name="description">Use Arrow Up/Down; adjacent controls are hidden.</c-fill>
        <c-fill name="default">
          <c-CNumberInput value="5" min="0" max="10" c-show_controls="False" />
        </c-fill>
      </c-CField>
    """


preview = NumberInputWithoutControls()
preview  # noqa: B018
````



### Opt in to focused wheel stepping

[Open the rendered preview](/v/0.4.4/ui-library/components/number-input/_previews/wheel/)

````citry
from citry import Component


class WheelNumberInput(Component):
    template = """
      <section class="number-input-example-grid">
        <c-CField>
          <c-fill name="label">Wheel remains page scrolling</c-fill>
          <c-fill name="default"><c-CNumberInput value="4" /></c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">Focused wheel changes value</c-fill>
          <c-fill name="description">Explicitly enabled for this control.</c-fill>
          <c-fill name="default"><c-CNumberInput value="4" wheel /></c-fill>
        </c-CField>
      </section>
    """
    css = """
      :where(.number-input-example-grid) {
        display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem
      }
    """


preview = WheelNumberInput()
preview  # noqa: B018
````


## Use localized decimal editing

With configured Citry i18n, the server formats the initial value through the
`citry-ui-number-input` number profile. Under a client-enabled `<c-i18n>`
provider, the editor accepts that locale's digits, decimal separator, grouping,
and signs and reformats an idle value after a live locale change.


### Inspect locale-aware NumberInput composition

[Open the rendered preview](/v/0.4.4/ui-library/components/number-input/_previews/locales/)

````citry
from citry import Component


class LocalizedNumberInput(Component):
    template = """
      <section class="number-input-example-stack">
        <p>
          Place the same component under a client-enabled
          <code>&lt;c-i18n&gt;</code> provider to switch locale in place.
        </p>
        <c-CNumberInput
          value="1234.5"
          step="0.1"
          c-input_attrs="{'aria-label':'Localized measurement'}"
        />
        <p>
          The editor and its ARIA value text use the provider locale; the
          enhanced Form value stays <code>1234.5</code>.
        </p>
      </section>
    """
    css = ":where(.number-input-example-stack){display:grid;gap:.75rem;max-inline-size:32rem}"


preview = LocalizedNumberInput()
preview  # noqa: B018
````


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


### Submit and reset canonical values

[Open the rendered preview](/v/0.4.4/ui-library/components/number-input/_previews/forms/)

````citry
from citry import Component


class NumberInputForms(Component):
    template = """
      <form
        x-data="{submitted:'Not submitted'}"
        @submit.prevent="submitted=new FormData($event.target).get('amount')"
        class="number-input-example-stack"
      >
        <c-CField required>
          <c-fill name="label">Amount</c-fill>
          <c-fill name="default"><c-CNumberInput name="amount" value="1.25" step="0.25" /></c-fill>
        </c-CField>
        <div><button type="submit">Submit</button> <button type="reset">Reset</button></div>
        <output x-text="submitted">Not submitted</output>
      </form>
    """
    css = ":where(.number-input-example-stack){display:grid;gap:.75rem;max-inline-size:28rem}"


preview = NumberInputForms()
preview  # noqa: B018
````


Readonly values remain focusable and submit. Disabled values do not submit.
An uncanceled reset restores the server value; controlled state receives a
reset request.

## Choose a variant, size, and public style

Outline, filled, and plain variants combine with sm, md, and lg sizes. Public
`--cui-number-input-*` variables and `[data-citry-ui-part="..."]` selectors
customize the stable root, control, editor, and step Buttons.


### Compare NumberInput states and styling

[Open the rendered preview](/v/0.4.4/ui-library/components/number-input/_previews/states/)

````citry
from citry import Component


class NumberInputStates(Component):
    template = """
      <section class="number-input-state-grid">
        <c-CNumberInput value="2" variant="outline" size="sm" c-input_attrs="{'aria-label':'Small outline'}" />
        <c-CNumberInput value="2" variant="filled" size="md" c-input_attrs="{'aria-label':'Medium filled'}" />
        <c-CNumberInput value="2" variant="plain" size="lg" c-input_attrs="{'aria-label':'Large plain'}" />
        <c-CNumberInput value="2" readonly c-input_attrs="{'aria-label':'Readonly'}" />
        <c-CNumberInput value="2" disabled c-input_attrs="{'aria-label':'Disabled'}" />
        <c-CNumberInput value="2" invalid c-input_attrs="{'aria-label':'Application invalid'}" />
      </section>
    """
    css = """
      :where(.number-input-state-grid) {
        display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem;align-items:start
      }
    """


preview = NumberInputStates()
preview  # noqa: B018
````


Logical CSS supports RTL while plus and minus keep their mathematical meaning.
Coarse pointers receive larger targets; forced colors preserve borders and
focus; print hides the controls.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CNumberInput server inputs

Server inputs are passed in a template through `<c-CNumberInput ... />` or in Python through
`CNumberInput(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 17rem; --ui-api-column-3-width: 12rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="number-input-input-cnumber-input-server-inputs-value"></span>`value` | `CNumberInputExact | None` ([`CNumberInputExact`](#number-input-interface-exact)) | `None` | Sets the initial exact canonical decimal or empty value. |
| <span id="number-input-input-cnumber-input-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the progressive native Form field name. |
| <span id="number-input-input-cnumber-input-server-inputs-form"></span>`form` | `str | None` | `None` | Associates the visible fallback and enhanced transport with an external Form ID. |
| <span id="number-input-input-cnumber-input-server-inputs-id"></span>`id` | `str | None` | generated | Sets the public editor ID and bases the private transport ID. |
| <span id="number-input-input-cnumber-input-server-inputs-min"></span>`min` | `CNumberInputExact | None` ([`CNumberInputExact`](#number-input-interface-exact)) | `None` | Sets the inclusive exact minimum and step-grid base. |
| <span id="number-input-input-cnumber-input-server-inputs-max"></span>`max` | `CNumberInputExact | None` ([`CNumberInputExact`](#number-input-interface-exact)) | `None` | Sets the inclusive exact maximum. |
| <span id="number-input-input-cnumber-input-server-inputs-step"></span>`step` | `CNumberInputExact` ([`CNumberInputExact`](#number-input-interface-exact)) | `1` | Sets a positive exact step. |
| <span id="number-input-input-cnumber-input-server-inputs-required"></span>`required` | `bool | None` | `None` | Enables empty-value validity outside Field; Field owns it inside Field. |
| <span id="number-input-input-cnumber-input-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Blocks focus mutation and Form submission outside Field; Form disabledness also wins. |
| <span id="number-input-input-cnumber-input-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Keeps a focusable submitted value while blocking mutation. |
| <span id="number-input-input-cnumber-input-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Adds application invalid state to native component validity. |
| <span id="number-input-input-cnumber-input-server-inputs-show-controls"></span>`show_controls` | `bool` | `True` | Shows or hides adjacent decrement and increment Buttons. |
| <span id="number-input-input-cnumber-input-server-inputs-wheel"></span>`wheel` | `bool` | `False` | Opts a focused editor into wheel and trackpad stepping. |
| <span id="number-input-input-cnumber-input-server-inputs-commit-behavior"></span>`commit_behavior` | `"validate" | "clamp"` ([`CNumberInputCommitBehavior`](#number-input-interface-commit-behavior)) | `"validate"` | Leaves an invalid committed draft visible or clamps a parse-valid out-of-range value. |
| <span id="number-input-input-cnumber-input-server-inputs-placeholder"></span>`placeholder` | `str | None` | `None` | Sets ordinary editor placeholder text. |
| <span id="number-input-input-cnumber-input-server-inputs-autocomplete"></span>`autocomplete` | `str | None` | `None` | Sets the native autocomplete hint. |
| <span id="number-input-input-cnumber-input-server-inputs-increment-label"></span>`increment_label` | `str` | `"Increase value"` | Overrides the catalog-backed increment Button accessible name. |
| <span id="number-input-input-cnumber-input-server-inputs-decrement-label"></span>`decrement_label` | `str` | `"Decrease value"` | Overrides the catalog-backed decrement Button accessible name. |
| <span id="number-input-input-cnumber-input-server-inputs-required-message"></span>`required_message` | `str` | `"Enter a number."` | Overrides catalog-backed empty required validity. |
| <span id="number-input-input-cnumber-input-server-inputs-invalid-message"></span>`invalid_message` | `str` | `"Enter a valid number."` | Overrides catalog-backed parse validity. |
| <span id="number-input-input-cnumber-input-server-inputs-minimum-message"></span>`minimum_message` | `str containing '{min}'` | `"Enter a value of at least {min}."` | Overrides catalog-backed minimum validity. |
| <span id="number-input-input-cnumber-input-server-inputs-maximum-message"></span>`maximum_message` | `str containing '{max}'` | `"Enter a value of at most {max}."` | Overrides catalog-backed maximum validity. |
| <span id="number-input-input-cnumber-input-server-inputs-step-message"></span>`step_message` | `str containing '{step}'` | `"Enter a value in increments of {step}."` | Overrides catalog-backed step-grid validity. |
| <span id="number-input-input-cnumber-input-server-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CNumberInputVariant`](#number-input-interface-variant)) | `"outline"` | Selects visual treatment. |
| <span id="number-input-input-cnumber-input-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CNumberInputSize`](#number-input-interface-size)) | `"md"` | Selects coordinated editor and control sizing. |
| <span id="number-input-input-cnumber-input-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#number-input-interface-class-value)) | `None` | Adds classes to the documented root and merges with attrs. |
| <span id="number-input-input-cnumber-input-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#number-input-interface-style-value)) | `None` | Adds styles to the documented root and merges with attrs. |
| <span id="number-input-input-cnumber-input-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes without replacing owned state or runtime identity. |
| <span id="number-input-input-cnumber-input-server-inputs-input-attrs"></span>`input_attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed editor attributes including accessible naming and native event observers. |

</div>

#### CNumberInput client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CNumberInput />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 17rem; --ui-api-column-3-width: 18rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="number-input-input-cnumber-input-client-inputs-value"></span>`value` | `canonical string | null` | Releases control to the last uncontrolled committed value. | Controls the exact canonical value while supplied. |
| <span id="number-input-input-cnumber-input-client-inputs-min"></span>`min` | `canonical string | null` | Uses the server minimum. | Replaces or removes the inclusive minimum. |
| <span id="number-input-input-cnumber-input-client-inputs-max"></span>`max` | `canonical string | null` | Uses the server maximum. | Replaces or removes the inclusive maximum. |
| <span id="number-input-input-cnumber-input-client-inputs-step"></span>`step` | `positive canonical string` | Uses the server step. | Replaces the exact step grid. |
| <span id="number-input-input-cnumber-input-client-inputs-required"></span>`required` | `boolean` | Uses server or Field state. | Controls standalone required validity. |
| <span id="number-input-input-cnumber-input-client-inputs-disabled"></span>`disabled` | `boolean` | Uses server or owner state. | Controls mutation and Form participation. |
| <span id="number-input-input-cnumber-input-client-inputs-readonly"></span>`readonly` | `boolean` | Uses server or owner state. | Controls focusable nonmutable state. |
| <span id="number-input-input-cnumber-input-client-inputs-invalid"></span>`invalid` | `boolean` | Uses server or Field state. | Controls application invalid state. |
| <span id="number-input-input-cnumber-input-client-inputs-show-controls"></span>`showControls` | `boolean` | Uses the server input. | Controls adjacent Button visibility. |
| <span id="number-input-input-cnumber-input-client-inputs-wheel"></span>`wheel` | `boolean` | Uses the server input. | Controls focused wheel stepping. |
| <span id="number-input-input-cnumber-input-client-inputs-commit-behavior"></span>`commitBehavior` | `"validate" | "clamp"` ([`CNumberInputCommitBehavior`](#number-input-interface-commit-behavior)) | Uses the server input. | Controls out-of-range commit policy. |
| <span id="number-input-input-cnumber-input-client-inputs-placeholder"></span>`placeholder` | `string | null` | Uses the server input. | Controls visible placeholder text. |
| <span id="number-input-input-cnumber-input-client-inputs-autocomplete"></span>`autocomplete` | `string | null` | Uses the server input. | Controls the autocomplete hint. |
| <span id="number-input-input-cnumber-input-client-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CNumberInputVariant`](#number-input-interface-variant)) | Uses the server input. | Controls visual treatment. |
| <span id="number-input-input-cnumber-input-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CNumberInputSize`](#number-input-interface-size)) | Uses the server input. | Controls coordinated sizing. |
| <span id="number-input-input-cnumber-input-client-inputs-on-value-change"></span>`onValueChange` | `function` | No semantic value callback. | Receives successful commit and reset requests. |
| <span id="number-input-input-cnumber-input-client-inputs-on-input-value-change"></span>`onInputValueChange` | `function` | No semantic draft callback. | Receives literal draft edits and parse status. |

</div>

### Slots

-

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CNumberInput events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="number-input-event-cnumber-input-events-on-value-change"></span>`onValueChange` | `(value: string | null, detail: CNumberInputValueChangeDetail) => void` ([`CNumberInputValueChangeDetail`](#number-input-interface-cnumber-input-value-change-detail)) | A valid blur, Enter, step, bound jump, wheel step, or reset requests a changed canonical value. | `{value, previousValue, inputValue, controlled, source, sourceEvent}` ([`CNumberInputValueChangeDetail`](#number-input-interface-cnumber-input-value-change-detail)) | Uncontrolled state and canonical Form transport commit before notification; controlled state is request-only. |
| <span id="number-input-event-cnumber-input-events-on-input-value-change"></span>`onInputValueChange` | `(inputValue: string, detail: CNumberInputInputValueChangeDetail) => void` ([`CNumberInputInputValueChangeDetail`](#number-input-interface-cnumber-input-input-value-change-detail)) | A native input or completed IME composition changes the literal editor draft. | `{inputValue, previousInputValue, status, controlled, composing, sourceEvent}` ([`CNumberInputInputValueChangeDetail`](#number-input-interface-cnumber-input-input-value-change-detail)) | Reports the draft without committing or reformatting it; native input remains observable through input_attrs. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CNumberInput CSS variables

Apply these variables to `CNumberInput` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="number-input-css-cnumber-input-css-variables-background"></span>`--cui-number-input-background` | `color` | Control background. | `Canvas` |
| <span id="number-input-css-cnumber-input-css-variables-foreground"></span>`--cui-number-input-foreground` | `color` | Editor and icon foreground. | `CanvasText` |
| <span id="number-input-css-cnumber-input-css-variables-border-color"></span>`--cui-number-input-border-color` | `color` | Control and step-divider border. | `Mixed CanvasText.` |
| <span id="number-input-css-cnumber-input-css-variables-focus-color"></span>`--cui-number-input-focus-color` | `color` | Focus border and ring. | `Highlight` |
| <span id="number-input-css-cnumber-input-css-variables-invalid-border-color"></span>`--cui-number-input-invalid-border-color` | `color` | Invalid border. | `Theme error.` |
| <span id="number-input-css-cnumber-input-css-variables-radius"></span>`--cui-number-input-radius` | `length` | Control corner radius. | `0.5rem` |
| <span id="number-input-css-cnumber-input-css-variables-height"></span>`--cui-number-input-height` | `length` | Editor and Button height. | `2.5rem` |
| <span id="number-input-css-cnumber-input-css-variables-inline-padding"></span>`--cui-number-input-inline-padding` | `length` | Editor inline inset. | `0.75rem` |
| <span id="number-input-css-cnumber-input-css-variables-control-size"></span>`--cui-number-input-control-size` | `length` | Step Button inline size. | `2.5rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CNumberInput attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="number-input-attribute-cnumber-input-root-attributes-data-empty"></span>`data-empty` | Root div | `present | absent` | Mirrors an empty canonical value. |
| <span id="number-input-attribute-cnumber-input-root-attributes-data-required"></span>`data-required` | Root div | `present | absent` | Mirrors effective requiredness. |
| <span id="number-input-attribute-cnumber-input-root-attributes-data-disabled"></span>`data-disabled` | Root div | `present | absent` | Mirrors effective disabledness. |
| <span id="number-input-attribute-cnumber-input-root-attributes-data-readonly"></span>`data-readonly` | Root div | `present | absent` | Mirrors effective readonly state. |
| <span id="number-input-attribute-cnumber-input-root-attributes-data-invalid"></span>`data-invalid` | Root div | `present | absent` | Mirrors application or revealed component invalidity. |
| <span id="number-input-attribute-cnumber-input-root-attributes-data-variant"></span>`data-variant` | Root div | `CNumberInputVariant` ([`CNumberInputVariant`](#number-input-interface-variant)) | Mirrors visual treatment. |
| <span id="number-input-attribute-cnumber-input-root-attributes-data-size"></span>`data-size` | Root div | `CNumberInputSize` ([`CNumberInputSize`](#number-input-interface-size)) | Mirrors coordinated sizing. |

</div>

#### CNumberInput attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="number-input-attribute-cnumber-input-editor-attributes-role"></span>`role` | Editor input | `"spinbutton"` | Exposes numeric stepping semantics while preserving text editing. |
| <span id="number-input-attribute-cnumber-input-editor-attributes-inputmode"></span>`inputmode` | Editor input | `"decimal"` | Requests a decimal-capable virtual keyboard. |
| <span id="number-input-attribute-cnumber-input-editor-attributes-aria-valuenow"></span>`aria-valuenow` | Editor input | `canonical decimal | absent` | Exposes a valid committed canonical value. |
| <span id="number-input-attribute-cnumber-input-editor-attributes-aria-valuetext"></span>`aria-valuetext` | Editor input | `localized string | absent` | Exposes the locale-formatted committed value. |
| <span id="number-input-attribute-cnumber-input-editor-attributes-aria-valuemin"></span>`aria-valuemin` | Editor input | `canonical decimal | absent` | Exposes the inclusive minimum. |
| <span id="number-input-attribute-cnumber-input-editor-attributes-aria-valuemax"></span>`aria-valuemax` | Editor input | `canonical decimal | absent` | Exposes the inclusive maximum. |
| <span id="number-input-attribute-cnumber-input-editor-attributes-aria-invalid"></span>`aria-invalid` | Editor input | `"true" | absent` | Mirrors application or revealed native validity. |

</div>

#### CNumberInput attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="number-input-attribute-cnumber-input-control-attributes-button-type"></span>`type` | Step Buttons | `"button"` | Prevents accidental Form submission. |
| <span id="number-input-attribute-cnumber-input-control-attributes-button-tabindex"></span>`tabindex` | Step Buttons | `"-1"` | Keeps the editor as the sole sequential Tab stop. |
| <span id="number-input-attribute-cnumber-input-control-attributes-button-aria-label"></span>`aria-label` | Step Buttons | `localized string` | Names increment or decrement. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CNumberInput selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="number-input-selector-cnumber-input-selectors-number-input"></span>`[data-citry-ui-part="number-input"]` | Root div | State reflections and class_, style, and attrs destination. |
| <span id="number-input-selector-cnumber-input-selectors-control"></span>`[data-citry-ui-part="control"]` | Control div | Contains the editor and optional step Buttons. |
| <span id="number-input-selector-cnumber-input-selectors-input"></span>`[data-citry-ui-part="input"]` | Text input | Public focus target and input_attrs destination. |
| <span id="number-input-selector-cnumber-input-selectors-decrement"></span>`[data-citry-ui-part="decrement"]` | Button | Requests one exact decrement. |
| <span id="number-input-selector-cnumber-input-selectors-increment"></span>`[data-citry-ui-part="increment"]` | Button | Requests one exact increment. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="number-input-interface-exact"></span>`CNumberInputExact` | `int | Decimal | str` |
| <span id="number-input-interface-commit-behavior"></span>`CNumberInputCommitBehavior` | `Literal["validate", "clamp"]` |
| <span id="number-input-interface-variant"></span>`CNumberInputVariant` | `Literal["outline", "filled", "plain"]` |
| <span id="number-input-interface-size"></span>`CNumberInputSize` | `Literal["sm", "md", "lg"]` |
| <span id="number-input-interface-parse-status"></span>`CNumberInputParseStatus` | `Literal["empty", "incomplete", "invalid", "valid"]` |
| <span id="number-input-interface-change-source"></span>`CNumberInputChangeSource` | `Literal["blur", "enter", "increment", "decrement", "page", "home", "end", "wheel", "reset"]` |
| <span id="number-input-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="number-input-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="number-input-interface-cnumber-input-value-change-detail"></span>

#### `CNumberInputValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="number-input-interface-cnumber-input-value-change-detail-value"></span>`value` | `string | null` | - | Requested exact canonical value. |
| <span id="number-input-interface-cnumber-input-value-change-detail-previous-value"></span>`previousValue` | `string | null` | - | Effective canonical value before the request. |
| <span id="number-input-interface-cnumber-input-value-change-detail-input-value"></span>`inputValue` | `string` | - | Visible formatted text associated with the request. |
| <span id="number-input-interface-cnumber-input-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client value owns canonical state. |
| <span id="number-input-interface-cnumber-input-value-change-detail-source"></span>`source` | `CNumberInputChangeSource` ([`CNumberInputChangeSource`](#number-input-interface-change-source)) | - | Interaction or reset cause. |
| <span id="number-input-interface-cnumber-input-value-change-detail-source-event"></span>`sourceEvent` | `object | null` | - | Native interaction event when one exists. |

</div>

<span id="number-input-interface-cnumber-input-input-value-change-detail"></span>

#### `CNumberInputInputValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="number-input-interface-cnumber-input-input-value-change-detail-input-value"></span>`inputValue` | `string` | - | Current literal draft. |
| <span id="number-input-interface-cnumber-input-input-value-change-detail-previous-input-value"></span>`previousInputValue` | `string` | - | Literal draft before this native input. |
| <span id="number-input-interface-cnumber-input-input-value-change-detail-status"></span>`status` | `CNumberInputParseStatus` ([`CNumberInputParseStatus`](#number-input-interface-parse-status)) | - | Locale-aware parse state. |
| <span id="number-input-interface-cnumber-input-input-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client value owns canonical state. |
| <span id="number-input-interface-cnumber-input-input-value-change-detail-composing"></span>`composing` | `boolean` | - | Whether an input method composition remains active. |
| <span id="number-input-interface-cnumber-input-input-value-change-detail-source-event"></span>`sourceEvent` | `object | null` | - | Native input or composition event. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CNumberInput translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="number-input-translation-cnumber-input-translations-decrement"></span>`citry-ui-number-input-decrement` | Names the decrement Button. | `None` | `decrement_label` | $c-tr updates the stable aria-label. |
| <span id="number-input-translation-cnumber-input-translations-increment"></span>`citry-ui-number-input-increment` | Names the increment Button. | `None` | `increment_label` | $c-tr updates the stable aria-label. |
| <span id="number-input-translation-cnumber-input-translations-required"></span>`citry-ui-number-input-required` | Supplies empty required validity. | `None` | `required_message` | Active `i18n.bind()` custom-validity destination. |
| <span id="number-input-translation-cnumber-input-translations-invalid"></span>`citry-ui-number-input-invalid` | Supplies malformed or incomplete draft validity. | `None` | `invalid_message` | Active `i18n.bind()` custom-validity destination. |
| <span id="number-input-translation-cnumber-input-translations-minimum"></span>`citry-ui-number-input-minimum` | Supplies inclusive-minimum validity. | `min: str` | `minimum_message` | `i18n.bind()` with locale-formatted min. |
| <span id="number-input-translation-cnumber-input-translations-maximum"></span>`citry-ui-number-input-maximum` | Supplies inclusive-maximum validity. | `max: str` | `maximum_message` | `i18n.bind()` with locale-formatted max. |
| <span id="number-input-translation-cnumber-input-translations-step"></span>`citry-ui-number-input-step` | Supplies exact step-grid validity. | `step: str` | `step_message` | `i18n.bind()` with locale-formatted step. |

</div>