---
title: Calendar
url: https://citry.dev/v/0.4.4/ui-library/components/calendar/
description: "Select one canonical date in an inline locale-aware calendar grid."
---
# Calendar

Use `CCalendar` when the active Citry locale must determine an inline calendar's
month heading, weekday order, day names, and accessible date labels. The public
value remains a canonical `YYYY-MM-DD` date regardless of display locale or
calendar system.

## Select one date

Compose Calendar in `CField` for a visible label, description, error, and shared
state. A standalone Calendar uses its localized `label` by default.


```citry-html
<c-CField required>
  <c-fill name="label">Arrival date</c-fill>
  <c-fill name="default"><c-CCalendar name="arrival" /></c-fill>
</c-CField>
```



### Select one date

[Open the rendered preview](/v/0.4.4/ui-library/components/calendar/_previews/basic/)

````citry
from datetime import date
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCalendar

citry.register_library(citry_ui)

# ruff: noqa: E501 - template and CSS lines stay readable in public source examples


class BasicCalendar(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"python_calendar": CCalendar(value=date(2026, 8, 19), label="Python-composed calendar")}

    template = """
      <section class="calendar-demo-grid">
        <c-CField required>
          <c-fill name="label">Arrival date</c-fill>
          <c-fill name="description">Choose your check-in day.</c-fill>
          <c-fill name="default"><c-CCalendar name="arrival" value="2026-08-19" /></c-fill>
        </c-CField>
        <article><h3>Python composition</h3>{{ python_calendar }}</article>
      </section>
    """
    css = ":where(.calendar-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(20rem,1fr));gap:1.25rem}:where(.calendar-demo-grid article){display:grid;align-content:start;gap:.75rem}:where(.calendar-demo-grid h3){margin:0}"


preview = BasicCalendar()
preview  # noqa: B018
````


The enhanced grid uses one roving tab stop. Arrow keys move by day or week,
Home and End move within the locale week, Page Up/Down move by calendar month,
and Shift+Page Up/Down move by calendar year. Enter or Space selects the
focused date.

## Submit and reset a canonical value

`name` contributes exactly one canonical date through the owned native Date
input. Disabled Calendar is omitted; readonly Calendar remains submitted. An
uncanceled reset restores the server value and visible month.


### Submit and reset Calendar

[Open the rendered preview](/v/0.4.4/ui-library/components/calendar/_previews/form/)

````citry
from citry import Component


class CalendarForm(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section x-data="{submitted:'Submit to inspect FormData'}">
        <form @submit.prevent="submitted=JSON.stringify(Object.fromEntries(new FormData($event.target)))">
          <c-CField control_id="trip-date" required>
            <c-fill name="label">Trip date</c-fill>
            <c-fill name="description">The native Form value remains YYYY-MM-DD.</c-fill>
            <c-fill name="default"><c-CCalendar id="trip-date" name="trip_date" value="2026-08-19" /></c-fill>
            <c-fill name="error">Choose a trip date.</c-fill>
          </c-CField>
          <div><button type="submit">Submit</button> <button type="reset">Reset</button></div>
        </form>
        <output x-text="submitted">Submit to inspect FormData</output>
      </section>
    """
    css = ":where(form,section){display:grid;justify-items:start;gap:.75rem}"


preview = CalendarForm()
preview  # noqa: B018
````


Without JavaScript, that Date input remains visible and usable. After
enhancement it becomes the visually hidden Form, validity, and reset transport;
the browser-generated grid is the interaction surface.

## Bound and block dates

`min` and `max` are inclusive. Dates outside them are disabled and leave the
focus sequence. `unavailable_dates` accepts up to 4096 unique exact dates;
those dates stay focusable so keyboard users can inspect the calendar, but
selection is rejected.


### Constrain available dates

[Open the rendered preview](/v/0.4.4/ui-library/components/calendar/_previews/constraints/)

````citry
from citry import Component


class CalendarConstraints(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CCalendar
        label="Book an appointment"
        visible_date="2026-08-19"
        min="2026-08-10"
        max="2026-09-15"
        c-unavailable_dates="('2026-08-18', '2026-08-20', '2026-08-24')"
      />
    """


preview = CalendarConstraints()
preview  # noqa: B018
````


This bounded exact list is for known application dates such as booked days.
The server must validate submitted availability again.

## Control selection and the visible month

Client `value` and `visibleDate` are independent controlled channels. A
controlled request invokes `onValueChange` or `onVisibleDateChange` without
claiming the selection or page changed; return the accepted canonical value to
commit it. Omitting a prop releases that channel at its latest accepted state.


### Control selection and month

[Open the rendered preview](/v/0.4.4/ui-library/components/calendar/_previews/controlled/)

````citry
from citry import Component

# ruff: noqa: E501 - Alpine expressions stay readable in the public source example


class ControlledCalendar(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section x-data="{selected:'2026-08-19',visible:'2026-08-19',last:'No request yet'}">
        <c-CCalendar
          label="Controlled calendar"
          value="2026-08-19"
          visible_date="2026-08-19"
          $c-props="{value:selected,visibleDate:visible,onValueChange:(value,detail)=>{last=`selection: ${value}`;selected=value},onVisibleDateChange:(value,detail)=>{last=`month: ${value}`;visible=value}}"
        />
        <output x-text="last">No request yet</output>
      </section>
    """
    css = ":where(section){display:grid;justify-items:start;gap:.75rem}"


preview = ControlledCalendar()
preview  # noqa: B018
````


Uncontrolled selection emits bubbling native `input` followed by `change` from
the fallback input. Controlled requests do not emit those transport events.

## Follow the active locale

Under a client-enabled `<c-i18n>` provider, Calendar rebuilds its heading,
weekday order, day numbers, and full accessible date labels immediately when
the locale changes. `first_day_of_week` can override only the week start; leave
it as `None` to follow locale week data.


### Configure locale-sensitive weeks

[Open the rendered preview](/v/0.4.4/ui-library/components/calendar/_previews/locales/)

````citry
from citry import Component

# ruff: noqa: E501 - template and CSS lines stay readable in the public source example


class CalendarLocales(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="calendar-demo-grid">
        <article><h3>Locale week start</h3><c-CCalendar label="Locale week start" visible_date="2026-08-19" /></article>
        <article><h3>Explicit Monday</h3><c-CCalendar label="Monday week start" visible_date="2026-08-19" c-first_day_of_week="1" /></article>
      </section>
    """
    css = ":where(.calendar-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(20rem,1fr));gap:1.25rem}:where(.calendar-demo-grid article){display:grid;align-content:start;gap:.5rem}:where(.calendar-demo-grid h3){margin:0}"


preview = CalendarLocales()
preview  # noqa: B018
````


Calendar navigates locale calendar months while retaining ISO Gregorian domain
dates for callbacks and FormData. The provider time zone determines today's
marker when explicit; otherwise Calendar uses the browser's local date.

## Choose stable or natural rows

`fixed_weeks=True` keeps six rows so surrounding layout does not jump between
months. Set it to `False` for the month's natural row count. Hide neighboring
month dates with `show_adjacent_days=False` when they should not be selectable
from the current page.


### Compare calendar row layouts

[Open the rendered preview](/v/0.4.4/ui-library/components/calendar/_previews/natural-weeks/)

````citry
from citry import Component

# ruff: noqa: E501 - template and CSS lines stay readable in the public source example


class CalendarNaturalWeeks(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="calendar-demo-grid">
        <article><h3>Fixed six rows</h3><c-CCalendar label="Fixed weeks" visible_date="2026-02-01" /></article>
        <article><h3>Natural rows</h3><c-CCalendar label="Natural weeks" visible_date="2026-02-01" c-fixed_weeks="False" c-show_adjacent_days="False" /></article>
      </section>
    """
    css = ":where(.calendar-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(20rem,1fr));align-items:start;gap:1.25rem}:where(.calendar-demo-grid article){display:grid;gap:.5rem}:where(.calendar-demo-grid h3){margin:0}"


preview = CalendarNaturalWeeks()
preview  # noqa: B018
````


## Compare states and sizes

Outline and plain variants combine with sm, md, and lg sizes. Readonly Calendar
allows focus and navigation but blocks selection. Disabled Calendar removes all
day tab stops and disables navigation.


### Compare Calendar states

[Open the rendered preview](/v/0.4.4/ui-library/components/calendar/_previews/states/)

````citry
from citry import Component

# ruff: noqa: E501 - template and CSS lines stay readable in the public source example


class CalendarStates(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="calendar-demo-grid">
        <article><h3>Small plain</h3><c-CCalendar label="Small plain calendar" value="2026-08-19" size="sm" variant="plain" /></article>
        <article><h3>Readonly</h3><c-CCalendar label="Readonly calendar" value="2026-08-19" readonly /></article>
        <article><h3>Disabled</h3><c-CCalendar label="Disabled calendar" value="2026-08-19" disabled /></article>
        <article><h3>Invalid large</h3><c-CCalendar label="Invalid calendar" value="2026-08-19" invalid size="lg" /></article>
      </section>
    """
    css = ":where(.calendar-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(20rem,1fr));align-items:start;gap:1.25rem}:where(.calendar-demo-grid article){display:grid;gap:.5rem}:where(.calendar-demo-grid h3){margin:0}"


preview = CalendarStates()
preview  # noqa: B018
````


## Customize documented anatomy

Public `--cui-calendar-*` variables style the root, navigation, dates, selected
day, today, and unavailable dates. Stable `data-citry-ui-part` selectors expose
the documented anatomy without making generated classes or arrow markup public.


### Customize Calendar

[Open the rendered preview](/v/0.4.4/ui-library/components/calendar/_previews/styling/)

````citry
from citry import Component

# ruff: noqa: E501 - template and CSS lines stay readable in the public source example


class StyledCalendar(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CCalendar class_="brand-calendar" label="Brand calendar" value="2026-08-19" c-unavailable_dates="('2026-08-20',)" />
    """
    css = """
      :where(.brand-calendar){--cui-calendar-background:#fff8eb;--cui-calendar-border-color:#9a6700;--cui-calendar-focus-color:#6f42c1;--cui-calendar-selected-background:#7c3aed;--cui-calendar-selected-foreground:white;--cui-calendar-today-color:#9a3412;--cui-calendar-radius:1rem}
      @media (prefers-color-scheme:dark){:where(.brand-calendar){--cui-calendar-background:#211a10;--cui-calendar-foreground:#fff7e6}}
    """


preview = StyledCalendar()
preview  # noqa: B018
````


Use `CDateInput` when browser-owned editing and picker UI are preferable. Use
`CDatePicker` for a popup field composed from DateInput and Calendar, and
`CDateRange` when the application value is an ordered start/end pair.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CCalendar server inputs

Server inputs are passed in a template through `<c-CCalendar ... />` or in Python through
`CCalendar(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 18rem; --ui-api-column-3-width: 16rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="calendar-input-ccalendar-server-inputs-value"></span>`value` | `CCalendarDate | None` ([`CCalendarDate`](#calendar-interface-date)) | `None` | Sets the initial/reset selected canonical date or empty value. |
| <span id="calendar-input-ccalendar-server-inputs-visible-date"></span>`visible_date` | `CCalendarDate | None` ([`CCalendarDate`](#calendar-interface-date)) | Selected date or today. | Sets the initially visible calendar month; otherwise uses value or today. |
| <span id="calendar-input-ccalendar-server-inputs-name"></span>`name` | `str | None` | `None` | Sets the native fallback input Form field name. |
| <span id="calendar-input-ccalendar-server-inputs-form"></span>`form` | `str | None` | `None` | Associates the native fallback input with an external Form ID. |
| <span id="calendar-input-ccalendar-server-inputs-id"></span>`id` | `str | None` | generated | Sets the public fallback input ID and the prefix for owned IDs. |
| <span id="calendar-input-ccalendar-server-inputs-min"></span>`min` | `CCalendarDate | None` ([`CCalendarDate`](#calendar-interface-date)) | `None` | Sets the inclusive minimum selectable canonical date. |
| <span id="calendar-input-ccalendar-server-inputs-max"></span>`max` | `CCalendarDate | None` ([`CCalendarDate`](#calendar-interface-date)) | `None` | Sets the inclusive maximum selectable canonical date. |
| <span id="calendar-input-ccalendar-server-inputs-unavailable-dates"></span>`unavailable_dates` | `Sequence[CCalendarDate]` | () | Marks at most 4096 unique in-range dates focusable but unavailable. |
| <span id="calendar-input-ccalendar-server-inputs-required"></span>`required` | `bool | None` | `None` | Enables native empty-value validity outside Field; Field owns it inside Field. |
| <span id="calendar-input-ccalendar-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Blocks interaction and Form participation outside Field; Form disabledness also wins. |
| <span id="calendar-input-ccalendar-server-inputs-readonly"></span>`readonly` | `bool | None` | `None` | Keeps a focusable submitted value while blocking selection changes. |
| <span id="calendar-input-ccalendar-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Adds application invalid state to revealed native validity. |
| <span id="calendar-input-ccalendar-server-inputs-first-day-of-week"></span>`first_day_of_week` | `Literal[1, 2, 3, 4, 5, 6, 7] | None` | `None` | Overrides the locale week start using ISO Monday 1 through Sunday 7. |
| <span id="calendar-input-ccalendar-server-inputs-show-adjacent-days"></span>`show_adjacent_days` | `bool` | `True` | Shows selectable dates from neighboring months in leading and trailing cells. |
| <span id="calendar-input-ccalendar-server-inputs-fixed-weeks"></span>`fixed_weeks` | `bool` | `True` | Uses six stable week rows instead of the natural month row count. |
| <span id="calendar-input-ccalendar-server-inputs-label"></span>`label` | `str` | `"Calendar"` | Names a standalone calendar; Field supplies the name when composed. |
| <span id="calendar-input-ccalendar-server-inputs-previous-label"></span>`previous_label` | `str` | `"Previous month"` | Names the previous-month button. |
| <span id="calendar-input-ccalendar-server-inputs-next-label"></span>`next_label` | `str` | `"Next month"` | Names the next-month button. |
| <span id="calendar-input-ccalendar-server-inputs-unavailable-message"></span>`unavailable_message` | `str` | `"Choose an available date."` | Supplies native custom validity when a formerly selected date becomes unavailable. |
| <span id="calendar-input-ccalendar-server-inputs-variant"></span>`variant` | `"outline" | "plain"` ([`CCalendarVariant`](#calendar-interface-variant)) | `"outline"` | Selects bordered or unframed treatment. |
| <span id="calendar-input-ccalendar-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CCalendarSize`](#calendar-interface-size)) | `"md"` | Selects coordinated cell navigation and text sizing. |
| <span id="calendar-input-ccalendar-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#calendar-interface-class-value)) | `None` | Adds classes to the root group and merges with attrs. |
| <span id="calendar-input-ccalendar-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#calendar-interface-style-value)) | `None` | Adds styles to the root group and merges with attrs. |
| <span id="calendar-input-ccalendar-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed root attributes without replacing owned roles state IDs or runtime markers. |

</div>

#### CCalendar client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CCalendar />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 18rem; --ui-api-column-3-width: 18rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="calendar-input-ccalendar-client-inputs-value"></span>`value` | `canonical string | null` | Releases control at the latest accepted value. | Controls the selected date while supplied. |
| <span id="calendar-input-ccalendar-client-inputs-visible-date"></span>`visibleDate` | `canonical string` | Releases visible-month control at its latest accepted month. | Controls the month containing this date while supplied. |
| <span id="calendar-input-ccalendar-client-inputs-min"></span>`min` | `canonical string | null` | Uses the server minimum. | Replaces or removes the inclusive minimum. |
| <span id="calendar-input-ccalendar-client-inputs-max"></span>`max` | `canonical string | null` | Uses the server maximum. | Replaces or removes the inclusive maximum. |
| <span id="calendar-input-ccalendar-client-inputs-unavailable-dates"></span>`unavailableDates` | `canonical string array` | Uses the server sequence. | Replaces the bounded unavailable-date set. |
| <span id="calendar-input-ccalendar-client-inputs-required"></span>`required` | `boolean` | Uses server or Field state. | Controls standalone required validity. |
| <span id="calendar-input-ccalendar-client-inputs-disabled"></span>`disabled` | `boolean` | Uses server or owner state. | Controls navigation selection and Form participation. |
| <span id="calendar-input-ccalendar-client-inputs-readonly"></span>`readonly` | `boolean` | Uses server or owner state. | Controls focusable nonmutable state. |
| <span id="calendar-input-ccalendar-client-inputs-invalid"></span>`invalid` | `boolean` | Uses server or Field state. | Controls application invalid state. |
| <span id="calendar-input-ccalendar-client-inputs-first-day-of-week"></span>`firstDayOfWeek` | `1 | 2 | 3 | 4 | 5 | 6 | 7 | null` | Uses the server input. | Replaces or restores the locale week start. |
| <span id="calendar-input-ccalendar-client-inputs-show-adjacent-days"></span>`showAdjacentDays` | `boolean` | Uses the server input. | Controls neighboring-month cell visibility. |
| <span id="calendar-input-ccalendar-client-inputs-fixed-weeks"></span>`fixedWeeks` | `boolean` | Uses the server input. | Controls six-row versus natural-row layout. |
| <span id="calendar-input-ccalendar-client-inputs-variant"></span>`variant` | `CCalendarVariant` ([`CCalendarVariant`](#calendar-interface-variant)) | Uses the server input. | Controls presentation. |
| <span id="calendar-input-ccalendar-client-inputs-size"></span>`size` | `CCalendarSize` ([`CCalendarSize`](#calendar-interface-size)) | Uses the server input. | Controls coordinated sizing. |
| <span id="calendar-input-ccalendar-client-inputs-on-value-change"></span>`onValueChange` | `function` | No semantic selection callback. | Receives pointer keyboard or reset selection requests. |
| <span id="calendar-input-ccalendar-client-inputs-on-visible-date-change"></span>`onVisibleDateChange` | `function` | No semantic month callback. | Receives button keyboard or selection-driven month requests. |

</div>

### Slots

-

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CCalendar events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="calendar-event-ccalendar-events-on-value-change"></span>`onValueChange` | `(value: string | null, detail: CCalendarValueChangeDetail) => void` ([`CCalendarValueChangeDetail`](#calendar-interface-ccalendar-value-change-detail)) | A pointer or keyboard selection requests a new date or the owning Form resets. | `{value, previousValue, controlled, source, sourceEvent}` ([`CCalendarValueChangeDetail`](#calendar-interface-ccalendar-value-change-detail)) | Uncontrolled selection commits before notification and emits native input/change; controlled selection is request-only. |
| <span id="calendar-event-ccalendar-events-on-visible-date-change"></span>`onVisibleDateChange` | `(visibleDate: string, detail: CCalendarVisibleDateChangeDetail) => void` ([`CCalendarVisibleDateChangeDetail`](#calendar-interface-ccalendar-visible-change-detail)) | Navigation or focus crossing a month requests another visible calendar month. | `{visibleDate, previousVisibleDate, controlled, source, sourceEvent}` ([`CCalendarVisibleDateChangeDetail`](#calendar-interface-ccalendar-visible-change-detail)) | Uncontrolled navigation commits before notification; controlled navigation waits for its owner. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CCalendar CSS variables

Apply these variables to `CCalendar` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="calendar-css-ccalendar-css-variables-background"></span>`--cui-calendar-background` | `color` | Root and native fallback background. | `Canvas` |
| <span id="calendar-css-ccalendar-css-variables-foreground"></span>`--cui-calendar-foreground` | `color` | Root foreground. | `CanvasText` |
| <span id="calendar-css-ccalendar-css-variables-border-color"></span>`--cui-calendar-border-color` | `color` | Root fallback and cell border. | `Mixed CanvasText.` |
| <span id="calendar-css-ccalendar-css-variables-focus-color"></span>`--cui-calendar-focus-color` | `color` | Navigation and day focus outline. | `Highlight` |
| <span id="calendar-css-ccalendar-css-variables-selected-background"></span>`--cui-calendar-selected-background` | `color` | Selected day background and border. | `Highlight` |
| <span id="calendar-css-ccalendar-css-variables-selected-foreground"></span>`--cui-calendar-selected-foreground` | `color` | Selected day text. | `HighlightText` |
| <span id="calendar-css-ccalendar-css-variables-today-color"></span>`--cui-calendar-today-color` | `color` | Today marker border. | `LinkText` |
| <span id="calendar-css-ccalendar-css-variables-adjacent-color"></span>`--cui-calendar-adjacent-color` | `color` | Weekdays and neighboring-month dates. | `Muted CanvasText.` |
| <span id="calendar-css-ccalendar-css-variables-unavailable-color"></span>`--cui-calendar-unavailable-color` | `color` | Unavailable date text. | `GrayText` |
| <span id="calendar-css-ccalendar-css-variables-radius"></span>`--cui-calendar-radius` | `length` | Root corner radius. | `0.75rem` |
| <span id="calendar-css-ccalendar-css-variables-padding"></span>`--cui-calendar-padding` | `length` | Root inset. | `0.75rem` |
| <span id="calendar-css-ccalendar-css-variables-gap"></span>`--cui-calendar-gap` | `length` | Header grid and cell spacing. | `0.25rem` |
| <span id="calendar-css-ccalendar-css-variables-cell-size"></span>`--cui-calendar-cell-size` | `length` | Day cell minimum target size. | `2.5rem` |
| <span id="calendar-css-ccalendar-css-variables-navigation-size"></span>`--cui-calendar-navigation-size` | `length` | Previous and next button size. | `2.5rem` |
| <span id="calendar-css-ccalendar-css-variables-font-size"></span>`--cui-calendar-font-size` | `length` | Root text size. | `1rem` |
| <span id="calendar-css-ccalendar-css-variables-invalid-border-color"></span>`--cui-calendar-invalid-border-color` | `color` | Invalid root border. | `Theme error.` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CCalendar attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="calendar-attribute-ccalendar-root-attributes-data-required"></span>`data-required` | Root group | `present | absent` | Mirrors effective requiredness. |
| <span id="calendar-attribute-ccalendar-root-attributes-data-disabled"></span>`data-disabled` | Root group | `present | absent` | Mirrors effective disabledness. |
| <span id="calendar-attribute-ccalendar-root-attributes-data-readonly"></span>`data-readonly` | Root group | `present | absent` | Mirrors effective readonly state. |
| <span id="calendar-attribute-ccalendar-root-attributes-data-invalid"></span>`data-invalid` | Root group | `present | absent` | Mirrors application or revealed native invalidity. |
| <span id="calendar-attribute-ccalendar-root-attributes-data-empty"></span>`data-empty` | Root group | `present | absent` | Marks no selected canonical value. |
| <span id="calendar-attribute-ccalendar-root-attributes-data-variant"></span>`data-variant` | Root group | `CCalendarVariant` ([`CCalendarVariant`](#calendar-interface-variant)) | Mirrors visual treatment. |
| <span id="calendar-attribute-ccalendar-root-attributes-data-size"></span>`data-size` | Root group | `CCalendarSize` ([`CCalendarSize`](#calendar-interface-size)) | Mirrors coordinated sizing. |

</div>

#### CCalendar attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="calendar-attribute-ccalendar-day-attributes-data-date"></span>`data-date` | Date gridcell | `canonical date` | Identifies the exact ISO domain date. |
| <span id="calendar-attribute-ccalendar-day-attributes-data-selected"></span>`data-selected` | Date gridcell | `present | absent` | Marks the committed selected date. |
| <span id="calendar-attribute-ccalendar-day-attributes-data-today"></span>`data-today` | Date gridcell | `present | absent` | Marks today in the effective provider time zone. |
| <span id="calendar-attribute-ccalendar-day-attributes-data-outside"></span>`data-outside` | Date gridcell | `present | absent` | Marks a neighboring-month date or blank. |
| <span id="calendar-attribute-ccalendar-day-attributes-data-unavailable"></span>`data-unavailable` | Date gridcell | `present | absent` | Marks a focusable date that selection rejects. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CCalendar selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="calendar-selector-ccalendar-selectors-calendar"></span>`[data-citry-ui-part="calendar"]` | Root group | State reflections root attrs and styling destination. |
| <span id="calendar-selector-ccalendar-selectors-header"></span>`[data-citry-ui-part="header"]` | Header div | Navigation and localized heading layout. |
| <span id="calendar-selector-ccalendar-selectors-previous"></span>`[data-citry-ui-part="previous"]` | Button | Requests the previous calendar month. |
| <span id="calendar-selector-ccalendar-selectors-heading"></span>`[data-citry-ui-part="heading"]` | Live h2 | Announces the localized visible month and year. |
| <span id="calendar-selector-ccalendar-selectors-next"></span>`[data-citry-ui-part="next"]` | Button | Requests the next calendar month. |
| <span id="calendar-selector-ccalendar-selectors-grid"></span>`[data-citry-ui-part="grid"]` | Table grid | Owns localized weekdays and roving date cells. |
| <span id="calendar-selector-ccalendar-selectors-weekday-row"></span>`[data-citry-ui-part="weekday-row"]` | Header row | Owns the seven localized weekday headers. |
| <span id="calendar-selector-ccalendar-selectors-weekday"></span>`[data-citry-ui-part="weekday"]` | Column header | Displays abbreviated and full localized weekday names. |
| <span id="calendar-selector-ccalendar-selectors-week"></span>`[data-citry-ui-part="week"]` | Grid row | Groups one locale-ordered week. |
| <span id="calendar-selector-ccalendar-selectors-day"></span>`[data-citry-ui-part="day"]` | Gridcell | Exact roving focus selection and day-state hook. |
| <span id="calendar-selector-ccalendar-selectors-fallback-input"></span>`[data-citry-ui-part="fallback-input"]` | Native Date input | Form reset validity and no-JavaScript transport. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="calendar-interface-date"></span>`CCalendarDate` | `date | str` |
| <span id="calendar-interface-variant"></span>`CCalendarVariant` | `Literal["outline", "plain"]` |
| <span id="calendar-interface-size"></span>`CCalendarSize` | `Literal["sm", "md", "lg"]` |
| <span id="calendar-interface-change-source"></span>`CCalendarChangeSource` | `Literal["pointer", "keyboard", "button", "value", "reset"]` |
| <span id="calendar-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="calendar-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="calendar-interface-ccalendar-value-change-detail"></span>

#### `CCalendarValueChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="calendar-interface-ccalendar-value-change-detail-value"></span>`value` | `string | null` | - | Requested selected canonical date or empty state. |
| <span id="calendar-interface-ccalendar-value-change-detail-previous-value"></span>`previousValue` | `string | null` | - | Effective selected date before the request. |
| <span id="calendar-interface-ccalendar-value-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client value owns committed selection. |
| <span id="calendar-interface-ccalendar-value-change-detail-source"></span>`source` | `CCalendarChangeSource` ([`CCalendarChangeSource`](#calendar-interface-change-source)) | - | Pointer keyboard value or reset cause. |
| <span id="calendar-interface-ccalendar-value-change-detail-source-event"></span>`sourceEvent` | `object | null` | - | Native interaction event when one exists. |

</div>

<span id="calendar-interface-ccalendar-visible-change-detail"></span>

#### `CCalendarVisibleDateChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="calendar-interface-ccalendar-visible-change-detail-visible-date"></span>`visibleDate` | `string` | - | Requested canonical date inside the new visible month. |
| <span id="calendar-interface-ccalendar-visible-change-detail-previous-visible-date"></span>`previousVisibleDate` | `string` | - | Visible canonical date before the request. |
| <span id="calendar-interface-ccalendar-visible-change-detail-controlled"></span>`controlled` | `boolean` | - | Whether client visibleDate owns the visible month. |
| <span id="calendar-interface-ccalendar-visible-change-detail-source"></span>`source` | `CCalendarChangeSource` ([`CCalendarChangeSource`](#calendar-interface-change-source)) | - | Button keyboard selection value or reset cause. |
| <span id="calendar-interface-ccalendar-visible-change-detail-source-event"></span>`sourceEvent` | `object | null` | - | Native interaction event when one exists. |

</div>

### Translation keys

Catalog keys used by this family. An explicit component input or slot listed in Override
takes precedence over the catalog for that instance.

#### CCalendar translation keys

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-3 ui-api-table--width-column-4 ui-api-table--width-column-5" markdown="1" style="--ui-api-column-1-width: 18rem; --ui-api-column-3-width: 10rem; --ui-api-column-4-width: 12rem; --ui-api-column-5-width: 13rem">

| Key | Purpose | Variables | Override | Browser updates |
|---|---|---|---|---|
| <span id="calendar-translation-ccalendar-translations-label"></span>`citry-ui-calendar-label` | Names a standalone root group and its native fallback. | `none` | `label` or root `attrs` aria-label/aria-labelledby | `$c-tr` updates both stable aria-label destinations. |
| <span id="calendar-translation-ccalendar-translations-previous-month"></span>`citry-ui-calendar-previous-month` | Names the previous-month button. | `none` | `previous_label` | `$c-tr` updates the stable aria-label destination. |
| <span id="calendar-translation-ccalendar-translations-next-month"></span>`citry-ui-calendar-next-month` | Names the next-month button. | `none` | `next_label` | `$c-tr` updates the stable aria-label destination. |
| <span id="calendar-translation-ccalendar-translations-unavailable"></span>`citry-ui-calendar-unavailable` | Supplies custom native validity when a selected date becomes unavailable. | `none` | `unavailable_message` | `i18n.bind()` updates the browser-owned validity message. |

</div>