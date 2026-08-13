# Listbox

**Status:** production implementation pass completed on 2026-08-10. Runtime,
public API data, examples, quality wiring, server tests, and Chromium/Firefox/
WebKit interaction and accessibility evidence are checked in. Release-wide
manual assistive-technology, touch, zoom, and Nu HTML review remain part of the
normal qualification pass.

## 1. Purpose and product bar

`CListbox` presents a persistent, scrollable collection from which a user can
select one or several values. It follows the WAI-ARIA Listbox pattern and ships
as a styled Citry UI family.

The family owns three public components:

- `CListbox` owns the visible label, selection, keyboard navigation, focus,
  disabled state, and collection reconciliation;
- `CListboxOption` declares one selectable value and its visible content; and
- `CListboxGroup` labels a related subset of direct Options.

Common jobs and their shortest intended expressions:

| Job | Template | Python composition | Support path |
|---|---|---|---|
| Choose one visible option | `<c-CListbox label="Density"><c-CListboxOption value="compact">Compact</c-CListboxOption></c-CListbox>` | `CListbox(label="Density", slots={"default": CListboxOption(value="compact", slots={"default": "Compact"})})` | direct API |
| Choose several visible options | `<c-CListbox label="Columns" multiple c-value="['owner']">...</c-CListbox>` | `CListbox(label="Columns", multiple=True, value=["owner"], ...)` | direct API |
| Show an icon or metadata | named `start`, `description`, and `end` Option fills | matching Option slots | direct slots |
| Group options | `CListboxGroup(label="Europe")` | same component | direct API |
| Submit one compact choice | `CSelect` | `CSelect(...)` | separate component |
| Submit several compact choices | `CMultiSelect` | `CMultiSelect(...)` | separate component |
| Filter or enter text | `CCombobox` | `CCombobox(...)` | separate component |
| Navigate or run actions | `CList` or `CMenu` | composition | separate components |
| Virtualize a very large collection | - | - | unsupported in v1 |

The component is complete when it has useful server HTML, exact Listbox ARIA,
pointer and keyboard parity, controlled and uncontrolled selection, dynamic
collection recovery, Fieldset-disabled behavior, theme and environment support,
public examples, structured reference data, and focused cross-browser evidence.

Non-goals:

- no popup, filtering, free-form entry, action items, links, or nested controls;
- no form submission, required validity, or Field ownership;
- no grid layout, range selection, drag reordering, async loading, or
  virtualization in v1; and
- no headless component.

## 2. Prior art and complaints

The design began with the shared taxonomy, complaint register, Vuetify,
React Aria, Ark/Zag, and Web Component dossiers. The component-specific refresh
reviewed these sources on 2026-08-10:

| Product or standard | Version or review date | Surface inspected | Decision supported |
|---|---|---|---|
| WAI-ARIA Authoring Practices | current 2026-08-10 | Listbox pattern, keyboard model, roles, grouping, typeahead | use `listbox`/`option`, separate focus from selection, label groups, and support arrows/Home/End/typeahead |
| WAI-ARIA | 1.2 Recommendation | `listbox`, `option`, `group`, `aria-selected`, `aria-multiselectable` | exact semantic state and owned relationships |
| Vuetify | 4.0.7 | `VList`, `VListItem`, `VSelect`, selection strategies and item slots | keep rich item regions and suite sizing; do not merge persistent Listbox with Select |
| React Aria / Spectrum | current 2026-08-10 | ListBox collections, controlled selection, Sections, disabled items, selection behavior | keyed declarations, controlled values, selection independent from focus |
| Ark UI / Zag | Ark 5.38.1; Zag 1.42.0 | Listbox anatomy, single/multiple modes, grouping, orientation, typeahead | use a compact compound family and one root callback |
| Vaadin Web Components | latest docs updated 2026-03-02 | `vaadin-list-box`, multi-selection, custom presentation, best practices | keep Listbox persistent and lightweight; leave field/form behavior to Select |
| Citry UI Tree and Menu | workspace 2026-08-10 | declaration context, roving focus, morph handoff, slot trust boundary | reuse contextual declarations and settled-DOM validation without inheriting Tree/Menu semantics |

Recurring complaints and failure modes shape the contract:

- listboxes become difficult to understand when option names repeat long
  prefixes or absorb every descriptive region into the accessible name;
- focus-following-selection can destroy a deliberate multi-selection while a
  user only navigates;
- prop-heavy object collections make rich server composition terse at first
  but hard to customize and morph safely;
- disabled options often remain activatable through programmatic `click()` or
  disappear from navigation inconsistently; and
- collection removal can leave focus and controlled values pointing at nodes
  that no longer exist.

Citry adopts explicit declarations, label-only accessible names, separate
descriptions, activation-based selection, skipped disabled Options, one
modifier-free multiple-selection model, and deterministic removal recovery.

### Vuetify disposition

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| selected model | direct API | `value`, client `value`, `onValueChange` | adopt with exact controlled request semantics |
| multiple | direct API | `multiple` | adopt as structural server configuration |
| mandatory | direct API | `mandatory` | adopt; prevents an empty committed selection |
| disabled root/item | direct API and native ancestor | `disabled` on root/Option plus Fieldset | adopt effective disabled state |
| item title/value/disabled keys | declarations | Option `value`, slots, `disabled` | reject configurable object-key indirection |
| prepend/default/subtitle/append item content | slots | `start`, default, `description`, `end` | adopt with explicit name and trust boundaries |
| groups/subheaders/dividers | declaration | `CListboxGroup`; no divider | adopt semantic groups; omit decorative dividers in v1 |
| active and selected styling | CSS and public state | `data-active`, `data-selected`, public variables | adopt |
| density/color/rounded dimensions | direct API and CSS | `size`, `variant`, variables, class/style | compress into suite vocabulary |
| navigation/action list behavior | separate component | `CList`, `CMenu` | reject mixed roles |
| virtual scrolling | omitted | none | defer until a real large-data requirement exists |

## 3. Public composition and anatomy

Smallest template:

```citry-html
<c-CListbox label="Density">
  <c-CListboxOption value="comfortable">Comfortable</c-CListboxOption>
  <c-CListboxOption value="compact">Compact</c-CListboxOption>
</c-CListbox>
```

Equivalent Python composition:

```python
CListbox(
    label="Density",
    slots={
        "default": [
            CListboxOption(
                value="comfortable",
                slots={"default": "Comfortable"},
            ),
            CListboxOption(
                value="compact",
                slots={"default": "Compact"},
            ),
        ],
    },
)
```

Anatomy:

```text
CListbox root
|- visible label
`- semantic listbox
   |- CListboxOption
   `- CListboxGroup (role=group, labelled)
      `- CListboxOption
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CListbox` | wrapper `div` plus owned `div[role=listbox]` | `attrs` -> wrapper; `listbox_attrs` -> semantic listbox | listbox `aria-labelledby` -> visible label |
| `CListboxOption` | `div[role=option]` | `attrs` -> Option | `aria-labelledby` -> label; optional `aria-describedby` -> description |
| `CListboxGroup` | `div[role=group]` | `attrs` -> Group | `aria-labelledby` -> Group label |

The listbox accepts only direct Options and Groups. A Group accepts only direct
Options and cannot be nested. Option content and Group labels cannot declare
Listbox children and must contain no interactive, focusable, form-associated,
editable, or nested option content. Nested `CListbox` roots belong outside an
Option.

Values are nonempty canonical strings. CRLF and CR normalize to LF; U+0000 is
rejected. Values need not be valid HTML IDs because Citry hashes them into
generated element IDs. Values are unique across the complete Listbox, including
Groups. Empty collections and empty Groups fail server rendering. Settled client
structure fails closed until it becomes valid again.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `CListbox.label` | nonempty string | required | structural | visible and accessible Listbox name |
| `value` | string, `None`, or sequence of strings | `None` | initial value | one value in single mode; sequence in multiple mode; members must exist |
| `multiple` | Boolean | `False` | structural | selects single or multiple state shape and ARIA |
| `mandatory` | Boolean | `False` | reactive configuration | prevents clearing the final selection; requires an initial value when true |
| `disabled` | Boolean | `False` | reactive configuration | disables the complete collection; Fieldset remains dominant |
| `loop` | Boolean | `False` | reactive configuration | wraps Arrow navigation at the ends |
| `variant` | `plain`, `soft`, or `outline` | `outline` | reactive configuration | visual surface treatment |
| `size` | `sm`, `md`, or `lg` | `md` | reactive configuration | Option geometry |
| `class_`, `style` | Citry class/style value or `None` | `None` | structural | wrapper styling |
| `attrs` | mapping or `None` | `None` | structural | allowed wrapper attributes |
| `listbox_attrs` | mapping or `None` | `None` | structural | allowed semantic-listbox attributes |
| `CListboxOption.value` | nonempty canonical string | required | structural identity | unique selectable identity |
| `disabled` | Boolean | `False` | reactive configuration | makes the Option unselectable and skipped by navigation |
| `text_value` | string or `None` | `None` | reactive configuration | explicit typeahead text; otherwise current label text |
| `class_`, `style`, `attrs` | shared styled inputs | `None` | structural | concrete Option styling and allowed attributes |
| `CListboxGroup.label` | nonempty string | required | structural | visible and accessible Group name |
| `class_`, `style`, `attrs` | shared styled inputs | `None` | structural | concrete Group styling and allowed attributes |

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| root `value` | single string/`null`, or string array in multiple mode | release to committed selection | controlled empty selection | diagnose once, release from current committed state | selected Options and callback ownership |
| `mandatory`, `disabled`, `loop` | Boolean | server fallback | invalid, server fallback | diagnose once and use server fallback | selection guards, navigation, disabled state |
| `variant`, `size` | documented string | server fallback | invalid, server fallback | diagnose once and use server fallback | root reflection and CSS |
| `onValueChange` | function | no callback | no callback | diagnose and ignore | selection notifications |
| Option `disabled` | Boolean | server fallback | invalid, server fallback | diagnose and use fallback | Option semantics and navigation |
| Option `textValue` | string or `null` | server/default label text | default label text | diagnose and use server fallback | typeahead |

Owner commits do not notify. In single mode, a supplied `null` is an
intentional controlled empty selection. In multiple mode a supplied `null`
also means controlled empty, while `[]` is the preferred explicit form.
Omission releases control and preserves the latest valid effective value.

## 5. State model

Public state consists of the selected vector, active Option, effective disabled
state, and valid/invalid settled structure.

| Trigger | Guard | Selection result | Focus result | Notification |
|---|---|---|---|---|
| single Option activation | enabled and not already selected | that value | activated Option | one request/commit |
| multiple Option activation | enabled | toggle that value | activated Option | one request/commit |
| Escape | not mandatory and selection nonempty | empty | unchanged | one request/commit |
| controlled owner update | valid value | exact supplied value | preserve active Option | none |
| control omission | previously controlled | latest effective value becomes committed | unchanged | none |
| selected Option removal | selected value disappeared | filter missing values; single becomes empty | nearest following, then preceding enabled survivor | one structural notification |
| active Option removal | active value disappeared | unchanged unless selected | nearest following, then preceding enabled survivor | selection notification only when needed |
| root becomes disabled | any | unchanged | move focus to owner Document body when focus was inside | none |
| structure becomes invalid | any | preserve internal selection | fail closed and remove from Tab order | one diagnostic episode |

In controlled mode a user request notifies but does not mutate selected ARIA or
public state until the owner accepts it. Structural removal is non-rejectable
for the live DOM: missing values disappear visually. A controlled owner gets one
fallback request per continuous missing-value episode. Releasing control commits
that requested fallback rather than reviving the missing value.

Disabled Options remain represented with `aria-disabled=true`, but navigation
skips them and every pointer, keyboard, and programmatic activation path guards
selection.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CListbox` | `default` | yes | one fill containing declarations | `{}` | none |
| `CListboxOption` | `default` | yes | one | `{value}` | none |
| `CListboxOption` | `start` | no | zero or one | `{value, selected, disabled}` server snapshot | absent |
| `CListboxOption` | `description` | no | zero or one | `{value}` | absent |
| `CListboxOption` | `end` | no | zero or one | `{value, selected, disabled}` server snapshot | absent |
| `CListboxGroup` | `default` | yes | one fill containing Options | `{}` | none |

The label wrapper alone supplies the Option accessible name. Description is
referenced separately. Start and end are `aria-hidden` decorative/textual
regions. Every Option slot and Group label remains noninteractive. Browser
selection changes do not rerender server slot data; public DOM state is the
reactive styling surface.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onValueChange` | `(value, detail)` | accepted activation, Escape clear, or selected-value removal | after focus settles; before uncontrolled DOM sync only when controlled | reports requested value; supplied prop remains authoritative | not cancellable |

`value` is `str | None` in single mode and `list[str]` in multiple mode.
`detail` contains `value`, `previousValue`, `option`, `selected`, `controlled`,
`source` (`pointer`, `keyboard`, or `structure`), and `sourceEvent` when one
exists.

Native `click`, `keydown`, and focus events remain available through Alpine
listeners. The family dispatches no custom DOM event and exposes no public
imperative method.

## 8. Semantics, keyboard, focus, and assistive technology

The semantic surface has `role=listbox`; Options have `role=option` and exact
Boolean `aria-selected`; multiple mode adds `aria-multiselectable=true`.
Groups have `role=group` and a visible `aria-labelledby` label. Disabled state
uses `aria-disabled`. The label, description, and decorative regions do not
pollute each other's accessible computation.

Options use roving DOM focus. The selected enabled Option is the initial Tab
stop; otherwise the first enabled Option is. It has `tabindex=0`; every other
Option has `tabindex=-1`. One Tab enters the composite and the next Tab leaves
it.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| Option | ArrowDown/ArrowUp | no selection change | next/previous enabled Option | yes |
| Option | Home/End | no selection change | first/last enabled Option | yes |
| Option | printable key, including Shift characters | buffered prefix match; repeated character cycles | next matching enabled Option | yes when handled |
| Option | Enter or Space | request selection | same Option | yes |
| Option | Escape | request empty when permitted | same Option | yes when handled |
| Listbox | Tab/Shift+Tab | no state change | ordinary page order continues | no |
| Option | pointer activation | request selection | clicked Option | no |

Typeahead uses explicit `text_value` or normalized current label text. It
collapses whitespace, accepts Shift-modified printable characters, rejects
Control/Meta shortcuts and composition, and falls back to locale-neutral
lowercase if the nearest inherited `lang` is invalid.

## 9. Native forms and validation

Listbox is not a form participant and does not emit hidden inputs. `name`,
`required`, validation, reset, and Field composition belong to `CSelect` and
`CMultiSelect`. Native form controls are forbidden in Option content. A
Listbox inside a disabled native Fieldset still becomes effectively disabled
because native ancestry is stronger than local configuration.

## 10. Styling and theme contract

Variants are `plain`, `soft`, and `outline`; sizes are `sm`, `md`, and `lg`.

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-listbox-gap` | length | label-to-surface gap | `0.375rem` |
| `--cui-listbox-max-block-size` | length | scroll boundary | `18rem` |
| `--cui-listbox-background` | color | surface background | variant-derived Canvas |
| `--cui-listbox-foreground` | color | primary text | `CanvasText` |
| `--cui-listbox-muted-color` | color | descriptions and disabled text | scheme-aware muted text |
| `--cui-listbox-border-color` | color | outline/dividers | scheme-aware subtle border |
| `--cui-listbox-hover-background` | color | pointer feedback | CanvasText mix |
| `--cui-listbox-selected-background` | color | selected Option | scheme-aware blue surface |
| `--cui-listbox-selected-foreground` | color | selected primary text | scheme-aware blue text |
| `--cui-listbox-focus-color` | color | focus outline | `Highlight` |
| `--cui-listbox-radius` | length | outer and Option corners | `0.625rem` |
| `--cui-listbox-option-padding` | padding shorthand | Option geometry | size-derived |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="listbox-root"]` | wrapper and root attrs | size, variant, disabled | owns label then surface |
| `[data-citry-ui-part="listbox-label"]` | visible Listbox label | disabled | direct root child |
| `[data-citry-ui-part="listbox"]` | semantic scroll surface | multiple, disabled | direct root child |
| `[data-citry-ui-part="listbox-option"]` | selectable Option | active, selected, disabled | direct listbox or Group child |
| `[data-citry-ui-part="listbox-indicator"]` | decorative selection mark | selected | direct Option child |
| `[data-citry-ui-part="listbox-option-start"]` | decorative leading content | Option states | direct Option child when present |
| `[data-citry-ui-part="listbox-option-copy"]` | label and description layout | Option states | direct Option child |
| `[data-citry-ui-part="listbox-option-label"]` | accessible label | Option states | inside copy wrapper |
| `[data-citry-ui-part="listbox-option-description"]` | accessible description | Option states | inside copy wrapper when present |
| `[data-citry-ui-part="listbox-option-end"]` | decorative trailing content | Option states | direct Option child when present |
| `[data-citry-ui-part="listbox-group"]` | labelled group | disabled descendants | direct listbox child |
| `[data-citry-ui-part="listbox-group-label"]` | visible Group label | none | first Group child |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| root `data-variant` | `plain`, `soft`, `outline` | effective presentation |
| root `data-size` | `sm`, `md`, `lg` | effective geometry |
| root `data-multiple` | present/absent | selection mode |
| root `data-mandatory` | present/absent | empty-selection guard |
| root `data-disabled` | present/absent | effective root disabled state |
| Option `data-value` | canonical string | stable identity |
| Option `data-selected` | present/absent | effective selected state |
| Option `data-active` | present/absent | current roving focus owner |
| Option `data-disabled` | present/absent | effective disabled state |

## 11. Environmental behavior

The family uses `light-dark()`, Canvas system colors, logical properties, and
the shared theme layer. Start/end regions follow inline direction. Narrow
content wraps instead of widening the page. The Listbox scrolls within its
public maximum block size at zoom. Reduced motion removes decorative
transitions. Forced colors preserves selected and focus state with system
colors and outlines. Print shows all current Options without the interactive
max-height or focus ring.

Library-authored visible strings: none. Labels and option text are authored by
the application.

## 12. Overlay and layering behavior

Listbox never creates an overlay, portal, top-layer element, scroll lock, or
outside-dismissal listener.

## 13. Collections, async data, and identity

Every Option value is unique across the root collection. DOM/declaration order
is collection order. Group labels are not options. Server morphs may add,
remove, and reorder Options; the browser reconciles once after the settled
batch. Retained values preserve selected and active state. Removed active state
chooses the nearest enabled survivor, preferring the following sibling on a
tie. Selected removal follows section 5.

The family has no browser item-array input, loading state, pagination, or
virtualization. Applications use server morphs for dynamic collections and
`CCombobox` for async filtered results.

## 14. Server render, morph, and cleanup

Without JavaScript, the labelled role/option structure and initial selected and
disabled ARIA remain useful. Server Options have one roving Tab stop.
Activation installs one delegated click listener, one delegated keydown
listener, one focusin listener, one collection observer, and bounded native
Fieldset observation. Reconciliation is coalesced per root.

Correlated rerenders preserve committed uncontrolled selection and active
identity when the server value baseline is unchanged. A changed server value
baseline resets uncontrolled selection. Cleanup cancels timers, disconnects
observers, removes listeners/readiness markers, and leaves no stale callback
able to mutate a replacement generation.

## 15. Security and content trust

Labels, values, descriptions, and Group labels are plain escaped text or
trusted component-template output under Citry's ordinary slot boundary.
Values never become executable source. IDs derive from framework identity and
hashed canonical values.

Root, Listbox, Option, and Group attribute mappings reject owned identity,
roles, focus, selection ARIA, visibility, semantic naming, runtime markers,
whole-object bindings, structural directives, and aliases that can overwrite
them. Option/Group content rejects interactive, focusable, editable,
form-associated, and nested Listbox anatomy at server and settled-client
boundaries.

## 16. Assets and performance

The family adds one CSS asset and one root JavaScript initializer; Options add
a small initializer only when reactive Option client props are used by the
runtime. It uses no external package, icon bundle, font, or overlay runtime.

The quality tools record raw/gzip/Brotli family assets and bounded server
render/output sizes at 1, 10, 100, 500, and 1,000 Options. Browser evidence
asserts one coalesced root reconciliation after initial child registration and
bounded observer/listener cleanup. Virtualization is not promised.

## 17. Acceptance matrix

Checked-in automated evidence must cover:

- exact public schemas, typing, exports, registration, and wheel inclusion;
- single/multiple/mandatory server anatomy and ARIA;
- Groups, rich Option regions, names, descriptions, and noninteractive
  enforcement;
- controlled request, acceptance, rejection, external update, invalid episode,
  and control release;
- uncontrolled pointer, Enter, Space, Escape, and structural-removal commits;
- Arrow/Home/End, loop, typeahead, repeated characters, shifted characters,
  disabled skipping, Tab boundaries, and programmatic click guards;
- Fieldset disabled changes and first-Legend exception;
- add/remove/reorder morph handoff, nearest focus recovery, retained selection,
  cleanup, and reinitialization;
- light/dark, nested schemes, RTL, narrow/zoom, long text, reduced motion,
  forced colors, print, public variables, selectors, and cascade overrides;
- settled invalid structure fail-close/recovery, hostile values/attrs/slots,
  duplicate/empty/unknown values, and no console/page errors in valid examples;
- serious/critical axe scans and exact accessibility-tree name/description
  checks; and
- scenario, docs-preview, asset, scaling, project, API-schema, and registration
  contracts.

Manual release evidence names keyboard-only use, VoiceOver/Safari,
NVDA/Firefox or Chromium, JAWS/Chromium, high contrast, 400% zoom, touch,
visual polish, and long translated text.

## 18. Compatibility classification

Stable public API includes component and input names, value shapes, slots,
callback payload, variants/sizes, variables, selectors, reflected attributes,
error behavior, and the explicit non-form boundary. Semantic roles, keyboard,
focus, selection ownership, disabled behavior, no-JavaScript output, and
documented relationships are behavioral contracts.

Exact colors, spacing, indicator drawing, transition timing, and undocumented
wrappers may evolve. `.cui-*` classes, private `data-cui-*` attributes,
initialization markers, JavaScript organization, and private variables are not
public API.

## 19. Public documentation contract

The guide will use this example catalog:

| Module | Reader task | Visible composition and controls | Contract evidence |
|---|---|---|---|
| `at_a_glance.py` | choose one project view | labelled outline Listbox with descriptions | shortest composition, single selection |
| `multiple.py` | choose visible columns | soft multiple Listbox with selected marks | multiple toggle and callback |
| `groups.py` | browse grouped locations | two labelled Groups | grouping ARIA and order |
| `rich_options.py` | compare owners | Avatar/start, description, status/end | slot anatomy and accessible naming |
| `controlled.py` | own selection in browser | accept/reject/release controls | controlled lifecycle |
| `keyboard.py` | learn efficient navigation | enough similarly named Options | arrows, Home/End, typeahead |
| `disabled.py` | inspect partial and root disablement | disabled Option and Fieldset toggle | effective disabled behavior |
| `customization.py` | adapt brand treatment | variants, sizes, public token overrides | cascade and stable parts |

The public `api.md` teaches composition, selection ownership, keyboard use,
the non-form boundary, dynamic collection behavior, and customization.
`api.yml` exhaustively owns Inputs, Slots, Events, CSS, Attributes, Selectors,
and Interfaces. Methods are empty.

## 20. Open decisions and deferred work

No implementation blocker remains in the design.

Deferred work:

- horizontal/grid layouts, modifier-based range selection, Select All,
  virtualization, async loading, action/link Options, and drag reordering;
- a headless Listbox; and
- form participation, which belongs to Select and MultiSelect.

Evidence that persistent Listbox use is rare or consistently misunderstood
would move advanced work to CSelect/CMultiSelect instead of expanding this
family.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
