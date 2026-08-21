# Rating component specification

**Status (2026-08-21): implementation, public docs, structured reference,
quality scenario, focused server tests, and three-browser behavior/axe evidence
complete; human visual and assistive-technology review remains.**

## 1. Purpose and product bar

`CRating` lets a person choose one score from a short bounded scale, normally
shown as stars. It also displays a submitted or aggregate score in readonly
mode. It is for quick qualitative feedback, not for arbitrary numeric entry.

```html
<c-CRating name="rating" label="Rate this article" />

<c-CField required>
  <c-slot name="label">Product rating</c-slot>
  <c-CRating value="3.5" precision="0.5" name="rating" />
</c-CField>

<c-CRating value="4.2" precision="0.1" readonly label="Average rating" />
```

Python may pass `int`, `Decimal`, or a canonical decimal string. Browser
state uses canonical decimal strings so fractional values never acquire
binary-float drift. `CField` owns a visible label, description, error, and
inherited form state. A standalone rating supplies `label`, `aria-label`, or
`aria-labelledby`.

The component is not a survey scale with authored labels per choice, a voting
counter, a sentiment picker with unrelated symbols, a general Slider, or a
distribution chart. Those jobs use Radio, Slider, ToggleGroup, or composition.

## 2. Prior art and complaints

The review used current official documentation and implementation source:

| Product or standard | Version or review date | Evidence inspected | Decision supported |
|---|---|---|---|
| Ark UI / Zag | 5.38.2 and current source, 2026-08-19 | Rating Group anatomy, half values, forms, translations, state machine | radio-style focus and selection, controlled state, hover, clearing, forms |
| Web Awesome | current 2026-08-19 | Rating docs | required accessible label, precision, readonly submission, form validity, hover |
| Mantine | current 2026-08-19 | Rating docs | uncontrolled FormData, clear-on-repeat, fractional display, readonly |
| PrimeVue | current 2026-08-19 | Rating docs | screen-reader radio inputs and native radio keyboard behavior |
| Vuetify | 4.1.6 source, 2026-08-19 | `VRating.tsx` | item labels, half increments, clearable state, icon layering |
| WAI-ARIA APG | 2026-08-19 | Radio Group pattern | single Tab stop, arrows, Home/End, Space, roving checked item |
| WHATWG HTML | living standard, 2026-08-18 | radio-button and form-control sections | progressive form submission, required validity, reset, disabledness |

Sources: [Ark UI Rating Group](https://ark-ui.com/docs/components/rating-group),
[Zag Rating Group machine](https://github.com/chakra-ui/zag/blob/main/packages/machines/rating-group/src/rating-group.machine.ts),
[Web Awesome Rating](https://webawesome.com/docs/components/rating/),
[Mantine Rating](https://mantine.dev/core/rating/),
[PrimeVue Rating](https://primevue.org/rating/),
[Vuetify VRating source](https://github.com/vuetifyjs/vuetify/blob/v4.1.6/packages/vuetify/src/components/VRating/VRating.tsx),
[APG Radio Group](https://www.w3.org/WAI/ARIA/apg/patterns/radio/), and
[HTML radio state](https://html.spec.whatwg.org/dev/input.html#radio-button-state-(type=radio)).

Citry adopts native radio semantics, exact arbitrary precision on a bounded
grid, an optional repeat-click clear action, hover preview, catalog-backed
choice names, controlled/uncontrolled state, and a real no-JavaScript form
fallback. It does not adopt a slider role: a rating is one choice among a
small enumerable set, and native radio behavior supplies stronger fallback
and required-validation semantics. It also avoids author callbacks returning
HTML for symbols; that surface is difficult to secure, type, localize, and
render fractionally.

### Vuetify disposition

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `modelValue` | direct API | exact `value` | Adopt without floats |
| `length` | direct API | `max` | Adopt with a bounded integer |
| `halfIncrements` | generalized direct API | `precision` | Support halves and other exact divisions |
| `clearable` | direct API | `allow_clear` | Adopt repeat-click clear |
| `hover` | fixed behavior | hover preview | Always preview while editable |
| `readonly`, `disabled` | direct/Field | same names | Adopt distinct submission behavior |
| `itemAriaLabel` | catalog/default override | `value_label` | Localized exact value and maximum |
| `emptyIcon`, `fullIcon`, item slot | deferred | fixed star symbol | Avoid an unsafe and underspecified markup callback |
| colors, density, size | CSS/theme/direct | variables, `variant`, `size` | Keep behavior API small |
| item labels and positions | composition | text beside `CRating` | Survey labels belong to Radio |
| ripple | omitted | none | No behavior value |

## 3. Public composition and anatomy

```text
div rating root
├─ div visual (aria-hidden)
│  ├─ span empty stars
│  └─ span filled stars (clipped to preview or committed ratio)
├─ div choices
│  └─ label choice hit target × bounded step count
│     ├─ input type=radio
│     └─ span visually-hidden localized value name
└─ input type=hidden (readonly submission only)
```

The root is the `attrs`/`class_`/`style` destination and has part `rating`.
The visual layer, empty layer, fill layer, choices layer, choice labels, radio
inputs, and readonly transport are stable parts. The public `id` identifies
the first native radio; subsequent radios append `-2`, `-3`, and so on. The
root uses `${id}-root`. The readonly hidden transport uses `${id}-transport`.

Each fractional grid value has one native radio and one equal-width pointer
target layered over the visual symbols. This keeps hit testing, accessible
choice count, and exact submitted values aligned. At most 200 choices render.

## 4. Server inputs and client inputs

`CRatingExact` is `int | Decimal | str`. Canonical strings use plain decimal
syntax only; floats, booleans, exponents, nonfinite values, and more than 128
digits are rejected. `max` is an integer from 1 through 20. `precision` is
positive, no greater than 1, exactly divides 1, and produces at most 200
choices across the scale. `value` is `None` or a grid value from zero to max.

| Python input | Type | Default | Class | Effect |
|---|---|---|---|---|
| `value` | exact or `None` | `None` (unrated) | initial value | committed score; zero and `None` both render unselected |
| `name`, `form`, `id` | `str \| None` | `None` | structural | native form and identity contract |
| `max` | `int` | `5` | structural | number of visual stars and maximum score |
| `precision` | exact | `1` | structural | selectable exact interval |
| `required` | `bool \| None` | `None` | reactive configuration | native required validity outside Field |
| `disabled`, `readonly`, `invalid` | `bool \| None` | `None` | reactive configuration | owner-aware form and visual state |
| `allow_clear` | `bool` | `False` | reactive configuration | repeat-click on the committed value clears it |
| `label` | `str \| None` | `None` | server accessibility | standalone accessible name; Field label wins |
| `value_label` | `str` with `{value}` and `{max}` | catalog default | server/localized | overrides every choice's accessible-name pattern |
| `size` | `"sm" \| "md" \| "lg"` | `"md"` | reactive styling | symbol and hit-target size |
| `variant` | `"solid" \| "subtle"` | `"solid"` | reactive styling | active-symbol treatment |
| `class_`, `style`, `attrs` | structured values/mapping | `None` | server styling | merge on documented root |
| `input_attrs` | mapping | `None` | server attributes | copied onto every radio except owned identity/state |

| Client input | Type | Omitted | Invalid | Affected surfaces |
|---|---|---|---|---|
| `value` | canonical string or `null` | uncontrolled | retain previous/report once | radios, fill, Form value |
| `required`, `disabled`, `readonly`, `invalid`, `allowClear` | boolean | server/owner value | retain previous | state and behavior |
| `size`, `variant` | documented literal | server value | retain previous | styles |
| `onValueChange`, `onHoverChange` | function | no callback | ignore/report | notifications |

An explicit valid client `value` controls the component. Omission releases it
to the last committed uncontrolled value. `null`, `"0"`, and zero mean
unrated. Structural `max` and `precision` do not change in browser props,
because changing the number or identity of radios requires a server render.

## 5. State model

State is `committedValue`, `hoveredValue`, current control status, and the
initial reset value. Values are canonical strings and safe grid indices.

| Trigger | Guard | Request/commit | Effects |
|---|---|---|---|
| pointer enters a choice | editable | preview only | fill and `onHoverChange` update |
| pointer leaves choices | any | clear preview | committed fill returns |
| click/tap a different choice | editable | request that value | native selection/form, fill, callback |
| click/tap committed choice | editable + allow clear | request null | uncheck group, remove Form value, callback |
| radio arrow/Home/End/Space | editable | native radio request | selection, form, focus, callback |
| external controlled value | valid | owner commit | surfaces update without callbacks |
| form reset | form owner | initial request/commit | uncontrolled resets; controlled requests reset value |
| disable/remove | any | cancel preview/listeners | no stale callback |

Controlled requests never move committed visual, native, or submitted state
until the owner supplies the new value. A refused request may be made again.
Hover preview is never submitted and never changes the checked radio.

## 6. Slots and slot data

There are no public slots. A fixed, CSS-driven star is intentionally part of
the first contract. Arbitrary symbol markup, per-score symbols, and authored
choice labels are deferred to avoid multiplying repeated slot ownership,
fraction clipping, pointer hit testing, and accessible naming. Applications
needing named survey choices use `CRadioGroup`.

## 7. Callbacks, native events, and methods

| Callback | Signature | Trigger | Behavior |
|---|---|---|---|
| `onValueChange` | `(str \| None, CRatingValueChangeDetail) => void` | user selection, clear, or reset request | uncontrolled state commits before callback; controlled state is request-only |
| `onHoverChange` | `(str \| None, CRatingHoverChangeDetail) => void` | preview enters a new value or leaves | never changes submitted value |

Value detail contains `value`, `previousValue`, `controlled`, `source`
(`pointer`, `keyboard`, or `reset`), and `sourceEvent`. Hover detail contains
`value`, `previousValue`, and `sourceEvent`. Uncontrolled selection dispatches
native bubbling `input` and `change` from the newly checked radio. Clearing
dispatches both from the previously checked radio. There are no custom DOM
events or wrapper methods.

## 8. Semantics, keyboard, focus, and assistive technology

The editable component exposes native radio buttons with one localized name
per exact choice. They share one name and therefore one Tab stop. The checked
radio receives entry focus; when unrated, browser radio behavior chooses the
first. Native arrows move and select, Space selects, and Home/End select the
first/last choice where browser support supplies those radio-group keys. Citry
normalizes Home and End without changing native arrow behavior.

The visual stars are `aria-hidden`. One visually hidden text node in each
native label supplies a choice name equivalent
of “3.5 out of 5”. The group receives its accessible name from `CField`, the
explicit `label`, or allowed ARIA input attributes. Required, invalid,
described-by, and error-message relationships follow Field ownership.

Readonly renders the radios disabled to make no-JavaScript mutation
impossible, provides one focusable root with `role="radiogroup"` and
`aria-readonly="true"`, and submits the committed value through a hidden
transport. Disabled mode is not focusable and does not submit.

## 9. Native forms and validation

Editable mode uses real same-name radios, including native `required`
validation. Only the checked value is successful. Unrated optional ratings
submit no entry. Readonly mode disables the radios and submits one hidden
canonical value when named and rated. Disabled mode submits nothing.

`form` associates every radio and the readonly transport with an external
form. CForm ownership cannot be redirected. Reset restores the initial
uncontrolled selection and clears hover. A controlled reset reports a request
and awaits the owner. Field/CForm disabledness wins; Field owns required,
readonly, invalid, IDs, descriptions, and errors when present.

## 10. Styling and theme contract

Rules live in `citry-ui.theme`. Public inherited inputs resolve through
private `--_cui-*` variables:

| Variable | Default purpose |
|---|---|
| `--cui-rating-empty-color` | muted empty star |
| `--cui-rating-fill-color` | committed active star |
| `--cui-rating-hover-color` | hover preview |
| `--cui-rating-focus-color` | keyboard focus ring |
| `--cui-rating-gap` | spacing between stars |
| `--cui-rating-symbol-size` | base symbol size |
| `--cui-rating-control-size` | minimum pointer target block size |
| `--cui-rating-disabled-opacity` | disabled treatment |

`size` adjusts the symbol and control fallbacks without overriding public
variables. `solid` uses a filled active star; `subtle` uses a softer active
color. Root states are `data-disabled`, `data-readonly`, `data-invalid`,
`data-hovering`, `data-size`, and `data-variant`. Choice labels expose
`data-checked` and `data-highlighted`. Styling works in light/dark, forced
colors, reduced motion, zoom/reflow, and RTL. There is no required animation.

## 11. Environmental behavior

- Without JavaScript, visible stars and native radios remain selectable,
  submit exact values, validate required state, reset, and honor disabled or
  readonly behavior.
- In RTL, the visual order follows inline direction and native radio arrows
  follow browser direction behavior; exact values stay associated with their
  visible positions.
- At 400% zoom and narrow widths, the row may wrap only if the author reduces
  `max` or symbol size; the default five-star control stays within 320 CSS px.
- Forced-colors uses system colors and visible outlines. Reduced motion needs
  no special substitution because state changes are not animated.
- Pointer coarse/fine and touch use the same label hit targets; hover preview
  is supplemental and never required to select.

## 12. Overlay and layering behavior

Rating opens no overlay, traps no focus, locks no scroll, and requests no
z-index. Its visual and hit-target layers form a local stacking context only.

## 13. Collections, async data, and identity

The bounded choice collection is derived synchronously from `max` and
`precision`. Choice identity is its canonical value. There is no async loader,
virtualization, mutation API, or author collection. Structural changes arrive
through a server rerender.

## 14. Server render, morph, and cleanup

Server HTML owns the initial checked state, labels, exact values, fill ratio,
form associations, and fallback behavior. Hydration adopts those values
without calling callbacks. Morph preserves the currently focused radio when
its public ID remains; changed structural grids replace their choices.
Runtime cleanup removes listeners, form-reset handling, i18n bindings, and
hover state. Reinserted fragments initialize once.

## 15. Security and content trust

Root and radio attribute maps reject owned IDs, names, form state, runtime
markers, `x-html`, and ownership directives. Labels and localized values are
written as text or ordinary attributes, never `innerHTML`. Exact decimal and
bounded-count validation prevents unbounded DOM generation. Callback errors
are isolated by the shared component runtime. No URL, HTML, remote asset, or
arbitrary property-assignment surface is exposed.

## 16. Assets and performance

One shared Rating runtime handles all instances and one component stylesheet
defines the star mask and interaction layers. Each instance renders
`max / precision` radios, capped at 200, plus `max` visual stars. There are no
observers, timers, network calls, or per-instance global listeners. The family
must stay inside the package's frozen raw/gzip/brotli budgets or record and
ratify an explicit budget change.

## 17. Acceptance matrix

| Area | Required evidence |
|---|---|
| render/validation | canonical exact values, grid/count limits, root/input attr ownership, IDs, messages-last rule |
| native fallback | selection, exact FormData, required validity, readonly transport, disabled omission, reset, external form |
| keyboard/focus | Tab entry, arrows, Space, Home/End, clear action, readonly focus, disabled exclusion |
| pointer | whole/fraction targets, hover preview, repeat-click clear, touch-compatible click |
| controlled state | accepted/refused/repeated request, release, reset request, no preview submission |
| Field/Form | labels, descriptions, errors, inherited states, ID/form conflict rejection |
| i18n | source locale, browser switch, fractional number formatting, explicit pattern override |
| styling | sizes/variant/states, public variables, part override, RTL, forced colors, zoom |
| lifecycle | morph, reinsert, cleanup, no duplicate callbacks |
| security/CSP | no inline-eval dependency, safe attrs/text, CSP runtime suite |
| browsers | focused Chromium, Firefox, and WebKit behavior plus automated accessibility scan |
| docs | guide, structured API, translation table, examples, quality scenario, inventory/counts |

## 18. Compatibility classification

`CRating` is additive. It does not alias an existing component. The name,
exact value model, public parts, data states, callbacks, catalog keys, and CSS
variables are release-contract surfaces. Fixed star markup inside the visual
layer is implementation detail except for documented part selectors.

Changing to slider semantics, accepting floats, changing zero/unrated FormData
behavior, or enabling custom symbol HTML is breaking. Adding a typed finite
symbol API later is additive only if existing star markup and parts remain.

## 19. Public documentation contract

The guide must show basic standalone and Field use, fractional precision,
controlled state, clearable behavior, readonly display, native forms/reset,
locale switching, states, and theming. It must explain that `value` callbacks
receive canonical strings, `None` means unrated, labels are required for
assistive technology, readonly submits while disabled does not, and custom
survey labels belong to Radio. The structured API ends with a translation-key
section listing every message ID, variables, default, output location, and
override input.

## 20. Open decisions and deferred work

- Custom empty/full symbols and per-value symbols are deferred pending a typed,
  secure repeated-content contract with fractional clipping evidence.
- Vertical Rating is deferred; current common jobs and the library's Radio and
  Slider components cover vertical selection better.
- Drag-across-to-select is deferred. Large label hit targets support touch,
  and a click/tap contract avoids implicit changes while scrolling.
- Aggregate count/distribution text is application content beside readonly
  Rating, not a component input.

## 21. Internationalization

`CRating.I18n.messages_locale` is `en-US`. Its `messages` block is the final
member of the class and defines:

| Key | Variables | Default | Output |
|---|---|---|---|
| `citry-ui-rating-value` | `value: number`, `max: number` | `{$value} out of {$max}` | each choice's accessible name and readonly value text |

The configured source render formats `value` and `max` with profile
`number.citry-ui-rating`; zero-configuration source mode uses their canonical
decimal spellings, then translates the label. Stable native names use
the explicit Citry translation binding when the catalog default is active;
the browser runtime refreshes dynamically created state with `i18n.bind()`.
An explicit `value_label` override disables the catalog binding and receives
formatted `{value}` and `{max}` substitutions. Locale switching updates every
choice name and readonly value text in place without changing exact values,
checked state, form payloads, or hover state.
