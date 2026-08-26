---
title: Toggle
url: https://citry.dev/v/0.4.4/ui-library/components/toggle/
description: "Build standalone or grouped pressed Buttons with Citry UI."
---
# Toggle

Use `CToggle` for a Button whose pressed state persists. Use `CToggleGroup` for related exclusive or multiple choices.

## Toggle at a glance


### Toggle at a glance

[Open the rendered preview](/v/0.4.4/ui-library/components/toggle/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToggleGlance(Component):
    template = """
      <c-CToggleGroup label="Star map layers" value="constellations" c-mandatory="True">
        <c-CToggle value="constellations">Constellations</c-CToggle>
        <c-CToggle value="planets">Planets</c-CToggle>
        <c-CToggle value="grid">Grid</c-CToggle>
      </c-CToggleGroup>
    """


preview = ToggleGlance()
preview  # noqa: B018
````


## Choose Toggle, Switch, or Button Group

Toggle changes an active tool or view. Switch changes an immediate setting. Button Group groups related actions without selection.

## Toggle one tool


### Toggle one tool

[Open the rendered preview](/v/0.4.4/ui-library/components/toggle/_previews/standalone/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class StandaloneToggle(Component):
    template = """
      <c-CToggle c-pressed="True">Pin observation</c-CToggle>
    """


preview = StandaloneToggle()
preview  # noqa: B018
````


## Select one or several values


### Compare single and multiple Toggle Groups

[Open the rendered preview](/v/0.4.4/ui-library/components/toggle/_previews/groups/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToggleGroups(Component):
    template = """
      <c-CCol gap="lg">
        <c-CToggleGroup label="Chart scale" value="linear">
          <c-CToggle value="linear">Linear</c-CToggle>
          <c-CToggle value="log">Log</c-CToggle>
        </c-CToggleGroup>
        <c-CToggleGroup label="Visible layers" c-value="['stars', 'labels']" c-multiple="True">
          <c-CToggle value="stars">Stars</c-CToggle>
          <c-CToggle value="labels">Labels</c-CToggle>
          <c-CToggle value="grid">Grid</c-CToggle>
        </c-CToggleGroup>
      </c-CCol>
    """


preview = ToggleGroups()
preview  # noqa: B018
````


## Keep one value selected

`mandatory=True` rejects only the user action that would clear the final value.


### Keep one Toggle selected

[Open the rendered preview](/v/0.4.4/ui-library/components/toggle/_previews/mandatory/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MandatoryToggle(Component):
    template = """
      <c-CToggleGroup label="Coordinate system" value="equatorial" c-mandatory="True">
        <c-CToggle value="equatorial">Equatorial</c-CToggle>
        <c-CToggle value="galactic">Galactic</c-CToggle>
      </c-CToggleGroup>
    """


preview = MandatoryToggle()
preview  # noqa: B018
````


## Control selection in the browser

Client inputs are passed with `$c-props="{...}"`. `onValueChange` reports the next requested value.


### Control Toggle selection

[Open the rendered preview](/v/0.4.4/ui-library/components/toggle/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledToggle(Component):
    template = """
      <section x-data="{ view: 'sky' }">
        <p>Current view: <strong x-text="view"></strong></p>
        <c-CToggleGroup
          label="Observation view"
          value="sky"
          $c-props="{ value: view, onValueChange: (next) => view = next }"
        >
          <c-CToggle value="sky">Sky</c-CToggle>
          <c-CToggle value="spectrum">Spectrum</c-CToggle>
        </c-CToggleGroup>
      </section>
    """


preview = ControlledToggle()
preview  # noqa: B018
````


## Choose presentation


### Compare Toggle variants and sizes

[Open the rendered preview](/v/0.4.4/ui-library/components/toggle/_previews/presentation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TogglePresentation(Component):
    template = """
      <c-CCol gap="md">
        <c-for each="variant in variants">
          <c-CToggleGroup c-label="variant + ' display'" value="one" c-variant="variant">
            <c-CToggle value="one">One</c-CToggle>
            <c-CToggle value="two">Two</c-CToggle>
          </c-CToggleGroup>
        </c-for>
      </c-CCol>
    """

    def template_data(self, kwargs, slots):  # noqa: ANN001, ANN201, ARG002
        return {"variants": ("soft", "outline", "plain")}


preview = TogglePresentation()
preview  # noqa: B018
````


## Customize Toggle


### Customize Toggle

[Open the rendered preview](/v/0.4.4/ui-library/components/toggle/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToggleCustomization(Component):
    template = """
      <c-CToggleGroup class_="nebula-toggle" label="Nebula filter" value="oxygen">
        <c-CToggle value="oxygen">Oxygen</c-CToggle>
        <c-CToggle value="hydrogen">Hydrogen</c-CToggle>
      </c-CToggleGroup>
    """
    css = """
      :where(.nebula-toggle) {
        --cui-toggle-pressed-background: light-dark(#7c3aed, #a78bfa);
        --cui-toggle-pressed-foreground: white;
        --cui-toggle-radius: 999px;
      }
    """


preview = ToggleCustomization()
preview  # noqa: B018
````


## Accessibility and behavior

Each Toggle is a native Button with `aria-pressed`. Space and Enter activate it. All enabled Toggles remain in ordinary Tab order; the family does not claim arrow keys or Form submission.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CToggleGroup server inputs

Server inputs are passed in a template through `<c-CToggleGroup ... />` or in Python through
`CToggleGroup(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="toggle-input-ctoggle-group-server-inputs-label"></span>`label` | `str` | required | Names the related Toggle choices. |
| <span id="toggle-input-ctoggle-group-server-inputs-value"></span>`value` | `str | None | Sequence[str]` ([`CToggleValue`](#toggle-interface-input-type-aliases-toggle-value)) | `None` | Selects the initial single value or multiple values. |
| <span id="toggle-input-ctoggle-group-server-inputs-multiple"></span>`multiple` | `bool` | `False` | Allows several Toggles to be pressed together. |
| <span id="toggle-input-ctoggle-group-server-inputs-mandatory"></span>`mandatory` | `bool` | `False` | Prevents user activation from clearing the final pressed Toggle. |
| <span id="toggle-input-ctoggle-group-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables every owned Toggle; enclosing CForm disabled remains dominant. |
| <span id="toggle-input-ctoggle-group-server-inputs-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CToggleOrientation`](#toggle-interface-input-type-aliases-toggle-orientation)) | `"horizontal"` | Selects the group axis. |
| <span id="toggle-input-ctoggle-group-server-inputs-variant"></span>`variant` | `"soft" | "outline" | "plain"` ([`CToggleVariant`](#toggle-interface-input-type-aliases-toggle-variant)) | `"outline"` | Owns visual treatment for every grouped Toggle. |
| <span id="toggle-input-ctoggle-group-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CToggleSize`](#toggle-interface-input-type-aliases-toggle-size)) | `"md"` | Owns geometry for every grouped Toggle. |
| <span id="toggle-input-ctoggle-group-server-inputs-grow"></span>`grow` | `bool` | `False` | Gives direct Toggles equal available width. |
| <span id="toggle-input-ctoggle-group-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#toggle-interface-input-type-aliases-class-value)) | `None` | Adds root classes. |
| <span id="toggle-input-ctoggle-group-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#toggle-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles. |
| <span id="toggle-input-ctoggle-group-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted copied root attributes without replacing group ownership. |

</div>

#### CToggleGroup client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CToggleGroup />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="toggle-input-ctoggle-group-client-inputs-value"></span>`value` | `string | null | string[] | undefined` | Uses the server input. | Controls pressed values while supplied; omission releases ownership. |
| <span id="toggle-input-ctoggle-group-client-inputs-disabled"></span>`disabled` | `boolean | undefined` | Uses the server input. | Overrides local disabled while supplied; Form disabled remains dominant. |
| <span id="toggle-input-ctoggle-group-client-inputs-orientation"></span>`orientation` | `"horizontal" | "vertical" | undefined` | Uses the server input. | Overrides orientation while valid and supplied. |
| <span id="toggle-input-ctoggle-group-client-inputs-variant"></span>`variant` | `"soft" | "outline" | "plain" | undefined` | Uses the server input. | Overrides visual treatment for every grouped Toggle. |
| <span id="toggle-input-ctoggle-group-client-inputs-size"></span>`size` | `"sm" | "md" | "lg" | undefined` | Uses the server input. | Overrides geometry for every grouped Toggle. |
| <span id="toggle-input-ctoggle-group-client-inputs-on-value-change"></span>`onValueChange` | `((value, detail) => void) | undefined` | Uses the server input. | Runs after an accepted grouped activation. |

</div>

#### CToggle server inputs

Server inputs are passed in a template through `<c-CToggle ... />` or in Python through
`CToggle(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="toggle-input-ctoggle-server-inputs-value"></span>`value` | `str | None` | `None` | Required unique identity inside CToggleGroup; unused standalone. |
| <span id="toggle-input-ctoggle-server-inputs-pressed"></span>`pressed` | `bool` | `False` | Sets standalone initial pressed state; group value owns grouped state. |
| <span id="toggle-input-ctoggle-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables this Toggle; enclosing CForm disabled remains dominant. |
| <span id="toggle-input-ctoggle-server-inputs-variant"></span>`variant` | `"soft" | "outline" | "plain" | None` ([`CToggleVariant`](#toggle-interface-input-type-aliases-toggle-variant)) | `None` | Selects standalone visual treatment; CToggleGroup owns grouped presentation. |
| <span id="toggle-input-ctoggle-server-inputs-size"></span>`size` | `"sm" | "md" | "lg" | None` ([`CToggleSize`](#toggle-interface-input-type-aliases-toggle-size)) | `None` | Selects standalone geometry; CToggleGroup owns grouped presentation. |
| <span id="toggle-input-ctoggle-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#toggle-interface-input-type-aliases-class-value)) | `None` | Adds Button classes. |
| <span id="toggle-input-ctoggle-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#toggle-interface-input-type-aliases-style-value)) | `None` | Adds Button inline styles. |
| <span id="toggle-input-ctoggle-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted copied Button attributes without replacing Toggle ownership. |

</div>

#### CToggle client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CToggle />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="toggle-input-ctoggle-client-inputs-pressed"></span>`pressed` | `boolean | undefined` | Uses the server input. | Controls a standalone Toggle while supplied. |
| <span id="toggle-input-ctoggle-client-inputs-disabled"></span>`disabled` | `boolean | undefined` | Uses the server input. | Overrides local disabled while supplied; enclosing CForm disabled remains dominant. |
| <span id="toggle-input-ctoggle-client-inputs-variant"></span>`variant` | `"soft" | "outline" | "plain" | undefined` | Uses the server input. | Overrides standalone visual treatment; grouped presentation comes from CToggleGroup. |
| <span id="toggle-input-ctoggle-client-inputs-size"></span>`size` | `"sm" | "md" | "lg" | undefined` | Uses the server input. | Overrides standalone geometry; grouped presentation comes from CToggleGroup. |
| <span id="toggle-input-ctoggle-client-inputs-on-pressed-change"></span>`onPressedChange` | `((pressed, detail) => void) | undefined` | Uses the server input. | Runs after accepted standalone activation. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CToggleGroup slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="toggle-slot-ctoggle-group-slots-default"></span>`default` | yes | `{}` ([`CToggleGroupDefaultSlotData`](#toggle-interface-ctoggle-group-default-slot-data)) | None. |

</div>

#### CToggle slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="toggle-slot-ctoggle-slots-default"></span>`default` | yes | `{}` ([`CToggleDefaultSlotData`](#toggle-interface-ctoggle-default-slot-data)) | None. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CToggleGroup events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="toggle-event-ctoggle-group-events-on-value-change"></span>`onValueChange` | `(value, detail: CToggleValueChangeDetail) => void` ([`CToggleValueChangeDetail`](#toggle-interface-ctoggle-value-change-detail)) | Accepted grouped activation. | `{value, previousValue, source}` ([`CToggleValueChangeDetail`](#toggle-interface-ctoggle-value-change-detail)) | Reports the requested next selection; a supplied client value remains authoritative. |

</div>

#### CToggle events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="toggle-event-ctoggle-events-on-pressed-change"></span>`onPressedChange` | `(pressed: boolean, detail: object) => void` | Accepted standalone activation. | `{value: boolean, previousValue: boolean, source: "activation"}` | Reports the requested pressed state; a supplied client value remains authoritative. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CToggle CSS variables

Apply these variables to `CToggle` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="toggle-css-ctoggle-css-variables-cui-toggle-foreground"></span>`--cui-toggle-foreground` | `color` | Resting text/icon foreground. | `CanvasText` |
| <span id="toggle-css-ctoggle-css-variables-cui-toggle-background"></span>`--cui-toggle-background` | `color` | Resting background. | `transparent` |
| <span id="toggle-css-ctoggle-css-variables-cui-toggle-border-color"></span>`--cui-toggle-border-color` | `color` | Border color. | `Nested-scheme border color.` |
| <span id="toggle-css-ctoggle-css-variables-cui-toggle-pressed-background"></span>`--cui-toggle-pressed-background` | `color` | Pressed background. | `Nested-scheme blue surface.` |
| <span id="toggle-css-ctoggle-css-variables-cui-toggle-pressed-foreground"></span>`--cui-toggle-pressed-foreground` | `color` | Pressed foreground. | `Nested-scheme blue foreground.` |
| <span id="toggle-css-ctoggle-css-variables-cui-toggle-radius"></span>`--cui-toggle-radius` | `length` | Outer group corners. | `0.55rem` |
| <span id="toggle-css-ctoggle-css-variables-cui-toggle-height"></span>`--cui-toggle-height` | `length` | Minimum block size. | `Size-derived.` |
| <span id="toggle-css-ctoggle-css-variables-cui-toggle-padding"></span>`--cui-toggle-padding` | `length` | Inline padding. | `Size-derived.` |
| <span id="toggle-css-ctoggle-css-variables-cui-toggle-focus-ring"></span>`--cui-toggle-focus-ring` | `color` | Keyboard focus outline. | `Highlight` |

</div>

#### CToggleGroup CSS variables

Apply these variables to `CToggleGroup` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="toggle-css-ctoggle-group-css-variables-cui-toggle-group-gap"></span>`--cui-toggle-group-gap` | `length` | Gap between Toggles. | `0` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CToggleGroup attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="toggle-attribute-ctoggle-group-attributes-data-multiple"></span>`data-multiple` | Root | `present-or-absent` | Present in multiple mode. |
| <span id="toggle-attribute-ctoggle-group-attributes-data-mandatory"></span>`data-mandatory` | Root | `present-or-absent` | Present while final user deselection is prevented. |
| <span id="toggle-attribute-ctoggle-group-attributes-data-disabled"></span>`data-disabled` | Root | `present-or-absent` | Present while all owned Toggles are disabled. |
| <span id="toggle-attribute-ctoggle-group-attributes-data-orientation"></span>`data-orientation` | Root | `"horizontal" | "vertical"` | Reflects layout axis. |
| <span id="toggle-attribute-ctoggle-group-attributes-data-variant"></span>`data-variant` | Root | `"soft" | "outline" | "plain"` | Reflects group-owned visual treatment. |
| <span id="toggle-attribute-ctoggle-group-attributes-data-size"></span>`data-size` | Root | `"sm" | "md" | "lg"` | Reflects group-owned geometry. |
| <span id="toggle-attribute-ctoggle-group-attributes-data-grow"></span>`data-grow` | Root | `present-or-absent` | Present when Toggles share the available width. |

</div>

#### CToggle attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="toggle-attribute-ctoggle-attributes-aria-pressed"></span>`aria-pressed` | Native Button | `boolean` | Exposes native Toggle pressed state. |
| <span id="toggle-attribute-ctoggle-attributes-data-pressed"></span>`data-pressed` | Native Button | `present-or-absent` | Public pressed styling hook. |
| <span id="toggle-attribute-ctoggle-attributes-data-disabled"></span>`data-disabled` | Native Button | `present-or-absent` | Mirrors effective disabled state. |
| <span id="toggle-attribute-ctoggle-attributes-data-value"></span>`data-value` | Grouped native Button | `string` | Stable group identity. |
| <span id="toggle-attribute-ctoggle-attributes-data-variant"></span>`data-variant` | Native Button | `"soft" | "outline" | "plain"` | Reflects visual treatment. |
| <span id="toggle-attribute-ctoggle-attributes-data-size"></span>`data-size` | Native Button | `"sm" | "md" | "lg"` | Reflects geometry. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CToggleGroup selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="toggle-selector-ctoggle-group-selectors-data-citry-ui-part-toggle-group"></span>`[data-citry-ui-part="toggle-group"]` | Root | Stable group and attrs destination. |

</div>

#### CToggle selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="toggle-selector-ctoggle-selectors-data-citry-ui-part-toggle"></span>`[data-citry-ui-part="toggle"]` | Native Button root | Stable Toggle, attrs, focus, and pressed-state surface. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="toggle-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="toggle-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="toggle-interface-input-type-aliases-toggle-variant"></span>`CToggleVariant` | `Literal["soft", "outline", "plain"]` |
| <span id="toggle-interface-input-type-aliases-toggle-size"></span>`CToggleSize` | `Literal["sm", "md", "lg"]` |
| <span id="toggle-interface-input-type-aliases-toggle-orientation"></span>`CToggleOrientation` | `Literal["horizontal", "vertical"]` |
| <span id="toggle-interface-input-type-aliases-toggle-value"></span>`CToggleValue` | `str | None | Sequence[str]` |

</div>

<span id="toggle-interface-ctoggle-value-change-detail"></span>

#### `CToggleValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="toggle-interface-ctoggle-value-change-detail-value"></span>`value` | `str | list[str] | None` | - | Requested selection. |
| <span id="toggle-interface-ctoggle-value-change-detail-previous-value"></span>`previousValue` | `str | list[str] | None` | - | Selection before activation. |
| <span id="toggle-interface-ctoggle-value-change-detail-source"></span>`source` | `"activation"` | - | Change origin. |

</div>

<span id="toggle-interface-ctoggle-group-default-slot-data"></span>

#### `CToggleGroupDefaultSlotData`

Empty dataclass: `{}`.

<span id="toggle-interface-ctoggle-default-slot-data"></span>

#### `CToggleDefaultSlotData`

Empty dataclass: `{}`.

### Translation keys

-