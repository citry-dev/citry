# NavigationMenu

**Status:** production implementation pass completed on 2026-08-11. Runtime,
public API/examples, quality wiring, server tests, and focused Chromium,
Firefox, and WebKit interaction/accessibility evidence are checked in. Manual
AT, touch/pen hardware, 400% zoom, and release visual review remain
qualification work.

## 1. Purpose and product bar

`CNavigationMenu` is a persistent website-navigation list containing ordinary
links and optional disclosure panels of richer navigation links. It must feel
like familiar web navigation, not an application `menu`/`menubar` widget.

## 2. Prior art and complaints

Current Radix Navigation Menu and the W3C disclosure-navigation approach were
reviewed on 2026-08-10. Radix’s strongest pressure is explicit Link versus
Trigger/Content anatomy, managed panel transitions, hover delay, and ordinary
navigation semantics without `role=menu`. Citry avoids the large shared
viewport/submenu abstraction in v1: each disclosure owns one adjacent panel.

## 3. Public composition and anatomy

The family is `CNavigationMenu`, `CNavigationMenuLink`, and
`CNavigationMenuItem`. Root renders `nav > ul`. Each direct child renders one
`li`: Link owns one native `a`; Item owns one `button type=button` immediately
followed by one panel div. Item `label` slot names the Button; default slot is
the panel. Every child must be rendered under one root context; duplicate Item
values and empty roots fail server rendering.

## 4. Server inputs and client inputs

Root: required `label`; `value=None`; `orientation=horizontal | vertical`;
`disabled=False`; `delay=200`; `close_delay=300`; `loop=False`;
`variant=plain | surface`; `size=sm | md | lg`; `class_`, `style`, `attrs`.

Link: required `href`; `current=False`; optional `target`, `rel`, `download`;
`class_`, `style`, `attrs`; required default slot.

Item: required nonempty unique `value`; `disabled=False`; `class_`, `style`,
`attrs`, `trigger_attrs`, `panel_attrs`; required `label` and default slots.

Client root inputs mirror `value`, disabled, delays, loop, variant, and size,
plus `onValueChange`. Supplied string or `null` value controls the open Item;
omission releases ownership. Unknown values diagnose and release to closed.

## 5. State model

State is committed open Item value or `null`, controlled ownership, hover
timers, focus location, effective disabledness, and configuration. Click,
Enter, or Space toggles an Item. Fine-pointer hover opens after `delay`; leaving
the whole root closes after `close_delay`. Touch/pen contact uses click only.
Opening one Item closes the previous panel atomically.

## 6. Slots and slot data

Root default accepts only direct family children (ordinary template control
flow may resolve to them). Link default is phrasing link content without nested
interactive descendants. Item `label` is noninteractive phrasing content;
default is trusted flow content and may contain ordinary links/buttons/forms,
but no nested NavigationMenu declaration in v1.

## 7. Callbacks, native events, and methods

`onValueChange(value, detail)` reports `value: string | null`, `previousValue`,
`reason: trigger | hover | escape | outside | focus-outside | link | disabled |
structure`, `controlled`, `forced`, and `source`. Controlled requests wait for
acceptance; disabled/structure safety closes are forced. Native link and Button
events remain usable. There are no public methods or custom DOM events.

## 8. Semantics, keyboard, focus, and assistive technology

Root is a named native `nav`; its `ul/li` structure stays in the accessibility
tree. Links remain native. Item Buttons own `aria-expanded` and `aria-controls`.
Panels are neutral divs: they have IDs but no prohibited generic names.

Tab visits every top-level Link/Button and every visible panel control in
ordinary order. Enter/Space toggle focused Item. Horizontal Right/Left (or
vertical Down/Up) move among top-level controls without removing them from Tab
order; Home/End move to edges. Down on an open horizontal Item focuses the
first panel focus target. Escape closes and restores its Item Button. RTL swaps
horizontal direction. No menu roles or typeahead are authored.

## 9. Native forms and validation

All disclosure triggers are `type=button`; navigation links retain native
navigation. Panels may contain ordinary forms. Closed `hidden`+`inert` panels
remain in DOM and therefore may still contribute form controls; authors who
need conditional form participation must disable or remove those controls.

## 10. Styling and theme contract

Public variables are `--cui-navigation-menu-background`,
`--cui-navigation-menu-foreground`, `--cui-navigation-menu-border-color`,
`--cui-navigation-menu-trigger-background`,
`--cui-navigation-menu-trigger-hover-background`,
`--cui-navigation-menu-trigger-open-background`,
`--cui-navigation-menu-focus-color`, `--cui-navigation-menu-radius`,
`--cui-navigation-menu-gap`, `--cui-navigation-menu-padding`,
`--cui-navigation-menu-panel-background`,
`--cui-navigation-menu-panel-inline-size`,
`--cui-navigation-menu-panel-max-inline-size`,
`--cui-navigation-menu-panel-padding`, `--cui-navigation-menu-panel-shadow`,
`--cui-navigation-menu-offset`, `--cui-navigation-menu-duration`, and
`--cui-navigation-menu-easing`.

Variants and sizes style the entire tree. Panels wrap long content and expose a
polished elevated surface. Unlayered consumer CSS remains able to override the
zero-specificity component layer.

## 11. Environmental behavior

Logical geometry supports LTR/RTL. Panels clamp at narrow widths and 400%
zoom. Reduced motion removes transition timing. Forced colors retains system
boundaries/focus. Print renders links and hides disclosure Buttons/panels.
Touch never hover-opens; pen hover requires no contact.

## 12. Overlay and layering behavior

Panels are anchored absolute descendants, not top-layer Popovers. The root
creates a positioning context and stacking layer. Horizontal panels open below
their Item and flip alignment at the viewport edge through bounded JS geometry;
vertical panels remain below the trigger in document flow. Outside pointer and
focus close without focus restoration; panels never trap focus or inert page
content.

## 13. Collections, async data, and identity

Direct child order is DOM order. Item `value` is canonicalized, nonempty,
U+0000-free, and unique. Links need no callback identity. Dynamic removal of
the open Item forces closed exactly once. Empty dynamic roots fail closed until
a valid collection returns. Loading and async ownership belong to the app.

## 14. Server render, morph, and cleanup

SSR exposes complete `nav/ul/li/a/button/panel` structure; all panels are
closed unless the server value selects one. Correlated rerender retains an
uncontrolled value when its server baseline is unchanged and the value still
exists. Cleanup cancels timers/listeners/observers and old generations cannot
mutate replacements.

## 15. Security and content trust

All attrs maps are copied. Each destination rejects owned semantics, identity,
focus, visibility, runtime/state/part fields, object binds, and structural
directives including `x-if`, `x-for`, `x-show`, `x-ignore`, and `x-teleport`.
`href` is application-trusted navigation data and is not sanitized. Slot markup
uses Citry’s trusted-template boundary; no raw-HTML API is added.

## 16. Assets and performance

One root owns delegated click/keydown/focusin/pointerover/pointerout handlers,
one open-only outside listener pair, one structure observer, and at most two
timers. While a panel is open, viewport resize/scroll invalidation coalesces to
one animation-frame geometry pass. Same-batch mutations coalesce to one O(n)
reconciliation. Asset and render scaling are measured through 1,000 Items.

## 17. Acceptance matrix

Server evidence covers public schemas, context/nesting, duplicate/empty values,
IDs, attrs, link metadata, and hostile strings. Three-engine browser evidence
covers click/Enter/Space/hover/touch, controlled reject/accept/release, outside
and focus close, Arrow/Home/End/RTL, panel focus/Escape, link navigation event,
dynamic removal, Form safety, all variants/sizes, narrow/zoom, themes, forced
colors, reduced motion, print, zero console/page errors, and Axe.

Manual release evidence remains VoiceOver/Safari, NVDA/Firefox or Chromium,
JAWS/Chromium, real touch/pen, and 400% visual review.

## 18. Compatibility classification

Public: class/type names, inputs, slots, callback detail, semantics/keyboard,
parts, reflections, variables, variants, sizes. Stable parts are
`navigation-menu`, `list`, `link-item`, `link`, `item`, `trigger`, `indicator`,
and `panel`. Stable reflections are root `data-orientation`, `data-disabled`,
`data-loop`, `data-variant`, `data-size`, and Item/trigger/panel `data-open` and
`data-value`. Stable native relationships and states are root `aria-label`, Link
`aria-current`, trigger `aria-controls`, `aria-expanded`, and `disabled`, plus
panel `hidden` and `inert`.
Private: readiness marker, generated IDs, timers, observer, geometry, and
handoff storage.

## 19. Public documentation contract

Examples: at a glance; link-only navigation; rich panels; controlled state;
orientation; states; variants/sizes; keyboard; and customization. Docs evidence
initializes every example, exercises open/link/Escape behavior, checks zero
console/page errors, and runs serious/critical Axe scans.

## 20. Open decisions and deferred work

- Nested NavigationMenu submenus, shared animated viewport, route-adapter
  callbacks, and mobile hamburger/drawer composition are deferred.
- Top-level Link versus Item is explicit so Buttons never masquerade as links.
- This family never gains `role=menu`; application commands belong in `CMenu`.

Changing native navigation semantics, focus model, or the one-level disclosure
limit requires another design review.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
