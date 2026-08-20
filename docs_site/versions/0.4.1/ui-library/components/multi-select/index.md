---
title: MultiSelect
url: https://citry.dev/v/0.4.1/ui-library/components/multi-select/
description: "Choose several fixed values from a compact, styled form control."
---
# MultiSelect

Use `CMultiSelect` when people choose several fixed values and the collection
should remain compact until opened. Selected values appear as noninteractive
chips. A native multiple Select preserves repeated-value form submission and
reset behavior.

## MultiSelect at a glance


### MultiSelect at a glance

[Open the rendered preview](/v/0.4.1/ui-library/components/multi-select/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class MultiSelectAtAGlance(Component):
    template = """
      <c-CField>
        <c-fill name="label">Workspaces</c-fill>
        <c-fill name="description">Choose every workspace that should receive this observation.</c-fill>
        <c-fill name="default">
          <c-CMultiSelect c-options="options" placeholder="Choose workspaces" c-value="['atlas', 'aurora']" />
        </c-fill>
      </c-CField>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CMultiSelectOption("atlas", "Atlas research", "12 collaborators"),
                CMultiSelectOption("aurora", "Aurora field notes", "7 collaborators"),
                CMultiSelectOption("archive", "Archived studies", disabled=True),
            ]
        }


preview = MultiSelectAtAGlance()
preview  # noqa: B018
````


## Submit repeated values


### Submit a MultiSelect

[Open the rendered preview](/v/0.4.1/ui-library/components/multi-select/_previews/forms/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class MultiSelectForm(Component):
    template = """
      <form x-data @submit.prevent="result = Array.from(new FormData($event.target).entries())">
        <c-CField required>
          <c-fill name="label">Reviewers</c-fill>
          <c-fill name="default">
            <c-CMultiSelect c-options="options" placeholder="Choose reviewers" name="reviewer" />
          </c-fill>
        </c-CField>
        <c-CButton type="submit">Save</c-CButton>
        <c-CButton type="reset" variant="ghost">Reset</c-CButton>
        <output x-text="JSON.stringify(result)"></output>
      </form>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CMultiSelectOption("maya", "Maya Chen"),
                CMultiSelectOption("noah", "Noah Williams"),
                CMultiSelectOption("ines", "Inês Silva"),
            ]
        }


preview = MultiSelectForm()
preview  # noqa: B018
````


## Group related options


### Group options

[Open the rendered preview](/v/0.4.1/ui-library/components/multi-select/_previews/groups/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class GroupedMultiSelect(Component):
    template = """
      <c-CMultiSelect
        c-options="options"
        placeholder="Choose a destination"
        c-trigger_attrs="{'aria-label':'Destination'}"
      />
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CMultiSelectOption("oslo", "Oslo", group="Europe"),
                CMultiSelectOption("prague", "Prague", group="Europe"),
                CMultiSelectOption("kyoto", "Kyoto", group="Asia"),
                CMultiSelectOption("seoul", "Seoul", group="Asia"),
            ]
        }


preview = GroupedMultiSelect()
preview  # noqa: B018
````


## Control selection


### Control selection

[Open the rendered preview](/v/0.4.1/ui-library/components/multi-select/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class ControlledMultiSelect(Component):
    template = """
      <div x-data>
        <c-CMultiSelect
          c-options="options"
          placeholder="Choose channels"
          c-value="['email']"
          c-trigger_attrs="{'aria-label':'Notification channels'}"
          $c-props="{
            value:$store.multiSelectExample.value,
            onValueChange:(next) => $store.multiSelectExample.value = next,
          }"
        />
        <p>Current: <strong x-text="$store.multiSelectExample.value.join(', ')"></strong></p>
      </div>
    """
    js = "Alpine.store('multiSelectExample', {value:['email']});"

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CMultiSelectOption("email", "Email"),
                CMultiSelectOption("push", "Push"),
                CMultiSelectOption("sms", "SMS"),
            ]
        }


preview = ControlledMultiSelect()
preview  # noqa: B018
````


## Read-only and disabled states


### MultiSelect states

[Open the rendered preview](/v/0.4.1/ui-library/components/multi-select/_previews/states/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class MultiSelectStates(Component):
    template = """
      <c-CStack>
        <c-CMultiSelect
          c-options="options" placeholder="Choose" c-value="['active', 'paused']" readonly
          c-trigger_attrs="{'aria-label':'Read-only state'}"
        />
        <c-CMultiSelect
          c-options="options" placeholder="Choose" disabled
          c-trigger_attrs="{'aria-label':'Disabled state'}"
        />
        <c-CMultiSelect
          c-options="options" placeholder="Choose" invalid
          c-trigger_attrs="{'aria-label':'Invalid state'}"
        />
      </c-CStack>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CMultiSelectOption("active", "Active"), CMultiSelectOption("paused", "Paused")]}


preview = MultiSelectStates()
preview  # noqa: B018
````


## Close after each choice

By default the popup stays open so several values can be toggled efficiently.
Use `close_on_select` for workflows that should close after every change.


### Close after selection

[Open the rendered preview](/v/0.4.1/ui-library/components/multi-select/_previews/close-on-select/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class CloseOnSelectMultiSelect(Component):
    template = """
      <c-CMultiSelect
        c-options="options"
        placeholder="Choose a delivery method"
        close_on_select
        c-trigger_attrs="{'aria-label':'Delivery methods'}"
      />
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CMultiSelectOption("courier", "Courier"),
                CMultiSelectOption("pickup", "Pickup"),
                CMultiSelectOption("locker", "Parcel locker"),
            ]
        }


preview = CloseOnSelectMultiSelect()
preview  # noqa: B018
````


## Variants and sizes


### MultiSelect variants and sizes

[Open the rendered preview](/v/0.4.1/ui-library/components/multi-select/_previews/variants/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class MultiSelectVariants(Component):
    template = """
      <c-CStack>
        <c-CMultiSelect
          c-options="options" placeholder="Outline" variant="outline" size="sm"
          c-trigger_attrs="{'aria-label':'Small outline'}"
        />
        <c-CMultiSelect
          c-options="options" placeholder="Filled" variant="filled"
          c-trigger_attrs="{'aria-label':'Medium filled'}"
        />
        <c-CMultiSelect
          c-options="options" placeholder="Plain" variant="plain" size="lg"
          c-trigger_attrs="{'aria-label':'Large plain'}"
        />
      </c-CStack>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CMultiSelectOption("one", "One"), CMultiSelectOption("two", "Two")]}


preview = MultiSelectVariants()
preview  # noqa: B018
````


## Keyboard behavior

Enter, Space, Down, or Up opens the Listbox. Down and Up move the highlight;
Home and End jump to its edges; printable text performs buffered typeahead;
Enter or Space toggles the highlighted value; Escape closes; and Tab closes while ordinary
page navigation continues.


### Navigate MultiSelect

[Open the rendered preview](/v/0.4.1/ui-library/components/multi-select/_previews/keyboard/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class KeyboardMultiSelect(Component):
    template = """
      <c-CMultiSelect
        c-options="options"
        placeholder="Focus and use the keyboard"
        loop
        c-trigger_attrs="{'aria-label':'Planet keyboard example'}"
      />
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CMultiSelectOption("earth", "Earth"),
                CMultiSelectOption("mars", "Mars"),
                CMultiSelectOption("jupiter", "Jupiter"),
            ]
        }


preview = KeyboardMultiSelect()
preview  # noqa: B018
````


## Customize MultiSelect


### Customize MultiSelect

[Open the rendered preview](/v/0.4.1/ui-library/components/multi-select/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class CustomizedMultiSelect(Component):
    css = """
      .brand-select {
        --cui-multi-select-radius: 1rem;
        --cui-multi-select-selected-background: #53389e;
        --cui-multi-select-selected-foreground: white;
        --cui-multi-select-focus-color: #7f56d9;
        inline-size: min(100%, 22rem);
      }
    """
    template = """
      <c-CMultiSelect
        class_="brand-select"
        c-options="options"
        placeholder="Choose a collection"
        c-trigger_attrs="{'aria-label':'Collection'}"
      />
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CMultiSelectOption("botany", "Botany"), CMultiSelectOption("astronomy", "Astronomy")]}


preview = CustomizedMultiSelect()
preview  # noqa: B018
````


## Accessibility and forms

The visible Button uses the select-only combobox pattern and keeps DOM focus
while `aria-activedescendant` identifies the highlighted Option. A native
multiple Select remains the repeated form value, validity, and reset truth. Before client
initialization, that native control is the visible fallback.

Use `CListbox(multiple=True)` for a persistent collection, `CSelect` for one
compact value, and `CCombobox` when users need text filtering or custom input.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CMultiSelect server inputs

Server inputs are passed in a template through `<c-CMultiSelect ... />` or in Python through
`CMultiSelect(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 8rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="multi-select-input-cmulti-select-server-inputs-options"></span>`options` | `Sequence[CMultiSelectOption]` | required | Supplies the nonempty ordered stable collection. |
| <span id="multi-select-input-cmulti-select-server-inputs-placeholder"></span>`placeholder` | `str` | required | Supplies author-localized empty-value text. |
| <span id="multi-select-input-cmulti-select-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the native form field name. |
| <span id="multi-select-input-cmulti-select-server-inputs-form"></span>`form` | `str | None` | `None` | Associates the native value proxy with a Form ID. |
| <span id="multi-select-input-cmulti-select-server-inputs-id"></span>`id` | `str | None` | `None` | Sets native proxy identity and generated relationships. |
| <span id="multi-select-input-cmulti-select-server-inputs-value"></span>`value` | `Sequence[str] | None` | `None` | Sets initial selected stable values in collection order. |
| <span id="multi-select-input-cmulti-select-server-inputs-open"></span>`open` | `bool` | `False` | Sets initial popup visibility when eligible. |
| <span id="multi-select-input-cmulti-select-server-inputs-required"></span>`required` | `bool | None` | `None` | Enables native required validity outside Field. |
| <span id="multi-select-input-cmulti-select-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Disables selection and form contribution. |
| <span id="multi-select-input-cmulti-select-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Preserves submission while preventing changes. |
| <span id="multi-select-input-cmulti-select-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Adds owner-supplied invalid presentation. |
| <span id="multi-select-input-cmulti-select-server-inputs-loop"></span>`loop` | `bool` | `False` | Wraps open Listbox arrow navigation. |
| <span id="multi-select-input-cmulti-select-server-inputs-close-on-select"></span>`close_on_select` | `bool` | `False` | Closes the popup after each accepted toggle. |
| <span id="multi-select-input-cmulti-select-server-inputs-placement"></span>`placement` | `"bottom-start" | "bottom-end" | "top-start" | "top-end"` ([`CMultiSelectPlacement`](#multi-select-interface-placement)) | `"bottom-start"` | Sets preferred logical popup placement. |
| <span id="multi-select-input-cmulti-select-server-inputs-match-width"></span>`match_width` | `bool` | `True` | Matches the popup inline size to the control within viewport limits. |
| <span id="multi-select-input-cmulti-select-server-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CMultiSelectVariant`](#multi-select-interface-variant)) | `"outline"` | Selects control treatment. |
| <span id="multi-select-input-cmulti-select-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CMultiSelectSize`](#multi-select-interface-size)) | `"md"` | Selects control and Option geometry. |
| <span id="multi-select-input-cmulti-select-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#multi-select-interface-class-value)) | `None` | Adds root classes. |
| <span id="multi-select-input-cmulti-select-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#multi-select-interface-style-value)) | `None` | Adds root inline styles. |
| <span id="multi-select-input-cmulti-select-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted nonconflicting root attributes. |
| <span id="multi-select-input-cmulti-select-server-inputs-trigger-attrs"></span>`trigger_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted relationships events and accessible naming to the combobox Button. |
| <span id="multi-select-input-cmulti-select-server-inputs-listbox-attrs"></span>`listbox_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted nonconflicting Listbox attributes. |

</div>

#### CMultiSelect client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CMultiSelect />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="multi-select-input-cmulti-select-client-inputs-value"></span>`value` | `string[] | null` | Releases control to committed selection. | Controls the selected collection while supplied; an empty array is controlled empty. |
| <span id="multi-select-input-cmulti-select-client-inputs-open"></span>`open` | `boolean | null` | Releases control to committed visibility. | Controls popup visibility while supplied. |
| <span id="multi-select-input-cmulti-select-client-inputs-required"></span>`required` | `bool` | Uses the server or Field fallback. | Reactively changes required validity. |
| <span id="multi-select-input-cmulti-select-client-inputs-disabled"></span>`disabled` | `bool` | Uses the server or Field fallback. | Reactively disables selection. |
| <span id="multi-select-input-cmulti-select-client-inputs-readonly"></span>`readonly` | `bool` | Uses the server or Field fallback. | Reactively prevents changes while preserving submission. |
| <span id="multi-select-input-cmulti-select-client-inputs-invalid"></span>`invalid` | `bool` | Uses the server or Field fallback. | Reactively changes invalid presentation. |
| <span id="multi-select-input-cmulti-select-client-inputs-loop"></span>`loop` | `bool` | Uses the server value. | Reactively changes arrow wrapping. |
| <span id="multi-select-input-cmulti-select-client-inputs-close-on-select"></span>`closeOnSelect` | `bool` | Uses the server value. | Reactively changes whether a toggle closes the popup. |
| <span id="multi-select-input-cmulti-select-client-inputs-placement"></span>`placement` | `CMultiSelectPlacement` | Uses the server value. | Reactively changes preferred placement. |
| <span id="multi-select-input-cmulti-select-client-inputs-match-width"></span>`matchWidth` | `bool` | Uses the server value. | Reactively changes popup sizing. |
| <span id="multi-select-input-cmulti-select-client-inputs-variant"></span>`variant` | `CMultiSelectVariant` | Uses the server value. | Reactively changes treatment. |
| <span id="multi-select-input-cmulti-select-client-inputs-size"></span>`size` | `CMultiSelectSize` | Uses the server value. | Reactively changes geometry. |
| <span id="multi-select-input-cmulti-select-client-inputs-on-value-change"></span>`onValueChange` | `((value: string[], detail: CMultiSelectValueChangeDetail) => void) | undefined` | No component callback runs. | Receives toggle reset and structural requests. |
| <span id="multi-select-input-cmulti-select-client-inputs-on-open-change"></span>`onOpenChange` | `((open: boolean, detail: CMultiSelectOpenChangeDetail) => void) | undefined` | No component callback runs. | Receives visibility requests and forced-close notices. |

</div>

### Slots

-

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CMultiSelect events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="multi-select-event-cmulti-select-events-value-change"></span>`onValueChange` | `(value: string[], detail: CMultiSelectValueChangeDetail) => void` ([`CMultiSelectValueChangeDetail`](#multi-select-interface-cmulti-select-value-change-detail)) | Enabled toggle reset or structural recovery. | `{value, previousValue, option, selected, controlled, source, sourceEvent}` ([`CMultiSelectValueChangeDetail`](#multi-select-interface-cmulti-select-value-change-detail)) | Commits immediately when uncontrolled and waits for owner acceptance when controlled. |
| <span id="multi-select-event-cmulti-select-events-open-change"></span>`onOpenChange` | `(open: boolean, detail: CMultiSelectOpenChangeDetail) => void` ([`CMultiSelectOpenChangeDetail`](#multi-select-interface-cmulti-select-open-change-detail)) | Visibility request or nonrejectable safety close. | `{open, reason, controlled, forced, source}` ([`CMultiSelectOpenChangeDetail`](#multi-select-interface-cmulti-select-open-change-detail)) | Controlled requests notify without changing visibility; forced safety closes always hide. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CMultiSelect CSS variables

Apply these variables to `CMultiSelect` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="multi-select-css-cmulti-select-css-variables-background"></span>`--cui-multi-select-background` | `color` | Control and popup surface. | `Canvas` |
| <span id="multi-select-css-cmulti-select-css-variables-foreground"></span>`--cui-multi-select-foreground` | `color` | Primary foreground. | `CanvasText` |
| <span id="multi-select-css-cmulti-select-css-variables-placeholder-color"></span>`--cui-multi-select-placeholder-color` | `color` | Empty-value foreground. | `scheme-aware muted` |
| <span id="multi-select-css-cmulti-select-css-variables-muted-color"></span>`--cui-multi-select-muted-color` | `color` | Description and disabled foreground. | `scheme-aware muted` |
| <span id="multi-select-css-cmulti-select-css-variables-border-color"></span>`--cui-multi-select-border-color` | `color` | Outline border. | `scheme-aware subtle border` |
| <span id="multi-select-css-cmulti-select-css-variables-hover-background"></span>`--cui-multi-select-hover-background` | `color` | Highlighted Option surface. | `CanvasText mix` |
| <span id="multi-select-css-cmulti-select-css-variables-selected-background"></span>`--cui-multi-select-selected-background` | `color` | Selected Option surface. | `scheme-aware blue` |
| <span id="multi-select-css-cmulti-select-css-variables-selected-foreground"></span>`--cui-multi-select-selected-foreground` | `color` | Selected Option foreground. | `scheme-aware blue text` |
| <span id="multi-select-css-cmulti-select-css-variables-chip-background"></span>`--cui-multi-select-chip-background` | `color` | Selected-value chip surface. | `CanvasText mix` |
| <span id="multi-select-css-cmulti-select-css-variables-chip-foreground"></span>`--cui-multi-select-chip-foreground` | `color` | Selected-value chip foreground. | `CanvasText` |
| <span id="multi-select-css-cmulti-select-css-variables-focus-color"></span>`--cui-multi-select-focus-color` | `color` | Focus outline. | `Highlight` |
| <span id="multi-select-css-cmulti-select-css-variables-radius"></span>`--cui-multi-select-radius` | `length` | Control and popup corners. | `0.625rem` |
| <span id="multi-select-css-cmulti-select-css-variables-control-padding"></span>`--cui-multi-select-control-padding` | `length` | Control padding. | `size-derived` |
| <span id="multi-select-css-cmulti-select-css-variables-option-padding"></span>`--cui-multi-select-option-padding` | `length` | Option padding. | `size-derived` |
| <span id="multi-select-css-cmulti-select-css-variables-max-block-size"></span>`--cui-multi-select-max-block-size` | `length` | Popup scroll boundary. | `18rem` |
| <span id="multi-select-css-cmulti-select-css-variables-offset"></span>`--cui-multi-select-offset` | `length` | Anchor gap. | `0.25rem` |
| <span id="multi-select-css-cmulti-select-css-variables-shadow"></span>`--cui-multi-select-shadow` | `shadow` | Popup elevation. | `scheme-aware shadow` |
| <span id="multi-select-css-cmulti-select-css-variables-duration"></span>`--cui-multi-select-duration` | `time` | Indicator rotation motion. | `120ms` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CMultiSelect attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="multi-select-attribute-cmulti-select-attributes-role-combobox"></span>`role` | Control Button | `combobox` | Declares the select-only popup control. |
| <span id="multi-select-attribute-cmulti-select-attributes-role-listbox"></span>`role` | Listbox div | `listbox` | Declares the popup collection. |
| <span id="multi-select-attribute-cmulti-select-attributes-aria-multiselectable"></span>`aria-multiselectable` | Listbox div | `true` | Declares independent multiple selection. |
| <span id="multi-select-attribute-cmulti-select-attributes-role-option"></span>`role` | Option div | `option` | Declares each value. |
| <span id="multi-select-attribute-cmulti-select-attributes-aria-expanded"></span>`aria-expanded` | Control Button | `true | false` | Reflects popup visibility. |
| <span id="multi-select-attribute-cmulti-select-attributes-aria-controls"></span>`aria-controls` | Control Button | `IDREF` | Targets the Listbox. |
| <span id="multi-select-attribute-cmulti-select-attributes-aria-activedescendant"></span>`aria-activedescendant` | Control Button | `IDREF or absent` | Identifies the highlighted open Option. |
| <span id="multi-select-attribute-cmulti-select-attributes-aria-required"></span>`aria-required` | Control Button | `true or absent` | Mirrors effective required state. |
| <span id="multi-select-attribute-cmulti-select-attributes-aria-disabled"></span>`aria-disabled` | Control Button | `true or absent` | Mirrors effective unavailability. |
| <span id="multi-select-attribute-cmulti-select-attributes-aria-readonly"></span>`aria-readonly` | Control Button | `true or absent` | Mirrors read-only interaction. |
| <span id="multi-select-attribute-cmulti-select-attributes-aria-invalid"></span>`aria-invalid` | Control Button | `true or absent` | Mirrors effective invalid presentation. |
| <span id="multi-select-attribute-cmulti-select-attributes-aria-selected"></span>`aria-selected` | Option div | `true | false` | Reflects effective selection. |
| <span id="multi-select-attribute-cmulti-select-attributes-data-open"></span>`data-open` | Root div | `present-or-absent` | Mirrors effective visibility. |
| <span id="multi-select-attribute-cmulti-select-attributes-data-empty"></span>`data-empty` | Root div | `present-or-absent` | Mirrors no selected value. |
| <span id="multi-select-attribute-cmulti-select-attributes-data-required"></span>`data-required` | Root div | `present-or-absent` | Mirrors effective required state. |
| <span id="multi-select-attribute-cmulti-select-attributes-data-readonly"></span>`data-readonly` | Root div | `present-or-absent` | Mirrors read-only interaction. |
| <span id="multi-select-attribute-cmulti-select-attributes-data-invalid"></span>`data-invalid` | Root div | `present-or-absent` | Mirrors effective invalid presentation. |
| <span id="multi-select-attribute-cmulti-select-attributes-data-close-on-select"></span>`data-close-on-select` | Root div | `present-or-absent` | Mirrors close-after-toggle behavior. |
| <span id="multi-select-attribute-cmulti-select-attributes-data-match-width"></span>`data-match-width` | Root div | `present-or-absent` | Mirrors popup width matching. |
| <span id="multi-select-attribute-cmulti-select-attributes-data-variant"></span>`data-variant` | Root div | `outline | filled | plain` | Mirrors effective treatment. |
| <span id="multi-select-attribute-cmulti-select-attributes-data-size"></span>`data-size` | Root div | `sm | md | lg` | Mirrors effective geometry. |
| <span id="multi-select-attribute-cmulti-select-attributes-data-value"></span>`data-value` | Option div | `string` | Exposes stable identity. |
| <span id="multi-select-attribute-cmulti-select-attributes-data-selected"></span>`data-selected` | Option div | `present-or-absent` | Mirrors selection. |
| <span id="multi-select-attribute-cmulti-select-attributes-data-highlighted"></span>`data-highlighted` | Option div | `present-or-absent` | Mirrors active descendant. |
| <span id="multi-select-attribute-cmulti-select-attributes-data-disabled"></span>`data-disabled` | Root or Option div | `present-or-absent` | Mirrors effective unavailability. |
| <span id="multi-select-attribute-cmulti-select-attributes-data-placement"></span>`data-placement` | Popup div | `CMultiSelectPlacement` | Reflects preferred logical placement. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CMultiSelect selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="multi-select-selector-cmulti-select-selectors-root"></span>`[data-citry-ui-part="root"]` | Root div | Stable root attrs and state surface. |
| <span id="multi-select-selector-cmulti-select-selectors-control"></span>`[data-citry-ui-part="control"]` | Combobox Button | Visible control and focus owner. |
| <span id="multi-select-selector-cmulti-select-selectors-values"></span>`[data-citry-ui-part="values"]` | Values span | Selected chips or placeholder. |
| <span id="multi-select-selector-cmulti-select-selectors-placeholder"></span>`[data-citry-ui-part="placeholder"]` | Placeholder span | Empty-selection copy. |
| <span id="multi-select-selector-cmulti-select-selectors-chip"></span>`[data-citry-ui-part="chip"]` | Chip span | Noninteractive selected-value label. |
| <span id="multi-select-selector-cmulti-select-selectors-indicator"></span>`[data-citry-ui-part="indicator"]` | Indicator span | Decorative popup-state mark. |
| <span id="multi-select-selector-cmulti-select-selectors-popup"></span>`[data-citry-ui-part="popup"]` | Manual popover div | Top-layer scrolling surface. |
| <span id="multi-select-selector-cmulti-select-selectors-listbox"></span>`[data-citry-ui-part="listbox"]` | Listbox div | Semantic collection. |
| <span id="multi-select-selector-cmulti-select-selectors-group"></span>`[data-citry-ui-part="group"]` | Group div | Related Options. |
| <span id="multi-select-selector-cmulti-select-selectors-group-label"></span>`[data-citry-ui-part="group-label"]` | Group label span | Visible group name. |
| <span id="multi-select-selector-cmulti-select-selectors-option"></span>`[data-citry-ui-part="option"]` | Option div | Value semantics and state. |
| <span id="multi-select-selector-cmulti-select-selectors-option-label"></span>`[data-citry-ui-part="option-label"]` | Option label span | Accessible Option name. |
| <span id="multi-select-selector-cmulti-select-selectors-option-description"></span>`[data-citry-ui-part="option-description"]` | Option description span | Supporting description. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="multi-select-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="multi-select-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |
| <span id="multi-select-interface-placement"></span>`CMultiSelectPlacement` | `Literal["bottom-start", "bottom-end", "top-start", "top-end"]` |
| <span id="multi-select-interface-variant"></span>`CMultiSelectVariant` | `Literal["outline", "filled", "plain"]` |
| <span id="multi-select-interface-size"></span>`CMultiSelectSize` | `Literal["sm", "md", "lg"]` |
| <span id="multi-select-interface-source"></span>`CMultiSelectChangeSource` | `Literal["pointer", "keyboard", "reset", "structure"]` |
| <span id="multi-select-interface-reason"></span>`CMultiSelectOpenReason` | `Literal["trigger", "keyboard", "selection", "escape", "tab", "outside", "focus-outside", "reset", "native", "ancestor"]` |

</div>

<span id="multi-select-interface-cmulti-select-option"></span>

#### `CMultiSelectOption`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="multi-select-interface-cmulti-select-option-value"></span>`value` | `str` | - | Stable unique form value. |
| <span id="multi-select-interface-cmulti-select-option-label"></span>`label` | `str` | - | Visible accessible Option name. |
| <span id="multi-select-interface-cmulti-select-option-description"></span>`description` | `str | None` | - | Optional separately described supporting text. |
| <span id="multi-select-interface-cmulti-select-option-disabled"></span>`disabled` | `bool` | - | Prevents user selection. |
| <span id="multi-select-interface-cmulti-select-option-group"></span>`group` | `str | None` | - | Optional contiguous visible group label. |

</div>

<span id="multi-select-interface-cmulti-select-value-change-detail"></span>

#### `CMultiSelectValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="multi-select-interface-cmulti-select-value-change-detail-value"></span>`value` | `string[]` | - | Requested copied value collection. |
| <span id="multi-select-interface-cmulti-select-value-change-detail-previous-value"></span>`previousValue` | `string[]` | - | Previous copied effective collection. |
| <span id="multi-select-interface-cmulti-select-value-change-detail-option"></span>`option` | `HTMLElement | None` | - | Activated Option or None for reset and structure. |
| <span id="multi-select-interface-cmulti-select-value-change-detail-selected"></span>`selected` | `bool` | - | Resulting selected state for the activated Option. |
| <span id="multi-select-interface-cmulti-select-value-change-detail-controlled"></span>`controlled` | `bool` | - | Whether client value owns selection. |
| <span id="multi-select-interface-cmulti-select-value-change-detail-source"></span>`source` | `CMultiSelectChangeSource` | - | Request source. |
| <span id="multi-select-interface-cmulti-select-value-change-detail-source-event"></span>`sourceEvent` | `Event | None` | - | Native source event when present. |

</div>

<span id="multi-select-interface-cmulti-select-open-change-detail"></span>

#### `CMultiSelectOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="multi-select-interface-cmulti-select-open-change-detail-open"></span>`open` | `bool` | - | Requested or forced visibility. |
| <span id="multi-select-interface-cmulti-select-open-change-detail-reason"></span>`reason` | `CMultiSelectOpenReason` | - | Visibility reason. |
| <span id="multi-select-interface-cmulti-select-open-change-detail-controlled"></span>`controlled` | `bool` | - | Whether client open owns visibility. |
| <span id="multi-select-interface-cmulti-select-open-change-detail-forced"></span>`forced` | `bool` | - | Whether safety made the close nonrejectable. |
| <span id="multi-select-interface-cmulti-select-open-change-detail-source"></span>`source` | `EventTarget | None` | - | Native source or safety owner. |

</div>

### Translation keys

-