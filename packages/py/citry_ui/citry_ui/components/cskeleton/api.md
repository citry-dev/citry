---
title: Skeleton
description: Compose precise loading placeholders from visible primitives.
---

# Skeleton

Use `CSkeleton` to hold a known layout while its data loads. Compose explicit
primitives instead of encoding a page shape in a preset string.

## Skeleton at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cskeleton/snippets/at_a_glance.py" title="Skeleton at a glance" />

## Choose a primitive

Rectangles hold media and panels, circles hold avatars and icons, and text
lines track typography.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cskeleton/snippets/primitives.py" title="Compare Skeleton primitives" />

## Shape text

`lines` produces compact paragraph geometry. Set the final line width to make
the placeholder resemble real prose.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cskeleton/snippets/text_lines.py" title="Compose text lines" />

## Compose real layouts

Build familiar patterns with `CCol`, `CRow`, and ordinary CSS. The visible
structure stays inspectable and responsive.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cskeleton/snippets/field_note_card.py" title="Compose a field-note card" />

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cskeleton/snippets/specimen_list.py" title="Compose a specimen list" />

## Choose motion

Pulse is the default. Wave provides stronger progress motion, while none makes
a static wireframe. Reduced-motion preferences disable both animations.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cskeleton/snippets/motion.py" title="Compare motion treatments" />

## Customize Skeleton

Public variables control dimensions, color, radius, spacing, and timing.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cskeleton/snippets/customization.py" title="Customize Skeleton with public CSS" />

## Accessibility and loading ownership

Skeletons are decorative and hidden from assistive technology. Put
`aria-busy="true"` and a useful accessible name on the region whose content is
loading. That region, not Skeleton, owns async state and announcements.
