# Toast component specification

**Status (2026-08-09): production implementation pass complete. Specification,
runtime, public reference/examples, quality/scaling wiring, wheel inventory,
and focused Chromium/Firefox/WebKit evidence are checked in. Human visual,
live-region/assistive-technology, mobile/real-device, and released-artifact
review remain.**

## 1. Purpose and product bar

`CToastRegion` delivers brief global application feedback through one
persistent queue, viewport, and announcer. It accepts declarative server
messages and client-created message records, limits visible items, pauses
timers, deduplicates by stable identity, supports one optional action, and
provides an F6 focus route without stealing focus on arrival.

Toast is not a floating Alert. `CAlert` remains the visible persistent or
modal-local feedback surface. Toast does not anchor, trap focus, dismiss on
outside interaction, contribute Form values, or remain interactable behind a
modal Dialog.

## 2. Prior art and complaints

Reviewed 2026-08-09:

- the HTML Dialog and Page Visibility contracts for modal/background and
  timer-pausing behavior;
- WAI-ARIA 1.2 live-region, status, alert, group, and region semantics;
- React Aria ToastRegion/ToastQueue for external queue ownership, hover/focus
  pause, F6 access, focus-next, and focus restoration;
- Radix Toast 1.2.23 for Provider/Viewport separation, hotkey, foreground and
  background announcement content, pause, and swipe tradeoffs;
- Vuetify VSnackbar for queueing, timeout, visibility pause, and its deliberate
  separation from focus/scrim/global overlay-stack behavior;
- Bootstrap Toast for compact item anatomy, autohide, placement, and explicit
  accessibility guidance;
- Web Awesome 3.11 Toast as the web-component comparison; and
- the Citry three-engine Toast-host spike, which proved identity replacement,
  ordered items, hover pause, stable announcer identity, expiration, and F6
  entry, while falsifying a global manual-Popover host above modal Dialog.

The decisive complaint is architectural: a fixed Alert plus `setTimeout`
duplicates announcements, expires while users read or act, steals or loses
focus when removed, and becomes inert behind native modality. The region owns
those behaviors together.

Vuetify disposition: Snackbar's queue, timeout, visibility pause, color intent,
action, and location jobs map to message records, region inputs, and callbacks.
Multi-line arbitrary HTML, absolute positioning, shaped variants, vertical
layout, and transitions are omitted from V1 because they weaken the bounded
notification job or can be composed as persistent Alert. Swipe/drag is deferred.

## 3. Public composition and anatomy

Python:

```python
CToastRegion(
    items=(
        CToastMessage(
            id="saved-note",
            title="Field note saved",
            description="Aurora Ridge is synchronized.",
            intent="success",
        ),
    )
)
```

Template with client-created records:

```citry-html
<c-CToastRegion
  $c-props="{
    items: notices,
    onDismiss: (id) => notices = notices.filter((item) => item.id !== id),
  }"
/>
```

The native anatomy is one persistent `<section role="region">` viewport,
two persistent visually hidden polite/assertive announcers, and zero or more
direct message groups. A message owns title, optional description, optional
action Button, and optional dismiss Button. Consumers do not render or replace
those structural descendants.

Only one global Region should be active per `Document`/open `ShadowRoot`.
Multiple initialized Regions in the same root fail closed with one diagnostic.
Place the Region near the end of the application root so CSS inheritance and
document ownership are deliberate.

## 4. Server inputs and client inputs

### `CToastRegion`

| Input | Channel | Type / default | Contract |
|---|---|---|---|
| `items` | server fallback | `Sequence[CToastMessage] = ()` | Ordered initial queue; copied and validated once per render. |
| `label` | structural server | nonempty `str = "Notifications"` | Accessible Region name. |
| `placement` | initial/reactive | `CToastPlacement = "block-end-end"` | Logical viewport corner. |
| `limit` | initial/reactive | `int = 3`, 1..10 | Maximum simultaneously presented messages. |
| `duration_ms` | initial/reactive | `int = 8000`, 0 or 1000..120000 | Default lifetime; zero is persistent. |
| `pause_on_hover` | initial/reactive | `bool = True` | Hovering the viewport pauses all active timers. |
| `pause_on_focus` | initial/reactive | `bool = True` | Focus within the viewport pauses all active timers. |
| `pause_on_hidden` | initial/reactive | `bool = True` | Hidden owner document pauses all active timers. |
| `class_`, `style`, `attrs` | server | standard root values | Merge onto the viewport without replacing owned semantics, focus, structure, live regions, placement, or runtime. |

Client `items` accepts an Array of `CToastClientMessage` records and replaces
the supplied queue snapshot. Omission uses the server snapshot. `null` is
invalid rather than a release signal because queue ownership is not a control
toggle. Client `placement`, `limit`, `durationMs`, and pause Booleans use their
server fallback when omitted and diagnose one continuous invalid episode.
`onDismiss` and `onAction` are optional Functions.

### `CToastMessage`

| Field | Type / default | Contract |
|---|---|---|
| `id` | nonempty `str` | Canonical stable identity; no U+0000; unique in one snapshot. |
| `title` | nonempty `str` | Visible and accessible message name. |
| `description` | `str | None = None` | Optional plain supporting text. |
| `intent` | `neutral | info | success | warn | error = neutral` | Presentation only; does not choose announcement priority. |
| `priority` | `polite | assertive = polite` | Announcement urgency. Assertive is reserved for information needing immediate attention. |
| `duration_ms` | `int | None = None` | Per-message lifetime override; zero is persistent. |
| `action_label` | `str | None = None` | One optional action Button. |
| `close_on_action` | `bool = True` | Whether a successful action also dismisses the message. |
| `dismissible` | `bool = True` | Whether the visible dismiss Button is present. |

All strings are exact plain text. CRLF and CR normalize to LF; U+0000 is
rejected. IDs additionally reject ASCII whitespace. Client object keys use
`durationMs`, `actionLabel`, and `closeOnAction`.

## 5. State model

The Region reconciles each supplied snapshot into an internal queue. A new ID
appends in supplied order. A retained ID updates in place; a material update
resets its lifetime and announces the replacement once. Duplicate IDs make the
snapshot invalid and retain the last valid snapshot.

Only the first `limit` unsuppressed messages are presented. Later messages are
queued and receive neither timer nor announcement until promoted. Timeout,
dismiss, and close-on-action remove the runtime entry and suppress that ID
while the producer continues to supply it. Removing the ID ends suppression;
supplying it in a later snapshot creates a fresh message. This prevents a
declined producer update from resurrecting an expired Toast.

Timer state records remaining duration rather than a new full timeout after
every pause. The Region pauses while configured hover/focus/document-hidden
conditions apply and always pauses while any modal Dialog is open outside the
Region. Global messages arriving during modality queue silently. When modality
ends, presentation, announcement, and lifetime begin in normal order.

## 6. Slots and slot data

V1 has no slots. Toast content is plain message data so a client-created item
has the same trusted, measurable, announceable anatomy as an SSR item. Rich
markup, multiple actions, embedded controls, images, progress, or a custom
renderer use a persistent `CAlert` or another task surface.

## 7. Callbacks, native events, and methods

`onDismiss(id, detail)` fires once after runtime removal. Detail contains
`reason: "timeout" | "dismiss" | "action"`, `source`, and the canonical
message snapshot. `onAction(id, detail)` fires for the optional action Button
before an action-caused dismissal. If the action callback removes/replaces the
Region, stale dismissal work stops at a generation/connectedness checkpoint.

Native click and focus events remain observable on the viewport through
`attrs`; callbacks own Toast meaning. No public imperative Python or DOM method
is added. Client creation is ordinary reactive-array composition.

## 8. Semantics, keyboard, focus, and assistive technology

The viewport is a named `role="region"` with `tabindex="-1"`. Arrival never
moves focus. Pressing unmodified F6 outside an eligible Region records the
deep active element and focuses the first presented Toast; pressing F6 inside
returns to that element when usable, otherwise to the owner document body.
Tab and Shift+Tab use ordinary page order and are not trapped.

Each presented Toast is `role="group"`, `tabindex="0"`, and labelled by its
title, with optional description through `aria-describedby`. Dismiss and action
Buttons follow it in ordinary Tab order. When a focused Toast is removed, focus
moves to the following presented Toast, then the preceding one, then the
recorded external target/body when none survive. Escape does not dismiss;
explicit dismissal prevents an invisible global Escape owner.

The polite and assertive announcer nodes are stable for the Region lifetime.
They are empty in server HTML and receive one plain-text announcement at a
time. Repeated identical content is cleared and committed in a later task so
it announces again only for a genuinely fresh ID episode. Announcement text
contains title, description, and `Action available: …` when relevant; the
visible Toast itself is not a live region, preventing duplicate speech.

## 9. Native forms and validation

The Region is not a Form participant. Internal Buttons are always
`type="button"`; no message field contributes FormData or constraint
validation. A Region inside a Form cannot submit it. Put validation feedback
next to the owning Field/Form; Toast may summarize completion but never
replaces error relationships.

## 10. Styling and theme contract

Public variables:

| Variable | Purpose | Default |
|---|---|---|
| `--cui-toast-inline-offset` | viewport inline edge offset | `1rem` |
| `--cui-toast-block-offset` | viewport block edge offset | `1rem` |
| `--cui-toast-gap` | stack gap | `0.75rem` |
| `--cui-toast-width` | preferred message width | `22rem` |
| `--cui-toast-background` | message background | `Canvas` |
| `--cui-toast-foreground` | message foreground | `CanvasText` |
| `--cui-toast-border-color` | message boundary | subtle CanvasText mix |
| `--cui-toast-shadow` | message elevation | `0 1rem 3rem rgb(15 23 42 / 22%)` |
| `--cui-toast-radius` | message corners | `0.75rem` |
| `--cui-toast-padding` | message padding | `1rem` |
| `--cui-toast-accent` | neutral accent | current foreground |
| `--cui-toast-z-index` | nonmodal application stacking hint | `1000` |

Stable parts are `region`, `announcer-polite`, `announcer-assertive`, `toast`,
`content`, `title`, `description`, `actions`, `action`, and `dismiss`. Region
mirrors `data-placement` and `data-paused`; Toast mirrors `data-intent` and
`data-priority`. Unlayered consumer CSS wins. Intent fallbacks remain readable
in light/dark and forced-colors modes.

## 11. Environmental behavior

Logical placement follows direction and writing mode. Width clamps to the
dynamic viewport and long text/actions wrap. The fixed Region observes safe
area insets, narrow/400% zoom, nested color schemes, forced colors, print,
coarse pointer, page visibility, and open ShadowRoot ownership. V1 has no
required motion, so reduced motion needs no behavioral branch.

Print suppresses the Region: transient delivery is not document content.

## 12. Overlay and layering behavior

Toast is ordinary fixed content, not a Popover, dismissible layer, or modal.
It never consumes outside interaction or Escape. While any native modal Dialog
is active outside the Region, the Region is `inert`, visually suppressed, and
its queue/announcers/timers pause. Existing messages resume with their prior
remaining duration after the last relevant modal closes. Immediate feedback
inside a modal uses `CAlert` inside that modal.

The Region does not teleport. Authors place it in the intended document or
open ShadowRoot; theme, direction, events, and focus remain in that physical
context. Iframe queues are independent.

## 13. Collections, async data, and identity

Identity is the canonical message ID. Snapshot order is queue order; retained
IDs preserve their position unless the supplied sequence reorders them. A
replacement is one episode, not a duplicate. Async producers own race and
authorization policy before updating `items`; Region callbacks always return
the canonical snapshot they acted on.

One, ten, one hundred, and one thousand queued items are diagnostic scaling
profiles. Only `limit` messages create visible interaction/timers. Queue
reconciliation is O(n) with a Map/Set pass; no pairwise duplicate search.

## 14. Server render, morph, and cleanup

SSR emits the first visible-limit messages, empty stable announcers, and the
complete queue in component data. Without JavaScript, those messages remain
visible and persistent; no timeout, F6 service, dynamic creation, or modal
pause is claimed.

A correlated retained Region transfers active/suppressed identity, remaining
durations, queue order, focus identity, and announcer episode without
re-announcing unchanged items. A changed server message resets that identity's
lifetime and announcement. Replacement creates a fresh generation; old
timeouts/tasks/observers cannot mutate it. Removal clears timers, observers,
document listeners, focus records, and the root registry.

## 15. Security and content trust

All message fields enter through text nodes; no HTML or URL field exists.
Callbacks receive data and connected DOM sources, never executable strings.
Server mappings/records are copied before validation. Client records reject
accessors/prototypes only to the degree ordinary JS object reads allow; the
Region never evaluates them or interpolates them into code.

`attrs` rejects case-insensitive static and dynamic/property aliases for
`role`, `tabindex`, `aria-label`, `aria-labelledby`, `aria-live`,
`aria-atomic`, `aria-hidden`, `hidden`, `inert`, part/state/runtime markers,
`x-html`, `x-text`, `x-if`, `x-for`, `x-teleport`, `x-ignore`, `x-model`,
`x-modelable`, and whole-object spreads. It may carry unrelated targeted
bindings and native events.

## 16. Assets and performance

The family ships one JS initializer and one CSS asset. One Region owns one
document/ShadowRoot keydown listener, visibility listener, modal observer, and
at most `limit` timeout handles. Hover/focus are viewport-local listeners.
No listener or observer is added per queued message.

Asset reports record raw/gzip/Brotli bytes. Scaling records bounded server
render/output diagnostics for 1/10/100/1000 messages and a browser counter for
visible DOM/timers at a large queue. These are diagnostic, not latency gates.

## 17. Acceptance matrix

Server tests prove exact native anatomy; all record/config validation; copied
inputs; duplicate/canonical IDs; string hostility; no-JS initial limit;
trusted attrs; class/style; exports, typing, API schema, docs discovery,
quality/scaling registration, asset budget, and wheel inventory.

Focused Chromium/Firefox/WebKit tests prove insertion, order, replacement,
dedupe, limit promotion, timeout, persistent duration, hover/focus/visibility
pause with remaining time, repeated announcement sequencing, priority
separation, action/dismiss callback order, no arrival focus movement, F6 in/out,
focused removal handoff, modal pause/resume, logical RTL placement, long text,
light/dark/forced-colors/print, hostile reactive records, retained replacement,
and zero-resource cleanup. Axe covers initial and active states.

Manual release evidence covers VoiceOver/Safari, NVDA/Firefox or Chromium,
JAWS/Chromium, mobile screen readers, repeated live announcements, keyboard
timing, real safe areas, visual hierarchy, and motion comfort. Hosted Nu is
required when local Java is unavailable.

## 18. Compatibility classification

Stable: `CToastRegion`, `CToastMessage`, documented inputs/callbacks/types,
message field names, native roles/relationships, F6 behavior, public parts,
reflections, variables, timeout/dedupe/modal policy, and no-JS boundary.

Private: registration markers, announcer scheduling, timer/observer records,
root registry, exact DOM class names, and implementation generation tokens.

Deferred: imperative service method, custom renderer/slots, more than one
action, swipe/drag, transitions, portal/top-layer host, modal-local Region,
cross-frame queue, persistence across navigation, and service-worker delivery.

## 19. Public documentation contract

The guide has ten result-first examples: at-a-glance intents; reactive client
queue; replacement/dedupe; timeout/pause; persistent action; visible limit;
F6 focus access; modal pause with Alert substitute; placement/RTL; and theme
customization. Every preview initializes cleanly, has no unexpected console or
page errors, and maps to focused evidence. API data exhaustively covers Inputs,
Events, CSS, Attributes, Selectors, and Interfaces; Slots and Methods are empty.

## 20. Open decisions and deferred work

No implementation blocker remains in the V1 contract. Public imperative
dispatch advances only after application code proves reactive-array composition
is materially awkward. Custom content advances only with an announceable,
focus-safe, client-creatable renderer contract. Swipe/drag must earn its touch,
selection, scroll, direction, and accessibility cost independently.

## 21. Internationalization

Region, dismiss, and action-announcement text use the keys and typed values in
the structured [Translation keys table](../../../packages/py/citry_ui/citry_ui/components/ctoast/api.yml).
The stable region and initial dismiss controls use `$c-tr`; browser-created
dismiss controls use `i18n.bind()` against each toast's current title. The
action announcement translates once when the toast is added so a later locale
switch does not replay an old notification. `CToastMessages` overrides each
runtime pattern independently.
