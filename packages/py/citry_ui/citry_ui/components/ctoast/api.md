---
title: Toast
description: Deliver queued, timed application feedback with Citry UI.
---

# Toast

Use `CToastRegion` once near the end of an application root. It owns a
persistent visible queue, polite and assertive announcers, remaining-time
pause, action/dismiss semantics, and F6 focus access. Arrival never steals
focus.

## Toast at a glance

Intent controls presentation; priority independently controls announcement
urgency.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctoast/snippets/at_a_glance.py"
  title="Toast at a glance"
/>

## Drive a reactive queue

Pass an Array of plain client message records. A stable `id` is queue identity.
Remove IDs in `onDismiss` so expired or dismissed messages can later begin a
fresh episode.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctoast/snippets/reactive_queue.py"
  title="Add application notifications"
/>

```citry-html
<c-CToastRegion
  $c-props="{
    items: notices,
    onDismiss: (id) => notices = notices.filter(item => item.id !== id),
  }"
/>
```

## Replace and deduplicate by ID

A retained ID updates in place. A material update restarts its lifetime and
announces the replacement once; a byte-equivalent snapshot does neither.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctoast/snippets/replacement.py"
  title="Replace a message"
/>

## Pause remaining lifetime

The default lifetime is eight seconds. Set `duration_ms=0` for persistent
messages. Hover, focus within, document visibility, and an unrelated modal
pause remaining time rather than starting a new timeout.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctoast/snippets/timeout_pause.py"
  title="Pause a timed Toast"
/>

## Add one persistent action

`onAction` runs before action-caused dismissal. Set `closeOnAction: false` when
the result should remain visible.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctoast/snippets/persistent_action.py"
  title="Act on a notification"
/>

## Limit the visible stack

Only the first `limit` unsuppressed messages render, announce, and run timers.
Queued records start when promoted.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctoast/snippets/visible_limit.py"
  title="Queue beyond the visible limit"
/>

## Reach notifications with F6

Unmodified F6 moves from the application to the first presented Toast. F6
inside returns to the recorded element. Tab remains ordinary and is never
trapped.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctoast/snippets/focus_access.py"
  title="Use the F6 focus route"
/>

## Pause behind a modal

A global Region becomes hidden, inert, and paused while an unrelated native
modal is open. Use `CAlert` inside the modal for feedback that must be immediate
there.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctoast/snippets/modal_pause.py"
  title="Keep modal feedback local"
/>

## Choose a logical corner

Placements are `block-start-start`, `block-start-end`, `block-end-start`, and
`block-end-end`. Logical edges follow direction and writing mode.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctoast/snippets/placement_rtl.py"
  title="Place Toasts in RTL"
/>

## Customize the surface

Use documented variables and part selectors. Unlayered application CSS wins;
safe-area, narrow viewport, forced-colors, and print behavior stay owned.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctoast/snippets/customization.py"
  title="Customize Toast"
/>

## Composition boundaries

Toast is brief global feedback, not a task surface, form-error relationship,
arbitrary card renderer, or dismissible overlay. Use `CAlert` for persistent
rich content, `CDialog`/`CDrawer` for tasks, and Field/Form errors beside their
controls. V1 deliberately has no slots, imperative service, swipe, portal, or
multi-action layout.
