---
title: ContextMenu
description: Offer target-relative application commands while preserving browser context actions.
---

# ContextMenu

Use `CContextMenu` for application commands that belong to one target region.
It opens the existing Citry Menu at a trusted pointer point or at a visible
point derived from the focused target. It does not create a second Menu model.

Keep the browser's native context menu when copy, spelling, editing, links,
images, media, or embedded content are the primary job. The
[`contextmenu` event](https://w3c.github.io/uievents/#event-type-contextmenu),
the [browser event guide](https://developer.mozilla.org/en-US/docs/Web/API/Element/contextmenu_event),
and the [APG Menu pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/)
describe the platform contracts that ContextMenu joins. The safest native
browser path is to render no ContextMenu for content that mainly needs browser
commands.

## Start with a contextual action

Bind every value from the required `target` slot to exactly one direct native
Element. Make that target, or a useful descendant, focusable so keyboard users
can press the Context Menu key or Shift+F10.

```citry-html
<c-CContextMenu aria_label="Document actions">
  <c-fill name="target" data="{ target_attrs }">
    <div c-bind="target_attrs" tabindex="0">
      Quarterly report.pdf
    </div>
  </c-fill>
  <c-fill name="menu">
    <c-CMenuItem value="rename">Rename</c-CMenuItem>
    <c-CMenuItem value="duplicate">Duplicate</c-CMenuItem>
  </c-fill>
</c-CContextMenu>
```

The target keeps its native semantics. ContextMenu does not add `role=button`,
`aria-expanded`, or Menu Button keys. A native focusable descendant is better
than adding an extra wrapper Tab stop when the content already has one.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccontext_menu/snippets/basic_context_menu.py" title="Start with a contextual action" />

## Keep one Menu model

The `menu` slot accepts the existing `CMenuItem`, `CMenuCheckboxItem`,
`CMenuRadioGroup`, `CMenuRadioItem`, `CMenuGroup`, `CMenuSeparator`, and
`CMenuSubmenu` declarations. Their values, choices, action ordering, item
callbacks, typeahead, submenu keys, links, disabled state, and validation are
the [Menu contract](/ui-library/components/menu/).

ContextMenu adds no item-model array or duplicate declaration API. Import Menu
declarations and `CMenuActionDetail` from their existing `citry_ui` exports.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccontext_menu/snippets/choices_and_submenus.py" title="Keep one Menu model" />

## Own visibility without stealing native fallback

Supply client `open` and `onOpenChange` together when application state owns
visibility. A trusted closed-to-open request has to decide whether to suppress
the browser menu before its event listener returns. The callback therefore
uses a narrow claim protocol:

1. Set the owner's `open` state to `true` synchronously.
2. Return the literal Boolean `true` in the same callback turn.

Every other return, including a Promise or another truthy value, refuses that
opening. The candidate coordinates remain available in the detail, but the
component does not commit them or prevent the native default. Returning
`true` without supplying `open=true` on the next settled props turn is a broken
claim: the component stays closed and reports one diagnostic.

Return values are ignored for uncontrolled opening and for every close.
`open=null` or prop removal releases control from the currently committed
visibility, using the same handoff as CMenu.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccontext_menu/snippets/controlled_open.py" title="Own visibility without stealing native fallback" />

## Keep browser commands

ContextMenu preserves native behavior for:

- input, textarea, select, option, and editable content;
- links with `href`, images, audio, video, object, embed, and iframe Elements;
- custom Elements and detectable open-shadow hosts;
- a noncollapsed Selection that intersects the target; and
- any composed event path containing `data-citry-context-menu-native`.

Put `data-citry-context-menu-native` on a standard host when outside code
cannot inspect a closed shadow. Shift plus secondary click is always a native
escape. Firefox may not dispatch `contextmenu` for that gesture, so
ContextMenu also recognizes the pointer sequence and never suppresses it.

If a custom Menu is already open, a protected native request closes it once
and leaves the platform default untouched. Citry never clears selected text.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccontext_menu/snippets/native_content.py" title="Keep browser commands" />

## Bound touch and pen fallback

An eligible primary touch or pen press can request the Menu after 700 ms. The
hold cancels for movement beyond 10 CSS pixels, scrolling, selection, another
pointer, pointer end or cancellation, blur, visibility loss, disabledness, or
structural change. Citry does not cancel pointerdown, capture the pointer,
change `touch-action`, disable selection, or apply callout-suppression CSS.

An accepted synthetic hold suppresses only its matching trusted derived click,
through pointerup plus 1,500 ms and never beyond the 10-second absolute
deadline. This prevents one hold from also navigating, submitting, resetting,
or running a target click. Other clicks keep their native behavior.

Desktop emulation cannot prove an operating system's callout timing. If a
platform shows a native callout without a cancelable `contextmenu`, Citry does
not claim to suppress it. Test real touch and pen devices before release.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccontext_menu/snippets/touch_and_pen.py" title="Bound long press" />

## Return focus deliberately

After an accepted request, focus moves to the first enabled Menu item. Escape
and a non-link command try the original deep focus snapshot, then the invoking
Element, then the focusable target. If those are unavailable, focus moves to
the nearest open modal Dialog or to the document body. A link action keeps
native navigation and skips focus return.

Outside pointer, focus outside, Tab, Shift+Tab, ancestor closure, and owner
focus movement do not restore focus. Owner-moved focus always wins.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccontext_menu/snippets/focus_and_keyboard.py" title="Return focus deliberately" />

## Share the layer coordinator

Nested ContextMenus use the deepest bound target. A ContextMenu inside a
Popover, Tooltip, or Dialog keeps that logical ancestry. A coexisting ordinary
Menu shares the same coordinator; right-clicking inside its open surface stays
native and does not reinvoke the ContextMenu. A later modal outside the ancestry
force-closes it. Point and Menu surfaces remain inline in the same Document or
open ShadowRoot, then use native Popover for the top layer.

Events do not cross iframe Document boundaries. A child document needs its own
Citry installation and coordinator. An iframe Element inside the parent target
keeps its native context menu.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccontext_menu/snippets/layers_and_roots.py" title="Share the layer coordinator" />

## Anchor to the accepted point

Pointer requests use the trusted event's viewport point. Keyboard and external
owner-open requests derive a visible logical start and block-end point from the
focused descendant or target. The Menu reads its own computed direction and
uses logical `bottom-start`, native CSS Anchor Positioning, and collision
fallbacks.

There is no public coordinate, target selector, Element reference, placement,
offset, or positioning-strategy input. A request whose target-derived rect is
fully outside the visual viewport is rejected rather than anchored to a stale
or arbitrary point.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccontext_menu/snippets/positioning_and_rtl.py" title="Anchor to the accepted point" />

## Use Menu styling and native fallback

`class_`, `style`, and `attrs` target the ContextMenu host. The host renders no
visual box, so set target presentation on the Element that binds
`target_attrs`. Existing `--cui-menu-*` variables inherit from the host or an
ancestor to the inline Menu surface. Existing Menu part selectors customize
its surface and items. ContextMenu adds no theme or coordinate variables.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ccontext_menu/snippets/customization_and_fallback.py" title="Use Menu styling and native fallback" />

Without JavaScript, the target stays ordinary native content. A server-closed
Menu remains hidden through native Popover presence, while an initially open
Menu remains readable in document flow. Before successful initialization,
ContextMenu does not suppress native requests. Capability loss after
initialization closes the enhanced Menu before removing its point.

## Distinguish callbacks from native events

`onOpenChange` and `onAction` are component callbacks supplied through
`$c-props`. `onOpenChange` describes requests and forced closes;
`onAction` uses the existing `CMenuActionDetail`. ContextMenu dispatches no
custom DOM event.

Native events remain Alpine listeners in allowed `attrs` or target content.
The ContextMenu root has Citry's isolated expression scope, so an attrs listener
cannot read ancestor-local `x-data` identifiers directly. Use `$event`,
`$dispatch`, `$store`, or an explicit global bridge. Use component callbacks
for owner-local state.

The component owns `contextmenu`, ContextMenu/Shift+F10 keydown, and its
touch/pen pointer sequence. It does not stop propagation on those paths. Only
the exact trusted click derived from an accepted synthetic long press is
prevented and stopped immediately so the target's primary action cannot also
run.

## Keep target and host attributes separate

`target_attrs` is copied, validated, and included in the target slot data. It
may carry ordinary classes, styles, safe ARIA, semantic native attributes,
nonreserved data, and unrelated native listeners. It cannot author the target
ID, ContextMenu marker, owned invocation events, `role`, native `disabled`,
Popover/anchor state, or Menu Button ARIA.

Host `attrs` accepts ordinary descriptive attributes, `dir`, `lang`,
nonreserved data, and unrelated native listeners. It cannot replace owned
identity, roles, ARIA, parts, reflections, lifecycle, Popover/anchor state, or
Citry runtime namespaces. Mappings are copied once. ContextMenu trusts ordinary
slot content as application content; it is not an HTML or URL sanitizer.

CContextMenu is not Form-associated. It emits no name/value pair and does not
participate in reset or constraint validation. Target descendants keep their
native Form behavior. A target Button may submit or reset on primary
activation; only the exact derived click from an accepted synthetic long press
is suppressed.

<!-- UI_LIBRARY_API_REFERENCE -->
