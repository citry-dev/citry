---
title: Stepper
description: Communicate and optionally navigate ordered workflow progress.
---

# Stepper

Use `CStepper` for the progress and navigation surface of a finite workflow.
Compose the current panel, validation, and Previous/Next actions beside it so
application state has one owner.

## Stepper at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cstepper/snippets/at_a_glance.py" title="Stepper at a glance" />

## Navigate a linear workflow

Set `interactive` to render form-safe native Buttons. Linear mode permits the
current and completed Steps while future Steps remain unavailable.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cstepper/snippets/interactive.py" title="Navigate completed Steps" />

## Allow non-linear navigation

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cstepper/snippets/nonlinear.py" title="Navigate Steps in any order" />

## Show workflow metadata

Optional descriptions and error state belong to each Step declaration.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cstepper/snippets/states.py" title="Show optional and error Steps" />

## Control the active Step

Client `active` is controlled while supplied. `onActiveChange` requests a new
zero-based index; the application decides whether to accept it.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cstepper/snippets/controlled.py" title="Control active workflow state" />

## Compare orientation, size, and variant

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cstepper/snippets/presentation.py" title="Compare Stepper presentation" />

## Customize Stepper

Public variables and part selectors work from an ancestor or the Stepper root.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cstepper/snippets/customization.py" title="Customize Stepper" />

## Accessibility and behavior

The root is a named navigation landmark with an ordered list. The current
Step uses `aria-current="step"`. Interactive Steps are ordinary
`button type="button"` controls, so Tab, Enter, Space, focus, disabledness, and
form safety remain native. Stepper does not implement a composite Arrow-key
model and does not render workflow panels.

<!-- UI_LIBRARY_API_REFERENCE -->
