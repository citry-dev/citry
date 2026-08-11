---
title: Progress
description: Communicate determinate and indeterminate task progress with a native Citry UI progress element.
---

# Progress

Use `CProgress` for completion of an ongoing task. It renders the native
`progress` element, so determinate values, unknown duration, direction, and
assistive-technology semantics stay browser-owned.

## Progress at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cprogress/snippets/at_a_glance.py" title="Progress at a glance" />

## Show known completion

Pass a finite `value` from zero through `max`. The default maximum is 100.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cprogress/snippets/determinate.py" title="Compare determinate values" />

```citry-html
<c-CProgress label="Mapping the reef shelf" c-value="68" />
```

## Show unknown duration

Omit `value`, or pass `None`, while work is active but its remaining duration
is unknown. This removes the native value attribute.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cprogress/snippets/indeterminate.py" title="Show indeterminate work" />

Reduced-motion preferences replace continuous motion with a static patterned
track.

## Use custom units

Set a positive `max` and supply `value_text` when the value is better explained
as items, bytes, stages, or another unit.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cprogress/snippets/custom_range.py" title="Use a custom range and value text" />

## Choose a palette

Intent changes the range color. Keep the task label and surrounding text clear
without color.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cprogress/snippets/intents.py" title="Compare Progress intents" />

## Choose thickness and shape

Sizes set track thickness. Shape selects square, rounded, or pill geometry.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cprogress/snippets/sizes_and_shapes.py" title="Compare Progress sizes and shapes" />

## Control progress in the browser

Client inputs are passed through `$c-props="{...}"`. A number controls
determinate completion; `null` switches to indeterminate; omission returns to
the server fallback.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cprogress/snippets/controlled.py" title="Control Progress in the browser" />

## Describe a busy region

When Progress describes another region, the application owns `aria-busy` on
that region and connects it to Progress. Clear busy state when the work
finishes.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cprogress/snippets/busy_region.py" title="Connect Progress to a busy region" />

## Customize Progress

Override public track, range, height, and radius variables on an ancestor or
one native Progress root.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cprogress/snippets/customization.py" title="Customize Progress with public CSS" />

## Choose the right indicator

Progress represents task completion. Use `CSpinner` for a compact unknown wait
without a linear track, and native `meter` for a scalar measurement that is not
task completion.

Progress has no focus, keyboard behavior, form value, live announcement, or
automatic busy-region mutation.
