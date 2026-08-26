---
title: Drawer
url: https://citry.dev/v/0.4.4/ui-library/components/drawer/
description: "Build accessible modal side Drawers and Sheets with Citry UI."
---
# Drawer

Use `CDrawer` for a modal task that enters from a viewport edge. It renders a
native modal Dialog, so focus containment, background inertness, top-layer
ordering, native Forms, and restoration remain platform semantics.

Persistent navigation is not a Drawer mode. Build that later with the layout
and AppShell vocabulary so it can reserve space without trapping focus.

## Drawer at a glance

Logical placement works in LTR, RTL, and other writing modes. `block-end` is
the bottom-Sheet path in ordinary horizontal writing.


### Drawer at a glance

[Open the rendered preview](/v/0.4.4/ui-library/components/drawer/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DrawerAtAGlance(Component):
    template = """
      <section class="drawer-sampler">
        <c-CDrawer placement="inline-start" size="sm">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">Leading Drawer</c-CButton>
          </c-fill>
          <c-fill name="title">Atlas index</c-fill>
          <c-fill name="default">Browse nearby observations.</c-fill>
        </c-CDrawer>
        <c-CDrawer placement="inline-end">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Trailing Drawer</c-CButton>
          </c-fill>
          <c-fill name="title">Field note</c-fill>
          <c-fill name="default">Edit the selected observation.</c-fill>
        </c-CDrawer>
        <c-CDrawer placement="block-end" size="sm">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="ghost" c-attrs="activator_attrs">Bottom Sheet</c-CButton>
          </c-fill>
          <c-fill name="title">Quick actions</c-fill>
          <c-fill name="default">Choose an action for this record.</c-fill>
        </c-CDrawer>
      </section>
    """
    css = """
      :where(.drawer-sampler) { display:flex; flex-wrap:wrap; gap:.75rem; padding:2rem 1rem; }
    """


preview = DrawerAtAGlance()
preview  # noqa: B018
````


## Build a Drawer

Provide a visible title and body. Spread `activator_attrs` on one `CButton`.
Spread `close_attrs` on explicit completion or cancel actions.


### Edit a field note

[Open the rendered preview](/v/0.4.4/ui-library/components/drawer/_previews/edit-field-note/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditFieldNote(Component):
    template = """
      <section class="drawer-example">
        <p>Northern ridge · 01:42</p>
        <c-CDrawer>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Edit field note</c-CButton>
          </c-fill>
          <c-fill name="title">Aurora field note</c-fill>
          <c-fill name="description">Update the observation saved at the northern ridge.</c-fill>
          <c-fill name="default">
            <label for="drawer-note">Observation</label>
            <textarea id="drawer-note" rows="7">Green arcs above the eastern horizon.</textarea>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton variant="ghost" c-attrs="close_attrs">Cancel</c-CButton>
            <c-CButton c-attrs="close_attrs">Save note</c-CButton>
          </c-fill>
        </c-CDrawer>
      </section>
    """
    css = """
      :where(.drawer-example) { display:grid; gap:.75rem; justify-items:start; padding:1.5rem; }
      :where(.drawer-example p) { margin:0; color:color-mix(in srgb, CanvasText 68%, transparent); }
      :where(.cui-drawer__body label, .cui-drawer__body textarea) { display:block; inline-size:100%; }
      :where(.cui-drawer__body textarea) { box-sizing:border-box; margin-block-start:.4rem; padding:.75rem; }
    """


preview = EditFieldNote()
preview  # noqa: B018
````



```citry-html
<c-CDrawer placement="inline-end">
  <c-fill name="activator" data="{ activator_attrs }">
    <c-CButton c-attrs="activator_attrs">Edit note</c-CButton>
  </c-fill>
  <c-fill name="title">Field note</c-fill>
  <c-fill name="description">Update the selected observation.</c-fill>
  <c-fill name="default">...</c-fill>
  <c-fill name="actions" data="{ close_attrs }">
    <c-CButton c-attrs="close_attrs">Done</c-CButton>
  </c-fill>
</c-CDrawer>
```


The activator must settle to exactly one native Button with `type="button"`.
`CButton` already has that safe default. Set the type explicitly when using a
native `<button>`.

## Build a bottom Sheet

Use the same semantic family with `placement="block-end"`; there is no second
`CSheet` alias or mini-language.


### Open a bottom Sheet

[Open the rendered preview](/v/0.4.4/ui-library/components/drawer/_previews/bottom-sheet/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BottomSheet(Component):
    template = """
      <section class="sheet-example">
        <c-CDrawer placement="block-end" size="sm">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open observation actions</c-CButton>
          </c-fill>
          <c-fill name="title">Observation actions</c-fill>
          <c-fill name="default">
            <c-CButton variant="ghost" block>Duplicate note</c-CButton>
            <c-CButton variant="ghost" block>Share coordinates</c-CButton>
          </c-fill>
        </c-CDrawer>
      </section>
    """
    css = """
      :where(.sheet-example) { display:grid; place-items:center; min-block-size:10rem; }
      :where(.sheet-example .cui-drawer__body) { display:grid; gap:.5rem; }
    """


preview = BottomSheet()
preview  # noqa: B018
````


## Configure placement and size

Placement accepts `inline-start`, `inline-end`, `block-start`, or `block-end`.
Size accepts `sm`, `md`, `lg`, or `full`. The viewport-safe maximum wins over
an oversized requested extent.


### Configure Drawer geometry

[Open the rendered preview](/v/0.4.4/ui-library/components/drawer/_previews/configuration/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ConfigureDrawer(Component):
    template = """
      <section x-data="{placement:'inline-end', size:'md', scroll:'body'}"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)">
        <c-CDrawer $c-props="{placement, size, scroll}">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Preview geometry</c-CButton>
          </c-fill>
          <c-fill name="title">Configurable archive</c-fill>
          <c-fill name="default">Change the logical edge, extent, and scrolling policy.</c-fill>
        </c-CDrawer>
      </section>
    """


preview_controls = (
    {
        "name": "placement",
        "label": "Placement",
        "type": "select",
        "default": "inline-end",
        "options": (
            ("inline-start", "Inline start"),
            ("inline-end", "Inline end"),
            ("block-start", "Block start"),
            ("block-end", "Block end"),
        ),
    },
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large"), ("full", "Full")),
    },
    {
        "name": "scroll",
        "label": "Scroll",
        "type": "select",
        "default": "body",
        "options": (("body", "Body"), ("drawer", "Complete Drawer")),
    },
)
preview = ConfigureDrawer()
preview  # noqa: B018
````


Every server configuration input has a matching client input except identity,
text, class, style, and attrs. Use `initialFocus`, `placement`, `size`, and
`scroll` through `$c-props` for live changes.

## Control visibility

Pass Boolean `open` and `onOpenChange` through `$c-props`. Controlled requests
wait for the owner; retaining `open` declines an ordinary request. Forced
ancestor/native safety closure happens first and reports `forced: true`.


### Control Drawer visibility

[Open the rendered preview](/v/0.4.4/ui-library/components/drawer/_previews/controlled-drawer/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledDrawer(Component):
    template = """
      <section class="controlled-drawer" x-data="{open:false, accept:true, log:'No request yet'}">
        <c-CDrawer $c-props="{open, onOpenChange:(next, detail) => {
          log = `${detail.reason}: ${next ? 'open' : 'closed'}`; if (accept) open = next;
        }}">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Controlled archive</c-CButton>
          </c-fill>
          <c-fill name="title">Controlled archive</c-fill>
          <c-fill name="default">The owner may accept or decline visibility requests.</c-fill>
        </c-CDrawer>
        <label><input type="checkbox" x-model="accept" /> Accept requests</label>
        <output x-text="log"></output>
      </section>
    """
    css = """
      :where(.controlled-drawer) { display:grid; gap:.75rem; justify-items:start; padding:1rem; }
    """


preview = ControlledDrawer()
preview  # noqa: B018
````


Callback reasons are `trigger`, `close-button`, `action`, `escape`, `outside`,
`native`, and `ancestor`. Detail also carries `controlled`, `forced`, `source`,
and `returnValue`. Removing `open` or passing `null` releases ownership from
the current committed state.

## Place focus and scroll content

`initial_focus="auto"` preserves native autofocus/focus steps.
`initial_focus="title"` starts reading at the visible title. `scroll="body"`
keeps header/actions fixed; `scroll="drawer"` scrolls the whole surface.


### Read long Drawer content

[Open the rendered preview](/v/0.4.4/ui-library/components/drawer/_previews/long-content/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class LongDrawer(Component):
    template = """
      <section>
        <c-CDrawer initial_focus="title" size="sm">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Read expedition log</c-CButton>
          </c-fill>
          <c-fill name="title">Seven-night aurora expedition</c-fill>
          <c-fill name="default">
            <c-for each="night in nights">
              <h3>Night {{ night }}</h3>
              <p>Cloud cover shifted before a clear interval revealed green and violet arcs.</p>
            </c-for>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">Finish reading</c-CButton>
          </c-fill>
        </c-CDrawer>
      </section>
    """

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, range]:  # noqa: ARG002
        return {"nights": range(1, 8)}


preview = LongDrawer()
preview  # noqa: B018
````


Tab and Shift+Tab remain inside the nearest modal. Closing returns focus to
the deep active element recorded before opening when it is still usable.

## Use native Forms

Forms retain validation, reset, FormData, and Citry Events. A
`method="dialog"` Form reports its submitter through callback `returnValue`.


### Submit a Drawer Form

[Open the rendered preview](/v/0.4.4/ui-library/components/drawer/_previews/drawer-form/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DrawerForm(Component):
    template = """
      <section x-data="{result:'No chart selected'}">
        <c-CDrawer $c-props="{onOpenChange:(open, detail) => {
          if (!open && detail.returnValue) result = `Selected: ${detail.returnValue}`;
        }}">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Choose a chart</c-CButton>
          </c-fill>
          <c-fill name="title">Choose a chart</c-fill>
          <c-fill name="default">
            <form method="dialog" class="drawer-chart-form">
              <button type="submit" value="altitude">Altitude chart</button>
              <button type="submit" value="intensity">Intensity chart</button>
            </form>
          </c-fill>
        </c-CDrawer>
        <output x-text="result"></output>
      </section>
    """
    css = """
      :where(.drawer-chart-form) { display:grid; gap:.75rem; }
    """


preview = DrawerForm()
preview  # noqa: B018
````


## Compose anchored layers

Menu, Popover, and Tooltip may open inside a Drawer. Opening a modal suppresses
ineligible anchored layers outside it; closing a parent closes descendants.


### Use a Menu inside a Drawer

[Open the rendered preview](/v/0.4.4/ui-library/components/drawer/_previews/nested-layers/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NestedLayers(Component):
    template = """
      <section>
        <c-CDrawer>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open archive tools</c-CButton>
          </c-fill>
          <c-fill name="title">Archive tools</c-fill>
          <c-fill name="default">
            <c-CMenu>
              <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Choose action</c-CButton>
              </c-fill>
              <c-fill name="default">
                <c-CMenuItem value="duplicate">Duplicate record</c-CMenuItem>
                <c-CMenuItem value="export">Export coordinates</c-CMenuItem>
              </c-fill>
            </c-CMenu>
          </c-fill>
        </c-CDrawer>
      </section>
    """


preview = NestedLayers()
preview  # noqa: B018
````


## Require explicit completion

Set `dismissible=False` to remove the built-in close control and reject Escape
and backdrop dismissal. Explicit controls using `close_attrs` still work.


### Require explicit completion

[Open the rendered preview](/v/0.4.4/ui-library/components/drawer/_previews/explicit-completion/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ExplicitCompletion(Component):
    template = """
      <section>
        <c-CDrawer c-dismissible="False" placement="block-start" size="sm">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Review coordinates</c-CButton>
          </c-fill>
          <c-fill name="title">Confirm coordinates</c-fill>
          <c-fill name="default">Check the latitude and longitude before continuing.</c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">Coordinates verified</c-CButton>
          </c-fill>
        </c-CDrawer>
      </section>
    """


preview = ExplicitCompletion()
preview  # noqa: B018
````


## Customize the Drawer

Use the documented `--cui-drawer-*` variables and part selectors. Defaults use
low-specificity rules, so unlayered application CSS wins. Safe-area insets,
logical placement, forced colors, and reduced motion remain component-owned.


### Customize the Drawer

[Open the rendered preview](/v/0.4.4/ui-library/components/drawer/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedDrawer(Component):
    template = """
      <section class="polar-drawer-theme">
        <c-CDrawer class_="polar-drawer" size="sm">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open polar archive</c-CButton>
          </c-fill>
          <c-fill name="title">Polar archive</c-fill>
          <c-fill name="description">A cool-toned field-research adaptation.</c-fill>
          <c-fill name="default">Ice-core and aurora records from the northern station.</c-fill>
          <c-fill name="close"><span aria-hidden="true">✦</span></c-fill>
        </c-CDrawer>
      </section>
    """
    css = """
      :where(.polar-drawer-theme) { color-scheme:light dark; padding:1.5rem; }
      :where(.polar-drawer) {
        --cui-drawer-background: light-dark(#eef8fb, #102a34);
        --cui-drawer-foreground: light-dark(#17343e, #e6f7fb);
        --cui-drawer-border-color: light-dark(#76b7c7, #5ea5b6);
        --cui-drawer-radius: 1.25rem;
      }
      :where(.polar-drawer [data-citry-ui-part="title"]) { letter-spacing:.04em; }
    """


preview = CustomizedDrawer()
preview  # noqa: B018
````


`class_`, `style`, and allowed `attrs` merge onto the native Dialog. They may
not replace modality, relationships, visibility, parts, or structure.

## Composition boundaries

Drawer is modal and task-oriented. It does not reserve application layout
space, become permanent at a breakpoint, teleport, expose z-index, or support
swipe/drag. Use `CDialog` for centered work and a later AppShell navigation
surface for persistent navigation.

## API reference

### Inputs

#### CDrawer server inputs

Server inputs are passed in a template through `<c-CDrawer ... />` or in Python through
`CDrawer(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 8rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="drawer-input-cdrawer-server-inputs-id"></span>`id` | `str | None` | generated | Sets native identity and title/description/activator relationships. |
| <span id="drawer-input-cdrawer-server-inputs-open"></span>`open` | `bool` | `False` | Sets server-visible initial state; valid client `open` controls later state. |
| <span id="drawer-input-cdrawer-server-inputs-dismissible"></span>`dismissible` | `bool` | `True` | Shows the built-in close Button and permits passive dismissal. |
| <span id="drawer-input-cdrawer-server-inputs-close-on-escape"></span>`close_on_escape` | `bool` | `True` | Permits Escape/platform cancel when dismissible. |
| <span id="drawer-input-cdrawer-server-inputs-close-on-outside"></span>`close_on_outside` | `bool` | `True` | Permits a press beginning and ending on the backdrop when dismissible. |
| <span id="drawer-input-cdrawer-server-inputs-initial-focus"></span>`initial_focus` | `"auto" | "title"` ([`CDrawerInitialFocus`](#drawer-interface-initial-focus)) | `"auto"` | Preserves native autofocus/focus steps or focuses the visible title. |
| <span id="drawer-input-cdrawer-server-inputs-placement"></span>`placement` | `"inline-start" | "inline-end" | "block-start" | "block-end"` ([`CDrawerPlacement`](#drawer-interface-placement)) | `"inline-end"` | Chooses the logical viewport edge. Block-end is the bottom-Sheet path in horizontal writing. |
| <span id="drawer-input-cdrawer-server-inputs-size"></span>`size` | `"sm" | "md" | "lg" | "full"` ([`CDrawerSize`](#drawer-interface-size)) | `"md"` | Sets the viewport-safe extent along the opening axis. |
| <span id="drawer-input-cdrawer-server-inputs-scroll"></span>`scroll` | `"body" | "drawer"` ([`CDrawerScroll`](#drawer-interface-scroll)) | `"body"` | Scrolls only task content or the complete Drawer surface. |
| <span id="drawer-input-cdrawer-server-inputs-close-label"></span>`close_label` | `non-empty str` | `"Close"` | Names the built-in close Button. |
| <span id="drawer-input-cdrawer-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#drawer-interface-class-value)) | `None` | Merges consumer classes onto the native Dialog. |
| <span id="drawer-input-cdrawer-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#drawer-interface-style-value)) | `None` | Merges consumer inline styles onto the native Dialog. |
| <span id="drawer-input-cdrawer-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native Dialog, ARIA, Alpine, and data attributes without replacing owned state or structure. |

</div>

#### CDrawer client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CDrawer />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="drawer-input-cdrawer-client-inputs-open"></span>`open` | `boolean | null` | Releases to uncontrolled ownership from the committed state. `null` is equivalent. | Controls visibility while supplied as a Boolean. Invalid values report once and release control. |
| <span id="drawer-input-cdrawer-client-inputs-dismissible"></span>`dismissible` | `boolean` | Uses the server fallback. | Controls built-in close visibility and passive dismissal. |
| <span id="drawer-input-cdrawer-client-inputs-close-on-escape"></span>`closeOnEscape` | `boolean` | Uses the server fallback. | Controls Escape/platform cancel. |
| <span id="drawer-input-cdrawer-client-inputs-close-on-outside"></span>`closeOnOutside` | `boolean` | Uses the server fallback. | Controls backdrop-press dismissal. |
| <span id="drawer-input-cdrawer-client-inputs-initial-focus"></span>`initialFocus` | `"auto" | "title"` ([`CDrawerInitialFocus`](#drawer-interface-initial-focus)) | Uses the server fallback. | Controls focus placement on the next opening. |
| <span id="drawer-input-cdrawer-client-inputs-placement"></span>`placement` | `"inline-start" | "inline-end" | "block-start" | "block-end"` ([`CDrawerPlacement`](#drawer-interface-placement)) | Uses the server fallback. | Controls `data-placement` and edge geometry without reopening. |
| <span id="drawer-input-cdrawer-client-inputs-size"></span>`size` | `"sm" | "md" | "lg" | "full"` ([`CDrawerSize`](#drawer-interface-size)) | Uses the server fallback. | Controls `data-size` and responsive extent. |
| <span id="drawer-input-cdrawer-client-inputs-scroll"></span>`scroll` | `"body" | "drawer"` ([`CDrawerScroll`](#drawer-interface-scroll)) | Uses the server fallback. | Controls `data-scroll` and overflow behavior. |
| <span id="drawer-input-cdrawer-client-inputs-on-open-change"></span>`onOpenChange` | `function` | Does not notify a component callback. | Receives ordinary visibility requests and non-rejectable forced close notices. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CDrawer slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="drawer-slot-cdrawer-slots-activator"></span>`activator` | no | `{activator_attrs: dict[str, object]}` ([`CDrawerActivatorSlotData`](#drawer-interface-activator-slot-data)) | No activator. |
| <span id="drawer-slot-cdrawer-slots-title"></span>`title` | yes | `{}` ([`CDrawerTitleSlotData`](#drawer-interface-title-slot-data)) | none |
| <span id="drawer-slot-cdrawer-slots-description"></span>`description` | no | `{}` ([`CDrawerDescriptionSlotData`](#drawer-interface-description-slot-data)) | No `aria-describedby` relationship. |
| <span id="drawer-slot-cdrawer-slots-default"></span>`default` | yes | `{}` ([`CDrawerDefaultSlotData`](#drawer-interface-default-slot-data)) | none |
| <span id="drawer-slot-cdrawer-slots-actions"></span>`actions` | no | `{close_attrs: dict[str, object]}` ([`CDrawerActionsSlotData`](#drawer-interface-actions-slot-data)) | omitted |
| <span id="drawer-slot-cdrawer-slots-close"></span>`close` | no | `{}` ([`CDrawerCloseSlotData`](#drawer-interface-close-slot-data)) | Built-in multiplication-sign glyph. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CDrawer events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="drawer-event-cdrawer-events-on-open-change"></span>`onOpenChange` | `(requestedOpen: boolean, detail: CDrawerOpenChangeDetail) => void` ([`CDrawerOpenChangeDetail`](#drawer-interface-open-change-detail)) | An owned trigger, close control, action, Escape, outside press, native close, or structural safety close changes or requests visibility. | `{reason: "trigger" | "close-button" | "action" | "escape" | "outside" | "native" | "ancestor", controlled: boolean, forced: boolean, source: Element | EventTarget | null, returnValue: string}` ([`CDrawerOpenChangeDetail`](#drawer-interface-open-change-detail)) | Uncontrolled ordinary requests commit first. Controlled ordinary requests wait for the owner. Forced safety/native closures commit first and cannot be declined. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CDrawer CSS variables

Apply these variables to `CDrawer` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="drawer-css-cdrawer-css-variables-cui-drawer-backdrop"></span>`--cui-drawer-backdrop` | `color` | Modal backdrop. | `rgb(15 23 42 / 58%)` |
| <span id="drawer-css-cdrawer-css-variables-cui-drawer-background"></span>`--cui-drawer-background` | `color` | Surface background. | `Canvas` |
| <span id="drawer-css-cdrawer-css-variables-cui-drawer-foreground"></span>`--cui-drawer-foreground` | `color` | Surface text. | `CanvasText` |
| <span id="drawer-css-cdrawer-css-variables-cui-drawer-border-color"></span>`--cui-drawer-border-color` | `color` | Inner-edge boundary. | `Subtle CanvasText mix.` |
| <span id="drawer-css-cdrawer-css-variables-cui-drawer-shadow"></span>`--cui-drawer-shadow` | `shadow` | Edge elevation. | `0 1.5rem 4rem rgb(15 23 42 / 28%)` |
| <span id="drawer-css-cdrawer-css-variables-cui-drawer-extent"></span>`--cui-drawer-extent` | `length` | Extent along the opening axis. | `Size-derived; 28rem at md.` |
| <span id="drawer-css-cdrawer-css-variables-cui-drawer-padding"></span>`--cui-drawer-padding` | `length` | Region padding before safe-area augmentation. | `1.25rem` |
| <span id="drawer-css-cdrawer-css-variables-cui-drawer-gap"></span>`--cui-drawer-gap` | `length` | Region spacing. | `1rem` |
| <span id="drawer-css-cdrawer-css-variables-cui-drawer-radius"></span>`--cui-drawer-radius` | `length` | Inner-edge corners. | `0.875rem` |
| <span id="drawer-css-cdrawer-css-variables-cui-drawer-close-size"></span>`--cui-drawer-close-size` | `length` | Built-in close target. | `2.5rem` |
| <span id="drawer-css-cdrawer-css-variables-cui-drawer-close-radius"></span>`--cui-drawer-close-radius` | `length` | Built-in close corners. | `0.5rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CDrawer attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="drawer-attribute-cdrawer-attributes-data-open"></span>`data-open` | Native Drawer Dialog | `present | absent` | Mirrors effective visible state. |
| <span id="drawer-attribute-cdrawer-attributes-data-placement"></span>`data-placement` | Native Drawer Dialog | `logical placement` | Mirrors the effective viewport edge. |
| <span id="drawer-attribute-cdrawer-attributes-data-size"></span>`data-size` | Native Drawer Dialog | `"sm" | "md" | "lg" | "full"` | Mirrors effective extent. |
| <span id="drawer-attribute-cdrawer-attributes-data-scroll"></span>`data-scroll` | Native Drawer Dialog | `"body" | "drawer"` | Mirrors effective overflow policy. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CDrawer selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="drawer-selector-cdrawer-selectors-drawer"></span>`[data-citry-ui-part="drawer"]` | Native Dialog | Modal root and attrs destination. |
| <span id="drawer-selector-cdrawer-selectors-surface"></span>`[data-citry-ui-part="surface"]` | Surface | Edge-filling visual surface. |
| <span id="drawer-selector-cdrawer-selectors-header"></span>`[data-citry-ui-part="header"]` | Header | Title and close layout. |
| <span id="drawer-selector-cdrawer-selectors-title"></span>`[data-citry-ui-part="title"]` | Title | Visible accessible name. |
| <span id="drawer-selector-cdrawer-selectors-description"></span>`[data-citry-ui-part="description"]` | Description | Optional described-by content. |
| <span id="drawer-selector-cdrawer-selectors-close"></span>`[data-citry-ui-part="close"]` | Close Button | Built-in dismissal. |
| <span id="drawer-selector-cdrawer-selectors-body"></span>`[data-citry-ui-part="body"]` | Body | Primary task content. |
| <span id="drawer-selector-cdrawer-selectors-actions"></span>`[data-citry-ui-part="actions"]` | Actions | Optional explicit actions. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="drawer-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="drawer-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="drawer-interface-initial-focus"></span>`CDrawerInitialFocus` | `Literal["auto", "title"]` |
| <span id="drawer-interface-placement"></span>`CDrawerPlacement` | `Literal["inline-start", "inline-end", "block-start", "block-end"]` |
| <span id="drawer-interface-size"></span>`CDrawerSize` | `Literal["sm", "md", "lg", "full"]` |
| <span id="drawer-interface-scroll"></span>`CDrawerScroll` | `Literal["body", "drawer"]` |

</div>

<span id="drawer-interface-activator-slot-data"></span>

#### `CDrawerActivatorSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="drawer-interface-activator-slot-data-activator-attrs"></span>`activator_attrs` | `dict[str, object]` | - | Owned trigger marker plus dialog relationship attributes. |

</div>

<span id="drawer-interface-title-slot-data"></span>

#### `CDrawerTitleSlotData`

Empty dataclass: `{}`.

<span id="drawer-interface-description-slot-data"></span>

#### `CDrawerDescriptionSlotData`

Empty dataclass: `{}`.

<span id="drawer-interface-default-slot-data"></span>

#### `CDrawerDefaultSlotData`

Empty dataclass: `{}`.

<span id="drawer-interface-actions-slot-data"></span>

#### `CDrawerActionsSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="drawer-interface-actions-slot-data-close-attrs"></span>`close_attrs` | `dict[str, object]` | - | Explicit-close marker; Button value becomes the return value. |

</div>

<span id="drawer-interface-close-slot-data"></span>

#### `CDrawerCloseSlotData`

Empty dataclass: `{}`.

<span id="drawer-interface-open-change-detail"></span>

#### `CDrawerOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="drawer-interface-open-change-detail-reason"></span>`reason` | `"trigger" | "close-button" | "action" | "escape" | "outside" | "native" | "ancestor"` | - | Request or safety-close reason. |
| <span id="drawer-interface-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client `open` currently owns state. |
| <span id="drawer-interface-open-change-detail-forced"></span>`forced` | `boolean` | - | True for a non-rejectable structural or external-native closure. |
| <span id="drawer-interface-open-change-detail-source"></span>`source` | `Element | EventTarget | null` | - | Browser source associated with the transition. |
| <span id="drawer-interface-open-change-detail-return-value"></span>`returnValue` | `string` | - | Explicit action/native Dialog Form result; otherwise empty. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CDrawer translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="drawer-translation-cdrawer-translations-close"></span>`citry-ui-drawer-close` | Names the generated close control. | `None` | `close_label` input or `close` slot | $c-tr updates `aria-label`. |

</div>