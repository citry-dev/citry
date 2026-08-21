# Citry UI TimeInput and TimePicker specification

**Status (2026-08-21): `CTimeInput` and `CTimePicker` runtime, public docs,
structured references, quality scenario, focused server tests, and
three-browser behavior/axe evidence complete; human visual, mobile, and
assistive-technology review remains.** This specification governs
the native-editing `CTimeInput` and finite-option popup `CTimePicker` family.
Both represent a wall-clock time without a date or time zone.

## 1. Purpose and product bar

`CTimeInput` styles the native HTML time input and preserves the browser's
localized editing, mobile keyboard, validation, and no-JavaScript behavior.
`CTimePicker` gives applications a consistent popup of bounded, localized
choices while submitting the same canonical `HH:MM` or `HH:MM:SS` value.

| Job | Shortest path | Classification |
|---|---|---|
| Enter a time with the platform editor | `<c-CTimeInput name="start" />` | direct native API |
| Pick one of regular appointment times | `<c-CTimePicker name="start" />` | direct popup API |
| Offer an irregular finite schedule | `CTimePicker(options=("09:10", "11:40"))` | direct API |
| Restrict the valid interval | `min="09:00" max="17:00"` | native/direct API |
| Label and validate | compose inside `CField` | composition |
| Submit a duration or instant | use a duration or date-time control | unsupported here |

Production completeness requires canonical Forms, exact bounds/step behavior,
controlled and uncontrolled state, reset and invalid focus, locale-sensitive
display, live switching, logical direction, no-JavaScript output, three-browser
tests, docs, structured reference, and bounded assets. Non-goals are duration
editing, dates, zones, DST resolution, free-form natural-language parsing,
milliseconds, and an analog clock face. There is no headless family.

## 2. Prior art and complaints

The source record was refreshed immediately before implementation.

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Vuetify | 4.1.11 source, 2026-08-20 | `VTimePicker`, controls, clock, validation, browser tests | Preserve canonical 24-hour values, hours/minutes/optional seconds, controlled value, bounds, allowed values, disabled/read-only, density and locale labels; reject an inaccessible bespoke dial as Citry's only path. |
| React Aria | 1.18/current docs, 2026-08-20 | TimeField anatomy, segments, value, formats, Forms | Separate direct editing from selection, localize display, keep a plain wall-clock value, and require explicit field labeling. |
| Vaadin Web Components | current docs/source notes, 2026-08-20 | Time Picker entry/list overlay, steps, bounds, validation, native Popover migration | Adopt a field plus finite list for the picker and keep direct entry as a separate native control. |
| HTML | Living Standard through MDN, 2026-08-20 | time state, periodic ranges, step, value/Form format | Canonical native value, seconds implied by precision, wrapped ranges, native validation, and no implicit ARIA role are normative. |
| WAI-ARIA APG | current, 2026-08-20 | spinbutton and listbox keyboard guidance | Do not rebuild native editing; use the existing tested Listbox for finite choices. |
| Complaint register | current, 2026-08-20 | React Aria tab-fatigue discussion; Vaadin iOS keyboard-overlay issue; React Spectrum millisecond request | Avoid mandatory multi-segment tab stops, preserve a native alternative, close overlays on mobile keyboard completion, and defer milliseconds. |

Citry adopts native input for open-ended editing and a composed Popover/Listbox
for bounded selection. It rejects an analog dial: APG defines no clock-dial
pattern, touch geometry adds significant code, and a list is more predictable
for keyboard and screen-reader users.

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `modelValue` | direct API | `value` / client `value` | adopt canonical string |
| `format=ampm|24hr` | locale profile | provider locale | replace manual default; no forced-cycle prop initially |
| `useSeconds` | native precision | seconds in value/bounds or non-minute step | adopt by inference |
| `min`, `max` | direct/native | same names | adopt, including wrapped intervals |
| allowed hours/minutes/seconds | finite composition | `options` | simplify to exact allowed times |
| `disabled`, `readonly` | direct/Field/Form | same states | adopt |
| `scrollable` clock | ordinary scrolling | Listbox viewport | replace |
| `variant=input|dial` | separate components | `CTimeInput`, `CTimePicker` | clearer ownership |
| title/actions slots | authored composition outside | `CField`, surrounding controls | omit |
| density/color/elevation | theme/CSS | `size`, `variant`, variables | replace prop breadth |
| hour/minute/second/view-mode events | one value request | `onValueChange` | simplify |

## 3. Public composition and anatomy

```html
<c-CField required>
  <c-fill name="label">Start time</c-fill>
  <c-fill name="default"><c-CTimePicker name="start" min="09:00" max="17:00" /></c-fill>
</c-CField>
```

Python composition is `CTimeInput(name="start", value=time(9, 30))` or
`CTimePicker(name="start", options=("09:00", "09:30"))`.

```text
CTimeInput: native input[type=time]

CTimePicker root
├─ clipped native input[type=time] (Form/no-JS transport)
├─ composed CPopover
│  ├─ full-width native Button activator + CIcon(clock)
│  └─ composed CListbox
│     └─ generated CListboxOption per checked canonical choice
└─ optional clear Button
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CTimeInput` | native time Input | input | Field label/description/error and Form owner |
| `CTimePicker` | state div | root; native attrs remain on transport | trigger controls Popover; Listbox has localized label |

The picker is one Field/Form control. Its child Listbox receives no Form name
and is isolated from the outer Field/Form context. `attrs` cannot replace
identity, native constraints, component directives, runtime markers, roles,
i18n bindings, or reflected state. Generated option anatomy is not a slot API.

## 4. Server inputs and client inputs

`CTimeInput` inputs are `value: time|str|None`, `name`, `form`, `id`, `min`,
`max`, `step: int=60`, nullable Field-owned `required/disabled/readonly/invalid`,
`autocomplete`, `variant`, `size`, `class_`, `style`, and `attrs`.

`CTimePicker` adds `options: Sequence[time|str]|None`, defaults `step=900`,
`clearable=True`, Popover `placement="bottom-start"`, `match_width=True`,
`dismissible=True`, `placeholder`, `picker_label`, `change_label`, `clear_label`,
and `unavailable_message`. Options are structural server data. Without options,
step must be an exact integer of at least 300 seconds and generation is capped
at 288 unique times. Explicit options must be unique, nonempty, and at most 288.

| Client input | Type | Omitted | `null` | Invalid | Affected surfaces |
|---|---|---|---|---|---|
| `value` | canonical string | uncontrolled | controlled empty | retain/report | native, trigger/list |
| `open` (picker) | boolean | uncontrolled | invalid | retain/report | Popover |
| min/max/step (input) | canonical/int | server fallback | clears nullable bound | retain/report | native validity |
| states | boolean | server/owner | invalid | retain/report | native/root |
| variant/size | enum | server | invalid | retain/report | styling |
| picker placement flags | existing Popover types | server | invalid unless nullable | retain/report | popup |
| callbacks | function | none | none | ignore/report | notifications |

Server output initializes state. A defined client `value` or picker `open`
controls that channel. Removal releases control to the last committed state.

## 5. State model

Canonical empty is `null` in callbacks and `""` in native controls. Native
input edits commit immediately unless controlled. Picker option activation
requests a value and closes only after an uncontrolled commit or after a
controlled owner reflects the request. Same-value requests are ignored.
Disabled blocks focus and change. Read-only remains submitted and inspectable
but blocks changes. Reset returns uncontrolled channels to server defaults;
controlled channels remain owner values. Invalid client configuration retains
the prior valid state and reports once per invalid episode.

## 6. Slots and slot data

Neither component exposes slots. Labels, descriptions, errors, prefix/suffix
content, presets, and action buttons compose through `CField` and surrounding
markup. This deliberately avoids forwarding the child Listbox's declaration
surface and avoids user content inside generated options.

## 7. Callbacks, native events, and methods

`onValueChange(next, detail)` uses `value`, `previousValue`, `controlled`,
`source` (`native`, `option`, `clear`, `reset`), and `sourceEvent`. Picker
`onOpenChange(next, detail)` follows `CPopoverOpenChangeDetail`. Native
`input`/`change` bubble from the public transport when an uncontrolled commit
occurs. There are no custom DOM events or public methods.

## 8. Semantics, keyboard, focus, and assistive technology

`CTimeInput` relies on the native control. Picker Tab reaches the activator and
optional clear button. Enter/Space/ArrowDown opens; focus enters the selected
or first Listbox option. Existing Listbox Arrow/Home/End/typeahead behavior
applies. Enter/Space selects. Escape/outside interaction restores the trigger.
The trigger name is “Choose time” when empty and “Change time, {time}” when set.
The popup and Listbox share the localized picker label. No unsupported
`aria-required` or `aria-readonly` is placed on the Button.

## 9. Native forms and validation

Both submit one canonical time string. Native input supports `required`,
periodic min/max, step mismatch, reset, external `form`, fieldset disabling,
read-only submission, and ordinary input/change events. Picker keeps a real
time input in the no-JavaScript path and as enhanced transport. Explicit
options add checked custom validity for a value no longer present. Invalid
submission focuses the native input without enhancement and opens/focuses the
visible picker route after enhancement. Citry Events sees ordinary FormData.

## 10. Styling and theme contract

Both expose `outline`, `filled`, `plain` and `sm`, `md`, `lg`. Stable variables
use the component prefix for background, foreground, border, hover border,
focus, invalid border, disabled background, radius, height, padding, font size,
and minimum inline size. Picker additionally exposes popup/list maximum block
size and clear-control size. Stable selectors/parts are root/control/value,
fallback-input, enhanced-control, clear; TimeInput exposes `time-input`.
Reflected states are required, disabled, readonly, invalid, empty, open,
variant, size, enhanced. Child component selectors remain owned by their
families.

## 11. Environmental behavior

Logical properties and existing Popover placement handle RTL. Time digits and
day periods come from the locale formatter; canonical values never change.
Light/dark, nested color schemes, forced colors, reduced motion, narrow/touch,
400% zoom, long localized labels, and print are covered. Native input keeps the
mobile platform editor. Picker options update through one parent i18n
subscription because their labels are generated; stable title/clear labels use
`$c-tr`. Application overrides never register catalog bindings.

## 12. Overlay and layering behavior

Only `CTimePicker` opens an overlay. It composes non-modal `CPopover`, inherits
its logical ownership across teleports, collision handling, Escape/outside
closure, focus restoration, nesting, animation, and cleanup. It does not lock
scroll or make the background inert.

## 13. Async, loading, empty, and error behavior

The family is synchronous and finite. Explicit empty `options` is an error;
runtime structural loss fails closed. There is no loading API. Invalid reactive
values retain prior checked state and report without partially rewriting the
control.

## 14. Server rerender, fragments, morphing, and cleanup

Canonical value, open state, active option, focus, and composition ownership
must survive compatible morphs by public identity. Structural option changes
come from a server rerender. Locale fragments register beneath their logical
provider before activation. Every listener, effect, reset entry, observer,
Popover callback, i18n subscription, and generated binding is released.

## 15. Security and trust boundaries

Times and arrays are strictly bounded and validated. Labels use `textContent`;
no catalog or application string reaches `innerHTML`. Attribute filtering
blocks executable, owned, and runtime attributes. IDs are Citry-derived.
Callbacks and Form values remain untrusted application input.

## 16. Assets and performance

`CTimeInput` adds one small component JS/CSS block over the shared Form runtime.
`CTimePicker` adds a parent block and composes deduplicated Popover, Listbox,
Icon, anchored-layer, Form, and i18n assets. At most 288 options render. There
is no temporal library, network request, global listener, or unbounded scan.
Record raw/gzip/Brotli deltas and 1/10/100-instance activation.

## 17. Acceptance matrix

Automated evidence covers canonical values including seconds, time objects,
periodic ranges, step/options, every validation error, Field/Form ownership,
no-JS, controlled/uncontrolled state, reset, native events, invalid focus,
Popover/Listbox keyboard and pointer selection, localization and live switch,
RTL, cleanup, CSP, docs/API projection, assets, installed wheel, and axe in
Chromium/Firefox/WebKit. Manual evidence covers major screen readers, mobile
native editors, touch scrolling, zoom, and locale/day-period review.

## 18. Compatibility classification

Stable API includes names, inputs, callback records, canonical Form shape,
translation keys, profile names, public variables/selectors/attributes, and
validation errors. Browser-native editor appearance and exact theme values are
not stable. Child private wrappers, generated option IDs, scope names, and JS
organization are private.

## 19. Public documentation contract

Each component owns a README, reader guide, exhaustive `api.yml`, snippets,
and quality fixture. Previews cover basic, Form, constraints/steps, explicit
options, states, controlled behavior, locales/seconds/RTL, and styling. Every
API reference ends with a structured Translation keys section; TimeInput has
an explicit empty table because it authors no text.

## 20. Open decisions and deferred work

No choice blocks implementation. Deferred work includes segmented localized
editing, a separately researched analog clock, milliseconds, durations,
date-time composition, zones, presets, async option sources, and forced hour
cycle. The design is falsified if composed Listbox control cannot settle
without duplicate requests or if current-locale option labels cannot update
without replacing focused option nodes.

## 21. Internationalization

Profiles `citry-ui-time-picker-display` (short) and
`citry-ui-time-picker-display-seconds` (medium) format plain wall-clock fields.
Messages are placeholder, picker label, change label with typed `time: str`,
clear label, and unavailable validity. Source-locale English works without root
i18n configuration. Cross-component source lookup applies. Stable title/clear
destinations use `$c-tr`; dynamic trigger, option labels, and custom validity
use the parent's provider subscription or `i18n.bind()`. `CTimeInput` authors no
visible or accessibility text and relies on browser locale plus application
labeling. Both preserve bidi isolation supplied by the formatter/message layer.
