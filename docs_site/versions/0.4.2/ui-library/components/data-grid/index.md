---
title: Data Grid
url: https://citry.dev/v/0.4.2/ui-library/components/data-grid/
description: "Navigate, sort, select, and server-window tabular application data with Citry UI."
---
# Data Grid

Use `CDataGrid` for application data that benefits from one composite Tab
stop, cell navigation, row selection, server-owned sorting, or fixed-height
server windowing. Use `CTable` instead for document-like tables, ordinary
links and controls in cells, spans, footers, and print-first reading.

## Build a complete grid

Columns and rows are immutable Python records. Every Row supplies exactly one
Cell value for every Column key, and every key is a stable nonempty string.


### Navigate a complete Data Grid

[Open the rendered preview](/v/0.4.2/ui-library/components/data-grid/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow

citry.register_library(citry_ui)


class DataGridAtAGlance(Component):
    template = """
      <c-CDataGrid c-columns="columns" c-rows="rows" label="Project members" striped>
        <c-fill name="caption">Current project members</c-fill>
      </c-CDataGrid>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "columns": (
                CDataGridColumn("name", "Name", width=190),
                CDataGridColumn("role", "Role", width=180),
                CDataGridColumn("status", "Status", width=130),
            ),
            "rows": (
                CDataGridRow("ada", {"name": "Ada Lovelace", "role": "Engineer", "status": "Active"}),
                CDataGridRow("grace", {"name": "Grace Hopper", "role": "Admiral", "status": "Active"}),
                CDataGridRow("katherine", {"name": "Katherine Johnson", "role": "Mathematician", "status": "Away"}),
            ),
        }


preview = DataGridAtAGlance()
preview  # noqa: B018
````


The server output is a native table with exact row and column positions. Once
enhanced, one Header or Cell is in the page Tab order. Arrow keys move between
rendered Cells; Home, End, Page Up, Page Down, Ctrl/Cmd+Home, and Ctrl/Cmd+End
provide larger movement.

## Request sorting and select rows

Set `sortable=True` on Columns that can be sorted. Header activation cycles
ascending, descending, then unsorted. The grid never reorders application
Rows itself: `onSortChange` receives a request, and accepted `sort` state must
come back from the owner. Shift preserves other Columns when `multi_sort=True`.


### Sort and select people

[Open the rendered preview](/v/0.4.2/ui-library/components/data-grid/_previews/sorting-selection/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow, CDataGridSort

citry.register_library(citry_ui)


class DataGridSortingSelection(Component):
    template = """
      <section x-data="{sort:[{key:'name',direction:'asc'}],notice:'Activate a sortable header or select a row'}">
        <output x-text="notice">Activate a sortable header or select a row</output>
        <c-CDataGrid
          c-columns="columns"
          c-rows="rows"
          c-sort="sort"
          label="Sortable people"
          selection="multiple"
          c-selected="['grace']"
          $c-props="{
            sort,
            onSortChange:(next,detail)=>{
              sort=next;
              notice=`Accepted sort: ${detail.columnKey} ${detail.direction ?? 'none'}`;
            },
            onSelectionChange:(selected)=>notice=`Selected: ${selected.join(', ') || 'none'}`,
          }"
        />
      </section>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "columns": (
                CDataGridColumn("name", "Name", sortable=True, width=190),
                CDataGridColumn("team", "Team", sortable=True, width=150),
                CDataGridColumn("score", "Score", sortable=True, width=100, align="end"),
            ),
            "rows": (
                CDataGridRow("ada", {"name": "Ada Lovelace", "team": "Platform", "score": 98}),
                CDataGridRow("grace", {"name": "Grace Hopper", "team": "Compiler", "score": 95}),
                CDataGridRow("lin", {"name": "Lin Clark", "team": "Runtime", "score": 91}),
            ),
            "sort": (CDataGridSort("name", "asc"),),
        }


preview = DataGridSortingSelection()
preview  # noqa: B018
````


`selection="single"` or `selection="multiple"` enables Row selection.
Uncontrolled selection commits immediately. A non-null client `selected`
array makes selection controlled, so the visible state waits for acceptance.

## Control models from Alpine

Pass `sort`, `selected`, and callbacks through `$c-props`. Invalid client
models are diagnosed and the last valid state remains active.


### Control Data Grid models

[Open the rendered preview](/v/0.4.2/ui-library/components/data-grid/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow

citry.register_library(citry_ui)


class ControlledDataGrid(Component):
    template = """
      <section x-data="{sort:[],selected:['ada']}">
        <button type="button" @click="selected=[]">Clear selection</button>
        <c-CDataGrid
          c-columns="columns"
          c-rows="rows"
          label="Controlled members"
          selection="multiple"
          $c-props="{
            sort,
            selected,
            onSortChange:(next)=>sort=next,
            onSelectionChange:(next)=>selected=next,
          }"
        />
      </section>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "columns": (
                CDataGridColumn("name", "Name", sortable=True, width=190),
                CDataGridColumn("role", "Role", sortable=True, width=170),
            ),
            "rows": (
                CDataGridRow("ada", {"name": "Ada Lovelace", "role": "Engineer"}),
                CDataGridRow("grace", {"name": "Grace Hopper", "role": "Admiral"}),
            ),
        }


preview = ControlledDataGrid()
preview  # noqa: B018
````


Sort is always request/accept because only the application understands its
data. Selection becomes uncontrolled again when client `selected` is omitted
or null. Accepted sort and selection changes are announced politely.

## Supply a server window

Set `total_count` and `start_index` when `rows` is one contiguous window of a
larger collection. `row_height` is fixed geometry. `onRangeChange` receives a
half-open desired range when scrolling, resizing, or navigation leaves the
supplied range.


### Request Data Grid windows

[Open the rendered preview](/v/0.4.2/ui-library/components/data-grid/_previews/windowed/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow

citry.register_library(citry_ui)


class WindowedDataGrid(Component):
    template = """
      <section x-data="{notice:'This preview shows the final server range'}">
        <output x-text="notice">This preview shows the final server range</output>
        <c-CDataGrid
          c-columns="columns"
          c-rows="rows"
          label="Audit records"
          c-total_count="36"
          c-start_index="20"
          c-row_height="44"
          c-initial_index="20"
          $c-props="{onRangeChange:(detail)=>notice=`Requested ${detail.startIndex}-${detail.endIndex - 1}`}"
        />
      </section>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "columns": (
                CDataGridColumn("number", "Record", width=120),
                CDataGridColumn("action", "Action", width=230),
                CDataGridColumn("actor", "Actor", width=160),
            ),
            "rows": tuple(
                CDataGridRow(
                    f"audit-{index}",
                    {"number": f"#{index + 1:05d}", "action": "Signed deployment record", "actor": "Release bot"},
                )
                for index in range(20, 36)
            ),
        }


preview = WindowedDataGrid()
preview  # noqa: B018
````


The component does not fetch. The owner handles supersession, retries,
offline state, and replacement. Keep Row keys stable across windows. This
first version does not select unloaded rows or expose a remote select-all
operation.

## Loading, empty, and error states

`state="loading"` and `state="error"` replace ready Rows with one spanning
state output. Ready with `total_count=0` becomes empty. Fill the corresponding
Slot for richer server content, or override the plain localized label.


### Render Data Grid states

[Open the rendered preview](/v/0.4.2/ui-library/components/data-grid/_previews/states/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow

citry.register_library(citry_ui)


class DataGridStates(Component):
    template = """
      <div class="grid-states">
        <c-CDataGrid c-columns="columns" c-rows="[]" label="Empty records" />
        <c-CDataGrid c-columns="columns" c-rows="rows" label="Loading records" state="loading" />
        <c-CDataGrid c-columns="columns" c-rows="rows" label="Failed records" state="error">
          <c-fill name="error"><strong>Records are unavailable.</strong> Try again from the toolbar.</c-fill>
        </c-CDataGrid>
      </div>
    """
    css = ":where(.grid-states){display:grid;gap:1rem}"

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "columns": (CDataGridColumn("name", "Name"), CDataGridColumn("status", "Status")),
            "rows": (CDataGridRow("placeholder", {"name": "Placeholder", "status": "Pending"}),),
        }


preview = DataGridStates()
preview  # noqa: B018
````


## Accessibility and Cell content

The family follows the ARIA data-grid interaction model. Header and Cell Slot
content cannot contain links, buttons, inputs, editable content, or another
Tab stop in this first version; focus remains on the Header or Cell. Use
`onCellActivate` for Enter and double-click activation.


### Use exact positions and disabled Rows

[Open the rendered preview](/v/0.4.2/ui-library/components/data-grid/_previews/accessibility/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow

citry.register_library(citry_ui)


class AccessibleDataGrid(Component):
    template = """
      <c-CDataGrid
        c-columns="columns"
        c-rows="rows"
        label="Deployment approvals"
        selection="multiple"
      >
        <c-fill name="caption">Use Arrow keys to move and Shift+Space to select an enabled Row.</c-fill>
      </c-CDataGrid>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "columns": (
                CDataGridColumn("change", "Change", width=240),
                CDataGridColumn("owner", "Owner", width=160),
                CDataGridColumn("status", "Approval status", width=160),
            ),
            "rows": (
                CDataGridRow("api", {"change": "API release", "owner": "Ada", "status": "Approved"}),
                CDataGridRow(
                    "locked",
                    {"change": "Security policy", "owner": "Grace", "status": "Locked"},
                    disabled=True,
                ),
                CDataGridRow("docs", {"change": "Guide update", "owner": "Lin", "status": "Review"}),
            ),
        }


preview = AccessibleDataGrid()
preview  # noqa: B018
````


Column labels and Cell values belong to the application and should already be
localized. State labels and browser announcements use the Citry UI catalog by
default. Explicit label overrides remain caller-owned and do not switch with
the client locale.

## Styling and scope boundaries

Use `density`, `striped`, `column_borders`, and `sticky_header` for common
presentation. Customize the root and native table separately with `attrs` and
`table_attrs`, or use the documented public variables and part selectors.


### Customize a Data Grid

[Open the rendered preview](/v/0.4.2/ui-library/components/data-grid/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow

citry.register_library(citry_ui)


class CustomizedDataGrid(Component):
    template = """
      <div class="custom-grid">
        <c-CDataGrid
          c-columns="columns"
          c-rows="rows"
          label="Compact metrics"
          density="compact"
          striped
          column_borders
          c-style="{
            '--cui-data-grid-radius':'1rem',
            '--cui-data-grid-selected-background':'color-mix(in srgb, #7c3aed 20%, Canvas)',
          }"
        />
      </div>
    """
    css = """
      :where(.custom-grid [data-citry-ui-part="header-cell"]) { text-transform:uppercase;letter-spacing:.04em; }
      :where(.custom-grid [data-column-key="value"]) { font-variant-numeric:tabular-nums; }
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "columns": (
                CDataGridColumn("metric", "Metric", width=220),
                CDataGridColumn("value", "Value", width=120, align="end"),
            ),
            "rows": (
                CDataGridRow("latency", {"metric": "P95 latency", "value": "128 ms"}),
                CDataGridRow("errors", {"metric": "Error rate", "value": "0.04%"}),
                CDataGridRow("uptime", {"metric": "Uptime", "value": "99.99%"}),
            ),
        }


preview = CustomizedDataGrid()
preview  # noqa: B018
````


Inline editing, arbitrary Cell widgets, built-in filtering, grouping,
aggregation, pivoting, tree Rows, pinning, reordering, resizing, clipboard
mutation, export, and browser-owned data sources are outside this first
family. Compose application controls around the grid instead.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CDataGrid server inputs

Server inputs are passed in a template through `<c-CDataGrid ... />` or in Python through
`CDataGrid(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="data-grid-input-cdata-grid-server-inputs-columns"></span>`columns` | `Sequence[CDataGridColumn]` | required | Defines the nonempty ordered structural Column schema. |
| <span id="data-grid-input-cdata-grid-server-inputs-rows"></span>`rows` | `Sequence[CDataGridRow]` | required | Supplies a complete collection or one contiguous server window. |
| <span id="data-grid-input-cdata-grid-server-inputs-label"></span>`label` | `str` | required | Supplies the required accessible grid name. |
| <span id="data-grid-input-cdata-grid-server-inputs-id"></span>`id` | `str | None` | generated | Sets root identity and bases stable Header Row and Cell IDs. |
| <span id="data-grid-input-cdata-grid-server-inputs-state"></span>`state` | `CDataGridState` ([`CDataGridState`](#data-grid-interface-state)) | `"ready"` | Selects ready loading or error output; zero ready Rows become empty. |
| <span id="data-grid-input-cdata-grid-server-inputs-sort"></span>`sort` | `Sequence[CDataGridSort]` | `"()"` | Supplies the server-authoritative ordered sort model. |
| <span id="data-grid-input-cdata-grid-server-inputs-multi-sort"></span>`multi_sort` | `bool` | `True` | Allows Shift-modified sort requests to preserve other Columns. |
| <span id="data-grid-input-cdata-grid-server-inputs-selection"></span>`selection` | `CDataGridSelection` ([`CDataGridSelection`](#data-grid-interface-selection)) | `"none"` | Selects no single or multiple supplied-Row selection. |
| <span id="data-grid-input-cdata-grid-server-inputs-selected"></span>`selected` | `Sequence[str]` | `"()"` | Supplies unique initially selected Row keys. |
| <span id="data-grid-input-cdata-grid-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Blocks sorting selection activation and navigation. |
| <span id="data-grid-input-cdata-grid-server-inputs-total-count"></span>`total_count` | `int | None` | `None` | Sets logical Row count; omission means the complete supplied collection. |
| <span id="data-grid-input-cdata-grid-server-inputs-start-index"></span>`start_index` | `int` | `0` | Sets the zero-based logical index of the first supplied Row. |
| <span id="data-grid-input-cdata-grid-server-inputs-row-height"></span>`row_height` | `int` | `48` | Sets the fixed Row stride in CSS pixels. |
| <span id="data-grid-input-cdata-grid-server-inputs-viewport-size"></span>`viewport_size` | `int` | `400` | Sets initial scroll-viewport block size in CSS pixels. |
| <span id="data-grid-input-cdata-grid-server-inputs-overscan"></span>`overscan` | `int` | `3` | Adds 0 through 100 Rows around each desired range. |
| <span id="data-grid-input-cdata-grid-server-inputs-initial-index"></span>`initial_index` | `int` | `0` | Performs one initial scroll to a clamped logical Row. |
| <span id="data-grid-input-cdata-grid-server-inputs-density"></span>`density` | `CDataGridDensity` ([`CDataGridDensity`](#data-grid-interface-density)) | `"comfortable"` | Selects compact comfortable or spacious Row presentation. |
| <span id="data-grid-input-cdata-grid-server-inputs-striped"></span>`striped` | `bool` | `False` | Adds alternate supplied-Row surfaces. |
| <span id="data-grid-input-cdata-grid-server-inputs-column-borders"></span>`column_borders` | `bool` | `False` | Shows boundaries between Columns. |
| <span id="data-grid-input-cdata-grid-server-inputs-sticky-header"></span>`sticky_header` | `bool` | `True` | Keeps Headers at the viewport block start. |
| <span id="data-grid-input-cdata-grid-server-inputs-loading-label"></span>`loading_label` | `str` | `"Loading data..."` | Overrides the localized loading state. |
| <span id="data-grid-input-cdata-grid-server-inputs-empty-label"></span>`empty_label` | `str` | `"No data."` | Overrides the localized empty state. |
| <span id="data-grid-input-cdata-grid-server-inputs-error-label"></span>`error_label` | `str` | `"Unable to load data."` | Overrides the localized error state. |
| <span id="data-grid-input-cdata-grid-server-inputs-sort-ascending-label"></span>`sort_ascending_label` | `str` | `"{column} sorted ascending"` | Overrides ascending-sort announcements and must retain column. |
| <span id="data-grid-input-cdata-grid-server-inputs-sort-descending-label"></span>`sort_descending_label` | `str` | `"{column} sorted descending"` | Overrides descending-sort announcements and must retain column. |
| <span id="data-grid-input-cdata-grid-server-inputs-sort-cleared-label"></span>`sort_cleared_label` | `str` | `"Sort cleared for {column}"` | Overrides cleared-sort announcements and must retain column. |
| <span id="data-grid-input-cdata-grid-server-inputs-selected-one-label"></span>`selected_one_label` | `str` | `"One row selected"` | Overrides the one-Row selection announcement. |
| <span id="data-grid-input-cdata-grid-server-inputs-selected-label"></span>`selected_label` | `str` | `"{count} rows selected"` | Overrides multi-Row selection announcements and must retain count. |
| <span id="data-grid-input-cdata-grid-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#data-grid-interface-class-value)) | `None` | Adds root classes. |
| <span id="data-grid-input-cdata-grid-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#data-grid-interface-style-value)) | `None` | Adds root styles merged with owned geometry variables. |
| <span id="data-grid-input-cdata-grid-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes without replacing state or runtime ownership. |
| <span id="data-grid-input-cdata-grid-server-inputs-table-attrs"></span>`table_attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed native table attributes without replacing Grid semantics or positions. |

</div>

#### CDataGrid client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CDataGrid />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="data-grid-input-cdata-grid-client-inputs-sort"></span>`sort` | `Array<{key: string, direction: "asc" | "desc"}> | null` | Uses the server sort model. | Controls accepted sort indicators while supplied. |
| <span id="data-grid-input-cdata-grid-client-inputs-selected"></span>`selected` | `string[] | null` | Omission or null releases control to committed selection. | Controls unique supplied-Row selection while supplied. |
| <span id="data-grid-input-cdata-grid-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server value. | Reactively disables owned interaction. |
| <span id="data-grid-input-cdata-grid-client-inputs-overscan"></span>`overscan` | `number` | Uses the server value. | Reactively changes desired range buffering. |
| <span id="data-grid-input-cdata-grid-client-inputs-on-sort-change"></span>`onSortChange` | `function` | Sort activation emits no callback. | Receives request-only sort changes. |
| <span id="data-grid-input-cdata-grid-client-inputs-on-selection-change"></span>`onSelectionChange` | `function` | Selection still commits when uncontrolled. | Receives selection requests or commits. |
| <span id="data-grid-input-cdata-grid-client-inputs-on-range-change"></span>`onRangeChange` | `function` | Uncovered ranges only reflect pending state. | Receives animation-frame-coalesced desired ranges. |
| <span id="data-grid-input-cdata-grid-client-inputs-on-cell-activate"></span>`onCellActivate` | `function` | Enter and double-click have no activation callback. | Receives enabled Cell activation. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CDataGrid slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="data-grid-slot-cdata-grid-slots-caption"></span>`caption` | no | `{}` ([`CDataGridCaptionSlotData`](#data-grid-interface-cdata-grid-caption-slot-data)) | Omitted. |
| <span id="data-grid-slot-cdata-grid-slots-toolbar"></span>`toolbar` | no | `{}` ([`CDataGridToolbarSlotData`](#data-grid-interface-cdata-grid-toolbar-slot-data)) | Omitted before the viewport. |
| <span id="data-grid-slot-cdata-grid-slots-header"></span>`header` | no | `{column, column_index, sort_direction, sort_priority}` ([`CDataGridHeaderSlotData`](#data-grid-interface-cdata-grid-header-slot-data)) | Escaped Column label plus owned sort indicator. |
| <span id="data-grid-slot-cdata-grid-slots-cell"></span>`cell` | no | `{row, column, cell, row_index, column_index, selected}` ([`CDataGridCellSlotData`](#data-grid-interface-cdata-grid-cell-slot-data)) | Escaped or component-like Cell value. |
| <span id="data-grid-slot-cdata-grid-slots-loading"></span>`loading` | no | `{}` ([`CDataGridLoadingSlotData`](#data-grid-interface-cdata-grid-loading-slot-data)) | Localized loading label. |
| <span id="data-grid-slot-cdata-grid-slots-empty"></span>`empty` | no | `{}` ([`CDataGridEmptySlotData`](#data-grid-interface-cdata-grid-empty-slot-data)) | Localized empty label. |
| <span id="data-grid-slot-cdata-grid-slots-error"></span>`error` | no | `{}` ([`CDataGridErrorSlotData`](#data-grid-interface-cdata-grid-error-slot-data)) | Localized error label. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CDataGrid events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="data-grid-event-cdata-grid-events-sort-change"></span>`onSortChange` | `(sort: sort[], detail: CDataGridSortChangeDetail) => void` ([`CDataGridSortChangeDetail`](#data-grid-interface-cdata-grid-sort-change-detail)) | Click or Enter activates an enabled sortable Header. | `{sort, previousSort, columnKey, direction, source, sourceEvent}` ([`CDataGridSortChangeDetail`](#data-grid-interface-cdata-grid-sort-change-detail)) | Always request-only; DOM Rows never reorder locally. |
| <span id="data-grid-event-cdata-grid-events-selection-change"></span>`onSelectionChange` | `(selected: string[], detail: CDataGridSelectionChangeDetail) => void` ([`CDataGridSelectionChangeDetail`](#data-grid-interface-cdata-grid-selection-change-detail)) | Pointer or Shift+Space requests a supplied-Row selection change. | `{selected, previousSelected, changed, rowKey, selectedRow, controlled, source, sourceEvent}` ([`CDataGridSelectionChangeDetail`](#data-grid-interface-cdata-grid-selection-change-detail)) | Uncontrolled state commits first; controlled state waits for acceptance. |
| <span id="data-grid-event-cdata-grid-events-range-change"></span>`onRangeChange` | `(detail: CDataGridRangeChangeDetail) => void` ([`CDataGridRangeChangeDetail`](#data-grid-interface-cdata-grid-range-change-detail)) | Scroll resize configuration or navigation exposes an uncovered desired range. | `{startIndex, endIndex, visibleStartIndex, visibleEndIndex, requestId, reason, sourceEvent}` ([`CDataGridRangeChangeDetail`](#data-grid-interface-cdata-grid-range-change-detail)) | Coalesced per animation frame with a monotonic request ID. |
| <span id="data-grid-event-cdata-grid-events-cell-activate"></span>`onCellActivate` | `(detail: CDataGridCellActivateDetail) => void` ([`CDataGridCellActivateDetail`](#data-grid-interface-cdata-grid-cell-activate-detail)) | Enter or double-click activates an enabled body Cell. | `{rowKey, columnKey, rowIndex, columnIndex, source, sourceEvent}` ([`CDataGridCellActivateDetail`](#data-grid-interface-cdata-grid-cell-activate-detail)) | Does not enter edit mode or mutate data. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CDataGrid CSS variables

Apply these variables to `CDataGrid` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="data-grid-css-cdata-grid-css-variables-viewport-size"></span>`--cui-data-grid-viewport-size` | `length` | Maximum scroll-viewport block size. | `Server viewport_size or 400px` |
| <span id="data-grid-css-cdata-grid-css-variables-row-height"></span>`--cui-data-grid-row-height` | `length` | Fixed ready-Row and Cell block size. | `Server row_height or 48px` |
| <span id="data-grid-css-cdata-grid-css-variables-min-width"></span>`--cui-data-grid-min-width` | `length` | Horizontal overflow threshold. | `Sum of Column widths` |
| <span id="data-grid-css-cdata-grid-css-variables-background"></span>`--cui-data-grid-background` | `color` | Grid surface. | `Canvas` |
| <span id="data-grid-css-cdata-grid-css-variables-foreground"></span>`--cui-data-grid-foreground` | `color` | Primary text. | `CanvasText` |
| <span id="data-grid-css-cdata-grid-css-variables-muted"></span>`--cui-data-grid-muted` | `color` | State and secondary text. | `Accessible CanvasText mix` |
| <span id="data-grid-css-cdata-grid-css-variables-border-color"></span>`--cui-data-grid-border-color` | `color` | Row Column and viewport borders. | `Adaptive neutral` |
| <span id="data-grid-css-cdata-grid-css-variables-header-background"></span>`--cui-data-grid-header-background` | `color` | Header surface. | `Adaptive neutral` |
| <span id="data-grid-css-cdata-grid-css-variables-selected-background"></span>`--cui-data-grid-selected-background` | `color` | Selected Row surface. | `Adaptive blue` |
| <span id="data-grid-css-cdata-grid-css-variables-striped-background"></span>`--cui-data-grid-striped-background` | `color` | Alternate Row surface. | `Subtle neutral` |
| <span id="data-grid-css-cdata-grid-css-variables-hover-background"></span>`--cui-data-grid-hover-background` | `color` | Pointer Row feedback. | `Subtle Highlight mix` |
| <span id="data-grid-css-cdata-grid-css-variables-focus-color"></span>`--cui-data-grid-focus-color` | `color` | Active Header and Cell outline. | `Highlight` |
| <span id="data-grid-css-cdata-grid-css-variables-radius"></span>`--cui-data-grid-radius` | `length` | Viewport corners. | `0.625rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CDataGrid attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="data-grid-attribute-cdata-grid-attributes-role-grid"></span>`role` | Native table | `grid` | Exposes one composite data grid. |
| <span id="data-grid-attribute-cdata-grid-attributes-aria-rowcount"></span>`aria-rowcount` | Native table | `integer` | Reports logical Rows plus the Header Row. |
| <span id="data-grid-attribute-cdata-grid-attributes-aria-colcount"></span>`aria-colcount` | Native table | `integer` | Reports logical Column count. |
| <span id="data-grid-attribute-cdata-grid-attributes-aria-rowindex"></span>`aria-rowindex` | Header and supplied Rows | `positive integer` | Reports exact one-based logical position. |
| <span id="data-grid-attribute-cdata-grid-attributes-aria-colindex"></span>`aria-colindex` | Headers and Cells | `positive integer` | Reports exact one-based Column position. |
| <span id="data-grid-attribute-cdata-grid-attributes-aria-sort"></span>`aria-sort` | Sorted Header | `ascending | descending | absent` | Reflects accepted sort direction. |
| <span id="data-grid-attribute-cdata-grid-attributes-aria-selected"></span>`aria-selected` | Supplied Row | `boolean-string | absent` | Reflects accepted selection when selection is enabled. |
| <span id="data-grid-attribute-cdata-grid-attributes-data-row-key"></span>`data-row-key` | Supplied Row and Cells | `string` | Exposes stable Row identity. |
| <span id="data-grid-attribute-cdata-grid-attributes-data-column-key"></span>`data-column-key` | Header and Cells | `string` | Exposes stable Column identity. |
| <span id="data-grid-attribute-cdata-grid-attributes-data-row-index"></span>`data-row-index` | Supplied Row and Cells | `nonnegative integer` | Exposes zero-based logical Row position for owned navigation. |
| <span id="data-grid-attribute-cdata-grid-attributes-data-column-index"></span>`data-column-index` | Header and Cells | `nonnegative integer` | Exposes zero-based Column position for owned navigation. |
| <span id="data-grid-attribute-cdata-grid-attributes-data-selected"></span>`data-selected` | Supplied Row | `present | absent` | Reflects accepted selection for styling. |
| <span id="data-grid-attribute-cdata-grid-attributes-data-pending"></span>`data-pending` | Root | `present | absent` | Marks a desired range outside the supplied window. |
| <span id="data-grid-attribute-cdata-grid-attributes-data-state"></span>`data-state` | Root | `ready | loading | empty | error` | Reflects settled server output state. |
| <span id="data-grid-attribute-cdata-grid-attributes-tabindex"></span>`tabindex` | Viewport Header or Cell | `0 | -1` | Maintains one composite page Tab stop. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CDataGrid selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="data-grid-selector-cdata-grid-selectors-data-grid"></span>`[data-citry-ui-part="data-grid"]` | Root div | State reflections attrs and theme destination. |
| <span id="data-grid-selector-cdata-grid-selectors-toolbar"></span>`[data-citry-ui-part="toolbar"]` | Optional toolbar wrapper | Application controls before the viewport. |
| <span id="data-grid-selector-cdata-grid-selectors-status"></span>`[data-citry-ui-part="status"]` | Visually hidden polite live region | Accepted sort and selection announcements. |
| <span id="data-grid-selector-cdata-grid-selectors-viewport"></span>`[data-citry-ui-part="viewport"]` | Scroll div | Horizontal and vertical scroll ownership. |
| <span id="data-grid-selector-cdata-grid-selectors-table"></span>`[data-citry-ui-part="table"]` | Native table Grid | Semantic and keyboard owner. |
| <span id="data-grid-selector-cdata-grid-selectors-caption"></span>`[data-citry-ui-part="caption"]` | Optional native caption | Supplementary visible description. |
| <span id="data-grid-selector-cdata-grid-selectors-header"></span>`[data-citry-ui-part="header"]` | thead | Header Row group. |
| <span id="data-grid-selector-cdata-grid-selectors-header-row"></span>`[data-citry-ui-part="header-row"]` | Header tr | Exact Header Row position. |
| <span id="data-grid-selector-cdata-grid-selectors-header-cell"></span>`[data-citry-ui-part="header-cell"]` | th | Navigable sortable Column Header. |
| <span id="data-grid-selector-cdata-grid-selectors-sort-indicator"></span>`[data-citry-ui-part="sort-indicator"]` | Decorative span | Accepted sort direction glyph. |
| <span id="data-grid-selector-cdata-grid-selectors-body"></span>`[data-citry-ui-part="body"]` | tbody | Supplied Rows spacers and state output. |
| <span id="data-grid-selector-cdata-grid-selectors-row"></span>`[data-citry-ui-part="row"]` | Supplied tr | Stable selection and Row customization. |
| <span id="data-grid-selector-cdata-grid-selectors-cell"></span>`[data-citry-ui-part="cell"]` | Supplied td | Navigable application Cell. |
| <span id="data-grid-selector-cdata-grid-selectors-loading"></span>`[data-citry-ui-part="loading"]` | Loading td | Localized loading output. |
| <span id="data-grid-selector-cdata-grid-selectors-empty"></span>`[data-citry-ui-part="empty"]` | Empty td | Localized empty output. |
| <span id="data-grid-selector-cdata-grid-selectors-error"></span>`[data-citry-ui-part="error"]` | Error td | Localized failure output. |
| <span id="data-grid-selector-cdata-grid-selectors-state-row"></span>`[data-citry-ui-part="state-row"]` | State tr | Loading empty or error output. |
| <span id="data-grid-selector-cdata-grid-selectors-spacer-row"></span>`[data-citry-ui-part="spacer-row"]` | Presentation tr | Represents omitted fixed-height Rows. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="data-grid-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="data-grid-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |
| <span id="data-grid-interface-state"></span>`CDataGridState` | `Literal["ready", "loading", "error"]` |
| <span id="data-grid-interface-density"></span>`CDataGridDensity` | `Literal["comfortable", "compact", "spacious"]` |
| <span id="data-grid-interface-selection"></span>`CDataGridSelection` | `Literal["none", "single", "multiple"]` |
| <span id="data-grid-interface-align"></span>`CDataGridAlign` | `Literal["start", "center", "end"]` |
| <span id="data-grid-interface-sort-direction"></span>`CDataGridSortDirection` | `Literal["asc", "desc"]` |
| <span id="data-grid-interface-sort-source"></span>`CDataGridSortSource` | `Literal["pointer", "keyboard", "client"]` |
| <span id="data-grid-interface-selection-source"></span>`CDataGridSelectionSource` | `Literal["pointer", "keyboard", "client"]` |
| <span id="data-grid-interface-range-reason"></span>`CDataGridRangeReason` | `Literal["initial", "scroll", "resize", "configuration", "navigation"]` |

</div>

<span id="data-grid-interface-cdata-grid-column"></span>

#### `CDataGridColumn`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="data-grid-interface-cdata-grid-column-key"></span>`key` | `str` | - | Unique stable Column identity and Row mapping key. |
| <span id="data-grid-interface-cdata-grid-column-label"></span>`label` | `str` | - | Application-localized accessible Header label. |
| <span id="data-grid-interface-cdata-grid-column-sortable"></span>`sortable` | `bool` | - | Whether Header activation can request sorting. |
| <span id="data-grid-interface-cdata-grid-column-width"></span>`width` | `int` | - | Initial 40 through 2000 CSS-pixel Column width. |
| <span id="data-grid-interface-cdata-grid-column-align"></span>`align` | `CDataGridAlign` ([`CDataGridAlign`](#data-grid-interface-align)) | - | Logical Cell text alignment. |
| <span id="data-grid-interface-cdata-grid-column-header-attrs"></span>`header_attrs` | `Mapping[str, object] | None` | - | Copied allowed Header attributes. |
| <span id="data-grid-interface-cdata-grid-column-cell-attrs"></span>`cell_attrs` | `Mapping[str, object] | None` | - | Copied allowed attributes merged into every Cell in the Column. |

</div>

<span id="data-grid-interface-cdata-grid-cell"></span>

#### `CDataGridCell`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="data-grid-interface-cdata-grid-cell-value"></span>`value` | `object` | - | Escaped or component-like server Cell output. |
| <span id="data-grid-interface-cdata-grid-cell-attrs"></span>`attrs` | `Mapping[str, object] | None` | - | Copied allowed attributes merged after Column Cell attributes. |

</div>

<span id="data-grid-interface-cdata-grid-row"></span>

#### `CDataGridRow`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="data-grid-interface-cdata-grid-row-key"></span>`key` | `str` | - | Unique stable supplied-Row identity. |
| <span id="data-grid-interface-cdata-grid-row-cells"></span>`cells` | `Mapping[str, object | CDataGridCell]` | - | Exact one-to-one mapping for every Column key. |
| <span id="data-grid-interface-cdata-grid-row-disabled"></span>`disabled` | `bool` | - | Blocks selection and activation for this Row. |
| <span id="data-grid-interface-cdata-grid-row-attrs"></span>`attrs` | `Mapping[str, object] | None` | - | Copied allowed Row attributes. |

</div>

<span id="data-grid-interface-cdata-grid-sort"></span>

#### `CDataGridSort`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="data-grid-interface-cdata-grid-sort-key"></span>`key` | `str` | - | Known sortable Column key. |
| <span id="data-grid-interface-cdata-grid-sort-direction"></span>`direction` | `CDataGridSortDirection` ([`CDataGridSortDirection`](#data-grid-interface-sort-direction)) | - | Accepted ascending or descending direction. |

</div>

<span id="data-grid-interface-cdata-grid-caption-slot-data"></span>

#### `CDataGridCaptionSlotData`

Empty dataclass: `{}`.

<span id="data-grid-interface-cdata-grid-toolbar-slot-data"></span>

#### `CDataGridToolbarSlotData`

Empty dataclass: `{}`.

<span id="data-grid-interface-cdata-grid-header-slot-data"></span>

#### `CDataGridHeaderSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="data-grid-interface-cdata-grid-header-slot-data-column"></span>`column` | `CDataGridColumn` | - | Current Column record. |
| <span id="data-grid-interface-cdata-grid-header-slot-data-column-index"></span>`column_index` | `int` | - | Zero-based Column position. |
| <span id="data-grid-interface-cdata-grid-header-slot-data-sort-direction"></span>`sort_direction` | `CDataGridSortDirection | None` | - | Accepted direction or none. |
| <span id="data-grid-interface-cdata-grid-header-slot-data-sort-priority"></span>`sort_priority` | `int | None` | - | One-based multi-sort priority or none. |

</div>

<span id="data-grid-interface-cdata-grid-cell-slot-data"></span>

#### `CDataGridCellSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="data-grid-interface-cdata-grid-cell-slot-data-row"></span>`row` | `CDataGridRow` | - | Current Row record. |
| <span id="data-grid-interface-cdata-grid-cell-slot-data-column"></span>`column` | `CDataGridColumn` | - | Current Column record. |
| <span id="data-grid-interface-cdata-grid-cell-slot-data-cell"></span>`cell` | `CDataGridCell` | - | Normalized Cell record. |
| <span id="data-grid-interface-cdata-grid-cell-slot-data-row-index"></span>`row_index` | `int` | - | Zero-based logical Row position. |
| <span id="data-grid-interface-cdata-grid-cell-slot-data-column-index"></span>`column_index` | `int` | - | Zero-based Column position. |
| <span id="data-grid-interface-cdata-grid-cell-slot-data-selected"></span>`selected` | `bool` | - | Initial accepted supplied-Row selection. |

</div>

<span id="data-grid-interface-cdata-grid-loading-slot-data"></span>

#### `CDataGridLoadingSlotData`

Empty dataclass: `{}`.

<span id="data-grid-interface-cdata-grid-empty-slot-data"></span>

#### `CDataGridEmptySlotData`

Empty dataclass: `{}`.

<span id="data-grid-interface-cdata-grid-error-slot-data"></span>

#### `CDataGridErrorSlotData`

Empty dataclass: `{}`.

<span id="data-grid-interface-cdata-grid-sort-change-detail"></span>

#### `CDataGridSortChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="data-grid-interface-cdata-grid-sort-change-detail-sort"></span>`sort` | `list[dict[str, str]]` | - | Requested ordered sort model. |
| <span id="data-grid-interface-cdata-grid-sort-change-detail-previous-sort"></span>`previousSort` | `list[dict[str, str]]` | - | Accepted model before the request. |
| <span id="data-grid-interface-cdata-grid-sort-change-detail-column-key"></span>`columnKey` | `str` | - | Activated Column key. |
| <span id="data-grid-interface-cdata-grid-sort-change-detail-direction"></span>`direction` | `CDataGridSortDirection | None` | - | Requested direction or none when cleared. |
| <span id="data-grid-interface-cdata-grid-sort-change-detail-source"></span>`source` | `CDataGridSortSource` | - | Pointer keyboard or client cause. |
| <span id="data-grid-interface-cdata-grid-sort-change-detail-source-event"></span>`sourceEvent` | `object | None` | - | Native source Event. |

</div>

<span id="data-grid-interface-cdata-grid-selection-change-detail"></span>

#### `CDataGridSelectionChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="data-grid-interface-cdata-grid-selection-change-detail-selected"></span>`selected` | `list[str]` | - | Requested or committed selected supplied-Row keys. |
| <span id="data-grid-interface-cdata-grid-selection-change-detail-previous-selected"></span>`previousSelected` | `list[str]` | - | Accepted selection before the request. |
| <span id="data-grid-interface-cdata-grid-selection-change-detail-changed"></span>`changed` | `list[str]` | - | Keys whose selection changed. |
| <span id="data-grid-interface-cdata-grid-selection-change-detail-row-key"></span>`rowKey` | `str | None` | - | Directly activated Row key. |
| <span id="data-grid-interface-cdata-grid-selection-change-detail-selected-row"></span>`selectedRow` | `bool | None` | - | Requested state of the directly activated Row. |
| <span id="data-grid-interface-cdata-grid-selection-change-detail-controlled"></span>`controlled` | `bool` | - | Whether client selected owns the model. |
| <span id="data-grid-interface-cdata-grid-selection-change-detail-source"></span>`source` | `CDataGridSelectionSource` | - | Pointer keyboard or client cause. |
| <span id="data-grid-interface-cdata-grid-selection-change-detail-source-event"></span>`sourceEvent` | `object | None` | - | Native source Event. |

</div>

<span id="data-grid-interface-cdata-grid-range-change-detail"></span>

#### `CDataGridRangeChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="data-grid-interface-cdata-grid-range-change-detail-start-index"></span>`startIndex` | `int` | - | Desired inclusive logical start. |
| <span id="data-grid-interface-cdata-grid-range-change-detail-end-index"></span>`endIndex` | `int` | - | Desired exclusive logical end. |
| <span id="data-grid-interface-cdata-grid-range-change-detail-visible-start-index"></span>`visibleStartIndex` | `int` | - | Estimated visible inclusive start. |
| <span id="data-grid-interface-cdata-grid-range-change-detail-visible-end-index"></span>`visibleEndIndex` | `int` | - | Estimated visible exclusive end. |
| <span id="data-grid-interface-cdata-grid-range-change-detail-request-id"></span>`requestId` | `int` | - | Monotonic instance-local request ID. |
| <span id="data-grid-interface-cdata-grid-range-change-detail-reason"></span>`reason` | `CDataGridRangeReason` | - | Initial scroll resize configuration or navigation cause. |
| <span id="data-grid-interface-cdata-grid-range-change-detail-source-event"></span>`sourceEvent` | `object | None` | - | Native source Event when available. |

</div>

<span id="data-grid-interface-cdata-grid-cell-activate-detail"></span>

#### `CDataGridCellActivateDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="data-grid-interface-cdata-grid-cell-activate-detail-row-key"></span>`rowKey` | `str` | - | Activated Row key. |
| <span id="data-grid-interface-cdata-grid-cell-activate-detail-column-key"></span>`columnKey` | `str` | - | Activated Column key. |
| <span id="data-grid-interface-cdata-grid-cell-activate-detail-row-index"></span>`rowIndex` | `int` | - | Zero-based logical Row position. |
| <span id="data-grid-interface-cdata-grid-cell-activate-detail-column-index"></span>`columnIndex` | `int` | - | Zero-based Column position. |
| <span id="data-grid-interface-cdata-grid-cell-activate-detail-source"></span>`source` | `keyboard | pointer` | - | Activation cause. |
| <span id="data-grid-interface-cdata-grid-cell-activate-detail-source-event"></span>`sourceEvent` | `object` | - | Native source Event. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CDataGrid translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="data-grid-translation-cdata-grid-translations-loading"></span>`citry-ui-data-grid-loading` | Labels the loading state. | `None.` | `loading_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="data-grid-translation-cdata-grid-translations-empty"></span>`citry-ui-data-grid-empty` | Labels the empty state. | `None.` | `empty_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="data-grid-translation-cdata-grid-translations-error"></span>`citry-ui-data-grid-error` | Labels the error state. | `None.` | `error_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="data-grid-translation-cdata-grid-translations-sort-ascending"></span>`citry-ui-data-grid-sort-ascending` | Announces accepted ascending sorting. | `column: str` | `sort_ascending_label` with `{column}` | One-shot `i18n.tr()` writes the live region after acceptance. |
| <span id="data-grid-translation-cdata-grid-translations-sort-descending"></span>`citry-ui-data-grid-sort-descending` | Announces accepted descending sorting. | `column: str` | `sort_descending_label` with `{column}` | One-shot `i18n.tr()` writes the live region after acceptance. |
| <span id="data-grid-translation-cdata-grid-translations-sort-cleared"></span>`citry-ui-data-grid-sort-cleared` | Announces accepted cleared sorting. | `column: str` | `sort_cleared_label` with `{column}` | One-shot `i18n.tr()` writes the live region after acceptance. |
| <span id="data-grid-translation-cdata-grid-translations-selected-one"></span>`citry-ui-data-grid-selected-one` | Announces one selected supplied Row. | `None.` | `selected_one_label` | One-shot `i18n.tr()` writes the live region after commit or acceptance. |
| <span id="data-grid-translation-cdata-grid-translations-selected"></span>`citry-ui-data-grid-selected` | Announces multiple selected supplied Rows. | `count: str` | `selected_label` with `{count}` | One-shot `i18n.tr()` writes the live region after commit or acceptance. |

</div>