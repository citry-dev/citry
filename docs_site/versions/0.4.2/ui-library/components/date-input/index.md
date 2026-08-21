---
title: DateInput
url: https://citry.dev/v/0.4.2/ui-library/components/date-input/
description: "Collect one canonical calendar date with the browser's native date control."
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



### Collect one date

[Open the rendered preview](/v/0.4.2/ui-library/components/date-input/_previews/basic/)

````citry
from datetime import date
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CDateInput

citry.register_library(citry_ui)

# ruff: noqa: E501 - template and CSS lines stay readable in public source examples


class BasicDateInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"python_input": CDateInput(value=date(2026, 8, 19), attrs={"aria-label": "Python date"})}

    template = """
      <section class="date-input-demo-grid">
        <c-CField required>
          <c-fill name="label">Arrival date</c-fill>
          <c-fill name="description">Choose your check-in day.</c-fill>
          <c-fill name="default"><c-CDateInput name="arrival" /></c-fill>
        </c-CField>
        <article><h3>Python composition</h3>{{ python_input }}</article>
      </section>
    """
    css = ":where(.date-input-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1.25rem}"


preview = BasicDateInput()
preview  # noqa: B018
````


Python composition accepts an exact `datetime.date`; a `datetime`, localized
text, or noncanonical string is rejected.

## Set exact bounds

`min`, `max`, and positive integer `step` map directly to native date
constraints. The server must validate submitted values again.


### Constrain a native date

[Open the rendered preview](/v/0.4.2/ui-library/components/date-input/_previews/bounds/)

````citry
from citry import Component

# ruff: noqa: E501 - template lines stay readable in the public source example


class DateInputBounds(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CField required>
        <c-fill name="label">Alternating August date</c-fill>
        <c-fill name="description">Choose every second day from 1 through 31 August 2026.</c-fill>
        <c-fill name="default"><c-CDateInput name="day" value="2026-08-19" min="2026-08-01" max="2026-08-31" c-step="2" /></c-fill>
      </c-CField>
    """


preview = DateInputBounds()
preview  # noqa: B018
````


The component does not clamp or round. Browser constraint validity remains
observable through the native input.

## Use native Forms and reset

`name` contributes exactly one canonical value. Disabled inputs are omitted;
readonly inputs remain submitted. `CForm` and `CField` own their shared state.


### Submit and reset a date

[Open the rendered preview](/v/0.4.2/ui-library/components/date-input/_previews/form/)

````citry
from citry import Component

# ruff: noqa: E501 - template expression remains readable as authored HTML


class DateInputForm(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <form class="date-input-demo-stack" x-data="{result:'Submit or reset the Form'}" @submit.prevent="result=JSON.stringify(Array.from(new FormData($event.target).entries()))">
        <c-CField required>
          <c-fill name="label">Departure date</c-fill>
          <c-fill name="default"><c-CDateInput name="departure" value="2026-08-22" /></c-fill>
        </c-CField>
        <c-CGroup><c-CButton type="submit">Submit</c-CButton><c-CButton type="reset" variant="outline">Reset</c-CButton></c-CGroup>
        <output x-text="result">Submit or reset the Form</output>
      </form>
    """
    css = ":where(.date-input-demo-stack){display:grid;justify-items:start;gap:1rem}"


preview = DateInputForm()
preview  # noqa: B018
````


## Control a date in Alpine

Client `value` accepts a canonical string or `null`. Native `input` and
`change` events remain the observation surface; a supplied client value is
restored after event listeners run until its owner accepts another value.


### Control a date

[Open the rendered preview](/v/0.4.2/ui-library/components/date-input/_previews/controlled/)

````citry
from citry import Component

# ruff: noqa: E501 - Alpine expressions stay readable in the public source example


class ControlledDateInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="date-input-demo-stack" x-data="{day:'2026-08-19',last:'No native input yet'}">
        <c-CDateInput c-attrs="{'aria-label':'Controlled arrival date'}" value="2026-08-19" $c-props="{value:day}" @input="last=$event.currentTarget.value" />
        <c-CGroup><button type="button" @click="day='2026-08-22'">Set 22 August</button><button type="button" @click="day=null">Clear</button></c-CGroup>
        <output x-text="last">No native input yet</output>
      </section>
    """
    css = ":where(.date-input-demo-stack){display:grid;justify-items:start;gap:.75rem}"


preview = ControlledDateInput()
preview  # noqa: B018
````


Omitting client `value` releases control at the last accepted value.

## Hint birthday autofill

The ordinary native `autocomplete` input can request browser-managed birthday
autofill without changing the canonical value contract.


### Request birthday autofill

[Open the rendered preview](/v/0.4.2/ui-library/components/date-input/_previews/birthday/)

````citry
from citry import Component


class BirthdayDateInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CField>
        <c-fill name="label">Date of birth</c-fill>
        <c-fill name="description">Your browser may offer saved birthday information.</c-fill>
        <c-fill name="default"><c-CDateInput name="birthday" autocomplete="bday" max="2026-08-19" /></c-fill>
      </c-CField>
    """


preview = BirthdayDateInput()
preview  # noqa: B018
````


## Understand locale behavior

The DOM value and FormData stay `YYYY-MM-DD`; the browser chooses the visible
segment spelling and native picker UI. That UI may follow browser or platform
locale rather than the nearest Citry i18n provider.


### Compare native locale contexts

[Open the rendered preview](/v/0.4.2/ui-library/components/date-input/_previews/locales/)

````citry
from citry import Component

# ruff: noqa: E501 - localized template and CSS lines stay readable in the public source example


class DateInputLocales(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="date-input-demo-grid">
        <div lang="en"><label for="date-en">English context</label><c-CDateInput id="date-en" value="2026-08-19" /></div>
        <div lang="ar" dir="rtl"><label for="date-ar">سياق عربي</label><c-CDateInput id="date-ar" value="2026-08-19" /></div>
        <p>The submitted value is 2026-08-19 in both controls; visible native formatting remains browser-owned.</p>
      </section>
    """
    css = ":where(.date-input-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));gap:1rem}:where(.date-input-demo-grid>div){display:grid;gap:.5rem}"


preview = DateInputLocales()
preview  # noqa: B018
````


Use the custom Calendar/DatePicker family when the active Citry locale must
determine the exact calendar UI.

## Compare states and styles

Outline, filled, and plain variants combine with sm, md, and lg sizes. Public
variables customize the outer native control without hiding its picker
indicator or replacing its internal semantics.


### Compare DateInput states

[Open the rendered preview](/v/0.4.2/ui-library/components/date-input/_previews/states/)

````citry
from citry import Component

# ruff: noqa: E501 - template and CSS lines stay readable in the public source example


class DateInputStates(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="date-input-state-grid">
        <c-CDateInput c-attrs="{'aria-label':'Small outlined date'}" value="2026-08-19" size="sm" />
        <c-CDateInput c-attrs="{'aria-label':'Filled date'}" value="2026-08-20" variant="filled" />
        <c-CDateInput c-attrs="{'aria-label':'Large plain date'}" value="2026-08-21" size="lg" variant="plain" />
        <c-CDateInput c-attrs="{'aria-label':'Readonly date'}" value="2026-08-22" readonly />
        <c-CDateInput c-attrs="{'aria-label':'Disabled date'}" value="2026-08-23" disabled />
        <c-CDateInput c-attrs="{'aria-label':'Invalid date'}" value="2026-08-24" invalid />
      </section>
    """
    css = ":where(.date-input-state-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:1rem}"


preview = DateInputStates()
preview  # noqa: B018
````



### Customize DateInput

[Open the rendered preview](/v/0.4.2/ui-library/components/date-input/_previews/styling/)

````citry
from citry import Component


class StyledDateInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = (
        '<c-CDateInput c-attrs="{\'aria-label\':\'Brand date\'}" value="2026-08-19" class_="brand-date-input" />'
    )
    css = """
      :where(.brand-date-input){--cui-date-input-background:light-dark(#f0fdf4,#14261d);--cui-date-input-border-color:#16a34a;--cui-date-input-focus-color:#15803d;--cui-date-input-radius:1rem}
    """


preview = StyledDateInput()
preview  # noqa: B018
````


`CDateInput` owns no translation key: labels and errors belong to the
application, while native picker and validation prose belong to the browser.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CDateInput server inputs

Server inputs are passed in a template through `<c-CDateInput ... />` or in Python through
`CDateInput(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 17rem; --ui-api-column-3-width: 15rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="date-input-input-cdate-input-server-inputs-value"></span>`value` | `CDateInputValue | None` ([`CDateInputValue`](#date-input-interface-value)) | `None` | Sets the initial/reset exact date or empty value. |
| <span id="date-input-input-cdate-input-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the native Form field name. |
| <span id="date-input-input-cdate-input-server-inputs-form"></span>`form` | `str | None` | `None` | Associates the input with an external native Form ID. |
| <span id="date-input-input-cdate-input-server-inputs-id"></span>`id` | `str | None` | generated | Sets the public native input ID. |
| <span id="date-input-input-cdate-input-server-inputs-min"></span>`min` | `CDateInputValue | None` ([`CDateInputValue`](#date-input-interface-value)) | `None` | Sets the inclusive native minimum date. |
| <span id="date-input-input-cdate-input-server-inputs-max"></span>`max` | `CDateInputValue | None` ([`CDateInputValue`](#date-input-interface-value)) | `None` | Sets the inclusive native maximum date. |
| <span id="date-input-input-cdate-input-server-inputs-step"></span>`step` | `int` | `1` | Sets the exact positive native day step. |
| <span id="date-input-input-cdate-input-server-inputs-required"></span>`required` | `bool | None` | `None` | Enables native empty-value validity outside Field; Field owns it inside Field. |
| <span id="date-input-input-cdate-input-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Blocks interaction and Form participation outside Field; Form disabledness also wins. |
| <span id="date-input-input-cdate-input-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Keeps a focusable submitted value while blocking native edits. |
| <span id="date-input-input-cdate-input-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Adds application invalid state to revealed native validity. |
| <span id="date-input-input-cdate-input-server-inputs-autocomplete"></span>`autocomplete` | `str | None` | `None` | Sets a native autofill hint such as bday. |
| <span id="date-input-input-cdate-input-server-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CDateInputVariant`](#date-input-interface-variant)) | `"outline"` | Selects outer native-control treatment. |
| <span id="date-input-input-cdate-input-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CDateInputSize`](#date-input-interface-size)) | `"md"` | Selects coordinated sizing. |
| <span id="date-input-input-cdate-input-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#date-input-interface-class-value)) | `None` | Adds classes to the native root and merges with attrs. |
| <span id="date-input-input-cdate-input-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#date-input-interface-style-value)) | `None` | Adds styles to the native root and merges with attrs. |
| <span id="date-input-input-cdate-input-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed native attributes without replacing owned identity state constraints or runtime markers. |

</div>

#### CDateInput client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CDateInput />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 17rem; --ui-api-column-3-width: 18rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="date-input-input-cdate-input-client-inputs-value"></span>`value` | `canonical string | null` | Releases control at the latest accepted value. | Controls the exact native value while supplied. |
| <span id="date-input-input-cdate-input-client-inputs-min"></span>`min` | `canonical string | null` | Uses the server minimum. | Replaces or removes the inclusive minimum. |
| <span id="date-input-input-cdate-input-client-inputs-max"></span>`max` | `canonical string | null` | Uses the server maximum. | Replaces or removes the inclusive maximum. |
| <span id="date-input-input-cdate-input-client-inputs-step"></span>`step` | `positive integer` | Uses the server step. | Replaces the native day step. |
| <span id="date-input-input-cdate-input-client-inputs-required"></span>`required` | `boolean` | Uses server or Field state. | Controls standalone required validity. |
| <span id="date-input-input-cdate-input-client-inputs-disabled"></span>`disabled` | `boolean` | Uses server or owner state. | Controls interaction and Form participation. |
| <span id="date-input-input-cdate-input-client-inputs-readonly"></span>`readonly` | `boolean` | Uses server or owner state. | Controls focusable nonmutable state. |
| <span id="date-input-input-cdate-input-client-inputs-invalid"></span>`invalid` | `boolean` | Uses server or Field state. | Controls application invalid state. |
| <span id="date-input-input-cdate-input-client-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CDateInputVariant`](#date-input-interface-variant)) | Uses the server input. | Controls presentation. |
| <span id="date-input-input-cdate-input-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CDateInputSize`](#date-input-interface-size)) | Uses the server input. | Controls coordinated sizing. |

</div>

### Slots

-

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CDateInput CSS variables

Apply these variables to `CDateInput` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="date-input-css-cdate-input-css-variables-background"></span>`--cui-date-input-background` | `color` | Native control background. | `Canvas` |
| <span id="date-input-css-cdate-input-css-variables-foreground"></span>`--cui-date-input-foreground` | `color` | Native date text and indicator foreground. | `CanvasText` |
| <span id="date-input-css-cdate-input-css-variables-border-color"></span>`--cui-date-input-border-color` | `color` | Resting border. | `Mixed CanvasText.` |
| <span id="date-input-css-cdate-input-css-variables-hover-border-color"></span>`--cui-date-input-hover-border-color` | `color` | Hover border. | `Stronger mixed CanvasText.` |
| <span id="date-input-css-cdate-input-css-variables-focus-color"></span>`--cui-date-input-focus-color` | `color` | Focus border and outline. | `Highlight` |
| <span id="date-input-css-cdate-input-css-variables-invalid-border-color"></span>`--cui-date-input-invalid-border-color` | `color` | Invalid border. | `Theme error.` |
| <span id="date-input-css-cdate-input-css-variables-disabled-background"></span>`--cui-date-input-disabled-background` | `color` | Disabled background. | `Muted Canvas.` |
| <span id="date-input-css-cdate-input-css-variables-radius"></span>`--cui-date-input-radius` | `length` | Outer corner radius. | `0.5rem` |
| <span id="date-input-css-cdate-input-css-variables-height"></span>`--cui-date-input-height` | `length` | Minimum block size. | `2.5rem` |
| <span id="date-input-css-cdate-input-css-variables-inline-padding"></span>`--cui-date-input-inline-padding` | `length` | Logical inline inset. | `0.75rem` |
| <span id="date-input-css-cdate-input-css-variables-block-padding"></span>`--cui-date-input-block-padding` | `length` | Logical block inset. | `0.5rem` |
| <span id="date-input-css-cdate-input-css-variables-font-size"></span>`--cui-date-input-font-size` | `length` | Date text size. | `1rem` |
| <span id="date-input-css-cdate-input-css-variables-min-inline-size"></span>`--cui-date-input-min-inline-size` | `length` | Preferred minimum width before container clamping. | `10rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CDateInput attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="date-input-attribute-cdate-input-root-attributes-type"></span>`type` | Native root input | `"date"` | Selects browser-owned calendar-date editing and picker behavior. |
| <span id="date-input-attribute-cdate-input-root-attributes-value"></span>`value` | Native root input | `canonical date | absent` | Carries the initial/reset date. |
| <span id="date-input-attribute-cdate-input-root-attributes-min"></span>`min` | Native root input | `canonical date | absent` | Sets inclusive native minimum validity. |
| <span id="date-input-attribute-cdate-input-root-attributes-max"></span>`max` | Native root input | `canonical date | absent` | Sets inclusive native maximum validity. |
| <span id="date-input-attribute-cdate-input-root-attributes-step"></span>`step` | Native root input | `positive integer` | Sets the day step grid. |
| <span id="date-input-attribute-cdate-input-root-attributes-aria-invalid"></span>`aria-invalid` | Native root input | `"true" | absent` | Mirrors application or revealed native invalidity. |
| <span id="date-input-attribute-cdate-input-root-attributes-data-empty"></span>`data-empty` | Native root input | `present | absent` | Mirrors an empty canonical value. |
| <span id="date-input-attribute-cdate-input-root-attributes-data-required"></span>`data-required` | Native root input | `present | absent` | Mirrors effective requiredness. |
| <span id="date-input-attribute-cdate-input-root-attributes-data-disabled"></span>`data-disabled` | Native root input | `present | absent` | Mirrors effective disabledness. |
| <span id="date-input-attribute-cdate-input-root-attributes-data-readonly"></span>`data-readonly` | Native root input | `present | absent` | Mirrors effective readonly state. |
| <span id="date-input-attribute-cdate-input-root-attributes-data-invalid"></span>`data-invalid` | Native root input | `present | absent` | Mirrors application or revealed native invalidity. |
| <span id="date-input-attribute-cdate-input-root-attributes-data-variant"></span>`data-variant` | Native root input | `CDateInputVariant` ([`CDateInputVariant`](#date-input-interface-variant)) | Mirrors visual treatment. |
| <span id="date-input-attribute-cdate-input-root-attributes-data-size"></span>`data-size` | Native root input | `CDateInputSize` ([`CDateInputSize`](#date-input-interface-size)) | Mirrors coordinated sizing. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CDateInput selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="date-input-selector-cdate-input-selectors-date-input"></span>`[data-citry-ui-part="date-input"]` | Native root input | Stable styling state Form focus event and attrs destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="date-input-interface-value"></span>`CDateInputValue` | `date | str` |
| <span id="date-input-interface-variant"></span>`CDateInputVariant` | `Literal["outline", "filled", "plain"]` |
| <span id="date-input-interface-size"></span>`CDateInputSize` | `Literal["sm", "md", "lg"]` |
| <span id="date-input-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="date-input-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

### Translation keys

-