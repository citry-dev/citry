---
title: Switch
url: https://citry.dev/v/0.4.2/ui-library/components/switch/
description: "Change an immediate on or off setting with a native Citry UI Switch."
---
# Switch

Use `CSwitch` for a setting that takes effect immediately. Use Checkbox for a
selection or acknowledgement, and Button for an action.

## Switch at a glance


### Switch at a glance

[Open the rendered preview](/v/0.4.2/ui-library/components/switch/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SwitchAtAGlance(Component):
    template = """
      <section class="switch-room">
        <h2>Evening room</h2>
        <c-CSwitch checked>Reading lamp</c-CSwitch>
        <c-CSwitch>Window shades</c-CSwitch>
        <c-CSwitch checked>
          <c-fill name="default">Quiet ventilation</c-fill>
          <c-fill name="description">Keep air moving below the bedroom.</c-fill>
        </c-CSwitch>
      </section>
    """
    css = """
      :where(.switch-room) {
        display: grid;
        gap: 0.9rem;
        max-inline-size: 28rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c8bda8, #665d50);
        border-radius: 0.9rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.switch-room h2) {
        margin: 0;
      }
    """


preview = SwitchAtAGlance()

preview  # noqa: B018
````


## Change an immediate setting

The visible label describes the setting and stays the same when state changes.


### Change home settings

[Open the rendered preview](/v/0.4.2/ui-library/components/switch/_previews/basic/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class HomeSettings(Component):
    template = """
      <c-CStack>
        <c-CSwitch checked>Porch light</c-CSwitch>
        <c-CSwitch>Robot vacuum schedule</c-CSwitch>
        <c-CSwitch checked>Door chime</c-CSwitch>
      </c-CStack>
    """


preview = HomeSettings()

preview  # noqa: B018
````


## Add descriptions

Description content is connected to the native Switch. Disabled switches stay
visible but cannot change or submit.


### Describe Switch settings

[Open the rendered preview](/v/0.4.2/ui-library/components/switch/_previews/descriptions/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DescribedSwitches(Component):
    template = """
      <c-CStack>
        <c-CSwitch checked>
          <c-fill name="default">Air purifier</c-fill>
          <c-fill name="description">Runs quietly until the room reaches clean-air target.</c-fill>
        </c-CSwitch>
        <c-CSwitch disabled>
          <c-fill name="default">Fireplace fan</c-fill>
          <c-fill name="description">Available while the fireplace is warm.</c-fill>
        </c-CSwitch>
      </c-CStack>
    """


preview = DescribedSwitches()

preview  # noqa: B018
````


## Control state in the browser

Pass `checked` through `$c-props="{...}"`; handle native `input` with
`$event.target.checked`. Omit the prop to release browser ownership.


### Control a Switch

[Open the rendered preview](/v/0.4.2/ui-library/components/switch/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledSwitch(Component):
    template = """
      <section class="switch-controlled" x-data="{enabled: true}">
        <c-CSwitch
          $c-props="{checked: enabled}"
          @input="enabled = $event.target.checked"
        >Reading mode</c-CSwitch>
        <output x-text="enabled ? 'Reading mode is on' : 'Reading mode is off'"></output>
      </section>
    """
    css = """
      :where(.switch-controlled) {
        display: grid;
        gap: 0.7rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.switch-controlled output) {
        color: light-dark(#3f6212, #bef264);
        font-size: 0.82rem;
      }
    """


preview = ControlledSwitch()

preview  # noqa: B018
````


## Submit and validate

A checked named Switch contributes its value to FormData. Required means the
setting must be on.


### Submit Switch settings

[Open the rendered preview](/v/0.4.2/ui-library/components/switch/_previews/forms/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SwitchForm(Component):
    template = """
      <form
        class="switch-form"
        x-data="{result: ''}"
        @submit.prevent="result = new FormData($event.target).has('quiet_hours') ? 'Saved' : 'Enable quiet hours'"
      >
        <c-CSwitch name="quiet_hours" value="enabled" required>Quiet hours</c-CSwitch>
        <c-CGroup>
          <c-CButton type="submit">Save home settings</c-CButton>
          <button type="reset">Reset</button>
        </c-CGroup>
        <output x-text="result"></output>
      </form>
    """
    css = """
      :where(.switch-form) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = SwitchForm()

preview  # noqa: B018
````


## Choose size and label position

Use `sm`, `md`, or `lg`. `label_pos="start"` puts text before the control in
logical reading order.


### Compare Switch presentation

[Open the rendered preview](/v/0.4.2/ui-library/components/switch/_previews/presentation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SwitchPresentation(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CStack>
        <c-for each="size in sizes">
          <c-CSwitch c-size="size" checked>{{ size }} switch</c-CSwitch>
        </c-for>
        <c-CSwitch label_pos="start" checked>Label before track</c-CSwitch>
      </c-CStack>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"sizes": ("sm", "md", "lg")}


preview = SwitchPresentation()

preview  # noqa: B018
````


## Compose with Field

Inside `CField`, Field owns label, description, error, required, disabled, and
invalid state. Do not add Switch slots there.


### Compose Switch with Field

[Open the rendered preview](/v/0.4.2/ui-library/components/switch/_previews/field/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SwitchField(Component):
    template = """
      <c-CField control_id="away-mode" required>
        <c-fill name="label">Away mode</c-fill>
        <c-fill name="default"><c-CSwitch name="away_mode" /></c-fill>
        <c-fill name="description">Lower heating and pause routine lighting.</c-fill>
        <c-fill name="error">Enable away mode before leaving.</c-fill>
      </c-CField>
    """


preview = SwitchField()

preview  # noqa: B018
````


## Use Switch semantics deliberately

Switches announce on/off. Keep their labels stable and use them only for
immediate settings.


### Choose Switch or Checkbox

[Open the rendered preview](/v/0.4.2/ui-library/components/switch/_previews/semantics/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ChoiceSemantics(Component):
    template = """
      <c-CStack>
        <c-CSwitch checked>
          <c-fill name="default">Automatic hallway lighting</c-fill>
          <c-fill name="description">Takes effect immediately.</c-fill>
        </c-CSwitch>
        <c-CCheckbox>
          <c-fill name="default">Include spare keys in the move checklist</c-fill>
          <c-fill name="description">A selection, not an immediate setting.</c-fill>
        </c-CCheckbox>
      </c-CStack>
    """


preview = ChoiceSemantics()

preview  # noqa: B018
````


## Customize Switch

Override public colors, geometry, motion, and part selectors.


### Customize Switch with public CSS

[Open the rendered preview](/v/0.4.2/ui-library/components/switch/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomSwitch(Component):
    template = """
      <section class="switch-oak">
        <c-CSwitch checked size="lg">Oak reading nook</c-CSwitch>
      </section>
    """
    css = """
      :where(.switch-oak) {
        --cui-switch-on-color: light-dark(#7c4a25, #d8a06f);
        --cui-switch-off-color: light-dark(#8f8376, #9f9385);
        --cui-switch-thumb-color: light-dark(#fffaf2, #2a2119);
        --cui-switch-width: 3.4rem;
        --cui-switch-height: 1.9rem;
        padding: 1rem;
        border: 1px solid light-dark(#c6ad91, #725b44);
        border-radius: 0.8rem;
      }
    """


preview = CustomSwitch()

preview  # noqa: B018
````


## API reference

### Inputs

#### CSwitch server inputs

Server inputs are passed in a template through `<c-CSwitch ... />` or in Python through
`CSwitch(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 16rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="switch-input-cswitch-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the optional native/FormData name. |
| <span id="switch-input-cswitch-server-inputs-value"></span>`value` | `str` | `"on"` | Sets the submitted token while checked. |
| <span id="switch-input-cswitch-server-inputs-id"></span>`id` | `str | None` | `None` | Sets native input identity and the label relationship. |
| <span id="switch-input-cswitch-server-inputs-checked"></span>`checked` | `bool` | `False` | Sets server default checkedness. |
| <span id="switch-input-cswitch-server-inputs-required"></span>`required` | `bool | None` | `None` | Requires the setting to be on; CField owns it when composed. |
| <span id="switch-input-cswitch-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Disables activation and submission; Field/Form remain dominant. |
| <span id="switch-input-cswitch-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Sets explicit invalid styling and relationships; CField owns it when composed. |
| <span id="switch-input-cswitch-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CSwitchSize`](#switch-interface-size)) | `"md"` | Sets control and text scale. |
| <span id="switch-input-cswitch-server-inputs-label-pos"></span>`label_pos` | `"start" | "end"` ([`CSwitchLabelPos`](#switch-interface-label-pos)) | `"end"` | Places the visible label before or after the track. |
| <span id="switch-input-cswitch-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#switch-interface-class-value)) | `None` | Adds root classes and merges them with attrs. |
| <span id="switch-input-cswitch-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#switch-interface-style-value)) | `None` | Adds root inline styles and merges them with attrs. |
| <span id="switch-input-cswitch-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted nonconflicting metadata and targeted Alpine attributes to the root. |
| <span id="switch-input-cswitch-server-inputs-input-attrs"></span>`input_attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted nonconflicting naming metadata and native listeners to the input. |

</div>

#### CSwitch client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CSwitch />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 16rem; --ui-api-column-3-width: 7rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="switch-input-cswitch-client-inputs-checked"></span>`checked` | `boolean` | Releases control to native checkedness. | Controls current checkedness; omission releases control. |
| <span id="switch-input-cswitch-client-inputs-value"></span>`value` | `string` | Uses the server fallback. | Controls the native submission token. |
| <span id="switch-input-cswitch-client-inputs-required"></span>`required` | `boolean` | Uses the server or Field fallback. | Controls native required state outside Field. |
| <span id="switch-input-cswitch-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server or Field/Form fallback. | Controls local disabled state outside Field. |
| <span id="switch-input-cswitch-client-inputs-invalid"></span>`invalid` | `boolean` | Uses the server or Field fallback. | Controls explicit invalid state outside Field. |
| <span id="switch-input-cswitch-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` | Uses the server fallback. | Controls public size. |
| <span id="switch-input-cswitch-client-inputs-label-pos"></span>`label_pos` | `"start" | "end"` | Uses the server fallback. | Controls logical label placement. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CSwitch slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="switch-slot-cswitch-slots-default"></span>`default` | no | `{}` ([`CSwitchDefaultSlotData`](#switch-interface-default)) | Label-free standalone Switch requires an ARIA name; the slot is forbidden under CField. |
| <span id="switch-slot-cswitch-slots-description"></span>`description` | no | `{}` ([`CSwitchDescriptionSlotData`](#switch-interface-description)) | Description and relationship are omitted; the slot is forbidden under CField. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CSwitch CSS variables

Apply these variables to `CSwitch` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="switch-css-cswitch-css-variables-cui-switch-off-color"></span>`--cui-switch-off-color` | `color` | Track color while off. | `Scheme-aware neutral.` |
| <span id="switch-css-cswitch-css-variables-cui-switch-on-color"></span>`--cui-switch-on-color` | `color` | Track color while on. | `Scheme-aware primary.` |
| <span id="switch-css-cswitch-css-variables-cui-switch-thumb-color"></span>`--cui-switch-thumb-color` | `color` | Thumb fill. | `Canvas.` |
| <span id="switch-css-cswitch-css-variables-cui-switch-foreground"></span>`--cui-switch-foreground` | `color` | Label and description foreground. | `CanvasText.` |
| <span id="switch-css-cswitch-css-variables-cui-switch-focus-color"></span>`--cui-switch-focus-color` | `color` | Keyboard focus ring. | `Highlight.` |
| <span id="switch-css-cswitch-css-variables-cui-switch-invalid-color"></span>`--cui-switch-invalid-color` | `color` | Invalid-state outline. | `Scheme-aware danger.` |
| <span id="switch-css-cswitch-css-variables-cui-switch-disabled-opacity"></span>`--cui-switch-disabled-opacity` | `number` | Disabled root opacity. | `0.52.` |
| <span id="switch-css-cswitch-css-variables-cui-switch-width"></span>`--cui-switch-width` | `length` | Track inline size. | `Size-derived length.` |
| <span id="switch-css-cswitch-css-variables-cui-switch-height"></span>`--cui-switch-height` | `length` | Track block size. | `Size-derived length.` |
| <span id="switch-css-cswitch-css-variables-cui-switch-padding"></span>`--cui-switch-padding` | `length` | Track inset around the thumb. | `0.1875rem.` |
| <span id="switch-css-cswitch-css-variables-cui-switch-gap"></span>`--cui-switch-gap` | `length` | Track-to-label spacing. | `0.625rem.` |
| <span id="switch-css-cswitch-css-variables-cui-switch-duration"></span>`--cui-switch-duration` | `time` | Track and thumb transition duration. | `140ms.` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CSwitch attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="switch-attribute-cswitch-attributes-role"></span>`role` | Native input | `"switch"` | Exposes on/off semantics. |
| <span id="switch-attribute-cswitch-attributes-checked"></span>`checked` | Native input | `boolean present or absent` | Server default checkedness; current checkedness is the native property. |
| <span id="switch-attribute-cswitch-attributes-required"></span>`required` | Native input | `boolean present or absent` | Native required state. |
| <span id="switch-attribute-cswitch-attributes-disabled"></span>`disabled` | Native input | `boolean present or absent` | Native disabled state. |
| <span id="switch-attribute-cswitch-attributes-data-checked"></span>`data-checked` | Root | `boolean present or absent` | Mirrors current native checkedness. |
| <span id="switch-attribute-cswitch-attributes-data-required"></span>`data-required` | Root | `boolean present or absent` | Mirrors effective required state. |
| <span id="switch-attribute-cswitch-attributes-data-disabled"></span>`data-disabled` | Root | `boolean present or absent` | Mirrors effective disabled state. |
| <span id="switch-attribute-cswitch-attributes-data-invalid"></span>`data-invalid` | Root | `boolean present or absent` | Mirrors explicit or native invalid state. |
| <span id="switch-attribute-cswitch-attributes-data-size"></span>`data-size` | Root | `"sm" | "md" | "lg"` | Mirrors effective size. |
| <span id="switch-attribute-cswitch-attributes-data-label-pos"></span>`data-label-pos` | Root | `"start" | "end"` | Mirrors logical label placement. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CSwitch selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="switch-selector-cswitch-selectors-switch"></span>`[data-citry-ui-part="switch"]` | Root span | Root styling and attrs destination. |
| <span id="switch-selector-cswitch-selectors-input"></span>`[data-citry-ui-part="input"]` | Native checkbox input | Focus form state and native events. |
| <span id="switch-selector-cswitch-selectors-surface"></span>`[data-citry-ui-part="surface"]` | Presentation span | Shared track and text layout surface. |
| <span id="switch-selector-cswitch-selectors-track"></span>`[data-citry-ui-part="track"]` | Decorative span | Off/on visual track. |
| <span id="switch-selector-cswitch-selectors-thumb"></span>`[data-citry-ui-part="thumb"]` | Decorative span | Moving state indicator. |
| <span id="switch-selector-cswitch-selectors-body"></span>`[data-citry-ui-part="body"]` | Text wrapper span | Label and description layout. |
| <span id="switch-selector-cswitch-selectors-label"></span>`[data-citry-ui-part="label"]` | Visible label span | Stable setting name. |
| <span id="switch-selector-cswitch-selectors-description"></span>`[data-citry-ui-part="description"]` | Description span | Optional connected guidance. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="switch-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="switch-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="switch-interface-size"></span>`CSwitchSize` | `Literal["sm", "md", "lg"]` |
| <span id="switch-interface-label-pos"></span>`CSwitchLabelPos` | `Literal["start", "end"]` |

</div>

<span id="switch-interface-default"></span>

#### `CSwitchDefaultSlotData`

Empty dataclass: `{}`.

<span id="switch-interface-description"></span>

#### `CSwitchDescriptionSlotData`

Empty dataclass: `{}`.

### Translation keys

-