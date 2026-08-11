---
title: Splitter
description: Resize two or more adjacent application panels.
---

# Splitter

Use `CSplitter` when adjacent regions need user-adjustable space. Every
`CSplitterPanel` has stable identity, an accessible name, and percentage
constraints. Persist accepted sizes in application state through
`onResizeEnd` when a layout should survive navigation.

## Splitter at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitter/snippets/at_a_glance.py" title="Splitter at a glance" />

## Resize multiple panels

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitter/snippets/multiple.py" title="Resize three panels" />

## Stack and nest Splitters

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitter/snippets/vertical_nested.py" title="Stack and nest Splitters" />

## Constrain keyboard resizing

Arrow keys move by `keyboard_step` percentage points, Shift uses four times
the step, and Home or End reaches the adjacent pair constraint.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitter/snippets/constraints_keyboard.py" title="Constrain panel sizes" />

## Control and persist sizes

Client `sizes` is controlled while supplied. The owner accepts resize
requests by updating the vector and can persist the final vector from
`onResizeEnd`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitter/snippets/controlled.py" title="Control Splitter sizes" />

## Disable resizing

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitter/snippets/disabled.py" title="Disable Splitter" />

## Customize Splitter

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csplitter/snippets/customization.py" title="Customize Splitter" />

## Accessibility and behavior

Each resize handle is a focusable ARIA separator with its current percentage,
allowed range, physical orientation, and the IDs of its adjacent panels.
Side-by-side layouts use Left and Right; stacked layouts use Up and Down.
Pointer and keyboard interaction change only the adjacent pair, preserving its
combined size. Controls inside panels retain their ordinary form behavior.

<!-- UI_LIBRARY_API_REFERENCE -->
