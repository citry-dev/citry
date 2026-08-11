# Split Button component design

Status: frozen for independent design review on 2026-08-11. No runtime or
public documentation work is authorized until this package passes that review.

## 1. Purpose and product bar

`CSplitButton` presents one dominant native action beside a separate Button
that opens a Menu of related actions. It is a compound interaction, not a
visual shortcut for two unrelated Buttons.

The product bar is:

- the dominant action is visible and immediately operable;
- the Menu Button is a distinct native Button with an explicit accessible
  name, independent focus, and standard Menu Button relationships;
- the two controls form one labelled horizontal group while retaining two Tab
  stops and two activation behaviors;
- the Menu is the existing Citry Menu model, including declarations,
  controlled state, keyboard behavior, anchored layering, submenus, choices,
  lifecycle, and callback ordering;
- the primary Button keeps CButton's native form, loading, disabled, reactive
  presentation, and focus behavior;
- narrow, zoomed, RTL, forced-colors, reduced-motion, light, dark, ShadowRoot,
  modal, morph, and no-JavaScript cases have explicit outcomes; and
- implementation shares the private Button and Menu machinery. It does not
  copy CMenu JavaScript, create a second collection model, or hide a public
  CMenu component behind a forwarding wrapper.

This is more than consumer composition. A plain `CButtonGroup` plus `CMenu`
cannot make a CMenu activator an immediate grouped Button, forward one
`$c-props` owner across a nested public component boundary, anchor width and
placement to the full joined control, close exactly once when the primary
action runs, or expose one coherent disabled and lifecycle contract. Consumers
may still compose those primitives when they need a different policy.

Use Split Button only when one action is clearly dominant and the Menu actions
are close alternatives. Use CButton for one action, CMenu for a Menu Button,
CButtonGroup for several visible peers, Select for choosing a value, and
Disclosure for revealing content.

Common jobs and their shortest intended surfaces are:

| Job | Template or Python expression | Support path |
|---|---|---|
| run the dominant command | `<c-CSplitButton label="Save actions" menu_label="More save actions"><c-fill name="default">Save</c-fill><c-fill name="menu">...</c-fill></c-CSplitButton>` | direct component API plus native `@click` |
| submit with alternatives | `CSplitButton("Save", type="submit", primary_attrs={"name": "action", "value": "save"}, menu=[...], ...)` | native Button/form attributes |
| expose related commands and choices | existing `CMenuItem`, choice, group, separator, and submenu declarations in `menu` | composition with the existing CMenu family |
| own Menu visibility | `$c-props="{open, onOpenChange}"` | controlled client API |
| keep alternatives usable while primary work is pending | `$c-props="{loading}"` | direct reactive configuration |
| style a brand-specific pair and Menu | inherited `--cui-button-*`, `--cui-menu-*`, and `--cui-split-button-*` | public CSS contract |
| make the dominant action a link | explicit CButtonGroup plus CMenu composition | supported composition, not direct SplitButton API |
| show equal-priority visible actions | CButtonGroup | separate component |
| choose a value without immediate actions | CSelect or CCombobox | separate component |

Non-goals are a vertical control, selected-action replacement, hidden
long-press Menu access, router/link primary, arbitrary activator, item-model
adapter, responsive semantic collapse, and generic overlay configuration.
There is no headless SplitButton API. The stable native anatomy and existing
CMenu declaration model are the extension points.

## 2. Prior art and complaints

Sources were reviewed on 2026-08-11. Versioned product sources use the current
release recorded in Citry's source dossier.

| Source | Current version or review date | Evidence used | Citry disposition |
|---|---|---|---|
| [HTML Living Standard, Button](https://html.spec.whatwg.org/multipage/form-elements.html#the-button-element) and [Popover](https://html.spec.whatwg.org/multipage/popover.html) | living standard, 2026-08-11 | native Button type/form rules and manual popover lifecycle | adopt native roots; keep controlled ownership above native popover |
| [WAI-ARIA APG Menu Button](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/) and [Menu and Menubar](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/) | current, 2026-08-11 | Menu Button relationships, focus entry, item keyboard model | adopt through CMenu; do not invent split-specific Menu keys |
| [PrimeVue SplitButton](https://primevue.org/splitbutton/) | 4.5.5 | dedicated two-native-Button anatomy, explicit Menu Button name, nested Menu and keyboard support | adopt the boundary and naming requirement; reject model-only content and opaque pass-through bags |
| [MUI Button Group, Split button](https://mui.com/material-ui/react-button-group/) | 9.3.1 | immediate-child grouping; Menu may change the default or run a related action | adopt joined visual precedent; keep Citry's dominant action stable and immediate |
| [Fluent 2 Button usage](https://fluent2.microsoft.design/components/web/react/core/button/usage) | reviewed 2026-08-11 | dominant action plus related Menu; dominant action should not be repeated; full accessible wording | adopt product and content guidance |
| [Web Awesome Button Group, Split Buttons](https://webawesome.com/docs/components/button-group/) | 3.9.0 | Button + Dropdown composition and visually hidden Menu Button label | adopt explicit secondary name; dedicated Citry component closes ownership gaps |
| [React Spectrum MenuTrigger](https://react-spectrum.adobe.com/react-spectrum/MenuTrigger.html) | React Spectrum 1.4.0; React Aria 1.20.0 | trigger/Menu composition and long-press alternative | retain ordinary two-Button behavior; omit long press and Alt+Arrow hidden modes |
| [Open UI Menu Elements explainer](https://open-ui.org/components/menu.explainer/) | current, 2026-08-11 | Button-invoked Menu roles and platform direction | follow through CMenu; do not use customizable-select semantics |
| [Vuetify Button](https://vuetifyjs.com/en/components/buttons/), [Button Group](https://vuetifyjs.com/en/components/button-groups/), and [Menu](https://vuetifyjs.com/en/components/menus/) | 4.1.8 | composition from `VBtn`, `VBtnGroup`, `VMenu`, and list declarations | use as a coverage ledger, not a public API template; Vuetify has no dedicated current SplitButton |
| PrimeVue implementation | 4.5.5 | tagged [`SplitButton.vue`](https://github.com/primefaces/primevue/blob/4.5.5/packages/primevue/src/splitbutton/SplitButton.vue) and [type/API source](https://github.com/primefaces/primevue/blob/4.5.5/packages/primevue/src/splitbutton/SplitButton.d.ts) | verify two-Button implementation, Menu ownership, pass-through pressure, and events rather than copying docs labels alone |
| Material UI implementation | 9.3.1 | tagged [`ButtonGroup.js`](https://github.com/mui/material-ui/blob/v9.3.1/packages/mui-material/src/ButtonGroup/ButtonGroup.js) and [`Button.js`](https://github.com/mui/material-ui/blob/v9.3.1/packages/mui-material/src/Button/Button.js) | verify immediate-child styling and Button loading/form behavior behind the composed demo |
| Web Awesome implementation | 3.9.0 | tagged [`button-group.ts`](https://github.com/shoelace-style/webawesome/blob/v3.9.0/packages/webawesome/src/components/button-group/button-group.ts) and [`dropdown.ts`](https://github.com/shoelace-style/webawesome/blob/v3.9.0/packages/webawesome/src/components/dropdown/dropdown.ts) | verify composition remains separate components and needs an explicit trigger name |
| Vuetify implementation | 4.1.8 | tagged [`VBtn.tsx`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VBtn/VBtn.tsx), [`VBtnGroup.tsx`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VBtnGroup/VBtnGroup.tsx), and [`VMenu.tsx`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VMenu/VMenu.tsx) | primary styled-suite source for direct Button, group, activator, controlled visibility, placement, and omitted layer props |
| Citry local foundations | current workspace, 2026-08-11 | [Button](./button.md), [ButtonGroup](./button-group.md), [Menu](./menu.md), [overlay foundations](../ui_overlay_foundations.md), current runtime, server tests, browser tests, asset tests, inventory, taxonomy, and complaint register | prove why public composition alone cannot forward state or preserve immediate-child geometry; reuse all completed behavior privately |

Recurring complaints and failure modes are concrete:

- icon-only Menu Buttons are announced as an unlabeled “button”;
- duplicating the primary action in the Menu makes the hierarchy ambiguous;
- an outer wrapper cannot safely forward reactive controlled Menu state into a
  nested public child;
- a Menu host wrapper breaks ButtonGroup's immediate-child joined selectors;
- `match_width` against the narrow chevron Button produces an unusable Menu;
- putting `type=submit` on both halves causes accidental form submission;
- disabling or loading both halves when only one is unavailable hides useful
  alternatives;
- uncontrolled and controlled close paths can double-notify when a primary
  click is also treated as outside interaction;
- local z-index, copied dismissal handlers, or copied Menu JS drift from the
  shared layer contract; and
- physical right/left assumptions break corner joining, placement, and icon
  order in RTL.

No still-material SplitButton-specific defect report was found in the official
PrimeVue, MUI, Web Awesome, or Vuetify trackers during the 2026-08-11 refresh.
The complaints above are attributed to the cited official behavior and Citry's
current local source/tests, not presented as external issue reports. General
Menu complaints and tagged issue dispositions remain recorded in the current
[Menu specification](./menu.md); SplitButton adopts those exact acceptance
cases rather than duplicating them here.

Vuetify carries the primary styled-suite comparison weight. Its current
surfaces map as follows:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `VBtn` primary click | native HTML/event | primary Button plus `@click` | adopt native behavior |
| `VBtn` `type`, form attrs | direct API/native attrs | `type`, `primary_attrs` | adopt through CButton contract |
| `VBtn` `href`, router `to`, exact/replace | explicit composition | CButtonGroup + link CButton + CMenu | omit from SplitButton |
| `VBtn` loading and disabled | direct API | `loading`, `primary_disabled`, common `disabled` | adopt with loading scoped to primary |
| `VBtn` variant/color/size/block | direct API | `variant`, `intent`, `size`, `block` | normalize to existing CButton vocabulary |
| `VBtn` prepend/append/loading content | named slots | `start`, `end`, `loading` | adopt existing CButton slots |
| `VBtnGroup` joined horizontal geometry | internal compound anatomy | root plus two immediate native Buttons | adopt; vertical omitted |
| `VBtnGroup` selected/toggle state | separate selection component | no SplitButton surface | reject unrelated state |
| `VMenu` `v-model` | controlled client API | `open`, `onOpenChange` | adopt nullable release through CMenu |
| `VMenu` activator slot/props | owned internal trigger | `menu_label`, `trigger_attrs` | omit arbitrary activator; retain safe native destination |
| `VMenu` location/close-on-content-click | direct API | `placement`, `close_on_select` | adopt logical vocabulary |
| `VMenu` min/max width, offset, origin | CSS/direct bounded API | Menu variables, `match_width` | use public CSS; omit coordinate props |
| `VMenu` open/close delays and transition props | CSS/private behavior | Menu duration/easing variables | omit behavioral delay configuration |
| `VMenu` attach/contained/absolute/teleport | shared layer policy | native top layer and anchored coordinator | omit local layer escape hatches |
| `VMenu` scrim and persistent policy | Dialog/Popover jobs | separate components | omit |
| `VList` items, nested children, active choices | existing declarations | CMenu declaration family | adopt without a model adapter |
| imperative activator/menu methods | declarative/native refs | `$c-props`, native `focus()`/`click()` | omit public methods |
| dedicated SplitButton component | no current Vuetify surface | `CSplitButton` | Citry adds it to close forwarding, form, and lifecycle ownership |

PrimeVue supplies the strongest dedicated-component comparison. MUI and Web
Awesome prove the common composition shape. Fluent supplies the strongest
content distinction. No reviewed product provides a safe reason to copy Menu
runtime or to blur the two native activation targets.

## 3. Public composition and anatomy

The public family adds `CSplitButton`. It does not add SplitButton-specific
item declarations. The required `menu` slot accepts the existing public
`CMenuItem`, `CMenuCheckboxItem`, `CMenuRadioGroup`, `CMenuRadioItem`,
`CMenuGroup`, `CMenuSeparator`, and `CMenuSubmenu` declarations with every
existing CMenu nesting rule.

Template composition:

```html
<c-CSplitButton
  label="Save actions"
  menu_label="More save actions"
  type="submit"
  c-primary_attrs="{'name': 'action', 'value': 'save'}"
>
  <c-fill name="default">Save</c-fill>
  <c-fill name="start"><c-CIcon name="save" /></c-fill>
  <c-fill name="menu">
    <c-CMenuItem value="save-copy">Save a copy</c-CMenuItem>
    <c-CMenuItem value="export">Export</c-CMenuItem>
  </c-fill>
</c-CSplitButton>
```

Python composition uses the same slots and existing declaration components:

```python
CSplitButton(
    label="Save actions",
    menu_label="More save actions",
    type="submit",
    primary_attrs={"name": "action", "value": "save"},
    slots={
        "default": "Save",
        "start": CIcon(name="save"),
        "menu": (
            CMenuItem(value="save-copy", slots={"default": "Save a copy"}),
            CMenuItem(value="export", slots={"default": "Export"}),
        ),
    },
)
```

The exact stable anatomy is:

```text
div[role=group][aria-label=label][data-citry-ui-part=split-button]
  button[data-citry-ui-part=split-button-primary]
    span[data-citry-ui-part=split-button-primary-start]?
    span[data-citry-ui-part=split-button-primary-content]
    span[data-citry-ui-part=split-button-primary-end]?
    span[data-citry-ui-part=split-button-primary-loading-indicator]
  button[type=button][data-citry-ui-part=split-button-menu-trigger]
    span[aria-hidden=true][data-citry-ui-part=split-button-menu-indicator]
  div[popover=manual][role=menu][data-citry-ui-part=menu]
    existing CMenu declaration output
```

The root and two Buttons are in ordinary DOM order. The Menu surface is the
same native/manual-popover anatomy used by CMenu. The Menu Button owns
`aria-label=menu_label`, `aria-haspopup=menu`, `aria-controls`, and
`aria-expanded`. The Menu surface uses `aria-labelledby` to that Button. The
group's `aria-label` is the separate `label`; it names the compound without
rewriting either Button's accessible name. For example, `label="Save actions"`
and `menu_label="More save actions"` avoid announcing the secondary purpose as
the name of the whole compound. `menu_label` must describe the secondary
purpose, not only “More”.

Identity is literal. A supplied `id="save-actions"` yields root
`id="save-actions"`, primary `id="save-actions-primary"`, Menu Button
`id="save-actions-menu-trigger"`, and root Menu surface
`id="save-actions-menu"`. When omitted, the root base is
`cui-split-button-{self.id}`, where `self.id` is Citry's render-frame identity;
the same three suffixes apply. Submenu IDs continue from the Menu surface base
through CMenu's current canonical value-token algorithm. Every owned ID and
IDREF is case-sensitive and repaired as one correlated set.

The primary and Menu Buttons are immediate root children so joined geometry is
reliable. The surface is a third root child, but top-layer rendering removes it
from layout. There is no public activator slot, orientation, selected-default
state, or declarative item `model`. The dominant action is not repeated in the
Menu. Duplicate wording is a documentation/content error, not a structural
render error, because translated and decorated labels cannot be compared
reliably.

`class_`, `style`, and `attrs` target the group. `primary_attrs` targets the
primary native Button. `trigger_attrs` targets the Menu Button. `menu_attrs`
targets the root Menu surface. The three mappings are snapshotted independently
and never mutate caller data.

## 4. Server inputs and client inputs

`CSplitButton` server inputs are exact:

| Input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `id` | `str | None` | generated | structural | stable root, primary, trigger, and surface ID base; nonempty, no ASCII whitespace or U+0000 |
| `label` | `str` | required | structural | non-whitespace accessible name for the compound group |
| `menu_label` | `str` | required | structural | non-whitespace accessible name for the Menu Button |
| `type` | `CButtonType` | `"button"` | structural | primary native `button`, `submit`, or `reset` behavior |
| `disabled` | `bool` | `False` | reactive configuration | common override that disables both Buttons and force-closes the Menu |
| `primary_disabled` | `bool` | `False` | reactive configuration | disables only the primary Button |
| `menu_disabled` | `bool` | `False` | reactive configuration | disables only the Menu Button and force-closes the Menu |
| `loading` | `bool` | `False` | reactive configuration | primary pending state; retains primary focus and leaves an otherwise enabled Menu Button available |
| `variant` | `CButtonVariant` | `"solid"` | reactive configuration | common Button presentation strength |
| `intent` | `CButtonIntent` | `"primary"` | reactive configuration | common semantic color role |
| `size` | `CButtonSize` | `"md"` | reactive configuration | common control and Menu item size |
| `block` | `bool` | `False` | reactive configuration | group fills its containing inline size; primary takes remaining width |
| `loading_pos` | `CButtonLoadingPos` | `"center"` | reactive configuration | primary loading indicator placement |
| `open` | `bool` | `False` | initial value | initial Menu visibility and uncontrolled fallback |
| `loop` | `bool` | `True` | reactive configuration | CMenu arrow and typeahead wrapping |
| `placement` | `CMenuPlacement` | `"bottom-end"` | reactive configuration | logical placement relative to the full SplitButton root |
| `match_width` | `bool` | `False` | reactive configuration | matches the full SplitButton width, not the narrow Menu Button width |
| `close_on_select` | `bool` | `True` | reactive configuration | CMenu default item close policy |
| `class_` | `CClassValue | None` | `None` | structural | root classes |
| `style` | `CStyleValue | None` | `None` | structural | root styles; private anchor identity merges last |
| `attrs` | `Mapping[str, object] | None` | `None` | structural | allowed group attributes |
| `primary_attrs` | `Mapping[str, object] | None` | `None` | structural | allowed native primary Button attributes |
| `trigger_attrs` | `Mapping[str, object] | None` | `None` | structural | allowed native Menu Button attributes |
| `menu_attrs` | `Mapping[str, object] | None` | `None` | structural | allowed root Menu surface attributes |

`name`, `value`, `form`, `formaction`, `formenctype`, `formmethod`,
`formnovalidate`, and `formtarget` remain available through `primary_attrs`
exactly as they do through `CButton.attrs`. `href` is deliberately absent. A
split dominant action is a command or form action; consumers needing a
dominant link compose CButtonGroup and CMenu explicitly.

The component uses existing public aliases without redefining or re-exporting
them: `CButtonType`, `CButtonVariant`, `CButtonIntent`, `CButtonSize`,
`CButtonLoadingPos`, and `CMenuPlacement`. `size` uses the identical `sm | md |
lg` vocabulary for both Button and Menu geometry.

Client inputs are exact:

| Input | Type | Omitted / `null` | Invalid | Effect |
|---|---|---|---|---|
| `open` | `boolean | null` | releases control from committed state | reports once and releases | controlled Menu visibility |
| `disabled` | `boolean` | server fallback | reports once, uses fallback | common disabled override |
| `primaryDisabled` | `boolean` | server fallback | reports once, uses fallback | primary effective disabledness |
| `menuDisabled` | `boolean` | server fallback | reports once, uses fallback | Menu trigger disabledness and forced close |
| `loading` | `boolean` | server fallback | reports once, uses fallback | primary pending guard |
| `variant` | `CButtonVariant` | server fallback | reports once, uses fallback | both Buttons' presentation |
| `intent` | `CButtonIntent` | server fallback | reports once, uses fallback | both Buttons' color role |
| `size` | `CButtonSize` | server fallback | reports once, uses fallback | Button and Menu geometry |
| `block` | `boolean` | server fallback | reports once, uses fallback | group width behavior |
| `loadingPosition` | `CButtonLoadingPos` | server fallback | reports once, uses fallback | primary loading layout |
| `loop` | `boolean` | server fallback | reports once, uses fallback | CMenu navigation wrapping |
| `placement` | `CMenuPlacement` | server fallback | reports once, uses fallback | preferred root Menu placement |
| `matchWidth` | `boolean` | server fallback | reports once, uses fallback | root-width matching |
| `closeOnSelect` | `boolean` | server fallback | reports once, uses fallback | Menu action close policy |
| `onOpenChange` | `function | null` | no component callback | reports once, uses no callback | CMenu visibility notices |
| `onAction` | `function | null` | no component callback | reports once, uses no callback | valued command/choice actions |

Valid client configuration wins field by field. Omission restores a server
configuration fallback except `open`, whose omission or `null` releases
control from the latest committed open state. One invalid episode ends only
after a valid value or omission. Structural server inputs and attribute
destinations cannot be changed through `$c-props`.

The component module and family/package `__all__` export exactly
`CSplitButton`, `CSplitButtonDefaultSlotData`, `CSplitButtonStartSlotData`,
`CSplitButtonEndSlotData`, `CSplitButtonLoadingSlotData`, and
`CSplitButtonMenuSlotData`. Existing CButton/CMenu aliases and
`CMenuOpenChangeDetail`/`CMenuActionDetail` stay owned and exported by their
original families; SplitButton references those public types. `Kwargs` stays
nested. Private validators, Menu adapters, Button render records, and client
records are not exported.

## 5. State model

The root owns one compound configuration snapshot. The primary state is
`enabled | disabled | loading`. The Menu root retains CMenu's exact
`closed | opening | open | closing` state, committed open value, controlled
owner, active item, submenu path, layer generation, focus destination, and
structural suppression latch.

Effective values are:

```text
primary disabled = disabled OR primaryDisabled OR native :disabled
menu disabled = disabled OR menuDisabled OR native :disabled
primary loading = loading
effective Menu open = desired open AND NOT menu disabled AND eligible ancestry
```

Native `fieldset[disabled]` contributes through each Button's `:disabled`
state. Loading alone never makes the primary Button natively disabled during
client operation, so it retains focus, exposes busy/disabled ARIA, and blocks
new activation through the shared CButton guard. Disabled and loading may both
remain reflected, matching CButton; native disabled behavior then governs
focus and activation. The Menu Button can remain active while the primary
action is loading. `disabled=True` always wins for activation and focus but
does not erase the authored loading state.

The Menu state and all requests follow CMenu exactly. `open` is controlled
while a Boolean client value is supplied. Trigger, Escape, outside,
focus-outside, Tab, item action, and native visibility changes only request a
change when controlled. Omission or `null` releases from the last committed
state. Disabling the Menu or a native fieldset force-closes with
`reason="disabled", forced=True`; a still-supplied controlled `True` may reopen
on re-enable unless the owner acknowledges with `False`. Ancestor/modal safety
close suppresses resurrection until a new accepted edge, exactly as CMenu.

Primary activation is one transaction:

1. the CButton capture guard rejects it if disabled or already loading;
2. if the Menu is open, SplitButton synchronously requests one ordinary close
   during the component's capture handler with
   `reason="action"` and `source` equal to the primary Button;
3. the uncontrolled Menu commits closed and notifies, or the controlled Menu
   notifies and waits for its owner; and
4. the native target/bubble handlers and click, submit, or reset default action
   continue.

The primary Button is registered as an `insideElement` of the Menu layer. Its
pointer/focus transition is therefore not an outside dismissal. One primary
activation cannot report both `outside` and `action`. An uncontrolled Menu
commits closed before the native primary default action. A controlled owner may
decline the close; that does not cancel the native action. Focus stays on the
primary Button, and accepted Menu close never restores focus to the Menu
Button when focus already belongs to the primary Button or another owner-moved
destination.

The synchronous ordinary action-close notice cannot be retracted, relabelled,
or superseded by a later consumer click/form handler. If it already closed the
Menu, a handler that then opens a modal or removes/replaces the SplitButton
produces no second close notice. If a controlled owner refused the action
request and a later handler opens a modal, the still-open Menu receives the
separate forced `ancestor` safety close required by CMenu; that is a later real
transition, not duplicate reporting of the ordinary request. Removal disposes
without another notice. A primary handler that sets `loading=True` affects
later activations, not the accepted current click. Same-value commits do not
notify. Every notice uses CMenu's callback snapshot rules.

## 6. Slots and slot data

| Slot | Required | Cardinality | Slot data | Fallback |
|---|---:|---:|---|---|
| `default` | yes | one fill | empty `CSplitButtonDefaultSlotData` | none |
| `start` | no | one fill | empty `CSplitButtonStartSlotData` | omitted |
| `end` | no | one fill | empty `CSplitButtonEndSlotData` | omitted |
| `loading` | no | one fill | empty `CSplitButtonLoadingSlotData` | CSS spinner |
| `menu` | yes | nonempty declaration collection | empty `CSplitButtonMenuSlotData` | none |

The first four slots use CButton's content rules. They accept text and
decorative noninteractive content, never links, controls, editable content,
focusable descendants, Menu declarations, unresolved custom elements,
customized built-ins, or detectable authored shadow hosts. The default slot
must be structurally nonempty but may be an icon or other decorative content.
The final primary Button must receive a nonempty accessible name from visible
default text, permitted `primary_attrs` `aria-label`, or permitted
`aria-labelledby`; the final browser name, not the slot alone, is the
requirement. The loading fill is decorative and hidden from the accessibility
tree.

The `menu` slot accepts exactly the existing CMenu declarations and transparent
Citry components that resolve to them. All current CMenu collection, value,
nested, label, item-content, and settled browser validation applies unchanged.
No raw HTML, arbitrary CButton, or nested CMenu root is accepted at collection
level. Existing declaration-specific slots and their existing public slot data
types remain unchanged.

Slot data is a server snapshot. Browser state is available through reflected
attributes and callback detail, not through reactive Python slot data.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger and timing | Controlled behavior |
|---|---|---|---|
| `onOpenChange` | `(requestedOpen, CMenuOpenChangeDetail)` | every CMenu root request, plus primary `action` close; after validation and before controlled commit | uncontrolled commits first; controlled waits; forced safety closes bypass refusal |
| `onAction` | `(value: str, CMenuActionDetail)` | existing valued command/check/radio action after item-specific change callback | identical to CMenu |

The detail records, reason vocabulary, callback sequence, source, controlled
and forced fields, canonical path, mutation isolation, error propagation, and
generation rechecks are exactly CMenu's public contract. A primary close uses
the existing `"action"` reason but does not call `onAction`; only Menu
declarations can emit a Menu action. Anonymous commands and links retain
CMenu's native-event policy.

The primary Button adds no component callback. Consumers listen to its native
`@click` and native form `submit`/`reset`. `@click`, `@focus`, and other
listeners in the three attribute destinations observe native events. No custom
`toggle`, `action`, `click`, or form event is dispatched.

There are no public methods. Native `focus()` and `click()` are available on
the two rendered Buttons. Opening, closing, and selection are declarative
owner state rather than imperative component methods.

## 8. Semantics, keyboard, focus, and assistive technology

The root is `div[role=group]` with `aria-label=label`. The primary is a
native Button named by its content or permitted `primary_attrs` ARIA. Server
preflight rejects an empty default fill. Settled validation requires either
nonempty rendered text or an authored `aria-label`/`aria-labelledby`; browser
AX and axe evidence then prove the computed name under supported CSS. Citry
does not claim to compute an accessible name through arbitrary consumer CSS.
The Menu Button
is a separate native `button[type=button]` named by `menu_label` and owns
`aria-haspopup=menu`, `aria-controls`, and current `aria-expanded`. The Menu
surface and items retain CMenu semantics. The indicator is `aria-hidden=true`.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| primary Button | click, Enter, Space | native click/submit/reset; open Menu requests one action close | primary stays focused unless native/application behavior moves it | no, except the existing loading guard |
| closed Menu Button | click, Enter, Space | request open | first Menu item after accepted open | only as needed to prevent duplicate Button activation |
| closed Menu Button | ArrowDown | request open | first Menu item | yes |
| closed Menu Button | ArrowUp | request open | last Menu item | yes |
| open Menu tree | CMenu keys | exact CMenu navigation, typeahead, submenu, action, Escape rules | exact CMenu result | exact CMenu rule |
| either Button | Tab / Shift+Tab | native document order | primary then Menu Button in LTR and RTL DOM order; disabled Buttons are skipped | no |
| open Menu tree | Tab / Shift+Tab | request full close without trapping | browser advances in document order; no restoration | no |

Arrow keys on the primary Button do nothing SplitButton-specific. Long press,
Alt+Arrow, combined roving focus, and a single Tab stop are omitted. DOM order
does not reverse in RTL: the primary remains first and appears at logical
start, which is the right side in RTL.

Loading primary behavior is CButton behavior: it remains focusable, keeps its
accessible name, sets `aria-busy=true` and `aria-disabled=true`, and blocks
new pointer, keyboard, `.click()`, and submitter activation. The Menu Button
remains a separate available Tab stop unless effectively disabled. A disabled
CMenu item remains navigable under APG rules; a disabled native half does not.

Escape and accepted ordinary Menu Button close restore focus only if focus
still belongs to the Menu tree. Outside, Tab, primary action, callback-moved
focus, removal, ancestor, and modal closes never steal an external destination.
If Menu-disabled state closes while focus remains in the tree, focus moves to
an enabled, connected, rendered primary Button when available. Otherwise it
uses CMenu's nearest open modal Dialog or `ownerDocument.body` fallback with a
temporary `tabindex=-1`. Focus success is verified; failed primary focus falls
through to the modal/body fallback. A disabled/disconnected/hidden primary is
never focused.

Automated accessibility evidence must assert both Button names separately,
the group name, Menu relations, item relations, busy/disabled states, native
Tab order, and no serious/critical axe findings. Manual evidence covers
VoiceOver/Safari and NVDA/Firefox naming and focus announcements.

## 9. Native forms and validation

Only the primary Button can participate in a form. The Menu Button, every
button-root Menu item, and every submenu trigger are always
`type="button"`. SplitButton is not a form-associated custom control and adds
no hidden input.

For the primary Button:

- `type="submit"` uses the native form owner and submitter;
- `type="reset"` invokes native reset;
- `name`, `value`, and `form` from `primary_attrs` land on that Button;
- every listed native form attribute in `primary_attrs` lands on it for all
  three `type` values, matching CButton and native HTML; browsers apply
  `formaction`, `formenctype`, `formmethod`, `formnovalidate`, and `formtarget`
  only when the Button is a submitter and ignore them on `button`/`reset`;
- native constraint validation, `SubmitEvent.submitter`, FormData submitter
  name/value, `requestSubmit(primary)`, and reset behavior are preserved;
- disabled primary is not a successful submitter; and
- already-loading primary blocks pointer, keyboard, `.click()`, and
  `requestSubmit(primary)` while retaining focus.

The Menu Button cannot submit even when consumer attributes, omitted HTML
defaults, a morph, or a structural failure occur. Its `type=button` is
server-rendered, owned, synchronously revalidated, and repaired before any
activation. Menu declarations keep CMenu's no-form-submit contract.

`form`, `name`, and `value` do not apply to the Menu Button or Menu surface and
are rejected there. As with native Button and CButton, a `value` without a
`name` is allowed but contributes no successful submitter pair. The primary
form owner may be outside an open ShadowRoot only where the browser's native
`form` IDREF rules allow it; Citry does not invent cross-root form ownership.

With JavaScript unavailable, server disabled/loading primary output follows
CButton's native safe fallback. The primary action remains useful when
enabled. The closed Menu surface remains in safe noninteractive server flow as
defined by CMenu, and an initially open surface is readable; the Menu Button
cannot toggle without initialization. It still cannot submit.

Citry Events sees the primary as an ordinary native submitter. Success,
server-validation failure, transport failure, retry, cancellation, and
out-of-order completion stay owned by CForm/Citry Events and application code.
SplitButton does not clear inputs, move focus, close a surrounding surface, or
set `loading`; the owner does so from the request lifecycle. A failed request
therefore preserves native edits, submitter identity, primary focus where the
transport keeps it, and Menu availability. Menu actions do not enter the form
transport unless their application callback explicitly requests it.

## 10. Styling and theme contract

The family follows [`../ui_theme.md`](../ui_theme.md). Both native Buttons use
the same private CButton renderer and consume the existing public
`--cui-button-*` variables for color, typography, spacing, target height,
loading, focus, and disabled presentation. The root Menu surface and every
declaration preserve the full public `--cui-menu-*` variable contract. Those
are intentional inherited cross-family inputs, not copied defaults.

The exact reused Button variable set is
`--cui-button-background`, `--cui-button-foreground`,
`--cui-button-border-color`, `--cui-button-hover-background`,
`--cui-button-active-background`, `--cui-button-focus-color`,
`--cui-button-radius`, `--cui-button-font-weight`, `--cui-button-gap`,
`--cui-button-disabled-opacity`, `--cui-button-height`,
`--cui-button-inline-padding`, `--cui-button-block-padding`, and
`--cui-button-font-size`. Their value types, meaning, fallback precedence, and
current defaults are exactly the CButton contract.

The exact reused Menu variable set is
`--cui-menu-background`, `--cui-menu-foreground`,
`--cui-menu-muted-color`, `--cui-menu-border-color`,
`--cui-menu-border-width`, `--cui-menu-radius`, `--cui-menu-shadow`,
`--cui-menu-submenu-shadow`, `--cui-menu-inline-size`,
`--cui-menu-min-inline-size`, `--cui-menu-max-inline-size`,
`--cui-menu-max-block-size`, `--cui-menu-padding`,
`--cui-menu-item-block-size`, `--cui-menu-item-padding-inline`,
`--cui-menu-item-gap`, `--cui-menu-item-radius`,
`--cui-menu-hover-background`, `--cui-menu-focus-background`,
`--cui-menu-focus-foreground`, `--cui-menu-focus-outline-color`,
`--cui-menu-danger-color`, `--cui-menu-disabled-opacity`,
`--cui-menu-offset`, `--cui-menu-submenu-offset`, `--cui-menu-duration`, and
`--cui-menu-easing`. Their value types, meaning, fallback precedence, and
current defaults are exactly the CMenu contract. SplitButton `api.yml` will
list every reused variable as a distinct stable entry under the component that
reads it, with a cross-link to its source-family definition.

SplitButton adds only compound variables:

| Public variable | Type | Purpose | Default |
|---|---|---|---|
| `--cui-split-button-divider-color` | color | boundary between native Buttons | `color-mix(in srgb, currentColor 32%, transparent)`; independent of a transparent solid Button border |
| `--cui-split-button-divider-width` | length | joined overlap/divider width | `1px` |
| `--cui-split-button-menu-inline-size` | length | Menu Button inline target size | equal to effective Button height |
| `--cui-split-button-radius` | length | outer joined corners | `var(--cui-button-radius, 0.5rem)` |

Stable selectors are exact:

| `data-citry-ui-part` | Element and purpose |
|---|---|
| `split-button` | labelled compound root and root attribute destination |
| `split-button-primary` | native dominant Button and primary attribute destination |
| `split-button-primary-start` | optional decorative start wrapper |
| `split-button-primary-content` | required visible primary content |
| `split-button-primary-end` | optional decorative end wrapper |
| `split-button-primary-loading-indicator` | stable pending wrapper |
| `split-button-menu-trigger` | native Menu Button and trigger attribute destination |
| `split-button-menu-indicator` | built-in decorative logical-down chevron |
| `menu` | root and submenu Menu surfaces |
| `menu-item` | command, link, checkbox, and radio semantic roots |
| `menu-item-start` | item decorative start wrapper |
| `menu-item-label` | item accessible label wrapper |
| `menu-item-description` | item accessible description wrapper |
| `menu-item-end` | item decorative end wrapper |
| `menu-choice-indicator` | checkbox/radio visual state wrapper |
| `menu-group` | generic labelled group root |
| `menu-group-label` | generic group visible name |
| `menu-radio-group` | radio choice group root |
| `menu-separator` | collection separator |
| `menu-submenu` | neutral submenu wrapper |
| `menu-submenu-trigger` | nested Menu Button with `role=menuitem` |

Stable reflections and semantic attributes are exact:

| Owner | Attribute | Values and meaning |
|---|---|---|
| root | `data-variant`, `data-intent`, `data-size` | effective common presentation |
| root | `data-block` | present when full inline width |
| root | `data-disabled` | present when common disabled override is effective |
| root | `data-primary-disabled` | present when primary is effectively disabled, including fieldset |
| root | `data-menu-disabled` | present when Menu Button is effectively disabled, including fieldset |
| root | `data-loading`, `data-loading-position` | effective primary pending state and placement |
| root | `data-open` | present while the root Menu is logically open/opening |
| primary | `id`, `type` | exact generated ID; authored `button`, `submit`, or `reset` |
| primary | native `disabled` | present for effective disabledness and the no-JavaScript loading fallback; client loading alone removes it to retain focus |
| primary | `aria-busy` | `"true"` only while loading |
| primary | `aria-disabled` | `"true"` while disabled or loading; absent otherwise |
| primary | `data-disabled`, `data-loading` | present for each independent effective condition |
| primary | `data-variant`, `data-intent`, `data-size`, `data-loading-position` | effective presentation and loading placement |
| Menu Button | `id`, `type` | exact generated ID; type always `"button"` |
| Menu Button | `aria-label`, `aria-haspopup`, `aria-controls`, `aria-expanded` | explicit secondary name, `"menu"`, exact surface IDREF, and `"true"` or `"false"` logical state |
| Menu Button | native `disabled`, `data-disabled` | present for effective Menu disabledness |
| Menu Button | `data-variant`, `data-intent`, `data-size` | effective common presentation |
| root Menu surface | `id`, `popover`, `role`, `aria-labelledby` | exact generated ID, `"manual"`, `"menu"`, and Menu Button IDREF |
| root Menu surface | `data-open`, `data-placement`, `data-match-width`, `data-size` | committed logical open, requested placement, match flag, and effective size |
| item/link | `role`, `aria-labelledby`, optional `aria-describedby` | `"menuitem"` and owned exact label/description IDREFs |
| checkbox/radio item | `role`, `aria-checked`, `data-checked` | `menuitemcheckbox` or `menuitemradio` and exact effective false, true, or mixed where supported |
| any actionable item | optional `aria-disabled`, `data-disabled` | present/`"true"` for focusable inactive items |
| ordinary/submenu item | `data-intent` | `"default"` or `"danger"` |
| generic/radio group | `role`, optional `aria-labelledby` | `"group"` and exact group-label IDREF |
| separator | `role` | `"separator"` |
| submenu wrapper | `data-open` | present only while its child Menu is logically open |
| submenu trigger | `role`, `aria-haspopup`, `aria-controls`, `aria-expanded` | `"menuitem"`, `"menu"`, child surface IDREF, and exact logical state |

Joined layout uses logical corners. The primary owns logical-start corners and
the Menu Button logical-end corners. The common border overlaps by the divider
width. `:focus-visible` raises the focused Button above its sibling so neither
ring is clipped. Consumer part selectors can change presentation but cannot
invalidate semantics, hit testing, presence, or ownership.
The divider is a dedicated noninteractive logical-start border/pseudo-element
on the Menu Button, not whichever Button border happens to remain. Forced
colors sets it to `ButtonText`. Computed-style and visual assertions cover
solid, outline, ghost, disabled, forced-colors, and both brand schemes.

## 11. Environmental behavior

Light, dark, and opposite nested `color-scheme` scopes use the current Button
and Menu roles without a document-only snapshot. Both Buttons and the top-layer
Menu inherit the nearest authored scheme and public variables through native
ancestry. Dynamic ancestor scheme changes update an open Menu.

In RTL, the primary stays logical-start, the Menu Button stays logical-end,
joined corners reverse, the chevron retains a vertical meaning, and
`bottom-end` aligns to the full root's logical end. CMenu submenu arrows and
collision behavior continue to use actual logical geometry.

At narrow widths the group stays one horizontal compound. The primary uses
`min-inline-size: 0`, its label can wrap, and the Menu Button retains its target
width. `block=True` fills the container and gives remaining width to the
primary. The component never silently collapses the visible primary action,
reorders Buttons, or turns into one Menu Button. Long labels, 320 CSS px,
400% zoom/reflow, and nested containers must not create page-level horizontal
overflow.

Reduced motion removes spinner rotation and Menu entry/exit animation while
retaining state. Forced colors preserves native Button borders, the divider,
both focus rings, indicator visibility, Menu focus, and checked states. Print
shows the primary Button and closed Menu Button as ordinary controls but never
forces Menu surfaces open. Coarse pointer does not add hover-only behavior;
target size and spacing remain compliant with the Button contract.

The component authors only the decorative icon. All visible language belongs
to slots/declarations. `menu_label` and item labels must be translated by the
application. The primary and Menu item wording should be full, concise action
phrases; the dominant action should not be repeated in the Menu.

## 12. Overlay and layering behavior

The Menu surface uses `popover="manual"`, native top-layer rendering, CSS
anchor positioning, and the shared anchored-layer coordinator from
[`../ui_overlay_foundations.md`](../ui_overlay_foundations.md). It gets no
local z-index scale, teleport, portal option, scrim, focus trap, scroll lock,
or alternate dismissal engine.

The full SplitButton root is the positioning and width anchor. The Menu Button
is the semantic trigger and focus-return target. The private Menu controller
must therefore accept distinct `trigger`, `anchor`, `surface`, and
`insideElements`; CMenu passes the same activator as trigger and anchor, while
CSplitButton passes the Menu Button as trigger, the group as anchor, and the
primary Button as an inside element. This adapter is private and does not
change CMenu's public anatomy.

Placement uses CMenu's six logical root placements and current collision
fallback. `match_width=True` uses the group's border-box width up to
`--cui-menu-max-inline-size`; the viewport-safe maximum wins. Submenus remain
anchored to their own triggers. Open surfaces escape ordinary overflow through
the top layer while preserving logical DOM ancestry and CSS inheritance.

Outside pointer/focus, Escape, Tab, modal changes, ancestor layer close,
ShadowRoot scope discovery, nested parentage, forced structural close,
generation cancellation, focus return, and resource accounting are CMenu's
exact behavior. The primary Button is inside this logical layer only for
dismissal deduplication. It is not a Menu activator and does not inherit Menu
Button keyboard behavior.

SplitButton inside an open ShadowRoot is supported. SplitButton inside an open
Dialog/Popover is supported when the coordinator finds the same logical modal
and ancestor ownership as CMenu. A primary action may open a sibling Dialog;
the prior synchronous action-close remains the recorded ordinary reason and
the Dialog owns its later focus. Closed or
opaque descendant shadow roots and already-open top-layer reparenting retain
the shared foundation's documented limits.

## 13. Collections, async data, and identity

The `menu` slot uses CMenu's exact declaration registry, canonical value
normalization, direct-child collection validation, group/radio/submenu
structure, path identity, choice ownership, typeahead source, and correlated
morph recovery. SplitButton neither converts Python model records nor creates
a parallel item identity scheme.

`id` derives the literal root, primary, Menu Button, and surface IDs specified
in section 3. Declaration
values are canonical only at their current Menu level; submenu values form
callback paths. Duplicate identities, invalid separators/groups, orphan
declarations, empty collections, and invalid settled output fail with CMenu's
same errors. Consumer DOM IDs do not replace owned relationships.

The component owns no request. Application code owns primary async work,
loading changes, cancellation, retry, stale completion, item loading, and
controlled state. `loading=True` describes only the primary action. Removing,
reordering, or replacing declarations while open follows CMenu's exact
settlement and focus recovery. If no valid actionable items remain, the Menu
fails closed; it never makes the primary unavailable automatically.

## 14. Server render, morph, and cleanup

Server output includes the useful primary native Button, a non-submitting Menu
Button, stable Menu surface markup, and all relationships. Initialization
validates the exact two-Button anatomy, declaration output, owned attributes,
anchor identity, native types, and current ancestry before opening or moving
focus. Invalid structure fails closed and reports a bounded error; it does not
submit from the Menu Button or show an unowned surface.

Correlated morph handoff preserves one retained root record, committed Menu
state, controlled ownership, active item/path, primary focus/loading guard,
and valid native form owner. It refreshes element references, anchor identity,
inside-element membership, declaration registry, disabled fieldset ancestry,
and computed configuration before reconciling the latest owner input once.
Uncorrelated replacement disposes the old root before a new root initializes.

Mutation validation observes only while needed and batches correlated output.
It repairs owned IDs, ARIA, Menu Button `type=button`, disabled/loading
semantics, part/reflection attributes, anchor styles, and popover attributes.
Content mutations re-run the same primary/declaration/settled validators.
Invalidity force-closes an open Menu, blocks primary activation only when the
primary itself is unsafe, and recovers after valid settlement plus a new open
edge. Recovery sends no synthetic primary action or duplicate callback.

Cleanup force-closes descendant submenus, unregisters the root layer, hides
the native popover, removes Button/Menu listeners and reactive effects,
disconnects mutation/fieldset observers, cancels timers/animation frames and
queued generation work, removes temporary focus attributes, and releases all
node references. Repeated initialization is idempotent. Removal of the last
instance leaves no document, ShadowRoot, observer, timer, animation, or
registry entry.

### Private reuse and forwarding feasibility

Implementation has one required private refactor and no public prerequisite:

1. Extract CMenu's existing root setup into one private Menu-root controller
   and one private server surface/collection builder. They accept the root
   configuration record, semantic trigger, positioning anchor, surface,
   inside-elements list, callback getters, a `disabledFocusTarget()` resolver,
   a committed-open reflection sink, and the existing declaration registry.
   The controller returns one synchronous `requestActionClose(source)` handle
   bound to its current generation. `CMenu` and `CSplitButton` both call these
   helpers. CMenu passes a resolver that returns `null`; SplitButton returns its
   connected, rendered, effectively enabled primary Button or `null`.
2. Keep all root Menu state transitions, collection code, submenus, callbacks,
   validators, layer registration, assets, and cleanup in those helpers. There
   is one JavaScript source/dependency and one behavior owner.
3. Render SplitButton's two native Buttons through private CButton rendering
   and activation helpers shared with CButton. SplitButton owns the compound
   configuration record; it does not mount nested public CButton components
   whose `$c-props` would become separate owners.
4. Do not instantiate public `CButtonGroup`. Reuse its group semantics and
   joined-layout rules against SplitButton's immediate native children.
5. Preserve public CMenu declarations unchanged. The SplitButton `menu` slot
   establishes the same private declaration context and uses the same
   collection builder, so no declaration forwarding or duplicate component
   class exists.
6. Move the current CButton theme rules and current CMenu theme rules from
   component-class-owned `Style` content into private deduplicated Style
   dependencies. CButton/CMenu continue to depend on those assets and retain
   byte-equivalent public styling. CSplitButton depends on the same assets plus
   its compound Style. Shared private selectors accept an exact part-name map
   so CButton and SplitButton can keep distinct public parts without copying
   declarations.

`requestActionClose(source)` runs the controller's ordinary controlled or
uncontrolled CMenu request synchronously and at most once for the current
native activation. The committed-open sink receives every logical root change
after commit and removes/sets SplitButton root `data-open`; requested but
refused controlled state never reaches it. Disabled focus recovery asks the
resolver only after hiding/inerting the tree, verifies focus success, and then
falls through to the existing modal/body policy. These hooks add policy inputs
to one controller; they do not fork its state machine.

The implementation gate is falsifiable: if the extracted Menu controller
cannot mount both CMenu's activator anatomy and SplitButton's distinct
trigger/anchor anatomy while the entire CMenu test suite remains unchanged,
the action-close handle cannot notify synchronously once, the committed mirror
or enabled-primary focus target is wrong, a SplitButton-only page lacks current
Button/Menu styling, coexistence emits duplicate Style/Script content, or
retained-resource counts do not return to baseline, SplitButton runtime work
stops. Copying Menu JavaScript/CSS or nesting CMenu behind reactive forwarding
is not an allowed fallback.

## 15. Security and content trust

All mappings require `Mapping[str, object]`, use string keys, reject duplicate
case variants, are copied, and are validated case-insensitively by exact
destination. The allowed common static grammar is `class`, `style`, `lang`,
`dir`, `title`, `translate`, `spellcheck`, permitted destination ARIA listed
below, and `data-*` except `data-citry-*`, `data-cev*`, `data-cid*`, and the
destination's owned reflections. Primary alone also permits the native form
attributes listed below. `@event` and `x-on:event` Alpine listeners are
allowed. Raw `on*` browser-expression attributes are rejected.

The exact ownership directives rejected everywhere are `x-data`, `x-init`,
`x-effect`, `x-if`, `x-for`, `x-teleport`, `x-ignore`, `x-id`, `x-show`,
`x-html`, `x-text`, `x-model`, `x-modelable`, bare `x-bind`, `$c-props`, and
Citry `c-bind`/`c-props` ownership forms. `x-bind:name`, `:name`, and `.name`
are allowed only when `name` is permitted for that destination; a target in
the corresponding reserved set is rejected. Modifiers do not change the
target. `is` is reserved on the root and every descendant destination, so
customized built-ins cannot be introduced statically or dynamically.

Destination rules and reserved sets are exact:

| Destination | Additional allowed names | Case-insensitive reserved names |
|---|---|---|
| root `attrs` | `aria-describedby`, `aria-details`, `aria-keyshortcuts` | `id`, `is`, `role`, `aria-label`, `aria-labelledby`, `aria-controls`, `aria-expanded`, `aria-disabled`, `aria-busy`, `tabindex`, `autofocus`, `hidden`, `inert`, `contenteditable`, `popover`, `popovertarget`, `popovertargetaction`, `command`, `commandfor`, `disabled`, `href`, `type`, `form`, `formaction`, `formenctype`, `formmethod`, `formnovalidate`, `formtarget`, `name`, `value`, every `data-citry-*`, `data-disabled`, `data-primary-disabled`, `data-menu-disabled`, `data-loading`, `data-loading-position`, `data-open`, `data-variant`, `data-intent`, `data-size`, `data-block`, `data-citry-ui-part` |
| `primary_attrs` | `aria-label`, `aria-labelledby`, `aria-describedby`, `aria-details`, `aria-keyshortcuts`, `form`, `formaction`, `formenctype`, `formmethod`, `formnovalidate`, `formtarget`, `name`, `value` | `id`, `is`, `type`, `disabled`, `href`, `role`, `aria-busy`, `aria-disabled`, `aria-hidden`, `aria-haspopup`, `aria-controls`, `aria-expanded`, `aria-pressed`, `tabindex`, `autofocus`, `hidden`, `inert`, `contenteditable`, `popover`, `popovertarget`, `popovertargetaction`, `command`, `commandfor`, every `data-citry-*`, `data-disabled`, `data-loading`, `data-loading-position`, `data-variant`, `data-intent`, `data-size`, `data-citry-ui-part` |
| `trigger_attrs` | `aria-describedby`, `aria-details`, `aria-keyshortcuts` | `id`, `is`, `type`, `disabled`, `href`, `role`, `aria-label`, `aria-labelledby`, `aria-busy`, `aria-disabled`, `aria-hidden`, `aria-haspopup`, `aria-controls`, `aria-expanded`, `aria-pressed`, `tabindex`, `autofocus`, `hidden`, `inert`, `contenteditable`, `popover`, `popovertarget`, `popovertargetaction`, `command`, `commandfor`, `form`, `formaction`, `formenctype`, `formmethod`, `formnovalidate`, `formtarget`, `name`, `value`, every `data-citry-*`, `data-disabled`, `data-variant`, `data-intent`, `data-size`, `data-citry-ui-part` |
| `menu_attrs` | `aria-describedby`, `aria-details`, `aria-keyshortcuts` | `id`, `is`, `role`, `aria-label`, `aria-labelledby`, `aria-roledescription`, `aria-hidden`, `tabindex`, `autofocus`, `hidden`, `inert`, `contenteditable`, `popover`, `popovertarget`, `popovertargetaction`, `command`, `commandfor`, `disabled`, `href`, `type`, `form`, `formaction`, `formenctype`, `formmethod`, `formnovalidate`, `formtarget`, `name`, `value`, every `data-citry-*`, `data-open`, `data-placement`, `data-match-width`, `data-size`, `data-citry-ui-part` |

`tabindex` is reserved unconditionally on both Buttons. This protects the
documented two-stop order across later reactive disabled/loading changes;
consumers cannot make either half an extra, missing, or reordered Tab stop.
Presence, naming, disabledness, busy state, and editability are likewise
component-owned for the entire lifetime, not conditionally reserved only while
a state happens to be active.

Class and style values merge only through direct `class_`/`style` and the
ordinary allowed mapping rules. Generated anchor ownership merges last and
cannot be replaced by consumer style. URL-like native form action destinations
remain consumer-owned and are not trusted by Citry.

Primary content uses normal escaping. Trusted HTML is an explicit application
decision but still must pass the settled noninteractive validator. Menu
declaration content uses CMenu's exact trust boundary. Unsafe or spoofed roots,
interactive authored descendants, duplicate semantic roles, raw popovers or
dialogs, unresolved custom elements, and detectable authored shadow hosts fail
closed rather than becoming extra activation surfaces.

## 16. Assets and performance

The family adds one SplitButton CSS asset and a thin compound initializer. It
reuses and deduplicates the existing CButton initializer/helpers, CMenu root
runtime, CMenu CSS, declarations, and anchored-layer dependency. It adds no
icon network request, font, external package, per-instance document listener,
scroll listener, resize loop, or coordinate-writing engine. The chevron is CSS
or the existing bundled icon primitive and is hidden from accessibility.

Asset evidence records raw, gzip, and Brotli size for the incremental family
and verifies one copy of every shared dependency for 1, 10, and 100 instances.
The target is less than 3 KiB gzip incremental JavaScript and less than 2 KiB
gzip incremental CSS after shared Button/Menu assets. A page with only
CSplitButton must not emit a second textual copy of CMenu's state machine.

Closed instances retain no document/ShadowRoot listener or observer beyond the
bounded per-root reactive/mutation work already required for integrity. Open
instances share one coordinator scope listener/observer set. One hundred
closed instances, repeated open/close, correlated morph, and full removal must
return anchored-layer, observer, listener, timer, and component counters to
their recorded baseline.

## 17. Acceptance matrix

Automated evidence is required before release:

| Area | Required proof and falsifier |
|---|---|
| schema and exports | exact `Kwargs`, six family exports, existing alias reuse, template and Python composition, missing/empty menu label/content/Menu errors, exact declaration acceptance |
| anatomy | one group, two immediate native Buttons, Menu Button always `type=button`, exact IDs/ARIA/parts/reflections, Menu surface identical to CMenu |
| native primary | click, Enter, Space, submit, reset, name/value FormData, `SubmitEvent.submitter`, external `form`, submit overrides, `requestSubmit`, disabled and loading guards |
| no accidental submit | Menu Button, Menu item Buttons, submenu triggers, malformed/morphed type repair, Enter/Space/Arrow activation never submit |
| state ownership | uncontrolled open/close, controlled accept/refuse/release, same-value commits, forced disabled/fieldset/ancestor/modal close, re-enable, suppression/new-edge behavior |
| primary while open | synchronous capture `action` close before native handlers/default action, no outside duplicate, native action proceeds after controlled refusal, accepted close gets no later duplicate, refused close plus later modal reports one distinct forced ancestor transition |
| disabled/loading | common and each per-half combination, native fieldset changes/moves, loading focus retention, available Menu during primary loading, verified focus fallback on Menu disable |
| keyboard/focus | native two-stop Tab order, primary no arrow behavior, Menu Button open keys, complete CMenu root/submenu/typeahead keys, Escape, Tab out, focus restoration and refusal repair |
| collection | every existing CMenu declaration/slot/callback, choices, links, duplicate/invalid structures, settled invalidity/recovery, correlated reorder/removal/path recovery |
| layering | full-root anchor, `bottom-end`, all placements, root-width matching, overflow escape, nested layers, ShadowRoot, modal eligibility, sibling Dialog from primary/item callback, RTL collision |
| styling | all variants/intents/sizes/loading positions, Button variables on both halves, compound variables/parts, full CMenu variables/parts, root/ancestor overrides and reflection changes |
| environments | light/dark/nested dynamic scheme, two brands, RTL, narrow and long label, 320 px, 400% zoom, reduced motion, forced colors, print, coarse pointer, no page overflow |
| accessibility | separate primary/Menu Button names, group and Menu relationships, busy/disabled states, target size, axe, browser AX snapshots, VoiceOver/NVDA manual record |
| trust | every destination allowlist/reserved attr/static and dynamic alias, namespace/directive rejection, `is`, unsafe slot descendants, spoofed declaration roots, mutation recovery |
| SSR/lifecycle | no-JS primary/form utility and Menu fallback, delayed init, repeat init, fragment insertion, morph handoff/replacement, removal while open/loading, zero retained resources |
| reuse/performance | full existing CButton/CButtonGroup/CMenu suites stay green; one Menu runtime and anchored dependency in output; incremental asset budgets and 1/10/100 instance timing |

Focused cross-browser evidence runs in current Chromium, Firefox, and WebKit.
Family tests must include open-ShadowRoot and native Dialog compositions, not
only light-DOM happy paths. Browser console output is an assertion surface:
expected invalidity produces one bounded Citry error; supported paths produce
no uncaught exception, warning, invalid-form-focus error, duplicate callback,
or unhandled rejection.

Manual evidence covers keyboard-only use, VoiceOver/Safari, NVDA/Firefox,
touch, forced colors, 400% zoom, long translation, visual hierarchy, and
primary-versus-related-action comprehension. Release evidence records exact
browser versions and current official-source versions.

## 18. Compatibility classification

Stable public API includes the component and six schema exports, all server
and client input names/types/defaults, slot names/data records, existing CMenu
declaration acceptance, callback types/reasons/order, native-event policy,
form behavior, controlled release, disabled/loading precedence, parts,
variables, reflections, attribute destinations/validation, and errors.

Stable behavioral/structural contracts include two immediate native Buttons,
Menu Button `type=button`, semantic trigger versus full-root anchor, two Tab
stops, primary action deduplication, exact CMenu state/collection/layer model,
useful server output, logical RTL order, focus rules, no accidental submission,
and shared-runtime rather than copied-runtime behavior.

Evolvable design includes exact colors, shadows, radius/spacing defaults,
chevron drawing, spinner drawing, animation curves, private classes, private
helper names, private data records, and internal JavaScript organization. A
private refactor may change file boundaries but may not fork behavior or alter
CMenu's existing public output.

Removing a server/client input, slot, declaration, callback field/reason,
public selector/variable/reflection, native form capability, or accepted
composition is breaking. Adding a Menu declaration kind or CMenu callback
reason automatically becomes available only after SplitButton evidence proves
the reused path; publication must update both references in one release.

## 19. Public documentation contract

After design and runtime gates pass, component-owned `api.md` and exhaustive
`api.yml` must teach the family as one dominant action plus a related existing
Menu, not as a generic dropdown. Both show template and direct Python
composition before reactive control. They link CButton, CButtonGroup, CMenu,
APG Menu Button guidance, and the native Button no-JavaScript path.

The public example catalog is required in this order:

| Order and module | Reader task and evidence |
|---|---|
| 1. `at_a_glance.py` | visible dominant Save action plus related alternatives; separate names and no repeated dominant item |
| 2. `basic_actions.py` | minimal template and Python composition with existing `CMenuItem` declarations and native click evidence |
| 3. `forms.py` | submit/reset/name/value/external form behavior; prove Menu Button and items never submit |
| 4. `controlled_menu.py` | accept, refuse, and release controlled `open`; display owner and committed state |
| 5. `variants_and_sizes.py` | external controls update variant, intent, size, block, placement, width matching, and reflections |
| 6. `disabled_and_loading.py` | common/per-half disabled, fieldset, focus-retaining primary loading, Menu remains useful |
| 7. `menu_composition.py` | groups, separators, choices, valued commands, links, and nested submenu through existing declarations |
| 8. `focus_and_keyboard.py` | two Tab stops, primary native keys, Menu Button arrow keys, Escape/Tab and focus restoration |
| 9. `layers_and_dialog.py` | SplitButton in overflow, open ShadowRoot, and modal; primary/item opens a sibling controlled Dialog |
| 10. `customization.py` | Button/Menu/compound variables and stable selectors across two brands, dark nested scheme, RTL, long label, narrow width |

Reader prose must state:

- the primary action should not be repeated in the Menu;
- `menu_label` must name the secondary purpose explicitly;
- `loading` affects only the primary; use `disabled` to disable the whole;
- primary native events are distinct from Menu `onAction` callbacks;
- `open` omission releases to the committed state, which may differ from the
  last visible controlled state;
- `match_width` and placement use the full group;
- Menu declarations, callbacks, parts, and limits are CMenu's existing public
  contract; and
- compose CButtonGroup/CMenu when the primary must be a link, the actions are
  peers, vertical layout is needed, or different ownership is required.

The quality scenario includes primary submit/reset continuity, Menu controlled
state, nested Menu, open layer, both brands in light/dark, RTL/narrow/long
content, forced colors, reduced motion, zoom, and repeated morph/removal. Asset,
scaling, registration, docs catalog, visual, accessibility, and focused browser
integrations are implementation-stage work and are deliberately not edited by
this design phase.

## 20. Open decisions and deferred work

No product or public API decision remains open for implementation.

The private controller extraction in section 14 is a mandatory implementation
gate, not a license to redesign Menu. Independent review must specifically try
to falsify reactive forwarding, distinct trigger/anchor geometry, primary
action deduplication, controlled refusal, native form behavior, focus fallback,
attribute ownership, declaration reuse, and one-runtime output before this
document is marked ratified.

Deferred from the first release:

- dominant link/router actions;
- vertical SplitButtons;
- Menu-driven replacement of the dominant action;
- repeating the selected Menu action as the primary action;
- long-press or Alt+Arrow hidden Menu activation;
- public open/close/focus methods or custom DOM events;
- configurable indicator slots, arbitrary activator slots, item-model input,
  portals/teleports, virtual anchors, arrows, delays, scrims, offsets, and local
  z-index controls; and
- responsive collapse into a single Menu Button.

These are omitted because they change semantics or ownership, not because the
private runtime lacks hooks. Any future addition needs its own evidence and
compatibility review. Until the mandatory extraction preserves all existing
CMenu and CButton behavior and the section 17 matrix passes, runtime release is
blocked. The design itself is frozen for independent adversarial review.
