---
title: Button Group
url: https://citry.dev/v/0.4.1/ui-library/components/button-group/
description: "Arrange related Citry UI actions as one named group."
---
# Button Group

Use `CButtonGroup` when several Buttons perform closely related actions. It owns grouping and layout, not selection.

## Button Group at a glance


### Button Group at a glance

[Open the rendered preview](/v/0.4.1/ui-library/components/button-group/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonGroupGlance(Component):
    template = """
      <c-CButtonGroup label="Telescope controls">
        <c-CButton variant="outline">Previous</c-CButton>
        <c-CButton variant="outline">Center</c-CButton>
        <c-CButton variant="outline">Next</c-CButton>
      </c-CButtonGroup>
    """


preview = ButtonGroupGlance()
preview  # noqa: B018
````


## Group related actions

Give every group a concise accessible label. Buttons remain ordinary native actions.


### Group related actions

[Open the rendered preview](/v/0.4.1/ui-library/components/button-group/_previews/related-actions/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RelatedActions(Component):
    template = """
      <c-CButtonGroup label="Map controls">
        <c-CButton variant="outline">Zoom in</c-CButton>
        <c-CButton variant="outline">Reset</c-CButton>
        <c-CButton variant="outline">Zoom out</c-CButton>
      </c-CButtonGroup>
    """


preview = RelatedActions()
preview  # noqa: B018
````



```citry-html
<c-CButtonGroup label="Map controls">
  <c-CButton variant="outline">Zoom in</c-CButton>
  <c-CButton variant="outline">Zoom out</c-CButton>
</c-CButtonGroup>
```


## Attach or space Buttons

Attached groups share outer geometry. Set `attached=False` for separate Buttons that still belong to one named action set.


### Compare attached and spaced groups

[Open the rendered preview](/v/0.4.1/ui-library/components/button-group/_previews/attachment/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class Attachment(Component):
    template = """
      <c-CStack gap="md">
        <c-CButtonGroup label="Attached view controls">
          <c-CButton variant="outline">Map</c-CButton>
          <c-CButton variant="outline">Sky</c-CButton>
        </c-CButtonGroup>
        <c-CButtonGroup label="Spaced view controls" c-attached="False">
          <c-CButton variant="outline">Map</c-CButton>
          <c-CButton variant="outline">Sky</c-CButton>
        </c-CButtonGroup>
      </c-CStack>
    """


preview = Attachment()
preview  # noqa: B018
````


## Choose orientation and growth

Vertical groups describe stacked actions. `grow=True` gives direct Buttons equal width.


### Choose Button Group layout

[Open the rendered preview](/v/0.4.1/ui-library/components/button-group/_previews/layout/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class Layout(Component):
    template = """
      <c-CStack gap="lg">
        <c-CButtonGroup label="Time range" c-grow="True">
          <c-CButton variant="outline">Night</c-CButton>
          <c-CButton variant="outline">Week</c-CButton>
          <c-CButton variant="outline">Month</c-CButton>
        </c-CButtonGroup>
        <c-CButtonGroup label="Export format" orientation="vertical">
          <c-CButton variant="outline">Star chart</c-CButton>
          <c-CButton variant="outline">Observation log</c-CButton>
        </c-CButtonGroup>
      </c-CStack>
    """


preview = Layout()
preview  # noqa: B018
````


## Compose mixed actions

Each Button keeps its own variant, intent, loading, disabled, and link behavior. Use `CToggleGroup` instead when the Buttons represent selected choices.


### Compose mixed Button actions

[Open the rendered preview](/v/0.4.1/ui-library/components/button-group/_previews/composition/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class Composition(Component):
    template = """
      <c-CButtonGroup label="Expedition actions">
        <c-CButton intent="primary">Save route</c-CButton>
        <c-CButton variant="outline" href="/preview">Preview</c-CButton>
        <c-CButton variant="ghost" intent="danger">Discard</c-CButton>
      </c-CButtonGroup>
    """


preview = Composition()
preview  # noqa: B018
````


## Customize Button Group

Public variables control spacing, outer radius, and border overlap.


### Customize Button Group

[Open the rendered preview](/v/0.4.1/ui-library/components/button-group/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class Customization(Component):
    template = """
      <c-CButtonGroup class_="orbit-group" label="Orbit controls">
        <c-CButton variant="outline">Inner</c-CButton>
        <c-CButton variant="outline">Stable</c-CButton>
        <c-CButton variant="outline">Outer</c-CButton>
      </c-CButtonGroup>
    """
    css = """
      :where(.orbit-group) {
        --cui-button-group-radius: 999px;
        --cui-button-group-border-width: 2px;
      }
    """


preview = Customization()
preview  # noqa: B018
````


## Accessibility and behavior

The root is a named `group`. Tab order, activation, Form behavior, loading, and disabled state belong to each Button. Button Group adds no JavaScript or roving focus.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CButtonGroup server inputs

Server inputs are passed in a template through `<c-CButtonGroup ... />` or in Python through
`CButtonGroup(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="button-group-input-cbutton-group-server-inputs-label"></span>`label` | `str` | required | Supplies the accessible name for the related action group. |
| <span id="button-group-input-cbutton-group-server-inputs-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CButtonGroupOrientation`](#button-group-interface-input-type-aliases-cbutton-group-orientation)) | `"horizontal"` | Selects the action layout axis. |
| <span id="button-group-input-cbutton-group-server-inputs-attached"></span>`attached` | `bool` | `True` | Joins direct CButton children with shared edge geometry. |
| <span id="button-group-input-cbutton-group-server-inputs-grow"></span>`grow` | `bool` | `False` | Distributes direct CButton children evenly across the available inline size. |
| <span id="button-group-input-cbutton-group-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#button-group-interface-input-type-aliases-class-value)) | `None` | Adds root classes. |
| <span id="button-group-input-cbutton-group-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#button-group-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles. |
| <span id="button-group-input-cbutton-group-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted attributes without replacing group semantics, naming, layout reflections, children, focus ownership, or Citry runtime fields. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CButtonGroup slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="button-group-slot-cbutton-group-slots-default"></span>`default` | yes | `{}` ([`CButtonGroupDefaultSlotData`](#button-group-interface-cbutton-group-default-slot-data)) | None. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CButtonGroup CSS variables

Apply these variables to `CButtonGroup` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="button-group-css-cbutton-group-css-variables-cui-button-group-gap"></span>`--cui-button-group-gap` | `length` | Gap between nonattached actions. | `0.5rem` |
| <span id="button-group-css-cbutton-group-css-variables-cui-button-group-radius"></span>`--cui-button-group-radius` | `length` | Outer corner radius of attached direct Buttons. | `0.55rem` |
| <span id="button-group-css-cbutton-group-css-variables-cui-button-group-border-width"></span>`--cui-button-group-border-width` | `length` | Adjacent border overlap for attached Buttons. | `1px` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CButtonGroup attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="button-group-attribute-cbutton-group-attributes-data-orientation"></span>`data-orientation` | Root | `"horizontal" | "vertical"` | Reflects the layout axis. |
| <span id="button-group-attribute-cbutton-group-attributes-data-attached"></span>`data-attached` | Root | `present-or-absent` | Present when direct Buttons use joined geometry. |
| <span id="button-group-attribute-cbutton-group-attributes-data-grow"></span>`data-grow` | Root | `present-or-absent` | Present when direct Buttons share the available width. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CButtonGroup selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="button-group-selector-cbutton-group-selectors-data-citry-ui-part-button-group"></span>`[data-citry-ui-part="button-group"]` | Root | Stable group and attrs destination. |
| <span id="button-group-selector-cbutton-group-selectors-data-citry-ui-part-button"></span>`[data-citry-ui-part="button"]` | Direct CButton root | Applies joined geometry to direct Button children through the CButton public selector. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="button-group-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="button-group-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="button-group-interface-input-type-aliases-cbutton-group-orientation"></span>`CButtonGroupOrientation` | `Literal["horizontal", "vertical"]` |

</div>

<span id="button-group-interface-cbutton-group-default-slot-data"></span>

#### `CButtonGroupDefaultSlotData`

Empty dataclass: `{}`.

### Translation keys

-