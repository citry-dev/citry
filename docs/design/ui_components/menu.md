# Menu component family

**Status (2026-08-09): production implementation and independent
implementation review complete. The eight-class runtime/export family,
structured API, thirteen public previews, focused server and
Chromium/Firefox/WebKit evidence, real correlated-rerender coverage, shared
anchored-layer integration, quality/scaling routes, docs projection, and exact
wheel qualification are checked in. Human visual and assistive-technology
review, hosted Nu evidence, and released-artifact qualification remain.**

## 1. Purpose and product bar

`CMenu` presents a temporary application-command collection from one Button.
It covers commands, navigation links, grouped commands, separators, checkable
and radio choices, and nested command submenus. It follows the WAI-ARIA Menu
Button and Menu patterns and ships styled, keyboard-complete, pointer-complete,
touch-safe, RTL-aware output.

Menu is not a generic dropdown container. Use `CPopover` for forms, arbitrary
controls, settings panels, or explanatory rich content; `CCombobox` for
filtering; `CList` for persistent navigation; and a later dedicated family for
menubars or context menus.

Common jobs and shortest supported paths:

| Job | Shortest path | Classification |
|---|---|---|
| Open commands from a Button | `CMenu` + `CMenuItem` | direct API |
| Navigate to another URL | `CMenuItem(href=...)` | native anchor through direct API |
| Show icons, shortcuts, and descriptions | item `start`, `end`, and `description` slots | composition |
| Group related commands | `CMenuGroup` | direct API |
| Divide unrelated commands | `CMenuSeparator` | direct API |
| Toggle an application preference | `CMenuCheckboxItem` | direct API |
| Choose one application mode | `CMenuRadioGroup` + `CMenuRadioItem` | direct API |
| Open nested command families | `CMenuSubmenu` | direct API |
| Add arbitrary classes or styles | `class_`, `style`, and allowed `attrs` | CSS or utilities |
| Place a search field or Form in a flyout | `CPopover` or `CCombobox` | separate component |

The common command path stays concise:

```django
<c-CMenu>
  <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
    <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Open menu</c-CButton>
  </c-fill>
  <c-fill name="default">
    <c-CMenuItem value="rename">Rename</c-CMenuItem>
    <c-CMenuItem value="duplicate">Duplicate</c-CMenuItem>
    <c-CMenuSeparator />
    <c-CMenuItem value="delete" intent="danger">Delete</c-CMenuItem>
  </c-fill>
</c-CMenu>
```

```python
CMenu(
    slots={
        "activator": lambda data: CButton(
            "Open menu",
            disabled=data.activator_disabled,
            attrs=data.activator_attrs,
        ),
        "default": lambda: (
            CMenuItem("Rename", value="rename"),
            CMenuItem("Duplicate", value="duplicate"),
            CMenuSeparator(),
            CMenuItem("Delete", value="delete", intent="danger"),
        ),
    },
)
```

Non-goals for this family are arbitrary interactive descendants, searchable
content, a generic records-to-items mapping, point/context triggers, hover-only
root opening, split buttons, multiple activators, virtualization, menubars,
public collision middleware, and imperative open/close methods. There is no
headless variant.

## 2. Prior art and complaints

Sources reviewed on 2026-08-09:

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---:|---|---|
| [WAI-ARIA Menu Button](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/) and [Menu/Menubar](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/) | living, 2026-08-09 | patterns and examples | semantic roles, focus entry, navigation, typeahead, Tab, Escape, disabled and submenu behavior |
| [WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria/) | 1.2 | menu, menuitem, checkbox, radio, group, separator roles | exact semantic ownership |
| [HTML Popover](https://html.spec.whatwg.org/multipage/popover.html) | living, 2026-08-09 | manual-popover ancestry algorithms | native manual popovers do not provide the required submenu close cascade |
| Vuetify `VMenu`, `VList`, and `VListItem` source | 4.1.8 | public props, slots, nesting, density, links, close behavior | primary styled-suite reference; concise activator, decoration, link, size, nested-menu, and close-after-action paths |
| [React Aria Menu](https://react-aria.adobe.com/Menu) | 1.20.0 | collection, selection, sections, submenus, disabled, typeahead | strict item content, complex labels, direct focus, choice items, link behavior |
| [Radix Dropdown Menu](https://www.radix-ui.com/primitives/docs/components/dropdown-menu) | 2.1.21 | anatomy, groups, choices, submenus, typeahead, collision | compound family and submenu geometry evidence |
| [Ark Menu](https://ark-ui.com/docs/components/menu) and [Zag Menu](https://zagjs.com/components/menu) | 5.38.1 / 1.43.0 | state machine, values, positioning, links, submenus | controlled-state and exactly-once callback pressure |
| [Mantine Menu](https://mantine.dev/core/menu/) | 9.5.1 | actions, links, danger, choices, submenu safe area | practical styled API and rejection of hover-only roots |
| [MUI Menu](https://mui.com/material-ui/react-menu/) | 9.3.1 | focus, selected item, dense mode, close reasons | focus and close vocabulary; cascading gaps |
| [Web Awesome Dropdown](https://webawesome.com/docs/components/dropdown) | 3.11.0 | Web Component items, choices, submenus, placement, parts | browser-native comparison and public styling surfaces |
| [Bootstrap Dropdown](https://getbootstrap.com/docs/5.3/components/dropdowns/) | 5.3.8 | arbitrary-content dropdown and keyboard boundary | evidence that generic dropdown content must not claim ARIA Menu semantics |

Material complaints become explicit acceptance cases:

- Radix issue 4036: a collision-flipped submenu used stale direction for its
  pointer grace area. Citry derives the safe corridor from current rectangles.
- MUI issue 11723: ad hoc cascading menus exhibit focus jumps, duplicate
  outside dismissal, incomplete keyboard traversal, and submenu scrollbar
  problems. Citry owns one logical tree.
- React Aria issue 8675: Shadow DOM ownership could close before the action.
  Citry tests retained ancestry and the action-before-close sequence.
- Ark/Zag release history includes duplicate checkbox/radio notifications,
  stale geometry, diagonal submenu flashes, and duplicate link activation.
  Citry locks exactly-once behavior and current geometry.
- Mantine warns that hover-only opening excludes keyboard users. Citry does not
  expose it.

Disposable Chromium 151, Firefox 153, and WebKit 26.5 probes confirmed that
hiding a parent manual Popover or closing a containing Dialog leaves a nested
manual Popover open. Native DOM ancestry is therefore not a Menu close tree.
The same engines accepted `position-area: inline-end span-block-end`, flipped
the submenu to inline-start at a narrow physical edge, and reversed the
unflipped logical side under RTL. Inline submenu anchoring is therefore a
proven platform input; Citry still derives pointer intent from settled
rectangles rather than assuming the requested side won.
They also placed an explicitly selected `position-area: block-end` submenu
below and centered on its trigger without viewport overflow. This supplies the
overlap fallback when neither inline corridor is usable.

Vuetify disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| activator slot and attributes | direct API | `CMenu.activator` + `activator_attrs` + `activator_disabled` | adopt |
| controlled visibility | direct API | server/client `open`, `onOpenChange` | adopt with nullable release |
| nested menus | direct API | `CMenuSubmenu` | adopt with one logical tree and safe corridor |
| links | direct API | `CMenuItem.href` | adopt native anchor behavior |
| prepend/append/title/subtitle | composition | `start`, default, `description`, `end` slots | adopt clearer vocabulary |
| density | direct API | `size="sm" | "md" | "lg"` | align with Citry vocabulary |
| close on content | direct API | root/item `close_on_select` | adopt for semantic items only |
| open/close delays | private behavior | fixed reviewed submenu timing | omit public tuning until a user job requires it |
| hover root opening | omitted | - | reject as inaccessible root default |
| absolute/attach/location strategy/offset/origin/scrim | private overlay foundation | logical placement and public CSS variables | do not inherit generic Overlay breadth |
| eager/transition/raw dimensions | CSS/composition | variables, `class_`, `style`, `attrs` | capability without prop parity |
| activator-parent and custom target modes | separate future trigger work | - | defer |

Citry adopts native buttons/anchors, direct focus, typeahead, groups, choices,
submenus, a concise size and danger surface, and reactive root visibility. It
rejects arbitrary content and a generic Overlay API. It must prove logical
close cascading, collision-aware pointer intent, exactly-once activation,
ShadowRoot behavior, and controlled focus recovery.

## 3. Public composition and anatomy

```text
CMenu host (private, display: contents)
├─ caller Button from activator slot
└─ menu surface [role=menu][popover=manual]
   ├─ CMenuItem [button|a, role=menuitem]
   ├─ CMenuCheckboxItem [button, role=menuitemcheckbox]
   ├─ CMenuRadioGroup [div, role=group]
   │  └─ CMenuRadioItem [button, role=menuitemradio]
   ├─ CMenuGroup [div, role=group]
   │  └─ direct menu family declarations
   ├─ CMenuSeparator [hr, role=separator]
   └─ CMenuSubmenu [div, role=none]
      ├─ trigger [button, role=menuitem]
      └─ submenu surface [div, role=menu][popover=manual]
         └─ direct menu family declarations
```

The submenu surface immediately follows its trigger. Generic group and radio
group children are permitted ARIA ownership intermediates. No other wrapper
may appear between a Menu and its item roles.

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CMenu` | `div[role=menu]` | `class_`, `style`, `attrs` land on the surface | exactly one native Button activator; nonempty collection |
| `CMenuItem` | `button` or `a` with `role=menuitem` | root | direct child of Menu or `CMenuGroup` |
| `CMenuCheckboxItem` | `button[role=menuitemcheckbox]` | root | direct child of Menu or `CMenuGroup` |
| `CMenuRadioGroup` | `div[role=group]` | root | direct child of Menu or `CMenuGroup`; one or more direct radio items |
| `CMenuRadioItem` | `button[role=menuitemradio]` | root | direct child of one radio group |
| `CMenuGroup` | `div[role=group]` | root | required visible label and nonempty direct collection |
| `CMenuSeparator` | `hr[role=separator]` | root | between actionable siblings |
| `CMenuSubmenu` | `div[role=none]` | `class_`, `style`, `attrs` land on the wrapper; `trigger_attrs` and `menu_attrs` have explicit destinations | direct collection child; trigger immediately followed by nonempty submenu |

The activator must resolve to exactly one native `HTMLButtonElement`.
`activator_attrs` owns anchor identity, `aria-haspopup`, `aria-controls`, and
`aria-expanded`; `activator_disabled` carries the server-owned disabled input
without crossing CButton's attribute boundary. Native Buttons still set
`type=button` directly. Effective activator disabledness is Menu
configuration OR native `trigger.matches(":disabled")`; native disabled
`fieldset` ancestry is supported, reflected, and observed rather than treated
as invalid composition. The Menu configuration owns the activator's direct
`disabled` input; consumers use `CMenu.disabled` rather than a competing Button
configuration.

Item values are canonical within their current menu level. Non-`None` command
values and choice values cannot collide at one level. Radio values are unique
within their group. Values normalize CRLF/CR to LF and reject U+0000.
Every supplied command/submenu/choice identity is nonempty after
canonicalization. A supplied `CMenu.id` is nonempty and contains neither ASCII
whitespace nor U+0000 so every generated IDREF remains valid.

Leading, trailing, or consecutive separators, empty groups, empty radio
groups, empty submenus, bare nested items, nested generic groups, misplaced
radio items, arbitrary HTML among declarations, and duplicate values raise at
server render. Transparent Citry components that add no HTML remain allowed.

Every item removes the ambient Menu declaration context while rendering its
visible content. Item slots never accept any Menu declaration. `CMenuSubmenu`
must itself be a direct declaration of the current Menu or `CMenuGroup`; only
its own `default` slot establishes the nested collection. Settled browser
validation rejects links, buttons, controls, editable content, focusable
descendants, and nested menuitem roles inside item label/decorative regions.
`CMenuGroup.label` and `CMenuRadioGroup.label` follow the same noninteractive
phrasing-content rule. Both label outlets remove the declaration context and
settled validation rejects controls, links, editable/focusable descendants,
and Menu declarations there.

## 4. Server inputs and client inputs

`CMenu` server inputs:

| Input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `id` | `str | None` | generated | structural | stable surface and relationship identity |
| `open` | `bool` | `False` | initial value | initial visibility and uncontrolled fallback |
| `disabled` | `bool` | `False` | reactive configuration | disables the activator and forcibly closes the tree |
| `loop` | `bool` | `True` | reactive configuration | wraps arrow navigation and typeahead search |
| `placement` | `CMenuPlacement` | `"bottom-start"` | reactive configuration | preferred logical root placement |
| `match_width` | `bool` | `False` | reactive configuration | matches the activator width up to the viewport-safe maximum |
| `close_on_select` | `bool` | `True` | reactive configuration | default close policy for actionable items |
| `size` | `CMenuSize` | `"md"` | reactive configuration | `sm`, `md`, or `lg` item geometry |
| `class_` | `CClassValue | None` | `None` | structural | surface classes |
| `style` | `CStyleValue | None` | `None` | structural | surface styles; generated anchor ownership merges last |
| `attrs` | `Mapping[str, object] | None` | `None` | structural | allowed surface attributes |

`CMenuItem` server inputs:

| Input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `value` | `str | None` | `None` | structural identity | optional canonical command callback identity; rejected with `href` |
| `href` | `str | None` | `None` | structural | trusted URL; selects anchor instead of Button root |
| `disabled` | `bool` | `False` | reactive configuration | focusable `aria-disabled` activation guard |
| `close_on_select` | `bool | None` | `None` | reactive configuration | item override; `None` inherits root policy |
| `intent` | `CMenuIntent` | `"default"` | reactive configuration | default or danger reflection/styling |
| `text_value` | `str | None` | `None` | reactive configuration | explicit typeahead text; `None` reads current label text |
| `class_` / `style` | `CClassValue | None` / `CStyleValue | None` | `None` | structural | semantic root customization |
| `attrs` | `Mapping[str, object] | None` | `None` | structural | allowed semantic-root native/ARIA/Alpine/data attrs |

Supplying `href` selects the anchor root; omitting it selects
`button[type=button]`. `value` with `href` is rejected because links preserve
native navigation and do not emit the command callback; an accepted value must
have an observable action identity.

`CMenuCheckboxItem` server inputs:

| Input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `value` | `str` | required | structural identity | nonempty canonical value unique at this menu level |
| `checked` | `CMenuChecked` | `False` | initial value | false, true, or mixed ownership fallback |
| `disabled` | `bool` | `False` | reactive configuration | focusable inactive item |
| `close_on_select` | `bool | None` | `None` | reactive configuration | item/root close policy |
| `text_value` | `str | None` | `None` | reactive configuration | explicit or current-label typeahead text |
| `class_` / `style` | `CClassValue | None` / `CStyleValue | None` | `None` | structural | semantic root customization |
| `attrs` | `Mapping[str, object] | None` | `None` | structural | allowed semantic-root attrs |

`CMenuRadioGroup` server inputs:

| Input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `value` | `str` | required | initial value | must identify one direct radio item |
| `class_` / `style` | `CClassValue | None` / `CStyleValue | None` | `None` | structural | group root customization |
| `attrs` | `Mapping[str, object] | None` | `None` | structural | allowed group attrs |

`CMenuRadioItem` server inputs:

| Input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `value` | `str` | required | structural identity | nonempty canonical value unique in its radio group |
| `disabled` | `bool` | `False` | reactive configuration | focusable inactive item |
| `close_on_select` | `bool | None` | `None` | reactive configuration | item/root close policy |
| `text_value` | `str | None` | `None` | reactive configuration | explicit or current-label typeahead text |
| `class_` / `style` | `CClassValue | None` / `CStyleValue | None` | `None` | structural | semantic root customization |
| `attrs` | `Mapping[str, object] | None` | `None` | structural | allowed semantic-root attrs |

`CMenuGroup` and `CMenuSeparator` each expose structural `class_:
CClassValue | None`, `style: CStyleValue | None`, and `attrs: Mapping[str,
object] | None`, all defaulting to `None` and landing on their documented root.

`CMenuSubmenu` server inputs:

| Input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `value` | `str` | required | structural identity | canonical path segment unique at its menu level |
| `disabled` | `bool` | `False` | reactive configuration | focusable inactive trigger and forced child close |
| `intent` | `CMenuIntent` | `"default"` | reactive configuration | default or danger trigger styling |
| `text_value` | `str | None` | `None` | reactive configuration | explicit or current-label typeahead text |
| `class_` / `style` | `CClassValue | None` / `CStyleValue | None` | `None` | structural | neutral submenu wrapper customization |
| `attrs` | `Mapping[str, object] | None` | `None` | structural | allowed neutral-wrapper attrs |
| `trigger_attrs` | `Mapping[str, object] | None` | `None` | structural | allowed submenu-trigger attrs |
| `menu_attrs` | `Mapping[str, object] | None` | `None` | structural | allowed nested Menu-surface attrs |

Submenu openness and timing remain private in the first contract.

Public aliases are exact:

```python
CMenuPlacement = Literal[
    "top-start", "top", "top-end",
    "bottom-start", "bottom", "bottom-end",
]
CMenuSize = Literal["sm", "md", "lg"]
CMenuIntent = Literal["default", "danger"]
CMenuChecked = bool | Literal["mixed"]
```

Client inputs:

| Owner | Input | Type | Omitted / `null` | Invalid | Effect |
|---|---|---|---|---|---|
| `CMenu` | `open` | `boolean | null` | releases control from the committed state | reports once and releases | controls root visibility |
| `CMenu` | `disabled` | `boolean` | server fallback | reports once, uses fallback | activator and forced tree close |
| `CMenu` | `loop` | `boolean` | server fallback | reports once, uses fallback | keyboard wrapping |
| `CMenu` | `placement` | `CMenuPlacement` | server fallback | reports once, uses fallback | preferred root placement |
| `CMenu` | `matchWidth` | `boolean` | server fallback | reports once, uses fallback | root width matching |
| `CMenu` | `closeOnSelect` | `boolean` | server fallback | reports once, uses fallback | default selection close policy |
| `CMenu` | `size` | `CMenuSize` | server fallback | reports once, uses fallback | geometry mirror |
| `CMenu` | `onOpenChange` | `function` | no component callback | reports once, uses no callback | visibility requests and forced-close notices |
| `CMenu` | `onAction` | `function` | no component callback | reports once, uses no callback | enabled valued-command/choice actions |
| `CMenuItem` | `disabled` | `boolean` | server fallback | reports once, uses fallback | activation guard and ARIA |
| `CMenuItem` | `closeOnSelect` | `boolean | null` | root fallback | reports once, uses fallback | per-item close override |
| `CMenuItem` | `intent` | `CMenuIntent` | server fallback | reports once, uses fallback | `data-intent` and styling |
| `CMenuItem` | `textValue` | `string | null` | server fallback | reports once, uses fallback | typeahead source; `null` fallback may still resolve to current label |
| `CMenuCheckboxItem` | `checked` | `boolean | "mixed" | null` | releases control from committed value | reports once and releases | check state ownership |
| `CMenuCheckboxItem` | `disabled` / `closeOnSelect` / `textValue` | as above | as above | as above | item behavior |
| `CMenuCheckboxItem` | `onCheckedChange` | `function` | no component callback | reports once, uses no callback | checked-value requests |
| `CMenuRadioGroup` | `value` | `string | null` | releases control from committed value | reports once and retains last valid value | radio selection ownership |
| `CMenuRadioGroup` | `onValueChange` | `function` | no component callback | reports once, uses no callback | activation/removal value requests |
| `CMenuRadioItem` | `disabled` / `closeOnSelect` / `textValue` | as above | as above | as above | item behavior |
| `CMenuSubmenu` | `disabled` | `boolean` | server fallback | reports once, uses fallback | trigger behavior and forced child close |
| `CMenuSubmenu` | `intent` | `CMenuIntent` | server fallback | reports once, uses fallback | trigger reflection and styling |
| `CMenuSubmenu` | `textValue` | `string | null` | server fallback | reports once, uses fallback | trigger typeahead source |

All client strings use the same canonicalizer as Python. A valid client value
wins over the server fallback. Omission or `null` releases only controlled
state; configuration returns to its server fallback. One invalid episode ends
only after a valid value or omission.

## 5. State model

The root tracks logical `closed | opening | open | closing`, committed open,
optional client control, active item identity, layer generation, pending focus
destination, and one descendant submenu chain. A submenu tracks the same
presence phases without public control.

| Request | Guard | Uncontrolled result | Controlled result | Focus |
|---|---|---|---|---|
| trigger activation | enabled | toggles root | notifies only | first item when accepted open; trigger when accepted close and focus still belongs to tree |
| external `open=true` | enabled | n/a | opens | first item after registration |
| Escape in root | open | closes | notifies | trigger when accepted |
| Escape in submenu | child open | closes deepest child | n/a | parent submenu trigger |
| outside pointer/focus | tree open | closes full root | root notifies | never steals outside focus |
| Tab / Shift+Tab | tree open | closes full root | root notifies | browser continues document order; no restoration |
| command/check/radio selection | enabled | action/change callback, optional full close | root close request only when controlled | selected item stays focused if open; trigger only when close is accepted and focus remains in tree |
| link activation | enabled | optional full close plus native navigation | close request; native navigation remains | callback/navigation may move focus and wins |
| root disabled/removal/ancestor layer close | applicable | force-closes descendants then root | structural close is forced | ancestor/removal never restores; disabled follows the explicit rule below |

Desired open state is the controlled Boolean while supplied, otherwise the
committed internal Boolean. Effective open is desired open AND not effectively
disabled. Becoming effectively disabled force-closes the entire tree and
notifies `onOpenChange(false, reason="disabled", forced=True)` when it changed
visible state; the owner cannot reject this native safety override. Uncontrolled
state commits closed. Controlled desired state remains intact, so re-enabling
while the supplied value is still `True` predictably reopens and focuses the
first item. An owner that does not want that reopen accepts the forced callback
by setting `open=False`. Native fieldset changes follow the same rule.

When effective disabledness closes a tree whose focus is still inside it,
Citry first hides/inerts the tree, then focuses the nearest containing open
modal Dialog when one exists; otherwise it focuses `ownerDocument.body`. A
temporary `tabindex=-1` is used only when the chosen fallback is not natively
focusable and is removed after focus settles. If focus already moved outside
the tree, Citry preserves it. It never tries to focus the now-disabled
activator. This rule is identical for Menu configuration and native fieldset
disabledness in all engines.

Controlled requests never flash the requested visibility before acceptance.
Same-value owner commits do not notify. Rejected trigger and Escape closes
snapshot the previously active item. After a rejected trigger close, Citry
restores that item (or its nearest survivor) when focus is still on the
activator or document body; callback-moved focus elsewhere wins. Rejected
Escape similarly repairs body focus. Rejected outside, focus-outside, and Tab
closes never restore or
move focus: the user's outside target and native Tab order win even while the
controlled owner leaves the Menu visible. The owner is responsible for
accepting those close requests promptly; Citry does not turn a controlled Menu
into a focus trap.

Tab/Shift+Tab installs one gesture-scoped focus-transition token before native
focus advances. The resulting focusin outside the tree consumes that token and
does not issue `focus-outside`; `tab` is the sole close request even when a
controlled owner rejects it. The token clears after that focus transition or
one task, whichever comes first, and cannot suppress a later independent
focus-outside gesture.

An ancestor Popover/Dialog close, unrelated modal safety close, or ancestor
layer removal force-closes the tree, notifies `reason="ancestor", forced=True`,
never restores Menu focus, and sets a structural suppression latch. Reopening
the ancestor does not reopen or focus the Menu even if controlled `open=True`
remains supplied. The owner must acknowledge with `False` or release control;
a later `True` edge may open again. This preserves Dialog/Popover initial-focus
ownership instead of resurrecting stale transient UI.

Every path that could show a surface—server initialization, trigger request,
client `open`, re-enable, morph handoff, and submenu open—first runs the same
synchronous `mayOpen()` gate. It requires a connected, rendered, effectively
enabled trigger; no composed `hidden`/`inert`/closed Dialog/closed Popover
ancestor; every logical parent Menu currently open; and eligibility inside the
coordinator's current modal. Failure never calls `showPopover()` or moves
focus. It force-closes any stale descendant, applies the ancestor structural
suppression latch, and sends the forced ancestor notice after callbacks are
resolved. A Menu initialized with `open=True` inside a closed ancestor or
behind a modal therefore stays native/logically closed until the owner
acknowledges and later supplies a new open edge.

Checkbox activation maps `"mixed"` to `True`, otherwise negates the Boolean.
Radio activation requests its item value. Controlled choice requests do not
mutate ARIA until accepted. Callback order is choice change, root action, then
root close request. Command and choice activation run exactly once.

At most one direct submenu is open at each level. Opening a sibling closes the
prior child first. Parent close/disposal synchronously force-closes every
descendant before hiding the parent. A descendant may never remain logically
open or native-`:popover-open` while an ancestor is closed.

If an active item disappears, focus moves to the nearest surviving item in
settled DOM order. If no item survives, the tree closes. Disabling an active
item does not move focus because APG-disabled items remain navigable. An empty
server collection is an error; a client morph that leaves no items closes.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---:|---:|---|---|
| `CMenu` | `activator` | yes | one native Button | `{activator_attrs: dict[str, object], activator_disabled: bool}` | none |
| `CMenu` | `default` | yes | nonempty declaration collection | `{}` | none |
| command/check/radio item | `start` | no | one fill | `{}` | omitted |
| command/check/radio item | `default` | yes | one fill | `{}` | none |
| command/check/radio item | `description` | no | one fill | `{}` | omitted |
| command/check/radio item | `end` | no | one fill | `{}` | omitted |
| `CMenuGroup` | `label` | yes | one fill | `{}` | none |
| `CMenuGroup` | `default` | yes | nonempty direct collection | `{}` | none |
| `CMenuRadioGroup` | `label` | no | one fill | `{}` | omitted |
| `CMenuRadioGroup` | `default` | yes | one or more direct radio items | `{}` | none |
| `CMenuSubmenu` | `start` | no | one fill | `{}` | omitted |
| `CMenuSubmenu` | `label` | yes | one fill | `{}` | none |
| `CMenuSubmenu` | `description` | no | one fill | `{}` | omitted |
| `CMenuSubmenu` | `end` | no | one fill | `{}` | built-in logical chevron |
| `CMenuSubmenu` | `default` | yes | nonempty nested collection | `{}` | none |

Item content accepts text and decorative phrasing content only. It cannot add
independent semantics or Tab stops. `text_value` is required when the visible
label does not yield concise plain text. Slot data is server render data; item
browser state is exposed through public attributes, not reactive slot data.

Every actionable item receives a generated label ID and optional description
ID. Its semantic root owns `aria-labelledby` pointing only at the default/label
wrapper and optional `aria-describedby` pointing only at the description
wrapper. `start`, `end`, choice-indicator, and submenu-chevron wrappers are
`aria-hidden=true`; icon titles and visual shortcuts therefore cannot pollute
the accessible name. Root attrs cannot replace these relationships.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| root `onOpenChange` | `(requestedOpen, CMenuOpenChangeDetail)` | trigger, Escape, outside, focus outside, Tab, selection, native visibility | after validation, before controlled commit | uncontrolled commits before notification; controlled waits | no semantic cancellation; owner chooses state |
| root `onAction` | `(value: str, CMenuActionDetail)` | enabled valued-command or choice activation | once after item-specific choice request | fires for accepted activation even if choice is controlled | native `preventDefault` does not cancel the component callback |
| checkbox `onCheckedChange` | `(requestedChecked, CMenuCheckedChangeDetail)` | enabled checkbox activation | before root action and close request | controlled waits | owner chooses state |
| radio group `onValueChange` | `(requestedValue, CMenuRadioChangeDetail)` | enabled different radio activation | before root action and close request | controlled waits | owner chooses state |

`CMenuActionDetail` contains `kind: "command" | "checkbox" | "radio"`, the
item element, the native event, and the canonical path through ancestor
submenus. Link items emit their native click and preserve navigation but do not
emit command `onAction`. Callers use Alpine `@click`, `@focusin`, and other
`@...` listeners for native events.

The public callback records are exact:

```python
class CMenuOpenChangeDetail(TypedDict):
    reason: Literal[
        "trigger", "escape", "outside", "focus-outside", "tab",
        "action", "native", "disabled", "ancestor",
    ]
    controlled: bool
    forced: bool
    source: object | None

class CMenuActionDetail(TypedDict):
    kind: Literal["command", "checkbox", "radio"]
    item: object
    event: object
    path: list[str]

class CMenuCheckedChangeDetail(TypedDict):
    checked: bool
    previousChecked: CMenuChecked
    controlled: bool
    item: object
    event: object
    path: list[str]

class CMenuRadioChangeDetail(TypedDict):
    value: str
    previousValue: str
    reason: Literal["activation", "removal"]
    controlled: bool
    item: object | None
    event: object | None
    path: list[str]
```

`path` is the ordered canonical `CMenuSubmenu.value` sequence from the root to
the item. Root items use `[]`. The callback's first argument repeats the
requested `checked`/`value` where that keeps the common call site concise.
An ordinary command without `value` still emits its native click and applies
its close policy but does not call root `onAction`; callers use the native
`@click` surface for anonymous commands. Choice values are always required.

Component capture handlers retain activation ownership even when an authored
descendant listener stops propagation. They observe `defaultPrevented` only
for the native default action, not as a second component-state cancellation
API. Callback detail arrays are copies; mutation cannot affect internal state.

An activation snapshots its callback functions and immutable/copy detail, then
invokes the item-specific choice callback followed by root `onAction` exactly
once. DOM removal or ordinary prop updates during the first callback do not
erase the already accepted activation notification. A thrown callback aborts
the remaining sequence and propagates through the ordinary client error path.
The root callback step is simply absent for an anonymous command or link.
Activating an already-selected radio skips `onValueChange` because no value is
requested, but it remains an accepted choice activation: root `onAction` and
the item's close policy still run exactly once.
After the callbacks, Citry re-checks the root generation, connectedness,
current native modal, logical tree, and item identity before requesting close.
If a callback removed/replaced the tree or opened a modal Dialog, the stale
action-close step is skipped. Modal safety closure is `reason="ancestor"`, not
`"action"`, and Menu never restores focus over the Dialog. No callback or
scheduled close from the old generation runs a second time.

The tree marks that callback sequence as one activation transaction. Shared
focus-outside handling records, but does not reentrantly notify, focus moved
outside by a callback. After callbacks and the generation/modal checks, exactly
one close path wins: forced modal/ancestor first; otherwise `action` when the
effective item policy closes on selection; otherwise the deferred
`focus-outside` request. Callback-moved focus is preserved. A controlled owner
therefore never receives `focus-outside` before `onAction` followed by a second
`action` request for one activation.

There are no public methods or custom DOM events.

## 8. Semantics, keyboard, focus, and assistive technology

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| closed activator | click, Enter, Space | request open | first item after accepted open | click default only as needed to avoid duplicate activation |
| closed activator | ArrowDown | request open | first item | yes |
| closed activator | ArrowUp | request open | last item | yes |
| current menu | ArrowDown / ArrowUp | next / previous item, optionally wraps | target item and nearest scroll | yes |
| current menu | Home / End | first / last item | target item | yes |
| current menu | printable text | buffered prefix search in current menu | matched item | when handled |
| command/choice | Enter / Space / click | activate once | item or accepted close destination | Space yes; click as native requires |
| link | Enter / click | native navigation, optional close | native result | no unless disabled |
| link | Space | one synthesized native-equivalent activation | native result | yes |
| closed submenu trigger | click / Enter / Space | open child | first child item | Space yes; click/Enter only as needed to avoid duplication |
| open submenu trigger | click / Enter / Space | keep child open | first child item | as above |
| submenu trigger | logical forward arrow | open child | first child item | yes |
| submenu | logical reverse arrow / Escape | close child | parent trigger | yes |
| root | Escape | request root close | activator if accepted | yes |
| tree | Tab / Shift+Tab | request full close | next / previous document Tab stop | never trap; hide early enough for order |

The menu surface has `aria-labelledby` to the activator. Submenu surfaces are
labelled by their trigger. Group labels use `aria-labelledby`; radio groups use
their optional visible label when present. Separators are horizontal and
nonfocusable. `CMenuSeparator` is a horizontal rule between vertically stacked
items; it uses the role's default horizontal orientation and does not emit a
contradictory `aria-orientation`.

Each item name comes only from its owned label wrapper; the optional description
is a separate accessible description. Start/end glyphs, choice indicators,
shortcuts, and submenu chevrons are decorative and hidden from the accessibility
tree. Visible text and the computed accessible name therefore remain aligned.

Items use direct element focus and `tabindex=-1`; the currently focused item
may use `tabindex=0` only as a morph handoff marker. Disabled items use
`aria-disabled=true`, remain included in arrows/Home/End/typeahead, and never
use native `disabled`. Every pointer, keyboard, and programmatic activation
path checks the effective disabled value. Disabled anchors temporarily omit
`href` and restore it when enabled.

Typeahead uses a 500 ms buffered case-insensitive prefix, stays within the
current menu, begins after the current item, and honors `loop`. Its exact
normalization is Unicode NFKC, all whitespace collapsed
to one ASCII space, trim, then locale-aware lowercase in the current document
language. Citry resolves the nearest nonempty inherited `lang` through composed
ancestors (including a ShadowRoot host), falling back to `documentElement.lang`.
It catches invalid/unsupported language tags and uses locale-neutral
`toLowerCase()` rather than breaking navigation. This is native text matching,
not the future Citry locale/translation API. A supplied `text_value` wins;
otherwise each key event reads the
current owned label wrapper's `textContent`, so a retained DOM label change is
visible without reinitialization. Empty normalized labels do not match. When
the active buffer and new key are repetitions of one normalized character,
the buffer remains that character and successive presses cycle matching items;
other keys append normally until timeout. Labels, not icons, descriptions, or
shortcuts, supply matching text. Focused items scroll with `block="nearest"`.

An eligible key has one printable `event.key` character, is not composing, and
does not carry Ctrl, Meta, or ordinary Alt. Shift-modified characters are
accepted exactly as reported, so uppercase and punctuation remain reachable.
AltGraph-modified printable characters are accepted even when the browser also
sets Ctrl/Alt; dead and other non-character keys are ignored. Item activation
handles Space before typeahead matching.

Mouse movement may focus items and open submenus after a short delay. Pen hover
does so only while `buttons===0` and pressure is zero; pen contact/drag follows
the click/touch path and cannot move focus or open through hover. Touch has no
hover path. Pointer grace uses current trigger and child-surface rectangles
after collision resolution. Entering the actual child wins over heuristics;
moving toward a sibling closes promptly.

A disabled submenu trigger ignores pointer, keyboard, and programmatic click.
Hover may reveal a child without moving focus; activation always enters it. A
second activation while already open enters the child rather than toggling it
closed. Touch therefore has a complete click-to-open path without hover.

Automated engines prove all keyboard transitions except actual Safari Tab
continuation, which remains manual release evidence because Playwright WebKit
does not reliably advance Tab even between ordinary controls. VoiceOver,
NVDA, and JAWS review remains a release task.

## 9. Native forms and validation

Menu is not a native form participant. Activator, command, checkbox, radio, and
submenu Buttons are `type=button`; check/radio items are ARIA choices, not
inputs. They submit no name/value, emit no native input/change event, and do
not participate in constraint validation or reset. Link items remain anchors.

The family rejects form controls inside item content. A menu may sit inside a
Form without accidental submit. An owner may update application or server
state from callbacks. Citry Events transport, pending, server validation, and
retry remain owner concerns.

## 10. Styling and theme contract

Menu variants are intentionally small: one surface treatment, sizes `sm/md/lg`,
ordinary and `danger` item intent, checked/radio indicators, group labels,
separators, and nested elevation. Public variables resolve through private
effective variables so ancestor and root overrides work.

| Public variable | Type | Purpose | Initial default |
|---|---|---|---|
| `--cui-menu-background` | color | surface | `Canvas` |
| `--cui-menu-foreground` | color | item text | `CanvasText` |
| `--cui-menu-muted-color` | color | descriptions, labels, shortcuts | `color-mix(in srgb, current foreground 72%, transparent)` |
| `--cui-menu-border-color` | color | surface and separator boundary | `color-mix(in srgb, CanvasText 18%, transparent)` |
| `--cui-menu-border-width` | length | surface boundary | `1px` |
| `--cui-menu-radius` | length | surface corners | `0.75rem` |
| `--cui-menu-shadow` | shadow | root elevation | `0 0.75rem 2rem rgb(15 23 42 / 18%)` |
| `--cui-menu-submenu-shadow` | shadow | nested elevation | `0 1rem 2.5rem rgb(15 23 42 / 22%)` |
| `--cui-menu-inline-size` | length | preferred width | `14rem` |
| `--cui-menu-min-inline-size` | length | minimum useful inline submenu corridor | `10rem` |
| `--cui-menu-max-inline-size` | length | viewport-safe width | `calc(100dvi - 1rem)` |
| `--cui-menu-max-block-size` | length | scroll limit | `min(24rem, calc(100dvb - 1rem))` |
| `--cui-menu-padding` | length | surface edge spacing | `0.375rem` |
| `--cui-menu-item-block-size` | length | item minimum height | `sm: 2rem; md: 2.25rem; lg: 2.5rem` |
| `--cui-menu-item-padding-inline` | length | item inline spacing | `sm: 0.5rem; md: 0.625rem; lg: 0.75rem` |
| `--cui-menu-item-gap` | length | item-region gap | `0.625rem` |
| `--cui-menu-item-radius` | length | active item corners | `0.5rem` |
| `--cui-menu-hover-background` | color | pointer hover | `color-mix(in srgb, CanvasText 8%, transparent)` |
| `--cui-menu-focus-background` | color | focused item fill | `light-dark(#175cd3, #84adff)` |
| `--cui-menu-focus-foreground` | color | focused item content | `light-dark(#ffffff, #101828)` |
| `--cui-menu-focus-outline-color` | color | focus-visible outline | `light-dark(#175cd3, #84adff)` |
| `--cui-menu-danger-color` | color | destructive item | `light-dark(#b42318, #fda29b)` |
| `--cui-menu-disabled-opacity` | number | disabled content | `0.5` |
| `--cui-menu-offset` | length | root anchor gap | `0.375rem` |
| `--cui-menu-submenu-offset` | length | nested inline gap | `0.25rem` |
| `--cui-menu-duration` | time | entry/exit | `120ms` |
| `--cui-menu-easing` | easing | entry/exit | `cubic-bezier(0.2, 0.8, 0.2, 1)` |

| Public selector | Exact element and purpose | Stable relationship |
|---|---|---|
| `[data-citry-ui-part="menu"]` | root or submenu `div[role=menu]` surface | owns Popover presence and collection focus |
| `[data-citry-ui-part="menu-item"]` | command/link/check/radio semantic root | direct collection item, optionally through one group |
| `[data-citry-ui-part="menu-item-start"]` | decorative start wrapper | direct item child before label |
| `[data-citry-ui-part="menu-item-label"]` | visible and accessible item name | direct item child; target of `aria-labelledby` |
| `[data-citry-ui-part="menu-item-description"]` | optional visible accessible description | direct item child; target of `aria-describedby` |
| `[data-citry-ui-part="menu-item-end"]` | decorative shortcut/end wrapper | direct item child after label content |
| `[data-citry-ui-part="menu-choice-indicator"]` | decorative checked/radio indicator | direct choice-item child |
| `[data-citry-ui-part="menu-group"]` | labelled `div[role=group]` | direct collection child |
| `[data-citry-ui-part="menu-group-label"]` | visible group name | direct group child and `aria-labelledby` target |
| `[data-citry-ui-part="menu-radio-group"]` | `div[role=group]` owning radio state | direct collection/group child |
| `[data-citry-ui-part="menu-separator"]` | horizontal `hr[role=separator]` | between actionable collection siblings |
| `[data-citry-ui-part="menu-submenu"]` | neutral submenu wrapper | direct collection/group child |
| `[data-citry-ui-part="menu-submenu-trigger"]` | `button[role=menuitem]` | immediately precedes and controls child Menu surface |

| Public attribute | Element | Values | Meaning |
|---|---|---|---|
| `popover` | Menu surface | `"manual"` | native top-layer presence with Citry dismissal |
| `role` | Menu surface | `"menu"` | application Menu composite |
| `aria-labelledby` | Menu surface | activator/submenu-trigger IDREF | exact Menu name |
| `data-open` | Menu surface / submenu wrapper | present / absent | logical open ownership; absent during exit |
| `data-placement` | root Menu surface | six `CMenuPlacement` strings | requested logical placement, not collision result |
| `data-match-width` | root Menu surface | present / absent | trigger-width matching |
| `data-size` | root Menu surface | `"sm" | "md" | "lg"` | effective inherited item geometry |
| `aria-haspopup` | activator/submenu trigger | `"menu"` | controlled popup kind |
| `aria-controls` | activator/submenu trigger | Menu-surface IDREF | controlled surface |
| `aria-expanded` | activator/submenu trigger | `"true" | "false"` | logical open state |
| `role` | ordinary item | `"menuitem"` | command/link semantics |
| `role` | check/radio item | `"menuitemcheckbox" | "menuitemradio"` | choice semantics |
| `aria-labelledby` | actionable item | owned label IDREF | exact item name |
| `aria-describedby` | actionable item | description IDREF / absent | optional separate description |
| `aria-disabled` | actionable item | `"true"` / absent | focusable but inactive item |
| `data-disabled` | actionable item | present / absent | public styling mirror |
| `data-intent` | ordinary/submenu item | `"default" | "danger"` | visual emphasis |
| `aria-checked` | check item | `"false" | "true" | "mixed"` | effective checked value |
| `data-checked` | check item | `"false" | "true" | "mixed"` | styling mirror |
| `aria-checked` | radio item | `"false" | "true"` | effective group selection |
| `data-checked` | radio item | `"false" | "true"` | styling mirror |
| `role` | generic/radio group | `"group"` | item ownership grouping |
| `aria-labelledby` | labelled group | group-label IDREF | exact group name |
| `role` | separator | `"separator"` | horizontal collection division |

Requested placement is not a promise of post-collision physical side. Nested
CIcon roots retain their own Icon selector contract.

When `match_width=True`, CSS uses the activator anchor width only up to
`--cui-menu-max-inline-size`; the viewport-safe maximum wins over matching.
An over-wide activator can therefore be wider than the Menu but cannot force
horizontal page overflow. The same clamp applies after zoom and text-spacing
changes.

Default CSS uses `@layer citry-ui.theme` and zero-specificity selectors.
Consumer unlayered CSS and inline `style` win. Exact private classes, temporary
presence markers, and collision implementation attributes remain private.

## 11. Environmental behavior

- Defaults adapt to light and dark `color-scheme`; nested surfaces copy the
  trigger's settled scheme before entering the top layer.
- Logical properties and actual geometry support RTL; submenu forward/reverse
  arrows and default inline side reverse.
- Reduced motion resolves duration to zero without delaying logical close.
- Forced colors retain boundaries, focused items, disabled differentiation,
  and check/radio indicators with system colors.
- Menus remain usable at 200%/400% zoom, with text spacing, long localized
  labels, long shortcuts, and narrow viewports. Labels wrap only when needed;
  descriptions wrap; surfaces scroll without horizontal page overflow.
- Coarse pointer and touch use click activation and no hover-only behavior.
- Print hides closed menus and prints an initially/open currently visible menu
  in document flow without shadow or animation.

Library-authored visible strings: none. All labels and descriptions are user
content. Typeahead honors the nearest valid native `lang`; translated
library-authored strings and a broader Citry locale contract remain future
localization work.

## 12. Overlay and layering behavior

Root and submenu surfaces use native `popover="manual"`, CSS Anchor
Positioning, no teleport, and the shared
`Symbol.for("citry-ui:anchored-layer-runtime")` controller. The root supports
six logical block placements. Submenus prefer logical inline-end and flip by
current collision space.

The shared anchored-layer controller is implemented as one coordinator per
`ownerDocument`, with a
`WeakMap<Document | ShadowRoot, Scope>` and one ordered layer stack spanning
those scopes. Each layer records its actual scope and logical parent. Scope
listeners observe the unretargeted local path; document listeners observe
outside interaction; all containment uses `event.composedPath()` and composed
ancestor traversal through `ShadowRoot.host`. A processed-event guard prevents
the scope and document listeners from handling one event twice. The last layer
removes its scope listeners; the last document layer removes the coordinator.

This refactor applies to `CPopover`, `CTooltip`, and `CMenu` together. A layer
inside an open ShadowRoot can be a descendant of a Document-scope layer when
its composed host ancestry lies inside that parent. Parent close cascades to
cross-scope descendants. Separate unrelated roots share outside/Escape order
through the document stack without becoming logical parent/child layers.
Closed ShadowRoot support is not claimed.

Menu adds an explicit tree atop that shared layer stack:

- each root has one logical tree identity;
- every submenu records its parent surface, parent trigger, and root;
- ancestor triggers and surfaces count as logically inside the deepest child;
- outside pointer/focus closes the whole tree once;
- Escape is consumed by only the deepest submenu;
- selection closes the whole tree according to close policy;
- parent close, removal, Popover close, or Dialog close force-closes every
  descendant synchronously before the ancestor hides;
- logical layer ownership ends immediately on accepted close, while exit
  presence may remain inert and hidden from assistive technology;
- one shared listener set exists per actual Document or ShadowRoot and is
  removed after the last layer.

Opening a modal Dialog also force-closes and structurally suppresses every
anchored layer whose trigger is outside that Dialog's composed subtree before
the Dialog can own Escape/focus. Layers triggered inside the Dialog remain
eligible. The document coordinator checks the current topmost `:modal` Dialog
before every shared event and observes Dialog `open`/tree changes while layers
exist, so native `showModal()` and `CDialog` use the same rule. Controlled
layers cannot reject this safety close and follow the ancestor suppression
latch; exactly the Dialog consumes the next Escape. Removing/closing the modal
does not resurrect suppressed layers.

The coordinator never infers modal stacking from DOM order. It records a
monotonic open sequence from captured Dialog toggle/open mutations in every
known Document/open ShadowRoot and reconciles it synchronously before each
shared event and `mayOpen()` call. Bootstrap scans all known roots and promotes
the `:modal` Dialog containing the deep active element. Newly discovered
already-open Dialogs receive older sequence positions. If several pre-existing
modal Dialogs remain and neither deep focus nor a recorded transition can
disambiguate them, no anchored layer is eligible until focus/interaction or a
later open transition establishes the current modal; Citry never guesses from
document order. An event composed from inside a modal also reconciles that
known current Dialog. Reverse DOM/open order therefore cannot expose a
background Dialog's layer or let it consume Escape.

Click, not pointerdown, opens the root so touch scrolling is not intercepted.
Outside pointerdown may request dismissal, but the following focus transition
from the same gesture is deduplicated. A root-trigger click while its submenu
is topmost produces one root toggle, never close-on-pointerdown then reopen.

Pointer grace exists only while a mouse/pen leaves a submenu trigger toward
its open child. One temporary pointermove observer compares current rectangles
and actual child containment; it is generation-scoped and cleaned on close,
resize, replacement, or pointer-type change.

Submenu placement order is inline-end, inline-start, then a centered overlapping
block fallback. Citry compares both physical inline corridors with the computed
`--cui-menu-min-inline-size`. A private absolutely positioned, noninteractive
measurement probe inherits the token as its `inline-size`; its settled geometry
provides real CSS pixels for `rem`, `calc()`, `clamp()`, and other valid lengths.
Citry never `parseFloat`s the custom-property source text.

If neither inline corridor fits, the greater block corridor wins (`block-end`
on a tie), with `flip-block` as the final collision fallback and the normal
viewport max-size clamp. After layout, Citry derives one private physical side
(`inline-start`, `inline-end`, `block-start`, or `block-end`) from current
trigger/surface rectangles. The safe corridor targets that actual edge,
including overlap placement. The built-in submenu chevron rotates toward the
same settled physical side; collision flips and RTL can never leave it pointing
away from its surface.

One document-coordinator `requestAnimationFrame` loop exists only while at least
one submenu is open. It snapshots trigger/surface/probe rectangles, direction,
and visual-viewport bounds and schedules one reconciliation when any changes.
This covers document/ancestor scroll, visual-viewport movement, window resize,
anchor movement, font/root-size changes, direction changes, and public token or
theme updates without one listener per submenu. It stops after the last
submenu closes. Pointer intent always consumes the most recent settled snapshot.

The per-root shared-runtime refactor and focused Document/open-ShadowRoot proof
are implementation prerequisites, not release polish.

## 13. Collections, async data, and identity

Settled DOM order is navigation order. Collection identity uses private stable
component registrations, not forgeable public attributes. Server validation
matches actual component render frames to direct output roots, following the
Accordion collector precedent. Browser registration coalesces one bounded
reconciliation after an initialization/morph batch.

Groups flatten to their direct actionable descendants for root navigation.
Radio-group selection remains scoped to its group. Submenu descendants belong
to a separate current menu and never participate in parent arrows/typeahead.

Removing an uncontrolled radio selection commits the nearest surviving radio
in prior settled order (following sibling wins a distance tie) and calls
`onValueChange` once with `reason="removal"`; it does not call root `onAction`
or close the Menu. Removing a controlled selection leaves no radio checked,
reports the now-unknown supplied value once, and requests the same nearest
survivor through `onValueChange(reason="removal")`; only owner acceptance
checks it. Releasing control then commits that requested fallback. If no radio
survives, the group has no selection, emits no impossible string-valued change
request, reports its invalid empty structure, and contributes no item. A server
render still rejects an empty group; a client morph that empties the only group
closes the root Menu.

Reorder preserves the focused item by stable registration when possible.
Removal selects the nearest survivor. Removing an open submenu trigger closes
that branch before unregistering it. Duplicate/stale registrations are errors
or diagnostics, never silent competing owners.

There is no async loading, pagination, virtualization, or empty-state UI. Use
server rendering/loops to produce declarations. A Menu with no actionable item
is invalid rather than an inaccessible empty popup.

## 14. Server render, morph, and cleanup

Closed server output contains a labelled native Button and complete semantic
menu markup, hidden by native Popover presence. Initially open output has the
same in-flow no-JavaScript fallback used by Popover so commands and links remain
readable without client activation; enhanced activation moves it to the top
layer and focuses the first item. No-JavaScript choice state is readable but
not mutable through the ARIA buttons.

Initialization is ancestor-first. The root publishes its registration context,
items register, then one reconciliation validates the nonempty collection,
applies client inputs, opens if requested, and focuses only after all direct
items exist. A private initialized marker is set only after this first
successful reconciliation; it is readiness evidence, not stable public API.

Correlated rerender handoff preserves semantic state only: committed open,
client-control ownership/value, focused item identity, choice state, and the
descendant-open path where still valid. The replacement creates a fresh
generation greater than the handed-off numeric seed. Old timers, microtasks,
animations, pointer intent, pending notifications, and focus tasks are canceled
and never transferred or allowed to mutate the replacement. Each mutable or
side-effecting public input is consumed once per render and shared by template
and JS.

Cleanup force-closes descendants; leaves the shared stack immediately; cancels
exit, typeahead, pointer-intent, focus-return, and reconciliation tasks; removes
capture listeners, observers, and registrations; restores no stale `href` or
ARIA state; and removes the shared root listener set after the last layer.
Repeated initialization must not duplicate callbacks or listeners.

Focused morph cases include trigger/surface replacement, root removal during
exit, reordered groups/items, removed focused/selected/open items, disabled
changes, nested Menu replacement, placement flips, and Popover/Dialog ancestor
closure while a submenu is open.

## 15. Security and content trust

Visible slot text is escaped by Citry. Direct strings and identities are
converted to exact plain strings before rendering; CRLF/CR normalize where
identity requires it; U+0000 is rejected. `href` is a trusted URL boundary
like native anchor attributes: Citry does not classify application schemes,
but disabled links cannot navigate.

All mappings are copied once. Each destination rejects case-insensitive
duplicates, Citry/Events runtime namespaces, owned identity/role/focus/ARIA/
presence/anchor/state attributes, dynamic/property aliases to them, object
spreads, and structural/ownership directives including `x-html`, `x-text`,
`x-if`, `x-for`, `x-show`, `x-ignore`, and `x-teleport`.

Item roots additionally reserve `type`, `href` where component-owned,
`disabled`, `role`, `tabindex`, `aria-disabled`, `aria-checked`,
`aria-haspopup`, `aria-expanded`, `aria-controls`, `hidden`, `inert`,
`contenteditable`, Popover/command attributes, and public reflections. Surface
destinations reserve `popover`, `role`, labels, presence, focus, and anchors.

Allowed native `@...` listeners and unrelated Alpine bindings cannot stop the
capture-phase owner from maintaining collection semantics. Decorative slots
cannot introduce active content or form participation. Settled-DOM validation
is a defense against invalid composition, not HTML sanitization.

## 16. Assets and performance

Menu adds family CSS and one client behavior payload when rendered. It reuses
native Popover, CSS anchors, the shared layer runtime, and the existing audited
CIcon glyph resolver for a single submenu chevron/check indicator path; it
does not render four hidden Icon components or add fonts.

Each initialized root tree owns five delegated capture listeners (`click`,
`keydown`, `focusin`, `pointerover`, and `pointerout`) on its host; submenus add
no permanent listener set. A tree owns at most one temporary `pointermove`
listener while submenu grace is active. Shared outside/Escape/focus listeners
remain one set per actual root/document coordinator.

Native-fieldset disabled tracking uses one shared mutation observer per actual
Document/ShadowRoot with registered Menu triggers, not one observer per Menu.
It observes ancestor fieldset `disabled` changes and direct-child changes that
can alter the first-legend exception, then re-evaluates only affected
registrants. The same document coordinator supplies the bounded modal-Dialog
observer. All shared observers disconnect after their last registration.
Same-batch item registrations coalesce to one O(n) reconciliation using
maps/sets; no O(n²) duplicate scans.

Open submenu geometry uses one shared rAF sampler per ownerDocument regardless
of submenu count; closed Menus incur no geometry frames or measurement probe.

Quality tools record raw/gzip/Brotli family assets and bounded server
render/output diagnostics at 1, 10, 100, 500, and 1,000 root Menus. Focused
browser tests prove initialization and first action behavior but do not claim
cross-machine timing gates. A disposable submenu geometry benchmark must show
one surface and one icon path per submenu, not multiplied hidden components.

## 17. Acceptance matrix

The design gate requires independent adversarial review of this document.
Implementation closure requires:

- schema/default/type and every invalid input path;
- every declaration class, valid nesting, transparent wrapper, and invalid
  direct-root/frame spoofing path;
- duplicate/canonicalized values and mutable-input one-snapshot behavior;
- native Button/anchor roots, ARIA roles/relationships, group labels, choice
  states, separator semantics, and no Form submission;
- trigger click/Enter/Space/Down/Up entry; all item arrows/Home/End/typeahead;
  Space-on-link exactly once; disabled pointer/keyboard/`.click()` guards;
- Tab/Shift+Tab close semantics, Escape at two levels, focus restoration and
  owner-moved-focus preservation;
- controlled root and choice request/accept/reject/release ordering and
  exactly-once callbacks;
- root close cascading two submenu levels; deepest outside dismissal;
  parent Popover/Dialog close; ancestor removal; root-trigger retoggle;
- actual-geometry safe corridor on both inline sides and the block-overlap
  fallback, narrow collision flip, chevron direction, RTL, fast transfer,
  sibling intent, touch and pen;
- add/remove/reorder/disable, no survivors, radio selection removal,
  submenu-trigger removal, retained morph, and cleanup/reinitialization;
- public variable overrides from ancestor/root, each selector, each size,
  danger, check/radio, light/dark/nested schemes, RTL, narrow/zoom/long text,
  reduced motion, forced colors, print, and host CSS before/after Citry;
- Document and open ShadowRoot behavior, nested Popover/Tooltip/Menu layers,
  no console/page errors, axe, Nu HTML, and three-engine functional checks;
- all public previews rendered, initialized, interactive, console-clean, and
  free of serious/critical axe findings;
- asset/scaling records, exact registration/export/package resources, and a
  wheel containing only runtime family files.

Manual release evidence covers Safari Tab continuation, VoiceOver, NVDA, and
JAWS announcements, touch/pen devices, collision visuals, and final light/dark
visual design. Tests and benchmarks are bounded; release tools make their
evidence human-reviewable without turning diagnostics into machine speed gates.

## 18. Compatibility classification

Stable public API includes the eight class names, inputs, slots/data,
callbacks/details, aliases, variables, selectors, reflections, validation
errors, and no-Form contract. Behavioral/structural contract includes the
documented semantic roots/relationships, direct nesting, logical tree,
keyboard/focus, controlled ownership, action/choice ordering, disabled
behavior, no-JavaScript fallback, and close cascade.

Exact default colors, spacing, shadows, easing, and incidental private hosts or
label layout may evolve. Private classes, private variables, render-frame
registrations, initialization/presence markers, JS organization, timers,
pointer-polygon algorithm, and collision attributes are implementation detail.

## 19. Public documentation contract

`components/cmenu/api.md` is the reader-first guide;
`components/cmenu/api.yml` is the exhaustive reference. The guide starts with
composition and a visible sampler, then commands and links, item content,
controlled opening, choices, groups, submenus, keyboard/typeahead, placement,
styling, accessibility, and lifecycle boundaries.

All examples use one coherent enchanted-library theme and concise copy:

| Module | Reader task | Visible/interactive contract | Focused evidence |
|---|---|---|---|
| `at_a_glance.py` | recognize the family | commands, link, separator, danger, one submenu | anatomy, roles, open/close |
| `commands_and_links.py` | run actions or navigate | command callback plus real anchor | exactly-once action, native href/context behavior |
| `item_content.py` | add icons/descriptions/shortcuts | all four item regions | wrapping, typeahead text isolation |
| `controlled_open.py` | own visibility/configuration | controls for open, disabled, size, and intent outside rendered result | accept/reject/release, reactive config, and focus |
| `choices.py` | toggle and select | mixed checkbox and radio group | callback order and ARIA |
| `groups_and_separators.py` | organize commands | labelled groups and separators | labelledby and valid ordering |
| `submenus.py` | navigate nested commands | two levels, both pointer sides | keyboard, close chain, safe corridor |
| `keyboard_and_typeahead.py` | learn operation | long scrollable collection with `loop` and `close_on_select` controls | entry, no-wrap/wrap, retained-open action, matching, scrolling |
| `disabled_and_forms.py` | understand inactive commands | disabled items plus Menu inside a toggled native disabled fieldset | navigable disabled items, programmatic guard, no submit, reactive effective disabled |
| `placement_and_rtl.py` | place near edges | collision, `match_width`, over-wide trigger, and RTL controls | viewport clamp, current geometry, logical arrows |
| `sizes.py` | compare density | `sm`, `md`, `lg` | computed geometry |
| `customization.py` | adapt brand tokens | two library-themed token sets | variable/selector/class precedence |
| `lifecycle.py` | understand composition limits | nested Popover/Menu and an unrelated modal Dialog | cascade, modal suppression, and non-resurrection |

Controls are visually separate and collapsible; code is collapsed by default.
Rendered examples use the docs code-block surface, smaller demo typography, no
decorative card backgrounds, and no empty announcement prose. Public prose is
direct and skimmable. Invalid-input diagnostics remain focused-test evidence,
not console errors in public examples.

## 20. Open decisions and deferred work

No open implementation decision remains after independent design and
implementation review.

Deferred surfaces: context/point menu, menubar/navigation menu, split/long-
press/multiple triggers, hover root opening, generic data records,
virtualization, search/forms/arbitrary content, public highlighted identity,
public submenu control, raw collision middleware, imperative methods, and a
headless family. Add one only after a concrete application job and its focus,
touch, morph, and accessibility contract exist.
