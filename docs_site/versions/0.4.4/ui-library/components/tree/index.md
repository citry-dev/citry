---
title: Tree
url: https://citry.dev/v/0.4.4/ui-library/components/tree/
description: "Explore and select hierarchical application data."
---
# Tree

Use `CTree` for compact hierarchical application data such as files or object
structures. Use disclosure navigation for ordinary site links.

## Tree at a glance


### Tree at a glance

[Open the rendered preview](/v/0.4.4/ui-library/components/tree/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TreeAtAGlance(Component):
    template = """
      <c-CTree label="Project files" c-expanded="['src']" c-selected="['app']" variant="soft">
        <c-CTreeItem value="src" label="src">
          <c-CTreeItem value="app" label="app.py" />
          <c-CTreeItem value="styles" label="styles.css" />
        </c-CTreeItem>
        <c-CTreeItem value="tests" label="tests" />
        <c-CTreeItem value="readme" label="README.md" />
      </c-CTree>
    """


preview = TreeAtAGlance()
preview  # noqa: B018
````


## Control expansion


### Control expanded branches

[Open the rendered preview](/v/0.4.4/ui-library/components/tree/_previews/controlled-expansion/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledExpansion(Component):
    template = """
      <section x-data="{ expanded: ['docs'] }">
        <c-CTree
          label="Knowledge base"
          $c-props="{ expanded, onExpandedChange: (next) => expanded = next }"
        >
          <c-CTreeItem value="docs" label="Documentation">
            <c-CTreeItem value="guides" label="Guides" />
            <c-CTreeItem value="reference" label="Reference" />
          </c-CTreeItem>
          <c-CTreeItem value="examples" label="Examples" />
        </c-CTree>
        <output x-text="expanded.join(', ') || 'All branches collapsed'"></output>
      </section>
    """


preview = ControlledExpansion()
preview  # noqa: B018
````


## Select one Item


### Select one Item

[Open the rendered preview](/v/0.4.4/ui-library/components/tree/_previews/single-selection/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TreeSingleSelection(Component):
    template = """
      <section x-data="{ selected: ['mercury'] }">
        <c-CTree
          label="Planets"
          c-selected="['mercury']"
          $c-props="{ selected, onSelectionChange: (next) => selected = next }"
        >
          <c-CTreeItem value="mercury" label="Mercury" />
          <c-CTreeItem value="venus" label="Venus" />
          <c-CTreeItem value="earth" label="Earth" />
        </c-CTree>
        <output x-text="selected[0] ?? 'No selection'"></output>
      </section>
    """


preview = TreeSingleSelection()
preview  # noqa: B018
````


## Select multiple Items


### Select multiple Items

[Open the rendered preview](/v/0.4.4/ui-library/components/tree/_previews/multiple-selection/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TreeMultipleSelection(Component):
    template = """
      <section x-data="{ selected: ['alder'] }">
        <c-CTree
          label="Specimens"
          selection_mode="multiple"
          c-selected="['alder']"
          $c-props="{ selected, onSelectionChange: (next) => selected = next }"
        >
          <c-CTreeItem value="alder" label="Alder" />
          <c-CTreeItem value="birch" label="Birch" />
          <c-CTreeItem value="cedar" label="Cedar" />
        </c-CTree>
        <output x-text="selected.join(', ')"></output>
      </section>
    """


preview = TreeMultipleSelection()
preview  # noqa: B018
````


## Navigate with the keyboard

Down and Up move through visible Items. Right expands or enters a branch;
Left collapses or returns to its parent. Home, End, and buffered
typeahead follow the ARIA Tree pattern.


### Navigate a Tree

[Open the rendered preview](/v/0.4.4/ui-library/components/tree/_previews/keyboard/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class KeyboardTree(Component):
    template = """
      <c-CTree label="Keyboard explorer" c-expanded="['animals']" variant="outline">
        <c-CTreeItem value="animals" label="Animals">
          <c-CTreeItem value="badger" label="Badger" />
          <c-CTreeItem value="beaver" label="Beaver" />
        </c-CTreeItem>
        <c-CTreeItem value="minerals" label="Minerals" />
        <c-CTreeItem value="plants" label="Plants" />
      </c-CTree>
    """


preview = KeyboardTree()
preview  # noqa: B018
````


## Disable Items


### Disable Tree Items

[Open the rendered preview](/v/0.4.4/ui-library/components/tree/_previews/disabled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TreeDisabledItems(Component):
    template = """
      <c-CTree label="Deployment targets" c-expanded="['regions']">
        <c-CTreeItem value="regions" label="Regions">
          <c-CTreeItem value="eu" label="Europe" />
          <c-CTreeItem value="us" label="United States" disabled />
        </c-CTreeItem>
        <c-CTreeItem value="archive" label="Archived targets" disabled />
      </c-CTree>
    """


preview = TreeDisabledItems()
preview  # noqa: B018
````


## Customize Tree


### Customize Tree

[Open the rendered preview](/v/0.4.4/ui-library/components/tree/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedTree(Component):
    template = """
      <div class="brand-tree">
        <style>
          .brand-tree {
            --cui-tree-indent: 1.75rem;
            --cui-tree-radius: 1rem;
            --cui-tree-selected-background: rebeccapurple;
            --cui-tree-selected-color: white;
          }
        </style>
        <c-CTree label="Branded catalog" c-selected="['ferns']" variant="outline" size="lg">
          <c-CTreeItem value="mosses" label="Mosses" />
          <c-CTreeItem value="ferns" label="Ferns" />
          <c-CTreeItem value="orchids" label="Orchids" />
        </c-CTree>
      </div>
    """


preview = CustomizedTree()
preview  # noqa: B018
````


## Accessibility and behavior

The named root uses `role="tree"`; Items use `role="treeitem"` and nested
children use `role="group"`. One visible Item is in the Tab order. Expansion,
selection, focus, and application action are separate states. Space selects,
Enter selects and invokes `onAction`, and double-click invokes the action.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CTree server inputs

Server inputs are passed in a template through `<c-CTree ... />` or in Python through
`CTree(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="tree-input-ctree-server-inputs-label"></span>`label` | `str` | required | Names the Tree widget. |
| <span id="tree-input-ctree-server-inputs-expanded"></span>`expanded` | `Sequence[str]` | () | Sets initially expanded branch values. |
| <span id="tree-input-ctree-server-inputs-selected"></span>`selected` | `Sequence[str]` | () | Sets initially selected Item values. |
| <span id="tree-input-ctree-server-inputs-selection-mode"></span>`selection_mode` | `"none" | "single" | "multiple"` ([`CTreeSelectionMode`](#tree-interface-ctree-selection-mode)) | `"single"` | Selects no-selection single-selection or independent multi-selection behavior. |
| <span id="tree-input-ctree-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables expansion selection and action throughout the Tree. |
| <span id="tree-input-ctree-server-inputs-variant"></span>`variant` | `"plain" | "soft" | "outline"` ([`CTreeVariant`](#tree-interface-ctree-variant)) | `"plain"` | Selects surface treatment. |
| <span id="tree-input-ctree-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CTreeSize`](#tree-interface-ctree-size)) | `"md"` | Selects row and indentation geometry. |
| <span id="tree-input-ctree-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#tree-interface-ctree-class-value)) | `None` | Adds root classes. |
| <span id="tree-input-ctree-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#tree-interface-ctree-style-value)) | `None` | Adds root inline styles. |
| <span id="tree-input-ctree-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted root attributes without replacing owned semantics focus state structure or runtime. |

</div>

#### CTree client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CTree />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="tree-input-ctree-client-inputs-expanded"></span>`expanded` | `string[] | null` | Uses uncontrolled committed expansion. | Controls expanded branches while supplied; null releases control. |
| <span id="tree-input-ctree-client-inputs-selected"></span>`selected` | `string[] | null` | Uses uncontrolled committed selection. | Controls selected Items while supplied; null releases control. |
| <span id="tree-input-ctree-client-inputs-selection-mode"></span>`selectionMode` | `"none" | "single" | "multiple"` ([`CTreeSelectionMode`](#tree-interface-ctree-selection-mode)) | Uses the server value. | Reactively changes selection behavior. |
| <span id="tree-input-ctree-client-inputs-disabled"></span>`disabled` | `bool` | Uses the server value. | Reactively disables Tree operations. |
| <span id="tree-input-ctree-client-inputs-variant"></span>`variant` | `"plain" | "soft" | "outline"` ([`CTreeVariant`](#tree-interface-ctree-variant)) | Uses the server value. | Reactively changes presentation. |
| <span id="tree-input-ctree-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CTreeSize`](#tree-interface-ctree-size)) | Uses the server value. | Reactively changes geometry. |
| <span id="tree-input-ctree-client-inputs-on-expanded-change"></span>`onExpandedChange` | `((expanded: string[], detail: CTreeExpandedChangeDetail) => void) | undefined` | No component callback runs. | Receives branch expansion requests. |
| <span id="tree-input-ctree-client-inputs-on-selection-change"></span>`onSelectionChange` | `((selected: string[], detail: CTreeSelectionChangeDetail) => void) | undefined` | No component callback runs. | Receives Item selection requests. |
| <span id="tree-input-ctree-client-inputs-on-action"></span>`onAction` | `((value: string, detail: CTreeActionDetail) => void) | undefined` | No component callback runs. | Receives enabled Enter or double-click actions. |

</div>

#### CTreeItem server inputs

Server inputs are passed in a template through `<c-CTreeItem ... />` or in Python through
`CTreeItem(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="tree-input-ctree-item-server-inputs-value"></span>`value` | `str` | required | Supplies stable unique Item identity. |
| <span id="tree-input-ctree-item-server-inputs-label"></span>`label` | `str` | required | Supplies visible text accessible naming and typeahead text. |
| <span id="tree-input-ctree-item-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Keeps the Item focusable by Tree navigation but prevents operations. |
| <span id="tree-input-ctree-item-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#tree-interface-ctree-class-value)) | `None` | Adds classes to the concrete Item. |
| <span id="tree-input-ctree-item-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#tree-interface-ctree-style-value)) | `None` | Adds inline styles to the concrete Item. |
| <span id="tree-input-ctree-item-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted Item attributes without replacing owned semantics identity focus state or children. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CTree slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="tree-slot-ctree-slots-default"></span>`default` | yes | `{}` ([`CTreeDefaultSlotData`](#tree-interface-ctree-default-slot-data)) | None. Requires one or more direct CTreeItem declarations. |

</div>

#### CTreeItem slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="tree-slot-ctree-item-slots-default"></span>`default` | no | `{parent_value, level}` ([`CTreeItemDefaultSlotData`](#tree-interface-ctree-item-default-slot-data)) | Omitted for a leaf; otherwise accepts child CTreeItem declarations only. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CTree events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="tree-event-ctree-events-expanded-change"></span>`onExpandedChange` | `(expanded: string[], detail: CTreeExpandedChangeDetail) => void` ([`CTreeExpandedChangeDetail`](#tree-interface-ctree-expanded-change-detail)) | Enabled pointer-indicator or keyboard branch request. | `{value, expanded, previousExpanded, controlled, source, item, sourceEvent}` ([`CTreeExpandedChangeDetail`](#tree-interface-ctree-expanded-change-detail)) | Commits immediately when uncontrolled and waits when controlled. |
| <span id="tree-event-ctree-events-selection-change"></span>`onSelectionChange` | `(selected: string[], detail: CTreeSelectionChangeDetail) => void` ([`CTreeSelectionChangeDetail`](#tree-interface-ctree-selection-change-detail)) | Enabled row click Space or Enter in a selectable mode. | `{value, selected, previousSelected, controlled, source, item, sourceEvent}` ([`CTreeSelectionChangeDetail`](#tree-interface-ctree-selection-change-detail)) | Applies single or independent multiple selection policy. |
| <span id="tree-event-ctree-events-action"></span>`onAction` | `(value: string, detail: CTreeActionDetail) => void` ([`CTreeActionDetail`](#tree-interface-ctree-action-detail)) | Enabled Enter or double-click. | `{value, item, sourceEvent}` ([`CTreeActionDetail`](#tree-interface-ctree-action-detail)) | Notifies application action without navigation or form submission. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CTree CSS variables

Apply these variables to `CTree` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="tree-css-ctree-css-variables-cui-tree-indent"></span>`--cui-tree-indent` | `length` | Logical child indentation. | `sm 1rem; md 1.25rem; lg 1.5rem` |
| <span id="tree-css-ctree-css-variables-cui-tree-row-gap"></span>`--cui-tree-row-gap` | `length` | Gap between sibling rows. | `0.125rem` |
| <span id="tree-css-ctree-css-variables-cui-tree-row-padding"></span>`--cui-tree-row-padding` | `length` | Row block and inline padding. | `size-derived` |
| <span id="tree-css-ctree-css-variables-cui-tree-radius"></span>`--cui-tree-radius` | `length` | Root and row corner radius. | `0.5rem` |
| <span id="tree-css-ctree-css-variables-cui-tree-background"></span>`--cui-tree-background` | `color` | Root background. | `plain and outline transparent; soft subtle CanvasText mix` |
| <span id="tree-css-ctree-css-variables-cui-tree-border-color"></span>`--cui-tree-border-color` | `color` | Outline border. | `light #d0d5dd; dark #535862` |
| <span id="tree-css-ctree-css-variables-cui-tree-hover-background"></span>`--cui-tree-hover-background` | `color` | Enabled row hover background. | `7% CanvasText mix` |
| <span id="tree-css-ctree-css-variables-cui-tree-selected-background"></span>`--cui-tree-selected-background` | `color` | Selected row background. | `light #dbeafe; dark #1e3a5f` |
| <span id="tree-css-ctree-css-variables-cui-tree-selected-color"></span>`--cui-tree-selected-color` | `color` | Selected row foreground. | `light #1849a9; dark #d1e9ff` |
| <span id="tree-css-ctree-css-variables-cui-tree-muted-color"></span>`--cui-tree-muted-color` | `color` | Disabled Item foreground. | `light #667085; dark #a4a7ae` |
| <span id="tree-css-ctree-css-variables-cui-tree-focus-color"></span>`--cui-tree-focus-color` | `color` | Roving focus outline. | `Highlight` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CTree attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="tree-attribute-ctree-attributes-role"></span>`role` | Root or Item/group div | `tree | treeitem | group` | Owns Tree hierarchy semantics. |
| <span id="tree-attribute-ctree-attributes-aria-label"></span>`aria-label` | Root or Item div | `string` | Names the Tree and each Item. |
| <span id="tree-attribute-ctree-attributes-tabindex"></span>`tabindex` | Item div | `0 | -1` | Implements one roving visible Tab stop. |
| <span id="tree-attribute-ctree-attributes-aria-disabled"></span>`aria-disabled` | Item div | `true | false` | Reflects effective Item unavailability. |
| <span id="tree-attribute-ctree-attributes-aria-expanded"></span>`aria-expanded` | Branch Item div | `true | false` | Reflects branch visibility; omitted on leaves. |
| <span id="tree-attribute-ctree-attributes-aria-selected"></span>`aria-selected` | Selectable Item div | `true | false` | Reflects selection; omitted in none mode. |
| <span id="tree-attribute-ctree-attributes-data-selection-mode"></span>`data-selection-mode` | Root div | `none | single | multiple` | Mirrors effective selection model. |
| <span id="tree-attribute-ctree-attributes-data-disabled"></span>`data-disabled` | Root or Item div | `present-or-absent` | Reflects effective unavailability. |
| <span id="tree-attribute-ctree-attributes-data-variant"></span>`data-variant` | Root div | `plain | soft | outline` | Mirrors effective presentation. |
| <span id="tree-attribute-ctree-attributes-data-size"></span>`data-size` | Root div | `sm | md | lg` | Mirrors effective geometry. |
| <span id="tree-attribute-ctree-attributes-data-value"></span>`data-value` | Item div | `string` | Exposes canonical Item identity. |
| <span id="tree-attribute-ctree-attributes-data-level"></span>`data-level` | Item div | `positive-integer-string` | Exposes settled hierarchy depth. |
| <span id="tree-attribute-ctree-attributes-data-expanded"></span>`data-expanded` | Branch Item div | `present-or-absent` | Present while expanded. |
| <span id="tree-attribute-ctree-attributes-data-selected"></span>`data-selected` | Item div | `present-or-absent` | Present while selected. |
| <span id="tree-attribute-ctree-attributes-hidden"></span>`hidden` | Child group div | `present-or-absent` | Removes collapsed descendants from rendering. |
| <span id="tree-attribute-ctree-attributes-inert"></span>`inert` | Child group div | `present-or-absent` | Guards collapsed descendants from interaction. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CTree selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="tree-selector-ctree-selectors-part-tree"></span>`[data-citry-ui-part="tree"]` | Root div | Stable root and attrs destination. |
| <span id="tree-selector-ctree-selectors-part-item"></span>`[data-citry-ui-part="item"]` | Tree Item div | Stable Item attrs and state surface. |
| <span id="tree-selector-ctree-selectors-part-row"></span>`[data-citry-ui-part="row"]` | Row span | Stable visible Item surface. |
| <span id="tree-selector-ctree-selectors-part-indicator"></span>`[data-citry-ui-part="indicator"]` | Decorative span | Pointer expansion target and branch indicator. |
| <span id="tree-selector-ctree-selectors-part-label"></span>`[data-citry-ui-part="label"]` | Label span | Stable visible and typeahead text. |
| <span id="tree-selector-ctree-selectors-part-group"></span>`[data-citry-ui-part="group"]` | Child group div | Stable nested collection and visibility surface. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="tree-interface-ctree-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="tree-interface-ctree-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |
| <span id="tree-interface-ctree-selection-mode"></span>`CTreeSelectionMode` | `Literal["none", "single", "multiple"]` |
| <span id="tree-interface-ctree-variant"></span>`CTreeVariant` | `Literal["plain", "soft", "outline"]` |
| <span id="tree-interface-ctree-size"></span>`CTreeSize` | `Literal["sm", "md", "lg"]` |
| <span id="tree-interface-ctree-change-source"></span>`CTreeChangeSource` | `Literal["pointer", "keyboard", "structure"]` |

</div>

<span id="tree-interface-ctree-default-slot-data"></span>

#### `CTreeDefaultSlotData`

Empty dataclass: `{}`.

<span id="tree-interface-ctree-item-default-slot-data"></span>

#### `CTreeItemDefaultSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tree-interface-ctree-item-default-slot-data-parent-value"></span>`parent_value` | `str` | - | Canonical parent Item identity. |
| <span id="tree-interface-ctree-item-default-slot-data-level"></span>`level` | `int` | - | One-based child hierarchy level. |

</div>

<span id="tree-interface-ctree-expanded-change-detail"></span>

#### `CTreeExpandedChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tree-interface-ctree-expanded-change-detail-value"></span>`value` | `str` | - | Changed branch identity. |
| <span id="tree-interface-ctree-expanded-change-detail-expanded"></span>`expanded` | `bool` | - | Requested branch state. |
| <span id="tree-interface-ctree-expanded-change-detail-previous-expanded"></span>`previousExpanded` | `string[]` | - | Prior vector. |
| <span id="tree-interface-ctree-expanded-change-detail-controlled"></span>`controlled` | `bool` | - | Whether client expanded controls state. |
| <span id="tree-interface-ctree-expanded-change-detail-source"></span>`source` | `"pointer" | "keyboard" | "structure"` ([`CTreeChangeSource`](#tree-interface-ctree-change-source)) | - | Request source. |
| <span id="tree-interface-ctree-expanded-change-detail-item"></span>`item` | `HTMLElement` | - | Changed Item. |
| <span id="tree-interface-ctree-expanded-change-detail-source-event"></span>`sourceEvent` | `Event` | - | Native source event. |

</div>

<span id="tree-interface-ctree-selection-change-detail"></span>

#### `CTreeSelectionChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tree-interface-ctree-selection-change-detail-value"></span>`value` | `str` | - | Changed Item identity. |
| <span id="tree-interface-ctree-selection-change-detail-selected"></span>`selected` | `bool` | - | Requested selection state. |
| <span id="tree-interface-ctree-selection-change-detail-previous-selected"></span>`previousSelected` | `string[]` | - | Prior vector. |
| <span id="tree-interface-ctree-selection-change-detail-controlled"></span>`controlled` | `bool` | - | Whether client selected controls state. |
| <span id="tree-interface-ctree-selection-change-detail-source"></span>`source` | `"pointer" | "keyboard" | "structure"` ([`CTreeChangeSource`](#tree-interface-ctree-change-source)) | - | Request source. |
| <span id="tree-interface-ctree-selection-change-detail-item"></span>`item` | `HTMLElement` | - | Changed Item. |
| <span id="tree-interface-ctree-selection-change-detail-source-event"></span>`sourceEvent` | `Event` | - | Native source event. |

</div>

<span id="tree-interface-ctree-action-detail"></span>

#### `CTreeActionDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="tree-interface-ctree-action-detail-value"></span>`value` | `str` | - | Activated Item identity. |
| <span id="tree-interface-ctree-action-detail-item"></span>`item` | `HTMLElement` | - | Activated Item. |
| <span id="tree-interface-ctree-action-detail-source-event"></span>`sourceEvent` | `Event` | - | Native Enter or double-click event. |

</div>

### Translation keys

-