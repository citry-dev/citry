---
title: Avatar
url: https://citry.dev/v/0.4.2/ui-library/components/avatar/
description: "Present image identities with explicit names and reliable fallbacks."
---
# Avatar

Use `CAvatar` for a compact image identity. Supply an explicit accessible name,
then choose an image, authored fallback, or built-in generic silhouette.

## Avatar at a glance


### Avatar at a glance

[Open the rendered preview](/v/0.4.2/ui-library/components/avatar/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AvatarAtAGlance(Component):
    template = """
      <section class="avatar-guide" aria-labelledby="avatar-guide-title">
        <p class="avatar-guide__eyebrow">Moonfen field guide</p>
        <h2 id="avatar-guide-title">Night expedition</h2>
        <div class="avatar-guide__row">
          <div><c-CAvatar alt="Mira Vale">MV</c-CAvatar><span>Mira</span></div>
          <div><c-CAvatar alt="Orrin Moss" variant="solid">OM</c-CAvatar><span>Orrin</span></div>
          <div><c-CAvatar alt="Unknown guide" variant="outline" /><span>Guide</span></div>
        </div>
      </section>
    """
    css = """
      :where(.avatar-guide) {
        max-inline-size: 28rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#a8c7b5, #426151);
        border-radius: 0.9rem;
        background: light-dark(#f4fbf6, #15241c);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.avatar-guide h2, .avatar-guide p) {
        margin: 0;
      }

      :where(.avatar-guide h2) {
        margin-block: 0.2rem 1rem;
        font-size: 1.1rem;
      }

      :where(.avatar-guide__eyebrow) {
        color: light-dark(#35624b, #a9d7bc);
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.avatar-guide__row) {
        display: flex;
        gap: 1rem;
      }

      :where(.avatar-guide__row > div) {
        display: grid;
        justify-items: center;
        gap: 0.35rem;
        font-size: 0.8rem;
      }
    """


preview = AvatarAtAGlance()

preview  # noqa: B018
````


## Choose images and fallbacks

`src` shows one image. The default slot remains behind it and appears when the
source is absent or fails. Without a slot, Avatar uses a generic silhouette.


### Compare image and fallback paths

[Open the rendered preview](/v/0.4.2/ui-library/components/avatar/_previews/images-and-fallbacks/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)

PORTRAIT = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 80'%3E"
    "%3Crect width='80' height='80' fill='%23365f50'/%3E"
    "%3Ccircle cx='40' cy='31' r='14' fill='%23f4d6b0'/%3E"
    "%3Cpath d='M13 80c4-22 15-32 27-32s23 10 27 32' fill='%238fc5a8'/%3E%3C/svg%3E"
)


class AvatarImages(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <div class="avatar-image-grid">
        <div><c-CAvatar c-src="portrait" alt="Fen cartographer">FC</c-CAvatar><span>Loaded</span></div>
        <div>
          <c-CAvatar src="/missing-moonfen-portrait.png" alt="Marsh scout">MS</c-CAvatar>
          <span>Error fallback</span>
        </div>
        <div><c-CAvatar alt="Unassigned explorer" /><span>Generic fallback</span></div>
      </div>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"portrait": PORTRAIT}

    css = """
      :where(.avatar-image-grid) {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.avatar-image-grid > div) {
        display: grid;
        justify-items: center;
        gap: 0.35rem;
        color: light-dark(#315546, #b7ddc8);
        font-size: 0.75rem;
      }
    """


preview = AvatarImages()

preview  # noqa: B018
````



```citry-html
<c-CAvatar src="/portraits/mira.jpg" alt="Mira Vale">MV</c-CAvatar>
```


Python composition uses the same surface:


```python
from citry_ui import CAvatar

avatar = CAvatar(src="/portraits/mira.jpg", alt="Mira Vale")
```


## Provide an accessible name

Use `alt` for the identity conveyed by Avatar. An empty value is deliberately
decorative. The internal image never duplicates the root name.


### Compare named and decorative Avatars

[Open the rendered preview](/v/0.4.2/ui-library/components/avatar/_previews/accessible-names/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AvatarNames(Component):
    template = """
      <div class="avatar-name-list">
        <div><c-CAvatar alt="Mira Vale">MV</c-CAvatar><span>Named identity</span></div>
        <div><c-CAvatar><span aria-hidden="true">MF</span></c-CAvatar><span>Decorative companion</span></div>
      </div>
    """
    css = """
      :where(.avatar-name-list) {
        display: grid;
        gap: 0.75rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.avatar-name-list > div) {
        display: flex;
        align-items: center;
        gap: 0.75rem;
      }
    """


preview = AvatarNames()

preview  # noqa: B018
````


## Choose appearance

Variants style the fallback. Sizes and shapes control the fixed visual frame.


### Compare Avatar variants and sizes

[Open the rendered preview](/v/0.4.2/ui-library/components/avatar/_previews/variants-and-sizes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AvatarVariants(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <div class="avatar-variants">
        <c-for each="variant in variants">
          <div>
            <strong>{{ variant }}</strong>
            <c-for each="size in sizes">
              <c-CAvatar c-variant="variant" c-size="size" c-alt="f'{variant} {size} guide'">MF</c-CAvatar>
            </c-for>
          </div>
        </c-for>
      </div>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"variants": ("soft", "solid", "outline"), "sizes": ("sm", "md", "lg")}

    css = """
      :where(.avatar-variants) {
        display: grid;
        gap: 0.8rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.avatar-variants > div) {
        display: flex;
        align-items: center;
        gap: 0.65rem;
      }

      :where(.avatar-variants strong) {
        inline-size: 4.5rem;
        color: light-dark(#315546, #b7ddc8);
        font-size: 0.75rem;
        text-transform: capitalize;
      }
    """


preview = AvatarVariants()

preview  # noqa: B018
````



### Compare Avatar shapes

[Open the rendered preview](/v/0.4.2/ui-library/components/avatar/_previews/shapes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AvatarShapes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <div class="avatar-shapes">
        <c-for each="shape in shapes">
          <div>
            <c-CAvatar c-shape="shape" c-alt="f'{shape} spirit guide'" variant="soft">SG</c-CAvatar>
            <span>{{ shape }}</span>
          </div>
        </c-for>
      </div>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"shapes": ("circle", "rounded", "square")}

    css = """
      :where(.avatar-shapes) {
        display: flex;
        gap: 1rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.avatar-shapes > div) {
        display: grid;
        justify-items: center;
        gap: 0.35rem;
        font-size: 0.75rem;
        text-transform: capitalize;
      }
    """


preview = AvatarShapes()

preview  # noqa: B018
````


## Update the image in the browser

Client inputs are passed through `$c-props="{...}"`. `src` accepts a URL or
`null`; `onStatusChange` reports fallback, loading, loaded, and error states.


### Change an Avatar source

[Open the rendered preview](/v/0.4.2/ui-library/components/avatar/_previews/reactive-sources/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AvatarReactive(Component):
    template = """
      <div
        class="avatar-reactive"
        x-data="{source: null, status: 'fallback'}"
      >
        <c-CAvatar
          alt="Moonfen lookout"
          $c-props="{src: source, onStatusChange: detail => status = detail.status}"
        >ML</c-CAvatar>
        <p>Status: <strong x-text="status">fallback</strong></p>
        <div class="avatar-reactive__actions">
          <c-CButton size="sm" @click="source = '/missing-lookout-a.png'">Try missing image</c-CButton>
          <c-CButton size="sm" variant="outline" @click="source = null">Use fallback</c-CButton>
        </div>
      </div>
    """
    css = """
      :where(.avatar-reactive) {
        display: grid;
        justify-items: start;
        gap: 0.75rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.avatar-reactive p) {
        margin: 0;
        font-size: 0.8rem;
      }

      :where(.avatar-reactive__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }
    """


preview = AvatarReactive()

preview  # noqa: B018
````


## Compose adjacent UI

Avatar does not own presence, badges, or overlapping groups. Compose those jobs
with `CBadge`, `CGroup`, and application layout.


### Compose Avatar with badges and groups

[Open the rendered preview](/v/0.4.2/ui-library/components/avatar/_previews/composition/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AvatarComposition(Component):
    template = """
      <div class="avatar-party">
        <div class="avatar-party__member">
          <c-CAvatar alt="Mira Vale">MV</c-CAvatar>
          <c-CBadge intent="success" shape="pill">Ready</c-CBadge>
        </div>
        <div class="avatar-party__group" aria-label="Moonfen expedition party">
          <c-CAvatar alt="Orrin Moss">OM</c-CAvatar>
          <c-CAvatar alt="Sable Reed" variant="solid">SR</c-CAvatar>
          <c-CAvatar alt="Tarin Wisp" variant="outline">TW</c-CAvatar>
        </div>
      </div>
    """
    css = """
      :where(.avatar-party) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1.5rem;
      }

      :where(.avatar-party__member) {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      :where(.avatar-party__group) {
        display: flex;
        padding-inline-start: 0.5rem;
      }

      :where(.avatar-party__group [data-citry-ui-part="avatar"]) {
        margin-inline-start: -0.5rem;
        border-color: Canvas;
        border-width: 2px;
      }
    """


preview = AvatarComposition()

preview  # noqa: B018
````


## Customize Avatar

Override public variables on a scope or instance. Stable selectors target the
root, fallback, and image without relying on private classes.


### Customize Avatar with public CSS

[Open the rendered preview](/v/0.4.2/ui-library/components/avatar/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AvatarCustomization(Component):
    template = """
      <div class="avatar-moonlit">
        <c-CAvatar alt="Moonlit ranger" size="lg">MR</c-CAvatar>
        <c-CAvatar alt="Reed oracle" size="lg" variant="outline">RO</c-CAvatar>
      </div>
    """
    css = """
      :where(.avatar-moonlit) {
        --cui-avatar-background: light-dark(#d9f1e4, #234738);
        --cui-avatar-foreground: light-dark(#174b35, #c9f4dd);
        --cui-avatar-border-color: light-dark(#4b8a69, #83c9a3);
        --cui-avatar-radius: 35% 65% 58% 42%;
        display: flex;
        gap: 0.75rem;
      }

      :where(.avatar-moonlit [data-citry-ui-part="fallback"]) {
        letter-spacing: 0.06em;
      }
    """


preview = AvatarCustomization()

preview  # noqa: B018
````


## Accessibility and loading behavior

A nonempty `alt` makes the root one named image semantic. The internal HTML
image and fallback are decorative, avoiding duplicate announcements. Empty
`alt` makes the entire Avatar decorative.

Avatar owns no focus or keyboard behavior. Failed images are hidden after
client activation; the fallback remains mounted throughout loading.

## API reference

### Inputs

#### CAvatar server inputs

Server inputs are passed in a template through `<c-CAvatar ... />` or in Python through
`CAvatar(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 8rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="avatar-input-cavatar-server-inputs-src"></span>`src` | `str | None` | `None` | Sets one escaped image URL. `None` shows the fallback only. |
| <span id="avatar-input-cavatar-server-inputs-alt"></span>`alt` | `str` | `""` | Names the Avatar as one image semantic. Empty text makes the Avatar decorative. |
| <span id="avatar-input-cavatar-server-inputs-variant"></span>`variant` | `"soft" | "solid" | "outline"` ([`CAvatarVariant`](#avatar-interface-variant)) | `"soft"` | Selects fallback visual emphasis. |
| <span id="avatar-input-cavatar-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CAvatarSize`](#avatar-interface-size)) | `"md"` | Selects the size preset. |
| <span id="avatar-input-cavatar-server-inputs-shape"></span>`shape` | `"circle" | "rounded" | "square"` ([`CAvatarShape`](#avatar-interface-shape)) | `"circle"` | Selects clipping geometry. |
| <span id="avatar-input-cavatar-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#avatar-interface-class-value)) | `None` | Adds root classes and merges them with `attrs`. |
| <span id="avatar-input-cavatar-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#avatar-interface-style-value)) | `None` | Adds root inline styles and merges them with `attrs`. |
| <span id="avatar-input-cavatar-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted root attributes without replacing Avatar semantics, focus, children, reflections, or Citry runtime fields. |
| <span id="avatar-input-cavatar-server-inputs-img-attrs"></span>`img_attrs` | `Mapping[str, object] | None` | `None` | Adds copied inert image attributes such as `loading`, `decoding`, and `referrerpolicy` without replacing source, alternative text, events, or ownership. |

</div>

#### CAvatar client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CAvatar />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 15rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="avatar-input-cavatar-client-inputs-src"></span>`src` | `string | null` | Uses the server input. | Replaces the current image URL or switches to fallback-only output. |
| <span id="avatar-input-cavatar-client-inputs-alt"></span>`alt` | `string` | Uses the server input. | Updates the root accessible name; empty text makes it decorative. |
| <span id="avatar-input-cavatar-client-inputs-variant"></span>`variant` | `"soft" | "solid" | "outline"` ([`CAvatarVariant`](#avatar-interface-variant)) | Uses the server input. | Controls fallback visual emphasis. |
| <span id="avatar-input-cavatar-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CAvatarSize`](#avatar-interface-size)) | Uses the server input. | Controls size. |
| <span id="avatar-input-cavatar-client-inputs-shape"></span>`shape` | `"circle" | "rounded" | "square"` ([`CAvatarShape`](#avatar-interface-shape)) | Uses the server input. | Controls clipping geometry. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CAvatar slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="avatar-slot-cavatar-slots-default"></span>`default` | no | `{}` ([`CAvatarDefaultSlotData`](#avatar-interface-default-slot-data)) | Generic decorative person silhouette. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CAvatar events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="avatar-event-cavatar-events-on-status-change"></span>`onStatusChange` | `(detail: {status: CAvatarStatus, src: string | null}) => void` | The committed image status changes. | `{status: "fallback" | "loading" | "loaded" | "error", src: string | null}` | Runs after the image visibility and root status reflection synchronize; return values do not cancel the transition. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CAvatar CSS variables

Apply these variables to `CAvatar` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="avatar-css-cavatar-css-variables-size"></span>`--cui-avatar-size` | `length` | Root inline and block size. | `Size-derived 2rem, 2.5rem, or 3rem.` |
| <span id="avatar-css-cavatar-css-variables-background"></span>`--cui-avatar-background` | `color` | Fallback surface. | `Variant- and scheme-derived color.` |
| <span id="avatar-css-cavatar-css-variables-foreground"></span>`--cui-avatar-foreground` | `color` | Fallback text and icon foreground. | `Variant- and scheme-derived color.` |
| <span id="avatar-css-cavatar-css-variables-border-color"></span>`--cui-avatar-border-color` | `color` | Root boundary color. | `Transparent except outline.` |
| <span id="avatar-css-cavatar-css-variables-border-width"></span>`--cui-avatar-border-width` | `length` | Root boundary width. | `1px` |
| <span id="avatar-css-cavatar-css-variables-radius"></span>`--cui-avatar-radius` | `length` | Root clipping radius. | `Shape-derived.` |
| <span id="avatar-css-cavatar-css-variables-font-size"></span>`--cui-avatar-font-size` | `length` | Authored fallback text size. | `Size-derived.` |
| <span id="avatar-css-cavatar-css-variables-font-weight"></span>`--cui-avatar-font-weight` | `font-weight` | Authored fallback text emphasis. | `700` |
| <span id="avatar-css-cavatar-css-variables-image-fit"></span>`--cui-avatar-image-fit` | `keyword` | Internal image object fit. | `cover` |
| <span id="avatar-css-cavatar-css-variables-image-position"></span>`--cui-avatar-image-position` | `position` | Internal image object position. | `center` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CAvatar attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="avatar-attribute-cavatar-attributes-data-variant"></span>`data-variant` | Root | `"soft" | "solid" | "outline"` | Mirrors effective fallback emphasis. |
| <span id="avatar-attribute-cavatar-attributes-data-size"></span>`data-size` | Root | `"sm" | "md" | "lg"` | Mirrors effective size. |
| <span id="avatar-attribute-cavatar-attributes-data-shape"></span>`data-shape` | Root | `"circle" | "rounded" | "square"` | Mirrors effective clipping geometry. |
| <span id="avatar-attribute-cavatar-attributes-data-status"></span>`data-status` | Root | `"fallback" | "loading" | "loaded" | "error"` ([`CAvatarStatus`](#avatar-interface-status)) | Mirrors the current image lifecycle state. |
| <span id="avatar-attribute-cavatar-attributes-role"></span>`role` | Named root | `"img"` | Exposes the Avatar as one image semantic when `alt` is nonempty. |
| <span id="avatar-attribute-cavatar-attributes-aria-label"></span>`aria-label` | Named root | `string` | Uses the exact nonempty `alt` input as the Avatar name. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CAvatar selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="avatar-selector-cavatar-selectors-avatar"></span>`[data-citry-ui-part="avatar"]` | Root span | Stable Avatar surface and `attrs` destination. |
| <span id="avatar-selector-cavatar-selectors-fallback"></span>`[data-citry-ui-part="fallback"]` | Decorative fallback wrapper | Authored or generic fallback styling. |
| <span id="avatar-selector-cavatar-selectors-image"></span>`[data-citry-ui-part="image"]` | Decorative image | Image presentation and `img_attrs` destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="avatar-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="avatar-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="avatar-interface-variant"></span>`CAvatarVariant` | `Literal["soft", "solid", "outline"]` |
| <span id="avatar-interface-size"></span>`CAvatarSize` | `Literal["sm", "md", "lg"]` |
| <span id="avatar-interface-shape"></span>`CAvatarShape` | `Literal["circle", "rounded", "square"]` |
| <span id="avatar-interface-status"></span>`CAvatarStatus` | `Literal["fallback", "loading", "loaded", "error"]` |

</div>

<span id="avatar-interface-default-slot-data"></span>

#### `CAvatarDefaultSlotData`

Empty dataclass: `{}`.

### Translation keys

-