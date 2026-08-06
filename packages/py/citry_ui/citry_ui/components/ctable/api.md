---
title: Table
description: Present finite server-owned records in a styled native Table.
---

# Table

`CTable` renders finite, read-only tabular data with native HTML semantics. It
owns structure and presentation, not sorting, selection, editing, pagination,
or remote queries.

## Table at a glance

Line and outline variants, three densities, stripes, hover, column borders,
sticky headers, and explicit loading, empty, and error output share one native
Table model.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctable/snippets/at_a_glance.py"
  title="Table at a glance"
/>

`CTable` has no component JavaScript or client inputs. Every Table input is a
server input passed through `<c-CTable ... />` or `CTable(...)`. Controls
inside cells keep their own client props and native events.

## Build a Table

Declare columns once, then give every keyed row exactly one value per column.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctable/snippets/moons_of_jupiter.py"
  title="List the moons of Jupiter"
/>

```citry-html
<c-CTable
  c-columns="columns"
  c-rows="rows"
  striped
>
  <c-fill name="caption">
    Galilean moons
  </c-fill>
</c-CTable>
```

```python
from citry_ui import CTable, CTableColumn, CTableRow

moon_table = CTable(
    columns=(
        CTableColumn("moon", "Moon", row_header=True),
        CTableColumn("diameter", "Diameter", align="end"),
    ),
    rows=(
        CTableRow("europa", {"moon": "Europa", "diameter": "3,122 km"}),
    ),
    slots={"caption": "Galilean moons"},
)
```

Keys are stable application identity, not display text or array positions.
They must be unique and non-empty. Row and column keys are exposed in escaped
`data-*` attributes, so do not put secrets in them.

Use one `row_header=True` column for the entity or category that identifies
each row. `align="end"` follows text direction and suits numeric values. Add
tabular numerals through `cell_attrs`, a class, or the public cell selector.

## Present rich cells

Raw values are escaped. A `CTableCell` adds attributes to one position, and a
component-like value renders directly. Use the generic `cell` fill when output
depends on the current row and column.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctable/snippets/rich_cells.py"
  title="Build an observation catalog"
/>

```citry-html
<c-fill name="cell" data="{ row, column, cell }">
  <c-if cond="column.key == 'action'">
    <c-CButton size="sm">
      View {{ row.key }}
    </c-CButton>
  </c-if>
  <c-else>
    {{ cell.value }}
  </c-else>
</c-fill>
```

`header_attrs` targets one column header. `cell_attrs` supplies defaults to
every body cell in that column. `CTableCell.attrs` wins for ordinary duplicate
attributes while class and style contributions merge. Structural values such
as scopes and spans remain Table-owned.

Sorting links, row actions, checkboxes, Inputs, and Comboboxes may live in
cells, but their behavior belongs to those controls. Hover never makes a row
selectable or clickable.

## Add totals and summaries

Set one or more column `footer` values to render a native one-row `tfoot`.
Footer content may be plain text or another component. `footer_attrs` targets
that column's footer cell.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctable/snippets/survey_totals.py"
  title="Summarize telescope time"
/>

The `footer` fill receives `{column, value, column_index}` once per footer
cell. Its fallback is the matching column value. The row-header column remains
a row header in the footer.

Version 1 owns one summary row. Multiple footer rows, grouped headers,
`rowspan`, `colspan`, and `colgroup` need a future logical-grid schema.

## Choose appearance

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctable/snippets/appearance.py"
  title="Compare Table appearance"
/>

- `variant="line"` separates rows; `outline` also frames the root.
- `density` accepts `default`, `comfortable`, or `compact`.
- `striped` alternates ready-row surfaces.
- `hover` adds pointer feedback without behavior.
- `column_borders` adds vertical separators.
- `caption_side` places a native caption at the top or bottom.
- `layout="fixed"` uses native fixed table layout; set widths through column
  attribute styles, classes, or public selectors.

These are server inputs. Side-by-side examples show their output without
pretending that Table owns browser-reactive configuration.

## Show loading, empty, and error output

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctable/snippets/states.py"
  title="Show survey states"
/>

The header stays visible. Loading, empty, and error replace body rows with one
native cell spanning every column. Loading sets `aria-busy` on the Table.
Configured footers appear only in ready output, including ready-empty output.

The `loading`, `empty`, and `error` slots change visible content. Their matching
label inputs also feed a persistent polite live region outside the busy Table.
Keep each label consistent with its custom slot.

Entering a state removes stale ready rows. Returning to ready renders the next
complete keyed collection.

## Keep wide and long Tables usable

`overflow="auto"` is the default. It preserves native row and column
relationships and lets two-dimensional data scroll horizontally at narrow
widths or high zoom.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctable/snippets/sticky_overflow.py"
  title="Keep headers visible"
/>

For a bounded scroller, combine `sticky_header=True` with a block-size limit:

```citry-html
<c-CTable
  c-columns="columns"
  c-rows="rows"
  sticky_header
  style="max-block-size: 24rem"
/>
```

For a header that follows page scroll, use `sticky_header=True` with
`overflow="visible"`. The two modes have different scroll ancestors.

Auto overflow always adds one keyboard focus stop because a zero-JavaScript
component cannot measure overflow before deciding. A caption names that region.
Without a caption, set `scroll_label` or name the native Table with
`table_attrs={"aria-label": ...}`. The focus ring stays visible.

An auto-overflow wrapper can clip inline menus, listboxes, and other overlays.
Use a top-layer or portaled overlay when available, or choose visible overflow
when the page can contain the Table.

## Preserve native semantics and focus

Column headers use `<th scope="col">`. The optional row-header column uses
`<th scope="row">`; other cells use `<td>`. A caption supplies the Table's
native accessible name. Use `table_attrs` for `aria-label`, `aria-labelledby`,
or `aria-describedby` when visible caption text is not appropriate.

Table does not use `role="grid"`, move focus with arrow keys, or select rows.
Tab order contains the auto-overflow wrapper and focusable content supplied in
cells. Native table navigation remains available to assistive technology.

Ready rows use private Citry morph keys. Reordering preserves a surviving row
subtree and its control state where Citry can preserve the control. Removing a
row removes its complete subtree. Table does not guess a new focus target.

Sorting, filtering, pagination, and selection belong to controls composed
around the Table. Those controls update server state and render the next
complete `columns` and `rows`; they are not Table callbacks.

## Theme and customize Table

Use `class_`, `style`, public CSS variables, or documented selectors. Do not
target private `.cui-*` classes or `--_cui-*` variables.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctable/snippets/theme_customization.py"
  title="Theme observatory Tables"
/>

Variables inherit, so one ancestor can theme several Tables. Set a variable on
one root for an isolated override. Public selectors such as
`[data-citry-ui-part="footer-cell"]` target stable elements. Reflected
attributes expose the selected visual configuration for CSS and inspection.

Nested Tables resolve their own density and variant rules. Structural styles
from an outer Table do not stripe, hover, border, or resize an inner Table.
Public color variables may intentionally inherit unless the nested root
overrides them.

## Support direction, long content, and print

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctable/snippets/environment.py"
  title="Read translated star names"
/>

Logical alignment follows LTR and RTL. Long text wraps by default; use fixed
layout and explicit widths only when truncation or stable columns improve the
task. At narrow widths and 400% zoom, surrounding content still reflows while
the Table may scroll as a two-dimensional exception.

Default colors support light and dark scopes. Forced colors retains text,
focus, and borders without using stripes or hover as the only signal. Print
removes overflow clipping and sticky positioning.

`CTable` targets ordinary finite collections. The repository's diagnostic
scaling harness records server rendering at 10, 100, and 1,000 rows; hosted
results remain release evidence, not a performance guarantee. Virtualization,
grouped headers, interactive grid navigation, editing, and remote collection
ownership belong to a future DataTable/DataGrid.
