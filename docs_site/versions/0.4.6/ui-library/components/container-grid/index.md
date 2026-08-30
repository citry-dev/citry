---
title: Container and Grid
url: https://citry.dev/v/0.4.6/ui-library/components/container-grid/
description: "Constrain page content, build responsive equal grids, and add asymmetric spans when needed."
---
# Container and Grid

`CContainer` constrains page width. `CGrid` handles the common equal-column
layout. Add `CGridItem` only when individual content needs an asymmetric span.
All three render with native CSS and no JavaScript.

## Layout at a glance


### Browse a responsive mineral atlas

[Open the rendered preview](/v/0.4.6/ui-library/components/container-grid/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GridAtAGlance(Component):
    template = """
      <c-CContainer class_="mineral-atlas" size="lg">
        <header class="mineral-atlas__header">
          <p>Field atlas · volcanic collection</p>
          <h2>Minerals born from fire</h2>
        </header>
        <c-CGrid sm="2" lg="4" gap="lg">
          <article class="mineral-atlas__card mineral-atlas__card--olivine">
            <span class="mineral-atlas__sample"></span>
            <h3>Olivine</h3>
            <p>Olive-green crystals found in basalt and mantle rock.</p>
          </article>
          <article class="mineral-atlas__card mineral-atlas__card--obsidian">
            <span class="mineral-atlas__sample"></span>
            <h3>Obsidian</h3>
            <p>Volcanic glass cooled before crystals could form.</p>
          </article>
          <article class="mineral-atlas__card mineral-atlas__card--sulfur">
            <span class="mineral-atlas__sample"></span>
            <h3>Sulfur</h3>
            <p>Bright deposits gathered around volcanic vents.</p>
          </article>
          <article class="mineral-atlas__card mineral-atlas__card--pumice">
            <span class="mineral-atlas__sample"></span>
            <h3>Pumice</h3>
            <p>Foamed lava light enough to float on water.</p>
          </article>
        </c-CGrid>
      </c-CContainer>
    """

    css = """
      :where(.mineral-atlas) {
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.mineral-atlas__header) {
        margin-block-end: 1.25rem;
      }

      :where(.mineral-atlas__header h2, .mineral-atlas__header p, .mineral-atlas__card h3, .mineral-atlas__card p) {
        margin: 0;
      }

      :where(.mineral-atlas__header p) {
        color: light-dark(#7c3f16, #f4ad74);
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.mineral-atlas__header h2) {
        margin-block-start: 0.25rem;
        font-size: 1.1rem;
      }

      :where(.mineral-atlas__card) {
        padding: 1rem;
        border: 1px solid light-dark(#d7d3c8, #55524b);
        border-radius: 0.8rem;
        background: light-dark(#fffefa, #22211f);
      }

      :where(.mineral-atlas__sample) {
        display: block;
        inline-size: 2.25rem;
        block-size: 2.25rem;
        margin-block-end: 0.8rem;
        border-radius: 0.65rem 1rem 0.5rem 0.9rem;
        background: var(--sample-color);
        box-shadow: inset -0.3rem -0.3rem 0.7rem rgb(0 0 0 / 20%);
        transform: rotate(-7deg);
      }

      :where(.mineral-atlas__card h3) {
        font-size: 0.9rem;
      }

      :where(.mineral-atlas__card p) {
        margin-block-start: 0.35rem;
        color: GrayText;
        font-size: 0.78rem;
        line-height: 1.45;
      }

      :where(.mineral-atlas__card--olivine) {
        --sample-color: #7c9d38;
      }

      :where(.mineral-atlas__card--obsidian) {
        --sample-color: #493e57;
      }

      :where(.mineral-atlas__card--sulfur) {
        --sample-color: #efc928;
      }

      :where(.mineral-atlas__card--pumice) {
        --sample-color: #caa68e;
      }
    """


preview = GridAtAGlance()

preview  # noqa: B018
````



```citry-html
<c-CContainer>
  <c-CGrid sm="2" lg="4">
    ...
  </c-CGrid>
</c-CContainer>
```


The base layout has one column. `sm="2"` applies from `40rem`; `lg="4"`
applies from `64rem`. Missing breakpoints keep the nearest earlier value.

## Choose responsive columns

Put equal-column counts on Grid itself. This keeps the frequent card, tile,
and gallery case short—no item wrapper required.


### Compare fixed and responsive columns

[Open the rendered preview](/v/0.4.6/ui-library/components/container-grid/_previews/responsive-columns/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GridResponsiveColumns(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="grid-columns" aria-labelledby="grid-columns-title">
        <h2 id="grid-columns-title">Crystal systems</h2>
        <p>Resize the preview to watch one column become two, then four.</p>
        <c-CGrid sm="2" lg="4" gap="sm">
          <c-for each="system in systems">
            <div class="grid-columns__cell">{{ system }}</div>
          </c-for>
        </c-CGrid>
        <h3>Fixed three-column index</h3>
        <c-CGrid cols="3" gap="sm">
          <c-for each="name in fixed_names">
            <div class="grid-columns__cell grid-columns__cell--quiet">{{ name }}</div>
          </c-for>
        </c-CGrid>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "systems": ("Cubic", "Hexagonal", "Monoclinic", "Trigonal"),
            "fixed_names": ("Quartz", "Calcite", "Galena"),
        }

    css = """
      :where(.grid-columns) {
        max-inline-size: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.grid-columns h2, .grid-columns h3, .grid-columns p) {
        margin: 0;
      }

      :where(.grid-columns h2) {
        font-size: 1rem;
      }

      :where(.grid-columns h3) {
        margin-block-start: 1.25rem;
        margin-block-end: 0.5rem;
        font-size: 0.82rem;
      }

      :where(.grid-columns p) {
        margin-block: 0.25rem 0.8rem;
        color: GrayText;
        font-size: 0.78rem;
      }

      :where(.grid-columns__cell) {
        min-block-size: 3.25rem;
        padding: 0.7rem;
        border-inline-start: 0.3rem solid #4b77be;
        border-radius: 0.35rem;
        background: light-dark(#edf4ff, #1c2b40);
        font-size: 0.78rem;
        font-weight: 700;
      }

      :where(.grid-columns__cell--quiet) {
        border-inline-start-color: #a55f38;
        background: light-dark(#faf0e9, #35241c);
      }
    """


preview = GridResponsiveColumns()

preview  # noqa: B018
````


Static template values use flat decimal attributes. Dynamic template values
use the normal `c-` expression prefix:


```citry-html
<c-CGrid sm="2" c-lg="desktop_cols">
  ...
</c-CGrid>
```


Python uses integers: `CGrid(sm=2, lg=desktop_cols)`.

## Build asymmetric layouts

Use a 12-column Grid and span only the exceptional items. `CGridItem` remains
a normal wrapper; it adds no region or landmark semantics.


### Compose field notes and a specimen index

[Open the rendered preview](/v/0.4.6/ui-library/components/container-grid/_previews/asymmetric-layout/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GridAsymmetricLayout(Component):
    template = """
      <c-CContainer class_="field-journal" size="lg">
        <c-CGrid cols="12" gap="lg">
          <c-CGridItem tag="article" span="12" md="8" class_="field-journal__notes">
            <p class="field-journal__eyebrow">Expedition 14 · obsidian ridge</p>
            <h2>Glass formed at the lava margin</h2>
            <p>
              The largest fragments show conchoidal fractures, faint silver
              banding, and almost no visible crystal growth.
            </p>
          </c-CGridItem>
          <c-CGridItem tag="aside" span="12" md="4" class_="field-journal__index">
            <h3>Specimen index</h3>
            <dl>
              <div><dt>R-14A</dt><dd>Black glass</dd></div>
              <div><dt>R-14B</dt><dd>Snowflake</dd></div>
              <div><dt>R-14C</dt><dd>Mahogany</dd></div>
            </dl>
          </c-CGridItem>
        </c-CGrid>
      </c-CContainer>
    """

    css = """
      :where(.field-journal) {
        color: CanvasText;
        font-family: ui-serif, Georgia, serif;
      }

      :where(.field-journal__notes, .field-journal__index) {
        padding: 1.1rem;
        border: 1px solid light-dark(#cec8b8, #625d52);
        border-radius: 0.65rem;
        background: light-dark(#fffdf6, #25231f);
      }

      :where(.field-journal h2, .field-journal h3, .field-journal p, .field-journal dl) {
        margin: 0;
      }

      :where(.field-journal__eyebrow) {
        color: light-dark(#8d4727, #eab08d);
        font-family: ui-sans-serif, system-ui, sans-serif;
        font-size: 0.68rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.field-journal h2) {
        margin-block: 0.35rem 0.65rem;
        font-size: 1.05rem;
      }

      :where(.field-journal__notes > p:last-child) {
        color: GrayText;
        font-size: 0.8rem;
        line-height: 1.55;
      }

      :where(.field-journal h3) {
        margin-block-end: 0.6rem;
        font-size: 0.85rem;
      }

      :where(.field-journal dl > div) {
        display: flex;
        justify-content: space-between;
        gap: 0.5rem;
        padding-block: 0.35rem;
        border-block-end: 1px dotted GrayText;
        font-size: 0.76rem;
      }

      :where(.field-journal dd) {
        margin: 0;
        color: GrayText;
      }
    """


preview = GridAsymmetricLayout()

preview  # noqa: B018
````



```citry-html
<c-CGrid cols="12">
  <c-CGridItem span="12" md="8">...</c-CGridItem>
  <c-CGridItem span="12" md="4">...</c-CGridItem>
</c-CGrid>
```


Keep DOM order meaningful. Responsive spans change visual width, not reading,
keyboard, or form-submission order.

## Fit columns to available space

`min_col` uses intrinsic auto-fit tracks. It is useful when card width matters
more than named viewport steps.


### Fit mineral cards by minimum width

[Open the rendered preview](/v/0.4.6/ui-library/components/container-grid/_previews/intrinsic-grid/)

````citry
from dataclasses import dataclass

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


@dataclass(frozen=True, slots=True)
class Mineral:
    name: str
    hardness: str


class GridIntrinsic(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="intrinsic-minerals" aria-labelledby="intrinsic-minerals-title">
        <h2 id="intrinsic-minerals-title">Mohs hardness field set</h2>
        <c-CGrid min_col="11rem" gap="sm">
          <c-for each="mineral in minerals">
            <article class="intrinsic-minerals__card">
              <strong>{{ mineral.name }}</strong>
              <span>{{ mineral.hardness }}</span>
            </article>
          </c-for>
        </c-CGrid>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "minerals": (
                Mineral("Talc", "1 · very soft"),
                Mineral("Calcite", "3 · copper scratch"),
                Mineral("Apatite", "5 · knife edge"),
                Mineral("Quartz", "7 · scratches glass"),
                Mineral("Corundum", "9 · near diamond"),
            )
        }

    css = """
      :where(.intrinsic-minerals) {
        max-inline-size: 50rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.intrinsic-minerals h2) {
        margin: 0 0 0.75rem;
        font-size: 0.95rem;
      }

      :where(.intrinsic-minerals__card) {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        padding: 0.75rem;
        border-block-start: 0.2rem solid #6f63a8;
        background: light-dark(#f5f1ff, #28243a);
        font-size: 0.76rem;
      }

      :where(.intrinsic-minerals__card span) {
        color: GrayText;
        text-align: end;
      }
    """


preview = GridIntrinsic()

preview  # noqa: B018
````


Intrinsic mode owns track sizing, so it cannot be combined with `cols` or
breakpoint counts. For CSS functions such as `clamp()`, set
`--cui-grid-min-column` instead.

## Constrain page content

Container defaults to a centered `80rem` maximum with `1rem` inline gutters.
Choose a smaller/larger size, or use `fluid` to retain gutters without a
maximum width.


### Compare Container sizes and fluid width

[Open the rendered preview](/v/0.4.6/ui-library/components/container-grid/_previews/container-sizes/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GridContainerSizes(Component):
    template = """
      <section class="container-sizes" aria-labelledby="container-sizes-title">
        <h2 id="container-sizes-title">Atlas page widths</h2>
        <c-CContainer size="sm" class_="container-sizes__sample container-sizes__sample--sm">
          <strong>sm · 40rem maximum</strong>
          <span>Focused specimen notes</span>
        </c-CContainer>
        <c-CContainer size="md" class_="container-sizes__sample container-sizes__sample--md">
          <strong>md · 48rem maximum</strong>
          <span>Illustrated field article</span>
        </c-CContainer>
        <c-CContainer fluid class_="container-sizes__sample container-sizes__sample--fluid">
          <strong>fluid · no maximum</strong>
          <span>Full-width comparison plate</span>
        </c-CContainer>
      </section>
    """

    css = """
      :where(.container-sizes) {
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.container-sizes h2) {
        margin: 0 0 0.75rem;
        font-size: 0.95rem;
      }

      :where(.container-sizes__sample) {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        margin-block: 0.5rem;
        padding-block: 0.65rem;
        border: 1px solid light-dark(#cbc7bb, #5c5952);
        border-radius: 0.45rem;
        font-size: 0.74rem;
      }

      :where(.container-sizes__sample span) {
        color: GrayText;
        text-align: end;
      }

      :where(.container-sizes__sample--sm) {
        border-inline-start: 0.3rem solid #b56b3f;
      }

      :where(.container-sizes__sample--md) {
        border-inline-start: 0.3rem solid #4c7a6a;
      }

      :where(.container-sizes__sample--fluid) {
        border-inline-start: 0.3rem solid #596fb1;
      }
    """


preview = GridContainerSizes()

preview  # noqa: B018
````


Container does not establish a CSS query container. Add `container-type` in
consumer CSS only where that behavior is needed.

## Adjust spacing

Grid `gap` controls both axes. Container `gutter` controls logical inline
padding. Both use `0`, `xs`, `sm`, `md`, `lg`, and `xl`.


### Compare Grid gaps and Container gutters

[Open the rendered preview](/v/0.4.6/ui-library/components/container-grid/_previews/spacing/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GridSpacing(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="grid-spacing" aria-labelledby="grid-spacing-title">
        <h2 id="grid-spacing-title">Spacing scale</h2>
        <c-CGrid sm="2" gap="lg">
          <c-for each="gap in gaps">
            <article class="grid-spacing__example">
              <strong>gap={{ gap }}</strong>
              <c-CGrid cols="3" c-gap="gap">
                <span></span><span></span><span></span>
              </c-CGrid>
            </article>
          </c-for>
        </c-CGrid>
        <c-CContainer gutter="xl" class_="grid-spacing__gutter">
          Container gutter=xl keeps this note away from both inline edges.
        </c-CContainer>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"gaps": ("0", "sm", "md", "xl")}

    css = """
      :where(.grid-spacing) {
        max-inline-size: 46rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.grid-spacing h2) {
        margin: 0 0 0.75rem;
        font-size: 0.95rem;
      }

      :where(.grid-spacing__example) {
        padding: 0.7rem;
        border: 1px solid light-dark(#d4d0c5, #56534c);
        border-radius: 0.5rem;
        font-size: 0.7rem;
      }

      :where(.grid-spacing__example strong) {
        display: block;
        margin-block-end: 0.45rem;
      }

      :where(.grid-spacing__example span) {
        min-block-size: 1.8rem;
        border-radius: 0.25rem;
        background: light-dark(#d1e3dd, #285044);
      }

      :where(.grid-spacing__gutter) {
        margin-block-start: 1rem;
        padding-block: 0.65rem;
        border-block: 1px dashed light-dark(#8d7662, #b9a28d);
        background: light-dark(#f9f3ea, #30271f);
        font-size: 0.74rem;
      }
    """


preview = GridSpacing()

preview  # noqa: B018
````


## Choose semantics and nest layouts

Select native elements that match the content. Grid can render `ul`/`ol`, and
GridItem can render `li`; Citry does not fabricate list or landmark semantics.
Nested grids keep their own breakpoint values.


### Build a semantic nested specimen catalog

[Open the rendered preview](/v/0.4.6/ui-library/components/container-grid/_previews/semantics-and-nesting/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GridSemanticsAndNesting(Component):
    template = """
      <c-CContainer
        tag="section"
        class_="mineral-catalog"
        size="md"
        c-attrs="{'aria-labelledby': 'mineral-catalog-title'}"
      >
        <h2 id="mineral-catalog-title">Mineral families</h2>
        <c-CGrid tag="ul" sm="2" class_="mineral-catalog__list">
          <c-CGridItem tag="li">
            <strong>Silicates</strong>
            <c-CGrid cols="2" gap="xs" class_="mineral-catalog__nested">
              <span>Quartz</span><span>Feldspar</span>
            </c-CGrid>
          </c-CGridItem>
          <c-CGridItem tag="li">
            <strong>Carbonates</strong>
            <c-CGrid cols="2" gap="xs" class_="mineral-catalog__nested">
              <span>Calcite</span><span>Dolomite</span>
            </c-CGrid>
          </c-CGridItem>
        </c-CGrid>
      </c-CContainer>
    """

    css = """
      :where(.mineral-catalog) {
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.mineral-catalog h2) {
        margin: 0 0 0.75rem;
        font-size: 0.95rem;
      }

      :where(.mineral-catalog__list) {
        margin: 0;
        padding: 0;
        list-style: none;
      }

      :where(.mineral-catalog__list > li) {
        padding: 0.85rem;
        border: 1px solid light-dark(#d7cfbe, #5e574c);
        border-radius: 0.55rem;
        background: light-dark(#fffaf0, #29251f);
        font-size: 0.78rem;
      }

      :where(.mineral-catalog__nested) {
        margin-block-start: 0.6rem;
      }

      :where(.mineral-catalog__nested span) {
        padding: 0.35rem;
        border-radius: 0.25rem;
        background: light-dark(#e5eee9, #263a32);
        text-align: center;
      }
    """


preview = GridSemanticsAndNesting()

preview  # noqa: B018
````


## Customize the layout

Use public variables for local changes and stable part selectors or `class_`
for bespoke responsive rules. Tailwind and similar utility frameworks can
style these native roots through `class_`; Citry UI does not duplicate their
utility vocabulary.


### Customize Grid variables and a container query

[Open the rendered preview](/v/0.4.6/ui-library/components/container-grid/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GridCustomization(Component):
    template = """
      <section class="grid-custom" aria-labelledby="grid-custom-title">
        <h2 id="grid-custom-title">Custom field trays</h2>
        <div class="grid-custom__brand">
          <c-CGrid class_="grid-custom__variable-grid">
            <span>Granite</span><span>Gabbro</span><span>Rhyolite</span>
          </c-CGrid>
        </div>
        <div class="grid-custom__query-box">
          <c-CGrid class_="grid-custom__query-grid">
            <span>Slate</span><span>Schist</span><span>Gneiss</span>
          </c-CGrid>
        </div>
        <div dir="rtl" class="grid-custom__rtl">
          <c-CContainer gutter="xl">
            Logical gutters follow the reading direction without a separate RTL input.
          </c-CContainer>
        </div>
      </section>
    """

    css = """
      :where(.grid-custom) {
        max-inline-size: 48rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.grid-custom h2) {
        margin: 0 0 0.75rem;
        font-size: 0.95rem;
      }

      :where(.grid-custom__brand) {
        --cui-grid-columns: 3;
        --cui-grid-gap: 0.35rem;
        padding: 0.75rem;
        border-radius: 0.55rem;
        background: light-dark(#e9f0f7, #1d2e3e);
      }

      :where(.grid-custom__brand [data-citry-ui-part="grid"] > span) {
        padding: 0.55rem;
        border-radius: 0.3rem;
        background: light-dark(#ffffff, #2c4357);
        font-size: 0.74rem;
        text-align: center;
      }

      :where(.grid-custom__query-box) {
        container-type: inline-size;
        margin-block-start: 0.75rem;
        padding: 0.75rem;
        border: 1px solid light-dark(#b9af9d, #6c6254);
        border-radius: 0.55rem;
      }

      :where(.grid-custom__query-grid > span) {
        padding: 0.5rem;
        background: light-dark(#f4eadb, #3a2d22);
        font-size: 0.74rem;
        text-align: center;
      }

      @container (min-width: 28rem) {
        :where(.grid-custom__query-grid) {
          --cui-grid-columns: 3;
        }
      }

      :where(.grid-custom__rtl) {
        margin-block-start: 0.75rem;
        border-inline-start: 0.25rem solid #7f5baa;
        background: light-dark(#f6efff, #332541);
        font-size: 0.74rem;
      }
    """


preview = GridCustomization()

preview  # noqa: B018
````


The built-in `sm`, `md`, `lg`, `xl`, and `xxl` thresholds are viewport-based
and fixed. A custom class can use any media or container query without adding
another component input.

The family reserves its part/configuration attributes, Citry runtime fields,
whole-object spreads, and structural Alpine directives. Ordinary native,
ARIA, data, listener, and targeted unrelated binding attributes remain
available through `attrs`.

## API reference

### Inputs

#### CContainer server inputs

Server inputs are passed in a template through `<c-CContainer ... />` or in Python through
`CContainer(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="grid-container-input-ccontainer-server-inputs-tag"></span>`tag` | `"div" | "main" | "section" | "article" | "nav" | "aside"` ([`CContainerTag`](#grid-container-interface-input-type-aliases-container-tag)) | `"div"` | Selects the native root without adding a role or accessible name. |
| <span id="grid-container-input-ccontainer-server-inputs-size"></span>`size` | `"sm" | "md" | "lg" | "xl" | "xxl"` ([`CContainerSize`](#grid-container-interface-input-type-aliases-container-size)) | `"xl"` | Selects the centered maximum inline size from `40rem` through `96rem`. |
| <span id="grid-container-input-ccontainer-server-inputs-fluid"></span>`fluid` | `bool` | `False` | Removes the maximum width while retaining the selected inline gutter. |
| <span id="grid-container-input-ccontainer-server-inputs-gutter"></span>`gutter` | `"0" | "xs" | "sm" | "md" | "lg" | "xl"` ([`CLayoutGap`](#grid-container-interface-input-type-aliases-layout-gap)) | `"lg"` | Selects logical inline padding from `0` through `1.5rem`. |
| <span id="grid-container-input-ccontainer-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#grid-container-interface-input-type-aliases-class-value)) | `None` | Adds root classes and merges them with `attrs`. |
| <span id="grid-container-input-ccontainer-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#grid-container-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles and merges them with `attrs`. |
| <span id="grid-container-input-ccontainer-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds native, ARIA, data, and trusted targeted Alpine attributes without replacing owned layout or Citry runtime fields. |

</div>

#### CGrid server inputs

Server inputs are passed in a template through `<c-CGrid ... />` or in Python through
`CGrid(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="grid-container-input-cgrid-server-inputs-tag"></span>`tag` | `"div" | "main" | "section" | "article" | "ul" | "ol"` ([`CGridTag`](#grid-container-interface-input-type-aliases-grid-tag)) | `"div"` | Selects the native Grid root without adding semantics. |
| <span id="grid-container-input-cgrid-server-inputs-cols"></span>`cols` | `int` | `1` | Sets the equal base column count from 1 through 12. |
| <span id="grid-container-input-cgrid-server-inputs-sm"></span>`sm` | `int | None` | `None` | Overrides equal columns at `40rem` and wider. |
| <span id="grid-container-input-cgrid-server-inputs-md"></span>`md` | `int | None` | `None` | Overrides equal columns at `48rem` and wider. |
| <span id="grid-container-input-cgrid-server-inputs-lg"></span>`lg` | `int | None` | `None` | Overrides equal columns at `64rem` and wider. |
| <span id="grid-container-input-cgrid-server-inputs-xl"></span>`xl` | `int | None` | `None` | Overrides equal columns at `80rem` and wider. |
| <span id="grid-container-input-cgrid-server-inputs-xxl"></span>`xxl` | `int | None` | `None` | Overrides equal columns at `96rem` and wider. |
| <span id="grid-container-input-cgrid-server-inputs-min-col"></span>`min_col` | `str | None` | `None` | Uses intrinsic auto-fit columns with one positive `px`, `rem`, `em`, `ch`, viewport-width, or viewport-height length; cannot be combined with fixed/responsive counts. |
| <span id="grid-container-input-cgrid-server-inputs-gap"></span>`gap` | `"0" | "xs" | "sm" | "md" | "lg" | "xl"` ([`CLayoutGap`](#grid-container-interface-input-type-aliases-layout-gap)) | `"md"` | Selects row and column gap from `0` through `1.5rem`. |
| <span id="grid-container-input-cgrid-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#grid-container-interface-input-type-aliases-class-value)) | `None` | Adds root classes and merges them with `attrs`. |
| <span id="grid-container-input-cgrid-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#grid-container-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles and merges them with `attrs`. |
| <span id="grid-container-input-cgrid-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds native, ARIA, data, and trusted targeted Alpine attributes without replacing owned layout or Citry runtime fields. |

</div>

#### CGridItem server inputs

Server inputs are passed in a template through `<c-CGridItem ... />` or in Python through
`CGridItem(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 15rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="grid-container-input-cgriditem-server-inputs-tag"></span>`tag` | `"div" | "main" | "section" | "article" | "aside" | "li"` ([`CGridItemTag`](#grid-container-interface-input-type-aliases-grid-item-tag)) | `"div"` | Selects the native Grid item root without adding semantics. |
| <span id="grid-container-input-cgriditem-server-inputs-span"></span>`span` | `int` | `1` | Sets the base column span from 1 through 12. |
| <span id="grid-container-input-cgriditem-server-inputs-sm"></span>`sm` | `int | None` | `None` | Overrides the span at `40rem` and wider. |
| <span id="grid-container-input-cgriditem-server-inputs-md"></span>`md` | `int | None` | `None` | Overrides the span at `48rem` and wider. |
| <span id="grid-container-input-cgriditem-server-inputs-lg"></span>`lg` | `int | None` | `None` | Overrides the span at `64rem` and wider. |
| <span id="grid-container-input-cgriditem-server-inputs-xl"></span>`xl` | `int | None` | `None` | Overrides the span at `80rem` and wider. |
| <span id="grid-container-input-cgriditem-server-inputs-xxl"></span>`xxl` | `int | None` | `None` | Overrides the span at `96rem` and wider. |
| <span id="grid-container-input-cgriditem-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#grid-container-interface-input-type-aliases-class-value)) | `None` | Adds root classes and merges them with `attrs`. |
| <span id="grid-container-input-cgriditem-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#grid-container-interface-input-type-aliases-style-value)) | `None` | Adds root inline styles and merges them with `attrs`. |
| <span id="grid-container-input-cgriditem-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds native, ARIA, data, and trusted targeted Alpine attributes without replacing owned layout or Citry runtime fields. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CContainer slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="grid-container-slot-ccontainer-slots-default"></span>`default` | no | `{}` ([`CContainerDefaultSlotData`](#grid-container-interface-ccontainer-default-slot-data)) | Renders an empty Container root. |

</div>

#### CGrid slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="grid-container-slot-cgrid-slots-default"></span>`default` | no | `{}` ([`CGridDefaultSlotData`](#grid-container-interface-cgrid-default-slot-data)) | Renders an empty Grid root. |

</div>

#### CGridItem slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="grid-container-slot-cgriditem-slots-default"></span>`default` | no | `{}` ([`CGridItemDefaultSlotData`](#grid-container-interface-cgriditem-default-slot-data)) | Renders an empty Grid item root. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CContainer CSS variables

Apply these variables to `CContainer` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="grid-container-css-ccontainer-css-variables-cui-container-max-width"></span>`--cui-container-max-width` | `length` | Overrides the selected centered maximum inline size. | ``Selected size from `40rem` through `96rem`.`` |
| <span id="grid-container-css-ccontainer-css-variables-cui-container-gutter"></span>`--cui-container-gutter` | `length` | Overrides logical inline padding. | `Selected gutter-preset length.` |

</div>

#### CGrid CSS variables

Apply these variables to `CGrid` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="grid-container-css-cgrid-css-variables-cui-grid-columns"></span>`--cui-grid-columns` | `integer` | Overrides the effective equal column count at every breakpoint. | ``Effective responsive `cols` value.`` |
| <span id="grid-container-css-cgrid-css-variables-cui-grid-gap"></span>`--cui-grid-gap` | `length` | Overrides row and column gap. | `Selected gap-preset length.` |
| <span id="grid-container-css-cgrid-css-variables-cui-grid-min-column"></span>`--cui-grid-min-column` | `length` | Overrides the requested intrinsic minimum column size. | `` `min_col` value. `` |

</div>

#### CGridItem CSS variables

Apply these variables to `CGridItem` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="grid-container-css-cgriditem-css-variables-cui-grid-item-span"></span>`--cui-grid-item-span` | `integer` | Overrides the effective span at every breakpoint. | ``Effective responsive `span` value.`` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CContainer attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="grid-container-attribute-ccontainer-attributes-data-size"></span>`data-size` | Root | `"sm" | "md" | "lg" | "xl" | "xxl"` | Reflects the selected maximum-width preset. |
| <span id="grid-container-attribute-ccontainer-attributes-data-fluid"></span>`data-fluid` | Root | `Boolean presence` | Present while the maximum width is removed. |
| <span id="grid-container-attribute-ccontainer-attributes-data-gutter"></span>`data-gutter` | Root | `"0" | "xs" | "sm" | "md" | "lg" | "xl"` | Reflects the selected inline-gutter preset. |

</div>

#### CGrid attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="grid-container-attribute-cgrid-attributes-data-cols"></span>`data-cols` | Root | `Integer 1–12` | Reflects the base equal column count. |
| <span id="grid-container-attribute-cgrid-attributes-data-cols-sm"></span>`data-cols-sm` | Root | `Integer 1–12 when supplied` | Reflects the authored `sm` column override. |
| <span id="grid-container-attribute-cgrid-attributes-data-cols-md"></span>`data-cols-md` | Root | `Integer 1–12 when supplied` | Reflects the authored `md` column override. |
| <span id="grid-container-attribute-cgrid-attributes-data-cols-lg"></span>`data-cols-lg` | Root | `Integer 1–12 when supplied` | Reflects the authored `lg` column override. |
| <span id="grid-container-attribute-cgrid-attributes-data-cols-xl"></span>`data-cols-xl` | Root | `Integer 1–12 when supplied` | Reflects the authored `xl` column override. |
| <span id="grid-container-attribute-cgrid-attributes-data-cols-xxl"></span>`data-cols-xxl` | Root | `Integer 1–12 when supplied` | Reflects the authored `xxl` column override. |
| <span id="grid-container-attribute-cgrid-attributes-data-intrinsic"></span>`data-intrinsic` | Root | `Boolean presence` | Present in intrinsic auto-fit mode. |
| <span id="grid-container-attribute-cgrid-attributes-data-gap"></span>`data-gap` | Root | `"0" | "xs" | "sm" | "md" | "lg" | "xl"` | Reflects the selected gap preset. |

</div>

#### CGridItem attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="grid-container-attribute-cgriditem-attributes-data-span"></span>`data-span` | Root | `Integer 1–12` | Reflects the base column span. |
| <span id="grid-container-attribute-cgriditem-attributes-data-span-sm"></span>`data-span-sm` | Root | `Integer 1–12 when supplied` | Reflects the authored `sm` span override. |
| <span id="grid-container-attribute-cgriditem-attributes-data-span-md"></span>`data-span-md` | Root | `Integer 1–12 when supplied` | Reflects the authored `md` span override. |
| <span id="grid-container-attribute-cgriditem-attributes-data-span-lg"></span>`data-span-lg` | Root | `Integer 1–12 when supplied` | Reflects the authored `lg` span override. |
| <span id="grid-container-attribute-cgriditem-attributes-data-span-xl"></span>`data-span-xl` | Root | `Integer 1–12 when supplied` | Reflects the authored `xl` span override. |
| <span id="grid-container-attribute-cgriditem-attributes-data-span-xxl"></span>`data-span-xxl` | Root | `Integer 1–12 when supplied` | Reflects the authored `xxl` span override. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CContainer selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="grid-container-selector-ccontainer-selectors-data-citry-ui-part-container"></span>`[data-citry-ui-part="container"]` | Native root | Stable Container root and `attrs` destination. |

</div>

#### CGrid selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="grid-container-selector-cgrid-selectors-data-citry-ui-part-grid"></span>`[data-citry-ui-part="grid"]` | Native root | Stable Grid root and `attrs` destination. |

</div>

#### CGridItem selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="grid-container-selector-cgriditem-selectors-data-citry-ui-part-grid-item"></span>`[data-citry-ui-part="grid-item"]` | Native root | Stable GridItem root and `attrs` destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="grid-container-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="grid-container-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="grid-container-interface-input-type-aliases-container-tag"></span>`CContainerTag` | `Literal["div", "main", "section", "article", "nav", "aside"]` |
| <span id="grid-container-interface-input-type-aliases-grid-tag"></span>`CGridTag` | `Literal["div", "main", "section", "article", "ul", "ol"]` |
| <span id="grid-container-interface-input-type-aliases-grid-item-tag"></span>`CGridItemTag` | `Literal["div", "main", "section", "article", "aside", "li"]` |
| <span id="grid-container-interface-input-type-aliases-container-size"></span>`CContainerSize` | `Literal["sm", "md", "lg", "xl", "xxl"]` |
| <span id="grid-container-interface-input-type-aliases-layout-gap"></span>`CLayoutGap` | `Literal["0", "xs", "sm", "md", "lg", "xl"]` |

</div>

<span id="grid-container-interface-ccontainer-default-slot-data"></span>

#### `CContainerDefaultSlotData`

Empty dataclass: `{}`.

<span id="grid-container-interface-cgrid-default-slot-data"></span>

#### `CGridDefaultSlotData`

Empty dataclass: `{}`.

<span id="grid-container-interface-cgriditem-default-slot-data"></span>

#### `CGridItemDefaultSlotData`

Empty dataclass: `{}`.

### Translation keys

-