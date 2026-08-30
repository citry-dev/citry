---
title: Badge
url: https://citry.dev/v/0.4.6/ui-library/components/badge/
description: "Present compact status, category, count, and metadata labels with Citry UI."
---
# Badge

Use `CBadge` for short inline status, category, count, or metadata text. Badge
is a visual label, not a Button, selectable Chip, removable Tag, or live
announcement region.

## Badge at a glance


### Badge at a glance

[Open the rendered preview](/v/0.4.6/ui-library/components/badge/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeAtAGlance(Component):
    template = """
      <section class="badge-glance" aria-labelledby="badge-glance-title">
        <div>
          <p>Mineral archive · specimen 184</p>
          <h2 id="badge-glance-title">Azurite rosette</h2>
        </div>
        <c-CRow>
          <c-CBadge intent="primary">Copper carbonate</c-CBadge>
          <c-CBadge intent="success" variant="outline">Verified</c-CBadge>
          <c-CBadge shape="pill">3 fragments</c-CBadge>
        </c-CRow>
      </section>
    """
    css = """
      :where(.badge-glance) {
        display: flex;
        flex-wrap: wrap;
        align-items: end;
        justify-content: space-between;
        gap: 1rem;
        max-inline-size: 38rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b7c6cf, #526873);
        border-radius: 0.85rem;
        background: light-dark(#f5fbff, #17232a);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.badge-glance h2, .badge-glance p) {
        margin: 0;
      }

      :where(.badge-glance p) {
        color: light-dark(#496471, #a9c5d2);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.badge-glance h2) {
        margin-block-start: 0.25rem;
        font-size: 1.1rem;
      }
    """


preview = BadgeAtAGlance()

preview  # noqa: B018
````


## Compose a Badge

The default slot supplies the visible meaning. It is required.


### Compose short inline labels

[Open the rendered preview](/v/0.4.6/ui-library/components/badge/_previews/basic-badges/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicBadges(Component):
    template = """
      <div class="badge-basic">
        <p>Fluorite <c-CBadge>New</c-CBadge></p>
        <p>Cabinet 7 <c-CBadge shape="pill">24</c-CBadge></p>
        <p>Catalog record <c-CBadge variant="outline">Draft</c-CBadge></p>
      </div>
    """
    css = """
      :where(.badge-basic) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 24rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.badge-basic p) {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin: 0;
        padding-block-end: 0.5rem;
        border-block-end: 1px solid light-dark(#d8d2c6, #4f4a42);
      }
    """


preview = BasicBadges()

preview  # noqa: B018
````



```citry-html
<c-CBadge intent="success">Verified</c-CBadge>
```


Compose the same result in Python:


```python
from citry_ui import CBadge

verified = CBadge(intent="success", slots={"default": "Verified"})
```


## Carry meaning with text

Intent selects a palette. The visible label must still explain the state, so
the result remains understandable without color.


### Compare Badge intents

[Open the rendered preview](/v/0.4.6/ui-library/components/badge/_previews/intents/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeIntents(Component):
    template = """
      <c-CRow class_="badge-intents">
        <c-CBadge intent="neutral">Unsorted</c-CBadge>
        <c-CBadge intent="primary">In study</c-CBadge>
        <c-CBadge intent="success">Verified</c-CBadge>
        <c-CBadge intent="warn">Handle carefully</c-CBadge>
        <c-CBadge intent="danger">Restricted</c-CBadge>
      </c-CRow>
    """
    css = """
      :where(.badge-intents) {
        max-inline-size: 34rem;
        padding: 1rem;
        border-radius: 0.75rem;
        background: light-dark(#f5f1e8, #25221e);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = BadgeIntents()

preview  # noqa: B018
````


## Choose visual emphasis

Use `soft` for quiet metadata, `solid` for stronger emphasis, and `outline`
when the surrounding surface should remain visible.


### Compare Badge variants

[Open the rendered preview](/v/0.4.6/ui-library/components/badge/_previews/variants/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeVariants(Component):
    template = """
      <c-CCol class_="badge-variants" gap="sm">
        <c-CRow><strong>Soft</strong><c-CBadge intent="primary">Lapis</c-CBadge></c-CRow>
        <c-CRow><strong>Solid</strong><c-CBadge intent="primary" variant="solid">Lapis</c-CBadge></c-CRow>
        <c-CRow><strong>Outline</strong><c-CBadge intent="primary" variant="outline">Lapis</c-CBadge></c-CRow>
      </c-CCol>
    """
    css = """
      :where(.badge-variants) {
        max-inline-size: 20rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.badge-variants > [data-citry-ui-part="row"]) {
        justify-content: space-between;
        padding: 0.75rem;
        border: 1px solid light-dark(#d4cabc, #514940);
        border-radius: 0.6rem;
      }
    """


preview = BadgeVariants()

preview  # noqa: B018
````


## Choose size and shape

Sizes change compact type and spacing. Shape changes only the corner radius.


### Compare sizes and shapes

[Open the rendered preview](/v/0.4.6/ui-library/components/badge/_previews/sizes-and-shapes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeSizesAndShapes(Component):
    template = """
      <c-CCol class_="badge-sizes">
        <c-CRow align="baseline">
          <c-CBadge size="sm">Small</c-CBadge>
          <c-CBadge>Medium</c-CBadge>
          <c-CBadge size="lg">Large</c-CBadge>
        </c-CRow>
        <c-CRow>
          <c-CBadge shape="rounded" intent="success">Rounded</c-CBadge>
          <c-CBadge shape="pill" intent="success">Pill</c-CBadge>
        </c-CRow>
      </c-CCol>
    """
    css = """
      :where(.badge-sizes) {
        max-inline-size: 28rem;
        padding: 1rem;
        border: 1px solid light-dark(#cbd5d9, #475a62);
        border-radius: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = BadgeSizesAndShapes()

preview  # noqa: B018
````


## Add registered icons

Use the `start` and `end` slots for short decorative content. Keep the default
label meaningful without the icon.


### Add registered icons

[Open the rendered preview](/v/0.4.6/ui-library/components/badge/_previews/icons/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeIcons(Component):
    template = """
      <c-CRow class_="badge-icons">
        <c-CBadge intent="success">
          <c-fill name="start"><c-CIcon name="check" /></c-fill>
          <c-fill name="default">Verified origin</c-fill>
        </c-CBadge>
        <c-CBadge intent="warn" variant="outline">
          <c-fill name="default">Requires gloves</c-fill>
          <c-fill name="end"><c-CIcon name="triangle-alert" /></c-fill>
        </c-CBadge>
      </c-CRow>
    """
    css = """
      :where(.badge-icons) {
        max-inline-size: 30rem;
        padding: 1rem;
        background: light-dark(#f4f0e7, #29251f);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = BadgeIcons()

preview  # noqa: B018
````


## Give counts context

A lone number is ambiguous. Put counts beside understandable owner text and
include the count's meaning in the owner accessible name when needed.


### Present counts in context

[Open the rendered preview](/v/0.4.6/ui-library/components/badge/_previews/counts-and-context/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeCountsAndContext(Component):
    template = """
      <nav class="badge-counts" aria-label="Mineral archive queues">
        <a href="#unfiled" aria-label="Unfiled specimens, 12 items">
          <span>Unfiled specimens</span><c-CBadge shape="pill">12</c-CBadge>
        </a>
        <a href="#review" aria-label="Awaiting review, 4 items">
          <span>Awaiting review</span><c-CBadge shape="pill" intent="warn">4</c-CBadge>
        </a>
      </nav>
    """
    css = """
      :where(.badge-counts) {
        display: grid;
        gap: 0.375rem;
        max-inline-size: 22rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.badge-counts a) {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.75rem;
        border-radius: 0.6rem;
        color: CanvasText;
        text-decoration: none;
      }

      :where(.badge-counts a:hover) {
        background: light-dark(#ece6da, #322d27);
      }
    """


preview = BadgeCountsAndContext()

preview  # noqa: B018
````


Badge does not cap large values or hide zero. Format the slot content in your
application so display and accessible context stay under one policy.

## Position a Badge around an owner

Badge owns no positioning or overlap. Use ordinary CSS when a count belongs at
the corner of a Button, Avatar, or other item.


### Position a Badge with consumer CSS

[Open the rendered preview](/v/0.4.6/ui-library/components/badge/_previews/positioning/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgePositioning(Component):
    template = """
      <div class="badge-positioning">
        <c-CButton c-attrs="{'aria-label': 'Field notes, 7 unread'}">
          Field notes
          <c-CBadge intent="danger" shape="pill">7</c-CBadge>
        </c-CButton>
      </div>
    """
    css = """
      :where(.badge-positioning) {
        min-block-size: 7rem;
        padding: 1.5rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.badge-positioning [data-citry-ui-part="button"]) {
        position: relative;
      }

      :where(.badge-positioning [data-citry-ui-part="badge"]) {
        position: absolute;
        inset-block-start: 0;
        inset-inline-end: 0;
        translate: 45% -45%;
      }
    """


preview = BadgePositioning()

preview  # noqa: B018
````


## Customize Badge

Override public variables on an ancestor or one Badge. Stable part selectors
support local geometry without relying on private classes.


### Customize Badge with public CSS

[Open the rendered preview](/v/0.4.6/ui-library/components/badge/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeCustomization(Component):
    template = """
      <c-CRow class_="badge-themes">
        <div class="badge-themes__quartz">
          <c-CBadge>Quartz archive</c-CBadge>
        </div>
        <div class="badge-themes__basalt">
          <c-CBadge variant="outline">Basalt archive</c-CBadge>
        </div>
      </c-CRow>
    """
    css = """
      :where(.badge-themes > div) {
        padding: 1.25rem;
        border-radius: 0.75rem;
      }

      :where(.badge-themes__quartz) {
        --cui-badge-background: #f0e7ff;
        --cui-badge-foreground: #4c1d75;
        --cui-badge-radius: 0.2rem;
        background: #faf7ff;
      }

      :where(.badge-themes__basalt) {
        color-scheme: dark;
        --cui-badge-background: #1e2930;
        --cui-badge-foreground: #d7edf2;
        --cui-badge-border-color: #72a8b5;
        --cui-badge-radius: 999px;
        background: #10171b;
      }
    """


preview = BadgeCustomization()

preview  # noqa: B018
````


## Accessibility and behavior

Badge renders a neutral, unfocusable `span` with no JavaScript. Do not place
Buttons, links, inputs, or other controls inside it. Put Badge inside the
interactive owner instead.

Changing Badge text does not create a live announcement. Use a persistent
status or Alert surface when a browser update must be announced.

## API reference

### Inputs

#### CBadge server inputs

Server inputs are passed in a template through `<c-CBadge ... />` or in Python through
`CBadge(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="badge-input-cbadge-server-inputs-variant"></span>`variant` | `"soft" | "solid" | "outline"` ([`CBadgeVariant`](#badge-interface-input-type-aliases-cbadge-variant)) | `"soft"` | Selects quiet fill, strong fill, or outlined emphasis. |
| <span id="badge-input-cbadge-server-inputs-intent"></span>`intent` | `"neutral" | "primary" | "success" | "warn" | "danger"` ([`CBadgeIntent`](#badge-interface-input-type-aliases-cbadge-intent)) | `"neutral"` | Selects a visual palette; authored text must still carry status meaning. |
| <span id="badge-input-cbadge-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CBadgeSize`](#badge-interface-input-type-aliases-cbadge-size)) | `"md"` | Sets compact height, type, padding, icon size, and gap. |
| <span id="badge-input-cbadge-server-inputs-shape"></span>`shape` | `"rounded" | "pill"` ([`CBadgeShape`](#badge-interface-input-type-aliases-cbadge-shape)) | `"rounded"` | Selects compact rounded or fully pill-shaped geometry. |
| <span id="badge-input-cbadge-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#badge-interface-input-type-aliases-class-value)) | `None` | Adds root classes and merges them with `attrs`. |
| <span id="badge-input-cbadge-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#badge-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles and merges them with `attrs`. |
| <span id="badge-input-cbadge-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted native, data, and targeted Alpine root attributes without replacing Badge anatomy, semantics, or Citry runtime fields. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CBadge slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="badge-slot-cbadge-slots-default"></span>`default` | yes | `{}` ([`CBadgeDefaultSlotData`](#badge-interface-cbadge-default-slot-data)) | Missing fill raises before rendering. |
| <span id="badge-slot-cbadge-slots-start"></span>`start` | no | `{}` ([`CBadgeStartSlotData`](#badge-interface-cbadge-start-slot-data)) | Leading wrapper omitted. |
| <span id="badge-slot-cbadge-slots-end"></span>`end` | no | `{}` ([`CBadgeEndSlotData`](#badge-interface-cbadge-end-slot-data)) | Trailing wrapper omitted. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CBadge CSS variables

Apply these variables to `CBadge` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="badge-css-cbadge-css-variables-cui-badge-background"></span>`--cui-badge-background` | `color` | Root fill. | `Variant- and intent-derived color.` |
| <span id="badge-css-cbadge-css-variables-cui-badge-foreground"></span>`--cui-badge-foreground` | `color` | Label and icon foreground. | `Contrast-checked variant and intent color.` |
| <span id="badge-css-cbadge-css-variables-cui-badge-border-color"></span>`--cui-badge-border-color` | `color` | Root border. | `Variant-derived transparent or currentColor.` |
| <span id="badge-css-cbadge-css-variables-cui-badge-radius"></span>`--cui-badge-radius` | `length` | Root corner radius. | `Shape-derived 0.375rem or 999px.` |
| <span id="badge-css-cbadge-css-variables-cui-badge-min-height"></span>`--cui-badge-min-height` | `length` | Compact minimum block size. | `Size-derived length.` |
| <span id="badge-css-cbadge-css-variables-cui-badge-padding-inline"></span>`--cui-badge-padding-inline` | `length` | Root inline padding. | `Size-derived length.` |
| <span id="badge-css-cbadge-css-variables-cui-badge-gap"></span>`--cui-badge-gap` | `length` | Space between supplied slot wrappers. | `Size-derived length.` |
| <span id="badge-css-cbadge-css-variables-cui-badge-font-size"></span>`--cui-badge-font-size` | `length` | Label font size. | `Size-derived length.` |
| <span id="badge-css-cbadge-css-variables-cui-badge-font-weight"></span>`--cui-badge-font-weight` | `font-weight` | Label weight. | `650` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CBadge attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="badge-attribute-cbadge-attributes-data-variant"></span>`data-variant` | Root | `"soft" | "solid" | "outline"` | Reflects the selected emphasis treatment. |
| <span id="badge-attribute-cbadge-attributes-data-intent"></span>`data-intent` | Root | `"neutral" | "primary" | "success" | "warn" | "danger"` | Reflects the selected visual palette. |
| <span id="badge-attribute-cbadge-attributes-data-size"></span>`data-size` | Root | `"sm" | "md" | "lg"` | Reflects compact geometry. |
| <span id="badge-attribute-cbadge-attributes-data-shape"></span>`data-shape` | Root | `"rounded" | "pill"` | Reflects corner geometry. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CBadge selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="badge-selector-cbadge-selectors-data-citry-ui-part-badge"></span>`[data-citry-ui-part="badge"]` | Native span root | Stable Badge root and `attrs` destination. |
| <span id="badge-selector-cbadge-selectors-data-citry-ui-part-start"></span>`[data-citry-ui-part="start"]` | Optional leading wrapper | Leading icon/content layout. |
| <span id="badge-selector-cbadge-selectors-data-citry-ui-part-label"></span>`[data-citry-ui-part="label"]` | Required label wrapper | Visible meaning-bearing content. |
| <span id="badge-selector-cbadge-selectors-data-citry-ui-part-end"></span>`[data-citry-ui-part="end"]` | Optional trailing wrapper | Trailing icon/content layout. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="badge-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="badge-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="badge-interface-input-type-aliases-cbadge-variant"></span>`CBadgeVariant` | `Literal["soft", "solid", "outline"]` |
| <span id="badge-interface-input-type-aliases-cbadge-intent"></span>`CBadgeIntent` | `Literal["neutral", "primary", "success", "warn", "danger"]` |
| <span id="badge-interface-input-type-aliases-cbadge-size"></span>`CBadgeSize` | `Literal["sm", "md", "lg"]` |
| <span id="badge-interface-input-type-aliases-cbadge-shape"></span>`CBadgeShape` | `Literal["rounded", "pill"]` |

</div>

<span id="badge-interface-cbadge-default-slot-data"></span>

#### `CBadgeDefaultSlotData`

Empty dataclass: `{}`.

<span id="badge-interface-cbadge-start-slot-data"></span>

#### `CBadgeStartSlotData`

Empty dataclass: `{}`.

<span id="badge-interface-cbadge-end-slot-data"></span>

#### `CBadgeEndSlotData`

Empty dataclass: `{}`.

### Translation keys

-