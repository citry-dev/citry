---
title: Stepper
url: https://citry.dev/v/0.4.4/ui-library/components/stepper/
description: "Communicate and optionally navigate ordered workflow progress."
---
# Stepper

Use `CStepper` for the progress and navigation surface of a finite workflow.
Compose the current panel, validation, and Previous/Next actions beside it so
application state has one owner.

## Stepper at a glance


### Stepper at a glance

[Open the rendered preview](/v/0.4.4/ui-library/components/stepper/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class StepperAtAGlance(Component):
    template = """
      <c-CStepper label="Account setup" c-active="1" variant="soft">
        <c-CStep>Profile</c-CStep>
        <c-CStep>Security</c-CStep>
        <c-CStep>Review</c-CStep>
      </c-CStepper>
    """


preview = StepperAtAGlance()
preview  # noqa: B018
````


## Navigate a linear workflow

Set `interactive` to render form-safe native Buttons. Linear mode permits the
current and completed Steps while future Steps remain unavailable.


### Navigate completed Steps

[Open the rendered preview](/v/0.4.4/ui-library/components/stepper/_previews/interactive/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InteractiveStepper(Component):
    template = """
      <section x-data="{ active: 1 }">
        <c-CStepper
          label="Publication workflow"
          c-active="1"
          interactive
          $c-props="{ active, onActiveChange: (next) => active = next }"
        >
          <c-CStep>Draft</c-CStep>
          <c-CStep>Review</c-CStep>
          <c-CStep>Publish</c-CStep>
        </c-CStepper>
        <p>Current zero-based index: <strong x-text="active"></strong></p>
      </section>
    """


preview = InteractiveStepper()
preview  # noqa: B018
````


## Allow non-linear navigation


### Navigate Steps in any order

[Open the rendered preview](/v/0.4.4/ui-library/components/stepper/_previews/nonlinear/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NonlinearStepper(Component):
    template = """
      <section x-data="{ active: 0 }">
        <c-CStepper
          label="Profile sections"
          interactive
          c-linear="False"
          $c-props="{ active, onActiveChange: (next) => active = next }"
        >
          <c-CStep>Identity</c-CStep>
          <c-CStep>Preferences</c-CStep>
          <c-CStep>Notifications</c-CStep>
        </c-CStepper>
      </section>
    """


preview = NonlinearStepper()
preview  # noqa: B018
````


## Show workflow metadata

Optional descriptions and error state belong to each Step declaration.


### Show optional and error Steps

[Open the rendered preview](/v/0.4.4/ui-library/components/stepper/_previews/states/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class StepperStates(Component):
    template = """
      <c-CStepper label="Checkout" c-active="1" orientation="vertical" variant="outline">
        <c-CStep>
          <c-fill name="default">Delivery address</c-fill>
          <c-fill name="description">Saved</c-fill>
        </c-CStep>
        <c-CStep error>
          <c-fill name="default">Payment</c-fill>
          <c-fill name="description">Check the card number</c-fill>
        </c-CStep>
        <c-CStep optional>
          <c-fill name="default">Gift message</c-fill>
          <c-fill name="description">Optional</c-fill>
        </c-CStep>
      </c-CStepper>
    """


preview = StepperStates()
preview  # noqa: B018
````


## Control the active Step

Client `active` is controlled while supplied. `onActiveChange` requests a new
zero-based index; the application decides whether to accept it.


### Control active workflow state

[Open the rendered preview](/v/0.4.4/ui-library/components/stepper/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledStepper(Component):
    template = """
      <section x-data="{ active: 0 }">
        <c-CStepper
          label="Workspace setup"
          interactive
          c-linear="False"
          $c-props="{ active, onActiveChange: (next) => active = next }"
        >
          <c-CStep>Workspace</c-CStep>
          <c-CStep>Members</c-CStep>
          <c-CStep>Permissions</c-CStep>
        </c-CStepper>
        <c-CRow>
          <c-CButton @click="active = Math.max(0, active - 1)">Previous</c-CButton>
          <c-CButton @click="active = Math.min(2, active + 1)">Next</c-CButton>
        </c-CRow>
      </section>
    """


preview = ControlledStepper()
preview  # noqa: B018
````


## Compare orientation, size, and variant


### Compare Stepper presentation

[Open the rendered preview](/v/0.4.4/ui-library/components/stepper/_previews/presentation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class StepperPresentation(Component):
    template = """
      <c-CCol>
        <c-CStepper label="Small plain" size="sm">
          <c-CStep>Start</c-CStep><c-CStep>Finish</c-CStep>
        </c-CStepper>
        <c-CStepper label="Medium soft" variant="soft" c-active="1">
          <c-CStep>Start</c-CStep><c-CStep>Finish</c-CStep>
        </c-CStepper>
        <c-CStepper label="Large vertical outline" orientation="vertical" variant="outline" size="lg">
          <c-CStep>Start</c-CStep><c-CStep>Finish</c-CStep>
        </c-CStepper>
      </c-CCol>
    """


preview = StepperPresentation()
preview  # noqa: B018
````


## Customize Stepper

Public variables and part selectors work from an ancestor or the Stepper root.


### Customize Stepper

[Open the rendered preview](/v/0.4.4/ui-library/components/stepper/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedStepper(Component):
    css = """
      .orchid-stepper {
        --cui-stepper-active-color: #7f56d9;
        --cui-stepper-complete-color: #039855;
        --cui-stepper-radius: 1.25rem;
      }
      .orchid-stepper [data-citry-ui-part="label"] { letter-spacing: 0.02em; }
    """
    template = """
      <c-CStepper label="Orchid order" c-active="1" variant="outline" class_="orchid-stepper">
        <c-CStep>Choose</c-CStep><c-CStep>Prepare</c-CStep><c-CStep>Deliver</c-CStep>
      </c-CStepper>
    """


preview = CustomizedStepper()
preview  # noqa: B018
````


## Accessibility and behavior

The root is a named navigation landmark with an ordered list. The current
Step uses `aria-current="step"`. Interactive Steps are ordinary
`button type="button"` controls, so Tab, Enter, Space, focus, disabledness, and
form safety remain native. Stepper does not implement a composite Arrow-key
model and does not render workflow panels.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CStepper server inputs

Server inputs are passed in a template through `<c-CStepper ... />` or in Python through
`CStepper(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="stepper-input-cstepper-server-inputs-label"></span>`label` | `str` | required | Supplies the accessible navigation landmark name. |
| <span id="stepper-input-cstepper-server-inputs-active"></span>`active` | `int` | `0` | Sets the zero-based initial active Step. |
| <span id="stepper-input-cstepper-server-inputs-interactive"></span>`interactive` | `bool` | `False` | Structurally renders eligible Step triggers as native Buttons. |
| <span id="stepper-input-cstepper-server-inputs-linear"></span>`linear` | `bool` | `True` | Makes upcoming interactive Steps unavailable. |
| <span id="stepper-input-cstepper-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables every interactive Step. |
| <span id="stepper-input-cstepper-server-inputs-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CStepperOrientation`](#stepper-interface-cstepper-orientation)) | `"horizontal"` | Selects logical Step layout. |
| <span id="stepper-input-cstepper-server-inputs-variant"></span>`variant` | `"plain" | "soft" | "outline"` ([`CStepperVariant`](#stepper-interface-cstepper-variant)) | `"plain"` | Selects surface treatment. |
| <span id="stepper-input-cstepper-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CStepperSize`](#stepper-interface-cstepper-size)) | `"md"` | Selects indicator and spacing geometry. |
| <span id="stepper-input-cstepper-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#stepper-interface-cstepper-class-value)) | `None` | Adds root classes. |
| <span id="stepper-input-cstepper-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#stepper-interface-cstepper-style-value)) | `None` | Adds root inline styles. |
| <span id="stepper-input-cstepper-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted root attributes without replacing owned semantics state visibility children or runtime. |

</div>

#### CStepper client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CStepper />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="stepper-input-cstepper-client-inputs-active"></span>`active` | `int | null` | Uses uncontrolled committed state. | Controls the zero-based active Step; null releases control. |
| <span id="stepper-input-cstepper-client-inputs-linear"></span>`linear` | `bool` | Uses the server value. | Reactively limits navigation to current and completed Steps. |
| <span id="stepper-input-cstepper-client-inputs-disabled"></span>`disabled` | `bool` | Uses the server value. | Reactively disables interactive Steps. |
| <span id="stepper-input-cstepper-client-inputs-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CStepperOrientation`](#stepper-interface-cstepper-orientation)) | Uses the server value. | Reactively changes logical layout. |
| <span id="stepper-input-cstepper-client-inputs-variant"></span>`variant` | `"plain" | "soft" | "outline"` ([`CStepperVariant`](#stepper-interface-cstepper-variant)) | Uses the server value. | Reactively changes surface treatment. |
| <span id="stepper-input-cstepper-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CStepperSize`](#stepper-interface-cstepper-size)) | Uses the server value. | Reactively changes geometry. |
| <span id="stepper-input-cstepper-client-inputs-on-active-change"></span>`onActiveChange` | `((active: number, detail: CStepperActiveChangeDetail) => void) | undefined` | No component callback runs. | Receives eligible different Step navigation requests. |

</div>

#### CStep server inputs

Server inputs are passed in a template through `<c-CStep ... />` or in Python through
`CStep(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="stepper-input-cstep-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Makes this Step unavailable when interactive. |
| <span id="stepper-input-cstep-server-inputs-optional"></span>`optional` | `bool` | `False` | Reflects optional workflow metadata. |
| <span id="stepper-input-cstep-server-inputs-error"></span>`error` | `bool` | `False` | Reflects an application-owned error state. |
| <span id="stepper-input-cstep-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#stepper-interface-cstepper-class-value)) | `None` | Adds classes to the concrete Step list item. |
| <span id="stepper-input-cstep-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#stepper-interface-cstepper-style-value)) | `None` | Adds inline styles to the concrete Step list item. |
| <span id="stepper-input-cstep-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted list-item attributes without replacing owned identity state or trigger behavior. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CStepper slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="stepper-slot-cstepper-slots-default"></span>`default` | yes | `{}` ([`CStepperDefaultSlotData`](#stepper-interface-cstepper-default-slot-data)) | None. Requires at least two direct CStep declarations. |

</div>

#### CStep slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="stepper-slot-cstep-slots-default"></span>`default` | yes | `{index, state, is_current, is_disabled}` ([`CStepDefaultSlotData`](#stepper-interface-cstep-default-slot-data)) | None. Supplies the Step label. |
| <span id="stepper-slot-cstep-slots-description"></span>`description` | no | `{index, state, is_current, is_disabled}` ([`CStepDescriptionSlotData`](#stepper-interface-cstep-description-slot-data)) | Omitted. |
| <span id="stepper-slot-cstep-slots-indicator"></span>`indicator` | no | `{index, state, is_current, is_disabled}` ([`CStepIndicatorSlotData`](#stepper-interface-cstep-indicator-slot-data)) | One-based ASCII Step number. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CStepper events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="stepper-event-cstepper-events-on-active-change"></span>`onActiveChange` | `(active: number, detail: CStepperActiveChangeDetail) => void` ([`CStepperActiveChangeDetail`](#stepper-interface-cstepper-active-change-detail)) | Eligible different Step activation. | `{active, previousActive, controlled, step, sourceEvent}` ([`CStepperActiveChangeDetail`](#stepper-interface-cstepper-active-change-detail)) | Requests navigation before an uncontrolled commit or controlled reconciliation. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CStepper CSS variables

Apply these variables to `CStepper` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="stepper-css-cstepper-css-variables-cui-stepper-gap"></span>`--cui-stepper-gap` | `length` | Gap between Steps. | `sm: 0.5rem; md: 0.75rem; lg: 1rem` |
| <span id="stepper-css-cstepper-css-variables-cui-stepper-indicator-size"></span>`--cui-stepper-indicator-size` | `length` | Indicator inline and block size. | `sm: 1.625rem; md: 2rem; lg: 2.5rem` |
| <span id="stepper-css-cstepper-css-variables-cui-stepper-trigger-gap"></span>`--cui-stepper-trigger-gap` | `length` | Gap between indicator and copy. | `0.625rem` |
| <span id="stepper-css-cstepper-css-variables-cui-stepper-radius"></span>`--cui-stepper-radius` | `length` | Root and trigger corner radius input. | `0.75rem` |
| <span id="stepper-css-cstepper-css-variables-cui-stepper-active-color"></span>`--cui-stepper-active-color` | `color` | Current indicator color. | `light #175cd3; dark #93c5fd` |
| <span id="stepper-css-cstepper-css-variables-cui-stepper-complete-color"></span>`--cui-stepper-complete-color` | `color` | Completed indicator color. | `light #067647; dark #6ce9a6` |
| <span id="stepper-css-cstepper-css-variables-cui-stepper-muted-color"></span>`--cui-stepper-muted-color` | `color` | Upcoming indicator and description color. | `light #667085; dark #a4a7ae` |
| <span id="stepper-css-cstepper-css-variables-cui-stepper-background"></span>`--cui-stepper-background` | `color` | Root background. | `plain and outline transparent; soft subtle CanvasText mix` |
| <span id="stepper-css-cstepper-css-variables-cui-stepper-border-color"></span>`--cui-stepper-border-color` | `color` | Outline indicator and separator color. | `light #d0d5dd; dark #535862` |
| <span id="stepper-css-cstepper-css-variables-cui-stepper-focus-color"></span>`--cui-stepper-focus-color` | `color` | Interactive trigger focus outline. | `Highlight` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CStepper attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="stepper-attribute-cstepper-attributes-aria-label"></span>`aria-label` | Root nav | `string` | Names the workflow navigation landmark. |
| <span id="stepper-attribute-cstepper-attributes-data-active"></span>`data-active` | Root nav | `nonnegative-integer-string` | Mirrors effective active index. |
| <span id="stepper-attribute-cstepper-attributes-data-orientation"></span>`data-orientation` | Root nav | `horizontal | vertical` | Mirrors effective layout. |
| <span id="stepper-attribute-cstepper-attributes-data-interactive"></span>`data-interactive` | Root nav | `present-or-absent` | Present when Steps render native Button triggers. |
| <span id="stepper-attribute-cstepper-attributes-data-linear"></span>`data-linear` | Root nav | `present-or-absent` | Present when upcoming Steps are unavailable. |
| <span id="stepper-attribute-cstepper-attributes-data-variant"></span>`data-variant` | Root nav | `plain | soft | outline` | Mirrors effective surface treatment. |
| <span id="stepper-attribute-cstepper-attributes-data-size"></span>`data-size` | Root nav | `sm | md | lg` | Mirrors effective geometry. |
| <span id="stepper-attribute-cstepper-attributes-data-index"></span>`data-index` | Step li | `nonnegative-integer-string` | Exposes zero-based settled order. |
| <span id="stepper-attribute-cstepper-attributes-data-state"></span>`data-state` | Step li | `complete | current | upcoming` | Mirrors derived status. |
| <span id="stepper-attribute-cstepper-attributes-aria-current"></span>`aria-current` | Current trigger | `step` | Identifies the current workflow Step. |
| <span id="stepper-attribute-cstepper-attributes-data-disabled"></span>`data-disabled` | Root or Step | `present-or-absent` | Reflects effective component or Step unavailability. |
| <span id="stepper-attribute-cstepper-attributes-data-optional"></span>`data-optional` | Step li | `present-or-absent` | Reflects optional metadata. |
| <span id="stepper-attribute-cstepper-attributes-data-error"></span>`data-error` | Step li | `present-or-absent` | Reflects error metadata. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CStepper selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="stepper-selector-cstepper-selectors-part-stepper"></span>`[data-citry-ui-part="stepper"]` | Root nav | Stable root and attrs destination. |
| <span id="stepper-selector-cstepper-selectors-part-list"></span>`[data-citry-ui-part="list"]` | Ordered list | Stable Step collection. |
| <span id="stepper-selector-cstepper-selectors-part-step"></span>`[data-citry-ui-part="step"]` | Step list item | Stable declaration attrs destination and state surface. |
| <span id="stepper-selector-cstepper-selectors-part-trigger"></span>`[data-citry-ui-part="trigger"]` | Button or span | Stable interactive or static Step surface. |
| <span id="stepper-selector-cstepper-selectors-part-indicator"></span>`[data-citry-ui-part="indicator"]` | Decorative span | Stable Step marker. |
| <span id="stepper-selector-cstepper-selectors-part-copy"></span>`[data-citry-ui-part="copy"]` | Copy wrapper span | Stable label and description wrapper. |
| <span id="stepper-selector-cstepper-selectors-part-label"></span>`[data-citry-ui-part="label"]` | Label span | Stable accessible label content. |
| <span id="stepper-selector-cstepper-selectors-part-description"></span>`[data-citry-ui-part="description"]` | Optional description span | Stable described-by target. |
| <span id="stepper-selector-cstepper-selectors-part-separator"></span>`[data-citry-ui-part="separator"]` | Decorative span | Stable connector. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="stepper-interface-cstepper-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="stepper-interface-cstepper-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |
| <span id="stepper-interface-cstepper-orientation"></span>`CStepperOrientation` | `Literal["horizontal", "vertical"]` |
| <span id="stepper-interface-cstepper-variant"></span>`CStepperVariant` | `Literal["plain", "soft", "outline"]` |
| <span id="stepper-interface-cstepper-size"></span>`CStepperSize` | `Literal["sm", "md", "lg"]` |
| <span id="stepper-interface-cstep-state"></span>`CStepState` | `Literal["complete", "current", "upcoming"]` |
| <span id="stepper-interface-cstep-description-slot-data"></span>`CStepDescriptionSlotData` | `CStepDefaultSlotData` |
| <span id="stepper-interface-cstep-indicator-slot-data"></span>`CStepIndicatorSlotData` | `CStepDefaultSlotData` |

</div>

<span id="stepper-interface-cstepper-default-slot-data"></span>

#### `CStepperDefaultSlotData`

Empty dataclass: `{}`.

<span id="stepper-interface-cstep-default-slot-data"></span>

#### `CStepDefaultSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="stepper-interface-cstep-default-slot-data-index"></span>`index` | `int` | - | Zero-based settled Step index. |
| <span id="stepper-interface-cstep-default-slot-data-state"></span>`state` | `"complete" | "current" | "upcoming"` ([`CStepState`](#stepper-interface-cstep-state)) | - | Server-rendered status. |
| <span id="stepper-interface-cstep-default-slot-data-is-current"></span>`is_current` | `bool` | - | Whether this Step is initially current. |
| <span id="stepper-interface-cstep-default-slot-data-is-disabled"></span>`is_disabled` | `bool` | - | Whether this Step is initially unavailable. |

</div>

<span id="stepper-interface-cstepper-active-change-detail"></span>

#### `CStepperActiveChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="stepper-interface-cstepper-active-change-detail-active"></span>`active` | `int` | - | Requested zero-based index. |
| <span id="stepper-interface-cstepper-active-change-detail-previous-active"></span>`previousActive` | `int` | - | Prior effective index. |
| <span id="stepper-interface-cstepper-active-change-detail-controlled"></span>`controlled` | `bool` | - | Whether a client active value currently controls state. |
| <span id="stepper-interface-cstepper-active-change-detail-step"></span>`step` | `HTMLElement` | - | Activated Step list item. |
| <span id="stepper-interface-cstepper-active-change-detail-source-event"></span>`sourceEvent` | `Event` | - | Native click event. |

</div>

### Translation keys

-