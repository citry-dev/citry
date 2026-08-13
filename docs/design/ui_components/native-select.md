# Citry UI Native Select specification

**Status (2026-08-08): production pass complete; independent implementation
review found no remaining high- or medium-severity issue.**
This specification advances one styled `CNativeSelect` with a native `<select>`
root. A custom popup Select, multiple selection, search, async options, and
virtualization remain separate work.

## 1. Purpose and product bar

`CNativeSelect` chooses one value from a finite server-owned option list. It
works inside or outside `CField`, preserves native keyboard, touch, mobile
picker, form, validation, autofill, reset, and assistive-technology behavior,
and adds Citry UI presentation plus optional browser-side value control.

Common jobs and shortest support paths:

| Job | Shortest template or Python call | Support path |
|---|---|---|
| Choose one option | `<c-CNativeSelect options="options" name="habitat" />` | direct API |
| Label and describe the control | place it in `CField` | composition |
| Prompt before a choice | `placeholder="Choose a habitat"` | direct API; creates the empty option |
| Require a nonempty choice | `required` | direct native validation |
| Group related choices | `CNativeSelectGroup(...)` inside `options` | structured collection API |
| Disable one choice | `CNativeSelectOption(..., disabled=True)` | structured collection API |
| Set the initial choice | `value="wetland"` | direct API |
| Control selection in the browser | `$c-props="{ value: habitat }"` | client input |
| Listen for user selection | `@input` or `@change` | native events |
| Submit to another native Form | `attrs={"form": "survey"}` | native attribute through trusted attrs |
| Change presentation | `variant="filled" size="lg"` | direct API |
| Style one option where supported | option `attrs` | native option attributes and browser limits |

Production completeness means a polished closed control, honest native
picker behavior, exact option/value validation, safe text rendering, native
forms and reset, Field relationships, controlled and uncontrolled ownership,
light/dark and forced-color behavior, no custom overlay, public styling
contracts, examples, structured reference, and packaged-artifact evidence.

Non-goals:

- custom popup positioning, scroll lock, focus containment, or portal work;
- search, creatable values, remote options, virtualization, or rich option
  content;
- multiple selection or listbox presentation;
- a simulated read-only state;
- component-authored value callbacks or custom DOM events; and
- a headless variant.

## 2. Prior art and complaints

The shared taxonomy gives Select/Listbox 12/12 ecosystem coverage. The
component inventory deliberately names this family Native Select so a later
custom `CSelect` can own an ARIA collection and overlay without changing this
contract.

Current-source record:

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| HTML Standard | Living Standard updated 2026-07-20, reviewed 2026-08-08 | [Select](https://html.spec.whatwg.org/multipage/form-elements.html#the-select-element), Option, Optgroup, form reset, value, `selectedIndex`, and `showPicker()` | Keep a native single-select root, native options/groups, native form/validation/reset, and browser-owned picker. |
| MDN | updated 2026-07-14, reviewed 2026-08-08 | [`select`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/select) | Record cross-platform popup styling limits and native mobile/keyboard benefits. |
| Vuetify | 4.1.8 source reviewed 2026-08-08 | [VSelect docs](https://vuetifyjs.com/en/components/selects/) and [`VSelect.tsx`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VSelect/VSelect.tsx) | Use as the primary styled-suite capability check. Defer its custom menu, filtering, chips, multiple selection, rich item slots, and virtual scroll to custom Select. |
| Material UI | 7.3.4 source and current docs reviewed 2026-08-08 | [Select and Native Select](https://mui.com/material-ui/react-select/#native-select), [`NativeSelect.js`](https://github.com/mui/material-ui/blob/v7.3.4/packages/mui-material/src/NativeSelect/NativeSelect.js) | Validate the explicit native/custom split and native mobile job. Avoid a detached indicator hit target. |
| Mantine | current docs reviewed 2026-08-08 | [NativeSelect](https://mantine.dev/core/native-select/) | Confirm native options/groups, variants, sizes, wrapper composition, and platform popup limits. |
| Chakra UI | current docs reviewed 2026-08-08 | [Native Select](https://chakra-ui.com/docs/components/native-select) | Confirm native root, Field composition, size/variant/state styling, and compound indicator tradeoff. |
| Bootstrap | 5.3 docs reviewed 2026-08-08 | [Select](https://getbootstrap.com/docs/5.3/forms/select/) | Confirm concise native styling, disabled and size jobs, and inability to style the open options consistently. |
| Shoelace | current docs reviewed 2026-08-08 | [Select](https://shoelace.style/components/select) | Boundary evidence for custom popup, slots, clear action, multiple values, methods, and placement. |
| Material UI issue 17353 | open, originally MUI 3.1.1 | [non-modal Select request](https://github.com/mui/material-ui/issues/17353) | A custom menu imports scroll-lock and page-layout policy that Native Select must avoid. |
| Material UI issue 42982 | closed, waiting for author | [custom icon is not clickable](https://github.com/mui/material-ui/issues/42982) | Keep the whole native root as the hit target; do not add a sibling indicator element. |
| Material UI issue 18494 | closed | [out-of-range value](https://github.com/mui/material-ui/issues/18494) | Validate server options and value together; client unknown values retain the last valid controlled or server selection and report once. |
| Material UI issue 11069 | closed historical | [placeholder request](https://github.com/mui/material-ui/issues/11069) | Make the common empty prompt concise and define it as a real empty native option. |
| React issue 30580 | closed/fixed historical | [controlled Select reset](https://github.com/react/react/issues/30580) | Specify native reset and controlled restoration explicitly. |
| Material UI issue 35586 | closed by implementation change | [ARIA alignment](https://github.com/mui/material-ui/issues/35586) | Prefer native Select semantics instead of reconstructing combobox/listbox ARIA. |

Patterns adopted:

- explicit native/custom family boundary;
- a native root and native option descendants;
- server-owned typed option records, groups, placeholder, value, states,
  variants, sizes, root class/style/attrs, and optional client value control;
- native `input` and `change` events; and
- browser-owned popup behavior.

Patterns rejected for this family:

- custom popup, menu props, item slots, chips, filtering, multiple selection,
  clear buttons, loading UI, and rich items;
- raw default-slot options mixed with structured value ownership;
- a decorative sibling icon; and
- broad option inference from arbitrary objects.

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `items`, `item-title`, `item-value`, `item-disabled`, `item-children` | direct API | typed option/group records | adopt a smaller explicit schema |
| `model-value`, `default-value` | direct/client API | `value` and client `value` | adopt native single value |
| `multiple`, `chips`, `closable-chips` | separate component | `CMultiSelect`, `CTagsInput`, or `CListbox` | omit from native family |
| `menu`, `menu-props`, `open-on-clear` | separate component | `CSelect` or `CMultiSelect` | omit from native family |
| `clearable`, clear icon and clear event | native empty option or separate action | `placeholder`; consumer native events | no internal clear button |
| `loading` and progress | composition | Field description or separate progress | omit |
| `disabled`, `readonly` | direct/native or unsupported | `disabled`; no `readonly` | adopt native disabled, reject simulated read-only |
| `error`, `error-messages`, rules | Field/native forms | `invalid`, `CField`, native constraints | adopt existing ownership |
| `label`, hint, messages, prefix/suffix | composition | `CField` and ordinary layout | no wrapper anatomy |
| density, variant, theme, class, style | direct/CSS | `variant`, `size`, `class_`, `style`, variables | adopt suite vocabulary |
| item, selection, prepend/append slots | separate custom Select | none | rich popup content conflicts with native popup |
| update/open/highlight callbacks | native events or separate custom Select | `input`, `change`; no popup callbacks | keep browser event contract |
| focus and menu methods | native ref | `focus()`, `showPicker()` when supported | no wrapper method API |
| autocomplete/filter/custom value comparator | separate custom Select | native autofill only | omit |

## 3. Public composition and anatomy

Template composition:

```html
<c-CField control_id="habitat">
  <c-fill name="label">Habitat</c-fill>
  <c-CNativeSelect
    name="habitat"
    options="options"
    placeholder="Choose a habitat"
  />
  <c-fill name="description">Choose the closest match.</c-fill>
</c-CField>
```

Python composition:

```python
CField(
    control_id="habitat",
    slots={
        "label": "Habitat",
        "default": CNativeSelect(
            name="habitat",
            options=[
                CNativeSelectOption("forest", "Forest"),
                CNativeSelectOption("wetland", "Wetland"),
            ],
            placeholder="Choose a habitat",
        ),
    },
)
```

Anatomy:

```text
CField, optional
└── select.cui-native-select
    ├── option[value=""], only when placeholder is supplied
    ├── option
    └── optgroup
        └── option
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CNativeSelect` | one native `<select>` | `attrs`, `class_`, and `style` merge on the Select | exactly one option collection; at most one surrounding Field |

There is no component wrapper, indicator element, popup element, or public
option component. The browser owns the open picker. The public root selector
is stable; the open popup DOM and rendering are not Citry UI API.

`CNativeSelectOption` and `CNativeSelectGroup` are frozen public data-record
shells. A group contains only options, not nested groups. Options preserve
input order. Option values must be unique across the full flattened list.
Nested caller-owned sequences and mappings are snapshotted per render as
specified below; the frozen shell alone is not treated as deep immutability.

## 4. Server inputs and client inputs

Public supporting records:

```python
@dataclass(frozen=True, slots=True)
class CNativeSelectOption:
    value: str
    label: str
    disabled: bool = False
    attrs: Mapping[str, object] | None = None

@dataclass(frozen=True, slots=True)
class CNativeSelectGroup:
    label: str
    options: Sequence[CNativeSelectOption]
    disabled: bool = False
    attrs: Mapping[str, object] | None = None
```

`CNativeSelectItem = CNativeSelectOption | CNativeSelectGroup`.

At the start of each server render, Native Select creates one private
normalized snapshot: the outer options sequence and each group options
sequence become tuples, and root, option, and group attrs become ordinary
dict copies. Validation, template data, JS data, and rendering use only that
snapshot. No later read reaches a caller-owned sequence or mapping during the
same render.

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `options` | `Sequence[CNativeSelectItem]` | required | structural server data | finite ordered collection; unique values; one group level |
| `name` | `str | None` | `None` | native form configuration | nonempty when supplied |
| `id` | `str | None` | generated | identity | nonempty and no ASCII whitespace |
| `value` | `str | None` | `None` | initial/reset value | canonical nonempty string identifies one enabled option; `None`, or `""` when a placeholder exists, selects the placeholder; `None` without one uses native first-option selection |
| `placeholder` | `str | None` | `None` | structural server data | inserts an enabled first option with empty value; conflicts with an explicit empty-value option |
| `required` | `bool | None` | Field value or `False` | reactive configuration fallback | requires `placeholder`; Field-owned when composed |
| `disabled` | `bool | None` | Field/Form value or `False` | reactive configuration fallback | Field-owned when composed; native disabled state |
| `invalid` | `bool | None` | Field value or `False` | reactive configuration fallback | Field-owned when composed; merges with native invalid state |
| `autocomplete` | `str | None` | `None` | native configuration | forwarded as plain text |
| `variant` | `Literal["outline", "filled", "plain"]` | `"outline"` | reactive presentation | public reflected attribute |
| `size` | `Literal["sm", "md", "lg"]` | `"md"` | reactive presentation | visual size, not native Select `size` |
| `class_` | `CClassValue | None` | `None` | server styling | merges on root |
| `style` | `CStyleValue | None` | `None` | server styling | merges on root |
| `attrs` | `Mapping[str, object] | None` | `None` | trusted native escape path | native `form`, `autofocus`, data, Alpine, and other unowned attrs |

Native `multiple`, native `size`, and the unsupported no-op `readonly`
attribute are reserved and rejected in `attrs`, including their dynamic and
property-binding aliases. This family always renders a drop-down single
Select. `size` is visual, as it is for `CInput`; `CListbox` has a separate
contract.

Option and group `label` values and option `value` values must be nonempty
strings. The synthesized placeholder exclusively owns the empty option value.
Option values, the Python `value` input, and client `value` strings share one
canonicalizer: normalize CRLF and CR to LF and reject U+0000 before duplicate
checking, enabled-option lookup, HTML rendering, JS serialization, and client
lookup. Option/group `disabled` must be Boolean. Option attrs cannot
replace `value`, `label`, `disabled`, or `selected`. Group attrs cannot replace
`label` or `disabled`.

Root/option/group attrs reject case-insensitive Alpine shorthand, longhand,
property bindings, and object spreads that can write an owned attribute.
`x-model`, `x-modelable`, `x-text`, and `x-html` are rejected wherever they
could create a second value or option-content owner. Native event listeners
and unrelated Alpine bindings remain allowed.

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `value` | string or null | release client ownership immediately | select the placeholder when present, otherwise clear to `selectedIndex = -1` | empty string selects an existing placeholder; without one it is unknown; other invalid values follow section 5 recovery | native value and selected option |
| `required` | Boolean | server/Field fallback | invalid, fallback | true without placeholder is unsupported and resolves false with one diagnostic | native property, validity, mirror |
| `disabled` | Boolean | server/Field/Form fallback | invalid, fallback | report once, fallback | native property and mirror |
| `invalid` | Boolean | server/Field fallback | invalid, fallback | report once, fallback | ARIA, Field message, mirror |
| `variant` | allowed string | server fallback | invalid, fallback | report once, fallback | reflected attribute and CSS |
| `size` | allowed string | server fallback | invalid, fallback | report once, fallback | reflected attribute and CSS |

Inside `CField`, server and client `required`, `disabled`, and `invalid` on the
Select are rejected or ignored with a diagnostic because Field is the owner.
`CNativeSelect` registers two private Field capabilities: required is
supported only when `placeholder` exists, and read-only is unsupported. A
server-rendered Field whose effective required/read-only value exceeds those
capabilities raises after control registration settles. In the browser, Field
resolves an unsupported request to false, keeps context, label indicator, and
reflected attributes coherent with the Select, and reports the rejected
request once. Native Select registers its current capabilities through a
private reactive Field-context method on every initialization and unregisters
the returned generation token on cleanup. A child-only rerender that adds or
removes `placeholder` therefore updates required support even when Field is
retained. Replacement cleanup and registration settle in one lifecycle turn;
an older token cannot unregister a newer registration. This capability record
is private control plumbing, not public Native Select state.

`CForm.readonly` has no effect on a standalone Native Select. A Native Select
inside a read-only Form uses `CField(readonly=False)` to opt its Field out of
that unsupported default. A later Form read-only request cannot override that
explicit false.

## 5. State model

States:

- uncontrolled: browser selection is authoritative;
- controlled: a supplied client `value` is authoritative;
- empty: placeholder selected or `selectedIndex == -1`;
- disabled: native disabled property is true;
- externally invalid: Field or standalone `invalid` is true;
- natively invalid: native `invalid` event has fired and validity has not
  recovered; and
- effective invalid: external or native invalid.

| Transition | Trigger | Result |
|---|---|---|
| initialize without client value | activation | preserve server/native selected option; browser owns later changes |
| initialize with valid client string | prop effect | select matching enabled option and enter controlled state |
| initialize with client null | prop effect | select placeholder or clear and enter controlled state |
| user changes while uncontrolled | native interaction | native value changes; native events run; no restoration |
| user changes while controlled | native interaction | consumer native handlers run, then deferred reconciliation reads latest prop; mirrored updates incur no second assignment; unchanged props restore the controlled selection |
| client value omitted | prop effect | release immediately without changing current selection |
| client value invalid or unknown | prop effect | report once; before any valid controlled value, preserve the current uncontrolled DOM selection; after valid control, retain its value while it remains enabled, otherwise use the structural fallback from section 13 |
| native invalid fires | browser validation | set native invalid, notify Field, synchronize ARIA and mirrors |
| uncontrolled input/change becomes valid | native event | clear native invalid and Field native-invalid state immediately |
| controlled input/change after a native-invalid episode | native event | defer the clear decision until latest-prop reconciliation; clear only if the settled controlled selection is valid, otherwise retain the episode |
| reset while uncontrolled | native Form reset | browser restores server-selectedness |
| reset while controlled | reset followed by bounded task | latest controlled value is restored after native reset |

Python and client empty string identify the synthesized placeholder when it
exists. Client empty string without a placeholder is unknown; client null
without a placeholder explicitly controls no selection.

Repeated semantic same-value control performs no assignment. Null or empty
string with a placeholder is equal only when that exact placeholder option is
selected. Null without a placeholder is equal only when
`selectedIndex == -1`. A nonempty value is equal when the uniquely matching
enabled option is selected. This distinguishes a selected empty placeholder
from no selection even though native `.value` is empty in both cases.

Client value strings use the same CRLF/CR to LF canonicalization as server
option values and reject U+0000. Every value or configuration effect,
controlled reconciliation, client initialization after a server replacement,
and uncanceled reset rechecks native validity. If a prior native-invalid
episode has become valid, Native Select clears it and notifies Field even
though those programmatic operations do not dispatch native `input` or
`change` events. Programmatic invalidity does not create a new native-invalid
episode. In controlled mode, a native input handler does not clear an existing
episode before deferred reconciliation settles the latest prop.

## 6. Slots and slot data

`CNativeSelect` has no slots. Options are structured server data because the
component must validate unique values, placeholder collisions, selectedness,
disabled groups, and safe text consistently in template and Python
composition.

Raw `<option>` children would create a second ownership path that cannot be
validated against `value`, so they are deliberately unsupported. Rich labels,
icons, descriptions, arbitrary content, and dynamic item slots belong to
`CSelect`, `CMultiSelect`, or `CListbox`.

## 7. Callbacks, native events, and methods

There are no component-authored callbacks or custom DOM events. Consumers use
native `@input`, `@change`, `@invalid`, `@focus`, and `@blur`. The current value
is `event.currentTarget.value`.

No wrapper methods are added. A consumer ref may use native `focus()`,
`checkValidity()`, `reportValidity()`, and `showPicker()` where the browser
supports and permits it. `showPicker()` may require transient user activation
and may throw native exceptions; Citry UI does not hide those conditions.

## 8. Semantics, keyboard, focus, and assistive technology

The root is the native single-select control with its browser-computed role.
`CField` provides native label association and description/error IDREFs.
Standalone usage requires an accessible name through a native `<label>`,
`aria-label`, or `aria-labelledby`.

`aria-invalid` is owned and cannot be supplied through `attrs`. Consumer
`aria-describedby` tokens merge with Field description and the effective
invalid Field error without duplicates. Consumer `aria-errormessage` tokens
merge with the Field error only while effective invalid is true and are absent
otherwise. Standalone consumer IDREFs remain. Client state changes recompute
the same merge instead of overwriting consumer tokens.

Citry UI does not override keyboard interaction. Browser and platform behavior
owns Tab entry, arrow and character navigation, picker opening, confirmation,
Escape, touch, and mobile wheel/picker interaction. Disabled options remain
unavailable through native interaction. The placeholder is an ordinary empty
option and is announced according to the platform.

There is exactly one focus stop and no indicator focus target. Focus-visible
styling applies to the Select root. Programmatic client value changes do not
move focus.

## 9. Native forms and validation

With a nonempty `name`, the enabled Select is a native successful control and
submits its selected option value. An empty or absent name does not submit;
empty name is rejected so omission is explicit. Disabled Select and options
follow native successful-control rules.

`required` uses native Select value-missing validation and therefore requires
the synthesized first direct empty placeholder option. A direct or
Field-owned server `required=True` without `placeholder` raises. A standalone
or Field-owned client true request without it resolves to false with one
diagnostic. With a placeholder, its empty value is invalid when required and
remains a clearable empty choice when optional. Without placeholder,
`value=None` leaves browser initial selection to native selectedness, normally
the first enabled option.

`CField` owns required, disabled, and invalid state when composed. `CForm`'s
disabled fieldset dominates. Native Select has no read-only state, so this
component neither simulates one nor inserts hidden submission controls.

Native Form reset restores server-selectedness when uncontrolled and the
latest valid client value when controlled. Every reset event owns its own
deferred task. A later reset never cancels an earlier task because either
event may be canceled independently. Each task checks its event's final
`defaultPrevented` state, reads the latest controlled prop, and restores only
for its uncanceled reset. Cleanup cancels all outstanding reset tasks.

External form ownership through
trusted `attrs.form` is supported outside `CForm`; a Select inside `CForm`
cannot target a different form owner. Citry Events observes ordinary native
form data and validation behavior. HTML attribute lookup is case-insensitive,
duplicate case spellings are invalid, and dynamic `form` bindings are rejected.

The native Form owner element and association are static for one Select
initializer lifetime. If an external owner node is replaced or its ID/`form`
association changes, the same update must rerender/reinitialize Native Select.
That paired lifecycle removes the old reset listener and binds the new owner.
Independently replacing only the externally referenced Form is outside the
component contract.

## 10. Styling and theme contract

Variants are `outline`, `filled`, and `plain`. Sizes are `sm`, `md`, and `lg`.
The root uses `appearance: none` plus a static CSS background indicator so the
whole native element remains the hit target. Forced-colors restores native
appearance and removes the image. The open option picker remains platform
styled.

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-native-select-background` | color | closed-control background | `Canvas` |
| `--cui-native-select-foreground` | color | selected text | `CanvasText` |
| `--cui-native-select-border-color` | color | border | mixed `CanvasText` |
| `--cui-native-select-hover-border-color` | color | hover border | stronger mixed `CanvasText` |
| `--cui-native-select-focus-color` | color | focus border and ring | `Highlight` |
| `--cui-native-select-invalid-border-color` | color | invalid border | scheme-aware red |
| `--cui-native-select-disabled-background` | color | disabled background | mixed Canvas |
| `--cui-native-select-placeholder-color` | color | empty selection foreground | muted CanvasText |
| `--cui-native-select-radius` | length | root radius | `0.5rem` |
| `--cui-native-select-inline-padding` | length | text-side padding | `0.75rem` |
| `--cui-native-select-block-padding` | length | block padding | `0.625rem` |
| `--cui-native-select-font-size` | font size | visual size | `1rem` |
| `--cui-native-select-indicator-size` | length | each background-indicator triangle and its reserved space | `0.4rem` |
| `--cui-native-select-indicator-gap` | length | reserved indicator space | `0.75rem` |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="native-select"]` | native Select root | all states and variants | component root |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| `data-variant` | `outline`, `filled`, `plain` | effective presentation |
| `data-size` | `sm`, `md`, `lg` | effective visual size |
| `data-empty` | present or absent | placeholder or no option selected |
| `data-required` | present or absent | effective native required state |
| `data-disabled` | present or absent | effective native disabled state |
| `data-invalid` | present or absent | external or observed native invalid state |

Defaults live in `citry-ui.theme` at low specificity. Public variables are
inherited inputs resolved through private effective variables. Unlayered
consumer classes work before or after the component sheet; named layers obey
the documented global layer order.

## 11. Environmental behavior

- Light and dark scopes use Canvas system colors and `light-dark()` fallbacks.
- Logical padding and mirrored background positioning support RTL.
- Forced colors restores the native indicator and uses system colors.
- Reduced motion needs no special branch because the component animates
  nothing.
- Narrow layouts keep `inline-size: 100%` and `min-inline-size: 0`; long labels
  are browser-ellipsized or clipped according to the native closed control.
- 200% and 400% zoom retain native popup and one focus target.
- Touch and coarse pointers keep the platform picker because the native root
  remains interactive.
- Print shows the selected closed-control value; open popup content is not
  printable output.

Library-authored visible strings: none. `placeholder`, option labels, and
group labels are caller content. The Citry UI i18n migration therefore needs
no NativeSelect catalog keys, while locale-sensitive option content remains
application-owned.

## 12. Overlay and layering behavior

Citry UI creates and controls no overlay. The browser or operating system owns
the native picker, its stacking, placement, dismissal, scrolling, focus, and
screen-reader presentation. Citry UI cannot theme or inspect that picker
reliably and does not promise its DOM.

A need for portal ownership, rich rows, custom placement, persistent open
state, or popup callbacks selects `CSelect` or `CMultiSelect` instead.

## 13. Collections, async data, and identity

`options` is a finite server-owned ordered collection. The canonical option
`value` is its stable identity and must be unique across groups after newline
normalization. U+0000 is invalid. Groups preserve order and cannot nest.
Disabled groups disable their options through native semantics.
The per-render normalized tuple/dict snapshot is the collection observed by
all render phases; caller mutation can affect only a later render.

Server rerenders may add, remove, reorder, relabel, regroup, or disable
options. The same render validates its server `value` against the resulting
enabled set. A client-controlled value missing after replacement is invalid
and falls back as defined in section 5.

For a retained uncontrolled Select, the incoming server `value` updates reset
selectedness, not an existing valid user selection. Cleanup records a semantic
handoff on a private root property before a correlated morph: either a
no-selection sentinel when `selectedIndex == -1`, or the canonical selected
value. The new initialization consumes and deletes that property. No selection
remains no selection. If a recorded value still identifies an enabled option,
it remains current across reorder, relabel, or regroup. Otherwise current
selection resolves in this order: the incoming enabled server `value`, the
synthesized placeholder, the first enabled option, then no selection. A
supplied valid client `value` wins after this handoff.
Option output also uses value-derived private morph keys, but selection
correctness does not depend on an option remaining under the same parent.

There is no client `options` prop, async request owner, filtering, pagination,
virtualization, or item mutation API. Applications may resolve async data on
the server and rerender the complete finite collection. Browser-created
option mutation is outside the contract.

## 14. Server render, morph, and cleanup

Without JavaScript, the component is a complete styled native Select with
option/group semantics, forms, keyboard, touch, validation, autofill, and
reset. Client activation adds reactive configuration, optional controlled
selection, reflected state, native-invalid integration, one replaceable value
reconciliation task, and one independent bounded task per reset event.

Each server render snapshots nested option sequences and attrs once before
validation. Correlated rerender records the selected-value or no-selection
sentinel on the retained root, disposes listeners and tasks, morphs the server
option collection, then initializes with the semantic handoff from section 13. Controlled selection
is reapplied only after the latest prop is validated against the new options.
Initialization and every programmatic state path recheck validity. Cleanup
removes listeners, cancels the reconciliation task and every pending reset
task, clears Field native-invalid state, and removes the private initialized
marker. A semantic handoff property on a detached root is inert and remains
collectible with that root.

The reset listener captures the native Form owner for one initialization.
Paired Select rerender is required when external ownership changes; cleanup
must detach the old owner before initialization attaches the new one.

Initialization registers `{required: placeholder exists, readonly: false}`
with the nearest Field's private reactive capability registry. Cleanup removes
only its own generation. Same-turn replacement makes the new generation
authoritative before Field effects settle, so child-only placeholder add/remove
cannot leave stale or transient required state.

No observer, global listener, recurring timer, overlay, detached node, or
request survives removal.

## 15. Security and content trust

`name`, `id`, `value`, `placeholder`, `autocomplete`, option values/labels,
and group labels are plain text. Trusted-string subclasses are converted to
exact base strings before escaping. Arbitrary non-string `__html__` objects
are rejected. Option identity strings normalize newlines and reject U+0000 so
Python, HTML, DOM, JS, and FormData observe one value. Option label text cannot
create HTML or script nodes.

`attrs`, `class_`, `style`, and option/group `attrs` are the explicit
developer-trusted escape paths. Their caller-owned mappings are copied before
validation so later mutation cannot bypass the checked snapshot. Exact,
case-insensitive dynamic/property aliases that can write owned attributes,
object binding spreads, and content/value ownership directives are rejected.
Owned native attributes, public part/state markers, Citry runtime namespaces,
Citry Events namespaces, and private initialization markers are reserved at
their applicable destination.

Static background indicator CSS is package-authored and has no remote URL,
runtime HTML injection, or caller-controlled SVG content. The family performs
no request and stores no sensitive data beyond the native selected value.

## 16. Assets and performance

Native Select adds one CSS asset and one component JS asset, each emitted once
per registered concrete class. Runtime work is proportional to the flattened
option count during initialization and value resolution. Client value lookup
uses a Map from option values to elements. There is no popup tree, filter,
virtualizer, observer, global listener, recurring timer, icon component, font,
or remote dependency.

Asset reporting records raw, gzip, and Brotli bytes. Diagnostic scaling
records 1, 10, 100, and 1,000 Select instances with representative small
option sets and no timing gate. Exact wheel qualification excludes design,
snippets, tests, and reports.

## 17. Acceptance matrix

Checked-in server tests cover the public records and component schema; native
root, ordered options and one-level groups; placeholder and initial selectedness;
unique, nonempty, canonical values; disabled selected-value rejection; invalid
collection shapes; direct-string de-trusting; rejected arbitrary `__html__`;
owned and dynamic-ownership attributes; trusted native listeners; copied
option/group attrs; one nested snapshot per render; Field required and
read-only capabilities; Form read-only opt-out; merged Field IDREFs; root
class/style/attrs; no slots; exports; and exact assets.

Checked-in focused browser tests cover:

- native root, options/groups, disabled choices, FormData, required validity,
  Field relationships, native empty-string events, and placeholder selection;
- immutable controlled restoration, client null without a placeholder,
  unsupported dynamic Field required fallback, and the controlled
  native-invalid reconciliation race;
- same-turn uncanceled then canceled reset and canceled then uncanceled reset;
- ancestor variables, the public selector, client variant/size reflection,
  and computed presentation; and
- real correlated rerenders that preserve selection by value across
  reorder/regroup, use structural fallback after removal, and preserve semantic
  no-selection.

The shared quality route proves exact initialization, initial and active
release/reset states, no console errors, and no serious or critical axe
findings. Docs projection discovers all ten component-owned previews; the
focused docs browser pass exercises groups, controlled release/reacquisition,
clear-to-placeholder, theme variables, dark scope, and page-wide console
cleanliness. Asset, scaling, reference-schema, registration, and exact wheel
tools include Native Select.

Configured release qualification still covers exhaustive invalid client-prop
recovery; semantic no-write assignment counting; external Form ownership and
paired rebinding; retained-Field child-only placeholder capability changes;
required/invalid recovery after every programmatic path; cleanup with pending
tasks; real keyboard and pointer paths; autofill; disabled-group interaction;
unlayered class order; dark, RTL, narrow, zoom, forced-color, and print
profiles; Nu HTML output; and repeated correlated morph/removal cycles.

Manual release evidence covers real mobile pickers, VoiceOver/TalkBack and
desktop screen readers, browser autofill, 400% zoom, long localized labels,
forced colors, and platform-specific option styling.

## 18. Compatibility classification

1. **Stable public API:** `CNativeSelect`, option/group records and alias,
   inputs/defaults, no-slot rule, native-root anatomy, unique value identity,
   placeholder behavior, Field/Form boundary, controlled/uncontrolled phases,
   native events, variables, selector, and reflected attributes.
2. **Evolvable defaults:** exact colors, spacing, radius, static indicator
   drawing, and internal JS/CSS organization while the native root and public
   customization contracts remain.
3. **Private:** context keys, initialized marker, internal effective variables,
   value map, invalid-episode tracking, and bounded task details.

Breaking changes include renaming the family to generic Select, adding a
wrapper or custom popup, accepting multiple selection under the same API,
mixing raw slots with structured options, changing placeholder empty-value
semantics, permitting duplicate values, or simulating read-only behavior.

## 19. Public documentation contract

`cnative_select/api.md` is the reader-first guide and `api.yml` is the
exhaustive structured reference. The page uses one ocean-research theme and
teaches the complete labelled control first, then option structures,
placeholder/required behavior, variants and sizes, form states, controlled
selection, native picker boundaries, direction and long labels, and theming.

Example catalog:

| Order and module | Reader task | Visible behavior | Controls/environment | Contract evidence |
|---|---|---|---|---|
| 1. `at_a_glance.py` | Classify an ocean habitat | labelled required Select with groups and description | dark and narrow smoke | first impression, Field, grouping, placeholder |
| 2. `compose_select.py` | Build template and Python-composed controls | two equivalent native Selects | no controls | structured records, composition, no wrapper |
| 3. `options_and_groups.py` | Choose an expedition region | flat options, groups, disabled option/group | native interaction | order, disabled semantics, safe text |
| 4. `placeholder_and_required.py` | Choose optional and required destinations | empty prompt can be reselected; required prompt validates | submit/reset | placeholder, validity, reset |
| 5. `variants.py` | Compare closed-control treatments | outline, filled, plain | light/dark | variant CSS and native picker boundary |
| 6. `sizes.py` | Compare compact and prominent controls | sm, md, lg | narrow and long labels | visual sizing, overflow |
| 7. `field_states.py` | Review survey states | required, disabled, invalid, Form-disabled | static comparison | state ownership and no read-only claim |
| 8. `controlled_selection.py` | Steer a research-vessel assignment | select, replace, clear, release, reacquire | explicit owner controls | client ownership, native event flow, reset |
| 9. `native_picker.py` | Understand the browser-owned picker | native focus, keyboard, touch, external form | RTL and coarse-pointer note | platform boundary, native methods/events |
| 10. `theme_customization.py` | Adapt Selects to two expedition brands | variable, selector, and class overrides | scheme toggle | public CSS contract |

Every preview keeps controls outside rendered content, starts code collapsed,
uses the shared preview background, initializes without console errors, and
has no serious or critical axe finding. API reference order follows the
component reference schema and omits empty surfaces.

## 20. Open decisions and deferred work

Resolved for this pass:

- one native root, structured server-owned options, single selection, enabled
  empty placeholder, unique option values, no raw option slot, no simulated
  read-only state, native events, and no custom popup;
- the static background indicator remains part of the closed-control styling,
  while forced colors restores native appearance; and
- option/group records stay data types rather than public rendered
  components.

Owned by the later custom families:

- rich item content, search, custom popup ownership, multiple selection,
  chips, clear actions, and dynamic item slots are covered by `CSelect`,
  `CMultiSelect`, `CListbox`, and `CTagsInput` as appropriate.

Still deferred:

- generic async-data and virtualized-collection ownership;
- capabilities beyond the private reactive Field required/read-only
  registration introduced by this family; and
- real-device platform qualification. Localization follows the shared Citry
  UI migration contract; NativeSelect contributes no catalog keys.

Definition of done for this family:

Native Select is complete when:

- current standards and library research, complaint disposition, Vuetify
  capability pass, this 20-section contract, and the ten-example catalog pass
  independent design review;
- runtime implements the native-root, option, Field/Form, value ownership,
  security, style, and cleanup contracts without a custom overlay;
- focused server/browser, docs, shared quality, assets, scaling, package, and
  wheel checks pass with claims limited to proven evidence;
- public guide, structured reference, snippets, exports, registration,
  projection, navigation, and wheel inventory agree; and
- independent implementation review finds no unresolved high- or
  medium-severity issue.

Human visual, keyboard, assistive-technology, mobile-picker, autofill, and
real-device polish remains named release evidence rather than an automated
claim.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
