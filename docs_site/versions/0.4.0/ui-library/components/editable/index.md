---
title: Editable
url: https://citry.dev/v/0.4.0/ui-library/components/editable/
description: "Edit one short text value in place without giving up native form behavior."
---
# Editable

Use `CEditable` for compact names, titles, and labels that are usually read and
occasionally changed. It keeps one native Input as form and validity truth.

## Editable at a glance


### Editable at a glance

[Open the rendered preview](/v/0.4.0/ui-library/components/editable/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditableAtAGlance(Component):
    template = """
      <c-CField>
        <c-fill name="label">Project name</c-fill>
        <c-fill name="description">Use the pencil to rename this project in place.</c-fill>
        <c-fill name="default">
          <c-CEditable value="Aurora atlas" name="project-name" />
        </c-fill>
      </c-CField>
    """


preview = EditableAtAGlance()
preview  # noqa: B018
````


## Submit and reset a value


### Use Editable in a form

[Open the rendered preview](/v/0.4.0/ui-library/components/editable/_previews/forms/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditableForm(Component):
    template = """
      <form x-data @submit.prevent="result = Object.fromEntries(new FormData($event.target))">
        <c-CField required>
          <c-fill name="label">Workspace title</c-fill>
          <c-fill name="default">
            <c-CEditable value="Field notes" name="title" />
          </c-fill>
        </c-CField>
        <c-CButton type="submit">Save form</c-CButton>
        <c-CButton type="reset" variant="ghost">Reset</c-CButton>
        <output x-text="JSON.stringify(result)"></output>
      </form>
    """


preview = EditableForm()
preview  # noqa: B018
````


## Control the committed value


### Control Editable

[Open the rendered preview](/v/0.4.0/ui-library/components/editable/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledEditable(Component):
    template = """
      <div x-data>
        <c-CEditable
          value="Atlas"
          $c-props="{
            value:$store.editableExample.value,
            onValueChange:(next) => $store.editableExample.value = next,
          }"
        />
        <p>Committed: <strong x-text="$store.editableExample.value"></strong></p>
      </div>
    """
    js = "Alpine.store('editableExample', {value:'Atlas'});"


preview = ControlledEditable()
preview  # noqa: B018
````


## Choose when editing commits

The default `both` mode commits with Enter or when focus leaves the whole
component. `enter`, `blur`, and `explicit` narrow that behavior.


### Editable submit modes

[Open the rendered preview](/v/0.4.0/ui-library/components/editable/_previews/submit-modes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditableSubmitModes(Component):
    template = """
      <c-CStack>
        <c-CEditable value="Enter or blur" submit_mode="both" c-input_attrs="{'aria-label':'Both'}" />
        <c-CEditable value="Enter only" submit_mode="enter" c-input_attrs="{'aria-label':'Enter only'}" />
        <c-CEditable value="Blur only" submit_mode="blur" c-input_attrs="{'aria-label':'Blur only'}" />
        <c-CEditable value="Buttons only" submit_mode="explicit" c-input_attrs="{'aria-label':'Explicit'}" />
      </c-CStack>
    """


preview = EditableSubmitModes()
preview  # noqa: B018
````


## Place edit actions

Pencil, confirm, and cancel actions sit inside the Input at inline-end by
default. Use `action_position="outside"` when they need independent space.


### Place Editable actions

[Open the rendered preview](/v/0.4.0/ui-library/components/editable/_previews/action-positions/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditableActionPositions(Component):
    template = """
      <c-CStack>
        <c-CEditable value="Actions inside by default" editing c-input_attrs="{'aria-label':'Inside actions'}" />
        <c-CEditable
          value="Actions beside the input" editing action_position="outside"
          c-input_attrs="{'aria-label':'Outside actions'}"
        />
      </c-CStack>
    """


preview = EditableActionPositions()
preview  # noqa: B018
````


## States, variants, and sizes


### Editable states

[Open the rendered preview](/v/0.4.0/ui-library/components/editable/_previews/states/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditableStates(Component):
    template = """
      <c-CStack>
        <c-CEditable value="Available" c-input_attrs="{'aria-label':'Available title'}" />
        <c-CEditable value="Read only" readonly c-input_attrs="{'aria-label':'Read-only title'}" />
        <c-CEditable value="Disabled" disabled c-input_attrs="{'aria-label':'Disabled title'}" />
        <c-CEditable value="Needs review" invalid c-input_attrs="{'aria-label':'Invalid title'}" />
        <c-CEditable placeholder="Empty value" c-input_attrs="{'aria-label':'Empty title'}" />
      </c-CStack>
    """


preview = EditableStates()
preview  # noqa: B018
````



### Editable variants and sizes

[Open the rendered preview](/v/0.4.0/ui-library/components/editable/_previews/variants/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditableVariants(Component):
    template = """
      <c-CStack>
        <c-CEditable value="Small outline" variant="outline" size="sm" />
        <c-CEditable value="Medium filled" variant="filled" />
        <c-CEditable value="Large plain" variant="plain" size="lg" />
      </c-CStack>
    """


preview = EditableVariants()
preview  # noqa: B018
````


## Keyboard behavior

The edit Button enters edit mode. Enter commits when enabled by `submit_mode`,
Escape cancels, and Tab follows ordinary page order. Blur modes commit only
after focus leaves the Input and both edit actions.


### Edit with the keyboard

[Open the rendered preview](/v/0.4.0/ui-library/components/editable/_previews/keyboard/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditableKeyboard(Component):
    template = """
      <c-CStack>
        <p>Tab to Edit, press Enter to edit, then Enter to save or Escape to cancel.</p>
        <c-CEditable value="Keyboard friendly" />
        <c-CButton variant="outline">Next focus target</c-CButton>
      </c-CStack>
    """


preview = EditableKeyboard()
preview  # noqa: B018
````


## Customize Editable


### Customize Editable

[Open the rendered preview](/v/0.4.0/ui-library/components/editable/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedEditable(Component):
    template = """
      <c-CEditable
        value="Branded title" editing
        style="--cui-editable-background:#fff8eb; --cui-editable-border-color:#f79009;
               --cui-editable-focus-color:#b54708; --cui-editable-radius:1rem"
        c-input_attrs="{'aria-label':'Branded title'}"
      />
    """


preview = CustomizedEditable()
preview  # noqa: B018
````


## Accessibility and forms

View mode exposes ordinary text and a named edit Button. Edit mode exposes one
native text Input plus named confirm and cancel Buttons. The Input stays the
successful form control in both modes and owns required validity and reset.
Before client initialization the native Input is the visible fallback.

Use `CInput` for a value that is primarily edited, and `CTextarea` for
multiline content.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CEditable server inputs

Server inputs are passed in a template through `<c-CEditable ... />` or in Python through
`CEditable(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 9rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="editable-input-ceditable-server-inputs-value"></span>`value` | `str` | `""` | Sets the initial committed and native form value. |
| <span id="editable-input-ceditable-server-inputs-placeholder"></span>`placeholder` | `str` | `"Click to edit"` | Supplies author-localized empty preview and Input text. |
| <span id="editable-input-ceditable-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the native form field name. |
| <span id="editable-input-ceditable-server-inputs-form"></span>`form` | `str | None` | `None` | Associates the native Input with a Form ID. |
| <span id="editable-input-ceditable-server-inputs-id"></span>`id` | `str | None` | `None` | Sets native Input identity. |
| <span id="editable-input-ceditable-server-inputs-editing"></span>`editing` | `bool` | `False` | Sets initial edit mode. |
| <span id="editable-input-ceditable-server-inputs-required"></span>`required` | `bool | None` | `None` | Enables native required validity outside Field. |
| <span id="editable-input-ceditable-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Disables editing and form contribution. |
| <span id="editable-input-ceditable-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Preserves submission while preventing editing. |
| <span id="editable-input-ceditable-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Adds owner-supplied invalid presentation. |
| <span id="editable-input-ceditable-server-inputs-max-length"></span>`max_length` | `int | None` | `None` | Sets native maximum length. |
| <span id="editable-input-ceditable-server-inputs-autocomplete"></span>`autocomplete` | `str | None` | `None` | Sets the native autocomplete hint. |
| <span id="editable-input-ceditable-server-inputs-inputmode"></span>`inputmode` | `str | None` | `None` | Sets the native virtual-keyboard hint. |
| <span id="editable-input-ceditable-server-inputs-submit-mode"></span>`submit_mode` | `"enter" | "blur" | "both" | "explicit"` ([`CEditableSubmitMode`](#editable-interface-submit-mode)) | `"both"` | Selects commit triggers. |
| <span id="editable-input-ceditable-server-inputs-select-on-focus"></span>`select_on_focus` | `bool` | `True` | Selects the draft when editing begins. |
| <span id="editable-input-ceditable-server-inputs-action-position"></span>`action_position` | `"inside" | "outside"` ([`CEditableActionPosition`](#editable-interface-action-position)) | `"inside"` | Places edit actions inside the Input at inline-end or outside it. |
| <span id="editable-input-ceditable-server-inputs-edit-label"></span>`edit_label` | `str` | `"Edit"` | Names the pencil Button. |
| <span id="editable-input-ceditable-server-inputs-submit-label"></span>`submit_label` | `str` | `"Save"` | Names the confirm Button. |
| <span id="editable-input-ceditable-server-inputs-cancel-label"></span>`cancel_label` | `str` | `"Cancel"` | Names the cancel Button. |
| <span id="editable-input-ceditable-server-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CEditableVariant`](#editable-interface-variant)) | `"outline"` | Selects surface treatment. |
| <span id="editable-input-ceditable-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CEditableSize`](#editable-interface-size)) | `"md"` | Selects Input and action geometry. |
| <span id="editable-input-ceditable-server-inputs-class"></span>`class_` | `CClassValue | None` | `None` | Adds root classes. |
| <span id="editable-input-ceditable-server-inputs-style"></span>`style` | `CStyleValue | None` | `None` | Adds root inline styles. |
| <span id="editable-input-ceditable-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted nonconflicting root attributes. |
| <span id="editable-input-ceditable-server-inputs-input-attrs"></span>`input_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted native Input attributes and relationships. |
| <span id="editable-input-ceditable-server-inputs-preview-attrs"></span>`preview_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted nonconflicting preview attributes. |

</div>

#### CEditable client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CEditable />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="editable-input-ceditable-client-inputs-value"></span>`value` | `string | null` | Releases control to the committed value. | Controls the committed value while supplied. |
| <span id="editable-input-ceditable-client-inputs-editing"></span>`editing` | `boolean | null` | Releases control to committed edit mode. | Controls view or edit mode while supplied. |
| <span id="editable-input-ceditable-client-inputs-required"></span>`required` | `bool` | Uses the server or Field fallback. | Reactively changes required validity. |
| <span id="editable-input-ceditable-client-inputs-disabled"></span>`disabled` | `bool` | Uses the server or Field fallback. | Reactively disables editing. |
| <span id="editable-input-ceditable-client-inputs-readonly"></span>`readonly` | `bool` | Uses the server or Field fallback. | Reactively prevents editing while preserving submission. |
| <span id="editable-input-ceditable-client-inputs-invalid"></span>`invalid` | `bool` | Uses the server or Field fallback. | Reactively changes invalid presentation. |
| <span id="editable-input-ceditable-client-inputs-submit-mode"></span>`submitMode` | `CEditableSubmitMode` | Uses the server value. | Reactively changes commit triggers. |
| <span id="editable-input-ceditable-client-inputs-select-on-focus"></span>`selectOnFocus` | `bool` | Uses the server value. | Reactively changes entry selection. |
| <span id="editable-input-ceditable-client-inputs-action-position"></span>`actionPosition` | `CEditableActionPosition` | Uses the server value. | Reactively places the actions inside or outside. |
| <span id="editable-input-ceditable-client-inputs-variant"></span>`variant` | `CEditableVariant` | Uses the server value. | Reactively changes treatment. |
| <span id="editable-input-ceditable-client-inputs-size"></span>`size` | `CEditableSize` | Uses the server value. | Reactively changes geometry. |
| <span id="editable-input-ceditable-client-inputs-on-value-change"></span>`onValueChange` | `((value: string, detail: CEditableValueChangeDetail) => void) | undefined` | No component callback runs. | Receives commit and reset requests. |
| <span id="editable-input-ceditable-client-inputs-on-edit-change"></span>`onEditChange` | `((editing: boolean, detail: CEditableEditChangeDetail) => void) | undefined` | No component callback runs. | Receives mode requests and forced closes. |

</div>

### Slots

-

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CEditable events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="editable-event-ceditable-events-value-change"></span>`onValueChange` | `(value: string, detail: CEditableValueChangeDetail) => void` ([`CEditableValueChangeDetail`](#editable-interface-ceditable-value-detail)) | Submit blur or reset request. | `{value, previousValue, controlled, source, sourceEvent}` ([`CEditableValueChangeDetail`](#editable-interface-ceditable-value-detail)) | Commits immediately when uncontrolled and waits for owner acceptance when controlled. |
| <span id="editable-event-ceditable-events-edit-change"></span>`onEditChange` | `(editing: boolean, detail: CEditableEditChangeDetail) => void` ([`CEditableEditChangeDetail`](#editable-interface-ceditable-edit-detail)) | Edit submit cancel blur reset or safety transition. | `{editing, reason, controlled, forced, source}` ([`CEditableEditChangeDetail`](#editable-interface-ceditable-edit-detail)) | Controlled requests notify without changing mode; forced safety transitions always close. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CEditable CSS variables

Apply these variables to `CEditable` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="editable-css-ceditable-css-variables-background"></span>`--cui-editable-background` | `color` | Preview and Input surface. | `Canvas` |
| <span id="editable-css-ceditable-css-variables-foreground"></span>`--cui-editable-foreground` | `color` | Primary text. | `CanvasText` |
| <span id="editable-css-ceditable-css-variables-border-color"></span>`--cui-editable-border-color` | `color` | Surface border. | `scheme-aware border` |
| <span id="editable-css-ceditable-css-variables-hover-border-color"></span>`--cui-editable-hover-border-color` | `color` | Hover border. | `scheme-aware strong border` |
| <span id="editable-css-ceditable-css-variables-focus-color"></span>`--cui-editable-focus-color` | `color` | Focus outline. | `Highlight` |
| <span id="editable-css-ceditable-css-variables-invalid-border-color"></span>`--cui-editable-invalid-border-color` | `color` | Invalid border. | `scheme-aware red` |
| <span id="editable-css-ceditable-css-variables-muted-color"></span>`--cui-editable-muted-color` | `color` | Empty preview foreground. | `scheme-aware muted` |
| <span id="editable-css-ceditable-css-variables-action-background"></span>`--cui-editable-action-background` | `color` | Action Button surface. | `CanvasText mix` |
| <span id="editable-css-ceditable-css-variables-action-foreground"></span>`--cui-editable-action-foreground` | `color` | Action Button foreground. | `CanvasText` |
| <span id="editable-css-ceditable-css-variables-radius"></span>`--cui-editable-radius` | `length` | Surface corners. | `0.5rem` |
| <span id="editable-css-ceditable-css-variables-height"></span>`--cui-editable-height` | `length` | Minimum surface height. | `size-derived` |
| <span id="editable-css-ceditable-css-variables-padding"></span>`--cui-editable-padding` | `length` | Surface padding. | `size-derived` |
| <span id="editable-css-ceditable-css-variables-action-size"></span>`--cui-editable-action-size` | `length` | Action Button square size. | `size-derived` |
| <span id="editable-css-ceditable-css-variables-gap"></span>`--cui-editable-gap` | `length` | Action and outside-layout gap. | `0.375rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CEditable attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="editable-attribute-ceditable-attributes-data-editing"></span>`data-editing` | Root | `present-or-absent` | Mirrors effective edit mode. |
| <span id="editable-attribute-ceditable-attributes-data-empty"></span>`data-empty` | Root | `present-or-absent` | Mirrors an empty committed value. |
| <span id="editable-attribute-ceditable-attributes-data-required"></span>`data-required` | Root | `present-or-absent` | Mirrors required validity. |
| <span id="editable-attribute-ceditable-attributes-data-disabled"></span>`data-disabled` | Root | `present-or-absent` | Mirrors effective disabled state. |
| <span id="editable-attribute-ceditable-attributes-data-readonly"></span>`data-readonly` | Root | `present-or-absent` | Mirrors read-only state. |
| <span id="editable-attribute-ceditable-attributes-data-invalid"></span>`data-invalid` | Root | `present-or-absent` | Mirrors external or native invalid state. |
| <span id="editable-attribute-ceditable-attributes-data-submit-mode"></span>`data-submit-mode` | Root | `CEditableSubmitMode` | Reflects commit behavior. |
| <span id="editable-attribute-ceditable-attributes-data-action-position"></span>`data-action-position` | Root | `CEditableActionPosition` | Reflects action placement. |
| <span id="editable-attribute-ceditable-attributes-data-variant"></span>`data-variant` | Root | `CEditableVariant` | Reflects treatment. |
| <span id="editable-attribute-ceditable-attributes-data-size"></span>`data-size` | Root | `CEditableSize` | Reflects geometry. |
| <span id="editable-attribute-ceditable-attributes-aria-invalid"></span>`aria-invalid` | Native Input | `true or absent` | Mirrors external or native invalid state. |
| <span id="editable-attribute-ceditable-attributes-aria-describedby"></span>`aria-describedby` | Native Input | `IDREF list or absent` | Merges Field and trusted description relationships. |
| <span id="editable-attribute-ceditable-attributes-aria-errormessage"></span>`aria-errormessage` | Native Input | `IDREF list or absent` | Merges active Field and trusted error relationships. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CEditable selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="editable-selector-ceditable-selectors-root"></span>`[data-citry-ui-part="root"]` | Root div | Stable root and state surface. |
| <span id="editable-selector-ceditable-selectors-preview"></span>`[data-citry-ui-part="preview"]` | Preview div | View-mode surface. |
| <span id="editable-selector-ceditable-selectors-preview-value"></span>`[data-citry-ui-part="preview-value"]` | Preview span | Committed or placeholder text. |
| <span id="editable-selector-ceditable-selectors-edit-action"></span>`[data-citry-ui-part="edit-action"]` | Button | Enters edit mode. |
| <span id="editable-selector-ceditable-selectors-edit-surface"></span>`[data-citry-ui-part="edit-surface"]` | Div | Input and edit action layout. |
| <span id="editable-selector-ceditable-selectors-input"></span>`[data-citry-ui-part="input"]` | Native Input | Draft focus form and validity owner. |
| <span id="editable-selector-ceditable-selectors-actions"></span>`[data-citry-ui-part="actions"]` | Span | Confirm and cancel layout. |
| <span id="editable-selector-ceditable-selectors-submit-action"></span>`[data-citry-ui-part="submit-action"]` | Button | Commits the draft. |
| <span id="editable-selector-ceditable-selectors-cancel-action"></span>`[data-citry-ui-part="cancel-action"]` | Button | Discards the draft. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="editable-interface-action-position"></span>`CEditableActionPosition` | `Literal["inside", "outside"]` |
| <span id="editable-interface-submit-mode"></span>`CEditableSubmitMode` | `Literal["enter", "blur", "both", "explicit"]` |
| <span id="editable-interface-variant"></span>`CEditableVariant` | `Literal["outline", "filled", "plain"]` |
| <span id="editable-interface-size"></span>`CEditableSize` | `Literal["sm", "md", "lg"]` |
| <span id="editable-interface-value-source"></span>`CEditableValueSource` | `Literal["submit", "blur", "reset"]` |
| <span id="editable-interface-edit-reason"></span>`CEditableEditReason` | `Literal["edit", "submit", "cancel", "blur", "reset", "disabled", "readonly", "invalid"]` |

</div>

<span id="editable-interface-ceditable-value-detail"></span>

#### `CEditableValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="editable-interface-ceditable-value-detail-value"></span>`value` | `string` | - | Requested value. |
| <span id="editable-interface-ceditable-value-detail-previous-value"></span>`previousValue` | `string` | - | Previous committed value. |
| <span id="editable-interface-ceditable-value-detail-controlled"></span>`controlled` | `bool` | - | Whether client value owns the channel. |
| <span id="editable-interface-ceditable-value-detail-source"></span>`source` | `CEditableValueSource` | - | Commit source. |
| <span id="editable-interface-ceditable-value-detail-source-event"></span>`sourceEvent` | `Event | None` | - | Native source event when present. |

</div>

<span id="editable-interface-ceditable-edit-detail"></span>

#### `CEditableEditChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="editable-interface-ceditable-edit-detail-editing"></span>`editing` | `bool` | - | Requested or forced mode. |
| <span id="editable-interface-ceditable-edit-detail-reason"></span>`reason` | `CEditableEditReason` | - | Mode reason. |
| <span id="editable-interface-ceditable-edit-detail-controlled"></span>`controlled` | `bool` | - | Whether client editing owns the channel. |
| <span id="editable-interface-ceditable-edit-detail-forced"></span>`forced` | `bool` | - | Whether safety made closure nonrejectable. |
| <span id="editable-interface-ceditable-edit-detail-source"></span>`source` | `EventTarget | None` | - | Native source or safety owner. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CEditable translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="editable-translation-ceditable-translations-click-to-edit"></span>`citry-ui-editable-click-to-edit` | Supplies empty preview text and the editor placeholder. | `None` | `placeholder` input | `i18n.bind()` updates every stateful destination. |
| <span id="editable-translation-ceditable-translations-edit"></span>`citry-ui-editable-edit` | Names the edit control. | `None` | `edit_label` input | $c-tr updates `aria-label`. |
| <span id="editable-translation-ceditable-translations-save"></span>`citry-ui-editable-save` | Names the save control. | `None` | `submit_label` input | $c-tr updates `aria-label`. |
| <span id="editable-translation-ceditable-translations-cancel"></span>`citry-ui-editable-cancel` | Names the cancel control. | `None` | `cancel_label` input | $c-tr updates `aria-label`. |

</div>