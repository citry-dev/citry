---
title: AlertDialog
url: https://citry.dev/v/0.4.6/ui-library/components/alert-dialog/
description: "Ask for an immediate cancel-or-action decision in an urgent modal prompt."
---
# AlertDialog

Use `CAlertDialog` when a consequential action needs an immediate explicit
decision. It requires a visible title, concise description, Cancel control,
and Action control. Use `CAlert` for persistent feedback and `CDialog` for
general modal content, forms, or more than two decisions.


### AlertDialog at a glance

[Open the rendered preview](/v/0.4.6/ui-library/components/alert-dialog/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertDialogGlance(Component):
    template = """
      <c-CAlertDialog id="glance-delete">
        <c-fill name="activator" data="{activator_attrs}">
          <c-CButton c-attrs="activator_attrs" intent="danger">Delete project</c-CButton>
        </c-fill>
        <c-fill name="title">Delete this project?</c-fill>
        <c-fill name="description">This permanently removes all project data.</c-fill>
        <c-fill name="cancel" data="{cancel_attrs}">
          <c-CButton c-attrs="cancel_attrs" variant="outline">Keep project</c-CButton>
        </c-fill>
        <c-fill name="action" data="{action_attrs}">
          <c-CButton c-attrs="action_attrs" intent="danger">Delete</c-CButton>
        </c-fill>
      </c-CAlertDialog>
    """


preview = AlertDialogGlance()
preview  # noqa: B018
````



```citry-html
<c-CAlertDialog id="delete-project">
  <c-fill name="activator" data="{activator_attrs}">
    <c-CButton c-attrs="activator_attrs" intent="danger">Delete project</c-CButton>
  </c-fill>
  <c-fill name="title">Delete this project?</c-fill>
  <c-fill name="description">This permanently removes all project data.</c-fill>
  <c-fill name="cancel" data="{cancel_attrs}">
    <c-CButton c-attrs="cancel_attrs" variant="outline">Keep project</c-CButton>
  </c-fill>
  <c-fill name="action" data="{action_attrs}">
    <c-CButton c-attrs="action_attrs" intent="danger">Delete</c-CButton>
  </c-fill>
</c-CAlertDialog>
```


## Choose the right interruption

AlertDialog is intentionally narrow. The native surface has
`role="alertdialog"`, a required name and description, and exactly two owned
decision regions. Outside presses never close it. Escape acts like Cancel when
`close_on_escape=True`.


### Acknowledge a blocking error

[Open the rendered preview](/v/0.4.6/ui-library/components/alert-dialog/_previews/blocking-error/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BlockingError(Component):
    template = """
      <c-CAlertDialog id="sync-error" size="md">
        <c-fill name="activator" data="{activator_attrs}">
          <c-CButton c-attrs="activator_attrs" variant="outline">Show sync error</c-CButton>
        </c-fill>
        <c-fill name="title">Changes could not be synchronized</c-fill>
        <c-fill name="description">
          Reconnect before continuing so this draft is not overwritten.
        </c-fill>
        <c-fill name="default">
          Your local draft remains available in this browser.
        </c-fill>
        <c-fill name="cancel" data="{cancel_attrs}">
          <c-CButton c-attrs="cancel_attrs" variant="outline">Review draft</c-CButton>
        </c-fill>
        <c-fill name="action" data="{action_attrs}">
          <c-CButton c-attrs="action_attrs">Retry connection</c-CButton>
        </c-fill>
      </c-CAlertDialog>
    """


preview = BlockingError()
preview  # noqa: B018
````


## Control asynchronous decisions

A supplied client `open` Boolean is authoritative. `onOpenChange` requests the
next state; accept it when application work is ready. Cancel and Action both
use `reason="action"`; inspect `detail.returnValue` for `"cancel"` or
`"action"`.


### Control an asynchronous decision

[Open the rendered preview](/v/0.4.6/ui-library/components/alert-dialog/_previews/controlled-action/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledArchive(Component):
    template = """
      <section x-data="{open: false, pending: false, result: 'No decision yet'}">
        <c-CAlertDialog
          id="archive-record"
          $c-props="{
            open,
            onOpenChange: (next, detail) => {
              if (detail.returnValue === 'action') {
                pending = true;
                result = 'Archiving...';
                setTimeout(() => {
                  pending = false;
                  open = false;
                  result = 'Record archived';
                }, 500);
              } else {
                open = next;
                if (!next) result = 'Archive cancelled';
              }
            }
          }"
        >
          <c-fill name="activator" data="{activator_attrs}">
            <c-CButton c-attrs="activator_attrs">Archive record</c-CButton>
          </c-fill>
          <c-fill name="title">Archive this record?</c-fill>
          <c-fill name="description">It will leave the active workspace.</c-fill>
          <c-fill name="cancel" data="{cancel_attrs}">
            <c-CButton c-attrs="cancel_attrs" variant="outline" $c-props="{disabled: pending}">Cancel</c-CButton>
          </c-fill>
          <c-fill name="action" data="{action_attrs}">
            <c-CButton c-attrs="action_attrs" $c-props="{loading: pending}">Archive</c-CButton>
          </c-fill>
        </c-CAlertDialog>
        <p aria-live="polite" x-text="result"></p>
      </section>
    """


preview = ControlledArchive()
preview  # noqa: B018
````



```citry-html
<c-CAlertDialog
  $c-props="{
    open: confirming,
    onOpenChange: (open, detail) => {
      if (detail.returnValue === 'action') archiveThenClose()
      else confirming = open
    }
  }"
>
  ...
</c-CAlertDialog>
```


Omit or supply `null` for the client `open` prop to release control while
preserving the effective state.

## Compose native Buttons safely

`CButton` already owns `type="button"`; pass only `*_attrs` to it. A native
Button must consume both the attribute mapping and adjacent type field.


### Use native decision Buttons

[Open the rendered preview](/v/0.4.6/ui-library/components/alert-dialog/_previews/native-buttons/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NativeAlertButtons(Component):
    template = """
      <c-CAlertDialog id="leave-editor">
        <c-fill name="activator" data="{activator_attrs, activator_type}">
          <button c-type="activator_type" c-bind="activator_attrs">Leave editor</button>
        </c-fill>
        <c-fill name="title">Leave the editor?</c-fill>
        <c-fill name="description">Changes since the last save will be lost.</c-fill>
        <c-fill name="cancel" data="{cancel_attrs, cancel_type}">
          <button c-type="cancel_type" c-bind="cancel_attrs">Stay</button>
        </c-fill>
        <c-fill name="action" data="{action_attrs, action_type}">
          <button c-type="action_type" c-bind="action_attrs">Leave</button>
        </c-fill>
      </c-CAlertDialog>
    """


preview = NativeAlertButtons()
preview  # noqa: B018
````



```citry-html
<c-fill name="cancel" data="{cancel_attrs, cancel_type}">
  <button c-type="cancel_type" c-bind="cancel_attrs">Stay</button>
</c-fill>
```


Native click handlers run before the component open-change request. This lets
the application perform or schedule domain work without a duplicate custom
confirm event.

## Focus and accessibility

Cancel receives initial focus so the destructive choice is never the default.
Tab and Shift+Tab remain inside the modal. Closing restores the connected
activator unless application code deliberately moved focus elsewhere. The
required title and description become the exact `aria-labelledby` and
`aria-describedby` targets.

## Size and customization

Sizes are `sm`, `md`, and `lg`; `sm` is the default. Full-screen workflows
belong to Dialog. AlertDialog shares Dialog layout behavior while exposing
family-specific variables.


### Compare AlertDialog sizes

[Open the rendered preview](/v/0.4.6/ui-library/components/alert-dialog/_previews/sizes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertDialogSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CRow gap="md" wrap>
        <c-for each="size in sizes">
          <c-CAlertDialog c-size="size">
            <c-fill name="activator" data="{activator_attrs}">
              <c-CButton c-attrs="activator_attrs" variant="outline">Open {{ size }}</c-CButton>
            </c-fill>
            <c-fill name="title">{{ size }} decision surface</c-fill>
            <c-fill name="description">Compare the responsive width for this size.</c-fill>
            <c-fill name="cancel" data="{cancel_attrs}">
              <c-CButton c-attrs="cancel_attrs" variant="outline">Cancel</c-CButton>
            </c-fill>
            <c-fill name="action" data="{action_attrs}">
              <c-CButton c-attrs="action_attrs">Continue</c-CButton>
            </c-fill>
          </c-CAlertDialog>
        </c-for>
      </c-CRow>
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {"sizes": ("sm", "md", "lg")}


preview = AlertDialogSizes()
preview  # noqa: B018
````



### Customize AlertDialog

[Open the rendered preview](/v/0.4.6/ui-library/components/alert-dialog/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedAlertDialog(Component):
    template = """
      <c-CAlertDialog
        id="custom-archive"
        class_="archive-alert"
        c-style="{
          '--cui-alert-dialog-radius': '1.25rem',
          '--cui-alert-dialog-inline-size': '30rem',
          '--cui-alert-dialog-border-color': '#8b5cf6'
        }"
      >
        <c-fill name="activator" data="{activator_attrs}">
          <c-CButton c-attrs="activator_attrs" variant="outline">Archive workspace</c-CButton>
        </c-fill>
        <c-fill name="title">Archive this workspace?</c-fill>
        <c-fill name="description">Collaborators will lose active access.</c-fill>
        <c-fill name="cancel" data="{cancel_attrs}">
          <c-CButton c-attrs="cancel_attrs" variant="outline">Keep active</c-CButton>
        </c-fill>
        <c-fill name="action" data="{action_attrs}">
          <c-CButton c-attrs="action_attrs">Archive</c-CButton>
        </c-fill>
      </c-CAlertDialog>
    """


preview = CustomizedAlertDialog()
preview  # noqa: B018
````



```css
.archive-alert {
  --cui-alert-dialog-radius: 1.25rem;
  --cui-alert-dialog-inline-size: 30rem;
  --cui-alert-dialog-border-color: #8b5cf6;
}
```


See [`api.yml`](api.yml) for the exhaustive inputs, callbacks, variables,
attributes, selectors, slots, and public interfaces.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CAlertDialog server inputs

Server inputs are passed in a template through `<c-CAlertDialog ... />` or in Python through
`CAlertDialog(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="alert-dialog-input-calert-dialog-server-inputs-id"></span>`id` | `str | None` | generated | Sets native Dialog identity and title, description, and activator relationships. |
| <span id="alert-dialog-input-calert-dialog-server-inputs-open"></span>`open` | `bool` | `False` | Sets the server-visible initial modal state. |
| <span id="alert-dialog-input-calert-dialog-server-inputs-close-on-escape"></span>`close_on_escape` | `bool` | `True` | Permits Escape and platform cancel requests. |
| <span id="alert-dialog-input-calert-dialog-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CAlertDialogSize`](#alert-dialog-interface-size)) | `"sm"` | Sets bounded decision-surface width. |
| <span id="alert-dialog-input-calert-dialog-server-inputs-scroll"></span>`scroll` | `"body" | "dialog"` ([`CAlertDialogScroll`](#alert-dialog-interface-scroll)) | `"body"` | Chooses the overflow owner. |
| <span id="alert-dialog-input-calert-dialog-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#alert-dialog-interface-class-value)) | `None` | Adds native Dialog classes. |
| <span id="alert-dialog-input-calert-dialog-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#alert-dialog-interface-style-value)) | `None` | Adds native Dialog inline styles. |
| <span id="alert-dialog-input-calert-dialog-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted native Dialog attributes without replacing owned modal semantics. |

</div>

#### CAlertDialog client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CAlertDialog />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="alert-dialog-input-calert-dialog-client-inputs-open"></span>`open` | `boolean | null | undefined` | Releases control and preserves effective state. | Controls modal visibility while supplied as a Boolean. |
| <span id="alert-dialog-input-calert-dialog-client-inputs-close-on-escape"></span>`closeOnEscape` | `boolean | undefined` | Uses the server fallback. | Controls Escape and platform cancel behavior. |
| <span id="alert-dialog-input-calert-dialog-client-inputs-size"></span>`size` | `"sm" | "md" | "lg" | undefined` | Uses the server fallback. | Controls `data-size` and width. |
| <span id="alert-dialog-input-calert-dialog-client-inputs-scroll"></span>`scroll` | `"body" | "dialog" | undefined` | Uses the server fallback. | Controls `data-scroll` and overflow. |
| <span id="alert-dialog-input-calert-dialog-client-inputs-on-open-change"></span>`onOpenChange` | `((open, detail) => void) | undefined` | No component callback. | Receives trigger, Escape, action, and native close requests. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CAlertDialog slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="alert-dialog-slot-calert-dialog-slots-activator"></span>`activator` | no | `{activator_attrs, activator_type}` ([`CAlertDialogActivatorSlotData`](#alert-dialog-interface-activator-slot)) | No activator. |
| <span id="alert-dialog-slot-calert-dialog-slots-title"></span>`title` | yes | `{}` ([`CAlertDialogTitleSlotData`](#alert-dialog-interface-title-slot)) | none |
| <span id="alert-dialog-slot-calert-dialog-slots-description"></span>`description` | yes | `{}` ([`CAlertDialogDescriptionSlotData`](#alert-dialog-interface-description-slot)) | none |
| <span id="alert-dialog-slot-calert-dialog-slots-default"></span>`default` | no | `{}` ([`CAlertDialogDefaultSlotData`](#alert-dialog-interface-default-slot)) | Supplemental body omitted. |
| <span id="alert-dialog-slot-calert-dialog-slots-cancel"></span>`cancel` | yes | `{cancel_attrs, cancel_type}` ([`CAlertDialogCancelSlotData`](#alert-dialog-interface-cancel-slot)) | none |
| <span id="alert-dialog-slot-calert-dialog-slots-action"></span>`action` | yes | `{action_attrs, action_type}` ([`CAlertDialogActionSlotData`](#alert-dialog-interface-action-slot)) | none |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CAlertDialog events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="alert-dialog-event-calert-dialog-events-on-open-change"></span>`onOpenChange` | `(requestedOpen: boolean, detail: CAlertDialogOpenChangeDetail) => void` ([`CAlertDialogOpenChangeDetail`](#alert-dialog-interface-open-change-detail)) | An owned trigger, Escape, explicit decision, or external native close requests a different visible state. | `{reason: "trigger" | "escape" | "action" | "native", controlled: boolean, source: Element | EventTarget | null, returnValue: string}` ([`CAlertDialogOpenChangeDetail`](#alert-dialog-interface-open-change-detail)) | Uncontrolled requests commit before notification. Controlled requests wait for the owner. Cancel and Action return `cancel` and `action` respectively. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CAlertDialog CSS variables

Apply these variables to `CAlertDialog` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="alert-dialog-css-calert-dialog-css-variables-backdrop"></span>`--cui-alert-dialog-backdrop` | `color` | Modal backdrop. | `rgb(15 23 42 / 58%)` |
| <span id="alert-dialog-css-calert-dialog-css-variables-background"></span>`--cui-alert-dialog-background` | `color` | Surface background. | `Canvas` |
| <span id="alert-dialog-css-calert-dialog-css-variables-foreground"></span>`--cui-alert-dialog-foreground` | `color` | Surface text. | `CanvasText` |
| <span id="alert-dialog-css-calert-dialog-css-variables-border-color"></span>`--cui-alert-dialog-border-color` | `color` | Surface boundary. | `Subtle CanvasText mix.` |
| <span id="alert-dialog-css-calert-dialog-css-variables-radius"></span>`--cui-alert-dialog-radius` | `length` | Surface radius. | `0.875rem` |
| <span id="alert-dialog-css-calert-dialog-css-variables-shadow"></span>`--cui-alert-dialog-shadow` | `shadow` | Surface elevation. | `0 1.5rem 4rem rgb(15 23 42 / 28%)` |
| <span id="alert-dialog-css-calert-dialog-css-variables-inline-size"></span>`--cui-alert-dialog-inline-size` | `length` | Preferred responsive width. | `Size derived; 26rem at sm.` |
| <span id="alert-dialog-css-calert-dialog-css-variables-max-block-size"></span>`--cui-alert-dialog-max-block-size` | `length` | Maximum surface height. | `calc(100dvb - 2rem)` |
| <span id="alert-dialog-css-calert-dialog-css-variables-padding"></span>`--cui-alert-dialog-padding` | `length` | Surface region padding. | `1.25rem` |
| <span id="alert-dialog-css-calert-dialog-css-variables-gap"></span>`--cui-alert-dialog-gap` | `length` | Gap between regions. | `1rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CAlertDialog attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="alert-dialog-attribute-calert-dialog-attributes-role"></span>`role` | Native AlertDialog | `alertdialog` | Exposes the urgent modal decision role. |
| <span id="alert-dialog-attribute-calert-dialog-attributes-aria-modal"></span>`aria-modal` | Native AlertDialog | `true` | Matches native showModal modality. |
| <span id="alert-dialog-attribute-calert-dialog-attributes-aria-labelledby"></span>`aria-labelledby` | Native AlertDialog | `IDREF` | References the required title. |
| <span id="alert-dialog-attribute-calert-dialog-attributes-aria-describedby"></span>`aria-describedby` | Native AlertDialog | `IDREF` | References the required alert message. |
| <span id="alert-dialog-attribute-calert-dialog-attributes-open"></span>`data-open` | Native AlertDialog | `present-or-absent` | Mirrors effective native open state. |
| <span id="alert-dialog-attribute-calert-dialog-attributes-size"></span>`data-size` | Native AlertDialog | `"sm" | "md" | "lg"` | Mirrors effective responsive size. |
| <span id="alert-dialog-attribute-calert-dialog-attributes-scroll"></span>`data-scroll` | Native AlertDialog | `"body" | "dialog"` | Mirrors effective overflow mode. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CAlertDialog selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="alert-dialog-selector-calert-dialog-selectors-alert-dialog"></span>`[data-citry-ui-part="alert-dialog"]` | Native Dialog | Stable modal root and attrs destination. |
| <span id="alert-dialog-selector-calert-dialog-selectors-surface"></span>`[data-citry-ui-part="surface"]` | Surface | Visual decision surface. |
| <span id="alert-dialog-selector-calert-dialog-selectors-header"></span>`[data-citry-ui-part="header"]` | Header | Title layout. |
| <span id="alert-dialog-selector-calert-dialog-selectors-title"></span>`[data-citry-ui-part="title"]` | Title | Required accessible name. |
| <span id="alert-dialog-selector-calert-dialog-selectors-description"></span>`[data-citry-ui-part="description"]` | Description | Required alert message. |
| <span id="alert-dialog-selector-calert-dialog-selectors-body"></span>`[data-citry-ui-part="body"]` | Body | Optional supplemental content. |
| <span id="alert-dialog-selector-calert-dialog-selectors-actions"></span>`[data-citry-ui-part="actions"]` | Actions | Required Cancel and Action controls. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="alert-dialog-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="alert-dialog-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="alert-dialog-interface-size"></span>`CAlertDialogSize` | `Literal["sm", "md", "lg"]` |
| <span id="alert-dialog-interface-scroll"></span>`CAlertDialogScroll` | `Literal["body", "dialog"]` |

</div>

<span id="alert-dialog-interface-activator-slot"></span>

#### `CAlertDialogActivatorSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="alert-dialog-interface-activator-slot-attrs"></span>`activator_attrs` | `dict[str, object]` | - | Owned trigger relationships and marker. |
| <span id="alert-dialog-interface-activator-slot-type"></span>`activator_type` | `Literal["button"]` | - | Form-safe native Button type. |

</div>

<span id="alert-dialog-interface-title-slot"></span>

#### `CAlertDialogTitleSlotData`

Empty dataclass: `{}`.

<span id="alert-dialog-interface-description-slot"></span>

#### `CAlertDialogDescriptionSlotData`

Empty dataclass: `{}`.

<span id="alert-dialog-interface-default-slot"></span>

#### `CAlertDialogDefaultSlotData`

Empty dataclass: `{}`.

<span id="alert-dialog-interface-cancel-slot"></span>

#### `CAlertDialogCancelSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="alert-dialog-interface-cancel-slot-attrs"></span>`cancel_attrs` | `dict[str, object]` | - | Owned close marker, cancel return value, and autofocus. |
| <span id="alert-dialog-interface-cancel-slot-type"></span>`cancel_type` | `Literal["button"]` | - | Form-safe native Button type. |

</div>

<span id="alert-dialog-interface-action-slot"></span>

#### `CAlertDialogActionSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="alert-dialog-interface-action-slot-attrs"></span>`action_attrs` | `dict[str, object]` | - | Owned close marker and action return value. |
| <span id="alert-dialog-interface-action-slot-type"></span>`action_type` | `Literal["button"]` | - | Form-safe native Button type. |

</div>

<span id="alert-dialog-interface-open-change-detail"></span>

#### `CAlertDialogOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="alert-dialog-interface-open-change-detail-reason"></span>`reason` | `"trigger" | "escape" | "action" | "native"` | - | Request origin. |
| <span id="alert-dialog-interface-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client open currently owns state. |
| <span id="alert-dialog-interface-open-change-detail-source"></span>`source` | `Element | EventTarget | null` | - | Browser source associated with the request. |
| <span id="alert-dialog-interface-open-change-detail-return-value"></span>`returnValue` | `string` | - | cancel, action, or an empty string. |

</div>

### Translation keys

-