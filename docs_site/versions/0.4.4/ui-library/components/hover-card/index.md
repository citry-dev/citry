---
title: HoverCard
url: https://citry.dev/v/0.4.4/ui-library/components/hover-card/
description: "Preview supplementary content behind a link or control."
---
# HoverCard

Use `CHoverCard` to preview supplementary profile, document, or destination
details on hover and keyboard focus. Essential information and actions must
remain available without the preview.

## HoverCard at a glance


### HoverCard at a glance

[Open the rendered preview](/v/0.4.4/ui-library/components/hover-card/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class HoverCardAtAGlance(Component):
    template = """
      <p>Meet
        <c-CHoverCard>
          <c-fill name="activator" data="{ activator_attrs }">
            <a href="#maya" c-bind="activator_attrs">Maya Chen</a>
          </c-fill>
          <c-fill name="default">
            <c-CCol gap="sm">
              <c-CAvatar>MC</c-CAvatar>
              <strong>Maya Chen</strong>
              <span>Field researcher · 18 shared observations</span>
            </c-CCol>
          </c-fill>
        </c-CHoverCard>
      </p>
    """


preview = HoverCardAtAGlance()
preview  # noqa: B018
````


## Preview a document


### Preview a document

[Open the rendered preview](/v/0.4.4/ui-library/components/hover-card/_previews/document/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DocumentHoverCard(Component):
    template = """
      <c-CHoverCard placement="top-start">
        <c-fill name="activator" data="{ activator_attrs }">
          <a href="#survey" c-bind="activator_attrs">Northern reef survey</a>
        </c-fill>
        <c-fill name="default">
          <c-CCol gap="sm">
            <strong>Northern reef survey</strong>
            <span>Updated today · 42 observations</span>
            <c-CProgress c-value="68" label="Review progress" />
          </c-CCol>
        </c-fill>
      </c-CHoverCard>
    """


preview = DocumentHoverCard()
preview  # noqa: B018
````


## Control visibility


### Control HoverCard

[Open the rendered preview](/v/0.4.4/ui-library/components/hover-card/_previews/controlled/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledHoverCard(Component):
    template = """
      <div x-data>
        <c-CHoverCard $c-props="{open:$store.hoverExample.open,onOpenChange:(next)=>$store.hoverExample.open=next}">
          <c-fill name="activator" data="{ activator_attrs }">
            <a href="#atlas" c-bind="activator_attrs">Atlas workspace</a>
          </c-fill>
          <c-fill name="default"><strong>Atlas</strong><p>12 collaborators · Active now</p></c-fill>
        </c-CHoverCard>
        <c-CButton variant="outline" @click="$store.hoverExample.open=!$store.hoverExample.open">Toggle preview</c-CButton>
      </div>
    """
    js = "Alpine.store('hoverExample',{open:false});"


preview = ControlledHoverCard()
preview  # noqa: B018
````


## Tune delays


### Tune HoverCard delays

[Open the rendered preview](/v/0.4.4/ui-library/components/hover-card/_previews/delays/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class HoverCardDelays(Component):
    template = """
      <c-CRow>
        <c-CHoverCard c-delay="0" c-close_delay="0">
          <c-fill name="activator" data="{ activator_attrs }"><a href="#instant" c-bind="activator_attrs">Instant</a></c-fill>
          <c-fill name="default">No opening or closing delay.</c-fill>
        </c-CHoverCard>
        <c-CHoverCard c-delay="900" c-close_delay="500">
          <c-fill name="activator" data="{ activator_attrs }"><a href="#deliberate" c-bind="activator_attrs">Deliberate</a></c-fill>
          <c-fill name="default">A slower, forgiving preview.</c-fill>
        </c-CHoverCard>
      </c-CRow>
    """


preview = HoverCardDelays()
preview  # noqa: B018
````


## Choose placement


### Place HoverCard

[Open the rendered preview](/v/0.4.4/ui-library/components/hover-card/_previews/placements/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class HoverCardPlacements(Component):
    template = """
      <c-CRow style="padding-block:8rem">
        <c-CHoverCard placement="top-start">
          <c-fill name="activator" data="{ activator_attrs }"><a href="#top" c-bind="activator_attrs">Top start</a></c-fill>
          <c-fill name="default">Collision-aware top preview.</c-fill>
        </c-CHoverCard>
        <c-CHoverCard placement="bottom-end">
          <c-fill name="activator" data="{ activator_attrs }"><a href="#bottom" c-bind="activator_attrs">Bottom end</a></c-fill>
          <c-fill name="default">Collision-aware bottom preview.</c-fill>
        </c-CHoverCard>
      </c-CRow>
    """


preview = HoverCardPlacements()
preview  # noqa: B018
````


## Choose size and arrow


### HoverCard sizes

[Open the rendered preview](/v/0.4.4/ui-library/components/hover-card/_previews/sizes/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class HoverCardSizes(Component):
    template = """
      <c-CRow>
        <c-CHoverCard size="sm">
          <c-fill name="activator" data="{ activator_attrs }"><a href="#small" c-bind="activator_attrs">Small</a></c-fill>
          <c-fill name="default">A compact preview card.</c-fill>
        </c-CHoverCard>
        <c-CHoverCard size="lg" c-arrow="False">
          <c-fill name="activator" data="{ activator_attrs }"><a href="#large" c-bind="activator_attrs">Large without arrow</a></c-fill>
          <c-fill name="default">A generous preview without a pointer arrow.</c-fill>
        </c-CHoverCard>
      </c-CRow>
    """


preview = HoverCardSizes()
preview  # noqa: B018
````


## Nested color schemes


### HoverCard themes

[Open the rendered preview](/v/0.4.4/ui-library/components/hover-card/_previews/themes/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class HoverCardThemes(Component):
    template = """
      <c-CRow>
        <div style="color-scheme:light;background:Canvas;color:CanvasText;padding:2rem">
          <c-CHoverCard>
            <c-fill name="activator" data="{ activator_attrs }"><a href="#day" c-bind="activator_attrs">Day profile</a></c-fill>
            <c-fill name="default"><strong>Light scheme</strong><p>Follows its anchor context.</p></c-fill>
          </c-CHoverCard>
        </div>
        <div style="color-scheme:dark;background:Canvas;color:CanvasText;padding:2rem">
          <c-CHoverCard>
            <c-fill name="activator" data="{ activator_attrs }"><a href="#night" c-bind="activator_attrs">Night profile</a></c-fill>
            <c-fill name="default"><strong>Dark scheme</strong><p>Follows its anchor context.</p></c-fill>
          </c-CHoverCard>
        </div>
      </c-CRow>
    """


preview = HoverCardThemes()
preview  # noqa: B018
````


## Customize HoverCard


### Customize HoverCard

[Open the rendered preview](/v/0.4.4/ui-library/components/hover-card/_previews/customization/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedHoverCard(Component):
    template = """
      <c-CHoverCard
        style="--cui-hover-card-background:#fff8eb;--cui-hover-card-foreground:#7a2e0e;
               --cui-hover-card-border-color:#f79009;--cui-hover-card-radius:1.25rem"
      >
        <c-fill name="activator" data="{ activator_attrs }"><a href="#coral" c-bind="activator_attrs">Coral study</a></c-fill>
        <c-fill name="default"><strong>Coral study</strong><p>Warm brand adaptation.</p></c-fill>
      </c-CHoverCard>
    """


preview = CustomizedHoverCard()
preview  # noqa: B018
````


## Accessibility and interaction

The activator keeps its authored accessible name, navigation, and click
behavior. The preview is `aria-hidden` supplementary content and cannot contain
focusable or interactive descendants. Focus opens it visually; Escape and blur
close it without moving focus. Touch contact does not open it.

Use `CTooltip` for a concise accessible description and `CPopover` when people
must interact with the overlay.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CHoverCard server inputs

Server inputs are passed in a template through `<c-CHoverCard ... />` or in Python through
`CHoverCard(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="hover-card-input-chover-card-server-inputs-id"></span>`id` | `str | None` | generated | Sets private surface identity and exposes it as slot data. |
| <span id="hover-card-input-chover-card-server-inputs-open"></span>`open` | `bool` | `False` | Sets the server-visible initial state and uncontrolled fallback. |
| <span id="hover-card-input-chover-card-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Suppresses visual opening without changing the activator itself. |
| <span id="hover-card-input-chover-card-server-inputs-delay"></span>`delay` | `int` | `600` | Sets the first fine-pointer hover delay in milliseconds from 0 through 60000. Focus remains immediate. |
| <span id="hover-card-input-chover-card-server-inputs-close-delay"></span>`close_delay` | `int` | `300` | Sets the pointer bridge delay in milliseconds from 0 through 60000. |
| <span id="hover-card-input-chover-card-server-inputs-placement"></span>`placement` | `"top-start" | "top" | "top-end" | "bottom-start" | "bottom" | "bottom-end"` ([`CHoverCardPlacement`](#hover-card-interface-input-type-aliases-chover-card-placement)) | `"bottom-start"` | Sets the preferred logical placement. Collision fallback may choose another rendered side. |
| <span id="hover-card-input-chover-card-server-inputs-arrow"></span>`arrow` | `bool` | `True` | Shows the owned decorative pointer arrow. |
| <span id="hover-card-input-chover-card-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CHoverCardSize`](#hover-card-interface-input-type-aliases-chover-card-size)) | `"md"` | Selects preview width padding and text scale. |
| <span id="hover-card-input-chover-card-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#hover-card-interface-input-type-aliases-class-value)) | `None` | Adds surface classes and merges them with `attrs`. |
| <span id="hover-card-input-chover-card-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#hover-card-interface-input-type-aliases-style-value)) | `None` | Adds surface inline styles and merges them with `attrs`; Citry retains anchor ownership. |
| <span id="hover-card-input-chover-card-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native, Alpine, and data attributes to the HoverCard surface. Owned presence, semantics, focus, and relationships are rejected. |

</div>

#### CHoverCard client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CHoverCard />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="hover-card-input-chover-card-client-inputs-open"></span>`open` | `boolean | null` | Releases control and preserves the current committed state. `null` has the same effect. | Controls visual visibility while supplied as a Boolean. Disabled still dominates. |
| <span id="hover-card-input-chover-card-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls HoverCard-local availability. |
| <span id="hover-card-input-chover-card-client-inputs-delay"></span>`delay` | `integer` | Uses the server input. | Controls future first-hover delay from 0 through 60000 milliseconds. |
| <span id="hover-card-input-chover-card-client-inputs-close-delay"></span>`closeDelay` | `integer` | Uses the server input. | Controls the pointer bridge from 0 through 60000 milliseconds. |
| <span id="hover-card-input-chover-card-client-inputs-placement"></span>`placement` | `"top-start" | "top" | "top-end" | "bottom-start" | "bottom" | "bottom-end"` ([`CHoverCardPlacement`](#hover-card-interface-input-type-aliases-chover-card-placement)) | Uses the server input. | Controls requested placement and `data-placement`. |
| <span id="hover-card-input-chover-card-client-inputs-arrow"></span>`arrow` | `boolean` | Uses the server input. | Reactively shows or hides the decorative arrow. |
| <span id="hover-card-input-chover-card-client-inputs-size"></span>`size` | `CHoverCardSize` | Uses the server input. | Reactively changes card geometry. |
| <span id="hover-card-input-chover-card-client-inputs-on-open-change"></span>`onOpenChange` | `function` | Does not notify a component callback. | Receives hover, focus, dismissal, peer, press, and external-native visibility requests. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CHoverCard slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="hover-card-slot-chover-card-slots-activator"></span>`activator` | yes | `{activator_attrs: dict[str, object], hover_card_id: str}` ([`CHoverCardActivatorSlotData`](#hover-card-interface-chover-card-activator-slot-data)) | none |
| <span id="hover-card-slot-chover-card-slots-default"></span>`default` | yes | `{}` ([`CHoverCardDefaultSlotData`](#hover-card-interface-chover-card-default-slot-data)) | none |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CHoverCard events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="hover-card-event-chover-card-events-on-open-change"></span>`onOpenChange` | `(requestedOpen: boolean, detail: CHoverCardOpenChangeDetail) => void` ([`CHoverCardOpenChangeDetail`](#hover-card-interface-chover-card-open-change-detail)) | Hover, focus, pointer departure, blur, Escape, trigger press, a peer HoverCard, or external native visibility requests another state. | `{reason: "hover" | "focus" | "pointer-leave" | "blur" | "escape" | "press" | "peer" | "native" | "ancestor" | "modal", controlled: boolean, forced: boolean, source: EventTarget | null}` ([`CHoverCardOpenChangeDetail`](#hover-card-interface-chover-card-open-change-detail)) | Uncontrolled requests commit before notification. Controlled requests wait for the owner. Owner commits do not notify. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CHoverCard CSS variables

Apply these variables to `CHoverCard` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="hover-card-css-chover-card-css-variables-cui-hover-card-background"></span>`--cui-hover-card-background` | `color` | Surface background. | `Canvas` |
| <span id="hover-card-css-chover-card-css-variables-cui-hover-card-foreground"></span>`--cui-hover-card-foreground` | `color` | Surface text. | `CanvasText` |
| <span id="hover-card-css-chover-card-css-variables-cui-hover-card-border-color"></span>`--cui-hover-card-border-color` | `color` | Surface boundary. | `Subtle currentColor mix.` |
| <span id="hover-card-css-chover-card-css-variables-cui-hover-card-radius"></span>`--cui-hover-card-radius` | `length` | Surface corner radius. | `0.75rem` |
| <span id="hover-card-css-chover-card-css-variables-cui-hover-card-shadow"></span>`--cui-hover-card-shadow` | `shadow` | Top-layer elevation. | `Scheme-aware layered shadow.` |
| <span id="hover-card-css-chover-card-css-variables-cui-hover-card-inline-size"></span>`--cui-hover-card-inline-size` | `length` | Preferred preview width. | `Size-derived.` |
| <span id="hover-card-css-chover-card-css-variables-cui-hover-card-max-inline-size"></span>`--cui-hover-card-max-inline-size` | `length` | Maximum preview width. | `22rem` |
| <span id="hover-card-css-chover-card-css-variables-cui-hover-card-padding"></span>`--cui-hover-card-padding` | `length` | Content padding. | `Size-derived.` |
| <span id="hover-card-css-chover-card-css-variables-cui-hover-card-offset"></span>`--cui-hover-card-offset` | `length` | Gap between activator and surface. | `0.375rem` |
| <span id="hover-card-css-chover-card-css-variables-cui-hover-card-duration"></span>`--cui-hover-card-duration` | `time` | Entry and exit duration; reduced motion resolves to zero. | `100ms` |
| <span id="hover-card-css-chover-card-css-variables-cui-hover-card-easing"></span>`--cui-hover-card-easing` | `easing` | Entry and exit easing. | `cubic-bezier(0.2, 0.8, 0.2, 1)` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CHoverCard attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="hover-card-attribute-chover-card-attributes-popover"></span>`popover` | Surface | `"manual"` | Uses native top-layer presence while Citry owns timing and dismissal. |
| <span id="hover-card-attribute-chover-card-attributes-aria-hidden"></span>`aria-hidden` | Surface | `"true"` | Keeps supplementary visual content outside the accessibility tree. |
| <span id="hover-card-attribute-chover-card-attributes-data-open"></span>`data-open` | Surface | `present | absent` | Mirrors logical visual visibility; absent during exit. |
| <span id="hover-card-attribute-chover-card-attributes-data-placement"></span>`data-placement` | Surface | `six placement strings` ([`CHoverCardPlacement`](#hover-card-interface-input-type-aliases-chover-card-placement)) | Mirrors requested placement, not the collision fallback result. |
| <span id="hover-card-attribute-chover-card-attributes-data-side"></span>`data-side` | Surface | `"top" | "bottom"` | Mirrors the collision-settled physical block side. |
| <span id="hover-card-attribute-chover-card-attributes-data-size"></span>`data-size` | Surface | `CHoverCardSize` | Reflects preview geometry. |
| <span id="hover-card-attribute-chover-card-attributes-data-arrow"></span>`data-arrow` | Surface | `present | absent` | Reflects decorative arrow visibility. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CHoverCard selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="hover-card-selector-chover-card-selectors-host"></span>`[data-citry-ui-part="host"]` | Host div | Activator and surface ownership boundary. |
| <span id="hover-card-selector-chover-card-selectors-hover-card"></span>`[data-citry-ui-part="hover-card"]` | Surface | Visual surface and attrs destination. |
| <span id="hover-card-selector-chover-card-selectors-content"></span>`[data-citry-ui-part="content"]` | Content div | Supplementary flow content wrapper. |
| <span id="hover-card-selector-chover-card-selectors-arrow"></span>`[data-citry-ui-part="arrow"]` | Decorative span | Collision-side pointer mark. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="hover-card-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="hover-card-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="hover-card-interface-input-type-aliases-chover-card-placement"></span>`CHoverCardPlacement` | `Literal["top-start", "top", "top-end", "bottom-start", "bottom", "bottom-end"]` |
| <span id="hover-card-interface-input-type-aliases-chover-card-size"></span>`CHoverCardSize` | `Literal["sm", "md", "lg"]` |

</div>

<span id="hover-card-interface-chover-card-activator-slot-data"></span>

#### `CHoverCardActivatorSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="hover-card-interface-chover-card-activator-slot-data-activator-attrs"></span>`activator_attrs` | `dict[str, object]` | - | Owned trigger marker and CSS anchor style. |
| <span id="hover-card-interface-chover-card-activator-slot-data-hover-card-id"></span>`hover_card_id` | `str` | - | Generated or authored surface identity. |

</div>

<span id="hover-card-interface-chover-card-default-slot-data"></span>

#### `CHoverCardDefaultSlotData`

Empty dataclass: `{}`.

<span id="hover-card-interface-chover-card-open-change-detail"></span>

#### `CHoverCardOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="hover-card-interface-chover-card-open-change-detail-reason"></span>`reason` | `"hover" | "focus" | "pointer-leave" | "blur" | "escape" | "press" | "peer" | "native" | "ancestor" | "modal"` | - | Source of the requested visibility change. |
| <span id="hover-card-interface-chover-card-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether a valid client `open` Boolean currently owns state. |
| <span id="hover-card-interface-chover-card-open-change-detail-forced"></span>`forced` | `boolean` | - | Whether structural or modal safety required the component to close regardless of controlled ownership. |
| <span id="hover-card-interface-chover-card-open-change-detail-source"></span>`source` | `EventTarget | null` | - | Browser source associated with the request. |

</div>

### Translation keys

-