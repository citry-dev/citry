---
title: Radio
description: Select one visible option with native Citry UI Radio Groups and Radios.
---

# Radio

Use `CRadioGroup` and `CRadio` when people should see every option and select
exactly one. Native fieldset, legend, labels, keyboard behavior, validity,
reset, and FormData stay browser-owned.

## Radio at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cradio/snippets/at_a_glance.py" title="Radio at a glance" />

## Compose a group

Give Group one shared `name`, a visible `label` slot, and Radios with unique
values. `CRadio` cannot be used outside Group.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cradio/snippets/basic.py" title="Compose a Radio Group" />

```citry-html
<c-CRadioGroup name="habitat" value="woodland">
  <c-fill name="label">Habitat</c-fill>
  <c-fill name="default">
    <c-CRadio value="woodland">Woodland</c-CRadio>
    <c-CRadio value="wetland">Wetland</c-CRadio>
  </c-fill>
</c-CRadioGroup>
```

## Add descriptions and disabled choices

Descriptions connect to their native Radio. Disable one unavailable option
without disabling its siblings.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cradio/snippets/descriptions.py" title="Describe and disable Radio options" />

## Control selection in the browser

Pass `value` through `$c-props="{...}"`. A known string controls one option;
`null` clears selection; omission releases control. Handle native `input` or
`change` with `$event.target.value`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cradio/snippets/controlled.py" title="Control a Radio Group" />

## Use native forms and validation

The checked enabled Radio contributes one shared name/value entry. Required
groups use native validation and reset.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cradio/snippets/forms.py" title="Submit and validate Radio values" />

## Choose orientation

Vertical is easiest to scan. Horizontal groups wrap and keep native keyboard
behavior.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cradio/snippets/orientation.py" title="Compare Radio orientations" />

## Choose presentation

Compare solid and outline treatments, three sizes, and logical label placement.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cradio/snippets/presentation.py" title="Compare Radio presentation" />

## Compose with Field

Inside `CField`, Field owns label, description, error, required, disabled, and
invalid state. Do not add the Group `label` slot there.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cradio/snippets/field.py" title="Compose Radio with Field" />

## Customize Radio

Override public group, control, color, focus, spacing, and disabled variables.
Stable part selectors target the fieldset, legend, item, input, label, and
description.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cradio/snippets/customization.py" title="Customize Radio with public CSS" />

## Choose the right control

Use Native Select when choices should collapse, Checkbox for independent
choices, and Switch for an immediate Boolean setting. Radio Card and Segmented
Control are separate interaction and anatomy families.
