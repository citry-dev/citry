---
title: DateRange
url: https://citry.dev/v/0.4.4/ui-library/components/date-range/
description: "Choose two ordered canonical dates as one localized range."
---
# DateRange

Use `CDateRange` when users choose a start and end date together. It renders
two usable native Date inputs first, then enhances them into one localized
Popover and Calendar when JavaScript activates.

## Choose one range

Use a fieldset and legend because DateRange submits two controls. It rejects
composition inside `CField` rather than giving two Form fields one field-owned
identity.


```citry-html
<fieldset>
  <legend>Travel dates</legend>
  <c-CDateRange start_name="arrival" end_name="departure" />
</fieldset>
```



### Choose one date range

[Open the rendered preview](/v/0.4.4/ui-library/components/date-range/_previews/basic/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicDateRange(Component):
    template = """
      <fieldset>
        <legend>Travel dates</legend>
        <c-CDateRange start_name="arrival" end_name="departure" start="2026-08-19" end="2026-08-23" />
      </fieldset>
    """


preview = BasicDateRange()
preview  # noqa: B018
````


The first Calendar selection starts a draft and the second commits an ordered
range. Selecting the same date twice commits a one-day range. Hover and focus
preview a draft without changing submitted values.

## Submit and reset both endpoints

`start_name` and `end_name` create separate canonical `YYYY-MM-DD` FormData
entries. Both endpoints are empty or both are committed. Native `input` and
`change` events fire only after an uncontrolled range commit.


### Submit and reset a date range

[Open the rendered preview](/v/0.4.4/ui-library/components/date-range/_previews/form/)

````citry
# ruff: noqa: E501 - embedded example markup stays readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DateRangeForm(Component):
    template = """
      <form x-data="{result:'Submit the form to inspect its canonical values.'}" @submit.prevent="result=JSON.stringify(Object.fromEntries(new FormData($event.target)))">
        <fieldset><legend>Conference stay</legend><c-CDateRange start_name="check_in" end_name="check_out" start="2026-09-14" end="2026-09-18" required /></fieldset>
        <div><button type="submit">Submit dates</button> <button type="reset">Reset dates</button></div>
        <output x-text="result">Submit the form to inspect its canonical values.</output>
      </form>
    """
    css = ":where(form,fieldset){display:grid;gap:.75rem;max-inline-size:32rem}"


preview = DateRangeForm()
preview  # noqa: B018
````


Without JavaScript the two labeled native Date inputs remain fully usable.
Reset restores both initial endpoints and closes the enhanced surface.

## Bound the whole interval

`min` and `max` are inclusive. `unavailable_dates` accepts at most 4096 unique
dates, and a committed range may not cross any unavailable date. Recheck the
same business rules on the server when processing a submission.


### Constrain a date range

[Open the rendered preview](/v/0.4.4/ui-library/components/date-range/_previews/constraints/)

````citry
# ruff: noqa: E501 - embedded example markup stays readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ConstrainedDateRange(Component):
    template = """
      <fieldset>
        <legend>Available booking window</legend>
        <p id="range-help">August 20 and 24 are unavailable; a range cannot cross either date.</p>
        <c-CDateRange min="2026-08-10" max="2026-09-15" c-unavailable_dates="('2026-08-20','2026-08-24')" c-attrs="{'aria-describedby':'range-help'}" />
      </fieldset>
    """


preview = ConstrainedDateRange()
preview  # noqa: B018
````


## Control value and popup visibility

Client `value` is either `{start, end}` or `null`. `value` and `open` are
independent controlled channels; while supplied, requests call
`onValueChange` or `onOpenChange` and wait for the owner to return accepted
state through `$c-props`.


### Control DateRange

[Open the rendered preview](/v/0.4.4/ui-library/components/date-range/_previews/controlled/)

````citry
# ruff: noqa: E501 - embedded example markup stays readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledDateRange(Component):
    template = """
      <section x-data="{value:{start:'2026-08-19',end:'2026-08-23'},open:false,last:'No request yet'}">
        <p>Range: <strong x-text="value ? `${value.start} through ${value.end}` : 'empty'"></strong>; popup: <strong x-text="open ? 'open' : 'closed'"></strong></p>
        <c-CDateRange start="2026-08-19" end="2026-08-23" $c-props="{value,open,onValueChange:(next,detail)=>{last=`${detail.source}: ${JSON.stringify(next)}`;value=next},onOpenChange:(next,detail)=>{last=`${detail.reason}: ${next}`;open=next}}" />
        <div><button type="button" @click="value={start:'2026-08-25',end:'2026-08-29'}">Set August 25 through 29</button> <button type="button" @click="open=!open">Toggle popup</button></div>
        <output x-text="last">No request yet</output>
      </section>
    """
    css = ":where(section){display:grid;gap:.75rem;max-inline-size:32rem}:where(section p){margin:0}"


preview = ControlledDateRange()
preview  # noqa: B018
````


Omitting a client prop releases only that channel at its latest committed
state.

## Follow the active locale

The visible range, Calendar labels, endpoint descriptions, trigger name, and
validation text follow the active i18n provider. The canonical Form values do
not change when the locale changes.


### Localize DateRange

[Open the rendered preview](/v/0.4.4/ui-library/components/date-range/_previews/locales/)

````citry
# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DateRangeLocales(Component):
    template = """
      <section class="date-range-locales">
        <article><h3>Provider locale week</h3><c-CDateRange start="2026-08-19" end="2026-08-23" /></article>
        <article><h3>Explicit Monday start</h3><c-CDateRange start="2026-08-19" end="2026-08-23" c-first_day_of_week="1" /></article>
        <article lang="ar" dir="rtl"><h3>RTL scope</h3><c-CDateRange start="2026-08-19" end="2026-08-23" /></article>
      </section>
    """
    css = ":where(.date-range-locales){display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:1rem}:where(.date-range-locales article){display:grid;align-content:start;gap:.5rem;padding:.75rem}:where(.date-range-locales h3){margin:0}"


preview = DateRangeLocales()
preview  # noqa: B018
````


`first_day_of_week` overrides only the week start. Generic browser parsing of
localized date text is not part of this family; its transport always uses
native canonical Date controls.

## Compare states and presentation

Readonly keeps the range submitted and lets users inspect the Calendar but
blocks commits. Disabled blocks interaction and Form participation. Required
ranges cannot be cleared.


### Compare DateRange states

[Open the rendered preview](/v/0.4.4/ui-library/components/date-range/_previews/states/)

````citry
# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DateRangeStates(Component):
    template = """
      <section class="date-range-states">
        <fieldset><legend>Optional</legend><c-CDateRange start="2026-08-19" end="2026-08-23" clearable /></fieldset>
        <fieldset><legend>Readonly</legend><c-CDateRange start="2026-08-19" end="2026-08-23" readonly variant="filled" size="sm" /></fieldset>
        <fieldset><legend>Disabled</legend><c-CDateRange start="2026-08-19" end="2026-08-23" disabled /></fieldset>
        <fieldset><legend>Invalid</legend><c-CDateRange start="2026-08-19" end="2026-08-23" invalid variant="plain" size="lg" /></fieldset>
      </section>
    """
    css = ":where(.date-range-states){display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem}:where(.date-range-states fieldset){min-inline-size:0}"


preview = DateRangeStates()
preview  # noqa: B018
````


Use `variant`, `size`, the documented `--cui-date-range-*` variables, and
stable `data-citry-ui-part` selectors for styling. Nested Calendar and Popover
variables keep their own public contracts.

The Calendar uses its complete grid keyboard model. Manual screen-reader
review remains important for range grids, especially on mobile.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CDateRange server inputs

Server inputs are passed in a template through `<c-CDateRange ... />` or in Python through
`CDateRange(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 18rem; --ui-api-column-3-width: 17rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="date-range-input-cdate-range-server-inputs-start"></span>`start` | `CDateRangeDate | None` ([`CDateRangeDate`](#date-range-interface-date)) | `None` | Sets the initial and reset canonical start date or empty range. |
| <span id="date-range-input-cdate-range-server-inputs-end"></span>`end` | `CDateRangeDate | None` ([`CDateRangeDate`](#date-range-interface-date)) | `None` | Sets the initial and reset canonical end date or empty range. |
| <span id="date-range-input-cdate-range-server-inputs-start-name"></span>`start_name` | `str | None` | `None` | Sets the start native transport Form field name. |
| <span id="date-range-input-cdate-range-server-inputs-end-name"></span>`end_name` | `str | None` | `None` | Sets the end native transport Form field name and must differ from start_name. |
| <span id="date-range-input-cdate-range-server-inputs-form"></span>`form` | `str | None` | `None` | Associates both native transports with an external Form ID. |
| <span id="date-range-input-cdate-range-server-inputs-id"></span>`id` | `str | None` | generated | Sets the enhanced Button ID and owned ID prefix. |
| <span id="date-range-input-cdate-range-server-inputs-min"></span>`min` | `CDateRangeDate | None` ([`CDateRangeDate`](#date-range-interface-date)) | `None` | Sets the inclusive minimum endpoint. |
| <span id="date-range-input-cdate-range-server-inputs-max"></span>`max` | `CDateRangeDate | None` ([`CDateRangeDate`](#date-range-interface-date)) | `None` | Sets the inclusive maximum endpoint. |
| <span id="date-range-input-cdate-range-server-inputs-unavailable-dates"></span>`unavailable_dates` | `Sequence[CDateRangeDate]` | () | Rejects any range crossing one of at most 4096 unique dates. |
| <span id="date-range-input-cdate-range-server-inputs-required"></span>`required` | `bool | None` | `None` | Requires both endpoint transports. |
| <span id="date-range-input-cdate-range-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Blocks opening selection clearing and Form participation; Form disabledness also wins. |
| <span id="date-range-input-cdate-range-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Keeps the range focusable and submitted but blocks commits. |
| <span id="date-range-input-cdate-range-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Adds application invalid state to revealed native validity. |
| <span id="date-range-input-cdate-range-server-inputs-clearable"></span>`clearable` | `bool` | `True` | Shows a clear action for an optional non-empty writable range. |
| <span id="date-range-input-cdate-range-server-inputs-dismissible"></span>`dismissible` | `bool` | `True` | Permits Escape outside and focus-outside close requests. |
| <span id="date-range-input-cdate-range-server-inputs-placement"></span>`placement` | `CPopoverPlacement` ([`CPopoverPlacement`](#date-range-interface-popover-placement)) | `"bottom-start"` | Sets the preferred logical Popover placement. |
| <span id="date-range-input-cdate-range-server-inputs-match-width"></span>`match_width` | `bool` | `True` | Makes the Popover at least as wide as the visible control. |
| <span id="date-range-input-cdate-range-server-inputs-first-day-of-week"></span>`first_day_of_week` | `Literal[1, 2, 3, 4, 5, 6, 7] | None` | `None` | Overrides locale week start using ISO Monday 1 through Sunday 7. |
| <span id="date-range-input-cdate-range-server-inputs-show-adjacent-days"></span>`show_adjacent_days` | `bool` | `True` | Shows selectable neighboring-month dates in the Calendar. |
| <span id="date-range-input-cdate-range-server-inputs-fixed-weeks"></span>`fixed_weeks` | `bool` | `True` | Uses six stable Calendar rows instead of the natural month row count. |
| <span id="date-range-input-cdate-range-server-inputs-placeholder"></span>`placeholder` | `str` | `"Choose dates"` | Supplies visible empty-state text when explicitly overridden. |
| <span id="date-range-input-cdate-range-server-inputs-range-label"></span>`range_label` | `str` | `"Choose date range"` | Names the group popup and empty trigger when explicitly overridden. |
| <span id="date-range-input-cdate-range-server-inputs-change-label"></span>`change_label` | `str` | `"Change date range, {start} to {end}"` | Formats a committed trigger name and must retain both placeholders when explicitly overridden. |
| <span id="date-range-input-cdate-range-server-inputs-start-label"></span>`start_label` | `str` | `"Start date"` | Names the native start input and Calendar start endpoint when explicitly overridden. |
| <span id="date-range-input-cdate-range-server-inputs-end-label"></span>`end_label` | `str` | `"End date"` | Names the native end input and Calendar end endpoint when explicitly overridden. |
| <span id="date-range-input-cdate-range-server-inputs-clear-label"></span>`clear_label` | `str` | `"Clear date range"` | Names the clear Button when explicitly overridden. |
| <span id="date-range-input-cdate-range-server-inputs-unavailable-message"></span>`unavailable_message` | `str` | `"Choose an available date range."` | Supplies native custom validity if a committed interval becomes unavailable. |
| <span id="date-range-input-cdate-range-server-inputs-variant"></span>`variant` | `CDateRangeVariant` ([`CDateRangeVariant`](#date-range-interface-variant)) | `"outline"` | Selects outline filled or plain field treatment. |
| <span id="date-range-input-cdate-range-server-inputs-size"></span>`size` | `CDateRangeSize` ([`CDateRangeSize`](#date-range-interface-size)) | `"md"` | Selects coordinated control and text sizing. |
| <span id="date-range-input-cdate-range-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#date-range-interface-class-value)) | `None` | Adds classes to the root and merges with attrs. |
| <span id="date-range-input-cdate-range-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#date-range-interface-style-value)) | `None` | Adds styles to the root and merges with attrs. |
| <span id="date-range-input-cdate-range-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes without replacing owned state identity or runtime markers. |

</div>

#### CDateRange client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CDateRange />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 18rem; --ui-api-column-3-width: 18rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="date-range-input-cdate-range-client-inputs-value"></span>`value` | `CDateRangeValue | null` ([`CDateRangeValue`](#date-range-interface-cdate-range-value)) | Releases control at the latest committed range. | Controls both ordered selected and submitted endpoints while supplied. |
| <span id="date-range-input-cdate-range-client-inputs-open"></span>`open` | `boolean | null` | Releases control at the latest committed visibility. | Controls popup visibility while supplied. |
| <span id="date-range-input-cdate-range-client-inputs-required"></span>`required` | `boolean` | Uses server state. | Controls two-endpoint native required validity. |
| <span id="date-range-input-cdate-range-client-inputs-disabled"></span>`disabled` | `boolean` | Uses server or Form state. | Controls interaction and Form participation. |
| <span id="date-range-input-cdate-range-client-inputs-readonly"></span>`readonly` | `boolean` | Uses server or Form state. | Controls focusable nonmutable state. |
| <span id="date-range-input-cdate-range-client-inputs-invalid"></span>`invalid` | `boolean` | Uses server state. | Controls application invalid state. |
| <span id="date-range-input-cdate-range-client-inputs-clearable"></span>`clearable` | `boolean` | Uses the server input. | Controls the optional clear action. |
| <span id="date-range-input-cdate-range-client-inputs-dismissible"></span>`dismissible` | `boolean` | Uses the server input. | Controls passive popup dismissal. |
| <span id="date-range-input-cdate-range-client-inputs-placement"></span>`placement` | `CPopoverPlacement` ([`CPopoverPlacement`](#date-range-interface-popover-placement)) | Uses the server input. | Controls preferred logical placement. |
| <span id="date-range-input-cdate-range-client-inputs-match-width"></span>`matchWidth` | `boolean` | Uses the server input. | Controls trigger-width matching. |
| <span id="date-range-input-cdate-range-client-inputs-variant"></span>`variant` | `CDateRangeVariant` ([`CDateRangeVariant`](#date-range-interface-variant)) | Uses the server input. | Controls field presentation. |
| <span id="date-range-input-cdate-range-client-inputs-size"></span>`size` | `CDateRangeSize` ([`CDateRangeSize`](#date-range-interface-size)) | Uses the server input. | Controls coordinated sizing. |
| <span id="date-range-input-cdate-range-client-inputs-on-value-change"></span>`onValueChange` | `function` | No semantic range callback. | Receives Calendar clear native and reset range requests. |
| <span id="date-range-input-cdate-range-client-inputs-on-open-change"></span>`onOpenChange` | `function` | No semantic visibility callback. | Receives trigger selection dismissal reset and forced-close requests. |

</div>

### Slots

-

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CDateRange events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="date-range-event-cdate-range-events-on-value-change"></span>`onValueChange` | `(value: CDateRangeValue | null, detail: CDateRangeValueChangeDetail) => void` ([`CDateRangeValue`](#date-range-interface-cdate-range-value), [`CDateRangeValueChangeDetail`](#date-range-interface-cdate-range-value-change-detail)) | A completed Calendar pair clear reset or valid native pair requests another range. | `{value, previousValue, controlled, source, sourceEvent}` ([`CDateRangeValueChangeDetail`](#date-range-interface-cdate-range-value-change-detail)) | Uncontrolled commits emit native input/change for endpoints that changed; controlled requests wait for the owner. |
| <span id="date-range-event-cdate-range-events-on-open-change"></span>`onOpenChange` | `(open: boolean, detail: CDateRangeOpenChangeDetail) => void` ([`CDateRangeOpenChangeDetail`](#date-range-interface-cdate-range-open-change-detail)) | Trigger selection clear reset Escape outside focus-outside native or forced layer changes request visibility. | `{reason, controlled, forced, source}` ([`CDateRangeOpenChangeDetail`](#date-range-interface-cdate-range-open-change-detail)) | Uncontrolled requests commit before notification; controlled requests wait except forced safety closure. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CDateRange CSS variables

Apply these variables to `CDateRange` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="date-range-css-cdate-range-css-variables-background"></span>`--cui-date-range-background` | `color` | Visible control clear and fallback input background. | `Canvas or variant-derived.` |
| <span id="date-range-css-cdate-range-css-variables-foreground"></span>`--cui-date-range-foreground` | `color` | Text and icon color. | `CanvasText` |
| <span id="date-range-css-cdate-range-css-variables-border-color"></span>`--cui-date-range-border-color` | `color` | Control clear and native endpoint boundaries. | `Mixed CanvasText.` |
| <span id="date-range-css-cdate-range-css-variables-invalid-border-color"></span>`--cui-date-range-invalid-border-color` | `color` | Revealed invalid control boundary. | `Theme error.` |
| <span id="date-range-css-cdate-range-css-variables-focus-color"></span>`--cui-date-range-focus-color` | `color` | Focus outlines and draft-range indication. | `Highlight` |
| <span id="date-range-css-cdate-range-css-variables-range-background"></span>`--cui-date-range-range-background` | `color` | Committed and preview interval background. | `Highlight mixed with Canvas.` |
| <span id="date-range-css-cdate-range-css-variables-endpoint-background"></span>`--cui-date-range-endpoint-background` | `color` | Start and end date background. | `Theme primary.` |
| <span id="date-range-css-cdate-range-css-variables-endpoint-foreground"></span>`--cui-date-range-endpoint-foreground` | `color` | Start and end date foreground. | `white` |
| <span id="date-range-css-cdate-range-css-variables-radius"></span>`--cui-date-range-radius` | `length` | Control clear and native input corner radius. | `0.625rem` |
| <span id="date-range-css-cdate-range-css-variables-min-block-size"></span>`--cui-date-range-min-block-size` | `length` | Minimum interactive control height. | `2.5rem` |
| <span id="date-range-css-cdate-range-css-variables-padding-inline"></span>`--cui-date-range-padding-inline` | `length` | Visible control and native endpoint inline inset. | `0.75rem` |
| <span id="date-range-css-cdate-range-css-variables-gap"></span>`--cui-date-range-gap` | `length` | Endpoint field and control content gap. | `0.5rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CDateRange attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="date-range-attribute-cdate-range-root-attributes-data-empty"></span>`data-empty` | Root | `present | absent` | Marks no committed pair. |
| <span id="date-range-attribute-cdate-range-root-attributes-data-open"></span>`data-open` | Root | `present | absent` | Mirrors effective popup visibility. |
| <span id="date-range-attribute-cdate-range-root-attributes-data-required"></span>`data-required` | Root | `present | absent` | Mirrors effective requiredness. |
| <span id="date-range-attribute-cdate-range-root-attributes-data-disabled"></span>`data-disabled` | Root | `present | absent` | Mirrors effective disabledness. |
| <span id="date-range-attribute-cdate-range-root-attributes-data-readonly"></span>`data-readonly` | Root | `present | absent` | Mirrors effective readonly state. |
| <span id="date-range-attribute-cdate-range-root-attributes-data-invalid"></span>`data-invalid` | Root | `present | absent` | Mirrors application unavailable or revealed native invalidity. |
| <span id="date-range-attribute-cdate-range-root-attributes-data-variant"></span>`data-variant` | Root | `CDateRangeVariant` ([`CDateRangeVariant`](#date-range-interface-variant)) | Mirrors visual treatment. |
| <span id="date-range-attribute-cdate-range-root-attributes-data-size"></span>`data-size` | Root | `CDateRangeSize` ([`CDateRangeSize`](#date-range-interface-size)) | Mirrors coordinated sizing. |
| <span id="date-range-attribute-cdate-range-root-attributes-data-enhanced"></span>`data-enhanced` | Root | `present | absent` | Marks completed custom control activation. |
| <span id="date-range-attribute-cdate-range-root-attributes-data-in-range"></span>`data-in-range` | Calendar day | `present | absent` | Marks selectable days within the committed or preview interval. |
| <span id="date-range-attribute-cdate-range-root-attributes-data-range-start"></span>`data-range-start` | Calendar day | `present | absent` | Marks the displayed interval start. |
| <span id="date-range-attribute-cdate-range-root-attributes-data-range-end"></span>`data-range-end` | Calendar day | `present | absent` | Marks the displayed interval end. |
| <span id="date-range-attribute-cdate-range-root-attributes-data-range-preview"></span>`data-range-preview` | Calendar day | `present | absent` | Marks draft interval days before the second commit. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CDateRange selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="date-range-selector-cdate-range-selectors-date-range"></span>`[data-citry-ui-part="date-range"]` | Root div | State reflections root attrs and styling destination. |
| <span id="date-range-selector-cdate-range-selectors-fallback-group"></span>`[data-citry-ui-part="fallback-group"]` | Div | Contains the two no-JavaScript and Form transport fields. |
| <span id="date-range-selector-cdate-range-selectors-start-input"></span>`[data-citry-ui-part="start-input"]` | Native Date input | Start endpoint transport validity and reset owner. |
| <span id="date-range-selector-cdate-range-selectors-end-input"></span>`[data-citry-ui-part="end-input"]` | Native Date input | End endpoint transport validity and reset owner. |
| <span id="date-range-selector-cdate-range-selectors-enhanced-control"></span>`[data-citry-ui-part="enhanced-control"]` | Layout div | Groups the Popover activator and optional clear action. |
| <span id="date-range-selector-cdate-range-selectors-control"></span>`[data-citry-ui-part="control"]` | Native Button | Full-width popup activator and enhanced public focus target. |
| <span id="date-range-selector-cdate-range-selectors-value"></span>`[data-citry-ui-part="value"]` | Span | Displays the localized committed range or placeholder. |
| <span id="date-range-selector-cdate-range-selectors-calendar"></span>`[data-citry-ui-part="calendar"]` | CCalendar root | Owns draft preview endpoint labels and final range selection. |
| <span id="date-range-selector-cdate-range-selectors-clear"></span>`[data-citry-ui-part="clear"]` | Native Button | Requests an empty optional range. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="date-range-interface-date"></span>`CDateRangeDate` | `date | str` |
| <span id="date-range-interface-variant"></span>`CDateRangeVariant` | `Literal["outline", "filled", "plain"]` |
| <span id="date-range-interface-size"></span>`CDateRangeSize` | `Literal["sm", "md", "lg"]` |
| <span id="date-range-interface-value-source"></span>`CDateRangeValueChangeSource` | `Literal["calendar", "clear", "reset", "native"]` |
| <span id="date-range-interface-popover-placement"></span>`CPopoverPlacement` | `Literal["top-start", "top", "top-end", "bottom-start", "bottom", "bottom-end"]` |
| <span id="date-range-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="date-range-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="date-range-interface-cdate-range-value"></span>

#### `CDateRangeValue`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="date-range-interface-cdate-range-value-start"></span>`start` | `canonical string` | - | Inclusive ordered start endpoint. |
| <span id="date-range-interface-cdate-range-value-end"></span>`end` | `canonical string` | - | Inclusive ordered end endpoint. |

</div>

<span id="date-range-interface-cdate-range-value-change-detail"></span>

#### `CDateRangeValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="date-range-interface-cdate-range-value-change-detail-value"></span>`value` | `CDateRangeValue | null` ([`CDateRangeValue`](#date-range-interface-cdate-range-value)) | - | Requested ordered range or empty state. |
| <span id="date-range-interface-cdate-range-value-change-detail-previous-value"></span>`previousValue` | `CDateRangeValue | null` ([`CDateRangeValue`](#date-range-interface-cdate-range-value)) | - | Effective range before the request. |
| <span id="date-range-interface-cdate-range-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client value owns the commit. |
| <span id="date-range-interface-cdate-range-value-change-detail-source"></span>`source` | `CDateRangeValueChangeSource` ([`CDateRangeValueChangeSource`](#date-range-interface-value-source)) | - | Calendar clear reset or native cause. |
| <span id="date-range-interface-cdate-range-value-change-detail-source-event"></span>`sourceEvent` | `object | null` | - | Native interaction event when one exists. |

</div>

<span id="date-range-interface-cdate-range-open-change-detail"></span>

#### `CDateRangeOpenChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="date-range-interface-cdate-range-open-change-detail-reason"></span>`reason` | `trigger | selection | clear | reset | escape | outside | focus-outside | native | ancestor | modal` | - | Exact request or forced-close cause. |
| <span id="date-range-interface-cdate-range-open-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client open owns ordinary visibility commits. |
| <span id="date-range-interface-cdate-range-open-change-detail-forced"></span>`forced` | `boolean` | - | Whether ancestor or modal safety required closure. |
| <span id="date-range-interface-cdate-range-open-change-detail-source"></span>`source` | `object | null` | - | Associated browser source when one exists. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CDateRange translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="date-range-translation-cdate-range-translations-placeholder"></span>`citry-ui-date-range-placeholder` | Displays the empty enhanced control value. | `none` | `placeholder` | Parent i18n subscription calls `tr()` because the destination later displays formatted dates. |
| <span id="date-range-translation-cdate-range-translations-label"></span>`citry-ui-date-range-label` | Names the group popup Calendar and empty trigger. | `none` | `range_label` or root `attrs` accessible name | `$c-tr` updates stable HTML destinations; parent state forwards it into the composed Calendar and dynamic trigger. |
| <span id="date-range-translation-cdate-range-translations-change"></span>`citry-ui-date-range-change` | Names a trigger with a committed range. | `` `start: str` and `end: str` localized by `citry-ui-date-picker-display` `` | `change_label` containing `{start}` and `{end}` | Parent i18n subscription recomputes both formatted endpoints and calls `tr()`. |
| <span id="date-range-translation-cdate-range-translations-start-label"></span>`citry-ui-date-range-start-label` | Names the native start input and Calendar start endpoint. | `none` | `start_label` | `$c-tr` updates stable native text; parent state forwards it into Calendar endpoint presentation. |
| <span id="date-range-translation-cdate-range-translations-end-label"></span>`citry-ui-date-range-end-label` | Names the native end input and Calendar end endpoint. | `none` | `end_label` | `$c-tr` updates stable native text; parent state forwards it into Calendar endpoint presentation. |
| <span id="date-range-translation-cdate-range-translations-clear"></span>`citry-ui-date-range-clear` | Names the optional clear Button. | `none` | `clear_label` | `$c-tr` updates the stable aria-label destination. |
| <span id="date-range-translation-cdate-range-translations-unavailable"></span>`citry-ui-date-range-unavailable` | Supplies native custom validity when the committed interval becomes unavailable. | `none` | `unavailable_message` | `i18n.bind()` updates the browser-owned validity message. |

</div>