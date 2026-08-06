# Citry UI Combobox specification

**Status (2026-08-06): production contract implemented. Structured reference,
nine public examples, and focused server/browser tests are complete. The full
Phase 7.5 release matrix plus human visual, content, keyboard,
assistive-technology, and real-device review remain.** `CCombobox` is a styled
editable single select. A submitted value must match an option. It is closest
to Vuetify `VAutocomplete`, not free-entry `VCombobox`.

## 1. Purpose and product bar

`CCombobox` lets a user search a known collection, choose one option, and keep
its stable value separate from its human label. It must work without consumer
CSS, with local or remote options, native forms, keyboard, pointer, touch, IME,
assistive technology, independent browser ownership, Field/Form composition,
server replacement, and requests that resolve out of order or ignore abort.

Production-complete means:

- DOM focus stays on the editable input while an active option is exposed with
  `aria-activedescendant`;
- canonical value, editable query, popup visibility, highlight, collection,
  loading, and error state cannot silently overwrite one another;
- selecting, clearing, typing, resetting, and owner commits have exact callback
  and native-event behavior;
- remote loading debounces, aborts, rejects stale results, escapes content, and
  cleans up;
- a missing browser initializer cannot let edited display text submit an old
  hidden value;
- light, dark, RTL, forced-colors, narrow, zoomed, and touch layouts remain
  usable; and
- every public input, callback, slot, part, variable, reflected attribute, and
  interface is documented and tested.

Common jobs are first-class:

| Job | Shortest contract |
|---|---|
| Search and choose locally | `CCombobox(options=...)` or `<c-CCombobox c-options="options" />` |
| Submit a stable key | add `name="planet_id"`; omit `name` when no form value is needed |
| Explain options | set `description` on each `CComboboxOption` |
| Start from a selection | set `value`; its matching label becomes the initial query |
| Search remotely | pass `loadOptions` through `$c-props` |
| Avoid noisy remote requests | set `min_chars` and `debounce_ms` |
| Open when focused | set `open_on_focus=True` or client `openOnFocus` |
| Highlight the first match while typing | set `auto_highlight=True` or client `autoHighlight` |
| Control selection, query, or popup | pass `value`, `inputValue`, or `open` independently through `$c-props` |
| Clear or reset | use the built-in clear Button or a native Form reset |
| Disable, require, or describe the control | compose with `CField` and `CForm` |
| Adjust appearance | use `variant`, `size`, `class_`, `style`, public variables, or allowed attributes |

Minimal template use:

```citry-html
<c-CCombobox
  c-options="planets"
  placeholder="Choose a planet"
/>
```

Minimal Python composition:

```python
from citry_ui import CCombobox, CComboboxOption

planet_picker = CCombobox(
    options=(
        CComboboxOption("mars", "Mars"),
        CComboboxOption("saturn", "Saturn"),
    ),
)
```

Phase 7 supports strict single selection only. Free values, create-new,
multiple selection and tags, grouping, pagination, infinite loading,
virtualization, interactive option content, and arbitrary browser renderers
change the data or accessibility model and remain separate later work. A
headless API is parked until real application use establishes one.

## 2. Prior art and complaints

The family was re-audited from its runtime, render and browser tests, quality
scenario, structured API, public guide, and composed uses. Existing behavior
remained provisional wherever those artifacts disagreed.

### Source record

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Citry UI prototype | 2026-08-06 | `ccombobox.py`, focused browser tests, quality scenario, `api.md`, and `api.yml` | Keep local and remote strict selection, independent public axes, Field/Form integration, and token model. Repair ownership coupling, collection loss, abort coverage, reset, sizes, server output, and public examples. |
| WAI-ARIA APG | reviewed 2026-08-06 | [Combobox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/) | Editable strict list autocomplete, input focus, active descendant, popup indicator Tab behavior, keyboard, and native text editing. |
| HTML and MDN | reviewed 2026-08-06 | [HTML datalist](https://html.spec.whatwg.org/multipage/form-elements.html#the-datalist-element), [MDN datalist](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/datalist), and [Popover API](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API) | Native datalist is suggestions rather than strict styled selection. Keep the inline popup now; evaluate native popover before accepting clipping forever. |
| Vuetify | 4.1.7 source reviewed 2026-08-06 | [`VAutocomplete.tsx`](https://github.com/vuetifyjs/vuetify/blob/v4.1.7/packages/vuetify/src/components/VAutocomplete/VAutocomplete.tsx), [`VCombobox.tsx`](https://github.com/vuetifyjs/vuetify/blob/v4.1.7/packages/vuetify/src/components/VCombobox/VCombobox.tsx), and [`VSelect.tsx`](https://github.com/vuetifyjs/vuetify/blob/v4.1.7/packages/vuetify/src/components/VSelect/VSelect.tsx) | Use `VAutocomplete` as the closest product reference. Confirm filtering, disabled options, clear/open controls, controlled selection and query, rich item needs, and breadth that belongs in later products. |
| React Spectrum | current docs reviewed 2026-08-06 | [ComboBox](https://react-spectrum.adobe.com/ComboBox) | Confirm distinct selected key and input value, strict versus custom values, static and async collections, supporting descriptions, Forms, and popup trigger modes. |
| React Aria | current docs reviewed 2026-08-06 | [ComboBox](https://react-aria.adobe.com/ComboBox) | Confirm current primitive breadth, controlled axes, collection and async composition, parts, and accessibility behavior. Do not confuse it with the styled Spectrum product. |
| MUI | current docs reviewed 2026-08-06 | [Autocomplete guide](https://mui.com/material-ui/react-autocomplete/) and [API](https://mui.com/material-ui/api/autocomplete/) | Confirm auto-highlight, open-on-focus, async search, callback reasons, grouping, free values, browser autofill limitations, and portal tradeoffs. Keep Citry's narrower direct API. |
| Ark and Chakra | current docs reviewed 2026-08-06 | [Ark Combobox](https://ark-ui.com/docs/components/combobox) and [Chakra Combobox](https://next.chakra-ui.com/docs/components/combobox) | Confirm highlighted/query/value/open axes, input behavior, rehydration, async collections, grouping, virtualization, and custom values. |
| Headless UI | current docs reviewed 2026-08-06 | [Combobox](https://headlessui.com/react/combobox) | Confirm object identity mapping, hidden form output, portals, virtual options, and application-owned async behavior. |
| PrimeVue | current docs reviewed 2026-08-06 | [AutoComplete](https://primevue.org/autocomplete/) | Confirm force-selection, suggestions, groups, virtualization, loading, forms, and option templates. Do not copy its highlighted-item Tab selection. |
| Failure reports | status reviewed 2026-08-06 | [Vuetify #17573](https://github.com/vuetifyjs/vuetify/issues/17573), [Vuetify #22531](https://github.com/vuetifyjs/vuetify/issues/22531), [React Spectrum #4016](https://github.com/adobe/react-spectrum/issues/4016), [MUI #18784](https://github.com/mui/material-ui/issues/18784), [MUI #29727](https://github.com/mui/material-ui/issues/29727), [MUI #25417](https://github.com/mui/material-ui/issues/25417), [Headless UI #1177](https://github.com/tailwindlabs/headlessui/issues/1177), [Headless UI #2932](https://github.com/tailwindlabs/headlessui/issues/2932), and [Zag #2936](https://github.com/chakra-ui/zag/issues/2936) | Treat query/selection synchronization, exact reasons, object identity, virtualization, blur, async transitions, and portal navigation as explicit failure modes. Issue reports are historical evidence, not claims about current unresolved behavior. |

Common shortcomings informed the contract:

- selection and query control often become coupled, leaving stale visible or
  submitted state;
- blur or Tab can accidentally commit a highlight;
- an older remote response can replace a newer result even after abort;
- object equality and duplicate identity create confusing selection bugs;
- rich renderers can hide accessible text or introduce interactive descendants;
- portal, mobile keyboard, and virtualized positioning behavior need dedicated
  evidence; and
- browser autofill can edit visible text independently of a hidden canonical
  input.

Citry adopts unique string values, independent control axes, a typed plain-text
item shape, optional first-match highlight, optional focus opening, and owned
remote request safety. It rejects implicit free values, implicit selection on
blur or Tab, arbitrary object equality, and an unproven browser renderer.

Vuetify carries roughly 30 percent of comparative decision weight:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `modelValue` | direct client API | `value`, `onValueChange` | adopt string-or-null controlled selection |
| `search` | direct client API | `inputValue`, `onInputValueChange` | adopt as an independent axis |
| menu model | direct client API | `open`, `onOpenChange` | adopt as an independent axis |
| `items`, item title and value | direct API | `options`, client `items`, `{value, label}` | adopt a narrow explicit record |
| item subtitle | direct API | optional `description` | adopt safe supporting text |
| item comparator and return object | data-model choice | unique string value | reject object equality and object form output |
| filtering and `filterKeys` | direct API | `filter` | adopt `contains`, `starts_with`, or `none`; defer arbitrary filter callbacks |
| `autoSelectFirst` | direct API | `auto_highlight` | adopt Boolean first-match highlight without implicit blur selection |
| clear and menu controls | built-in anatomy | `clearable`, clear Button, trigger Button | adopt |
| multiple, chips, hide-selected | separate family | none | defer to a tags or multi-combobox specification |
| free values and delimiters | separate product mode or family | none | omit from strict Combobox |
| grouped and rich items | later collection renderer | `description` only in v1 | support common text hierarchy; defer arbitrary structure |
| virtual scrolling | later collection engine | none | defer with a bounded v1 collection scale |
| menu positioning, attach, transitions | later overlay/motion work | inline popup | omit dedicated inputs now |
| dimensions | CSS or utility classes | variables, `style`, `class_` | support without dedicated size-per-axis inputs |
| loading and no-data slots | named slots | `loading`, `empty`, `error` | adopt and add explicit error state |
| prepend/append item, selection, chip, item slots | later browser renderer | none | defer until local and remote rendering share one safe contract |
| focus, blur, change, keydown events | native DOM | Alpine `@...` | keep native events native |

## 3. Public composition and anatomy

```citry-html
<c-CField>
  <c-fill name="label">
    Destination
  </c-fill>
  <c-fill name="default">
    <c-CCombobox
      name="planet_id"
      c-options="planets"
      placeholder="Search planets"
    />
  </c-fill>
</c-CField>
```

```python
from citry_ui import CCombobox, CComboboxOption

destination = CCombobox(
    name="planet_id",
    options=(
        CComboboxOption("europa", "Europa", "Icy moon of Jupiter"),
        CComboboxOption("titan", "Titan", "Moon with a dense atmosphere"),
    ),
)
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CCombobox` | grouping `<div>` containing an editable input and optional hidden form input | `class_`, `style`, and `attrs` target the root; `input_attrs` targets the visible input | input, popup listbox, active option, Field descriptions, and optional form value stay paired |

The public anatomy is `root`, `control`, `input`, `clear`, `trigger`, `popup`,
`listbox`, `option`, `option-label`, optional `option-description`, `loading`,
`empty`, and `error`. The hidden canonical input and private behavior markers
are implementation details, not public selectors. The visible parts remain
stable customization hooks.

`attrs` may add ordinary root, ARIA, `data-*`, and Alpine attributes. It may
contribute class and style values, which merge with direct inputs. It cannot
replace identity, reflected attributes, public part markers, or private
behavior markers. `input_attrs` may add ordinary text-input attributes but
cannot replace owned role, type, value, state, relationships, part markers,
name, or form ownership. Use `CField` for the accessible label.

The anatomy review found no administrative child component to remove.
Collection entries are data rather than declaration components. A single
component owns the relationships and state machine.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `options` | sequence of `CComboboxOption` | empty | initial collection | unique non-empty values and labels; optional non-empty descriptions |
| `name` | `str` or `None` | `None` | structural server-only | adds optional canonical native form participation |
| `id` | `str` or `None` | Field ID or generated | structural server-only | identity base for input, popup, and options |
| `value` | `str` or `None` | `None` | initial state | canonical selected identity; may temporarily lack a matching item |
| `input_value` | `str` or `None` | selected label or empty | initial state | editable query |
| `open` | `bool` | `False` | initial state | initial popup visibility, forced closed when interaction is blocked or below threshold |
| `required`, `disabled`, `readonly`, `invalid` | `bool` or `None` | inherit Field/Form | reactive fallback | form and interaction semantics |
| `loading` | `bool` | `False` | reactive fallback | external loading presentation |
| `clearable` | `bool` | `True` | reactive fallback | exposes clear when useful |
| `open_on_focus` | `bool` | `False` | reactive fallback | opens after focus when the query meets the threshold |
| `auto_highlight` | `bool` | `False` | reactive fallback | highlights the first enabled match after filtering or loading |
| `filter` | `contains`, `starts_with`, or `none` | `contains` | reactive fallback | local plain case-insensitive matching |
| `min_chars` | non-negative `int` | `0` | reactive fallback | minimum Unicode-code-point query length for popup visibility and remote loading |
| `debounce_ms` | non-negative `int` | `200` | reactive fallback | remote request delay |
| `placeholder`, `autocomplete`, `inputmode` | `str` or `None` | `None`, `off`, `None` | structural server-only | visible native-input hints |
| `required_message` | non-empty `str` | `Select an option.` | structural server-only | native custom-validity text |
| `clear_label`, `open_label`, `close_label` | non-empty `str` | `Clear selection`, `Show options`, `Hide options` | structural server-only | action Button accessible names |
| `loading_label`, `empty_label`, `error_label` | non-empty `str` | status defaults | structural server-only | status fallbacks |
| `variant` | `outline`, `filled`, or `plain` | `outline` | reactive fallback | control presentation |
| `size` | `sm`, `md`, or `lg` | `md` | reactive fallback | control geometry |
| `class_` | Citry class value or `None` | `None` | structural server-only | root classes |
| `style` | Citry style value or `None` | `None` | structural server-only | root inline styles |
| `attrs`, `input_attrs` | mapping or `None` | `None` | structural server-only | allowed root and visible-input attributes |

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `items` | `CComboboxItem[]` | keep current collection | invalid | retain prior collection and diagnose | collection, labels, filtering, popup |
| `value` | non-empty string or `null` | uncontrolled from current selection | clears selection while supplied | diagnose empty strings and other invalid values, then become uncontrolled from current selection | canonical value, hidden input, selected option, validity |
| `inputValue` | string or `null` | uncontrolled from current query | uncontrolled from current query | diagnose and become uncontrolled from current query | visible query, filtering, loading |
| `open` | Boolean or `null` | uncontrolled from current visibility | uncontrolled from current visibility | diagnose and become uncontrolled from current visibility | popup, highlight, ARIA, request lifetime |
| `required`, `disabled`, `readonly`, `invalid`, `loading`, `clearable`, `openOnFocus`, `autoHighlight` | Boolean | server/inherited fallback | invalid, server fallback | diagnose independently and use server fallback | semantics, interaction, form output, state presentation |
| `filter` | documented enum | server fallback | invalid, server fallback | same | local matching |
| `minChars`, `debounceMs` | non-negative integer | server fallback | invalid, server fallback | same | popup threshold and remote scheduling |
| `variant`, `size` | documented enum | server fallback | invalid, server fallback | same | reflected attributes and CSS |
| `loadOptions` | function | local filtering | no loader | diagnose and disable remote mode | remote collection source |
| callback inputs | function | no callback | no callback | diagnose and ignore independently | component notifications |

Valid client values win. Removing or passing `null` to `inputValue` or `open`
preserves the last committed state and releases control. `value=null` is an
intentional controlled empty selection, so removing it requires omission.
Configuration inputs return to server fallbacks when removed. `items` omission
does not restore the server array because doing so could erase accepted remote
results. Owner commits do not notify.

## 5. State model

`value`, `inputValue`, and `open` are independent public ownership axes.
Highlight, collection, loading, error, and request identity are internal axes.
Every compound interaction handles each public axis independently.

| Trigger | Value | Query | Open and highlight | Remote work | Notifications and native events |
|---|---|---|---|---|---|
| native text input | request `null` when a selection exists | request typed text | open only at threshold; highlight first only with `auto_highlight` | run once after IME composition; controlled query loads only after owner commits it | value callback before input callback; no native `change` |
| choose option | request option value | request option label | request close; clear highlight | abort; label synchronization does not load | value, query, open callbacks in that order for changed axes; native `change` only after an uncontrolled value commit |
| clear Button | request `null` | request empty text | request close; clear highlight | abort | same order; native `change` only after an uncontrolled value commit |
| Escape | unchanged | unchanged | request close; clear highlight | abort | open callback only; never selects highlight |
| Tab or outside blur | unchanged | restore known selected label when query is uncontrolled | request close; clear highlight | abort | optional query callback, then open callback; never selects highlight |
| owner value commit | commit without callback | rehydrate matching label only when query is uncontrolled and still reflects the prior selected label | keep state; incompatible highlight clears | none | no callback or native event |
| owner query commit | unchanged | commit | reconcile filter, threshold, popup, and highlight | qualifying changed query loads | no input callback; open callback only for an uncontrolled visibility change caused by threshold |
| collection replacement or remote success | preserve canonical value even when absent | fill a missing or prior selected label when a match arrives and query is uncontrolled | preserve open; keep compatible highlight, otherwise clear or auto-highlight | current request completes | no value/query callbacks |
| uncanceled Form reset | restore uncontrolled server value and query | controlled axes reassert current values | request close; clear highlight | abort | callbacks only for changed uncontrolled axes; no native `change` |
| disable or read-only becomes true | preserve value and query | preserve | force closed without ownership callback; clear highlight | abort | no component callback |
| component cleanup | no state commit | no state commit | remove transient state | abort and invalidate request ID | no callback |

An axis callback runs after its uncontrolled DOM, ARIA, form, and validity
commit, or immediately as a request when that axis is controlled. Repeated
same-value requests do not notify. Controlled owners may independently accept
or decline value, query, and open requests.

An authoritative collection cannot be distinguished from a temporary remote
page in v1. If a selected value is absent, Citry preserves the canonical value,
its last known label, and form output. It clears the option's selected marker
because no matching node exists. Required validity remains satisfied because a
canonical value exists. Server validation remains authoritative. When the item
returns, Citry rehydrates its current label without a callback.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CCombobox` | `loading` | no | one | empty `CComboboxLoadingSlotData` | `loading_label` |
| `CCombobox` | `empty` | no | one | empty `CComboboxEmptySlotData` | `empty_label` |
| `CCombobox` | `error` | no | one | empty `CComboboxErrorSlotData` | `error_label`, never exception text |

Slot data is a server snapshot. Browser state only changes visibility. Rich
option, group, and selected-value slots remain deferred because browser-only
remote entries cannot instantiate Python slots and arbitrary option content
requires stable accessible text plus a rule against interactive descendants.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onValueChange` | `value`, `{reason, option, query, controlled, source}` | option, clear, text invalidation, reset | after uncontrolled value/form/validity commit; before dependent query and open requests | request only when controlled | ignored |
| `onInputValueChange` | `query`, `{reason, controlled, source}` | input, option, clear, blur, reset | after uncontrolled visible-query commit | request only when controlled | ignored |
| `onOpenChange` | `open`, `{reason, controlled, source}` | input, focus, trigger, keyboard, selection, Escape, outside, blur, threshold | after uncontrolled visibility/ARIA commit | request only when controlled | ignored |
| `onLoadError` | `error`, `{query, requestId}` | current non-abort remote failure | after error state is visible | not an ownership callback | ignored |

Native `input`, `change`, `focus`, `blur`, `invalid`, and Form events remain
available through Alpine `@...`. Only a successful uncontrolled canonical
selection change dispatches bubbling native `change` from the visible input.
Owner commits and display-only query updates do not synthesize native events.

No public imperative methods are added. Browser state and an input ref cover
the current jobs without a second control surface.

## 8. Semantics, keyboard, focus, and assistive technology

The visible native text input has `role=combobox`, `aria-autocomplete=list`,
`aria-expanded`, and `aria-controls`. DOM focus stays on it. When open, a valid
highlight is exposed through `aria-activedescendant`. The popup is a listbox;
options have stable IDs, `role=option`, `aria-selected`, and optional
`aria-disabled`. Label and description are non-interactive text.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| closed, enabled | ArrowDown | request open at threshold and highlight first enabled item | input stays focused | yes |
| closed, enabled | ArrowUp | request open at threshold and highlight last enabled item | input stays focused | yes |
| open | ArrowDown or ArrowUp | move with wrap across enabled visible items | input stays focused | yes |
| open | Home or End without modifiers | move to first or last enabled visible item | input stays focused | yes |
| open with selectable highlight | Enter | request selection and close | input stays focused | yes |
| any popup state | Escape | request close without selection | input stays focused | only while open |
| open | Tab or Shift+Tab | request close without selection | native next or prior focus | no |
| input | printable key, editing shortcut, horizontal arrow, IME | native editing | input stays focused | no |
| option | pointer down and click | keep input focus through selection | input stays focused | pointer down only |
| trigger | click | toggle at threshold | input receives focus | no |
| clear | click | clear and close | input receives focus | no |

The popup indicator is removed from sequential Tab order per APG. The clear
Button remains reachable only through pointer or direct focus APIs because the
editable input and popup are one composite Tab stop. Disabled options never
highlight or select. Blur, outside press, Escape, and Tab never commit a
highlight. Empty, loading, and error changes use polite status announcements
without moving focus.

## 9. Native forms and validation

When `name` is supplied, a visually hidden native input submits the canonical
value. When omitted, no named form value is produced. The visible input owns
constraint validation and never submits the display label. Disabled state
disables both inputs. Read-only remains submittable but blocks editing and
selection. Required fails only when no canonical value exists.

Before browser activation, the visible input is read-only. This preserves a
useful selected label without letting edited text submit a stale hidden value
when JavaScript is unavailable. Activation applies the effective read-only
state.

| Browser or Form action | Reconciliation | Hidden value | Validity and events |
|---|---|---|---|
| user or autofill enters an exact unique label | normal input path clears old selection; no implicit selection | empty until the user selects | required remains missing; native input is preserved |
| user or autofill enters unmatched text | clear old selection | empty | required remains missing |
| duplicate labels | never infer identity from label | empty until explicit option selection | no ambiguous auto-selection |
| option selection | set canonical value | selected value | valid when otherwise allowed; bubbling native change for uncontrolled commit |
| clear | remove canonical value | empty | required becomes missing; bubbling native change for uncontrolled commit |
| uncanceled reset | restore uncontrolled server state; reassert controlled state after the reset turn | corresponding canonical value | callbacks for changed uncontrolled axes only |
| canceled reset | no component-owned change | unchanged | no callback |
| disabled | preserve internal state, omit from FormData | disabled hidden input | excluded from validation |
| read-only | preserve and submit canonical value | current value | no user edits or selection |

`input_attrs` rejects `form` because visible validation and hidden submitted
value cannot safely belong to different Forms. Server validation must verify
that the submitted key is allowed. Citry Events success, error replacement,
and transport retry use ordinary native Form behavior and Citry instance
lifecycle.

## 10. Styling and theme contract

`CCombobox` follows [`../ui_theme.md`](../ui_theme.md). Variants are `outline`,
`filled`, and `plain`; sizes are `sm`, `md`, and `lg`.

Public variables are `--cui-combobox-background`,
`--cui-combobox-foreground`, `--cui-combobox-border-color`,
`--cui-combobox-focus-color`, `--cui-combobox-invalid-color`,
`--cui-combobox-radius`, `--cui-combobox-height`,
`--cui-combobox-inline-padding`, `--cui-combobox-icon-size`,
`--cui-combobox-popup-background`, `--cui-combobox-popup-border-color`,
`--cui-combobox-popup-shadow`, `--cui-combobox-popup-max-height`,
`--cui-combobox-option-padding`, `--cui-combobox-option-gap`,
`--cui-combobox-option-description-color`,
`--cui-combobox-highlighted-background`,
`--cui-combobox-selected-background`, `--cui-combobox-disabled-opacity`, and
`--cui-combobox-error-color`.

Public selector values are `root`, `control`, `input`, `clear`, `trigger`,
`popup`, `listbox`, `option`, `option-label`, `option-description`, `loading`,
`empty`, and `error`. Public root reflected
attributes are `data-open`, `data-loading`, `data-empty`, `data-error`,
`data-required`, `data-disabled`, `data-readonly`, `data-invalid`,
`data-variant`, and `data-size`. Options expose `data-value`, `data-selected`,
`data-highlighted`, and `data-disabled`.

Public variables inherit through private effective variables. Default rules
live in `citry-ui.theme` with low specificity. Private classes, effective
variables, behavior markers, and the hidden form input are not supported hooks.

## 11. Environmental behavior

Defaults support light and dark schemes, including nested opposite schemes.
Logical properties support RTL. Forced colors keeps control and popup
boundaries, focus, highlight, selection, and disabled state distinguishable.
Long labels and descriptions wrap without covering controls. A narrow or
zoomed container retains a usable input and scrollable popup. Touch relies on
pointer ordering, not hover. No essential animation is present.

Visible library strings are required, clear, open, close, loading, empty, and
error labels. Locale selection and translation remain follow-up work.

## 12. Overlay and layering behavior

The popup remains a DOM child of the root, inherits theme and provided browser
context, and is absolutely positioned. It does not enter the top layer, lock
scroll, trap focus, or make background content inert. Ancestor clipping and
collision avoidance are current limitations, not accessibility claims.

A follow-up should evaluate the native Popover API before building a portal.
Any later overlay service must prove mobile keyboard, zoom, touch scrolling,
outside interaction, theme, context, Citry ownership, cleanup, and assistive
technology behavior.

## 13. Collections, async data, and identity

Python options are `CComboboxOption(value, label, description=None,
disabled=False)`. Client items and loader results use `{value, label,
description?, disabled?}`. Values and labels are non-empty strings, optional
descriptions are non-empty when present, and values are unique. Duplicate
labels are allowed but never used to infer identity. Invalid or duplicate
collections are rejected as a whole, reported once per invalid episode, and do
not replace the prior valid collection.

Local filtering performs plain case-insensitive `contains` or `starts_with`
matching on labels. `none` preserves collection order. It does not promise
accent folding, word segmentation, locale collation, or fuzzy matching.
When the uncontrolled query still mirrors the selected label, local filtering
treats it as pristine and an opened popup shows the full collection. Editing
the text turns it back into a search query. An explicitly controlled query is
always filter input.

When `loadOptions` is valid, it replaces local filtering. Each qualifying
committed query aborts and invalidates the previous request, then calls
`loadOptions({query, signal, requestId})` after `debounceMs`. Results apply only
when the request ID is current and its signal is not aborted. A synchronous
throw, rejection, malformed result, or duplicate result enters the same safe
error path. Closing, falling below the threshold, disabling, read-only, reset,
replacement, and cleanup abort current work. A later qualifying query clears
the error and may recover. Replacing or removing `loadOptions` aborts the
current request. A valid replacement immediately loads a qualifying query when
the popup is open; `null` returns to local filtering.

Remote failure preserves the last valid collection internally but hides it
while error is visible. A successful later result replaces it. Empty and error
states never render exception text. Version 1 targets ordinary collections up
to 1,000 items. Historical label memory is capped at 1,000 identities while
preserving the current orphan selection. Larger collections require measured
application evidence or future virtualization.

## 14. Server render, morph, and cleanup

Server output contains safe selected text, option content, all required ARIA
relationships, and optional canonical form output. The input remains read-only
until client activation. Effective disabled, read-only, threshold, loading,
and open state are truthful before activation.

Each activation is scoped to the nearest root. Same-identity morphing preserves
uncontrolled value, query, compatible highlight, focus and selection range,
accepted remote collection, and request supersession. A replacement with new
identity gets server defaults. Cleanup aborts and invalidates requests, clears
timers, removes document and Form listeners, releases Field native-invalid
state, drops option nodes and callbacks, and cannot reopen or notify late.

## 15. Security and content trust

Labels and descriptions render as text, never HTML. Values are assigned to
properties and attributes without selector interpolation. Loader errors are
never rendered. No query or option causes an implicit request unless the
consumer supplies `loadOptions`. Attribute mappings cannot replace owned
identity, semantics, relationships, reflected attributes, public parts, or
private behavior markers.

## 16. Assets and performance

The family adds shared CSS and one JavaScript initializer, with no font, icon
pack, CDN, or implicit network request. It uses one document outside-pointer
listener per active instance and at most one debounce timer and
`AbortController` per query.

Automated measurements record compressed assets and representative local and
remote interactions without turning microbenchmarks into the product bar.
Release qualification must cover 100 and 1,000 local items, repeated queries,
stale requests, and retained listeners/resources. Focused tests already cover
request supersession and cleanup; the scaling profile remains outstanding.
Virtualization remains out of scope.

## 17. Acceptance matrix

Repository-automated evidence must cover:

- Python schema validation, optional form name, owned attributes, option
  identity and descriptions, slots, exports, and packaging;
- independent controlled/uncontrolled value, query, and open combinations,
  removal, invalid values, same-value requests, and selected-label rehydration;
- every keyboard row, pointer ordering, nested-root ownership, disabled options,
  IME, focus opening, auto-highlight, threshold, and no implicit blur/Tab
  selection;
- native input/change/invalid/reset/FormData behavior, canceled and controlled
  reset, disabled/read-only/required, and safe pre-activation output;
- debounce, synchronous throw, rejection, malformed and duplicate results,
  abort, ignored abort, stale IDs, threshold, close, reset, disable, read-only,
  cleanup, and recovery;
- Field/Form inheritance, server replacement, public variables, selectors and
  reflected attributes, computed override behavior, light/dark, RTL, forced
  colors, narrow layout, quality catalog, axe, browser floor, and asset budget;
  and
- structured API schema, API/runtime inventory parity, live snippets, and docs
  projection.

Human review remains required for visual hierarchy, screen-reader result and
state announcements, keyboard-only use, touch and mobile keyboards, browser
autofill, 200 and 400 percent zoom, long translated text, RTL, forced colors,
and real app integration.

## 18. Compatibility classification

Stable API includes component and interface names, option shape, server and
client inputs, ownership and callback ordering, slots, callback detail, native
event and Form behavior, public variables, selectors, reflected attributes,
async ordering, errors, and cleanup outcomes. ARIA, focus, canonical form
output, pre-activation safety, and collection identity are behavioral
contracts. Exact design values and popup geometry may evolve. Private classes,
effective variables, behavior markers, hidden form structure, option node
implementation, request storage, and JavaScript layout remain private.

## 19. Public documentation contract

[`ccombobox/api.md`](../../../packages/py/citry_ui/citry_ui/components/ccombobox/api.md)
is the component-owned public guide. Structured `api.yml` is the exhaustive API
reference source. The page leads with the strict searchable-single-select job
and shows the rendered result before details.

The coherent page theme is astronomy. Planned live examples are:

| Section | Example | Contract exercised |
|---|---|---|
| At a glance | planet destination sampler | local options, descriptions, variants, and states |
| Build | choose a moon | minimal template and Python composition |
| Configure | observatory control panel | variants, sizes, clearable, focus opening, and auto-highlight controls |
| Search remotely | star catalog | debounce, threshold, loading, empty, failure, recovery, and abort |
| Control state | mission target | independent value, query, and open ownership plus callback trace |
| Forms | launch destination | Field/Form, required, reset, and FormData |
| Keyboard | constellation picker | highlight, selection, Escape, Tab, and disabled options |
| Customize | deep-sky theme | root and ancestor variables plus public selectors |
| Environment | celestial names | narrow layout, long text, RTL, nested dark/light, and forced-colors guidance |

Each public API entry has a stable anchor. The guide states whether every input
is server or client, keeps long behavior in conceptual sections, and keeps API
table rows concise.

## 20. Open decisions and deferred work

- Rich option and selection rendering needs a browser collection-renderer
  contract, required attribute forwarding, trusted accessible text, nested
  lifecycle, and a ban on interactive option descendants.
- Grouping, multiple selection and tags, custom values, create-new, pagination,
  infinite loading, and virtualization require separate specifications.
- A native-popover or positioned-overlay spike must prove clipping, collision,
  context, mobile, focus, outside interaction, assistive technology, and cleanup.
- Browser autofill requires continuing real-device observation even with the
  stale-canonical safety rule.
- Locale-aware matching and every library-authored label belong to later
  localization work.
