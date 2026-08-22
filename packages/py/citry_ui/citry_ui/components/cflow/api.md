---
title: Col and Row
description: Arrange Citry UI content in predictable vertical columns and wrapping horizontal rows.
---

# Col and Row

Use `CCol` for vertical flow and `CRow` for horizontal flow. Both keep your
children unchanged, expose one native root, and render without JavaScript.

## Layout at a glance

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cflow/snippets/at_a_glance.py"
  title="Compose Col and Row"
/>

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

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cflow/snippets/col_spacing.py"
  title="Compare Col spacing"
/>

## Align and distribute children

`align` controls the cross axis. `justify` distributes children along the
flow axis. The same vocabulary works across both components.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cflow/snippets/row_alignment.py"
  title="Align and distribute Row children"
/>

## Wrap horizontal content

Row wraps by default, making action rows and short metadata collections safe
at narrow widths. Set `wrap=False` only when horizontal overflow is deliberate.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cflow/snippets/wrapping.py"
  title="Compare wrapping behavior"
/>

## Choose native semantics

The default `div` makes no semantic claim. Use `section` for a named section,
`nav` for navigation, or `ul`/`ol` when every direct child follows native list
content rules.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cflow/snippets/semantic_roots.py"
  title="Choose semantic roots"
/>

The components add no role, accessible name, heading, or list item. Supply the
native structure required by your content.

## Nest layouts

Col and Row can be nested without extra coordination or client state.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cflow/snippets/nested_layouts.py"
  title="Build a nested ceramics layout"
/>

## Customize layout

Override the public gap variables on an ancestor or one instance. Use stable
part selectors, `class_`, or `style` for responsive rules beyond the preset
API.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cflow/snippets/customization.py"
  title="Customize Flow with public CSS"
/>

## Direction, visual order, and accessibility

Logical alignment follows the document direction. `reverse=True` reverses only
the visual flex flow: DOM, reading, and keyboard order do not change. Use it
only when the original order remains understandable.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cflow/snippets/direction.py"
  title="Compare direction and visual order"
/>

Flow renders completely without JavaScript. Attribute maps accept native,
ARIA, data, and trusted targeted Alpine attributes, but reserve layout
reflections, part markers, structural directives, and Citry runtime ownership
fields.
