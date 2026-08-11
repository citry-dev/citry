# MultiSelect

**Status:** production implementation pass completed on 2026-08-10. Checked-in
evidence covers server contracts, public docs/quality integration, and focused
Chromium, Firefox, and WebKit behavior. Manual AT, hardware, zoom, and Nu HTML
sessions remain release evidence.

## 1. Purpose and product bar

`CMultiSelect` is a compact form control for choosing several values from a
fixed collection. Selected labels appear as visual chips in the trigger; an
owned Listbox popup toggles Options without filtering text; and a native
multiple Select remains the form, reset, and validity truth.

Use `CListbox(multiple=True)` when choices should remain visible, `CSelect` for
exactly one compact value, and `CCombobox` when filtering or arbitrary text is
the primary job.

## 2. Prior art and complaints

Reviewed 2026-08-10: current WAI-ARIA Listbox and Combobox APG patterns; React
Aria Select multiple-selection composition; Ark Select multiple mode; Vuetify
Select multiple/chips; Radix Select's deliberate single-value boundary; and
the repository's CSelect, CListbox, Combobox, Tag, Field, Form, Popover, Menu,
and anchored-layer contracts.

Adopt: multiselect Listbox semantics, native repeated-value form truth,
controlled request semantics, chip-like noninteractive value presentation,
and popup persistence while toggling. Reject: editable filtering, arbitrary
value creation, interactive remove Buttons inside the combobox trigger,
virtualization, async fetching, and a second bespoke overlay stack.

## 3. Public composition and anatomy

Public exports:

- `CMultiSelect`; and
- frozen `CMultiSelectOption(value, label, description=None, disabled=False,
  group=None)`.

Stable anatomy is root `div`; native `<select multiple>`; custom
`button[role=combobox]`; value/chip/indicator spans; manual-popover popup;
`div[role=listbox][aria-multiselectable=true]`; optional labelled Groups; and
Options. Before initialization the custom surfaces are hidden and the native
multiple Select is visible. After successful initialization the custom control
is visible and the proxy is visually clipped, out of the AX tree and Tab order.

## 4. Server inputs and client inputs

| Input | Type | Default | Contract |
|---|---|---|---|
| `options` | `Sequence[CMultiSelectOption]` | required | nonempty ordered unique fixed collection |
| `placeholder` | `str` | required | author-localized empty trigger copy |
| `name`, `form`, `id` | `str | None` | `None` | native form/identity ownership |
| `value` | `Sequence[str] | None` | `None` | initial selected values in collection order |
| `open` | `bool` | `False` | initial eligible popup visibility |
| `required`, `disabled`, `readonly`, `invalid` | `bool | None` | `None` | standalone state; Field owns when composed |
| `loop` | `bool` | `False` | arrow edge wrapping |
| `close_on_select` | `bool` | `False` | close after each accepted toggle |
| `placement` | logical placement | `bottom-start` | preferred popup position |
| `match_width` | `bool` | `True` | match popup/control inline size within viewport |
| `variant` | `outline | filled | plain` | `outline` | control treatment |
| `size` | `sm | md | lg` | `md` | control, chip and Option geometry |
| `class_`, `style`, `attrs` | trusted root attrs | empty | root customization |
| `trigger_attrs`, `listbox_attrs` | trusted mappings | empty | bounded destination attrs |

Direct strings are de-trusted, CRLF/CR canonicalized to LF, nonempty where
required, and reject U+0000. IDs reject ASCII whitespace. Values are unique;
groups are contiguous; and selected values must be unique known values.

## 5. State model

Client inputs are `value`, `open`, state/config counterparts, `onValueChange`,
and `onOpenChange`. Supplied `value: string[]` controls selection; omission or
`null` releases to the committed selection (unlike CSelect, an empty supplied
array is the explicit controlled-empty value). Supplied Boolean `open` controls
visibility; `null`/omission releases it.

Invalid values report once per continuous invalid episode and use the server
fallback for configuration or release selection/open control. Controlled user
requests notify but do not mutate. Forced disabled/ancestor/modal/invalid-tree
closures always hide and report one forced close. Correlated reinitialization
retains committed selection/open state when their server baselines are
unchanged; stale tasks cannot affect replacements.

## 6. Slots and slot data

Selected Options render one noninteractive `chip` span each, in collection
order. Empty selection renders only the placeholder. The trigger owns
`aria-controls`, `aria-expanded`, and open `aria-activedescendant`; the Listbox
owns `aria-multiselectable=true`; every Option owns `aria-selected`.

Standalone use requires static `aria-label` or `aria-labelledby` in
`trigger_attrs`. Field supplies concrete label/description/error IDs and rejects
competing naming. Option descriptions remain separate through
`aria-describedby`; decorative indicators are hidden from accessibility APIs.
The trigger reflects `role=combobox`, `aria-controls`, `aria-expanded`, open
`aria-activedescendant`, and effective `aria-required`, `aria-disabled`,
`aria-readonly`, and `aria-invalid`. The popup collection reflects
`role=listbox` and `aria-multiselectable=true`; every Option reflects
`role=option` and `aria-selected`.

## 7. Callbacks, native events, and methods

`onValueChange(next, detail)` receives copied `value`, `previousValue`,
activated `option`, resulting `selected`, `controlled`, source
`pointer | keyboard | reset | structure`, and source event. `onOpenChange`
receives `open`, reason, `controlled`, `forced`, and source.

An enabled toggle invokes value callback first, then optionally requests close
when `close_on_select=True`, with generation/connectedness rechecks between.
Uncontrolled user commits dispatch native bubbling `input` then `change` from
the multiple Select. Programmatic synchronization emits neither.

## 8. Semantics, keyboard, focus, and assistive technology

DOM focus remains on the combobox Button. Closed Enter/Space/Down opens at the
first selected/first enabled Option; Up opens at the last selected/last enabled.
Open Up/Down, Home/End, buffered typeahead, Enter/Space toggle, Escape close,
and Tab close/continue. Disabled Options are skipped and never toggle.

Click—not pointerdown—opens and toggles. Pointer hover may update highlight for
mouse or non-contact pen; touch/pen contact does not hover-open. Focus never
enters popup Options.

## 9. Native forms and validation

The native `<select multiple>` owns `name`, `form`, selected/disabled Options,
required validity, FormData, and reset. FormData submits one entry per selected
value in collection order and none while empty. Required means at least one.
Readonly disables the native Select and uses repeated hidden inputs to preserve
submission. Disabled contributes nothing.

Before JS, the native multiple Select remains visible and operable. Invalid
events move focus to the custom control after initialization and inform Field.
Uncontrolled reset returns to the server selection after the reset task;
controlled reset requests it without mutating first.

## 10. Styling and theme contract

Variants `outline`, `filled`, `plain`; sizes `sm`, `md`, `lg`. Public variables:
`--cui-multi-select-background`, `--cui-multi-select-foreground`,
`--cui-multi-select-placeholder-color`, `--cui-multi-select-muted-color`,
`--cui-multi-select-border-color`, `--cui-multi-select-hover-background`,
`--cui-multi-select-selected-background`,
`--cui-multi-select-selected-foreground`,
`--cui-multi-select-chip-background`, `--cui-multi-select-chip-foreground`,
`--cui-multi-select-focus-color`, `--cui-multi-select-radius`,
`--cui-multi-select-control-padding`, `--cui-multi-select-option-padding`,
`--cui-multi-select-max-block-size`, `--cui-multi-select-offset`,
`--cui-multi-select-shadow`, and `--cui-multi-select-duration` (indicator
rotation motion).

Stable parts: `root`, `control`, `values`, `placeholder`, `chip`, `indicator`,
`popup`, `listbox`, `group`, `group-label`, `option`, `option-label`, and
`option-description`. Stable public reflections include root `data-open`,
`data-empty`, `data-required`, `data-disabled`, `data-readonly`, `data-invalid`,
`data-close-on-select`, `data-match-width`, `data-variant`, `data-size`; Option
`data-value`, `data-selected`, `data-highlighted`, `data-disabled`; and popup
preferred `data-placement`.

## 11. Environmental behavior

Logical layout supports RTL; chips wrap; long labels break; popup scrolls and
is viewport-clamped; viewport safety wins over match width. Live inherited
color-scheme reaches top-layer popup. Reduced motion removes duration; forced
colors use system border/highlight; reduced motion removes indicator rotation;
print shows only the closed control.

## 12. Overlay and layering behavior

The manual popover uses the shared anchored-layer coordinator. Every open path
passes `mayOpen` and `register`. Outside press/focus and Escape dismiss in stack
order; unrelated modal and closed/hidden/inert ancestors force-close with
public `ancestor`; cleanup cascades. Structural suppression requires a fresh
false/released edge before controlled true may reopen.

## 13. Collections, async data, and identity

Fixed server Options may morph add/remove/reorder/relabel/regroup/disable.
Removed selected values are dropped once in the requested next collection;
controlled owners receive one structural request until accepted/released or the
values return. Highlight recovers to nearest enabled survivor. Async/loading,
virtualization and custom renderers are deferred.

## 14. Server render, morph, and cleanup

One component instance, one shared anchored dependency, one root click/pointer
listener, one key listener, one toggle listener, native reset/invalid hooks,
and bounded ancestor-fieldset observers. Closed instances own no global overlay
listener. Reconciliation snapshots Options and selected Sets once per pass.
Quality tools record 1/10/100/500/1000 server output and asset bytes.

## 15. Security and content trust

All attrs are copied. Root/listbox/trigger reject owned identity, semantics,
focus, visibility, popover/command ownership, structural directives, runtime
markers, `aria-hidden`, role/tabindex/contenteditable, and object spreads.
Static trigger naming/description relationships are extracted once; dynamic
writers to owned IDREFs are rejected. Option strings render as text only; no
HTML/eval path exists.

## 16. Assets and performance

Invalid server inputs raise before output. Invalid client inputs diagnose once
and recover on valid/omitted input. Failed open normalizes fully closed/inert.
Missing anatomy or invalid settled structure fails closed, omits readiness, and
may recover after a valid morph. Empty/disabled collections cannot open.

## 17. Acceptance matrix

Server evidence covers schema/types, normalization, groups, forms, Field/Form,
readonly repeated hidden inputs, attrs/security, public parts/tokens, fallback,
and hostile strings. Browser evidence across Chromium/Firefox/WebKit covers
open/toggle/control/release, keyboard/typeahead/Tab, FormData/reset/validity,
disabled/readonly/fieldset, overlay/modal/ShadowRoot safety, geometry, RTL,
themes, reduced motion, forced colors, print, cleanup and Axe.

Manual release evidence remains VoiceOver/Safari, NVDA/Firefox or Chromium,
JAWS/Chromium, live Safari Tab, touch/pen hardware, 400% zoom and Nu HTML.

## 18. Compatibility classification

Public: exports, input/callback schemas, form behavior, keyboard/focus, ARIA,
parts, reflections, variables, variants and sizes. Private: generated IDs,
native proxy markers, readiness marker, exact maps/timers/animation, shared
coordinator protocol, and collision refinement beyond preferred placement.

## 19. Public documentation contract

Required examples: at a glance Field, form/repeated values, grouped Options,
controlled selection, empty/disabled/readonly/invalid, close-on-select,
variants/sizes, keyboard, and customization. Docs tests discover every preview,
initialize it, exercise selection/form output, scan Axe, and reject console or
page errors.

## 20. Open decisions and deferred work

- Separate family rather than overloading CSelect's scalar contract.
- Visual chips are noninteractive; Option toggles are the single removal path.
- Popup stays open by default; `close_on_select` is explicit.
- Placeholder remains required author-localized text until Citry UI i18n lands.
- Filtering, arbitrary values, async loading, virtualization, interactive chip
  removal, max-count messaging, and rich Option slots are deferred.

Changing multiple-value type, repeated form serialization, focus model, native
fallback, or overlay ownership requires a new design review.
