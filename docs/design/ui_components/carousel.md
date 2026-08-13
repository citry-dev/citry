# Carousel

**Status:** production implementation pass completed on 2026-08-11. Runtime,
public API/examples, quality wiring, server tests, and focused Chromium,
Firefox, and WebKit interaction/accessibility evidence are checked in. Manual
AT, touch/trackpad/pen hardware, 400% zoom, and release visual review remain
qualification work.

## 1. Purpose and product bar

`CCarousel` presents one composed content slide at a time with native scrolling,
explicit previous/next controls, and optional slide pickers. It must feel like
a polished content rail without hiding page structure behind a desktop-widget
keyboard model.

## 2. Prior art and complaints

The WAI-ARIA APG Carousel pattern and current Zag Carousel 1.43.0 were reviewed
on 2026-08-10. Citry adopts APG naming, native Buttons, stable focus, and no
scripted Tab handling; it adopts Zag's CSS Scroll Snap foundation. Autoplay is
deferred because accessible autoplay requires an always-discoverable rotation
control plus permanent pause after focus or hover.

## 3. Public composition and anatomy

The family is `CCarousel` and `CCarouselSlide`. Root renders one named carousel
region containing a controls row, a scroll viewport, a direct track, and
optional picker group. Each direct Slide renders one `div` content container.
Slides require unique nonempty values and accessible labels; empty collections
and orphan Slides fail server rendering.

## 4. Server inputs and client inputs

Root: required `label`; optional `id`; `index=0`; `orientation=horizontal |
vertical`; `loop=False`; `disabled=False`; `controls=True`; `indicators=True`;
`draggable=True`; `variant=plain | surface`; `size=sm | md | lg`; customizable
`previous_label`, `next_label`, and `picker_label`; plus `class_`, `style`, and
`attrs`. Slide: required `value` and `label`, plus `class_`, `style`, `attrs`,
and required default content.

Client root inputs mirror `index`, orientation, loop, disabled, controls,
indicators, draggable, variant, size, and `onIndexChange`. A supplied integer
controls the index; omission releases ownership. Invalid values diagnose once
per continuous episode and use the server/uncontrolled fallback.

## 5. State model

State is active zero-based index, controlled ownership, current collection,
scroll settlement, drag gesture, and configuration. Previous/next and picker
requests are atomic. Native scrolling selects the nearest snap point. In
controlled mode a rejected button/picker request never scrolls; a rejected
native scroll settles back to the controlled index.

## 6. Slots and slot data

Root default accepts direct Slides and transparent control flow only. Slide
default accepts trusted flow content including ordinary controls. It must not
contain a nested `CCarouselSlide`; nested independent Carousels are allowed
inside slide content.

## 7. Callbacks, native events, and methods

`onIndexChange(index, detail)` reports `index`, `previousIndex`, selected
`value`, `reason: previous | next | picker | scroll | structure`, `controlled`,
`forced`, and `source`. Native Button and viewport scroll events remain usable.
There are no public methods or custom DOM events.

## 8. Semantics, keyboard, focus, and assistive technology

Root is `role=region`, has the supplied accessible label, and owns
`aria-roledescription=carousel`. Each Slide is `role=group`, has its supplied
label, and owns `aria-roledescription=slide`. Slides remain in DOM and in the
accessibility tree; offscreen content is never incorrectly announced as
hidden. Previous, next, and picker controls are native Buttons. Controls do not
move focus after activation. Tab follows ordinary page order; no Arrow keys are
captured outside focused native controls.

Picker Buttons are grouped by `picker_label`, named by their Slide labels, and
the current picker has `aria-current=true`. Pickers add Tab stops, so authors
should disable them for large collections.

The native scroll viewport has `tabindex=0`, so keyboard and Safari users can
focus and scroll the region directly without Carousel capturing Arrow keys.

## 9. Native forms and validation

All owned controls use `type=button`. Slide content preserves ordinary native
form ownership, submission, reset, and validation. Offscreen Slides remain
rendered and therefore form-associated; conditional participation requires the
app to disable or remove its controls.

## 10. Styling and theme contract

Public variables are `--cui-carousel-background`, `--cui-carousel-foreground`,
`--cui-carousel-border-color`, `--cui-carousel-radius`,
`--cui-carousel-gap`, `--cui-carousel-padding`,
`--cui-carousel-block-size`,
`--cui-carousel-control-background`, `--cui-carousel-control-foreground`,
`--cui-carousel-control-size`, `--cui-carousel-focus-color`,
`--cui-carousel-indicator-size`, `--cui-carousel-indicator-color`,
`--cui-carousel-indicator-active-color`, `--cui-carousel-duration`, and
`--cui-carousel-easing`.

Variants and sizes affect the complete family. Unlayered consumer CSS can
override zero-specificity component styles.

## 11. Environmental behavior

Logical geometry supports LTR/RTL and horizontal/vertical orientation. Native
Scroll Snap supports touch, trackpad, narrow layouts, and zoom. Reduced motion
uses instant scrolling. Forced colors retains boundaries and current picker.
Print removes controls and renders all Slides sequentially without clipping.

## 12. Overlay and layering behavior

Carousel does not create an overlay, top layer, focus trap, inert page region,
or global dismissal listener. Nested overlays inside a Slide own themselves.

## 13. Collections, async data, and identity

DOM order is collection order. Slide `value` is canonicalized, nonempty,
U+0000-free, and unique. Dynamic removal of the active Slide selects the same
index when possible, otherwise the previous final Slide, and reports one forced
structure change. Empty dynamic collections fail closed and disable controls
until a valid Slide returns.

## 14. Server render, morph, and cleanup

SSR emits the complete semantic list with the selected Slide aligned first only
after activation; no content depends on JavaScript to exist. Correlated rerender
retains an uncontrolled selected value when the server index baseline is
unchanged. Cleanup removes listeners/observers and stale scroll/drag callbacks
cannot mutate a replacement.

## 15. Security and content trust

Attrs maps are copied. Destinations reject owned identity, role, name, focus,
scroll, visibility, state, part, object-bind, and structural directives. Slot
content uses Citry's trusted-template boundary; no raw HTML or URL API exists.

## 16. Assets and performance

One root owns delegated click and pointer listeners, one viewport scroll
listener, one ResizeObserver, and one collection MutationObserver. Scroll work
coalesces to one animation frame. Asset and server-render scaling are measured
through 1,000 Slides.

## 17. Acceptance matrix

Server evidence covers schema, direct anatomy, duplicate/empty values, labels,
IDs, attrs, form-safe controls, hostile strings, and SSR content. Three-engine
browser evidence covers previous/next/pickers, controlled reject/accept/release,
native scroll, mouse drag, touch-compatible Scroll Snap, loop boundaries,
dynamic removal, focus stability, horizontal/vertical, RTL, all variants/sizes,
narrow/zoom, themes, reduced motion, forced colors, print, zero console/page
errors, and Axe.

Manual release evidence remains VoiceOver/Safari, NVDA/Firefox or Chromium,
JAWS/Chromium, real touch/trackpad/pen, and 400% visual review.

## 18. Compatibility classification

Public: class names, inputs, slots, callback detail, semantics, parts,
reflections, variables, variants, and sizes. Stable parts are `carousel`,
`controls`, `previous`, `next`, `viewport`, `track`, `slide`, `indicators`, and
`indicator`. Stable attributes are root `role`, `aria-label`,
`aria-roledescription`, `data-orientation`, `data-loop`, `data-disabled`,
`data-draggable`, `data-variant`, `data-size`, and `data-index`; Slide `role`,
`aria-label`, `aria-roledescription`, `data-active`, `data-index`, and
`data-value`; viewport `tabindex=0`; Button `disabled` and picker
`aria-current`. Private: readiness,
drag and scroll markers, generated IDs, observers, frame IDs, and handoff data.

## 19. Public documentation contract

Examples: at a glance; content cards; controlled index; orientation; controls
and pickers; loop/disabled; variants/sizes; forms; and customization. Docs
evidence initializes every example, navigates Slides, checks stable focus and
zero console/page errors, and runs serious/critical Axe scans.

## 20. Open decisions and deferred work

- Autoplay, pause/play controls, multiple Slides per view, variable-width
  Slides, virtualization, and lazy media policies are deferred.
- v1 uses grouped picker Buttons; authors disable indicators for large sets.
- Carousel is for browsable content, not workflow progress (`CStepper`) or
  mutually exclusive application panels (`CTabs`).

Changing autoplay, hidden-slide semantics, or multi-Slide paging requires a
new design review.

## 21. Internationalization

Previous, next, picker, carousel-role, and slide-role text use separate stable
keys recorded in the structured [Translation keys table](../../../packages/py/citry_ui/citry_ui/components/ccarousel/api.yml).
Server `tr()` supplies initial accessible attributes and `$c-tr` updates them
in place. Explicit label inputs win; `role_description=None` deliberately omits
the related `aria-roledescription` and registers no binding.
