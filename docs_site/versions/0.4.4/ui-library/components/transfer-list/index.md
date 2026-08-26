---
title: Transfer List
url: https://citry.dev/v/0.4.4/ui-library/components/transfer-list/
description: "Build an ordered chosen set with an accessible, form-capable Citry UI PickList."
---
# Transfer List

Use `CTransferList` when people need to compare a finite set of available
items with an ordered chosen set. `CTransferListItem` declares stable values,
plain accessible labels, optional rich presentation, and disabled state.

## Move items between two lists

The enhanced component uses two labeled multi-select listboxes and explicit
buttons. Without JavaScript, the same values remain available through a native
`select[multiple]` form control.


### Choose and order reviewers

[Open the rendered preview](/v/0.4.4/ui-library/components/transfer-list/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TransferListAtAGlance(Component):
    template = """
      <c-CTransferList name="reviewers" c-value="['grace']">
        <c-CTransferListItem value="ada" label="Ada Lovelace" />
        <c-CTransferListItem value="grace" label="Grace Hopper" />
        <c-CTransferListItem value="katherine" label="Katherine Johnson" />
        <c-CTransferListItem value="margaret" label="Margaret Hamilton" />
      </c-CTransferList>
    """


preview = TransferListAtAGlance()
preview  # noqa: B018
````


Selection inside a pane is separate from the chosen form value. Select one or
more enabled options, then use Add or Remove. The Add all and Remove all
buttons can be omitted with `show_move_all=False`. Chosen items retain the
exact order in `value` and in submitted form entries.

## Render rich, noninteractive items

The Item default slot can replace its visible label with server-rendered
presentation. Keep `label` plain and descriptive because native fallback,
typeahead, and assistive naming use it.


### Render rich Transfer List items

[Open the rendered preview](/v/0.4.4/ui-library/components/transfer-list/_previews/rich-items/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TransferListRichItems(Component):
    template = """
      <c-CTransferList name="owners" c-value="['platform']">
        <c-CTransferListItem value="platform" label="Platform team">
          <strong>Platform</strong><br /><small>Runtime and release infrastructure</small>
        </c-CTransferListItem>
        <c-CTransferListItem value="design" label="Design systems team">
          <strong>Design systems</strong><br /><small>Components, tokens, and accessibility</small>
        </c-CTransferListItem>
        <c-CTransferListItem value="security" label="Security team" c-disabled="True">
          <strong>Security</strong><br /><small>Managed by policy</small>
        </c-CTransferListItem>
      </c-CTransferList>
    """


preview = TransferListRichItems()
preview  # noqa: B018
````


Do not place links, buttons, inputs, editable content, or other focus stops
inside an Item. The family follows the listbox interaction model and rejects
interactive descendants during enhancement.

## Control chosen values from Alpine

Pass `value` and `onValueChange` through `$c-props` for controlled state.
Transfer and reorder actions become requests: the visible order changes only
after the owner accepts the proposed array.


### Control a Transfer List

[Open the rendered preview](/v/0.4.4/ui-library/components/transfer-list/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TransferListControlled(Component):
    template = """
      <section x-data="{chosen:['grace'],last:'No request'}">
        <c-CTransferList
          $c-props="{
            value:chosen,
            onValueChange:(next,detail)=>{chosen=next;last=`${detail.source}: ${next.join(', ') || 'none'}`},
          }"
        >
          <c-CTransferListItem value="ada" label="Ada" />
          <c-CTransferListItem value="grace" label="Grace" />
          <c-CTransferListItem value="katherine" label="Katherine" />
        </c-CTransferList>
        <output x-text="last">No request</output>
      </section>
    """


preview = TransferListControlled()
preview  # noqa: B018
````


Omit client `value`, or set it to `null`, for uncontrolled behavior. In that
mode an accepted action updates the native form owner, emits native `input`
then `change`, and calls `onValueChange`.

## Submit and validate forms

Set `name` to submit one entry per chosen item in chosen order. `form` can
associate the control with a non-ancestor form. `required=True` requires at
least one chosen value and moves focus to the chosen list when native
validation fails.


### Submit a required ordered selection

[Open the rendered preview](/v/0.4.4/ui-library/components/transfer-list/_previews/forms/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TransferListForm(Component):
    template = """
      <form x-data="{result:'Not submitted'}"
        @submit.prevent="result=[...new FormData($el).getAll('reviewers')].join(' → ')"
      >
        <c-CTransferList name="reviewers" c-required="True" c-value="['ada']">
          <c-CTransferListItem value="ada" label="Ada" />
          <c-CTransferListItem value="grace" label="Grace" />
          <c-CTransferListItem value="katherine" label="Katherine" />
        </c-CTransferList>
        <p><button type="submit">Submit order</button> <button type="reset">Reset</button></p>
        <output x-text="result">Not submitted</output>
      </form>
    """


preview = TransferListForm()
preview  # noqa: B018
````


Native reset restores the server-rendered value. A disabled Item cannot be
moved or reordered. An initially chosen disabled Item remains submitted by
the native fallback through an ordered hidden option proxy.

## Keyboard and accessibility

Each pane has one tab stop and an active descendant. Arrow keys, Home, End,
typeahead, Space, Enter, Shift+Arrow range selection, and Ctrl/Cmd+A are
available. Explicit transfer and reorder buttons remain reachable in normal
tab order, so drag and drop is never required.


### Use disabled items and accessible labels

[Open the rendered preview](/v/0.4.4/ui-library/components/transfer-list/_previews/accessibility/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TransferListAccessibility(Component):
    template = """
      <c-CTransferList
        name="permissions"
        available_label="Available permissions"
        chosen_label="Granted permissions"
        c-value="['audit','read']"
      >
        <c-CTransferListItem value="read" label="Read records" />
        <c-CTransferListItem value="write" label="Write records" />
        <c-CTransferListItem value="audit" label="Audit access required by policy" c-disabled="True">
          <strong>Audit access</strong><br /><small>Required by policy; cannot be removed</small>
        </c-CTransferListItem>
      </c-CTransferList>
    """


preview = TransferListAccessibility()
preview  # noqa: B018
````


The family announces accepted moves and reorders through a polite live region.
Pane labels, counts, controls, empty states, announcements, and required
validation use Citry UI catalog messages by default. Any explicit `*_label`
input belongs to the caller and does not switch with the Citry client locale.

## Responsive layout and customization

The three-column layout stacks automatically in a narrow container and uses
logical CSS properties for RTL. Customize the root and Items with `class_`,
`style`, and `attrs`, or use the documented public variables and part
selectors.


### Customize Transfer List

[Open the rendered preview](/v/0.4.4/ui-library/components/transfer-list/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TransferListCustomization(Component):
    template = """
      <c-CTransferList class_="brand-transfer" size="lg" c-value="['stable']">
        <c-CTransferListItem value="alpha" label="Alpha channel" />
        <c-CTransferListItem value="beta" label="Beta channel" />
        <c-CTransferListItem value="stable" label="Stable channel" />
      </c-CTransferList>
    """
    css = """
      .brand-transfer {
        --cui-transfer-list-selected: color-mix(in srgb, MediumPurple 25%, Canvas);
        --cui-transfer-list-focus: MediumPurple;
        --cui-transfer-list-radius: 1rem;
      }
    """


preview = TransferListCustomization()
preview  # noqa: B018
````


`size` changes the default list height. Forced colors preserve selected-state
outlines, reduced-motion environments disable component motion, and print
hides action controls while retaining both supplied panes.

## Scope boundaries

This first family owns a complete finite server-rendered collection. It does
not fetch, filter, virtualize, group into a tree, expose read-only mode, or
provide drag and drop. Use `CMultiSelect` for compact selection and compose
application state with `CVirtualWindow` when the collection cannot be fully
rendered.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CTransferList server inputs

Server inputs are passed in a template through `<c-CTransferList ... />` or in Python
through `CTransferList(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="transfer-list-input-ctransfer-list-server-inputs-id"></span>`id` | `str | None` | generated | Sets the root ID and bases stable listbox and option IDs. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-value"></span>`value` | `Sequence[str]` | `"()"` | Sets the ordered initial chosen values; every unique value must name one Item. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the repeated native form-entry name. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-form"></span>`form` | `str | None` | `None` | Associates native and enhanced form values with an external Form ID. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-required"></span>`required` | `bool` | `False` | Requires at least one chosen value. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables list selection controls and form contribution. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-show-move-all"></span>`show_move_all` | `bool` | `True` | Shows Add all and Remove all controls. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-show-reorder"></span>`show_reorder` | `bool` | `True` | Shows chosen-order controls. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-size"></span>`size` | `CTransferListSize` ([`CTransferListSize`](#transfer-list-interface-size)) | `"md"` | Selects compact default or spacious list height. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-available-label"></span>`available_label` | `str` | `"Available items"` | Overrides the localized available-pane title. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-chosen-label"></span>`chosen_label` | `str` | `"Chosen items"` | Overrides the localized chosen-pane title and native fallback label. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-available-empty-label"></span>`available_empty_label` | `str` | `"No available items"` | Overrides the localized available empty state. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-chosen-empty-label"></span>`chosen_empty_label` | `str` | `"No chosen items"` | Overrides the localized chosen empty state. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-count-label"></span>`count_label` | `str` | `"{selected} of {total} selected"` | Overrides pane counts and must retain both named placeholders. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-transfer-controls-label"></span>`transfer_controls_label` | `str` | `"Transfer controls"` | Overrides the transfer toolbar accessible name. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-add-label"></span>`add_label` | `str` | `"Add selected"` | Overrides the Add selected action. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-add-all-label"></span>`add_all_label` | `str` | `"Add all"` | Overrides the Add all action. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-remove-label"></span>`remove_label` | `str` | `"Remove selected"` | Overrides the Remove selected action. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-remove-all-label"></span>`remove_all_label` | `str` | `"Remove all"` | Overrides the Remove all action. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-reorder-controls-label"></span>`reorder_controls_label` | `str` | `"Chosen item order"` | Overrides the reorder toolbar accessible name. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-move-top-label"></span>`move_top_label` | `str` | `"Move to top"` | Overrides the Move to top action. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-move-up-label"></span>`move_up_label` | `str` | `"Move up"` | Overrides the Move up action. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-move-down-label"></span>`move_down_label` | `str` | `"Move down"` | Overrides the Move down action. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-move-bottom-label"></span>`move_bottom_label` | `str` | `"Move to bottom"` | Overrides the Move to bottom action. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-added-label"></span>`added_label` | `str` | `"{count} items added"` | Overrides multi-item Add announcements and must retain count. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-removed-label"></span>`removed_label` | `str` | `"{count} items removed"` | Overrides multi-item Remove announcements and must retain count. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-reordered-label"></span>`reordered_label` | `str` | `"{count} items reordered"` | Overrides multi-item reorder announcements and must retain count. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-required-label"></span>`required_label` | `str` | `"Choose at least one item"` | Overrides the required-validation announcement. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#transfer-list-interface-class-value)) | `None` | Adds classes to the root. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#transfer-list-interface-style-value)) | `None` | Adds root styles before owned theme variables. |
| <span id="transfer-list-input-ctransfer-list-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes without replacing owned form semantics state or runtime markers. |

</div>

#### CTransferList client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CTransferList />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="transfer-list-input-ctransfer-list-client-inputs-value"></span>`value` | `string[] | null` | Omission or null releases control to the committed value. | Controls the exact ordered chosen values while supplied. |
| <span id="transfer-list-input-ctransfer-list-client-inputs-required"></span>`required` | `boolean` | Uses the server value. | Reactively changes required validity. |
| <span id="transfer-list-input-ctransfer-list-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server and Fieldset state. | Reactively disables interaction and form contribution. |
| <span id="transfer-list-input-ctransfer-list-client-inputs-on-value-change"></span>`onValueChange` | `function` | No component callback runs. | Receives transfer reorder and reset requests. |

</div>

#### CTransferListItem server inputs

Server inputs are passed in a template through `<c-CTransferListItem ... />` or in Python
through `CTransferListItem(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="transfer-list-input-ctransfer-list-item-server-inputs-value"></span>`value` | `str` | required | Supplies nonempty unique stable identity and submitted value. |
| <span id="transfer-list-input-ctransfer-list-item-server-inputs-label"></span>`label` | `str` | required | Supplies native fallback typeahead and accessible text. |
| <span id="transfer-list-input-ctransfer-list-item-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Prevents selection transfer and reorder while preserving an initial chosen value. |
| <span id="transfer-list-input-ctransfer-list-item-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#transfer-list-interface-class-value)) | `None` | Adds classes to the enhanced Option. |
| <span id="transfer-list-input-ctransfer-list-item-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#transfer-list-interface-style-value)) | `None` | Adds styles to the enhanced Option. |
| <span id="transfer-list-input-ctransfer-list-item-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed Option attributes without replacing owned semantics identity or state. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CTransferList slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="transfer-list-slot-ctransfer-list-slots-default"></span>`default` | no | `{}` ([`CTransferListDefaultSlotData`](#transfer-list-interface-ctransfer-list-default-slot-data)) | Empty collection; accepts only CTransferListItem declarations. |

</div>

#### CTransferListItem slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="transfer-list-slot-ctransfer-list-item-slots-default"></span>`default` | no | `{value, label, disabled, in_target, index}` ([`CTransferListItemDefaultSlotData`](#transfer-list-interface-ctransfer-list-item-default-slot-data)) | Plain label text. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CTransferList events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="transfer-list-event-ctransfer-list-events-value-change"></span>`onValueChange` | `(value: string[], detail: CTransferListChangeDetail) => void` ([`CTransferListChangeDetail`](#transfer-list-interface-ctransfer-list-change-detail)) | A transfer reorder reset or accepted client reconciliation requests another ordered value. | `{value, previousValue, moved, source, controlled, sourceEvent}` ([`CTransferListChangeDetail`](#transfer-list-interface-ctransfer-list-change-detail)) | Uncontrolled state commits and emits native input/change first; controlled state is request-only until accepted. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CTransferList CSS variables

Apply these variables to `CTransferList` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="transfer-list-css-ctransfer-list-css-variables-pane-size"></span>`--cui-transfer-list-pane-size` | `length` | Native fallback and pane inline-size preference. | `15rem` |
| <span id="transfer-list-css-ctransfer-list-css-variables-list-size"></span>`--cui-transfer-list-list-size` | `length` | Enhanced listbox block size. | `sm 11rem; md 15rem; lg 20rem` |
| <span id="transfer-list-css-ctransfer-list-css-variables-gap"></span>`--cui-transfer-list-gap` | `length` | Pane and control spacing. | `0.75rem` |
| <span id="transfer-list-css-ctransfer-list-css-variables-border"></span>`--cui-transfer-list-border` | `complete border value` | Pane control and Button borders. | `Adaptive 1px solid neutral` |
| <span id="transfer-list-css-ctransfer-list-css-variables-radius"></span>`--cui-transfer-list-radius` | `length` | Pane and native fallback corners. | `0.625rem` |
| <span id="transfer-list-css-ctransfer-list-css-variables-surface"></span>`--cui-transfer-list-surface` | `color` | Pane native fallback and Button surfaces. | `Canvas` |
| <span id="transfer-list-css-ctransfer-list-css-variables-selected"></span>`--cui-transfer-list-selected` | `color` | Selected Option background. | `Adaptive blue` |
| <span id="transfer-list-css-ctransfer-list-css-variables-hover"></span>`--cui-transfer-list-hover` | `color` | Hovered Option background. | `Adaptive neutral` |
| <span id="transfer-list-css-ctransfer-list-css-variables-focus"></span>`--cui-transfer-list-focus` | `color` | Listbox and Button focus outline. | `Highlight` |
| <span id="transfer-list-css-ctransfer-list-css-variables-disabled-opacity"></span>`--cui-transfer-list-disabled-opacity` | `number` | Disabled root Option and Button opacity. | `0.55` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CTransferList attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="transfer-list-attribute-ctransfer-list-attributes-role-listbox"></span>`role` | Available and chosen listbox divs | `listbox` | Exposes each enhanced pane as a selectable collection. |
| <span id="transfer-list-attribute-ctransfer-list-attributes-aria-multiselectable"></span>`aria-multiselectable` | Both listboxes | `true` | Declares independent multi-selection. |
| <span id="transfer-list-attribute-ctransfer-list-attributes-aria-activedescendant"></span>`aria-activedescendant` | Focused listbox | `IDREF | absent` | Identifies the active Option while DOM focus remains on the listbox. |
| <span id="transfer-list-attribute-ctransfer-list-attributes-role-option"></span>`role` | Enhanced Item div | `option` | Exposes one declared choice. |
| <span id="transfer-list-attribute-ctransfer-list-attributes-aria-selected"></span>`aria-selected` | Enhanced Item div | `boolean-string` | Reflects ephemeral pane selection rather than chosen membership. |
| <span id="transfer-list-attribute-ctransfer-list-attributes-aria-disabled"></span>`aria-disabled` | Root listboxes and disabled Items | `boolean-string` | Reflects effective unavailability. |
| <span id="transfer-list-attribute-ctransfer-list-attributes-aria-invalid"></span>`aria-invalid` | Root | `true | absent` | Marks a failed required validity check. |
| <span id="transfer-list-attribute-ctransfer-list-attributes-data-value"></span>`data-value` | Enhanced Item div | `string` | Exposes stable identity. |
| <span id="transfer-list-attribute-ctransfer-list-attributes-data-selected"></span>`data-selected` | Enhanced Item div | `present | absent` | Reflects ephemeral pane selection. |
| <span id="transfer-list-attribute-ctransfer-list-attributes-data-disabled"></span>`data-disabled` | Root and disabled Items | `present | absent` | Reflects effective unavailability. |
| <span id="transfer-list-attribute-ctransfer-list-attributes-data-required"></span>`data-required` | Root | `present | absent` | Reflects required validity. |
| <span id="transfer-list-attribute-ctransfer-list-attributes-data-invalid"></span>`data-invalid` | Root | `present | absent` | Reflects a failed native validity check. |
| <span id="transfer-list-attribute-ctransfer-list-attributes-data-size"></span>`data-size` | Root | `CTransferListSize` ([`CTransferListSize`](#transfer-list-interface-size)) | Mirrors list-height profile. |
| <span id="transfer-list-attribute-ctransfer-list-attributes-data-available-empty"></span>`data-available-empty` | Root | `present | absent` | Marks no available Items. |
| <span id="transfer-list-attribute-ctransfer-list-attributes-data-chosen-empty"></span>`data-chosen-empty` | Root | `present | absent` | Marks no chosen Items. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CTransferList selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="transfer-list-selector-ctransfer-list-selectors-transfer-list"></span>`[data-citry-ui-part="transfer-list"]` | Root div | State reflections attrs and theme destination. |
| <span id="transfer-list-selector-ctransfer-list-selectors-native"></span>`[data-citry-ui-part="native"]` | Native select multiple | Progressive fallback validity reset and initial form owner. |
| <span id="transfer-list-selector-ctransfer-list-selectors-control"></span>`[data-citry-ui-part="control"]` | Enhanced grid | Contains both panes and transfer controls. |
| <span id="transfer-list-selector-ctransfer-list-selectors-pane"></span>`[data-citry-ui-part="pane"]` | Available or chosen section | Pane surface. |
| <span id="transfer-list-selector-ctransfer-list-selectors-pane-header"></span>`[data-citry-ui-part="pane-header"]` | Pane header | Groups title and selection count. |
| <span id="transfer-list-selector-ctransfer-list-selectors-pane-title"></span>`[data-citry-ui-part="pane-title"]` | Pane h3 | Visible listbox label. |
| <span id="transfer-list-selector-ctransfer-list-selectors-count"></span>`[data-citry-ui-part="count"]` | Count span | Localized selected and total summary. |
| <span id="transfer-list-selector-ctransfer-list-selectors-listbox"></span>`[data-citry-ui-part="listbox"]` | Pane listbox div | Focus selection and Item-scroll owner. |
| <span id="transfer-list-selector-ctransfer-list-selectors-option"></span>`[data-citry-ui-part="option"]` | Item div | Rich presentation selection and stable Item customization. |
| <span id="transfer-list-selector-ctransfer-list-selectors-empty"></span>`[data-citry-ui-part="empty"]` | Pane paragraph | Localized empty state. |
| <span id="transfer-list-selector-ctransfer-list-selectors-transfer-controls"></span>`[data-citry-ui-part="transfer-controls"]` | Transfer toolbar | Add and Remove actions. |
| <span id="transfer-list-selector-ctransfer-list-selectors-reorder-controls"></span>`[data-citry-ui-part="reorder-controls"]` | Reorder toolbar | Chosen-order actions. |
| <span id="transfer-list-selector-ctransfer-list-selectors-button"></span>`[data-citry-ui-part="button"]` | Native action Button | Transfer and reorder actions. |
| <span id="transfer-list-selector-ctransfer-list-selectors-status"></span>`[data-citry-ui-part="status"]` | Visually hidden polite live region | Accepted action and validation announcements. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="transfer-list-interface-size"></span>`CTransferListSize` | `Literal["sm", "md", "lg"]` |
| <span id="transfer-list-interface-change-source"></span>`CTransferListChangeSource` | `Literal["add", "add-all", "remove", "remove-all", "move-top", "move-up", "move-down", "move-bottom", "reset", "client"]` |
| <span id="transfer-list-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="transfer-list-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="transfer-list-interface-ctransfer-list-default-slot-data"></span>

#### `CTransferListDefaultSlotData`

Empty dataclass: `{}`.

<span id="transfer-list-interface-ctransfer-list-item-default-slot-data"></span>

#### `CTransferListItemDefaultSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="transfer-list-interface-ctransfer-list-item-default-slot-data-value"></span>`value` | `str` | - | Stable declared Item value. |
| <span id="transfer-list-interface-ctransfer-list-item-default-slot-data-label"></span>`label` | `str` | - | Plain accessible and typeahead label. |
| <span id="transfer-list-interface-ctransfer-list-item-default-slot-data-disabled"></span>`disabled` | `bool` | - | Declared disabled state. |
| <span id="transfer-list-interface-ctransfer-list-item-default-slot-data-in-target"></span>`in_target` | `bool` | - | Whether the Item is initially chosen. |
| <span id="transfer-list-interface-ctransfer-list-item-default-slot-data-index"></span>`index` | `int` | - | Initial zero-based index in its pane. |

</div>

<span id="transfer-list-interface-ctransfer-list-change-detail"></span>

#### `CTransferListChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="transfer-list-interface-ctransfer-list-change-detail-value"></span>`value` | `list[str]` | - | Requested or committed ordered chosen values. |
| <span id="transfer-list-interface-ctransfer-list-change-detail-previous-value"></span>`previousValue` | `list[str]` | - | Effective ordered chosen values before the request. |
| <span id="transfer-list-interface-ctransfer-list-change-detail-moved"></span>`moved` | `list[str]` | - | Values directly affected by the action in their action order. |
| <span id="transfer-list-interface-ctransfer-list-change-detail-source"></span>`source` | `CTransferListChangeSource` ([`CTransferListChangeSource`](#transfer-list-interface-change-source)) | - | Transfer reorder reset or client cause. |
| <span id="transfer-list-interface-ctransfer-list-change-detail-controlled"></span>`controlled` | `bool` | - | Whether client value currently owns chosen state. |
| <span id="transfer-list-interface-ctransfer-list-change-detail-source-event"></span>`sourceEvent` | `object | None` | - | Native source Event or null for client reconciliation. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CTransferList translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="transfer-list-translation-ctransfer-list-translations-available"></span>`citry-ui-transfer-list-available` | Titles the available pane. | `None.` | `available_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="transfer-list-translation-ctransfer-list-translations-chosen"></span>`citry-ui-transfer-list-chosen` | Titles the chosen pane and native fallback. | `None.` | `chosen_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="transfer-list-translation-ctransfer-list-translations-available-empty"></span>`citry-ui-transfer-list-available-empty` | Describes an empty available pane. | `None.` | `available_empty_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="transfer-list-translation-ctransfer-list-translations-chosen-empty"></span>`citry-ui-transfer-list-chosen-empty` | Describes an empty chosen pane. | `None.` | `chosen_empty_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="transfer-list-translation-ctransfer-list-translations-count"></span>`citry-ui-transfer-list-count` | Summarizes selected and total Items in one pane. | `selected: str; total: str` | `count_label` with `{selected}` and `{total}` | Two `i18n.bind()` registrations update when selection totals or locale change. |
| <span id="transfer-list-translation-ctransfer-list-translations-transfer-controls"></span>`citry-ui-transfer-list-transfer-controls` | Names the transfer toolbar. | `None.` | `transfer_controls_label` | Stable `$c-tr` attribute follows client locale changes. |
| <span id="transfer-list-translation-ctransfer-list-translations-add"></span>`citry-ui-transfer-list-add` | Labels the Add selected action. | `None.` | `add_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="transfer-list-translation-ctransfer-list-translations-add-all"></span>`citry-ui-transfer-list-add-all` | Labels the Add all action. | `None.` | `add_all_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="transfer-list-translation-ctransfer-list-translations-remove"></span>`citry-ui-transfer-list-remove` | Labels the Remove selected action. | `None.` | `remove_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="transfer-list-translation-ctransfer-list-translations-remove-all"></span>`citry-ui-transfer-list-remove-all` | Labels the Remove all action. | `None.` | `remove_all_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="transfer-list-translation-ctransfer-list-translations-reorder-controls"></span>`citry-ui-transfer-list-reorder-controls` | Names the chosen-order toolbar. | `None.` | `reorder_controls_label` | Stable `$c-tr` attribute follows client locale changes. |
| <span id="transfer-list-translation-ctransfer-list-translations-move-top"></span>`citry-ui-transfer-list-move-top` | Labels the Move to top action. | `None.` | `move_top_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="transfer-list-translation-ctransfer-list-translations-move-up"></span>`citry-ui-transfer-list-move-up` | Labels the Move up action. | `None.` | `move_up_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="transfer-list-translation-ctransfer-list-translations-move-down"></span>`citry-ui-transfer-list-move-down` | Labels the Move down action. | `None.` | `move_down_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="transfer-list-translation-ctransfer-list-translations-move-bottom"></span>`citry-ui-transfer-list-move-bottom` | Labels the Move to bottom action. | `None.` | `move_bottom_label` | Stable `$c-tr` text follows client locale changes. |
| <span id="transfer-list-translation-ctransfer-list-translations-added-one"></span>`citry-ui-transfer-list-added-one` | Announces one accepted addition. | `None.` | `added_label` formats the fallback | One-shot `i18n.tr()` writes the live region. |
| <span id="transfer-list-translation-ctransfer-list-translations-added"></span>`citry-ui-transfer-list-added` | Announces multiple accepted additions. | `count: str` | `added_label` with `{count}` | One-shot `i18n.tr()` writes the live region. |
| <span id="transfer-list-translation-ctransfer-list-translations-removed-one"></span>`citry-ui-transfer-list-removed-one` | Announces one accepted removal. | `None.` | `removed_label` formats the fallback | One-shot `i18n.tr()` writes the live region. |
| <span id="transfer-list-translation-ctransfer-list-translations-removed"></span>`citry-ui-transfer-list-removed` | Announces multiple accepted removals. | `count: str` | `removed_label` with `{count}` | One-shot `i18n.tr()` writes the live region. |
| <span id="transfer-list-translation-ctransfer-list-translations-reordered-one"></span>`citry-ui-transfer-list-reordered-one` | Announces one accepted reorder. | `None.` | `reordered_label` formats the fallback | One-shot `i18n.tr()` writes the live region. |
| <span id="transfer-list-translation-ctransfer-list-translations-reordered"></span>`citry-ui-transfer-list-reordered` | Announces multiple accepted reorders. | `count: str` | `reordered_label` with `{count}` | One-shot `i18n.tr()` writes the live region. |
| <span id="transfer-list-translation-ctransfer-list-translations-required"></span>`citry-ui-transfer-list-required` | Announces failed required validity. | `None.` | `required_label` | One-shot `i18n.tr()` writes the live region. |

</div>