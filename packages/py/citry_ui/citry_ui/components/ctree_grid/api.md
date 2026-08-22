---
title: Tree Grid
description: Navigate expandable and selectable hierarchical records in aligned columns.
---

# Tree Grid

`CTreeGrid` combines a finite Row hierarchy with Data Grid columns. It is for
account trees, threaded records, work breakdowns, and similar structured data,
not spreadsheet formulas or inline editing.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctree_grid/snippets/at_a_glance.py" title="Present an account hierarchy" />

## Expand nested Rows

Put child `CTreeGridRow` records in `children` and list initially open branch
keys in `expanded`. The first Column owns indentation and expansion.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctree_grid/snippets/expansion.py" title="Control visible project levels" />

## Select and submit Rows

Choose `single` or `multiple` selection and set `name` to emit repeated hidden
Row keys in preorder. Shift+Space toggles the focused Row, including unselect.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctree_grid/snippets/selection.py" title="Select organization units" />

## Own state in Alpine

Client `expanded` and `selected` props are controlled. Their callbacks report
the requested vector, previous vector, Row key, requested boolean state,
controlled flag, source, and native event.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctree_grid/snippets/controlled.py" title="Own expansion and selection" />

## Customize cells

Use `header`, `cell`, `toolbar`, and `caption` slots. Cell navigation stays on
the gridcell; interactive editing remains the separate Data Grid contract.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctree_grid/snippets/custom_cells.py" title="Format hierarchical metrics" />

## Navigate accessibly

Arrow keys move through visible Rows and Columns. Left and Right also collapse,
expand, and return to parents from the hierarchy cell. Disabled Rows remain
readable but cannot mutate or activate.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctree_grid/snippets/accessibility.py" title="Keep focus and selection distinct" />

Hierarchical sorting, async children, virtual Rows, and editing are explicit
future or adjacent contracts, not hidden Tree Grid modes.

<!-- UI_LIBRARY_API_REFERENCE -->
