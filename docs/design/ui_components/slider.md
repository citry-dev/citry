# Slider and RangeSlider component specification

**Status:** ratified for Phase 8 implementation. Reviewed 2026-08-19.

## 1. Purpose and product bar

`CSlider` selects one approximate position from a bounded exact-decimal scale.
`CRangeSlider` selects one ordered lower/upper interval from that scale. Both
are useful when the bounds are known and direct manipulation is more important
than typing an exact value. `CNumberInput` remains the better control when the
user must enter or inspect a precise arbitrary number.

Common jobs stay short:

```html
<c-CSlider name="volume" value="40" min="0" max="100" />

<c-CField>
  <c-slot name="label">Price range</c-slot>
  <c-CRangeSlider name="price" c-value="('20', '80')" min="0" max="100" />
</c-CField>

<c-CSlider
  value="0.5"
  step="0.1"
  :value="opacity"
  :onValueChange="value => opacity = value"
/>
```

Python composition uses `CSlider(value=Decimal("0.5"), step=Decimal("0.1"))`
and `CRangeSlider(value=(Decimal("20"), Decimal("80")))`. `CField` supplies
the visible label, description, error, disabled, readonly, and invalid state.
`attrs`, `class_`, and `style` customize the documented root.

The family is not a scrubber for media playback, a free-form numeric editor,
an unbounded scale, a color/angle/coordinate picker, a histogram brush, or a
more-than-two-thumb constraint editor. It does not infer logarithmic or other
nonlinear scales. There is no headless API.

## 2. Prior art and complaints

The current-source review used official standards, docs, tagged source, and
project issue/changelog records:

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Vuetify | 4.1.5, 2026-08-19 | `VSlider`, `VRangeSlider`, shared slider and thumb source | Styled anatomy, ticks, labels, exact public surface, range collision behavior |
| React Aria / Spectrum | current 2026-08-19 | Slider and RangeSlider docs | controlled/uncontrolled state, live/end callbacks, locale-aware value text, forms |
| Ark UI / Zag | current 2026-08-19 | Slider docs and changelog through 1.42 | anatomy, pointer lifecycle, min gap, collision and drag-regression evidence |
| Base UI | 1.7.0, 2026-08-19 | Slider docs | SSR thumb identity, forms, explicit multi-thumb labels, edge alignment |
| Mantine | current 2026-08-19 | Slider/RangeSlider docs and RTL issue 7822 | marks, decimal steps, vertical geometry, value labels, RTL regression risk |
| Web Awesome | 3.11.0, 2026-08-19 | Slider docs | form-associated surface, native events, range mode, methods and public parts |
| WHATWG HTML | living standard, updated 2026-08-18 | Range state and rendering | useful native fallback, form/reset semantics, direction behavior |
| WAI-ARIA APG | 2026-08-19 | Slider and multi-thumb patterns | thumb roles, keyboard, dependent bounds, stable Tab order, touch-AT warning |

Sources: [Vuetify Slider](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/components/VSlider/VSlider.tsx),
[Vuetify RangeSlider](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/components/VRangeSlider/VRangeSlider.tsx),
[Vuetify shared slider source](https://github.com/vuetifyjs/vuetify/blob/v4.1.5/packages/vuetify/src/components/VSlider/slider.ts),
[React Aria Slider](https://react-aria.adobe.com/Slider),
[React Spectrum RangeSlider](https://react-spectrum.adobe.com/v3/RangeSlider.html),
[Ark UI Slider](https://ark-ui.com/docs/components/slider),
[Ark changelog](https://github.com/chakra-ui/ark/blob/main/packages/react/CHANGELOG.md),
[Base UI Slider](https://base-ui.com/react/components/slider),
[Mantine Slider](https://mantine.dev/core/slider/),
[Mantine issue 7822](https://github.com/mantinedev/mantine/issues/7822),
[Web Awesome Slider](https://webawesome.com/docs/components/slider/),
[HTML range state](https://html.spec.whatwg.org/dev/input.html#range-state-(type=range)),
[APG Slider](https://www.w3.org/WAI/ARIA/apg/patterns/slider/), and
[APG multi-thumb Slider](https://www.w3.org/WAI/ARIA/apg/patterns/slider-multithumb/).

Citry adopts separate live/change-end callbacks, stable thumb identity, exact
step values, an explicit minimum gap, localized value text, named marks, and a
native fallback. It rejects binary-float application state, arbitrary thumb
counts, default push/swap collisions, pointer-only access, and a value array
that silently changes a component from one semantic job to another. Ark's
repeated fixes for stuck overlapping thumbs, drag offsets, fast-drag end
values, runtime disable, and step gaps make pointer capture and cleanup direct
acceptance requirements. APG's touch-assistive-technology warning remains a
manual release gate rather than a claim that ARIA alone proves mobile access.

### Vuetify disposition

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `VSlider` / `VRangeSlider` | separate components | `CSlider` / `CRangeSlider` | Adopt the explicit family split |
| `modelValue` | direct API | exact `value` / pair | Adopt without binary floats |
| `min`, `max`, `step` | direct API | same names | Adopt with min-origin exact grid |
| `strict` range collision | fixed behavior | ordered, non-crossing pair | Always strict; clearer identity |
| `direction` | direct API | `orientation` | Use established naming |
| `reverse` | omitted | RTL and logical geometry | Avoid a second directional model |
| `ticks`, `showTicks`, tick labels | direct API | `marks`, `show_marks` | One bounded mark model |
| `thumbLabel` and slot | direct API plus formatting | `show_value`, `format` | Text only; no arbitrary tooltip markup |
| `trackFillColor`, `trackColor`, `thumbColor` | CSS | public variables | No behavior props for colors |
| `thumbSize`, `trackSize`, `tickSize` | CSS/size | public variables and `size` | Adopt as theme contract |
| color, rounded, elevation, ripple | CSS/theme | `variant`, variables | No ripple or elevation behavior |
| disabled, readonly, error | Field/direct API | `disabled`, `readonly`, `invalid` | Adopt |
| `noKeyboard` | omitted | keyboard is required | Reject inaccessible opt-out |
| prepend/append/label slots | composition | `CField` and layout | Avoid duplicate Field contract |
| start/end events | callbacks | `onValueChange`, `onValueChangeEnd` | Use value-oriented names/details |
| `focus()` | native ref | first thumb selector | No wrapper method |

## 3. Public composition and anatomy

```text
div slider root
├─ input type=range native fallback / canonical form control
└─ div control (hidden until enhanced)
   └─ div track
      ├─ span fill
      ├─ mark spans (optional)
      └─ button role=slider thumb
         └─ span value bubble (optional)

div range-slider root
├─ input type=range lower native fallback / canonical form control
├─ input type=range upper native fallback / canonical form control
└─ div control (hidden until enhanced)
   └─ div track
      ├─ span fill between thumbs
      ├─ mark spans (optional)
      ├─ button role=slider lower thumb
      └─ button role=slider upper thumb
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CSlider` | wrapper `div` | root attrs/class/style; `input_attrs` on native input | one fallback/form input and one enhanced thumb |
| `CRangeSlider` | wrapper `div` | root attrs/class/style; lower/upper input attrs on matching fallback | two fixed-identity inputs and two fixed-identity thumbs |

The public ID names the single native input for `CSlider` and the lower native
input for `CRangeSlider`; generated `-upper` and `-root` IDs identify the other
range control and its wrapper. The
track, fill, thumb(s), optional marks, and optional value bubbles are stable
public parts. Incidental geometry wrappers are not public.

The post-implementation anatomy review must retain two explicit roots because
their form, label, callback, and accessibility payloads differ. Shared private
normalization and runtime code are expected; a public declaration child is not.

## 4. Server inputs and client inputs

Exact decimals accept `int`, `Decimal`, or canonical plain-decimal `str`.
`bool`, float, exponent notation, nonfinite values, and more than 128
significant digits are rejected. `min < max`, `step > 0`, and `(max-min)/step`
must be an integer no greater than 1,000,000. Values and marks must lie on that
min-origin grid.

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `value` (`CSlider`) | exact decimal or `None` | `None` -> min | initial value | one bounded grid value |
| `value` (`CRangeSlider`) | pair of exact decimals or `None` | `None` -> `(min,max)` | initial value | ordered bounded grid pair |
| `name` | `str \| None` | `None` | structural | single value; range submits two ordered entries |
| `lower_name`, `upper_name` | `str \| None` | `None` | structural range-only | optional distinct names; both or neither |
| `form`, `id` | `str \| None` | `None` | structural | native form/public identity |
| `min`, `max`, `step` | exact decimal | `0`, `100`, `1` | reactive configuration | exact finite grid |
| `large_step` | exact decimal or `None` | ten steps | reactive configuration | Page keys; positive aligned multiple |
| `min_steps_between_thumbs` | nonnegative int | `0` | reactive range-only | lower/upper gap |
| `disabled`, `readonly`, `invalid` | `bool \| None` | `None` | reactive configuration | inherited from Field/Form when omitted |
| `orientation` | `"horizontal" \| "vertical"` | `"horizontal"` | reactive configuration | geometry and ARIA |
| `variant` | `"solid" \| "subtle"` | `"solid"` | reactive styling | fill treatment |
| `size` | `"sm" \| "md" \| "lg"` | `"md"` | reactive styling | track/thumb size |
| `show_value` | `"never" \| "interaction" \| "always"` | `"interaction"` | reactive configuration | value bubbles |
| `show_marks` | `bool` | inferred from labels | reactive configuration | render mark dots |
| `marks` | mapping/sequence | empty | structural server data | at most 101 unique grid values; optional author text |
| `format` | `str` | `citry-ui-slider` | reactive i18n configuration | named number-format profile |
| `lower_label`, `upper_label` | `str` | catalog defaults | server/localized range-only | explicit strings remove catalog binding |
| `class_`, `style`, `attrs` | structured values/mapping | `None` | server styling | merged on root |
| input attr mappings | mapping | `None` | server attributes | safe non-owned native-input attributes |

`marks` accepts exact values or a mapping from exact values to already
localized display labels. Mark labels are application content, not Citry UI
messages. `show_marks=False` hides dots and labels without changing the step
grid. `CRangeSlider.name` produces two ordered form entries unless the caller
uses both `lower_name` and `upper_name`.

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `value` | canonical string or two-item string array | uncontrolled | invalid | retain previous/report once | thumb(s), fill, forms, ARIA |
| `min`, `max`, `step`, `largeStep` | canonical strings | server value | invalid except optional largeStep | retain previous | grid/keys/geometry |
| `minStepsBetweenThumbs` | safe nonnegative integer | server value | invalid | retain previous | range constraints |
| booleans/literals above | documented type | server value | invalid | retain previous | behavior/style |
| `onValueChange`, `onValueChangeEnd` | function | none | none | ignore/report | notifications |

An explicit valid client value controls state. Omission releases control to the
last committed uncontrolled value. A server rerender updates uncontrolled
configuration and value unless a live pointer/key interaction owns a handoff
token. Controlled state never moves without the owner returning a new value.

## 5. State model

Each value is stored as an exact canonical decimal plus a safe integer grid
index. Geometry uses the grid index ratio; it never performs decimal stepping
with JavaScript `number`. The range pair keeps fixed `lower` and `upper`
identity and never swaps or crosses.

| Trigger | Guard | Request/commit | Effects |
|---|---|---|---|
| pointer/touch down on track | editable | choose nearest thumb and request | focus chosen thumb; pointer capture |
| pointer/touch move | captured, editable | repeated live request | update uncontrolled thumb/fill/form and callback |
| pointer up/cancel | captured | end notification | release capture; one `onValueChangeEnd` if changed |
| Arrow key | editable | one step | exact bounded request; end fires for the action |
| Page key | editable | large step | exact bounded request; end fires |
| Home/End | editable | thumb-specific bound | exact request; end fires |
| external controlled value | valid | owner commit | update all surfaces without callbacks |
| form reset | form owner | initial request/commit | uncontrolled restores initial; controlled requests it |
| disable/remove during drag | any | cancel | release capture/listeners; no stale end callback |

Range pointer selection chooses the geometrically nearest thumb. At an exact
tie, the last-focused thumb wins; without history, movement toward the upper
side chooses upper and movement toward lower chooses lower. The lower thumb's
maximum is the upper value minus the configured gap; the upper thumb's minimum
is the lower value plus the gap. Repeated same-value requests do not notify.
Readonly thumbs stay focusable and expose values but do not mutate. Disabled
thumbs leave the Tab order and form entries.

## 6. Slots and slot data

There are no public slots. `CField` owns label, description, and error content;
`marks` owns bounded author text. Icons or arbitrary markup inside a thumb or
value bubble are deferred because they complicate hit testing, accessible
names, and safe localized value output.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onValueChange` | `(str, CSliderValueChangeDetail)` or `(tuple[str,str], CRangeSliderValueChangeDetail)` | each user value request | during pointer drag or key action | request only | none |
| `onValueChangeEnd` | same value/detail shapes | completed drag/key/reset request | after last live request | reports requested/returned controlled value status | pointer cancel reports only if a value changed |

Details contain `value`, `previousValue`, `controlled`, `source` (`pointer`,
`keyboard`, or `reset`), `sourceEvent`, and `phase` (`change` or `end`). Range
detail also contains `activeThumb` (`lower` or `upper`). Uncontrolled live
changes dispatch bubbling native-compatible `input` on the appropriate native
form input; a completed change dispatches `change`. Range events preserve
lower-then-upper form order. There are no custom DOM events or wrapper methods;
consumers may focus the documented thumb selector.

## 8. Semantics, keyboard, focus, and assistive technology

Every enhanced thumb is a focusable `button type=button` with `role=slider`,
an accessible name, exact `aria-valuenow`, bounded `aria-valuemin/max`,
localized `aria-valuetext`, and vertical `aria-orientation` when applicable.
The range's dependent ARIA bounds update on every value change. The lower and
upper labels default to localized component messages and remain distinct.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| horizontal thumb | Right / Up | increase one step | same thumb | yes |
| horizontal thumb | Left / Down | decrease one step | same thumb | yes |
| vertical thumb | Up / Right | increase one step | same thumb | yes |
| vertical thumb | Down / Left | decrease one step | same thumb | yes |
| any thumb | PageUp/PageDown | increase/decrease large step | same thumb | yes |
| any thumb | Home/End | allowed minimum/maximum | same thumb | yes |
| track | pointer/touch press and drag | nearest allowed grid value | active thumb | pointer default |

Keyboard value direction follows APG and does not reverse in RTL; Right and Up
mean numerically greater even when the horizontal visual high edge is left.
Pointer geometry does mirror in RTL. `CRangeSlider` contributes two fixed Tab
stops in lower-then-upper order regardless of values or visual overlap. Value
bubbles are presentation and are never live regions. Touch targets are at least
44 CSS pixels on coarse pointers, and pointer capture must coexist with touch
exploration tests rather than suppressing the APG mobile warning.

## 9. Native forms and validation

Before enhancement, `CSlider` is one ordinary `input type=range` and
`CRangeSlider` is two clearly labeled native range inputs. They provide a
functional no-JavaScript form even though the range fallback shows two tracks.
After enhancement those same inputs become non-focusable hidden canonical form
controls; the styled thumbs own interaction. No duplicate hidden value exists.

Single `name` submits one value. Range `name` submits two entries in lower then
upper order; the distinct-name mode submits one each. Disabled values do not
submit. Readonly fallbacks are disabled plus a hidden canonical transport so
they remain immutable and successful; enhancement restores the documented
focusable readonly thumb. Form reset restores initial uncontrolled values and
requests controlled resets. All production values already satisfy bounds,
step, and gap, so the family has no required or parse-validity messages.
`invalid=True` is application/Field state, not a second numeric parser.

## 10. Styling and theme contract

Variants are solid and subtle; sizes are sm, md, and lg. Logical geometry
supports horizontal and vertical controls. The visual fill runs min-to-value
for Slider and lower-to-upper for RangeSlider.

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-slider-track-color` | color | unselected rail | mixed CanvasText |
| `--cui-slider-fill-color` | color | selected rail | AccentColor |
| `--cui-slider-thumb-color` | color | thumb fill | Canvas |
| `--cui-slider-thumb-border-color` | color | thumb edge | AccentColor |
| `--cui-slider-focus-color` | color | focus ring | Highlight |
| `--cui-slider-mark-color` | color | mark dot | CanvasText |
| `--cui-slider-value-background` | color | value bubble | CanvasText |
| `--cui-slider-value-foreground` | color | value text | Canvas |
| `--cui-slider-track-size` | length | rail thickness | `.375rem` |
| `--cui-slider-thumb-size` | length | visual thumb | `1.25rem` |
| `--cui-slider-control-size` | length | interaction cross-size | `2.75rem` |
| `--cui-slider-radius` | length | track/thumb rounding | `999px` |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="slider"]` | single root | all | owns one input/control |
| `[data-citry-ui-part="range-slider"]` | range root | all | owns two inputs/control |
| `[data-citry-ui-part="native-input"]` | no-JS/form control | each value | hidden only after enhancement |
| `[data-citry-ui-part="control"]` | pointer geometry region | enhanced | contains track |
| `[data-citry-ui-part="track"]` | complete rail | enhanced | contains fill/marks/thumbs |
| `[data-citry-ui-part="fill"]` | selected interval | enhanced | positioned logically |
| `[data-citry-ui-part="thumb"]` | focusable slider | one/two | fixed value identity |
| `[data-citry-ui-part="mark"]` | optional step reference | marks | author text may follow |
| `[data-citry-ui-part="value"]` | formatted value bubble | optional | belongs to one thumb |

Reflected root attributes are `data-orientation`, `data-variant`, `data-size`,
`data-disabled`, `data-readonly`, `data-invalid`, `data-dragging`, and
`data-enhanced`. Thumbs reflect `data-thumb=single|lower|upper` and
`data-active`. These are observable styling state, not configuration inputs.

## 11. Environmental behavior

Light/dark use `light-dark`; forced colors preserves a distinct track, fill,
thumb, focus ring, and marks. Reduced motion removes bubble/thumb transitions.
Horizontal pointer geometry mirrors under RTL while fixed numeric keyboard
semantics do not. Vertical minimum is physically at the bottom. At 200/400%
zoom the horizontal track remains usable without page-level horizontal scroll;
vertical layout requires an explicit block-size from the caller and defaults to
12rem. Long mark labels may wrap without changing their grid positions. Print
shows a static rail, fill, value(s), and labels without focus decoration.

`number.citry-ui-slider` is the package-owned decimal display profile. Source
mode uses deterministic en-US formatting; configured SSR uses the provider
locale. Client providers reformat value bubbles and `aria-valuetext` on locale
changes without changing exact canonical state or geometry. Because values are
never typed, the family needs formatting but no browser number parser.
Explicit application mark labels remain application-owned and do not change
automatically unless their owner rerenders them.

Range thumb labels render with server `tr()` and conditional `$c-tr` bindings
on `aria-label`; explicit label props emit no catalog binding. Formatted values
are native properties/text updated through the format service and the logical
provider subscription, with cleanup on removal. Direction comes from the
effective i18n context unless an ordinary `dir` ancestor overrides CSS layout.

## 12. Overlay and layering behavior

Value bubbles are contained presentation elements, not Popover/Tooltip
components. They do not portal, trap focus, dismiss, or escape overflow. The
family creates no global overlay, scroll lock, or stacking manager.

## 13. Collections, async data, and identity

Marks are a bounded server collection with canonical-value identity. They are
sorted by grid index; duplicate normalized values are errors. There is no async
data, virtualization, selection model, or mutable client collection. Thumb
identity is fixed even when values overlap.

## 14. Server render, morph, and cleanup

SSR is a useful native form control. Activation is idempotent, validates the
settled anatomy, hides native interaction, and reveals the styled control.
Morph token handoff preserves uncontrolled exact value(s), active thumb,
controlled ownership, focus, drag cancellation, and form reset baseline when
public identity remains. A morph during drag cancels pointer capture before
replacement; it never resumes a drag against new geometry. Removal releases
pointer capture, document listeners, form hooks, i18n format subscriptions,
Field invalid state, and token data. Late fragments format against their
logical provider's current locale before the custom control is revealed.

## 15. Security and content trust

All mark labels and values render as escaped text. Exact-decimal and mark
counts are bounded before serialization. Runtime code rejects unknown owned
identity, role, ARIA-value, form, and executable binding attributes. It never
uses `innerHTML`, `eval`, or caller-provided style expressions. Pointer
coordinates are clamped to settled track geometry before conversion to a grid
index. Callback results never become markup.

## 16. Assets and performance

The family owns one shared CSS block and one CSP-safe program used by both
components, plus existing Field/form and i18n services. Each instance adds
thumb/track/input listeners but no observer, timer, font, network request, or
permanent document listener. Pointer-move work is one geometry read at drag
start plus ratio/index writes scheduled at most once per animation frame.
Qualification records raw/gzip/Brotli deltas, 100-instance mount and key-step
cost, dense-mark cost, drag latency, and shared-asset uniqueness.

## 17. Acceptance matrix

Automated evidence covers exact normalization and integral grids; schema/type
exports; SSR/native fallbacks; Field/Form ownership; controlled/uncontrolled
single/range state; pointer capture and cancellation; tie-breaking; no-cross
gap constraints; all keys; stable Tab order; reset/native input/change;
readonly/disabled during drag; marks; orientations; RTL; localized digits and
live locale switch; explicit label overrides; dark/forced/reduced/zoom/touch;
morph/removal/late fragment; attribute attacks; 100 instances; docs/API;
standalone quality scenario; wheel; Chromium, Firefox, and WebKit.

Manual gates cover keyboard-only use; VoiceOver/Safari; NVDA/Firefox;
TalkBack/Chrome touch exploration; speech control; mouse, stylus, and coarse
touch drag; 400% zoom; long translated thumb/mark labels; light/dark/RTL/forced
colors; and real-device vertical controls.

Public examples are fixed before implementation:

| Module | Reader task and visible states | Controls / environments | Contract evidence |
|---|---|---|---|
| `basic.py` | volume slider in Field | value/min/max/step | basic form and keys |
| `range.py` | price interval | lower/upper values | fixed two-thumb contract |
| `exact_decimals.py` | opacity in tenths | decimal step | exact state/no float |
| `controlled.py` | owner-controlled slider | callbacks | control and end timing |
| `marks.py` | labeled discrete scale | marks/show_marks | identity and author text |
| `vertical.py` | vertical single and range | orientation | geometry and keys |
| `locales.py` | en-US, cs-CZ, ar-EG | locale/RTL switch | value text and direction |
| `forms.py` | repeated and distinct range names | submit/reset | fallback/transport |
| `states.py` | readonly, disabled, invalid, variants/sizes | theme | visual/state matrix |

The Python-owned scenario catalog maps these modules to docs previews,
standalone routes, Playwright, screenshots, axe, Lighthouse, and manual tasks.

## 18. Compatibility classification

Stable API includes both component/type names, documented inputs/callbacks,
exact canonical form values, public CSS variables/selectors/reflected attrs,
and translation keys. Behavioral contract includes fixed thumb identity,
non-crossing range, APG keys, callback timing, native fallback, form/reset,
controlled ownership, and locale formatting. Exact colors, dimensions, shadow,
and transition curves are evolvable. `.cui-*`, private variables, runtime
markers, frame scheduling, and incidental geometry wrappers are private.

## 19. Public documentation contract

`api.md` teaches when to choose Slider versus NumberInput, basic Field use,
RangeSlider identity and names, exact decimals, controlled state, marks,
vertical/RTL, forms, and locale formatting. `api.yml` exhaustively lists
Inputs, Events, CSS, Attributes, Selectors, Interfaces, and finally Translation
keys. There are no Slots or Methods. Every example above is result-first and
uses shared scenario data.

## 20. Open decisions and deferred work

No decision blocks implementation. Push/swap collisions, arbitrary thumb
counts, nonlinear scales, draggable whole ranges, tooltips with arbitrary
markup, marker click callbacks, tick-only snap sets, media scrubbing,
histograms, and a headless primitive are deferred separate jobs.

## 21. Internationalization

| Message ID | Variables | Override input | Browser update |
|---|---|---|---|
| `citry-ui-range-slider-lower` | none | `lower_label` | conditional `$c-tr` on lower thumb and fallback `aria-label` |
| `citry-ui-range-slider-upper` | none | `upper_label` | conditional `$c-tr` on upper thumb and fallback `aria-label` |

The package profile is `number.citry-ui-slider`. Single Slider requires an
application/CField accessible name and adds no generic component-authored
label. Formatted bubbles and `aria-valuetext` use the active profile rather
than a message. Exact state/form values remain canonical ASCII. Mark labels are
already localized by the application. Live locale changes, RTL pointer
geometry, source mode, server-only i18n, explicit range-label overrides, late
fragment adoption, and subscription cleanup are release evidence. The
structured component API repeats this table as its final section.
