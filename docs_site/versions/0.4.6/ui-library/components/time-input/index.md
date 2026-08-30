---
title: TimeInput
url: https://citry.dev/v/0.4.6/ui-library/components/time-input/
description: "Collect one canonical wall-clock time with the browser's native time control."
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



### Collect one time

[Open the rendered preview](/v/0.4.6/ui-library/components/time-input/_previews/basic/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicTimeInput(Component):
    template = """
      <c-CField required>
        <c-fill name="label">Start time</c-fill>
        <c-fill name="description">Choose when the session starts.</c-fill>
        <c-fill name="default"><c-CTimeInput name="start" /></c-fill>
      </c-CField>
    """


preview = BasicTimeInput()
preview  # noqa: B018
````


Python composition accepts an exact zone-free `datetime.time`. Localized text,
offset-aware times, fractional seconds, and noncanonical strings are rejected.

## Constrain a periodic time range

`min`, `max`, and positive integer `step` map to native time constraints. A
minimum later than the maximum deliberately expresses a wrapped interval such
as 23:00 through 02:00.


### Constrain a native time

[Open the rendered preview](/v/0.4.6/ui-library/components/time-input/_previews/constraints/)

````citry
import citry_ui
from citry import Component, citry

# ruff: noqa: E501 - embedded Citry templates remain readable

citry.register_library(citry_ui)


class TimeInputConstraints(Component):
    template = """
      <section style="display:grid;gap:1rem;max-width:22rem">
        <label>Office appointment <c-CTimeInput name="office" min="09:00" max="17:00" c-step="900" value="09:30" /></label>
        <label>Overnight window <c-CTimeInput name="overnight" min="23:00" max="02:00" value="23:30" /></label>
      </section>
    """


preview = TimeInputConstraints()
preview  # noqa: B018
````


The server must validate submitted values again; the component never silently
clamps or rounds.

## Use Forms and client control

`name` contributes exactly one canonical value. Disabled inputs are omitted;
readonly inputs remain submitted. Client `value` accepts a canonical string or
`null`, and omission releases control at the latest accepted value.


### Submit and reset a time

[Open the rendered preview](/v/0.4.6/ui-library/components/time-input/_previews/form/)

````citry
import citry_ui
from citry import Component, citry

# ruff: noqa: E501 - embedded Citry templates remain readable

citry.register_library(citry_ui)


class TimeInputForm(Component):
    template = """
      <form x-data="{result:'Submit to inspect FormData'}" @submit.prevent="result=JSON.stringify(Object.fromEntries(new FormData($event.target)))">
        <c-CField required>
          <c-fill name="label">Delivery time</c-fill>
          <c-fill name="default"><c-CTimeInput name="delivery" value="14:30" /></c-fill>
        </c-CField>
        <c-CButton type="submit">Submit</c-CButton>
        <c-CButton type="reset" variant="outline">Reset</c-CButton>
        <output x-text="result">Submit to inspect FormData</output>
      </form>
    """


preview = TimeInputForm()
preview  # noqa: B018
````


## Understand locale behavior

The DOM value and FormData stay `HH:MM` or `HH:MM:SS`; the browser chooses the
visible segment order, hour cycle, picker, and native validation prose. Use
`CTimePicker` when Citry i18n must own the visible choice labels.

## Compare states and styles

Outline, filled, and plain variants combine with sm, md, and lg sizes. Public
variables style the native control without replacing its semantics.


### Compare TimeInput states

[Open the rendered preview](/v/0.4.6/ui-library/components/time-input/_previews/states/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimeInputStates(Component):
    template = """
      <section style="display:grid;grid-template-columns:repeat(auto-fit,minmax(12rem,1fr));gap:1rem">
        <label>Outline <c-CTimeInput value="09:00" /></label>
        <label>Filled <c-CTimeInput value="10:15" variant="filled" size="sm" /></label>
        <label>Plain readonly <c-CTimeInput value="11:30" variant="plain" size="lg" readonly /></label>
        <label>Invalid <c-CTimeInput value="12:45" invalid /></label>
        <label>Disabled <c-CTimeInput value="13:00" disabled /></label>
      </section>
    """


preview = TimeInputStates()
preview  # noqa: B018
````


`CTimeInput` owns no translation keys. Labels and errors belong to the
application; the platform owns the native editor and its prose.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CTimeInput server inputs

Server inputs are passed in a template through `<c-CTimeInput ... />` or in Python through
`CTimeInput(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 17rem; --ui-api-column-3-width: 15rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="time-input-input-ctime-input-server-inputs-value"></span>`value` | `CTimeInputValue | None` ([`CTimeInputValue`](#time-input-interface-value)) | `None` | Sets the initial and reset canonical time or empty value. |
| <span id="time-input-input-ctime-input-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the native Form field name. |
| <span id="time-input-input-ctime-input-server-inputs-form"></span>`form` | `str | None` | `None` | Associates the input with an external native Form ID. |
| <span id="time-input-input-ctime-input-server-inputs-id"></span>`id` | `str | None` | generated | Sets the public native input ID. |
| <span id="time-input-input-ctime-input-server-inputs-min"></span>`min` | `CTimeInputValue | None` ([`CTimeInputValue`](#time-input-interface-value)) | `None` | Sets the inclusive native minimum and may start a wrapped range. |
| <span id="time-input-input-ctime-input-server-inputs-max"></span>`max` | `CTimeInputValue | None` ([`CTimeInputValue`](#time-input-interface-value)) | `None` | Sets the inclusive native maximum and may end a wrapped range. |
| <span id="time-input-input-ctime-input-server-inputs-step"></span>`step` | `int` | `60` | Sets the exact positive native step in seconds. |
| <span id="time-input-input-ctime-input-server-inputs-required"></span>`required` | `bool | None` | `None` | Enables native empty-value validity outside Field; Field owns it inside Field. |
| <span id="time-input-input-ctime-input-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Blocks interaction and Form participation outside Field; Form disabledness also wins. |
| <span id="time-input-input-ctime-input-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Keeps a focusable submitted value while blocking native edits. |
| <span id="time-input-input-ctime-input-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Adds application invalid state to revealed native validity. |
| <span id="time-input-input-ctime-input-server-inputs-autocomplete"></span>`autocomplete` | `str | None` | `None` | Sets a native autofill hint. |
| <span id="time-input-input-ctime-input-server-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CTimeInputVariant`](#time-input-interface-variant)) | `"outline"` | Selects outer native-control treatment. |
| <span id="time-input-input-ctime-input-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CTimeInputSize`](#time-input-interface-size)) | `"md"` | Selects coordinated sizing. |
| <span id="time-input-input-ctime-input-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#time-input-interface-class-value)) | `None` | Adds classes to the native root and merges with attrs. |
| <span id="time-input-input-ctime-input-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#time-input-interface-style-value)) | `None` | Adds styles to the native root and merges with attrs. |
| <span id="time-input-input-ctime-input-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed native attributes without replacing owned identity state constraints or runtime markers. |

</div>

#### CTimeInput client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CTimeInput />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 17rem; --ui-api-column-3-width: 18rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="time-input-input-ctime-input-client-inputs-value"></span>`value` | `canonical string | null` | Releases control at the latest accepted value. | Controls the exact native value while supplied. |
| <span id="time-input-input-ctime-input-client-inputs-min"></span>`min` | `canonical string | null` | Uses the server minimum. | Replaces or removes the inclusive minimum. |
| <span id="time-input-input-ctime-input-client-inputs-max"></span>`max` | `canonical string | null` | Uses the server maximum. | Replaces or removes the inclusive maximum. |
| <span id="time-input-input-ctime-input-client-inputs-step"></span>`step` | `positive integer` | Uses the server step. | Replaces the native seconds step. |
| <span id="time-input-input-ctime-input-client-inputs-required"></span>`required` | `boolean` | Uses server or Field state. | Controls standalone required validity. |
| <span id="time-input-input-ctime-input-client-inputs-disabled"></span>`disabled` | `boolean` | Uses server or owner state. | Controls interaction and Form participation. |
| <span id="time-input-input-ctime-input-client-inputs-readonly"></span>`readonly` | `boolean` | Uses server or owner state. | Controls focusable nonmutable state. |
| <span id="time-input-input-ctime-input-client-inputs-invalid"></span>`invalid` | `boolean` | Uses server or Field state. | Controls application invalid state. |
| <span id="time-input-input-ctime-input-client-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CTimeInputVariant`](#time-input-interface-variant)) | Uses the server input. | Controls presentation. |
| <span id="time-input-input-ctime-input-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CTimeInputSize`](#time-input-interface-size)) | Uses the server input. | Controls coordinated sizing. |

</div>

### Slots

-

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CTimeInput CSS variables

Apply these variables to `CTimeInput` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="time-input-css-ctime-input-css-variables-background"></span>`--cui-time-input-background` | `color` | Native control background. | `Canvas` |
| <span id="time-input-css-ctime-input-css-variables-foreground"></span>`--cui-time-input-foreground` | `color` | Native time text and indicator foreground. | `CanvasText` |
| <span id="time-input-css-ctime-input-css-variables-border-color"></span>`--cui-time-input-border-color` | `color` | Resting border. | `Mixed CanvasText.` |
| <span id="time-input-css-ctime-input-css-variables-hover-border-color"></span>`--cui-time-input-hover-border-color` | `color` | Hover border. | `Stronger mixed CanvasText.` |
| <span id="time-input-css-ctime-input-css-variables-focus-color"></span>`--cui-time-input-focus-color` | `color` | Focus border and outline. | `Highlight` |
| <span id="time-input-css-ctime-input-css-variables-invalid-border-color"></span>`--cui-time-input-invalid-border-color` | `color` | Invalid border. | `Theme error.` |
| <span id="time-input-css-ctime-input-css-variables-disabled-background"></span>`--cui-time-input-disabled-background` | `color` | Disabled background. | `Muted Canvas.` |
| <span id="time-input-css-ctime-input-css-variables-radius"></span>`--cui-time-input-radius` | `length` | Outer corner radius. | `0.5rem` |
| <span id="time-input-css-ctime-input-css-variables-height"></span>`--cui-time-input-height` | `length` | Minimum block size. | `2.5rem` |
| <span id="time-input-css-ctime-input-css-variables-inline-padding"></span>`--cui-time-input-inline-padding` | `length` | Logical inline inset. | `0.75rem` |
| <span id="time-input-css-ctime-input-css-variables-block-padding"></span>`--cui-time-input-block-padding` | `length` | Logical block inset. | `0.5rem` |
| <span id="time-input-css-ctime-input-css-variables-font-size"></span>`--cui-time-input-font-size` | `length` | Time text size. | `1rem` |
| <span id="time-input-css-ctime-input-css-variables-min-inline-size"></span>`--cui-time-input-min-inline-size` | `length` | Preferred minimum width before container clamping. | `10rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CTimeInput attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="time-input-attribute-ctime-input-root-attributes-type"></span>`type` | Native root input | `"time"` | Selects browser-owned wall-clock editing and picker behavior. |
| <span id="time-input-attribute-ctime-input-root-attributes-value"></span>`value` | Native root input | `canonical time | absent` | Carries the initial and reset time. |
| <span id="time-input-attribute-ctime-input-root-attributes-min"></span>`min` | Native root input | `canonical time | absent` | Sets inclusive native minimum validity. |
| <span id="time-input-attribute-ctime-input-root-attributes-max"></span>`max` | Native root input | `canonical time | absent` | Sets inclusive native maximum validity. |
| <span id="time-input-attribute-ctime-input-root-attributes-step"></span>`step` | Native root input | `positive integer` | Sets the seconds step grid. |
| <span id="time-input-attribute-ctime-input-root-attributes-aria-invalid"></span>`aria-invalid` | Native root input | `"true" | absent` | Mirrors application or revealed native invalidity. |
| <span id="time-input-attribute-ctime-input-root-attributes-data-empty"></span>`data-empty` | Native root input | `present | absent` | Mirrors an empty canonical value. |
| <span id="time-input-attribute-ctime-input-root-attributes-data-required"></span>`data-required` | Native root input | `present | absent` | Mirrors effective requiredness. |
| <span id="time-input-attribute-ctime-input-root-attributes-data-disabled"></span>`data-disabled` | Native root input | `present | absent` | Mirrors effective disabledness. |
| <span id="time-input-attribute-ctime-input-root-attributes-data-readonly"></span>`data-readonly` | Native root input | `present | absent` | Mirrors effective readonly state. |
| <span id="time-input-attribute-ctime-input-root-attributes-data-invalid"></span>`data-invalid` | Native root input | `present | absent` | Mirrors application or revealed native invalidity. |
| <span id="time-input-attribute-ctime-input-root-attributes-data-variant"></span>`data-variant` | Native root input | `CTimeInputVariant` ([`CTimeInputVariant`](#time-input-interface-variant)) | Mirrors visual treatment. |
| <span id="time-input-attribute-ctime-input-root-attributes-data-size"></span>`data-size` | Native root input | `CTimeInputSize` ([`CTimeInputSize`](#time-input-interface-size)) | Mirrors coordinated sizing. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CTimeInput selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="time-input-selector-ctime-input-selectors-time-input"></span>`[data-citry-ui-part="time-input"]` | Native root input | Stable styling state Form focus event and attrs destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="time-input-interface-value"></span>`CTimeInputValue` | `time | str` |
| <span id="time-input-interface-variant"></span>`CTimeInputVariant` | `Literal["outline", "filled", "plain"]` |
| <span id="time-input-interface-size"></span>`CTimeInputSize` | `Literal["sm", "md", "lg"]` |
| <span id="time-input-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="time-input-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

### Translation keys

-