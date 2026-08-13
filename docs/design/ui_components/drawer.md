# Citry UI Drawer specification

**Status (2026-08-09): production implementation pass complete. Specification,
runtime, public reference/examples, quality/scaling wiring, wheel inventory,
and focused Chromium/Firefox/WebKit evidence are checked in. Human visual,
assistive-technology, mobile/real-device, and released-artifact review remain.**

## 1. Purpose and product bar

`CDrawer` presents a modal task surface from a viewport edge. It covers side
drawers and top/bottom sheets without pretending that persistent application
navigation is an overlay. It uses native `<dialog>` modality and the existing
Citry modal focus/scroll contract, remains in authored DOM ancestry, and must
compose with Dialog, Popover, Tooltip, and Menu.

Common jobs:

| Job | Shortest path |
|---|---|
| Edit contextual details | `CDrawer` with `placement="inline-end"` |
| Show a navigation/task panel from the leading edge | `placement="inline-start"` |
| Present a mobile-style bottom sheet | `placement="block-end"` |
| Present a top task sheet | `placement="block-start"` |
| Control visibility | client `open` plus `onOpenChange` |
| Require explicit completion | `dismissible=False` plus an action using `close_attrs` |
| Keep header/actions fixed | default `scroll="body"` |
| Fill the opening axis | `size="full"` |

```citry-html
<c-CDrawer placement="inline-end">
  <c-fill name="activator" data="{ activator_attrs }">
    <c-CButton c-attrs="activator_attrs">Edit field note</c-CButton>
  </c-fill>
  <c-fill name="title">Field note</c-fill>
  <c-fill name="default">...</c-fill>
  <c-fill name="actions" data="{ close_attrs }">
    <c-CButton c-attrs="close_attrs">Done</c-CButton>
  </c-fill>
</c-CDrawer>
```

Use `CDialog` for centered tasks and decisions. Use `CDrawer` when edge
orientation materially preserves page context or suits a narrow task. Use a
future AppShell/navigation surface for persistent or responsive layout
drawers. Toast, AlertDialog, generic Overlay, swipeable sheets, and non-modal
drawers are separate products.

## 2. Prior art and complaints

The load-bearing research is recorded in
[`ui_overlay_foundations.md`](../ui_overlay_foundations.md) and its
[three-engine prototype report](../ui_overlay_foundations_spikes/prototype-report.md).
The prototype proved that a modal edge `<dialog>` contains focus, makes the
background inert, hosts anchored layers, and remains a different job from an
in-flow `<aside>`.

Reviewed comparators include native HTML Dialog and APG modal-dialog guidance;
Vuetify NavigationDrawer/BottomSheet; Mantine Drawer; Material UI temporary,
persistent, and permanent Drawer; Chakra/Ark Drawer; Web Awesome Drawer; and
the current Citry `CDialog`. The recurring failures are focus-scope conflicts,
portal theme loss, nested-layer Escape races, scroll-lock leaks, controlled
presence races, ambiguous persistent/modal modes, unsafe swipe state, and
physical left/right APIs that become wrong in RTL.

Citry adopts native modality, logical placement, reason-bearing controlled
requests, exact focus restoration, safe-area-aware geometry, and separate
body/surface scrolling. It rejects portal relocation, layout participation,
swipe/drag, arbitrary focus selectors, z-index inputs, and a generic Overlay.

## 3. Public composition and anatomy

`CDrawer` is the only public class in the family.

| Element | Native/ARIA role | Stable relationship |
|---|---|---|
| Drawer | native modal `<dialog>` | labelled by required visible title; optionally described |
| Surface | neutral `<div>` | direct child filling the Drawer geometry |
| Header | `<header>` | title plus built-in close Button |
| Title | `<h2>` | owns the accessible name |
| Description | neutral `<div>` | optional `aria-describedby` target |
| Body | neutral `<div>` | arbitrary task content and native Forms |
| Actions | `<footer>` | optional explicit actions |

The private host uses `display: contents` to scope activator/close ownership.
The activator slot must settle to exactly one native `<button type="button">`
carrying the supplied marker. `CButton` already defaults to that type; a native
Button must author it explicitly. Extra activator controls fail closed.

`class_`, `style`, and allowed `attrs` target the native Dialog. Slots retain
ordinary Citry escaping. Title, description, and custom close content must not
contain interactive descendants; body and actions may.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Effect |
|---|---|---|---|---|
| `id` | `str | None` | generated | structural | native identity and IDREF base |
| `open` | `bool` | `False` | initial state fallback | server-visible and client-upgraded state |
| `dismissible` | `bool` | `True` | reactive fallback | built-in close plus passive dismissal |
| `close_on_escape` | `bool` | `True` | reactive fallback | Escape/platform cancel gate |
| `close_on_outside` | `bool` | `True` | reactive fallback | start-and-end backdrop press gate |
| `initial_focus` | `auto | title` | `auto` | reactive fallback | native autofocus/focus steps or title |
| `placement` | logical placement | `inline-end` | reactive fallback | opening edge and geometry |
| `size` | `sm | md | lg | full` | `md` | reactive fallback | extent along the opening axis |
| `scroll` | `body | drawer` | `body` | reactive fallback | body-only or complete-surface scrolling |
| `close_label` | non-empty `str` | `Close` | structural | close Button accessible name |
| `class_` | Citry class value | `None` | structural | merged root classes |
| `style` | Citry style value | `None` | structural | merged root styles |
| `attrs` | mapping | `None` | structural | allowed native/ARIA/Alpine/data attrs |

Logical placement is exactly `inline-start`, `inline-end`, `block-start`, or
`block-end`. Client inputs are `open`, `dismissible`, `closeOnEscape`,
`closeOnOutside`, `initialFocus`, `placement`, `size`, `scroll`, and
`onOpenChange` with the corresponding Boolean/enum/function types.

A valid client input wins. Omitted configuration returns to its server
fallback. Omitted or `null` `open` releases control while preserving the last
committed state. Invalid values report once per continuous invalid episode;
invalid `open` releases control, while invalid configuration uses its server
fallback. Owner commits do not notify.

## 5. State model

The open state and callback ordering match `CDialog`:

- uncontrolled requests commit before notifying;
- controlled requests notify and wait for the owner;
- native close is unavoidable, reconciles immediately, and suppresses a stale
  controlled `true` until a later false/released edge;
- opening is permitted only when the Drawer and activator are connected and
  no composed ancestor is hidden, inert, a closed Dialog, or a closed
  Popover; a failed open normalizes closed and never moves focus;
- opening records the deep active element and enters modal state;
- closing releases descendant anchored layers, modal state, and scroll lock
  before focus restoration; and
- cleanup cancels every pending task/generation and cannot affect a replacement.

`onOpenChange(requestedOpen, detail)` detail is
`{reason, controlled, forced, source, returnValue}`. Ordinary reasons are
`trigger`, `close-button`, `action`, `escape`, `outside`, and `native`.
`ancestor` identifies a non-rejectable safety close caused by hidden/inert/
disconnected ancestry or an invalid settled structure. `forced` is true only
for those safety closes and unavoidable external native closure.

## 6. Slots and slot data

| Slot | Required | Data | Fallback |
|---|---|---|---|
| `activator` | no | `{activator_attrs}` | omitted |
| `title` | yes | `{}` | none |
| `description` | no | `{}` | no described-by relationship |
| `default` | yes | `{}` | none |
| `actions` | no | `{close_attrs}` | omitted |
| `close` | no | `{}` | built-in multiplication-sign glyph |

`activator_attrs` supplies `aria-haspopup="dialog"`, `aria-controls`,
`aria-expanded`, and a private marker. It deliberately does not supply native
Button `type`; `CButton` owns that input and native Button examples author
`type="button"`. `close_attrs` carries the owned explicit-close marker.

## 7. Callbacks, native events, and methods

`onOpenChange` has signature
`(requestedOpen: boolean, detail: CDrawerOpenChangeDetail) => void`. Return
values never cancel. A controlled owner declines ordinary requests by keeping
`open` unchanged. Forced requests close first and notify afterward; stale
controlled `true` cannot reopen until a false or released edge. Native
`cancel`, `close`, and `submit` events remain usable.
No custom DOM event or imperative component method is added.

Native Button events on activator/actions stay on those controls. Component
root attrs target the Dialog, so callers use `@cancel`/`@close` there rather
than treating component-tag `@click` as an action API.

## 8. Semantics, keyboard, focus, and assistive technology

The native Dialog supplies modal semantics and background inertness. The
required visible title labels it. `initial_focus="auto"` preserves native
autofocus/focus steps; `title` gives the title `tabindex=-1` and focuses it
without scrolling. Tab and Shift+Tab remain inside the nearest open Drawer;
nested Dialog/Drawer focus scopes do not leak into parents. Escape requests
close only from the topmost eligible native modal.

Arrival never focuses an unrelated page element. Close restores the exact
deep active element recorded before open when still connected and usable. If
the activator disappears, native/browser-safe fallback applies without
focusing arbitrary content. The built-in close Button is visible whenever
`dismissible`; non-dismissible tasks require an explicit completion path.

Placement is visual only and does not alter reading order, name, role, or
keyboard behavior.

## 9. Native forms and validation

Body Forms retain native validation, reset, FormData, and Citry Events.
`method="dialog"` supplies the submitter value through `returnValue`.
Controlled mode intercepts only the final close request after validation and
submit dispatch, allowing acceptance or rejection without duplicating native
events. Activator and built-in close Buttons are always `type="button"`.

## 10. Styling and theme contract

Public variables:

| Variable | Purpose | Default |
|---|---|---|
| `--cui-drawer-backdrop` | modal scrim | `rgb(15 23 42 / 58%)` |
| `--cui-drawer-background` | surface | `Canvas` |
| `--cui-drawer-foreground` | text | `CanvasText` |
| `--cui-drawer-border-color` | inner-edge boundary | subtle CanvasText mix |
| `--cui-drawer-shadow` | edge elevation | placement-aware theme shadow |
| `--cui-drawer-extent` | size along opening axis | size-derived |
| `--cui-drawer-padding` | region padding | `1.25rem` plus safe area |
| `--cui-drawer-gap` | region spacing | `1rem` |
| `--cui-drawer-radius` | inner-edge corner radius | `0.875rem` |
| `--cui-drawer-close-size` | close target | `2.5rem` |
| `--cui-drawer-close-radius` | close radius | `0.5rem` |

Public selectors are `[data-citry-ui-part="drawer"]`, `surface`, `header`,
`title`, `description`, `close`, `body`, and `actions`. Public root mirrors are
`data-open`, `data-placement`, `data-size`, and `data-scroll`.

Inline placements fill `100dvb` and size their inline extent; block
placements fill `100dvi` and size their block extent. `full` fills the opening
axis. Viewport-safe maximums beat requested extent. Safe-area insets augment
padding at the touched viewport edge. Logical placement follows writing mode
and direction. V1 requires no entry or exit animation; applications may add
motion through ordinary CSS, and correctness never waits on animation.

## 11. Environmental behavior

Light/dark schemes, nested opposite schemes, forced colors, print, RTL,
vertical writing, 200/400% zoom, narrow dynamic viewports, mobile safe areas,
long unbroken title/body/action text, coarse pointers, and software keyboard
resizes remain usable. The Drawer does not teleport, so inherited custom
properties, direction, color scheme, event ancestry, and Citry context remain.
Print omits closed Drawers and renders explicitly open content in ordinary
flow where the engine supports Dialog printing.

## 12. Overlay and layering behavior

`showModal()` owns top-layer position, background inertness, and modal order.
The Drawer participates in the shared Dialog scroll-lock record. The shared
anchored-layer coordinator discovers the modal, force-closes ineligible
outside Menu/Popover/Tooltip layers, and permits anchored descendants whose
triggers are inside the Drawer. Closing a parent modal closes nested native
Dialogs/Drawers and anchored descendants deepest-first.

Drawer does not use the anchored-layer registry as a dismissible layer and
does not expose z-index. It stays in authored DOM ancestry. A Drawer behind a
newer modal cannot consume Escape or focus.

## 13. Collections, async data, and identity

Drawer owns no collection or async operation. Applications own loading,
cancellation, errors, and close-on-success. Stable `id` links the Drawer,
title, optional description, and activator. Callback values are ordinary data.

## 14. Server render, morph, and cleanup

Server `open=True` is visible but not modal without JavaScript, matching native
Dialog limits. Initialization upgrades it with `showModal()` only when
eligible. Correlated rerenders preserve committed uncontrolled open state when
the server `open` fallback is unchanged, preserve controlled intent, update
placement/size/scroll without close/reopen, and transfer semantic focus state
without old-generation callbacks.

Cleanup closes descendants, releases modal and scroll ownership, removes all
listeners/observers/tasks, clears activator state, and restores focus once.
Removal or invalid settled anatomy fails closed and leaves no top-layer entry.

## 15. Security and content trust

`attrs` cannot replace `id`, `open`, modality, `role`, `tabindex`, naming and
description relationships, public mirrors, part markers, `popover`,
`closedby`, `hidden`, `inert`, `aria-hidden`, or structure/ownership directives
including `x-html`, `x-text`, `x-if`, `x-for`, `x-teleport`, `x-ignore`,
`x-model`, and whole-object `x-bind`. Static and dynamic/property aliases are
reserved case-insensitively. Native listeners and unrelated targeted Alpine
bindings remain allowed.

Title/description/close validation rejects interactive/focusable descendants.
Activator validation rejects missing/wrong Button type and extra interactive
siblings. `returnValue` and IDs are canonical plain strings with U+0000 and ID
whitespace rules enforced before serialization.

## 16. Assets and performance

Drawer adds one family CSS/initializer asset and reuses the shared modal
scroll/focus machinery; it adds no network request, portal, icon font, global
idle observer, or anchored-position work. Closed instances have bounded local
cost. Quality diagnostics record raw/gzip/Brotli assets plus server render at
1, 10, 100, 500, and 1,000 instances.

## 17. Acceptance matrix

Focused server/browser evidence must cover:

- every input, slot, exact slot-data shape, export, API projection, preview,
  quality route, wheel entry, and hostile attrs mapping;
- native anatomy/name/description, no-JS output, activator form safety, and
  invalid settled structure fail-closed recovery;
- controlled/uncontrolled open, invalid episodes, trigger/close/action/
  Escape/outside/native reasons, declined requests, and rapid changes;
- autofocus/title focus, forward/reverse loops, deep ShadowRoot restoration,
  nested modal isolation, removed activator, and cleanup;
- native Form validation/reset/FormData/`method=dialog` return values;
- all logical placements/sizes/scroll modes in LTR/RTL, narrow/zoomed dynamic
  viewports, safe areas, long content, and public token/selector overrides;
- anchored Menu/Popover inside Drawer, unrelated-modal suppression, parent
  close cascades, and zero leaked scroll/layer/listener resources;
- light/dark/nested scheme, forced colors, reduced motion, print, axe, and
  Chromium/Firefox/WebKit.

Manual release evidence covers VoiceOver/Safari, NVDA/Firefox or Chromium,
JAWS/Chromium, real mobile safe areas and keyboards, touch, 400% zoom, visual
hierarchy, and motion comfort. Hosted Nu validation is required when Java is
available.

## 18. Compatibility classification

Stable: `CDrawer`; all inputs/slots/slot data; callback/detail fields; enums;
variables; selectors; public mirrors; native semantics; focus, Form,
controlled-state, overlay-composition, no-JS, and cleanup behavior. Private:
`.cui-*` classes, `--_cui-*` variables, host/runtime markers, exact listener
organization, generated IDs, and animation implementation.

## 19. Public documentation contract

The guide teaches: at-a-glance placements; ordinary edit Drawer; bottom Sheet;
configuration; controlled requests; focus; long content/scroll; native Form;
nested Menu/Popover; non-dismissible workflow; customization; narrow/safe-area
layout; and lifecycle/modal composition. Controls stay outside preview
specimens, code is collapsed, public examples intentionally produce no
console/page errors, and every rendered preview receives browser/axe coverage.

## 20. Open decisions and deferred work

No open decision blocks modal Drawer implementation. Deferred: persistent or
responsive navigation drawers, AppShell space reservation, non-modal mode,
swipe/drag, snap points, browser-history integration, physical left/right
aliases, portals, lazy mounting, public imperative methods, and a generic
Overlay/Sheet export. A concrete product job must justify each addition.

## 21. Internationalization

The generated close control uses the key and precedence recorded in the
structured [Translation keys table](../../../packages/py/citry_ui/citry_ui/components/cdrawer/api.yml).
Server `tr()` supplies the initial accessible name and `$c-tr` follows locale
changes. An explicit `close_label` or `close` slot owns the result and prevents
registration of the default catalog binding.
