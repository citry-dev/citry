---
title: Col and Row
url: https://citry.dev/v/0.4.4/ui-library/components/col-row/
description: "Arrange Citry UI content in predictable vertical columns and wrapping horizontal rows."
---
# Col and Row

Use `CCol` for vertical flow and `CRow` for horizontal flow. Both keep your
children unchanged, expose one native root, and render without JavaScript.

## Layout at a glance


### Compose Col and Row

[Open the rendered preview](/v/0.4.4/ui-library/components/col-row/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FlowAtAGlance(Component):
    template = """
      <c-CCol class_="flow-glance" gap="lg">
        <c-CCol gap="xs">
          <p class="flow-glance__eyebrow">Kiln room · shelf 4</p>
          <h2>Moon jar firing notes</h2>
          <p>Hold at 1,280°C until the glaze softens to a pale blue-white.</p>
        </c-CCol>
        <c-CRow>
          <span class="flow-glance__tag">Porcelain</span>
          <span class="flow-glance__tag">Reduction</span>
          <span class="flow-glance__tag">12 hours</span>
        </c-CRow>
        <c-CRow justify="end">
          <c-CButton variant="ghost">Archive</c-CButton>
          <c-CButton>Save firing</c-CButton>
        </c-CRow>
      </c-CCol>
    """

    css = """
      :where(.flow-glance) {
        max-inline-size: 34rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#d7c8b4, #6f6357);
        border-radius: 0.85rem;
        background: light-dark(#fffaf2, #241f1a);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-glance h2, .flow-glance p) {
        margin: 0;
      }

      :where(.flow-glance h2) {
        font-size: 1.05rem;
      }

      :where(.flow-glance__eyebrow) {
        color: light-dark(#8a4b2b, #f0aa7d);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.flow-glance__tag) {
        padding: 0.25rem 0.55rem;
        border-radius: 999px;
        background: light-dark(#ead8bd, #4a3d31);
        font-size: 0.78rem;
      }
    """


preview = FlowAtAGlance()

preview  # noqa: B018
````



```citry-html
<c-CCol gap="lg">
  <h2>Glaze tests</h2>
  <c-CRow>
    <c-CButton>Archive</c-CButton>
    <c-CButton intent="primary">Publish</c-CButton>
  </c-CRow>
</c-CCol>
```


Compose the same layout in Python:


```python
from citry_ui import CCol, CRow

actions = CRow(slots={"default": ["Archive", "Publish"]})
panel = CCol(gap="lg", slots={"default": ["Glaze tests", actions]})
```


## Choose spacing

Use the shared `0`, `xs`, `sm`, `md`, `lg`, and `xl` presets. Col defaults to
`md`; Row defaults to the tighter `sm`.


### Compare Col spacing

[Open the rendered preview](/v/0.4.4/ui-library/components/col-row/_previews/col-spacing/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class StackSpacing(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="flow-spacing" aria-label="Col gap presets">
        <c-for each="gap in gaps">
          <c-CCol c-gap="gap" class_="flow-spacing__stack">
            <strong>{{ gap }}</strong>
            <span>Clay body</span>
            <span>Glaze test</span>
          </c-CCol>
        </c-for>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"gaps": ("0", "xs", "sm", "md", "lg", "xl")}

    css = """
      :where(.flow-spacing) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr));
        gap: 1rem;
        max-inline-size: 62rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-spacing__stack) {
        padding: 0.85rem;
        border: 1px solid light-dark(#d9c8b2, #62564b);
        border-radius: 0.65rem;
        background: light-dark(#fffaf2, #251f1a);
      }

      :where(.flow-spacing__stack span) {
        padding: 0.35rem;
        border-radius: 0.3rem;
        background: light-dark(#ead8bd, #493b30);
        font-size: 0.8rem;
      }
    """


preview = StackSpacing()

preview  # noqa: B018
````


## Align and distribute children

`align` controls the cross axis. `justify` distributes children along the
flow axis. The same vocabulary works across both components.


### Align and distribute Row children

[Open the rendered preview](/v/0.4.4/ui-library/components/col-row/_previews/row-alignment/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GroupAlignment(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CCol class_="flow-alignments" gap="lg">
        <c-for each="justify in justifies">
          <c-CCol gap="xs">
            <strong>justify={{ justify }}</strong>
            <c-CRow c-justify="justify" class_="flow-alignments__group">
              <span>Trim</span><span>Bisque</span><span>Glaze</span>
            </c-CRow>
          </c-CCol>
        </c-for>
      </c-CCol>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"justifies": ("start", "center", "end", "between", "around", "evenly")}

    css = """
      :where(.flow-alignments) {
        max-inline-size: 44rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-alignments__group) {
        min-block-size: 3.5rem;
        padding: 0.65rem;
        border-radius: 0.55rem;
        background: light-dark(#f2e4cf, #362c24);
      }

      :where(.flow-alignments__group span) {
        padding: 0.35rem 0.5rem;
        border-radius: 0.35rem;
        background: light-dark(#b96540, #d7815b);
        color: #ffffff;
        font-size: 0.78rem;
      }
    """


preview = GroupAlignment()

preview  # noqa: B018
````


## Wrap horizontal content

Row wraps by default, making action rows and short metadata collections safe
at narrow widths. Set `wrap=False` only when horizontal overflow is deliberate.


### Compare wrapping behavior

[Open the rendered preview](/v/0.4.4/ui-library/components/col-row/_previews/wrapping/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GroupWrapping(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="flow-wrapping" aria-label="Row wrapping">
        <c-CCol gap="xs">
          <strong>Wraps by default</strong>
          <c-CRow class_="flow-wrapping__group">
            <c-for each="label in labels"><span>{{ label }}</span></c-for>
          </c-CRow>
        </c-CCol>
        <c-CCol gap="xs">
          <strong>No wrap</strong>
          <div class="flow-wrapping__scroll">
            <c-CRow c-wrap="False" class_="flow-wrapping__group">
              <c-for each="label in labels"><span>{{ label }}</span></c-for>
            </c-CRow>
          </div>
        </c-CCol>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"labels": ("Wheel throwing", "Hand building", "Slip casting", "Raku firing")}

    css = """
      :where(.flow-wrapping) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
        gap: 1rem;
        max-inline-size: 46rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-wrapping__group) {
        inline-size: 100%;
        padding: 0.75rem;
        background: light-dark(#f1e0c7, #352b23);
      }

      :where(.flow-wrapping__group span) {
        padding: 0.35rem 0.55rem;
        border: 1px solid currentColor;
        border-radius: 999px;
        white-space: nowrap;
      }

      :where(.flow-wrapping__scroll) {
        overflow-x: auto;
      }
    """


preview = GroupWrapping()

preview  # noqa: B018
````


## Choose native semantics

The default `div` makes no semantic claim. Use `section` for a named section,
`nav` for navigation, or `ul`/`ol` when every direct child follows native list
content rules.


### Choose semantic roots

[Open the rendered preview](/v/0.4.4/ui-library/components/col-row/_previews/semantic-roots/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FlowSemanticRoots(Component):
    template = """
      <c-CCol class_="flow-semantics" gap="lg">
        <c-CRow tag="nav" c-attrs="{'aria-label': 'Ceramics notebook'}">
          <a href="#clay">Clay</a><a href="#glaze">Glaze</a><a href="#kilns">Kilns</a>
        </c-CRow>
        <c-CCol tag="ol" gap="sm" class_="flow-semantics__list">
          <li>Wedge the porcelain.</li>
          <li>Center it on the wheel.</li>
          <li>Pull the walls evenly.</li>
        </c-CCol>
      </c-CCol>
    """

    css = """
      :where(.flow-semantics) {
        max-inline-size: 36rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-semantics a) {
        color: light-dark(#8a3f24, #f0a47c);
      }

      :where(.flow-semantics__list) {
        margin: 0;
        padding-inline-start: 1.4rem;
      }
    """


preview = FlowSemanticRoots()

preview  # noqa: B018
````


The components add no role, accessible name, heading, or list item. Supply the
native structure required by your content.

## Nest layouts

Col and Row can be nested without extra coordination or client state.


### Build a nested ceramics layout

[Open the rendered preview](/v/0.4.4/ui-library/components/col-row/_previews/nested-layouts/)

````citry
from dataclasses import dataclass

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


@dataclass(frozen=True, slots=True)
class FiringBatch:
    name: str
    clay: str
    cone: str


class NestedFlowLayouts(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CCol class_="flow-nested" gap="lg">
        <c-for each="batch in batches">
          <c-CRow justify="between" class_="flow-nested__row">
            <c-CCol gap="0">
              <strong>{{ batch.name }}</strong>
              <span>{{ batch.clay }}</span>
            </c-CCol>
            <c-CRow gap="xs">
              <span class="flow-nested__cone">{{ batch.cone }}</span>
              <c-CButton size="sm" variant="outline">Open log</c-CButton>
            </c-CRow>
          </c-CRow>
        </c-for>
      </c-CCol>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "batches": (
                FiringBatch("Sea mist bowls", "Porcelain", "Cone 10"),
                FiringBatch("Cedar cups", "Speckled stoneware", "Cone 6"),
                FiringBatch("Ember vases", "Red earthenware", "Cone 04"),
            )
        }

    css = """
      :where(.flow-nested) {
        max-inline-size: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-nested__row) {
        padding: 0.8rem;
        border-block-end: 1px solid light-dark(#d6c4ad, #5f5247);
      }

      :where(.flow-nested__cone) {
        padding: 0.2rem 0.5rem;
        border-radius: 999px;
        background: light-dark(#ead7bd, #4b3b30);
        font-size: 0.75rem;
      }
    """


preview = NestedFlowLayouts()

preview  # noqa: B018
````


## Customize layout

Override the public gap variables on an ancestor or one instance. Use stable
part selectors, `class_`, or `style` for responsive rules beyond the preset
API.


### Customize Flow with public CSS

[Open the rendered preview](/v/0.4.4/ui-library/components/col-row/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FlowCustomization(Component):
    template = """
      <section class="flow-custom" aria-label="Customized Flow layouts">
        <div class="flow-custom__brand flow-custom__brand--cobalt">
          <c-CCol><strong>Cobalt studio</strong><span>Wide vertical rhythm</span></c-CCol>
        </div>
        <div class="flow-custom__brand flow-custom__brand--clay">
          <c-CRow><strong>Clay archive</strong><span>Compact action spacing</span></c-CRow>
        </div>
      </section>
    """

    css = """
      :where(.flow-custom) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        max-inline-size: 40rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-custom__brand) {
        padding: 1rem;
        border-radius: 0.75rem;
      }

      :where(.flow-custom__brand--cobalt) {
        --cui-col-gap: 1.35rem;
        background: light-dark(#dbe8f5, #172b40);
      }

      :where(.flow-custom__brand--clay) {
        --cui-row-gap: 0.25rem;
        background: light-dark(#f2dfd0, #3b2820);
      }

      :where(.flow-custom__brand [data-citry-ui-part="col"], .flow-custom__brand [data-citry-ui-part="row"]) {
        padding: 0.7rem;
        border: 1px solid currentColor;
        border-radius: 0.5rem;
      }
    """


preview = FlowCustomization()

preview  # noqa: B018
````


## Direction, visual order, and accessibility

Logical alignment follows the document direction. `reverse=True` reverses only
the visual flex flow: DOM, reading, and keyboard order do not change. Use it
only when the original order remains understandable.


### Compare direction and visual order

[Open the rendered preview](/v/0.4.4/ui-library/components/col-row/_previews/direction/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FlowDirection(Component):
    template = """
      <section class="flow-direction" aria-label="Direction and long content">
        <c-CCol gap="sm">
          <strong>LTR kiln sequence</strong>
          <c-CRow><span>Load</span><span>Fire</span><span>Cool</span></c-CRow>
        </c-CCol>
        <div dir="rtl">
          <c-CCol gap="sm">
            <strong>تسلسل الفرن</strong>
            <c-CRow><span>تحميل</span><span>حرق</span><span>تبريد</span></c-CRow>
          </c-CCol>
        </div>
        <c-CRow class_="flow-direction__long">
          <strong>Long label</strong>
          <span>celadon-test-series-with-a-deliberately-long-unbroken-identifier</span>
        </c-CRow>
      </section>
    """

    css = """
      :where(.flow-direction) {
        display: grid;
        gap: 1.25rem;
        max-inline-size: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-direction [data-citry-ui-part="row"]) {
        padding: 0.7rem;
        background: light-dark(#eee0c9, #372d24);
      }

      :where(.flow-direction__long span) {
        min-inline-size: 0;
        overflow-wrap: anywhere;
      }
    """


preview = FlowDirection()

preview  # noqa: B018
````


Flow renders completely without JavaScript. Attribute maps accept native,
ARIA, data, and trusted targeted Alpine attributes, but reserve layout
reflections, part markers, structural directives, and Citry runtime ownership
fields.

## API reference

### Inputs

#### CCol server inputs

Server inputs are passed in a template through `<c-CCol ... />` or in Python through
`CCol(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 16rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="flow-layout-input-ccol-server-inputs-tag"></span>`tag` | `"div" | "section" | "nav" | "ul" | "ol"` ([`CFlowTag`](#flow-layout-interface-input-type-aliases-cflow-tag)) | `"div"` | Selects the native root without adding a role or accessible name. |
| <span id="flow-layout-input-ccol-server-inputs-gap"></span>`gap` | `"0" | "xs" | "sm" | "md" | "lg" | "xl"` ([`CFlowGap`](#flow-layout-interface-input-type-aliases-cflow-gap)) | `"md"` | Selects the vertical space between direct children. |
| <span id="flow-layout-input-ccol-server-inputs-align"></span>`align` | `"start" | "center" | "end" | "stretch" | "baseline"` ([`CFlowAlign`](#flow-layout-interface-input-type-aliases-cflow-align)) | `"stretch"` | Aligns direct children across the horizontal axis. |
| <span id="flow-layout-input-ccol-server-inputs-justify"></span>`justify` | `"start" | "center" | "end" | "between" | "around" | "evenly"` ([`CFlowJustify`](#flow-layout-interface-input-type-aliases-cflow-justify)) | `"start"` | Distributes direct children along the vertical axis. |
| <span id="flow-layout-input-ccol-server-inputs-reverse"></span>`reverse` | `bool` | `False` | Reverses visual flow without changing DOM, reading, or Tab order. |
| <span id="flow-layout-input-ccol-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#flow-layout-interface-input-type-aliases-class-value)) | `None` | Adds root classes and merges them with `attrs`. |
| <span id="flow-layout-input-ccol-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#flow-layout-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles and merges them with `attrs`. |
| <span id="flow-layout-input-ccol-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds native, ARIA, data, and trusted targeted Alpine attributes without replacing owned layout or Citry runtime fields. |

</div>

#### CRow server inputs

Server inputs are passed in a template through `<c-CRow ... />` or in Python through
`CRow(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 16rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="flow-layout-input-crow-server-inputs-tag"></span>`tag` | `"div" | "section" | "nav" | "ul" | "ol"` ([`CFlowTag`](#flow-layout-interface-input-type-aliases-cflow-tag)) | `"div"` | Selects the native root without adding a role or accessible name. |
| <span id="flow-layout-input-crow-server-inputs-gap"></span>`gap` | `"0" | "xs" | "sm" | "md" | "lg" | "xl"` ([`CFlowGap`](#flow-layout-interface-input-type-aliases-cflow-gap)) | `"sm"` | Selects horizontal and wrapped-row spacing between direct children. |
| <span id="flow-layout-input-crow-server-inputs-align"></span>`align` | `"start" | "center" | "end" | "stretch" | "baseline"` ([`CFlowAlign`](#flow-layout-interface-input-type-aliases-cflow-align)) | `"center"` | Aligns direct children across each row. |
| <span id="flow-layout-input-crow-server-inputs-justify"></span>`justify` | `"start" | "center" | "end" | "between" | "around" | "evenly"` ([`CFlowJustify`](#flow-layout-interface-input-type-aliases-cflow-justify)) | `"start"` | Distributes direct children along each row. |
| <span id="flow-layout-input-crow-server-inputs-wrap"></span>`wrap` | `bool` | `True` | Allows direct children to continue on later rows when space runs out. |
| <span id="flow-layout-input-crow-server-inputs-reverse"></span>`reverse` | `bool` | `False` | Reverses visual flow without changing DOM, reading, or Tab order. |
| <span id="flow-layout-input-crow-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#flow-layout-interface-input-type-aliases-class-value)) | `None` | Adds root classes and merges them with `attrs`. |
| <span id="flow-layout-input-crow-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#flow-layout-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles and merges them with `attrs`. |
| <span id="flow-layout-input-crow-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds native, ARIA, data, and trusted targeted Alpine attributes without replacing owned layout or Citry runtime fields. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CCol slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="flow-layout-slot-ccol-slots-default"></span>`default` | no | `{}` ([`CColDefaultSlotData`](#flow-layout-interface-ccol-default-slot-data)) | Renders an empty layout root. |

</div>

#### CRow slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="flow-layout-slot-crow-slots-default"></span>`default` | no | `{}` ([`CRowDefaultSlotData`](#flow-layout-interface-crow-default-slot-data)) | Renders an empty layout root. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CCol CSS variables

Apply these variables to `CCol` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="flow-layout-css-ccol-css-variables-cui-col-gap"></span>`--cui-col-gap` | `length` | Overrides the selected direct-child gap. | `Gap-preset length.` |

</div>

#### CRow CSS variables

Apply these variables to `CRow` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="flow-layout-css-crow-css-variables-cui-row-gap"></span>`--cui-row-gap` | `length` | Overrides horizontal and wrapped-row gaps. | `Gap-preset length.` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CCol attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="flow-layout-attribute-ccol-attributes-data-gap"></span>`data-gap` | Root | `"0" | "xs" | "sm" | "md" | "lg" | "xl"` | Reflects the selected spacing preset. |
| <span id="flow-layout-attribute-ccol-attributes-data-align"></span>`data-align` | Root | `"start" | "center" | "end" | "stretch" | "baseline"` | Reflects cross-axis alignment. |
| <span id="flow-layout-attribute-ccol-attributes-data-justify"></span>`data-justify` | Root | `"start" | "center" | "end" | "between" | "around" | "evenly"` | Reflects main-axis distribution. |
| <span id="flow-layout-attribute-ccol-attributes-data-reverse"></span>`data-reverse` | Root | `Boolean presence` | Present while visual order is reversed. |

</div>

#### CRow attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="flow-layout-attribute-crow-attributes-data-gap"></span>`data-gap` | Root | `"0" | "xs" | "sm" | "md" | "lg" | "xl"` | Reflects the selected spacing preset. |
| <span id="flow-layout-attribute-crow-attributes-data-align"></span>`data-align` | Root | `"start" | "center" | "end" | "stretch" | "baseline"` | Reflects cross-axis alignment. |
| <span id="flow-layout-attribute-crow-attributes-data-justify"></span>`data-justify` | Root | `"start" | "center" | "end" | "between" | "around" | "evenly"` | Reflects main-axis distribution. |
| <span id="flow-layout-attribute-crow-attributes-data-wrap"></span>`data-wrap` | Root | `Boolean presence` | Present while wrapping is enabled. |
| <span id="flow-layout-attribute-crow-attributes-data-reverse"></span>`data-reverse` | Root | `Boolean presence` | Present while visual order is reversed. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CCol selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="flow-layout-selector-ccol-selectors-data-citry-ui-part-col"></span>`[data-citry-ui-part="col"]` | Native root | Stable Col root and `attrs` destination. |

</div>

#### CRow selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="flow-layout-selector-crow-selectors-data-citry-ui-part-row"></span>`[data-citry-ui-part="row"]` | Native root | Stable Row root and `attrs` destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="flow-layout-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="flow-layout-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="flow-layout-interface-input-type-aliases-cflow-tag"></span>`CFlowTag` | `Literal["div", "section", "nav", "ul", "ol"]` |
| <span id="flow-layout-interface-input-type-aliases-cflow-gap"></span>`CFlowGap` | `Literal["0", "xs", "sm", "md", "lg", "xl"]` |
| <span id="flow-layout-interface-input-type-aliases-cflow-align"></span>`CFlowAlign` | `Literal["start", "center", "end", "stretch", "baseline"]` |
| <span id="flow-layout-interface-input-type-aliases-cflow-justify"></span>`CFlowJustify` | `Literal["start", "center", "end", "between", "around", "evenly"]` |

</div>

<span id="flow-layout-interface-ccol-default-slot-data"></span>

#### `CColDefaultSlotData`

Empty dataclass: `{}`.

<span id="flow-layout-interface-crow-default-slot-data"></span>

#### `CRowDefaultSlotData`

Empty dataclass: `{}`.

### Translation keys

-