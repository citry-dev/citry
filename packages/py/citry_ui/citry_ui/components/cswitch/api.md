---
title: Switch
description: Change an immediate on or off setting with a native Citry UI Switch.
---

# Switch

Use `CSwitch` for a setting that takes effect immediately. Use Checkbox for a
selection or acknowledgement, and Button for an action.

## Switch at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cswitch/snippets/at_a_glance.py" title="Switch at a glance" />

## Change an immediate setting

The visible label describes the setting and stays the same when state changes.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cswitch/snippets/basic.py" title="Change home settings" />

## Add descriptions

Description content is connected to the native Switch. Disabled switches stay
visible but cannot change or submit.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cswitch/snippets/descriptions.py" title="Describe Switch settings" />

## Control state in the browser

Pass `checked` through `$c-props="{...}"`; handle native `input` with
`$event.target.checked`. Omit the prop to release browser ownership.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cswitch/snippets/controlled.py" title="Control a Switch" />

## Submit and validate

A checked named Switch contributes its value to FormData. Required means the
setting must be on.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cswitch/snippets/forms.py" title="Submit Switch settings" />

## Choose size and label position

Use `sm`, `md`, or `lg`. `label_pos="start"` puts text before the control in
logical reading order.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cswitch/snippets/presentation.py" title="Compare Switch presentation" />

## Compose with Field

Inside `CField`, Field owns label, description, error, required, disabled, and
invalid state. Do not add Switch slots there.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cswitch/snippets/field.py" title="Compose Switch with Field" />

## Use Switch semantics deliberately

Switches announce on/off. Keep their labels stable and use them only for
immediate settings.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cswitch/snippets/semantics.py" title="Choose Switch or Checkbox" />

## Customize Switch

Override public colors, geometry, motion, and part selectors.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cswitch/snippets/customization.py" title="Customize Switch with public CSS" />
