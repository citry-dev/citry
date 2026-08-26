---
title: Sortable
url: https://citry.dev/v/0.4.4/ui-library/components/sortable/
description: "Reorder server-rendered items with pointer, touch, or keyboard while preserving native form order."
---
# Sortable

Use `CSortable` for a finite collection whose order matters. Each
`CSortableItem` supplies stable identity, a plain accessible label, and visible
content. The initial server order remains useful before JavaScript starts.

## Reorder a list

Drag an Item by its handle. Keyboard users focus the same handle, press Space
or Enter to pick it up, use arrow keys, Home, or End to move it, then press
Space or Enter to drop. Escape cancels.


### Prioritize release work

[Open the rendered preview](/v/0.4.4/ui-library/components/sortable/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SortableAtAGlance(Component):
    template = """
      <c-CSortable name="release-priority">
        <c-CSortableItem value="design" label="Design review">Design review</c-CSortableItem>
        <c-CSortableItem value="accessibility" label="Accessibility pass">Accessibility pass</c-CSortableItem>
        <c-CSortableItem value="implementation" label="Implementation">Implementation</c-CSortableItem>
        <c-CSortableItem value="release" label="Release">Release</c-CSortableItem>
      </c-CSortable>
    """


preview = SortableAtAGlance()
preview  # noqa: B018
````


Values must be unique. `order` can provide a full initial permutation;
otherwise declaration order wins. Disabled Items remain in order but cannot
be moved.

## Render rich items and custom handles

The default slot receives `value`, `label`, `disabled`, and zero-based `index`.
The optional `handle` slot changes only the button contents. Citry UI keeps the
native button, accessible name, focus behavior, and moving semantics.


### Reorder rich task cards

[Open the rendered preview](/v/0.4.4/ui-library/components/sortable/_previews/rich-items/)

````citry
# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SortableRichItems(Component):
    template = """
      <c-CSortable label="Reorder sprint tasks">
        <c-CSortableItem value="audit" label="Audit keyboard paths">
          <c-fill name="handle"><span aria-hidden="true">↕</span></c-fill>
          <c-fill name="default"><strong>Audit keyboard paths</strong><br /><small>Accessibility · 3 points</small></c-fill>
        </c-CSortableItem>
        <c-CSortableItem value="tokens" label="Refine theme tokens">
          <c-fill name="handle"><span aria-hidden="true">↕</span></c-fill>
          <c-fill name="default"><strong>Refine theme tokens</strong><br /><small>Design system · 2 points</small></c-fill>
        </c-CSortableItem>
        <c-CSortableItem value="locked" label="Publish release" c-disabled="True">
          <strong>Publish release</strong><br /><small>Fixed until approval</small>
        </c-CSortableItem>
      </c-CSortable>
    """


preview = SortableRichItems()
preview  # noqa: B018
````


Interactive controls may live in Item content because dragging begins only on
the handle. Avoid making the handle slot itself interactive.

## Control order from Alpine

Pass `order` and `onOrderChange` through `$c-props`. Controlled moves are
requests: the component restores the accepted order until the owner supplies
the requested permutation.


### Accept controlled reorder requests

[Open the rendered preview](/v/0.4.4/ui-library/components/sortable/_previews/controlled/)

````citry
# ruff: noqa: E501 - Alpine expression remains readable in the public example

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SortableControlled(Component):
    template = """
      <section x-data="{order:['draft','review','ship'],last:'No request'}">
        <c-CSortable $c-props="{
          order,
          onOrderChange:(next,detail)=>{order=next;last=`${detail.value}: ${detail.fromIndex + 1} → ${detail.toIndex + 1}`},
        }">
          <c-CSortableItem value="draft" label="Draft" />
          <c-CSortableItem value="review" label="Review" />
          <c-CSortableItem value="ship" label="Ship" />
        </c-CSortable>
        <output x-text="last">No request</output>
      </section>
    """


preview = SortableControlled()
preview  # noqa: B018
````


Omit client `order`, or set it to `null`, for uncontrolled behavior. An
accepted move emits native `input` then `change` from the root and calls
`onOrderChange`.

## Arrange a sortable grid

Set `layout="grid"` for cards or `layout="horizontal"` for a single row. The
keyboard uses visual inline direction in horizontal and grid layouts, including
RTL. Pointer collision uses the nearest Item center.


### Reorder a responsive grid

[Open the rendered preview](/v/0.4.4/ui-library/components/sortable/_previews/grid/)

````citry
# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SortableGrid(Component):
    template = """
      <c-CSortable layout="grid" label="Arrange dashboard cards" c-style="{'--cui-sortable-columns':'repeat(2,minmax(0,1fr))'}">
        <c-CSortableItem value="revenue" label="Revenue"><strong>Revenue</strong><br />€42,800</c-CSortableItem>
        <c-CSortableItem value="orders" label="Orders"><strong>Orders</strong><br />318</c-CSortableItem>
        <c-CSortableItem value="retention" label="Retention"><strong>Retention</strong><br />91%</c-CSortableItem>
        <c-CSortableItem value="alerts" label="Alerts"><strong>Alerts</strong><br />4 open</c-CSortableItem>
      </c-CSortable>
    """


preview = SortableGrid()
preview  # noqa: B018
````


Use `--cui-sortable-columns` to tune the responsive grid. Do not combine this
family with a partial virtual window because a partial DOM cannot expose the
complete accepted order.

## Submit the accepted order

Set `name` to submit one successful form entry per Item in accepted order.
`form` can refer to an external Form ID. A disabled root submits no entries,
and native reset restores the server order or requests it in controlled mode.


### Submit ordered priorities

[Open the rendered preview](/v/0.4.4/ui-library/components/sortable/_previews/forms/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SortableForms(Component):
    template = """
      <form>
        <c-CSortable name="priority" c-order="['security','quality','speed']">
          <c-CSortableItem value="speed" label="Delivery speed" />
          <c-CSortableItem value="quality" label="Product quality" />
          <c-CSortableItem value="security" label="Security" />
        </c-CSortable>
        <button type="reset">Reset order</button>
        <button type="submit">Save priorities</button>
      </form>
    """


preview = SortableForms()
preview  # noqa: B018
````


Application code still owns persistence. The component never sends a request
or stores order outside the current page.

## Accessibility and localization

The handle has a localized name containing the Item's plain `label`. A polite
live region announces pickup, movement, drop, and cancellation with position
and total. Explicit `*_label` inputs belong to the caller and remain fixed;
catalog defaults switch with the active Citry client locale.


### Keep fixed and disabled Items understandable

[Open the rendered preview](/v/0.4.4/ui-library/components/sortable/_previews/accessibility/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SortableAccessibility(Component):
    template = """
      <c-CSortable label="Arrange deployment checks">
        <c-CSortableItem value="backup" label="Verify backup" />
        <c-CSortableItem value="approval" label="Security approval" c-disabled="True" />
        <c-CSortableItem value="deploy" label="Deploy application" />
        <c-CSortableItem value="observe" label="Observe health metrics" />
      </c-CSortable>
    """


preview = SortableAccessibility()
preview  # noqa: B018
````


Pointer dragging has a touch delay so ordinary scrolling remains available.
Reduced-motion and forced-color preferences retain the complete interaction.
Multi-container transfer and moving tree nodes between parents are outside the
first family.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CSortable server inputs

Server inputs are passed in a template through `<c-CSortable ... />` or in Python through
`CSortable(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="sortable-input-csortable-server-inputs-id"></span>`id` | `str | None` | generated | Sets the root ID and bases stable Item IDs. |
| <span id="sortable-input-csortable-server-inputs-order"></span>`order` | `Sequence[str] | None` | `None` | Sets a full unique initial permutation; declaration order wins when omitted. |
| <span id="sortable-input-csortable-server-inputs-name"></span>`name` | `str | None` | `None` | Submits one hidden native entry per Item in accepted order. |
| <span id="sortable-input-csortable-server-inputs-form"></span>`form` | `str | None` | `None` | Associates hidden inputs with an external Form ID. |
| <span id="sortable-input-csortable-server-inputs-layout"></span>`layout` | `CSortableLayout` ([`CSortableLayout`](#sortable-interface-layout)) | `"vertical"` | Selects vertical horizontal or responsive-grid collision and layout. |
| <span id="sortable-input-csortable-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables all handles and form contribution. |
| <span id="sortable-input-csortable-server-inputs-size"></span>`size` | `CSortableSize` ([`CSortableSize`](#sortable-interface-size)) | `"md"` | Selects handle and Item density. |
| <span id="sortable-input-csortable-server-inputs-label"></span>`label` | `str` | `"Reorder items"` | Overrides the localized ordered-list accessible name. |
| <span id="sortable-input-csortable-server-inputs-handle-label"></span>`handle_label` | `str` | `"Move {item}"` | Overrides each localized handle name and must retain item. |
| <span id="sortable-input-csortable-server-inputs-instructions-label"></span>`instructions_label` | `str` | `"Press Space or Enter to pick up. Use arrow keys to move. Press Space or Enter to drop or Escape to cancel."` | Overrides hidden keyboard instructions. |
| <span id="sortable-input-csortable-server-inputs-picked-up-label"></span>`picked_up_label` | `str` | `"Picked up {item}, position {position} of {total}"` | Overrides pickup announcements and must retain item position and total. |
| <span id="sortable-input-csortable-server-inputs-moved-label"></span>`moved_label` | `str` | `"Moved {item} to position {position} of {total}"` | Overrides movement announcements and must retain item position and total. |
| <span id="sortable-input-csortable-server-inputs-dropped-label"></span>`dropped_label` | `str` | `"Dropped {item} at position {position} of {total}"` | Overrides drop announcements and must retain item position and total. |
| <span id="sortable-input-csortable-server-inputs-cancelled-label"></span>`cancelled_label` | `str` | `"Cancelled moving {item}. Position restored to {position} of {total}"` | Overrides cancellation announcements and must retain item position and total. |
| <span id="sortable-input-csortable-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#sortable-interface-class-value)) | `None` | Adds classes to the root. |
| <span id="sortable-input-csortable-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#sortable-interface-style-value)) | `None` | Adds styles to the root. |
| <span id="sortable-input-csortable-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes without replacing owned semantics or runtime markers. |

</div>

#### CSortable client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CSortable />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="sortable-input-csortable-client-inputs-order"></span>`order` | `string[] | null` | Omission or null releases control. | Controls the complete accepted permutation. |
| <span id="sortable-input-csortable-client-inputs-layout"></span>`layout` | `"vertical" | "horizontal" | "grid"` | Uses the server value. | Reactively changes layout and keyboard axes. |
| <span id="sortable-input-csortable-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server value. | Reactively disables interaction and form entries. |
| <span id="sortable-input-csortable-client-inputs-on-order-change"></span>`onOrderChange` | `function` | No component callback runs. | Receives pointer keyboard and reset requests. |

</div>

#### CSortableItem server inputs

Server inputs are passed in a template through `<c-CSortableItem ... />` or in Python
through `CSortableItem(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="sortable-input-csortable-item-server-inputs-value"></span>`value` | `str` | required | Supplies stable nonempty unique identity and submitted value. |
| <span id="sortable-input-csortable-item-server-inputs-label"></span>`label` | `str` | required | Supplies the plain Item name used by handles and announcements. |
| <span id="sortable-input-csortable-item-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Keeps the Item fixed while preserving it in the order. |
| <span id="sortable-input-csortable-item-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#sortable-interface-class-value)) | `None` | Adds classes to the rendered Item. |
| <span id="sortable-input-csortable-item-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#sortable-interface-style-value)) | `None` | Adds styles to the rendered Item. |
| <span id="sortable-input-csortable-item-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed Item attributes. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CSortable slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="sortable-slot-csortable-slots-default"></span>`default` | yes | `{}` ([`CSortableDefaultSlotData`](#sortable-interface-csortable-default-slot-data)) | None; accepts only Item declarations. |

</div>

#### CSortableItem slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="sortable-slot-csortable-item-slots-default"></span>`default` | no | `{value, label, disabled, index}` ([`CSortableItemSlotData`](#sortable-interface-csortable-item-slot-data)) | Plain label text. |
| <span id="sortable-slot-csortable-item-slots-handle"></span>`handle` | no | `{value, label, disabled, index}` ([`CSortableItemSlotData`](#sortable-interface-csortable-item-slot-data)) | A neutral drag-grip glyph inside the owned Button. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CSortable events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="sortable-event-csortable-events-order-change"></span>`onOrderChange` | `(order: string[], detail: CSortableOrderChangeDetail) => void` ([`CSortableOrderChangeDetail`](#sortable-interface-csortable-order-change-detail)) | A completed pointer keyboard reset or client reconciliation proposes another order. | `{order, previousOrder, value, fromIndex, toIndex, source, controlled, sourceEvent}` ([`CSortableOrderChangeDetail`](#sortable-interface-csortable-order-change-detail)) | Uncontrolled state commits first; controlled state requests and restores accepted order. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CSortable CSS variables

Apply these variables to `CSortable` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="sortable-css-csortable-css-variables-gap"></span>`--cui-sortable-gap` | `length` | Space between Items. | `0.625rem` |
| <span id="sortable-css-csortable-css-variables-columns"></span>`--cui-sortable-columns` | `grid-template-columns` | Responsive grid tracks. | `repeat(auto-fit, minmax(12rem, 1fr))` |
| <span id="sortable-css-csortable-css-variables-surface"></span>`--cui-sortable-item-surface` | `color` | Item surface. | `Canvas` |
| <span id="sortable-css-csortable-css-variables-border"></span>`--cui-sortable-item-border` | `complete border` | Item and handle divider. | `Adaptive 1px neutral` |
| <span id="sortable-css-csortable-css-variables-radius"></span>`--cui-sortable-item-radius` | `length` | Item and placeholder corners. | `0.625rem` |
| <span id="sortable-css-csortable-css-variables-shadow"></span>`--cui-sortable-item-shadow` | `box-shadow` | Moving Item elevation. | `Adaptive soft shadow` |
| <span id="sortable-css-csortable-css-variables-handle-size"></span>`--cui-sortable-handle-size` | `length` | Minimum handle size. | `2.75rem` |
| <span id="sortable-css-csortable-css-variables-focus"></span>`--cui-sortable-focus` | `color` | Handle focus and placeholder accent. | `Highlight` |
| <span id="sortable-css-csortable-css-variables-disabled-opacity"></span>`--cui-sortable-disabled-opacity` | `number` | Disabled Item opacity. | `0.55` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CSortable attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="sortable-attribute-csortable-attributes-data-layout"></span>`data-layout` | Root | `CSortableLayout` ([`CSortableLayout`](#sortable-interface-layout)) | Reflects current layout and collision profile. |
| <span id="sortable-attribute-csortable-attributes-data-size"></span>`data-size` | Root | `CSortableSize` ([`CSortableSize`](#sortable-interface-size)) | Reflects density. |
| <span id="sortable-attribute-csortable-attributes-data-disabled"></span>`data-disabled` | Root and disabled Items | `present | absent` | Reflects effective unavailability. |
| <span id="sortable-attribute-csortable-attributes-data-dragging"></span>`data-dragging` | Root | `present | absent` | Marks any active pointer or keyboard move. |
| <span id="sortable-attribute-csortable-attributes-data-moving"></span>`data-moving` | Item | `present | absent` | Marks the actively moved Item. |
| <span id="sortable-attribute-csortable-attributes-data-value"></span>`data-value` | Item | `string` | Exposes stable Item identity. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CSortable selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="sortable-selector-csortable-selectors-sortable"></span>`[data-citry-ui-part="sortable"]` | Root div | Theme and reflected-state destination. |
| <span id="sortable-selector-csortable-selectors-items"></span>`[data-citry-ui-part="items"]` | Ordered list | Named collection, layout, and accepted DOM order. |
| <span id="sortable-selector-csortable-selectors-item"></span>`[data-citry-ui-part="item"]` | One Item | Stable Item customization. |
| <span id="sortable-selector-csortable-selectors-handle"></span>`[data-citry-ui-part="handle"]` | Native Button | Pointer touch keyboard and focus owner. |
| <span id="sortable-selector-csortable-selectors-content"></span>`[data-citry-ui-part="content"]` | Item content div | Consumer presentation wrapper. |
| <span id="sortable-selector-csortable-selectors-placeholder"></span>`[data-citry-ui-part="placeholder"]` | Temporary list item | Proposed pointer drop position. |
| <span id="sortable-selector-csortable-selectors-status"></span>`[data-citry-ui-part="status"]` | Polite live region | Reorder announcements. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="sortable-interface-layout"></span>`CSortableLayout` | `Literal["vertical", "horizontal", "grid"]` |
| <span id="sortable-interface-size"></span>`CSortableSize` | `Literal["sm", "md", "lg"]` |
| <span id="sortable-interface-change-source"></span>`CSortableChangeSource` | `Literal["pointer", "keyboard", "reset", "client"]` |
| <span id="sortable-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="sortable-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="sortable-interface-csortable-default-slot-data"></span>

#### `CSortableDefaultSlotData`

Empty dataclass: `{}`.

<span id="sortable-interface-csortable-item-slot-data"></span>

#### `CSortableItemSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="sortable-interface-csortable-item-slot-data-value"></span>`value` | `str` | - | Stable Item value. |
| <span id="sortable-interface-csortable-item-slot-data-label"></span>`label` | `str` | - | Plain accessible label. |
| <span id="sortable-interface-csortable-item-slot-data-disabled"></span>`disabled` | `bool` | - | Declared disabled state. |
| <span id="sortable-interface-csortable-item-slot-data-index"></span>`index` | `int` | - | Initial zero-based accepted index. |

</div>

<span id="sortable-interface-csortable-order-change-detail"></span>

#### `CSortableOrderChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="sortable-interface-csortable-order-change-detail-order"></span>`order` | `list[str]` | - | Requested or committed order. |
| <span id="sortable-interface-csortable-order-change-detail-previous-order"></span>`previousOrder` | `list[str]` | - | Accepted order before the move. |
| <span id="sortable-interface-csortable-order-change-detail-value"></span>`value` | `str` | - | Moved Item value. |
| <span id="sortable-interface-csortable-order-change-detail-from-index"></span>`fromIndex` | `int` | - | Previous zero-based index. |
| <span id="sortable-interface-csortable-order-change-detail-to-index"></span>`toIndex` | `int` | - | Proposed zero-based index. |
| <span id="sortable-interface-csortable-order-change-detail-source"></span>`source` | `CSortableChangeSource` ([`CSortableChangeSource`](#sortable-interface-change-source)) | - | Pointer keyboard reset or client cause. |
| <span id="sortable-interface-csortable-order-change-detail-controlled"></span>`controlled` | `bool` | - | Whether client order owns accepted state. |
| <span id="sortable-interface-csortable-order-change-detail-source-event"></span>`sourceEvent` | `object | None` | - | Native source Event or null. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CSortable translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="sortable-translation-csortable-translations-label"></span>`citry-ui-sortable-label` | Names the collection. | `None.` | `label` | Stable `$c-tr` attribute. |
| <span id="sortable-translation-csortable-translations-handle"></span>`citry-ui-sortable-handle` | Names each handle. | `item: str` | `handle_label` with `{item}` | Stable reactive `$c-tr` attribute. |
| <span id="sortable-translation-csortable-translations-instructions"></span>`citry-ui-sortable-instructions` | Explains keyboard operation. | `None.` | `instructions_label` | Server HTML; instructions do not change while a move is active. |
| <span id="sortable-translation-csortable-translations-picked-up"></span>`citry-ui-sortable-picked-up` | Announces pickup. | `item: str; position: str; total: str` | `picked_up_label` | One-shot `i18n.tr()` live-region output. |
| <span id="sortable-translation-csortable-translations-moved"></span>`citry-ui-sortable-moved` | Announces a proposed position. | `item: str; position: str; total: str` | `moved_label` | One-shot `i18n.tr()` live-region output. |
| <span id="sortable-translation-csortable-translations-dropped"></span>`citry-ui-sortable-dropped` | Announces accepted drop. | `item: str; position: str; total: str` | `dropped_label` | One-shot `i18n.tr()` live-region output. |
| <span id="sortable-translation-csortable-translations-cancelled"></span>`citry-ui-sortable-cancelled` | Announces cancellation and restored position. | `item: str; position: str; total: str` | `cancelled_label` | One-shot `i18n.tr()` live-region output. |

</div>