# Context Menu component design

Status: implemented and independently reviewed, 2026-08-12.

## 1. Purpose and product bar

`CContextMenu` presents the existing Citry Menu declaration family at the
location where a user requests commands for one target region. It adds
contextual activation and point positioning. It does not add a second Menu
model.

The product bar is:

- a trusted secondary-button `contextmenu` event opens at the event's viewport
  point;
- the Context Menu key and Shift+F10 open from the focused descendant and a
  deterministic target-derived point;
- eligible touch and pen input has one bounded 700 ms long-press fallback
  without canceling pointerdown, capturing the pointer, changing
  `touch-action`, or disabling the platform callout in CSS; an accepted
  fallback suppresses only its matching derived click while the bounded
  sequence token is armed, so an ordinary derived activation cannot also
  submit the target;
- editable controls, links, media, embedded content, custom/shadow hosts, and
  selected text retain the native context menu by default;
- the Menu surface, declarations, item state, keyboard model, typeahead,
  submenus, choices, controlled visibility, dismissal, action ordering,
  layering, styling, morph behavior, and diagnostics are the existing CMenu
  contracts;
- point placement uses a private real element, native Popover, CSS Anchor
  Positioning, logical direction, and the existing anchored-layer coordinator;
- pointer, keyboard, focus, native-default, modal, ShadowRoot, iframe, narrow,
  zoom, RTL, forced-colors, print, morph, and cleanup outcomes are explicit;
  and
- implementation extracts and reuses private Menu server and controller
  machinery. It must not copy Menu JavaScript, declarations, collection
  validation, item rendering, submenu logic, theme CSS, or layer listeners.

This component earns itself over consumer event wiring. A consumer can set
`open` on CMenu after `contextmenu`, but cannot supply a virtual point through
CMenu's public Button activator, preserve native defaults only after a
controlled owner accepts, deduplicate keyboard and native events, coordinate
long press, or attach arbitrary-target focus return without bypassing CMenu's
private state and layer generation.

Use CContextMenu for target-relative application commands. Use CMenu for a
visible Menu Button, CPopover for interactive non-menu content, Tooltip for a
short description, and the browser's native context menu when copy, spelling,
link, image, media, or editing commands are the primary job.

The shortest supported jobs are:

| Job | Template or Python expression | Support path |
|---|---|---|
| contextual commands for a focusable row | `<c-CContextMenu aria_label="Row actions">...existing CMenu declarations...</c-CContextMenu>` | direct component API |
| use the full Menu declaration model | `CMenuItem`, choice, group, separator, and submenu declarations in `menu` | existing CMenu family |
| own visibility | `$c-props="{open, onOpenChange}"` | controlled client API |
| observe command activation | `onAction` | existing `CMenuActionDetail` |
| preserve a descendant's native menu | `data-citry-context-menu-native` | public target-content escape marker |
| open commands from a visible Button | CMenu | separate component |
| display arbitrary controls or a Form | CPopover | separate component |
| expose browser copy/edit/media actions | no CContextMenu at that point | native platform path |

Non-goals are a command palette, radial menu, item-model adapter, selection
menu, editor toolbar, drag menu, arbitrary virtual-reference API, consumer
coordinates, configurable placement or collision engine, hover/click opening,
global page context menu, cross-origin iframe interception, portal/teleport,
modal context menu, rich content, or replacement of browser spelling, copy,
link, image, and media commands.

## 2. Prior art and complaints

Sources were reviewed on 2026-08-11. Product versions are the current official
documentation or latest public tags verified on that date.

| Source | Version or review date | Evidence used | Citry disposition |
|---|---|---|---|
| [UI Events `contextmenu`](https://w3c.github.io/uievents/#event-type-contextmenu), [MDN `contextmenu`](https://developer.mozilla.org/en-US/docs/Web/API/Element/contextmenu_event), and [KeyboardEvent key values](https://developer.mozilla.org/en-US/docs/Web/API/UI_Events/Keyboard_event_key_values) | current, 2026-08-11 | cancelable native event, ContextMenu key value, Firefox Shift+secondary-click exception | adopt trusted event and explicit key paths; never claim interception of Firefox Shift+secondary-click |
| [WAI-ARIA APG Menu and Menubar](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/) and [Menu Button](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/) | current, 2026-08-11 | Menu item roles, direct focus, entry, arrows, Home/End, typeahead, Escape | adopt through CMenu; an arbitrary context target is not relabelled as a Menu Button |
| [HTML Popover](https://html.spec.whatwg.org/multipage/popover.html) | living standard, 2026-08-11 | manual Popover top-layer and toggle lifecycle | adopt through CMenu and the shared layer coordinator |
| [CSS Anchor Positioning](https://drafts.csswg.org/css-anchor-position-1/) | working draft, 2026-08-11 | real anchor element, logical `position-area`, try fallbacks | adopt one private point element; no JavaScript surface-position engine |
| [Selection API `getComposedRanges`](https://w3c.github.io/selection-api/#dom-selection-getcomposedranges) | living draft, 2026-08-11 | open-ShadowRoot selection boundaries without document-range retargeting | use the component's known actual root to preserve selected-text native menus |
| [Zag Menu](https://zagjs.com/components/react/menu) and [official source](https://github.com/chakra-ui/zag/tree/%40zag-js/menu%401.43.0/packages/machines/menu) | 1.43.0 | one Menu machine exposes `anchorPoint`; context trigger and Button trigger share the same model; reactivation repositions while open | adopt one model and same-open reposition; implement with Citry's real CSS anchor rather than a copied positioning machine |
| [Radix Context Menu](https://www.radix-ui.com/primitives/docs/components/context-menu), [immutable npm package](https://www.npmjs.com/package/@radix-ui/react-context-menu/v/2.3.7), and [official current source](https://github.com/radix-ui/primitives/blob/main/packages/react/context-menu/src/context-menu.tsx) | Context Menu 2.3.7; no matching public source tag was available at review | target composition, point reference, managed focus, full Menu parts, 700 ms touch/pen timer | adopt target plus Menu composition and 700 ms bound; reject portal, modal default, and unconditional `-webkit-touch-callout:none` |
| [Reka Context Menu](https://reka-ui.com/docs/components/context-menu) and [tagged source](https://github.com/unovue/reka-ui/tree/v2.10.3/packages/core/src/ContextMenu) | 2.10.3 | right click, long press, controlled open, collision options, full Menu family | adopt the dedicated boundary; reject teleport and broad placement surface |
| [Base UI Context Menu](https://base-ui.com/react/components/context-menu) and [tagged source](https://github.com/mui/base-ui/tree/v1.7.0/packages/react/src/context-menu) | 1.7.0 | controlled/uncontrolled root, target trigger, nested Menu declarations, long press | use as corroboration; retain Citry's inline top-layer and CMenu semantics |
| [Vaadin Context Menu](https://vaadin.com/docs/latest/components/context-menu), [immutable npm package](https://www.npmjs.com/package/@vaadin/context-menu/v/25.2.7), and [tagged source](https://github.com/vaadin/web-components/tree/v25.2.7/packages/context-menu) | 25.2.7 | Web Component wrapper target, right click/long press, optional left click, item model/custom renderer, selection event | adopt wrapper target composition and platform inputs; reject left-click mode, item-model duplication, and arbitrary custom-item content |
| [Vuetify VMenu](https://vuetifyjs.com/en/components/menus/) and [`target` implementation](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VOverlay/useActivator.tsx) | 4.1.8 | `target="cursor"` stores click coordinates and overlay accepts a point tuple | record cursor targeting; add a dedicated Citry family because Vuetify does not supply the required context/native-preservation contract |
| [React Aria component index](https://react-spectrum.adobe.com/react-aria/components.html) | React Aria 1.20.0 | no dedicated ContextMenu primitive in the reviewed component catalog | no direct API to copy; reuse Citry Menu semantics and require manual AT evidence |
| Citry local sources | current workspace, 2026-08-11 | [Menu](./menu.md), [Split Button](./split-button.md), [overlay foundations](../ui_overlay_foundations.md), current CMenu/SplitButton/anchored runtime and focused tests | prove private reuse and identify the native-Button and real-anchor extension points |

The local and external complaint set is concrete:

- suppressing `contextmenu` everywhere removes copy, spelling, link, image,
  media, and developer tools paths;
- a right-click-only design is inaccessible to keyboard users;
- using event coordinates for keyboard invocation places the Menu at zero or
  at inconsistent browser coordinates;
- handling keydown and the following native event independently opens twice;
- a synthetic timer that cancels pointerdown or applies `touch-action:none`
  breaks scrolling and selection;
- an unconditional callout-suppression style hides native mobile affordances;
- a consumer-owned absolute `left/top` overlay misses top-layer, collision,
  RTL, modal, and ShadowRoot behavior;
- a second Menu implementation drifts in actions, check/radio state,
  submenus, typeahead, dismissal, and callback order;
- treating the original target as outside makes a second right click close
  before it can reposition, while treating it as unconditionally inside makes
  primary click and programmatic focus fail to close;
- controlled refusal can suppress the native menu without displaying the
  custom one unless default prevention depends on synchronous acceptance;
- a portal can escape scheme, modal, and ownership ancestry; and
- clone/morph cleanup can leave a point element, shared layer registration, or
  apparently initialized target without a live controller.

### Browser proof record

A disposable inline Playwright 1.62.0 harness, with no retained workspace
script, ran in Chromium 151.0.7922.34, Firefox 153.0, and WebKit 26.5:

- trusted right click dispatched a cancelable composed `contextmenu` with
  viewport `clientX/clientY` in all three engines;
- Chromium generated a centered `contextmenu` after the ContextMenu key in the
  automation environment, while Firefox and WebKit did not, proving that the
  native event alone is not an adequate keyboard contract;
- preventing ContextMenu or Shift+F10 keydown suppressed Chromium's following
  native event and caused no duplicate in any engine;
- a fixed 1 px CSS anchor at center and bottom/inline viewport edges placed a
  fixed Menu surface correctly, and `flip-block`, `flip-inline`, and their
  combination contained it in all three engines;
- an ordinary fixed point under a transformed containing block was offset and
  produced divergent surface geometry, while promoting that same point through
  `showPopover()` before the Menu surface restored exact coordinates in all
  three engines, including inside an open ShadowRoot;
- logical `bottom-start` placement grew physical right from the point in LTR
  and physical left in RTL; `bottom-end` produced the opposite alignment and
  is not the ContextMenu root placement;
- `contextmenu` crossed an open ShadowRoot boundary with its composed path,
  but an event inside an iframe did not bubble to its parent Document;
- a noncollapsed light-DOM Selection remained observable during right click;
- for a real drag selection inside an open ShadowRoot, Chromium and WebKit
  retargeted `getRangeAt(0)` to a collapsed body range while Firefox exposed
  the inner range; `getComposedRanges({shadowRoots: [actualRoot]})` returned the
  inner text boundaries in all three; and
- input right click showed engine-specific Selection side effects, reinforcing
  the rule that the component must not replace editable native behavior.

Additional trusted-input probes showed that Firefox intentionally emits no
`contextmenu` for Shift+secondary-click and no event on a disabled native
Button, while Chromium and WebKit emit in those cases. Citry therefore treats
Shift+secondary-pointer input as a universal native escape and independently
checks native `:disabled`. A Chromium CDP touch held for 800 ms produced
pointerdown, pointerup, and a trusted derived click without a native
`contextmenu`; this is why an accepted synthetic fallback owns one exact click
suppression token instead of allowing the target action to run.

Desktop automation does not prove operating-system touch callout timing,
assistive-technology announcements, or hardware Context Menu keys. Those are
manual release gates.

### Vuetify disposition

| Vuetify surface or job | Support path | Citry surface | Decision |
|---|---|---|---|
| `modelValue` / `update:modelValue` | controlled client API | `open`, claim-returning `onOpenChange` | adopt visibility ownership; add same-turn native-default claim |
| `id` | direct server API | `id` | adopt correlated target/point/surface identity |
| `disabled` | direct/reactive API | `disabled` | adopt for custom invocation only; target remains independently operable |
| submenu mode/parent registration | existing Menu tree | `CMenuSubmenu` and shared layer coordinator | adopt without public ContextMenu submenu state |
| VOverlay `target="cursor"` | private point from accepted invocation | no public coordinate input | adopt the point job, not tuple-valued public state |
| explicit element, selector, coordinate targets | required bound target slot | `target` and `target_attrs` | omit public selectors, Element objects, and coordinates |
| activator slot and `activatorProps` | target composition | `target` slot data | normalize to one exact bound native Element |
| default/content slot data | Menu declarations | required `menu` slot | reject arbitrary interactive content/model adapters |
| `closeOnContentClick` | existing Menu action policy | `close_on_select` and item override | adopt CMenu vocabulary |
| click, hover, and focus opening | separate products | CMenu, HoverCard, Tooltip, Popover | omit from ContextMenu |
| open/close delays | fixed contextual policy | 700 ms touch/pen fallback only | omit general delay configuration |
| location, origin, offset, strategy | fixed logical point placement | `bottom-start`, existing `--cui-menu-offset` and collision CSS | omit broad positioning API |
| click-outside, Escape, focus, keyboard | shared coordinator/Menu | no wrapper-specific escape hatch | adopt existing reasons and focus policy |
| scroll strategy | native top layer plus CSS anchor | shared anchored reconciliation | omit strategy selection |
| transition props | existing Menu CSS | `--cui-menu-duration` and easing | omit behavioral transition objects |
| theme and dimensions | existing Menu CSS | full `--cui-menu-*` contract, `size` | adopt without ContextMenu theme duplication |
| attach/contained/teleport | native top layer, inline DOM | no public surface | reject |
| scrim/persistent/modal policy | Dialog/Popover jobs | separate components | reject |
| forwarded overlay refs/methods | declarative state/native refs | no public controller | omit |
| dedicated native-preservation policy | no equivalent frozen VMenu surface | exact eligibility and native escape rules | Citry-specific required addition |

## 3. Public composition and anatomy

The family adds `CContextMenu`. It adds no item declaration. The required
`menu` slot accepts the existing `CMenuItem`, `CMenuCheckboxItem`,
`CMenuRadioGroup`, `CMenuRadioItem`, `CMenuGroup`, `CMenuSeparator`, and
`CMenuSubmenu` declarations with all current CMenu nesting and validation.

Template composition is literal:

```html
<c-CContextMenu aria_label="Document actions">
  <c-fill name="target" data="{ target_attrs }">
    <div c-bind="target_attrs" tabindex="0">
      Quarterly report.pdf
    </div>
  </c-fill>
  <c-fill name="menu">
    <c-CMenuItem value="rename">Rename</c-CMenuItem>
    <c-CMenuItem value="duplicate">Duplicate</c-CMenuItem>
    <c-CMenuSeparator />
    <c-CMenuItem value="delete" intent="danger">Delete</c-CMenuItem>
  </c-fill>
</c-CContextMenu>
```

Python composition uses the same target binding and declarations:

```python
CContextMenu(
    aria_label="Document actions",
    slots={
        "target": lambda data: CButton(
            attrs=data.target_attrs,
            slots={"default": "Quarterly report.pdf"},
        ),
        "menu": (
            CMenuItem(value="rename", slots={"default": "Rename"}),
            CMenuItem(value="duplicate", slots={"default": "Duplicate"}),
            CMenuSeparator(),
            CMenuItem(
                value="delete",
                intent="danger",
                slots={"default": "Delete"},
            ),
        ),
    },
)
```

The exact stable anatomy is:

```text
div.cui-context-menu-host[data-citry-ui-part=context-menu]
  TARGET-ELEMENT[data-citry-context-menu-target]  # private marker
  span[popover=manual][aria-hidden=true]
      [data-citry-context-menu-point]  # private
  div[popover=manual][role=menu][aria-label=aria_label]
      [data-citry-ui-part=menu]
    existing CMenu declaration output
```

The root is an ordinary `div` with component CSS `display: contents`. It owns
identity, initialization, inheritance, observation, and lifecycle, but no box
or ARIA role. The target slot must settle to exactly one direct Element with
the complete `target_attrs` mapping bound to that Element. A server-resolved
Citry component such as CButton is valid only when it settles to that one
standard native Element. Text-only output, multiple direct Elements, fragments
that hide the bound marker, customized built-ins, custom-element target roots,
detectable authored open-shadow target roots, and a target moved outside the
root are invalid. Ordinary descendants may be rich application content subject
to the native-preservation rules.

The private point remains an inline DOM child in the same actual root and
ancestry as the target and surface, but `popover="manual"` promotes it to the
top layer while an opening request is pending or the Menu is open. This avoids
fixed-containing-block offsets from transform, filter, perspective, or contain
ancestors without teleporting its DOM ownership. It is fixed, 1 CSS px by 1
CSS px, noninteractive, pointer-transparent, empty, and `aria-hidden`. It is
deliberately not `inert`: the shared anchored-layer eligibility walk rejects an
inert trigger. Private CSS is exact before owned top/left and the generated
`anchor-name` are added:

```css
position: fixed;
inset: auto;
width: 1px;
height: 1px;
margin: 0;
padding: 0;
border: 0;
background: transparent;
overflow: visible;
pointer-events: none;
```

Its ID and private marker are not public CSS or query contracts.
It is the geometric and anchored-layer trigger; the semantic target is
registered as an inside element and focus owner.

The surface is the same root Menu surface used by CMenu and CSplitButton. It
has no visible activator and therefore uses required `aria-label`, never
`aria-labelledby` to the arbitrary target. The target is not assigned
`role=button`, `aria-expanded`, or Menu Button keyboard semantics. Consumers
must make the target or a descendant focusable when keyboard contextual access
is required. A native focusable descendant is preferred over a redundant
wrapper Tab stop.

Identity is exact. Supplied `id="document-actions"` yields root
`id="document-actions"`, target `id="document-actions-target"`, surface
`id="document-actions-menu"`, and private point
`id="document-actions-point"`. When omitted, the base is
`cui-context-menu-{self.id}`. A target-authored ID is rejected because it would
break the owned correlated set. CMenu continues to derive declaration and
submenu IDs from the surface base.

No JavaScript leaves the target completely native. As in CMenu, a server-closed
surface remains hidden by native Popover presence and an initially open surface
is visible in ordinary flow. The private point remains hidden by its own native
Popover presence and has no fallback content. Enhancement may suppress native
invocation only after target, point, declarations, labels, IDs, and layer
capability validate.

## 4. Server inputs and client inputs

### Public Python inputs

| Input | Type and default | Destination and exact rule |
|---|---|---|
| `id` | `str | None = None` | component root base; nonempty HTML-safe token when supplied |
| `aria_label` | `str`, required | Menu surface accessible name; Unicode string must contain non-whitespace text and no U+0000 |
| `open` | `bool = False` | server/uncontrolled visibility baseline |
| `disabled` | `bool = False` | blocks all custom invocation; native context menu remains available |
| `loop` | `bool = True` | existing CMenu root navigation policy |
| `close_on_select` | `bool = True` | existing CMenu root action-close policy |
| `size` | `CMenuSize = "md"` | existing CMenu size vocabulary and CSS reflection |
| `class_` | `CClassValue | None = None` | public ContextMenu host/root classes |
| `style` | `CStyleValue | None = None` | public ContextMenu host/root styles; Menu variables inherit to the surface |
| `attrs` | `Mapping[str, object] | None = None` | public ContextMenu host/root safe attributes, narrowed by section 15 |
| `target_attrs` | `Mapping[str, object] | None = None` | copied into `target_attrs` slot data after validation |

Booleans reject integers. Mappings are copied once and never mutated. `size`
accepts only the current CMenu literals. Server `open` is not controlled state;
control begins only when the client `open` property is non-null.

### Exhaustive client inputs

| Client property | Accepted values | Invalid/null/removal behavior |
|---|---|---|
| `open` | `boolean | null` | Boolean controls visibility. `null` or removal releases control from the current committed visible state. Invalid reports once and releases in the same way, matching CMenu. |
| `disabled` | `boolean` | Invalid/removal uses the server fallback. Becoming true closes with `disabled`. |
| `loop` | `boolean` | Invalid/removal uses the server fallback; forwarded to the one Menu controller. |
| `closeOnSelect` | `boolean` | Invalid/removal uses the server fallback; forwarded to the one Menu controller. |
| `size` | current `CMenuSize` literal | Invalid/removal uses the server fallback. |
| `onOpenChange` | `(bool, CContextMenuOpenChangeDetail) -> bool | None`, or `null` | `null`/removal means no callback; invalid reports once and uses no callback. Only literal `true` is the controlled opening claim below; every other return refuses that one opening request. |
| `onAction` | `(str, CMenuActionDetail) -> None`, or `null` | existing CMenu callback; invalid reports once and uses no callback. |

`aria_label`, IDs, slots, declaration structure, attrs mappings, and long-press
timing are structural server inputs, not client properties. There is no client
coordinate, target, placement, long-press-delay, or native-preservation prop.

The exact family/package exports are four names:

- `CContextMenu`
- `CContextMenuTargetSlotData`
- `CContextMenuMenuSlotData`
- `CContextMenuOpenChangeDetail`

The ContextMenu family imports but does not re-export CMenu declarations,
aliases, slot-data classes, or action/choice details. Consumers import those
from their existing CMenu exports. Private surface records, point adapters,
controller options, parsers, validators, and client records are excluded from
all `__all__` lists.

## 5. State model

The component has one visibility axis and one component-owned invocation
record.

### Visibility ownership

- Before a non-null client `open`, state is uncontrolled from the server
  baseline.
- An accepted uncontrolled request commits synchronously, updates native
  Popover/layer state, then invokes `onOpenChange` once.
- A non-null client `open` controls visibility. User paths request; they do not
  flash an unaccepted state.
- `open=null` or invalid `open` releases control from the current committed
  visible state, exactly matching CMenu. Configuration and callback invalidity
  use the CMenu server/no-callback fallbacks rather than a wrapper last-valid
  cache.
- Forced `disabled` or ancestor/modal closure follows CMenu's controlled
  forced-close rule and cannot be refused.
- Native toggle, morph, invalid anatomy, and cleanup reconcile through the
  existing CMenu generation. They do not create a second visibility state.

### Invocation record

The private record contains generation, kind (`pointer`, `keyboard`,
`long-press`, or `external`), viewport point, invoking composed-path Element,
deep active-element snapshot, pointer identity when applicable, and pending
native-event suppression token. It is not public mutable state.

For every closed opening request, the adapter computes candidate coordinates,
writes them synchronously, calls the point's `showPopover()`, and verifies its
top-layer geometry before entering the one Menu request path. For an
uncontrolled Menu, it then proves shared layer eligibility, commits the Menu
surface open above the point, runs the uncontrolled notification, rechecks the
connected root, owner token, generation, logical/native open state, point,
surface, and layer registration after callback reentrancy, and only then
prevents the matching native default. For a closed controlled Menu, ordinary
Citry `$c-props` effects do not reflect owner mutation before a trusted event
listener returns. The component therefore uses an explicit public claim
handshake:

- `onOpenChange(true, detail)` must synchronously set the owner's `open=true`
  and return the literal Boolean `true` to claim the native default;
- only that exact return, while the same root/generation remains connected and
  the shown point remains structurally/layer eligible, commits the requested
  point and calls
  `preventDefault()`;
- `false`, `null`, a thenable, any other value, a missing/invalid callback,
  callback removal, mutation, or disconnection refuses, discards the point,
  cancels the pending Menu request, hides the point before listener return, and
  leaves the native default untouched;
- a literal-true callback that synchronously invalidates the external owner is
  diagnosed before the request is rolled back and the native default resumes;
- the next props settle after a claim must supply `open=true`; otherwise the
  claim expires at the next task, remains closed, hides the point, and
  diagnoses one broken owner claim without inventing a native replay; and
- a later external owner change to true uses a fresh target-derived fallback,
  never stale refused event coordinates.

Callback return values are ignored for uncontrolled openings and all closes.
The handshake is limited to a controlled closed-to-open request because only
that path must decide a native default in the same event turn.

When already open, a valid new pointer, keyboard, or long-press invocation
moves the already-open point synchronously before focus, resets Menu focus to the first
enabled item, updates the
invocation/return-focus snapshot, and remains open. It emits no false-to-true
callback. A newer invocation generation cancels all prior point, key-dedupe,
long-press, and focus-return work.

External false-to-true control with no accepted pending invocation derives a
point from the current target/focused descendant, shows and verifies the point,
then opens the Menu surface. External true on first
initialization follows the same rule. External control owns visibility, not
arbitrary viewport coordinates.

### Disabledness and target eligibility

Effective disabledness is component disabled OR a native target that matches
`:disabled`, including dynamic fieldset ancestry and the first-legend
exception. One shared fieldset-ancestry observer path, already used by Menu,
must track correlated moves. Disabled state cancels timers/tokens, restores the
native menu, and closes custom state with reason `disabled`.

Pre-readiness initialization or capability failure removes any tentative point
top-layer entry, leaves readiness absent, performs no callback, and restores
the immutable server fallback exactly: server-closed stays hidden and
server-open stays readable in flow. After readiness, an observed structural or
capability invalidation stops custom event prevention, closes and unregisters
the surface, hides the point only after that completion, removes readiness, and
leaves native target behavior. Repair revalidates the whole correlated set and
reconciles the latest owner input once without a spurious callback.

`data-invocation` is present only while the root is logically open with a valid
accepted point. It is set to `pointer`, `keyboard`, `long-press`, or `external`
in the same synchronous point commit, changes on accepted same-open
reinvocation, survives only an eligible retained-root handoff, and is removed
on refusal, close completion, fail-closed invalidation, replacement, or
cleanup.

## 6. Slots and slot data

| Slot | Cardinality and accepted content | Slot data |
|---|---|---|
| `target` | required; exactly one direct standard HTML Element, directly or from one server-resolved Citry component, with the full mapping bound; descendants may contain ordinary application content subject to section 15 | `CContextMenuTargetSlotData(target_attrs: dict[str, object])` |
| `menu` | required; one or more direct existing CMenu declarations, including transparent framework wrappers allowed by CMenu | `CContextMenuMenuSlotData()` |

The `menu` slot has no forwarding wrapper and no raw item model. It enters the
same `_MenuServerContext`, registry, direct-output validator, radio/group
validator, and collection renderer as CMenu and CSplitButton.

The target binding is structural. `target_attrs` contains the generated target
ID, private `data-citry-context-menu-target` ownership marker, and validated
consumer target attributes. It deliberately contains no
`data-citry-ui-part`, `data-disabled`, `aria-disabled`, or native `disabled`,
so a CButton or another server-resolved native component keeps its own part,
state, and primary behavior. The consumer may add ordinary content and safe
attributes, but may not replace or partially bind the mapping.

The target root may contain inputs, links, selectable text, images, audio,
video, and embedded content. Those paths intentionally preserve the native
menu. A target that consists solely of such preserved paths is valid but the
custom Menu may be reachable only by an explicit non-preserved focusable
subregion; documentation must make that consequence visible.

## 7. Callbacks, native events, and methods

`onOpenChange(next_open, detail)` is synchronous. The detail is:

```python
class CContextMenuOpenChangeDetail(TypedDict):
    reason: Literal[
        "contextmenu",
        "keyboard",
        "long-press",
        "escape",
        "outside",
        "focus-outside",
        "tab",
        "action",
        "native",
        "disabled",
        "ancestor",
    ]
    controlled: bool
    forced: bool
    source: object | None
    clientX: float
    clientY: float
```

Opening uses `contextmenu`, `keyboard`, or `long-press`. A mouse/unknown-pointer
native event uses `contextmenu`; a native touch/pen event for the active press
and an accepted 700 ms fallback use `long-press`. External owner changes do not
invoke the callback. Every opening request detail contains that request's
viewport-clamped candidate coordinates, even when controlled ownership refuses
it. Acceptance alone commits the candidate. Same-open and close callbacks use
the latest committed point: trusted pointer coordinates for
`contextmenu`/`long-press`, or the derived target point for keyboard/external
opening. Close callbacks retain those numbers through callback return and then
clear the record. `source` is the original composed-path target Element for
context/long-press, the focused Element for keyboard, the focused item for
Escape/Tab/action, the outside/focus target for those dismissals, the surface
for native toggle, the target for disabled, and the responsible ancestor/modal
Element for ancestor close. It is null only when the responsible Element was
removed before a forced notice. Event objects are never retained in detail.

`forced` is true for disabled/ancestor force-close and for a native-preserved
context request that must remove an already-open custom Menu. It is false for
ordinary accepted requests and dismissals. A controlled open claim must return
Boolean `true` from `onOpenChange`; section 5 defines the only path on which a
return value is observed.

`onAction(value: str, detail: CMenuActionDetail)` and every declaration-level
action, checked-change, and radio-change callback preserve CMenu's exact order
and reentrancy guards. ContextMenu introduces no action detail alias. A
successful action may close with reason `action` according to
`closeOnSelect`; callback removal or DOM mutation cannot make a stale close
run.

One CContextMenu instance represents one logical command subject. The owner
closure already knows that subject, while `CMenuActionDetail` identifies the
chosen item/path. Root action detail therefore does not duplicate the original
context target or point. If one visual container has multiple independently
actionable subjects, render one CContextMenu per subject; multiple-target
identity is deferred. Open/close detail still exposes the accepted coordinates
for visibility diagnostics.

Native events remain real events. The component does not dispatch a synthetic
`contextmenu`, `toggle`, action, or custom open event. Consumer listeners on
safe non-owned events see browser events in the component's isolated root
scope; `$event`, `$store`, `$dispatch`, and explicit globals are supported,
while ancestor component-local identifiers are not implicitly captured.
`onOpenChange` and `onAction` are the owner-local state surfaces.

`contextmenu`, ContextMenu/Shift+F10 keydown, and the touch/pen pointer sequence
are component-owned on the target destination and cannot be overridden through
attrs. The accepted trusted invocation is the only path that calls
`preventDefault`. The sole propagation exception is the one trusted derived
click matching an accepted synthetic touch/pen long press. A host capture
listener calls `preventDefault()` and `stopImmediatePropagation()` for that
one click so target `@click`, navigation, submit, and reset cannot run. Events
already observed by outer capture listeners cannot be undone. No contextmenu,
keyboard, ordinary pointer, or unmatched click path stops propagation.

There is no public imperative controller. Native `focus()` on a consumer-owned
focusable target and declarative client props are sufficient. Programmatic
`dispatchEvent(new MouseEvent("contextmenu"))` is untrusted and does not open;
programmatic controlled `open=true` remains supported.

## 8. Semantics, keyboard, focus, and assistive technology

### Semantics

The target keeps its authored native semantics. CContextMenu does not add a
Button or application role and does not claim Menu Button `aria-expanded`.
The surface is `role=menu`, vertical, and named by required `aria-label`.
Existing declaration output owns menuitem, checkbox/radio, group, separator,
disabled, checked, submenu, and label semantics exactly as CMenu specifies.

### Opening keys

When focus is the target or a composed descendant and the path is not native
preserved:

- `ContextMenu` key requests open;
- `Shift+F10` requests open;
- composing/repeating keydown is ignored;
- unmodified F10, Shift plus any other key, Alt/Control/Meta variants, and keys
  originating outside the target are untouched; and
- the accepted path prevents keydown default and records a one-task token so a
  browser-generated following `contextmenu` cannot open twice.

A refused controlled request does not prevent keydown. Its one-task token lets
the browser's native behavior proceed without making a duplicate custom
request. A controlled claim follows section 5's explicit `true` return rather
than attempting to observe a not-yet-settled `$c-props` effect.

Keyboard point fallback uses the deepest focused Element inside the target
when it has a nonempty rendered rect; otherwise it uses the target. The point
is the visible intersection rect's logical inline-start and block-end:
physical left/bottom in LTR, physical right/bottom in RTL. Section 11 defines
visual-viewport intersection and 1 px clamping. If neither rect intersects the
current visual viewport, or it is hidden, inert, disconnected, under a closed
Dialog/Popover, or outside the actual root, custom opening is rejected and
native behavior remains.

### Menu keys

After acceptance, focus moves to the first enabled root Menu item. CMenu owns
ArrowDown/Up, Home/End, printable typeahead, Enter, Space, submenu arrows with
RTL inversion, Escape, Tab, Shift+Tab, disabled items, and focusable item
roots. ContextMenu adds no alternate item keyboard model.

### Focus return

Every accepted invocation snapshots the ownerDocument's composed deep active
Element before Menu focus moves. Escape and accepted non-link action close
attempt to restore that snapshot. A CMenu link action preserves native
navigation and skips focus restoration exactly as CMenu does. If a return
snapshot is disconnected, disabled, hidden, inert, or no longer in the same
open composed tree, focus tries the invoking Element, then the target when
natively focusable. If those fail, it uses the nearest open composed-ancestor
modal Dialog, otherwise `ownerDocument.body` with a temporary `tabindex=-1`.
The temporary attribute is removed after verified focus or the next task,
without deleting an authored value.

Target pointer/focus ordering has two bounded tokens. Every trusted unmodified
secondary pointerdown within the owned target, including a path that may later
classify as native-preserved, defers its matching target `focusin` until the
corresponding `contextmenu`. An accepted custom invocation consumes the token
and repositions; a preserved request consumes it and issues only the one
`native` force-close; an absent event expires in the next task and closes once
as `focus-outside` if focus moved. Primary pointerdown requests one `outside`
close and records its expected focus target, so the following target `focusin`
cannot issue a second close request. Shift+secondary pointerdown is the
universal native escape: it never opens, force-closes an already-open custom
Menu as `native`, and leaves the platform event/default untouched.

Outside pointer, focus-outside, Tab, Shift+Tab, ancestor/modal force-close, and
owner-moved focus do not restore. A focus attempt is successful only if the
composed deep active Element becomes the requested node or one of its composed
descendants. Focus moved by the owner during a callback wins.

Because the target can be a nonfocusable region, documentation must include a
focusable target or descendant. Screen-reader and hardware testing must prove
the required Menu label, item focus, choice announcements, submenu expansion,
keyboard opening, and return behavior without claiming an announcement for the
arbitrary target itself.

## 9. Native forms and validation

CContextMenu is not a Form-associated control. It emits no name/value pair,
hidden input, required proxy, reset listener, or form callback. Its private
point and surface never submit.

Target descendants remain ordinary Form controls. Right click, selection,
validation, label activation, text editing, reset, and submission are not
intercepted on input, textarea, select, option, editable, or other preserved
paths. Menu declaration roots preserve CMenu's `type=button` and no-submit
contract.

A target native Button may submit or reset on primary activation according to
its own attributes. If the Context Menu is open, the target's primary
pointerdown requests an `outside` close without preventing the Button's click
or native activation. Controlled refusal leaves the Menu open and still does
not interfere with native form behavior. The sole exception is the exact
trusted click derived from an accepted synthetic long press; section 7
suppresses it specifically so holding a submit/reset target for context
commands cannot also perform the primary form action.

Dynamic fieldset disabledness only blocks custom invocation and closes an open
Menu. It does not rewrite unrelated target form attributes. External form
ownership and validation remain the target control's native concern.

## 10. Styling and theme contract

ContextMenu adds no second Menu theme. The surface and every declaration reuse
the full public CMenu selectors and `--cui-menu-*` variables. `class_`, `style`,
and `attrs` target the documented ContextMenu host/root. CMenu variables set on
that root or an ancestor inherit to the inline surface because no teleport
occurs. The surface has no separate ContextMenu attrs/class/style destination;
consumers use inherited variables and existing public Menu part selectors.

Public selectors are:

- `[data-citry-ui-part="context-menu"]`
- every existing CMenu public part selector from `menu.md`

Citry applies no cursor, selection, touch-action, user-select, outline,
dimensions, or layout styling to consumer target content. Consumers style the
target with their own bound class/style, not a ContextMenu target part. The
component root has only `display: contents` plus state reflections; overriding
that structural display is outside the styling contract. The private target
and point markers and IDs are not public.

There are no ContextMenu-specific public variables. Point separation is the
existing CMenu chain `--cui-menu-offset` with CMenu's exact `0.375rem`
fallback. All colors, borders, shadows, widths, density, motion, danger,
selected state, submenu geometry, and focus styles are CMenu variables. There
are no public x/y, transform-origin, z-index, or long-press variables.

Root reflections are `data-open`, `data-disabled`, `data-size`, and
`data-invocation` with `pointer | keyboard | long-press | external` only under
section 5's open accepted-record rule. The target keeps only its own semantic
component/native state. Surface/item reflections remain CMenu's exact
contract. Reflections are component-owned, settled-state outputs and cannot be
authored through attrs.

## 11. Environmental behavior

- **LTR/RTL:** pointer coordinates remain physical viewport coordinates. Both
  JavaScript keyboard fallback and CSS placement use
  `getComputedStyle(surface).direction`; a target-local `dir` does not override
  that one source. The surface uses logical `bottom-start` in both directions,
  growing physical right in LTR and physical left in RTL from a logical-start
  point. Existing CSS collision flips and CMenu submenu direction handle
  surface direction.
- **Narrow and 400% zoom:** the adapter clamps the point through the exact
  visual-viewport algorithm below; CSS collision contains the surface. The
  Menu's existing max block/inline sizes and scrolling apply. No horizontal
  page overflow is introduced.
- **Visual viewport:** each point is converted into the layout-coordinate
  bounds described by `visualViewport.offsetLeft`, `offsetTop`, `width`, and
  `height`, falling back to the layout viewport. A 1 px point clamps to
  `[left, right - 1]` and `[top, bottom - 1]`. A target fallback first
  intersects its rect with those bounds; no intersection rejects custom open.
  CSS collision handles surface overflow but is not falsely treated as a clamp
  for an offscreen anchor. Pointer/long-press invocation stores its offset from
  the visual viewport origin, so viewport pan keeps the Menu at the same screen
  point. Keyboard/external invocation recomputes the visible target/focused
  rect so it follows that owner. Losing all visible target intersection on a
  target-derived repair closes through the shared structural `ancestor` path.
  While open, visualViewport/window resize or scroll batches one repair frame;
  accepted invocation point writes never wait for a frame.
- **Touch/pen:** one 700 ms trusted primary-pointer fallback is armed only on a
  non-preserved path. It never prevents pointerdown, captures a pointer, or
  changes touch-action/callout/selection CSS. Before acceptance, its timer
  cancels on pointerup/cancel, second pointer, movement beyond 10 CSS px,
  scroll, blur, hidden document, disabledness, mutation, disconnection, a
  noncollapsed target Selection, or a native `contextmenu` event. An accepted
  fallback records pointer ID when the derived PointerEvent supplies one,
  pointer type, deepest composed target, origin within 10 CSS px, button, and
  owner generation. The token remains
  generation-owned through the matching pointerup and expires on the first
  matching trusted derived touch/pen click, 1,500 ms after that pointerup, or
  an absolute 10,000 ms after acceptance, whichever happens first.
  Pointercancel, a new pointer sequence, blur, hidden document, invalidation,
  disconnection, or cleanup removes it. That one click is suppressed under
  section 7. A matching native contextmenu before the timer cancels the timer
  and opens as `long-press`; one after accepted fallback is deduplicated and
  prevented only while that custom open remains accepted. Refusal creates
  neither suppression token.
- **Mouse:** secondary-button `contextmenu` is the opening event. Primary target
  interaction closes as `outside` without blocking native click. Auxiliary
  click is untouched.
- **Shift+secondary-click:** this is a universal native escape. Firefox may
  omit `contextmenu`; Chromium/WebKit may emit it. Citry opens in neither case
  and never prevents the platform default.
- **Selection/copy:** in a Document, any noncollapsed Selection with a Range
  intersecting the target preserves native context behavior. In an open
  ShadowRoot, the adapter calls
  `selection.getComposedRanges({shadowRoots: [actualRoot]})`, recreates each
  returned boundary pair as a temporary ownerDocument Range, and tests target
  intersection. If that API is unavailable or throws while the document or
  actual-root Selection exposes noncollapsed/nonempty shadow selection, the
  adapter conservatively preserves native behavior. Citry never clears or
  rewrites a Selection.
- **Reduced motion:** inherited CMenu transitions become immediate according to
  the existing contract. Point movement itself is not animated.
- **Forced colors:** inherited CMenu forced-color border/focus treatment applies;
  the target receives no color override.
- **Light/dark/nested schemes:** inline DOM preserves the nearest scheme and
  existing Menu variable inheritance.
- **Print:** JavaScript does not open. The target prints normally; Menu fallback
  follows CMenu's print policy; the private point and enhanced closed overlay
  are not printed.
- **No JavaScript or pre-readiness capability failure:** target behavior and
  the browser context menu are native. A server-closed Menu remains hidden; an
  initially open surface remains readable in flow, exactly as in CMenu. A
  post-readiness capability loss instead uses section 5's ordered
  surface-close/point-hide invalidation so no enhanced orphan remains.

Mobile callout timing varies by operating system and cannot be release-proved
by desktop synthetic PointerEvents. Real touch/pen devices are mandatory
manual evidence. If a platform displays its native callout without a
cancelable `contextmenu`, Citry does not attempt CSS suppression.

## 12. Overlay and layering behavior

The point and surface stay inline in DOM and enter the native top layer through
their own `popover="manual"` attributes. On a closed request, the adapter writes
and shows the point first, verifies its viewport rect, then registers and shows
the Menu surface above it. The point is the CSS anchor and the shared
anchored-layer trigger but is not a second logical layer. On close, descendants
and the Menu surface finish closing and unregistering before the point hides.
Controlled refusal, broken claim, pre-readiness failure, and cleanup hide a
tentatively shown point; same-open reposition moves it without hide/show. A
native or hostile point close while its Menu surface is open invalidates and
closes that surface before completing point cleanup. The target is an explicit
inside element, so a second right click can reposition without a coordinator
close/open race.

The adapter closes on primary target pointerdown and target focusin as
`outside`/`focus-outside` subject to section 8's pointer/focus dedupe tokens and
verified focus return. All other outside, Escape, focus, Tab, modal, ancestor,
submenu, and native-toggle decisions are the existing coordinator and CMenu
controller.

If an already-open custom Menu receives a native-preserved context request
(selection, link, editable/media path, native marker, custom host, or universal
Shift escape), it force-closes once with `reason="native"`, `forced=true`,
then leaves the platform default untouched. A controlled true owner is
suppressed against resurrection until it commits false then true or a newer
accepted custom invocation clears suppression. Closed state receives no
callback for a preserved request.

One ContextMenu registers one root layer. Existing submenus register as child
layers. A ContextMenu opened inside another anchored surface acquires the
existing inferred logical parent. Opening a later modal outside its ancestry
force-closes with `ancestor`. A ContextMenu inside the current modal remains
eligible because point, target, and surface share that ancestry.

Nested ContextMenu targets use deepest-boundary arbitration for every owned
pointer, key, and context event. Each host reads the composed path and finds
the nearest `[data-citry-context-menu-target]` boundary. Only that boundary's
live owner may act; an invalid or unowned nearest boundary blocks ancestor
fallback. The inner owner does not stop propagation, and every outer host exits
before requesting or changing state because the nearest boundary is not its
own. Contextmenu inside an open Menu surface is never treated as a target
reinvocation; native-preserved links/media remain native there.

Document and open ShadowRoot roots are supported. The component may live in an
open ShadowRoot; target, point, and surface must share the same actual root.
Every custom-element descendant and every detectable open-shadow host is
native-preserved. A closed shadow on a standard host needs the explicit native
escape marker because outside code cannot classify it. Correlated movement
between Document/open ShadowRoot scopes refreshes the shared coordinator
registration exactly once.

Events do not cross iframe Document boundaries. A parent component cannot own
context invocations within child iframe content. A same-origin or cross-origin
iframe may host its own Citry instance and coordinator inside that Document.
The iframe Element in the parent target is native-preserved. Cross-document
surface ownership and point positioning are not supported.

There is no public z-index, portal, attach, strategy, offset, collision, modal,
persistent, or scrim prop. CSS Anchor Positioning and the shared coordinator
are mandatory capabilities. Missing, mixed-generation, or incompatible
capability restores the exact server fallback before readiness or uses the
ordered post-readiness invalidation in section 5.

## 13. Collections, async data, and identity

ContextMenu has no collection model of its own. `_build_menu_root_snapshot`,
`_MenuRegistry`, `_MenuServerContext`, `CInternalMenuCollection`, and all CMenu
declaration classes remain the sole server parser/registry. Existing direct
declaration, transparent wrapper, canonical value, duplicate, group, radio,
separator, submenu, and empty-collection rules apply byte for behavior.

The ContextMenu facade passes `declaration_slot="menu"` into the shared
builder, as SplitButton already proves. It must not instantiate a hidden public
CMenu, forward through an item-model array, or translate declarations into a
second record type.

Client add/remove/reorder/disable/choice updates reconcile through one CMenu
controller. Point or target state does not key items. Existing item values and
paths are the only Menu identity. Reinvocation while open leaves collection
identity and controlled choice state intact but resets active focus to the
first enabled root item.

Async declaration replacement follows ordinary signed Citry morph. There is no
fetching, remote collection, virtualization, filtering, or loading surface in
v1. Empty or invalid settled collection fails closed and restores native
target behavior.

## 14. Server render, morph, and cleanup

Server render performs two-stage validation:

1. synchronous server preflight validates public inputs, copied mappings,
   required target/menu slot presence, required nonblank surface label, and
   registered Menu declaration output. It does not claim to parse arbitrary
   target DOM before render;
2. synchronous browser initialization, before any native suppression, confirms
   exactly one direct standard target Element and the complete bound private
   marker/identity; settled validation then confirms retained object identities, exact
   parentage/order, IDs/IDREFs, roles, owned attrs/reflections, point and
   surface capability, actual-root equality, nonempty Menu collection, and
   CMenu controller generation before readiness.

Every owned event, client-prop reconciliation, external or same-open request,
geometry callback, and mutation/repair hook repeats a synchronous preflight of
the live owner token, target identity/parentage/actual root, effective
disabledness, current native-preservation path, target `shadowRoot`,
point/surface capability, and Menu generation before changing state, invoking
a callback, or preventing a default. `attachShadow()` does not itself produce
an observable light-DOM mutation, so an already-open idle component may detect
a newly attached open shadow only at the next one of these hooks; no polling
claim is made. Once observed, post-readiness invalidation follows section 5.

The root receives `data-citry-context-menu-initialized` only after the shared
Menu controller has completed a successful nonempty collection reconcile, the
point and target validate, the surface is named, and the layer capability is
current. It is removed synchronously on invalidation and cleanup. A copied
attribute on a clone is never proof of ownership; readiness also requires a
live root-object owner token.

Handoff fingerprints include immutable server baselines for root/target/point/
surface IDs, aria label, open, disabled, loop, close-on-select, size, Menu
declarations, allowed attrs, and actual root. Retained root, target, point, and
surface object identity plus equal baselines may hand off uncontrolled Menu
state, current valid CMenu configuration, accepted point, invocation kind, and
CMenu collection state. It never hands off an active long-press timer, derived
click token, keyboard/pointer dedupe token, pending controlled request, stale
event object, or focus-return task.

An eligible retained open handoff preserves the already-open point and surface
objects and transfers one owner token before stale cleanup. Old cleanup may not
hide either Popover after a newer controller owns that exact object. A retained
closed handoff keeps the point hidden. Every replacement or changed-root path
uses the full surface-close/unregister then point-hide order.

If the target, point, or surface is replaced, the old instance closes and
unregisters its surface silently, hides its point, removes readiness, cancels
work, and the new instance initializes from current server/client inputs with a
target fallback point.
Same-marker clones do not inherit a controller. A changed server baseline wins
per changed axis; unchanged uncontrolled axes may hand off. Controlled props
remain owner-authoritative.

Mutation recovery restores the exact owned IDs, roles, label, Popover/anchor
attrs, part markers, target marker, private point geometry, and reflections as
one correlated set. Unknown reserved-prefix attributes or unauthorized changes
fail closed rather than becoming a new baseline. Consumer content mutations
inside a retained valid target are allowed and do not rebuild Menu items.

Cleanup cancels long-press, key, suppression, resize, focus, and repair tasks;
removes target/viewport listeners and observers; closes descendants and the
surface; calls the one Menu controller cleanup; unregisters
layer/fieldset/root-scope records by owner token; hides then removes the point;
clears readiness; and restores no stale attribute or Popover state onto a newer
instance. Removing/restoring the same signed component twice must settle with
root count equal to readiness count, coordinator registrations, and zero orphan
point top-layer entries.

## 15. Security and content trust

Visible strings are escaped by Citry. `aria_label`, IDs, declaration values,
and paths reject U+0000; required labels contain non-whitespace accessible
text. ContextMenu is not an HTML sanitizer. Trusted application slot content
may render ordinary HTML and server-resolved Citry components within the exact
target/declaration boundaries.

All attrs mappings are copied once, compared case-insensitively for duplicate
destinations, and reject object spreads and Citry/Events runtime namespaces.
Every destination rejects `is`, customized built-ins, `x-html`, `x-text`,
`x-data`, `x-init`, `x-effect`, `x-id`, `x-if`, `x-for`, `x-show`, `x-ignore`,
`x-teleport`, `hidden`, `inert`, `popover`, and dynamic/property aliases to an
owned attribute.

The host is the one public ContextMenu root and the sole destination for
`class_`, `style`, and `attrs`. Root attrs reserve ID, role, tabindex, all ARIA
names, the public part, ownership/readiness, open/disabled/size/invocation
reflections, anchor/Popover attrs, every owned event directive/listener, and
all `data-citry-*`/`data-cid*` names. They permit `dir`, `lang`, test/data
attributes outside reserved prefixes, classes/styles, and unrelated native
listeners/bindings under the ordinary isolated component-root expression
boundary. The Menu surface has no ContextMenu attrs destination; its required
label, role, Popover/anchor attrs, CMenu parts, and state are wholly owned.

`target_attrs` reserves the generated ID, private owner marker,
`aria-expanded`, `aria-controls`, anchor/Popover attrs, and the owned
`contextmenu`, keydown, pointerdown/move/up/cancel, scroll, visibility, and blur
directives/listeners. It permits the target's pre-existing native role and
semantic attrs, classes/styles, safe ARIA, and unrelated events. ContextMenu
rejects a mapping that authors `role` or native `disabled`. A server-resolved
target component independently rejects every other attribute owned by its
public API; authors pass those values through that component's inputs.

The public `data-citry-context-menu-native` marker is the sole allowed
consumer-authored exception to the reserved ContextMenu prefix and may appear
on a target or descendant. A trusted event whose composed path contains it is
never custom.
The same preservation applies without a marker to input, textarea, select,
option, editable content, anchors with `href`, image, audio, video, object,
embed, iframe, every hyphenated custom element, customized built-ins,
detectable open-shadow hosts, and any target-intersecting Selection determined
by section 11's Document/composed-range algorithm. A closed shadow on a
standard host is indistinguishable from ordinary
standard-element content outside that root; the consumer must put the native
escape marker on that host. Automatic classification of that case is deferred.
These rules are safety boundaries, not a promise to classify arbitrary
script-created widgets.

Only trusted native input can invoke. Controlled state may still open through
owner code. Diagnostics never include target text, selected content, form
values, clipboard data, URLs, callback objects, or event objects.

## 16. Assets and performance

Context Menu reuses the Menu surface and collection runtime, anchored-layer
coordinator, native-fieldset tracking, and Menu styling. Combined Menu, Split
Button, and Context Menu pages must emit each shared payload once. Context Menu
adds no icon, font, image, network, worker, or polling dependency.

One initialized instance owns only its bounded target listeners and
point-popover guards. Long-press cancellation listeners exist only while a
gesture is armed, and geometry repair batches to one animation frame. Shared
root-scope, fieldset, mutation, and layer registries must return to baseline
after final cleanup.

Asset accounting uses ordinary incremental and standalone family measurements.
The incremental measurement catches growth in Context Menu-specific payloads;
the standalone and catalog-wide measurements catch growth moved into shared
dependencies.

The stable production limits are:

| Asset | Raw | gzip | Brotli |
|---|---:|---:|---:|
| Context Menu-specific incremental JavaScript | `< 32 KiB` | `< 10 KiB` | `< 9 KiB` |
| Complete Context Menu JavaScript, including shared dependencies | `< 160 KiB` | `< 34 KiB` | `< 30 KiB` |
| Complete Context Menu CSS, including shared dependencies | `< 20 KiB` | `< 3 KiB` | `< 2.5 KiB` |

The asset report and focused tests are authoritative for current measurements.
Behavior, native-preservation rules, diagnostics, lifecycle safety, and cleanup
cannot be removed merely to meet a limit; a legitimate overage returns to
design review.

## 17. Acceptance matrix

Design implementation is accepted only with all of the following focused,
human-reviewable evidence:

| Area | Required falsifiers |
|---|---|
| Server/API | exact four exports; renderable `c-bind` template and real CButton Python target; private compatible target mapping; all existing declarations; input defaults/types; nonblank label; mapping snapshots; class/style/attrs land on the public host and variables cascade to the Menu surface; no ContextMenu surface destination; invalid target shape/binding/custom/open-shadow roots; no new registered item class |
| Shared extraction | full existing CMenu and CSplitButton focused server and Chromium suites unchanged before adapter; later cross-engine regression for controlled state, choices, submenu, form neutrality, ShadowRoot, morph, cleanup |
| Pointer opening | trusted secondary right click opens once at exact client point; preventDefault only after acceptance; pointer event on preserved content remains native; untrusted dispatch does nothing |
| Keyboard opening | ContextMenu and Shift+F10 from target and descendant; repeat/composition/modifiers rejected; deterministic LTR/RTL fallback; browser-following native event deduped; no keyboard event from outside target |
| Controlled state | literal-true same-turn claim, false/null/thenable/missing refusal with candidate coordinates, accepted committed coordinates, broken-claim expiry, callback removal, owner mutation, CMenu-exact null/invalid release, first/later external true, refused point discard/hide, disabled/ancestor/native forced close, no flash, exactly-once details and coordinates |
| Reinvocation | new right click and keyboard request while open repositions and focuses first item without false visibility callback; new generation cancels prior point/focus/timer work |
| Native preservation | input, textarea, select, contenteditable, link, image, audio/video, object/embed/iframe, every custom element, detectable open-shadow host, marked closed standard host, selected target text, universal Shift+secondary escape, disabled target/component; preserved secondary pointerdown/focusin/contextmenu produces only one native close request; real drag-selection inside light DOM and open ShadowRoot uses Document/composed ranges in all three engines; an already-open custom Menu force-closes once as native |
| Long press | touch and pen, 700 ms acceptance, movement threshold, scroll, second pointer, up/cancel/lost-up, selection, native-event-before/after timer, controlled accept/refuse, exact trusted derived-click suppression through pointerup plus 1,500 ms with absolute 10,000 ms acceptance deadline, pointer-ID reuse/new-sequence cancellation, target click/navigation/submit/reset not run while armed, no pointer capture/pointerdown cancellation/touch-action/callout CSS, mouse exclusion |
| Focus | secondary-pointer focus deferral, primary pointer/focus close dedupe, first enabled item; Escape/non-link action verified return; link action no return; disconnected/disabled/hidden fallback; composed modal/body temporary tabindex; outside/focus/Tab/ancestor no return; owner-moved focus wins |
| Menu parity | command/checkbox/radio callback order, close-on-select, loop, typeahead, disabled items, links, two-level submenu, RTL arrows, all CMenu reconciliation and action details |
| Point geometry | synchronous point `showPopover()` and rect verification before Menu registration/surface/focus; reverse surface-close/unregister then point-hide; center and every viewport corner; partially/fully offscreen targets; transform/filter/perspective/contain ancestors; exact visualViewport 1 px clamp; narrow surface, 400% zoom; surface computed direction drives JS and CSS despite target-local opposite `dir`; logical bottom-start in LTR/RTL; repair and same-open movement; Document/open ShadowRoot/current modal; contained surface in Chromium/Firefox/WebKit |
| Layering | deduped target primary click/focus close; outside/focus/Escape/Tab; target second right click no pre-close; preserved/Shift native forced close and suppression; nested ContextMenu inner wins; Popover/Dialog/Tooltip ancestry; coexisting sibling ordinary Menu shares one coordinator and right-click inside that Menu stays native/non-reinvoking; later modal force-close; no resurrection |
| Iframes | parent cannot intercept child; iframe Element native-preserved; separately initialized same-origin child works with its own coordinator; cross-origin explicitly unsupported |
| Morph/lifecycle | retained equal-baseline open/closed Popover handoff; changed axis; target/point/surface replacement; same-marker clone; hostile ID/role/label/anchor/part/runtime marker; root-scope move; attach open shadow while closed then external true and while open then next owned/prop/geometry hook; two remove/restore cycles; timers/listeners/layers/point top-layer entries/readiness return to baseline |
| Environment | no JS; server-open/server-closed pre-readiness capability failure preserves fallback; post-readiness loss closes surface then point; print, reduced motion, forced colors, light/dark/nested schemes, high contrast, long target text, narrow, 400% zoom, RTL, scroll containers, console cleanliness |
| Accessibility | Nu HTML, axe, browser AX label/roles/states, hardware/context keys, VoiceOver/NVDA/JAWS Menu name and focus, real touch/pen callouts, selected-text copy path |
| Assets/scaling | incremental, standalone, and catalog budgets remain within section 16 limits; shared payloads emit once; 1/10/100 roots keep bounded temporary-listener, observer, and coordinator counts; final cleanup zeroes registrants |

The disposable automated browser suite must run the trust, point, controlled,
keyboard, focus, layer, ShadowRoot, morph, and cleanup falsifiers in Chromium,
Firefox, and WebKit. Real-device and assistive-technology checks remain manual
release evidence, not inferred from desktop automation.

## 18. Compatibility classification

Stable public API consists of the four ContextMenu exports, inputs, two slots
and their data, callback/detail shape, required label, target binding, native
escape marker, public selectors/reflections, inherited Menu variables, and the
reuse of existing CMenu declarations/details. Removing native preservation or
accepting new target classes is a public behavior change.

Stable behavioral/structural contract includes one target Element, one Menu
surface/model, point/event fallback rules, controlled native-default ordering,
same-open reposition, keyboard and focus behavior, CMenu parity, no Form
participation, no teleport, logical placement, no-JavaScript fallback,
ShadowRoot/iframe boundaries, fail-closed capability policy, and cleanup.

Private implementation details include the point marker/ID, private surface
record/renderer, controller adapter option names, observer batching, exact
diagnostic codes, and compact emitted syntax. They may change only while the
stable outcomes and payload budgets remain.

Current compatibility classification is **new additive design**. The required
private CMenu extraction is internal refactoring but is gated by unchanged
existing behavior and asset identity. No CMenu public API or open-detail reason
union is extended.

## 19. Public documentation contract

The eventual public package must include `api.yml`, generated `api.md`, README,
quality/scaling/asset integration, and exactly these nine executable examples:

| Example | Page theme and order | Fixture and visible copy | Visible states and controls | Required interaction | Environmental profile | Focused evidence |
|---|---|---|---|---|---|---|
| `basic_context_menu.py` | “Start with a contextual action” first | template file row “Quarterly report.pdf”; Python CButton row “Invoices”; Rename, Duplicate, Delete | two closed targets, last action/status output | right click each; ContextMenu and Shift+F10 on focused target; run one action | light, ordinary width | renderable template/Python binding, exact target/menu anatomy, command/separator/danger action |
| `choices_and_submenus.py` | “Keep one Menu model” second | “Canvas card” with Show grid, Sort radio family, Export submenu | checkbox checked/unchecked, selected radio, closed/open submenu; event log | keyboard typeahead, choice changes, two-level submenu, action | RTL wrapper plus LTR peer, narrow 22rem | unchanged CMenu callback order, path, choices, submenu arrows, one shared runtime |
| `controlled_open.py` | “Own visibility without stealing native fallback” third | “Controlled diagram” target; owner state/claim result/candidate-coordinate panel | refused closed, claimed open, released uncontrolled, external open | toggle accept/refuse; trusted invocation; same-open second point; release; external open | light/dark side-by-side | literal-true claim, false/null refusal with uncommitted candidate, broken claim diagnostic, exact CMenu release, no flash/default theft |
| `native_content.py` | “Keep browser commands” fourth | selectable paragraph, input, editable note, link, image/media label, custom-element host, marked closed-shadow fixture, open-ShadowRoot selection, plain file row | native-preserved targets plus one custom eligible region; custom-open status | select/copy by real drag; right click every preserved path; Shift+secondary escape; custom row open; native request while custom open | light, long text, open ShadowRoot | no preventDefault on preserved paths, one deferred-focus/native-close ledger, composed-range selection remains, forced native close/no resurrection, iframe element boundary |
| `touch_and_pen.py` | “Bound long press” fifth | “Touch card” and “Scrollable card”; visible 700 ms/10 px/pointerup-plus-1,500 ms/absolute-10 s policy | idle, armed, accepted, canceled, controlled refused; event ledger | synthetic test controls for hold/move/scroll/lost-up/second pointer plus real pointer path; derived click target counter | coarse-pointer emulation and bounded scroll container | no pointerdown cancellation/capture/CSS suppression; exact timer/token/click suppression; manual-device disclaimer |
| `focus_and_keyboard.py` | “Return focus deliberately” sixth | focusable row with nested Button/link; three fallback controls | closed/open, removed/disabled return target, link action | both opening keys; Escape, command, link, outside, Tab/Shift+Tab; owner-moved focus | Document and composed modal fixture | first item, link no-return, verified snapshot/fallback/modal/body, primary/secondary pointer-focus dedupe |
| `layers_and_roots.py` | “Share the layer coordinator” seventh | outer/inner target, target inside Popover/Tooltip, coexisting sibling ordinary Menu, sibling Dialog, ShadowRoot target, same-origin iframe explanation | parent/child surfaces and modal state; layer/registration counters | inner-wins invocation, ordinary Menu right-click stays native/non-reinvoking, ancestor close, modal force-close, remove/restore twice | open ShadowRoot, Dialog, narrow nested scheme | one coordinator/runtime, logical parents, root-scope refresh, iframe non-bubbling, cleanup parity |
| `positioning_and_rtl.py` | “Anchor to the accepted point” eighth | four-corner board, transformed/filter/contain wrappers, partially/fully offscreen target, and long Menu | pointer/keyboard/external points; current coordinates and invocation reflection | open/reposition at every corner; scroll/resize repair; toggle root and target-local direction independently | LTR/RTL, 400% profile, visualViewport diagnostic, 18rem width | synchronous point-Popover then surface order, exact clamp/rejection, surface-owned bottom-start direction, three-engine collision containment |
| `customization_and_fallback.py` | “Use Menu styling and native fallback” ninth | two branded file rows; one server-open fallback and one server-closed fallback | host class/style/attrs and cascaded CMenu size/intent/focus states, open/closed no-JS copy | open and select under both brands; disable enhancement before and after readiness | light/dark nested schemes, forced colors, reduced motion, print | exact root destinations, inherited `--cui-menu-*`, root selector/reflections, no new theme, pre-readiness fallback vs post-readiness close, axe/console cleanliness |

The main guide must link to native `contextmenu`, APG Menu, and the native
browser path. It must explicitly warn against replacing editing/copy/link/media
menus and explain that ContextMenu/Shift+F10 requires a focusable target or
descendant. It must never advertise arbitrary coordinate control, right-click
as the only access path, or synthetic long press as guaranteed platform callout
suppression.

Structured docs distinguish component callbacks from native Alpine events and
state the isolated component-root expression boundary. Every preview must be
interactive, console-clean, initialized at the settled marker, and free of
serious/critical axe findings. The public catalog must not duplicate the CMenu
declaration API; it links to that family.

## 20. Open decisions and deferred work

There are no unresolved v1 API decisions. The following are explicitly
deferred:

- public virtual points, coordinate props, arbitrary placement, offsets, and
  collision strategies;
- multiple targets sharing one ContextMenu model;
- selection-aware command bars and editable text commands;
- synthetic callout suppression, configurable long-press delay, pointer
  capture, touch-action changes, and drag gestures;
- context menus inside iframe content owned by a parent Document;
- automatic classification of a closed shadow on a standard host and
  imperatively attached opaque descendant shadows; the native escape marker is
  the v1 path;
- portal/teleport, modal context menus, scrims, persistence, and global page
  interception;
- arbitrary custom-element targets, consumer shadow hosts, raw HTML item
  models, async/virtual collections, and rich interactive Menu content; and
- public methods, target selectors, Element references, or exposing the
  private point element.

The implementation sequence is frozen:

1. extract a private Menu surface record/renderer and prove all existing CMenu
   and CSplitButton focused server/browser behavior unchanged;
2. add external activation to the existing Menu controller and prove the
   default Button/SplitButton modes unchanged;
3. implement the small ContextMenu target/point/long-press adapter against the
   shared request/state/layer path;
4. add the focused three-engine, trust, lifecycle, asset, and scaling evidence;
5. complete an independent implementation review; and
6. only then add public registration, docs, quality, and release integration.

Implementation is blocked if the extraction requires copied Menu runtime, if
controlled native-default acceptance cannot be observed synchronously, if the
private real point cannot remain in the same actual root/modal ancestry, if
long press requires invasive pointer or CSS suppression, or if the strict
incremental payload cannot be met without deleting contract behavior.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
