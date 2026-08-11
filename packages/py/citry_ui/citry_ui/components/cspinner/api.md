---
title: Spinner
description: Show compact unknown-duration activity with a labelled Citry UI Spinner.
---

# Spinner

Use `CSpinner` for compact activity whose duration is unknown. It renders one
indeterminate `progressbar`, works before JavaScript loads, and always requires
an accessible task label.

## Spinner at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cspinner/snippets/at_a_glance.py" title="Spinner at a glance" />

## Show active work

Pass a concise label that identifies the active task. Spinner does not display
the label, so pair it with visible text when users need the same context.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cspinner/snippets/basic.py" title="Show basic Spinners" />

```citry-html
<c-CSpinner label="Loading star catalog" />
```

## Choose a palette

Intent changes the ring color. Keep status meaning in surrounding text rather
than color alone.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cspinner/snippets/intents.py" title="Compare Spinner intents" />

## Choose a size

Use `sm`, `md`, or `lg`. Public CSS variables can set a one-off diameter or
thickness.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cspinner/snippets/sizes.py" title="Compare Spinner sizes" />

## Pair Spinner with text

Spinner is inline-sized and works beside concise status text. It never adds a
focus stop or changes surrounding controls.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cspinner/snippets/inline.py" title="Compose inline activity" />

## Control presentation in the browser

Client inputs are passed through `$c-props="{...}"`. They can update `label`,
`intent`, and `size`; omission returns to the server fallback.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cspinner/snippets/controlled.py" title="Control Spinner in the browser" />

## Describe a busy region

The region owner sets `aria-busy`, controls Spinner presence, and clears busy
state when work completes. Spinner does not mutate another element.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cspinner/snippets/busy_region.py" title="Connect Spinner to a busy region" />

## Avoid flashes for brief work

Delay Spinner in application state when a task normally finishes immediately.
The application also owns any minimum-visible duration.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cspinner/snippets/delayed.py" title="Delay brief activity feedback" />

## Customize Spinner

Override public color, track, diameter, thickness, and duration variables on an
ancestor or one Spinner root.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cspinner/snippets/customization.py" title="Customize Spinner with public CSS" />

## Choose the right indicator

Use `CProgress` when completion has a meaningful linear track or known value.
Use `CButton(loading=True)` for a Button-owned pending action. Spinner does not
own overlays, live announcements, task timing, or determinate values.
