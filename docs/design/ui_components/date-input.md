# Citry UI DateInput specification

**Status (2026-08-19): implemented and focused automation complete.** This specification
governs one styled `CDateInput` whose semantic root is the native
`<input type="date">`. `CCalendar`, `CDatePicker`, time entry, and date ranges
remain separate families with their own research and acceptance contracts.

## 1. Purpose and product bar

`CDateInput` lets an application collect one calendar date without a time or
time zone. It preserves native keyboard entry, touch and desktop picker UI,
autofill, form submission, reset, constraint validation, and assistive-
technology behavior. Its public value is a Python `date` or canonical ISO
string on the server and a canonical `YYYY-MM-DD` string in the browser.

Common jobs and shortest support paths:

| Job | Shortest template or Python call | Support path |
|---|---|---|
| Collect one date | `<c-CDateInput name="arrival" />` | direct API |
| Label and describe it | place it in `CField` | composition |
| Set an initial date | `value="2026-08-19"` or `value=date(...)` | direct API |
| Constrain the date | `min="2026-01-01" max="2026-12-31"` | native attributes through direct API |
| Require a value | `required` | native validation |
| Submit a canonical value | `name="arrival"` | native Form behavior |
| Control it in Alpine | `$c-props="{ value: arrival }"` | client input |
| Observe editing | `@input` or `@change` | native events |
| Ask the browser to open its picker | an input `x-ref` and `showPicker()` | native method |
| Change presentation | `variant="filled" size="lg"` | direct API |

Production completeness means exact date validation, native Form and Field
integration, controlled and uncontrolled values, no-JavaScript usefulness,
light/dark and forced-color styling, narrow and touch behavior, public docs,
structured reference, three-browser evidence, and honest documentation of
browser-owned picker appearance and locale behavior.

Non-goals:

- localized free-form text parsing or a custom segmented editor;
- a custom calendar, popup, dialog, or focus scope;
- date ranges, multiple dates, weeks, months, years, or date-time values;
- unavailable-date callbacks beyond native `min`, `max`, and `step`;
- component callbacks or custom DOM events that duplicate native events;
- a wrapper method for `focus()` or `showPicker()`; and
- a headless variant.

## 2. Prior art and complaints

The shared taxonomy reports calendar/date/time controls in 8/12 ecosystem
work units. The current i18n design explicitly permits native temporal
controls, segmented adapters, or server validation rather than waiting for a
generic browser temporal parser.

Current-source record:

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| HTML Standard | Living Standard, reviewed 2026-08-19 | [Date state](https://html.spec.whatwg.org/multipage/input.html#date-state-(type=date)), value sanitization, `min`, `max`, `step`, validation, reset, and picker behavior | Keep a native Date input and canonical date string as the source of truth. |
| MDN | updated 2026-06-09, reviewed 2026-08-19 | [`input type="date"`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/date) | Native UI varies, displayed spelling follows the browser locale, submitted value stays `YYYY-MM-DD`, and server validation remains required. |
| Vuetify | 4.1.6 source reviewed 2026-08-19 | [`VDateInput.tsx`](https://github.com/vuetifyjs/vuetify/blob/v4.1.6/packages/vuetify/src/components/VDateInput/VDateInput.tsx), [`VDatePicker.tsx`](https://github.com/vuetifyjs/vuetify/blob/v4.1.6/packages/vuetify/src/components/VDatePicker/VDatePicker.tsx), and Date adapter source | Use Vuetify as the main styled-suite reference. Split its text field, menu, calendar, range, and confirmation jobs across focused Citry families. |
| React Aria | current docs and `useDateField` 3.50.0 reviewed 2026-08-19 | [DateField](https://react-aria.adobe.com/DateField), [DatePicker](https://react-aria.adobe.com/DatePicker), and [`useDateField`](https://react-aria.adobe.com/DateField/useDateField) | Segmented editing and multi-calendar conversion are a substantial separate adapter. Preserve ISO Form values and reserve that richer job instead of approximating it. |
| Material UI X | current docs reviewed 2026-08-19 | [Fields](https://mui.com/x/react-date-pickers/fields/), [Date Picker](https://mui.com/x/react-date-pickers/date-picker/), [accessibility](https://mui.com/x/react-date-pickers/accessibility/) | Keep field and calendar jobs separable. Do not add a hidden-input/ARIA-section editor without its full keyboard and focus contract. |
| Ark UI | current docs reviewed 2026-08-19 | [Date Picker](https://ark-ui.com/docs/components/date-picker) | Calendar input, range, multiple selection, presets, multiple months, unavailable dates, and inline mode belong to later Calendar/Picker families. |
| Vaadin | current Flow and Web Component docs reviewed 2026-08-19 | [Date Picker](https://vaadin.com/docs/latest/components/date-picker) and [date formats](https://vaadin.com/docs/latest/components/date-picker/date-formats) | A server framework can use bounded client parsing or a server parser, but the field and submitted canonical value must never silently disagree. |
| WAI-ARIA APG | current example reviewed 2026-08-19 | [Date picker dialog example](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/examples/datepicker-dialog/) | Treat a custom calendar dialog as its own high-risk family; native DateInput needs no reconstructed ARIA role. |
| PrimeVue issue 7545 | PrimeVue 4.3.3, open when repository was archived, reviewed 2026-08-19 | [manual input and Form mismatch](https://github.com/primefaces/primevue/issues/7545) | Never let displayed partial text, selected date, and submitted Form value drift into different representations. |
| Vuetify issue 20217 | Vuetify 3.6.13, closed, reviewed 2026-08-19 | [formatted string model broke calendar state](https://github.com/vuetifyjs/vuetify/issues/20217) | Accept one canonical public representation; reject locale-formatted strings passed as domain values. |

Patterns adopted:

- one native date input as the semantic, editing, validation, and submission
  owner;
- canonical ISO values across Python, DOM, Alpine, native events, and FormData;
- direct `min`, `max`, `step`, state, variant, size, and trusted attributes;
- native `input`, `change`, `invalid`, focus, reset, autofill, and picker
  behavior; and
- a separate custom Calendar and DatePicker contract.

Patterns rejected here:

- localized strings as model values;
- a second hidden submitted value beside a differently owned visible value;
- custom segment roles without a complete segment adapter;
- custom overlay, confirmation, presets, ranges, multiple dates, or events;
  and
- hiding the browser picker indicator and replacing only its icon.

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `model-value` | direct/client API | `value` | canonical `date`/ISO only; no locale-formatted model |
| formatted text input and `display-format` | native behavior or later component | browser-owned display; later segmented field | omit custom parsing from this family |
| `min`, `max`, allowed range | direct/native API | `min`, `max`, `step` | adopt the native finite constraints |
| `allowed-dates`, allowed months/years | separate component | future `CCalendar`/`CDatePicker` | omit arbitrary calendar predicates |
| `multiple`, numeric maximum, and `range` | separate component | DateRange or later multiple-date family | omit |
| menu, `menu-props`, location, open state | separate component | future `CDatePicker` | omit |
| DatePicker title/header/day/month/year/actions slots | separate component | future Calendar/DatePicker slots | omit |
| save, cancel, menu, preview, month/year callbacks | native events or separate component | `input`/`change`; future Calendar callbacks | no duplicate callbacks |
| `update-on` blur/enter parsing | native behavior | browser date editing | omit custom commit policy |
| disabled, readonly, required, error | direct/native and Field/Form composition | matching state inputs | adopt |
| clearable, prefix/suffix, messages | native empty edit or composition | native edit; `CField`; ordinary layout | no internal action anatomy |
| density, variant, class, style | direct/CSS | `size`, `variant`, `class_`, `style`, variables | adopt suite vocabulary |
| focus and picker methods | native ref | `focus()`, `showPicker()` where supported | no wrapper methods |

## 3. Public composition and anatomy

Template composition:

```html
<c-CField control_id="arrival" required>
  <c-fill name="label">Arrival date</c-fill>
  <c-CDateInput
    name="arrival"
    min="2026-08-19"
    max="2027-08-19"
  />
  <c-fill name="description">Choose a date in the next year.</c-fill>
</c-CField>
```

Python composition:

```python
CField(
    control_id="arrival",
    required=True,
    slots={
        "label": "Arrival date",
        "default": CDateInput(
            name="arrival",
            min=date(2026, 8, 19),
            max=date(2027, 8, 19),
        ),
    },
)
```

Anatomy:

```text
CField, optional
└── input.cui-date-input[type="date"]
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CDateInput` | one native `<input type="date">` | `attrs`, `class_`, and `style` merge on that input | at most one surrounding `CField`; native Form owner may be explicit |

No wrapper, indicator, hidden transport, dialog, or calendar is public or
rendered. The browser owns internal shadow/UI anatomy. Consumer attributes
cannot replace the component-owned type, identity, value, constraints, Field
relationships, state mirrors, or initialization marker.

The post-implementation anatomy review must retain the one-element contract.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `value` | `date | str | None` | `None` | initial/reset value | exact Python `date` or canonical real `YYYY-MM-DD`; `datetime` and formatted strings are rejected |
| `name` | `str | None` | `None` | native Form configuration | nonempty when supplied |
| `form` | `str | None` | enclosing Form or `None` | native Form configuration | valid HTML ID; cannot escape an enclosing `CForm` |
| `id` | `str | None` | Field ID or generated | identity | valid HTML ID and must agree with Field ownership |
| `min` | `date | str | None` | `None` | reactive constraint fallback | canonical real date; must not exceed `max` |
| `max` | `date | str | None` | `None` | reactive constraint fallback | canonical real date; must not precede `min` |
| `step` | `int` | `1` | reactive constraint fallback | exact positive integer number of days |
| `required` | `bool | None` | Field value or `False` | reactive state fallback | Field-owned when composed; native constraint |
| `disabled` | `bool | None` | Field/Form value or `False` | reactive state fallback | Field-owned when composed; disabled Form wins |
| `readonly` | `bool | None` | Field/Form value or `False` | reactive state fallback | Field-owned when composed |
| `invalid` | `bool | None` | Field value or `False` | reactive state fallback | Field-owned when composed; combines with native invalidity |
| `autocomplete` | `str | None` | `None` | native configuration | forwards a plain autofill token such as `bday` |
| `variant` | `Literal["outline", "filled", "plain"]` | `"outline"` | reactive presentation | reflected public presentation |
| `size` | `Literal["sm", "md", "lg"]` | `"md"` | reactive presentation | reflected visual size |
| `class_` | `CClassValue | None` | `None` | server styling | merges on the input |
| `style` | `CStyleValue | None` | `None` | server styling | merges on the input |
| `attrs` | `Mapping[str, object] | None` | `None` | trusted native escape path | adds unowned ARIA, data, Alpine, and native attributes |

`date` means an exact `datetime.date`; `datetime.datetime` is rejected even
though Python subclasses `date`. Canonical strings contain four year digits,
two month digits, and two day digits and must name a real proleptic-Gregorian
date from year 0001 through 9999. The component never accepts locale-formatted
domain strings.

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `value` | canonical `string | null` | releases control while retaining the latest committed native value | clears the value | retain the previous valid value and report once per invalid episode | native value, empty/invalid state, FormData |
| `min` | canonical `string | null` | server fallback | removes the minimum | retain previous valid/server fallback | native constraint and validity |
| `max` | canonical `string | null` | server fallback | removes the maximum | retain previous valid/server fallback | native constraint and validity |
| `step` | positive integer | server fallback | invalid | retain previous valid/server fallback | native constraint and validity |
| `required` | boolean | server/Field fallback | invalid | fallback and report | native/ARIA/reflected state |
| `disabled` | boolean | server/Field/Form fallback | invalid | fallback and report | native/reflected state |
| `readonly` | boolean | server/Field/Form fallback | invalid | fallback and report | native/reflected state |
| `invalid` | boolean | server/Field fallback | invalid | fallback and report | ARIA/reflected state |
| `variant` | public variant | server fallback | invalid | fallback and report | presentation |
| `size` | public size | server fallback | invalid | fallback and report | presentation |

The client `value` is controlled when present. Native edits still dispatch
native events, then the component restores the controlled value unless the
owner accepts the request by changing the prop. Removing the prop releases
control at the latest accepted value. A server morph supplies a new fallback
and reset baseline without reading locale-formatted UI text.

## 5. State model

Public states are empty/filled, enabled/disabled, editable/readonly,
valid/application-invalid/native-invalid, focused/unfocused, controlled/
uncontrolled, required/optional, and the selected size/variant.

| Transition | Trigger | Commit and observable effects |
|---|---|---|
| empty to filled | native edit/picker or accepted controlled prop | native `value` becomes canonical ISO; `data-empty` is removed; native `input`/`change` behavior is preserved |
| filled to empty | native clearing, reset, or accepted `null` | value becomes `""`; `data-empty` appears; required validity may fail |
| uncontrolled edit | native `input` | commit the canonical native value and retain it for release/reset semantics |
| controlled edit | native `input` | native event exposes the requested value; restore the controlled value after listeners run |
| controlled prop update | Alpine effect | accept canonical value or `null`; invalid input retains the last valid state and reports once |
| reset | native Form reset | restore the server initial value when uncontrolled; controlled owners retain control and receive only the native reset event surface |
| invalid submission | native `invalid` | combine native and explicit invalid state, update Field, and focus the native input through the shared invalid-focus policy |
| state/config update | valid client prop | update the native property, public data mirror, Field relationships, and validity |

The component does not round or clamp an out-of-range or step-mismatched value.
The browser exposes constraint validity and the application validates again on
the server. Disabled and readonly states prevent user edits; a disabled input
is omitted from FormData, while readonly behavior follows the native browser.

## 6. Slots and slot data

There are no slots. Labels, descriptions, and errors belong to `CField`.
Prefix/suffix content and a custom picker trigger belong to composition or the
future `CDatePicker`, not inside the native control.

## 7. Callbacks, native events, and methods

`CDateInput` adds no component callback and dispatches no custom DOM event.
Consumers use Alpine `@input`, `@change`, `@focus`, `@blur`, and `@invalid` on
the native root. Event handlers read `$event.currentTarget.value`, which is
always empty or canonical ISO.

There are no wrapper methods. An author who needs imperative focus or native
picker opening places `x-ref` through `attrs` and calls `focus()` or
`showPicker()` where the browser supports it. `showPicker()` remains a native
capability with user-activation and browser restrictions.

## 8. Semantics, keyboard, focus, and assistive technology

The root remains a native Date input with no author-added ARIA role. The
browser owns its internal segment/picker semantics, keyboard behavior, touch
UI, spoken formatting, and focus. `CField` supplies the label and description/
error relationships. Standalone authors must provide an accessible name with
a native label, `aria-label`, or `aria-labelledby`.

The component does not intercept Arrow, Page, Home, End, Enter, Escape, or
typing keys. Browser differences are part of the native contract and must be
checked in Chromium, Firefox, and WebKit. Focus remains on the one native
input; there is no focus restoration or popup focus scope owned by Citry UI.

## 9. Native forms and validation

With `name`, a non-disabled value contributes exactly one `FormData` entry in
`YYYY-MM-DD`; empty optional controls contribute `""`, and disabled controls
contribute nothing. `form` supports native out-of-tree ownership. `required`,
`min`, `max`, and `step` use native constraint validation. `CForm` reset,
disabled, readonly, invalid-focus, and server morph behavior follow the shared
form-control contract.

The server must parse and validate the canonical submitted string again. The
browser's picker and client validation are convenience and early feedback,
not a trust boundary. Locale-formatted text is never submitted by this family.

## 10. Styling and theme contract

The root class is private; the stable public selector is
`[data-citry-ui-part="date-input"]`. Public variables cover background,
foreground, border, hover border, focus color, invalid border, disabled
background, radius, logical padding, font size, and minimum inline size.

The implementation preserves native appearance and the browser picker
indicator. It may style the outer control colors, border, typography, and
spacing, but it must not use `appearance: none`, hide internal native date
segments, or promise indicator geometry. Variants are `outline`, `filled`, and
`plain`; sizes are `sm`, `md`, and `lg`.

## 11. Environmental behavior

- Light and dark: scheme-aware Canvas colors and inherited `color-scheme`.
- Forced colors: native colors and a visible Highlight focus outline win.
- Reduced motion: no component animation.
- RTL: logical padding and borders follow direction; native segment order and
  indicator placement remain browser-owned.
- Narrow/touch: the input may shrink to its public minimum; the browser owns
  touch picker presentation.
- Zoom/reflow: no fixed outer width or clipped text.
- Print: print the native control as the browser renders it; applications that
  require plain text compose a print-only `<time>` value.
- No JavaScript: all editing, constraints, picker UI, submission, and reset
  remain useful; only Alpine-controlled overrides and Citry state mirrors are
  absent.

## 12. Overlay and layering behavior

`CDateInput` owns no DOM overlay, anchoring, z-index, dismissal, focus trap, or
scroll lock. A browser may display native picker UI outside page DOM; Citry UI
does not style or inspect it. `CDatePicker` will define the custom overlay
contract separately.

## 13. Collections, async data, and identity

There is no collection or async data. The date domain is one canonical value.
Generated identity follows the Field/input convention and remains stable for
one server render. Min/max changes are ordinary synchronous constraints.

## 14. Server render, morph, and cleanup

Server output is a complete working native control. Client activation adds
one component effect, native invalid/input/reset integration, and state
mirrors without replacing the element. Initialization is idempotent. Cleanup
releases listeners/effects, Form registration, and Field native-invalid state.

A morph updates the server fallback, constraints, and reset baseline. Active
native focus and editing follow Citry's retained-element behavior; the
component never parses the browser's displayed locale spelling. Removal while
focused leaves no overlay or global listener.

## 15. Security and content trust

Date values and constraints are validated before rendering. Text attributes
are escaped. `attrs` is a trusted author escape path but cannot replace owned
type, value, constraints, Field/Form identity, state mirrors, or runtime
directives, including dynamic/property aliases. Form submissions remain
untrusted and require server validation. No HTML, URL, remote data, or caller
callback is evaluated by the component.

## 16. Assets and performance

The family adds one small component JavaScript block, one CSS block, and the
already shared form-control runtime/style dependencies. It adds no icon, font,
observer, timer, global listener, calendar data, locale catalog, or third-party
date library. Assets emit once per page and instance work is constant.

Acceptance records raw, gzip, and Brotli family/catalog deltas and proves that
1, 10, and 100 controls do not duplicate component or shared assets. The
native picker avoids a custom calendar payload on pages that only need basic
date entry.

## 17. Acceptance matrix

Automated evidence:

- exact server HTML for empty, filled, bounded, Field, Form, and trusted-attrs
  cases;
- Python type/date/ordering/step validation and owned-attribute rejection;
- no-JavaScript canonical submission and native reset shape;
- controlled/uncontrolled value, release, invalid client values, reset,
  min/max/step updates, Field/Form state, invalid focus, and cleanup;
- native `input`/`change` behavior and exact FormData in Chromium, Firefox,
  and WebKit;
- axe on initial and edited quality states;
- light/dark, narrow, RTL, coarse pointer, forced colors, reduced motion,
  print, 200%/400% zoom, long surrounding content, and host CSS;
- docs preview rendering, structured reference, wheel contents, exports,
  typing, CSP compatibility, and asset budgets.

Manual evidence still required for release:

- keyboard entry and picker use in each browser/OS combination;
- mobile iOS and Android native pickers;
- VoiceOver, NVDA, and TalkBack naming, segments, constraints, and errors;
- password manager/autofill behavior for birthday use; and
- visual review across browser-owned indicator and segment presentations.

## 18. Compatibility classification

Stable public API includes `CDateInput`, every documented server/client input,
canonical value rules, native event surface, FormData shape, public variables,
part selector, and reflected attributes. Behavioral contract includes the
native root, Field/Form ownership, controlled semantics, validation, reset,
no-JavaScript output, and cleanup.

Exact colors, spacing, border strength, and browser-native internal rendering
are evolvable. The `.cui-date-input` class, private variables, runtime marker,
JavaScript organization, and browser shadow DOM are private.

## 19. Public documentation contract

The guide order is basic use, Python `date` values, constraints, Field/Form,
controlled use and native events, picker opening through `x-ref`, styling,
browser locale/platform behavior, no-JavaScript behavior, and security.

Planned examples:

| Preview | Reader task and visible state | Controls and interaction | Profiles and contract coverage | Module and focused evidence |
|---|---|---|---|---|
| Basic | choose an arrival date | native date edit | light/dark; value and native picker | `basic.py`; render + browser |
| Bounds | choose within a season | min/max/step | invalid boundary; constraints | `bounds.py`; render + browser |
| Form | required date in Field/Form | submit and reset | descriptions, error, FormData | `form.py`; browser + axe |
| Controlled | Alpine-owned date | accept/reject/release controls | controlled semantics and native events | `controlled.py`; browser |
| Birthday | birthday autofill | native `bday` hint | autocomplete and long-range value | `birthday.py`; render |
| States | readonly, disabled, invalid, variants/sizes | none | all public visual states | `states.py`; screenshot + axe |
| Locales | native inputs under `lang`/`dir` examples | native edit | browser-owned locale caveat, RTL | `locales.py`; three-browser |
| Styling | public variables and host classes | none | theming contract and host CSS | `styling.py`; CSS guard |

The sibling `api.yml` exhaustively lists Inputs, Slots, Events, Methods, CSS,
Attributes, Selectors, Interfaces, and ends with `translations: []` because
this family owns no translatable text.

## 20. Open decisions and deferred work

No decision blocks implementation. Deferred work:

- custom segmented localized editing needs a browser calendar adapter and its
  own complete accessibility contract;
- `CCalendar` owns reusable grid selection and calendar navigation;
- `CDatePicker` composes a custom calendar with a field/trigger;
- DateRange owns two-value ordering and range preview; and
- non-Gregorian editing/conversion remains outside the native HTML date value
  contract even when the browser displays localized UI.

Evidence that native date UI cannot meet baseline keyboard, assistive-
technology, canonical Form, or mobile behavior in a supported browser would
falsify this design and reopen a segmented adapter. Cosmetic differences do
not.

## 21. Internationalization

`CDateInput` owns no visible text, placeholder, validation prose, accessible
name, announcement, or browser-created message. The browser owns native date
segments, picker UI, and its built-in validation wording. Application labels,
descriptions, and error text belong to `CField` and application catalogs.

The domain and submitted value is always the locale-neutral proleptic-
Gregorian `YYYY-MM-DD` form required by HTML. The browser may display another
localized spelling based on its own locale and platform. An ancestor Citry
i18n provider supplies `lang` and `dir`, but this family does not claim that
every browser uses that `lang` for native Date UI. Applications that require
the active Citry locale to determine exact date spelling use the later custom
Calendar/DatePicker path or server-formatted read-only output.

There are no family translation keys, `$c-tr` bindings, `i18n.bind()` calls,
named Citry format profiles, locale-sensitive comparisons, or library-owned
directional icons. The structured reference therefore ends with an empty
Translation keys projection.
