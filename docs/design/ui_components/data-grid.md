# Data Grid

**Status:** implementation contract accepted for the first production pass.
The family is an interactive, server-rendered ARIA data grid. It is separate
from semantic `CTable` because it owns composite focus, row selection, sort
requests, and optional fixed-height server windowing.

## 1. Purpose and product bar

`CDataGrid` presents tabular records that people navigate as one composite
widget. It supports complete server collections and contiguous server windows.
The first pass owns:

- arrow, Home, End, Page, and control-modified grid navigation;
- single or multiple row selection;
- single and shift-modified multi-column sort requests;
- exact row and column position metadata;
- fixed-height server window requests;
- controlled and uncontrolled selection;
- loading, empty, error, and pending states;
- responsive overflow, sticky headers, localization, and cleanup.

The shortest intended use is Python composition because columns and rows are
data records:

```python
CDataGrid(
    columns=(
        CDataGridColumn("name", "Name", sortable=True),
        CDataGridColumn("role", "Role"),
    ),
    rows=(
        CDataGridRow("ada", {"name": "Ada", "role": "Engineer"}),
        CDataGridRow("grace", {"name": "Grace", "role": "Admiral"}),
    ),
    label="People",
)
```

Use `CTable` for document-like tabular reading, native links in the ordinary
Tab order, spans, footers, and print-first output. Use `CDataGrid` when one
managed cell stop and directional navigation materially improve the task.

Non-goals for this pass are inline editing, arbitrary widgets in cells,
filter UI, grouping, aggregation, pivoting, tree rows, column pinning or
reordering, resize handles, drag and drop, clipboard mutation, export, and a
browser-owned data source. There is no headless API.

## 2. Prior art and complaints

Research was refreshed on 2026-08-21.

| Product or standard | Version or review date | Surface inspected | Citry UI decision |
|---|---|---|---|
| [WAI-ARIA APG Grid pattern](https://www.w3.org/WAI/ARIA/apg/patterns/grid/) | current 2026-08-21 | composite focus, data-grid navigation, selection shortcuts, cell/widget focus boundary | Use one cell in the page Tab order, exact grid roles/positions, directional navigation, and Shift+Space row selection. Defer edit mode and multi-widget cells. |
| [Vuetify Data tables](https://vuetifyjs.com/en/components/data-tables/basics/) and [virtual tables](https://vuetifyjs.com/en/components/data-tables/virtual-tables/) | current 2026-08-21 | headers/items, selection, sorting, density, loading/no-data, server and virtual variants, scoped cells | Adopt data records, generic render slots, selection, sort models, density, status outputs, and explicit complete/windowed ownership. Do not copy pagination or footer ownership into the grid. |
| [MUI X Data Grid 9](https://mui.com/x/react-data-grid/) and [accessibility](https://mui.com/x/react-data-grid/accessibility/) | 9.11, 2026-08-21 | controlled models, cell navigation, sorting, selection, virtualization, editing boundary, density | Adopt controlled sort/selection models, complete keyboard navigation, stable IDs, and fixed row geometry. Defer edit mode, column menus, and premium breadth. |
| [Vaadin Grid 25](https://vaadin.com/docs/latest/components/grid) | 25 docs, 2026-08-21 | Web Component columns, selection, sorting, lazy loading, pagination tradeoffs, cell focus | Adopt server-provider-shaped range requests and row/cell focus. Keep pagination composable because it provides different orientation and select-all semantics. |
| [AG Grid 36](https://www.ag-grid.com/javascript-data-grid/server-side-model-datasource/) | 36.1, 2026-08-21 | server-side range/sort contracts, stable row IDs, selection across unloaded data | Adopt explicit half-open row ranges, request IDs, server sort metadata, and stable keys. Reject implicit “all rows” selection across unloaded data in v1. |
| Native HTML table | current browsers | no-script reading, native row/column relationships, print | Render a native table with `role=grid`; retain meaningful no-JavaScript content and native table layout while taking composite keyboard ownership only after enhancement. |

Common complaints addressed are unclear table-versus-grid choice, every link
becoming a Tab stop, client sorting that disagrees with the server, select-all
ambiguity across unloaded rows, losing focus when a window changes, and
virtualized rows reporting the wrong logical positions.

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `headers`, `items`, `item-value` | direct API | `columns`, `rows`, stable `row.key` | adopt typed server records |
| per-column and per-cell slots | generic scoped slots | `header`, `cell` | adopt one typed fallback chain; dynamic keyed slots wait for parser/runtime support |
| `show-select`, single/multiple value | direct API | `selection`, `selected`, `onSelectionChange` | adopt without an ambiguous all-pages checkbox |
| `sort-by`, multi-sort | direct API | `sort`, `multi_sort`, `onSortChange` | server-owned request model |
| `loading-text`, `no-data-text` | i18n/slots | state labels and state slots | adopt and add error state |
| density, fixed header, height | direct API/CSS | `density`, `sticky_header`, `viewport_size` | adopt logical equivalents |
| server table `items-length` | direct API | `total_count`, `start_index`, `onRangeChange` | use contiguous fixed-height windows |
| virtual table `item-height` | direct API | `row_height`, `overscan` | fixed-height only |
| pagination and rows-per-page footer | composition | `CPagination` plus application query state | keep separate |
| search/filter | composition | application controls and server rows | omit built-in query language |
| group, expand, row details | separate future design | none | defer |
| column/body replacement slots | deliberate omission | generic slots and public parts | preserve semantic/focus ownership |

## 3. Public composition and anatomy

```text
CDataGrid → div.cui-data-grid
├─ span[role=status]                       announcements
└─ div                                    scroll viewport
   └─ table[role=grid]
      ├─ caption?                         authored label supplement
      ├─ colgroup
      ├─ thead
      │  └─ tr[role=row]
      │     └─ th[role=columnheader] × columns
      └─ tbody
         ├─ spacer row?                   omitted rows before window
         ├─ tr[role=row] × supplied rows
         │  └─ td[role=gridcell] × columns
         ├─ spacer row?                   omitted rows after window
         └─ one state row when not ready
```

`CDataGrid` is the only public component. `CDataGridColumn`, `CDataGridRow`,
`CDataGridCell`, and `CDataGridSort` are immutable input records, not component
children. Root `attrs` and table `table_attrs` are separate destinations.
Column, row, and cell mappings cannot replace owned roles, positions, focus,
sort/selection state, IDs, keys, or part markers.

The native caption is optional, but `label` is required because a composite
grid must always have an accessible name. Generated IDs derive from root,
row, and column indices; stable keys preserve logical identity.

## 4. Server inputs and client inputs

`CDataGrid` server inputs:

| Input | Type/default | Class and effect |
|---|---|---|
| `columns` | nonempty `Sequence[CDataGridColumn]` | structural server schema |
| `rows` | `Sequence[CDataGridRow]` | supplied complete collection or contiguous range |
| `label` | nonempty `str` | required accessible name |
| `id` | `str | None` | stable identity; generated by default |
| `state` | `ready | loading | error = ready` | body/state output |
| `sort` | `Sequence[CDataGridSort] = ()` | server-authoritative sort model |
| `multi_sort` | `bool = True` | Shift-click/Shift+Enter model extension |
| `selection` | `none | single | multiple = none` | row selection mode |
| `selected` | `Sequence[str] = ()` | initial selected keys |
| `disabled` | `bool = False` | interaction configuration |
| `total_count` | `int | None` | logical row count; omission means `len(rows)` |
| `start_index` | `int = 0` | first supplied logical row index |
| `row_height` | positive `int = 48` | fixed pixel row stride |
| `viewport_size` | positive `int = 400` | initial scroll viewport block size |
| `overscan` | `int = 3`, 0–100 | range request buffer |
| `initial_index` | nonnegative `int = 0` | one-shot initial scroll row |
| `density` | `comfortable | compact | spacious = comfortable` | cell padding profile |
| `striped`, `column_borders`, `sticky_header` | booleans | presentation |
| status and announcement labels | source English catalog defaults | per-output explicit overrides |
| `class_`, `style`, `attrs`, `table_attrs` | structured values/`None` | trusted extension destinations |

Record inputs are also public and checked eagerly:

| Record | Fields and constraints |
|---|---|
| `CDataGridColumn` | unique nonempty `key`; nonempty application-localized `label`; `sortable`; `width` from 40 through 2000 CSS pixels; logical `align`; allowed `header_attrs` and `cell_attrs` |
| `CDataGridRow` | unique nonempty `key`; exact string-keyed Cell mapping for every Column; `disabled`; allowed Row `attrs` |
| `CDataGridCell` | escaped or component-like `value`; allowed Cell `attrs` merged after Column Cell attributes |
| `CDataGridSort` | unique known sortable Column `key`; `asc` or `desc` direction |

Client `$c-props`:

| Input | Type | Omitted/null | Invalid | Effect |
|---|---|---|---|---|
| `sort` | sort-record array | server model | diagnose, retain | controls accepted sort indicators |
| `selected` | unique known-key array | uncontrolled/server initial; null releases | diagnose, retain | controls row selection |
| `disabled` | boolean | server value | diagnose, retain | controls interaction |
| `overscan` | integer 0–100 | server value | diagnose, retain | changes desired range |
| `onSortChange` | function | none | diagnose, retain | receives sort requests |
| `onSelectionChange` | function | none | diagnose, retain | receives selection requests/commits |
| `onRangeChange` | function | none | diagnose, retain | receives uncovered range requests |
| `onCellActivate` | function | none | diagnose, retain | receives Enter/double-click activation |

Server and valid client models remain isolated per instance. Sort is always
request/accept because the component does not compare application values.
Selection is uncontrolled unless a non-null client `selected` is supplied.

## 5. State model

`state=loading` or `error` replaces supplied ready rows with one spanning
state row, sets `aria-busy` only for loading, and disables navigation and
selection. Ready with zero logical rows is empty. A ready window whose desired
range is outside the supplied range sets `data-pending` and `aria-busy=true`
while retaining current rows.

Sort activation cycles `none → asc → desc → none`. Without Shift, the request
contains only the activated column. With Shift and `multi_sort=True`, it
updates that column in the ordered existing model. It never reorders DOM rows.

Selection modes:

- `none`: no selection behavior or `aria-selected` rows;
- `single`: one enabled row or none;
- `multiple`: independent toggles plus loaded-range Shift selection.

Disabled rows cannot be selected or activated. Disabled grid state blocks all
owned interactions but retains current selection and readable content.

## 6. Slots and slot data

| Slot | Required | Data | Fallback |
|---|---|---|---|
| `caption` | no | `{}` | omitted |
| `toolbar` | no | `{}` | omitted before viewport |
| `header` | no | `{column, column_index, sort_direction, sort_priority}` | escaped column label plus owned indicator |
| `cell` | no | `{row, column, cell, row_index, column_index, selected}` | escaped/component-like cell value |
| `loading` | no | `{}` | localized loading label |
| `empty` | no | `{}` | localized empty label |
| `error` | no | `{}` | localized error label |

Generic slots avoid promising an unproven dynamic `cell.<key>` namespace.
Header and cell slot output must not contain focusable or editable descendants
in v1; client initialization rejects them because focus remains on cells.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger and timing |
|---|---|---|
| `onSortChange` | `(sort, detail)` | request-only after sortable header click or Enter |
| `onSelectionChange` | `(selected, detail)` | after uncontrolled commit or before controlled acceptance |
| `onRangeChange` | `(detail)` | animation-frame-coalesced uncovered desired range |
| `onCellActivate` | `(detail)` | Enter or double-click on an enabled body cell |

Details include stable row/column keys, previous values, source, controlled
flag, source event, and monotonic request ID where applicable. Failures are
isolated and logged. No custom DOM events or public imperative methods ship.
Native pointer, keydown, focus, and scroll events remain available through
ordinary Alpine listeners on consumer wrappers.

## 8. Semantics, keyboard, focus, and assistive technology

The native table uses `role=grid`, `aria-label`, `aria-rowcount`, and
`aria-colcount`. Rows, headers, and cells expose explicit roles plus
`aria-rowindex` and `aria-colindex`. Headers expose `aria-sort`; selected rows
expose `aria-selected`. Only one navigable header/cell has `tabindex=0`.

| Context | Input | Result |
|---|---|---|
| any grid cell/header | Arrow keys | adjacent rendered cell/header; horizontal arrows follow visual DOM order |
| cell/header | Home / End | first / last cell in the row or header |
| body cell | Page Up / Page Down | nearest rendered row one viewport away and schedules range request |
| any cell/header | Ctrl/Cmd+Home / End | first header or last supplied cell; window requests logical edge if absent |
| sortable header | Enter/click | single sort request |
| sortable header | Shift+Enter/Shift+click | multi-sort request when enabled |
| selectable row cell | Shift+Space | toggle current row |
| multiple selection cell | Shift+click | select loaded enabled range from anchor |
| enabled body cell | Enter/double-click | cell activation callback |
| grid | Tab / Shift+Tab | enter at retained active cell, then leave composite |

When a requested range is not supplied, focus stays on the nearest retained
cell until the next server render. A new window restores the desired logical
row and column when present. The status region announces accepted sorting and
selection changes. Manual screen-reader evidence remains required because
virtualized ARIA grids are high risk.

## 9. Native forms and validation

The family is not a form control. Row selection is application state and does
not submit hidden inputs, claim required validity, or intercept form reset.
Applications that submit selected keys create their own inputs or controlled
form field. Slots cannot contain form controls in v1.

## 10. Styling and theme contract

Public variables are:

| Variable | Type | Purpose | Default |
|---|---|---|---|
| `--cui-data-grid-viewport-size` | length | viewport block size | server `viewport_size`, 400px |
| `--cui-data-grid-row-height` | length | fixed ready-row height | server `row_height`, 48px |
| `--cui-data-grid-min-width` | length | horizontal overflow threshold | sum of column widths |
| `--cui-data-grid-background` | color | grid surface | Canvas |
| `--cui-data-grid-foreground` | color | primary text | CanvasText |
| `--cui-data-grid-muted` | color | status and secondary text | accessible CanvasText mix |
| `--cui-data-grid-border-color` | color | row/column/outline borders | adaptive neutral |
| `--cui-data-grid-header-background` | color | header surface | adaptive neutral |
| `--cui-data-grid-selected-background` | color | selected row surface | adaptive blue |
| `--cui-data-grid-striped-background` | color | alternate rows | subtle neutral |
| `--cui-data-grid-hover-background` | color | pointer row feedback | subtle highlight |
| `--cui-data-grid-focus-color` | color | active-cell outline | Highlight |
| `--cui-data-grid-radius` | length | viewport corners | 0.625rem |

Stable parts are `data-grid`, `toolbar`, `viewport`, `table`, `caption`,
`header`, `header-row`, `header-cell`, `sort-indicator`, `body`, `row`, `cell`,
`spacer-row`, `state-row`, `loading`, `empty`, `error`, and `status`.

Public reflected attributes are `data-state`, `data-density`, `data-striped`,
`data-column-borders`, `data-sticky-header`, `data-selection`, `data-disabled`,
`data-pending`, `data-selected`, `data-row-key`, `data-column-key`,
`data-row-index`, `data-column-index`, `data-align`, `data-sort`,
`data-sort-priority`, `aria-busy`, `aria-disabled`,
`aria-selected`, `aria-sort`, `aria-rowcount`, `aria-colcount`,
`aria-rowindex`, `aria-colindex`, `role`, and `tabindex`.

## 11. Environmental behavior

Logical properties and text alignment support RTL without changing column or
row data order. Horizontal Arrow behavior follows physical visual movement,
matching APG. Narrow containers scroll horizontally; no card transformation
destroys grid relationships. Forced colors retain cell focus and selected-row
outlines. Reduced motion disables smooth scrolling and transitions. Zoom and
text spacing may clip within fixed row windows, so applications choose a
larger `row_height` for wrapping content. Print removes the viewport limit and
prints only supplied rows; a window cannot print unloaded rows.

Application cell content retains its own language and direction. Column labels
are application-localized. Library status, sort announcements, and selection
announcements use Citry UI messages. No locale-sensitive client sorting occurs.

## 12. Overlay and layering behavior

The family creates no overlay, column menu, editor, tooltip, or top-layer
surface. Applications place external filters and actions in the toolbar slot.

## 13. Collections, async data, and identity

Column keys and row keys are unique, nonempty stable strings. Every row maps
exactly every column key. In complete mode `total_count=len(rows)` and
`start_index=0`. Window mode requires `total_count >= start_index + len(rows)`
and fixed row height. Spacer rows reserve omitted block size and are hidden
from assistive technology.

`onRangeChange` reports half-open desired and visible ranges plus request ID,
reason, and source event. The application owns fetching, cancellation,
supersession, retry, offline behavior, and replacement. Stable request IDs let
it discard stale results. Sort changes usually replace rows and reset the
window to zero; the component does not issue network requests.

Selection can contain known supplied row keys only in v1. This deliberately
avoids claiming selection of unloaded rows. A future remote-selection model
needs explicit include/exclude rules like mature server grids.

## 14. Server render, morph, and cleanup

Without JavaScript, the native table remains readable, sortable headers are
not falsely interactive, and supplied range spacers preserve geometry. After
activation, one delegated keydown, click, double-click, focus, and scroll path
owns interaction. Repeated initialization is idempotent.

A compatible replacement retains scroll position, active logical row/column,
uncontrolled selection for surviving keys, and pending desired range. A hard
replacement starts from server inputs. Cleanup cancels animation frames and
timers, removes listeners/effects/markers, and prevents callbacks after
removal.

## 15. Security and content trust

Labels and values use ordinary escaped Citry output. Slot output is trusted
component composition but is checked for unsupported focusable descendants.
No `innerHTML`, eval, client template generation, URL parsing, clipboard, or
remote fetch occurs. Attribute maps reject owned semantics, identity,
runtime markers, event directives, and dynamic bindings to owned targets.

## 16. Assets and performance

The family adds one CSS asset and one component JavaScript asset. Runtime work
is linear in supplied rows times columns. One instance owns delegated event
listeners, at most one resize observer for viewport geometry, and one pending
animation frame. It never clones cell content. Fixed windowing bounds row DOM;
column virtualization is deferred because it complicates keyboard and browser
find behavior.

Do not raise package asset ceilings for this family. Measure raw, gzip, and
Brotli deltas and report them in batch reconciliation.

## 17. Acceptance matrix

| Area | Required evidence |
|---|---|
| schema/render | exact records, keys, mappings, positions, complete/windowed geometry, states, attrs ownership |
| keyboard/focus | all APG navigation keys, one Tab stop, sort activation, selection, disabled rows, focus after range replacement |
| models | sort request/accept, controlled selection rejection/acceptance, uncontrolled commit, invalid clients |
| async/window | desired ranges, pending state, request coalescing/IDs, edge clamping, cleanup |
| i18n | all default/override paths, sort/selection announcements, live locale switching, no binding on caller text |
| environment | RTL, narrow overflow, fixed rows, forced colors, reduced motion, zoom/text growth, print |
| quality | structured docs, six snippets, standalone scenario, axe, three browsers, asset evidence |

Automated checks do not replace manual NVDA/Firefox, JAWS/Chrome,
VoiceOver/Safari, high-zoom keyboard, touch-scroll, and visual-design review.

## 18. Compatibility classification

`CDataGrid`, input records, aliases, callbacks, slot data, documented parts,
variables, reflected attributes, catalog keys, semantics, keyboard model, and
window request model are stable public API. Exact colors/spacing and
undocumented wrappers may evolve. Private normalized records, behavior hooks,
request scheduling, and class names remain implementation details.

## 19. Public documentation contract

The guide teaches: choosing Table versus DataGrid; complete grid; sorting and
selection; controlled models; server windowing; keyboard/accessibility;
states; customization; and deferred editing/filtering. Planned snippets are
`at_a_glance.py`, `sorting_selection.py`, `controlled.py`, `windowed.py`,
`states.py`, `accessibility.py`, and `customization.py`.

The structured API ends with Translation keys and lists every family key.
The quality scenario covers ready, selection, sorting, complete/windowed,
loading, empty, error, narrow, RTL, long content, and cleanup.

## 20. Open decisions and deferred work

Inline editing, arbitrary focusable cell widgets, built-in filters, pagination
footer, remote all-selection, resize/reorder/pin/hide columns, grouping,
aggregation, pivoting, row details/tree data, export, clipboard mutation, and
column virtualization are deferred. Each changes focus, data, async, or
selection ownership and requires its own evidence. None blocks the first pass.

## 21. Internationalization

`CDataGrid.I18n.messages_locale` is `en-US`. The final class member owns
loading, empty, error, ascending-sort, descending-sort, cleared-sort,
one-row-selected, and multiple-rows-selected messages. Initial state DOM uses
server `tr()`. Stable state text uses `$c-tr`; browser sort and selection
announcements use one-shot `i18n.tr()` with application-localized column labels
and string counts. Explicit label overrides remain caller-owned and do not
register catalog bindings. The grid never compares, folds, formats, parses, or
sorts application data in the browser.
