# Citry UI Table specification

**Status (2026-08-06): production contract implemented. Structured reference,
nine public examples, focused server tests, and focused Chromium, Firefox, and
WebKit tests are complete. Hosted Phase 7.5 evidence plus human visual,
keyboard, assistive-technology, print, and real-device review remain.**
`CTable` is a styled native Table for finite, server-owned data. It is not an
interactive DataTable or ARIA grid.

## 1. Purpose and product bar

`CTable` presents related records with native row and column relationships. It
must be useful without component JavaScript, look complete without consumer
CSS, remain navigable with assistive technology, preserve keyed row subtrees
across server replacement, and stay usable at narrow widths and high zoom.

Production-complete means:

- output remains a native `table` with `caption`, `thead`, `tbody`, optional
  `tfoot`, column headers, and optional row headers;
- keys are unique and every ready row has exactly one cell per declared
  column;
- simple headers remain truthful, with one header row, no spans, and at most
  one row-header column;
- loading, empty, and error output never replaces table semantics with a grid
  or generic list;
- horizontal overflow, bounded sticky headers, page-sticky headers, nested
  Tables, controls in cells, print, RTL, light/dark, and forced colors have
  explicit behavior;
- styling is zero-JavaScript and scoped so an outer Table does not restyle a
  nested Table's internal rows and cells; and
- every public input, slot, record, variable, selector, and reflected
  attribute is documented and tested.

Common application jobs are first-class:

| Job | Shortest contract | Support path |
|---|---|---|
| Render related records | `CTable(columns=..., rows=...)` | direct API |
| Name the Table visibly | `slots={"caption": "..."}` | native caption slot |
| Mark entity names as row headers | `CTableColumn(..., row_header=True)` | direct column API |
| Align numeric values | `CTableColumn(..., align="end")` | direct column API |
| Apply one attribute to a whole column | `cell_attrs={...}` | direct column API |
| Add links, Buttons, badges, or controls | component-like cell value or `cell` slot | composition |
| Render totals | set column `footer` values or fill `footer` | direct footer API |
| Show loading, empty, or error output | `state` plus the matching slot or label | direct API |
| Compare densities and borders | `density`, `variant`, `striped`, `hover`, `column_borders` | direct visual API |
| Keep a wide Table usable | default `overflow="auto"` | direct responsive API |
| Keep headers visible in a bounded scroller | `sticky_header=True` plus root `max-block-size` through `style` | direct API plus CSS |
| Keep headers visible during page scroll | `sticky_header=True, overflow="visible"` | direct API |
| Set widths, wrapping, or tabular numerals | `header_attrs`, `cell_attrs`, `style`, classes, or public selectors | native attributes and CSS |
| Sort, filter, paginate, or select externally | compose controls, then render the next complete collection | composition |
| Build a spreadsheet-like experience | use a future DataTable/DataGrid | separate product |

Minimal template use:

```citry-html
<c-CTable
  c-columns="columns"
  c-rows="rows"
>
  <c-fill name="caption">
    Visible moons
  </c-fill>
</c-CTable>
```

Minimal Python composition:

```python
from citry_ui import CTable, CTableColumn, CTableRow

moon_table = CTable(
    columns=(
        CTableColumn("moon", "Moon", row_header=True),
        CTableColumn("planet", "Planet"),
    ),
    rows=(
        CTableRow("europa", {"moon": "Europa", "planet": "Jupiter"}),
    ),
    slots={"caption": "Visible moons"},
)
```

Sorting, filtering, pagination, row selection, editing, resizable or pinned
columns, grouped headers, spans, trees, virtualization, and remote collection
protocols are not `CTable` features. A headless Table is parked until real
application evidence establishes a useful contract.

## 2. Prior art and complaints

The family was re-audited from its runtime, server and browser tests, quality
scenario, structured API, public guide, scaling fixture, and composed uses.
Existing behavior remained provisional wherever those artifacts disagreed.

### Source record

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Citry UI prototype | 2026-08-06 | `ctable.py`, focused tests, `table.states`, `api.md`, `api.yml`, and scaling fixture | Keep native zero-JavaScript output, strict keyed rows, slots, status states, responsive wrapper, and token model. Add footer, cell defaults, nested scoping, scroll naming, and truthful evidence. |
| HTML and WAI | reviewed 2026-08-06 | [HTML tables](https://html.spec.whatwg.org/multipage/tables.html), [WAI table tutorial](https://www.w3.org/WAI/tutorials/tables/), and [MDN table accessibility](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Structuring_content/Table_accessibility) | Use native sections, caption, `th`, `td`, and `scope`. Defer complex header relationships until a logical-grid model exists. |
| WCAG and W3C Design System | reviewed 2026-08-06 | [Reflow understanding](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html), [scrollable region rule](https://www.w3.org/WAI/standards-guidelines/act/rules/0ssw9k/), and [labelled Table scroller example](https://design-system.w3.org/styles/tables.html) | Keep two-dimensional data horizontally scrollable; make named scroll regions possible and focus-visible. |
| WAI-ARIA and MDN | reviewed 2026-08-06 | [`aria-busy`](https://www.w3.org/TR/wai-aria/#aria-busy) and [live regions](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions) | Keep state cells semantic and place a persistent polite announcer outside the busy table. Manual AT evidence remains required. |
| Vuetify | 4.1.7 source reviewed 2026-08-06 | [`VTable.tsx`](https://raw.githubusercontent.com/vuetifyjs/vuetify/v4.1.7/packages/vuetify/src/components/VTable/VTable.tsx), [`VTable.sass`](https://raw.githubusercontent.com/vuetifyjs/vuetify/v4.1.7/packages/vuetify/src/components/VTable/VTable.sass), [`VDataTable.tsx`](https://raw.githubusercontent.com/vuetifyjs/vuetify/v4.1.7/packages/vuetify/src/components/VDataTable/VDataTable.tsx), and [types](https://raw.githubusercontent.com/vuetifyjs/vuetify/v4.1.7/packages/vuetify/src/components/VDataTable/types.ts) | Treat `VTable` as the closest styled reference and `VDataTable` as boundary evidence. Confirm density, fixed headers and footers, height, hover, stripes, gridlines, slots, and advanced collection exclusions. |
| Material UI | current docs reviewed 2026-08-06 | [Table guide](https://mui.com/material-ui/react-table/) and [Table API](https://mui.com/material-ui/api/table/) | Confirm native compound sections, footer, size, sticky header, horizontal container, and separate composition for sort, pagination, selection, and collapse. |
| Mantine | current docs reviewed 2026-08-06 | [Table](https://mantine.dev/core/table/) and [sticky-border fix](https://github.com/mantinedev/mantine/pull/8778) | Confirm data shorthand, footer, sticky offset, caption side, borders, stripes, hover, spacing, scroll container, and tabular numerals. Avoid collapsed-border sticky artifacts. |
| Chakra | current docs/source reviewed 2026-08-06 | [Table](https://chakra-ui.com/docs/components/table), [recipe source](https://github.com/chakra-ui/chakra-ui/blob/main/packages/react/src/theme/recipes/table.ts), and [performance report #10878](https://github.com/chakra-ui/chakra-ui/issues/10878) | Confirm semantic parts, sizes, line/outline, stripes, column borders, sticky header, colgroup, and the value of native static styling without per-cell runtime work. |
| Bootstrap | 5.3 docs reviewed 2026-08-06 | [Tables](https://getbootstrap.com/docs/5.3/content/tables/) | Confirm durable visual options, captions, footers, responsive wrappers, direct-child nested-table isolation, color caveats, and documented overlay clipping. |
| React Aria | current docs reviewed 2026-08-06 | [Table](https://react-aria.adobe.com/Table) | Treat selection, directional navigation, sorting, resizing, drag/drop, hierarchy, virtualization, and async loading as a separate interactive grid model. |
| Failure reports | status reviewed 2026-08-06 | [Vuetify #18854](https://github.com/vuetifyjs/vuetify/issues/18854), [Vuetify #18901](https://github.com/vuetifyjs/vuetify/issues/18901), Mantine #8778, and Chakra #10878 | Record whole-section slot ambiguity, header-schema friction, sticky-border artifacts, and per-cell styling cost as explicit failure modes. Historical resolved reports are evidence, not claims about current defects. |

Common shortcomings informed the contract:

- a semantic Table becomes hard to learn and type when it absorbs DataGrid
  behavior;
- whole `thead` or `tbody` replacement slots create unclear precedence and
  can bypass structural validation;
- sticky headers fail when scroll ancestry and vertical bounds are implicit;
- responsive overflow can clip inline menus and listboxes;
- per-cell runtime styling multiplies cost across the complete matrix;
- outer Table selectors can leak stripes, borders, density, and hover into a
  nested Table; and
- contextual colors can become the only signal and often lag dark-mode work.

Citry adopts a small explicit schema, native sections, one generic header and
cell slot, an owned one-row footer, direct-child CSS, zero component JavaScript,
and external advanced controls. It rejects whole-section replacement, implicit
DataGrid behavior, responsive card transforms, and arbitrary spans.

Vuetify carries roughly 30 percent of comparative decision weight:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| native Table structure | direct API | `CTable`, `CTableColumn`, `CTableRow`, `CTableCell` | adopt with a validated data shorthand |
| density | direct API | `density` | adopt consistent Citry density vocabulary |
| hover and stripes | direct API | `hover`, `striped` | adopt without implying selection |
| gridlines | direct API | `variant`, `column_borders` | adopt line/outline and optional column separators |
| fixed header | direct API plus CSS | `sticky_header`, `overflow`, `style` | adopt both bounded-scroller and page-scroll modes |
| fixed footer | public selector/CSS | `footer` part plus `style` | make achievable without a first-class Boolean until call-site demand exists |
| height | CSS or utility classes | `style={"max-block-size": ...}` | support without a dedicated dimension input |
| caption | named slot | `caption` | adopt native caption |
| top, bottom, wrapper slots | composition | content before or after `CTable` | omit anatomy replacement slots |
| theme, class, style | theme and direct root inputs | variables, selectors, `class_`, `style` | adopt |
| sorting and filtering | separate controls | next complete `columns` and `rows` render | omit from semantic Table |
| pagination | composition or later recipe | external paginator | omit from semantic Table |
| selection and expansion | separate DataTable | none | omit because behavior and keyboard model change |
| grouped headers, widths, fixed columns | later logical-grid schema or CSS | attributes/styles for simple widths only | defer grouped structure and fixed-column state |
| keyed header/item slots | later dynamic slot protocol | generic `header`, `cell`, `footer` | defer namespaced slots until Citry can type and validate them |
| loading and no-data output | named slots | `loading`, `empty`, `error` | adopt and add explicit error output |
| virtualization | separate DataTable/DataGrid | none | omit |

## 3. Public composition and anatomy

```citry-html
<c-CTable
  c-columns="columns"
  c-rows="moons"
  striped
  hover
>
  <c-fill name="caption">
    Moons by orbital period
  </c-fill>
  <c-fill name="cell" data="{ row, column, cell }">
    <c-if cond="column.key == 'actions'">
      <c-CButton size="sm">
        Inspect {{ row.key }}
      </c-CButton>
    </c-if>
    <c-else>
      {{ cell.value }}
    </c-else>
  </c-fill>
</c-CTable>
```

```python
table = CTable(
    columns=(
        CTableColumn("moon", "Moon", row_header=True, footer="Known moons"),
        CTableColumn("radius", "Radius", align="end", footer="4 records"),
    ),
    rows=(
        CTableRow("europa", {"moon": "Europa", "radius": "1,560.8 km"}),
    ),
    slots={"caption": "Selected moons"},
)
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CTable` | wrapper `<div>` containing one native `<table>` | `class_`, `style`, and `attrs` target the wrapper; `table_attrs` targets the table | one header row, one body, optional caption, optional one-row footer |

The stable native anatomy is wrapper, table, optional caption, one header group
and row, one body, and optional footer group and row. Ready body rows render one
cell per declared column. Loading, empty, and error output uses one spanning
body cell. Incidental private helpers, including the live announcer, are not
public parts.

`attrs` may add ordinary wrapper attributes. It cannot replace identity,
scroll-region semantics, reflected configuration, or public part markers.
`table_attrs` may add ordinary table and ARIA attributes but cannot replace
`aria-busy`, role, or the table part. Column, row, and cell mappings may add
safe native, ARIA, data, Alpine, class, and style attributes but cannot replace
scopes, spans, public identity, or part markers.

The anatomy review found no administrative child component to publish. The
Table owns the native structure, while records provide concise typed data.
Compound `CHeader`, `CBody`, or `CFooter` children would add writing and let
callers bypass the shape validator without adding expressivity.

## 4. Server inputs and client inputs

`CTableColumn` defines `key`, `label`, `row_header`, `align`, `header_attrs`,
`cell_attrs`, `footer`, and `footer_attrs`. Header attrs target its `th`.
Column cell attrs are defaults merged before a specific `CTableCell.attrs`, so
the specific cell wins while class and style contributions combine. Footer
attrs target the optional footer cell.

`CTableRow` defines a unique `key`, a `cells` mapping containing exactly every
column key, and optional row attrs. A raw value becomes `CTableCell(value)`.
`CTableCell` defines `value` and optional attrs. Record attribute mappings are
copied and validated during render so later caller mutation cannot bypass
validation.

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `columns` | sequence of `CTableColumn` | required | structural server-only | non-empty, unique keys, at most one row-header column |
| `rows` | sequence of `CTableRow` | required | structural server-only | unique keys and exact cell shape |
| `state` | `ready`, `loading`, or `error` | `ready` | structural server-only | selects body and announcement output |
| `id` | `str` or `None` | generated | structural server-only | wrapper and caption identity base |
| `variant` | `line` or `outline` | `line` | structural server-only | border presentation |
| `density` | `default`, `comfortable`, or `compact` | `comfortable` | structural server-only | cell geometry |
| `striped` | `bool` | `False` | structural server-only | alternating ready-row surface |
| `hover` | `bool` | `False` | structural server-only | pointer feedback without row behavior |
| `sticky_header` | `bool` | `False` | structural server-only | sticky header cells in the selected scroll mode |
| `column_borders` | `bool` | `False` | structural server-only | vertical separators |
| `layout` | `auto` or `fixed` | `auto` | structural server-only | native `table-layout` |
| `overflow` | `auto` or `visible` | `auto` | structural server-only | responsive scroll wrapper or page-flow mode |
| `caption_side` | `top` or `bottom` | `top` | structural server-only | native caption placement |
| `scroll_label` | non-empty `str` or `None` | caption or table ARIA name | structural server-only | names the auto-overflow region when supplied |
| `loading_label` | non-empty `str` | `Loading data...` | structural server-only | visual fallback and polite transition text |
| `empty_label` | non-empty `str` | `No data.` | structural server-only | visual fallback and polite transition text |
| `error_label` | non-empty `str` | `Unable to load data.` | structural server-only | visual fallback and polite transition text |
| `class_` | Citry class value or `None` | `None` | structural server-only | wrapper classes |
| `style` | Citry style value or `None` | `None` | structural server-only | wrapper inline styles, including optional scroll bounds |
| `attrs` | mapping or `None` | `None` | structural server-only | allowed wrapper attributes |
| `table_attrs` | mapping or `None` | `None` | structural server-only | allowed native table and ARIA attributes |

`CTable` has no client inputs. Every input takes effect on the next server
render. This is intentional: the component owns no browser state. Controls
inside cells keep their own client props, callbacks, and native events.

## 5. State model

| State | Header | Body | Footer | Busy | Persistent announcer text |
|---|---|---|---|---|---|
| ready with rows | visible | keyed rows | configured footer | false | empty |
| ready without rows | visible | empty slot | configured footer | false | `empty_label` |
| loading | visible | loading slot | hidden | true | `loading_label` |
| error | visible | error slot | hidden | false | `error_label` |

Entering loading, error, or empty replaces ready body rows rather than keeping
stale rows. The live announcer sits outside the busy native table, persists at
one stable location across morphs, and contains the configured state label.
Custom state slots change visible output; the matching label remains the
announcement text and must describe that output. Exact AT announcement timing
remains a manual qualification item.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CTable` | `caption` | no | once | empty `CTableCaptionSlotData` | no caption |
| `CTable` | `header` | no | once per column | `{column, column_index}` | escaped column label |
| `CTable` | `cell` | no | once per ready body cell | `{row, column, cell, row_index, column_index}` | escaped or component-like cell value |
| `CTable` | `footer` | no | once per footer column | `{column, value, column_index}` | escaped or component-like column footer value |
| `CTable` | `empty` | no | once in ready-empty | empty `CTableEmptySlotData` | `empty_label` |
| `CTable` | `loading` | no | once in loading | empty `CTableLoadingSlotData` | `loading_label` |
| `CTable` | `error` | no | once in error | empty `CTableErrorSlotData` | `error_label` |

Slots are server callbacks. Slot data is a typed attribute-access record and
may be destructured one level. A footer renders when the `footer` slot exists
or any column has a non-`None` footer. Generic slots retain complete structural
validation. Dynamic `header.<key>`, `cell.<key>`, and `footer.<key>` namespaces
remain deferred until Citry can validate, type, introspect, and render them.

## 7. Callbacks, native events, and methods

`CTable` emits no component-authored callback and exposes no public method.
Native events from links, Buttons, form controls, and other content inside
cells remain available through Alpine `@...` listeners. External sorting,
filtering, pagination, and selection controls own their notifications.

## 8. Semantics, keyboard, focus, and assistive technology

Column headers render `th scope="col"`. The optional row-header column renders
`th scope="row"` in body and footer; every other position uses `td`. A caption
provides the table's native accessible name. Without one, applications may use
`aria-label` or `aria-labelledby` through `table_attrs` when surrounding text
does not already identify the Table.

The Table has no arrow-key, selection, or row-activation model and never uses
`role="grid"`. Sequential focus includes controls supplied inside cells. With
`overflow="auto"`, the wrapper has `tabindex="0"` so WebKit and older browsers
can keyboard-scroll it. Zero JavaScript means Citry cannot add the tab stop only
after measuring actual overflow; the predictable extra stop is an accepted
tradeoff. Its focus ring must remain visible.

When auto overflow has a caption, the wrapper becomes a region labelled by the
caption. `scroll_label` overrides that region name. With no caption or explicit
scroll label, a non-empty table `aria-label` or `aria-labelledby` is reused. If
none exists, the wrapper remains focusable without adding an unnamed landmark.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| auto-overflow wrapper | Tab or Shift+Tab | enter or leave scroll container | wrapper or adjacent native focus target | no |
| focused auto-overflow wrapper | browser scrolling key or gesture | pan overflowing Table | wrapper remains focused | browser-native |
| control inside cell | native keyboard or pointer input | control-owned behavior | control-owned | control-owned |
| non-interactive row | click, Enter, arrows | no Table behavior | unchanged | no |

Hover is visual feedback only. It does not make rows focusable or imply
activation. Long and translated content may wrap. Numeric alignment uses
logical `end`, and applications can add `font-variant-numeric: tabular-nums`
through column attrs or public selectors.

## 9. Native forms and validation

The Table itself is not a form participant. Native controls and Citry UI form
components inside cells retain their own Form owner, name, validation, reset,
submission, disabled state, client props, Events behavior, and no-JavaScript
output. Table row replacement follows Citry's ordinary control-preservation
rules and never serializes cell content as Table state.

## 10. Styling and theme contract

`CTable` follows [`../ui_theme.md`](../ui_theme.md). It supports system light
and dark color schemes and keeps styling in the `citry-ui.theme` layer with
low-specificity selectors and private resolved variables.

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-table-background` | color | table surface | `Canvas` |
| `--cui-table-foreground` | color | primary text | `CanvasText` |
| `--cui-table-muted-foreground` | color | caption and subdued state text | muted `CanvasText` mix |
| `--cui-table-border-color` | color | row, outline, footer, and optional column borders | subtle `CanvasText` mix |
| `--cui-table-header-background` | color | header surface | subtle `CanvasText` and `Canvas` mix |
| `--cui-table-footer-background` | color | footer surface | subtle `CanvasText` and `Canvas` mix |
| `--cui-table-striped-background` | color | alternating ready-row surface | subtle `CanvasText` and `Canvas` mix |
| `--cui-table-hover-background` | color | ready-row pointer hover surface | subtle `Highlight` and `Canvas` mix |
| `--cui-table-error-foreground` | color | error state text | scheme-aware error color |
| `--cui-table-focus-color` | color | overflow-wrapper focus ring | `Highlight` |
| `--cui-table-radius` | length | outline and wrapper radius | `0.625rem` |
| `--cui-table-cell-block-padding` | length | logical block cell padding | density-derived |
| `--cui-table-cell-inline-padding` | length | logical inline cell padding | density-derived |
| `--cui-table-caption-padding` | CSS padding shorthand | caption spacing | `0.75rem 1rem` |
| `--cui-table-min-width` | length | width before horizontal overflow | `32rem` |
| `--cui-table-sticky-offset` | length | sticky header block offset | `0px` |

Public selectors cover `root`, `table`, `caption`, `header`, `header-row`,
`header-cell`, `body`, `row`, `cell`, `state-row`, `state-cell`, `loading`,
`empty`, `error`, `footer`, `footer-row`, and `footer-cell`. Direct-child
relationships scope Table-owned rules to the current Table. Public variables
may intentionally inherit into a nested Table, but the nested root resolves
its own density and variant fallbacks.

Public root reflected attributes are `data-state`, `data-variant`,
`data-density`, `data-striped`, `data-hover`, `data-sticky-header`,
`data-column-borders`, `data-layout`, `data-overflow`, and
`data-caption-side`. Ready rows expose the escaped application key through
`data-row-key`; header, body, and footer cells expose `data-column-key` and
`data-align`. These mirrors are styling and inspection contracts, not writable
inputs. Do not place secrets in row or column keys.

`.cui-*` classes and `--_cui-*` variables remain private. Contextual colors
are consumer CSS, not Table intents; visible text, icons, or accessible labels
must carry meaning independently of color.

## 11. Environmental behavior

Default colors work in light and dark scopes, including nested scopes. Logical
properties support RTL. Reduced motion has no effect because Table has no
animation. Forced colors preserves text, focus, and borders without depending
on stripe or hover color. Print removes overflow clipping and sticky
positioning and allows the native table to paginate.

At narrow widths and 400% zoom, surrounding content reflows while the Table
may scroll horizontally as a two-dimensional exception. `layout="fixed"`
plus explicit widths provides predictable truncation; `auto` preserves
intrinsic sizing. Long cells must wrap or scroll without expanding the page.

Library-authored visible strings are `loading_label`, `empty_label`, and
`error_label`. Locale selection and translation ownership remain separate
follow-up work.

## 12. Overlay and layering behavior

Table creates no overlay and owns no application stacking category. Sticky
header cells use a small local stacking order inside their scroll context.

`overflow="auto"` may clip an inline menu, Combobox popup, tooltip, or other
non-portaled overlay inside a cell. Use a top-layer or portaled overlay when its
component supports one, or choose `overflow="visible"` when page layout can
contain the Table. This limitation is public and appears in the guide.

## 13. Collections, async data, and identity

Column and row keys are canonical application identity, not display text or
array positions. Keys are unique and non-empty. Each ready row receives one
private Citry morph key and the public escaped `data-row-key`. Reordering keeps
surviving row subtrees; removal removes the complete subtree. Every row must
provide exactly the declared column keys. Missing and unknown keys fail the
render.

Table owns no request or browser collection. Applications own sorting,
filtering, pagination, pending work, cancellation, stale-result rejection,
retry, and selection, then render the next complete server collection. Loading
and error replace stale rows. Version 1 qualification covers ordinary finite
Tables at 10, 100, and 1,000 rows; virtualization is not claimed.

Grouped or multiple header rows, `rowspan`, `colspan`, `colgroup`, and tree
rows remain deferred. They require validating the complete logical grid and
its `scope`, `headers`, or group relationships rather than accepting isolated
cell flags.

## 14. Server render, morph, and cleanup

The complete server output is the product output. `CTable` has no client
initializer, listener, observer, timer, request, or cleanup resource. Events
replacement may insert, reorder, remove, or update keyed rows. Focus and
unsubmitted edits survive when Citry preserves the keyed row and control. If
their row is removed, focus follows Citry's general replacement policy rather
than moving to a guessed neighboring row.

The persistent live region stays at one root position across state changes.
Nested Tables have independent roots, state output, tokens, and keys. Fragment
insertion needs only the shared stylesheet; no family script activates.

## 15. Security and content trust

Labels, keys, fallback text, ordinary values, and slot text are escaped by
Citry. Component-like values and slot results own their own trust contract.
Attribute mappings are application-authored structure after validation and
copying. They cannot replace scope, span, role, owned identity, public part
markers, or reflected configuration.

Row and column keys enter public `data-*` attributes and are therefore visible
to browser code and inspectors. Do not use credentials, private identifiers,
or other secrets as keys. No Table data is interpolated into JavaScript or CSS
selectors by the library.

## 16. Assets and performance

`CTable` adds CSS and no JavaScript. Render work is linear in columns plus rows
times columns. The quality harness records stylesheet size and server render
and HTML output at 10, 100, and 1,000 rows. Those measurements catch obvious
regressions without treating microbenchmarks as the product bar.

Direct native elements and one static stylesheet avoid per-cell browser
initializers and runtime styling. Footer and state helpers add constant work.
The wheel contains runtime Python only; family docs, snippets, and tests remain
source-distribution support files.

## 17. Acceptance matrix

The required release matrix is broader than the evidence completed in this
family pass. Checked-in automated evidence currently covers:

- record and enum validation, one row-header limit, exact cell shape, duplicate
  keys, rejected spans, attribute snapshotting, and owned-attribute rejection;
- native caption, header, row-header, body, one-row footer, and state-cell
  semantics, including generic header, cell, footer, and state slots;
- escaped ordinary values, component-like body and footer values, and explicit
  key disclosure;
- row reorder, edit preservation, row removal, ready/loading/error/empty
  replacement, persistent live-region identity, and busy-state separation;
- caption-derived and explicit scroll naming, focus-visible auto overflow,
  bounded and page-sticky computed behavior, and nested Table CSS isolation;
- ancestor token and public selector overrides, density isolation, caption
  side, footer tokens, reflected configuration, and zero Table JavaScript;
- the nine public examples, structured API validation, docs build, static
  quality scenario, and serious or critical axe scan in Chromium; and
- focused Table rendering in Chromium, Firefox, and WebKit.

Repository infrastructure also provides diagnostic 10, 100, and 1,000-row
render records, visual candidates, Lighthouse, Nu HTML, wheel, asset, host,
and coexistence jobs. Those tools become accepted release evidence only after
their hosted runs and review; diagnostic scaling is not a performance gate.

Pending release qualification covers hostile attribute/content cases beyond
generic escaping, RTL and long-cell computed behavior, narrow and 200%/400%
zoom review, forced-colors and print output, touch panning, an actual clipped
cell overlay and escape path, approved visual candidates, and complete-page
HTML results.

Manual qualification covers keyboard scrolling, visible focus, visual
hierarchy, touch panning, VoiceOver/Safari and NVDA/Firefox table navigation,
live-state announcements, 400% zoom, real long translations, print output,
and overlays used inside an actual responsive Table.

## 18. Compatibility classification

Stable public API consists of component and record names, server-input
meanings, slots and exact data shapes, validation, public variables, selectors,
reflected and identity attributes, semantic sections, keyed replacement, and
script-free behavior. Exact colors, spacing, border widths, private helpers,
and undocumented classes may evolve.

Adding a client state machine, changing Table to `role="grid"`, removing native
sections, changing the meaning of row keys, or making advanced controls
Table-owned would be a product and behavior compatibility change, not a small
visual enhancement.

## 19. Public documentation contract

[`ctable/api.md`](../../../packages/py/citry_ui/citry_ui/components/ctable/api.md)
is the result-first guide. [`ctable/api.yml`](../../../packages/py/citry_ui/citry_ui/components/ctable/api.yml)
is the exhaustive structured reference appended by the docs builder.

The page uses one astronomy theme and this conceptual order:

| Section | Example | Contract exercised |
|---|---|---|
| At a glance | solar-system sampler | basic anatomy, line/outline, density, stripes, and state output |
| Build | moons of Jupiter | minimal template and Python composition, caption, row header, alignment |
| Present rich cells | observation catalog | component-like values, generic scoped cell slot, links, Buttons, badges, and cell attrs |
| Add totals | survey summary | footer values, footer slot, footer attrs, and semantics |
| Compare appearance | planetary measurements | variants, densities, borders, hover, and caption side in side-by-side output |
| Show state | deep-space survey | loading, empty, and error visual output plus state labels |
| Keep headers visible | exoplanet catalog | bounded and page-sticky modes, fixed layout, widths, and horizontal overflow |
| Theme | observatory palette | ancestor and root variables, selectors, and nested light/dark scopes |
| Environment | translated star names | long content, RTL, narrow width, nested Table isolation, and print guidance |

Table has no client inputs, so a configurator would either mutate documented
server state imperatively or swap hidden prerendered Tables. Side-by-side
examples teach server-only visual differences more truthfully. Source remains
collapsed by default, and every snippet exports one explicit `preview` value.

## 20. Open decisions and deferred work

- Dynamic keyed slots need a proven Citry parser, typing, validation, and
  introspection contract.
- Column groups, multiple header rows, spans, and `colgroup` need a validated
  logical-grid schema.
- Fixed footers may gain a concise input after real Tables prove repeated
  demand; the public footer selector and ordinary CSS provide the current path.
- Sort, filter, pagination, selection, expansion, and editable collection
  recipes need separate state and notification specifications.
- A top-layer or portal contract must exist before Table can promise that cell
  overlays escape auto-overflow clipping.
- Virtualized and spreadsheet-like DataTable/DataGrid behavior remains a
  specialist companion boundary.
- Human visual, keyboard, assistive-technology, print, and real-device review
  remain release evidence after automated qualification.
