---
title: Skeleton
url: https://citry.dev/v/0.4.3/ui-library/components/skeleton/
description: "Compose precise loading placeholders from visible primitives."
---
# Skeleton

Use `CSkeleton` to hold a known layout while its data loads. Compose explicit
primitives instead of encoding a page shape in a preset string.

## Skeleton at a glance


### Skeleton at a glance

[Open the rendered preview](/v/0.4.3/ui-library/components/skeleton/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SkeletonGlance(Component):
    template = """
      <section class="skeleton-glance" aria-label="Loading field note" aria-busy="true">
        <c-CSkeleton height="8rem" animation="wave" />
        <c-CRow c-gap="'sm'">
          <c-CSkeleton kind="circle" width="2.75rem" />
          <c-CSkeleton kind="text" c-lines="3" />
        </c-CRow>
      </section>
    """
    css = """
      :where(.skeleton-glance) {
        display: grid;
        max-inline-size: 24rem;
        gap: 1rem;
        padding: 1rem;
        border: 1px solid light-dark(#b8cbb9, #425947);
        border-radius: 0.9rem;
      }
    """


preview = SkeletonGlance()
preview  # noqa: B018
````


## Choose a primitive

Rectangles hold media and panels, circles hold avatars and icons, and text
lines track typography.


### Compare Skeleton primitives

[Open the rendered preview](/v/0.4.3/ui-library/components/skeleton/_previews/primitives/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SkeletonPrimitives(Component):
    template = """
      <div class="skeleton-primitives" aria-label="Loading archive specimens" aria-busy="true">
        <c-CSkeleton width="10rem" height="5rem" />
        <c-CSkeleton kind="circle" width="3rem" />
        <c-CSkeleton kind="text" width="12rem" />
      </div>
    """
    css = """
      :where(.skeleton-primitives) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
      }
    """


preview = SkeletonPrimitives()
preview  # noqa: B018
````


## Shape text

`lines` produces compact paragraph geometry. Set the final line width to make
the placeholder resemble real prose.


### Compose text lines

[Open the rendered preview](/v/0.4.3/ui-library/components/skeleton/_previews/text-lines/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SkeletonText(Component):
    template = """
      <div class="skeleton-text" aria-label="Loading fern description" aria-busy="true">
        <c-CSkeleton kind="text" height="1.15rem" width="55%" />
        <c-CSkeleton kind="text" c-lines="4" last_line_width="38%" />
      </div>
    """
    css = """
      :where(.skeleton-text) {
        display: grid;
        max-inline-size: 30rem;
        gap: 1rem;
      }
    """


preview = SkeletonText()
preview  # noqa: B018
````


## Compose real layouts

Build familiar patterns with `CCol`, `CRow`, and ordinary CSS. The visible
structure stays inspectable and responsive.


### Compose a field-note card

[Open the rendered preview](/v/0.4.3/ui-library/components/skeleton/_previews/field-note-card/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SkeletonCard(Component):
    template = """
      <c-CCard c-attrs="{'aria-label': 'Loading moonfern field note', 'aria-busy': 'true'}">
        <c-fill name="media"><c-CSkeleton height="9rem" /></c-fill>
        <c-fill name="default">
          <c-CCol c-gap="'sm'">
            <c-CSkeleton kind="text" height="1.2rem" width="48%" />
            <c-CSkeleton kind="text" c-lines="3" />
          </c-CCol>
        </c-fill>
      </c-CCard>
    """


preview = SkeletonCard()
preview  # noqa: B018
````



### Compose a specimen list

[Open the rendered preview](/v/0.4.3/ui-library/components/skeleton/_previews/specimen-list/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SkeletonList(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <div class="skeleton-list" aria-label="Loading specimen index" aria-busy="true">
        <c-for each="item in items">
          <c-CRow #c-key="item" c-gap="'sm'" c-align="'center'">
            <c-CSkeleton kind="circle" width="2.5rem" />
            <c-CSkeleton kind="text" c-lines="2" c-last_line_width="f'{45 + item * 8}%'" />
            <c-CSkeleton width="3.5rem" height="1.5rem" />
          </c-CRow>
        </c-for>
      </div>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"items": (0, 1, 2)}

    css = """
      :where(.skeleton-list) {
        display: grid;
        max-inline-size: 30rem;
        gap: 1rem;
      }

      :where(.skeleton-list [data-citry-ui-part="row"] > :nth-child(2)) {
        flex: 1 1 auto;
      }
    """


preview = SkeletonList()
preview  # noqa: B018
````


## Choose motion

Pulse is the default. Wave provides stronger progress motion, while none makes
a static wireframe. Reduced-motion preferences disable both animations.


### Compare motion treatments

[Open the rendered preview](/v/0.4.3/ui-library/components/skeleton/_previews/motion/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SkeletonMotion(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <div class="skeleton-motion" aria-label="Loading archive shelves" aria-busy="true">
        <c-for each="motion in motions">
          <div><span>{{ motion }}</span><c-CSkeleton c-animation="motion" height="2.5rem" /></div>
        </c-for>
      </div>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"motions": ("pulse", "wave", "none")}

    css = """
      :where(.skeleton-motion) {
        display: grid;
        gap: 0.75rem;
      }

      :where(.skeleton-motion > div) {
        display: grid;
        grid-template-columns: 4rem 1fr;
        align-items: center;
        gap: 0.75rem;
        font: 0.75rem ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = SkeletonMotion()
preview  # noqa: B018
````


## Customize Skeleton

Public variables control dimensions, color, radius, spacing, and timing.


### Customize Skeleton with public CSS

[Open the rendered preview](/v/0.4.3/ui-library/components/skeleton/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SkeletonCustomization(Component):
    template = """
      <div class="skeleton-lichen" aria-label="Loading lichen plates" aria-busy="true">
        <c-CSkeleton height="5rem" animation="wave" />
        <c-CSkeleton kind="text" c-lines="3" />
      </div>
    """
    css = """
      :where(.skeleton-lichen) {
        --cui-skeleton-background: light-dark(#c9dfc8, #36513c);
        --cui-skeleton-highlight: light-dark(rgb(255 255 255 / 70%), rgb(190 239 200 / 28%));
        --cui-skeleton-radius: 1rem;
        display: grid;
        max-inline-size: 24rem;
        gap: 1rem;
      }
    """


preview = SkeletonCustomization()
preview  # noqa: B018
````


## Accessibility and loading ownership

Skeletons are decorative and hidden from assistive technology. Put
`aria-busy="true"` and a useful accessible name on the region whose content is
loading. That region, not Skeleton, owns async state and announcements.

## API reference

### Inputs

#### CSkeleton server inputs

Server inputs are passed in a template through `<c-CSkeleton ... />` or in Python through
`CSkeleton(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 8rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="skeleton-input-cskeleton-server-inputs-kind"></span>`kind` | `"rect" | "text" | "circle"` ([`CSkeletonKind`](#skeleton-interface-kind)) | `"rect"` | Selects primitive geometry. |
| <span id="skeleton-input-cskeleton-server-inputs-lines"></span>`lines` | `int (1..100)` | `1` | Renders one or more text lines; values above one require text kind. |
| <span id="skeleton-input-cskeleton-server-inputs-animation"></span>`animation` | `"pulse" | "wave" | "none"` ([`CSkeletonAnimation`](#skeleton-interface-animation)) | `"pulse"` | Selects CSS-only motion. Reduced-motion always disables it. |
| <span id="skeleton-input-cskeleton-server-inputs-width"></span>`width` | `str | None` | `None` | Sets the root width to one CSS length or percentage. |
| <span id="skeleton-input-cskeleton-server-inputs-height"></span>`height` | `str | None` | `None` | Sets the primitive or line height to one CSS length or percentage. |
| <span id="skeleton-input-cskeleton-server-inputs-last-line-width"></span>`last_line_width` | `str` | `"70%"` | Sets the final line width when multiple text lines render. |
| <span id="skeleton-input-cskeleton-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#skeleton-interface-class-value)) | `None` | Adds root classes and merges them with `attrs`. |
| <span id="skeleton-input-cskeleton-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#skeleton-interface-style-value)) | `None` | Adds root inline styles before direct dimension inputs. |
| <span id="skeleton-input-cskeleton-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted root attributes without replacing decorative semantics, children, reflections, focus, or Citry runtime fields. |

</div>

### Slots

-

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CSkeleton CSS variables

Apply these variables to `CSkeleton` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="skeleton-css-cskeleton-css-variables-width"></span>`--cui-skeleton-width` | `length-or-percentage` | Root or line-group width. | `Kind-derived 100% or 3rem.` |
| <span id="skeleton-css-cskeleton-css-variables-height"></span>`--cui-skeleton-height` | `length-or-percentage` | Root or line height. | `Kind-derived 6rem, 0.75em, or 3rem.` |
| <span id="skeleton-css-cskeleton-css-variables-radius"></span>`--cui-skeleton-radius` | `length` | Primitive corners. | `Kind-derived 0.5rem, 999px, or 50%.` |
| <span id="skeleton-css-cskeleton-css-variables-background"></span>`--cui-skeleton-background` | `color` | Resting placeholder surface. | `Scheme-derived neutral.` |
| <span id="skeleton-css-cskeleton-css-variables-highlight"></span>`--cui-skeleton-highlight` | `color` | Wave highlight. | `Translucent white.` |
| <span id="skeleton-css-cskeleton-css-variables-gap"></span>`--cui-skeleton-gap` | `length` | Text line gap. | `0.5em` |
| <span id="skeleton-css-cskeleton-css-variables-duration"></span>`--cui-skeleton-duration` | `time` | Pulse or wave cycle. | `1.5s` |
| <span id="skeleton-css-cskeleton-css-variables-last-line-width"></span>`--cui-skeleton-last-line-width` | `length-or-percentage` | Final text-line width. | `Input-derived 70%.` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CSkeleton attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="skeleton-attribute-cskeleton-attributes-data-kind"></span>`data-kind` | Root | `"rect" | "text" | "circle"` | Reflects primitive geometry. |
| <span id="skeleton-attribute-cskeleton-attributes-data-animation"></span>`data-animation` | Root | `"pulse" | "wave" | "none"` | Reflects requested motion. |
| <span id="skeleton-attribute-cskeleton-attributes-aria-hidden"></span>`aria-hidden` | Root | `"true"` | Keeps decorative placeholder geometry out of the accessibility tree. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CSkeleton selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="skeleton-selector-cskeleton-selectors-skeleton"></span>`[data-citry-ui-part="skeleton"]` | Root span | Stable primitive and attrs destination. |
| <span id="skeleton-selector-cskeleton-selectors-line"></span>`[data-citry-ui-part="line"]` | Text line span | Stable direct child in text mode. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="skeleton-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="skeleton-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="skeleton-interface-kind"></span>`CSkeletonKind` | `Literal["rect", "text", "circle"]` |
| <span id="skeleton-interface-animation"></span>`CSkeletonAnimation` | `Literal["pulse", "wave", "none"]` |

</div>

### Translation keys

-