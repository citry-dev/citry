---
title: Badge
description: Present compact status, category, count, and metadata labels with Citry UI.
---

# Badge

Use `CBadge` for short inline status, category, count, or metadata text. Badge
is a visual label, not a Button, selectable Chip, removable Tag, or live
announcement region.

## Badge at a glance

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbadge/snippets/at_a_glance.py"
  title="Badge at a glance"
/>

## Compose a Badge

The default slot supplies the visible meaning. It is required.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbadge/snippets/basic_badges.py"
  title="Compose short inline labels"
/>

```citry-html
<c-CBadge intent="success">Verified</c-CBadge>
```

Compose the same result in Python:

```python
from citry_ui import CBadge

verified = CBadge(intent="success", slots={"default": "Verified"})
```

## Carry meaning with text

Intent selects a palette. The visible label must still explain the state, so
the result remains understandable without color.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbadge/snippets/intents.py"
  title="Compare Badge intents"
/>

## Choose visual emphasis

Use `soft` for quiet metadata, `solid` for stronger emphasis, and `outline`
when the surrounding surface should remain visible.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbadge/snippets/variants.py"
  title="Compare Badge variants"
/>

## Choose size and shape

Sizes change compact type and spacing. Shape changes only the corner radius.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbadge/snippets/sizes_and_shapes.py"
  title="Compare sizes and shapes"
/>

## Add registered icons

Use the `start` and `end` slots for short decorative content. Keep the default
label meaningful without the icon.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbadge/snippets/icons.py"
  title="Add registered icons"
/>

## Give counts context

A lone number is ambiguous. Put counts beside understandable owner text and
include the count's meaning in the owner accessible name when needed.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbadge/snippets/counts_and_context.py"
  title="Present counts in context"
/>

Badge does not cap large values or hide zero. Format the slot content in your
application so display and accessible context stay under one policy.

## Position a Badge around an owner

Badge owns no positioning or overlap. Use ordinary CSS when a count belongs at
the corner of a Button, Avatar, or other item.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbadge/snippets/positioning.py"
  title="Position a Badge with consumer CSS"
/>

## Customize Badge

Override public variables on an ancestor or one Badge. Stable part selectors
support local geometry without relying on private classes.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cbadge/snippets/customization.py"
  title="Customize Badge with public CSS"
/>

## Accessibility and behavior

Badge renders a neutral, unfocusable `span` with no JavaScript. Do not place
Buttons, links, inputs, or other controls inside it. Put Badge inside the
interactive owner instead.

Changing Badge text does not create a live announcement. Use a persistent
status or Alert surface when a browser update must be announced.
