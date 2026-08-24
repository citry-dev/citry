# Tree Grid

**Status (2026-08-22):** production implementation, public docs, structured
reference, examples, quality scenario, and focused browser
coverage shipped in `citry-ui` 0.2.0. Research refreshed 2026-08-21.

## 1. Purpose and boundary

`CTreeGrid` presents hierarchical records in aligned data columns. It is the
Salesforce-style expandable and selectable grid requested for Citry UI, not a
spreadsheet. Each `CTreeGridRow` owns a stable key, cells, optional child Rows,
disabled state, and attributes. The first column owns hierarchy indentation and
the branch control.

The WAI APG treegrid pattern is authoritative for composite focus, cell
navigation, row hierarchy, expansion, and selection. Salesforce's current Tree
Grid confirms the practical product boundary: a Data Grid-like table with
expandable nested rows. Spreadsheet editing, formulas, merged cells, arbitrary
range selection, infinite loading, and inline editing are excluded. Editing
belongs to the existing `CDataGrid` extension in this batch.

## 2. Data and anatomy

`columns` is a nonempty sequence of `CTreeGridColumn`. `rows` is a nonempty
recursive sequence of `CTreeGridRow`; every Row must contain exactly the Column
keys and every Row key is globally unique. The server flattens Rows in preorder
while retaining parent key, one-based level, position in set, and set size.

```text
div root
|- optional toolbar
|- viewport
|  `- table role=treegrid
|     |- header row and columnheaders
|     `- body rows
|        `- gridcells; first owns indent and expander
|- hidden selected-row inputs
`- polite status
```

Collapsed descendants stay in the DOM but are hidden and inert. Server output
therefore contains the complete finite hierarchy and preserves accepted state
without JavaScript.

## 3. Interaction

One gridcell is in the page tab order. Up and Down move through visible Rows in
the same Column. Right and Left move across cells, except at the first cell:
Right expands a collapsed branch before moving, while Left collapses an open
branch or moves to its parent Row. Home and End move to the first and last cell
in a Row; Control plus Home or End reaches the first or last visible gridcell.
Enter toggles a branch from the first cell and activates other cells.

Shift plus Space toggles the focused Row in single or multiple selection mode,
including unselecting a selected Row. Pointer activation of a cell selects its
Row; the expander changes only expansion. Focus and selection stay visually
distinct. Disabled Rows can receive reading focus but cannot expand, select, or
activate.

## 4. Controlled state, forms, and callbacks

`expanded` and `selected` accept stable Row keys. Each can be controlled with a
same-named client prop. Uncontrolled requests commit immediately; controlled
requests emit and restore accepted state until the owner supplies a value.
`onExpandedChange`, `onSelectionChange`, and `onCellActivate` include requested
state, previous state, Row and Column identity, controlled flag, source, and
native event.

When `name` exists, selected Row keys are emitted as repeated hidden inputs in
preorder. Disabled Tree Grids emit none. Form reset restores server selection
and expansion or requests them from controlled owners.

## 5. Accessibility, localization, and styling

The table has `role=treegrid`, an accessible label, row and column counts,
columnheaders, rows, and gridcells. Rows expose `aria-level`, `aria-posinset`,
`aria-setsize`, `aria-expanded` for branches, and `aria-selected` when selection
is enabled. The expander's localized name includes the application Row label.
Selection and expansion announcements are localized browser strings. Explicit
message overrides remain fixed.

Public parts include `tree-grid`, `toolbar`, `status`, `viewport`, `table`,
`header`, `header-cell`, `body`, `row`, `cell`, `hierarchy`, `expander`,
`cell-content`, and `inputs`. Variables cover minimum width, Row height,
indent, border, surfaces, selected state, focus, and disabled opacity. Narrow
viewports scroll horizontally; RTL uses logical indentation. Forced colors,
reduced motion, zoom, and print retain meaning.

## 6. Lifecycle, security, acceptance, and deferred work

Initialization is idempotent. Cleanup removes listeners, form hooks, reactive
effects, and state. No global observer or document listener is needed. Cell
values are escaped by Citry; keys and labels are plain strings; the runtime
uses maps rather than raw-key selectors and never uses HTML execution.

Evidence covers recursive validation, complete server output, expansion,
selection and unselection, cell navigation, parent navigation, controlled
requests, native form order and reset, disabled Rows, RTL, narrow overflow,
i18n, cleanup, axe, API schema, six snippets, and three browser engines.

Deferred work includes hierarchical sorting, async children, virtualization,
column resizing, and editing. Those require contracts that cannot be inferred
from this finite hierarchy.
