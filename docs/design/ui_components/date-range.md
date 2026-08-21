# Citry UI DateRange specification

**Status (2026-08-21): runtime, public docs, structured reference, quality
scenario, focused server tests, and three-browser behavior/i18n evidence
complete; human visual, mobile, and assistive-technology review remains.** This specification
governs one `CDateRange` that collects an ordered start and end calendar date,
offers one anchored range-calendar popup, and submits two canonical Gregorian
values. `CDateInput`, `CCalendar`, and `CDatePicker` remain the single-date
paths.

## 1. Purpose and product bar

`CDateRange` lets a person choose an inclusive interval such as a trip,
reporting window, or reservation. The visible summary follows the active Citry
locale while the two Form values remain `YYYY-MM-DD`.

| Job | Shortest path | Classification |
|---|---|---|
| Choose an inclusive trip interval | `<c-CDateRange start_name="depart" end_name="return" />` | direct API |
| Set exact outer bounds | `min`, `max` | direct API |
| Block a bounded set of dates | `unavailable_dates` | direct API |
| Submit and reset two values | native start/end transports | native composition |
| Build two independently labeled date fields | two `CDateInput` or `CDatePicker` instances | ordinary composition |
| Choose multiple unrelated dates | later multiple-date family | unsupported here |

Production completeness requires ordered controlled and uncontrolled state,
an explicit two-click draft, pointer/focus range preview, exact constraints,
two native Form fields, reset and invalid focus, useful no-JavaScript controls,
localized display and live switching, three-browser evidence, public docs,
structured API data, and bounded assets. Non-goals are free-form parsing,
dates with times or zones, arbitrary executable disabled-date predicates,
multiple intervals, presets, multi-month layout, and a headless family.

## 2. Prior art and complaints

The source record was refreshed immediately before implementation.

| Product or standard | Version or review date | Source inspected | Decision supported |
|---|---|---|---|
| Vuetify | master/current source, 2026-08-20 | `VDatePicker` range model, header, bounds, allowed dates, preview plumbing | Treat range as a distinct array-valued mode, normalize dates, retain one calendar, preview a draft, and keep bounded constraints. |
| React Aria | current docs, 2026-08-20 | `DateRangePicker`, `RangeCalendar`, Forms, locale/calendar behavior | Use two Form names, one range object, two date endpoints, a shared popup calendar, canonical values, and explicit unavailable-range policy. |
| MUI X | current docs, 2026-08-20 | DateRangePicker variants, validation, accessibility and keyboard tables | Keep field and calendar behavior coherent, label the dialog, expose one or two native values clearly, and avoid device-dependent semantic contracts. |
| Vaadin | current docs, 2026-08-20 | Date Picker date-range usage pattern | Preserve the robust fallback: two ordinary date inputs linked by ordered bounds are enough without JavaScript. |
| HTML | Living Standard through current MDN behavior, 2026-08-20 | date input value, Form, reset, constraint validation | There is no native range control; submit two named canonical inputs and revalidate on the server. |
| Complaint register | current, 2026-08-20 | React Aria adjacent-month issue and multi-month discussion; MUI incomplete-value acceptance and placeholder bugs | Keep adjacent days selectable, avoid segmented typing, make the two-click commit boundary explicit, and do not infer partial typed state. |

Vuetify receives the workflow's weighted review. Its `multiple="range"` model
and hover preview are adopted as jobs, not as its broad prop surface. Citry
reuses its already tested Calendar and Popover rather than duplicating adapter,
grid, or layer behavior.

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `modelValue` array in range mode | direct range state | `start`, `end`; client `value` | adopt as named endpoints |
| `multiple="range"` | dedicated family | `CDateRange` | adopt without mode union |
| hover `previewValue` | internal draft preview | reflected day attributes | adopt; no public hover state |
| `min`, `max`, `allowedDates` | bounded data | `min`, `max`, `unavailable_dates` | adopt finite values; omit callbacks |
| month/year/view mode | composed Calendar state | existing Calendar navigation | keep month navigation only |
| header/actions and confirmation | immediate second-date commit | no confirmation slot | simplify |
| landscape, color, elevation, density | theme contract | variant, size, variables | replace |
| multiple unrelated dates | separate later family | none | omit |

## 3. Public composition and anatomy

```html
<fieldset>
  <legend>Travel dates</legend>
  <c-CDateRange start_name="departure" end_name="return" required />
</fieldset>
```

Python composition is `CDateRange(start=date(2026, 8, 19),
end=date(2026, 8, 24), start_name="from", end_name="through")`.

```text
CDateRange root (group)
├─ fallback group
│  ├─ localized Start date label + native input[type=date]
│  └─ localized End date label + native input[type=date]
└─ enhanced group
   ├─ CPopover
   │  ├─ one Button trigger + CIcon(calendar)
   │  └─ one controlled CCalendar (no name, isolated from Field/Form)
   └─ optional clear Button
```

The component deliberately does not compose inside `CField`: a Field owns one
label and one Form control, while DateRange has two submitted controls. Authors
use a native `fieldset`/`legend`, surrounding text, or the component's
`range_label`, `start_label`, and `end_label`. `CForm` may own both values.

## 4. Server inputs and client inputs

Server inputs are `start`, `end`, `start_name`, `end_name`, `form`, `id`,
`min`, `max`, `unavailable_dates`, nullable owner states
`required/disabled/readonly/invalid`, `clearable`, Popover `dismissible`,
`placement`, `match_width`, Calendar `first_day_of_week`,
`show_adjacent_days`, `fixed_weeks`, localized-label overrides,
`variant`, `size`, `class_`, `style`, and `attrs`.

`start` and `end` are both empty or both present. Present endpoints are ordered,
inside bounds, and available. A committed range cannot cross an unavailable
date. The unavailable list is unique and capped at 4096.

| Client input | Type | Omitted | `null` | Invalid | Affected surfaces |
|---|---|---|---|---|---|
| `value` | `{start,end}` | uncontrolled | controlled empty | retain/report | inputs, trigger, Calendar |
| `open` | boolean | uncontrolled | invalid | retain/report | Popover |
| states | boolean | server/owner | invalid | retain/report | inputs/root |
| popup/layout inputs | existing bounded types | server | invalid unless nullable | retain/report | popup/Calendar |
| callbacks | function | none | none | ignore/report | notifications |

Bounds and unavailable dates are structural server inputs in v1. A server
rerender replaces them atomically.

## 5. State model

Committed state is either empty or `{start,end}` with `start <= end`. Opening a
completed or empty range has no draft. The first available day activation
starts a draft and leaves the popup open. Pointer hover or keyboard focus marks
the inclusive prospective range. The second available activation commits the
two endpoints in chronological order and closes. Activating the same day twice
creates a one-day range. Escape or outside dismissal discards the draft and
keeps the committed value.

A defined client `value` controls the pair as one atomic channel. A defined
client `open` controls visibility. Reset returns uncontrolled state to both
server endpoints, discards draft state, and closes. Disabled blocks focus,
selection, clearing, and Form participation. Readonly remains focusable and
submitted but blocks changes.

## 6. Slots and slot data

There are no slots. Presets, helper prose, error messages, and actions compose
outside through ordinary markup. The generated Calendar remains an owned
implementation detail rather than a partially forwarded slot API.

## 7. Callbacks, native events, and methods

`onValueChange(next, detail)` receives an object or `null`; detail contains
`value`, `previousValue`, `controlled`, `source` (`calendar`, `clear`, `reset`,
`native`), and `sourceEvent`. One uncontrolled commit updates both inputs, then
dispatches `input` and `change` from each changed native input in start/end
order. Draft changes do not emit value callbacks or native events.

`onOpenChange(next, detail)` follows the existing Popover detail vocabulary.
There are no custom DOM events or public methods.

## 8. Semantics, keyboard, focus, and assistive technology

The root is a named group. Before enhancement, two explicitly labeled native
date inputs are ordinary tab stops. After enhancement, the trigger is the
public tab stop and owns the popup relationship. The popup is named by the
localized range label. Calendar grid navigation and one-tab-stop behavior are
unchanged. The first activation announces and marks a start endpoint; focus or
hover previews the interval; the second activation commits it. Escape restores
the trigger and discards only the draft.

Range styling never replaces `aria-selected`: committed or draft cells expose
range position with labels and data attributes while Calendar retains its one
active selection for focus. Screen-reader names add “start date” or “end date”
only at endpoints, not repetitive prose on every interior day.

## 9. Native forms and validation

Two native date inputs submit `start_name` and `end_name`. `required` applies
to both. `min`/`max` apply to both; the current start also becomes the end
input's minimum, and the current end becomes the start input's maximum. Native
fallback editing rejects partial pairs, reversed endpoints, unavailable
endpoints, or a range crossing unavailable dates through checked custom
validity. Invalid submission focuses the first invalid native input without
enhancement; after enhancement it opens and focuses the Calendar.

External `form`, disabled omission, readonly submission, fieldset disabledness,
reset, and FormData are preserved. Server validation remains mandatory.

## 10. Styling and theme contract

The family exposes outline, filled, plain and sm, md, lg. Stable variables
cover control background/foreground/border/focus/invalid colors, range fill,
endpoint fill/foreground, radius, height, padding, gap, and clear size. Stable
parts are range root, fallback group, start input, end input, enhanced control,
control, value, icon, and clear. Within the composed Calendar, DateRange owns
only additional `data-range-start`, `data-range-end`, `data-in-range`, and
`data-range-preview` styling.

## 11. Environmental behavior

Logical properties, Popover placement, and Calendar arrow behavior support
RTL. Locale formatting and week data come from the logical i18n provider;
canonical values never change. The contract covers light/dark, nested color
schemes, forced colors, reduced motion, narrow/touch, 400% zoom, long labels,
and print. The no-JavaScript path stays useful on mobile through native inputs.

## 12. Overlay and layering behavior

The non-modal `CPopover` owns positioning, collision, Escape/outside closure,
focus restoration, nesting, and cleanup. The range component neither traps
focus nor locks scroll. Selection commits close after the second activation;
the first activation never closes.

## 13. Async, loading, empty, and error behavior

The family is synchronous. Empty means both values are absent. One server
endpoint without the other is a configuration error. Invalid client values
retain the last complete pair and report once per invalid episode. There is no
loading surface.

## 14. Server rerender, fragments, morphing, and cleanup

Committed range, draft, open state, visible month, and focus survive compatible
morphs by public identity. Structural constraints come from a server rerender.
Locale fragments reconcile before activation. Every listener, effect, reset
entry, observer, Popover/Calendar callback, i18n subscription, and binding is
released on removal.

## 15. Security and trust boundaries

Dates and lists are strictly parsed and bounded. Generated labels use
`textContent`; no catalog string reaches `innerHTML`. Root filtering blocks
owned/executable/runtime attributes. Callbacks and submitted values remain
untrusted application input.

## 16. Assets and performance

`CDateRange` adds one small component initializer and theme block, reusing
Calendar, Popover, Icon, form-control runtime, and i18n assets by identity. It
creates at most one six-week grid and scans at most the bounded unavailable
list/range. No locale bundle, second calendar, or parser is embedded. Exact
connected/isolated gzip budgets are recorded after implementation.

## 17. Documentation, metadata, and export obligations

The family ships runtime, package exports, registration, source README,
component-owned `api.md`, schema-valid `api.yml`, preview catalog and sources,
quality scenario, three-browser tests, inventory/plan counts, i18n catalog
artifacts, asset baselines, distribution allowlist, and installed-wheel checks.

## 18. Compatibility and deprecation

The stable v1 surface is the ordered value pair, two native Form fields,
two-click draft/commit behavior, callback detail, state attributes, stable
parts, variables, and translation keys. Generated IDs, internal Calendar
composition, exact day markup, and JavaScript organization remain private.

## 19. Public documentation contract

Guide order: basic range, draft/commit behavior, Forms/reset, bounds and
unavailable dates, controlled state, keyboard/focus, locales, no-JavaScript
fallback, styles, and when to use two independent single-date controls.

| Preview | Reader task | Required coverage |
|---|---|---|
| Basic | choose a trip interval | two clicks, summary, preview |
| Form | submit/reset two dates | names, required, FormData, no-JS |
| Constraints | choose a valid interval | min/max, unavailable crossing |
| Controlled | own pair and popup | refusal/acceptance, callbacks |
| Locales | switch locale | range summary, Calendar, RTL |
| States | compare presentation | variants, sizes, readonly/disabled/invalid |

The structured reference ends with the Translation keys table. Every row names
the purpose, variables, server override, and live-update mechanism.

## 20. Open decisions and deferred work

No decision blocks implementation. Deferred work includes multi-month layout,
range presets, arbitrary unavailable predicates, noncontiguous ranges, minimum
or maximum duration, localized segmented editing, and date-time ranges. If one
composed controlled Calendar cannot preserve range preview and endpoint
announcements without breaking its public single-selection contract, the
implementation must stop and reopen a dedicated range-grid foundation rather
than patching private child internals blindly.

## 21. Implementation and acceptance plan

1. Add strict server normalization for an all-empty or complete ordered pair,
   bounds, unavailable crossings, names, labels, states, and root attrs.
2. Render two useful native inputs plus one enhanced Popover/Calendar route;
   isolate the child Calendar from Field/Form ownership.
3. Add the atomic controlled pair, two-click draft, pointer/focus preview,
   ordered commit, clear/reset/native edit, invalid focus, and cleanup runtime.
4. Add localized source messages and date-range format profile use. Stable
   labels use `$c-tr`; dynamic summary/day names use the provider subscription;
   custom validity uses `i18n.bind()`.
5. Add focused server tests, browser tests in Chromium/Firefox/WebKit, and axe
   evidence for default and active popup states.
6. Finish public guide, structured API reference with the final translation
   section, previews, quality catalog, inventory/counts, asset baselines, and
   installed-wheel qualification in the same change.

Acceptance requires useful server-only output, no-JavaScript two-input Forms,
ordered pair behavior, draft cancellation, range preview, exact constraints,
controlled refusal/acceptance, native events, reset, live locale switching,
logical ownership, cleanup, no high-impact axe findings, and bounded assets in
all three supported browser engines.
