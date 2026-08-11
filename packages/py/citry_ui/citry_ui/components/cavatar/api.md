---
title: Avatar
description: Present image identities with explicit names and reliable fallbacks.
---

# Avatar

Use `CAvatar` for a compact image identity. Supply an explicit accessible name,
then choose an image, authored fallback, or built-in generic silhouette.

## Avatar at a glance

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cavatar/snippets/at_a_glance.py"
  title="Avatar at a glance"
/>

## Choose images and fallbacks

`src` shows one image. The default slot remains behind it and appears when the
source is absent or fails. Without a slot, Avatar uses a generic silhouette.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cavatar/snippets/images_and_fallbacks.py"
  title="Compare image and fallback paths"
/>

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

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cavatar/snippets/accessible_names.py"
  title="Compare named and decorative Avatars"
/>

## Choose appearance

Variants style the fallback. Sizes and shapes control the fixed visual frame.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cavatar/snippets/variants_and_sizes.py"
  title="Compare Avatar variants and sizes"
/>

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cavatar/snippets/shapes.py"
  title="Compare Avatar shapes"
/>

## Update the image in the browser

Client inputs are passed through `$c-props="{...}"`. `src` accepts a URL or
`null`; `onStatusChange` reports fallback, loading, loaded, and error states.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cavatar/snippets/reactive_sources.py"
  title="Change an Avatar source"
/>

## Compose adjacent UI

Avatar does not own presence, badges, or overlapping groups. Compose those jobs
with `CBadge`, `CGroup`, and application layout.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cavatar/snippets/composition.py"
  title="Compose Avatar with badges and groups"
/>

## Customize Avatar

Override public variables on a scope or instance. Stable selectors target the
root, fallback, and image without relying on private classes.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cavatar/snippets/customization.py"
  title="Customize Avatar with public CSS"
/>

## Accessibility and loading behavior

A nonempty `alt` makes the root one named image semantic. The internal HTML
image and fallback are decorative, avoiding duplicate announcements. Empty
`alt` makes the entire Avatar decorative.

Avatar owns no focus or keyboard behavior. Failed images are hidden after
client activation; the fallback remains mounted throughout loading.
