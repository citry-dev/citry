# NumberInput component specification

**Status:** ratified for Phase 8 implementation. Reviewed 2026-08-19.

## 1. Purpose and product bar

`CNumberInput` edits a quantity for which incrementing and decrementing are
meaningful. It preserves an exact canonical decimal for application state and
form submission while presenting and accepting the active locale's decimal
syntax when Citry client i18n is available. Its closest accessibility pattern
is the ARIA spinbutton; its no-JavaScript fallback is an ordinary text input.

Common jobs are intentionally short:

```html
<c-CNumberInput name="quantity" value="2" min="1" max="20" />

<c-CField>
  <c-slot name="label">Quantity</c-slot>
  <c-CNumberInput name="quantity" value="2" />
</c-CField>

<c-CNumberInput
  name="temperature"
  value="21.5"
  step="0.5"
  :value="temperature"
  :onValueChange="value => temperature = value"
/>
```

Python composition uses `CNumberInput(value=Decimal("2.5"), step=Decimal("0.5"))`.
`CField` supplies the label, description, error, required, disabled, readonly,
and invalid state. `attrs`, `class_`, and `style` customize the documented root.

This family is not for credit-card numbers, one-time codes, postal codes, or
identifiers; those values do not have numeric stepping semantics. `CPinInput`
owns segmented codes. Currency, percentages with a visible affix, expression
evaluation, units, arbitrary scientific notation, and calculator behavior are
non-goals. There is no headless API.

## 2. Prior art and complaints

The current-source review used only official standards, documentation, source,
and project issue records:

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Vuetify | 4.1.5, 2026-08-19 | `VNumberInput.tsx`, number-input guide, locale API | Styled anatomy, controls, precision limits, localized editing |
| React Aria | 1.18.0, 2026-08-19 | NumberField and `useNumberField` docs; Spectrum issue 1674 | Separate draft and committed values, commit timing, ARIA behavior |
| Ark UI / Zag | current 2026-08-19 | Number Input docs and Zag changelog through 1.42.0 | Exact string state, wheel opt-in, commit/clamp policy, cursor risk |
| Mantine | current 2026-08-19 | NumberInput docs | String edge states, clamp modes, large-number warning |
| Web Awesome | 3.11.0, 2026-08-19 | Number Input docs | Form-associated surface, public parts, imperative stepping |
| WHATWG HTML | living standard, 2026-08-19 | Number state | Native sanitization, canonical submission, step baseline |
| WAI-ARIA APG | 2026-08-19 | Spinbutton pattern and example | Keyboard, focus, ARIA values, adjacent button behavior |
| GOV.UK Design System | 2026-08-19 | Text input guidance and number-input research | Exclude numeric-looking identifiers; avoid accidental wheel changes |

Sources: [Vuetify source](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/components/VNumberInput/VNumberInput.tsx),
[Vuetify guide](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/docs/src/pages/en/components/number-inputs.md),
[React Aria NumberField](https://react-aria.adobe.com/NumberField),
[React Aria hook](https://react-aria.adobe.com/NumberField/useNumberField),
[React Spectrum issue 1674](https://github.com/adobe/react-spectrum/issues/1674),
[Ark UI Number Input](https://ark-ui.com/docs/components/number-input),
[Zag changelog](https://github.com/chakra-ui/zag/blob/main/packages/components/number-input/CHANGELOG.md),
[Mantine NumberInput](https://mantine.dev/core/number-input/),
[Web Awesome Number Input](https://webawesome.com/docs/components/number-input/),
[HTML number state](https://html.spec.whatwg.org/multipage/input.html#number-state-(type=number)),
[APG spinbutton](https://www.w3.org/WAI/ARIA/apg/patterns/spinbutton/), and
[GOV.UK number-input research](https://technology.blog.gov.uk/2020/02/24/why-the-gov-uk-design-system-team-changed-the-input-type-for-numbers/).

Citry adopts exact string state, a separate editable draft, explicit commit
policy, locale-aware parsing, opt-in wheel stepping, and ordinary text-editing
keys. It rejects JavaScript `number` as the canonical domain, eager formatting
on every keystroke, type=number as the primary control, and silent default
clamping. Browser and assistive-technology checks must prove the spinbutton and
adjacent controls rather than treating the APG example as sufficient evidence.

### Vuetify disposition

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `modelValue` | direct API | exact `value` | Adopt without binary-float semantics |
| `min`, `max`, `step` | direct API | same names | Adopt as exact decimals |
| `precision` / `minFractionDigits` | omitted | inferred exact scale and locale formatter | Avoid a second rounding policy |
| `controlVariant` default/stacked/split/hidden | direct API plus CSS | `show_controls`; one inline layout | Keep one robust anatomy |
| `hideInput` | composition | use other controls/output | Omit because it removes the spinbutton job |
| `inset` | CSS | public variables | No behavior prop |
| prefix/suffix, prepend/append slots | composition | neighboring content in application layout | Keep numeric editor unambiguous |
| density, width, reverse controls | CSS | size and logical CSS | No physical-direction prop |
| localized decimal/group parsing | i18n profile | `citry-ui-number-input` | Adopt |
| clamp on blur | direct API | `commit_behavior="clamp"` | Opt in; validation is default |
| hold controls to repeat | omitted in v1 | repeated pointer clicks | Avoid hidden acceleration behavior |
| wheel stepping | direct API | `wheel` default false | Explicit opt in |
| native `input` and `change` | native events | visible draft input and canonical transport | Adopt with documented destinations |
| increment/decrement labels | component messages/props | `increment_label`, `decrement_label` | Adopt and localize |
| numeric JS value and safe-number caveat | exact domain | canonical decimal string | Reject the limitation |
| focus/select methods inherited from text field | native refs | consumer ref to `[data-citry-ui-part="input"]` | No wrapper method |

## 3. Public composition and anatomy

```text
div number-input (documented root)
└─ div control
   ├─ button decrement (optional)
   ├─ input text, role=spinbutton (public control ID)
   └─ button increment (optional)
└─ input hidden canonical form transport (enhanced mode only)
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CNumberInput` | wrapper `div` | `attrs`, `class_`, `style` land on wrapper; `input_attrs` lands on editor | editor owns public ID/name fallback and Field relationships |

The control, editor, optional buttons, and transport are the only stable
relationships. The decrement and increment buttons are not in the Tab order;
pointer activation preserves editor focus. The family has no child declaration
components and no required slots. Unknown or owned attributes are rejected.

The post-implementation anatomy review must verify that the wrapper is still
needed for two controls and one Field registration. It may not be removed while
that relationship and a single customization root remain public requirements.

## 4. Server inputs and client inputs

Server exact decimals accept `int`, `Decimal`, a canonical plain-decimal
`str`, or `None` where stated. `bool`, float, exponent notation, NaN, infinity,
and more than 128 significant digits are rejected. Values are normalized by
removing redundant leading/trailing zeroes and mapping negative zero to `0`.

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `value` | `int \| Decimal \| str \| None` | `None` | initial value | exact canonical value or empty |
| `name`, `form`, `id` | `str \| None` | `None` | structural | native form/public identity |
| `min`, `max` | exact decimal or `None` | `None` | reactive configuration | inclusive bounds; min <= max |
| `step` | exact positive decimal | `1` | reactive configuration | exact step grid based on min or zero |
| `required`, `disabled`, `readonly`, `invalid` | `bool \| None` | `None` | reactive configuration | inherited from Field/Form when omitted |
| `show_controls`, `wheel` | `bool` | `True`, `False` | reactive configuration | adjacent buttons and focused wheel stepping |
| `commit_behavior` | `"validate" \| "clamp"` | `"validate"` | reactive configuration | invalid draft remains invalid or clamps at commit |
| `placeholder`, `autocomplete` | `str \| None` | `None` | reactive configuration | ordinary editable-input attributes |
| `increment_label`, `decrement_label` | `str` | catalog defaults | server/localized | explicit strings opt out of catalog binding |
| five `*_message` validation overrides | `str` | catalog defaults | server/localized | required, invalid, minimum, maximum, and step mismatch text |
| `variant` | `"outline" \| "filled" \| "plain"` | `"outline"` | reactive configuration | visual treatment |
| `size` | `"sm" \| "md" \| "lg"` | `"md"` | reactive configuration | control size |
| `class_`, `style`, `attrs` | structured values/mapping | `None` | server styling | merged on root |
| `input_attrs` | mapping | `None` | server attributes | safe non-owned input attributes |

The validation override names are `required_message`, `invalid_message`,
`minimum_message`, `maximum_message`, and `step_message`; the last three must
contain `{min}`, `{max}`, or `{step}` respectively.

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `value` | canonical `string \| null` | uncontrolled | controlled empty | retain previous and report once | editor, ARIA, transport |
| `min`, `max`, `step` | canonical string / null where allowed | server value | remove bound for min/max; invalid for step | retain previous | stepping/validity |
| booleans above | boolean | server/inherited | invalid | retain previous | state |
| `commitBehavior`, `variant`, `size` | documented literal | server value | invalid | retain previous | behavior/style |
| `onValueChange` | function | none | none | ignore/report | commit notification |
| `onInputValueChange` | function | none | none | ignore/report | draft notification |

An explicit valid client value controls canonical state. Omission releases
control to the last committed uncontrolled value. Rerender/morph preserves a
focused draft, selection, composition, and controlled ownership through token
handoff when the same public editor ID remains.

## 5. State model

Canonical value and visible draft are separate. Draft parse state is `empty`,
`incomplete`, `invalid`, or `valid`. A valid draft may still violate required,
minimum, maximum, or step constraints.

| Trigger | Guard | Request/commit | Effects |
|---|---|---|---|
| text input | editable | draft only | callback, parse state, validity; no reformat/caret jump |
| blur or Enter | editable, not composing | commit | valid value commits and formats; invalid stays visible/focused by native validation |
| decrement/increment | editable | request then commit | exact one-step change, snap to grid, clamp to bounds |
| ArrowDown/ArrowUp | editable | same as buttons | decrement/increment |
| PageDown/PageUp | editable | ten exact steps | clamp to bounds |
| Home/End | matching bound exists | commit bound | min/max |
| wheel | focused, `wheel`, editable | one step | prevent page scroll only when used |
| external controlled value | valid | owner commit | update canonical; preserve active composition until it ends |
| reset | form reset | initial request/commit | uncontrolled restores initial; controlled callback requests it |

Repeated same-value commits do not call `onValueChange`. Disabled and readonly
states block mutation; readonly remains focusable. `invalid=True` combines with
native component validity. `clamp` only changes an otherwise parse-valid value
outside a bound; it does not guess an invalid or incomplete string.

## 6. Slots and slot data

There are no public slots. Labels, descriptions, errors, units, currency, and
other surrounding content compose through `CField` and ordinary layout. This
keeps the editable value free of affixes the parser could mistake for input.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onValueChange` | `(str \| null, CNumberInputValueChangeDetail)` | successful commit/step/reset request | before uncontrolled native change | request only; owner must update | none |
| `onInputValueChange` | `(str, CNumberInputInputValueChangeDetail)` | visible draft changes | after DOM input | reports draft even when value-controlled | none |

Value detail contains `value`, `previousValue`, `inputValue`, `controlled`,
`source` (`blur`, `enter`, `increment`, `decrement`, `page`, `home`, `end`,
`wheel`, or `reset`), and `sourceEvent`. Input detail contains `inputValue`,
`previousInputValue`, parse `status`, `controlled`, `composing`, and source
event. Native `input` remains on the visible editor. An uncontrolled canonical
commit dispatches bubbling synthetic `input` then `change` on the enhanced
hidden transport so form-level listeners see canonical changes. There are no
custom DOM events or wrapper methods; consumers can focus/select the public
input through a ref.

## 8. Semantics, keyboard, focus, and assistive technology

The editable text input has `role="spinbutton"`, an accessible name supplied
by its surrounding label or caller attributes, `aria-valuenow` as the exact
canonical decimal when valid, optional `aria-valuemin`/`aria-valuemax`, and a
localized `aria-valuetext` when formatted text differs. Invalid input removes
`aria-valuenow` and sets `aria-invalid=true`. The buttons have localized names
and are `tabindex=-1`.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| editor | text-edit keys | native editing | unchanged | no |
| editor | Up/Down | exact step | editor | yes |
| editor | PageUp/PageDown | ten steps | editor | yes |
| editor | Home/End with bound | bound | editor | yes |
| editor | Enter | commit | editor | only when handled |
| control button | click/touch | one step | editor | button default only |
| focused editor | wheel, opt in | one step | editor | only when stepped |

Tab reaches only the editor. Browser zoom, touch exploration, speech input,
and standard selection shortcuts must continue to work. The component adds no
live region because spinbutton state and form validity already expose changes.

## 9. Native forms and validation

Without JavaScript, the visible text input owns `name` and submits its localized
draft; servers parse it with the same named profile. After enhancement, a
hidden transport owns `name` and submits the exact canonical decimal while the
visible input owns constraint validation. Disabled controls do not submit;
readonly controls submit; empty optional values omit/submit an empty value in
the same way as a text input. `form` associates both surfaces with one owner.

The component applies required, parse, min, max, and exact step-grid validity
through `setCustomValidity`, forwards invalid state to `CField`, focuses the
editor on invalid submission, supports form reset, and does not intercept an
Enter that should submit after a successful commit. Citry Events receives the
canonical transport value after enhancement and preserves the ordinary no-JS
localized form value on server validation failures.

## 10. Styling and theme contract

Variants are outline, filled, and plain; sizes are sm, md, and lg. Controls use
logical inline order, equal hit targets, and the established Citry UI focus,
invalid, disabled, and forced-color treatments.

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-number-input-background` | color | control background | `Canvas` |
| `--cui-number-input-foreground` | color | text/icons | `CanvasText` |
| `--cui-number-input-border-color` | color | border | mixed CanvasText |
| `--cui-number-input-focus-color` | color | focus ring | `Highlight` |
| `--cui-number-input-invalid-border-color` | color | invalid border | theme error |
| `--cui-number-input-radius` | length | corner radius | `.5rem` |
| `--cui-number-input-height` | length | md height | `2.5rem` |
| `--cui-number-input-inline-padding` | length | editor padding | `.75rem` |
| `--cui-number-input-control-size` | length | step button width | `2.5rem` |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="number-input"]` | root | all | contains control/transport |
| `[data-citry-ui-part="control"]` | visual control | all | contains editor/buttons |
| `[data-citry-ui-part="input"]` | editor | all | public focus target |
| `[data-citry-ui-part="decrement"]` | decrement button | controls shown | adjacent to editor |
| `[data-citry-ui-part="increment"]` | increment button | controls shown | adjacent to editor |

Public reflected attributes on the root are `data-empty`, `data-required`,
`data-disabled`, `data-readonly`, `data-invalid`, `data-variant`, and
`data-size`. They are observable styling state, not writable inputs.

## 11. Environmental behavior

Light/dark colors use `light-dark`; logical borders and order support RTL;
plus/minus symbols do not mirror. Motion is not required. Forced colors retain
a visible border/focus indication. At 200/400 percent zoom the component wraps
with its layout instead of clipping; buttons retain at least a 44 CSS-pixel
coarse-pointer target. Mobile uses `inputmode="decimal"` without removing the
full keyboard path. Print shows the formatted value and hides step controls.

The `citry-ui-number-input` profile is a strict decimal `NumberFormat`. Source
mode uses canonical ASCII for formatting/parsing. Configured server rendering
uses the active locale. With a client provider, `i18n.parse.number()` and
`i18n.format.number()` handle live edits and locale switches. With configured
server-only i18n, the localized SSR text remains until editing starts; focus
then changes the draft to its separately shipped canonical value, avoiding any
attempt to infer locale punctuation in the browser.

During composition or a dirty focused draft, a locale switch preserves the
literal draft and its last parse result. A successful commit formats in the new
locale. An idle draft reformats immediately. Application content and labels
retain their caller locale/direction ownership.

Catalog defaults are rendered with server `tr()`. Stable control labels use
conditional `$c-tr` attribute bindings. Browser-created validation text uses
an `i18n.bind()` tied to the active failure reason and is disposed when the
reason changes or the component unmounts. Explicit label/message props emit no
catalog binding. Browser formatting/parsing uses the profile, not translation
messages.

## 12. Overlay and layering behavior

The family creates no overlay, portal, focus trap, scroll lock, or stacking
context.

## 13. Collections, async data, and identity

The family has no collection or async work. Each instance owns one exact value
and one draft; generated IDs and form transport are isolated per instance.

## 14. Server render, morph, and cleanup

SSR is a useful editable field with visible controls and localized initial
text. Buttons are ordinary submit-safe `type=button` controls. Activation is
idempotent and sanitizes exact settled anatomy. Morph token handoff preserves
canonical value, draft, selection, composition, controlled mode, and native
invalid state for the same public ID. Removal releases listeners, form-reset
hooks, i18n bindings/subscriptions, timers, Field invalid state, and token data.
Late fragments under an already-switched provider use the provider's current
profile before interaction.

## 15. Security and content trust

All visible values and labels are escaped text. Exact decimal inputs are
length-bounded and validated before serialization. The component rejects
owned role, identity, form, value, ARIA-value, runtime, and executable binding
attributes on the wrong surface. It never evaluates numeric expressions, uses
`innerHTML`, or converts untrusted input through `Number`. Callback results do
not become markup.

## 16. Assets and performance

Assets are one component CSS block, one CSP-safe component program, the shared
form-control runtime, and existing plus/minus icons or equivalent inline text
symbols. Each instance adds editor/button/form listeners but no observer,
network request, font, overlay, or global listener. Qualification records raw,
gzip, and Brotli deltas, 100-instance mount cost, repeated exact stepping, and
first-input latency. The no-JavaScript surface incurs no client asset beyond
ordinary Citry component selection.

## 17. Acceptance matrix

Automated evidence covers schema/type exports; exact normalization and bounds;
SSR/source/configured modes; Field/Form ownership; no-JS and enhanced form
values; controlled/uncontrolled commits; draft callbacks; every keyboard and
pointer transition; IME/caret preservation; min/max/step validation; reset;
wheel opt-in; locale digits/separators and live switch; explicit i18n overrides;
RTL, dark, forced colors, reduced motion, zoom, touch; morph/fragment/removal;
attribute attacks; 100 instances; built wheel; API docs; standalone scenario;
Chromium, Firefox, and WebKit.

Manual gates cover keyboard-only use, VoiceOver/Safari, NVDA/Firefox,
TalkBack/Chrome, speech input, touch exploration, 400 percent zoom, long
translated labels, and visual sign-off in light/dark/RTL/forced colors.

Public examples are fixed before implementation:

| Module | Reader task and visible states | Controls / environments | Contract evidence |
|---|---|---|---|
| `basic.py` | quantity in a labeled Field | value/min/max/step | basic form/stepping |
| `exact_decimals.py` | fractional price-like quantity | value/step | exact decimal, no float |
| `constraints.py` | required and bounded invalid states | commit behavior | validation/Field errors |
| `controlled.py` | owner-controlled value and details | value/onValueChange | control contract |
| `without_controls.py` | compact editor | show controls | anatomy variant |
| `wheel.py` | explicit wheel behavior | wheel toggle | scroll safety |
| `locales.py` | en-US, cs-CZ, ar-EG | locale switch | parser/formatter/RTL |
| `forms.py` | reset and submitted canonical output | submit/reset | transport/no-JS |
| `states.py` | disabled, readonly, invalid, sizes/variants | theme | visual matrix |

The Python-owned scenario catalog maps these modules to docs previews,
standalone routes, Playwright tests, screenshots, axe, Lighthouse, and manual
tasks.

## 18. Compatibility classification

Stable API includes the component/type names, all documented inputs and
callbacks, exact canonical form value, public CSS variables/selectors/reflected
attributes, and translation keys. Behavioral contract includes spinbutton
semantics, keyboard/focus, draft versus committed state, client/server i18n
behavior, no-JS submission, and the documented anatomy. Exact colors, spacing,
and shadows are evolvable. `.cui-*`, private variables, transport markers,
program layout, and incidental wrappers beyond the documented relationships
are private.

## 19. Public documentation contract

`api.md` teaches basic Field composition, exact decimal values, constraints,
controlled use, forms, locale behavior, and when not to use a numeric control.
`api.yml` exhaustively lists Inputs, Events, CSS, Attributes, Selectors,
Interfaces, and finally Translation keys. There are no Slots or Methods. Every
example above is result-first and uses shared scenario data.

## 20. Open decisions and deferred work

No decision blocks implementation. Long-press acceleration, scrubbing/pointer
lock, scientific notation, currency/unit affixes, arbitrary precision beyond
the documented bound, and a headless primitive are deferred separate jobs.

## 21. Internationalization

| Message ID | Variables | Override input | Browser update |
|---|---|---|---|
| `citry-ui-number-input-decrement` | none | `decrement_label` | conditional `$c-tr` on button `aria-label` |
| `citry-ui-number-input-increment` | none | `increment_label` | conditional `$c-tr` on button `aria-label` |
| `citry-ui-number-input-required` | none | `required_message` | active `i18n.bind()` custom validity |
| `citry-ui-number-input-invalid` | none | `invalid_message` | active `i18n.bind()` custom validity |
| `citry-ui-number-input-minimum` | `min: str` | `minimum_message` | active `i18n.bind()` custom validity |
| `citry-ui-number-input-maximum` | `max: str` | `maximum_message` | active `i18n.bind()` custom validity |
| `citry-ui-number-input-step` | `step: str` | `step_message` | active `i18n.bind()` custom validity |

The exact profile is `number.citry-ui-number-input` with decimal input. Button
symbols are language-neutral and do not mirror. Numeric `aria-valuetext`,
validation variables, draft parsing, display formatting, live locale changes,
source-mode canonical behavior, explicit overrides, fragment adoption, and
binding cleanup are all release evidence. The structured component API repeats
this table as its final section.
