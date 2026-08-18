---
title: Listbox
url: https://citry.dev/v/0.4.0/ui-library/components/listbox/
description: "Choose one or more values from a persistent collection."
---
# Listbox

Use `CListbox` when the choices should remain visible while people compare and
select them. Use Select or MultiSelect when the choices should open from a
compact form control.

## Listbox at a glance


### Listbox at a glance

[Open the rendered preview](/v/0.4.0/ui-library/components/listbox/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListboxAtAGlance(Component):
    template = """
      <c-CListbox label="Choose a workspace" value="atlas" variant="soft">
        <c-CListboxOption value="atlas">
          <c-fill name="default">Atlas research</c-fill>
          <c-fill name="description">12 collaborators</c-fill>
          <c-fill name="end">Active</c-fill>
        </c-CListboxOption>
        <c-CListboxOption value="aurora">
          <c-fill name="default">Aurora field notes</c-fill>
          <c-fill name="description">7 collaborators</c-fill>
        </c-CListboxOption>
        <c-CListboxOption value="archive" disabled>Archived studies</c-CListboxOption>
      </c-CListbox>
    """


preview = ListboxAtAGlance()
preview  # noqa: B018
````


## Select one value


### Select one value

[Open the rendered preview](/v/0.4.0/ui-library/components/listbox/_previews/single-selection/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SingleSelection(Component):
    template = """
      <c-CListbox label="Density" value="comfortable" mandatory variant="outline">
        <c-CListboxOption value="compact">Compact</c-CListboxOption>
        <c-CListboxOption value="comfortable">Comfortable</c-CListboxOption>
        <c-CListboxOption value="spacious">Spacious</c-CListboxOption>
      </c-CListbox>
    """


preview = SingleSelection()
preview  # noqa: B018
````


## Select several values


### Select several values

[Open the rendered preview](/v/0.4.0/ui-library/components/listbox/_previews/multiple-selection/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MultipleSelection(Component):
    template = """
      <c-CListbox label="Include signals" multiple c-value="['temperature', 'humidity']" variant="outline">
        <c-CListboxOption value="temperature">Temperature</c-CListboxOption>
        <c-CListboxOption value="humidity">Humidity</c-CListboxOption>
        <c-CListboxOption value="pressure">Pressure</c-CListboxOption>
        <c-CListboxOption value="wind">Wind speed</c-CListboxOption>
      </c-CListbox>
    """


preview = MultipleSelection()
preview  # noqa: B018
````


## Group related options


### Group options

[Open the rendered preview](/v/0.4.0/ui-library/components/listbox/_previews/groups/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GroupedOptions(Component):
    template = """
      <c-CListbox label="Choose a destination" value="prague">
        <c-CListboxGroup label="Europe">
          <c-CListboxOption value="prague">Prague</c-CListboxOption>
          <c-CListboxOption value="lisbon">Lisbon</c-CListboxOption>
        </c-CListboxGroup>
        <c-CListboxGroup label="Asia Pacific">
          <c-CListboxOption value="kyoto">Kyoto</c-CListboxOption>
          <c-CListboxOption value="wellington">Wellington</c-CListboxOption>
        </c-CListboxGroup>
      </c-CListbox>
    """


preview = GroupedOptions()
preview  # noqa: B018
````


## Control selection


### Control selection

[Open the rendered preview](/v/0.4.0/ui-library/components/listbox/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledListbox(Component):
    template = """
      <div x-data>
        <c-CListbox
          label="Review status"
          value="draft"
          $c-props="{
            value: $store.listboxExample.value,
            onValueChange: (next) => $store.listboxExample.value = next,
          }"
        >
          <c-CListboxOption value="draft">Draft</c-CListboxOption>
          <c-CListboxOption value="review">Ready for review</c-CListboxOption>
          <c-CListboxOption value="approved">Approved</c-CListboxOption>
        </c-CListbox>
        <p>Current: <strong x-text="$store.listboxExample.value"></strong></p>
      </div>
    """
    js = """
      Alpine.store('listboxExample', {value: 'draft'});
    """


preview = ControlledListbox()
preview  # noqa: B018
````


## Disabled collections and options


### Disable Listboxes and Options

[Open the rendered preview](/v/0.4.0/ui-library/components/listbox/_previews/disabled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisabledListbox(Component):
    template = """
      <c-CStack gap="lg">
        <c-CListbox label="Deployment region" value="eu" variant="outline">
          <c-CListboxOption value="eu">Europe</c-CListboxOption>
          <c-CListboxOption value="us" disabled>United States — unavailable</c-CListboxOption>
          <c-CListboxOption value="apac">Asia Pacific</c-CListboxOption>
        </c-CListbox>
        <c-CListbox label="Locked policy" value="strict" disabled variant="soft">
          <c-CListboxOption value="standard">Standard</c-CListboxOption>
          <c-CListboxOption value="strict">Strict</c-CListboxOption>
        </c-CListbox>
      </c-CStack>
    """


preview = DisabledListbox()
preview  # noqa: B018
````


## Keyboard navigation

Down and Up move between enabled Options. Home and End jump to the collection
edges, printable text performs buffered typeahead, Enter or Space selects, and
Escape clears a non-mandatory selection.


### Navigate a Listbox

[Open the rendered preview](/v/0.4.0/ui-library/components/listbox/_previews/keyboard/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class KeyboardListbox(Component):
    template = """
      <c-CListbox label="Jump to a city" value="brno" loop variant="outline">
        <c-CListboxOption value="brno">Brno</c-CListboxOption>
        <c-CListboxOption value="budapest">Budapest</c-CListboxOption>
        <c-CListboxOption value="krakow">Kraków</c-CListboxOption>
        <c-CListboxOption value="prague">Prague</c-CListboxOption>
        <c-CListboxOption value="vienna">Vienna</c-CListboxOption>
      </c-CListbox>
    """


preview = KeyboardListbox()
preview  # noqa: B018
````


## Customize Listbox


### Customize Listbox

[Open the rendered preview](/v/0.4.0/ui-library/components/listbox/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedListbox(Component):
    css = """
      .copper-listbox {
        --cui-listbox-radius: 1.1rem;
        --cui-listbox-selected-background: light-dark(#7c2d12, #fed7aa);
        --cui-listbox-selected-foreground: light-dark(#fff7ed, #431407);
        --cui-listbox-border-color: light-dark(#c2410c, #fdba74);
        --cui-listbox-option-padding: 0.7rem 0.8rem;
      }
    """
    template = """
      <c-CListbox label="Finish" value="copper" class_="copper-listbox" variant="outline">
        <c-CListboxOption value="copper">
          <c-fill name="start"><span aria-hidden="true">◆</span></c-fill>
          <c-fill name="default">Burnished copper</c-fill>
          <c-fill name="description">Warm and tactile</c-fill>
        </c-CListboxOption>
        <c-CListboxOption value="slate">Deep slate</c-CListboxOption>
        <c-CListboxOption value="linen">Soft linen</c-CListboxOption>
      </c-CListbox>
    """


preview = CustomizedListbox()
preview  # noqa: B018
````


## Accessibility and behavior

The named collection uses `role="listbox"`; Options use `role="option"`, and
visible group labels name `role="group"` collections. One enabled Option is in
the Tab order. Focus and selection remain separate, and disabled Options are
skipped by keyboard navigation.

`CListbox` is a persistent application selection surface, not a form control.
Use Select or MultiSelect when native form submission, reset, validity, or a
compact popup is required.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CListbox server inputs

Server inputs are passed in a template through `<c-CListbox ... />` or in Python through
`CListbox(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 8rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="listbox-input-clistbox-server-inputs-label"></span>`label` | `str` | required | Supplies the visible accessible Listbox name. |
| <span id="listbox-input-clistbox-server-inputs-value"></span>`value` | `str | None | Sequence[str]` ([`CListboxValue`](#listbox-interface-clistbox-value)) | `None` | Sets initial single or multiple selection. |
| <span id="listbox-input-clistbox-server-inputs-multiple"></span>`multiple` | `bool` | `False` | Enables independent multiple selection. |
| <span id="listbox-input-clistbox-server-inputs-mandatory"></span>`mandatory` | `bool` | `False` | Prevents user interaction from clearing the final selected Option. |
| <span id="listbox-input-clistbox-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables focus and selection throughout the collection. |
| <span id="listbox-input-clistbox-server-inputs-loop"></span>`loop` | `bool` | `False` | Wraps arrow navigation at collection edges. |
| <span id="listbox-input-clistbox-server-inputs-variant"></span>`variant` | `"plain" | "soft" | "outline"` ([`CListboxVariant`](#listbox-interface-clistbox-variant)) | `"outline"` | Selects surface treatment. |
| <span id="listbox-input-clistbox-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CListboxSize`](#listbox-interface-clistbox-size)) | `"md"` | Selects Option geometry. |
| <span id="listbox-input-clistbox-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#listbox-interface-clistbox-class-value)) | `None` | Adds root classes. |
| <span id="listbox-input-clistbox-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#listbox-interface-clistbox-style-value)) | `None` | Adds root inline styles. |
| <span id="listbox-input-clistbox-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted root attributes without replacing owned state structure or runtime. |
| <span id="listbox-input-clistbox-server-inputs-listbox-attrs"></span>`listbox_attrs` | `Mapping[str, object] | None` | `None` | Adds trusted attributes to the role listbox surface without replacing owned semantics or focus. |

</div>

#### CListbox client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CListbox />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="listbox-input-clistbox-client-inputs-value"></span>`value` | `string | string[] | null` | Releases control to committed selection. | Controls single or multiple selection while supplied. |
| <span id="listbox-input-clistbox-client-inputs-mandatory"></span>`mandatory` | `bool` | Uses the server value. | Reactively prevents the final user-selected value from clearing. |
| <span id="listbox-input-clistbox-client-inputs-disabled"></span>`disabled` | `bool` | Uses the server value. | Reactively disables collection interaction. |
| <span id="listbox-input-clistbox-client-inputs-loop"></span>`loop` | `bool` | Uses the server value. | Reactively changes arrow wrapping. |
| <span id="listbox-input-clistbox-client-inputs-variant"></span>`variant` | `"plain" | "soft" | "outline"` ([`CListboxVariant`](#listbox-interface-clistbox-variant)) | Uses the server value. | Reactively changes surface treatment. |
| <span id="listbox-input-clistbox-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CListboxSize`](#listbox-interface-clistbox-size)) | Uses the server value. | Reactively changes Option geometry. |
| <span id="listbox-input-clistbox-client-inputs-on-value-change"></span>`onValueChange` | `((value: string | string[] | null, detail: CListboxValueChangeDetail) => void) | undefined` | No component callback runs. | Receives selection and structural-recovery requests. |

</div>

#### CListboxOption server inputs

Server inputs are passed in a template through `<c-CListboxOption ... />` or in Python
through `CListboxOption(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 8rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="listbox-input-clistbox-option-server-inputs-value"></span>`value` | `str` | required | Supplies stable unique Option identity. |
| <span id="listbox-input-clistbox-option-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Prevents focus and selection for this Option. |
| <span id="listbox-input-clistbox-option-server-inputs-text-value"></span>`text_value` | `str | None` | `None` | Overrides normalized visible label text for typeahead. |
| <span id="listbox-input-clistbox-option-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#listbox-interface-clistbox-class-value)) | `None` | Adds classes to the concrete Option. |
| <span id="listbox-input-clistbox-option-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#listbox-interface-clistbox-style-value)) | `None` | Adds inline styles to the concrete Option. |
| <span id="listbox-input-clistbox-option-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted Option attributes without replacing semantics identity focus or state. |

</div>

#### CListboxOption client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CListboxOption />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="listbox-input-clistbox-option-client-inputs-disabled"></span>`disabled` | `bool` | Uses the server value. | Reactively disables this Option. |
| <span id="listbox-input-clistbox-option-client-inputs-text-value"></span>`textValue` | `string | null` | Uses the server value or visible label. | Reactively changes typeahead text. |

</div>

#### CListboxGroup server inputs

Server inputs are passed in a template through `<c-CListboxGroup ... />` or in Python
through `CListboxGroup(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 14rem; --ui-api-column-3-width: 8rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="listbox-input-clistbox-group-server-inputs-label"></span>`label` | `str` | required | Supplies the visible accessible group name. |
| <span id="listbox-input-clistbox-group-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#listbox-interface-clistbox-class-value)) | `None` | Adds classes to the group. |
| <span id="listbox-input-clistbox-group-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#listbox-interface-clistbox-style-value)) | `None` | Adds inline styles to the group. |
| <span id="listbox-input-clistbox-group-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds trusted group attributes without replacing owned semantics or label relationship. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CListbox slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="listbox-slot-clistbox-slots-default"></span>`default` | yes | `{}` ([`CListboxDefaultSlotData`](#listbox-interface-clistbox-default-slot-data)) | None. Accepts direct CListboxOption or CListboxGroup declarations. |

</div>

#### CListboxOption slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="listbox-slot-clistbox-option-slots-default"></span>`default` | yes | `{value}` ([`CListboxOptionDefaultSlotData`](#listbox-interface-clistbox-option-default-slot-data)) | None. Supplies visible accessible label content. |
| <span id="listbox-slot-clistbox-option-slots-start"></span>`start` | no | `{value, selected, disabled}` ([`CListboxOptionStateSlotData`](#listbox-interface-clistbox-option-state-slot-data)) | Omitted. Decorative leading content. |
| <span id="listbox-slot-clistbox-option-slots-description"></span>`description` | no | `{value}` ([`CListboxOptionDescriptionSlotData`](#listbox-interface-clistbox-option-description-slot-data)) | Omitted. Supplies separately described supporting text. |
| <span id="listbox-slot-clistbox-option-slots-end"></span>`end` | no | `{value, selected, disabled}` ([`CListboxOptionStateSlotData`](#listbox-interface-clistbox-option-state-slot-data)) | Omitted. Decorative trailing content. |

</div>

#### CListboxGroup slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="listbox-slot-clistbox-group-slots-default"></span>`default` | yes | `{}` ([`CListboxGroupDefaultSlotData`](#listbox-interface-clistbox-group-default-slot-data)) | None. Accepts one or more direct CListboxOption declarations. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CListbox events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="listbox-event-clistbox-events-value-change"></span>`onValueChange` | `(value: string | string[] | null, detail: CListboxValueChangeDetail) => void` ([`CListboxValueChangeDetail`](#listbox-interface-clistbox-value-change-detail)) | Enabled pointer or keyboard selection request or settled structural recovery. | `{value, previousValue, option, selected, controlled, source, sourceEvent}` ([`CListboxValueChangeDetail`](#listbox-interface-clistbox-value-change-detail)) | Commits immediately when uncontrolled and waits for owner acceptance when controlled. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CListbox CSS variables

Apply these variables to `CListbox` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="listbox-css-clistbox-css-variables-cui-listbox-gap"></span>`--cui-listbox-gap` | `length` | Gap between label and collection. | `0.375rem` |
| <span id="listbox-css-clistbox-css-variables-cui-listbox-max-block-size"></span>`--cui-listbox-max-block-size` | `length` | Maximum scrollable collection height. | `18rem` |
| <span id="listbox-css-clistbox-css-variables-cui-listbox-background"></span>`--cui-listbox-background` | `color` | Collection background. | `variant-derived Canvas surface` |
| <span id="listbox-css-clistbox-css-variables-cui-listbox-foreground"></span>`--cui-listbox-foreground` | `color` | Collection foreground. | `CanvasText` |
| <span id="listbox-css-clistbox-css-variables-cui-listbox-muted-color"></span>`--cui-listbox-muted-color` | `color` | Disabled and secondary foreground. | `light #667085; dark #a4a7ae` |
| <span id="listbox-css-clistbox-css-variables-cui-listbox-border-color"></span>`--cui-listbox-border-color` | `color` | Outline border. | `light #d0d5dd; dark #535862` |
| <span id="listbox-css-clistbox-css-variables-cui-listbox-hover-background"></span>`--cui-listbox-hover-background` | `color` | Enabled hover surface. | `7% CanvasText mix` |
| <span id="listbox-css-clistbox-css-variables-cui-listbox-selected-background"></span>`--cui-listbox-selected-background` | `color` | Selected Option surface. | `light #dbeafe; dark #1e3a5f` |
| <span id="listbox-css-clistbox-css-variables-cui-listbox-selected-foreground"></span>`--cui-listbox-selected-foreground` | `color` | Selected Option foreground. | `light #1849a9; dark #d1e9ff` |
| <span id="listbox-css-clistbox-css-variables-cui-listbox-focus-color"></span>`--cui-listbox-focus-color` | `color` | Roving focus outline. | `Highlight` |
| <span id="listbox-css-clistbox-css-variables-cui-listbox-radius"></span>`--cui-listbox-radius` | `length` | Collection corner radius. | `0.625rem` |
| <span id="listbox-css-clistbox-css-variables-cui-listbox-option-padding"></span>`--cui-listbox-option-padding` | `length` | Option block and inline padding. | `size-derived` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CListbox attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="listbox-attribute-clistbox-attributes-role-listbox"></span>`role` | Collection div | `listbox` | Declares the persistent selection widget. |
| <span id="listbox-attribute-clistbox-attributes-role-option"></span>`role` | Option div | `option` | Declares each selectable value. |
| <span id="listbox-attribute-clistbox-attributes-role-group"></span>`role` | Group div | `group` | Groups related Options under a visible label. |
| <span id="listbox-attribute-clistbox-attributes-aria-labelledby"></span>`aria-labelledby` | Collection Option or Group div | `IDREF` | Connects each semantic owner to its visible label. |
| <span id="listbox-attribute-clistbox-attributes-aria-selected"></span>`aria-selected` | Option div | `true | false` | Reflects effective selection. |
| <span id="listbox-attribute-clistbox-attributes-aria-disabled"></span>`aria-disabled` | Collection or Option div | `true | false` | Reflects effective unavailability. |
| <span id="listbox-attribute-clistbox-attributes-aria-multiselectable"></span>`aria-multiselectable` | Collection div | `true` | Present only in multiple mode. |
| <span id="listbox-attribute-clistbox-attributes-tabindex"></span>`tabindex` | Option div | `0 | -1` | Implements one enabled roving Tab stop. |
| <span id="listbox-attribute-clistbox-attributes-data-selected"></span>`data-selected` | Option div | `present-or-absent` | Mirrors selected styling state. |
| <span id="listbox-attribute-clistbox-attributes-data-active"></span>`data-active` | Option div | `present-or-absent` | Mirrors roving focus identity. |
| <span id="listbox-attribute-clistbox-attributes-data-disabled"></span>`data-disabled` | Root or Option div | `present-or-absent` | Mirrors effective unavailability. |
| <span id="listbox-attribute-clistbox-attributes-data-value"></span>`data-value` | Option div | `string` | Exposes canonical Option identity. |
| <span id="listbox-attribute-clistbox-attributes-data-multiple"></span>`data-multiple` | Root div | `present-or-absent` | Mirrors multiple selection mode. |
| <span id="listbox-attribute-clistbox-attributes-data-mandatory"></span>`data-mandatory` | Root div | `present-or-absent` | Mirrors final-selection protection. |
| <span id="listbox-attribute-clistbox-attributes-data-variant"></span>`data-variant` | Root div | `plain | soft | outline` | Mirrors effective surface treatment. |
| <span id="listbox-attribute-clistbox-attributes-data-size"></span>`data-size` | Root div | `sm | md | lg` | Mirrors effective geometry. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CListbox selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="listbox-selector-clistbox-selectors-part-root"></span>`[data-citry-ui-part="listbox-root"]` | Root div | Stable root attrs and state surface. |
| <span id="listbox-selector-clistbox-selectors-part-label"></span>`[data-citry-ui-part="listbox-label"]` | Label span | Visible collection label. |
| <span id="listbox-selector-clistbox-selectors-part-listbox"></span>`[data-citry-ui-part="listbox"]` | Collection div | Semantic and scrolling selection surface. |
| <span id="listbox-selector-clistbox-selectors-part-option"></span>`[data-citry-ui-part="listbox-option"]` | Option div | Stable Option attrs focus and state surface. |
| <span id="listbox-selector-clistbox-selectors-part-indicator"></span>`[data-citry-ui-part="listbox-indicator"]` | Indicator span | Decorative selected-state mark. |
| <span id="listbox-selector-clistbox-selectors-part-option-start"></span>`[data-citry-ui-part="listbox-option-start"]` | Start span | Decorative leading content wrapper. |
| <span id="listbox-selector-clistbox-selectors-part-option-copy"></span>`[data-citry-ui-part="listbox-option-copy"]` | Copy span | Stable label and description layout wrapper. |
| <span id="listbox-selector-clistbox-selectors-part-option-label"></span>`[data-citry-ui-part="listbox-option-label"]` | Label span | Visible Option name and default typeahead source. |
| <span id="listbox-selector-clistbox-selectors-part-option-description"></span>`[data-citry-ui-part="listbox-option-description"]` | Description span | Separately described supporting text. |
| <span id="listbox-selector-clistbox-selectors-part-option-end"></span>`[data-citry-ui-part="listbox-option-end"]` | End span | Decorative trailing content wrapper. |
| <span id="listbox-selector-clistbox-selectors-part-group"></span>`[data-citry-ui-part="listbox-group"]` | Group div | Stable semantic grouping surface. |
| <span id="listbox-selector-clistbox-selectors-part-group-label"></span>`[data-citry-ui-part="listbox-group-label"]` | Group label span | Visible group name. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="listbox-interface-clistbox-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="listbox-interface-clistbox-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |
| <span id="listbox-interface-clistbox-value"></span>`CListboxValue` | `str | None | Sequence[str]` |
| <span id="listbox-interface-clistbox-variant"></span>`CListboxVariant` | `Literal["plain", "soft", "outline"]` |
| <span id="listbox-interface-clistbox-size"></span>`CListboxSize` | `Literal["sm", "md", "lg"]` |
| <span id="listbox-interface-clistbox-source"></span>`CListboxChangeSource` | `Literal["pointer", "keyboard", "structure"]` |

</div>

<span id="listbox-interface-clistbox-default-slot-data"></span>

#### `CListboxDefaultSlotData`

Empty dataclass: `{}`.

<span id="listbox-interface-clistbox-group-default-slot-data"></span>

#### `CListboxGroupDefaultSlotData`

Empty dataclass: `{}`.

<span id="listbox-interface-clistbox-option-default-slot-data"></span>

#### `CListboxOptionDefaultSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="listbox-interface-clistbox-option-default-slot-data-value"></span>`value` | `str` | - | Canonical Option identity. |

</div>

<span id="listbox-interface-clistbox-option-state-slot-data"></span>

#### `CListboxOptionStateSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="listbox-interface-clistbox-option-state-slot-data-value"></span>`value` | `str` | - | Canonical Option identity. |
| <span id="listbox-interface-clistbox-option-state-slot-data-selected"></span>`selected` | `bool` | - | Server-rendered initial selected state. |
| <span id="listbox-interface-clistbox-option-state-slot-data-disabled"></span>`disabled` | `bool` | - | Server-rendered initial Option disabled state. |

</div>

<span id="listbox-interface-clistbox-option-description-slot-data"></span>

#### `CListboxOptionDescriptionSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="listbox-interface-clistbox-option-description-slot-data-value"></span>`value` | `str` | - | Canonical Option identity. |

</div>

<span id="listbox-interface-clistbox-value-change-detail"></span>

#### `CListboxValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="listbox-interface-clistbox-value-change-detail-value"></span>`value` | `str | list[str] | None` | - | Requested next effective value. |
| <span id="listbox-interface-clistbox-value-change-detail-previous-value"></span>`previousValue` | `str | list[str] | None` | - | Prior effective value. |
| <span id="listbox-interface-clistbox-value-change-detail-option"></span>`option` | `HTMLElement | None` | - | Changed Option or None for structural recovery. |
| <span id="listbox-interface-clistbox-value-change-detail-selected"></span>`selected` | `bool` | - | Whether the Option is requested selected. |
| <span id="listbox-interface-clistbox-value-change-detail-controlled"></span>`controlled` | `bool` | - | Whether the client value currently controls selection. |
| <span id="listbox-interface-clistbox-value-change-detail-source"></span>`source` | `"pointer" | "keyboard" | "structure"` ([`CListboxChangeSource`](#listbox-interface-clistbox-source)) | - | Request source. |
| <span id="listbox-interface-clistbox-value-change-detail-source-event"></span>`sourceEvent` | `Event | None` | - | Native source event or None for structure. |

</div>

### Translation keys

-