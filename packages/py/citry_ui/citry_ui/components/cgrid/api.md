---
title: Container and Grid
description: Constrain page content, build responsive equal grids, and add asymmetric spans when needed.
---

# Container and Grid

`CContainer` constrains page width. `CGrid` handles the common equal-column
layout. Add `CGridItem` only when individual content needs an asymmetric span.
All three render with native CSS and no JavaScript.

## Layout at a glance

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cgrid/snippets/at_a_glance.py"
  title="Browse a responsive mineral atlas"
/>

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

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cgrid/snippets/responsive_columns.py"
  title="Compare fixed and responsive columns"
/>

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

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cgrid/snippets/asymmetric_layout.py"
  title="Compose field notes and a specimen index"
/>

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

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cgrid/snippets/intrinsic_grid.py"
  title="Fit mineral cards by minimum width"
/>

Intrinsic mode owns track sizing, so it cannot be combined with `cols` or
breakpoint counts. For CSS functions such as `clamp()`, set
`--cui-grid-min-column` instead.

## Constrain page content

Container defaults to a centered `80rem` maximum with `1rem` inline gutters.
Choose a smaller/larger size, or use `fluid` to retain gutters without a
maximum width.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cgrid/snippets/container_sizes.py"
  title="Compare Container sizes and fluid width"
/>

Container does not establish a CSS query container. Add `container-type` in
consumer CSS only where that behavior is needed.

## Adjust spacing

Grid `gap` controls both axes. Container `gutter` controls logical inline
padding. Both use `0`, `xs`, `sm`, `md`, `lg`, and `xl`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cgrid/snippets/spacing.py"
  title="Compare Grid gaps and Container gutters"
/>

## Choose semantics and nest layouts

Select native elements that match the content. Grid can render `ul`/`ol`, and
GridItem can render `li`; Citry does not fabricate list or landmark semantics.
Nested grids keep their own breakpoint values.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cgrid/snippets/semantics_and_nesting.py"
  title="Build a semantic nested specimen catalog"
/>

## Customize the layout

Use public variables for local changes and stable part selectors or `class_`
for bespoke responsive rules. Tailwind and similar utility frameworks can
style these native roots through `class_`; Citry UI does not duplicate their
utility vocabulary.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cgrid/snippets/customization.py"
  title="Customize Grid variables and a container query"
/>

The built-in `sm`, `md`, `lg`, `xl`, and `xxl` thresholds are viewport-based
and fixed. A custom class can use any media or container query without adding
another component input.

The family reserves its part/configuration attributes, Citry runtime fields,
whole-object spreads, and structural Alpine directives. Ordinary native,
ARIA, data, listener, and targeted unrelated binding attributes remain
available through `attrs`.
