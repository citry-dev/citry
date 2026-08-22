---
title: Data Grid
description: Navigate, sort, select, edit, and server-window tabular application data with Citry UI.
---

# Data Grid

Use `CDataGrid` for application data that benefits from one composite Tab
stop, cell navigation, row selection, accepted complete-collection sorting,
or fixed-height server windowing. Use `CTable` instead for document-like tables, ordinary
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
ascending, descending, then unsorted. `onSortChange` receives the requested
model, and accepted `sort` state must come back from the owner. When that
accepted request belongs to a complete supplied collection, the grid visibly
reorders Rows by rendered Cell text. It uses locale-aware numeric comparison,
applies sort entries in priority order, and restores server order when sorting
is cleared. Shift preserves other Columns when `multi_sort=True`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdata_grid/snippets/sorting_selection.py" title="Sort and select people" />

`selection="single"` or `selection="multiple"` enables Row selection.
Uncontrolled selection commits immediately. A non-null client `selected`
array makes selection controlled, so the visible state waits for acceptance.
In multiple mode, drag a mouse pointer across loaded Rows to select a range;
starting on a selected Row removes the dragged range. Disabled Rows are
skipped. Shift+Space toggles the focused Row in either direction. Touch remains
ordinary scrolling rather than starting a drag selection.

## Control models from Alpine

Pass `sort`, `selected`, and callbacks through `$c-props`. Invalid client
models are diagnosed and the last valid state remains active.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdata_grid/snippets/controlled.py" title="Control Data Grid models" />

Sort remains request/accept so an application can reject it or wait for a
server response. Initial and programmatic models describe the server-authored
order; local reordering occurs when the browser accepts a Header request for a
complete collection. A server window cannot sort Rows it does not have, so its
owner must return the newly ordered range. Selection becomes uncontrolled again
when client `selected` is omitted or null. Accepted changes are announced
politely.

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

## Edit cells in place

Set `editable=True` on a `CDataGridColumn`, then choose its `editor` from
`text`, `number`, `checkbox`, or `select`. Select editors require named
`CDataGridEditOption` records. `editor_attrs` accepts only the documented
attributes for that native control, such as `min`, `max`, `step`,
`maxlength`, and `placeholder`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdata_grid/snippets/editing.py" title="Edit project assignments" />

Enter, F2, typing, Backspace, Delete, or double-click enters edit mode where
appropriate. Enter commits, Escape cancels, and Tab commits before moving to
the adjacent Cell. `onCellEditCommit` receives the typed value and stable Row
and Column details. Returning `False` rejects the value and keeps the editor
open. The component does not mutate server Rows: update the owner and render
the accepted value back into `rows`.

The static documentation preview uses a small self-contained range with no
omitted leading or trailing Rows. It therefore never exposes scrollable blank
space that the static page cannot replace. In an application, a partial range
keeps its spacers only until the owner replaces it after `onRangeChange`.

## Loading, empty, and error states

`state="loading"` and `state="error"` replace ready Rows with one spanning
state output. Ready with `total_count=0` becomes empty. Fill the corresponding
Slot for richer server content, or override the plain localized label.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdata_grid/snippets/states.py" title="Render Data Grid states" />

## Accessibility and Cell content

The family follows the ARIA data-grid interaction model. Header and Cell Slot
content cannot contain caller-authored links, buttons, inputs, editable
content, or another Tab stop; focus remains on the Header or Cell. Built-in
editors temporarily move focus into one owned native control. Use
`onCellActivate` for Enter and double-click activation on noneditable Cells.

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

Arbitrary caller-authored Cell widgets, built-in filtering, grouping,
aggregation, pivoting, tree Rows, pinning, reordering, resizing, clipboard
mutation, export, and browser-owned data sources are outside this first
family. Compose application controls around the grid instead.

<!-- UI_LIBRARY_API_REFERENCE -->
