---
title: Tour
description: Build modal, target-aware product walkthroughs with Citry UI.
---

# Tour

Use `CTour` with direct `CTourStep` declarations for a short modal walkthrough.
Every title, body, and media slot renders on the server. A step can point to an
exact element ID or remain centered in the viewport.

## Tour at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctour/snippets/at_a_glance.py" title="Tour at a glance" />

## Explain page targets

Set `target_id` to a stable HTML ID. Tour scrolls that element into view,
positions the card using logical placement, and keeps the highlighted target
noninteractive while the modal is open.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctour/snippets/targeted.py" title="Target page elements" />

## Use centered introduction and finish steps

Omit `target_id` for a centered dialog step. Centered steps work well for an
introduction, a summary, or a finish message that does not belong to one page
control.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctour/snippets/centered.py" title="Center Tour steps" />

## Control open and active state

`open` and `active` are independent `$c-props` controls. In controlled mode,
`onOpenChange` and `onActiveChange` report requests; update your Alpine state
to accept them. Each detail includes a reason and the stable step value.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctour/snippets/controlled.py" title="Control a Tour" />

## Handle conditional targets

With `missing_target="skip"`, Tour searches in the navigation direction for
the next available or centered step. Use `close` when continuing without the
requested target would be misleading. Tour accepts IDs, not arbitrary CSS
selectors or trusted HTML.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctour/snippets/missing_targets.py" title="Choose a missing-target policy" />

## Customize Tour

Public parts and `--cui-tour-*` variables customize the card, mask, spotlight,
spacing, and focus treatment without replacing modal behavior.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctour/snippets/customization.py" title="Customize Tour" />

## Accessibility and localization

Tour uses native modal `<dialog>` behavior, keeps Tab inside the card, supports
Escape when allowed, and restores focus to the activator. Step changes focus
the new title. `describe=True` explicitly connects a step body through
`aria-describedby`; leave it false for complex structured content.

Close, previous, next, finish, skip, and progress text come from the Citry UI
catalog. Explicit label inputs remain fixed; catalog defaults are server
rendered and update through `$c-tr` under a client-enabled i18n provider.

The highlighted page target is deliberately inert in this modal release. Use
ordinary application UI outside Tour when a user must interact with a target.

<!-- UI_LIBRARY_API_REFERENCE -->
