---
title: Cascader
url: https://citry.dev/v/0.4.4/ui-library/components/cascader/
description: "Select one path through a finite server-rendered hierarchy."
---
# Cascader

Use `CCascader` when a value is meaningful only as a path through related
levels. Each `CCascaderOption` declares a globally unique value and plain label;
nested Options create the next column.


### Choose a geographic path

[Open the rendered preview](/v/0.4.4/ui-library/components/cascader/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CascaderAtAGlance(Component):
    template = """
      <c-CCascader c-value="['europe','czechia','prague']">
        <c-CCascaderOption value="europe" label="Europe">
          <c-CCascaderOption value="czechia" label="Czechia">
            <c-CCascaderOption value="prague" label="Prague" />
          </c-CCascaderOption>
          <c-CCascaderOption value="germany" label="Germany">
            <c-CCascaderOption value="berlin" label="Berlin" />
          </c-CCascaderOption>
        </c-CCascaderOption>
      </c-CCascader>
    """


preview = CascaderAtAGlance()
preview  # noqa: B018
````


## Submit the complete path

Set `name` to produce one hidden input per accepted segment, in root-to-leaf
order. `form` supports an external native form. Without JavaScript, the initial
path remains visible and submits normally.


### Submit category segments

[Open the rendered preview](/v/0.4.4/ui-library/components/cascader/_previews/forms/)

````citry
# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CascaderForms(Component):
    template = """
      <form>
        <c-CCascader name="category" c-value="['hardware','cameras','mirrorless']">
          <c-CCascaderOption value="hardware" label="Hardware"><c-CCascaderOption value="cameras" label="Cameras"><c-CCascaderOption value="mirrorless" label="Mirrorless" /></c-CCascaderOption></c-CCascaderOption>
        </c-CCascader>
        <button type="submit">Save category</button>
      </form>
    """


preview = CascaderForms()
preview  # noqa: B018
````


## Control selection

Pass `value` and `onValueChange` through `$c-props` for controlled state. The
callback receives the path plus labels, previous path, selected Option element,
controlled flag, interaction source, and native event.
Invalid controlled `value` or `open` values are diagnosed once and retain the
last valid effective state. Omitting `value` returns to the retained uncontrolled
path; omitting `open` releases control without changing the current open state.


### Own the accepted location

[Open the rendered preview](/v/0.4.4/ui-library/components/cascader/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CascaderControlled(Component):
    template = """
      <div x-data="{place:['earth','north'], last:''}">
        <c-CCascader $c-props="{value:place,onValueChange:(value)=>{place=value;last=value.join(' / ')}}">
          <c-CCascaderOption value="earth" label="Earth">
            <c-CCascaderOption value="north" label="Northern hemisphere" />
            <c-CCascaderOption value="south" label="Southern hemisphere" />
          </c-CCascaderOption>
        </c-CCascader>
        <output x-text="last"></output>
      </div>
    """


preview = CascaderControlled()
preview  # noqa: B018
````


## Allow parent paths

The default requires a leaf. Set `change_on_select=True` when a category at any
depth is a complete result. Activating a collapsed branch selects it and opens
its children. Activating the expanded branch again collapses its child level.


### Select any category depth

[Open the rendered preview](/v/0.4.4/ui-library/components/cascader/_previews/parent-selection/)

````citry
# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CascaderParentSelection(Component):
    template = """
      <c-CCascader c-change_on_select="True">
        <c-CCascaderOption value="design" label="Design"><c-CCascaderOption value="research" label="Research" /><c-CCascaderOption value="systems" label="Design systems" /></c-CCascaderOption>
        <c-CCascaderOption value="engineering" label="Engineering"><c-CCascaderOption value="platform" label="Platform" /></c-CCascaderOption>
      </c-CCascader>
    """


preview = CascaderParentSelection()
preview  # noqa: B018
````


## Disable unavailable paths

A disabled Option cannot be opened or selected, and an initial value cannot
pass through it. Root `disabled` also disables form inputs.


### Keep unavailable regions visible

[Open the rendered preview](/v/0.4.4/ui-library/components/cascader/_previews/disabled/)

````citry
# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CascaderDisabled(Component):
    template = """
      <c-CCascader>
        <c-CCascaderOption value="available" label="Available"><c-CCascaderOption value="one" label="Warehouse one" /></c-CCascaderOption>
        <c-CCascaderOption value="maintenance" label="Under maintenance" c-disabled="True"><c-CCascaderOption value="two" label="Warehouse two" /></c-CCascaderOption>
      </c-CCascader>
    """


preview = CascaderDisabled()
preview  # noqa: B018
````


## Support keyboard and constrained layouts

Arrow keys move within and across columns; Home, End, typeahead, Enter, Space,
Escape, and Tab follow the popup tree contract. Pointer activation, Enter, and
Space toggle a branch's child level without changing an already accepted leaf.
Use `aria_label` or `aria_labelledby` to give the trigger an application-specific
accessible name. Active columns sit side by side whenever their preferred width
fits the viewport. Only when they do not fit do they stack vertically at the
trigger width, avoiding page-level and nested horizontal scrollbars. While open,
the popup also shifts back inside the viewport when its trigger sits near an
inline edge. RTL reverses both column progression and branch indicators. The
labeled taxonomy deliberately uses wider columns to demonstrate the stacked
form in its constrained preview.


### Navigate a labeled taxonomy

[Open the rendered preview](/v/0.4.4/ui-library/components/cascader/_previews/accessibility/)

````citry
# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CascaderAccessibility(Component):
    template = """
      <label id="team-label">Owning team</label>
      <c-CCascader aria_labelledby="team-label" c-value="['product','experience','research']" size="lg" variant="soft" c-style="{'--cui-cascader-column-width': '14rem'}">
        <c-CCascaderOption value="product" label="Product">
          <c-CCascaderOption value="experience" label="Customer experience">
            <c-CCascaderOption value="research" label="Customer research" />
          </c-CCascaderOption>
        </c-CCascaderOption>
        <c-CCascaderOption value="operations" label="Operations">
          <c-CCascaderOption value="support" label="Customer support">
            <c-CCascaderOption value="priority" label="Priority support" />
          </c-CCascaderOption>
        </c-CCascaderOption>
      </c-CCascader>
    """


preview = CascaderAccessibility()
preview  # noqa: B018
````


Search, multiple paths, async child loading, and virtualized levels are not
silent modes of this API; they remain separate future contracts.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CCascader server inputs

Server inputs are passed in a template through `<c-CCascader ... />` or in Python through
`CCascader(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="cascader-input-ccascader-server-inputs-value"></span>`value` | `Sequence[str]` | `"()"` | Supplies the accepted continuous root-to-Option path. |
| <span id="cascader-input-ccascader-server-inputs-id"></span>`id` | `str | None` | generated | Sets root and related popup IDs. |
| <span id="cascader-input-ccascader-server-inputs-aria-label"></span>`aria_label` | `str | None` | `None` | Gives the trigger an explicit accessible name. |
| <span id="cascader-input-ccascader-server-inputs-aria-labelledby"></span>`aria_labelledby` | `str | None` | `None` | Associates the trigger with external labeling elements. |
| <span id="cascader-input-ccascader-server-inputs-name"></span>`name` | `str | None` | `None` | Emits one hidden input per accepted path segment. |
| <span id="cascader-input-ccascader-server-inputs-form"></span>`form` | `str | None` | `None` | Associates hidden inputs with an external form. |
| <span id="cascader-input-ccascader-server-inputs-placeholder"></span>`placeholder` | `str` | `"Choose an option"` | Supplies empty trigger text or overrides its catalog message. |
| <span id="cascader-input-ccascader-server-inputs-separator"></span>`separator` | `str` | `" / "` | Joins application Option labels in the trigger. |
| <span id="cascader-input-ccascader-server-inputs-change-on-select"></span>`change_on_select` | `bool` | `False` | Allows branches as complete selected paths. |
| <span id="cascader-input-ccascader-server-inputs-open"></span>`open` | `bool` | `False` | Supplies initial uncontrolled popup state. |
| <span id="cascader-input-ccascader-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables selection and form output. |
| <span id="cascader-input-ccascader-server-inputs-size"></span>`size` | `CCascaderSize` ([`CCascaderSize`](#cascader-interface-size)) | `"md"` | Selects trigger height. |
| <span id="cascader-input-ccascader-server-inputs-variant"></span>`variant` | `CCascaderVariant` ([`CCascaderVariant`](#cascader-interface-variant)) | `"outline"` | Selects trigger presentation. |
| <span id="cascader-input-ccascader-server-inputs-empty-label"></span>`empty_label` | `str` | `"No options"` | Overrides empty-hierarchy text. |
| <span id="cascader-input-ccascader-server-inputs-selected-label"></span>`selected_label` | `str` | `"Selected {path}"` | Overrides selected-path announcement and must retain path. |
| <span id="cascader-input-ccascader-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#cascader-interface-class-value)) | `None` | Adds root classes. |
| <span id="cascader-input-ccascader-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#cascader-interface-style-value)) | `None` | Adds root styles. |
| <span id="cascader-input-ccascader-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes. |

</div>

#### CCascader client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CCascader />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="cascader-input-ccascader-client-inputs-value"></span>`value` | `string[]` | Uncontrolled server path. | Controls the accepted path. |
| <span id="cascader-input-ccascader-client-inputs-open"></span>`open` | `boolean` | Uncontrolled server open state. | Controls popup visibility. |
| <span id="cascader-input-ccascader-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server value. | Reactively disables interaction and form inputs. |
| <span id="cascader-input-ccascader-client-inputs-on-value-change"></span>`onValueChange` | `function` | No component callback runs. | Receives selection requests. |
| <span id="cascader-input-ccascader-client-inputs-on-open-change"></span>`onOpenChange` | `function` | No component callback runs. | Receives popup requests. |

</div>

#### CCascaderOption server inputs

Server inputs are passed in a template through `<c-CCascaderOption ... />` or in Python
through `CCascaderOption(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="cascader-input-ccascader-option-server-inputs-value"></span>`value` | `str` | required | Supplies globally unique stable Option identity. |
| <span id="cascader-input-ccascader-option-server-inputs-label"></span>`label` | `str` | required | Supplies visible plain application-localized text. |
| <span id="cascader-input-ccascader-option-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Prevents opening or selecting this path. |
| <span id="cascader-input-ccascader-option-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#cascader-interface-class-value)) | `None` | Adds Option classes. |
| <span id="cascader-input-ccascader-option-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#cascader-interface-style-value)) | `None` | Adds Option styles. |
| <span id="cascader-input-ccascader-option-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed Option attributes. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CCascader slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="cascader-slot-ccascader-slots-default"></span>`default` | no | `{}` ([`CCascaderDefaultSlotData`](#cascader-interface-ccascader-default-slot)) | Empty hierarchy status; accepts root Option declarations only. |

</div>

#### CCascaderOption slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="cascader-slot-ccascader-option-slots-default"></span>`default` | no | `{parent_value, level}` ([`CCascaderOptionDefaultSlotData`](#cascader-interface-ccascader-option-slot)) | Leaf Option; accepts child Option declarations only. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CCascader events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="cascader-event-ccascader-events-value-change"></span>`onValueChange` | `(value: string[], detail: CCascaderValueChangeDetail) => void` ([`CCascaderValueChangeDetail`](#cascader-interface-ccascader-value-detail)) | An allowed Option is activated. | `{value, labels, previousValue, controlled, source, option, sourceEvent}` ([`CCascaderValueChangeDetail`](#cascader-interface-ccascader-value-detail)) | Commits only while uncontrolled. |
| <span id="cascader-event-ccascader-events-open-change"></span>`onOpenChange` | `(open: boolean, detail: CCascaderOpenChangeDetail) => void` ([`CCascaderOpenChangeDetail`](#cascader-interface-ccascader-open-detail)) | The popup is requested open or closed. | `{open, reason, sourceEvent}` ([`CCascaderOpenChangeDetail`](#cascader-interface-ccascader-open-detail)) | Commits only while uncontrolled. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CCascader CSS variables

Apply these variables to `CCascader` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="cascader-css-ccascader-css-width"></span>`--cui-cascader-width` | `length` | Trigger inline size. | `18rem` |
| <span id="cascader-css-ccascader-css-column"></span>`--cui-cascader-column-width` | `length` | Preferred width of one hierarchy column before measured-fit stacking. | `11rem` |
| <span id="cascader-css-ccascader-css-height"></span>`--cui-cascader-max-height` | `length` | Maximum column height. | `18rem` |
| <span id="cascader-css-ccascader-css-border"></span>`--cui-cascader-border` | `complete border` | Trigger popup and column boundaries. | `Adaptive 1px neutral` |
| <span id="cascader-css-ccascader-css-surface"></span>`--cui-cascader-surface` | `color` | Trigger and popup surface. | `Canvas` |
| <span id="cascader-css-ccascader-css-active"></span>`--cui-cascader-active-surface` | `color` | Active branch and selected Option. | `Adaptive indigo` |
| <span id="cascader-css-ccascader-css-radius"></span>`--cui-cascader-radius` | `length` | Trigger and popup corners. | `0.625rem` |
| <span id="cascader-css-ccascader-css-shadow"></span>`--cui-cascader-shadow` | `shadow` | Popup elevation. | `Soft elevation` |
| <span id="cascader-css-ccascader-css-focus"></span>`--cui-cascader-focus` | `color` | Trigger and Option focus. | `Highlight` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CCascader attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="cascader-attribute-ccascader-attributes-data-open"></span>`data-open` | Root | `present | absent` | Reflects effective popup visibility. |
| <span id="cascader-attribute-ccascader-attributes-data-disabled"></span>`data-disabled` | Root and Option | `present | absent` | Reflects unavailable interaction. |
| <span id="cascader-attribute-ccascader-attributes-data-size"></span>`data-size` | Root | `CCascaderSize` ([`CCascaderSize`](#cascader-interface-size)) | Reflects presentation size. |
| <span id="cascader-attribute-ccascader-attributes-data-variant"></span>`data-variant` | Root | `CCascaderVariant` ([`CCascaderVariant`](#cascader-interface-variant)) | Reflects presentation variant. |
| <span id="cascader-attribute-ccascader-attributes-data-active"></span>`data-active` | Option | `present | absent` | Marks the branch whose child column is visible. |
| <span id="cascader-attribute-ccascader-attributes-data-selected"></span>`data-selected` | Option | `present | absent` | Marks the accepted path endpoint. |
| <span id="cascader-attribute-ccascader-attributes-data-value"></span>`data-value` | Option | `string` | Exposes stable Option identity. |
| <span id="cascader-attribute-ccascader-attributes-data-level"></span>`data-level` | Option | `positive integer string` | Exposes one-based hierarchy depth. |
| <span id="cascader-attribute-ccascader-attributes-aria-level"></span>`aria-level` | Option | `positive integer string` | Preserves hierarchy depth while visual columns are siblings. |
| <span id="cascader-attribute-ccascader-attributes-aria-posinset"></span>`aria-posinset` | Option | `positive integer string` | Exposes the Option position in its logical group. |
| <span id="cascader-attribute-ccascader-attributes-aria-setsize"></span>`aria-setsize` | Option | `positive integer string` | Exposes the number of Options in its logical group. |
| <span id="cascader-attribute-ccascader-attributes-aria-owns"></span>`aria-owns` | Branch Option | `ID reference` | Owns the sibling visual group that contains its children. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CCascader selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="cascader-selector-ccascader-selectors-root"></span>`[data-citry-ui-part="cascader"]` | Root | State and theme destination. |
| <span id="cascader-selector-ccascader-selectors-trigger"></span>`[data-citry-ui-part="trigger"]` | Native button | Accepted value and popup control. |
| <span id="cascader-selector-ccascader-selectors-value"></span>`[data-citry-ui-part="value"]` | Span | Selected path or placeholder. |
| <span id="cascader-selector-ccascader-selectors-indicator"></span>`[data-citry-ui-part="indicator"]` | Decorative span | Indicates popup disclosure. |
| <span id="cascader-selector-ccascader-selectors-popup"></span>`[data-citry-ui-part="popup"]` | Popup div | Responsive visual-column container. |
| <span id="cascader-selector-ccascader-selectors-tree"></span>`[data-citry-ui-part="tree"]` | Root tree | Composite keyboard owner. |
| <span id="cascader-selector-ccascader-selectors-group"></span>`[data-citry-ui-part="group"]` | Logically owned sibling group | One child column. |
| <span id="cascader-selector-ccascader-selectors-option"></span>`[data-citry-ui-part="option"]` | Treeitem | Focus branch and selection unit. |
| <span id="cascader-selector-ccascader-selectors-option-row"></span>`[data-citry-ui-part="option-row"]` | Div | Visible Option surface. |
| <span id="cascader-selector-ccascader-selectors-option-label"></span>`[data-citry-ui-part="option-label"]` | Span | Application Option label. |
| <span id="cascader-selector-ccascader-selectors-option-indicator"></span>`[data-citry-ui-part="option-indicator"]` | Decorative span | Indicates children in the current inline direction. |
| <span id="cascader-selector-ccascader-selectors-empty"></span>`[data-citry-ui-part="empty"]` | Paragraph | Empty-hierarchy status. |
| <span id="cascader-selector-ccascader-selectors-inputs"></span>`[data-citry-ui-part="inputs"]` | Hidden span | Native ordered path controls. |
| <span id="cascader-selector-ccascader-selectors-status"></span>`[data-citry-ui-part="status"]` | Polite status | Selection announcement. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="cascader-interface-size"></span>`CCascaderSize` | `Literal["sm", "md", "lg"]` |
| <span id="cascader-interface-variant"></span>`CCascaderVariant` | `Literal["outline", "soft", "plain"]` |
| <span id="cascader-interface-source"></span>`CCascaderChangeSource` | `Literal["pointer", "keyboard", "reset"]` |
| <span id="cascader-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="cascader-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="cascader-interface-ccascader-default-slot"></span>

#### `CCascaderDefaultSlotData`

Empty dataclass: `{}`.

<span id="cascader-interface-ccascader-option-slot"></span>

#### `CCascaderOptionDefaultSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="cascader-interface-ccascader-option-slot-parent"></span>`parent_value` | `str` | - | Parent Option value. |
| <span id="cascader-interface-ccascader-option-slot-level"></span>`level` | `int` | - | One-based parent level. |

</div>

<span id="cascader-interface-ccascader-value-detail"></span>

#### `CCascaderValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="cascader-interface-ccascader-value-detail-value"></span>`value` | `list[str]` | - | Requested path. |
| <span id="cascader-interface-ccascader-value-detail-labels"></span>`labels` | `list[str]` | - | Application labels for that path. |
| <span id="cascader-interface-ccascader-value-detail-previous"></span>`previousValue` | `list[str]` | - | Previously accepted path. |
| <span id="cascader-interface-ccascader-value-detail-controlled"></span>`controlled` | `bool` | - | Whether value was supplied as a client prop. |
| <span id="cascader-interface-ccascader-value-detail-source"></span>`source` | `CCascaderChangeSource` ([`CCascaderChangeSource`](#cascader-interface-source)) | - | Request interaction source. |
| <span id="cascader-interface-ccascader-value-detail-option"></span>`option` | `object` | - | Requested treeitem element. |
| <span id="cascader-interface-ccascader-value-detail-source-event"></span>`sourceEvent` | `object` | - | Native source Event. |

</div>

<span id="cascader-interface-ccascader-open-detail"></span>

#### `CCascaderOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="cascader-interface-ccascader-open-detail-open"></span>`open` | `bool` | - | Requested popup visibility. |
| <span id="cascader-interface-ccascader-open-detail-reason"></span>`reason` | `str` | - | Trigger selection escape tab or outside. |
| <span id="cascader-interface-ccascader-open-detail-source-event"></span>`sourceEvent` | `object` | - | Native source Event. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CCascader translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="cascader-translation-ccascader-translations-placeholder"></span>`citry-ui-cascader-placeholder` | Labels an empty trigger. | `None.` | `placeholder` | Runtime `i18n.bind()` while the accepted path is empty. |
| <span id="cascader-translation-ccascader-translations-empty"></span>`citry-ui-cascader-empty` | Labels an empty hierarchy. | `None.` | `empty_label` | Stable `$c-tr` text. |
| <span id="cascader-translation-ccascader-translations-selected"></span>`citry-ui-cascader-selected` | Announces an accepted path. | `path: str` | `selected_label` with `{path}` | Browser one-shot `i18n.tr()` with a server-localized fallback pattern. |

</div>