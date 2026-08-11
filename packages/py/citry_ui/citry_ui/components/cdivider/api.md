---
title: Divider
description: Separate sections semantically or visually with Citry UI.
---

# Divider

Use `CDivider` for a thematic break between sections or a decorative line in
dense layouts. It adds no external spacing and no JavaScript.

## Divider at a glance

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdivider/snippets/at_a_glance.py"
  title="Divider at a glance"
/>

## Compose a Divider

An unlabelled horizontal Divider is a native thematic break.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdivider/snippets/basic_dividers.py"
  title="Compose semantic Dividers"
/>

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

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdivider/snippets/semantic_and_decorative.py"
  title="Compare semantic and decorative lines"
/>

## Choose orientation

Horizontal Dividers separate vertically stacked content. Vertical Dividers
separate items across a flex or grid row and stretch with their container.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdivider/snippets/orientations.py"
  title="Compare horizontal and vertical Dividers"
/>

## Add a visible label

The optional default slot places ordinary visible content between two
decorative lines. Use a real heading inside when the document needs heading
semantics. Labels are horizontal only.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdivider/snippets/labels.py"
  title="Position visible Divider labels"
/>

## Choose line style and thickness

Variants select solid, dashed, or dotted lines. Sizes provide concise 1, 2,
and 4 pixel thickness presets.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdivider/snippets/variants_and_sizes.py"
  title="Compare Divider variants and sizes"
/>

## Align with nested content

Insets add logical spacing along the line axis. They follow text direction,
so `start` and `end` remain meaningful in LTR and RTL layouts.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdivider/snippets/insets.py"
  title="Apply logical Divider insets"
/>

## Customize Divider

Override public variables on an ancestor or one Divider. Stable selectors let
you style the root, label, or labelled line segments without private classes.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdivider/snippets/customization.py"
  title="Customize Divider with public CSS"
/>

## Accessibility and behavior

The default horizontal form renders a native `hr`. The vertical form renders
a nonfocusable ARIA separator. Decorative output is hidden from assistive
technology. Labelled lines are decorative while the label remains ordinary
document content.

Divider never owns focus, keyboard input, resize behavior, or external margin.
Use layout gaps for spacing and a future Splitter component for adjustable
panes.
