# Citry UI DatePicker specification

**Status (2026-08-20): runtime, public docs, structured reference, focused
server tests, and three-browser behavior/axe evidence complete; integrated
asset and installed-wheel qualification remains part of the final family
batch.** This specification governs one styled
`CDatePicker` that selects a single calendar date from an anchored popup.
`CDateInput` owns direct native editing, `CCalendar` owns inline selection, and
`CDateRange` owns two-ended ranges.

## 1. Purpose and product bar

`CDatePicker` gives a person one field-like control that opens a localized
Calendar, selects one date, closes, and submits a canonical Gregorian
`YYYY-MM-DD` value. It is for applications that need a consistent Citry-owned
calendar instead of the platform picker but do not need localized free-form or
segmented date typing.

| Job | Shortest path | Classification |
|---|---|---|
| Pick one date from a popup | `<c-CDatePicker name="arrival" />` | direct API |
| Label, describe, and validate it | place it inside `CField` | composition |
| Set value and bounds | `value=... min=... max=...` | direct API |
| Exclude known dates | `unavailable_dates=(...)` | direct finite constraint |
| Require a choice | `required` | native Form validation |
| Control value or open state | `$c-props="{value,open}"` | client API |
| Observe requests | `onValueChange`, `onOpenChange` | client callbacks |
| Type or use the platform picker | `CDateInput` | separate component |
| Show the calendar permanently | `CCalendar` | separate component |

Production completeness requires the complete Calendar and Popover contracts,
one coherent Form owner, useful no-JavaScript output, controlled and
uncontrolled value/open state, focus entry and restoration, exact locale
switching, Field/Form integration, three-browser evidence, docs, structured
reference, and installed-wheel evidence.

Non-goals are localized text parsing, segmented entry, range or multiple
selection, month/year selection views, multi-month panels, presets,
confirmation actions, arbitrary unavailable-date callbacks, and a headless
family.

## 2. Prior art and complaints

Current component-specific evidence was refreshed before implementation.
Vuetify carries the greatest styled-suite weight; the standards and accessibility
sources remain acceptance requirements.

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Vuetify | 4.1.6, reviewed 2026-08-20 | `VDateInput.tsx` and browser tests | Compose a field, menu, Calendar, and controlled proxy; close immediately for one-date selection. |
| React Aria Components | current, reviewed 2026-08-20 | DatePicker docs and `DatePicker.tsx` | Keep DateField, Button, Popover/Dialog, Calendar, validation, and hidden Form transport as explicit jobs. |
| Ark UI | current, reviewed 2026-08-20 | DatePicker docs, root props, basic and DateInput-composition examples | Keep trigger/content/calendar anatomy and controlled value/open channels; do not copy range and view-selection breadth. |
| WAI-ARIA APG | current, reviewed 2026-08-20 | Date Picker Dialog example | Focus the selected date or today, close on selection/Escape, restore trigger focus, and include the chosen date in the trigger name. |
| HTML | Living Standard, reviewed 2026-08-20 | Date state, Form association, Popover API | Retain a native Date input for canonical Form/reset/validity and no-JavaScript use; use the existing manual Popover owner. |
| Vaadin Web Components | current, reviewed 2026-08-20 | `vaadin-date-picker.js` | Treat opened/value/invalid as separate states and restore the input/trigger after overlay close. |
| React Spectrum complaint | issue 7006, reviewed 2026-08-20 | request to open on field focus because a small trigger is missed | Make the entire visible field-like Button the activator, not a small detached icon. |
| Vaadin complaints | issues 12398 and 12341, reviewed 2026-08-20 | iOS VoiceOver grid navigation and overlay scrolling reports | Keep the proved Calendar grid, avoid offscreen month stacks, and test mobile screen readers and scroll behavior manually. |
| Vuetify complaint | issue 20580, reviewed 2026-08-20 | mobile keyboard obscuring the calendar | Do not summon a text keyboard: the enhanced activator is a Button and this family does not parse text. |

Citry adopts composition, a full-control activator, immediate single-date
selection, a canonical transport, and separate controlled value/open state. It
rejects editable localized text in this family because an incomplete parser
would let the displayed draft and submitted ISO value disagree. `CDateInput`
remains the concise editable/native path.

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `modelValue` | direct controlled state | `value`, client `value`, `onValueChange` | adopt |
| `displayFormat` | package-owned locale profile | `citry-ui-date-picker-display` | adopt without per-instance callback |
| editable typed input and `updateOn` | separate component | `CDateInput` | omit here |
| menu/model/menu props | focused direct API | `open`, `placement`, `match_width`, `dismissible` | adopt bounded subset |
| picker props | direct Calendar inputs | min/max, unavailable dates, week/layout inputs | adopt proved subset |
| range/multiple | separate family | `CDateRange` | omit |
| confirmation actions | immediate single-date selection | none | omit |
| clearable field | direct optional action | `clearable` | adopt |
| prepend/append/details slots | Field and CSS composition | `CField`, `class_`, `style`, `attrs` | capability without slot parity |

## 3. Public composition and anatomy

Smallest use:

```citry-html
<c-CDatePicker name="arrival" />
```

Python composition is `CDatePicker(name="arrival", value=date(2026, 8, 19))`.

```text
DatePicker root (div)
├─ native Date input (no-JS control and enhanced Form transport)
└─ composed CPopover
   ├─ activator: one field-like native Button
   │  ├─ localized value or placeholder
   │  ├─ optional clear Button beside, not inside, the activator
   │  └─ calendar icon
   └─ surface
      ├─ localized title
      └─ composed CCalendar without a Form name
```

`class_`, `style`, and `attrs` land on the DatePicker root. The public control
ID belongs to the native input without JavaScript and to the visible activator
after enhancement; private IDs keep both nodes distinct. The nested Calendar
is a real `CCalendar`; the popup is a real `CPopover`. Their private wrappers
and classes are not DatePicker API.

No slots are added. The focused API avoids exposing partial replacement points
that could break the native Button, dialog name, Calendar grid, or Form owner.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `value` | `date | str | None` | `None` | initial state | exact date or canonical ISO |
| `name`, `form`, `id` | `str | None` | `None`/generated | Form/identity | non-empty name and valid IDs |
| `min`, `max` | `date | str | None` | `None` | reactive constraint | canonical and ordered |
| `unavailable_dates` | sequence of date/string | `()` | reactive constraint | unique, finite, at most 4096 |
| `required`, `disabled`, `readonly`, `invalid` | `bool | None` | `None` | Field/Form state | exact optional Booleans |
| `clearable` | `bool` | `True` | reactive configuration | clear action only when optional and non-empty |
| `dismissible` | `bool` | `True` | reactive overlay configuration | controls passive close |
| `placement` | `CPopoverPlacement` | `"bottom-start"` | reactive presentation | six logical placements |
| `match_width` | `bool` | `True` | reactive presentation | popup at least activator width |
| `first_day_of_week` | `int | None` | `None` | reactive Calendar configuration | ISO 1–7 or locale default |
| `show_adjacent_days`, `fixed_weeks` | `bool` | `True` | reactive Calendar configuration | forwards to Calendar |
| `variant` | `outline | filled | plain` | `outline` | reactive presentation | reflected root styling |
| `size` | `sm | md | lg` | `md` | reactive presentation | reflected root sizing |
| `placeholder`, `picker_label`, `clear_label` | `str` | catalog defaults | server/browser text | non-empty; explicit values suppress bindings |
| `class_`, `style`, `attrs` | structured values/mapping | `None` | server presentation | merge on validated root |

| Client input | Type | Omitted | `null` | Invalid | Effect |
|---|---|---|---|---|---|
| `value` | canonical string | uncontrolled | controlled empty | diagnostic; keep prior valid state | selected/Form value |
| `open` | Boolean | uncontrolled | release control | diagnostic; release from current state | popup visibility |
| all server reactive configuration in camelCase | matching server type | server fallback | server fallback except nullable date fields | diagnostic; retain prior valid value | both composed children and root |
| `onValueChange` | function | none | none | diagnostic; ignore | value requests |
| `onOpenChange` | function | none | none | diagnostic; ignore | open/close requests |

Python supplies the initial fallback. Valid client props take precedence after
activation. Prop removal releases to current uncontrolled state for `value`
and `open`; configuration returns to the current server fallback.

## 5. State model

`value` and `open` are independently controlled. A DatePicker may be controlled
in neither, either, or both channels.

| Transition | Guard | Uncontrolled commit | Controlled request |
|---|---|---|---|
| trigger activation | not disabled | toggle open | call `onOpenChange` |
| Calendar selection | not disabled/read-only/unavailable | set value, dispatch native input/change, close | call `onValueChange`; request close |
| clear | clearable, optional, non-empty, enabled, writable | clear, dispatch native input/change | request null |
| Escape/outside/focus-outside | dismissible and open | close | `onOpenChange(false, ...)` |
| Form reset | reset event not cancelled | restore initial value and close | request initial value and close |
| external prop change | valid | synchronize display, transport, Calendar, and popup | owner commit; no callback |

Repeated same-value requests do nothing. Disabled prevents every action and
Form submission. Read-only permits inspection/opening and Calendar navigation
but not selection or clearing. Invalid is an application state; native
constraint invalidity is tracked independently and merged visually.

## 6. Slots and slot data

There are no public slots. `CField` supplies label, description, and error
composition outside the DatePicker. Calendar-day replacement, icon slots,
action rows, presets, and custom popup content are deferred until their
semantics and interaction contracts justify them.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onValueChange` | `(str | null, CDatePickerValueChangeDetail)` | Calendar, clear, reset | after uncontrolled commit, before native events | request only | callback return ignored |
| `onOpenChange` | `(bool, CDatePickerOpenChangeDetail)` | trigger, selection, clear, Escape/outside/focus, reset, forced layer close | after uncontrolled commit | request only except forced safety close | callback return ignored |

Value detail includes `value`, `previousValue`, `controlled`, `source`, and
`sourceEvent`. Open detail follows `CPopoverOpenChangeDetail` and adds
`"selection"`, `"clear"`, and `"reset"` reasons where DatePicker initiates the
close. Native `input`, `change`, `invalid`, `focus`, and `blur` remain ordinary
Alpine listeners on the component roots. No custom DOM event and no public
imperative method are added.

## 8. Semantics, keyboard, focus, and assistive technology

Without JavaScript, the native Date input owns semantics and keys. After
enhancement, the full field-like native Button has `aria-haspopup="dialog"`,
`aria-expanded`, `aria-controls`, the Field label relationship, description,
error relationship, and an accessible name containing the current localized
date when non-empty. The visible text is the same localized date or localized
placeholder.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| trigger | Enter/Space/click | request open toggle | selected date, today, or first allowed Calendar cell | native Button activation |
| popup | Calendar keys | Calendar contract | roving grid focus | per Calendar |
| popup | Enter/Space on day | request value then close | trigger after close | per Calendar |
| open route | Escape | request close | trigger | yes |
| document | outside/focus outside | request close | outside target remains; no forced trigger restoration | no |
| clear control | Enter/Space/click | request empty value | clear control or trigger if it disappears | native Button activation |
| Tab/Shift+Tab | ordinary order | traverse trigger, optional clear, then popup when open | ordinary next/previous target | no |

The dialog is named by `picker_label`; the inner Calendar keeps its own
localized group name and live month heading. The trigger name changes from the
generic picker label to “Change date, {date}” when selected. Manual VoiceOver,
NVDA, and TalkBack evidence remains a release requirement because current
issue reports show grid/overlay combinations can still fail despite valid
ARIA.

## 9. Native forms and validation

One native `<input type="date">` is the Form owner in both modes. It carries
`name`, `form`, value, min/max, required, disabled, and reset baseline. The
enhanced control keeps it visually hidden but connected and validatable.
Read-only removes it from successful controls through the same Citry UI
read-only Form convention while retaining a hidden canonical value when a
name exists. Disabled submits nothing.

Required/min/max/unavailable validity is reflected on the visible control and
into `CField`. Invalid submission opens the popup and focuses the Calendar or
visible trigger; it never strands focus on the clipped transport. Native
`input` then `change` fire only for uncontrolled user commits. A controlled
owner decides whether to update its own native/application state.

No JavaScript leaves a fully usable native Date input. Citry Events and normal
Form submission see the same canonical value.

## 10. Styling and theme contract

Variants are `outline`, `filled`, and `plain`; sizes are `sm`, `md`, and `lg`.
The Calendar and Popover retain their own public variables. DatePicker adds:

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-date-picker-background` | color | visible control background | variant-derived Canvas |
| `--cui-date-picker-foreground` | color | text/icon color | CanvasText |
| `--cui-date-picker-border-color` | color | control boundary | CanvasText mix |
| `--cui-date-picker-invalid-border-color` | color | invalid boundary | scheme-aware red |
| `--cui-date-picker-focus-color` | color | focus ring | Highlight |
| `--cui-date-picker-radius` | length | control radius | `.625rem` |
| `--cui-date-picker-min-block-size` | length | control height | size-derived |
| `--cui-date-picker-padding-inline` | length | inline padding | `.75rem` |
| `--cui-date-picker-gap` | length | content gap | `.5rem` |

Stable selectors are the root, fallback input, control, value, icon, clear,
and popup Calendar `data-citry-ui-part` elements. Reflected root attributes are
`data-empty`, `data-open`, `data-required`, `data-disabled`, `data-readonly`,
`data-invalid`, `data-variant`, `data-size`, and `data-enhanced`.

## 11. Environmental behavior

Light/dark and nested color schemes use Canvas colors. Logical layout and the
existing Calendar/Popover contracts support RTL. Reduced motion is inherited
by Popover and Calendar. Forced colors retains visible Button, selected day,
invalid, and focus boundaries. At 400% zoom the popup fits the viewport and
the control wraps/truncates without page overflow. Coarse pointers retain at
least 44 CSS-pixel control/day targets. No virtual keyboard opens. Print shows
the localized selected value and hides trigger-only icon/action affordances.

| Output | Initial owner | Browser update |
|---|---|---|
| empty placeholder | server `tr()` | `$c-tr` text binding |
| popup title | server `tr()` | `$c-tr` text binding |
| clear accessible name | server `tr()` | `$c-tr` attribute binding |
| selected display and trigger name | named date profiles and messages | i18n subscription plus `i18n.tr()`/`format.date()` |
| Calendar strings/grid | `CCalendar` | Calendar's existing bindings/subscription |

Canonical values, comparisons, callbacks, and FormData never change with
locale. Explicit text overrides emit no catalog binding.

## 12. Overlay and layering behavior

The popup is a real non-modal `CPopover` anchored to the visible Button. It
uses native top layer without teleporting, preserves theme/Field ownership,
supports six logical placements and collision repair, restores focus after
selection/Escape, and follows the shared nested-layer coordinator. It does not
trap focus, lock scroll, or make the page inert. Dismissal, forced ancestor or
modal closure, animation generations, and cleanup remain `CPopover` behavior.

## 13. Collections, async data, and identity

The only collection is the nested finite Calendar grid. ISO dates are stable
keys; Calendar owns ordering, focus, selected/unavailable state, and bounded
cell creation. DatePicker adds no async work, remote collection, virtualization,
or dynamic slot namespace.

## 14. Server render, morph, and cleanup

Server output exposes the native Date input and keeps the inert Popover
composition hidden. Parent initialization wires client scope before composed
children consume `$c-props`; only after the first synchronized display is
ready does it mark the root enhanced and reveal the custom control.

A retained morph preserves valid uncontrolled value/open state when the
corresponding server baselines are unchanged, while fresh server inputs become
new fallbacks. An open overlay closes safely if replacement invalidates its
owner. Cleanup releases Form/reset/fieldset listeners, i18n subscription,
composed callbacks, and any retained handoff. A fragment inserted after locale
switch formats its first exposed display in the provider's current locale.

## 15. Security and content trust

Date inputs and arrays are strictly validated. Localized and authored strings
use `textContent` or safe attributes, never `innerHTML`. `attrs` is trusted
author configuration but cannot replace identity, Form state, roles, i18n
bindings, component ownership directives, runtime markers, Popover linkage, or
reflected state. Generated IDs derive from Citry identity. Callback and Form
values remain untrusted application input.

## 16. Assets and performance

DatePicker adds one small parent CSS/JavaScript block plus the existing
deduplicated Form runtime, `CPopover`, `CCalendar`, `CIcon`, anchored-layer
runtime, and i18n artifacts. It adds no date library, font, observer, global
listener, or network request. Per-instance parent work is constant; Calendar
retains its 42-cell bound. Record raw/gzip/Brotli family and catalog deltas and
activation for 1, 10, and 100 instances.

## 17. Acceptance matrix

Automated evidence covers exact server fallback, composition, messages,
profiles, bindings, IDs, Field/Form relationships, owned-attribute rejection,
all input validation, controlled/uncontrolled value/open state, clear/reset,
callback details, native events, required invalid focus, every dismissal path,
Calendar pointer/keyboard behavior, min/max/unavailable dates, live locale and
calendar switch, RTL, late fragments, morph/removal cleanup, axe in Chromium/
Firefox/WebKit, narrow/zoom/touch/forced-colors/reduced-motion/print scenarios,
docs examples, API projection, exports, typing, asset report, CSP, and installed
wheel.

Manual release evidence covers screen readers on desktop/mobile, browser zoom,
touch scrolling and safe areas, virtual-keyboard absence, non-Gregorian
calendars, and visual sign-off.

## 18. Compatibility classification

Stable API includes the component name, inputs, callbacks/detail fields,
canonical Form shape, translation keys, profile names, variables, selectors,
reflected attributes, and validation errors. Behavioral contract includes the
native fallback, composed Calendar/Popover behavior, focus, controlled state,
locale switching, reset, and cleanup. Exact theme values and incidental
wrappers may evolve. Private classes, private IDs/variables, parent-to-child
scope names, and JavaScript organization are private.

## 19. Public documentation contract

Guide order: basic selection, DatePicker versus DateInput/Calendar, Forms and
canonical values, constraints, clearing and states, controlled value/open,
keyboard/focus/accessibility, locale switching, no-JavaScript fallback,
styling, and environmental behavior.

| Preview | Reader task | Contract coverage |
|---|---|---|
| Basic | choose an arrival date | trigger, popup, selection, close |
| Form | submit/reset a required date | Field, FormData, invalid focus, no-JS |
| Constraints | avoid unavailable dates | min/max, unavailable, adjacent dates |
| Clear and states | clear and compare state variants | optional/required, disabled/read-only/invalid |
| Controlled | own value and open | both channels, refusal/acceptance, callbacks |
| Locales | switch locale/calendar/direction | display, trigger name, Calendar, RTL |
| Placement | compare logical placement/width | Popover composition and narrow viewport |
| Styling | customize public variables | variants, sizes, root/part selectors |

`api.yml` contains Inputs, Slots, Events, Methods, CSS, Attributes, Selectors,
Interfaces, and ends with Translation keys.

## 20. Open decisions and deferred work

No choice blocks implementation. Localized typed input remains deliberately in
`CDateInput`/future segmented editing rather than being approximated here.
Deferred work includes range/multiple dates, presets, action confirmation,
custom day rendering, month/year views, multi-month panels, and arbitrary
unavailable-date callbacks.

The design is falsified if composed `$c-props` cannot initialize before child
activation, if the clipped native transport cannot redirect invalid focus to
the visible route, or if an open controlled Popover and controlled Calendar
cannot settle without duplicate callbacks. Those results reopen composition
or require a documented shared-foundation change before shipping.

## 21. Internationalization

Named profile `citry-ui-date-picker-display` formats the selected date for
visible text. The trigger name uses the same formatted output as a typed
variable in `citry-ui-date-picker-change`; it never interpolates the canonical
ISO value. Locale changes recompute both while retaining selection and Form
value. The nested Calendar owns its established six profiles and four keys.

Source messages are final in the class:

```ftl
citry-ui-date-picker-placeholder = Choose a date
citry-ui-date-picker-label = Choose date
citry-ui-date-picker-change = Change date, { $date }
citry-ui-date-picker-clear = Clear date
citry-ui-date-picker-unavailable = Choose an available date.
```

The unavailable message is written to the native transport with `i18n.bind()`.
Stable placeholder, title, and clear outputs use `$c-tr`; selected display and
name are recomputed by the i18n subscription because they combine a format
profile and a message variable. Explicit overrides bind neither the relevant
message nor its browser updates. Application labels/descriptions remain owned
by `CField` and the active provider around that content.
