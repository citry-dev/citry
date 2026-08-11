# Citry UI overlay-foundations research

**Status:** ecosystem research and the architecture-gating browser spike are
complete on 2026-08-09. The private platform-first hybrid described in section
14 is ratified for component-family design work and now has two production
consumers: `CPopover` and `CTooltip`. No shared public Overlay API is defined here; each family
still advances through its own research and specification pass.

Independent adversarial review is still pending. The repository normally asks
for that gate, but the active collaboration policy during this research did not
permit delegating work to another agent.

This document refreshes and narrows the broader evidence in
[`ui_research/`](ui_research/README.md). It answers the deferred question behind
Menu, Tooltip, Popover, Drawer, and Toast: which capabilities are actually
shared, which belong to individual families, and what must be proved before
production component specifications begin.

## 1. Questions and scope

The research covers these jobs:

- place a floating surface relative to a trigger, including flip, shift,
  available-size, zoom, scroll, viewport, RTL, and arrow behavior;
- let the surface escape clipping and stacking contexts without losing theme,
  context, focus order, or accessible reading order;
- order nested layers and give only the correct layer ownership of outside
  interaction, Escape, browser Back, and focus restoration;
- distinguish non-modal, modal, and application-layout surfaces;
- keep an exiting surface present for animation without leaving stale focus
  guards, listeners, inertness, scroll locks, or ownership records;
- preserve server/client state and cleanup through retained Citry rerenders;
- deliver queued transient notifications without making ordinary Alert carry
  global queue, timing, or announcement responsibilities.

It does not design public inputs for the five component families. It also does
not assume that a public `COverlay` should exist merely because internal
behavior is shared.

### 1.1 Terms used here

| Term | Meaning |
|---|---|
| Anchored surface | A non-modal surface positioned relative to an element, range, point, or virtual rectangle. |
| Top layer | The browser-managed rendering plane used by modal dialogs and shown popovers. It escapes ordinary stacking contexts without moving the element to a different DOM parent. |
| Portal or teleport | Physical DOM reparenting to another container, commonly under `body`. |
| Layer stack | The ordered set of currently active dismissible surfaces used to decide which one owns outside interaction, Escape, focus restoration, and z-order. |
| Focus scope | The policy for initial focus, contained focus, return focus, and focus guards. It is not synonymous with positioning. |
| Presence | The interval during which a logically closed surface stays mounted for an exit transition and the rules for eventual removal and cleanup. |
| Toast host | A persistent owner of notification queueing, placement, timing, focus navigation, and announcements. |

## 2. Citry evidence already in the repository

Citry is not starting from zero:

- `CDialog` already uses native `<dialog>` and the top layer, with local focus,
  restoration, nested isolation, scroll locking, and cleanup. It proves the
  native-first direction for modal surfaces, but its component-local code is
  not yet a general overlay foundation.
- `CCombobox` uses an inline absolutely positioned popup and one bounded
  document listener. Its specification deliberately accepts clipping for now
  and asks that native Popover and anchor positioning be evaluated before a
  portal is introduced.
- `CAlert` owns persistent and live-region semantics but deliberately does not
  promise a queue, deduplication, timing, a global announcer, or focus access.
- client `$provide`, `$inject`, and `$unprovide` already follow Citry's rendered
  component route across fills, slots, and Alpine `x-teleport`, with cleanup.
  Logical ambient context is therefore not the old blocker. Physical CSS
  inheritance, DOM event ancestry, accessible reading order, and focus remain
  separate concerns when content is teleported.
- Citry's theme contract still records physical overlay placement and
  `color-scheme` propagation as an open question.

The inventory's original phrase "shared overlay foundation" therefore needs a
more precise reading. Some reusable capabilities are already present locally;
the missing work is to define their boundaries and prove that they compose.

## 3. Source record

All current-product claims below were checked on 2026-08-09. Package versions
were resolved from the public npm registry on that date; linked documentation
and tagged source are the evidence for behavior. Standards are living
documents and are identified by snapshot date rather than package version.

| Source | Studied line | Evidence used |
|---|---|---|
| Web platform | HTML Living Standard, CSS Anchor Positioning, MDN current on 2026-08-09 | [Popover API](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API), [anchor positioning](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Anchor_positioning), [HTML popover](https://html.spec.whatwg.org/multipage/popover.html), [HTML dialog](https://html.spec.whatwg.org/multipage/interactive-elements.html#the-dialog-element) |
| WAI-ARIA APG | Current on 2026-08-09 | [Menu button](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/), [Tooltip](https://www.w3.org/WAI/ARIA/apg/patterns/tooltip/), [Modal dialog](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) |
| Vuetify | 4.1.8 | [`VOverlay`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VOverlay/VOverlay.tsx), [location strategies](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VOverlay/locationStrategies.ts), [scroll strategies](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VOverlay/scrollStrategies.ts), [`VMenu`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VMenu/VMenu.tsx), [`VTooltip`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VTooltip/VTooltip.tsx), [`VSnackbar`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VSnackbar/VSnackbar.tsx), [`VNavigationDrawer`](https://github.com/vuetifyjs/vuetify/blob/v4.1.8/packages/vuetify/src/components/VNavigationDrawer/VNavigationDrawer.tsx) |
| React Aria Components | 1.20.0 | [Popover](https://react-aria.adobe.com/Popover), [Tooltip](https://react-aria.adobe.com/Tooltip), [Menu](https://react-aria.adobe.com/Menu), [Toast](https://react-aria.adobe.com/Toast), [FocusScope](https://react-spectrum.adobe.com/react-aria/FocusScope.html), [PortalProvider](https://react-spectrum.adobe.com/react-aria/PortalProvider.html) |
| Radix Primitives | Popover 1.1.23, Toast 1.2.23 and current repository source | [Popover](https://www.radix-ui.com/primitives/docs/components/popover), [Tooltip](https://www.radix-ui.com/primitives/docs/components/tooltip), [Dropdown Menu](https://www.radix-ui.com/primitives/docs/components/dropdown-menu), [Toast](https://www.radix-ui.com/primitives/docs/components/toast), [`DismissableLayer`](https://github.com/radix-ui/primitives/blob/main/packages/react/dismissable-layer/src/dismissable-layer.tsx), [`Presence`](https://github.com/radix-ui/primitives/blob/main/packages/react/presence/src/presence.tsx) |
| Ark UI and Zag | Ark 5.38.1, Zag Popover 1.43.0 | [Ark styling and layer index](https://ark-ui.com/docs/guides/styling), [Zag Popover](https://zagjs.com/components/popover), [Zag composition](https://zagjs.com/guides/composition), [Zag Menu](https://zagjs.com/components/menu) |
| Floating UI | DOM 1.8.0 | [autoUpdate](https://floating-ui.com/docs/autoupdate), [middleware](https://floating-ui.com/docs/middleware), [useFloating](https://floating-ui.com/docs/usefloating), [FloatingFocusManager](https://floating-ui.com/docs/floatingfocusmanager) |
| Mantine | 9.5.1 | [Popover](https://mantine.dev/core/popover/), [Menu](https://mantine.dev/core/menu/), [Tooltip](https://mantine.dev/core/tooltip/), [Drawer](https://mantine.dev/core/drawer/), [Portal](https://mantine.dev/core/portal/) |
| Material UI | 9.3.1 | [Popover](https://mui.com/material-ui/react-popover/), [Popper](https://mui.com/material-ui/react-popper/), [Drawer](https://mui.com/material-ui/react-drawer/), [Snackbar](https://mui.com/material-ui/react-snackbar/), [Click-Away Listener](https://mui.com/material-ui/react-click-away-listener/) |
| Web Awesome | 3.11.0 | [Popup](https://webawesome.com/docs/components/popup/), [Popover](https://webawesome.com/docs/components/popover/), [Tooltip](https://webawesome.com/docs/components/tooltip/), [Dropdown](https://webawesome.com/docs/components/dropdown/), [Drawer](https://webawesome.com/docs/components/drawer/), [Toast](https://webawesome.com/docs/components/toast/) |
| Bootstrap | 5.3.8 with Popper 2.11.8 | [Dropdowns](https://getbootstrap.com/docs/5.3/components/dropdowns/), [Tooltips](https://getbootstrap.com/docs/5.3/components/tooltips/), [Offcanvas](https://getbootstrap.com/docs/5.3/components/offcanvas/) |

Vuetify remains the most heavily weighted product reference, as required by
the component-authoring process. The other sources are used to challenge its
choices rather than to count votes.

## 4. The platform has changed the starting point

### 4.1 Native Popover is now a serious foundation candidate

The Popover API is Baseline 2025 in current MDN data. A shown popover enters
the browser top layer, escapes ordinary clipping and stacking contexts, and
keeps its original DOM ancestry. `popover="auto"` supplies light dismissal,
Escape behavior, and single-open behavior with nested-popover exceptions;
`manual` and `hint` provide different ownership policies. `beforetoggle` and
`toggle` expose lifecycle changes.

This solves a different problem from a portal. A top-layer element is painted
outside ordinary stacking but is not reparented under `body`, so ordinary DOM
relationships, Citry's component route, and CSS inheritance do not inherently
change. That is attractive for a server-authored component framework.

Native Popover does not provide Menu, Tooltip, or Popover semantics. It also
does not make a surface modal; native `<dialog>.showModal()` remains the right
modal primitive. Citry would still own ARIA, keyboard behavior, focus policy,
trigger behavior, controlled state, and cleanup.

The newer `interestfor` family can express hover/focus interest and delay, but
MDN explicitly flags varying support across parts of the Popover feature. It
is research evidence, not a safe Citry dependency yet.

### 4.2 CSS Anchor Positioning covers much of the geometry vocabulary

The current CSS module supports named anchors, logical placement areas,
anchor-relative sizes, ordered fallback positions, flipping tactics,
available-space responses, and conditional hiding. This overlaps strongly
with Floating UI, Vuetify's connected location strategy, and Popper.

The important qualification is recency. Individual anchor-positioning
features do not all have the same browser baseline. A broad statement such as
"CSS anchors are supported" is not enough; Citry must test the exact subset it
would ship.

### 4.3 Native top-layer transitions still need a presence policy

`display`, the `overlay` property, discrete transitions, and `@starting-style`
can animate popover and dialog entry/exit without a framework mounting
primitive. They do not eliminate state ownership. Citry still has to decide
when `open` changes, when callbacks run, what a server rerender may replace,
and when listeners and ownership records are cleaned.

## 5. Architecture patterns in mature libraries

### 5.1 Vuetify: one broad internal overlay engine

Vuetify's `VOverlay` is the clearest styled-suite example of consolidating
shared machinery. It owns activators, teleport selection, global and nested
stacking, focus trap/restoration, outside click, Escape, router Back, scrim,
lazy presence, transitions, theme and RTL classes, dimensions, connected or
static positioning, and scroll strategies. `VMenu` and `VTooltip` configure
that engine rather than rebuilding it.

Several details are especially relevant:

- only the local or global top layer owns dismissal;
- nested overlay activators are tracked so focus ownership can cross physical
  overlay roots;
- teleport selection respects a trigger's `ShadowRoot`;
- theme and RTL classes are copied to the teleported overlay root;
- positioning watches resize, visual viewport changes, target geometry, and
  scroll ancestry;
- scroll is a strategy: none, close, block, or reposition.

The caution is equally useful. `VOverlay` has a very wide prop surface and
every wrapper inherits many combinations. Citry should learn from Vuetify's
internals without exposing a universal public component or forwarding the
entire foundation API into each family.

`VNavigationDrawer` is a separate application-layout component rather than a
thin `VOverlay` wrapper. Its permanent, temporary, responsive, sticky, touch,
scrim, and app-layout behavior proves that "Drawer" spans at least two jobs:
a modal task sheet and application navigation/layout.

`VSnackbar` reuses some overlay rendering but disables global stack, focus,
scrim, and scroll ownership. Its queue adds timer, visibility, hover/focus,
overflow, and dismissal-reason behavior. Toast therefore shares only a subset
of overlay infrastructure.

### 5.2 React Aria: accessibility and portal behavior are inseparable

React Aria's Popover composes placement, portal rendering, focus scope,
outside interaction, modality, and accessible hiding. It defaults many
popover-like surfaces to modal accessibility behavior because portalled
content is otherwise far from the trigger in screen-reader reading order.
Non-modal behavior is reserved for cases such as Combobox where that trade-off
is intentional.

Its Tooltip coordinates warm-up and cool-down delays across triggers, opens
immediately on keyboard focus, and declines to show touch tooltips. Menu adds
collection semantics, typeahead, selection, links, and submenus; it is not a
Popover with a role added.

Its Toast design uses an external queue plus a persistent region. It pauses
timers while the region is hovered or focused, supports global pause/resume,
provides F6 navigation to and from the region, restores focus after dismissal,
and moves focus to the next toast when appropriate.

This is strong evidence that accessible reading order, physical placement,
focus, and queue ownership must be designed together. Citry's logical
`$provide` route alone cannot solve a portalled screen-reader experience.

### 5.3 Radix: decomposed primitives with real coupling at the edges

Radix exposes compound component parts and reusable internal primitives such
as `DismissableLayer` and `Presence`. Popover has Trigger, Anchor, Portal,
Content, Arrow, and Close parts; supports controlled and uncontrolled state;
and exposes collision geometry through data attributes and CSS variables.

The separation is valuable, but Radix's release and issue history shows where
the boundaries remain coupled: nested dismissible layers, focus guards,
presence loops, portals, Tooltip mount behavior, and Toast accessibility have
all required coordinated fixes. Decomposition is an implementation tool, not
proof that each concern can evolve independently.

Radix Toast supplies a Provider and Viewport, swipe gestures, pause on
hover/focus/window blur, a focus hotkey, and distinct foreground/background
announcement treatment. It does not provide a complete application queue;
its docs demonstrate app-owned state or a separate abstraction.

### 5.4 Ark and Zag: explicit state machines plus a shared layer index

Zag isolates behavior in state machines and maps machine state to DOM props.
Popover models modal/non-modal behavior, portal-aware tab order, initial and
final focus, outside interaction, Escape, multiple triggers, positioning, and
cleanup. Its docs explicitly warn against portalling a Popover out of a Dialog
focus scope.

Ark exposes a single base z-index chosen by the application and a zero-based
`--layer-index` from Zag. This is a useful answer to cross-family stacking:
do not assign Menu, Dialog, and Tooltip unrelated z-index scales; use one
ordered dismissible-layer stack with one shared base.

The recent Ark changelog is useful failure evidence. Fixes were needed for
shared trigger identities, ShadowRoot lookup, pointer-event loss after
framework style spreads, and controlled Drawer swipe/presence behavior.

Citry should copy the discipline of explicit transitions and reasoned state,
not import a second machine runtime beside Alpine.

### 5.5 Floating UI: a positioning specialist, not an overlay system

Floating UI offers the strongest reusable geometry vocabulary: offset, flip,
shift, size, hide, arrow, inline/virtual references, and middleware reset.
`autoUpdate` can observe ancestor scroll/resize, element resize, layout shift,
and animation frames. Its docs warn that update work should run only while a
surface is open and must be cleaned up.

The interaction package reports open-change reasons and supplies focus and
tree helpers, but it still does not choose component semantics, theme
propagation, server ownership, or Toast delivery. Its focus manager also
requires a compatible portal implementation.

Using Floating UI would be a deliberate JavaScript dependency and would not
remove Citry's lifecycle and accessibility work. It remains the strongest
fallback/reference if the exact native anchor subset proves insufficient.

### 5.6 Mantine and Material UI: component-local composition over helpers

Mantine builds Popover, Menu, and Tooltip over Floating UI, offers optional
portal and focus-trap behavior, and exposes middleware configuration. Its Menu
docs correctly reject hover-only activation as inaccessible. The practical
trade-off is a wide combination space: portal, trap, modal behavior, target
ref requirements, middleware, overlay, and nested surfaces all interact.

Material UI separates modal `Popover` from non-modal `Popper`. Popover is built
on Modal, blocks scroll, and owns click-away; Popper focuses on positioning.
This distinction is clearer than a single mode flag, though application
authors must still choose the semantically correct primitive. Its Drawer has
temporary, persistent, and permanent variants; SwipeableDrawer explicitly
adds payload and may miss frame rate on low-end devices.

MUI Snackbar is intentionally small and app-owned. Its docs show consecutive
messages and point to a supplementary queue library rather than treating queue
semantics as incidental component state.

### 5.7 Web Awesome: declarative Web Components and explicit low-level limits

Web Awesome's `wa-popup` is a declarative Floating UI wrapper. Its docs are
unusually clear that Popup provides positioning only and is not accessible by
itself. It tears down positioning listeners while inactive, supports external
or slotted anchors, exposes placement/flip/shift/size/arrow/hover-bridge
configuration, and publishes current placement.

Tooltip restricts content to text and presentation because its content cannot
be reliably operated by keyboard. Dropdown owns menu items and submenus rather
than accepting arbitrary interactive content. Drawer exposes cancelable
close requests with a source, light dismissal, initial focus, and an escape
hatch for a third-party modal that temporarily suspends its focus trap.

Web Awesome Toast uses one persistent host, creates a top-layer stack
imperatively, pauses on hover/focus, supports manual duration, and documents
the usability limits of transient notifications. It is also a useful warning:
its `allowHtml` option creates an explicit XSS trust boundary that Citry should
not reproduce casually.

## 6. Challenge-by-challenge synthesis

### 6.1 Escaping clipping and stacking contexts

| Answer | Used by | Strength | Cost or failure mode |
|---|---|---|---|
| Native top layer | Platform Popover/Dialog; Web Awesome Toast | Escapes clipping without DOM reparenting; browser owns top-layer order | Recent feature set; not a positioning or semantics solution by itself |
| Portal/teleport to a root | Vuetify, React Aria, Radix, Mantine, MUI | Established and works with JS positioners | Breaks physical CSS/event/reading ancestry; ShadowRoot and container choice matter |
| Stay inline | Citry Combobox today; optional in Zag/Mantine | Preserves all DOM ancestry and simplest SSR | Can be clipped or trapped in a stacking context |
| Application layout item | Vuetify NavigationDrawer; MUI persistent/permanent Drawer | Correct for app-shell space reservation | Not an overlay and should not inherit overlay assumptions |

The platform-first route is materially better for Citry if its exact support
matrix passes: it solves clipping while preserving DOM ancestry. A portal
should be a fallback or explicit physical-placement policy, not the automatic
definition of an overlay.

### 6.2 Positioning and collision

All mature solutions expose roughly the same concepts: preferred logical
placement, main/cross offset, flip fallbacks, shift within a boundary,
available size, arrow geometry, reference size, and current placement.

Differences are mostly implementation and escape-hatch depth:

- Vuetify maintains its own connected strategy and viewport/scroll handling;
- Floating UI/Popper provide middleware pipelines and virtual references;
- Mantine and Web Awesome surface a curated Floating UI subset;
- Radix and Zag expose curated inputs plus CSS variables/data attributes;
- native CSS expresses fallback positions declaratively.

Citry should not expose raw middleware configuration in ordinary component
APIs. The common path should remain flat and small. An advanced boundary or
ordinary consumer CSS is preferable to making every Tooltip author understand
positioning engines.

### 6.3 Layer order and nested dismissal

The common robust model is one shared ordered registry of active dismissible
layers. Only the top eligible layer handles outside press and Escape. Nested
children count as inside their parent even when physically separate.

Vuetify uses global/local stack ownership; Zag/Radix maintain dismissible layer
state; Ark exposes a shared `--layer-index`. Assigning unrelated z-index scales
per component family is consistently the wrong answer.

Native `popover="auto"` supplies a browser stack for its own popover family,
but Citry still needs an integration rule for native Dialog, manual popovers,
third-party overlays, exiting presence, and non-dismissible layers. The
prototype must determine how much of the registry the browser can own.

### 6.4 Outside interaction and Escape are requests, not raw events

Libraries increasingly expose cancelable close requests or callbacks with a
reason/source. This is more useful than an undifferentiated `onOpenChange`:
applications can distinguish trigger, outside pointer, focus outside, Escape,
close button, selection, swipe, timeout, route/back, and programmatic control.

The source vocabulary must only claim distinctions the browser can reliably
provide. Citry's Accordion work already found that pointer, keyboard, assistive
activation, and `HTMLElement.click()` cannot always be separated from a click
event alone. Overlay callbacks need the same honesty.

### 6.5 Focus, modality, inertness, and scroll are separate policies

| Family/job | Normal policy |
|---|---|
| Tooltip | Trigger retains focus; content is non-interactive; no trap |
| Menu | Focus moves into a composite; arrows/typeahead own navigation; return to trigger on close |
| Non-modal Popover | Initial focus depends on content/job; no global inertness; deliberate return policy |
| Modal Dialog/task Drawer | Initial focus, contained focus, outside inertness, scroll lock, and return focus |
| Persistent/navigation Drawer | Participates in layout; no modal trap or inertness |
| Toast | Opening must not steal focus; region needs an explicit keyboard access and restoration policy |

One `modal` Boolean on a generic public Overlay obscures these differences.
Internal focus, inertness, and scroll helpers can be shared, but each component
family must select and document its own policy.

### 6.6 Presence is an ownership protocol

Presence is not only an animation convenience. A closing surface may still be
painted while it must no longer:

- win outside interaction or Escape ownership;
- trap or restore focus twice;
- keep the page inert or scroll-locked after the last modal closes;
- remain an active positioning observer;
- expose stale ARIA relationships;
- survive a Citry rerender after its owning component is gone.

Radix Presence bugs and Ark Drawer swipe fixes show that controlled state,
lazy mounting, measurement, and exit timing easily race. Citry needs one
generation-safe presence lifecycle, even if native discrete transitions do
most of the visual work.

### 6.7 Portals do not preserve every kind of context

Citry can already preserve `$provide`/`$inject` along its logical rendered
route, including `x-teleport`. That does not automatically preserve:

- CSS custom properties and `color-scheme` inherited from a physical ancestor;
- scoped classes or direction attached only to the original subtree;
- native event delegation that expects physical ancestry;
- screen-reader reading order;
- focus-scope containment.

Vuetify copies theme and RTL classes to its teleported root. React Aria adapts
modality and accessible hiding to its portal. Radix now offers a configurable
portal container. If Citry ever teleports by default, it needs an equally
explicit physical-context contract.

Native top-layer rendering avoids most of this because the element remains in
place in the DOM. This is one of the strongest reasons to prototype it first.

### 6.8 Toast is a delivery subsystem, not merely a floating Alert

The common mature contract includes:

- one persistent host or region;
- imperative creation from application code and a declarative item path;
- queue order, visible limit, overflow, replacement, and deduplication rules;
- unique item identity and dismissal reasons;
- minimum/default duration and persistent duration;
- pause on hover, focus, page visibility loss, and sometimes global pause;
- no focus theft on arrival;
- a keyboard route into and out of the region;
- focus-next/restore behavior when a focused toast closes;
- announcement role/politeness/atomicity and action wording;
- safe behavior under server rerender, navigation, and host replacement.

Toast may share a top-layer host and presence utility. It should not register
as a normal outside-dismissible or focus-trapping layer, and it does not need
anchored positioning.

## 7. What each deferred family actually needs

| Family | Shared capabilities | Family-specific behavior that cannot be delegated to a generic Overlay |
|---|---|---|
| Tooltip | Anchoring, collision, presence, top-layer/physical placement | Shared warm-up/cool-down, hover and focus triggers, touch policy, non-interactive content, `aria-describedby`, Escape without focus movement |
| Popover | Anchoring, collision, layer order, outside/Escape request, presence, optional focus helpers | Dialog-like naming, controlled/uncontrolled state, trigger/content composition, initial and return focus, modal boundary if offered |
| Menu | Anchoring, collision, layer order, outside/Escape, presence | Collection identity, roles, roving/active focus, typeahead, selection, links, disabled items, submenu intent/safe polygon, close-after-action rules |
| Drawer/Sheet | Layer order, focus scope, inertness, scroll lock, backdrop, presence | Modal task sheet versus persistent/app-layout navigation, edge, size, responsive mode, swipe/drag if ever supported |
| Toast | Top-layer or fixed host, presence, theme/environment continuity | Queue, timing, pause, announcements, focus access/restoration, placement, visible limit, dedupe, imperative application API |

This matrix rejects two premature simplifications:

1. Menu is not Popover plus `role="menu"`.
2. Toast is not Alert with `position: fixed` and a timeout.

## 8. Failure evidence and lessons

The broader complaint register remains authoritative. The most relevant cases
for the foundation decision are:

| Project and status at review | Failure or tension | Citry lesson |
|---|---|---|
| React Aria [#7067](https://github.com/adobe/react-spectrum/issues/7067), closed report | Native popover integration conflicted with the reported z-index/portal architecture | Platform adoption can require architecture changes; do not bolt native Popover onto a portal-first model late |
| React Aria [#8675](https://github.com/adobe/react-spectrum/issues/8675), resolved | Shadow DOM portal/focus behavior caused premature close | `Document` is not a sufficient environment abstraction |
| Radix [#3520](https://github.com/radix-ui/primitives/issues/3520), closed report | A portalled Select inside a Drawer did not transfer keyboard focus into its items | Nested focus scopes and physically separate layers need one ownership model |
| Radix current release history and [#3664](https://github.com/radix-ui/primitives/issues/3664) | Presence/focus regressions and update loops | Presence must be generation-safe and independently tested |
| Radix [#3422](https://github.com/radix-ui/primitives/issues/3422), open | Escape capture behavior conflicted with non-Radix components | Global listener phase is part of the interoperability contract |
| Ark current changelog | Shared triggers, ShadowRoot lookup, pointer-event style loss, and controlled Drawer swipe races were fixed | Composition and style ownership need hostile integration tests |
| Mantine [#9072](https://github.com/mantinedev/mantine/issues/9072), closed/fixed-in-patch report | Tooltip content was not hoverable under the reported contract | Even non-interactive Tooltip content needs a deliberate hover bridge for WCAG hover persistence |
| Mantine [#8928](https://github.com/mantinedev/mantine/issues/8928), open iOS report | Portal, focus, and scrolling interacted badly on mobile | Mobile visual viewport and scroll lock require real-device release evidence |
| Bootstrap [responsive table warning](https://getbootstrap.com/docs/5.3/content/tables/#responsive-tables) | Overflow wrappers clip dropdowns and widgets | Inline anchored surfaces are insufficient inside common overflow containers |
| Vuetify [#17628](https://github.com/vuetifyjs/vuetify/issues/17628), closed/not planned | Consumer stacking contexts conflicted with overlay ordering expectations | A shared layer root/stack needs a documented escape hatch, not arbitrary per-component z-index |

These reports are not evidence that the libraries are poor. They are evidence
that the proposed foundation problems are real, cross-cutting, and easy to
regress even in mature implementations.

## 9. Architecture candidates to prototype

### 9.1 Candidate A: native-only

Use native Popover, native Dialog, CSS Anchor Positioning, and discrete CSS
transitions. Add only family behavior and minimal lifecycle glue.

**Why it is attractive:** least JavaScript, no portal reparenting, browser-owned
top layer and light dismissal, strong SSR shape.

**What can falsify it:** required browser support is below Citry's release
floor; anchor fallbacks fail zoom/mobile/scroll cases; native nested ordering
cannot express Menu/Popover/Dialog composition; needed controlled-state or
presence behavior becomes unreliable.

### 9.2 Candidate B: Citry-owned JavaScript overlay engine

Build or adopt a portal, positioning engine, layer registry, focus scope,
scroll lock, and presence manager similar to Vuetify/Radix/Floating UI.

**Why it is attractive:** mature, controllable behavior and older-browser
reach.

**What can falsify it:** excessive client payload and lifecycle complexity;
duplicate platform behavior; physical-context restoration becomes brittle;
maintenance exceeds the value of five component families.

### 9.3 Candidate C: platform-first hybrid

Prefer native top-layer and CSS anchor behavior; keep a small Citry layer and
presence protocol for controlled state, reasons, nested ownership, theme, and
cleanup; add a JS positioning fallback only for unsupported required cases.

**Why it currently leads:** it preserves Citry's server-authored DOM and
logical context while leaving room for exact compatibility needs. It also
avoids committing the public API to either implementation.

**What can falsify it:** maintaining native and fallback paths doubles the
test matrix or produces observably different semantics; the support floor
requires fallback for most users; browser-owned and Citry-owned layer stacks
cannot be reconciled cleanly.

This ranking is a research hypothesis, not a decision. The prototype should
try to disprove Candidate C rather than merely demonstrate a happy path.

## 10. Likely internal capability boundaries

If the hybrid survives, the smallest plausible reusable units are:

1. **open/presence lifecycle** — controlled/uncontrolled handoff, opening,
   open, closing, closed, cancellation, generation cleanup, and close reason;
2. **dismissible-layer registry** — ordered ownership, nested ancestry,
   outside interaction, Escape, and integration with native top-layer state;
3. **anchored-position adapter** — a flat logical placement vocabulary mapped
   to CSS anchors first and a bounded fallback only when needed;
4. **focus and modality helpers** — initial/return focus, scope, inertness,
   scroll locking, and reference-counted cleanup, selected by the family;
5. **physical-context adapter** — only if teleport remains necessary: root
   selection, theme/color-scheme/direction transfer, ShadowRoot/document
   environment, and cleanup;
6. **toast host/queue/announcer** — persistent and separate from the
   dismissible-layer registry.

These are implementation boundaries, not public components. Public component
APIs should expose only family jobs and the small shared vocabulary users
actually need.

## 11. Prototype and evidence plan

The bounded architecture probes are complete. Their executable harness, raw
three-engine evidence, limitations, and full decision are in the
[`ui_overlay_foundations_spikes/`](ui_overlay_foundations_spikes/prototype-report.md)
report. The wider cases below remain the source inventory for family-specific
qualification; they no longer form one all-or-nothing mega-spike before any
family can be designed.

### 11.1 Platform and positioning probe

Render one trigger and surface using native Popover plus the exact proposed
CSS-anchor subset. Prove or falsify:

- preferred logical placements and ordered flip/shift fallbacks;
- trigger width, available inline/block size, arrow location, and current
  placement reflection;
- nested scroll containers, transformed ancestors, ordinary clipping, fixed
  ancestors, page scroll, visual viewport resize, and mobile keyboard;
- RTL, vertical writing where supported, browser zoom, 400% page zoom,
  fractional geometry, narrow viewport, and oversized content;
- trigger removal, hidden trigger, retained-root replacement, and cleanup;
- current Chromium, Firefox, and WebKit behavior plus Citry's declared support
  floor.

### 11.2 Native layer and dismissal probe

Exercise auto, hint, and manual popovers with native Dialog:

- Popover inside Popover, Menu-like child surface, Tooltip over Popover,
  Popover in Dialog, and Dialog opened from Popover;
- outside pointer, focus outside, Escape, close button, selection,
  programmatic close, browser Back where applicable, and canceled requests;
- only the top eligible layer reacts;
- trigger and child layers count as inside their logical parent;
- focus returns once to the intended surviving element when triggers or
  parents disappear;
- exit presence never keeps a closing layer as the dismissal owner.

### 11.3 Portal comparison probe

Build the same small case with Alpine `x-teleport`. Compare it against native
top-layer rendering for:

- `$provide`/`$inject` and `$component` access;
- CSS variables, `color-scheme`, direction, scoped theme classes, and two
  nested themes;
- native and Alpine event ancestry;
- ShadowRoot and iframe ownership;
- screen-reader reading order and modal/non-modal exposure;
- focus-scope containment and return focus.

The result decides whether teleport is fallback, explicit opt-in, or rejected
for first release.

### 11.4 Presence and morph probe

Drive rapid open/close/open, controlled prop changes during exit, server
rerender during entry and exit, root replacement, trigger replacement, nested
child removal, and component cleanup. Instrument listeners, observers, layer
records, scroll locks, inert owners, focus guards, timers, and animations.
Every resource must settle to zero after removal.

### 11.5 Drawer probe

Keep two jobs separate:

- modal task Drawer/Sheet using native Dialog/top-layer behavior; and
- persistent/responsive application navigation that participates in layout.

Test nested Popover/Menu, initial and return focus, scroll lock, iOS viewport,
safe areas, edge placement, long content, forms, and reduced motion. Swipe and
drag are out unless a later job proves their cost worthwhile.

### 11.6 Toast host probe

Use a persistent host and exercise:

- declarative server-owned initial items and client-created items;
- visible limits, queue order, dedupe/replacement, timeouts, manual duration,
  hover/focus/page-visibility pause, and removal;
- polite/assertive announcements, repeated messages, actions, no focus theft,
  keyboard access, focus-next, and restoration;
- host replacement and Citry rerender without duplicate announcement;
- top-layer coexistence with Dialog and other overlays;
- 1, 10, 100, and 1,000 queued items as diagnostic scaling, not a benchmark
  gate.

## 12. Decision criteria

The prototype-backed decision should prefer the smallest architecture that
meets all of these:

- correct semantics, keyboard behavior, focus, and announcements for each
  family;
- no clipping in the supported default path;
- deterministic nested ownership across all five families and existing Dialog
  and Combobox;
- server/client agreement and generation-safe cleanup under Citry morphs;
- theme, direction, and environment continuity without undocumented copying;
- a flat, concise public placement vocabulary;
- bounded idle cost for pages with many closed triggers;
- no public generic Overlay API unless a real user job requires one;
- no second general reactive runtime beside Alpine;
- explicit behavior when native capabilities are unavailable.

## 13. Research conclusion

The original blocker was real, but it was too coarsely named.

- **Menu, Tooltip, and Popover** need one anchored-surface and dismissible-layer
  investigation, then separate family behavior specifications.
- **Modal Drawer/Sheet** can likely build on Dialog's modality plus shared
  presence/layer cleanup; **persistent navigation Drawer** is a layout job and
  may be a different family.
- **Toast** needs a persistent queue/announcer host. It shares presence and
  physical layering, but not anchored positioning, outside dismissal, or
  focus trapping.
- **Portalling is no longer the default assumption.** Native top-layer
  rendering preserves DOM ancestry and is now viable enough to test first.
- **CSS Anchor Positioning is the leading geometry candidate**, but only the
  exact browser-tested subset may become a dependency.
- **A public `COverlay` is not justified.** Mature suites share machinery
  internally while keeping family semantics explicit.

The overlay-foundation spike and decision record are complete. Popover and
Tooltip have finished their production implementation passes and validate the
platform-first boundary without creating a public Overlay. Menu is next; this
remains one-family-at-a-time work, not approval to implement all five as one
batch.

## 14. Prototype-backed architecture decision

The browser evidence ratifies Candidate C with two material corrections. See
the [prototype report](ui_overlay_foundations_spikes/prototype-report.md) and
[raw evidence](ui_overlay_foundations_spikes/evidence.json) for exact results.

### 14.1 Anchored surfaces

Menu, Tooltip, and Popover use native Popover top-layer rendering without DOM
relocation. CSS Anchor Positioning owns the default geometry through the exact
tested logical-placement subset. The installed Chromium 151, Firefox 153, and
WebKit 26.5 all passed anchored width, block-end placement, clipping escape,
inheritance, retained ancestry, and block-axis collision flipping.

Do not add Floating UI or another coordinate-writing engine before a concrete
family needs behavior outside that subset. Applied fallback-side reflection,
automatic arrows, virtual anchors, and advanced shift/available-size
middleware require their own bounded evidence before becoming public API.

### 14.2 Controlled dismissal and presence

Public components use `popover="manual"` with one private coordinator per
`ownerDocument` and a listener scope for its Document and each active open
ShadowRoot. Native auto-popover ordering is coherent, but
closing `beforetoggle` is non-cancelable in all three engines and therefore
cannot implement Citry's controlled request/decline contract alone.

The private coordinator owns ordered active registrations across those scopes,
logical nesting, composed-path containment, outside/Escape requests, modal
eligibility, close reason, controlled acceptance, focus return, and cleanup.
It discovers open ShadowRoots from the document and composed event paths, then
uses one bounded capture-listener and mutation-observer set per active scope.
Only an observed modal open transition advances modal order; later events in an
older modal cannot promote it. Capture-phase native Dialog `beforetoggle`
records the closing half synchronously, so even a same-task
`close(); showModal()` is recognized as a new modal generation without
patching browser prototypes. An anchored layer is modal-eligible only when its
trigger belongs to the current modal. Closed triggers retain neither
per-instance document listeners nor scope observers.

Queued dismissal work carries its registration generation, so a close/open
cycle cannot receive stale Escape work. Hidden, inert, disconnected, closed,
and collapsed trigger or surface paths invalidate the layer; a family may add
a private `isEligible()` predicate for policy such as Menu's effectively
enabled trigger. These safety closures bypass a controlled owner's right to
decline and report their real `ancestor` or `modal` reason with `forced: true`.
Focus return resolves the owner document's deep active element through open
ShadowRoots. Focused production tests prove
cross-scope parent cascades, unknown-root modal safety, controlled structural
suppression, declined ordinary close, nested ownership, immediate logical
release before exit, rapid reopen, and zero-resource disposal across all
engines.

Optional exit presence is generation-owned. The layer leaves the dismissal
stack, becomes inert and pointer-inactive, animates, then calls
`hidePopover()`. CSS `overlay` transition retention is only an optimization:
it worked in Chromium and was unavailable in the tested Firefox and WebKit.

### 14.3 Modality, relocation, and Toast

Modal task Drawer/Sheet builds on native Dialog and existing Citry Dialog
behavior. Persistent application navigation stays a layout job. A nested
anchored popover composed correctly with the modal Drawer probe in all three
engines.

Teleport is not the default. Native top-layer rendering preserved CSS
inheritance, DOM ancestry, and native bubbling; physical relocation lost those
properties exactly as Citry's existing `x-teleport` contract predicts.

Toast stays separate from the layer controller. It needs a persistent queue
and announcer host. A global manual-popover host did not become a reliable
interactive layer over modal Dialog in any tested engine, regardless of show
order. The Toast family specification must therefore decide a modal policy;
the leading safe rule queues global presentation/announcement while modal and
uses in-dialog Alert for immediate modal feedback.

### 14.4 Dispatch order

The shared-architecture blocker is cleared for family research and design in
this order:

1. Popover (production implementation pass complete);
2. Tooltip (production implementation pass complete);
3. Menu (next);
4. modal Drawer/Sheet, while separately deciding persistent navigation; and
5. Toast.

Each family still requires its complete 20-section specification, public
examples, API data, focused evidence, and review before runtime work. There is
no public `COverlay`.
