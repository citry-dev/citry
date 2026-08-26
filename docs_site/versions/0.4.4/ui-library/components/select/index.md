---
title: Select
url: https://citry.dev/v/0.4.4/ui-library/components/select/
description: "Choose one value from a compact, styled form control."
---
# Select

Use `CSelect` when people choose one value and the collection should remain
compact until opened. The component progressively enhances a native Select,
so form submission and reset retain native behavior.

## Select at a glance


### Select at a glance

[Open the rendered preview](/v/0.4.4/ui-library/components/select/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class SelectAtAGlance(Component):
    template = """
      <c-CField>
        <c-fill name="label">Workspace</c-fill>
        <c-fill name="description">Choose where new observations belong.</c-fill>
        <c-fill name="default">
          <c-CSelect c-options="options" placeholder="Choose a workspace" value="atlas" />
        </c-fill>
      </c-CField>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CSelectOption("atlas", "Atlas research", "12 collaborators"),
                CSelectOption("aurora", "Aurora field notes", "7 collaborators"),
                CSelectOption("archive", "Archived studies", disabled=True),
            ]
        }


preview = SelectAtAGlance()
preview  # noqa: B018
````


## Submit a value


### Submit a Select

[Open the rendered preview](/v/0.4.4/ui-library/components/select/_previews/forms/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class SelectForm(Component):
    template = """
      <form x-data @submit.prevent="result = Array.from(new FormData($event.target).entries())">
        <c-CField required>
          <c-fill name="label">Review status</c-fill>
          <c-fill name="default">
            <c-CSelect c-options="options" placeholder="Choose a status" name="status" />
          </c-fill>
        </c-CField>
        <c-CButton type="submit">Save</c-CButton>
        <c-CButton type="reset" variant="ghost">Reset</c-CButton>
        <output x-text="JSON.stringify(result)"></output>
      </form>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CSelectOption("draft", "Draft"), CSelectOption("review", "Ready for review")]}


preview = SelectForm()
preview  # noqa: B018
````


## Group related options


### Group options

[Open the rendered preview](/v/0.4.4/ui-library/components/select/_previews/groups/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class GroupedSelect(Component):
    template = """
      <c-CSelect
        c-options="options"
        placeholder="Choose a destination"
        c-trigger_attrs="{'aria-label':'Destination'}"
      />
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CSelectOption("oslo", "Oslo", group="Europe"),
                CSelectOption("prague", "Prague", group="Europe"),
                CSelectOption("kyoto", "Kyoto", group="Asia"),
                CSelectOption("seoul", "Seoul", group="Asia"),
            ]
        }


preview = GroupedSelect()
preview  # noqa: B018
````


## Control selection


### Control selection

[Open the rendered preview](/v/0.4.4/ui-library/components/select/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class ControlledSelect(Component):
    template = """
      <div x-data>
        <c-CSelect
          c-options="options"
          placeholder="Choose a status"
          value="draft"
          c-trigger_attrs="{'aria-label':'Status'}"
          $c-props="{
            value:$store.selectExample.value,
            onValueChange:(next) => $store.selectExample.value = next,
          }"
        />
        <p>Current: <strong x-text="$store.selectExample.value"></strong></p>
      </div>
    """
    js = "Alpine.store('selectExample', {value:'draft'});"

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CSelectOption("draft", "Draft"), CSelectOption("published", "Published")]}


preview = ControlledSelect()
preview  # noqa: B018
````


## Read-only and disabled states


### Select states

[Open the rendered preview](/v/0.4.4/ui-library/components/select/_previews/states/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class SelectStates(Component):
    template = """
      <c-CCol>
        <c-CSelect
          c-options="options" placeholder="Choose" value="active" readonly
          c-trigger_attrs="{'aria-label':'Read-only state'}"
        />
        <c-CSelect
          c-options="options" placeholder="Choose" disabled
          c-trigger_attrs="{'aria-label':'Disabled state'}"
        />
        <c-CSelect c-options="options" placeholder="Choose" invalid c-trigger_attrs="{'aria-label':'Invalid state'}" />
      </c-CCol>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CSelectOption("active", "Active"), CSelectOption("paused", "Paused")]}


preview = SelectStates()
preview  # noqa: B018
````


## Variants and sizes


### Select variants and sizes

[Open the rendered preview](/v/0.4.4/ui-library/components/select/_previews/variants/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class SelectVariants(Component):
    template = """
      <c-CCol>
        <c-CSelect
          c-options="options" placeholder="Outline" variant="outline" size="sm"
          c-trigger_attrs="{'aria-label':'Small outline'}"
        />
        <c-CSelect
          c-options="options" placeholder="Filled" variant="filled"
          c-trigger_attrs="{'aria-label':'Medium filled'}"
        />
        <c-CSelect
          c-options="options" placeholder="Plain" variant="plain" size="lg"
          c-trigger_attrs="{'aria-label':'Large plain'}"
        />
      </c-CCol>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CSelectOption("one", "One"), CSelectOption("two", "Two")]}


preview = SelectVariants()
preview  # noqa: B018
````


## Keyboard behavior

Enter, Space, Down, or Up opens the Listbox. Down and Up move the highlight;
Home and End jump to its edges; printable text performs buffered typeahead;
Enter or Space commits; Escape closes unchanged; and Tab closes while ordinary
page navigation continues.


### Navigate Select

[Open the rendered preview](/v/0.4.4/ui-library/components/select/_previews/keyboard/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class KeyboardSelect(Component):
    template = """
      <c-CSelect
        c-options="options"
        placeholder="Focus and use the keyboard"
        loop
        c-trigger_attrs="{'aria-label':'Planet keyboard example'}"
      />
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CSelectOption("earth", "Earth"),
                CSelectOption("mars", "Mars"),
                CSelectOption("jupiter", "Jupiter"),
            ]
        }


preview = KeyboardSelect()
preview  # noqa: B018
````


## Customize Select


### Customize Select

[Open the rendered preview](/v/0.4.4/ui-library/components/select/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class CustomizedSelect(Component):
    css = """
      .brand-select {
        --cui-select-radius: 1rem;
        --cui-select-selected-background: #53389e;
        --cui-select-selected-foreground: white;
        --cui-select-focus-color: #7f56d9;
        inline-size: min(100%, 22rem);
      }
    """
    template = """
      <c-CSelect
        class_="brand-select"
        c-options="options"
        placeholder="Choose a collection"
        c-trigger_attrs="{'aria-label':'Collection'}"
      />
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CSelectOption("botany", "Botany"), CSelectOption("astronomy", "Astronomy")]}


preview = CustomizedSelect()
preview  # noqa: B018
````


## Accessibility and forms

The visible Button uses the select-only combobox pattern and keeps DOM focus
while `aria-activedescendant` identifies the highlighted Option. A native
Select remains the form value, validity, and reset truth. Before client
initialization, that native control is the visible fallback.

Use `CListbox` for a persistent collection, `CMultiSelect` for several compact
values, and `CCombobox` when users need text filtering or custom input.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CSelect server inputs

Server inputs are passed in a template through `<c-CSelect ... />` or in Python through
`CSelect(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 8rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="select-input-cselect-server-inputs-options"></span>`options` | `Sequence[CSelectOption]` | required | Supplies the nonempty ordered stable collection. |
| <span id="select-input-cselect-server-inputs-placeholder"></span>`placeholder` | `str` | required | Supplies author-localized empty-value text. |
| <span id="select-input-cselect-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the native form field name. |
| <span id="select-input-cselect-server-inputs-form"></span>`form` | `str | None` | `None` | Associates the native value proxy with a Form ID. |
| <span id="select-input-cselect-server-inputs-id"></span>`id` | `str | None` | `None` | Sets native proxy identity and generated relationships. |
| <span id="select-input-cselect-server-inputs-value"></span>`value` | `str | None` | `None` | Sets the initial selected stable value. |
| <span id="select-input-cselect-server-inputs-open"></span>`open` | `bool` | `False` | Sets initial popup visibility when eligible. |
| <span id="select-input-cselect-server-inputs-required"></span>`required` | `bool | None` | `None` | Enables native required validity outside Field. |
| <span id="select-input-cselect-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Disables selection and form contribution. |
| <span id="select-input-cselect-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Preserves submission while preventing changes. |
| <span id="select-input-cselect-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Adds owner-supplied invalid presentation. |
| <span id="select-input-cselect-server-inputs-loop"></span>`loop` | `bool` | `False` | Wraps open Listbox arrow navigation. |
| <span id="select-input-cselect-server-inputs-placement"></span>`placement` | `"bottom-start" | "bottom-end" | "top-start" | "top-end"` ([`CSelectPlacement`](#select-interface-placement)) | `"bottom-start"` | Sets preferred logical popup placement. |
| <span id="select-input-cselect-server-inputs-match-width"></span>`match_width` | `bool` | `True` | Matches the popup inline size to the control within viewport limits. |
| <span id="select-input-cselect-server-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CSelectVariant`](#select-interface-variant)) | `"outline"` | Selects control treatment. |
| <span id="select-input-cselect-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CSelectSize`](#select-interface-size)) | `"md"` | Selects control and Option geometry. |
| <span id="select-input-cselect-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#select-interface-class-value)) | `None` | Adds root classes. |
| <span id="select-input-cselect-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#select-interface-style-value)) | `None` | Adds root inline styles. |
| <span id="select-input-cselect-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted nonconflicting root attributes. |
| <span id="select-input-cselect-server-inputs-trigger-attrs"></span>`trigger_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted relationships events and accessible naming to the combobox Button. |
| <span id="select-input-cselect-server-inputs-listbox-attrs"></span>`listbox_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted nonconflicting Listbox attributes. |

</div>

#### CSelect client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CSelect />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="select-input-cselect-client-inputs-value"></span>`value` | `string | null` | Releases control to committed selection. | Controls selected value while supplied. |
| <span id="select-input-cselect-client-inputs-open"></span>`open` | `boolean | null` | Releases control to committed visibility. | Controls popup visibility while supplied. |
| <span id="select-input-cselect-client-inputs-required"></span>`required` | `bool` | Uses the server or Field fallback. | Reactively changes required validity. |
| <span id="select-input-cselect-client-inputs-disabled"></span>`disabled` | `bool` | Uses the server or Field fallback. | Reactively disables selection. |
| <span id="select-input-cselect-client-inputs-readonly"></span>`readonly` | `bool` | Uses the server or Field fallback. | Reactively prevents changes while preserving submission. |
| <span id="select-input-cselect-client-inputs-invalid"></span>`invalid` | `bool` | Uses the server or Field fallback. | Reactively changes invalid presentation. |
| <span id="select-input-cselect-client-inputs-loop"></span>`loop` | `bool` | Uses the server value. | Reactively changes arrow wrapping. |
| <span id="select-input-cselect-client-inputs-placement"></span>`placement` | `CSelectPlacement` | Uses the server value. | Reactively changes preferred placement. |
| <span id="select-input-cselect-client-inputs-match-width"></span>`matchWidth` | `bool` | Uses the server value. | Reactively changes popup sizing. |
| <span id="select-input-cselect-client-inputs-variant"></span>`variant` | `CSelectVariant` | Uses the server value. | Reactively changes treatment. |
| <span id="select-input-cselect-client-inputs-size"></span>`size` | `CSelectSize` | Uses the server value. | Reactively changes geometry. |
| <span id="select-input-cselect-client-inputs-on-value-change"></span>`onValueChange` | `((value: string | null, detail: CSelectValueChangeDetail) => void) | undefined` | No component callback runs. | Receives selection reset and structural requests. |
| <span id="select-input-cselect-client-inputs-on-open-change"></span>`onOpenChange` | `((open: boolean, detail: CSelectOpenChangeDetail) => void) | undefined` | No component callback runs. | Receives visibility requests and forced-close notices. |

</div>

### Slots

-

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CSelect events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="select-event-cselect-events-value-change"></span>`onValueChange` | `(value: string | null, detail: CSelectValueChangeDetail) => void` ([`CSelectValueChangeDetail`](#select-interface-cselect-value-change-detail)) | Enabled selection reset or structural recovery. | `{value, previousValue, option, controlled, source, sourceEvent}` ([`CSelectValueChangeDetail`](#select-interface-cselect-value-change-detail)) | Commits immediately when uncontrolled and waits for owner acceptance when controlled. |
| <span id="select-event-cselect-events-open-change"></span>`onOpenChange` | `(open: boolean, detail: CSelectOpenChangeDetail) => void` ([`CSelectOpenChangeDetail`](#select-interface-cselect-open-change-detail)) | Visibility request or nonrejectable safety close. | `{open, reason, controlled, forced, source}` ([`CSelectOpenChangeDetail`](#select-interface-cselect-open-change-detail)) | Controlled requests notify without changing visibility; forced safety closes always hide. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CSelect CSS variables

Apply these variables to `CSelect` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="select-css-cselect-css-variables-background"></span>`--cui-select-background` | `color` | Control and popup surface. | `Canvas` |
| <span id="select-css-cselect-css-variables-foreground"></span>`--cui-select-foreground` | `color` | Primary foreground. | `CanvasText` |
| <span id="select-css-cselect-css-variables-placeholder-color"></span>`--cui-select-placeholder-color` | `color` | Empty-value foreground. | `scheme-aware muted` |
| <span id="select-css-cselect-css-variables-muted-color"></span>`--cui-select-muted-color` | `color` | Description and disabled foreground. | `scheme-aware muted` |
| <span id="select-css-cselect-css-variables-border-color"></span>`--cui-select-border-color` | `color` | Outline border. | `scheme-aware subtle border` |
| <span id="select-css-cselect-css-variables-hover-background"></span>`--cui-select-hover-background` | `color` | Highlighted Option surface. | `CanvasText mix` |
| <span id="select-css-cselect-css-variables-selected-background"></span>`--cui-select-selected-background` | `color` | Selected Option surface. | `scheme-aware blue` |
| <span id="select-css-cselect-css-variables-selected-foreground"></span>`--cui-select-selected-foreground` | `color` | Selected Option foreground. | `scheme-aware blue text` |
| <span id="select-css-cselect-css-variables-focus-color"></span>`--cui-select-focus-color` | `color` | Focus outline. | `Highlight` |
| <span id="select-css-cselect-css-variables-radius"></span>`--cui-select-radius` | `length` | Control and popup corners. | `0.625rem` |
| <span id="select-css-cselect-css-variables-control-padding"></span>`--cui-select-control-padding` | `length` | Control padding. | `size-derived` |
| <span id="select-css-cselect-css-variables-option-padding"></span>`--cui-select-option-padding` | `length` | Option padding. | `size-derived` |
| <span id="select-css-cselect-css-variables-max-block-size"></span>`--cui-select-max-block-size` | `length` | Popup scroll boundary. | `18rem` |
| <span id="select-css-cselect-css-variables-offset"></span>`--cui-select-offset` | `length` | Anchor gap. | `0.25rem` |
| <span id="select-css-cselect-css-variables-shadow"></span>`--cui-select-shadow` | `shadow` | Popup elevation. | `scheme-aware shadow` |
| <span id="select-css-cselect-css-variables-duration"></span>`--cui-select-duration` | `time` | Popup and indicator motion. | `120ms` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CSelect attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="select-attribute-cselect-attributes-role-combobox"></span>`role` | Control Button | `combobox` | Declares the select-only popup control. |
| <span id="select-attribute-cselect-attributes-role-listbox"></span>`role` | Listbox div | `listbox` | Declares the popup collection. |
| <span id="select-attribute-cselect-attributes-role-option"></span>`role` | Option div | `option` | Declares each value. |
| <span id="select-attribute-cselect-attributes-aria-expanded"></span>`aria-expanded` | Control Button | `true | false` | Reflects popup visibility. |
| <span id="select-attribute-cselect-attributes-aria-controls"></span>`aria-controls` | Control Button | `IDREF` | Targets the Listbox. |
| <span id="select-attribute-cselect-attributes-aria-activedescendant"></span>`aria-activedescendant` | Control Button | `IDREF or absent` | Identifies the highlighted open Option. |
| <span id="select-attribute-cselect-attributes-aria-required"></span>`aria-required` | Control Button | `true or absent` | Mirrors effective required state. |
| <span id="select-attribute-cselect-attributes-aria-disabled"></span>`aria-disabled` | Control Button | `true or absent` | Mirrors effective unavailability. |
| <span id="select-attribute-cselect-attributes-aria-readonly"></span>`aria-readonly` | Control Button | `true or absent` | Mirrors read-only interaction. |
| <span id="select-attribute-cselect-attributes-aria-invalid"></span>`aria-invalid` | Control Button | `true or absent` | Mirrors effective invalid presentation. |
| <span id="select-attribute-cselect-attributes-aria-selected"></span>`aria-selected` | Option div | `true | false` | Reflects effective selection. |
| <span id="select-attribute-cselect-attributes-data-open"></span>`data-open` | Root div | `present-or-absent` | Mirrors effective visibility. |
| <span id="select-attribute-cselect-attributes-data-empty"></span>`data-empty` | Root div | `present-or-absent` | Mirrors no selected value. |
| <span id="select-attribute-cselect-attributes-data-required"></span>`data-required` | Root div | `present-or-absent` | Mirrors effective required state. |
| <span id="select-attribute-cselect-attributes-data-readonly"></span>`data-readonly` | Root div | `present-or-absent` | Mirrors read-only interaction. |
| <span id="select-attribute-cselect-attributes-data-invalid"></span>`data-invalid` | Root div | `present-or-absent` | Mirrors effective invalid presentation. |
| <span id="select-attribute-cselect-attributes-data-match-width"></span>`data-match-width` | Root div | `present-or-absent` | Mirrors popup width matching. |
| <span id="select-attribute-cselect-attributes-data-variant"></span>`data-variant` | Root div | `outline | filled | plain` | Mirrors effective treatment. |
| <span id="select-attribute-cselect-attributes-data-size"></span>`data-size` | Root div | `sm | md | lg` | Mirrors effective geometry. |
| <span id="select-attribute-cselect-attributes-data-value"></span>`data-value` | Option div | `string` | Exposes stable identity. |
| <span id="select-attribute-cselect-attributes-data-selected"></span>`data-selected` | Option div | `present-or-absent` | Mirrors selection. |
| <span id="select-attribute-cselect-attributes-data-highlighted"></span>`data-highlighted` | Option div | `present-or-absent` | Mirrors active descendant. |
| <span id="select-attribute-cselect-attributes-data-disabled"></span>`data-disabled` | Root or Option div | `present-or-absent` | Mirrors effective unavailability. |
| <span id="select-attribute-cselect-attributes-data-placement"></span>`data-placement` | Popup div | `CSelectPlacement` | Reflects preferred logical placement. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CSelect selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="select-selector-cselect-selectors-root"></span>`[data-citry-ui-part="root"]` | Root div | Stable root attrs and state surface. |
| <span id="select-selector-cselect-selectors-control"></span>`[data-citry-ui-part="control"]` | Combobox Button | Visible control and focus owner. |
| <span id="select-selector-cselect-selectors-value"></span>`[data-citry-ui-part="value"]` | Value span | Selected label or placeholder. |
| <span id="select-selector-cselect-selectors-indicator"></span>`[data-citry-ui-part="indicator"]` | Indicator span | Decorative popup-state mark. |
| <span id="select-selector-cselect-selectors-popup"></span>`[data-citry-ui-part="popup"]` | Manual popover div | Top-layer scrolling surface. |
| <span id="select-selector-cselect-selectors-listbox"></span>`[data-citry-ui-part="listbox"]` | Listbox div | Semantic collection. |
| <span id="select-selector-cselect-selectors-group"></span>`[data-citry-ui-part="group"]` | Group div | Related Options. |
| <span id="select-selector-cselect-selectors-group-label"></span>`[data-citry-ui-part="group-label"]` | Group label span | Visible group name. |
| <span id="select-selector-cselect-selectors-option"></span>`[data-citry-ui-part="option"]` | Option div | Value semantics and state. |
| <span id="select-selector-cselect-selectors-option-label"></span>`[data-citry-ui-part="option-label"]` | Option label span | Accessible Option name. |
| <span id="select-selector-cselect-selectors-option-description"></span>`[data-citry-ui-part="option-description"]` | Option description span | Supporting description. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="select-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="select-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |
| <span id="select-interface-placement"></span>`CSelectPlacement` | `Literal["bottom-start", "bottom-end", "top-start", "top-end"]` |
| <span id="select-interface-variant"></span>`CSelectVariant` | `Literal["outline", "filled", "plain"]` |
| <span id="select-interface-size"></span>`CSelectSize` | `Literal["sm", "md", "lg"]` |
| <span id="select-interface-source"></span>`CSelectChangeSource` | `Literal["pointer", "keyboard", "reset", "structure"]` |
| <span id="select-interface-reason"></span>`CSelectOpenReason` | `Literal["trigger", "keyboard", "selection", "escape", "tab", "outside", "focus-outside", "reset", "native", "ancestor"]` |

</div>

<span id="select-interface-cselect-option"></span>

#### `CSelectOption`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="select-interface-cselect-option-value"></span>`value` | `str` | - | Stable unique form value. |
| <span id="select-interface-cselect-option-label"></span>`label` | `str` | - | Visible accessible Option name. |
| <span id="select-interface-cselect-option-description"></span>`description` | `str | None` | - | Optional separately described supporting text. |
| <span id="select-interface-cselect-option-disabled"></span>`disabled` | `bool` | - | Prevents user selection. |
| <span id="select-interface-cselect-option-group"></span>`group` | `str | None` | - | Optional contiguous visible group label. |

</div>

<span id="select-interface-cselect-value-change-detail"></span>

#### `CSelectValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="select-interface-cselect-value-change-detail-value"></span>`value` | `str | None` | - | Requested value. |
| <span id="select-interface-cselect-value-change-detail-previous-value"></span>`previousValue` | `str | None` | - | Previous effective value. |
| <span id="select-interface-cselect-value-change-detail-option"></span>`option` | `HTMLElement | None` | - | Activated Option or None for reset and structure. |
| <span id="select-interface-cselect-value-change-detail-controlled"></span>`controlled` | `bool` | - | Whether client value owns selection. |
| <span id="select-interface-cselect-value-change-detail-source"></span>`source` | `CSelectChangeSource` | - | Request source. |
| <span id="select-interface-cselect-value-change-detail-source-event"></span>`sourceEvent` | `Event | None` | - | Native source event when present. |

</div>

<span id="select-interface-cselect-open-change-detail"></span>

#### `CSelectOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="select-interface-cselect-open-change-detail-open"></span>`open` | `bool` | - | Requested or forced visibility. |
| <span id="select-interface-cselect-open-change-detail-reason"></span>`reason` | `CSelectOpenReason` | - | Visibility reason. |
| <span id="select-interface-cselect-open-change-detail-controlled"></span>`controlled` | `bool` | - | Whether client open owns visibility. |
| <span id="select-interface-cselect-open-change-detail-forced"></span>`forced` | `bool` | - | Whether safety made the close nonrejectable. |
| <span id="select-interface-cselect-open-change-detail-source"></span>`source` | `EventTarget | None` | - | Native source or safety owner. |

</div>

### Translation keys

-