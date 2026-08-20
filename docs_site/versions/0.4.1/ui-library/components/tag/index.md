---
title: Tag and TagGroup
url: https://citry.dev/v/0.4.1/ui-library/components/tag/
description: "Present descriptive, selectable, actionable, and removable Tag collections."
---
# Tag and TagGroup

Use `CTagGroup` for a labelled collection of compact categories, filters, or
keywords. A descriptive group renders list semantics. Selection, actions, or
removal switch it to one keyboard-operable grid.


### TagGroup at a glance

[Open the rendered preview](/v/0.4.1/ui-library/components/tag/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagGlance(Component):
    template = """
      <c-CStack gap="lg">
        <c-CTagGroup label="Topics">
          <c-CTag value="css">CSS</c-CTag>
          <c-CTag value="html">HTML</c-CTag>
          <c-CTag value="accessibility">Accessibility</c-CTag>
        </c-CTagGroup>
        <c-CTagGroup label="Amenities" selection_mode="multiple" c-value="['wifi']">
          <c-CTag value="wifi">Wi-Fi</c-CTag>
          <c-CTag value="parking">Parking</c-CTag>
          <c-CTag value="pool">Pool</c-CTag>
        </c-CTagGroup>
      </c-CStack>
    """


preview = TagGlance()
preview  # noqa: B018
````



```citry-html
<c-CTagGroup label="Topics">
  <c-CTag value="css">CSS</c-CTag>
  <c-CTag value="html">HTML</c-CTag>
</c-CTagGroup>
```


## Select Tags

Choose a selection mode and give every Tag a unique value.


### Select Tags

[Open the rendered preview](/v/0.4.1/ui-library/components/tag/_previews/selection/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagSelection(Component):
    template = """
      <div x-data="{chosen: ['quiet']}" class="citry-ui-demo-stack">
        <c-CTagGroup
          label="Workspace qualities"
          selection_mode="multiple"
          $c-props="{value: chosen, onValueChange: (value) => chosen = value}"
        >
          <c-CTag value="quiet">Quiet</c-CTag>
          <c-CTag value="bright">Bright</c-CTag>
          <c-CTag value="central">Central</c-CTag>
        </c-CTagGroup>
        <output x-text="chosen.join(', ')"></output>
      </div>
    """


preview = TagSelection()
preview  # noqa: B018
````



```citry-html
<c-CTagGroup
  label="Amenities"
  selection_mode="multiple"
  c-value="['wifi']"
  $c-props="{
    value: selectedAmenities,
    onValueChange: (value) => selectedAmenities = value
  }"
>
  <c-CTag value="wifi">Wi-Fi</c-CTag>
  <c-CTag value="parking">Parking</c-CTag>
  <c-CTag value="pool">Pool</c-CTag>
</c-CTagGroup>
```


A supplied client `value` is authoritative. The callback requests the next
selection; it does not mutate a controlled group. Omit the prop to release
control while preserving the last effective selection. `mandatory=True`
prevents user activation from clearing the final selection.

## Actions and removal

`actionable=True` reports enabled Tag activation through `onAction`.
`removable=True` adds one form-safe remove Button and enables Delete and
Backspace. Removal is a request: update your collection to remove the values.


### Request Tag removal

[Open the rendered preview](/v/0.4.1/ui-library/components/tag/_previews/removal/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagRemoval(Component):
    template = """
      <div x-data="{last: 'None'}" class="citry-ui-demo-stack">
        <c-CTagGroup
          label="Project topics"
          removable
          $c-props="{onRemove: (values) => last = values.join(', ')}"
        >
          <c-CTag value="Design">Design</c-CTag>
          <c-CTag value="Research">Research</c-CTag>
          <c-CTag value="Delivery">Delivery</c-CTag>
        </c-CTagGroup>
        <output x-text="`Requested removal: ${last}`"></output>
      </div>
    """


preview = TagRemoval()
preview  # noqa: B018
````



### Run Tag actions

[Open the rendered preview](/v/0.4.1/ui-library/components/tag/_previews/actions/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagActions(Component):
    template = """
      <div x-data="{last: 'None'}" class="citry-ui-demo-stack">
        <c-CTagGroup
          label="Open view"
          actionable
          $c-props="{onAction: (value) => last = value}"
        >
          <c-CTag value="overview">Overview</c-CTag>
          <c-CTag value="activity">Activity</c-CTag>
          <c-CTag value="settings">Settings</c-CTag>
        </c-CTagGroup>
        <output x-text="`Last action: ${last}`"></output>
      </div>
    """


preview = TagActions()
preview  # noqa: B018
````



```citry-html
<c-CTagGroup
  label="Saved filters"
  removable
  $c-props="{
    onRemove: (values) => removeSavedFilters(values)
  }"
>
  <c-CTag value="open">Open</c-CTag>
  <c-CTag value="assigned">Assigned to me</c-CTag>
</c-CTagGroup>
```


When a selected Tag in multiple mode receives Delete, the request includes all
selected removable values. Focus follows retained values across reorder and
moves to the nearest following Tag after removal.

## Content

The default slot is the Tag label. `start` accepts decorative noninteractive
phrasing content such as an Icon or Avatar.


### Compose Tag content

[Open the rendered preview](/v/0.4.1/ui-library/components/tag/_previews/content/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagContent(Component):
    template = """
      <div style="max-inline-size: 22rem">
        <c-CTagGroup label="People">
          <c-CTag value="ava">
            <c-fill name="start"><c-CAvatar alt="Ava" size="sm">A</c-CAvatar></c-fill>
            <c-fill name="default">Ava, accessibility research</c-fill>
          </c-CTag>
          <c-CTag value="leo">
            <c-fill name="start"><c-CAvatar alt="Leo" size="sm">L</c-CAvatar></c-fill>
            <c-fill name="default">Leo, design systems</c-fill>
          </c-CTag>
        </c-CTagGroup>
      </div>
    """


preview = TagContent()
preview  # noqa: B018
````



```citry-html
<c-CTagGroup label="People">
  <c-CTag value="ava">
    <c-fill name="start"><c-CAvatar alt="Ava" size="sm">A</c-CAvatar></c-fill>
    <c-fill name="default">Ava</c-fill>
  </c-CTag>
</c-CTagGroup>
```


Tag content must not contain links, Buttons, form controls, focusable content,
or nested Tags. Use a native anchor outside TagGroup when the job is
navigation. Free-form entry and editing belong to `CTagsInput`.

## Keyboard behavior

- Arrow keys move through enabled Tags and wrap.
- Home and End move to the first and last enabled Tag.
- Typing moves to the next matching Tag label or `text_value`.
- Enter and Space activate selection and actions.
- Delete and Backspace request removal.
- Tab from a removable Tag reaches its remove Button; Shift+Tab returns.

The group has one page-tab entry. Descriptive groups remain ordinary lists and
do not add keyboard stops.

## Disabledness and forms

Group disabledness, item disabledness, `CForm.disabled`, and native disabled
fieldsets all dominate interaction. TagGroup is not a form control and adds no
FormData. Owned remove Buttons always use `type="button"`.

## Presentation and customization

Variants are `soft`, `solid`, and `outline`. Sizes are `sm`, `md`, and `lg`.
Customize through public variables or stable part selectors:


### Compare Tag variants and sizes

[Open the rendered preview](/v/0.4.1/ui-library/components/tag/_previews/variants/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagVariants(Component):
    template = """
      <c-CStack gap="lg">
        <c-CTagGroup
          c-for="variant in ['soft', 'solid', 'outline']"
          c-label="variant"
          c-variant="variant"
          selection_mode="single"
          value="one"
        >
          <c-CTag value="one">Selected</c-CTag><c-CTag value="two">Available</c-CTag>
        </c-CTagGroup>
        <c-CTagGroup c-for="size in ['sm', 'md', 'lg']" c-label="size" c-size="size">
          <c-CTag value="sample">Sample</c-CTag>
        </c-CTagGroup>
      </c-CStack>
    """


preview = TagVariants()
preview  # noqa: B018
````



### Customize Tags

[Open the rendered preview](/v/0.4.1/ui-library/components/tag/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagCustomization(Component):
    css = """
      :where(.forest-tags) {
        --cui-tag-selected-background: #176b4d;
        --cui-tag-selected-foreground: #fff;
        --cui-tag-radius: 0.45rem;
      }
    """
    template = """
      <c-CTagGroup label="Forest filters" class_="forest-tags" selection_mode="multiple" c-value="['fern']">
        <c-CTag value="fern">Fern</c-CTag>
        <c-CTag value="moss">Moss</c-CTag>
        <c-CTag value="river">River</c-CTag>
      </c-CTagGroup>
    """


preview = TagCustomization()
preview  # noqa: B018
````



```css
.brand-tags {
  --cui-tag-selected-background: #176b4d;
  --cui-tag-selected-foreground: #fff;
  --cui-tag-radius: 0.5rem;
}
```


See [`api.yml`](api.yml) for the exhaustive inputs, callbacks, variables,
attributes, selectors, slots, and public interfaces.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CTagGroup server inputs

Server inputs are passed in a template through `<c-CTagGroup ... />` or in Python through
`CTagGroup(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="tag-input-ctag-group-server-inputs-label"></span>`label` | `str` | required | Supplies the visible fallback label and accessible group name. |
| <span id="tag-input-ctag-group-server-inputs-id"></span>`id` | `str | None` | `None` | Supplies the exact root and relationship prefix. |
| <span id="tag-input-ctag-group-server-inputs-value"></span>`value` | `str | Sequence[str] | None` ([`CTagValue`](#tag-interface-value)) | `None` | Sets initial single or multiple selection. |
| <span id="tag-input-ctag-group-server-inputs-selection-mode"></span>`selection_mode` | `"none" | "single" | "multiple"` ([`CTagSelectionMode`](#tag-interface-selection-mode)) | `"none"` | Selects descriptive or selectable behavior. |
| <span id="tag-input-ctag-group-server-inputs-mandatory"></span>`mandatory` | `bool` | `False` | Prevents activation from clearing the final selection. |
| <span id="tag-input-ctag-group-server-inputs-actionable"></span>`actionable` | `bool` | `False` | Enables Tag action callbacks. |
| <span id="tag-input-ctag-group-server-inputs-removable"></span>`removable` | `bool` | `False` | Adds form-safe remove Buttons and deletion keys. |
| <span id="tag-input-ctag-group-server-inputs-remove-label"></span>`remove_label` | `str` | `"Remove"` | Supplies the translated remove action label. |
| <span id="tag-input-ctag-group-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables the owned collection; Form and fieldset disabledness remain dominant. |
| <span id="tag-input-ctag-group-server-inputs-variant"></span>`variant` | `"soft" | "solid" | "outline"` ([`CTagVariant`](#tag-interface-variant)) | `"soft"` | Selects visual treatment. |
| <span id="tag-input-ctag-group-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CTagSize`](#tag-interface-size)) | `"md"` | Selects Tag geometry. |
| <span id="tag-input-ctag-group-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#tag-interface-class-value)) | `None` | Adds root classes. |
| <span id="tag-input-ctag-group-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#tag-interface-style-value)) | `None` | Adds root inline styles. |
| <span id="tag-input-ctag-group-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted root attributes without replacing owned semantics. |

</div>

#### CTagGroup client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CTagGroup />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="tag-input-ctag-group-client-inputs-value"></span>`value` | `string | null | string[] | undefined` | Releases control and preserves the last effective selection. | Controls selection while supplied. |
| <span id="tag-input-ctag-group-client-inputs-disabled"></span>`disabled` | `boolean | undefined` | Uses the server fallback. | Overrides local disabledness while valid. |
| <span id="tag-input-ctag-group-client-inputs-variant"></span>`variant` | `"soft" | "solid" | "outline" | undefined` | Uses the server fallback. | Overrides visual treatment while valid. |
| <span id="tag-input-ctag-group-client-inputs-size"></span>`size` | `"sm" | "md" | "lg" | undefined` | Uses the server fallback. | Overrides geometry while valid. |
| <span id="tag-input-ctag-group-client-inputs-on-value-change"></span>`onValueChange` | `((value, detail) => void) | undefined` | No selection notification. | Receives selection requests. |
| <span id="tag-input-ctag-group-client-inputs-on-action"></span>`onAction` | `((value, detail) => void) | undefined` | No action notification. | Receives enabled actionable Tag activation. |
| <span id="tag-input-ctag-group-client-inputs-on-remove"></span>`onRemove` | `((values, detail) => void) | undefined` | No removal notification. | Receives remove Button or deletion-key requests. |

</div>

#### CTag server inputs

Server inputs are passed in a template through `<c-CTag ... />` or in Python through
`CTag(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="tag-input-ctag-server-inputs-value"></span>`value` | `str` | required | Supplies unique canonical identity within the group. |
| <span id="tag-input-ctag-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables this Tag. |
| <span id="tag-input-ctag-server-inputs-text-value"></span>`text_value` | `str | None` | `None` | Supplies typeahead text instead of current label text. |
| <span id="tag-input-ctag-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#tag-interface-class-value)) | `None` | Adds Tag-root classes. |
| <span id="tag-input-ctag-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#tag-interface-style-value)) | `None` | Adds Tag-root inline styles. |
| <span id="tag-input-ctag-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted Tag-root attributes without replacing owned semantics. |

</div>

#### CTag client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CTag />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="tag-input-ctag-client-inputs-disabled"></span>`disabled` | `boolean | undefined` | Uses the server fallback. | Overrides item-local disabledness while valid. |
| <span id="tag-input-ctag-client-inputs-text-value"></span>`textValue` | `string | null | undefined` | Uses server text or current label text. | Overrides typeahead text while valid. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CTagGroup slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="tag-slot-ctag-group-slots-default"></span>`default` | yes | `{}` ([`CTagGroupDefaultSlotData`](#tag-interface-group-default-slot)) | None. |
| <span id="tag-slot-ctag-group-slots-label"></span>`label` | no | `{}` ([`CTagGroupLabelSlotData`](#tag-interface-group-label-slot)) | Escaped label input. |
| <span id="tag-slot-ctag-group-slots-description"></span>`description` | no | `{}` ([`CTagGroupDescriptionSlotData`](#tag-interface-group-description-slot)) | Wrapper omitted. |

</div>

#### CTag slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="tag-slot-ctag-slots-default"></span>`default` | yes | `{}` ([`CTagDefaultSlotData`](#tag-interface-tag-default-slot)) | None. |
| <span id="tag-slot-ctag-slots-start"></span>`start` | no | `{}` ([`CTagStartSlotData`](#tag-interface-tag-start-slot)) | Wrapper omitted. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CTagGroup events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="tag-event-ctag-events-on-value-change"></span>`onValueChange` | `(value, detail: CTagValueChangeDetail) => void` ([`CTagValueChangeDetail`](#tag-interface-value-change-detail)) | Enabled selectable Tag proposes a different value. | `{value, previousValue, tagValue, source, controlled, nativeEvent}` ([`CTagValueChangeDetail`](#tag-interface-value-change-detail)) | Runs before onAction; supplied client value remains authoritative. |
| <span id="tag-event-ctag-events-on-action"></span>`onAction` | `(value: str, detail: CTagActionDetail) => void` ([`CTagActionDetail`](#tag-interface-action-detail)) | Enabled actionable Tag activates. | `{value, source, nativeEvent}` ([`CTagActionDetail`](#tag-interface-action-detail)) | Runs after a selection request. |
| <span id="tag-event-ctag-events-on-remove"></span>`onRemove` | `(values: list[str], detail: CTagRemoveDetail) => void` ([`CTagRemoveDetail`](#tag-interface-remove-detail)) | Remove Button or Delete and Backspace. | `{values, tagValue, source, nativeEvent}` ([`CTagRemoveDetail`](#tag-interface-remove-detail)) | Requests owner collection removal without changing structure. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CTagGroup CSS variables

Apply these variables to `CTagGroup` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="tag-css-ctag-css-variables-gap"></span>`--cui-tag-gap` | `length` | Inline gap between Tags. | `0.5rem` |
| <span id="tag-css-ctag-css-variables-row-gap"></span>`--cui-tag-row-gap` | `length` | Gap between wrapped rows. | `0.5rem` |
| <span id="tag-css-ctag-css-variables-background"></span>`--cui-tag-background` | `color` | Unselected fill. | `Variant and scheme derived.` |
| <span id="tag-css-ctag-css-variables-foreground"></span>`--cui-tag-foreground` | `color` | Unselected text. | `Variant and scheme derived.` |
| <span id="tag-css-ctag-css-variables-border-color"></span>`--cui-tag-border-color` | `color` | Tag border. | `Scheme-derived neutral.` |
| <span id="tag-css-ctag-css-variables-selected-background"></span>`--cui-tag-selected-background` | `color` | Selected fill. | `Scheme-derived primary.` |
| <span id="tag-css-ctag-css-variables-selected-foreground"></span>`--cui-tag-selected-foreground` | `color` | Selected text. | `White.` |
| <span id="tag-css-ctag-css-variables-selected-border-color"></span>`--cui-tag-selected-border-color` | `color` | Selected border. | `Selected background.` |
| <span id="tag-css-ctag-css-variables-focus-color"></span>`--cui-tag-focus-color` | `color` | Focus outline. | `Highlight` |
| <span id="tag-css-ctag-css-variables-radius"></span>`--cui-tag-radius` | `length` | Tag corner radius. | `999px` |
| <span id="tag-css-ctag-css-variables-min-height"></span>`--cui-tag-min-height` | `length` | Minimum Tag block size. | `Size derived.` |
| <span id="tag-css-ctag-css-variables-padding-inline"></span>`--cui-tag-padding-inline` | `length` | Tag inline padding. | `Size derived.` |
| <span id="tag-css-ctag-css-variables-internal-gap"></span>`--cui-tag-internal-gap` | `length` | Gap between internal parts. | `Size derived.` |
| <span id="tag-css-ctag-css-variables-font-size"></span>`--cui-tag-font-size` | `length` | Tag label size. | `Size derived.` |
| <span id="tag-css-ctag-css-variables-label-color"></span>`--cui-tag-label-color` | `color` | Group-label foreground. | `CanvasText` |
| <span id="tag-css-ctag-css-variables-description-color"></span>`--cui-tag-description-color` | `color` | Description foreground. | `Scheme-derived muted text.` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CTagGroup attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="tag-attribute-ctag-group-attributes-selection-mode"></span>`data-selection-mode` | Group root | `"none" | "single" | "multiple"` | Reflects collection behavior. |
| <span id="tag-attribute-ctag-group-attributes-actionable"></span>`data-actionable` | Group root | `present-or-absent` | Present when action callbacks are enabled. |
| <span id="tag-attribute-ctag-group-attributes-removable"></span>`data-removable` | Group root | `present-or-absent` | Present when removal is enabled. |
| <span id="tag-attribute-ctag-group-attributes-disabled"></span>`data-disabled` | Group root | `present-or-absent` | Mirrors effective group disabledness. |
| <span id="tag-attribute-ctag-group-attributes-variant"></span>`data-variant` | Group root and Tag | `"soft" | "solid" | "outline"` | Reflects visual treatment. |
| <span id="tag-attribute-ctag-group-attributes-size"></span>`data-size` | Group root and Tag | `"sm" | "md" | "lg"` | Reflects geometry. |

</div>

#### CTag attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="tag-attribute-ctag-attributes-value"></span>`data-value` | Tag root | `string` | Exposes canonical identity. |
| <span id="tag-attribute-ctag-attributes-selected"></span>`data-selected` | Tag root | `present-or-absent` | Mirrors effective selection. |
| <span id="tag-attribute-ctag-attributes-disabled"></span>`data-disabled` | Tag root | `present-or-absent` | Mirrors effective item disabledness. |
| <span id="tag-attribute-ctag-attributes-removable"></span>`data-removable` | Tag root | `present-or-absent` | Present when the remove affordance exists. |
| <span id="tag-attribute-ctag-attributes-aria-selected"></span>`aria-selected` | Selectable Tag row | `boolean` | Exposes selection to assistive technology. |
| <span id="tag-attribute-ctag-attributes-aria-disabled"></span>`aria-disabled` | Interactive Tag row | `boolean` | Exposes effective disabledness. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CTagGroup selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="tag-selector-ctag-selectors-group"></span>`[data-citry-ui-part="tag-group"]` | Group root | Stable group and attrs destination. |
| <span id="tag-selector-ctag-selectors-group-label"></span>`[data-citry-ui-part="group-label"]` | Visible group label | Names the collection. |
| <span id="tag-selector-ctag-selectors-list"></span>`[data-citry-ui-part="list"]` | List or grid | Stable direct collection surface. |
| <span id="tag-selector-ctag-selectors-description"></span>`[data-citry-ui-part="description"]` | Optional description | Describes the collection. |
| <span id="tag-selector-ctag-selectors-tag"></span>`[data-citry-ui-part="tag"]` | Tag root | Stable Tag and attrs destination. |
| <span id="tag-selector-ctag-selectors-indicator"></span>`[data-citry-ui-part="indicator"]` | Selection indicator | Exposes selected state visually. |
| <span id="tag-selector-ctag-selectors-start"></span>`[data-citry-ui-part="start"]` | Decorative start wrapper | Positions composed decoration. |
| <span id="tag-selector-ctag-selectors-tag-label"></span>`[data-citry-ui-part="tag-label"]` | Tag label | Supplies the accessible Tag name. |
| <span id="tag-selector-ctag-selectors-remove"></span>`[data-citry-ui-part="remove"]` | Native Button | Requests removal. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="tag-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="tag-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="tag-interface-selection-mode"></span>`CTagSelectionMode` | `Literal["none", "single", "multiple"]` |
| <span id="tag-interface-variant"></span>`CTagVariant` | `Literal["soft", "solid", "outline"]` |
| <span id="tag-interface-size"></span>`CTagSize` | `Literal["sm", "md", "lg"]` |
| <span id="tag-interface-value"></span>`CTagValue` | `str | None | Sequence[str]` |

</div>

<span id="tag-interface-value-change-detail"></span>

#### `CTagValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tag-interface-value-change-detail-value"></span>`value` | `str | list[str] | None` | - | Requested selection. |
| <span id="tag-interface-value-change-detail-previous-value"></span>`previousValue` | `str | list[str] | None` | - | Selection before activation. |
| <span id="tag-interface-value-change-detail-tag-value"></span>`tagValue` | `str` | - | Activated Tag identity. |
| <span id="tag-interface-value-change-detail-source"></span>`source` | `"activation"` | - | Change origin. |
| <span id="tag-interface-value-change-detail-controlled"></span>`controlled` | `bool` | - | Whether client value controls selection. |
| <span id="tag-interface-value-change-detail-native-event"></span>`nativeEvent` | `Event` | - | Triggering native event. |

</div>

<span id="tag-interface-action-detail"></span>

#### `CTagActionDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tag-interface-action-detail-value"></span>`value` | `str` | - | Activated Tag identity. |
| <span id="tag-interface-action-detail-source"></span>`source` | `"activation"` | - | Action origin. |
| <span id="tag-interface-action-detail-native-event"></span>`nativeEvent` | `Event` | - | Triggering native event. |

</div>

<span id="tag-interface-remove-detail"></span>

#### `CTagRemoveDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tag-interface-remove-detail-values"></span>`values` | `list[str]` | - | Requested removal identities. |
| <span id="tag-interface-remove-detail-tag-value"></span>`tagValue` | `str` | - | Tag that received the removal action. |
| <span id="tag-interface-remove-detail-source"></span>`source` | `"remove-button" | "delete-key"` | - | Removal origin. |
| <span id="tag-interface-remove-detail-native-event"></span>`nativeEvent` | `Event` | - | Triggering native event. |

</div>

<span id="tag-interface-group-default-slot"></span>

#### `CTagGroupDefaultSlotData`

Empty dataclass: `{}`.

<span id="tag-interface-group-label-slot"></span>

#### `CTagGroupLabelSlotData`

Empty dataclass: `{}`.

<span id="tag-interface-group-description-slot"></span>

#### `CTagGroupDescriptionSlotData`

Empty dataclass: `{}`.

<span id="tag-interface-tag-default-slot"></span>

#### `CTagDefaultSlotData`

Empty dataclass: `{}`.

<span id="tag-interface-tag-start-slot"></span>

#### `CTagStartSlotData`

Empty dataclass: `{}`.

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CTagGroup translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="tag-translation-ctag-group-translations-remove"></span>`citry-ui-tag-remove` | Supplies hidden accessible text for every remove control. | `None` | `remove_label` input | $c-tr updates text content. |

</div>