# Citry UI Calendar specification

**Status (2026-08-19): approved design, implementation in progress.** This
specification governs one styled `CCalendar` that selects a single calendar
date inline. `CDateInput`, `CDatePicker`, and date-range selection remain
separate families.

## 1. Purpose and product bar

`CCalendar` lets a person inspect one localized calendar month, move between
months, and select one date. The application value and Form value remain a
canonical Gregorian `YYYY-MM-DD` string. The displayed calendar, month name,
weekday names, week start, day numbers, and full date names follow the active
Citry locale.

Common jobs and shortest support paths:

| Job | Shortest template or Python call | Support path |
|---|---|---|
| Select one date inline | `<c-CCalendar name="arrival" />` | direct API |
| Label and describe the choice | place it in `CField` | composition |
| Set an initial date | `value="2026-08-19"` or `value=date(...)` | direct API |
| Limit the date | `min=... max=...` | direct API |
| Exclude a finite set | `unavailable_dates=(...)` | direct API |
| Require a value | `required` | native Form validation through the transport input |
| Control selection in Alpine | `$c-props="{ value: arrival }"` | client input |
| Observe selection | `onValueChange` or bubbling native `input` and `change` | callback and native events |
| Control the visible month | client `visibleDate` plus `onVisibleDateChange` | client input and callback |
| Override the week start | `first_day_of_week=1` | direct API; `1` is Monday and `7` is Sunday |
| Change presentation | `variant="plain" size="lg"` | direct API |

Production completeness requires a one-tab-stop grid, complete keyboard
navigation, localized browser-created text, controlled and uncontrolled state,
native Form/reset/required behavior, a useful no-JavaScript fallback, live
locale switching, light/dark/RTL/forced-color behavior, three-browser tests,
public documentation, structured reference, and installed-wheel evidence.

Non-goals:

- free-form or segmented date entry;
- a popup, dialog, focus trap, or dismissal policy;
- date ranges, multiple dates, weeks, quarters, or time values;
- arbitrary browser callbacks that decide whether a date is unavailable;
- month/year selection views, multi-month layouts, presets, or day slots; and
- a headless family.

## 2. Prior art and complaints

Prior art checked before implementation:

- `VDatePicker.tsx` and `VDatePickerMonth.tsx` in Vuetify 4.1.6 for the
  adapter-backed model, view changes, adjacent days, range behavior, focus,
  and accessibility strings;
- React Aria Calendar and CalendarGrid for controlled state, localized
  calendars, unavailable dates, and grid keyboard behavior;
- Ark UI DatePicker 5.38.2 for its inline mode, anatomy, multi-view surface,
  week configuration, and unavailable-date distinction;
- the WAI-ARIA Authoring Practices date-picker-dialog example and Grid pattern
  for roles, one tab stop, full weekday names, live month headings, and keys;
- Spectrum Web Components Calendar for a Web Component value, min/max, and
  clear-method comparison;
- the HTML Date input for canonical values, native Form behavior, validation,
  and the no-JavaScript fallback;
- React Spectrum issue 3257 for complaints caused by disabling every adjacent
  date and for duplicate adjacent dates in multi-month views;
- React Spectrum issue 5630 for navigation-button naming and mobile screen
  reader heading tradeoffs; and
- Vuetify issue 20217 for failures caused by mixing formatted date strings
  with the component's canonical value domain.

Current-source record:

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Vuetify | 4.1.6, reviewed 2026-08-19 | `VDatePicker`, `VDatePickerMonth`, date adapter | Keep a canonical value, a separate visible-month state, adjacent days, min/max, and direct navigation controls. |
| React Aria | current, reviewed 2026-08-19 | Calendar and CalendarGrid docs | Follow the active locale, distinguish disabled from unavailable dates, and use one roving grid tab stop. |
| Ark UI | 5.38.2, reviewed 2026-08-19 | DatePicker docs and anatomy | Keep inline Calendar focused; reserve range, multiple, multi-month, preset, and view-selection jobs. |
| WAI-ARIA APG | current, reviewed 2026-08-19 | Date Picker Dialog example and Grid pattern | Adopt grid semantics, complete key navigation, a live month heading, and full accessible date names. |
| HTML | Living Standard, reviewed 2026-08-19 | Date state and Form rules | Preserve one native Date input as fallback, transport, reset baseline, and validity owner. |
| Spectrum Web Components | current, reviewed 2026-08-19 | `sp-calendar` docs | Support value, min/max, pointer, Space, Enter, and an imperative clear through ordinary controlled state rather than a special method. |
| ECMA-402 and MDN | 2026 / reviewed 2026-08-19 | `Intl.Locale.getWeekInfo()` and DateTimeFormat | Derive locale week starts in the browser and expose an explicit override. |
| React Spectrum complaints | issues 3257 and 5630, reviewed 2026-08-19 | adjacent-day and accessibility reports | Keep outside dates selectable in the one-month layout; use exact previous/next labels and verify real assistive technology. |
| Vuetify complaint | issue 20217, reviewed 2026-08-19 | formatted-string model failure | Never use localized display strings as selection, comparison, callback, or Form values. |

Citry adopts a single visible month, a canonical ISO domain, a locale-aware
calendar view, selectable adjacent days, focusable-but-unselectable unavailable
days, and native transport. Citry omits adapter objects from the component API.
The i18n provider and named profiles are the adapter.

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `modelValue` and `multiple` | direct for one value; separate family for ranges/multiple | `value`; DateRange | adopt single value only |
| `min`, `max`, `allowedDates` | direct finite constraints | `min`, `max`, `unavailable_dates` | adopt bounded data; omit executable predicates |
| `month`, `year`, `viewMode` | one visible-date state; omit alternate views | `visibleDate`, `onVisibleDateChange` | keep navigation without month/year selection views |
| adjacent months | direct presentation | `show_adjacent_days` | adopt; adjacent dates stay selectable |
| weeks in month | direct presentation | `fixed_weeks` | adopt stable six-week or natural-height layout |
| weekday format and locale | package profiles and provider locale | no format-string prop | adopt checked i18n ownership |
| header, title, controls, day slots | separate composition or omitted | no slots in v1 | omit unproved structural customization |
| previous/next icons and labels | built-in controls and translation keys | stable parts plus label overrides | adopt behavior, keep internal icon markup private |
| range hover and multi-month | separate family | DateRange | omit |
| density, elevation, color | CSS and suite vocabulary | `size`, `variant`, public variables | adopt through the theme contract |

## 3. Public composition and anatomy

```html
<c-CField control_id="arrival" required>
  <c-fill name="label">Arrival date</c-fill>
  <c-CCalendar
    name="arrival"
    min="2026-08-19"
    max="2027-08-19"
  />
  <c-fill name="description">Choose a date in the next year.</c-fill>
</c-CField>
```

```python
CField(
    control_id="arrival",
    required=True,
    slots={
        "label": "Arrival date",
        "default": CCalendar(name="arrival", value=date(2026, 8, 19)),
    },
)
```

```text
div[role="group"]
├── div header
│   ├── button previous
│   ├── h2 live month heading
│   └── button next
├── table[role="grid"]
│   ├── thead with seven localized weekday headers
│   └── tbody with four to six week rows
└── input[type="date"] native fallback and Form transport
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CCalendar` | one `div[role="group"]` | `attrs`, `class_`, and `style` merge on the root | one owned native Date input; one labelled grid and live heading |

The public `id` belongs to the native Form control so a `CField` label keeps
working before and after activation. The root, navigation buttons, heading,
grid, day cells, and fallback input expose stable part selectors. Consumers
cannot replace owned roles, IDs, relationships, transport attributes, or
runtime directives.

The anatomy review retains the native input because it supplies useful fallback
and browser validation. It retains the root because root attributes and state
apply to both the fallback and enhanced calendar. No declaration-only wrapper
or structural child component is needed.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `value` | `date | str | None` | `None` | initial/reset value | exact `date` or real canonical ISO date |
| `visible_date` | `date | str | None` | selected date, otherwise today | initial view | chooses the month containing this ISO date |
| `name` | `str | None` | `None` | Form configuration | nonempty when supplied |
| `form` | `str | None` | owner Form | Form configuration | valid ID and cannot escape an enclosing `CForm` |
| `id` | `str | None` | Field ID or generated | identity | valid ID and must agree with Field ownership |
| `min`, `max` | `date | str | None` | `None` | reactive constraints | real canonical dates in ascending order |
| `unavailable_dates` | `Sequence[date | str]` | `()` | reactive constraint fallback | at most 4096 unique real canonical dates |
| `required` | `bool | None` | Field or `False` | reactive state fallback | native empty-value validity |
| `disabled` | `bool | None` | Field/Form or `False` | reactive state fallback | blocks every interaction and Form participation |
| `readonly` | `bool | None` | Field/Form or `False` | reactive state fallback | permits navigation but not selection |
| `invalid` | `bool | None` | Field or `False` | reactive state fallback | combines with revealed native invalidity |
| `first_day_of_week` | `Literal[1,2,3,4,5,6,7] | None` | `None` | reactive locale policy | ISO weekday; `None` follows the locale |
| `show_adjacent_days` | `bool` | `True` | reactive presentation | shows selectable dates outside the named month |
| `fixed_weeks` | `bool` | `True` | reactive presentation | renders six rows instead of four to six |
| `label` | `str` | catalog `Calendar` | server accessible text | names a standalone calendar; explicit value stays literal |
| `previous_label`, `next_label` | `str` | catalog defaults | server accessible text | name chronological page controls; explicit values stay literal |
| `variant` | `"outline" | "plain"` | `"outline"` | reactive presentation | reflected on the root |
| `size` | `"sm" | "md" | "lg"` | `"md"` | reactive presentation | reflected on the root |
| `class_`, `style` | structured style values | `None` | server styling | merge on the root |
| `attrs` | `Mapping[str, object] | None` | `None` | trusted root escape path | adds unowned root attributes |

Localized, noncanonical, impossible, duplicate, or out-of-range inputs fail at
server construction. `datetime` is rejected even though it subclasses `date`.

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `value` | canonical string or null | releases control at latest accepted value | clears selection | retains previous valid value and reports once | selection and FormData |
| `visibleDate` | canonical string | releases view control | invalid | retains previous view and reports once | visible calendar month |
| `min`, `max` | canonical string or null | server fallback | removes bound | retains prior valid constraints | selectable dates and native validity |
| `unavailableDates` | array of unique canonical strings | server fallback | invalid | retains prior valid set | unavailable dates |
| state booleans | boolean | server/owner fallback | invalid | fallback and report | interaction, ARIA, Form |
| `firstDayOfWeek` | integer 1 through 7 or null | server fallback | follows locale | retains prior valid policy | weekday order and grid alignment |
| `showAdjacentDays`, `fixedWeeks` | boolean | server fallback | invalid | fallback and report | grid rows and outside cells |
| `variant`, `size` | documented value | server fallback | invalid | fallback and report | presentation |
| callbacks | function | no callback | invalid | ignored and reported | notifications only |

Value and visible month become controlled independently when their client
inputs are present. Removing either client input releases only that state.
Server morphs update fallbacks and reset baselines without parsing displayed
text. Nested instances keep separate state and provider ownership.

## 5. State model

Public state includes selected/empty, visible month, focused date,
enabled/disabled, editable/readonly, valid/invalid, controlled/uncontrolled,
required/optional, locale, size, and variant.

| Transition | Guard | Commit and effects |
|---|---|---|
| select focused date | enabled, editable, selectable | request/commit canonical value; update native input; notify callback and native events |
| select outside date | same | also make its calendar month visible |
| move focus | enabled and target within min/max | update roving tab stop; change visible month if needed |
| previous/next page | enabled | request/commit visible month while preserving day ordinal where possible |
| value prop change | canonical or null | update selection and show its month when view is uncontrolled |
| locale change | client provider active | reformat all browser-created text, reorder weekdays, retain canonical selection and focused date |
| constraints change | valid coherent set | update selectable state and move focus to nearest allowed date if necessary |
| reset | native Form reset | restore initial uncontrolled value/view and notify matching callback behavior |
| native invalid | required empty submission | mark component and Field invalid, then focus the active day |

Unavailable dates remain focusable so a person can inspect them, but Enter,
Space, and pointer selection do nothing. Dates outside min/max are disabled and
not focusable. Disabled Calendar makes every control unavailable. Readonly
Calendar keeps navigation and inspection available while blocking selection.

## 6. Slots and slot data

There are no slots. Application labels, descriptions, and errors belong to
`CField`. Custom day contents, headers, navigation controls, multi-month
layouts, and presets would expand the accessibility and live-localization
contract and need separate evidence before becoming public.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onValueChange` | `(value, detail)` | pointer, keyboard, or reset request | once after the request is formed | reports requested value without committing it | return value ignored |
| `onVisibleDateChange` | `(date, detail)` | navigation or focus crossing a month | once after the request is formed | reports requested month anchor without committing it | return value ignored |

Value detail contains `value`, `previousValue`, `controlled`, `source`, and
`sourceEvent`. Visible-date detail contains `visibleDate`,
`previousVisibleDate`, `controlled`, `source`, and `sourceEvent`. Sources are
`pointer`, `keyboard`, `button`, `value`, or `reset` as applicable.

Uncontrolled selection dispatches bubbling native `input` followed by
`change` from the owned Date input. Those events make ordinary root listeners
and Forms useful. Controlled requests do not claim that the transport value
changed.

Public methods:

- `focus()` focuses the current roving day and returns `true`, or `false` when
  disabled or no allowed day exists.
- `focusDate(value)` accepts a canonical ISO string, reveals and focuses the
  date when it is inside min/max, and otherwise returns `false` without change.
- `previousPage()` and `nextPage()` request one calendar-month move and return
  whether navigation was allowed.

## 8. Semantics, keyboard, focus, and assistive technology

The enhanced root is a named group. Its table has `role="grid"`, each week has
`role="row"`, and each date cell has `role="gridcell"`. Exactly one selectable
or unavailable date has `tabindex="0"`; other date cells use `-1`. Cells expose
a localized full date name, `aria-selected`, `aria-current="date"` for today,
and `aria-disabled` when unavailable. Min/max dates are absent from the focus
sequence. Weekday abbreviations display a short name and expose the full name.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| day grid | Arrow Left/Right | move one visual cell; chronological sign follows direction | target day | yes |
| day grid | Arrow Up/Down | move seven days | target day | yes |
| day grid | Home/End | first/last day in the current displayed row | target day | yes |
| day grid | Page Up/Down | previous/next calendar month | same ordinal day, clamped | yes |
| day grid | Shift+Page Up/Down | previous/next year in the displayed calendar | same month/day ordinal where available | yes |
| day grid | Enter or Space | request selection | stays on selected day | yes |
| anywhere | Tab/Shift+Tab | ordinary page order through navigation buttons and one grid cell | next/previous page control | no |

Pointer and touch select the same cells. Clicking a `CField` label focuses the
native input, whose focus handler forwards focus to the active grid cell after
activation. The month heading uses `aria-live="polite"`; focus changes do not
create a second custom announcement.

## 9. Native forms and validation

The owned Date input carries `name`, `form`, canonical `value`, min/max,
required, disabled, and readonly state. Before JavaScript it is an ordinary
visible Date input. After activation it becomes visually hidden but remains the
native Form, reset, and validity owner. It is never hidden with the HTML
`hidden` attribute and is not disabled merely because enhancement succeeded.

A non-disabled named selection contributes one `YYYY-MM-DD` FormData entry.
Required empty state blocks native submission. Invalid focus is redirected to
the active grid day. Reset restores the server baseline for uncontrolled state.
The server validates every submitted value and unavailable-date rule again.

## 10. Styling and theme contract

Variants are `outline` and `plain`; sizes are `sm`, `md`, and `lg`. Stable
public variables cover background, foreground, border, radius, padding, gap,
cell size, selected/today/unavailable/adjacent colors, focus color, navigation
button size, and heading/weekday typography.

Stable selectors are the `data-citry-ui-part` values `calendar`, `header`,
`previous`, `heading`, `next`, `grid`, `weekday`, `week`, `day`, and
`fallback-input`. Reflected root attributes are `data-disabled`,
`data-readonly`, `data-required`, `data-invalid`, `data-empty`, `data-variant`,
`data-size`, and `data-enhanced`. Day cells reflect `data-selected`,
`data-today`, `data-outside`, `data-unavailable`, and `data-focused`.

Private classes and exact theme values may change. Public variables inherit
through the root and resolve through private effective variables.

## 11. Environmental behavior

- Light/dark and nested schemes use Canvas-derived colors.
- RTL uses logical spacing and mirrors chronological arrows. Arrow keys follow
  the visual cell order.
- Reduced motion disables optional focus/selection transitions.
- Forced colors exposes selected, current, unavailable, and focus states with
  system colors and outlines rather than color alone.
- At 200% and 400% zoom the grid reflows within its container without horizontal
  page scrolling at a 320 CSS-pixel viewport.
- Touch targets use the configured cell size and coarse-pointer minimum.
- Print shows the selected month and hides interactive navigation controls.
- Long translated labels remain accessible names and do not determine control
  width.

Internationalization ownership:

| Output | Default owner | Initial destination | Live update |
|---|---|---|---|
| standalone Calendar name | `citry-ui-calendar-label` | server `aria-label` | `$c-tr` attribute binding |
| previous/next names | two component keys | server button attributes | `$c-tr` attribute bindings |
| month heading | named date profile | browser-created text | i18n subscription and `i18n.format.date()` |
| short/full weekdays | named date profiles | browser-created text/attribute | i18n subscription |
| day number and full date name | named date profiles | browser-created text/attribute | i18n subscription |

Explicit label overrides emit no catalog binding. The component uses only
literal package-owned profile names. A locale change rebuilds localized text
and week order while retaining ISO state. `first_day_of_week` overrides locale
week data when supplied. Locale week data comes from `Intl.Locale.getWeekInfo()`
or its earlier `weekInfo` property spelling; a browser with neither keeps the
server/source Sunday default unless the author supplies the explicit input.

## 12. Overlay and layering behavior

`CCalendar` creates no overlay, teleport, outside-interaction listener, focus
trap, scroll lock, or z-index policy. `CDatePicker` owns the popup composition.

## 13. Collections, async data, and identity

The finite collection is the visible four-to-six-week grid. ISO date strings
are stable keys. Ordering is chronological before CSS direction lays out the
row. Selection is singular. The unavailable set is copied, validated, bounded
to 4096 entries, and used as a membership set. There is no async work,
virtualization, remote data, or unbounded slot namespace.

## 14. Server render, morph, and cleanup

The server renders a useful native Date input plus hidden enhanced anatomy.
Activation builds weekday and day cells with DOM methods, subscribes to i18n,
registers Form/Field behavior, and marks the root enhanced only after the first
complete grid exists. Repeated initialization is idempotent.

A fragment inserted after a locale switch uses the provider's current locale
before exposing the custom grid. Morphs update fallback state without replacing
the component's canonical domain. Cleanup releases effects, i18n subscription,
listeners, Form/Field registration, and generated cells. Removal while focused
creates no global or overlay residue.

## 15. Security and content trust

Date strings and finite arrays are validated before use. Localized text is
written with `textContent` or safe attributes, never `innerHTML`. Generated
IDs derive from Citry identity. `attrs` is a trusted author escape path but
cannot replace roles, identity, Form state, i18n bindings, browser-expression
ownership, or runtime markers. Browser callbacks and submitted dates remain
untrusted application input.

## 16. Assets and performance

The family adds one component CSS block and one JavaScript block. It reuses the
shared Form runtime and i18n client already required by its catalog messages and
format profiles. It adds no third-party date library, font, icon request,
observer, timer, or global listener. One instance creates at most 42 date cells
and seven weekday headers. Work is bounded for a page move, locale change, or
prop update.

Acceptance records raw, gzip, and Brotli family/catalog deltas and checks 1,
10, and 100 instances for duplicate assets and bounded activation. The
implementation must remain within an explicitly reviewed catalog budget; a
budget increase must name the retained behavior that requires it.

## 17. Acceptance matrix

Automated evidence:

- exact server fallback HTML, package messages, bindings, IDs, Form/Field
  relationships, and owned-attribute rejection;
- all Python and client input validation, including impossible dates, bounds,
  duplicate/unbounded unavailable lists, and week-day range;
- pointer and every documented key in LTR and RTL;
- controlled/uncontrolled value and visible month, release, reset, callback
  details, native events, required invalid focus, Field/Form state, morph, and
  cleanup;
- locale-derived week starts, live locale switch, non-Gregorian calendar
  display, explicit week override, explicit string overrides, and a fragment
  inserted after switching;
- min/max disabled dates, focusable unavailable dates, adjacent-date selection,
  fixed/natural weeks, today, and year-boundary navigation;
- axe and structural accessibility checks in Chromium, Firefox, and WebKit;
- light/dark, RTL, narrow, zoom, touch, forced colors, reduced motion, print,
  and host styling scenarios;
- API YAML projection, examples, docs preview, exports, typing, source/wheel
  catalog consistency, installed wheel, CSP, and asset reports.

Manual release evidence still covers VoiceOver, NVDA, TalkBack, browser zoom,
mobile touch, non-Gregorian locales, and visual sign-off. The APG example warns
that code examples do not replace assistive-technology testing.

## 18. Compatibility classification

Stable public API includes the component name, documented server/client inputs,
callbacks, methods, canonical value and Form shape, translation keys, named
format profiles, public variables, part selectors, and reflected attributes.
Behavioral contract includes native fallback, enhanced roles, one tab stop,
keys, controlled semantics, locale switching, reset, and cleanup.

Exact spacing, colors, typography, arrow glyph markup, DOM classes, generated
cell implementation, and JavaScript organization are evolvable or private as
identified above.

## 19. Public documentation contract

Guide order: basic inline selection, canonical values and Forms, constraints
and unavailable dates, controlled value/month, keyboard and accessibility,
locales/calendars/week starts, no-JavaScript fallback, styling, and Calendar
versus DateInput/DatePicker/DateRange.

| Preview | Reader task | Interaction and contract coverage |
|---|---|---|
| Basic | select one date | pointer, keyboard, active day, today |
| Form | submit/reset a required date | Field, FormData, invalid focus, no-JS |
| Constraints | avoid blocked dates | min/max, unavailable, adjacent days |
| Controlled | own selection and month | both controlled channels and callbacks |
| Locales | switch locale and calendar | week start, headings, weekdays, RTL |
| States | compare disabled/readonly/invalid and sizes | visual and semantic states |
| Natural weeks | compare fixed and natural rows | layout behavior |
| Styling | change public variables | selectors, variables, host CSS |

The structured `api.yml` lists Inputs, Slots, Events, Methods, CSS,
Attributes, Selectors, Interfaces, and ends with the Translation keys table.

## 20. Open decisions and deferred work

No decision blocks implementation. Deferred work includes month/year selection
views, multiple months, custom day slots, week numbers, multiple selection,
presets, and arbitrary unavailable-date callbacks. DateRange owns range
preview and two-value ordering. DatePicker owns popup behavior.

The design is falsified if current supported browsers cannot expose a coherent
one-tab-stop grid while the native Date input remains the Form owner, if named
date profiles cannot keep Rust and browser formatting aligned, or if a locale
calendar cannot navigate months through bounded ISO-day scans. Any such result
reopens the adapter or server-rendered-grid choice before shipping.

## 21. Internationalization

Package-owned format profiles add a checked date field selection while keeping
`DateFormat(fields="year_month_day")` as the default. Calendar uses fixed
literal profiles for year, year-month heading, weekday short/full, day number,
and full date-with-weekday. Only `year_month_day` profiles may opt into parsing;
display-only field subsets cannot accidentally promise a parser.

The enhanced calendar is created in the browser, so the native Date input is
the complete source-locale server fallback. Component messages still render
its accessible names on the server. The i18n subscription formats the first
grid with the provider's effective current locale, including a late fragment,
and rebuilds every localized output on later locale changes. Canonical ISO
values, min/max comparison, unavailable membership, callbacks, and FormData do
not change with locale.

Source messages, declared as the final component class member:

```ftl
citry-ui-calendar-label = Calendar
citry-ui-calendar-previous-month = Previous month
citry-ui-calendar-next-month = Next month
```

The component does not interpolate application text into these messages. It
does not sort or search application content, parse localized input, or infer a
time zone for the selected domain date. The today marker uses the provider time
zone when one is explicit and the browser's local date otherwise.
