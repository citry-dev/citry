---
title: Editable
description: Edit one short text value in place without giving up native form behavior.
---

# Editable

Use `CEditable` for compact names, titles, and labels that are usually read and
occasionally changed. It keeps one native Input as form and validity truth.

## Editable at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ceditable/snippets/at_a_glance.py" title="Editable at a glance" />

## Submit and reset a value

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ceditable/snippets/forms.py" title="Use Editable in a form" />

## Control the committed value

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ceditable/snippets/controlled.py" title="Control Editable" />

## Choose when editing commits

The default `both` mode commits with Enter or when focus leaves the whole
component. `enter`, `blur`, and `explicit` narrow that behavior.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ceditable/snippets/submit_modes.py" title="Editable submit modes" />

## Place edit actions

Pencil, confirm, and cancel actions sit inside the Input at inline-end by
default. Use `action_position="outside"` when they need independent space.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ceditable/snippets/action_positions.py" title="Place Editable actions" />

## States, variants, and sizes

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ceditable/snippets/states.py" title="Editable states" />

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ceditable/snippets/variants.py" title="Editable variants and sizes" />

## Keyboard behavior

The edit Button enters edit mode. Enter commits when enabled by `submit_mode`,
Escape cancels, and Tab follows ordinary page order. Blur modes commit only
after focus leaves the Input and both edit actions.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ceditable/snippets/keyboard.py" title="Edit with the keyboard" />

## Customize Editable

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ceditable/snippets/customization.py" title="Customize Editable" />

## Accessibility and forms

View mode exposes ordinary text and a named edit Button. Edit mode exposes one
native text Input plus named confirm and cancel Buttons. The Input stays the
successful form control in both modes and owns required validity and reset.
Before client initialization the native Input is the visible fallback.

Use `CInput` for a value that is primarily edited, and `CTextarea` for
multiline content.

<!-- UI_LIBRARY_API_REFERENCE -->
