---
title: Carousel
url: https://citry.dev/v/0.4.4/ui-library/components/carousel/
description: "Browse composed content with native Scroll Snap and explicit controls."
---
# Carousel

Use `CCarousel` and `CCarouselSlide` for a named sequence of content cards,
stories, or media. It uses native scrolling and Scroll Snap, so touch and
trackpad navigation work without an application-widget keyboard model.

## Carousel at a glance


### Carousel at a glance

[Open the rendered preview](/v/0.4.4/ui-library/components/carousel/_previews/at-a-glance/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CarouselAtAGlance(Component):
    template = """
      <c-CCarousel label="Featured observations" variant="surface"><c-CCarouselSlide value="aurora" label="Aurora observation"><c-CCard variant="subtle"><c-fill name="header"><strong>Aurora field notes</strong></c-fill><c-fill name="default">A clear night above the northern ridge.</c-fill></c-CCard></c-CCarouselSlide><c-CCarouselSlide value="tide" label="Tide observation"><c-CCard variant="subtle"><c-fill name="header"><strong>Tide field notes</strong></c-fill><c-fill name="default">A spring tide reshaped the eastern inlet.</c-fill></c-CCard></c-CCarouselSlide></c-CCarousel>
    """


preview = CarouselAtAGlance()
preview  # noqa: B018
````


## Compose content cards


### Carousel content cards

[Open the rendered preview](/v/0.4.4/ui-library/components/carousel/_previews/cards/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CarouselCards(Component):
    template = """
      <c-CCarousel label="Research stories"><c-CCarouselSlide value="forest" label="Forest canopy story"><c-CCard variant="elevated"><c-fill name="header"><c-CBadge intent="success">Canopy</c-CBadge><h3>Listening above the forest floor</h3></c-fill><c-fill name="default">Sensors reveal the canopy's changing rhythm.</c-fill></c-CCard></c-CCarouselSlide><c-CCarouselSlide value="coast" label="Coastal story"><c-CCard variant="elevated"><c-fill name="header"><c-CBadge intent="primary">Coast</c-CBadge><h3>Mapping a moving shoreline</h3></c-fill><c-fill name="default">Field teams compare a decade of tidal change.</c-fill></c-CCard></c-CCarouselSlide></c-CCarousel>
    """


preview = CarouselCards()
preview  # noqa: B018
````


## Control the current Slide


### Controlled Carousel

[Open the rendered preview](/v/0.4.4/ui-library/components/carousel/_previews/controlled/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledCarousel(Component):
    template = """
      <section x-data="{index:0}"><p>Slide <strong x-text="index + 1"></strong> of 3</p><c-CCarousel label="Controlled stories" $c-props="{index,onIndexChange:(next)=>index=next}"><c-CCarouselSlide value="one" label="First story"><c-CAlert>First controlled Slide</c-CAlert></c-CCarouselSlide><c-CCarouselSlide value="two" label="Second story"><c-CAlert intent="success">Second controlled Slide</c-CAlert></c-CCarouselSlide><c-CCarouselSlide value="three" label="Third story"><c-CAlert intent="warn">Third controlled Slide</c-CAlert></c-CCarouselSlide></c-CCarousel></section>
    """


preview = ControlledCarousel()
preview  # noqa: B018
````


## Choose orientation


### Carousel orientations

[Open the rendered preview](/v/0.4.4/ui-library/components/carousel/_previews/orientation/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class VerticalCarousel(Component):
    template = """
      <c-CCarousel label="Vertical updates" orientation="vertical" style="--cui-carousel-block-size:12rem"><c-CCarouselSlide value="morning" label="Morning update"><c-CAlert>Morning observations</c-CAlert></c-CCarouselSlide><c-CCarouselSlide value="evening" label="Evening update"><c-CAlert intent="info">Evening observations</c-CAlert></c-CCarouselSlide></c-CCarousel>
    """


preview = VerticalCarousel()
preview  # noqa: B018
````


## Configure controls and indicators


### Carousel controls

[Open the rendered preview](/v/0.4.4/ui-library/components/carousel/_previews/controls/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CarouselControls(Component):
    template = """
      <c-CCol gap="lg"><c-CCarousel label="Buttons only" c-indicators="False"><c-CCarouselSlide value="one" label="First">Previous and next controls only.</c-CCarouselSlide><c-CCarouselSlide value="two" label="Second">Second Slide.</c-CCarouselSlide></c-CCarousel><c-CCarousel label="Pickers only" c-controls="False"><c-CCarouselSlide value="alpha" label="Alpha">Choose with a named picker.</c-CCarouselSlide><c-CCarouselSlide value="beta" label="Beta">Second picker target.</c-CCarouselSlide></c-CCarousel></c-CCol>
    """


preview = CarouselControls()
preview  # noqa: B018
````


## Loop and disable


### Carousel states

[Open the rendered preview](/v/0.4.4/ui-library/components/carousel/_previews/states/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CarouselStates(Component):
    template = """
      <c-CCol gap="lg"><c-CCarousel label="Looping stories" loop><c-CCarouselSlide value="one" label="First loop Slide">Previous wraps to the end.</c-CCarouselSlide><c-CCarouselSlide value="two" label="Second loop Slide">Next wraps to the start.</c-CCarouselSlide></c-CCarousel><c-CCarousel label="Disabled stories" disabled><c-CCarouselSlide value="locked" label="Locked Slide">Owned controls are disabled.</c-CCarouselSlide></c-CCarousel></c-CCol>
    """


preview = CarouselStates()
preview  # noqa: B018
````


## Variants and sizes


### Carousel variants and sizes

[Open the rendered preview](/v/0.4.4/ui-library/components/carousel/_previews/variants/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CarouselVariants(Component):
    template = """
      <c-CCol gap="lg"><c-CCarousel label="Small plain" size="sm"><c-CCarouselSlide value="small" label="Small Slide"><c-CAlert>Compact content</c-CAlert></c-CCarouselSlide></c-CCarousel><c-CCarousel label="Large surface" variant="surface" size="lg"><c-CCarouselSlide value="large" label="Large Slide"><c-CAlert intent="success">Spacious content</c-CAlert></c-CCarouselSlide></c-CCarousel></c-CCol>
    """


preview = CarouselVariants()
preview  # noqa: B018
````


## Put forms in Slides


### Carousel form content

[Open the rendered preview](/v/0.4.4/ui-library/components/carousel/_previews/forms/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CarouselForms(Component):
    template = """
      <form><c-CCarousel label="Profile setup" c-indicators="False"><c-CCarouselSlide value="identity" label="Identity form"><c-CField><c-fill name="label">Project name</c-fill><c-fill name="default"><c-CInput name="project" /></c-fill></c-CField></c-CCarouselSlide><c-CCarouselSlide value="preferences" label="Preferences form"><c-CCheckbox name="updates">Receive updates</c-CCheckbox></c-CCarouselSlide></c-CCarousel><c-CButton type="submit">Save profile</c-CButton></form>
    """


preview = CarouselForms()
preview  # noqa: B018
````


## Customize Carousel


### Customize Carousel

[Open the rendered preview](/v/0.4.4/ui-library/components/carousel/_previews/customization/)

````citry
# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomCarousel(Component):
    template = """
      <c-CCarousel label="Aurora stories" class_="aurora-carousel" variant="surface"><c-CCarouselSlide value="ridge" label="Northern ridge"><c-CAlert intent="info">The northern ridge at blue hour.</c-CAlert></c-CCarouselSlide><c-CCarouselSlide value="lake" label="Glacial lake"><c-CAlert intent="success">Reflections on the glacial lake.</c-CAlert></c-CCarouselSlide></c-CCarousel>
    """
    css = """
      .aurora-carousel { --cui-carousel-radius:1.25rem; --cui-carousel-indicator-active-color:#7c3aed; --cui-carousel-control-background:#ede9fe; }
    """


preview = CustomCarousel()
preview  # noqa: B018
````


## Accessibility and interaction

Give the root a concise `label` and every Slide a content-specific `label`.
Previous/next and picker controls are native Buttons that keep focus in place.
The native scroll viewport is also a Tab stop, so keyboard and Safari users can
focus and scroll it directly without a scripted Arrow-key model.
All Slides remain in the accessibility tree; offscreen content is never
incorrectly presented as hidden. Disable indicators for large collections to
avoid adding too many Tab stops. Autoplay is intentionally not part of v1.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CCarousel server inputs

Server inputs are passed in a template through `<c-CCarousel ... />` or in Python through
`CCarousel(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="carousel-input-carousel-server-inputs-label"></span>`label` | `str` | required | Names the carousel region without repeating the word carousel. |
| <span id="carousel-input-carousel-server-inputs-id"></span>`id` | `str | None` | generated | Sets root identity. |
| <span id="carousel-input-carousel-server-inputs-index"></span>`index` | `int` | `0` | Selects the initial zero-based Slide and uncontrolled fallback. |
| <span id="carousel-input-carousel-server-inputs-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CCarouselOrientation`](#carousel-interface-orientation)) | `"horizontal"` | Sets scroll axis. |
| <span id="carousel-input-carousel-server-inputs-loop"></span>`loop` | `bool` | `False` | Allows previous and next controls to wrap. |
| <span id="carousel-input-carousel-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables owned controls and drag handling. |
| <span id="carousel-input-carousel-server-inputs-controls"></span>`controls` | `bool` | `True` | Shows previous and next Buttons. |
| <span id="carousel-input-carousel-server-inputs-indicators"></span>`indicators` | `bool` | `True` | Shows the grouped picker Buttons. |
| <span id="carousel-input-carousel-server-inputs-draggable"></span>`draggable` | `bool` | `True` | Enables fine-pointer drag; native touch scroll remains available. |
| <span id="carousel-input-carousel-server-inputs-variant"></span>`variant` | `"plain" | "surface"` ([`CCarouselVariant`](#carousel-interface-variant)) | `"plain"` | Selects root treatment. |
| <span id="carousel-input-carousel-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CCarouselSize`](#carousel-interface-size)) | `"md"` | Selects complete-family geometry. |
| <span id="carousel-input-carousel-server-inputs-previous-label"></span>`previous_label` | `str` | `"Previous slide"` | Names the previous Button for the current locale. |
| <span id="carousel-input-carousel-server-inputs-next-label"></span>`next_label` | `str` | `"Next slide"` | Names the next Button for the current locale. |
| <span id="carousel-input-carousel-server-inputs-picker-label"></span>`picker_label` | `str` | `"Choose slide"` | Names the picker Button group for the current locale. |
| <span id="carousel-input-carousel-server-inputs-role-description"></span>`role_description` | `str | None` | `"carousel"` | Sets the localized `aria-roledescription`; None omits it. |
| <span id="carousel-input-carousel-server-inputs-class"></span>`class_` | `CClassValue` ([`CClassValue`](#carousel-interface-class-value)) | `None` | Adds root classes. |
| <span id="carousel-input-carousel-server-inputs-style"></span>`style` | `CStyleValue` ([`CStyleValue`](#carousel-interface-style-value)) | `None` | Adds root inline styles. |
| <span id="carousel-input-carousel-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native and data attributes to the root. |

</div>

#### CCarousel client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CCarousel />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="carousel-input-carousel-client-inputs-index"></span>`index` | `integer` | Releases control and preserves the current committed index. | Controls the active zero-based Slide while supplied. |
| <span id="carousel-input-carousel-client-inputs-orientation"></span>`orientation` | `CCarouselOrientation` | Uses the server input. | Reactively changes scroll axis. |
| <span id="carousel-input-carousel-client-inputs-loop"></span>`loop` | `boolean` | Uses the server input. | Controls boundary wrapping. |
| <span id="carousel-input-carousel-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls owned interaction availability. |
| <span id="carousel-input-carousel-client-inputs-controls"></span>`controls` | `boolean` | Uses the server input. | Shows or hides previous and next controls. |
| <span id="carousel-input-carousel-client-inputs-indicators"></span>`indicators` | `boolean` | Uses the server input. | Shows or hides picker controls. |
| <span id="carousel-input-carousel-client-inputs-draggable"></span>`draggable` | `boolean` | Uses the server input. | Controls fine-pointer dragging. |
| <span id="carousel-input-carousel-client-inputs-variant"></span>`variant` | `CCarouselVariant` | Uses the server input. | Changes root treatment. |
| <span id="carousel-input-carousel-client-inputs-size"></span>`size` | `CCarouselSize` | Uses the server input. | Changes complete-family geometry. |
| <span id="carousel-input-carousel-client-inputs-on-index-change"></span>`onIndexChange` | `function` | Does not notify a component callback. | Receives navigation scroll and structural index requests. |

</div>

#### CCarouselSlide server inputs

Server inputs are passed in a template through `<c-CCarouselSlide ... />` or in Python
through `CCarouselSlide(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="carousel-input-carousel-slide-server-inputs-value"></span>`value` | `str` | required | Sets unique stable Slide identity. |
| <span id="carousel-input-carousel-slide-server-inputs-label"></span>`label` | `str` | required | Names Slide content without repeating the word slide. |
| <span id="carousel-input-carousel-slide-server-inputs-role-description"></span>`role_description` | `str | None` | `"slide"` | Sets the localized `aria-roledescription`; None omits it. |
| <span id="carousel-input-carousel-slide-server-inputs-class"></span>`class_` | `CClassValue` ([`CClassValue`](#carousel-interface-class-value)) | `None` | Adds Slide classes. |
| <span id="carousel-input-carousel-slide-server-inputs-style"></span>`style` | `CStyleValue` ([`CStyleValue`](#carousel-interface-style-value)) | `None` | Adds Slide inline styles. |
| <span id="carousel-input-carousel-slide-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native and data attributes to the Slide. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CCarousel slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="carousel-slot-carousel-slots-default"></span>`default` | yes | `{}` ([`CCarouselDefaultSlotData`](#carousel-interface-carousel-slot)) | none |

</div>

#### CCarouselSlide slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="carousel-slot-carousel-slide-slots-default"></span>`default` | yes | `{}` ([`CCarouselSlideDefaultSlotData`](#carousel-interface-slide-slot)) | none |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CCarousel events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="carousel-event-carousel-events-on-index-change"></span>`onIndexChange` | `(index: integer, detail: CCarouselIndexChangeDetail) => void` ([`CCarouselIndexChangeDetail`](#carousel-interface-index-change-detail)) | Previous next picker native-scroll or structure requests a different index. | `{index, previousIndex, value, reason, controlled, forced, source}` ([`CCarouselIndexChangeDetail`](#carousel-interface-index-change-detail)) | Uncontrolled requests commit before notification; controlled requests wait for acceptance; removal fallback is forced. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CCarousel CSS variables

Apply these variables to `CCarousel` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="carousel-css-carousel-css-variables-background"></span>`--cui-carousel-background` | `color` | Root background. | `transparent` |
| <span id="carousel-css-carousel-css-variables-foreground"></span>`--cui-carousel-foreground` | `color` | Root foreground. | `CanvasText` |
| <span id="carousel-css-carousel-css-variables-border-color"></span>`--cui-carousel-border-color` | `color` | Surface boundaries. | `Scheme-aware neutral.` |
| <span id="carousel-css-carousel-css-variables-radius"></span>`--cui-carousel-radius` | `length` | Root viewport and Slide radius. | `0.9rem` |
| <span id="carousel-css-carousel-css-variables-gap"></span>`--cui-carousel-gap` | `length` | Slide and region gap. | `Size-derived.` |
| <span id="carousel-css-carousel-css-variables-padding"></span>`--cui-carousel-padding` | `length` | Root padding. | `Size-derived.` |
| <span id="carousel-css-carousel-css-variables-block-size"></span>`--cui-carousel-block-size` | `length` | Vertical viewport and Slide block size. | `20rem` |
| <span id="carousel-css-carousel-css-variables-control-background"></span>`--cui-carousel-control-background` | `color` | Previous and next Button background. | `Scheme-aware neutral.` |
| <span id="carousel-css-carousel-css-variables-control-foreground"></span>`--cui-carousel-control-foreground` | `color` | Previous and next Button foreground. | `CanvasText` |
| <span id="carousel-css-carousel-css-variables-control-size"></span>`--cui-carousel-control-size` | `length` | Previous and next Button size. | `Size-derived.` |
| <span id="carousel-css-carousel-css-variables-focus-color"></span>`--cui-carousel-focus-color` | `color` | Focus ring. | `Highlight` |
| <span id="carousel-css-carousel-css-variables-indicator-size"></span>`--cui-carousel-indicator-size` | `length` | Picker dot size. | `0.65rem` |
| <span id="carousel-css-carousel-css-variables-indicator-color"></span>`--cui-carousel-indicator-color` | `color` | Inactive picker color. | `Scheme-aware neutral.` |
| <span id="carousel-css-carousel-css-variables-indicator-active-color"></span>`--cui-carousel-indicator-active-color` | `color` | Current picker color. | `Highlight` |
| <span id="carousel-css-carousel-css-variables-duration"></span>`--cui-carousel-duration` | `time` | Reserved scroll transition duration and reduced-motion input. | `260ms` |
| <span id="carousel-css-carousel-css-variables-easing"></span>`--cui-carousel-easing` | `easing` | Reserved scroll transition easing. | `ease-out` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CCarousel attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="carousel-attribute-carousel-attributes-role"></span>`role` | Root and Slide | `"region" | "group"` | Identifies carousel region and Slide groups. |
| <span id="carousel-attribute-carousel-attributes-aria-label"></span>`aria-label` | Root Slide controls and picker group | `string` | Names each owned semantic surface. |
| <span id="carousel-attribute-carousel-attributes-aria-roledescription"></span>`aria-roledescription` | Root and Slide | `"carousel" | "slide"` | Supplies concise role descriptions. |
| <span id="carousel-attribute-carousel-attributes-data-orientation"></span>`data-orientation` | Root | `CCarouselOrientation` | Reflects scroll axis. |
| <span id="carousel-attribute-carousel-attributes-data-loop"></span>`data-loop` | Root | `present | absent` | Reflects boundary wrapping. |
| <span id="carousel-attribute-carousel-attributes-data-disabled"></span>`data-disabled` | Root | `present | absent` | Reflects owned disabledness. |
| <span id="carousel-attribute-carousel-attributes-data-draggable"></span>`data-draggable` | Root | `present | absent` | Reflects fine-pointer drag availability. |
| <span id="carousel-attribute-carousel-attributes-data-variant"></span>`data-variant` | Root | `CCarouselVariant` | Reflects treatment. |
| <span id="carousel-attribute-carousel-attributes-data-size"></span>`data-size` | Root | `CCarouselSize` | Reflects geometry. |
| <span id="carousel-attribute-carousel-attributes-data-index"></span>`data-index` | Root Slide and picker | `integer string` | Reflects active or collection position according to destination. |
| <span id="carousel-attribute-carousel-attributes-data-value"></span>`data-value` | Slide | `string` | Reflects stable Slide identity. |
| <span id="carousel-attribute-carousel-attributes-data-active"></span>`data-active` | Current Slide | `present | absent` | Reflects the nearest selected snap point. |
| <span id="carousel-attribute-carousel-attributes-disabled"></span>`disabled` | Owned Buttons | `present | absent` | Reflects navigation availability. |
| <span id="carousel-attribute-carousel-attributes-aria-current"></span>`aria-current` | Current picker | `"true"` | Identifies the picker for the active Slide. |
| <span id="carousel-attribute-carousel-attributes-tabindex"></span>`tabindex` | Viewport | `"0"` | Makes the native scroll region keyboard reachable. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CCarousel selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="carousel-selector-carousel-selectors-carousel"></span>`[data-citry-ui-part="carousel"]` | section | Root state and styling boundary. |
| <span id="carousel-selector-carousel-selectors-controls"></span>`[data-citry-ui-part="controls"]` | div | Previous and next control row. |
| <span id="carousel-selector-carousel-selectors-previous"></span>`[data-citry-ui-part="previous"]` | Button | Previous control. |
| <span id="carousel-selector-carousel-selectors-next"></span>`[data-citry-ui-part="next"]` | Button | Next control. |
| <span id="carousel-selector-carousel-selectors-viewport"></span>`[data-citry-ui-part="viewport"]` | div | Native Scroll Snap viewport. |
| <span id="carousel-selector-carousel-selectors-track"></span>`[data-citry-ui-part="track"]` | div | Direct Slide layout track. |
| <span id="carousel-selector-carousel-selectors-slide"></span>`[data-citry-ui-part="slide"]` | div | Named composed Slide. |
| <span id="carousel-selector-carousel-selectors-indicators"></span>`[data-citry-ui-part="indicators"]` | div | Picker Button group. |
| <span id="carousel-selector-carousel-selectors-indicator"></span>`[data-citry-ui-part="indicator"]` | Button | Runtime picker for one Slide. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="carousel-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="carousel-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="carousel-interface-orientation"></span>`CCarouselOrientation` | `Literal["horizontal", "vertical"]` |
| <span id="carousel-interface-variant"></span>`CCarouselVariant` | `Literal["plain", "surface"]` |
| <span id="carousel-interface-size"></span>`CCarouselSize` | `Literal["sm", "md", "lg"]` |

</div>

<span id="carousel-interface-carousel-slot"></span>

#### `CCarouselDefaultSlotData`

Empty dataclass: `{}`.

<span id="carousel-interface-slide-slot"></span>

#### `CCarouselSlideDefaultSlotData`

Empty dataclass: `{}`.

<span id="carousel-interface-index-change-detail"></span>

#### `CCarouselIndexChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="carousel-interface-index-change-detail-index"></span>`index` | `int` | - | Requested active index. |
| <span id="carousel-interface-index-change-detail-previous"></span>`previousIndex` | `int` | - | Previously effective index. |
| <span id="carousel-interface-index-change-detail-value"></span>`value` | `str` | - | Stable requested Slide value. |
| <span id="carousel-interface-index-change-detail-reason"></span>`reason` | `string` | - | Request source. |
| <span id="carousel-interface-index-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client index owns state. |
| <span id="carousel-interface-index-change-detail-forced"></span>`forced` | `boolean` | - | Whether structure forced fallback. |
| <span id="carousel-interface-index-change-detail-source"></span>`source` | `EventTarget | null` | - | Browser source. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CCarousel translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="carousel-translation-ccarousel-translations-previous"></span>`citry-ui-carousel-previous` | Names the previous-slide control. | `None` | `previous_label` input | $c-tr updates `aria-label`. |
| <span id="carousel-translation-ccarousel-translations-next"></span>`citry-ui-carousel-next` | Names the next-slide control. | `None` | `next_label` input | $c-tr updates `aria-label`. |
| <span id="carousel-translation-ccarousel-translations-picker"></span>`citry-ui-carousel-picker` | Names the slide-picker group. | `None` | `picker_label` input | $c-tr updates `aria-label`. |
| <span id="carousel-translation-ccarousel-translations-role"></span>`citry-ui-carousel-role` | Describes the carousel region role. | `None` | `role_description` input | $c-tr updates `aria-roledescription`. |

</div>

#### CCarouselSlide translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="carousel-translation-ccarousel-slide-translations-role"></span>`citry-ui-carousel-slide-role` | Describes each slide group role. | `None` | `role_description` input | $c-tr updates `aria-roledescription`. |

</div>