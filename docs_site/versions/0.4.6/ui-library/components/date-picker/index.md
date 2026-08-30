---
title: DatePicker
url: https://citry.dev/v/0.4.6/ui-library/components/date-picker/
description: "Choose one canonical date from a localized popup Calendar."
---
# DatePicker

Use `CDatePicker` when an application needs Citry's consistent localized
Calendar in a compact field-like control. Its display follows the active
locale, while its value and Form output remain canonical `YYYY-MM-DD` dates.

## Choose one date

Compose DatePicker in `CField` for a visible label, description, error, and
shared required, disabled, readonly, or invalid state.


```citry-html
<c-CField required>
  <c-fill name="label">Arrival date</c-fill>
  <c-fill name="default"><c-CDatePicker name="arrival" /></c-fill>
</c-CField>
```



### Choose one date

[Open the rendered preview](/v/0.4.6/ui-library/components/date-picker/_previews/basic/)

````citry
# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

from datetime import date
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CDatePicker

citry.register_library(citry_ui)


class BasicDatePicker(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"python_picker": CDatePicker(value=date(2026, 8, 19))}

    template = """
      <section class="date-picker-demo-grid">
        <c-CField required>
          <c-fill name="label">Arrival date</c-fill>
          <c-fill name="description">Choose your check-in day.</c-fill>
          <c-fill name="default"><c-CDatePicker name="arrival" value="2026-08-19" /></c-fill>
        </c-CField>
        <article><h3>Python composition</h3>{{ python_picker }}</article>
      </section>
    """
    css = ":where(.date-picker-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:1.25rem}:where(.date-picker-demo-grid article){display:grid;align-content:start;gap:.75rem}:where(.date-picker-demo-grid h3){margin:0}"


preview = BasicDatePicker()
preview  # noqa: B018
````


The whole visible field is a native Button, not a small detached icon. Opening
moves focus to the selected date or the Calendar's current focus candidate.
Selecting an available date closes the Popover and restores focus to the
field.

## Pick the right date family

Use `CDateInput` when direct native editing, the browser's platform picker, or
the shortest no-JavaScript path is the priority. Use `CCalendar` when dates
must stay visible. DatePicker is the composed popup route and deliberately does
not parse localized typed text.

## Submit and reset a canonical value

One native Date input owns `name`, `form`, required validity, reset, and
FormData. Enhancement hides it visually and gives its public ID to the visible
Button. Without JavaScript it remains the complete usable control.


### Submit and reset DatePicker

[Open the rendered preview](/v/0.4.6/ui-library/components/date-picker/_previews/form/)

````citry
# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DatePickerForm(Component):
    template = """
      <section x-data="{submitted:'Submit to inspect FormData'}">
        <form @submit.prevent="submitted=JSON.stringify(Array.from(new FormData($event.target).entries()))">
          <c-CField control_id="trip-date" required>
            <c-fill name="label">Trip date</c-fill>
            <c-fill name="description">The submitted value stays canonical.</c-fill>
            <c-fill name="default"><c-CDatePicker id="trip-date" name="trip_date" value="2026-08-19" /></c-fill>
            <c-fill name="error">Choose a trip date.</c-fill>
          </c-CField>
          <div><button type="submit">Submit</button> <button type="reset">Reset</button></div>
        </form>
        <output x-text="submitted">Submit to inspect FormData</output>
      </section>
    """
    css = ":where(form){display:grid;gap:.75rem;max-inline-size:28rem}:where(output){display:block;margin-block-start:.75rem;overflow-wrap:anywhere}"


preview = DatePickerForm()
preview  # noqa: B018
````


Uncontrolled user selection emits bubbling native `input` followed by
`change`. Controlled requests wait for the owner and emit neither transport
event until the owner commits its prop.

## Bound and block dates

`min` and `max` are inclusive. `unavailable_dates` accepts at most 4096 unique
exact dates. Calendar keeps unavailable dates focusable for inspection but
rejects selection. Always validate availability again on the server.


### Constrain available dates

[Open the rendered preview](/v/0.4.6/ui-library/components/date-picker/_previews/constraints/)

````citry
# ruff: noqa: E501 - embedded example markup stays readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DatePickerConstraints(Component):
    template = """
      <c-CField>
        <c-fill name="label">Workshop day</c-fill>
        <c-fill name="description">August 20, 24, and 27 are already booked.</c-fill>
        <c-fill name="default">
          <c-CDatePicker value="2026-08-19" min="2026-08-10" max="2026-09-15" c-unavailable_dates="('2026-08-20','2026-08-24','2026-08-27')" />
        </c-fill>
      </c-CField>
    """


preview = DatePickerConstraints()
preview  # noqa: B018
````


## Clear and compare states

An optional non-empty DatePicker shows a clear Button by default. Required
controls never expose it. Readonly permits opening and Calendar navigation but
blocks selection; disabled blocks opening and Form participation.


### Clear and compare DatePicker states

[Open the rendered preview](/v/0.4.6/ui-library/components/date-picker/_previews/states/)

````citry
# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DatePickerStates(Component):
    template = """
      <section class="date-picker-states">
        <article><h3>Optional and clearable</h3><c-CDatePicker value="2026-08-19" /></article>
        <article><h3>Required</h3><c-CDatePicker value="2026-08-20" required /></article>
        <article><h3>Readonly</h3><c-CDatePicker value="2026-08-21" readonly /></article>
        <article><h3>Disabled</h3><c-CDatePicker value="2026-08-22" disabled /></article>
        <article><h3>Invalid large</h3><c-CDatePicker value="2026-08-23" invalid size="lg" /></article>
        <article><h3>Small filled</h3><c-CDatePicker value="2026-08-24" variant="filled" size="sm" /></article>
      </section>
    """
    css = ":where(.date-picker-states){display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem}:where(.date-picker-states article){display:grid;align-content:start;gap:.5rem}:where(.date-picker-states h3){margin:0;font-size:.9rem}"


preview = DatePickerStates()
preview  # noqa: B018
````


## Control value and open state independently

Client `value` and `open` are separate controlled channels. A controlled
selection or open/close interaction calls `onValueChange` or `onOpenChange`
without claiming it committed. Return the accepted value through `$c-props`.


### Control value and popup state

[Open the rendered preview](/v/0.4.6/ui-library/components/date-picker/_previews/controlled/)

````citry
# ruff: noqa: E501 - embedded example markup stays readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledDatePicker(Component):
    template = """
      <section x-data="{value:'2026-08-19',open:false,last:'No request yet'}">
        <p>Value: <strong x-text="value || 'empty'"></strong>; popup: <strong x-text="open ? 'open' : 'closed'"></strong></p>
        <c-CDatePicker
          value="2026-08-19"
          $c-props="{value,open,onValueChange:(next,detail)=>{last=`${detail.source}: ${next}`;value=next},onOpenChange:(next,detail)=>{last=`${detail.reason}: ${next}`;open=next}}"
        />
        <div><button type="button" @click="value='2026-08-25'">Set August 25</button> <button type="button" @click="open=!open">Toggle popup</button></div>
        <output x-text="last">No request yet</output>
      </section>
    """
    css = ":where(section){display:grid;gap:.75rem;max-inline-size:28rem}:where(section p){margin:0}"


preview = ControlledDatePicker()
preview  # noqa: B018
````


Omitting either client prop releases that channel at its latest committed
state. The other channel remains controlled.

## Follow the active locale

Under a client-enabled `<c-i18n>` provider, the display value, trigger name,
popup title, clear name, Calendar heading, weekdays, day numbers, and full date
names switch in place. The ISO value does not change. Non-Gregorian display
calendars remain mapped to the same Gregorian domain date.


### Use locale-aware DatePicker output

[Open the rendered preview](/v/0.4.6/ui-library/components/date-picker/_previews/locales/)

````citry
# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DatePickerLocales(Component):
    template = """
      <section class="date-picker-locales">
        <article><h3>Provider locale week</h3><c-CDatePicker value="2026-08-19" /></article>
        <article><h3>Explicit Monday start</h3><c-CDatePicker value="2026-08-19" c-first_day_of_week="1" /></article>
        <article lang="ar" dir="rtl"><h3>RTL scope</h3><c-CDatePicker value="2026-08-19" /></article>
      </section>
    """
    css = ":where(.date-picker-locales){display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem}:where(.date-picker-locales article){display:grid;align-content:start;gap:.5rem;padding:.75rem}:where(.date-picker-locales h3){margin:0}"


preview = DatePickerLocales()
preview  # noqa: B018
````


`first_day_of_week` overrides only the week start. Leave it unset to follow
locale data.

## Configure placement

DatePicker uses the existing non-modal Popover contract. Choose one of six
logical placements and use `match_width` when the surface should be at least
the field width. Collision repair may use another rendered side.


### Configure logical placement

[Open the rendered preview](/v/0.4.6/ui-library/components/date-picker/_previews/placement/)

````citry
# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DatePickerPlacement(Component):
    template = """
      <section class="date-picker-placement">
        <article><h3>Bottom start and matched</h3><c-CDatePicker value="2026-08-19" /></article>
        <article><h3>Top end and intrinsic</h3><c-CDatePicker value="2026-08-20" placement="top-end" c-match_width="False" /></article>
      </section>
    """
    css = ":where(.date-picker-placement){display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:3rem;min-block-size:28rem;align-items:center}:where(.date-picker-placement article){display:grid;gap:.5rem}:where(.date-picker-placement h3){margin:0}"


preview = DatePickerPlacement()
preview  # noqa: B018
````


Escape and passive outside or focus-outside interaction close a dismissible
picker. It does not trap focus, lock the page, or make background content inert.

## Customize documented anatomy

Variants, sizes, public `--cui-date-picker-*` variables, and stable
`data-citry-ui-part` selectors style the field. The nested Calendar and Popover
keep their own public variables.


### Customize DatePicker

[Open the rendered preview](/v/0.4.6/ui-library/components/date-picker/_previews/styling/)

````citry
# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class StyledDatePicker(Component):
    template = """
      <c-CDatePicker class_="brand-date-picker" value="2026-08-19" c-unavailable_dates="('2026-08-20',)" />
    """
    css = """
      :where(.brand-date-picker){--cui-date-picker-background:#f0fdfa;--cui-date-picker-foreground:#134e4a;--cui-date-picker-border-color:#0f766e;--cui-date-picker-focus-color:#0d9488;--cui-date-picker-radius:1rem;--cui-calendar-selected-background:#0f766e;--cui-calendar-selected-foreground:white;max-inline-size:24rem}
      @media (prefers-color-scheme:dark){:where(.brand-date-picker){--cui-date-picker-background:#132f2d;--cui-date-picker-foreground:#ccfbf1;--cui-date-picker-border-color:#5eead4}}
    """


preview = StyledDatePicker()
preview  # noqa: B018
````


The Calendar grid follows its complete roving-focus keyboard contract. Manual
screen-reader review remains important for popup grids, especially on mobile.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CDatePicker server inputs

Server inputs are passed in a template through `<c-CDatePicker ... />` or in Python through
`CDatePicker(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 18rem; --ui-api-column-3-width: 16rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="date-picker-input-cdate-picker-server-inputs-value"></span>`value` | `CDatePickerDate | None` ([`CDatePickerDate`](#date-picker-interface-date)) | `None` | Sets the initial and reset canonical date or empty value. |
| <span id="date-picker-input-cdate-picker-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the native transport Form field name. |
| <span id="date-picker-input-cdate-picker-server-inputs-form"></span>`form` | `str | None` | `None` | Associates the native transport with an external Form ID. |
| <span id="date-picker-input-cdate-picker-server-inputs-id"></span>`id` | `str | None` | generated | Sets the public no-JavaScript input or enhanced Button ID and owned ID prefix. |
| <span id="date-picker-input-cdate-picker-server-inputs-min"></span>`min` | `CDatePickerDate | None` ([`CDatePickerDate`](#date-picker-interface-date)) | `None` | Sets the inclusive minimum selectable date. |
| <span id="date-picker-input-cdate-picker-server-inputs-max"></span>`max` | `CDatePickerDate | None` ([`CDatePickerDate`](#date-picker-interface-date)) | `None` | Sets the inclusive maximum selectable date. |
| <span id="date-picker-input-cdate-picker-server-inputs-unavailable-dates"></span>`unavailable_dates` | `Sequence[CDatePickerDate]` | () | Marks at most 4096 unique dates focusable but unavailable. |
| <span id="date-picker-input-cdate-picker-server-inputs-required"></span>`required` | `bool | None` | `None` | Enables native empty-value validity outside Field; Field owns it inside Field. |
| <span id="date-picker-input-cdate-picker-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Blocks opening selection clearing and Form participation outside Field; Form disabledness also wins. |
| <span id="date-picker-input-cdate-picker-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Keeps the picker focusable and submitted but blocks value changes. |
| <span id="date-picker-input-cdate-picker-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Adds application invalid state to revealed native validity. |
| <span id="date-picker-input-cdate-picker-server-inputs-clearable"></span>`clearable` | `bool` | `True` | Shows a clear action for an optional non-empty writable value. |
| <span id="date-picker-input-cdate-picker-server-inputs-dismissible"></span>`dismissible` | `bool` | `True` | Permits Escape outside and focus-outside close requests. |
| <span id="date-picker-input-cdate-picker-server-inputs-placement"></span>`placement` | `CPopoverPlacement` ([`CPopoverPlacement`](#date-picker-interface-popover-placement)) | `"bottom-start"` | Sets the preferred logical Popover placement. |
| <span id="date-picker-input-cdate-picker-server-inputs-match-width"></span>`match_width` | `bool` | `True` | Makes the Popover at least as wide as the visible control. |
| <span id="date-picker-input-cdate-picker-server-inputs-first-day-of-week"></span>`first_day_of_week` | `Literal[1, 2, 3, 4, 5, 6, 7] | None` | `None` | Overrides the locale week start using ISO Monday 1 through Sunday 7. |
| <span id="date-picker-input-cdate-picker-server-inputs-show-adjacent-days"></span>`show_adjacent_days` | `bool` | `True` | Shows selectable neighboring-month dates in the Calendar. |
| <span id="date-picker-input-cdate-picker-server-inputs-fixed-weeks"></span>`fixed_weeks` | `bool` | `True` | Uses six stable Calendar rows instead of the natural month row count. |
| <span id="date-picker-input-cdate-picker-server-inputs-placeholder"></span>`placeholder` | `str` | `"Choose a date"` | Supplies visible empty-state text when explicitly overridden. |
| <span id="date-picker-input-cdate-picker-server-inputs-picker-label"></span>`picker_label` | `str` | `"Choose date"` | Names the popup dialog and empty trigger when explicitly overridden. |
| <span id="date-picker-input-cdate-picker-server-inputs-change-label"></span>`change_label` | `str` | `"Change date, {date}"` | Formats a selected trigger name and must retain the date placeholder when explicitly overridden. |
| <span id="date-picker-input-cdate-picker-server-inputs-clear-label"></span>`clear_label` | `str` | `"Clear date"` | Names the clear Button when explicitly overridden. |
| <span id="date-picker-input-cdate-picker-server-inputs-unavailable-message"></span>`unavailable_message` | `str` | `"Choose an available date."` | Supplies native custom validity if a selected date becomes unavailable. |
| <span id="date-picker-input-cdate-picker-server-inputs-variant"></span>`variant` | `CDatePickerVariant` ([`CDatePickerVariant`](#date-picker-interface-variant)) | `"outline"` | Selects outline filled or plain field treatment. |
| <span id="date-picker-input-cdate-picker-server-inputs-size"></span>`size` | `CDatePickerSize` ([`CDatePickerSize`](#date-picker-interface-size)) | `"md"` | Selects coordinated control and text sizing. |
| <span id="date-picker-input-cdate-picker-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#date-picker-interface-class-value)) | `None` | Adds classes to the root and merges with attrs. |
| <span id="date-picker-input-cdate-picker-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#date-picker-interface-style-value)) | `None` | Adds styles to the root and merges with attrs. |
| <span id="date-picker-input-cdate-picker-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes without replacing owned state identity or runtime markers. |

</div>

#### CDatePicker client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CDatePicker />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 18rem; --ui-api-column-3-width: 18rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="date-picker-input-cdate-picker-client-inputs-value"></span>`value` | `canonical string | null` | Releases control at the latest committed value. | Controls selected and submitted date while supplied. |
| <span id="date-picker-input-cdate-picker-client-inputs-open"></span>`open` | `boolean | null` | Releases control at the latest committed visibility. | Controls popup visibility while supplied. |
| <span id="date-picker-input-cdate-picker-client-inputs-min"></span>`min` | `canonical string | null` | Uses the server minimum. | Replaces or removes the inclusive minimum. |
| <span id="date-picker-input-cdate-picker-client-inputs-max"></span>`max` | `canonical string | null` | Uses the server maximum. | Replaces or removes the inclusive maximum. |
| <span id="date-picker-input-cdate-picker-client-inputs-unavailable-dates"></span>`unavailableDates` | `canonical string array` | Uses the server sequence. | Replaces the bounded unavailable-date set. |
| <span id="date-picker-input-cdate-picker-client-inputs-required"></span>`required` | `boolean` | Uses server or Field state. | Controls standalone required validity. |
| <span id="date-picker-input-cdate-picker-client-inputs-disabled"></span>`disabled` | `boolean` | Uses server or owner state. | Controls interaction and Form participation. |
| <span id="date-picker-input-cdate-picker-client-inputs-readonly"></span>`readonly` | `boolean` | Uses server or owner state. | Controls focusable nonmutable state. |
| <span id="date-picker-input-cdate-picker-client-inputs-invalid"></span>`invalid` | `boolean` | Uses server or Field state. | Controls application invalid state. |
| <span id="date-picker-input-cdate-picker-client-inputs-clearable"></span>`clearable` | `boolean` | Uses the server input. | Controls the optional clear action. |
| <span id="date-picker-input-cdate-picker-client-inputs-dismissible"></span>`dismissible` | `boolean` | Uses the server input. | Controls passive popup dismissal. |
| <span id="date-picker-input-cdate-picker-client-inputs-placement"></span>`placement` | `CPopoverPlacement` ([`CPopoverPlacement`](#date-picker-interface-popover-placement)) | Uses the server input. | Controls preferred logical placement. |
| <span id="date-picker-input-cdate-picker-client-inputs-match-width"></span>`matchWidth` | `boolean` | Uses the server input. | Controls trigger-width matching. |
| <span id="date-picker-input-cdate-picker-client-inputs-first-day-of-week"></span>`firstDayOfWeek` | `1 | 2 | 3 | 4 | 5 | 6 | 7 | null` | Uses the server input. | Replaces or restores locale week start. |
| <span id="date-picker-input-cdate-picker-client-inputs-show-adjacent-days"></span>`showAdjacentDays` | `boolean` | Uses the server input. | Controls neighboring-month cell visibility. |
| <span id="date-picker-input-cdate-picker-client-inputs-fixed-weeks"></span>`fixedWeeks` | `boolean` | Uses the server input. | Controls six-row versus natural Calendar layout. |
| <span id="date-picker-input-cdate-picker-client-inputs-variant"></span>`variant` | `CDatePickerVariant` ([`CDatePickerVariant`](#date-picker-interface-variant)) | Uses the server input. | Controls field presentation. |
| <span id="date-picker-input-cdate-picker-client-inputs-size"></span>`size` | `CDatePickerSize` ([`CDatePickerSize`](#date-picker-interface-size)) | Uses the server input. | Controls coordinated sizing. |
| <span id="date-picker-input-cdate-picker-client-inputs-on-value-change"></span>`onValueChange` | `function` | No semantic value callback. | Receives Calendar clear native and reset value requests. |
| <span id="date-picker-input-cdate-picker-client-inputs-on-open-change"></span>`onOpenChange` | `function` | No semantic visibility callback. | Receives trigger selection dismissal reset and forced-close requests. |

</div>

### Slots

-

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CDatePicker events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="date-picker-event-cdate-picker-events-on-value-change"></span>`onValueChange` | `(value: string | null, detail: CDatePickerValueChangeDetail) => void` ([`CDatePickerValueChangeDetail`](#date-picker-interface-cdate-picker-value-change-detail)) | Calendar selection clear reset or native fallback editing requests another value. | `{value, previousValue, controlled, source, sourceEvent}` ([`CDatePickerValueChangeDetail`](#date-picker-interface-cdate-picker-value-change-detail)) | Uncontrolled user commits emit native input/change; controlled requests wait for the owner. |
| <span id="date-picker-event-cdate-picker-events-on-open-change"></span>`onOpenChange` | `(open: boolean, detail: CDatePickerOpenChangeDetail) => void` ([`CDatePickerOpenChangeDetail`](#date-picker-interface-cdate-picker-open-change-detail)) | Trigger selection clear reset Escape outside focus-outside native or forced layer changes request visibility. | `{reason, controlled, forced, source}` ([`CDatePickerOpenChangeDetail`](#date-picker-interface-cdate-picker-open-change-detail)) | Uncontrolled requests commit before notification; controlled requests wait except forced safety closure. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CDatePicker CSS variables

Apply these variables to `CDatePicker` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="date-picker-css-cdate-picker-css-variables-background"></span>`--cui-date-picker-background` | `color` | Visible control and clear background. | `Canvas or variant-derived.` |
| <span id="date-picker-css-cdate-picker-css-variables-foreground"></span>`--cui-date-picker-foreground` | `color` | Text and icon color. | `CanvasText` |
| <span id="date-picker-css-cdate-picker-css-variables-border-color"></span>`--cui-date-picker-border-color` | `color` | Visible control and clear boundary. | `Mixed CanvasText.` |
| <span id="date-picker-css-cdate-picker-css-variables-invalid-border-color"></span>`--cui-date-picker-invalid-border-color` | `color` | Revealed invalid control boundary. | `Theme error.` |
| <span id="date-picker-css-cdate-picker-css-variables-focus-color"></span>`--cui-date-picker-focus-color` | `color` | Control and clear focus outline. | `Highlight` |
| <span id="date-picker-css-cdate-picker-css-variables-radius"></span>`--cui-date-picker-radius` | `length` | Visible control and clear corner radius. | `0.625rem` |
| <span id="date-picker-css-cdate-picker-css-variables-min-block-size"></span>`--cui-date-picker-min-block-size` | `length` | Minimum interactive control height. | `2.5rem` |
| <span id="date-picker-css-cdate-picker-css-variables-padding-inline"></span>`--cui-date-picker-padding-inline` | `length` | Visible control inline inset. | `0.75rem` |
| <span id="date-picker-css-cdate-picker-css-variables-gap"></span>`--cui-date-picker-gap` | `length` | Visible value and icon gap. | `0.5rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CDatePicker attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="date-picker-attribute-cdate-picker-root-attributes-data-empty"></span>`data-empty` | Root | `present | absent` | Marks no committed canonical value. |
| <span id="date-picker-attribute-cdate-picker-root-attributes-data-open"></span>`data-open` | Root | `present | absent` | Mirrors effective popup visibility. |
| <span id="date-picker-attribute-cdate-picker-root-attributes-data-required"></span>`data-required` | Root | `present | absent` | Mirrors effective requiredness. |
| <span id="date-picker-attribute-cdate-picker-root-attributes-data-disabled"></span>`data-disabled` | Root | `present | absent` | Mirrors effective disabledness. |
| <span id="date-picker-attribute-cdate-picker-root-attributes-data-readonly"></span>`data-readonly` | Root | `present | absent` | Mirrors effective readonly state. |
| <span id="date-picker-attribute-cdate-picker-root-attributes-data-invalid"></span>`data-invalid` | Root | `present | absent` | Mirrors application unavailable or revealed native invalidity. |
| <span id="date-picker-attribute-cdate-picker-root-attributes-data-variant"></span>`data-variant` | Root | `CDatePickerVariant` ([`CDatePickerVariant`](#date-picker-interface-variant)) | Mirrors visual treatment. |
| <span id="date-picker-attribute-cdate-picker-root-attributes-data-size"></span>`data-size` | Root | `CDatePickerSize` ([`CDatePickerSize`](#date-picker-interface-size)) | Mirrors coordinated sizing. |
| <span id="date-picker-attribute-cdate-picker-root-attributes-data-enhanced"></span>`data-enhanced` | Root | `present | absent` | Marks completed custom control activation. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CDatePicker selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="date-picker-selector-cdate-picker-selectors-date-picker"></span>`[data-citry-ui-part="date-picker"]` | Root div | State reflections root attrs and styling destination. |
| <span id="date-picker-selector-cdate-picker-selectors-fallback-input"></span>`[data-citry-ui-part="fallback-input"]` | Native Date input | No-JavaScript control and enhanced Form reset validity transport. |
| <span id="date-picker-selector-cdate-picker-selectors-enhanced-control"></span>`[data-citry-ui-part="enhanced-control"]` | Layout div | Groups the Popover activator and optional clear action. |
| <span id="date-picker-selector-cdate-picker-selectors-control"></span>`[data-citry-ui-part="control"]` | Native Button | Full-width popup activator and enhanced public focus target. |
| <span id="date-picker-selector-cdate-picker-selectors-value"></span>`[data-citry-ui-part="value"]` | Span | Displays localized selected date or placeholder. |
| <span id="date-picker-selector-cdate-picker-selectors-icon"></span>`[data-citry-ui-part="icon"]` | Hidden decorative SVG | Identifies the calendar affordance. |
| <span id="date-picker-selector-cdate-picker-selectors-clear"></span>`[data-citry-ui-part="clear"]` | Native Button | Requests an empty optional value. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="date-picker-interface-date"></span>`CDatePickerDate` | `date | str` |
| <span id="date-picker-interface-variant"></span>`CDatePickerVariant` | `Literal["outline", "filled", "plain"]` |
| <span id="date-picker-interface-size"></span>`CDatePickerSize` | `Literal["sm", "md", "lg"]` |
| <span id="date-picker-interface-value-source"></span>`CDatePickerValueChangeSource` | `Literal["calendar", "clear", "reset", "native"]` |
| <span id="date-picker-interface-popover-placement"></span>`CPopoverPlacement` | `Literal["top-start", "top", "top-end", "bottom-start", "bottom", "bottom-end"]` |
| <span id="date-picker-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="date-picker-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="date-picker-interface-cdate-picker-value-change-detail"></span>

#### `CDatePickerValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="date-picker-interface-cdate-picker-value-change-detail-value"></span>`value` | `string | null` | - | Requested selected canonical date or empty state. |
| <span id="date-picker-interface-cdate-picker-value-change-detail-previous-value"></span>`previousValue` | `string | null` | - | Effective date before the request. |
| <span id="date-picker-interface-cdate-picker-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client value owns the commit. |
| <span id="date-picker-interface-cdate-picker-value-change-detail-source"></span>`source` | `CDatePickerValueChangeSource` ([`CDatePickerValueChangeSource`](#date-picker-interface-value-source)) | - | Calendar clear reset or native cause. |
| <span id="date-picker-interface-cdate-picker-value-change-detail-source-event"></span>`sourceEvent` | `object | null` | - | Native interaction event when one exists. |

</div>

<span id="date-picker-interface-cdate-picker-open-change-detail"></span>

#### `CDatePickerOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="date-picker-interface-cdate-picker-open-change-detail-reason"></span>`reason` | `trigger | selection | clear | reset | escape | outside | focus-outside | native | ancestor | modal` | - | Exact request or forced-close cause. |
| <span id="date-picker-interface-cdate-picker-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client open owns ordinary visibility commits. |
| <span id="date-picker-interface-cdate-picker-open-change-detail-forced"></span>`forced` | `boolean` | - | Whether ancestor or modal safety required closure. |
| <span id="date-picker-interface-cdate-picker-open-change-detail-source"></span>`source` | `object | null` | - | Associated browser source when one exists. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CDatePicker translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="date-picker-translation-cdate-picker-translations-placeholder"></span>`citry-ui-date-picker-placeholder` | Displays the empty control value. | `none` | `placeholder` | Parent i18n subscription calls `tr()` because the same destination later displays formatted dates. |
| <span id="date-picker-translation-cdate-picker-translations-label"></span>`citry-ui-date-picker-label` | Names the popup and empty trigger. | `none` | `picker_label` | `$c-tr` updates the stable title; parent subscription updates the dynamic trigger name. |
| <span id="date-picker-translation-cdate-picker-translations-change"></span>`citry-ui-date-picker-change` | Names a selected trigger. | `` `date: str` localized by `citry-ui-date-picker-display` `` | `change_label` containing `{date}` | Parent i18n subscription recomputes the formatted value and calls `tr()`. |
| <span id="date-picker-translation-cdate-picker-translations-clear"></span>`citry-ui-date-picker-clear` | Names the optional clear Button. | `none` | `clear_label` | `$c-tr` updates the stable aria-label destination. |
| <span id="date-picker-translation-cdate-picker-translations-unavailable"></span>`citry-ui-date-picker-unavailable` | Supplies native custom validity when a selected date becomes unavailable. | `none` | `unavailable_message` | `i18n.bind()` updates the browser-owned validity message. |

</div>