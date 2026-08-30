---
title: List
url: https://citry.dev/v/0.4.6/ui-library/components/list/
description: "Compose semantic content, navigation, and action lists with Citry UI."
---
# List

Use `CList` and `CListItem` for concise semantic collections. Items can stay static, navigate, or act as native Buttons.

## List at a glance


### List at a glance

[Open the rendered preview](/v/0.4.6/ui-library/components/list/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListGlance(Component):
    template = """
      <c-CList label="Recent observations" variant="surface" c-divided="True">
        <c-CListItem href="/observations/aurora" c-current="True">Aurora over Tromsø</c-CListItem>
        <c-CListItem href="/observations/comet">Comet C/2026 Q2</c-CListItem>
        <c-CListItem href="/observations/eclipse">Lunar eclipse</c-CListItem>
      </c-CList>
    """


preview = ListGlance()
preview  # noqa: B018
````


## Present semantic content


### Present semantic list content

[Open the rendered preview](/v/0.4.6/ui-library/components/list/_previews/content/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListContent(Component):
    template = """
      <c-CList c-ordered="True" marker="decimal" c-start="3">
        <c-CListItem>Align the telescope</c-CListItem>
        <c-CListItem>Calibrate the camera</c-CListItem>
        <c-CListItem>Begin the exposure</c-CListItem>
      </c-CList>
    """


preview = ListContent()
preview  # noqa: B018
````


## Build navigation

Set `href` on an Item for a whole-row link. `current=True` adds `aria-current="page"`.


### Build list navigation

[Open the rendered preview](/v/0.4.6/ui-library/components/list/_previews/navigation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListNavigation(Component):
    template = """
      <nav aria-label="Observatory">
        <c-CList variant="surface">
          <c-CListItem href="/sky" c-current="True">Sky map</c-CListItem>
          <c-CListItem href="/sessions">Sessions</c-CListItem>
          <c-CListItem href="/equipment">Equipment</c-CListItem>
        </c-CList>
      </nav>
    """


preview = ListNavigation()
preview  # noqa: B018
````


## Add media, descriptions, and trailing content


### Compose List Item anatomy

[Open the rendered preview](/v/0.4.6/ui-library/components/list/_previews/anatomy/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListAnatomy(Component):
    template = """
      <c-CList label="Specimens" c-divided="True">
        <c-CListItem>
          <c-fill name="start"><c-CAvatar alt="Mare Imbrium" /></c-fill>
          <c-fill name="default">Mare Imbrium basalt</c-fill>
          <c-fill name="description">Apollo 15 · sample 15555</c-fill>
          <c-fill name="end"><c-CBadge variant="outline">Lunar</c-CBadge></c-fill>
        </c-CListItem>
        <c-CListItem>
          <c-fill name="start"><c-CIcon name="star" /></c-fill>
          <c-fill name="default">Murchison meteorite</c-fill>
          <c-fill name="description">Carbonaceous chondrite · 1969</c-fill>
          <c-fill name="end">12.4 g</c-fill>
        </c-CListItem>
      </c-CList>
    """


preview = ListAnatomy()
preview  # noqa: B018
````


## Add whole-row and secondary actions

Use `action=True` for one whole-row Button. Keep an Item static when its end slot contains a separate control.


### Compose List actions

[Open the rendered preview](/v/0.4.6/ui-library/components/list/_previews/actions/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListActions(Component):
    template = """
      <c-CList label="Observation queue" variant="surface">
        <c-CListItem c-action="True" @click="console.log('opened')">Open current session</c-CListItem>
        <c-CListItem>
          <c-fill name="default">Nightly calibration</c-fill>
          <c-fill name="description">Ready to archive</c-fill>
          <c-fill name="end"><c-CButton size="sm" variant="outline">Archive</c-CButton></c-fill>
        </c-CListItem>
      </c-CList>
    """


preview = ListActions()
preview  # noqa: B018
````


## Nest Lists


### Nest semantic Lists

[Open the rendered preview](/v/0.4.6/ui-library/components/list/_previews/nested/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NestedList(Component):
    template = """
      <c-CList label="Solar system" marker="disc">
        <c-CListItem>
          <c-fill name="default">
            Inner planets
            <c-CList marker="disc">
              <c-CListItem>Mercury</c-CListItem>
              <c-CListItem>Venus</c-CListItem>
              <c-CListItem>Earth</c-CListItem>
            </c-CList>
          </c-fill>
        </c-CListItem>
        <c-CListItem>Outer planets</c-CListItem>
      </c-CList>
    """


preview = NestedList()
preview  # noqa: B018
````


## Choose density and dividers


### Choose List presentation

[Open the rendered preview](/v/0.4.6/ui-library/components/list/_previews/presentation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListPresentation(Component):
    template = """
      <c-CCol gap="lg">
        <c-CList label="Comfortable list" variant="surface">
          <c-CListItem>Andromeda Galaxy</c-CListItem>
          <c-CListItem>Triangulum Galaxy</c-CListItem>
        </c-CList>
        <c-CList label="Compact divided list" density="compact" c-divided="True">
          <c-CListItem>Whirlpool Galaxy</c-CListItem>
          <c-CListItem>Sombrero Galaxy</c-CListItem>
        </c-CList>
      </c-CCol>
    """


preview = ListPresentation()
preview  # noqa: B018
````


## Customize List


### Customize List

[Open the rendered preview](/v/0.4.6/ui-library/components/list/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListCustomization(Component):
    template = """
      <c-CList class_="violet-list" label="Nebula catalog" variant="surface">
        <c-CListItem href="/nebula/orion" c-current="True">Orion Nebula</c-CListItem>
        <c-CListItem href="/nebula/lagoon">Lagoon Nebula</c-CListItem>
      </c-CList>
    """
    css = """
      :where(.violet-list) {
        --cui-list-current-background: light-dark(#ede9fe, #4c1d95);
        --cui-list-radius: 1rem;
      }
    """


preview = ListCustomization()
preview  # noqa: B018
````


## Accessibility and behavior

Lists retain native `ul`/`ol` and `li` semantics. Only links, whole-row Buttons, and authored secondary controls enter Tab order. Use Menu for command popovers, Tabs for view switching, and DataTable for two-dimensional records.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CList server inputs

Server inputs are passed in a template through `<c-CList ... />` or in Python through
`CList(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="list-input-clist-server-inputs-ordered"></span>`ordered` | `bool` | `False` | Renders ol instead of ul. |
| <span id="list-input-clist-server-inputs-start"></span>`start` | `int | None` | `None` | Sets native ordered-list numbering start. |
| <span id="list-input-clist-server-inputs-reversed"></span>`reversed` | `bool` | `False` | Reverses native ordered-list numbering. |
| <span id="list-input-clist-server-inputs-marker"></span>`marker` | `"none" | "disc" | "decimal"` ([`CListMarker`](#list-interface-input-type-aliases-list-marker)) | `"none"` | Selects no marker or a semantic unordered/ordered marker. |
| <span id="list-input-clist-server-inputs-density"></span>`density` | `"comfortable" | "compact"` ([`CListDensity`](#list-interface-input-type-aliases-list-density)) | `"comfortable"` | Selects item spacing. |
| <span id="list-input-clist-server-inputs-variant"></span>`variant` | `"plain" | "surface"` ([`CListVariant`](#list-interface-input-type-aliases-list-variant)) | `"plain"` | Selects transparent or quiet item surfaces. |
| <span id="list-input-clist-server-inputs-divided"></span>`divided` | `bool` | `False` | Draws dividers between direct Items. |
| <span id="list-input-clist-server-inputs-label"></span>`label` | `str | None` | `None` | Optionally names the list. |
| <span id="list-input-clist-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#list-interface-input-type-aliases-class-value)) | `None` | Adds root classes. |
| <span id="list-input-clist-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#list-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles. |
| <span id="list-input-clist-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted copied list attributes without replacing semantics, children, or runtime fields. |

</div>

#### CListItem server inputs

Server inputs are passed in a template through `<c-CListItem ... />` or in Python through
`CListItem(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="list-input-clist-item-server-inputs-href"></span>`href` | `str | None` | `None` | Makes the whole Item a native link; disabled Items render static content. |
| <span id="list-input-clist-item-server-inputs-action"></span>`action` | `bool` | `False` | Makes the whole Item a native type=button action; cannot combine with href. |
| <span id="list-input-clist-item-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Removes link/action interaction and reflects disabled styling. |
| <span id="list-input-clist-item-server-inputs-current"></span>`current` | `bool` | `False` | Emits aria-current=page on an enabled link. |
| <span id="list-input-clist-item-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#list-interface-input-type-aliases-class-value)) | `None` | Adds li classes. |
| <span id="list-input-clist-item-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#list-interface-input-type-aliases-style-value)) | `None` | Adds li inline styles. |
| <span id="list-input-clist-item-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied li attributes without replacing Item semantics. |
| <span id="list-input-clist-item-server-inputs-surface-attrs"></span>`surface_attrs` | `Mapping[str, object] | None` | `None` | Adds copied static/link/Button surface attributes without replacing its identity or behavior. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CList slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="list-slot-clist-slots-default"></span>`default` | yes | `{}` ([`CListDefaultSlotData`](#list-interface-clist-default-slot-data)) | None. |

</div>

#### CListItem slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="list-slot-clist-item-slots-start"></span>`start` | no | `{}` ([`CListItemStartSlotData`](#list-interface-clist-item-start-slot-data)) | No leading media. |
| <span id="list-slot-clist-item-slots-default"></span>`default` | yes | `{}` ([`CListItemDefaultSlotData`](#list-interface-clist-item-default-slot-data)) | None. |
| <span id="list-slot-clist-item-slots-description"></span>`description` | no | `{}` ([`CListItemDescriptionSlotData`](#list-interface-clist-item-description-slot-data)) | No supplemental text. |
| <span id="list-slot-clist-item-slots-end"></span>`end` | no | `{}` ([`CListItemEndSlotData`](#list-interface-clist-item-end-slot-data)) | No trailing metadata or secondary action. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CList CSS variables

Apply these variables to `CList` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="list-css-clist-css-variables-cui-list-gap"></span>`--cui-list-gap` | `length` | Gap between direct Items. | `0.25rem` |
| <span id="list-css-clist-css-variables-cui-list-padding"></span>`--cui-list-padding` | `length` | Root padding. | `0.35rem` |
| <span id="list-css-clist-css-variables-cui-list-item-padding"></span>`--cui-list-item-padding` | `length` | Item surface padding. | `Density-derived.` |
| <span id="list-css-clist-css-variables-cui-list-radius"></span>`--cui-list-radius` | `length` | Item surface radius. | `0.65rem` |
| <span id="list-css-clist-css-variables-cui-list-foreground"></span>`--cui-list-foreground` | `color` | Primary foreground. | `CanvasText` |
| <span id="list-css-clist-css-variables-cui-list-muted"></span>`--cui-list-muted` | `color` | Description foreground. | `Nested-scheme muted foreground.` |
| <span id="list-css-clist-css-variables-cui-list-background"></span>`--cui-list-background` | `color` | Root background. | `transparent` |
| <span id="list-css-clist-css-variables-cui-list-hover-background"></span>`--cui-list-hover-background` | `color` | Interactive hover and surface variant background. | `Nested-scheme quiet surface.` |
| <span id="list-css-clist-css-variables-cui-list-current-background"></span>`--cui-list-current-background` | `color` | Current-link background. | `Nested-scheme blue surface.` |
| <span id="list-css-clist-css-variables-cui-list-divider-color"></span>`--cui-list-divider-color` | `color` | Divider color. | `Nested-scheme border color.` |
| <span id="list-css-clist-css-variables-cui-list-marker-color"></span>`--cui-list-marker-color` | `color` | Marker color. | `currentColor` |
| <span id="list-css-clist-css-variables-cui-list-focus-ring"></span>`--cui-list-focus-ring` | `color` | Interactive focus outline. | `Highlight` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CList attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="list-attribute-clist-attributes-data-marker"></span>`data-marker` | List root | `"none" | "disc" | "decimal"` | Marker contract. |
| <span id="list-attribute-clist-attributes-data-density"></span>`data-density` | List root | `"comfortable" | "compact"` | Spacing density. |
| <span id="list-attribute-clist-attributes-data-variant"></span>`data-variant` | List root | `"plain" | "surface"` | Surface treatment. |
| <span id="list-attribute-clist-attributes-data-divided"></span>`data-divided` | List root | `present-or-absent` | Present when direct Items have dividers. |

</div>

#### CListItem attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="list-attribute-clist-item-attributes-data-current"></span>`data-current` | li | `present-or-absent` | Present for the current link. |
| <span id="list-attribute-clist-item-attributes-data-disabled"></span>`data-disabled` | li | `present-or-absent` | Present when a link becomes static or an action Button is natively disabled. |
| <span id="list-attribute-clist-item-attributes-data-interactive"></span>`data-interactive` | li | `present-or-absent` | Present when the surface is an enabled link or Button. |
| <span id="list-attribute-clist-item-attributes-aria-current"></span>`aria-current` | Current link | `"page"` | Exposes current navigation location. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CList selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="list-selector-clist-selectors-data-citry-ui-part-list"></span>`[data-citry-ui-part="list"]` | ul or ol root | Stable list and attrs destination. |

</div>

#### CListItem selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="list-selector-clist-item-selectors-data-citry-ui-part-list-item"></span>`[data-citry-ui-part="list-item"]` | li | Stable Item and attrs destination. |
| <span id="list-selector-clist-item-selectors-data-citry-ui-part-surface"></span>`[data-citry-ui-part="surface"]` | div, a, or button | Stable content/action surface and surface_attrs destination. |
| <span id="list-selector-clist-item-selectors-data-citry-ui-part-start"></span>`[data-citry-ui-part="start"]` | Leading wrapper | Leading media surface. |
| <span id="list-selector-clist-item-selectors-data-citry-ui-part-body"></span>`[data-citry-ui-part="body"]` | Primary content wrapper | Primary and description layout surface. |
| <span id="list-selector-clist-item-selectors-data-citry-ui-part-description"></span>`[data-citry-ui-part="description"]` | Supplemental text wrapper | Muted description surface. |
| <span id="list-selector-clist-item-selectors-data-citry-ui-part-end"></span>`[data-citry-ui-part="end"]` | Trailing wrapper | Metadata or secondary action surface. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="list-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="list-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="list-interface-input-type-aliases-list-marker"></span>`CListMarker` | `Literal["none", "disc", "decimal"]` |
| <span id="list-interface-input-type-aliases-list-density"></span>`CListDensity` | `Literal["comfortable", "compact"]` |
| <span id="list-interface-input-type-aliases-list-variant"></span>`CListVariant` | `Literal["plain", "surface"]` |

</div>

<span id="list-interface-clist-default-slot-data"></span>

#### `CListDefaultSlotData`

Empty dataclass: `{}`.

<span id="list-interface-clist-item-default-slot-data"></span>

#### `CListItemDefaultSlotData`

Empty dataclass: `{}`.

<span id="list-interface-clist-item-start-slot-data"></span>

#### `CListItemStartSlotData`

Empty dataclass: `{}`.

<span id="list-interface-clist-item-description-slot-data"></span>

#### `CListItemDescriptionSlotData`

Empty dataclass: `{}`.

<span id="list-interface-clist-item-end-slot-data"></span>

#### `CListItemEndSlotData`

Empty dataclass: `{}`.

### Translation keys

-