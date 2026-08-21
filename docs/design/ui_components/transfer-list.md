# Transfer List

**Status:** implementation contract accepted for the first production pass.
The family is a form-capable, progressively enhanced pair of multi-select
listboxes. It deliberately does not make drag and drop the only way to move or
reorder items.

## 1. Purpose and product bar

`CTransferList` lets a person build an ordered chosen set from a finite set of
server-rendered options. `CTransferListItem` declares one stable value, plain
label, optional rich presentation, and disabled state. The family owns:

- selection inside each pane;
- moving selected or all enabled items between panes;
- reordering chosen items with explicit buttons;
- controlled and uncontrolled chosen-value state;
- native multi-select form submission and reset;
- keyboard, focus, status, responsive, RTL, and localized behavior.

The shortest intended use is:

```html
<c-CTransferList name="reviewers">
  <c-CTransferListItem value="ada" label="Ada" />
  <c-CTransferListItem value="grace" label="Grace" />
</c-CTransferList>
```

The native `<select multiple>` is usable before JavaScript starts and when
JavaScript is unavailable. Enhancement adds the two panes and controls; it
never changes the submitted value model. The family does not own fetching,
filtering, virtualization, hierarchical items, arbitrary interactive option
content, or drag-and-drop-only operation. Applications use MultiSelect or
Combobox for compact selection and `CVirtualWindow` plus application state for
remote or windowed data.

## 2. Prior art and complaints

Research was refreshed on 2026-08-21.

| Product or standard | Surface inspected | Citry UI decision |
|---|---|---|
| WAI-ARIA APG Listbox and rearrangeable examples | multi-select keyboard model, separate focus and selection, labeled listboxes, explicit move/reorder toolbars | Use two labeled listboxes, roving DOM focus, modifier-free Space selection, optional range shortcuts, and real buttons. |
| PrimeNG 22 PickList | controlled source/target data, transfer and reorder controls, filtering, templates, drag/drop, listbox semantics, keyboard table, localized control labels | Adopt controlled value, explicit transfer/reorder controls, templates, and localization. Defer filtering and drag/drop rather than shipping a second inaccessible path. |
| PatternFly 6 Dual list selector | composable two-pane anatomy, selection counts, search, rich/tree variants, controls wrapper, drag/drop add-on | Adopt titled panes, counts, stable parts, responsive layout, and a separate toolbar. Keep trees and drag/drop outside this flat family. |
| Material UI 9 Transfer List | basic/enhanced compositions, move-all/select-all choices, desktop-only limitation, no exported high-level component | Ship a cohesive component and a stacked narrow layout; do not repeat the desktop-only limitation. |
| Vaadin current List Box Web Component | multi-selection, disabled items, custom item rendering, warning that listbox is not itself a complete form field | Keep listbox semantics for interaction while retaining a real native select as the form owner. |
| Native HTML `select[multiple]` | submission, disabled options, required validity, reset, no-script interaction | Make one native select authoritative for form value and progressive fallback. |
| Vuetify current component suite | no dedicated transfer component; List, Button, Checkbox, and layout composition are the available building blocks | Use Vuetify mainly for styled list/button density and theme comparison. Do not invent compatibility props for a component Vuetify does not expose. |

Common complaints addressed are ambiguous arrow-only controls, inaccessible
drag-and-drop, losing form submission, desktop-only layouts, focus loss after
moving items, selected order diverging from submitted order, and English text
embedded in JavaScript.

Vuetify disposition:

| Vuetify surface or job | Citry support path | Decision |
|---|---|---|
| multiple List selection | direct behavior | two `role=listbox` panes with `aria-multiselectable=true` |
| List item content | item slot | preserve server-rendered rich but noninteractive presentation |
| disabled List item | item input | `CTransferListItem.disabled` |
| Button groups and density | direct API/CSS | visible localized controls, size input, public theme variables |
| responsive layout | family CSS | stack panes and controls at narrow widths |
| transfer/reorder state | new family behavior | ordered `value` plus `onValueChange` |
| filtering, tree data, drag/drop | deliberate omission | compose another selection family or wait for separate evidence |

## 3. Public composition and anatomy

```text
CTransferList → div.cui-transfer-list
├─ select[multiple]                       native fallback/form owner
└─ div.cui-transfer-list__control
   ├─ section.cui-transfer-list__pane     available
   │  ├─ heading + selection count
   │  ├─ div[role=listbox]
   │  │  └─ div[role=option] × available item
   │  └─ empty message
   ├─ div[role=toolbar]                   transfer controls
   │  └─ button × up to four
   └─ section.cui-transfer-list__pane     chosen
      ├─ heading + selection count
      ├─ div[role=listbox]
      │  └─ div[role=option] × chosen item
      ├─ empty message
      └─ div[role=toolbar]                reorder controls
         └─ button × four
```

`CTransferListItem` is declaration-only and must be a direct logical child of
one `CTransferList`. Its `label` supplies native fallback text, typeahead text,
and an accessible name. Its optional default slot replaces only the visible
presentation. Interactive descendants are unsupported because listbox options
do not expose a nested interaction model.

The anatomy review retains the item declaration because stable value, native
option, rich content, disabled state, and morph identity must come from one
record. Toolbars and panes are internal anatomy, not public child components.

## 4. Server inputs and client inputs

`CTransferList` server inputs:

| Input | Type/default | Effect |
|---|---|---|
| `id` | `str | None = None` | Sets the root ID and bases stable listbox and option IDs. |
| `value` | `Sequence[str] = ()` | Ordered initial chosen values; each must name one declaration. |
| `name`, `form` | `str | None = None` | Native multi-select form ownership. |
| `required`, `disabled` | `bool = False` | Native validity/effective disabled state and enhanced behavior. |
| `show_move_all` | `bool = True` | Includes Add all and Remove all controls. |
| `show_reorder` | `bool = True` | Includes chosen-order controls. |
| `size` | `"sm" | "md" | "lg" = "md"` | List height and control density. |
| label/message inputs | source English catalog defaults | Per-output explicit override; caller text never registers a catalog binding. |
| `class_`, `style`, `attrs` | structured values/`None` | Extend the root without replacing owned state or anatomy. |

`CTransferListItem` inputs are required nonempty `value` and `label`, optional
`disabled`, and direct `class_`, `style`, `attrs` for the rendered option.
Values are unique and may not contain U+0000, CR, or LF.

Client inputs:

| Input | Type | Omitted/null | Invalid | Effect |
|---|---|---|---|---|
| `value` | unique known string array | uncontrolled/server value; `null` returns uncontrolled | diagnose and retain last valid | authoritative chosen order when controlled |
| `required`, `disabled` | boolean | server value | diagnose and retain last valid | reactive form and interaction state |
| `onValueChange` | function | no callback | diagnose and retain last valid | receives transfer, reorder, and reset requests |

## 5. State model

The committed value is an ordered list of chosen item values. Available order
is always authored declaration order minus the committed value. Chosen order
is exactly committed value order. This makes one value sufficient to restore
the complete UI.

Pane selections and active options are ephemeral browser state. Selection is
not the form value. Moving selected items appends them to chosen order; moving
them back restores their authored available order. Reorder controls affect
chosen order only. Disabled items never move or reorder.

With client `value`, actions request a new value and wait for that prop. Without
it, the browser commits synchronously, updates the native select, emits native
`input` then `change`, and calls the callback. A controlled callback receives
the same detail with `controlled=true` but no native events are forged before
acceptance.

## 6. Slots and slot data

`CTransferList.default` accepts only `CTransferListItem` declarations.
`CTransferListItem.default` is optional and receives
`{value, label, disabled, in_target, index}`. Its fallback is `label`.
Pane headings, empty text, buttons, and status are localized message inputs,
not structural slots, so the family retains coherent semantics and responsive
layout.

## 7. Callbacks, native events, and methods

`onValueChange(next, detail)` receives:

```text
{value, previousValue, moved, source, controlled, sourceEvent}
```

`source` is `add`, `add-all`, `remove`, `remove-all`, `move-top`,
`move-up`, `move-down`, `move-bottom`, `reset`, or `client`. `moved` is the
ordered set directly affected by the action. Callback failures are diagnosed
and do not stop native synchronization or cleanup.

No public imperative methods ship in v1. Focus and actions remain available
through native elements and the controlled value API.

## 8. Semantics, keyboard, focus, and assistive technology

Each pane is a visibly labeled `role=listbox` with
`aria-multiselectable=true`. Options use `role=option`, `aria-selected`,
`aria-disabled`, a roving `tabindex`, and a stable ID. The root reflects
disabled, invalid, and empty-pane states. Toolbars and their visible buttons
have localized accessible names. A stable polite live region announces moves,
reorders, and validation without living inside an `aria-busy` subtree.

The public reflected attribute vocabulary is `role`,
`aria-multiselectable`, `aria-activedescendant`, `aria-selected`,
`aria-disabled`, `aria-invalid`, `data-value`, `data-selected`,
`data-disabled`, `data-required`, `data-invalid`, `data-size`,
`data-available-empty`, and `data-chosen-empty`.

Within a pane:

- Up/Down move focus; Home/End jump; printable text performs bounded
  case-insensitive typeahead;
- Space or Enter toggles the focused option without requiring modifiers;
- Shift+Space and Shift+Arrow extend a range from the selection anchor; and
- Ctrl/Command+A selects every enabled option in that pane.

After an accepted transfer, the first moved option receives focus in its new
pane and moved items remain selected there. After accepted reorder, focus
stays on the first moved option. Controlled rejection keeps focus and
selection in the originating pane. Tab order is pane, enabled controls, pane,
enabled reorder controls; disabled buttons remain discoverable only when their
action is globally present, using native `disabled`.

## 9. Native forms and validation

One real `<select multiple>` owns `name`, `form`, `required`, `disabled`,
selected option order, reset defaults, and submission. Before enhancement it
is visible. After enhancement it is visually hidden, not removed. The enhanced
listboxes are the focus destinations. An invalid native event marks the root,
announces the localized required message, and focuses the chosen pane.

Form reset restores server `value`. Uncontrolled mode commits it; controlled
mode requests it and waits. When `name` is absent the native select still
provides fallback and validity but does not submit. This family does not own
readonly because native multi-select has no equivalent and disabled would
incorrectly suppress submission.

## 10. Styling and theme contract

Stable parts are `transfer-list`, `native`, `control`, `pane`, `pane-header`,
`pane-title`, `count`, `listbox`, `option`, `empty`, `transfer-controls`,
`reorder-controls`, `button`, and `status`. Public variables are
`--cui-transfer-list-pane-size`, `--cui-transfer-list-list-size`,
`--cui-transfer-list-gap`, `--cui-transfer-list-border`,
`--cui-transfer-list-radius`, `--cui-transfer-list-surface`,
`--cui-transfer-list-selected`, `--cui-transfer-list-hover`,
`--cui-transfer-list-focus`, and `--cui-transfer-list-disabled-opacity`.
Defaults live behind private variables in
`citry-ui.theme`; direct `class_` and `style` remain normal escape hatches.

At narrow inline sizes the grid stacks available pane, transfer controls, and
chosen pane. Buttons use text rather than direction-only glyphs, so the same
controls remain intelligible in RTL and when the panes stack.

## 11. Environmental behavior

Logical CSS supports LTR and RTL without changing value order. Forced colors
retain borders, selected state, and focus outlines. Reduced motion disables
transitions. Print shows the two lists and hides controls/status/native form
owner. Zoom and text expansion may grow controls and pane headers without
clipping.

## 12. Overlay and layering behavior

There is no overlay or top-layer behavior. Rich item content must not create
interactive descendants. Tooltips may be composed outside but are never
required to understand a button.

## 13. Collections, async data, and identity

The complete finite declaration set is server-owned. Values are stable,
unique identity. A server morph may replace the set; the replacement value
must reference only new declarations. The family is not an async data
provider. Filtering, remote search, pagination, and virtualization require an
application-owned data boundary rather than hidden client cloning.

## 14. Server render, morph, and cleanup

Initial native options and enhanced panes agree before activation. A retained
root handoff may preserve committed value, pane selection, active values, and
focus only when declaration values still exist. Server value and a reactive
controlled value remain authoritative. Cleanup removes listeners, effects,
form-reset ownership, i18n bindings, mutation guards, and initialized markers.

## 15. Security and content trust

Labels and slot content use ordinary escaped Citry output. JavaScript compares
string values and moves existing owned nodes; it never uses `innerHTML`, parses
markup, evaluates labels, or clones component subtrees. Attribute mappings
reject roles, form ownership, ARIA state, part/identity/runtime markers, and
event/directive overrides owned by the family.

## 16. Assets and performance

One instance owns one native select, one delegated click listener, two
delegated keyboard listeners, one Alpine effect, and one form-reset listener.
There are no per-option listeners, observers, portals, or third-party assets.
Rendering and synchronization are linear in declared item count. Large remote
sets belong in a different product boundary.

## 17. Acceptance matrix

| Area | Required evidence |
|---|---|
| server/schema | exact inputs, declaration rules, duplicate/unknown values, native fallback, initial order, attrs ownership |
| interaction | pointer and keyboard multi-selection, all transfer sources, all reorder sources, disabled items, focus repair |
| control/forms | controlled rejection/acceptance, native input/change order, required invalid focus, reset, form/name/disabled |
| localization | every default/override path, browser announcements, locale switching, no binding on caller overrides |
| environment | narrow layout, RTL, forced colors, reduced motion, print, zoom/text growth |
| lifecycle | morph set changes, handoff, cleanup, callback/i18n failure isolation |
| quality | structured docs, live snippets, standalone scenarios, axe, three-browser suite, asset and timing evidence |

## 18. Compatibility classification

This is a new additive public family. `CTransferList` and
`CTransferListItem`, their callback record, source and size aliases, parts,
variables, reflected attributes, catalog keys, and component registry entries
are public API. Internal declaration/render helpers and runtime hooks are
private.

## 19. Public documentation contract

The page teaches, in order: at-a-glance form use, rich items, controlled value,
keyboard selection, disabled/required behavior, responsive use, localization,
customization, and unsupported remote/interactive cases. Planned snippets are
`at_a_glance.py`, `rich_items.py`, `controlled.py`, `forms.py`,
`accessibility.py`, and `customization.py`. Quality scenarios show default,
required/disabled, controlled, narrow, and RTL states.

The structured API ends with Translation keys and lists every key even though
all have source English defaults.

## 20. Open decisions and deferred work

Filtering, tree transfer, drag and drop, cross-pane arbitrary ordering,
virtualization, remote loading, per-pane action slots, and readonly are
deferred. Each changes collection ownership, accessibility, or native form
semantics and needs separate evidence. No blocker remains for the first pass.

## 21. Internationalization

`CTransferList.I18n.messages_locale` is `en-US`. The final component member
owns catalog messages for pane titles and empty states, selection counts,
toolbar names, eight action buttons, move/reorder announcements, and required
validation. Initial DOM uses server `tr()`. Stable visible text and button
labels use `$c-tr` only on catalog-default branches. Count text and browser
announcements use `i18n.bind()` because selection counts and action details are
browser state. Explicit caller label/message props are preserved across locale
changes and emit no Citry UI catalog binding.
