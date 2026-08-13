# HoverCard

**Status:** production implementation pass completed on 2026-08-10. Runtime,
public API/examples, shared anchored-layer integration, quality wiring, server
tests, and focused Chromium/Firefox/WebKit evidence are checked in. Manual AT,
touch hardware, 400% zoom, and release visual review remain qualification work.

## 1. Purpose and product bar

`CHoverCard` reveals supplementary visual preview content when an enabled,
focusable activator is hovered or focused. It is for a profile, document, or
link preview whose essential meaning and action remain available without the
card. It is not a Tooltip, Popover, Menu, or disclosure.

The product bar is a calm, polished card with forgiving pointer travel,
predictable delay, collision-safe placement, and no accidental touch behavior.

## 2. Prior art and complaints

Current Radix Hover Card, Ark UI Hover Card, Chakra UI Hover Card, and Radix
Themes were reviewed on 2026-08-10. Their shared pressure is controlled or
uncontrolled visibility, open/close delays, collision-aware placement, and an
optional visual arrow. Radix explicitly frames the pattern as a sighted-user
preview behind a link; Chakra says supplementary content must not be essential.

Citry keeps that narrow purpose. It uses the shared anchored-layer coordinator,
manual Popover top-layer rendering, CSS anchors, and exact ShadowRoot/modal
eligibility rather than adding another overlay foundation.

## 3. Public composition and anatomy

The family has one public component, `CHoverCard`.

The root host contains exactly one direct activator supplied through the
required `activator` slot and one sibling manual-popover Card surface. The
default slot renders inside a content wrapper. An optional owned decorative
arrow sits inside the surface. The activator must spread `activator_attrs` onto
exactly one direct enabled focusable HTMLElement.

The surface is `aria-hidden="true"`, nonfocusable, and has no widget or live
region role. It may remain pointer-hoverable so sighted users can select/copy
text. Settled content rejects interactive, form-associated, editable,
focusable, nested overlay, or nested HoverCard descendants.

## 4. Server inputs and client inputs

Server inputs are `id`, `open=False`, `disabled=False`, `delay=600`,
`close_delay=300`, `placement="bottom-start"`, `arrow=True`,
`size="md"`, `class_`, `style`, and trusted `attrs`.

`placement` is `top-start | top | top-end | bottom-start | bottom | bottom-end`.
`size` is `sm | md | lg`. Delays are integer milliseconds from 0 through
60000. The required `activator` slot receives `activator_attrs` and
`hover_card_id`; the required default slot receives no slot data.

Client inputs mirror `open`, `disabled`, delays, placement, arrow, and size,
plus `onOpenChange`. Supplied Boolean `open` controls visibility; `null` or
omission releases to current committed visibility. Invalid values diagnose once
per continuous episode and use server fallbacks.

## 5. State model

State is desired/visible open, controlled ownership, trigger hover/focus,
surface hover, touch-focus suppression, peer dismissal latch, timers,
placement, and shared layer eligibility. Hover waits `delay`; focus opens
without delay; leaving trigger and surface waits `close_delay`; blur closes
immediately. Returning before expiry cancels closure.

Touch pointer contact never opens. Pointer press closes an open preview and
suppresses its causal focus. Opening one HoverCard closes the prior peer in the
same coordinator scope. Forced ancestor/modal/structure closure is
nonrejectable.

## 6. Slots and slot data

`activator` is required and receives copied `activator_attrs` plus
`hover_card_id`. It must render one direct focusable HTMLElement and spread the
map. `default` is required and receives `{}`. It accepts trusted flow content
without interactive/focusable/form/editable descendants. Essential content,
actions, and alternative accessible descriptions remain outside the card.

## 7. Callbacks, native events, and methods

`onOpenChange(open, detail)` reports requests and forced closes with `open`,
`reason`, `controlled`, `forced`, and `source`. Reasons are `hover | focus |
pointer-leave | blur | escape | press | peer | native | ancestor | modal`.
Controlled requests notify without changing visibility; forced safety closes
always hide. There are no public custom DOM events or methods.

## 8. Semantics, keyboard, focus, and assistive technology

The activator retains its authored semantics and behavior. HoverCard adds no
accessible description and does not change its name. Keyboard focus opens the
visual preview; blur and Escape close it while focus remains on the activator.
The card is `aria-hidden="true"` and cannot contain focus targets, so it never
adds a Tab stop or inaccessible focused descendant.

Content is deliberately a visual enhancement. If content is required to
understand or operate the page, authors must place it in ordinary document
content or use `CPopover`.

## 9. Native forms and validation

HoverCard is not form-associated. Activator behavior remains native; a Button
activator should be `type=button`. The card contains no form controls and does
not alter submission, reset, or validation.

## 10. Styling and theme contract

Public variants are intentionally omitted: a HoverCard is one elevated preview
surface. Sizes set padding, width, and text scale. Public CSS variables are
`--cui-hover-card-background`, `--cui-hover-card-foreground`,
`--cui-hover-card-border-color`, `--cui-hover-card-radius`,
`--cui-hover-card-shadow`, `--cui-hover-card-padding`,
`--cui-hover-card-inline-size`, `--cui-hover-card-max-inline-size`,
`--cui-hover-card-offset`, `--cui-hover-card-duration`, and
`--cui-hover-card-easing`.

The surface follows its actual nested `color-scheme`, wraps unbroken content,
and clamps to the visual viewport. The arrow uses the same background/border
colors and follows collision-settled placement.

## 11. Environmental behavior

Logical placement follows LTR/RTL. Narrow and 400%-zoom layouts clamp within
the viewport without page overflow. Reduced motion removes entry/exit motion.
Forced colors use Canvas/CanvasText and a visible system border. Print hides
the preview. Touch does not open it; pen hover opens only without contact.

## 12. Overlay and layering behavior

The Card uses `popover="manual"`, CSS anchors, the shared anchored-layer
coordinator, and Document/open-ShadowRoot scopes. Placement flips between block
sides and start/end alignments within viewport padding. Geometry updates while
open on resize, visual-viewport change, and scroll.

Closed logical ancestors, hidden/inert ancestors, detached triggers/surfaces,
and an unrelated top modal suppress opening. Ancestor/modal closes are forced.
Nested anchored layers inside content are invalid because content is
noninteractive.

## 13. Collections, async data, and identity

Without JavaScript, the activator remains fully usable and the Card stays
hidden. Server output includes `popover="manual"`, `aria-hidden="true"`, and
the visual fallback placement/style contract without exposing hidden content
to assistive technology.

## 14. Server render, morph, and cleanup

Correlated retained-surface replacement transfers committed open intent only
when the server open baseline is unchanged. A fresh generation owns timers,
animations, listeners, and layer registration; old work cannot mutate the new
surface. Removal cancels timers/animation, unregisters, closes native Popover,
and returns shared coordinator statistics to baseline.

## 15. Security and content trust

`attrs` is copied and rejects role, tabindex, aria-hidden, aria-live,
aria-atomic, aria-label, aria-labelledby, aria-describedby, contenteditable,
hidden, inert, popover, id, runtime/state/part attributes, whole-object binds,
and structural/ownership directives. Dynamic/property aliases are rejected.

Activator attributes are owned slot data rather than arbitrary root forwarding.
Slot content is trusted template markup, but settled validation rejects every
interactive/focusable/form/editable descendant and nested overlay host. No
HTML parsing or executable-string API is introduced.

## 16. Assets and performance

Each instance owns bounded trigger/surface listeners and only active timers.
Shared document/scope listeners and modal discovery remain coordinator-owned.
No observer or animation runs while closed. Asset reporting includes the shared
runtime once and measures HoverCard CSS/JS at 1, 10, 100, 500, and 1000 renders.

## 17. Acceptance matrix

Server tests cover schema, exact anatomy, slot data, IDs, delay/placement/size,
trusted attrs, hostile strings, and rejected ownership. Browser tests cover
hover delay/cancellation, focus/Escape/blur, surface travel, touch/pen policy,
peer closure, controlled reject/accept/release, native/forced close, collision,
RTL, ShadowRoot/modal ancestry, morph cleanup, all sizes, public selectors and
variables, light/dark, narrow/zoom, reduced motion, forced colors, print, zero
console/page errors, and serious/critical Axe cleanliness in three engines.

Manual release evidence remains VoiceOver/Safari, NVDA/Firefox or Chromium,
JAWS/Chromium, real touch/pen hardware, and visual review at 400% zoom.

## 18. Compatibility classification

Public: component/type names, inputs, slots/data, callback detail, delays,
state transitions, parts, reflections, variables, sizes, and environmental
behavior. Private: readiness/exiting markers, generated anchor name, exact
collision algorithm, peer warmth storage, timers, animations, listener layout,
and handoff storage.

Stable parts are `host`, `hover-card`, `content`, and optional `arrow`. Stable
reflections are surface `data-open`, requested `data-placement`, settled
`data-side`, `data-size`, and `data-arrow`.

## 19. Public documentation contract

Examples: profile at a glance; document preview; controlled visibility; delays;
placements; sizes; no-arrow; nested schemes; and brand customization. Docs
browser evidence initializes every preview, opens with hover and focus, proves
content is noninteractive/aria-hidden, confirms zero console/page errors, and
runs serious/critical Axe scans.

## 20. Open decisions and deferred work

- Content is intentionally inaccessible supplementary preview material; a
  future interactive hover/focus container would be a different pattern.
- Default open/close delays are 600/300ms, aligned with current ecosystem
  pressure while retaining a forgiving trigger-to-card corridor.
- Touch long-press opening, rich asynchronous loaders, and hover intent
  trajectory heuristics are deferred.

Allowing essential or interactive content, changing assistive exposure, or
adding click ownership requires another design review.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
