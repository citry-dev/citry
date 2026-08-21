---
title: Divider
url: https://citry.dev/v/0.4.2/ui-library/components/divider/
description: "Separate sections semantically or visually with Citry UI."
---
# Divider

Use `CDivider` for a thematic break between sections or a decorative line in
dense layouts. It adds no external spacing and no JavaScript.

## Divider at a glance


### Divider at a glance

[Open the rendered preview](/v/0.4.2/ui-library/components/divider/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DividerAtAGlance(Component):
    template = """
      <section class="divider-glance" aria-labelledby="divider-glance-title">
        <p class="divider-glance__eyebrow">Deep-sky field guide</p>
        <h2 id="divider-glance-title">Northern summer</h2>
        <p>Trace bright nebulae before the Milky Way reaches the western horizon.</p>
        <c-CDivider>After midnight</c-CDivider>
        <div class="divider-glance__row">
          <span>Cygnus</span>
          <c-CDivider orientation="vertical" c-decorative="True" />
          <span>Lyra</span>
          <c-CDivider orientation="vertical" c-decorative="True" />
          <span>Aquila</span>
        </div>
      </section>
    """
    css = """
      :where(.divider-glance) {
        max-inline-size: 36rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9c9e8, #41557c);
        border-radius: 0.9rem;
        background: light-dark(#f7f9ff, #141b30);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.divider-glance h2, .divider-glance p) {
        margin: 0;
      }

      :where(.divider-glance h2) {
        margin-block: 0.2rem 0.5rem;
        font-size: 1.15rem;
      }

      :where(.divider-glance__eyebrow) {
        color: light-dark(#3d5c9a, #a9bfe8);
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.divider-glance [data-citry-ui-part="divider"][data-labeled]) {
        margin-block: 1rem;
      }

      :where(.divider-glance__row) {
        display: flex;
        min-block-size: 2.25rem;
        align-items: stretch;
        gap: 0.75rem;
      }
    """


preview = DividerAtAGlance()

preview  # noqa: B018
````


## Compose a Divider

An unlabelled horizontal Divider is a native thematic break.


### Compose semantic Dividers

[Open the rendered preview](/v/0.4.2/ui-library/components/divider/_previews/basic-dividers/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicDividers(Component):
    template = """
      <section class="divider-basic">
        <article>
          <h2>Orion Nebula</h2>
          <p>A luminous stellar nursery around 1,300 light-years away.</p>
        </article>
        <c-CDivider />
        {{ python_divider }}
        <article>
          <h2>Lagoon Nebula</h2>
          <p>Dark dust lanes cross a glowing cloud in Sagittarius.</p>
        </article>
      </section>
    """

    def template_data(
        self,
        kwargs: Any,  # noqa: ARG002
        slots: Any,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"python_divider": citry_ui.CDivider(variant="dotted")}

    css = """
      :where(.divider-basic) {
        display: grid;
        gap: 1rem;
        max-inline-size: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.divider-basic h2, .divider-basic p) {
        margin: 0;
      }

      :where(.divider-basic h2) {
        font-size: 1rem;
      }
    """


preview = BasicDividers()

preview  # noqa: B018
````



```citry-html
<c-CDivider />
```


Compose the same result in Python:


```python
from citry_ui import CDivider

divider = CDivider()
```


## Choose semantic or decorative output

Keep the default when the break separates topics. Use `decorative=True` when
the line is only visual and nearby structure already conveys the grouping.


### Compare semantic and decorative lines

[Open the rendered preview](/v/0.4.2/ui-library/components/divider/_previews/semantic-and-decorative/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SemanticAndDecorativeDividers(Component):
    template = """
      <section class="divider-meaning">
        <article>
          <h2>Semantic break</h2>
          <p>Observation notes end here.</p>
          <c-CDivider />
          <p>A new topic begins with the equipment log.</p>
        </article>
        <article>
          <h2>Decorative line</h2>
          <div class="divider-meaning__metric">
            <span>Exposure</span>
            <c-CDivider c-decorative="True" />
            <strong>180 s</strong>
          </div>
        </article>
      </section>
    """
    css = """
      :where(.divider-meaning) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
        gap: 1rem;
        max-inline-size: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.divider-meaning article) {
        display: grid;
        gap: 0.75rem;
        padding: 1rem;
        border: 1px solid light-dark(#cbd5e1, #475569);
        border-radius: 0.75rem;
      }

      :where(.divider-meaning h2, .divider-meaning p) {
        margin: 0;
      }

      :where(.divider-meaning h2) {
        font-size: 1rem;
      }

      :where(.divider-meaning__metric) {
        display: grid;
        gap: 0.5rem;
      }
    """


preview = SemanticAndDecorativeDividers()

preview  # noqa: B018
````


## Choose orientation

Horizontal Dividers separate vertically stacked content. Vertical Dividers
separate items across a flex or grid row and stretch with their container.


### Compare horizontal and vertical Dividers

[Open the rendered preview](/v/0.4.2/ui-library/components/divider/_previews/orientations/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DividerOrientations(Component):
    template = """
      <section class="divider-orientations">
        <div class="divider-orientations__horizontal">
          <span>First quarter</span>
          <c-CDivider variant="dashed" c-decorative="True" />
          <span>Full moon</span>
        </div>
        <div class="divider-orientations__vertical">
          <span>Rise 20:14</span>
          <c-CDivider orientation="vertical" c-decorative="True" />
          <span>Transit 01:36</span>
          <c-CDivider orientation="vertical" c-decorative="True" />
          <span>Set 06:51</span>
        </div>
      </section>
    """
    css = """
      :where(.divider-orientations) {
        display: grid;
        gap: 1.25rem;
        max-inline-size: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.divider-orientations__horizontal) {
        display: grid;
        gap: 0.75rem;
      }

      :where(.divider-orientations__vertical) {
        display: flex;
        min-block-size: 2.5rem;
        flex-wrap: wrap;
        align-items: stretch;
        gap: 0.75rem;
        padding: 0.75rem;
        border-radius: 0.6rem;
        background: light-dark(#eef2ff, #1e2744);
      }
    """


preview = DividerOrientations()

preview  # noqa: B018
````


## Add a visible label

The optional default slot places ordinary visible content between two
decorative lines. Use a real heading inside when the document needs heading
semantics. Labels are horizontal only.


### Position visible Divider labels

[Open the rendered preview](/v/0.4.2/ui-library/components/divider/_previews/labels/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DividerLabels(Component):
    template = """
      <section class="divider-labels">
        <c-CDivider label_pos="start">Inner planets</c-CDivider>
        <c-CDivider>Asteroid belt</c-CDivider>
        <c-CDivider label_pos="end">Outer planets</c-CDivider>
      </section>
    """
    css = """
      :where(.divider-labels) {
        display: grid;
        gap: 1.5rem;
        max-inline-size: 40rem;
        padding: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = DividerLabels()

preview  # noqa: B018
````


## Choose line style and thickness

Variants select solid, dashed, or dotted lines. Sizes provide concise 1, 2,
and 4 pixel thickness presets.


### Compare Divider variants and sizes

[Open the rendered preview](/v/0.4.2/ui-library/components/divider/_previews/variants-and-sizes/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DividerVariantsAndSizes(Component):
    template = """
      <section class="divider-matrix">
        <c-for each="variant in variants">
          <div class="divider-matrix__row">
            <code>{{ variant }}</code>
            <c-for each="size in sizes">
              <div>
                <span>{{ size }}</span>
                <c-CDivider c-variant="variant" c-size="size" c-decorative="True" />
              </div>
            </c-for>
          </div>
        </c-for>
      </section>
    """

    def template_data(
        self,
        kwargs: Any,  # noqa: ARG002
        slots: Any,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "variants": ("solid", "dashed", "dotted"),
            "sizes": ("sm", "md", "lg"),
        }

    css = """
      :where(.divider-matrix) {
        display: grid;
        gap: 1rem;
        max-inline-size: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.divider-matrix__row) {
        display: grid;
        grid-template-columns: 5rem repeat(3, minmax(4rem, 1fr));
        align-items: center;
        gap: 0.75rem;
      }

      :where(.divider-matrix__row > div) {
        display: grid;
        gap: 0.35rem;
      }

      :where(.divider-matrix span) {
        color: light-dark(#475569, #cbd5e1);
        font-size: 0.72rem;
        text-align: center;
      }
    """


preview = DividerVariantsAndSizes()

preview  # noqa: B018
````


## Align with nested content

Insets add logical spacing along the line axis. They follow text direction,
so `start` and `end` remain meaningful in LTR and RTL layouts.


### Apply logical Divider insets

[Open the rendered preview](/v/0.4.2/ui-library/components/divider/_previews/insets/)

````citry
from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DividerInsets(Component):
    template = """
      <section class="divider-insets">
        <c-for each="inset in insets">
          <div>
            <span>{{ inset }}</span>
            <c-CDivider c-inset="inset" c-decorative="True" />
          </div>
        </c-for>
        <div dir="rtl">
          <span>start in RTL</span>
          <c-CDivider inset="start" c-decorative="True" />
        </div>
      </section>
    """

    def template_data(
        self,
        kwargs: Any,  # noqa: ARG002
        slots: Any,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"insets": ("none", "start", "end", "both")}

    css = """
      :where(.divider-insets) {
        display: grid;
        gap: 1rem;
        max-inline-size: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.divider-insets > div) {
        display: grid;
        gap: 0.35rem;
        padding: 0.5rem;
        border-inline: 1px dashed light-dark(#94a3b8, #64748b);
      }

      :where(.divider-insets span) {
        font-size: 0.75rem;
      }
    """


preview = DividerInsets()

preview  # noqa: B018
````


## Customize Divider

Override public variables on an ancestor or one Divider. Stable selectors let
you style the root, label, or labelled line segments without private classes.


### Customize Divider with public CSS

[Open the rendered preview](/v/0.4.2/ui-library/components/divider/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DividerCustomization(Component):
    template = """
      <section class="divider-themes">
        <div class="divider-themes__aurora">
          <c-CDivider>Polar observatory</c-CDivider>
        </div>
        <div class="divider-themes__eclipse">
          <c-CDivider variant="dotted">Eclipse watch</c-CDivider>
        </div>
      </section>
    """
    css = """
      :where(.divider-themes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
        gap: 1rem;
        max-inline-size: 40rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.divider-themes > div) {
        padding: 1.25rem;
        border-radius: 0.75rem;
      }

      :where(.divider-themes__aurora) {
        --cui-divider-color: #138a7b;
        --cui-divider-label-color: #12584f;
        --cui-divider-thickness: 2px;
        background: #e7faf6;
      }

      :where(.divider-themes__eclipse) {
        color-scheme: dark;
        --cui-divider-color: #f2b84b;
        --cui-divider-label-color: #ffe2a6;
        --cui-divider-label-font-weight: 750;
        background: #171421;
      }

      :where(.divider-themes [data-citry-ui-part="label"]) {
        letter-spacing: 0.03em;
      }
    """


preview = DividerCustomization()

preview  # noqa: B018
````


## Accessibility and behavior

The default horizontal form renders a native `hr`. The vertical form renders
a nonfocusable ARIA separator. Decorative output is hidden from assistive
technology. Labelled lines are decorative while the label remains ordinary
document content.

Divider never owns focus, keyboard input, resize behavior, or external margin.
Use layout gaps for spacing and `CSplitter` for adjustable
panes.

## API reference

### Inputs

#### CDivider server inputs

Server inputs are passed in a template through `<c-CDivider ... />` or in Python through
`CDivider(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="divider-input-cdivider-server-inputs-orientation"></span>`orientation` | `"horizontal" | "vertical"` ([`CDividerOrientation`](#divider-interface-input-type-aliases-cdivider-orientation)) | `"horizontal"` | Selects native horizontal or ARIA vertical separator semantics. |
| <span id="divider-input-cdivider-server-inputs-variant"></span>`variant` | `"solid" | "dashed" | "dotted"` ([`CDividerVariant`](#divider-interface-input-type-aliases-cdivider-variant)) | `"solid"` | Selects the line style. |
| <span id="divider-input-cdivider-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CDividerSize`](#divider-interface-input-type-aliases-cdivider-size)) | `"sm"` | Selects 1px, 2px, or 4px fallback thickness. |
| <span id="divider-input-cdivider-server-inputs-inset"></span>`inset` | `"none" | "start" | "end" | "both"` ([`CDividerInset`](#divider-interface-input-type-aliases-cdivider-inset)) | `"none"` | Adds logical spacing along the line axis. |
| <span id="divider-input-cdivider-server-inputs-label-pos"></span>`label_pos` | `"start" | "center" | "end"` ([`CDividerLabelPos`](#divider-interface-input-type-aliases-cdivider-label-pos)) | `"center"` | Positions a supplied visible label; non-default values require the default slot. |
| <span id="divider-input-cdivider-server-inputs-decorative"></span>`decorative` | `bool` | `False` | Removes an unlabelled Divider from the accessibility tree. Labelled line segments are always decorative. |
| <span id="divider-input-cdivider-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#divider-interface-input-type-aliases-class-value)) | `None` | Adds root classes and merges them with `attrs`. |
| <span id="divider-input-cdivider-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#divider-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles and merges them with `attrs`. |
| <span id="divider-input-cdivider-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied trusted native, data, targeted Alpine, and event attributes without replacing Divider semantics, anatomy, or Citry runtime fields. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CDivider slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="divider-slot-cdivider-slots-default"></span>`default` | no | `{}` ([`CDividerDefaultSlotData`](#divider-interface-cdivider-default-slot-data)) | Renders one unlabelled line. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CDivider CSS variables

Apply these variables to `CDivider` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="divider-css-cdivider-css-variables-cui-divider-color"></span>`--cui-divider-color` | `color` | Line color. | `Nested-scheme border color.` |
| <span id="divider-css-cdivider-css-variables-cui-divider-thickness"></span>`--cui-divider-thickness` | `length` | Line thickness. | `Size-derived 1px, 2px, or 4px.` |
| <span id="divider-css-cdivider-css-variables-cui-divider-inset"></span>`--cui-divider-inset` | `length` | Logical start/end inset amount. | `1.5rem` |
| <span id="divider-css-cdivider-css-variables-cui-divider-label-gap"></span>`--cui-divider-label-gap` | `length` | Gap from a visible label to each line. | `0.75rem` |
| <span id="divider-css-cdivider-css-variables-cui-divider-label-color"></span>`--cui-divider-label-color` | `color` | Visible label foreground. | `CanvasText` |
| <span id="divider-css-cdivider-css-variables-cui-divider-label-font-size"></span>`--cui-divider-label-font-size` | `length` | Visible label text size. | `0.875rem` |
| <span id="divider-css-cdivider-css-variables-cui-divider-label-font-weight"></span>`--cui-divider-label-font-weight` | `font-weight` | Visible label emphasis. | `600` |
| <span id="divider-css-cdivider-css-variables-cui-divider-min-length"></span>`--cui-divider-min-length` | `length` | Useful vertical minimum length. | `1em` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CDivider attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="divider-attribute-cdivider-attributes-data-orientation"></span>`data-orientation` | Root | `"horizontal" | "vertical"` | Reflects the line axis and semantic form. |
| <span id="divider-attribute-cdivider-attributes-data-variant"></span>`data-variant` | Root | `"solid" | "dashed" | "dotted"` | Reflects the line style. |
| <span id="divider-attribute-cdivider-attributes-data-size"></span>`data-size` | Root | `"sm" | "md" | "lg"` | Reflects the thickness preset. |
| <span id="divider-attribute-cdivider-attributes-data-inset"></span>`data-inset` | Root | `"none" | "start" | "end" | "both"` | Reflects logical inset geometry. |
| <span id="divider-attribute-cdivider-attributes-data-labeled"></span>`data-labeled` | Root | `present-or-absent` | Present when the default label slot renders. |
| <span id="divider-attribute-cdivider-attributes-data-label-pos"></span>`data-label-pos` | Labelled root | `"start" | "center" | "end"` | Reflects labelled line balance. |
| <span id="divider-attribute-cdivider-attributes-data-decorative"></span>`data-decorative` | Root | `present-or-absent` | Present when the line exposes no separator semantics. |
| <span id="divider-attribute-cdivider-attributes-aria-orientation"></span>`aria-orientation` | Vertical semantic root | `"vertical"` | Communicates the nondefault separator orientation. |
| <span id="divider-attribute-cdivider-attributes-aria-hidden"></span>`aria-hidden` | Decorative root or labelled line | `boolean-presence` | Removes the decorative line from the accessibility tree. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CDivider selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="divider-selector-cdivider-selectors-data-citry-ui-part-divider"></span>`[data-citry-ui-part="divider"]` | Root | Stable Divider root and `attrs` destination. |
| <span id="divider-selector-cdivider-selectors-data-citry-ui-part-line"></span>`[data-citry-ui-part="line"]` | Labelled decorative line segment | Styles either of the two direct line children. |
| <span id="divider-selector-cdivider-selectors-data-citry-ui-part-label"></span>`[data-citry-ui-part="label"]` | Labelled visible-content wrapper | Styles the authored section label. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="divider-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="divider-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="divider-interface-input-type-aliases-cdivider-orientation"></span>`CDividerOrientation` | `Literal["horizontal", "vertical"]` |
| <span id="divider-interface-input-type-aliases-cdivider-variant"></span>`CDividerVariant` | `Literal["solid", "dashed", "dotted"]` |
| <span id="divider-interface-input-type-aliases-cdivider-size"></span>`CDividerSize` | `Literal["sm", "md", "lg"]` |
| <span id="divider-interface-input-type-aliases-cdivider-inset"></span>`CDividerInset` | `Literal["none", "start", "end", "both"]` |
| <span id="divider-interface-input-type-aliases-cdivider-label-pos"></span>`CDividerLabelPos` | `Literal["start", "center", "end"]` |

</div>

<span id="divider-interface-cdivider-default-slot-data"></span>

#### `CDividerDefaultSlotData`

Empty dataclass: `{}`.

### Translation keys

-