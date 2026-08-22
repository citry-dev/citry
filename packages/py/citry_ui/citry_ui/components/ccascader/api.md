---
title: Cascader
description: Select one path through a finite server-rendered hierarchy.
---

# Cascader

Use `CCascader` when a value is meaningful only as a path through related
levels. Each `CCascaderOption` declares a globally unique value and plain label;
nested Options create the next column.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccascader/snippets/at_a_glance.py" title="Choose a geographic path" />

## Submit the complete path

Set `name` to produce one hidden input per accepted segment, in root-to-leaf
order. `form` supports an external native form. Without JavaScript, the initial
path remains visible and submits normally.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccascader/snippets/forms.py" title="Submit category segments" />

## Control selection

Pass `value` and `onValueChange` through `$c-props` for controlled state. The
callback receives the path plus labels, previous path, selected Option element,
controlled flag, interaction source, and native event.
Invalid controlled `value` or `open` values are diagnosed once and retain the
last valid effective state. Omitting `value` returns to the retained uncontrolled
path; omitting `open` releases control without changing the current open state.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccascader/snippets/controlled.py" title="Own the accepted location" />

## Allow parent paths

The default requires a leaf. Set `change_on_select=True` when a category at any
depth is a complete result. Activating a collapsed branch selects it and opens
its children. Activating the expanded branch again collapses its child level.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccascader/snippets/parent_selection.py" title="Select any category depth" />

## Disable unavailable paths

A disabled Option cannot be opened or selected, and an initial value cannot
pass through it. Root `disabled` also disables form inputs.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccascader/snippets/disabled.py" title="Keep unavailable regions visible" />

## Support keyboard and constrained layouts

Arrow keys move within and across columns; Home, End, typeahead, Enter, Space,
Escape, and Tab follow the popup tree contract. Pointer activation, Enter, and
Space toggle a branch's child level without changing an already accepted leaf.
Use `aria_label` or `aria_labelledby` to give the trigger an application-specific
accessible name. Active columns sit side by side whenever their preferred width
fits the viewport. Only when they do not fit do they stack vertically at the
trigger width, avoiding page-level and nested horizontal scrollbars. While open,
the popup also shifts back inside the viewport when its trigger sits near an
inline edge. RTL reverses both column progression and branch indicators. The
labeled taxonomy deliberately uses wider columns to demonstrate the stacked
form in its constrained preview.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccascader/snippets/accessibility.py" title="Navigate a labeled taxonomy" />

Search, multiple paths, async child loading, and virtualized levels are not
silent modes of this API; they remain separate future contracts.

<!-- UI_LIBRARY_API_REFERENCE -->
