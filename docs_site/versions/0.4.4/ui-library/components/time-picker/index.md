---
title: TimePicker
url: https://citry.dev/v/0.4.4/ui-library/components/time-picker/
description: "Select one canonical wall-clock time from a localized finite popup list."
---
# TimePicker

Use `CTimePicker` when people choose from a bounded schedule and the active
Citry locale should format every visible time. It submits the same canonical
`HH:MM` or `HH:MM:SS` string as a native time input.

## Pick from regular intervals

The default fifteen-minute step produces a finite day list. Bounds limit the
choices; a later minimum than maximum creates a wrapped overnight interval.


```citry-html
<c-CField required>
  <c-fill name="label">Appointment time</c-fill>
  <c-fill name="default"><c-CTimePicker name="appointment" min="09:00" max="17:00" /></c-fill>
</c-CField>
```



### Pick an appointment time

[Open the rendered preview](/v/0.4.4/ui-library/components/time-picker/_previews/basic/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicTimePicker(Component):
    template = """
      <c-CField required>
        <c-fill name="label">Appointment time</c-fill>
        <c-fill name="description">Choose a fifteen-minute slot.</c-fill>
        <c-fill name="default"><c-CTimePicker name="appointment" min="09:00" max="12:00" value="09:30" /></c-fill>
      </c-CField>
    """


preview = BasicTimePicker()
preview  # noqa: B018
````


## Supply exact choices

Use `options` for irregular schedules or second precision. Options are checked,
bounded, unique, and preserve server order. Structural option changes require a
server rerender.


### Supply exact time choices

[Open the rendered preview](/v/0.4.4/ui-library/components/time-picker/_previews/options/)

````citry
from datetime import time
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTimePicker

citry.register_library(citry_ui)


class TimePickerOptions(Component):
    def template_data(self, kwargs, slots) -> dict[str, Any]:  # noqa: ANN001, ARG002
        return {
            "picker": CTimePicker(
                name="departure", value=time(23, 5, 9), options=(time(23, 5, 9), "00:00:10", "12:30:45")
            )
        }

    template = """
      <section>
        <h3>Irregular second-precision departures</h3>
        {{ picker }}
      </section>
    """


preview = TimePickerOptions()
preview  # noqa: B018
````


## Submit and reset

The hidden native time control remains the single Form transport and the
no-JavaScript control. `CField` and `CForm` own shared state; the nested Listbox
never becomes another form field.


### Submit and reset a time picker

[Open the rendered preview](/v/0.4.4/ui-library/components/time-picker/_previews/form/)

````citry
import citry_ui
from citry import Component, citry

# ruff: noqa: E501 - embedded Citry templates remain readable

citry.register_library(citry_ui)


class TimePickerForm(Component):
    template = """
      <form x-data="{result:'Submit to inspect FormData'}" @submit.prevent="result=JSON.stringify(Object.fromEntries(new FormData($event.target)))">
        <c-CField required>
          <c-fill name="label">Start time</c-fill>
          <c-fill name="default"><c-CTimePicker name="start" min="08:00" max="10:00" value="09:00" /></c-fill>
        </c-CField>
        <c-CButton type="submit">Submit</c-CButton>
        <c-CButton type="reset" variant="outline">Reset</c-CButton>
        <output x-text="result">Submit to inspect FormData</output>
      </form>
    """


preview = TimePickerForm()
preview  # noqa: B018
````


## Control value and visibility

Client `value` and `open` are independently controlled while supplied.
`onValueChange` and `onOpenChange` report requests; omission releases each
channel at its latest committed value.


### Control time and popup state

[Open the rendered preview](/v/0.4.4/ui-library/components/time-picker/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

# ruff: noqa: E501 - embedded Citry templates remain readable

citry.register_library(citry_ui)


class ControlledTimePicker(Component):
    template = """
      <section x-data="{value:'09:30',open:false,last:'No request yet'}" style="display:grid;gap:.75rem;max-width:24rem">
        <c-CTimePicker min="09:00" max="11:00" $c-props="{value,open,onValueChange:(next,detail)=>{last=`${detail.source}: ${next}`;value=next},onOpenChange:(next)=>open=next}" />
        <output x-text="last">No request yet</output>
      </section>
    """


preview = ControlledTimePicker()
preview  # noqa: B018
````


## Switch locales in place

The server renders source-locale text first. Under a client-enabled `c-i18n`
provider, the trigger, popup name, clear label, validity message, and generated
option labels update when the locale changes. Canonical Form values do not.


### Format time choices by locale

[Open the rendered preview](/v/0.4.4/ui-library/components/time-picker/_previews/locales/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class LocalizedTimePicker(Component):
    template = """
      <c-i18n tag="section" client>
        <div style="display:flex;gap:.5rem;margin-block-end:1rem">
          <c-CButton type="button" @click="$i18n.switchLocale('en-US')">English</c-CButton>
          <c-CButton type="button" @click="$i18n.switchLocale('cs-CZ')">Čeština</c-CButton>
        </div>
        <c-CTimePicker value="14:30" min="13:00" max="16:00" />
      </c-i18n>
    """


preview = LocalizedTimePicker()
preview  # noqa: B018
````


Literal `placeholder`, `picker_label`, `change_label`, `clear_label`, and
`unavailable_message` overrides remain exactly application-owned and do not
register catalog bindings.

## Compare states and styles

Outline, filled, and plain variants combine with sm, md, and lg sizes. The
picker inherits Popover collision handling, Listbox keyboard behavior, forced
colors, logical direction, and reduced-motion handling.


### Compare TimePicker states

[Open the rendered preview](/v/0.4.4/ui-library/components/time-picker/_previews/states/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimePickerStates(Component):
    template = """
      <section style="display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:1rem">
        <c-CTimePicker value="09:00" min="08:00" max="12:00" />
        <c-CTimePicker value="10:15" min="08:00" max="12:00" variant="filled" size="sm" />
        <c-CTimePicker value="11:30" min="08:00" max="12:00" variant="plain" size="lg" readonly />
        <c-CTimePicker value="12:00" min="08:00" max="12:00" invalid />
        <c-CTimePicker value="08:30" min="08:00" max="12:00" disabled />
      </section>
    """


preview = TimePickerStates()
preview  # noqa: B018
````


<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CTimePicker server inputs

Server inputs are passed in a template through `<c-CTimePicker ... />` or in Python through
`CTimePicker(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 18rem; --ui-api-column-3-width: 16rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="time-picker-input-ctime-picker-server-inputs-value"></span>`value` | `CTimePickerTime | None` ([`CTimePickerTime`](#time-picker-interface-time)) | `None` | Sets the initial and reset canonical time or empty value and must be an available option. |
| <span id="time-picker-input-ctime-picker-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the native transport Form field name. |
| <span id="time-picker-input-ctime-picker-server-inputs-form"></span>`form` | `str | None` | `None` | Associates the native transport with an external Form ID. |
| <span id="time-picker-input-ctime-picker-server-inputs-id"></span>`id` | `str | None` | generated | Sets the public no-JavaScript input or enhanced Button ID and owned ID prefix. |
| <span id="time-picker-input-ctime-picker-server-inputs-min"></span>`min` | `CTimePickerTime | None` ([`CTimePickerTime`](#time-picker-interface-time)) | `None` | Sets the inclusive first selectable time and may begin a wrapped interval. |
| <span id="time-picker-input-ctime-picker-server-inputs-max"></span>`max` | `CTimePickerTime | None` ([`CTimePickerTime`](#time-picker-interface-time)) | `None` | Sets the inclusive last selectable time and may end a wrapped interval. |
| <span id="time-picker-input-ctime-picker-server-inputs-step"></span>`step` | `int` | `900` | Generates choices at an exact interval of at least 300 seconds when options is absent. |
| <span id="time-picker-input-ctime-picker-server-inputs-options"></span>`options` | `Sequence[CTimePickerTime] | None` | `None` | Supplies one through 288 unique exact choices in server order instead of generated intervals. |
| <span id="time-picker-input-ctime-picker-server-inputs-required"></span>`required` | `bool | None` | `None` | Enables native empty-value validity outside Field; Field owns it inside Field. |
| <span id="time-picker-input-ctime-picker-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Blocks opening selection clearing and Form participation outside Field; Form disabledness also wins. |
| <span id="time-picker-input-ctime-picker-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Keeps the picker focusable and submitted but blocks value changes. |
| <span id="time-picker-input-ctime-picker-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Adds application invalid state to revealed native validity. |
| <span id="time-picker-input-ctime-picker-server-inputs-clearable"></span>`clearable` | `bool` | `True` | Shows a clear action for an optional non-empty writable value. |
| <span id="time-picker-input-ctime-picker-server-inputs-dismissible"></span>`dismissible` | `bool` | `True` | Permits Escape outside and focus-outside close requests. |
| <span id="time-picker-input-ctime-picker-server-inputs-placement"></span>`placement` | `CPopoverPlacement` ([`CPopoverPlacement`](#time-picker-interface-popover-placement)) | `"bottom-start"` | Sets the preferred logical Popover placement. |
| <span id="time-picker-input-ctime-picker-server-inputs-match-width"></span>`match_width` | `bool` | `True` | Makes the Popover at least as wide as the visible control. |
| <span id="time-picker-input-ctime-picker-server-inputs-placeholder"></span>`placeholder` | `str` | `"Choose a time"` | Supplies visible empty-state text when explicitly overridden. |
| <span id="time-picker-input-ctime-picker-server-inputs-picker-label"></span>`picker_label` | `str` | `"Choose time"` | Names the popup Listbox and empty trigger when explicitly overridden. |
| <span id="time-picker-input-ctime-picker-server-inputs-change-label"></span>`change_label` | `str` | `"Change time, {time}"` | Formats a selected trigger name and must retain the time placeholder when explicitly overridden. |
| <span id="time-picker-input-ctime-picker-server-inputs-clear-label"></span>`clear_label` | `str` | `"Clear time"` | Names the clear Button when explicitly overridden. |
| <span id="time-picker-input-ctime-picker-server-inputs-unavailable-message"></span>`unavailable_message` | `str` | `"Choose an available time."` | Supplies native custom validity if a selected value is unavailable. |
| <span id="time-picker-input-ctime-picker-server-inputs-variant"></span>`variant` | `CTimePickerVariant` ([`CTimePickerVariant`](#time-picker-interface-variant)) | `"outline"` | Selects outline filled or plain field treatment. |
| <span id="time-picker-input-ctime-picker-server-inputs-size"></span>`size` | `CTimePickerSize` ([`CTimePickerSize`](#time-picker-interface-size)) | `"md"` | Selects coordinated control and text sizing. |
| <span id="time-picker-input-ctime-picker-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#time-picker-interface-class-value)) | `None` | Adds classes to the root and merges with attrs. |
| <span id="time-picker-input-ctime-picker-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#time-picker-interface-style-value)) | `None` | Adds styles to the root and merges with attrs. |
| <span id="time-picker-input-ctime-picker-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes without replacing owned state identity or runtime markers. |

</div>

#### CTimePicker client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CTimePicker />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 18rem; --ui-api-column-3-width: 18rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="time-picker-input-ctime-picker-client-inputs-value"></span>`value` | `canonical string | null` | Releases control at the latest committed value. | Controls selected and submitted time while supplied. |
| <span id="time-picker-input-ctime-picker-client-inputs-open"></span>`open` | `boolean | null` | Releases control at the latest committed visibility. | Controls popup visibility while supplied. |
| <span id="time-picker-input-ctime-picker-client-inputs-required"></span>`required` | `boolean` | Uses server or Field state. | Controls standalone required validity. |
| <span id="time-picker-input-ctime-picker-client-inputs-disabled"></span>`disabled` | `boolean` | Uses server or owner state. | Controls interaction and Form participation. |
| <span id="time-picker-input-ctime-picker-client-inputs-readonly"></span>`readonly` | `boolean` | Uses server or owner state. | Controls focusable nonmutable state. |
| <span id="time-picker-input-ctime-picker-client-inputs-invalid"></span>`invalid` | `boolean` | Uses server or Field state. | Controls application invalid state. |
| <span id="time-picker-input-ctime-picker-client-inputs-clearable"></span>`clearable` | `boolean` | Uses the server input. | Controls the optional clear action. |
| <span id="time-picker-input-ctime-picker-client-inputs-dismissible"></span>`dismissible` | `boolean` | Uses the server input. | Controls passive popup dismissal. |
| <span id="time-picker-input-ctime-picker-client-inputs-placement"></span>`placement` | `CPopoverPlacement` ([`CPopoverPlacement`](#time-picker-interface-popover-placement)) | Uses the server input. | Controls preferred logical placement. |
| <span id="time-picker-input-ctime-picker-client-inputs-match-width"></span>`matchWidth` | `boolean` | Uses the server input. | Controls trigger-width matching. |
| <span id="time-picker-input-ctime-picker-client-inputs-variant"></span>`variant` | `CTimePickerVariant` ([`CTimePickerVariant`](#time-picker-interface-variant)) | Uses the server input. | Controls field presentation. |
| <span id="time-picker-input-ctime-picker-client-inputs-size"></span>`size` | `CTimePickerSize` ([`CTimePickerSize`](#time-picker-interface-size)) | Uses the server input. | Controls coordinated sizing. |
| <span id="time-picker-input-ctime-picker-client-inputs-on-value-change"></span>`onValueChange` | `function` | No semantic value callback. | Receives option clear native and reset value requests. |
| <span id="time-picker-input-ctime-picker-client-inputs-on-open-change"></span>`onOpenChange` | `function` | No semantic visibility callback. | Receives trigger selection dismissal reset and forced-close requests. |

</div>

### Slots

-

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CTimePicker events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="time-picker-event-ctime-picker-events-on-value-change"></span>`onValueChange` | `(value: string | null, detail: CTimePickerValueChangeDetail) => void` ([`CTimePickerValueChangeDetail`](#time-picker-interface-ctime-picker-value-change-detail)) | Listbox selection clear reset or native fallback editing requests another value. | `{value, previousValue, controlled, source, sourceEvent}` ([`CTimePickerValueChangeDetail`](#time-picker-interface-ctime-picker-value-change-detail)) | Uncontrolled user commits emit native input/change; controlled requests wait for the owner. |
| <span id="time-picker-event-ctime-picker-events-on-open-change"></span>`onOpenChange` | `(open: boolean, detail: CTimePickerOpenChangeDetail) => void` ([`CTimePickerOpenChangeDetail`](#time-picker-interface-ctime-picker-open-change-detail)) | Trigger selection clear reset Escape outside focus-outside native or forced layer changes request visibility. | `{reason, controlled, forced, source}` ([`CTimePickerOpenChangeDetail`](#time-picker-interface-ctime-picker-open-change-detail)) | Uncontrolled requests commit before notification; controlled requests wait except forced safety closure. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CTimePicker CSS variables

Apply these variables to `CTimePicker` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="time-picker-css-ctime-picker-css-variables-background"></span>`--cui-time-picker-background` | `color` | Visible control and clear background. | `Canvas or variant-derived.` |
| <span id="time-picker-css-ctime-picker-css-variables-foreground"></span>`--cui-time-picker-foreground` | `color` | Text and icon color. | `CanvasText` |
| <span id="time-picker-css-ctime-picker-css-variables-border-color"></span>`--cui-time-picker-border-color` | `color` | Visible control and clear boundary. | `Mixed CanvasText.` |
| <span id="time-picker-css-ctime-picker-css-variables-invalid-border-color"></span>`--cui-time-picker-invalid-border-color` | `color` | Revealed invalid control boundary. | `Theme error.` |
| <span id="time-picker-css-ctime-picker-css-variables-focus-color"></span>`--cui-time-picker-focus-color` | `color` | Control and clear focus outline. | `Highlight` |
| <span id="time-picker-css-ctime-picker-css-variables-radius"></span>`--cui-time-picker-radius` | `length` | Visible control and clear corner radius. | `0.625rem` |
| <span id="time-picker-css-ctime-picker-css-variables-min-block-size"></span>`--cui-time-picker-min-block-size` | `length` | Minimum interactive control height. | `2.5rem` |
| <span id="time-picker-css-ctime-picker-css-variables-padding-inline"></span>`--cui-time-picker-padding-inline` | `length` | Visible control inline inset. | `0.75rem` |
| <span id="time-picker-css-ctime-picker-css-variables-gap"></span>`--cui-time-picker-gap` | `length` | Visible value and icon gap. | `0.5rem` |
| <span id="time-picker-css-ctime-picker-css-variables-list-max-block-size"></span>`--cui-time-picker-list-max-block-size` | `length` | Maximum scrollable option-list height. | `18rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CTimePicker attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="time-picker-attribute-ctime-picker-root-attributes-data-empty"></span>`data-empty` | Root | `present | absent` | Marks no committed canonical value. |
| <span id="time-picker-attribute-ctime-picker-root-attributes-data-open"></span>`data-open` | Root | `present | absent` | Mirrors effective popup visibility. |
| <span id="time-picker-attribute-ctime-picker-root-attributes-data-required"></span>`data-required` | Root | `present | absent` | Mirrors effective requiredness. |
| <span id="time-picker-attribute-ctime-picker-root-attributes-data-disabled"></span>`data-disabled` | Root | `present | absent` | Mirrors effective disabledness. |
| <span id="time-picker-attribute-ctime-picker-root-attributes-data-readonly"></span>`data-readonly` | Root | `present | absent` | Mirrors effective readonly state. |
| <span id="time-picker-attribute-ctime-picker-root-attributes-data-invalid"></span>`data-invalid` | Root | `present | absent` | Mirrors application unavailable or revealed native invalidity. |
| <span id="time-picker-attribute-ctime-picker-root-attributes-data-variant"></span>`data-variant` | Root | `CTimePickerVariant` ([`CTimePickerVariant`](#time-picker-interface-variant)) | Mirrors visual treatment. |
| <span id="time-picker-attribute-ctime-picker-root-attributes-data-size"></span>`data-size` | Root | `CTimePickerSize` ([`CTimePickerSize`](#time-picker-interface-size)) | Mirrors coordinated sizing. |
| <span id="time-picker-attribute-ctime-picker-root-attributes-data-enhanced"></span>`data-enhanced` | Root | `present | absent` | Marks completed custom control activation. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CTimePicker selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="time-picker-selector-ctime-picker-selectors-time-picker"></span>`[data-citry-ui-part="time-picker"]` | Root div | State reflection attrs and styling destination. |
| <span id="time-picker-selector-ctime-picker-selectors-fallback-input"></span>`[data-citry-ui-part="fallback-input"]` | Native Time input | No-JavaScript control and enhanced Form reset validity transport. |
| <span id="time-picker-selector-ctime-picker-selectors-enhanced-control"></span>`[data-citry-ui-part="enhanced-control"]` | Layout div | Groups the Popover activator and optional clear action. |
| <span id="time-picker-selector-ctime-picker-selectors-control"></span>`[data-citry-ui-part="control"]` | Native Button | Full-width popup activator and enhanced public focus target. |
| <span id="time-picker-selector-ctime-picker-selectors-value"></span>`[data-citry-ui-part="value"]` | Span | Displays localized selected time or placeholder. |
| <span id="time-picker-selector-ctime-picker-selectors-clear"></span>`[data-citry-ui-part="clear"]` | Native Button | Requests an empty optional value. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="time-picker-interface-time"></span>`CTimePickerTime` | `time | str` |
| <span id="time-picker-interface-variant"></span>`CTimePickerVariant` | `Literal["outline", "filled", "plain"]` |
| <span id="time-picker-interface-size"></span>`CTimePickerSize` | `Literal["sm", "md", "lg"]` |
| <span id="time-picker-interface-value-source"></span>`CTimePickerValueChangeSource` | `Literal["option", "clear", "reset", "native"]` |
| <span id="time-picker-interface-popover-placement"></span>`CPopoverPlacement` | `Literal["top-start", "top", "top-end", "bottom-start", "bottom", "bottom-end"]` |
| <span id="time-picker-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="time-picker-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="time-picker-interface-ctime-picker-value-change-detail"></span>

#### `CTimePickerValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="time-picker-interface-ctime-picker-value-change-detail-value"></span>`value` | `string | null` | - | Requested selected canonical time or empty state. |
| <span id="time-picker-interface-ctime-picker-value-change-detail-previous-value"></span>`previousValue` | `string | null` | - | Effective time before the request. |
| <span id="time-picker-interface-ctime-picker-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client value owns the commit. |
| <span id="time-picker-interface-ctime-picker-value-change-detail-source"></span>`source` | `CTimePickerValueChangeSource` ([`CTimePickerValueChangeSource`](#time-picker-interface-value-source)) | - | Option clear reset or native cause. |
| <span id="time-picker-interface-ctime-picker-value-change-detail-source-event"></span>`sourceEvent` | `object | null` | - | Native interaction event when one exists. |

</div>

<span id="time-picker-interface-ctime-picker-open-change-detail"></span>

#### `CTimePickerOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="time-picker-interface-ctime-picker-open-change-detail-reason"></span>`reason` | `trigger | selection | clear | reset | escape | outside | focus-outside | native | ancestor | modal` | - | Exact request or forced-close cause. |
| <span id="time-picker-interface-ctime-picker-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client open owns ordinary visibility commits. |
| <span id="time-picker-interface-ctime-picker-open-change-detail-forced"></span>`forced` | `boolean` | - | Whether ancestor or modal safety required closure. |
| <span id="time-picker-interface-ctime-picker-open-change-detail-source"></span>`source` | `object | null` | - | Associated browser source when one exists. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CTimePicker translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="time-picker-translation-ctime-picker-translations-placeholder"></span>`citry-ui-time-picker-placeholder` | Displays the empty control value. | `none` | `placeholder` | Parent i18n subscription calls `tr()` because the same destination later displays formatted times. |
| <span id="time-picker-translation-ctime-picker-translations-label"></span>`citry-ui-time-picker-label` | Names the popup Listbox and empty trigger. | `none` | `picker_label` | `$c-tr` updates the stable title; parent subscription updates the dynamic trigger name. |
| <span id="time-picker-translation-ctime-picker-translations-change"></span>`citry-ui-time-picker-change` | Names a selected trigger. | `` `time: str` localized by a time display profile `` | `change_label` containing `{time}` | Parent i18n subscription recomputes the formatted value and calls `tr()`. |
| <span id="time-picker-translation-ctime-picker-translations-clear"></span>`citry-ui-time-picker-clear` | Names the optional clear Button. | `none` | `clear_label` | `$c-tr` updates the stable aria-label destination. |
| <span id="time-picker-translation-ctime-picker-translations-unavailable"></span>`citry-ui-time-picker-unavailable` | Supplies native custom validity when the value is unavailable. | `none` | `unavailable_message` | `i18n.bind()` updates the browser-owned validity message. |

</div>