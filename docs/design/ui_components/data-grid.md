# Data Grid

**Status (2026-08-22):** production implementation, public docs, structured
reference, examples, quality scenario, and focused browser
coverage shipped in `citry-ui` 0.2.0. The family is an interactive,
server-rendered ARIA data grid. It is separate from semantic `CTable` because
it owns composite focus, row selection, sort requests, and optional
fixed-height server windowing.

## 1. Purpose and product bar

`CDataGrid` presents tabular records that people navigate as one composite
widget. It supports complete server collections and contiguous server windows.
The first pass owns:

- arrow, Home, End, Page, and control-modified grid navigation;
- single or multiple row selection, including loaded-Row mouse drag selection;
- single and shift-modified multi-column sort requests;
- exact row and column position metadata;
- fixed-height server window requests;
- controlled and uncontrolled selection;
- loading, empty, error, and pending states;
- inline text, number, checkbox, and select Cell editors;
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

Non-goals for this pass are arbitrary caller-authored widgets in cells,
filter UI, grouping, aggregation, pivoting, tree rows, column pinning or
reordering, resize handles, row or column drag-and-drop reordering, clipboard mutation, export, and a
browser-owned data source. There is no headless API.

## 2. Prior art and complaints

Research was refreshed on 2026-08-21.

| Product or standard | Version or review date | Surface inspected | Citry UI decision |
|---|---|---|---|
| [WAI-ARIA APG Grid pattern](https://www.w3.org/WAI/ARIA/apg/patterns/grid/) | current 2026-08-21 | composite focus, data-grid navigation, selection shortcuts, and the Cell editing focus boundary | Use one Cell in the page Tab order, exact grid roles/positions, directional navigation, Shift+Space row selection, and Enter/F2 transitions between grid navigation and one owned editor. |
| [MUI X Data Grid editing](https://mui.com/x/react-data-grid/editing/) | current 2026-08-21 | editable Columns, Cell versus Row mode, edit entry/exit, select value options, validation, and controlled data | Adopt per-Column and per-Cell eligibility, native editor kinds, named select options, request-only commits, and synchronous rejection. Keep Row editing and arbitrary custom editors deferred. |
| [AG Grid Cell editing](https://www.ag-grid.com/javascript-data-grid/cell-editing-start-stop/) | current 2026-08-21 | Enter/F2/double-click/typing entry, Escape cancellation, Tab and Enter commit | Adopt familiar entry and exit keys while keeping one editor active and preserving server ownership of Row data. |
| [Vuetify Data tables](https://vuetifyjs.com/en/components/data-tables/basics/) and [virtual tables](https://vuetifyjs.com/en/components/data-tables/virtual-tables/) | current 2026-08-21 | headers/items, selection, sorting, density, loading/no-data, server and virtual variants, scoped cells | Adopt data records, generic render slots, selection, sort models, density, status outputs, and explicit complete/windowed ownership. Do not copy pagination or footer ownership into the grid. |
| [MUI X Data Grid 9](https://mui.com/x/react-data-grid/) and [accessibility](https://mui.com/x/react-data-grid/accessibility/) | 9.11, 2026-08-21 | controlled models, cell navigation, sorting, selection, virtualization, editing boundary, density | Adopt controlled sort/selection models, complete keyboard navigation, stable IDs, fixed row geometry, and Cell editing. Defer Row editing, column menus, and premium breadth. |
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
| `sort-by`, multi-sort | direct API | `sort`, `multi_sort`, `onSortChange` | Request/accept model; matching accepted Header requests reorder complete supplied collections while windows remain server-owned. |
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
`CDataGridCell`, `CDataGridEditOption`, and `CDataGridSort` are immutable input records, not component
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
| `sort` | `Sequence[CDataGridSort] = ()` | initial server-authored sort model |
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
| `CDataGridColumn` | unique nonempty `key`; nonempty application-localized `label`; sorting/layout fields; `editable`; `text`, `number`, `checkbox`, or `select` editor; checked `editor_attrs`; unique named `editor_options` for select |
| `CDataGridRow` | unique nonempty `key`; exact string-keyed Cell mapping for every Column; `disabled`; allowed Row `attrs` |
| `CDataGridCell` | escaped or component-like `value`; allowed Cell `attrs`; optional per-Cell `editable` override |
| `CDataGridEditOption` | unique nonempty string `value`; nonempty application-localized `label`; `disabled` |
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
| `onCellEditStart` | function | none | diagnose, retain | receives entry into an owned editor |
| `onCellEditCommit` | function | none | diagnose, retain | receives a changed typed value; synchronous `False` rejects |
| `onCellEditCancel` | function | none | diagnose, retain | receives Escape or disabled cancellation |

Server and valid client models remain isolated per instance. Sort is
request/accept. When a complete collection accepts the exact model requested by
a Header action, the browser orders Rows by normalized rendered Cell text with
an `Intl.Collator` configured for the active locale, numeric comparison, and
base sensitivity. Sort entries compare in model priority order and server DOM
order breaks ties. Initial or unrelated programmatic models retain the
server-authored Row order. A partial server window never sorts only its loaded
subset; its owner replaces the range. Selection is uncontrolled unless a
non-null client `selected` is supplied.

## 5. State model

`state=loading` or `error` replaces supplied ready rows with one spanning
state row, sets `aria-busy` only for loading, and disables navigation and
selection. Ready with zero logical rows is empty. A ready window whose desired
range is outside the supplied range sets `data-pending` and `aria-busy=true`
while retaining current rows.

Sort activation cycles `none → asc → desc → none`. Without Shift, the request
contains only the activated column. With Shift and `multi_sort=True`, it
updates that column in the ordered existing model. Accepting that exact request
reorders complete supplied Rows and rewrites their visual/ARIA Row positions;
clearing the model restores server order. Locale changes repeat a locally
accepted comparison. Server windows wait for authoritative replacement.

Selection modes:

- `none`: no selection behavior or `aria-selected` rows;
- `single`: one enabled row or none;
- `multiple`: independent toggles plus loaded-range Shift selection.

In multiple mode, primary-mouse drag is also a loaded-range gesture. Starting
on an unselected Row adds every enabled supplied Row crossed by the drag;
starting on a selected Row removes that range. Pointer capture keeps the
gesture coherent, the trailing click is suppressed, and disabled Rows are
skipped. Touch and pen input keep native viewport scrolling in this first pass.
Shift+Space is an independent keyboard toggle: it selects an unselected focused
Row and unselects a selected focused Row.

Disabled rows cannot be selected or activated. Disabled grid state blocks all
owned interactions but retains current selection and readable content.

Each editable Cell resolves its editor from the Column and an optional Cell
eligibility override. Text and select values are strings, number values are
finite Python integers or floats and become browser numbers, and checkbox
values are booleans. Select values must match one named option. Checked
`editor_attrs` support ordinary native constraints without allowing identity,
events, form ownership, or runtime markers.

Only one Cell edits at a time. Enter, F2, double-click, a printable key, Delete,
or Backspace starts an applicable editor. Enter or F2 submits, Escape cancels,
Tab submits and moves to the adjacent Cell, and an outside pointer submits.
Arrow keys belong to the native editor while editing. A synchronous `False`
from `onCellEditCommit` or a callback exception marks the editor invalid and
keeps it open. A valid commit closes the editor and reports a typed string,
number, or boolean, but never rewrites the Row. A server rerender is the only
acceptance path for application data.

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
Header and cell slot output must not contain caller-authored focusable or
editable descendants. Client initialization rejects them because the grid
must distinguish navigation mode from its one runtime-owned editor.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger and timing |
|---|---|---|
| `onSortChange` | `(sort, detail)` | request-only after sortable header click or Enter |
| `onSelectionChange` | `(selected, detail)` | after click, Shift range, Shift+Space, or mouse-drag uncontrolled commit; before controlled acceptance |
| `onRangeChange` | `(detail)` | animation-frame-coalesced uncovered desired range |
| `onCellActivate` | `(detail)` | Enter or double-click on an enabled noneditable body Cell |
| `onCellEditStart` | `(detail)` | an editable Cell enters edit mode |
| `onCellEditCommit` | `(value, detail)` | a valid changed value is submitted; `False` rejects and keeps editing |
| `onCellEditCancel` | `(detail)` | Escape or reactive disabling restores server Cell content |

Details include stable row/column keys, previous values, source, controlled
flag, source event, and monotonic request ID where applicable. Failures are
isolated and logged. No custom DOM events or public imperative methods ship.
Edit commits are request-only. The grid closes a valid accepted editor but
does not mutate the server-authored Row value. The owner applies the callback
value and rerenders. Native pointer, keydown, focus, and scroll events remain available through
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
| multiple selection cell | primary-mouse drag | add or remove the crossed loaded enabled range according to the starting Row state |
| editable body Cell | Enter / F2 / double-click | replace view content with its owned native editor |
| editable text/number Cell | printable key / Backspace / Delete | enter editing with the typed character or cleared value |
| active editor | Enter / F2 | submit a valid value and restore Grid navigation |
| active editor | Escape | cancel and restore server-rendered content |
| active editor | Tab / Shift+Tab | submit and move to the adjacent rendered Cell |
| enabled noneditable body Cell | Enter/double-click | Cell activation callback |
| grid | Tab / Shift+Tab | enter at retained active cell, then leave composite |

When a requested range is not supplied, focus stays on the nearest retained
cell until the next server render. A new window restores the desired logical
row and column when present. The status region announces accepted sorting and
selection changes. Manual screen-reader evidence remains required because
virtualized ARIA grids are high risk.

## 9. Native forms and validation

The family is not a form control. Row selection and edit drafts are application state and do
not submit hidden inputs, claim required validity, or intercept form reset.
Applications that submit selected keys create their own inputs or controlled
form field. Runtime editors have no `name` or `form`; the owner decides whether
an accepted callback becomes form state. Slots cannot contain form controls.

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
`header`, `header-row`, `header-cell`, `sort-indicator`, `body`, `row`, `cell`, `editor`,
`spacer-row`, `state-row`, `loading`, `empty`, `error`, and `status`.

Public reflected attributes are `data-state`, `data-density`, `data-striped`,
`data-column-borders`, `data-sticky-header`, `data-selection`, `data-disabled`,
`data-pending`, `data-selecting`, `data-editable`, `data-editing`, `data-editor`, `data-selected`, `data-row-key`, `data-column-key`,
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
announcements use Citry UI messages. Accepted complete-collection sorting uses
the active client locale and numeric collation; applications needing domain
ordering settle the request with a server render instead.

## 12. Overlay and layering behavior

The family creates no overlay, column menu, tooltip, or top-layer surface.
An active editor stays inside its Cell. Applications place external filters
and actions in the toolbar slot.

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
activation, delegated keydown, click, double-click, focus, pointer, and scroll
paths own interaction. An editor is created only for an active edit and its
server-rendered child nodes are retained for exact cancellation. Repeated
initialization is idempotent.

A compatible replacement retains scroll position, active logical row/column,
uncontrolled selection for surviving keys, and pending desired range. Active
editing is cancelled before replacement because Row data remains authoritative.
A hard replacement starts from server inputs. Cleanup cancels animation frames and
timers, restores retained Cell nodes, releases any pointer-selection state, removes listeners/effects/markers, and prevents callbacks after
removal.

## 15. Security and content trust

Labels and values use ordinary escaped Citry output. Slot output is trusted
component composition but is checked for unsupported focusable descendants.
No `innerHTML`, eval, URL parsing, clipboard, or remote fetch occurs. Editors
are created with DOM APIs. Select option labels use `textContent`, and
editor attributes pass a kind-specific allowlist. Attribute maps reject owned semantics, identity,
runtime markers, event directives, and dynamic bindings to owned targets.

## 16. Assets and performance

The family adds one CSS asset and one component JavaScript asset. Runtime work
is linear in supplied rows times columns. One instance owns delegated event
listeners, one document pointer listener, at most one resize observer for
viewport geometry, one pending animation frame, and at most one native editor.
It never clones Cell content. Fixed windowing bounds row DOM;
column virtualization is deferred because it complicates keyboard and browser
find behavior.

Do not raise package asset ceilings for this family in isolation. Measure raw,
gzip, and Brotli deltas and report them in batch reconciliation. The approved
six-family plus Data Grid editing expansion rebaselines the complete-catalog
ceiling once, in proportion to the catalog growth; narrow route budgets do not
change.

## 17. Acceptance matrix

| Area | Required evidence |
|---|---|
| schema/render | exact records, keys, mappings, positions, complete/windowed geometry, states, attrs ownership |
| keyboard/focus | all APG navigation keys, one Tab stop, sort activation, Shift+Space select and unselect, mouse drag add and remove ranges, edit entry/commit/cancel/Tab transitions, disabled rows, focus after range replacement |
| models | sort request/rejection/acceptance, complete Row reorder and clear restore, multi-sort priority, window non-reorder, controlled selection rejection/acceptance, uncontrolled commit, invalid clients |
| async/window | desired ranges, pending state, request coalescing/IDs, edge clamping, cleanup |
| editing | text, number, checkbox, select options, Cell override, native constraints, synchronous rejection, callback failure, request-only Row ownership, outside pointer, cleanup |
| i18n | all default/override paths, sort/selection/edit announcements, live locale switching, no binding on caller text or option labels |
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
selection; controlled models; server windowing; inline editing;
keyboard/accessibility; states; customization; and deferred filtering. Planned snippets are
`at_a_glance.py`, `sorting_selection.py`, `controlled.py`, `windowed.py`,
`editing.py`, `states.py`, `accessibility.py`, and `customization.py`.

The static window preview uses one self-contained range with no omitted leading
or trailing Rows. Partial-range spacer and replacement behavior remains covered
by browser tests, where the test owner can observe and settle requests.

The structured API ends with Translation keys and lists every family key.
The quality scenario covers ready, selection, sorting, complete/windowed,
loading, empty, error, narrow, RTL, long content, and cleanup.

## 20. Open decisions and deferred work

Row editing, arbitrary custom editors or focusable Cell widgets, async
validation, built-in filters, pagination
footer, remote all-selection, resize/reorder/pin/hide columns, grouping,
aggregation, pivoting, row details/tree data, export, clipboard mutation, and
column virtualization are deferred. Each changes focus, data, async, or
selection ownership and requires its own evidence. None blocks the first pass.

## 21. Internationalization

`CDataGrid.I18n.messages_locale` is `en-US`. The final class member owns
loading, empty, error, sorting, selection, editor naming, edit entry,
submission, cancellation, and invalid-value messages. Initial state DOM uses
server `tr()`. Stable state text uses `$c-tr`; browser sort and selection
announcements and runtime editor names use one-shot `i18n.tr()` with
application-localized Column labels and string counts. Explicit label
overrides remain caller-owned and do not
register catalog bindings. After an accepted complete-collection Header
request, the grid compares rendered Cell text with locale-aware numeric
collation. It still does not parse or format application values, and it never
sorts an incomplete server window.
