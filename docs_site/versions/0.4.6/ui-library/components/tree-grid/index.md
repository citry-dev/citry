---
title: Tree Grid
url: https://citry.dev/v/0.4.6/ui-library/components/tree-grid/
description: "Navigate expandable and selectable hierarchical records in aligned columns."
---
# Tree Grid

`CTreeGrid` combines a finite Row hierarchy with Data Grid columns. It is for
account trees, threaded records, work breakdowns, and similar structured data,
not spreadsheet formulas or inline editing.


### Present an account hierarchy

[Open the rendered preview](/v/0.4.6/ui-library/components/tree-grid/_previews/at-a-glance/)

````citry
# ruff: noqa: ANN001, ANN201 - public snippets keep focus on component use

import citry_ui
from citry import Component, citry
from citry_ui import CTreeGridColumn, CTreeGridRow

citry.register_library(citry_ui)
COLUMNS = [CTreeGridColumn("name", "Account", width=240), CTreeGridColumn("owner", "Owner")]
ROWS = [
    CTreeGridRow(
        "north",
        "Northern region",
        {"name": "Northern region", "owner": "Ada"},
        children=[
            CTreeGridRow("prague", "Prague", {"name": "Prague", "owner": "Mira"}),
            CTreeGridRow("berlin", "Berlin", {"name": "Berlin", "owner": "Noah"}),
        ],
    )
]


class TreeGridAtAGlance(Component):
    def template_data(self, _kwargs, _slots):
        return {"columns": COLUMNS, "rows": ROWS}

    template = '<c-CTreeGrid c-columns="columns" c-rows="rows" label="Account hierarchy" c-expanded="[\'north\']" />'


preview = TreeGridAtAGlance()
preview  # noqa: B018
````


## Expand nested Rows

Put child `CTreeGridRow` records in `children` and list initially open branch
keys in `expanded`. The first Column owns indentation and expansion.


### Control visible project levels

[Open the rendered preview](/v/0.4.6/ui-library/components/tree-grid/_previews/expansion/)

````citry
# ruff: noqa: ANN001, ANN201 - public snippets keep focus on component use

import citry_ui
from citry import Component, citry
from citry_ui import CTreeGridColumn, CTreeGridRow

citry.register_library(citry_ui)


class TreeGridExpansion(Component):
    def template_data(self, _kwargs, _slots):
        return {
            "columns": [CTreeGridColumn("work", "Work item", 260), CTreeGridColumn("state", "State")],
            "rows": [
                CTreeGridRow(
                    "launch",
                    "Launch",
                    {"work": "Launch", "state": "Active"},
                    children=[
                        CTreeGridRow("design", "Design", {"work": "Design", "state": "Done"}),
                        CTreeGridRow("build", "Build", {"work": "Build", "state": "Active"}),
                    ],
                )
            ],
        }

    template = '<c-CTreeGrid c-columns="columns" c-rows="rows" label="Project plan" c-expanded="[\'launch\']" />'


preview = TreeGridExpansion()
preview  # noqa: B018
````


## Select and submit Rows

Choose `single` or `multiple` selection and set `name` to emit repeated hidden
Row keys in preorder. Shift+Space toggles the focused Row, including unselect.


### Select organization units

[Open the rendered preview](/v/0.4.6/ui-library/components/tree-grid/_previews/selection/)

````citry
# ruff: noqa: ANN001, ANN201, E501 - public template stays readable

import citry_ui
from citry import Component, citry
from citry_ui import CTreeGridColumn, CTreeGridRow

citry.register_library(citry_ui)


class TreeGridSelection(Component):
    def template_data(self, _kwargs, _slots):
        return {
            "columns": [CTreeGridColumn("team", "Team"), CTreeGridColumn("people", "People")],
            "rows": [
                CTreeGridRow("product", "Product", {"team": "Product", "people": 18}),
                CTreeGridRow("ops", "Operations", {"team": "Operations", "people": 12}),
            ],
        }

    template = '<form><c-CTreeGrid c-columns="columns" c-rows="rows" label="Teams" selection="multiple" c-selected="[\'product\']" name="team" /></form>'


preview = TreeGridSelection()
preview  # noqa: B018
````


## Own state in Alpine

Client `expanded` and `selected` props are controlled. Their callbacks report
the requested vector, previous vector, Row key, requested boolean state,
controlled flag, source, and native event.


### Own expansion and selection

[Open the rendered preview](/v/0.4.6/ui-library/components/tree-grid/_previews/controlled/)

````citry
# ruff: noqa: ANN001, ANN201, E501 - public template stays readable

import citry_ui
from citry import Component, citry
from citry_ui import CTreeGridColumn, CTreeGridRow

citry.register_library(citry_ui)


class TreeGridControlled(Component):
    def template_data(self, _kwargs, _slots):
        return {
            "columns": [CTreeGridColumn("name", "Name")],
            "rows": [
                CTreeGridRow(
                    "root", "Root", {"name": "Root"}, children=[CTreeGridRow("child", "Child", {"name": "Child"})]
                )
            ],
        }

    template = """<div x-data="{open:[],chosen:[]}"><c-CTreeGrid c-columns="columns" c-rows="rows" label="Controlled tree" selection="multiple" $c-props="{expanded:open,selected:chosen,onExpandedChange:value=>open=value,onSelectionChange:value=>chosen=value}" /></div>"""


preview = TreeGridControlled()
preview  # noqa: B018
````


## Customize cells

Use `header`, `cell`, `toolbar`, and `caption` slots. Cell navigation stays on
the gridcell; interactive editing remains the separate Data Grid contract.


### Format hierarchical metrics

[Open the rendered preview](/v/0.4.6/ui-library/components/tree-grid/_previews/custom-cells/)

````citry
# ruff: noqa: ANN001, ANN201, E501 - public template stays readable

import citry_ui
from citry import Component, citry
from citry_ui import CTreeGridColumn, CTreeGridRow

citry.register_library(citry_ui)


class TreeGridCustomCells(Component):
    def template_data(self, _kwargs, _slots):
        return {
            "columns": [CTreeGridColumn("name", "Initiative", 240), CTreeGridColumn("score", "Score", align="end")],
            "rows": [
                CTreeGridRow(
                    "quality",
                    "Quality",
                    {"name": "Quality", "score": 92},
                    children=[CTreeGridRow("a11y", "Accessibility", {"name": "Accessibility", "score": 98})],
                )
            ],
        }

    template = """<c-CTreeGrid c-columns="columns" c-rows="rows" label="Initiatives" c-expanded="['quality']"><c-fill name="cell" data="{ column, cell }"><strong c-if="column.key == 'score'">{{ cell.value }}%</strong><span c-else>{{ cell.value }}</span></c-fill></c-CTreeGrid>"""


preview = TreeGridCustomCells()
preview  # noqa: B018
````


## Navigate accessibly

Arrow keys move through visible Rows and Columns. Left and Right also collapse,
expand, and return to parents from the hierarchy cell. Disabled Rows remain
readable but cannot mutate or activate.


### Keep focus and selection distinct

[Open the rendered preview](/v/0.4.6/ui-library/components/tree-grid/_previews/accessibility/)

````citry
# ruff: noqa: ANN001, ANN201 - public snippets keep focus on component use

import citry_ui
from citry import Component, citry
from citry_ui import CTreeGridColumn, CTreeGridRow

citry.register_library(citry_ui)


class TreeGridAccessibility(Component):
    def template_data(self, _kwargs, _slots):
        return {
            "columns": [CTreeGridColumn("name", "Record", 260), CTreeGridColumn("status", "Status")],
            "rows": [
                CTreeGridRow("available", "Available record", {"name": "Available record", "status": "Ready"}),
                CTreeGridRow(
                    "locked", "Locked record", {"name": "Locked record", "status": "Archived"}, disabled=True
                ),
            ],
        }

    template = (
        '<c-CTreeGrid c-columns="columns" c-rows="rows" label="Records" selection="multiple" density="spacious" />'
    )


preview = TreeGridAccessibility()
preview  # noqa: B018
````


Hierarchical sorting, async children, virtual Rows, and editing are explicit
future or adjacent contracts, not hidden Tree Grid modes.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CTreeGrid server inputs

Server inputs are passed in a template through `<c-CTreeGrid ... />` or in Python through
`CTreeGrid(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="tree-grid-input-ctree-grid-server-inputs-columns"></span>`columns` | `Sequence[CTreeGridColumn]` | required | Defines ordered aligned Columns; the first owns hierarchy controls. |
| <span id="tree-grid-input-ctree-grid-server-inputs-rows"></span>`rows` | `Sequence[CTreeGridRow]` | required | Defines a finite recursive Row hierarchy. |
| <span id="tree-grid-input-ctree-grid-server-inputs-label"></span>`label` | `str` | required | Names the treegrid. |
| <span id="tree-grid-input-ctree-grid-server-inputs-id"></span>`id` | `str | None` | generated | Sets the root ID. |
| <span id="tree-grid-input-ctree-grid-server-inputs-expanded"></span>`expanded` | `Sequence[str]` | `"()"` | Supplies initially expanded branch Row keys. |
| <span id="tree-grid-input-ctree-grid-server-inputs-selection"></span>`selection` | `CTreeGridSelection` ([`CTreeGridSelection`](#tree-grid-interface-selection)) | `"none"` | Enables no single or multiple Row selection. |
| <span id="tree-grid-input-ctree-grid-server-inputs-selected"></span>`selected` | `Sequence[str]` | `"()"` | Supplies initially selected Row keys. |
| <span id="tree-grid-input-ctree-grid-server-inputs-name"></span>`name` | `str | None` | `None` | Emits selected keys as repeated hidden inputs. |
| <span id="tree-grid-input-ctree-grid-server-inputs-form"></span>`form` | `str | None` | `None` | Associates hidden inputs with an external form. |
| <span id="tree-grid-input-ctree-grid-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables mutation activation and form output. |
| <span id="tree-grid-input-ctree-grid-server-inputs-density"></span>`density` | `CTreeGridDensity` ([`CTreeGridDensity`](#tree-grid-interface-density)) | `"comfortable"` | Selects Row height. |
| <span id="tree-grid-input-ctree-grid-server-inputs-expand-label"></span>`expand_label` | `str` | `"Expand {row}"` | Overrides branch Expand names and must retain row. |
| <span id="tree-grid-input-ctree-grid-server-inputs-collapse-label"></span>`collapse_label` | `str` | `"Collapse {row}"` | Overrides branch Collapse names and must retain row. |
| <span id="tree-grid-input-ctree-grid-server-inputs-expanded-label"></span>`expanded_label` | `str` | `"Expanded {row}"` | Overrides expanded announcements and must retain row. |
| <span id="tree-grid-input-ctree-grid-server-inputs-collapsed-label"></span>`collapsed_label` | `str` | `"Collapsed {row}"` | Overrides collapsed announcements and must retain row. |
| <span id="tree-grid-input-ctree-grid-server-inputs-selected-label"></span>`selected_label` | `str` | `"Selected {row}"` | Overrides selected announcements and must retain row. |
| <span id="tree-grid-input-ctree-grid-server-inputs-unselected-label"></span>`unselected_label` | `str` | `"Unselected {row}"` | Overrides unselected announcements and must retain row. |
| <span id="tree-grid-input-ctree-grid-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#tree-grid-interface-class-value)) | `None` | Adds root classes. |
| <span id="tree-grid-input-ctree-grid-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#tree-grid-interface-style-value)) | `None` | Adds root styles. |
| <span id="tree-grid-input-ctree-grid-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes. |
| <span id="tree-grid-input-ctree-grid-server-inputs-table-attrs"></span>`table_attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed table attributes. |

</div>

#### CTreeGrid client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CTreeGrid />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="tree-grid-input-ctree-grid-client-inputs-expanded"></span>`expanded` | `string[]` | Uncontrolled server branch state. | Controls expanded branch keys. |
| <span id="tree-grid-input-ctree-grid-client-inputs-selected"></span>`selected` | `string[]` | Uncontrolled server selection. | Controls selected Row keys. |
| <span id="tree-grid-input-ctree-grid-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server value. | Reactively disables behavior and inputs. |
| <span id="tree-grid-input-ctree-grid-client-inputs-on-expanded-change"></span>`onExpandedChange` | `function` | No component callback runs. | Receives expansion requests. |
| <span id="tree-grid-input-ctree-grid-client-inputs-on-selection-change"></span>`onSelectionChange` | `function` | No component callback runs. | Receives selection requests. |
| <span id="tree-grid-input-ctree-grid-client-inputs-on-cell-activate"></span>`onCellActivate` | `function` | No component callback runs. | Receives Enter or double-click activation outside the hierarchy toggle. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CTreeGrid slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="tree-grid-slot-ctree-grid-slots-caption"></span>`caption` | no | `{}` ([`CTreeGridCaptionSlotData`](#tree-grid-interface-ctree-grid-caption-slot)) | No native caption. |
| <span id="tree-grid-slot-ctree-grid-slots-toolbar"></span>`toolbar` | no | `{}` ([`CTreeGridToolbarSlotData`](#tree-grid-interface-ctree-grid-toolbar-slot)) | No toolbar. |
| <span id="tree-grid-slot-ctree-grid-slots-header"></span>`header` | no | `{column, column_index}` ([`CTreeGridHeaderSlotData`](#tree-grid-interface-ctree-grid-header-slot)) | Column label. |
| <span id="tree-grid-slot-ctree-grid-slots-cell"></span>`cell` | no | `{row, column, cell, row_index, column_index, level, expanded, selected}` ([`CTreeGridCellSlotData`](#tree-grid-interface-ctree-grid-cell-slot)) | Cell value. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CTreeGrid events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="tree-grid-event-ctree-grid-events-expanded"></span>`onExpandedChange` | `(expanded: string[], detail: CTreeGridExpandedChangeDetail) => void` ([`CTreeGridExpandedChangeDetail`](#tree-grid-interface-ctree-grid-expanded-detail)) | A branch changes. | `{expanded, previousExpanded, rowKey, rowExpanded, controlled, source, sourceEvent}` ([`CTreeGridExpandedChangeDetail`](#tree-grid-interface-ctree-grid-expanded-detail)) | Commits only while uncontrolled. |
| <span id="tree-grid-event-ctree-grid-events-selected"></span>`onSelectionChange` | `(selected: string[], detail: CTreeGridSelectionChangeDetail) => void` ([`CTreeGridSelectionChangeDetail`](#tree-grid-interface-ctree-grid-selection-detail)) | A Row selection toggles. | `{selected, previousSelected, rowKey, rowSelected, controlled, source, sourceEvent}` ([`CTreeGridSelectionChangeDetail`](#tree-grid-interface-ctree-grid-selection-detail)) | Commits only while uncontrolled. |
| <span id="tree-grid-event-ctree-grid-events-activate"></span>`onCellActivate` | `(detail: CTreeGridCellActivateDetail) => void` ([`CTreeGridCellActivateDetail`](#tree-grid-interface-ctree-grid-activate-detail)) | Enter or double-click activates a non-hierarchy Cell. | `{rowKey, columnKey, rowIndex, columnIndex, sourceEvent}` ([`CTreeGridCellActivateDetail`](#tree-grid-interface-ctree-grid-activate-detail)) | Reports without changing data. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CTreeGrid CSS variables

Apply these variables to `CTreeGrid` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="tree-grid-css-ctree-grid-css-min-width"></span>`--cui-tree-grid-min-width` | `length` | Computed minimum table width. | `Sum of Column widths` |
| <span id="tree-grid-css-ctree-grid-css-row-height"></span>`--cui-tree-grid-row-height` | `length` | Comfortable Row height. | `3rem` |
| <span id="tree-grid-css-ctree-grid-css-indent"></span>`--cui-tree-grid-indent` | `length` | Per-level logical indent. | `1.25rem` |
| <span id="tree-grid-css-ctree-grid-css-border"></span>`--cui-tree-grid-border` | `complete border` | Viewport Row and header boundaries. | `Adaptive 1px neutral` |
| <span id="tree-grid-css-ctree-grid-css-surface"></span>`--cui-tree-grid-surface` | `color` | Body surface. | `Canvas` |
| <span id="tree-grid-css-ctree-grid-css-header"></span>`--cui-tree-grid-header-surface` | `color` | Header surface. | `Adaptive neutral` |
| <span id="tree-grid-css-ctree-grid-css-selected"></span>`--cui-tree-grid-selected-surface` | `color` | Selected Row surface. | `Adaptive indigo` |
| <span id="tree-grid-css-ctree-grid-css-focus"></span>`--cui-tree-grid-focus` | `color` | Gridcell and expander focus. | `Highlight` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CTreeGrid attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="tree-grid-attribute-ctree-grid-attributes-data-density"></span>`data-density` | Root | `CTreeGridDensity` ([`CTreeGridDensity`](#tree-grid-interface-density)) | Reflects Row density. |
| <span id="tree-grid-attribute-ctree-grid-attributes-data-selection"></span>`data-selection` | Root | `CTreeGridSelection` ([`CTreeGridSelection`](#tree-grid-interface-selection)) | Reflects selection policy. |
| <span id="tree-grid-attribute-ctree-grid-attributes-data-disabled"></span>`data-disabled` | Root and Row | `present | absent` | Reflects unavailable behavior. |
| <span id="tree-grid-attribute-ctree-grid-attributes-data-expanded"></span>`data-expanded` | Row | `present | absent` | Reflects expanded branch state. |
| <span id="tree-grid-attribute-ctree-grid-attributes-data-selected"></span>`data-selected` | Row | `present | absent` | Reflects selected state. |
| <span id="tree-grid-attribute-ctree-grid-attributes-data-row-key"></span>`data-row-key` | Row and Cell | `string` | Exposes stable Row identity. |
| <span id="tree-grid-attribute-ctree-grid-attributes-data-parent-key"></span>`data-parent-key` | Row | `string | absent` | Exposes parent identity. |
| <span id="tree-grid-attribute-ctree-grid-attributes-data-level"></span>`data-level` | Row | `positive integer string` | Exposes hierarchy depth. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CTreeGrid selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="tree-grid-selector-ctree-grid-selectors-root"></span>`[data-citry-ui-part="tree-grid"]` | Root | Theme and state destination. |
| <span id="tree-grid-selector-ctree-grid-selectors-toolbar"></span>`[data-citry-ui-part="toolbar"]` | Optional div | Application controls. |
| <span id="tree-grid-selector-ctree-grid-selectors-status"></span>`[data-citry-ui-part="status"]` | Polite status | Expansion and selection announcements. |
| <span id="tree-grid-selector-ctree-grid-selectors-viewport"></span>`[data-citry-ui-part="viewport"]` | Scroll container | Narrow horizontal overflow. |
| <span id="tree-grid-selector-ctree-grid-selectors-table"></span>`[data-citry-ui-part="table"]` | Native table with treegrid role | Composite owner. |
| <span id="tree-grid-selector-ctree-grid-selectors-header-cell"></span>`[data-citry-ui-part="header-cell"]` | Columnheader | Column label. |
| <span id="tree-grid-selector-ctree-grid-selectors-row"></span>`[data-citry-ui-part="row"]` | Hierarchical Row | Expansion selection and hierarchy metadata. |
| <span id="tree-grid-selector-ctree-grid-selectors-cell"></span>`[data-citry-ui-part="cell"]` | Gridcell | Roving focus unit. |
| <span id="tree-grid-selector-ctree-grid-selectors-hierarchy"></span>`[data-citry-ui-part="hierarchy"]` | First-Cell wrapper | Indent branch control and content. |
| <span id="tree-grid-selector-ctree-grid-selectors-expander"></span>`[data-citry-ui-part="expander"]` | Native button | Pointer branch toggle. |
| <span id="tree-grid-selector-ctree-grid-selectors-cell-content"></span>`[data-citry-ui-part="cell-content"]` | Span | Cell slot destination. |
| <span id="tree-grid-selector-ctree-grid-selectors-inputs"></span>`[data-citry-ui-part="inputs"]` | Hidden span | Native selected-key controls. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="tree-grid-interface-selection"></span>`CTreeGridSelection` | `Literal["none", "single", "multiple"]` |
| <span id="tree-grid-interface-density"></span>`CTreeGridDensity` | `Literal["compact", "comfortable", "spacious"]` |
| <span id="tree-grid-interface-align"></span>`CTreeGridAlign` | `Literal["start", "center", "end"]` |
| <span id="tree-grid-interface-source"></span>`CTreeGridSource` | `Literal["pointer", "keyboard", "reset"]` |
| <span id="tree-grid-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="tree-grid-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="tree-grid-interface-ctree-grid-caption-slot"></span>

#### `CTreeGridCaptionSlotData`

Empty dataclass: `{}`.

<span id="tree-grid-interface-ctree-grid-toolbar-slot"></span>

#### `CTreeGridToolbarSlotData`

Empty dataclass: `{}`.

<span id="tree-grid-interface-ctree-grid-header-slot"></span>

#### `CTreeGridHeaderSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tree-grid-interface-ctree-grid-header-slot-column"></span>`column` | `CTreeGridColumn` | - | Current Column. |
| <span id="tree-grid-interface-ctree-grid-header-slot-column-index"></span>`column_index` | `int` | - | Zero-based Column index. |

</div>

<span id="tree-grid-interface-ctree-grid-cell-slot"></span>

#### `CTreeGridCellSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tree-grid-interface-ctree-grid-cell-slot-row"></span>`row` | `CTreeGridRow` | - | Current Row. |
| <span id="tree-grid-interface-ctree-grid-cell-slot-column"></span>`column` | `CTreeGridColumn` | - | Current Column. |
| <span id="tree-grid-interface-ctree-grid-cell-slot-cell"></span>`cell` | `CTreeGridCell` | - | Current Cell. |
| <span id="tree-grid-interface-ctree-grid-cell-slot-row-index"></span>`row_index` | `int` | - | Zero-based flattened Row index. |
| <span id="tree-grid-interface-ctree-grid-cell-slot-column-index"></span>`column_index` | `int` | - | Zero-based Column index. |
| <span id="tree-grid-interface-ctree-grid-cell-slot-level"></span>`level` | `int` | - | One-based hierarchy depth. |
| <span id="tree-grid-interface-ctree-grid-cell-slot-expanded"></span>`expanded` | `bool` | - | Initial branch expansion. |
| <span id="tree-grid-interface-ctree-grid-cell-slot-selected"></span>`selected` | `bool` | - | Initial Row selection. |

</div>

<span id="tree-grid-interface-ctree-grid-expanded-detail"></span>

#### `CTreeGridExpandedChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tree-grid-interface-ctree-grid-expanded-detail-expanded"></span>`expanded` | `list[str]` | - | Requested expanded keys. |
| <span id="tree-grid-interface-ctree-grid-expanded-detail-previous"></span>`previousExpanded` | `list[str]` | - | Previous keys. |
| <span id="tree-grid-interface-ctree-grid-expanded-detail-row-key"></span>`rowKey` | `str` | - | Changed Row. |
| <span id="tree-grid-interface-ctree-grid-expanded-detail-row-expanded"></span>`rowExpanded` | `bool` | - | Requested Row state. |
| <span id="tree-grid-interface-ctree-grid-expanded-detail-controlled"></span>`controlled` | `bool` | - | Whether client state is controlled. |
| <span id="tree-grid-interface-ctree-grid-expanded-detail-source"></span>`source` | `CTreeGridSource` | - | Interaction source. |
| <span id="tree-grid-interface-ctree-grid-expanded-detail-source-event"></span>`sourceEvent` | `object` | - | Native Event. |

</div>

<span id="tree-grid-interface-ctree-grid-selection-detail"></span>

#### `CTreeGridSelectionChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tree-grid-interface-ctree-grid-selection-detail-selected"></span>`selected` | `list[str]` | - | Requested selected keys. |
| <span id="tree-grid-interface-ctree-grid-selection-detail-previous"></span>`previousSelected` | `list[str]` | - | Previous keys. |
| <span id="tree-grid-interface-ctree-grid-selection-detail-row-key"></span>`rowKey` | `str` | - | Changed Row. |
| <span id="tree-grid-interface-ctree-grid-selection-detail-row-selected"></span>`rowSelected` | `bool` | - | Requested Row state. |
| <span id="tree-grid-interface-ctree-grid-selection-detail-controlled"></span>`controlled` | `bool` | - | Whether client state is controlled. |
| <span id="tree-grid-interface-ctree-grid-selection-detail-source"></span>`source` | `CTreeGridSource` | - | Interaction source. |
| <span id="tree-grid-interface-ctree-grid-selection-detail-source-event"></span>`sourceEvent` | `object` | - | Native Event. |

</div>

<span id="tree-grid-interface-ctree-grid-activate-detail"></span>

#### `CTreeGridCellActivateDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tree-grid-interface-ctree-grid-activate-detail-row-key"></span>`rowKey` | `str` | - | Activated Row. |
| <span id="tree-grid-interface-ctree-grid-activate-detail-column-key"></span>`columnKey` | `str` | - | Activated Column. |
| <span id="tree-grid-interface-ctree-grid-activate-detail-row-index"></span>`rowIndex` | `int` | - | Flattened Row index. |
| <span id="tree-grid-interface-ctree-grid-activate-detail-column-index"></span>`columnIndex` | `int` | - | Column index. |
| <span id="tree-grid-interface-ctree-grid-activate-detail-source-event"></span>`sourceEvent` | `object` | - | Native Event. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CTreeGrid translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="tree-grid-translation-ctree-grid-translations-expand"></span>`citry-ui-tree-grid-expand` | Names a collapsed branch control. | `row: str` | `expand_label` with `{row}` | Imperative reactive `i18n.bind()`. |
| <span id="tree-grid-translation-ctree-grid-translations-collapse"></span>`citry-ui-tree-grid-collapse` | Names an expanded branch control. | `row: str` | `collapse_label` with `{row}` | Imperative reactive `i18n.bind()`. |
| <span id="tree-grid-translation-ctree-grid-translations-expanded"></span>`citry-ui-tree-grid-expanded` | Announces branch expansion. | `row: str` | `expanded_label` with `{row}` | Browser-created one-shot `i18n.tr()`. |
| <span id="tree-grid-translation-ctree-grid-translations-collapsed"></span>`citry-ui-tree-grid-collapsed` | Announces branch collapse. | `row: str` | `collapsed_label` with `{row}` | Browser-created one-shot `i18n.tr()`. |
| <span id="tree-grid-translation-ctree-grid-translations-selected"></span>`citry-ui-tree-grid-selected` | Announces Row selection. | `row: str` | `selected_label` with `{row}` | Browser-created one-shot `i18n.tr()`. |
| <span id="tree-grid-translation-ctree-grid-translations-unselected"></span>`citry-ui-tree-grid-unselected` | Announces Row unselection. | `row: str` | `unselected_label` with `{row}` | Browser-created one-shot `i18n.tr()`. |

</div>