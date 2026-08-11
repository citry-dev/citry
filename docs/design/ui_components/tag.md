# Citry UI Tag and TagGroup specification

**Status (2026-08-10):** implementation pass complete. The checked-in server,
three-engine browser, accessibility, schema, preview, registration, asset, and
docs-projection evidence is green. Manual assistive-technology and release
qualification in section 17 remains a release task.

## 1. Purpose and product bar

`CTagGroup` presents a labelled collection of compact categories, filters, or
keywords. `CTag` declares one stable item in that collection. A group can be
descriptive, selectable, actionable, removable, or combine selection with an
action. Tag is deliberately distinct from `CBadge`: Badge is static status
text, while TagGroup owns collection identity, keyboard navigation, selection,
removal requests, and focus recovery.

The production bar is useful server HTML, exact controlled and uncontrolled
selection, safe removal requests, stable focus across Citry rerenders, light
and dark styling, RTL navigation, native-fieldset disabled behavior, and a
bounded client runtime. The closest ARIA pattern for an interactive collection
is a horizontal layout grid. A descriptive group uses native list semantics.

| Application job | Shortest template | Support path |
|---|---|---|
| Show descriptive categories | `<c-CTagGroup label="Topics"><c-CTag value="css">CSS</c-CTag></c-CTagGroup>` | direct API; native list semantics |
| Select one filter | `<c-CTagGroup label="Status" selection_mode="single"><c-CTag value="open">Open</c-CTag></c-CTagGroup>` | direct API |
| Select several filters | `<c-CTagGroup label="Amenities" selection_mode="multiple">...</c-CTagGroup>` | direct API |
| Request removal | `<c-CTagGroup label="Topics" removable>...</c-CTagGroup>` | direct API; owner removes the item |
| Run an item action | `<c-CTagGroup label="Genres" actionable>...</c-CTagGroup>` | direct API through `onAction` |
| Show a leading icon or Avatar | `<c-fill name="start">...</c-fill>` on `CTag` | composition |
| Enter or edit arbitrary tags | future TagsInput | separate form-control family |
| Navigate to a URL | native anchor styled by the application, or Button/Menu composition | deliberate omission from the grid contract |
| Display static status | `CBadge` | separate component |

Python composition uses the same two owners:

```python
CTagGroup(
    label="Amenities",
    selection_mode="multiple",
    slots={
        "default": [
            CTag(value="laundry", slots={"default": "Laundry"}),
            CTag(value="parking", slots={"default": "Parking"}),
        ],
    },
)
```

Non-goals are free-form entry, editing, autocomplete, form submission,
drag-and-drop ordering, virtualization, async collection loading, arbitrary
links inside the composite, and a headless API. `CTagsInput` remains a future
form-control family rather than a mode of TagGroup.

## 2. Prior art and complaints

The shared taxonomy, local prior-art audit, Vuetify dossier, complaint
register, Badge specification, and current implementations below were reviewed
before fixing this contract.

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| WAI-ARIA APG layout grid | reviewed 2026-08-10 | grid semantics, roving focus, directional keys, Home and End | Interactive TagGroup is one horizontal layout grid with one roving entry target. |
| HTML | reviewed 2026-08-10 | native Button, list, disabled fieldset, focus, and form behavior | Remove controls are `button type="button"`; descriptive groups use list/listitem; native fieldset disabledness dominates configuration. |
| Vuetify | 4.1.5 | `VChip.tsx`, `VChipGroup.tsx`, group and slide-group behavior | Adopt compact variants, sizes, selection, leading content, close action, disabled state, and group value ownership. Omit router coupling, arbitrary tag polymorphism, draggable chips, and slide pagination. |
| React Aria | current source reviewed 2026-08-10 | `useTagGroup`, `useTag`, TagGroup docs | Adopt grid/row/gridcell anatomy, stable keys, selection modes, Delete and Backspace removal, focus recovery, and labelled group ownership. |
| React Spectrum | current docs reviewed 2026-08-10 | TagGroup content, selection, actions, removal, links, and group action | Adopt selection, actions, removal, label, description, start media, and size. Defer links, row limiting, and a group action because existing Citry components compose those jobs. |
| Material UI | current docs reviewed 2026-08-10 | Chip clickable, deletable, link, size, variant, keyboard behavior | Keep selection/action and removal distinct, use native remove Button, and make Delete and Backspace work from the focused Tag. |
| Web Awesome | current docs reviewed 2026-08-10 | Tag appearance, size, pill, removal event, parts | Adopt a compact removable surface and explicit public parts. A component callback replaces the custom DOM removal event. |
| Chakra UI | current docs reviewed 2026-08-10 | Tag anatomy, close trigger, icon/avatar composition, variants and sizes | Adopt start/default/remove regions without exposing administrative wrapper components. |
| Ant Design | 6.x docs reviewed 2026-08-10 | Tag, CheckableTag, CheckableTagGroup, close, link, controlled values | Adopt controlled single/multiple selection. Omit arbitrary colors and a second standalone checkable class. |

No current issue report established a Tag-specific blocker. Broader collection
reports reinforce the need to preserve stable key identity and focus across
removal rather than deriving either from labels or indexes.

### Vuetify disposition

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `VChip` content | direct API | `CTag.default` | Adopt. |
| prepend icon/avatar | composition | `CTag.start` | Adopt one start region. |
| append icon/avatar | composition | use label content when essential; remove is the owned end control | Omit a generic interactive end region. |
| closable and close label | direct API | `CTagGroup.removable`, `remove_label`, `onRemove` | Group owns consistent removal. |
| selected/filter indicator | direct API | selection mode, `data-selected`, indicator part | Adopt. |
| `VChipGroup` single/multiple/mandatory value | direct API | `selection_mode`, `value`, `mandatory`, `onValueChange` | Adopt with exact string identity. |
| disabled group and item | direct API/native | group and item `disabled`; native fieldset | Adopt. |
| density and arbitrary dimensions | CSS/public variables | size and variables | Keep three suite sizes; application CSS owns uncommon dimensions. |
| tonal/flat/text/elevated/outlined variants | direct API/CSS | `soft`, `solid`, `outline` | Compress to three coherent variants. |
| arbitrary color | CSS variables | documented `--cui-tag-*` inputs | Omit a color prop. |
| router link and `href` | composition | native anchor or Button outside the grid | Omit from v1 to preserve real link semantics. |
| custom root tag | native/composition | fixed semantic elements | Omit. |
| draggable | separate future collection work | unsupported | Omit. |
| slide-group arrows, centering, overflow paging | CSS/composition | wrapping list; consumer ScrollArea when needed | Omit. |
| close, filter, prepend, append scoped slots | composition | `start`, `default`; owned indicator/remove parts | Keep the smallest explicit anatomy. |
| click and group model events | callbacks/native events | `onAction`, `onValueChange`, `onRemove`; root native events | Adopt without duplicate custom DOM events. |

## 3. Public composition and anatomy

```citry-html
<c-CTagGroup
  label="Amenities"
  selection_mode="multiple"
  c-value="['laundry']"
>
  <c-CTag value="laundry">Laundry</c-CTag>
  <c-CTag value="parking">Parking</c-CTag>
</c-CTagGroup>
```

The public declaration tree is exactly `CTagGroup > CTag`. `CTag` fails
outside a group. A Tag unprovides the group declaration context before
rendering authored label/start content, so nested Tag declarations in a label
fail rather than joining the outer collection.

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CTagGroup` | `div` | `class_`, `style`, and `attrs` target this root | Contains one label, optional description, and one owned collection. |
| `CTag` | `div` | `class_`, `style`, and `attrs` target this visible Tag root | Direct declaration in one group; owns one unique canonical value and label. |

The group contains stable public `group-label`, `list`, optional `description`,
and Tag roots. An interactive list uses `role="grid"`; each Tag uses
`role="row"` and contains one `role="gridcell"`. A descriptive list uses
`role="list"` and Tag roots use `role="listitem"`.

`CTagGroup.id` may supply the relationship prefix. Otherwise the component
generates `cui-tag-group-<render-id>`. Supplied IDs must be nonempty, contain
no ASCII whitespace, and contain no U+0000. Each Tag label ID derives from the
group ID and render identity, not its application value.

Server validation allows a labelled empty collection and rejects duplicate
values, unknown initial values, misplaced Tags, and nested declarations.
Client settled-DOM validation rejects
foreign direct collection children and interactive, labelable, focusable, or
editable descendants inside Tag label/start content.

## 4. Server inputs and client inputs

### `CTagGroup`

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `label` | `str` | required | structural | Nonempty visible label fallback and accessible name. |
| `id` | `str | None` | `None` | structural | Optional exact relationship prefix. |
| `value` | `str | Sequence[str] | None` | `None` | initial value | Single mode accepts one string/None; multiple accepts a unique sequence; none mode accepts only empty. |
| `selection_mode` | `"none" | "single" | "multiple"` | `"none"` | structural | Selects descriptive or selectable behavior and value shape. |
| `mandatory` | `bool` | `False` | structural | Selectable modes only; prevents the last selection from clearing. |
| `actionable` | `bool` | `False` | structural | Enables item activation and `onAction`. |
| `removable` | `bool` | `False` | structural | Enables remove controls and Delete/Backspace requests. |
| `remove_label` | `str` | `"Remove"` | structural | Nonempty visually hidden accessible label combined with the Tag label. |
| `disabled` | `bool` | `False` | reactive configuration | Local disabled request; CForm and native fieldset remain dominant. |
| `variant` | `"soft" | "solid" | "outline"` | `"soft"` | reactive configuration | Presentation. |
| `size` | `"sm" | "md" | "lg"` | `"md"` | reactive configuration | Tag geometry and text. |
| `class_` | `CClassValue | None` | `None` | structural | Merges on the root. |
| `style` | `CStyleValue | None` | `None` | structural | Merges on the root. |
| `attrs` | `Mapping[str, object] | None` | `None` | structural | Trusted root attributes after ownership validation. |

### `CTag`

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `value` | `str` | required | structural identity | Nonempty canonical string, unique within the group. |
| `disabled` | `bool` | `False` | reactive configuration | Prevents focus, selection, action, and removal for this Tag. |
| `text_value` | `str | None` | `None` | reactive configuration | Optional nonempty canonical typeahead text; otherwise current label text is read. |
| `class_` | `CClassValue | None` | `None` | structural | Merges on the Tag root. |
| `style` | `CStyleValue | None` | `None` | structural | Merges on the Tag root. |
| `attrs` | `Mapping[str, object] | None` | `None` | structural | Trusted Tag-root attributes after ownership validation. |

### Client inputs

| Owner/input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| Group `value` | single string/`null`, or multiple string array | releases control and preserves the last effective selection | explicit empty selection | keep the last valid selection and report once until valid/omitted | `aria-selected`, indicator, `data-selected`, callbacks |
| Group `disabled` | boolean | server fallback | invalid | server fallback and one episode diagnostic | focus eligibility, actions, remove Buttons, mirrors |
| Group `variant` | enum string | server fallback | invalid | server fallback and one episode diagnostic | group and Tag `data-variant`, CSS |
| Group `size` | enum string | server fallback | invalid | server fallback and one episode diagnostic | group and Tag `data-size`, CSS |
| Group `onValueChange` | function | no notification | no callback | ignore and report once | selection requests |
| Group `onAction` | function | no notification | no callback | ignore and report once | action requests |
| Group `onRemove` | function | no notification | no callback | ignore and report once | removal requests |
| Tag `disabled` | boolean | server fallback | invalid | server fallback and one episode diagnostic | item eligibility and mirrors |
| Tag `textValue` | string | server fallback/current label | invalid | server fallback/current label and one episode diagnostic | typeahead matching |

Python and client strings normalize CRLF and CR to LF and reject U+0000. Client
control begins whenever `value` is supplied, including `null`. Removing the
prop releases to the last effective controlled selection rather than the
original server value. Nested groups isolate state and callbacks.

## 5. State model

The group tracks ordered item registrations, effective disabledness, current
roving item, and committed selection. Selection shape is `null | str` in
single mode and `list[str]` in multiple mode. None mode always has no
selection.

| Transition | Guard | Uncontrolled result | Controlled result | Callback |
|---|---|---|---|---|
| Activate unselected Tag | enabled and selectable | select it; single replaces, multiple adds | DOM remains at supplied value after handlers | changed value request |
| Activate selected Tag | enabled and selectable | clear unless mandatory would become empty | same request rule | only when the proposed value differs |
| Activate actionable Tag | enabled and actionable | no component state required | same | `onAction` after any value request |
| Remove by Button/Delete | enabled and removable | collection is unchanged until owner rerenders | same | one `onRemove` request |
| Disable one focused Tag | another enabled Tag exists | nearest following, then preceding, receives focus | same | none |
| Disable whole group | focus is inside | list root receives programmatic focus; no item stays tabbable | same | none |
| Remove focused Tag structurally | surviving item exists | nearest following, then preceding, receives focus | same | none |
| Remove final Tag dynamically | focus was inside | empty labelled list/grid receives focus | same | none |
| Remove selected Tag structurally | item disappears | selection prunes to known survivors | controlled unknown keys diagnose; effective DOM uses the known intersection | none; owner initiated structure change |
| Rerender/reorder retained value | unique identity survives | selection and focus follow value, not index | same | none |

In multiple mode, Delete or Backspace requests all currently selected,
removable values when the focused Tag is selected. Otherwise it requests only
the focused value. Repeated invalid client values form one continuous
diagnostic episode, ended only by valid supply or omission.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CTagGroup` | `default` | yes | one | `CTagGroupDefaultSlotData {}` | none |
| `CTagGroup` | `label` | no | zero or one | `CTagGroupLabelSlotData {}` | escaped `label` input |
| `CTagGroup` | `description` | no | zero or one | `CTagGroupDescriptionSlotData {}` | wrapper omitted |
| `CTag` | `default` | yes | one | `CTagDefaultSlotData {}` | none |
| `CTag` | `start` | no | zero or one | `CTagStartSlotData {}` | wrapper remains hidden |

Group default content accepts only direct `CTag` declarations and ordinary
template control flow that settles to direct Tags. Tag label and start slots
accept noninteractive phrasing content only. They reject anchors, Buttons,
inputs, selects, textareas, labelable/form controls, nested Tag declarations,
`contenteditable`, and focusable descendants. The start wrapper is
decorative and hidden from the accessible name; the label wrapper alone names
the Tag.

No dynamic slot namespace is needed. Application data uses ordinary Citry
loops with stable Tag values.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onValueChange` | `(value, CTagValueChangeDetail)` | accepted activation proposes a different selection | before `onAction`, after native click/keydown listener dispatch reaches the group | request only; supplied value wins after handlers | not cancellable |
| `onAction` | `(value: str, CTagActionDetail)` | enabled actionable Tag activation | after value request; skipped if callback disposed the generation | selection may remain controlled independently | not cancellable |
| `onRemove` | `(values: list[str], CTagRemoveDetail)` | enabled remove Button or Delete/Backspace | once per activation; collection remains mounted | owner decides whether to rerender | not cancellable |

Value detail contains `value`, `previousValue`, `tagValue`, `source` equal to
`"activation"`, `controlled`, and `nativeEvent`. Action detail contains
`value`, `source`, and `nativeEvent`. Remove detail contains `values`,
`tagValue`, `source` equal to `"remove-button"` or `"delete-key"`, and
`nativeEvent`.

Native `click`, `keydown`, `focusin`, and focus events remain available through
Alpine listeners on public roots. The group installs capture listeners for its
owned click, keydown, and focus bookkeeping so a consumer bubble listener
cannot disable collection behavior. No custom DOM event and no public method
are added.

## 8. Semantics, keyboard, focus, and assistive technology

Descriptive mode uses `role="list"` and `role="listitem"`; Tags are not
focusable. Interactive mode uses `role="grid"`, `role="row"`, and one
`role="gridcell"` per Tag. The group label supplies `aria-labelledby`; the
optional description supplies `aria-describedby`. Selectable rows expose
`aria-selected`; disabled rows expose `aria-disabled`.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| interactive Tag | click, Enter, Space | selection/action transaction | current Tag | yes for Space; click/Enter as needed to avoid duplicate activation |
| Tag | ArrowRight/ArrowDown | next enabled Tag, wrapping | next Tag | yes |
| Tag | ArrowLeft/ArrowUp | previous enabled Tag, wrapping | previous Tag | yes |
| RTL Tag | ArrowRight/ArrowLeft | previous/next physical Tag respectively | resolved Tag | yes |
| Tag | Home/End | first/last enabled Tag | resolved Tag | yes |
| removable Tag | Delete/Backspace | one removal request | stays until owner rerender | yes |
| removable Tag | Tab | enter remove Button for the current Tag | remove Button | yes |
| remove Button | Shift+Tab | return to its Tag row | Tag | native or explicit equivalent |
| group | printable key | buffered case-insensitive prefix match using `text_value` or label text | next match | yes |
| any | Tab from final internal target | leave the component | browser next target | no |

Only one Tag row has `tabindex="0"`. Remove Buttons use `tabindex="-1"` and
are reached programmatically from their row, preserving one page-tab entry for
the composite. Pointer activation focuses the Tag before selection/action.
Disabled Tags are skipped and cannot activate programmatically through the
component handler. Focus indicators remain visible on both Tag and remove
Button.

Typeahead collapses whitespace, uses the nearest inherited valid `lang` when
available, falls back to locale-neutral lowercase on invalid locale data,
accepts Shift-modified printable characters, ignores composition and
Ctrl/Meta shortcuts, and cycles repeated characters through matching Tags.

Automated role/name/state checks and axe are required. Manual release tasks
cover VoiceOver/Safari, NVDA/Firefox or Chromium, JAWS/Chromium, TalkBack, and
touch exploration, particularly grid announcements and removal.

## 9. Native forms and validation

TagGroup is not a form control and contributes no FormData. Remove Buttons are
always `type="button"`, so the family cannot submit or reset an enclosing
form. `CForm.disabled` and effective native `fieldset[disabled]` disable
interaction. TagsInput will separately own names, hidden values, validation,
and arbitrary text entry.

Citry Events may rerender the collection after callbacks, but TagGroup does
not own transport, pending state, retry, or server validation.

## 10. Styling and theme contract

Variants are `soft`, `solid`, and `outline`; sizes are `sm`, `md`, and `lg`.
Tags are pill-shaped by default. Exact fallback colors may evolve while role,
contrast, focus, disabled, and selected differentiation remain stable.

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-tag-gap` | length | gap between Tags | `0.5rem` |
| `--cui-tag-row-gap` | length | wrapped-row gap | `0.5rem` |
| `--cui-tag-background` | color | unselected Tag fill | variant and scheme derived |
| `--cui-tag-foreground` | color | unselected Tag text | variant and scheme derived |
| `--cui-tag-border-color` | color | Tag border | variant and scheme derived |
| `--cui-tag-selected-background` | color | selected fill | scheme-derived primary |
| `--cui-tag-selected-foreground` | color | selected text | scheme-derived contrast color |
| `--cui-tag-selected-border-color` | color | selected border | selected background |
| `--cui-tag-focus-color` | color | focus outline | scheme-derived primary |
| `--cui-tag-radius` | length | Tag corner radius | `999px` |
| `--cui-tag-min-height` | length | Tag target height | size derived |
| `--cui-tag-padding-inline` | length | Tag inline padding | size derived |
| `--cui-tag-internal-gap` | length | indicator/start/label/remove spacing | size derived |
| `--cui-tag-font-size` | length | Tag label size | size derived |
| `--cui-tag-label-color` | color | group label text | `CanvasText` |
| `--cui-tag-description-color` | color | group description text | scheme-derived muted text |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="tag-group"]` | group root | all group mirrors | contains label, list, optional description |
| `[data-citry-ui-part="group-label"]` | visible group label | always | names the list/grid |
| `[data-citry-ui-part="list"]` | list or grid | interactive/descriptive, disabled, empty | contains direct Tags |
| `[data-citry-ui-part="description"]` | optional description | when authored | describes list/grid |
| `[data-citry-ui-part="tag"]` | visible Tag row | selected, disabled, removable, variant, size | direct collection child |
| `[data-citry-ui-part="indicator"]` | selection indicator | selectable; visible when selected | direct Tag child |
| `[data-citry-ui-part="start"]` | decorative start content | when authored | direct Tag child |
| `[data-citry-ui-part="tag-label"]` | Tag accessible label | always | direct Tag child |
| `[data-citry-ui-part="remove"]` | remove Button | removable groups | direct Tag child |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| group `data-selection-mode` | `none`, `single`, `multiple` | collection behavior |
| group `data-actionable` | present/absent | activation callback enabled |
| group `data-removable` | present/absent | removal enabled |
| group `data-disabled` | present/absent | effective group disabledness |
| group and Tag `data-variant` | `soft`, `solid`, `outline` | effective variant |
| group and Tag `data-size` | `sm`, `md`, `lg` | effective size |
| Tag `data-value` | canonical string | public item identity |
| Tag `data-selected` | present/absent | effective selection |
| Tag `data-disabled` | present/absent | effective item disabledness |
| Tag `data-removable` | present/absent | remove affordance exists |

Default CSS lives in `citry-ui.theme`, uses logical properties and low
specificity, and resolves public variables through private fallbacks.

## 11. Environmental behavior

Light and dark schemes must preserve 4.5:1 ordinary text contrast and 3:1
boundaries, indicators, and focus. Nested opposite schemes inherit correctly.
Logical layout and RTL-aware navigation apply without a locale provider.

Reduced motion removes nonessential color/indicator transitions. Forced colors
uses system ButtonText, Highlight, HighlightText, GrayText, and a visible
focus outline. Tags wrap at narrow widths; labels use `overflow-wrap:anywhere`
and do not create page overflow at 400% zoom. Pointer targets meet the
component size contract and remove Buttons remain separately operable. Print
keeps labels, selection indicators, and boundaries while removing hover-only
effects.

Library-authored visible/accessibility strings are the `remove_label` default
`"Remove"` only. Applications may supply a translated value now; locale
selection remains future shared work.

## 12. Overlay and layering behavior

The family creates no overlay, portal, top-layer element, scroll lock, focus
trap, or global dismissal listener. Tags may appear inside Dialog, Drawer,
Popover, Menu content where semantically valid, and other overlays without
changing their ownership.

## 13. Collections, async data, and identity

Every Tag value is a canonical nonempty string unique within its direct group.
Identity never comes from label text or index. Server loops may add, remove,
or reorder Tags. A retained value preserves selection and focus; removal uses
the prior settled order with the following item winning an equal-distance tie.

An initially empty server collection is a valid labelled list or grid and may
accept later Tags. A client/server update may remove the final Tag; the empty
collection remains focusable only when it must preserve focus. The group owns no loading,
error, pagination, virtualization, or remote-fetch state. Applications compose
Alert, Progress, Skeleton, or ordinary content around it.

## 14. Server render, morph, and cleanup

Server HTML exposes the correct label, description, roles, selected state,
disabled state, one roving tabindex, and form-safe remove Buttons. Without
JavaScript it remains readable and inspectable; selection/removal enhancement
requires the client runtime.

Ancestor-first activation provides the group registration context before Tag
initializers run. Registrations, disabled/text effects, and cleanup coalesce to
one root reconciliation per task. Correlated rerenders preserve committed
selection, focused value, and prior per-level order when the server selection
baseline is unchanged. Changing unrelated variant/size/attrs never resets
selection. A changed server value baseline resets an uncontrolled group unless
a client-controlled value is currently supplied.

Cleanup removes three root capture listeners, one focus listener, typeahead
timer, pending reconciliation, native-fieldset observers, and every Tag
registration. Old generations cannot focus, notify, or mutate a replacement.
Two groups with the same values remain isolated.

## 15. Security and content trust

Labels, values, and text values are de-trusted plain strings and escaped by
Citry. U+0000 is rejected; line endings canonicalize. Slot markup uses Citry's
ordinary trusted-template boundary, but settled validation rejects interactive
or focusable content that would break the grid model.

Group and Tag attrs reject case-insensitive static and dynamic/property aliases
for owned role, tabindex, ID, ARIA relationships/state, disabledness, runtime
markers, and state/configuration mirrors. Whole-object `x-bind`, `x-html`,
`x-text`, `x-if`, `x-for`, `x-ignore`, `x-model`, `x-modelable`, and
`x-teleport` are rejected. `aria-hidden`, `contenteditable`, popover/command
attributes, and hidden/inert ownership are rejected on both destinations.
Callbacks receive values as data and never interpolate them as executable
source.

## 16. Assets and performance

The family adds one CSS asset and one JavaScript asset. It uses no external
dependency, icon component, font, overlay coordinator, or network request.
One root owns delegated click, keydown, and focusin capture listeners plus a
focusout listener. Native-fieldset observation exists only for actual ancestor
fieldsets and disconnects on cleanup. Tags add registration effects, not
per-item event listeners.

Asset reporting records raw, gzip, and Brotli sizes. Scaling covers 1, 10,
100, 500, and 1,000 Tags plus 1, 10, 100, and 500 groups. Initialization and
one selection/removal action must remain linear in direct item count. Duplicate
validation uses a Set, never pairwise search.

## 17. Acceptance matrix

Checked-in automated evidence must cover:

- Python construction, tag syntax, public types, exports, introspection, and
  wheel registration;
- exact server anatomy, roles, names, descriptions, IDs, selected/disabled
  state, Button types, escaped hostile strings, attrs rejection, and no-JS
  output;
- descriptive, single, multiple, mandatory, actionable, removable, combined,
  disabled, empty-after-removal, and nested-instance paths;
- controlled request/rejection/acceptance/removal, invalid episodes, omission
  release, changed server baseline, and unrelated server configuration morphs;
- pointer, touch, Enter, Space, arrows, Home, End, typeahead, Delete,
  Backspace, Tab into remove, reverse Tab, and consumer stopPropagation;
- add, reorder, focused removal, selected removal, final removal, reinsert,
  fragment initialization, correlated rerender, cleanup, and two equal-valued
  groups;
- CForm/native-fieldset disabled changes including first-legend reorder;
- axe, role/name/state snapshots, focus visibility, light/dark/nested scheme,
  RTL, forced colors, reduced motion, narrow/long content, 200%/400% zoom, and
  print;
- every variant/size, ancestor/root variable overrides, public selector
  overrides, two brand adaptations, and unlayered consumer CSS;
- asset report, bounded listener/observer counts, scaling, quality scenario,
  docs preview, API schema/projection, registration, package allowlist, and
  focused Ruff/Node syntax.

Manual release evidence remains required for the screen-reader/browser pairs
in section 8, real touch devices, keyboard-only task completion, 400% visual
review, and two-brand design review. Nu HTML validation runs when Java is
available.

## 18. Compatibility classification

Stable public API includes both component names, inputs, slots and slot-data
types, callbacks and detail records, public variables, selectors, reflected
attributes, validation/error behavior, and defaults that affect behavior.

Behavioral and structural contract includes list/grid anatomy, direct Tag
ownership, accessible naming, keyboard/focus behavior, controlled selection,
removal requests, disabled precedence, no-JS output, morph handoff, and cleanup.

Exact colors, spacing, and transition timing are evolvable while semantic
roles, contrast floors, dimensions controlled by size, and customization
meaning stay stable. `.cui-*`, `--_cui-*`, registration markers, JavaScript
organization, timers, observer implementation, and incidental wrappers are
private.

## 19. Public documentation contract

`ctag/api.md` teaches the valid declaration tree, selection, controlled use,
removal, action, icons/avatars, keyboard behavior, styling, forms, and edge
cases. `ctag/api.yml` exhaustively lists both owners under Inputs, Slots,
Events, CSS, Attributes, Selectors, and Interfaces. Methods is `-`.

Planned public examples:

| Source | Reader task | Visible states and controls | Contract coverage |
|---|---|---|---|
| `at_a_glance.py` | compare descriptive, selectable, and removable Tags | three labelled groups | shortest jobs and anatomy |
| `selection.py` | control single/multiple values | accept/reject/release controls | controlled state and callbacks |
| `removal.py` | remove one or selected Tags | owner-backed rerender and empty result | removal, focus recovery, empty state |
| `actions.py` | run compact item actions | action log; combined selection/action | callback ordering |
| `content.py` | add Icon/Avatar start content and long labels | narrow wrapper | slots, naming, wrapping |
| `variants.py` | compare soft/solid/outline and sm/md/lg | static matrix | visual contract |
| `disabled.py` | compare item/group/Form/fieldset disabledness | reactive fieldset toggle | effective disabled state |
| `customization.py` | apply two brand mappings | variable and selector overrides | customization contract |
| `environment.py` | inspect RTL, nested dark, forced colors, print | environment controls | environmental behavior |

Focused docs browser evidence exercises selection, removal with focus recovery,
action ordering, keyboard navigation, nested isolation, variable overrides,
and zero unexpected console/page errors. API examples do not deliberately
supply invalid values; invalid recovery remains focused-test evidence.

## 20. Open decisions and deferred work

The following are explicit nonblocking deferrals:

- Tag links wait for a design that preserves real anchor semantics without
  weakening the grid contract.
- TagsInput owns free-form entry, editing, hidden form values, validation,
  autocomplete, paste delimiters, and IME behavior.
- row limiting, overflow pagination, drag-and-drop, and virtualization wait for
  demonstrated application demand and their separate behavior contracts.
- an optional group-wide action is composition with Button and Group until it
  proves a repeated job that requires collection ownership.

No unresolved decision blocks implementation.
