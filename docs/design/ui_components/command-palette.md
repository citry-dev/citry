# Command Palette

**Status:** implemented and independently reviewed, 2026-08-12.

**Research snapshot:** 2026-08-12. Browser probes used Chromium 151,
Firefox 153, and WebKit 26.5 from the repository Playwright installation.

This specification follows the
[`Citry UI family workflow`](../../../packages/py/citry_ui/docs/component-authoring.md#requalify-one-component-family-at-a-time),
the Fable research workflow, and the shared [component template](./_template.md).

## 1. Purpose and product bar

`CCommandPalette` is a modal, locally searchable collection of application
commands. It combines a visible Dialog title, an editable search combobox, and
a grouped listbox while keeping DOM focus in the search input. Applications
own command registration, domain authorization, global shortcuts, navigation,
and asynchronous data.

There is no WAI-ARIA command-palette pattern. The closest supported composition
is a native modal `<dialog>` containing an editable combobox whose popup is a
listbox. Commands use non-interactive `role="option"` rows and dispatch a value
to one application callback. A command is not a selected form value and no
public selected-value or active-value state exists.

The production bar is:

- native Dialog modality, focus containment, Escape, outside dismissal, page
  scroll locking, nested-overlay behavior, and focus return are supplied by the
  shared Dialog controller rather than copied into this family;
- the input has a stable name, listbox relationship, and active descendant;
- plain substring filtering is deterministic, local, synchronous, and stable;
- groups, visual separators, descriptions, keywords, disabled commands,
  shortcut hints, empty results, looping, and per-command close policy work in
  template and direct Python composition;
- controlled `open` and `query` state cannot create two state owners;
- IME input, native text editing, ancestor Forms, owner callbacks, retained
  morphs, open ShadowRoots, and cleanup have exact behavior; and
- Chromium, Firefox, WebKit, automated accessibility checks, manual VoiceOver
  and NVDA passes, security probes, scaling, and strict asset gates all pass.

Common jobs and their shortest intended forms are:

| Job | Template or Python expression | Support path |
|---|---|---|
| Show a small palette | `<c-CCommandPalette label="Commands" c-entries="commands" />` | Direct API with frozen record data supplied by the server |
| Open from a Button | `activator` slot with `activator_attrs` spread on `CButton` and `activator_disabled` passed to its `disabled` input | Direct slot composition |
| Search labels and aliases | command `label` plus `keywords=("theme", "appearance")` | Direct record API and built-in substring filtering |
| Organize commands | `CCommandPaletteGroup(label="Navigation", commands=(...))` | Direct record API |
| Add a visual boundary | `CCommandPaletteSeparator()` between top-level entries | Direct record API; accessibility-hidden visual separator |
| Show unavailable work | `CCommandPaletteCommand(..., disabled=True)` | Direct record API |
| Show a shortcut hint | `shortcut="Ctrl K"` | Presentational record field; the application still owns the shortcut |
| Execute a command | `$c-props.onAction = (value, detail) => ...` | Root callback with stable value identity |
| Keep a command open | `close_on_action=False` on that command | Direct record API |
| Control visibility and query | client `open`, `query`, `onOpenChange`, and `onQueryChange` | Controlled browser state |
| Add an icon or badge | `item_start` or `item_end` visual renderer slot | Finite, non-interactive composition |
| Navigate to a URL with native modifier and context-menu behavior | a native-link Menu or navigation list | Separate composition; intentionally not a command option |
| Register `Mod+K` globally | application event routing that sets controlled `open` | Application ownership; no component listener or helper |
| Fetch remote commands, keep history, or virtualize results | application workflow or a future specialist family | Unsupported in this family |

There is no headless CommandPalette API. `CDialog`, native Dialog, and an
application-owned search/list implementation are the lower-level alternatives.

Non-goals are a remote command registry, authorization layer, router, global
keyboard manager, fuzzy ranking engine, recent-history store, personalization,
telemetry, nested command pages, arbitrary interactive item renderer, async
fetch protocol, pagination, virtualization, voice input, or mobile launcher.

## 2. Prior art and complaints

### Current-source record

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| WAI-ARIA APG Dialog | Reviewed 2026-08-12 | [Modal Dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) | Reuse Dialog naming, focus containment, Escape, inert background, and return-focus rules. |
| WAI-ARIA APG Combobox | Reviewed 2026-08-12 | [Combobox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/) | Keep DOM focus in the editable input and expose the active option with `aria-activedescendant`; preserve native text editing. |
| WAI-ARIA APG Listbox | Reviewed 2026-08-12 | [Listbox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/listbox/) | Options cannot contain independently operable links or Buttons. Use flat, callback-dispatched command options. |
| HTML Living Standard | Living Standard, reviewed 2026-08-12 | [The `dialog` element](https://html.spec.whatwg.org/multipage/interactive-elements.html#the-dialog-element), [the `search` element](https://html.spec.whatwg.org/multipage/grouping-content.html#the-search-element), [text and search inputs](https://html.spec.whatwg.org/multipage/input.html#text-(type=text)-state-and-search-state-(type=search)) | Native modality and search input behavior remain authoritative; Enter submission in an ancestor Form needs an explicit containment contract. |
| Citry `CDialog` | Repository snapshot 2026-08-12 | `cdialog.py`, design, server tests, three-engine E2E | Extract and reuse the private Dialog controller. Do not copy top-layer, focus, scroll-lock, or restoration logic. |
| Citry collections | Repository snapshot 2026-08-12 | `ccombobox.py`, `clistbox.py`, `cmenu.py`, designs and tests | Reuse active-descendant ownership and text canonicalization; do not inherit selection/form behavior or roving DOM focus. |
| Citry `CInput`, `CField`, and `CTabs` | Repository snapshot 2026-08-12 | runtime, designs, and tests | Reuse theme vocabulary and record/renderer precedents, but do not compose a form-owned `CInput` or declaration component family inside the palette. |
| Vuetify `VCommandPalette` | 4.1.8, published 2026-08-07 | [`VCommandPalette.tsx`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/labs/VCommandPalette/VCommandPalette.tsx), [`types.ts`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/labs/VCommandPalette/types.ts), [`VCommandPaletteItem.tsx`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/labs/VCommandPalette/VCommandPaletteItem.tsx), [`useCommandPaletteNavigation.ts`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/labs/VCommandPalette/composables/useCommandPaletteNavigation.ts) | Adopt a styled modal, records, groups, visual shortcut text, local filter, disabled navigation, controlled open/query, and action-before-close order. Reject its window shortcut, non-input active-descendant placement, IME omission, and advertised-but-unforwarded `to`/`href`. |
| cmdk | 1.1.1 | [Official README and source](https://github.com/dip/cmdk/tree/v1.1.1), [IME issue #363](https://github.com/dip/cmdk/issues/363), prior composition issues [#206](https://github.com/dip/cmdk/issues/206), [#339](https://github.com/dip/cmdk/issues/339), and [#348](https://github.com/dip/cmdk/issues/348) | Adopt input focus, keywords, disabled options, loop, empty state, and consumer-owned actions. Reject text-content identity, implicit fuzzy ranking, compound declarations, and unscoped global-shortcut examples. |
| Radix Dialog | `@radix-ui/react-dialog` 1.1.23 | [Dialog docs](https://www.radix-ui.com/primitives/docs/components/dialog) | Confirms modal composition and focus restoration; Citry uses its native shared Dialog controller instead of another overlay runtime. |
| Mantine Spotlight | 9.5.1 | [Spotlight docs](https://mantine.dev/x/spotlight/), [`Spotlight.tsx`](https://github.com/mantinedev/mantine/blob/9.5.1/packages/%40mantine/spotlight/src/Spotlight.tsx), [`SpotlightRoot.tsx`](https://github.com/mantinedev/mantine/blob/9.5.1/packages/%40mantine/spotlight/src/SpotlightRoot.tsx) | Adopt records, controlled query, accepted-close query clearing, groups, keywords, limit-free local filtering, isolated instances, callback-then-close order, and explicit IME guards. Reject the default global shortcut and DOM-query selection authority. |
| Ark UI Combobox | `@ark-ui/react` 5.38.1 | [Combobox docs](https://ark-ui.com/react/docs/components/combobox), [tagged source](https://github.com/chakra-ui/ark/tree/%40ark-ui/react%405.38.1/packages/react/src/components/combobox) | Ark has no Command component. Its controlled input/highlight state and collection identity inform the internal primitive; async and virtualization examples remain out of scope. |
| Chakra UI | `@chakra-ui/react` 3.36.1 | [Combobox](https://chakra-ui.com/docs/components/combobox), [Dialog](https://chakra-ui.com/docs/components/dialog) | Chakra has no public Command component; its site palette is application composition. Keep Citry's family narrow. |
| Base UI | `@base-ui/react` 1.7.0 | [Autocomplete](https://base-ui.com/react/components/autocomplete), [Dialog](https://base-ui.com/react/components/dialog), [command-palette recipe](https://github.com/mui/base-ui/blob/v1.7.0/docs/src/app/%28docs%29/react/components/autocomplete/demos/command-palette/css-modules/index.tsx) | Adopt record/group composition and auto-highlight; reject treating an Autocomplete selection model as a command-action model. |
| shadcn/ui | CLI 4.17.0 | [Command docs](https://ui.shadcn.com/docs/components/radix/command) | Confirms the cmdk composition and application-owned `Mod+K` example. It is not evidence for library-owned global routing. |
| PrimeVue | 5.0.0 | [AutoComplete](https://primevue.dev/autocomplete/), [Dialog](https://primevue.dev/dialog/) | PrimeVue has no CommandPalette component; its closest surfaces confirm that suggestions, remote completion, Dialog, and command actions are separate jobs. |
| Vaadin Combo Box | 25.2.7 | [Combo Box docs](https://vaadin.com/docs/latest/components/combo-box), [tagged Web Component source](https://github.com/vaadin/web-components/tree/v25.2.7/packages/combo-box) | Confirms record data and input/listbox behavior, but its value selection and data-provider contract are not command actions. |

The local complaint register flags copied focus engines, hidden document
listeners, ambiguous value identity, DOM-text filtering, implicit form
submission, interactive content inside options, uncontrolled payload growth,
and examples that work only through one renderer. This design responds with
private shared controllers, explicit immutable records, callback-only action
values, an inert visual-renderer boundary, a disabled server search control,
and template plus Python examples.

### Semantic pressure and browser probes

No ecosystem API overrides the platform model. Exact Chromium, Firefox, and
WebKit accessibility-tree probes established that `<a role="option">` and
`<button role="option">` are exposed as options, not links or Buttons. Native
links and Buttons in an ordinary list preserve action semantics, but cannot be
the active descendant of the input-owned listbox without changing the pattern.
A grid can contain interactive descendants, but would impose grid-cell
semantics and two-dimensional keyboard rules on a simple one-column command
list. Citry therefore uses non-interactive options and one owner callback.

The same engines confirmed that Enter in a focused search input can submit an
ancestor Form. Server output therefore keeps the palette search input disabled
until activation, and the active runtime contains command Enter without making
the palette a form participant.

### Vuetify disposition

Vuetify is the primary styled-suite reference. Its complete relevant surface
is disposed as follows:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `modelValue` | Direct client API | `open`, `onOpenChange` | Adopt controlled and uncontrolled visibility with Dialog semantics. |
| `search` | Direct client API | `query`, `onQueryChange` | Adopt; clear only after an accepted close, never speculatively on open. |
| `items` | Structural record API | `entries` | Adopt records; use explicit command/group/separator records. |
| action item title/subtitle/value | Command record | `label`, `description`, `value` | Adopt explicit identity and text. |
| icons and avatars | Visual renderer slots | `item_start`, `item_end` | Adopt a finite non-interactive renderer boundary. |
| `hotkey` on a command | Presentational record field | `shortcut` | Adopt display only; no shortcut registration. |
| subheader/divider | Records | `CCommandPaletteGroup`, `CCommandPaletteSeparator` | Adopt with validated ordering and listbox semantics. |
| `disabled` command | Command record | `disabled` | Add the missing typed capability. |
| aliases and search-only text | Command record | `keywords` | Add explicit keywords rather than deriving from DOM text. |
| `closeOnSelect` | Root and command record | `close_on_action` | Adopt with command override and action terminology. |
| `noDataText` | Direct API and slot | `empty_label`, `empty` | Adopt. |
| `placeholder` | Direct API | `placeholder` | Adopt. |
| input icon | Visual renderer | `item_start` does not replace search chrome | Omit a dedicated prop; CSS or a future search-leading slot needs product evidence. |
| root hotkey | Application composition | controlled `open` | Reject component-owned global listener. |
| `offsetTop` | CSS | public spacing/size variables | Omit layout prop. |
| `listProps` | Stable selectors/variables | listbox selector and variables | Reject broad nested prop forwarding. |
| inherited custom filter/filter keys/mode/no-filter | Built-in fixed behavior | deterministic substring filter | Omit until a ranked or external-filter owner job is proven. |
| inherited density and Dialog props | Focused direct API/CSS | `size`; shared fixed Dialog policy | Avoid wholesale inheritance. |
| `update:modelValue` | Callback | `onOpenChange` | Adopt reason-bearing callback. |
| `update:search` | Callback | `onQueryChange` | Adopt exact input value. |
| `click:item` | Callback | `onAction(value, detail)` | Adopt one command callback. |
| `before-select` cancellation | State/record policy | `disabled`, `close_on_action`, controlled `open` | Reject a second cancellable event phase. |
| activator slot | Named slot | `activator` | Adopt with owned attributes. |
| prepend/append/footer/list prepend | Parent composition or CSS | none | Omit arbitrary Dialog regions from this focused task UI. |
| custom input slot | Owned semantic input | none | Reject because it can bypass IME, form, focus, and ARIA ownership. |
| item slot and item subslots | Finite visual renderers | `item_start`, `item_end` | Narrow to inert decorations; label and description remain owned text. |
| no-data slot | Named slot | `empty` | Adopt as a static visual renderer. |
| navigation through `to`/`href` | Native navigation component | none | Reject. The 4.1.8 item source does not forward the advertised fields, and option semantics cannot preserve link behavior. |
| query reset on open | Accepted-close state policy | close-driven query reset | Reject opening-time reset; adopt Mantine's completed-close timing. |
| manual focus restoration | Shared Dialog controller | none | Reject duplicate logic. |

Citry adopts the useful styled workflow while repairing its semantic, IME,
global-listener, and navigation boundaries.

## 3. Public composition and anatomy

The smallest template form receives server-built frozen records:

```html
<c-CCommandPalette
  label="Workspace commands"
  c-entries="command_entries"
  $c-props="{onAction: handleCommand}"
/>
```

The compatible `CButton` activator form keeps Button-owned disabled state out
of the attribute spread:

```html
<c-CCommandPalette label="Workspace commands" c-entries="command_entries">
  <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
    <c-CButton c-attrs="activator_attrs" c-disabled="activator_disabled">
      Open commands
    </c-CButton>
  </c-fill>
</c-CCommandPalette>
```

The direct Python equivalent is:

```python
CCommandPalette(
    label="Workspace commands",
    entries=(
        CCommandPaletteGroup(
            label="Navigation",
            commands=(
                CCommandPaletteCommand(
                    value="open-settings",
                    label="Open settings",
                    keywords=("preferences", "configuration"),
                    shortcut="Ctrl ,",
                ),
            ),
        ),
        CCommandPaletteSeparator(),
        CCommandPaletteCommand(
            value="delete-draft",
            label="Delete draft",
            description="Moves the current draft to Trash",
            intent="danger",
        ),
    ),
)
```

`CCommandPaletteCommand`, `CCommandPaletteGroup`, and
`CCommandPaletteSeparator` are frozen, slotted public value records. They are
not LibraryComponents and cannot render alone. They have no slots, runtime,
client context, or standalone semantics. This is intentionally record-first:
commands are bounded plain data consumed by one owner, while declaration
components would add identity, registration, anatomy errors, and interaction
trust without enabling a user job.

The stable anatomy is:

```text
span [private host; display:contents]
├─ activator slot content                         optional
└─ dialog [part=command-palette]
   └─ section [part=command-palette-surface]
      ├─ header [part=command-palette-header]
      │  ├─ h2 [part=command-palette-title]
      │  └─ button [part=command-palette-close]
      ├─ search [part=command-palette-search]
      │  ├─ label [part=command-palette-search-label]
      │  └─ input type=text role=combobox autofocus [part=command-palette-input]
      ├─ div role=listbox [part=command-palette-listbox]
      │  ├─ div role=option [part=command-palette-command] ...
      │  ├─ section role=group [part=command-palette-group]
      │  │  ├─ div [part=command-palette-group-label]
      │  │  └─ div role=option ...
      │  └─ hr aria-hidden=true [part=command-palette-separator]
      └─ div role=status [part=command-palette-empty]   when no match
```

| Component or record | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CCommandPalette` | native modal `<dialog>` | `class_`, `style`, and `attrs` land on Dialog; `input_attrs` land on the owned search input | one Dialog, title, search input, listbox, close Button, and zero or more record-rendered rows |
| `CCommandPaletteCommand` | none; emits one `role="option"` | record fields only | `value` globally unique in one palette; may be top-level or in one group |
| `CCommandPaletteGroup` | none; emits one labelled `role="group"` | record fields only | contains only commands; groups do not nest |
| `CCommandPaletteSeparator` | none; emits one visual `<hr>` | no fields | top-level only, not first/last/consecutive |

The Dialog, title, close Button, search input, listbox, groups, options, and
relationships are contractual. Incidental text wrappers inside an option are
not. `id` supplies the stable public root identity; generated IDs relate the
title, input, listbox, groups, option labels, and descriptions. Every derived
ID uses escaped framework identity and never raw record values.

`attrs` may carry ordinary Dialog class/style, `dir`, `lang`, test-data, and
unrelated safe listeners/bindings. `input_attrs` may carry class/style,
`inputmode`, `enterkeyhint`, test-data, and unrelated observational listeners.
Consumers cannot replace owned identity, `open`, modality, role, label/control
relationships, input type/value/disabled/name/form/list/autocomplete/autofocus,
active-descendant state, command identity, or public/private mirrors. Bare
binding maps, ownership directives, raw event-handler attributes, runtime
markers, and dynamic writes to owned destinations are rejected.

The component does not author `aria-modal`. Native `<dialog>.showModal()` makes
the enhanced open state modal and supplies the platform accessibility state.
Consumer `aria-modal` is reserved because it could falsely claim modality for
the server-open, non-top-layer fallback.

## 4. Server inputs and client inputs

Public exports are exactly:

```python
CCommandPalette
CCommandPaletteCommand
CCommandPaletteGroup
CCommandPaletteSeparator
CCommandPaletteEntry
CCommandPaletteIntent
CCommandPaletteSize
CCommandPaletteActionSource
CCommandPaletteActionDetail
CCommandPaletteOpenReason
CCommandPaletteOpenChangeDetail
CCommandPaletteQueryReason
CCommandPaletteQueryChangeDetail
CCommandPaletteItemSlotData
```

The aliases and records are exactly:

```python
from dataclasses import dataclass
from typing import Literal, TypeAlias, TypedDict

CCommandPaletteIntent = Literal["default", "danger"]
CCommandPaletteSize = Literal["sm", "md", "lg"]
CCommandPaletteActionSource = Literal["keyboard", "click"]
CCommandPaletteOpenReason = Literal[
    "trigger",
    "escape",
    "outside",
    "close-button",
    "action",
    "native",
    "disabled",
    "ancestor",
    "owner",
]
CCommandPaletteQueryReason = Literal["input", "close"]


@dataclass(frozen=True, slots=True)
class CCommandPaletteCommand:
    value: str
    label: str
    description: str | None = None
    keywords: tuple[str, ...] = ()
    shortcut: str | None = None
    disabled: bool = False
    close_on_action: bool | None = None
    intent: CCommandPaletteIntent = "default"


@dataclass(frozen=True, slots=True)
class CCommandPaletteGroup:
    label: str
    commands: tuple[CCommandPaletteCommand, ...]


@dataclass(frozen=True, slots=True)
class CCommandPaletteSeparator:
    pass


CCommandPaletteEntry: TypeAlias = (
    CCommandPaletteCommand | CCommandPaletteGroup | CCommandPaletteSeparator
)


@dataclass(frozen=True, slots=True)
class CCommandPaletteItemSlotData:
    value: str
    label: str
    description: str | None
    keywords: tuple[str, ...]
    shortcut: str | None
    disabled: bool
    close_on_action: bool
    intent: CCommandPaletteIntent


class CCommandPaletteOpenChangeDetail(TypedDict):
    reason: CCommandPaletteOpenReason
    controlled: bool
    source: object | None


class CCommandPaletteQueryChangeDetail(TypedDict):
    reason: CCommandPaletteQueryReason
    closeReason: CCommandPaletteOpenReason | None
    controlled: bool
    source: object | None


class CCommandPaletteActionDetail(TypedDict):
    query: str
    source: CCommandPaletteActionSource
    item: object
    event: object
    closeOnAction: bool
```

Python record fields use snake_case. Browser callback detail preserves the
documented JavaScript key `closeOnAction`; every other detail key has the same
spelling in Python typing and browser data. `object` means an ephemeral browser
Element or Event reference and is never serialized by the component.

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `entries` | `Sequence[CCommandPaletteEntry]` | required | structural server data | snapshot to tuples; validate record types, global unique command values, group contents, and separator ordering |
| `label` | `str` | required | structural server data | nonempty visible Dialog title and accessible name |
| `id` | optional string | `None` | structural server data | valid explicit ID or generated stable identity |
| `open` | `bool` | `False` | initial browser state | initial native open fallback; client `open` may control later state |
| `query` | `str` | `""` | initial browser state | exact input text; no server filtering |
| `disabled` | `bool` | `False` | reactive configuration | disables activator and input and force-closes an open palette |
| `loop` | `bool` | `True` | reactive configuration | wraps Arrow navigation at first/last enabled visible command |
| `close_on_action` | `bool` | `True` | reactive configuration | root action-close default; command field overrides |
| `size` | `CCommandPaletteSize` | `"md"` | reactive configuration | surface width/density preset |
| `placeholder` | `str` | `"Search commands"` | structural server data | visible input placeholder, not its accessible name |
| `search_label` | `str` | `"Search commands"` | structural server data | nonempty visually hidden input label |
| `empty_label` | `str` | `"No commands found"` | structural server data | visible live empty fallback when slot omitted |
| `close_label` | `str` | `"Close command palette"` | structural server data | nonempty close Button accessible name |
| `class_` | Citry structured class value | `None` | structural server data | merges on native Dialog |
| `style` | Citry structured style value | `None` | structural server data | merges on native Dialog |
| `attrs` | mapping | `None` | structural server data | safe Dialog attributes after owned-destination validation |
| `input_attrs` | mapping | `None` | structural server data | safe search-input attributes after owned/form validation |

Group commands must be nonempty. Separator construction accepts no arguments.
Strings reject U+0000 and forbidden controls. Values, labels, keywords, group
labels, and supplied visible strings must be nonempty after their
field-specific whitespace validation. Description and shortcut text are
escaped, never parsed as HTML or key bindings.

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `open` | Boolean | uncontrolled from committed state | uncontrolled from committed state | constant diagnostic and become uncontrolled | Dialog, focus, scroll lock, activator, `data-open` |
| `query` | string | release to last accepted internal fallback | release to last accepted internal fallback | constant diagnostic and release to that fallback | input text, filtering, active option, empty state |
| `disabled` | Boolean | server value | server value | constant diagnostic and retain last valid | activation and forced close |
| `loop` | Boolean | server value | server value | constant diagnostic and retain last valid | Arrow navigation |
| `closeOnAction` | Boolean | server value | server value | constant diagnostic and retain last valid | action close request |
| `size` | `sm`, `md`, or `lg` | server value | server value | constant diagnostic and retain last valid | layout and mirror |
| `onOpenChange` | function | no callback | clear callback | constant diagnostic and retain last valid callback | user-authored open requests |
| `onQueryChange` | function | no callback | clear callback | constant diagnostic and retain last valid callback | user query requests |
| `onAction` | function | no callback | clear callback | constant diagnostic and retain last valid callback | accepted command activation |

The server snapshot wins before initialization. Valid client inputs take
precedence afterward. Prop removal or `null` releases controlled `open` from
the current committed visibility and controlled `query` from the last accepted
internal fallback, never rejected browser text or the original server default.
An accepted close sets that query fallback empty even if a controlled nonempty
query remains supplied. Configuration prop removal restores the immutable
server value. Mirrors are outputs only.

Nested palettes resolve only their own `$c-props`, host, Dialog, input,
listbox, command records, and callbacks. No client array input can replace
server records.

## 5. State model

Public observable state is `closed | open`, `enabled | disabled`, the exact
query text, `results | empty`, and the internal active option. Active is not a
selected command and is not a public controlled axis.

Filtering derives a separate comparison form without rewriting the input:
NFKC normalization, Unicode whitespace collapse to U+0020, trim, and
locale-neutral lowercase. An empty comparison query matches all commands. A
command matches when the comparison query is a substring of its normalized
label or any normalized keyword. Description, shortcut, value, slot content,
and DOM text are not searched. Matching never reorders commands. There is no
score, fuzzy rank, diacritic folding, token AND/OR language, or result limit.

| From | Trigger and guard | Commit/request | Effects |
|---|---|---|---|
| closed, enabled | owned activator or owner `open=true` | uncontrolled trigger commits; controlled trigger requests | shared Dialog controller enters modal state; input gains focus; current query filters; first enabled visible command becomes active |
| open | user edits input outside composition | uncontrolled query commits; controlled query requests only | uncontrolled: preserve exact input/caret and recompute results; controlled: do not change logical query/filter/active until the owner accepts |
| open | owner changes query | commit supplied value without notification | synchronize input and filter; preserve caret only when the value is unchanged |
| open | Arrow Down/Up outside composition | internal commit | move active to next/previous enabled visible command; optionally wrap; scroll it into view; keep DOM focus in input |
| open | Home/End, Left/Right, editing keys | native | no collection action; browser edits or moves caret |
| open with active | unmodified Enter outside composition | action transaction | prevent ancestor Form submission; call `onAction`; optionally request close after survival recheck |
| open | plain primary option click/tap | action transaction | make that enabled visible option active, call `onAction`, optionally request close |
| open | modified or secondary option pointer/click | none | do not invoke or close; preserve native event behavior |
| open | Escape outside composition | close request | shared Dialog policy; after an accepted close, clear/query-request empty |
| open | built-in close or accepted outside dismissal | close request | shared Dialog policy; after an accepted close, clear/query-request empty |
| open | owner or config sets disabled | forced close | close deepest owned overlay work, release Dialog resources, disable input/activator, notify `reason="disabled"` |
| either | records morph | structural reconcile | preserve open/query/input/focus; retain active value if eligible, otherwise nearest following, then preceding, then first eligible |
| either | no visible command | derived empty | remove active descendant and show empty status; disabled visible commands still count as results |

Repeated requests for the already effective open/query value do not notify.
Disabled commands remain visible and searchable but are never active or
actionable. A group is hidden when none of its commands match. A separator is
visible only between two visible top-level command/group regions and is never
first, last, or adjacent after filtering.

A controlled input event is request-only. The runtime captures the browser's
requested text and selection, invokes `onQueryChange`, then rereads the exact
client prop. Only a synchronously accepted matching string becomes the
effective query and drives filtering. Otherwise, before the listener returns,
the input value, selection when representable, results, active option, empty
state, and action-detail query are restored from the still-supplied effective
query. Removing or nulling control during that callback releases from the last
accepted effective query, never from rejected browser text. An input whose
controlled query is `"a"` and whose attempted `"ab"` request is declined
therefore remains `"a"` on every observable surface and later release.

Uncontrolled action order is exact: validate owner token and option, set the
internal active value, call `onAction(value, detail)` synchronously, revalidate
the same owner/record/open generation, then request close if the effective
command policy is true. Controlled close reports `onOpenChange(false, ...)`
without mutating supplied `open`. Callback return values are ignored. An
exception stops the transaction before close, leaves a structurally valid
palette open, and is reported through the normal browser error path without
logging callback/event/DOM objects.

Query clears only after visibility actually commits closed. At that edge the
runtime first sets its uncontrolled fallback query to `""` and clears active
and `aria-activedescendant`. A nonempty uncontrolled query commits empty and
notifies once with `reason="close"`; a nonempty controlled query requests empty
once and remains supplied until its owner accepts. If that owner retains a
nonempty controlled query, the next open shows the owner value, but later
release while closed starts from the already-cleared fallback. An already
empty query does not notify. A declined controlled close neither clears the
fallback nor requests a query change.

Action-close order depends on open ownership. Uncontrolled order is
`onAction`, close commit, `onOpenChange(false, ...)`, then the close-driven
query commit and `onQueryChange("", ...)`. Controlled order is `onAction`,
`onOpenChange(false, ...)` request, a later matching owner `open=false` commit,
then the close-driven query commit/request. A controlled decline retains
`open=true` and performs no reset. An independent owner-driven `open=false` has
no open callback but still performs the accepted-close query reset. Equal
retained handoff is not a close. Changed-root replacement, removal cleanup,
and invalid initialization emit no callback; a real disabled, native,
descendant-ancestor, or ordinary dismissal close does reset. Each close
generation performs the reset edge at most once.

A controlled close request retains its generation, reason, and source only
until an owner accept/decline can be observed. A matching later `open=false`
commit uses that recorded reason for the close reset. An independent owner
false commit uses `closeReason="owner"`; a containing Dialog teardown uses
`ancestor`. Stale request details cannot label a later close.

Vuetify clears query on opening, which can erase context before an owner knows
whether a workflow should proceed. Mantine 9.5.1 instead defaults
`clearQueryOnClose=true` after close completion. Citry adopts the latter timing:
every completed invocation starts fresh, while an accidental or controlled
declined close preserves the user's current search.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CCommandPalette` | `activator` | no | one | `{activator_attrs: dict[str, object], activator_disabled: bool}` | omitted |
| `CCommandPalette` | `item_start` | no | one renderer reused for commands | `CCommandPaletteItemSlotData` | omitted |
| `CCommandPalette` | `item_end` | no | one renderer reused for commands | `CCommandPaletteItemSlotData` | built-in shortcut text when present |
| `CCommandPalette` | `empty` | no | one | `{}` | escaped `empty_label` |

`activator_attrs` contains `aria-haspopup="dialog"`, `aria-controls`, the
server-visible `aria-expanded`, and a private owner marker. It must be spread
on one standard HTML activator or compatible Citry UI Button.
`activator_disabled` carries the effective Boolean disabled state separately,
so a compatible `CButton` receives it through its owned `disabled` input
without permitting an attribute spread to override Button ownership. A native
Button uses the same Boolean for its `disabled` attribute.

`CCommandPaletteItemSlotData` is an immutable server snapshot with `value`,
`label`, `description`, `keywords`, `shortcut`, `disabled`, effective
`close_on_action: bool`, and `intent`. It does not contain live query, match
positions, active state, DOM objects, or callbacks. One renderer definition is
evaluated once per command in record order. Dynamic slot namespaces do not
apply.

Item renderer output is decoration only. Its wrapper is `inert` and
`aria-hidden="true"`. Detectable links, Buttons, inputs, controls,
contenteditable nodes, positive or negative tabindex, nested images with
meaningful alternative text, autonomous/customized built-ins, open or closed
ShadowRoots, and nested interactive Citry components are rejected server-side
when visible and fail closed if introduced by a morph. The empty slot follows
the same non-interactive rule. Label, description, shortcut semantics, option
identity, and action behavior cannot be replaced.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onOpenChange` | `(requested_open, detail)` | activator, Escape, outside, close Button, action, native close, or disabled transition | after uncontrolled commit; before controlled owner commit except unavoidable native close | supplied `open` remains authoritative | return ignored; retain controlled value to decline ordinary request |
| `onQueryChange` | `(requested_query, detail)` | user input after composition commits or an accepted close clears query | after uncontrolled commit; before controlled owner commit | supplied `query` remains authoritative; rejected text never filters | return ignored; retain controlled value to decline |
| `onAction` | `(value, detail)` | accepted Enter or plain primary click/tap | synchronous before optional close request | independent of controlled query/open; later close is a separate request | return ignored; use disabled or `close_on_action` policy |

`CCommandPaletteOpenChangeDetail` is `{reason, controlled, source}`. `source`
is the owned activator/close/option Element or event origin when available.
Reasons are the `CCommandPaletteOpenReason` values.

`CCommandPaletteQueryChangeDetail` is
`{reason, closeReason, controlled, source}`. Reasons are `input` and `close`.
Input uses `closeReason=null`, occurs only after composition commits, and uses
the owned search input as `source`. Close reset carries the accepted
`CCommandPaletteOpenReason` and uses its owned close/action/event origin when
available, otherwise `null`.

`CCommandPaletteActionDetail` is `{query, source, item, event,
closeOnAction}`. `source` is `keyboard` for the owned Enter path and `click`
for every accepted click-handler path, including pointer, touch,
assistive-technology, and programmatic activation. `item` is the exact owned
option Element; `event` is the triggering browser event and retains native
pointer/trust/detail information. Object fields are ephemeral browser values,
not serializable trusted data.

Native `input`, composition, key, pointer, click, cancel, close, and toggle
events remain native. The family emits no custom DOM event. Owned callbacks do
not fire for owner prop commits, filtered-out rows, disabled rows, secondary
clicks, modified clicks, hostile DOM, stale generations, or cleanup.

No public methods are added. Controlled props, the activator slot, callbacks,
and ordinary DOM refs cover open, close, focus, and action jobs. Direct native
Dialog methods are outside the controlled contract and are reconciled by the
shared Dialog controller.

## 8. Semantics, keyboard, focus, and assistive technology

The root is a native modal Dialog labelled by the required visible heading.
The owned `<search>` contains a visually hidden native label and one
`type="text"` input with `role="combobox"`, `aria-autocomplete="list"`,
`aria-controls` for the listbox, and `aria-expanded` matching the open result
surface. DOM focus remains in the input during command navigation.
`aria-activedescendant` names exactly one connected, visible, enabled option or
is absent. The active option has `aria-selected="true"`; all other visible
options use false. This selection is transient focus, not an application
value. The input is `type="text"`, not `search`: native search-clear and Escape
behavior diverges across the supported engines and would compete with the
owned query and Dialog-dismissal contract. The enclosing `<search>` still
provides the correct landmark for filtering commands.

Each group uses `role="group"` and `aria-labelledby` pointing to visible group
text. Each command uses `role="option"`, an owned label, and optional owned
description. Shortcut and visual slots are accessibility-hidden. Separators
are visual `<hr aria-hidden="true">` nodes with no accessibility role or node;
the listbox accessibility tree therefore owns only options and labelled groups.
The empty result is a concise `role="status"` message outside the listbox.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| closed | activate owned activator | request open | search input when committed | native Button activation continues |
| open input, not composing | Arrow Down/Up | move active among enabled visible commands | remains in input | yes |
| open input, not composing | Home/End | native caret movement | remains in input | no |
| open input, not composing | Enter with active | action transaction | remains until action/close policy settles | yes |
| open input, not composing | Enter without active | no action | remains in input | yes, to contain Form submission |
| open input, composing | Arrow keys | IME/native editing only | remains in input | no |
| open input, composing | Enter | commit composition, never act; arm exact Form-submit guard | remains in input | no key cancellation; only a correlated submit is canceled |
| open input, composing | Escape | IME cancellation only | remains in input | no key cancellation; shared Dialog cancel is blocked for that generation |
| open | Tab / Shift+Tab | shared Dialog traversal and wrap | input, close Button, or another owned tabbable | only at containment edge |
| open | plain primary option press/click | activate option | input is restored before action callback | pointerdown as needed to retain input focus; click only when acted |
| open | modified/secondary click | no action | unchanged | no |
| open | Escape outside composition | request close | shared Dialog restoration after commit | yes |
| open | outside pointer sequence | request close when allowed | shared Dialog restoration after commit | yes when committed |

The input owns visible focus indication even when active-descendant navigation
changes the row. Pointer hover may update active without moving DOM focus.
Disabled options remain exposed with `aria-disabled="true"` but cannot become
active. When a query removes the current active option, the next eligible
option is selected without announcing a selected application value.

Composition ownership is generation-bound. `compositionstart` arms the local
latch; every key handler treats the latch, `event.isComposing`, or legacy
`keyCode === 229` as composing. While true, Arrow, Enter, and Escape never
navigate, act, close, or intentionally cancel the key. `escapeBlocked()` also
prevents a native Dialog `cancel` from becoming a palette close. A composing
Enter arms the temporary Form guard defined in section 9. `compositionend`
queues one settlement after any trailing noncomposing `input`; that task emits
at most one query request for the final text. A later generation, blur, close,
morph replacement, or cleanup cancels stale settlement and the Form guard.

The recorded synthetic state-machine sequence was identical in repository
Chromium 151, Firefox 153, and WebKit 26.5:
`compositionstart`, `compositionupdate`, composing `beforeinput`, composing
`input`, composing Enter `keydown`, `compositionend`, then a final
noncomposing `input`. Synthetic dispatch proves state/duplicate handling but
not OS IME commit behavior, so manual real-IME testing in all three engines
remains release-blocking.

The Dialog controller captures deep active focus before opening. On ordinary
Escape, outside, close-button, or action close, it restores the eligible
invoker. If `onAction` deliberately focuses a different connected eligible
Element, that owner move wins and shared restoration must not overwrite it.
If a controlled owner declines closure, an owner focus move to an eligible
Element inside the still-modal Dialog remains; a move outside cannot survive
native modality and the controller restores the search input next task. If the
callback removes the palette before moving focus, normal cleanup permits that
connected outside destination and does not restore the old invoker. Removal
cannot leave focus in an inert or disconnected tree.

Automated accessibility trees in Chromium, Firefox, and WebKit must show a
Dialog, editable combobox, listbox, groups, and options, with no false link or
Button role. Manual VoiceOver/Safari and NVDA/Firefox testing must verify title
announcement, search editing, active-option announcements, descriptions,
disabled state, empty result, group boundaries, action, dismissal, and return
focus. Native-link semantics are intentionally outside this pattern.

## 9. Native forms and validation

`CCommandPalette` contributes no form value or validity. The search input has
no `name`, explicit `form`, submitted value, required state, reset contract,
autocomplete history, or submitter role. A native text input is nevertheless
associated with an ancestor Form for implicit submission. `input_attrs`
rejects `name`, `form`, `required`, `list`, form-action attributes, and dynamic
writes to them.

Server output renders the search input disabled. This prevents a visible
server-open palette from submitting an ancestor Form before activation. A
valid enabled runtime removes that exact owned disabled state. While the
palette is active, every non-composition Enter in the search input is contained
whether or not a command is active: `keydown.preventDefault()` runs before
eligibility or action. Repository probes observed Enter `keydown`,
`beforeinput(insertLineBreak)`, then `submit` in Chromium/Firefox and Enter
`keydown` then `submit` in WebKit; preventing the keydown removed later input
and submission in all three.

A composing Enter is not canceled because doing so can break native IME
commit. Instead the input installs one generation-owned capture listener on
its exact current ancestor Form before returning from that keydown. Until the
final noncomposing input or next task, it prevents only a submit received by
that Form while deep focus is this palette input and the same composition
guard owns it. The listener is removed on settlement, blur, close, root-scope
change, or cleanup. This preserves native composition while preventing the
correlated implicit submission; real OS IME behavior is manually verified.

The component never constructs a nested Form, intercepts a submit outside that
bounded composition correlation, calls `requestSubmit()`, or changes an
application Form's data. Citry
Events validation, transport, errors, retries, and cancellation remain
application-owned. An action callback may submit a Form explicitly as normal
application code.

No visual renderer slot may contain a form control. The activator slot may use
an ordinary `type="button"` Button and must not use a submit Button unless the
application intentionally wants activation to submit its Form independently.

## 10. Styling and theme contract

The family follows [`../ui_theme.md`](../ui_theme.md). `size` changes Dialog
width, spacing, and row density together. `intent="danger"` affects command
text/accent only; it does not bypass disabled, action, or close semantics.

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-command-palette-backdrop` | color | modal backdrop | theme overlay color |
| `--cui-command-palette-background` | color | surface background | theme surface color |
| `--cui-command-palette-foreground` | color | primary text | theme foreground |
| `--cui-command-palette-muted` | color | descriptions and shortcut text | theme muted foreground |
| `--cui-command-palette-border-color` | color | surface/input/row boundaries | theme border color |
| `--cui-command-palette-active-background` | color | active option background | theme subtle accent |
| `--cui-command-palette-active-foreground` | color | active option text | theme accent foreground |
| `--cui-command-palette-danger` | color | danger-intent text | theme danger color |
| `--cui-command-palette-radius` | length | Dialog surface radius | `0.875rem` |
| `--cui-command-palette-shadow` | shadow | Dialog elevation | theme overlay shadow |
| `--cui-command-palette-inline-size` | length | preferred Dialog width | size-specific |
| `--cui-command-palette-max-block-size` | length | viewport-constrained height | `calc(100dvb - 2rem)` |
| `--cui-command-palette-padding` | length | outer surface inset | `0.75rem` |
| `--cui-command-palette-gap` | length | region gap | `0.5rem` |
| `--cui-command-palette-input-block-size` | length | search control size | size-specific |
| `--cui-command-palette-row-min-block-size` | length | command touch/reading size | size-specific, at least `2.75rem` |
| `--cui-command-palette-row-padding-inline` | length | row horizontal inset | `0.75rem` |
| `--cui-command-palette-group-gap` | length | group spacing | `0.5rem` |
| `--cui-command-palette-focus-ring` | color | visible keyboard focus | theme focus color |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="command-palette"]` | native Dialog and attrs destination | open, disabled, size, empty | owns surface |
| `[data-citry-ui-part="command-palette-surface"]` | visual surface | all | fills Dialog |
| `[data-citry-ui-part="command-palette-header"]` | title/close layout | all | first surface region |
| `[data-citry-ui-part="command-palette-title"]` | visible accessible title | all | labels Dialog |
| `[data-citry-ui-part="command-palette-close"]` | built-in close Button | enabled and open | inside header |
| `[data-citry-ui-part="command-palette-search"]` | search landmark | all | contains label/input |
| `[data-citry-ui-part="command-palette-search-label"]` | visually hidden native label | all | names input |
| `[data-citry-ui-part="command-palette-input"]` | search combobox | all | controls listbox |
| `[data-citry-ui-part="command-palette-listbox"]` | filtered result collection | all | owns options/groups |
| `[data-citry-ui-part="command-palette-command"]` | one option row | active, disabled, intent | globally unique value identity |
| `[data-citry-ui-part="command-palette-group"]` | labelled option group | visible | contains group label and commands |
| `[data-citry-ui-part="command-palette-group-label"]` | visible group name | visible group | labels group |
| `[data-citry-ui-part="command-palette-separator"]` | visual boundary | between visible regions | accessibility-hidden |
| `[data-citry-ui-part="command-palette-empty"]` | empty status | no visible commands | sibling of listbox |
| `[data-citry-ui-part="command-palette-item-start"]` | inert leading decoration | slot supplied | inside command |
| `[data-citry-ui-part="command-palette-item-end"]` | inert trailing decoration or shortcut | slot/shortcut supplied | inside command |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| `data-open` | present or absent | effective native Dialog open state |
| `data-disabled` | present or absent | effective palette disabled state |
| `data-size` | `sm`, `md`, `lg` | effective size |
| `data-empty` | present or absent | current filter has no visible commands |
| command `data-active` | present or absent | internal active descendant |
| command `data-disabled` | present or absent | immutable command disabled state |
| command `data-intent` | `default`, `danger` | immutable visual intent |

Query text is not reflected to an attribute. Values may be exposed only on the
owned option identity destination documented by the API; they are never
included in diagnostics. Public variables inherit and resolve through private
effective variables. Defaults use low-specificity Citry UI layer rules.

## 11. Environmental behavior

Light and dark themes provide legible surface, input, options, active state,
disabled state, border, backdrop, and focus. A nested opposite color-scheme
scope remains effective because the native Dialog stays in authored ancestry
when it enters the top layer.

All layout uses logical properties. RTL reverses start/end decoration layout
but not Arrow Up/Down order. Long labels, descriptions, group names, and
shortcut hints wrap or truncate only at documented visual boundaries without
removing accessible text. At 200% and 400% zoom, the title, input, results,
empty state, and close Button remain reachable. Text-spacing overrides do not
clip rows.

Narrow/coarse-pointer layouts preserve a `44px` minimum actionable row and
close target. The Dialog max block size uses dynamic viewport units so a
virtual keyboard leaves the input visible and results independently
scrollable. Wide screens retain the size cap. Reduced motion removes optional
surface/row transitions without changing focus or settlement. Forced colors
preserve Dialog boundary, input boundary, active indication, disabled text,
and focus ring without color-only differentiation. Reduced-data preferences
have no effect because the family fetches nothing.

The modal palette and its empty/result content are hidden in print. An
activator remains ordinary consumer content unless the application hides it.

Library-authored visible strings are `Search commands`, `No commands found`,
and `Close command palette`. They are server inputs now; locale selection and
translation remain separate work.

## 12. Overlay and layering behavior

The palette uses the same private Dialog controller as `CDialog`. The native
Dialog stays in its authored Document or open ShadowRoot and enters the browser
top layer with `showModal()`. The shared controller, not CommandPalette code,
owns modality, focus trap, outside start/end matching, Escape, nested Dialog
ownership, descendant overlay closure, scroll-lock reference counting,
return-focus fallback, and teardown.

The controller accepts an owned `initialFocus()` resolver and an
`escapeBlocked()` guard. CommandPalette supplies the exact connected enabled
input and the current composition predicate. On every fresh committed open,
the controller runs native `showModal()`, then focuses the resolved input with
`preventScroll` when native autofocus did not already do so, and verifies deep
active focus before returning. `CDialog` maps its existing `auto`/`title`
policy to the same option without changing its public behavior. No caller may
provide a selector or arbitrary focus callback.

Opening closes incompatible anchored layers through the existing shared layer
coordination path before claiming modality. Anchored overlays opened from
inside the palette are descendants and close before the palette. A nested
native Dialog may open only through the shared controller and becomes the
topmost focus owner. Events from a nested Dialog or nested palette do not act
on an ancestor palette.

The palette adds no portal, teleport, z-index manager, anchor positioning, or
body relocation. Authored color-scheme and CSS-variable ancestry therefore
remain intact. One scroll-lock claim exists per open modal controller and the
last close restores exact authored document-root inline styles.

The shared controller must work from `ownerDocument`, the actual Document or
open ShadowRoot, composed paths, and deep active focus. Adoption into another
Document and closed ShadowRoots fail closed. Moving a retained root between its
Document and an open ShadowRoot closes the old top-layer registration before a
fresh activation; it is not an open handoff.

## 13. Collections, async data, and identity

Command `value` is the sole application identity and must be globally unique
across top-level commands and groups. Group labels and positions are not
command identity. Order is exactly the flattened server record order. Group
and separator normalization never changes relative command order.

Records are copied to immutable tuples at render time. Mutable caller lists,
dictionaries, keyword lists, or later record-container mutation cannot change
rendered output. Record values are compared structurally for server rendering
and morph fingerprints. Generated DOM keys derive from the component identity
and a safe digest of command value, never from raw text.

The internal collection primitive is an active-descendant manager extracted
from the current Combobox foundation. It owns exact option registration,
eligible navigation, active identity, scroll-into-view, composed containment,
and owner-token cleanup. Search canonicalization is one shared text helper.
CommandPalette adds action/filter/group policy but does not copy Listbox roving
focus, Combobox value selection, Menu focus/layer code, or Dialog behavior.
`CCombobox` must consume the extracted active-descendant foundation without
behavior or asset regression before CommandPalette claims reuse.

All data is server-owned. There is no remote fetch callback, promise input,
loading state, stale-result protocol, retry UI, pagination, virtualization,
history, nested page stack, or client command registry. Applications may
server-morph `entries`, but the component does not fetch or merge them. A
500-command acceptance ceiling covers the v1 local collection; larger dynamic
datasets require a separately designed virtualized or remote family.

## 14. Server render, morph, and cleanup

Closed server output contains the complete native Dialog, title, disabled
search input, listbox semantics, commands, descriptions, groups, and visual
separators. Open server output is visible but non-modal and remains readable;
it has no authored `aria-modal` claim and does not make background content
inert. Commands are not executable without JavaScript. Activation validates exact
owned anatomy and records, installs the shared controllers, removes only the
owned server-disabled input state, reconciles server open/query, and publishes
readiness atomically.

The private host, Dialog, surface, input, listbox, groups, options, and visual
slot wrappers have exact owner identities. A copied readiness marker is never
proof of ownership. Activation rejects duplicate/missing/unknown direct parts,
wrong roots, custom or replaced semantic elements, uncorrelated framework
markers, interactive renderer content, and cross-Document anatomy while
leaving useful server fallback unchanged.

Same-owner repeated initialization does nothing. A retained equal-record morph
preserves Dialog/input/listbox identities, uncontrolled open/query, input
selection, composition generation, active value, scroll position, focus,
callback ownership, and one set of resources. Framework correlation marker
rotation is validated separately from the immutable authored record digest.
Allowed class/style/test-data changes update their repairable baselines without
resetting collection state.

The extracted Dialog controller carries a correlated owner/handoff token that
binds the private host, native Dialog, surface, title, close Button, actual
Document/open-ShadowRoot, committed open generation, focus snapshot, nested
layer ownership, scroll-lock claim, and the initial-focus policy plus exact
resolved input/title target identity. Old cleanup may detach its listeners and
registration without closing DOM already accepted by an equal new owner; it
cannot delete the new owner, duplicate a scroll claim, run initial focus twice,
or overwrite a later focus snapshot. An unequal focus target/policy, missing,
invalid, or unconsumed provisional handoff closes the old native Dialog and
descendants synchronously before new initialization. Focused `CDialog`
equal/changed/replaced morph gates must pass on the same helper bytes.

A retained changed-record morph preserves open/query/input focus and reconciles
commands by value. The old active value survives only when still visible and
enabled; otherwise the nearest eligible declaration neighbor wins. Removed,
reordered, relabelled, disabled, regrouped, and keyword-changed commands do not
emit query/action/open callbacks. A newly empty collection removes active
descendant and exposes the empty status. A replaced root performs full cleanup
and starts from new server/client inputs.

An active composition token prevents a morph from dispatching a command. If
the retained input is replaced or the owner becomes invalid during composition,
the composition is canceled, no query/action callback is fabricated, and the
palette fails closed or reinitializes from the new valid server tree. Old
owner cleanup deletes registrations/listeners only when their token still owns
them.

Cleanup closes descendant overlays then the native Dialog, removes readiness
and public mirrors, releases scroll lock, restores eligible focus under the
shared Dialog policy, detaches delegated listeners, clears scheduled work and
composition/action generations, and unregisters collection entries. Removal is
silent and leaves no top-layer Dialog, disabled background, global listener,
observer, timer, stale active descendant, or callback. Clone readiness is
scrubbed only while a live shared root-scope manager exists, and the final
registration disconnects that manager.

## 15. Security and content trust

Label, description, keyword, shortcut, group, title, placeholder, empty, and
close text is escaped plain text. None accepts raw HTML. Values are opaque
application identifiers; they are validated for nonempty/control-safe text but
are not authorized by the component. `onAction` is trusted application code
and must still authorize the requested domain operation.

Visual renderer slots accept ordinary trusted Citry composition but are
wrapped inert and accessibility-hidden. Detectable interactive/focusable/form
content, custom elements, ShadowRoots, nested semantic command/image/link
owners, raw HTML sinks, and runtime-owned markers are rejected. There is no URL
or `href` input, script evaluation, router integration, command deserialization,
remote registry, or `innerHTML` path.

`attrs` and `input_attrs` use destination-specific allowlists plus owned,
directive, raw-event, dynamic-destination, ARIA, form, identity, and framework
marker rejection. Client hostile changes to owned roles, relationships,
disabled state, input value, IDs, record values, Dialog capability, or exact
anatomy fail closed. Allowed class/style changes preserve consumer bytes while
owned variables/reflections are repaired idempotently.

Diagnostics are constant, category-only messages. They never stringify or log
query, label, keyword, value, shortcut, callback, event, DOM Element, Error,
record object, attrs mapping, or framework payload. A malicious `toString`,
getter, proxy, or event object is never consulted to construct a diagnostic.

Synthetic DOM events are not an authority boundary. A programmatic plain
`.click()` on an exact owned enabled option may invoke the trusted application
callback just as an application could call it directly. Disabled, stale,
filtered, modified, secondary, cross-owner, and disconnected events do not.

## 16. Assets and performance

The implementation extracts one private Dialog controller consumed by both
`CDialog` and `CCommandPalette`, and one private active-descendant collection
foundation consumed by both `CCombobox` and `CCommandPalette`. It adds one
CommandPalette initializer and one CSS frame. It adds no icon font, image,
network request, worker, global shortcut listener, polling loop, per-command
listener, or async registry.

Immutable pre-Command baselines are:

| Foundation | Source SHA-256 | Emitted frame SHA-256 | Raw | Gzip | Brotli |
|---|---|---|---:|---:|---:|
| Dialog source | `58678782ef912ba4701890b6447106211ea3add1cc67ddbceb538d30b7663ddd` | JavaScript `17b49a6cc706860b32316c42c6d4822e1d85f245e508e9af07995933d2ca50db` | 17,870 | 4,327 | 3,723 |
| Dialog CSS | same source | `606c850bc1579e5fec93634659fb286521fcff0c75469682cdb86f20833b15fa` | 4,533 | 1,122 | 948 |
| Combobox source | `0e7d61f545075e6513c91c366a73009e1235780d103000b734157c3282fb9cea` | JavaScript `f1d24c5827e40c9990542b61375ab8aaa880b0703818bca1506df8cf760f078e` | 38,243 | 7,596 | 6,648 |
| Combobox CSS | same source | `60294c2d6a6575b3dc847e0b58bf8951fd42fabddd41b022aac28f07c461e86f` | 7,059 | 1,416 | 1,197 |

Final accounting records readable source, every uniquely registered/emitted
frame, and an optional reproducible Terser diagnostic. Acceptance gives no
Terser credit.

For each asset kind, a frame set is the ordered dependency payloads returned by
a fresh `Citry.register_library` installation. Exact duplicate payload bytes
are removed while preserving first topological dependency/emission order.
`M(payloads)` concatenates those remaining payload bytes with no inserted
delimiter, then reports raw length, deterministic
`gzip.compress(..., mtime=0)`, and default Brotli length. Compression is over
that canonical concatenation, never the sum of independently compressed frame
sizes. Individual frame hashes and sizes remain provenance evidence.

Incremental accounting uses stable logical attribution, not aggregate
subtraction. Production source marks every CommandPalette-specific initializer
and every CommandPalette-motivated addition inside the shared Dialog or
active-descendant helpers with unique reviewed begin/end anchors. Extraction
of behavior already present in frozen Dialog/Combobox bytes is baseline
foundation work; any new branch, option, guard, callback, or data field needed
for CommandPalette is CommandPalette-attributed even when another component
also consumes it later.

Let `P` be the exact ordered marker-bounded emitted bytes for all such
CommandPalette-attributed JavaScript or CSS, deduplicated by content. The
release report records each enclosing emitted frame hash, marker pair, slice
hash, raw/gzip/Brotli sizes, and their canonical `M(P)`. Moving an unchanged
slice between the CommandPalette initializer and a separately emitted shared
dependency leaves `P` byte-identical.

For every final shared Dialog/Combobox logical frame, the report removes the
`P` slices and compares the remaining anchored logical frame with its frozen
pre-Command counterpart. New non-`P` shared frames have a zero-byte baseline;
changed frames contribute `max(0, post - pre)` independently for raw, gzip,
and Brotli; removed/shrunk frames contribute zero and cannot offset another
frame. The strict incremental charge is `M(P)` plus every positive shared
logical-frame delta. CSS uses the same algorithm. A source/parser test fails if
markers overlap, are missing/duplicated, move bytes across ownership without a
provenance update, or do not reconstruct the exact emitted frames.

The standalone set is a fresh page registering only CommandPalette plus every
required private dependency and uses `M` over all unique full emitted frames.
It independently prevents logical attribution from hiding shipped helper cost.

Strict binary ceilings are:

| Charge | Raw | Gzip | Brotli |
|---|---:|---:|---:|
| Attributed JavaScript `P` plus all positive shared logical-frame deltas | `< 65,536` | `< 13,312` | `< 11,264` |
| Complete unique JavaScript reachable from a page using only CommandPalette | `< 114,688` | `< 20,480` | `< 17,408` |
| Attributed CSS `P` plus all positive shared logical-frame deltas | `< 10,240` | `< 2,304` | `< 2,048` |

The correctness-frozen readable CommandPalette JavaScript is 44,313 raw /
8,227 gzip / 7,217 Brotli bytes, SHA-256
`8ba0eba3a70430a2a9847c782dbe1c78b846317db9711d76ef7d95ed3021be00`.
Its registered initializer frame is 38,165 / 8,071 / 7,074 bytes,
SHA-256
`9e212dd9eba9c5d9439d0c273c4dd8e1db6c993d8c0757384c9de5e62744f185`.
The readable CSS is 11,440 / 1,797 / 1,539 bytes, SHA-256
`db5eb273fc0b0639c4a033031e235f581fc33d8b6a7339b6625db4360d4cbab4`;
the registered CSS frame is 9,714 / 1,760 / 1,523 bytes, SHA-256
`b969aee04a8dda0f9bb3f8d067375de3fa10093948fc706afa3494ad82bde0c8`.

The exact marker blocks in topological frame order are:

| Marker | Slice SHA-256 | Raw | Gzip | Brotli |
|---|---|---:|---:|---:|
| `initializer` | `8798500a6daf09ef5c6ea2ae12128b504e69009c94b9d2d6ef799f84b969c731` | 38,163 | 8,069 | 7,076 |
| `dialog-layer-preparation` | `f546714412b15bc9bc03e1e0cfbab623fac4ba6a66eb0a339c01cb146842257a` | 850 | 385 | 308 |
| `dialog-document-lock-state` | `8915078664595b1831407306a06a7d63289feebea10913963ccadbbc6c9d29e7` | 194 | 129 | 102 |
| `dialog-handoff-keys` | `e5090b2285cfa12fbdadc9183773931a0f57d222e35ce5dd9829b287a951ae69` | 281 | 151 | 129 |
| `dialog-root-scope-state` | `700056c404db3d445f6735e2f71ddeb80e171c08e9b8b8d60123a99c4c250c32` | 713 | 319 | 266 |
| `dialog-document-lock` | `4fd95ef4939f6bdc566aea6560f4ebcb4f297bce2aa1eec4c8e9b8992dcc7688` | 1,585 | 534 | 435 |
| `dialog-root-scope-manager` | `a24c21d8b734380631e49a34109b26425753ca2b2c0de2ebef979b6329ca1bd5` | 911 | 379 | 316 |
| `dialog-handoff-close-state` | `45f7dde61337c29f0b9eef6ee7516cd82a83001433505a95c57cd86185b983dd` | 261 | 140 | 112 |
| `dialog-focus-target` | `a4ef28977e3749ef7727212a171da2be377ca0527c2b3b0e2fc66fe57875aea5` | 200 | 133 | 108 |
| `dialog-handoff-consume` | `e0d47db9ecf279fc9534220079fb12db7952cf3c5f981557fbc74639fd901e08` | 1,450 | 465 | 392 |
| `dialog-focus-hooks` | `570fc52b3affaccca3e3f7fdd6470ab6b4a6220fd30b3775fcbe815bc11aa719` | 494 | 265 | 214 |
| `dialog-focus-restore` | `127f781c297f64eae55687bd40fb9610255183a6267701e13e814715f66b1145` | 832 | 345 | 277 |
| `dialog-handoff-close-intent` | `0968552314616b9e895f435df9b0cd251b2b3848d82e9929a0c34e509480704e` | 297 | 188 | 155 |
| `dialog-handoff-close-expected` | `f05963be04725f9600eded70df5a0e2deb60490430c98a98f6480b0d4df3bbf6` | 203 | 127 | 100 |
| `dialog-handoff-close-reclaim` | `b03bdc2b5c1ea068e26b8f017f7eb55ebd726017288a84b377da600f14e034ae` | 610 | 273 | 215 |
| `dialog-handoff-close-retire` | `91438cfb95a7036687bbd5bf10a8198d56cb66db93eddbd9ec1ba9baf240294a` | 195 | 124 | 97 |
| `dialog-root-scope-refresh` | `c179e45501c20cd2170f2fd655c79f63dd541624cd1845e2ade7bff81c76bfbb` | 1,120 | 395 | 333 |
| `dialog-handoff-close-listener` | `b7af13d89b1be1e8fe6e914b7b720e1bd6a69fe12aef7eafd5a8af81ef061425` | 224 | 144 | 116 |
| `dialog-handoff-close-cleanup` | `f9946ec657223c5c69751fcaa20c38141af57e91d0a578a3375b5fbcacfc1125` | 332 | 170 | 149 |
| `dialog-handoff-close-unlisten` | `f9e8f61c38e1f55f024e42775dfb69c6013373d4823f8e2c56f554a162835a2e` | 231 | 148 | 121 |
| `dialog-handoff-produce` | `8dd79fa974a41e758f4cf2a75d8eda2c24156a500e7c2f87074bd6fdf28ac4d1` | 1,153 | 441 | 367 |
| `dialog-handoff-abort` | `7cd757fca5f55f135041a6beac3fa0d1c067bb318fce616183562b436cc1fc7f` | 441 | 227 | 189 |
| `active-owner-key` | `63e82480940b1925753a78ded09ea21b73d6c31eac81732d2c1eb4ed48c511fa` | 202 | 138 | 114 |
| `active-owner-transfer` | `870ff916fed2f2d1f3799711f185b6e64c58657f27eb0a54de76ee980ad8e0dd` | 888 | 362 | 319 |
| `active-neighbor-handoff` | `e4e2bfe18026764575219524edcf7de05e7df2e18acb1b2e40be56c5562aad6b` | 968 | 379 | 317 |
| `active-group-registration` | `dd91e18fbd56fb6b393d3c69780c499defa5969062514fe14ecba7d592985d5d` | 377 | 198 | 159 |
| `active-owner-cleanup` | `5b40c7c87725629103816ac29dac224128dd8a8f5deffb989b5c113a0c8bd874` | 318 | 181 | 141 |

Canonical `M(P)` is 53,493 raw / 10,685 gzip / 9,208 Brotli
bytes, SHA-256
`62630986d4f4dd0e8613b77abc90a213194fc3dfb32b80ae4035dc83d15f2305`.
The CSS marker block is 9,712 / 1,760 / 1,508 bytes, SHA-256
`cb33b3d988f130cbf726d72ba8fbd1428a0d5d22cb069283daa054bc92f6a076`.

Removing those complete marker blocks and comparing each remaining logical
foundation independently produces these conservative positive deltas:

| Logical foundation | Current logical SHA-256 | Current raw/gzip/Brotli | Positive raw/gzip/Brotli delta |
|---|---|---:|---:|
| Dialog adapter plus extracted controller | `5ea7c89e58a908b74d897061f7b60170cedfb6ff87322ecd0a10234701440c05` | 21,442 / 4,899 / 4,273 | 3,572 / 572 / 550 |
| Anchored-layer foundation | `b4f93fb285d6bfe031fa04dffd2ef9b1b03436ed3b5cbb45eb80a1f46fafe909` | 29,545 / 5,608 / 4,884 | 11 / 1 / 2 |
| Combobox adapter plus extracted active-descendant controller | `9841c493487ced24be5622bca4c5d9b0aefa4c41fa08ac8463fd8238373474b3` | 41,116 / 8,497 / 7,367 | 2,873 / 901 / 719 |

The total positive shared JavaScript delta is therefore 6,456 raw / 1,474
gzip / 1,271 Brotli bytes. There is no positive shared CSS delta. The strict
attributed JavaScript charge is 59,949 / 12,159 / 10,479 bytes, leaving 5,587
/ 1,153 / 785 bytes, or 8.53% / 8.66% / 6.97% of each round ceiling,
for maintenance. CSS leaves 528 / 544 / 540 bytes.

The standalone installation emits exactly four unique JavaScript frames:

| Frame | SHA-256 | Raw | Gzip | Brotli |
|---|---|---:|---:|---:|
| CommandPalette initializer | `9e212dd9eba9c5d9439d0c273c4dd8e1db6c993d8c0757384c9de5e62744f185` | 38,165 | 8,071 | 7,074 |
| Anchored-layer runtime | `fa492f777a1752e9b6671f69d92bc3aa4983ee68f7bdfda489388f5b85fa2469` | 30,395 | 5,712 | 4,977 |
| Dialog controller | `066105ceba93c5a425b798e3f1ebf6606a0784ad79f89537e9c4c86a60737789` | 22,763 | 4,750 | 4,146 |
| Active-descendant controller | `f6eb4fbff815f87208ec3690db4546ef800673b27ef689c2551a795f9dced8b7` | 6,876 | 1,892 | 1,625 |

Their delimiter-free canonical payload is 98,199 raw / 18,754 gzip / 15,948
Brotli bytes, SHA-256
`3e87497507aef85e3ff4b8f7d726283f734356f856f72f5a0ab1335a81150831`,
leaving 16,489 / 1,726 / 1,460 bytes below the standalone ceilings.

The correctness freeze binds source hashes
`5072eb399bbfacb657893bcc56e5c8a15f9c21ab9841735e2a7f9a59f46acc97`
for Dialog,
`7fc12967908a6789a8f3c1f24718a759b8e792e994b80a1b9e96a8cab190e0be`
for Combobox,
`5439f917d4918c8926ee82f0a33056ae58d4f2a0b2c7bd903308df37b9c157c3`
for the Dialog controller,
`041544b5de5f5d59bc8ca8d5910516347f27c2e2591a48aca7c7f27d409766c6`
for the active-descendant controller, and
`7a27e4491359af9a4f916726e1423d1fd846fe55e9be24063748c2d8798f9694`
for anchored layers. Their current emitted adapter/helper frame identities are
`f5f69bbf2754d1b1230dec38bc055eeb4ed9ed9a40c94b2823c8a872a557a107`,
`97e56b416a5d33b31fc5c0297b7517c4fd4d5fa21336b77a91c552aec3860395`,
`066105ceba93c5a425b798e3f1ebf6606a0784ad79f89537e9c4c86a60737789`,
`f6eb4fbff815f87208ec3690db4546ef800673b27ef689c2551a795f9dced8b7`,
and `fa492f777a1752e9b6671f69d92bc3aa4983ee68f7bdfda489388f5b85fa2469`
respectively.

The former 32 KiB / 8 KiB / 7 KiB attributed and 48 KiB / 11 KiB / 10 KiB
standalone assumptions were falsified by the behavior-complete extraction and
runtime: per-root open ShadowRoot ownership, correlated handoff and stale
cleanup, callback-moved focus, pre-modal anchored-layer ordering, nested-group
active registration, controlled decline timing, IME/Form guards, hostile
anatomy validation, and privacy-safe diagnostics are required behavior. As a
reproducible lower-bound diagnostic, Terser 5.50.0 over the complete emitted
standalone payload with
`--compress passes=3,pure_getters=true,unsafe=true --mangle --ecma 2022`
produces 37,361 raw / 11,896 gzip / 10,697 Brotli bytes, SHA-256
`99746809e8bb7cf1d7d31b9b91c36e07526f2f02c2eed531fe2533382a5121b3`.
Even that non-emitted aggressive transform exceeds both former standalone
compressed ceilings. It receives no budget credit, and no behavior, trust,
diagnostic, readiness, or cleanup contract is removed for size.

One instance has bounded delegated input/listbox/Dialog listeners. Collection
rows have no listeners. Root-scope mutation/clone management is shared among
affected instances and disconnects after the last cleanup. Dialog scroll lock
is shared and reference-counted. No work runs while every palette is closed
except bounded owner/morph registration.

The scaling gate measures 1, 10, and 100 closed/open instances and 10, 100,
and 500 commands in one instance. Resource counts scale by instances, not
commands; filtering 500 commands completes in one synchronous task without a
long task over 50 ms on the project Chromium baseline; active navigation does
not scan hidden DOM repeatedly; cleanup returns listeners, observers, timers,
Dialog claims, and collection registrations to zero.

## 17. Acceptance matrix

Automated release evidence must include:

- schema, typing, frozen-record copying, all aliases/exports, template and
  direct Python rendering, generated IDs, group/value/separator validation,
  attrs destinations, all reserved/directive/form rejections, and constant
  privacy-safe diagnostics;
- exact native Dialog/search/combobox/listbox/group/option/empty anatomy,
  input-owned active descendant, no false link/Button semantics, descriptive
  relationships, disabled exposure, public mirrors, parts, variables, and the
  exact documented `CButton` activator composition with separately owned
  `activator_disabled` state;
- local NFKC/whitespace/lowercase substring matching, label/keyword-only
  search, stable order, group/separator visibility, disabled skip, empty/all
  disabled states, looping, scroll-into-view, and no ranking drift;
- uncontrolled and controlled open/query, release with omitted/null props,
  invalid-value retention, repeated requests, close decline, disabled forced
  close, accepted-close query reset, owner prop commits without callback, and nested
  instance isolation; the exact controlled `"a"` to rejected `"ab"` request
  keeps input/results/active/action detail/release at `"a"`;
- exact keyboard/pointer ledger: arrows, noncollection editing keys, Enter with
  and without active option, modified/secondary click, touch, disabled rows,
  Tab containment, Escape, outside start/end, close Button, action once, and
  truthful `keyboard` versus click-without-pointer callback source;
- C/F/W IME composition for Latin and a real composition sequence, including
  Arrow/Enter/Escape suppression, committed query callback order, no duplicate
  action, no ancestor Form submit, exact 229/latch ownership, final-input
  dedupe, and temporary Form-listener removal;
- native Form falsifiers with implicit submit, multiple submitters, disabled
  server fallback, activation, nested app Dialog, and explicit callback-owned
  submission;
- action callback order, per-command/root close policy, controlled close,
  callback removal/reentrancy/exception, stale click, action-generation
  supersession, owner-moved focus, and one callback under repeated events;
- shared Dialog controller evidence for focus entry/trap/return, nested Dialogs,
  anchored descendants, scroll lock, same-pointer outside matching, native
  close, ShadowRoot, hostile capability loss, reduced motion, and cleanup,
  alongside unchanged focused `CDialog` gates; fresh/reopen/handoff paths focus
  the exact CommandPalette input once through the correlated resolver;
- shared active-descendant helper evidence alongside unchanged focused
  `CCombobox` gates; `CListbox` and `CMenu` focused gates guard accidental
  canonicalization/navigation drift;
- retained equal/changed record morphs while closed/open/focused/composing,
  generated marker rotation, active removal/reorder/disable, query filtering,
  input selection, replacement, invalid anatomy, Document/open-ShadowRoot
  move, cross-Document adoption, remove/restore, late stale work, and final
  resource zero;
- visual renderer server/runtime interaction rejection, escaped text, hostile
  roles/ARIA/IDs/value/disabled/markers, uncorrelated clone readiness, no
  consumer-value diagnostic disclosure, CSP without unsafe eval, and no raw
  HTML or URL sink;
- light/dark/opposite nested schemes, RTL, sm/md/lg, default/danger, long text,
  200%/400% zoom, text spacing, narrow/wide, coarse pointer, virtual keyboard,
  reduced motion, forced colors, print, axe, console, and page-error gates;
- exact readable/emitted asset frames, positive shared deltas, strict ceilings,
  canonical no-delimiter set measurement, marker-bounded logical attribution,
  helper-frame relocation invariance,
  duplicate-frame detection, wheel inclusion, import/export boundaries, and
  1/10/100 instance plus 10/100/500 command scaling; and
- every catalog example rendered independently through the actual docs preview
  path plus the signed quality scenario in Chromium, Firefox, and WebKit.

The semantic pressure test compares accessibility snapshots of options built
from neutral rows, links with `role="option"`, Buttons with `role="option"`,
and ordinary native link/Button lists. Only the neutral callback option is an
accepted palette command. A grid alternative remains rejected unless a future
design proves its complete keyboard and AT model.

Manual release evidence is VoiceOver with Safari and NVDA with Firefox for
Dialog/title/search/listbox/group/option announcements, exact active movement,
description and disabled output, empty result, query editing, IME, action,
Escape, close Button, nested modal, and return focus. Manual keyboard work
includes every table row in section 8. Visual sign-off covers every environment
and size in the example catalog. These manual gates block release.

## 18. Compatibility classification

1. **Stable public API:** all exports, aliases, record names/fields/defaults,
   component server/client inputs, slots and exact slot-data fields, callbacks
   and detail fields, variables, selectors, reflected attributes, visible
   default strings, validation errors by category, filtering definition,
   accepted-close query reset, and absence of public methods/global shortcuts/URLs.
2. **Behavioral and structural contract:** native Dialog plus owned
   search/combobox/listbox/group/option relationships, callback-only actions,
   internal active descendant, exact keyboard/focus/form behavior, controlled
   ownership, action-before-close order, no-JavaScript output, record/morph
   identity, ShadowRoot support, and the documented stable anatomy.
3. **Evolvable design:** exact theme values, spacing, shadows, row typography,
   nonessential animation, private filtering loops, and undocumented wrappers
   may improve without changing public meaning or acceptance. User-visible
   changes require release notes.
4. **Private implementation:** private host, `.cui-*` classes, `--_cui-*`
   variables, readiness/owner/correlation attributes, fingerprints,
   controller/helper module structure, tasks, observers, and generated ID
   spelling.

Changing a stable name, field, type, default, meaning, semantic boundary, or
behavior follows the library deprecation and semantic-versioning policy.

## 19. Public documentation contract

The guide starts with a basic callback-driven palette, then records/groups,
filtering and empty results, disabled/shortcut/intent, visual adornments,
controlled open/query, action and close policy, app-owned shortcuts, Form/IME
safety, and Dialog/ShadowRoot/environment behavior. It explicitly states that
shortcut text is presentational and that native links belong in another
navigation surface.

`api.yml` is organized by Inputs, Slots, Events, Methods, CSS, Attributes,
Selectors, and Interfaces. Methods is `-`. Every public alias, record, slot-data
record, callback-detail record, literal value, server/client classification,
default, release-control behavior, and stable selector has a durable kebab-case
ID. Markdown contains no duplicate generated API table.

The exact public example catalog is:

| Reader task | Fixture theme and copy | Visible states | Controls | Interaction | Environment profiles | Contract coverage | Source module | Focused browser evidence |
|---|---|---|---|---|---|---|---|---|
| Open and run a command | Workspace: “Open settings”, “Create project”, “Invite teammate” | closed, open, active first command | owned Button activator | open, type, Arrow, Enter, Escape, return focus | light/dark, keyboard/pointer | basic semantics, activator attrs, callback, accepted-close query reset | `basic_command_palette.py` | C/F/W role tree, action ledger, axe, console |
| Build records in Python | “Project navigation” and “Draft actions” | grouped commands and visual separator | Python record tuple | filter and invoke | light, direct Python render | frozen records, global value identity, group/separator anatomy | `python_command_records.py` | C/F/W render parity and callback identity |
| Search aliases and empty results | “Theme”, “Appearance”, “Color mode”; query `zz` | matches, no match, all disabled match | query controls | exact substring filter and clear | narrow/wide, 400% zoom | canonicalization, label/keywords-only, empty status, no ranking | `search_and_empty.py` | C/F/W query/result/AX ledger |
| Show disabled commands and shortcuts | “Deploy production”, “Delete environment”, “View logs” | enabled, disabled, default/danger, shortcut hints | disabled/intent toggles | arrow skip, pointer refusal | light/dark, forced colors, RTL | disabled semantics, intent, visual-only shortcut, loop | `disabled_and_shortcuts.py` | C/F/W keyboard/pointer/forced-colors checks |
| Add safe adornments | icons and “Beta” badge | start/end renderer variants | slot source disclosure | filter and invoke through decorated row | light/dark, text spacing | immutable slot data, inert/aria-hidden wrappers, no DOM-text search | `command_adornments.py` | C/F/W anatomy, interaction rejection, axe |
| Control open and query | “Switch workspace” | accepted/declined open and exact query | owner accept toggles and request log | type, decline close, accept close, release control | keyboard/pointer | controlled ownership, request-only text, null release, close-only reset | `controlled_command_palette.py` | C/F/W exact callbacks/state/focus |
| Choose action close policy | “Copy ID”, “Toggle sidebar”, “Delete draft” | stay-open and close commands | root/command policy controls | callback order, owner focus move, exception diagnostic | keyboard/pointer/touch | action transaction, per-command override, reentrancy, focus winner | `command_actions.py` | C/F/W once/order/close/focus ledger |
| Own a global shortcut in the app | app shell with `Mod+K` help text | palette closed/open plus unrelated input | app-level shortcut enable toggle | shortcut outside editable; collision/editable/composition ignored | desktop keyboard, multiple palettes | no component global listener, app ownership, isolation | `application_shortcut.py` | C/F/W app listener scope and resource counts |
| Use inside an application Form | profile Form with Save submitter | closed, open, composing, empty | submit counter and IME fixture | Enter with/without option, IME Enter/Escape, explicit action submit | C/F/W native Forms | no form participation, server-disabled fallback, no implicit submit | `form_safe_palette.py` | C/F/W submit/input/composition ledger |
| Compose with modal and anchored layers | palette in Dialog, command opens Popover | nested modal/overlay and focus return | open/close controls | nested open, Escape order, outside, remove | Document/open ShadowRoot | shared Dialog/layer ownership, top-layer order, cleanup | `palette_layers.py` | C/F/W layer/focus/resource assertions |
| Inspect responsive and environment behavior | long localized command names | sm/md/lg, overflow, empty, danger, disabled | size/theme/direction toggles | keyboard and touch | light/dark, RTL, 200/400%, coarse, virtual keyboard, reduced motion, forced colors, print | public variables/selectors, wrapping, reachability, print | `command_palette_environment.py` | C/F/W computed style, screenshot, axe, print |

The Python-owned quality scenario combines the full record surface, controlled
state, action/focus behavior, Form containment, safe adornments, nested layers,
signed retained/changed/replacement/removal morphs, and resource cleanup. It is
reused by docs preview, standalone route, Playwright, axe, screenshot, scaling,
and packaging gates.

## 20. Open decisions and deferred work

No open decision blocks implementation. The following work is outside this
family and requires a new evidence-backed design rather than an incidental prop:

| Deferred job | Evidence required | Owner | Release effect |
|---|---|---|---|
| ranked/fuzzy/custom filtering | product queries where deterministic substring and keywords fail, plus cross-language ranking expectations and payload budget | future collection/search proposal | none |
| remote results, loading, cancellation, and virtualization | real dataset scale/latency/offline jobs and an async ownership protocol | future virtual/async collection family | none |
| recent history, nested pages, and command registration | application product model, persistence/privacy policy, and authorization boundary | application or future command-registry proposal | none |
| reusable global shortcut manager | multi-scope collision, editable-target, layout, IME, OS/browser-reserved key, teardown, and discoverability requirements | application infrastructure proposal | none |
| native navigation actions inside a palette-like surface | semantic proof retaining link name/role/modifier/context behavior plus a complete keyboard and manual AT plan | separate navigation component proposal | none |

The record model, callback-only activation, internal active state, absence of
`href`, and absence of a component-owned global shortcut are settled v1
boundaries, not implementation questions.

## 21. Internationalization

Placeholder, search label, empty fallback, and close label have distinct keys
in the structured [Translation keys table](../../../packages/py/citry_ui/citry_ui/components/ccommand_palette/api.yml).
Their stable text and attributes use server `tr()` plus `$c-tr`. Explicit
inputs win, and an `empty` slot owns its complete output so the component does
not bind catalog text beneath it. Search matching uses the provider locale but
does not claim full natural-language collation.
