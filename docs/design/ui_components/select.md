# Select

**Status:** production implementation pass completed on 2026-08-10. Runtime,
public reference/examples, quality wiring, server tests, and Chromium, Firefox,
and WebKit interaction evidence are checked in. Manual AT, live Safari Tab,
touch hardware, 400% zoom, and Nu HTML remain release-wide qualification work.

## 1. Purpose and product bar

`CSelect` is a compact, styled, single-value form control backed by a fixed
collection. It displays the selected label in a non-editable combobox trigger,
opens an owned Listbox popup, submits the stable value, participates in native
reset and validation, and composes with `CField` and `CForm`.

The family owns one public component plus one immutable data record:

- `CSelect` owns the trigger, popup, active descendant, single selection,
  controlled/uncontrolled state, form proxy, and overlay lifetime; and
- `CSelectOption` supplies one unique value, visible label, optional
  description and group label, and disabled state.

Product boundaries are deliberate:

- use `CNativeSelect` when browser-native popup behavior and the smallest
  runtime are more important than rich styling;
- use `CCombobox` when users search or edit text;
- use `CMultiSelect` for multiple compact selection;
- use `CListbox` when Options should remain visible; and
- use `CMenu` for actions rather than form values.

Production-complete means one stable selected value, one trigger Tab stop, one
active descendant while open, no selection on exploratory focus, native form
continuity, controlled request correctness, safe top-layer composition, exact
focus restoration, and coherent light/dark/RTL/forced-colors/narrow behavior.

## 2. Prior art and complaints

### Source record

| Product or standard | Version/review date | Surface inspected | Decision |
|---|---|---|---|
| WAI-ARIA APG | reviewed 2026-08-10 | current Combobox pattern, select-only combobox | use a focusable `role=combobox` trigger, `aria-controls`, `aria-expanded`, and `aria-activedescendant` into a Listbox popup |
| HTML | current 2026-08-10 | native select, form, reset, constraint validation, manual popover | keep a visually hidden native Select as the form truth and a manual-popover visual surface |
| React Aria | current 2026-08-10 | Select composition and current multi-selection change | keep label/trigger/value/popover/listbox anatomy; separate Citry single and multiple public families |
| Radix Select | current 2026-08-10 | trigger/value/content/items/viewport, controlled state | preserve exploratory highlight and commit only on activation |
| Ark Select | current 2026-08-10 | hidden Select, groups, overflow, controlled state, form integration | adopt hidden native form proxy and viewport-safe popup; omit async/virtualized breadth |
| Vuetify | 4.1.7/current source reviewed 2026-08-10 | VSelect versus VAutocomplete and multiple/chip modes | keep Select non-editable; place multiple selection in `CMultiSelect` |
| Citry UI | 2026-08-10 | Listbox, Combobox, NativeSelect, Field/Form, Popover/Menu, anchored-layer runtime | reuse value canonicalization, Field/Form ownership, top-layer coordination, and Listbox visual language without sharing incompatible focus state |

Recurring failures to avoid:

- treating a Select as a menu button, which loses value and required semantics;
- moving DOM focus into the popup while the trigger claims active-descendant
  focus;
- committing arrow exploration before Enter/Space/pointer activation;
- submitting the human label instead of the stable value;
- allowing a controlled rejected close to steal outside focus or trap Tab;
- using `display:none` form proxies that cannot participate in validation;
- reopening behind a closed Popover or active unrelated modal;
- letting option descriptions pollute the selected trigger label; and
- allowing built-in English placeholder or action prose to create a hidden
  localization dependency.

Citry therefore requires the visible `placeholder` string from the author,
uses labels as data, keeps item content plain, and delegates overlay safety to
the shared anchored-layer coordinator.

## 3. Public composition and anatomy

```citry-html
<c-CField>
  <c-fill name="label">Destination</c-fill>
  <c-fill name="default">
    <c-CSelect
      name="destination"
      placeholder="Choose a destination"
      c-options="destinations"
    />
  </c-fill>
</c-CField>
```

```python
from citry_ui import CSelect, CSelectOption

destination = CSelect(
    name="destination",
    placeholder="Choose a destination",
    options=(
        CSelectOption("prague", "Prague", "Czechia", group="Europe"),
        CSelectOption("kyoto", "Kyoto", "Japan", group="Asia Pacific"),
    ),
)
```

Stable rendered anatomy:

```text
div[root]
  button[control][role=combobox]
    span[value]
    span[indicator, aria-hidden]
  select[private native form proxy]
  div[popup][popover=manual]
    div[listbox][role=listbox]
      div[group][role=group]? -> span[group-label] + option*
      div[option][role=option] -> label + description?
```

`class_`, `style`, and `attrs` target the root. `trigger_attrs` target the
combobox Button; `listbox_attrs` target the Listbox. The hidden native Select,
manual-popover ownership, generated IDs, state relationships, and runtime
markers are owned.

`CSelectOption` is a frozen data record rather than a render component. It is
valid in Python sequences and in flat template expressions through
`c-options="..."`. This avoids declaration duplication between the visible
Listbox and hidden native Select.

## 4. Server inputs and client inputs

### `CSelect`

| Python input | Type | Default | Class | Validation/effect |
|---|---|---|---|---|
| `options` | `Sequence[CSelectOption]` | required nonempty | initial collection | unique nonempty canonical values and nonempty labels; contiguous groups are normalized |
| `placeholder` | `str` | required | structural | visible empty text; author-owned for localization |
| `name` | `str | None` | `None` | structural | native form field name |
| `form` | `str | None` | `None` | structural | explicit native form owner |
| `id` | `str | None` | Field ID/generated | structural | relationship identity |
| `value` | `str | None` | `None` | initial state | selected value; must match an Option |
| `open` | `bool` | `False` | initial state | initial popup request subject to eligibility |
| `required`, `disabled`, `readonly`, `invalid` | `bool | None` | Field/Form fallback | reactive fallback | semantics, interaction, proxy validity, Field state |
| `loop` | `bool` | `False` | reactive fallback | arrow navigation wrapping |
| `placement` | `bottom-start | bottom-end | top-start | top-end` | `bottom-start` | reactive fallback | logical preferred popup placement |
| `match_width` | `bool` | `True` | reactive fallback | popup uses trigger width unless viewport safety wins |
| `variant` | `outline | filled | plain` | `outline` | reactive fallback | visual treatment |
| `size` | `sm | md | lg` | `md` | reactive fallback | control and Option geometry |
| `class_`, `style` | Citry class/style value | `None` | structural | root styling |
| `attrs`, `trigger_attrs`, `listbox_attrs` | mapping | `None` | structural | trusted attributes bounded by ownership |

| Client input | Type | Omitted/null | Invalid | Effect |
|---|---|---|---|---|
| `value` | nonempty string or `null` | omission releases; null controls empty | diagnose once per invalid episode and release from committed value | selected value, visible label, proxy value, validity |
| `open` | Boolean or `null` | omission/null releases to committed internal state | diagnose and release | popup visibility and active descendant |
| `required`, `disabled`, `readonly`, `invalid`, `loop`, `matchWidth` | Boolean | server/Field/Form fallback | diagnose and use fallback | semantics, interaction, geometry |
| `placement`, `variant`, `size` | documented enum | server fallback | diagnose and use fallback | reflection and styling |
| `onValueChange` | function | none | diagnose and ignore | selection/reset/structure requests |
| `onOpenChange` | function | none | diagnose and ignore | visibility and forced-close notices |

`CSelectOption(value, label, description=None, disabled=False, group=None)` is
immutable. Every string is canonicalized CRLF/CR to LF and rejects U+0000;
value and label are nonempty. Group is optional but nonempty when supplied.
Repeated group names create one group only when their Options are contiguous;
noncontiguous reuse is rejected so the visual and native orders remain exact.

## 5. State model

Value and open are independent ownership axes. Highlight is internal and
ephemeral.

| Trigger | Value | Open/highlight | Form/events |
|---|---|---|---|
| trigger click, Enter, Space | unchanged | request open; highlight selected or first enabled | open callback only |
| closed ArrowDown/ArrowUp | unchanged | request open with first/last or selected highlight | open callback only |
| open arrows/Home/End/typeahead | unchanged | move active descendant | none |
| open Enter/Space or Option click | request highlighted/target value | request close | value callback then open callback; uncontrolled proxy dispatches native `input`, then `change` |
| Escape | unchanged | request close; discard highlight | open callback; restore trigger focus only when focus remains owned |
| Tab/Shift+Tab | unchanged | request close | browser order continues; no focus return |
| outside pointer/focus | unchanged | request close | outside target keeps focus; one request per physical gesture |
| owner value/open update | apply without callback | reconcile | no native events |
| native Form reset | request server value, close | controlled axes reassert | value/open callbacks for changed uncontrolled axes; no native input/change |
| effective disabled/readonly | preserve value | forced close | forced notice only when visible state changed; focus follows Field/form policy |
| selected Option removed by morph | request `null` | close if open and collection no longer represents value | one structure value request |
| ancestor/modal safety close | preserve value | force closed and suppress until a fresh edge | forced open callback with public reason `ancestor` |

Controlled requests never mutate the controlled axis before owner acceptance.
A valid owner commit after a request wins. Omission releases to the last
committed visible state. Invalid client supply releases rather than creating a
third fallback state.

## 6. Slots and slot data

`CSelect` has no public slots in v1. Option labels and descriptions are plain
data. This keeps the selected-value projection, native proxy, typeahead text,
and accessible names identical and prevents nested interactive descendants.

Arbitrary renderers, icons, avatars, actions, loading/empty slots, and async
collections are deferred. `CCombobox` owns async search; richer fixed Select
rendering requires a separately reviewed browser renderer.

## 7. Callbacks, native events, and methods

`onValueChange(next, detail)` receives:

- `value`, `previousValue`, `option`, `controlled`;
- `source`: `pointer`, `keyboard`, `reset`, or `structure`; and
- `sourceEvent` or `None`.

`onOpenChange(next, detail)` receives:

- `open`, `reason`, `controlled`, `forced`, and `source`;
- reasons `trigger`, `keyboard`, `selection`, `escape`, `tab`, `outside`,
  `focus-outside`, `reset`, `native`, or `ancestor`.

Value notification precedes close notification for selection. Callback
reentrancy is generation-checked: removal or modal opening during the value
callback prevents stale selection-close work. Modal/ancestor safety closes
immediately and defer their notice until an active selection transaction
unwinds.

Uncontrolled user commits dispatch native `input` then `change` from the
hidden Select after state and validity settle. Controlled requests and owner
commits dispatch neither. There are no custom DOM events or public methods.

## 8. Semantics, keyboard, focus, and assistive technology

The Button has `role=combobox`, `aria-haspopup=listbox`, `aria-expanded`,
`aria-controls`, and when open `aria-activedescendant`. It is labelled by
`CField` or trusted static trigger naming. The popup collection has
`role=listbox`; each entry has `role=option` and Boolean `aria-selected`.
Groups use `role=group` with visible `aria-labelledby` labels.

DOM focus stays on the combobox Button while open. Options are not Tab stops.

| State | Key | Result |
|---|---|---|
| closed | Enter/Space/click | open and highlight selected/first enabled |
| closed | ArrowDown | open; selected or first enabled highlight |
| closed | ArrowUp | open; selected or last enabled highlight |
| closed | printable | buffered matching Option becomes selected immediately |
| open | ArrowDown/ArrowUp | next/previous enabled highlight |
| open | Home/End | first/last enabled highlight |
| open | printable | buffered typeahead highlight |
| open | Enter/Space | commit highlight and close |
| open | Escape | close without selection change |
| open | Tab/Shift+Tab | close and continue ordinary page order |

Disabled Options are skipped and never activated by pointer, keyboard, or
programmatic click. Typeahead normalizes whitespace, supports repeated-letter
cycling and Shift characters, ignores composition/control shortcuts, and
falls back safely for invalid inherited `lang` values.

## 9. Native forms and validation

A progressively enhanced native `<select>` is the form truth. Before client
initialization it remains visible and operable while the custom trigger is
hidden. After initialization it is visually clipped and carries `name`,
`form`, `required`, `disabled`, `autocomplete` when later added, every Option
value/disabled state, and the selected value. It leaves the accessibility tree
and Tab order while remaining a programmatic validation candidate; an invalid
event moves focus to the visible trigger and informs Field native-invalid
state.

FormData submits exactly one selected stable value, or nothing while empty.
Native reset is cancelable; after an uncanceled reset task the component
restores its server fallback when uncontrolled and requests that value when
controlled. Programmatic state synchronization emits no native events.

Inside `CField`, Field owns required/disabled/readonly/invalid and concrete
relationships. Explicit competing component state raises server-side.
Standalone `CForm.disabled` remains dominant. `CForm.readonly` is inherited by
the custom Select because it has a defined read-only behavior.

## 10. Styling and theme contract

Variants: `outline`, `filled`, `plain`. Sizes: `sm`, `md`, `lg`.

Public variables:

| Variable | Purpose | Default |
|---|---|---|
| `--cui-select-background` | control/popup surface | `Canvas` |
| `--cui-select-foreground` | primary text | `CanvasText` |
| `--cui-select-placeholder-color` | empty value | scheme-aware muted |
| `--cui-select-muted-color` | descriptions/disabled | scheme-aware muted |
| `--cui-select-border-color` | outline | scheme-aware subtle border |
| `--cui-select-hover-background` | Option hover | CanvasText mix |
| `--cui-select-selected-background` | selected Option | scheme-aware blue |
| `--cui-select-selected-foreground` | selected Option text | scheme-aware blue text |
| `--cui-select-focus-color` | focus ring | `Highlight` |
| `--cui-select-radius` | control/popup corners | `0.625rem` |
| `--cui-select-control-padding` | control geometry | size-derived |
| `--cui-select-option-padding` | Option geometry | size-derived |
| `--cui-select-max-block-size` | popup scroll boundary | `18rem` |
| `--cui-select-offset` | anchor gap | `0.25rem` |
| `--cui-select-shadow` | popup elevation | scheme-aware shadow |
| `--cui-select-duration` | entry/exit motion | `120ms` |

Stable selectors: `root`, `control`, `value`, `indicator`, `popup`, `listbox`,
`group`, `group-label`, `option`, `option-label`, `option-description`.

Public state reflections: root `data-open`, `data-empty`, `data-required`,
`data-disabled`, `data-readonly`, `data-invalid`, `data-variant`, `data-size`,
and `data-match-width`; Option `data-value`, `data-selected`,
`data-highlighted`, and `data-disabled`; popup `data-placement` reflects the
preferred logical placement.

The control reflects effective capability and validation through
`aria-required`, `aria-disabled`, `aria-readonly`, and `aria-invalid` only when
the corresponding state applies.

## 11. Environmental behavior

- logical placement and CSS properties support RTL;
- popup maximum inline/block size preserves narrow and 400% zoom layouts;
- viewport maximum wins over match-width when the trigger is wider;
- long labels/descriptions wrap without horizontal overflow;
- top-layer color scheme follows live ancestry rather than a stale snapshot;
- reduced motion removes transition/animation duration;
- forced colors use system border, highlight, and focus colors; and
- print renders the closed control only and never the popup.

Touch uses click activation and never pointerdown opening. Pen contact behaves
like click, not hover. The component has no hover-open path.

## 12. Overlay and layering behavior

The popup is `popover=manual` and registers with the shared anchored-layer
coordinator. Every open path calls `mayOpen()` then `register()`. The layer
record uses trigger/surface, exact open state, dismissal requests, forced close,
and Select-specific effective eligibility.

Outside pointer/focus closes without preventing the outside action. Escape
closes the Select before ancestors. Opening an unrelated modal force-closes the
Select before the modal owns Escape. Closed Popover/Dialog ancestry, hidden or
inert ancestry, disconnected trigger/surface, or an ineligible active modal
suppress opening. Parent close and cleanup cascade through coordinator
ownership.

Placement uses CSS anchor positioning. Preferred logical `bottom-start`,
`bottom-end`, `top-start`, or `top-end` is publicly reflected while the popup
is clamped to the viewport. Collision fallback is browser/CSS-owned and does
not create a second public actual-placement reflection in v1.

## 13. Collections, async data, and identity

Server Options are canonical, unique, ordered, and nonempty. Disabled values
stay represented in the form proxy and Listbox but cannot become a user
selection. An initially selected disabled value is allowed for truthful server
display but cannot be reselected after change.

Server morph can add, remove, reorder, relabel, regroup, or disable Options.
Retained selected value rehydrates its current label. Removed uncontrolled
selection requests/commits `null` once; controlled missing value renders empty
and requests `null` once until accepted, released, or the value returns.
Highlight recovers to the nearest enabled survivor with following-sibling tie.

Client item replacement, async loading, virtualization, and object identity are
deferred. `CCombobox` remains the async searchable path.

## 14. Server render, morph, and cleanup

Without JavaScript, the browser-native Select is visible, labelled, operable,
submittable, resettable, and validatable while the custom trigger and popup are
hidden. After successful initialization, the custom trigger becomes visible,
the proxy is clipped and removed from ordinary Tab navigation, and proxy focus
or invalid handling redirects to the trigger. A failed initializer therefore
leaves the native fallback intact rather than a dead painted control.

Correlated morph transfers committed value/open intent, selected identity,
highlight identity, and pending controlled structural episode only when the
server value fallback remains the same. Unrelated presentation/config changes
must not reset an uncontrolled user value or open state. A changed server value
fallback deliberately resets uncontrolled committed value.

Cleanup invalidates generations, cancels timers/animations/rAF, removes native
listeners/observers, unregisters the layer with descendant cascade, clears
Field native-invalid state, and removes the private readiness marker.

## 15. Security and content trust

Option text is escaped plain data; matching reads text/data and never HTML.
Values are data only and never enter executable source. Attribute maps are
trusted application surfaces but cannot replace owned IDs, semantics, form
identity, state, visibility, focus, popover/command ownership, Citry markers,
or structural Alpine directives.

Reject static and dynamic/property aliases for owned attributes. Reject object
spreads, `x-html`, `x-text`, `x-if`, `x-for`, `x-show`, `x-teleport`, `x-ignore`,
`x-model`, and `x-modelable` where they could replace or suppress owned
runtime/children. Root and trigger reject `aria-hidden`, `role`, `tabindex`,
`contenteditable`, `hidden`, `inert`, and `popover`. The trigger permits static
ARIA naming only when no Field naming relationship exists; dynamic naming is
rejected.

The hidden Select is not an attrs destination. Option values/labels/groups and
direct strings reject U+0000; IDs reject empty/ASCII whitespace.

## 16. Assets and performance

The family ships one CSS asset and one client initializer plus the deduplicated
shared anchored-layer dependency. One root owns trigger keyboard/click,
popover toggle, form reset/invalid, and a bounded structural/fieldset observer.
Document/ShadowRoot dismissal listeners are shared and exist only while layers
are open.

Initialization and reconciliation are O(N), using Maps/Sets rather than nested
duplicate searches. Closed roots install no per-root global listener. Quality
reporting records raw/gzip/Brotli family assets and bounded 1/10/100/500/1000
server render/output measurements.

## 17. Acceptance matrix

Checked-in server evidence must cover:

- exact public schemas, exports, registration, option canonicalization,
  duplicate/noncontiguous groups, value membership, Field/Form ownership;
- hidden native Select anatomy, names/form/required/disabled/selected Options,
  no-JS fallback, IDs/ARIA, trusted attrs, hostile strings, CSS variables and
  public selectors; and
- complete API schema, snippets, docs discovery, scenario/asset/catalog wiring.

Checked-in browser evidence in Chromium/Firefox/WebKit must cover:

- trigger click/Enter/Space/arrows, open highlight, Home/End/typeahead,
  activation, Escape, Tab continuation, outside dismissal and dedupe;
- controlled value/open reject/accept/release, callback order, native
  input/change ordering, FormData/reset/required invalid focus, Field native
  error episode, disabled/readonly/fieldset transitions;
- structural remove/relabel/disable/reorder, same-value morph, cleanup and
  listener/layer baseline;
- closed ancestor/unrelated modal/ShadowRoot safety and forced reason mapping;
- actual placement, match width clamp, narrow/RTL/long content, light/dark,
  forced colors, reduced motion, print, public token overrides; and
- accessible name/value/description/active descendant plus serious/critical
  Axe cleanliness.

Manual release evidence names VoiceOver/Safari, NVDA/Firefox or Chromium,
JAWS/Chromium, live Safari Tab order, mobile touch, 200%/400% zoom, and visual
review in light/dark/RTL/forced-colors/print. Nu HTML validation remains part of
the normal release gate when Java is available.

## 18. Compatibility classification

Stable public compatibility surface:

- `CSelect`, `CSelectOption`, all Python/client inputs and callback details;
- form value/reset/validity behavior and Field/Form composition;
- roles, relationships, keyboard, focus, controlled semantics, reflections;
- public parts, variants, sizes, and CSS variables.

Private/evolvable:

- generated ID format, hidden proxy classes/markers, initialization marker;
- exact internal Maps, timer/rAF/animation mechanics;
- collision-algorithm refinements beyond the documented preferred placement
  and viewport clamp; and
- shared coordinator protocol.

## 19. Public documentation contract

Public docs provide:

1. at-a-glance Field composition;
2. standalone accessible naming;
3. grouped and described Options;
4. controlled value/open state;
5. required FormData/reset/validation;
6. disabled and read-only behavior;
7. keyboard/typeahead behavior;
8. placement and match width;
9. variants and sizes; and
10. token customization.

Examples use author-supplied visible strings, contain no intentional invalid
client supplies, and produce no console/page errors. Reference data enumerates
every public input, callback, interface, variable, selector, and reflection.

## 20. Open decisions and deferred work

Resolved:

- Select is a select-only combobox, not a menu button;
- it is single-value only; `CMultiSelect` is separate;
- focus remains on the trigger with active descendant;
- a hidden native Select owns forms and validation;
- Options are immutable data records in v1;
- placeholder is author-required rather than built-in localized prose; and
- the popup uses the shared manual-popover coordinator.

Deferred:

- arbitrary rich Option renderers, icons, avatars, actions;
- client collection replacement, async/virtualized collections;
- create-new/free text and search (`CCombobox` owns these);
- mobile native-sheet substitution; and
- public imperative focus/open methods.

Any future addition that changes value type, form serialization, accessible
focus, popup ownership, or content trust requires a new design review.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
