---
title: Sortable
description: Reorder server-rendered items with pointer, touch, or keyboard while preserving native form order.
---

# Sortable

Use `CSortable` for a finite collection whose order matters. Each
`CSortableItem` supplies stable identity, a plain accessible label, and visible
content. The initial server order remains useful before JavaScript starts.

## Reorder a list

Drag an Item by its handle. Keyboard users focus the same handle, press Space
or Enter to pick it up, use arrow keys, Home, or End to move it, then press
Space or Enter to drop. Escape cancels.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csortable/snippets/at_a_glance.py" title="Prioritize release work" />

Values must be unique. `order` can provide a full initial permutation;
otherwise declaration order wins. Disabled Items remain in order but cannot
be moved.

## Render rich items and custom handles

The default slot receives `value`, `label`, `disabled`, and zero-based `index`.
The optional `handle` slot changes only the button contents. Citry UI keeps the
native button, accessible name, focus behavior, and moving semantics.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csortable/snippets/rich_items.py" title="Reorder rich task cards" />

Interactive controls may live in Item content because dragging begins only on
the handle. Avoid making the handle slot itself interactive.

## Control order from Alpine

Pass `order` and `onOrderChange` through `$c-props`. Controlled moves are
requests: the component restores the accepted order until the owner supplies
the requested permutation.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csortable/snippets/controlled.py" title="Accept controlled reorder requests" />

Omit client `order`, or set it to `null`, for uncontrolled behavior. An
accepted move emits native `input` then `change` from the root and calls
`onOrderChange`.

## Arrange a sortable grid

Set `layout="grid"` for cards or `layout="horizontal"` for a single row. The
keyboard uses visual inline direction in horizontal and grid layouts, including
RTL. Pointer collision uses the nearest Item center.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csortable/snippets/grid.py" title="Reorder a responsive grid" />

Use `--cui-sortable-columns` to tune the responsive grid. Do not combine this
family with a partial virtual window because a partial DOM cannot expose the
complete accepted order.

## Submit the accepted order

Set `name` to submit one successful form entry per Item in accepted order.
`form` can refer to an external Form ID. A disabled root submits no entries,
and native reset restores the server order or requests it in controlled mode.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csortable/snippets/forms.py" title="Submit ordered priorities" />

Application code still owns persistence. The component never sends a request
or stores order outside the current page.

## Accessibility and localization

The handle has a localized name containing the Item's plain `label`. A polite
live region announces pickup, movement, drop, and cancellation with position
and total. Explicit `*_label` inputs belong to the caller and remain fixed;
catalog defaults switch with the active Citry client locale.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/csortable/snippets/accessibility.py" title="Keep fixed and disabled Items understandable" />

Pointer dragging has a touch delay so ordinary scrolling remains available.
Reduced-motion and forced-color preferences retain the complete interaction.
Multi-container transfer and moving tree nodes between parents are outside the
first family.

<!-- UI_LIBRARY_API_REFERENCE -->
