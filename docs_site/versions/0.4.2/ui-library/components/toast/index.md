---
title: Toast
url: https://citry.dev/v/0.4.2/ui-library/components/toast/
description: "Deliver queued, timed application feedback with Citry UI."
---
# Toast

Use `CToastRegion` once near the end of an application root. It owns a
persistent visible queue, polite and assertive announcers, remaining-time
pause, action/dismiss semantics, and F6 focus access. Arrival never steals
focus.

## Toast at a glance

Intent controls presentation; priority independently controls announcement
urgency.


### Toast at a glance

[Open the rendered preview](/v/0.4.2/ui-library/components/toast/_previews/at-a-glance/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToastAtAGlance(Component):
    template = """
      <section class="toast-sampler">
        <p>These initial messages demonstrate presentation intent separately from urgency.</p>
        <c-CToastRegion c-items="items" c-duration_ms="0" c-limit="5" />
      </section>
    """

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": tuple(
                citry_ui.CToastMessage(id=intent, title=title, intent=intent)
                for intent, title in (
                    ("neutral", "Draft retained"),
                    ("info", "Sync started"),
                    ("success", "Field note saved"),
                    ("warn", "Connection is slow"),
                    ("error", "Upload failed"),
                )
            )
        }

    css = ":where(.toast-sampler) { min-block-size:20rem; padding:1rem; }"


preview = ToastAtAGlance()
preview  # noqa: B018
````


## Drive a reactive queue

Pass an Array of plain client message records. A stable `id` is queue identity.
Remove IDs in `onDismiss` so expired or dismissed messages can later begin a
fresh episode.


### Add application notifications

[Open the rendered preview](/v/0.4.2/ui-library/components/toast/_previews/reactive-queue/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ReactiveToastQueue(Component):
    template = """
      <section class="toast-example" x-data="{notices: [], next: 1}">
        <c-CButton @click="notices = [...notices, {
          id: `note-${next}`, title: `Observation ${next++} queued`, intent: 'info'
        }]">Add notification</c-CButton>
        <c-CToastRegion $c-props="{
          items: notices,
          onDismiss: id => notices = notices.filter(item => item.id !== id),
        }" />
      </section>
    """
    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = ReactiveToastQueue()
preview  # noqa: B018
````



```citry-html
<c-CToastRegion
  $c-props="{
    items: notices,
    onDismiss: (id) => notices = notices.filter(item => item.id !== id),
  }"
/>
```


## Replace and deduplicate by ID

A retained ID updates in place. A material update restarts its lifetime and
announces the replacement once; a byte-equivalent snapshot does neither.


### Replace a message

[Open the rendered preview](/v/0.4.2/ui-library/components/toast/_previews/replacement/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToastReplacement(Component):
    template = """
      <section class="toast-example" x-data="{progress: 20}">
        <c-CButton @click="progress = Math.min(100, progress + 20)">Advance upload</c-CButton>
        <c-CToastRegion c-duration_ms="0" $c-props="{items: [{
          id: 'upload', title: `Upload ${progress}% complete`, description: 'Aurora Ridge photos'
        }]}" />
      </section>
    """
    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = ToastReplacement()
preview  # noqa: B018
````


## Pause remaining lifetime

The default lifetime is eight seconds. Set `duration_ms=0` for persistent
messages. Hover, focus within, document visibility, and an unrelated modal
pause remaining time rather than starting a new timeout.


### Pause a timed Toast

[Open the rendered preview](/v/0.4.2/ui-library/components/toast/_previews/timeout-pause/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimedToast(Component):
    template = """
      <section class="toast-example" x-data="{items: []}">
        <c-CButton @click="items = [{id: crypto.randomUUID(), title: 'Hover or focus to pause'}]">
          Start timed Toast
        </c-CButton>
        <c-CToastRegion c-duration_ms="4000" $c-props="{
          items,
          onDismiss: id => items = items.filter(item => item.id !== id),
        }" />
      </section>
    """
    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = TimedToast()
preview  # noqa: B018
````


## Add one persistent action

`onAction` runs before action-caused dismissal. Set `closeOnAction: false` when
the result should remain visible.


### Act on a notification

[Open the rendered preview](/v/0.4.2/ui-library/components/toast/_previews/persistent-action/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PersistentToastAction(Component):
    template = """
      <section class="toast-example" x-data="{items: [], result: 'No action yet'}">
        <c-CButton @click="items = [{
          id: 'offline', title: 'Working offline', actionLabel: 'Retry',
          closeOnAction: false, durationMs: 0, intent: 'warn'
        }]">Show persistent action</c-CButton>
        <output x-text="result"></output>
        <c-CToastRegion $c-props="{
          items,
          onAction: () => result = 'Retry requested',
          onDismiss: id => items = items.filter(item => item.id !== id),
        }" />
      </section>
    """
    css = ":where(.toast-example) { display:grid; gap:.75rem; min-block-size:16rem; padding:1rem; }"


preview = PersistentToastAction()
preview  # noqa: B018
````


## Limit the visible stack

Only the first `limit` unsuppressed messages render, announce, and run timers.
Queued records start when promoted.


### Queue beyond the visible limit

[Open the rendered preview](/v/0.4.2/ui-library/components/toast/_previews/visible-limit/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToastVisibleLimit(Component):
    template = """
      <section class="toast-example">
        <p>Dismiss a visible message to promote the queued third item.</p>
        <c-CToastRegion c-items="items" c-limit="2" c-duration_ms="0" />
      </section>
    """

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": tuple(
                citry_ui.CToastMessage(id=f"queue-{index}", title=f"Queue item {index}") for index in range(1, 4)
            )
        }

    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = ToastVisibleLimit()
preview  # noqa: B018
````


## Reach notifications with F6

Unmodified F6 moves from the application to the first presented Toast. F6
inside returns to the recorded element. Tab remains ordinary and is never
trapped.


### Use the F6 focus route

[Open the rendered preview](/v/0.4.2/ui-library/components/toast/_previews/focus-access/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToastFocusAccess(Component):
    template = """
      <section class="toast-example">
        <p>Focus this page, then press F6 to enter the notification and F6 again to return.</p>
        <c-CButton>Focus before F6</c-CButton>
        <c-CToastRegion c-items="items" c-duration_ms="0" />
      </section>
    """

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {"items": (citry_ui.CToastMessage(id="f6", title="F6 reaches this message"),)}

    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = ToastFocusAccess()
preview  # noqa: B018
````


## Pause behind a modal

A global Region becomes hidden, inert, and paused while an unrelated native
modal is open. Use `CAlert` inside the modal for feedback that must be immediate
there.


### Keep modal feedback local

[Open the rendered preview](/v/0.4.2/ui-library/components/toast/_previews/modal-pause/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToastModalPause(Component):
    template = """
      <section class="toast-example" x-data="{items: [{id:'global', title:'Global queue waits', durationMs:0}]}">
        <c-CDialog>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open modal task</c-CButton>
          </c-fill>
          <c-fill name="title">Modal-local feedback</c-fill>
          <c-fill name="default">
            <c-CAlert intent="info">Use Alert for immediate feedback inside this task.</c-CAlert>
          </c-fill>
        </c-CDialog>
        <c-CToastRegion $c-props="{items}" />
      </section>
    """
    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = ToastModalPause()
preview  # noqa: B018
````


## Choose a logical corner

Placements are `block-start-start`, `block-start-end`, `block-end-start`, and
`block-end-end`. Logical edges follow direction and writing mode.


### Place Toasts in RTL

[Open the rendered preview](/v/0.4.2/ui-library/components/toast/_previews/placement-rtl/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToastPlacementRtl(Component):
    template = """
      <section class="toast-example" dir="rtl">
        <p>Logical start follows this RTL context.</p>
        <c-CToastRegion c-items="items" placement="block-end-start" c-duration_ms="0" />
      </section>
    """

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {"items": (citry_ui.CToastMessage(id="rtl", title="Logical start placement"),)}

    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = ToastPlacementRtl()
preview  # noqa: B018
````


## Customize the surface

Use documented variables and part selectors. Unlayered application CSS wins;
safe-area, narrow viewport, forced-colors, and print behavior stay owned.


### Customize Toast

[Open the rendered preview](/v/0.4.2/ui-library/components/toast/_previews/customization/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedToast(Component):
    template = """
      <section class="toast-theme">
        <c-CToastRegion class_="polar-toast" c-items="items" c-duration_ms="0" />
      </section>
    """

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CToastMessage(
                    id="polar",
                    title="Polar archive synchronized",
                    description="A scheme-aware brand adaptation.",
                    intent="success",
                ),
            )
        }

    css = """
      :where(.toast-theme) { color-scheme:light dark; min-block-size:16rem; padding:1rem; }
      :where(.polar-toast) {
        --cui-toast-background: light-dark(#eef8fb, #102a34);
        --cui-toast-foreground: light-dark(#17343e, #e6f7fb);
        --cui-toast-border-color: light-dark(#76b7c7, #5ea5b6);
        --cui-toast-radius: 1.25rem;
      }
    """


preview = CustomizedToast()
preview  # noqa: B018
````


## Composition boundaries

Toast is brief global feedback, not a task surface, form-error relationship,
arbitrary card renderer, or dismissible overlay. Use `CAlert` for persistent
rich content, `CDialog`/`CDrawer` for tasks, and Field/Form errors beside their
controls. V1 deliberately has no slots, imperative service, swipe, portal, or
multi-action layout.

## API reference

### Inputs

#### CToastRegion server inputs

Server inputs are passed in a template through `<c-CToastRegion ... />` or in Python through
`CToastRegion(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 10rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="toast-input-ctoast-region-server-inputs-items"></span>`items` | `Sequence[CToastMessage]` | `"()"` | Ordered initial queue copied and validated once per render. |
| <span id="toast-input-ctoast-region-server-inputs-id"></span>`id` | `str | None` | generated | Sets exact Region identity and generated message relationships. |
| <span id="toast-input-ctoast-region-server-inputs-label"></span>`label` | `non-empty str` | `"Notifications"` | Names the Region. |
| <span id="toast-input-ctoast-region-server-inputs-messages"></span>`messages` | `CToastMessages | None` ([`CToastMessages`](#toast-interface-toast-messages)) | `None` | Overrides catalog-backed dismiss and action-announcement patterns per field. |
| <span id="toast-input-ctoast-region-server-inputs-placement"></span>`placement` | `"block-start-start" | "block-start-end" | "block-end-start" | "block-end-end"` ([`CToastPlacement`](#toast-interface-placement)) | `"block-end-end"` | Selects a logical viewport corner. |
| <span id="toast-input-ctoast-region-server-inputs-limit"></span>`limit` | `int (1..10)` | `3` | Limits simultaneously presented messages. |
| <span id="toast-input-ctoast-region-server-inputs-duration-ms"></span>`duration_ms` | `int` | `8000` | Sets default lifetime; zero is persistent and nonzero values are 1000..120000 milliseconds. |
| <span id="toast-input-ctoast-region-server-inputs-pause-on-hover"></span>`pause_on_hover` | `bool` | `True` | Pauses remaining time while the viewport is hovered. |
| <span id="toast-input-ctoast-region-server-inputs-pause-on-focus"></span>`pause_on_focus` | `bool` | `True` | Pauses remaining time while focus is inside. |
| <span id="toast-input-ctoast-region-server-inputs-pause-on-hidden"></span>`pause_on_hidden` | `bool` | `True` | Pauses remaining time while the owner document is hidden. |
| <span id="toast-input-ctoast-region-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#toast-interface-class-value)) | `None` | Merges consumer classes onto the Region. |
| <span id="toast-input-ctoast-region-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#toast-interface-style-value)) | `None` | Merges consumer inline styles onto the Region. |
| <span id="toast-input-ctoast-region-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native and data attributes without replacing owned semantics, focus, live regions, or structure. |

</div>

#### CToastRegion client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CToastRegion />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="toast-input-ctoast-region-client-inputs-items"></span>`items` | `Array<CToastClientMessage>` | Uses the copied server snapshot. | Reconciles the complete ordered queue by canonical ID. |
| <span id="toast-input-ctoast-region-client-inputs-placement"></span>`placement` | `"block-start-start" | "block-start-end" | "block-end-start" | "block-end-end"` ([`CToastPlacement`](#toast-interface-placement)) | Uses the server fallback. | Updates logical viewport placement. |
| <span id="toast-input-ctoast-region-client-inputs-limit"></span>`limit` | `integer (1..10)` | Uses the server fallback. | Changes visible capacity and promotes or queues messages. |
| <span id="toast-input-ctoast-region-client-inputs-duration-ms"></span>`durationMs` | `integer` | Uses the server fallback. | Sets default lifetime for messages without an override. |
| <span id="toast-input-ctoast-region-client-inputs-pause-on-hover"></span>`pauseOnHover` | `boolean` | Uses the server fallback. | Controls hover pause. |
| <span id="toast-input-ctoast-region-client-inputs-pause-on-focus"></span>`pauseOnFocus` | `boolean` | Uses the server fallback. | Controls focus pause. |
| <span id="toast-input-ctoast-region-client-inputs-pause-on-hidden"></span>`pauseOnHidden` | `boolean` | Uses the server fallback. | Controls document-visibility pause. |
| <span id="toast-input-ctoast-region-client-inputs-on-dismiss"></span>`onDismiss` | `function` | Does not notify a component callback. | Receives timeout, explicit-dismiss, and action-dismiss completion. |
| <span id="toast-input-ctoast-region-client-inputs-on-action"></span>`onAction` | `function` | Does not notify a component callback. | Receives the optional action before action-caused dismissal. |

</div>

### Slots

-

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CToastRegion events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="toast-event-ctoast-region-events-on-dismiss"></span>`onDismiss` | `(id: string, detail: CToastDismissDetail) => void` ([`CToastDismissDetail`](#toast-interface-toast-dismiss-detail)) | A presented message expires, is explicitly dismissed, or closes after its action. | `{reason: "timeout" | "dismiss" | "action", source: Element, message: CToastClientMessage}` ([`CToastDismissDetail`](#toast-interface-toast-dismiss-detail)) | Fires once after runtime removal; a producer should remove the ID to end suppression. |
| <span id="toast-event-ctoast-region-events-on-action"></span>`onAction` | `(id: string, detail: CToastActionDetail) => void` ([`CToastActionDetail`](#toast-interface-toast-action-detail)) | The optional action Button activates. | `{source: HTMLButtonElement, message: CToastClientMessage}` ([`CToastActionDetail`](#toast-interface-toast-action-detail)) | Fires before an action-caused dismissal; stale work stops if the callback removes the Region. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CToastRegion CSS variables

Apply these variables to `CToastRegion` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="toast-css-ctoast-css-variables-inline-offset"></span>`--cui-toast-inline-offset` | `length` | Logical viewport inline offset. | `1rem` |
| <span id="toast-css-ctoast-css-variables-block-offset"></span>`--cui-toast-block-offset` | `length` | Logical viewport block offset. | `1rem` |
| <span id="toast-css-ctoast-css-variables-gap"></span>`--cui-toast-gap` | `length` | Visible stack gap. | `0.75rem` |
| <span id="toast-css-ctoast-css-variables-width"></span>`--cui-toast-width` | `length` | Preferred visible width. | `22rem` |
| <span id="toast-css-ctoast-css-variables-background"></span>`--cui-toast-background` | `color` | Message background. | `Canvas` |
| <span id="toast-css-ctoast-css-variables-foreground"></span>`--cui-toast-foreground` | `color` | Message foreground and controls. | `CanvasText` |
| <span id="toast-css-ctoast-css-variables-border-color"></span>`--cui-toast-border-color` | `color` | Message boundary. | `Subtle CanvasText mix.` |
| <span id="toast-css-ctoast-css-variables-shadow"></span>`--cui-toast-shadow` | `shadow` | Message elevation. | `0 1rem 3rem rgb(15 23 42 / 22%)` |
| <span id="toast-css-ctoast-css-variables-radius"></span>`--cui-toast-radius` | `length` | Message corners. | `0.75rem` |
| <span id="toast-css-ctoast-css-variables-padding"></span>`--cui-toast-padding` | `length` | Message padding. | `1rem` |
| <span id="toast-css-ctoast-css-variables-accent"></span>`--cui-toast-accent` | `color` | Neutral message accent. | `currentColor` |
| <span id="toast-css-ctoast-css-variables-z-index"></span>`--cui-toast-z-index` | `integer` | Nonmodal application stacking hint. | `1000` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CToastRegion attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="toast-attribute-ctoast-attributes-data-placement"></span>`data-placement` | Region | `logical placement` | Mirrors the effective viewport corner. |
| <span id="toast-attribute-ctoast-attributes-data-paused"></span>`data-paused` | Region | `present | absent` | Present while timers are paused by hover, focus, visibility, or modality. |
| <span id="toast-attribute-ctoast-attributes-data-intent"></span>`data-intent` | Toast | `neutral | info | success | warn | error` | Mirrors presentation intent. |
| <span id="toast-attribute-ctoast-attributes-data-priority"></span>`data-priority` | Toast | `polite | assertive` | Mirrors announcement urgency. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CToastRegion selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="toast-selector-ctoast-selectors-region"></span>`[data-citry-ui-part="region"]` | Region section | Viewport and attrs destination. |
| <span id="toast-selector-ctoast-selectors-announcer-polite"></span>`[data-citry-ui-part="announcer-polite"]` | Hidden live region | Serialized polite announcements. |
| <span id="toast-selector-ctoast-selectors-announcer-assertive"></span>`[data-citry-ui-part="announcer-assertive"]` | Hidden live region | Serialized assertive announcements. |
| <span id="toast-selector-ctoast-selectors-toast"></span>`[data-citry-ui-part="toast"]` | Presented group | Focusable message surface. |
| <span id="toast-selector-ctoast-selectors-content"></span>`[data-citry-ui-part="content"]` | Content wrapper | Title and optional description. |
| <span id="toast-selector-ctoast-selectors-title"></span>`[data-citry-ui-part="title"]` | Title | Visible accessible name. |
| <span id="toast-selector-ctoast-selectors-description"></span>`[data-citry-ui-part="description"]` | Description | Optional relationship text. |
| <span id="toast-selector-ctoast-selectors-actions"></span>`[data-citry-ui-part="actions"]` | Controls wrapper | Optional action and dismissal layout. |
| <span id="toast-selector-ctoast-selectors-action"></span>`[data-citry-ui-part="action"]` | Button | Optional one-action control. |
| <span id="toast-selector-ctoast-selectors-dismiss"></span>`[data-citry-ui-part="dismiss"]` | Button | Explicit message dismissal. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="toast-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="toast-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="toast-interface-intent"></span>`CToastIntent` | `Literal["neutral", "info", "success", "warn", "error"]` |
| <span id="toast-interface-placement"></span>`CToastPlacement` | `Literal["block-start-start", "block-start-end", "block-end-start", "block-end-end"]` |
| <span id="toast-interface-priority"></span>`CToastPriority` | `Literal["polite", "assertive"]` |

</div>

<span id="toast-interface-toast-message"></span>

#### `CToastMessage`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="toast-interface-toast-message-id"></span>`id` | `str` | - | Unique canonical queue identity. |
| <span id="toast-interface-toast-message-title"></span>`title` | `str` | - | Visible and accessible plain-text name. |
| <span id="toast-interface-toast-message-description"></span>`description` | `str | None` | - | Optional plain supporting text. |
| <span id="toast-interface-toast-message-intent"></span>`intent` | `CToastIntent` | - | Presentation intent independent from urgency. |
| <span id="toast-interface-toast-message-priority"></span>`priority` | `CToastPriority` | - | Polite or assertive announcement channel. |
| <span id="toast-interface-toast-message-duration-ms"></span>`duration_ms` | `int | None` | - | Optional per-message lifetime; zero is persistent. |
| <span id="toast-interface-toast-message-action-label"></span>`action_label` | `str | None` | - | Optional one-action Button label. |
| <span id="toast-interface-toast-message-close-on-action"></span>`close_on_action` | `bool` | - | Whether action completion dismisses the message. |
| <span id="toast-interface-toast-message-dismissible"></span>`dismissible` | `bool` | - | Whether explicit dismissal is available. |

</div>

<span id="toast-interface-toast-messages"></span>

#### `CToastMessages`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="toast-interface-toast-messages-dismiss-label"></span>`dismiss_label` | `str | None` | None | Overrides the catalog-backed dismiss pattern and must contain `{title}`. |
| <span id="toast-interface-toast-messages-action-announcement"></span>`action_announcement` | `str | None` | None | Overrides the catalog-backed action announcement and must contain `{action_label}`. |

</div>

<span id="toast-interface-toast-client-message"></span>

#### `CToastClientMessage`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="toast-interface-toast-client-message-id"></span>`id` | `string` | - | Unique canonical queue identity. |
| <span id="toast-interface-toast-client-message-title"></span>`title` | `string` | - | Visible and accessible plain-text name. |
| <span id="toast-interface-toast-client-message-description"></span>`description` | `string | null` | - | Optional supporting text. |
| <span id="toast-interface-toast-client-message-intent"></span>`intent` | `CToastIntent` | - | Presentation intent. |
| <span id="toast-interface-toast-client-message-priority"></span>`priority` | `CToastPriority` | - | Announcement channel. |
| <span id="toast-interface-toast-client-message-duration-ms"></span>`durationMs` | `integer | null` | - | Optional lifetime override. |
| <span id="toast-interface-toast-client-message-action-label"></span>`actionLabel` | `string | null` | - | Optional one-action label. |
| <span id="toast-interface-toast-client-message-close-on-action"></span>`closeOnAction` | `boolean` | - | Whether action dismisses. |
| <span id="toast-interface-toast-client-message-dismissible"></span>`dismissible` | `boolean` | - | Whether explicit dismissal is available. |

</div>

<span id="toast-interface-toast-dismiss-detail"></span>

#### `CToastDismissDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="toast-interface-toast-dismiss-detail-reason"></span>`reason` | `"timeout" | "dismiss" | "action"` | - | Runtime removal reason. |
| <span id="toast-interface-toast-dismiss-detail-source"></span>`source` | `Element` | - | Browser source associated with dismissal. |
| <span id="toast-interface-toast-dismiss-detail-message"></span>`message` | `CToastClientMessage` | - | Canonical public message snapshot. |

</div>

<span id="toast-interface-toast-action-detail"></span>

#### `CToastActionDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="toast-interface-toast-action-detail-source"></span>`source` | `HTMLButtonElement` | - | Activated action Button. |
| <span id="toast-interface-toast-action-detail-message"></span>`message` | `CToastClientMessage` | - | Canonical public message snapshot. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CToastRegion translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="toast-translation-ctoast-region-translations-region"></span>`citry-ui-toast-region` | Names the notification region. | `None` | `label` input | $c-tr updates `aria-label`. |
| <span id="toast-translation-ctoast-region-translations-dismiss"></span>`citry-ui-toast-dismiss` | Names each toast dismiss control. | `title: str` | `messages.dismiss_label` | $c-tr handles initial items; `i18n.bind()` handles browser-created items. |
| <span id="toast-translation-ctoast-region-translations-action-available"></span>`citry-ui-toast-action-available` | Announces that the toast exposes an action. | `action_label: str` | `messages.action_announcement` | One-shot `i18n.tr()` when the toast is added. |

</div>