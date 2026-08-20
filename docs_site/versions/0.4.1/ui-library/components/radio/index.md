---
title: Radio
url: https://citry.dev/v/0.4.1/ui-library/components/radio/
description: "Select one visible option with native Citry UI Radio Groups and Radios."
---
# Radio

Use `CRadioGroup` and `CRadio` when people should see every option and select
exactly one. Native fieldset, legend, labels, keyboard behavior, validity,
reset, and FormData stay browser-owned.

## Radio at a glance


### Radio at a glance

[Open the rendered preview](/v/0.4.1/ui-library/components/radio/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RadioAtAGlance(Component):
    template = """
      <section class="radio-glance">
        <h2>Plan the garden path</h2>
        <p>Choose the habitat the path should pass through.</p>
        <c-CRadioGroup name="habitat" value="woodland" orientation="horizontal">
          <c-fill name="label">Habitat</c-fill>
          <c-fill name="default">
            <c-CRadio value="woodland">Woodland</c-CRadio>
            <c-CRadio value="meadow">Wildflower meadow</c-CRadio>
            <c-CRadio value="wetland">Wetland edge</c-CRadio>
          </c-fill>
        </c-CRadioGroup>
      </section>
    """
    css = """
      :where(.radio-glance) {
        display: grid;
        gap: 0.85rem;
        max-inline-size: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#a6b99b, #51664a);
        border-radius: 0.9rem;
        background: light-dark(#f4f8ef, #182219);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.radio-glance h2, .radio-glance p) {
        margin: 0;
      }

      :where(.radio-glance > p) {
        color: light-dark(#53634c, #b8c9b0);
        font-size: 0.82rem;
      }
    """


preview = RadioAtAGlance()

preview  # noqa: B018
````


## Compose a group

Give Group one shared `name`, a visible `label` slot, and Radios with unique
values. `CRadio` cannot be used outside Group.


### Compose a Radio Group

[Open the rendered preview](/v/0.4.1/ui-library/components/radio/_previews/basic/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicRadioGroup(Component):
    template = """
      <c-CRadioGroup name="watering" value="morning">
        <c-fill name="label">Watering time</c-fill>
        <c-fill name="default">
          <c-CRadio value="morning">Early morning</c-CRadio>
          <c-CRadio value="evening">Late evening</c-CRadio>
        </c-fill>
      </c-CRadioGroup>
    """


preview = BasicRadioGroup()

preview  # noqa: B018
````



```citry-html
<c-CRadioGroup name="habitat" value="woodland">
  <c-fill name="label">Habitat</c-fill>
  <c-fill name="default">
    <c-CRadio value="woodland">Woodland</c-CRadio>
    <c-CRadio value="wetland">Wetland</c-CRadio>
  </c-fill>
</c-CRadioGroup>
```


## Add descriptions and disabled choices

Descriptions connect to their native Radio. Disable one unavailable option
without disabling its siblings.


### Describe and disable Radio options

[Open the rendered preview](/v/0.4.1/ui-library/components/radio/_previews/descriptions/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DescribedRadios(Component):
    template = """
      <c-CRadioGroup name="soil" value="loam" class_="radio-described">
        <c-fill name="label">Soil blend</c-fill>
        <c-fill name="default">
          <c-CRadio value="loam">
            <c-fill name="default">Woodland loam</c-fill>
            <c-fill name="description">Balanced drainage for ferns and woodland flowers.</c-fill>
          </c-CRadio>
          <c-CRadio value="grit">
            <c-fill name="default">Alpine grit</c-fill>
            <c-fill name="description">Fast drainage for rock-garden plants.</c-fill>
          </c-CRadio>
          <c-CRadio value="peat" disabled>
            <c-fill name="default">Bog peat</c-fill>
            <c-fill name="description">Unavailable while the bog bed recovers.</c-fill>
          </c-CRadio>
        </c-fill>
      </c-CRadioGroup>
    """
    css = """
      :where(.radio-described) {
        max-inline-size: 34rem;
      }
    """


preview = DescribedRadios()

preview  # noqa: B018
````


## Control selection in the browser

Pass `value` through `$c-props="{...}"`. A known string controls one option;
`null` clears selection; omission releases control. Handle native `input` or
`change` with `$event.target.value`.


### Control a Radio Group

[Open the rendered preview](/v/0.4.1/ui-library/components/radio/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledRadios(Component):
    template = """
      <section class="radio-controlled" x-data="{value: 'moss'}">
        <c-CRadioGroup
          name="groundcover"
          $c-props="{value}"
          @input="value = $event.target.value"
          orientation="horizontal"
        >
          <c-fill name="label">Ground cover</c-fill>
          <c-fill name="default">
            <c-CRadio value="moss">Moss</c-CRadio>
            <c-CRadio value="thyme">Creeping thyme</c-CRadio>
            <c-CRadio value="clover">Microclover</c-CRadio>
          </c-fill>
        </c-CRadioGroup>
        <output x-text="`Selected: ${value}`"></output>
      </section>
    """
    css = """
      :where(.radio-controlled) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.radio-controlled output) {
        color: light-dark(#3f6212, #bef264);
        font-size: 0.8rem;
      }
    """


preview = ControlledRadios()

preview  # noqa: B018
````


## Use native forms and validation

The checked enabled Radio contributes one shared name/value entry. Required
groups use native validation and reset.


### Submit and validate Radio values

[Open the rendered preview](/v/0.4.1/ui-library/components/radio/_previews/forms/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RadioForm(Component):
    template = """
      <form
        class="radio-form"
        x-data="{result: ''}"
        @submit.prevent="result = new FormData($event.target).get('plot') || 'Choose a plot'"
      >
        <c-CRadioGroup name="plot" required>
          <c-fill name="label">Planting plot</c-fill>
          <c-fill name="default">
            <c-CRadio value="north">North wall</c-CRadio>
            <c-CRadio value="orchard">Old orchard</c-CRadio>
            <c-CRadio value="pond">Pond margin</c-CRadio>
          </c-fill>
        </c-CRadioGroup>
        <c-CGroup><c-CButton type="submit">Reserve plot</c-CButton><button type="reset">Reset</button></c-CGroup>
        <output x-text="result"></output>
      </form>
    """
    css = """
      :where(.radio-form) {
        display: grid;
        gap: 1rem;
        max-inline-size: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = RadioForm()

preview  # noqa: B018
````


## Choose orientation

Vertical is easiest to scan. Horizontal groups wrap and keep native keyboard
behavior.


### Compare Radio orientations

[Open the rendered preview](/v/0.4.1/ui-library/components/radio/_previews/orientation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RadioOrientation(Component):
    template = """
      <c-CStack gap="xl">
        <c-CRadioGroup name="season-vertical" value="spring">
          <c-fill name="label">Vertical</c-fill>
          <c-fill name="default">
            <c-CRadio value="spring">Spring</c-CRadio>
            <c-CRadio value="autumn">Autumn</c-CRadio>
          </c-fill>
        </c-CRadioGroup>
        <c-CRadioGroup name="season-horizontal" value="spring" orientation="horizontal">
          <c-fill name="label">Horizontal</c-fill>
          <c-fill name="default">
            <c-CRadio value="spring">Spring</c-CRadio>
            <c-CRadio value="autumn">Autumn</c-CRadio>
          </c-fill>
        </c-CRadioGroup>
      </c-CStack>
    """


preview = RadioOrientation()

preview  # noqa: B018
````


## Choose presentation

Compare solid and outline treatments, three sizes, and logical label placement.


### Compare Radio presentation

[Open the rendered preview](/v/0.4.1/ui-library/components/radio/_previews/presentation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RadioPresentation(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CStack gap="xl">
        <c-for each="variant in variants">
          <c-CRadioGroup c-name="f'variant-{variant}'" value="one" c-variant="variant" orientation="horizontal">
            <c-fill name="label">{{ variant }}</c-fill>
            <c-fill name="default"><c-CRadio value="one">One</c-CRadio><c-CRadio value="two">Two</c-CRadio></c-fill>
          </c-CRadioGroup>
        </c-for>
        <c-for each="size in sizes">
          <c-CRadioGroup c-name="f'size-{size}'" value="leaf" c-size="size" label_pos="start" orientation="horizontal">
            <c-fill name="label">{{ size }}, labels first</c-fill>
            <c-fill name="default">
              <c-CRadio value="leaf">Leaf</c-CRadio>
              <c-CRadio value="flower">Flower</c-CRadio>
            </c-fill>
          </c-CRadioGroup>
        </c-for>
      </c-CStack>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"variants": ("solid", "outline"), "sizes": ("sm", "md", "lg")}


preview = RadioPresentation()

preview  # noqa: B018
````


## Compose with Field

Inside `CField`, Field owns label, description, error, required, disabled, and
invalid state. Do not add the Group `label` slot there.


### Compose Radio with Field

[Open the rendered preview](/v/0.4.1/ui-library/components/radio/_previews/field/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RadioField(Component):
    template = """
      <c-CField control_id="shade-choice" required>
        <c-fill name="label">Preferred shade</c-fill>
        <c-fill name="default">
          <c-CRadioGroup name="shade" orientation="horizontal">
            <c-CRadio value="sun">Full sun</c-CRadio>
            <c-CRadio value="partial">Partial shade</c-CRadio>
            <c-CRadio value="deep">Deep shade</c-CRadio>
          </c-CRadioGroup>
        </c-fill>
        <c-fill name="description">Choose the light available in this bed.</c-fill>
        <c-fill name="error">Choose one shade level.</c-fill>
      </c-CField>
    """


preview = RadioField()

preview  # noqa: B018
````


## Customize Radio

Override public group, control, color, focus, spacing, and disabled variables.
Stable part selectors target the fieldset, legend, item, input, label, and
description.


### Customize Radio with public CSS

[Open the rendered preview](/v/0.4.1/ui-library/components/radio/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RadioCustomization(Component):
    template = """
      <div class="radio-custom">
        <c-CRadioGroup name="collection" value="fern" orientation="horizontal">
          <c-fill name="label">Plant collection</c-fill>
          <c-fill name="default">
            <c-CRadio value="fern">Fern house</c-CRadio>
            <c-CRadio value="alpine">Alpine house</c-CRadio>
            <c-CRadio value="orchid">Orchid house</c-CRadio>
          </c-fill>
        </c-CRadioGroup>
      </div>
    """
    css = """
      :where(.radio-custom) {
        --cui-radio-active-color: light-dark(#7c3f00, #fbbf24);
        --cui-radio-border-color: light-dark(#a16207, #fde68a);
        --cui-radio-background: light-dark(#fffbeb, #2d2108);
        --cui-radio-control-size: 1.35rem;
        --cui-radio-group-gap: 1.25rem;
        padding: 1.25rem;
        border-radius: 0.8rem;
        background: light-dark(#f7f2df, #211d10);
      }
    """


preview = RadioCustomization()

preview  # noqa: B018
````


## Choose the right control

Use Native Select when choices should collapse, Checkbox for independent
choices, and Switch for an immediate Boolean setting. Radio Card and Segmented
Control are separate interaction and anatomy families.

## API reference

### Inputs

#### CRadioGroup server inputs

Server inputs are passed in a template through `<c-CRadioGroup ... />` or in Python through
`CRadioGroup(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 16rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="radio-input-cradio-group-server-inputs-name"></span>`name` | `str` | required | Sets the required shared native radio-group and FormData name. |
| <span id="radio-input-cradio-group-server-inputs-value"></span>`value` | `str | None` | `None` | Sets initial checked value; it must match one Radio value; None leaves the group unselected. |
| <span id="radio-input-cradio-group-server-inputs-form"></span>`form` | `str | None` | `None` | Associates every Radio with an external native Form ID. |
| <span id="radio-input-cradio-group-server-inputs-required"></span>`required` | `bool | None` | `None` | Enables native same-name group validation; CField owns it when composed. |
| <span id="radio-input-cradio-group-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Disables the native fieldset; CField and CForm remain dominant. |
| <span id="radio-input-cradio-group-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Sets explicit invalid styling and ARIA; CField owns it when composed. |
| <span id="radio-input-cradio-group-server-inputs-orientation"></span>`orientation` | `"vertical" | "horizontal"` ([`CRadioOrientation`](#radio-interface-orientation)) | `"vertical"` | Selects stacked or wrapping inline layout without replacing native keyboard behavior. |
| <span id="radio-input-cradio-group-server-inputs-variant"></span>`variant` | `"solid" | "outline"` ([`CRadioVariant`](#radio-interface-variant)) | `"solid"` | Selects checked-control treatment. |
| <span id="radio-input-cradio-group-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CRadioSize`](#radio-interface-size)) | `"md"` | Sets control and text scale. |
| <span id="radio-input-cradio-group-server-inputs-label-pos"></span>`label_pos` | `"start" | "end"` ([`CRadioLabelPos`](#radio-interface-label-pos)) | `"end"` | Places item labels before or after controls. |
| <span id="radio-input-cradio-group-server-inputs-id"></span>`id` | `str | None` | `None` | Sets the fieldset ID. |
| <span id="radio-input-cradio-group-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#radio-interface-class-value)) | `None` | Adds fieldset classes and merges them with `attrs`. |
| <span id="radio-input-cradio-group-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#radio-interface-style-value)) | `None` | Adds fieldset inline styles and merges them with `attrs`. |
| <span id="radio-input-cradio-group-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted nonconflicting metadata and targeted Alpine attributes to the fieldset. |

</div>

#### CRadioGroup client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CRadioGroup />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 16rem; --ui-api-column-3-width: 7rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="radio-input-cradio-group-client-inputs-value"></span>`value` | `string | null` | Releases control to native selection. | Controls one known value or no selection; omission releases control. |
| <span id="radio-input-cradio-group-client-inputs-required"></span>`required` | `boolean` | Uses the server or Field fallback. | Controls native required state outside Field. |
| <span id="radio-input-cradio-group-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server or Field/Form fallback. | Controls local disabled state outside Field; Form disabled stays dominant. |
| <span id="radio-input-cradio-group-client-inputs-invalid"></span>`invalid` | `boolean` | Uses the server or Field fallback. | Controls explicit invalid state outside Field. |
| <span id="radio-input-cradio-group-client-inputs-orientation"></span>`orientation` | `"vertical" | "horizontal"` | Uses the server fallback. | Controls the public layout reflection. |
| <span id="radio-input-cradio-group-client-inputs-variant"></span>`variant` | `"solid" | "outline"` | Uses the server fallback. | Controls checked-control treatment. |
| <span id="radio-input-cradio-group-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` | Uses the server fallback. | Controls public size. |
| <span id="radio-input-cradio-group-client-inputs-label-pos"></span>`label_pos` | `"start" | "end"` | Uses the server fallback. | Controls label placement. |

</div>

#### CRadio server inputs

Server inputs are passed in a template through `<c-CRadio ... />` or in Python through
`CRadio(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 16rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="radio-input-cradio-server-inputs-value"></span>`value` | `str` | required | Sets unique canonical option and submitted value. |
| <span id="radio-input-cradio-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables this native Radio without disabling siblings. |
| <span id="radio-input-cradio-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#radio-interface-class-value)) | `None` | Adds item wrapper classes and merges them with `attrs`. |
| <span id="radio-input-cradio-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#radio-interface-style-value)) | `None` | Adds item wrapper inline styles and merges them with `attrs`. |
| <span id="radio-input-cradio-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted nonconflicting attributes to the item wrapper. |
| <span id="radio-input-cradio-server-inputs-input-attrs"></span>`input_attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted nonconflicting native metadata and event listeners to the Radio input. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CRadioGroup slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="radio-slot-cradio-group-slots-label"></span>`label` | no | `{}` ([`CRadioGroupLabelSlotData`](#radio-interface-group-label)) | Missing standalone label raises; the slot is forbidden under CField. |
| <span id="radio-slot-cradio-group-slots-default"></span>`default` | yes | `{}` ([`CRadioGroupDefaultSlotData`](#radio-interface-group-default)) | Missing fill raises before rendering. |

</div>

#### CRadio slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="radio-slot-cradio-slots-default"></span>`default` | yes | `{}` ([`CRadioDefaultSlotData`](#radio-interface-radio-default)) | Missing visible label raises before rendering. |
| <span id="radio-slot-cradio-slots-description"></span>`description` | no | `{}` ([`CRadioDescriptionSlotData`](#radio-interface-radio-description)) | Description wrapper and relationship are omitted. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CRadioGroup CSS variables

Apply these variables to `CRadioGroup` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="radio-css-cradio-css-variables-cui-radio-group-gap"></span>`--cui-radio-group-gap` | `length` | Spacing between items. | `0.75rem.` |
| <span id="radio-css-cradio-css-variables-cui-radio-active-color"></span>`--cui-radio-active-color` | `color` | Checked border/fill/dot. | `Scheme-aware primary.` |
| <span id="radio-css-cradio-css-variables-cui-radio-border-color"></span>`--cui-radio-border-color` | `color` | Unchecked border. | `Scheme-aware neutral.` |
| <span id="radio-css-cradio-css-variables-cui-radio-background"></span>`--cui-radio-background` | `color` | Native control background. | `Canvas.` |
| <span id="radio-css-cradio-css-variables-cui-radio-foreground"></span>`--cui-radio-foreground` | `color` | Labels and inherited text. | `CanvasText.` |
| <span id="radio-css-cradio-css-variables-cui-radio-focus-color"></span>`--cui-radio-focus-color` | `color` | Keyboard focus ring. | `Highlight.` |
| <span id="radio-css-cradio-css-variables-cui-radio-invalid-color"></span>`--cui-radio-invalid-color` | `color` | Invalid control border. | `Scheme-aware danger.` |
| <span id="radio-css-cradio-css-variables-cui-radio-control-size"></span>`--cui-radio-control-size` | `length` | Radio control box. | `Size-derived length.` |
| <span id="radio-css-cradio-css-variables-cui-radio-item-gap"></span>`--cui-radio-item-gap` | `length` | Control-to-body spacing. | `0.55rem.` |
| <span id="radio-css-cradio-css-variables-cui-radio-label-gap"></span>`--cui-radio-label-gap` | `length` | Label-to-description spacing. | `0.2rem.` |
| <span id="radio-css-cradio-css-variables-cui-radio-disabled-opacity"></span>`--cui-radio-disabled-opacity` | `number` | Disabled item opacity. | `0.52.` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CRadioGroup attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="radio-attribute-cradio-group-attributes-disabled"></span>`disabled` | Fieldset | `boolean present or absent` | Native group disabled state. |
| <span id="radio-attribute-cradio-group-attributes-aria-invalid"></span>`aria-invalid` | Fieldset | `"true" or absent` | Effective explicit or native invalid state. |
| <span id="radio-attribute-cradio-group-attributes-data-value"></span>`data-value` | Fieldset | `canonical string or absent` | Current checked option value. |
| <span id="radio-attribute-cradio-group-attributes-data-required"></span>`data-required` | Fieldset | `boolean present or absent` | Effective native-required request. |
| <span id="radio-attribute-cradio-group-attributes-data-disabled"></span>`data-disabled` | Fieldset | `boolean present or absent` | Effective group disabled state. |
| <span id="radio-attribute-cradio-group-attributes-data-invalid"></span>`data-invalid` | Fieldset | `boolean present or absent` | Effective invalid state. |
| <span id="radio-attribute-cradio-group-attributes-data-orientation"></span>`data-orientation` | Fieldset | `"vertical" | "horizontal"` | Effective layout. |
| <span id="radio-attribute-cradio-group-attributes-data-variant"></span>`data-variant` | Fieldset | `"solid" | "outline"` | Effective selected-control treatment. |
| <span id="radio-attribute-cradio-group-attributes-data-size"></span>`data-size` | Fieldset | `"sm" | "md" | "lg"` | Effective size. |
| <span id="radio-attribute-cradio-group-attributes-data-label-pos"></span>`data-label-pos` | Fieldset | `"start" | "end"` | Effective label placement. |

</div>

#### CRadio attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="radio-attribute-cradio-attributes-checked"></span>`checked` | Native input | `boolean present or absent` | Server default checkedness; current checkedness is the native property. |
| <span id="radio-attribute-cradio-attributes-disabled"></span>`disabled` | Native input | `boolean present or absent` | Item-local disabledness. |
| <span id="radio-attribute-cradio-attributes-name"></span>`name` | Native input | `nonempty string` | Shared Group name. |
| <span id="radio-attribute-cradio-attributes-value"></span>`value` | Native input | `canonical string` | Unique option/FormData value. |
| <span id="radio-attribute-cradio-attributes-data-checked"></span>`data-checked` | Item wrapper | `boolean present or absent` | Mirrors current native checkedness for styling. |
| <span id="radio-attribute-cradio-attributes-data-disabled"></span>`data-disabled` | Item wrapper | `boolean present or absent` | Mirrors effective native disabledness. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CRadioGroup selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="radio-selector-radio-selectors-radio-group"></span>`[data-citry-ui-part="radio-group"]` | Native fieldset | Group root and attrs destination. |
| <span id="radio-selector-radio-selectors-legend"></span>`[data-citry-ui-part="legend"]` | Native legend | Standalone group label. |
| <span id="radio-selector-radio-selectors-radio"></span>`[data-citry-ui-part="radio"]` | Item wrapper | Radio attrs destination. |
| <span id="radio-selector-radio-selectors-input"></span>`[data-citry-ui-part="input"]` | Native radio input | Input attrs destination. |
| <span id="radio-selector-radio-selectors-body"></span>`[data-citry-ui-part="body"]` | Item text wrapper | Label and description layout. |
| <span id="radio-selector-radio-selectors-label"></span>`[data-citry-ui-part="label"]` | Native label | Visible option name and activation target. |
| <span id="radio-selector-radio-selectors-description"></span>`[data-citry-ui-part="description"]` | Description span | Optional item guidance. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="radio-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="radio-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="radio-interface-orientation"></span>`CRadioOrientation` | `Literal["vertical", "horizontal"]` |
| <span id="radio-interface-variant"></span>`CRadioVariant` | `Literal["solid", "outline"]` |
| <span id="radio-interface-size"></span>`CRadioSize` | `Literal["sm", "md", "lg"]` |
| <span id="radio-interface-label-pos"></span>`CRadioLabelPos` | `Literal["start", "end"]` |

</div>

<span id="radio-interface-group-default"></span>

#### `CRadioGroupDefaultSlotData`

Empty dataclass: `{}`.

<span id="radio-interface-group-label"></span>

#### `CRadioGroupLabelSlotData`

Empty dataclass: `{}`.

<span id="radio-interface-radio-default"></span>

#### `CRadioDefaultSlotData`

Empty dataclass: `{}`.

<span id="radio-interface-radio-description"></span>

#### `CRadioDescriptionSlotData`

Empty dataclass: `{}`.

### Translation keys

-