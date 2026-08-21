---
title: Data Grid
description: Navigate, sort, select, and server-window tabular application data with Citry UI.
---

# Data Grid

Use `CDataGrid` for application data that benefits from one composite Tab
stop, cell navigation, row selection, server-owned sorting, or fixed-height
server windowing. Use `CTable` instead for document-like tables, ordinary
links and controls in cells, spans, footers, and print-first reading.

## Build a complete grid

Columns and rows are immutable Python records. Every Row supplies exactly one
Cell value for every Column key, and every key is a stable nonempty string.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdata_grid/snippets/at_a_glance.py" title="Navigate a complete Data Grid" />

The server output is a native table with exact row and column positions. Once
enhanced, one Header or Cell is in the page Tab order. Arrow keys move between
rendered Cells; Home, End, Page Up, Page Down, Ctrl/Cmd+Home, and Ctrl/Cmd+End
provide larger movement.

## Request sorting and select rows

Set `sortable=True` on Columns that can be sorted. Header activation cycles
ascending, descending, then unsorted. The grid never reorders application
Rows itself: `onSortChange` receives a request, and accepted `sort` state must
come back from the owner. Shift preserves other Columns when `multi_sort=True`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdata_grid/snippets/sorting_selection.py" title="Sort and select people" />

`selection="single"` or `selection="multiple"` enables Row selection.
Uncontrolled selection commits immediately. A non-null client `selected`
array makes selection controlled, so the visible state waits for acceptance.

## Control models from Alpine

Pass `sort`, `selected`, and callbacks through `$c-props`. Invalid client
models are diagnosed and the last valid state remains active.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdata_grid/snippets/controlled.py" title="Control Data Grid models" />

Sort is always request/accept because only the application understands its
data. Selection becomes uncontrolled again when client `selected` is omitted
or null. Accepted sort and selection changes are announced politely.

## Supply a server window

Set `total_count` and `start_index` when `rows` is one contiguous window of a
larger collection. `row_height` is fixed geometry. `onRangeChange` receives a
half-open desired range when scrolling, resizing, or navigation leaves the
supplied range.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdata_grid/snippets/windowed.py" title="Request Data Grid windows" />

The component does not fetch. The owner handles supersession, retries,
offline state, and replacement. Keep Row keys stable across windows. This
first version does not select unloaded rows or expose a remote select-all
operation.

## Loading, empty, and error states

`state="loading"` and `state="error"` replace ready Rows with one spanning
state output. Ready with `total_count=0` becomes empty. Fill the corresponding
Slot for richer server content, or override the plain localized label.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdata_grid/snippets/states.py" title="Render Data Grid states" />

## Accessibility and Cell content

The family follows the ARIA data-grid interaction model. Header and Cell Slot
content cannot contain links, buttons, inputs, editable content, or another
Tab stop in this first version; focus remains on the Header or Cell. Use
`onCellActivate` for Enter and double-click activation.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdata_grid/snippets/accessibility.py" title="Use exact positions and disabled Rows" />

Column labels and Cell values belong to the application and should already be
localized. State labels and browser announcements use the Citry UI catalog by
default. Explicit label overrides remain caller-owned and do not switch with
the client locale.

## Styling and scope boundaries

Use `density`, `striped`, `column_borders`, and `sticky_header` for common
presentation. Customize the root and native table separately with `attrs` and
`table_attrs`, or use the documented public variables and part selectors.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdata_grid/snippets/customization.py" title="Customize a Data Grid" />

Inline editing, arbitrary Cell widgets, built-in filtering, grouping,
aggregation, pivoting, tree Rows, pinning, reordering, resizing, clipboard
mutation, export, and browser-owned data sources are outside this first
family. Compose application controls around the grid instead.

<!-- UI_LIBRARY_API_REFERENCE -->
