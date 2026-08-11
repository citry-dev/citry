# Overlay-foundations prototype report

**Status:** architecture-gating probes complete on 2026-08-09. The
platform-first hybrid passes with two corrections: controlled anchored layers
need a small Citry-owned dismissal stack over `popover="manual"`, and exit
presence cannot rely on CSS `overlay` transitions across the browser matrix.

This is a disposable architecture probe, not a component implementation or a
browser-support declaration. The executable harness is
[`run_spikes.py`](run_spikes.py); its full recorded output is
[`evidence.json`](evidence.json).

Run it from the repository root:

```console
source .venv/bin/activate
python docs/design/ui_overlay_foundations_spikes/run_spikes.py \
  --output docs/design/ui_overlay_foundations_spikes/evidence.json
```

## 1. Environment

| Piece | Version |
|---|---|
| Playwright | 1.62.0 |
| Chromium | 151.0.7922.34 |
| Firefox | 153.0 |
| WebKit | 26.5 |
| Viewport | 960 by 720 CSS pixels |

Every probe completed with zero page errors and zero console errors in all
three engines. The versions above are the tested snapshot, not Citry UI's
eventual minimum-browser policy.

## 2. Results

### 2.1 Native Popover and CSS anchors

All three engines supported the exact proposed baseline:

- `showPopover()` and `:popover-open`;
- `anchor-name` and `position-anchor`;
- logical `position-area`;
- `anchor-size(width)`;
- `position-try-fallbacks: flip-block`; and
- `position-visibility: anchors-visible`.

The geometry probe exercised the first five items. `position-visibility` was
feature-detected only and remains a family-level trigger-visibility case.

The surface matched the 148 px trigger width, appeared at its block end,
escaped an `overflow: hidden` ancestor, remained hit-testable outside that
ancestor, inherited the provider's CSS color, and retained its original DOM
parent. A second surface next to the viewport block end flipped above its
anchor and stayed inside the viewport in every engine.

`popover="hint"` was supported by Chromium and Firefox but not WebKit. Tooltip
cannot depend on hint behavior in the first release.

The probe also confirmed a limitation relevant to arrows and public placement
reflection: CSS fallback chooses the final geometry, but does not expose an
interoperable applied-fallback state to component JavaScript or selectors.
The first component specifications should not promise a reflected current
side or an automatically reoriented arrow unless a separate bounded observer
probe earns that feature.

**Decision:** CSS Anchor Positioning owns coordinates on the supported default
path. Do not add Floating UI or a Citry coordinate-writing engine preemptively.
Use a flat logical placement vocabulary in public family specifications and
map only the browser-tested subset. Virtual anchors, selection ranges,
arbitrary shift middleware, reflected fallback side, and arrows remain
feature-specific follow-up work.

### 2.2 Native dismissal and Dialog composition

Nested `popover="auto"` surfaces behaved consistently:

- both parent and child could remain open;
- the first Escape closed only the child;
- the second Escape closed the parent;
- a Popover in a modal Dialog closed before the Dialog; and
- `popover="manual"` ignored outside click and Escape.

Opening `beforetoggle` was cancelable in all three engines. Closing
`beforetoggle` was not. Native auto-popover dismissal therefore cannot by
itself implement Citry's established controlled-owner contract, where an
`onOpenChange` request may be declined without first closing the surface.

**Decision:** Menu, Tooltip, and Popover should use native top-layer rendering
through `popover="manual"` plus a document- or ShadowRoot-scoped internal
controller. The controller owns only the behavior the browser no longer owns:
ordered registrations, logical ancestry, outside interaction, Escape,
controlled requests, close reasons, focus return, and cleanup. It must use a
bounded set of shared capture listeners rather than one document listener per
closed trigger.

Native auto-popover remains useful platform evidence and may serve explicitly
uncontrolled internal cases later. It is not the common public-component
state machine.

### 2.3 Controlled stack and presence

The manual-popover prototype supplied a two-layer stack and 160 ms exit
presence. All three engines proved the same sequence:

1. outer and inner layers registered in order;
2. the controlled inner owner declined Escape and both layers stayed open and
   interactive;
3. after acceptance, the inner layer left the logical stack immediately,
   became inert, and kept its top-layer rendering only for animation;
4. an immediate second Escape targeted the outer layer rather than the
   exiting child;
5. both animations settled and both popovers closed;
6. open → close → open canceled the stale exit generation and kept the layer
   open; and
7. disposal left zero stack entries, open popovers, and active animations.

The CSS-only presence probe produced a different matrix. Chromium retained a
closing popover during a discrete `overlay`/`display` transition and faded it
from opacity 1 to 0. Firefox and WebKit reported no `overlay` support and
removed the surface immediately, despite supporting
`transition-behavior: allow-discrete`.

**Decision:** logical dismissal ownership ends before visual exit. An exiting
surface is inert and pointer-inactive. Optional cross-browser exit presence
uses a generation-owned Web Animation or equivalent bounded client lifecycle,
then calls `hidePopover()` at settlement. CSS `overlay` transitions may be an
optimization, never the semantic owner or only implementation. Every family
must still work with zero-duration/reduced-motion exit.

Citry already proves correlated component cleanup, retained generation
replacement, nested Dialog removal, and teleport-frame retirement elsewhere.
The production helper must attach every animation, timer, listener, observer,
focus record, and stack registration to that existing component cleanup.

### 2.4 Native top layer versus physical relocation

A native shown popover retained:

- its authored DOM parent;
- its closest provider;
- inherited CSS variables; and
- native event bubbling through the authored ancestor.

Moving the comparison node to a portal container immediately lost the closest
provider, inherited fallback color instead, and no longer bubbled to the
authored ancestor. This physical result agrees with Citry's existing tested
`x-teleport` contract: lexical Alpine/Citry lookup follows the authored origin,
while CSS inheritance, native containment, `currentTarget`, focus, and event
bubbling follow the physical placement.

**Decision:** do not teleport the default anchored surface. Native top-layer
rendering preserves Citry ownership and physical theme/event context without
copying. A future physical-context adapter is justified only by a concrete
unsupported environment or feature; it is not part of the initial foundation.

ShadowRoot, iframe, and screen-reader routing remain family qualification
cases. They do not justify reparenting light-DOM components before a failure is
observed.

### 2.5 Drawer boundary

The same side-aligned markup proved two different jobs in every engine:

- a persistent `aside` remained in document layout, did not make the main
  content inert, and allowed ordinary main-content focus; and
- a modal side `<dialog>` occupied the full viewport block size at the inline
  end, contained focus, hosted an anchored Popover, and closed the child
  Popover on the first Escape before closing itself on the second.

**Decision:** modal task Drawer/Sheet builds on native Dialog, its existing
Citry focus/modality behavior, and the anchored-layer controller. Persistent
application navigation is a layout surface, not a weakened modal overlay.
The Drawer family design must keep those jobs explicit; research may still
decide whether they are modes of one component or separate exports.

### 2.6 Toast host

The persistent-host prototype proved the non-overlay mechanics needed for the
family:

- repeated ID updated one item instead of inserting a duplicate;
- two IDs produced two ordered items;
- hover paused the first timeout while the second item expired;
- the host remained independent of the producer node;
- the live-region node retained identity; and
- F6 moved focus to the first surviving Toast without focusing on arrival.

A global manual-popover host did not become a safe modal notification plane.
Whether shown before or after a modal Dialog, it was not the hit-tested layer
over the modal. Escape closed the Dialog while the manual popover remained
open. More importantly, a host outside a modal's subtree participates in the
background inertness boundary, so an action Toast there cannot be a reliable
focus target.

**Decision:** Toast does not use the dismissible-layer controller or a global
manual-popover host. It needs a persistent queue/announcer owner with an
explicit modal policy. The safest initial policy to evaluate in the Toast
family specification is:

- global items queue and pause announcement/timeout while a modal is active;
- immediate modal-scoped feedback is rendered inside the modal, normally as
  Alert; and
- interactive global Toasts become available after modality ends.

An alternative modal-local Toast region may advance only if it preserves live
region identity, dedupe, focus handoff, theme, and cleanup without moving an
already-announced node. The spike rejects only the tempting generic
`popover="manual"` host shortcut; it does not freeze the public Toast API.

## 3. Ratified internal boundaries

The research hypothesis survives in this narrower form:

| Boundary | Ratified responsibility |
|---|---|
| Anchored geometry | CSS Anchor Positioning with a small tested logical-placement mapping; no default coordinate-writing loop. |
| Anchored rendering | Native Popover top layer without DOM relocation. |
| Layer controller | Manual-popover registration, ancestry, outside/Escape requests, close reason, controlled acceptance, focus return, and bounded root listeners. |
| Presence | Generation-owned optional entry/exit lifecycle; logical ownership ends before inert visual exit. |
| Modality | Native Dialog plus existing Citry Dialog focus, inertness, scroll-lock, and cleanup behavior. |
| Physical context | No adapter on the default path; add only after a concrete teleport requirement. |
| Toast | Separate persistent queue/announcer host with a deliberate modal policy. |

These are private implementation boundaries. There is still no user job for a
public `COverlay`.

## 4. What is now unblocked

The architecture gate is complete enough for one-family-at-a-time research and
specification of:

1. Popover, to establish the base non-modal anchored surface contract;
2. Tooltip, reusing geometry/top-layer mechanics but defining hover, focus,
   delay, Escape, and noninteractive semantics separately;
3. Menu, adding collection keyboard behavior, focus, selection, submenus, and
   close-on-select rules;
4. modal Drawer/Sheet, building on Dialog; and
5. Toast, using its own host rather than the anchored layer stack.

Implementation does not start from this report alone. Each family still goes
through the normal component research, 20-section specification, example
catalog, adversarial design review, runtime, and evidence pipeline. Popover is
the recommended first family because it exercises the reusable foundation
without Menu's collection behavior or Tooltip's timing policy.

## 5. Remaining qualification, not architecture blockers

The broad checklist in [`../ui_overlay_foundations.md`](../ui_overlay_foundations.md)
still matters. These cases move into the relevant family specifications and
release evidence rather than keeping every family blocked behind one mega
spike:

- page/nested scroll, transformed/fixed ancestors, viewport resize, zoom,
  oversized content, RTL, vertical writing, trigger replacement, and arrows;
- ShadowRoot and iframe roots;
- real Citry rerenders during entry/exit and focus-return target replacement;
- real mobile keyboards, safe areas, iOS scroll, and reduced motion;
- screen-reader reading/announcement order and duplicate Toast announcements;
- Toast page-visibility pause, modal policy, queue limits, 1/10/100/1,000
  diagnostics, and host replacement; and
- manual keyboard, assistive-technology, visual, and released-browser review.

Independent adversarial review is still pending because the active session
policy did not permit spawning a review agent. Do not call the foundation
release-qualified until that review and the family-specific evidence are
complete.
