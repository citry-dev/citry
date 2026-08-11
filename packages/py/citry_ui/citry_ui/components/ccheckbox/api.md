---
title: Checkbox
description: Choose independent Boolean options with native forms, mixed state, and controlled browser checkedness.
---

# Checkbox

Use `CCheckbox` for one independent Boolean choice or one item in a native
multi-value field. It keeps a real checkbox input, visible label, optional
description, form submission, validation, reset, and browser events.

## Checkbox at a glance

Unchecked, checked, disabled, and described choices retain the same native
interaction model.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccheckbox/snippets/at_a_glance.py"
  title="Checkbox at a glance"
/>

## Compose a Checkbox

Write the visible label in the default slot. Add `description` when the choice
needs supporting text.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccheckbox/snippets/compose_checkbox.py"
  title="Compose Checkbox in templates and Python"
/>

```citry-html
<c-CCheckbox
  name="field_notes"
  value="included"
>
  Include field notes
</c-CCheckbox>
```

Compose the same control in Python:

```python
from citry_ui import CCheckbox

field_notes = CCheckbox(
    name="field_notes",
    value="included",
    slots={"default": "Include field notes"},
)
```

The default and description slots accept phrasing content. Keep controls,
editable content, and nested labels outside Checkbox.

## Configure Checkbox

Server inputs are passed in Python through `<c-CCheckbox ... />` attributes or
a `CCheckbox(...)` composition call. Client inputs are passed in the browser
through `$c-props="{...}"`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccheckbox/snippets/configuration.py"
  title="Configure Checkbox"
/>

`checked` and `indeterminate` are independently controllable. Omit either
client input to release that property without replacing the browser's current
value. Other omitted client inputs return to their server, Field, or Form
fallback.

## Submit and validate native values

A checked, enabled Checkbox with a name contributes one `FormData` entry.
Unchecked controls contribute nothing. Reuse a name to submit several checked
values.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccheckbox/snippets/forms_and_validation.py"
  title="Submit, validate, and reset Checkbox values"
/>

`required` applies to one Checkbox. It means that exact control must be
checked, not that one item in a group must be selected. Use application
validation for group minimums until `CCheckboxGroup` has its own contract.

Checkbox does not add a hidden false value. Native Form submission remains the
source of truth.

## Control checked state in the browser

Mirror `event.target.checked` from the native bubbling `input` event to accept
the browser's change. The listener lives on Checkbox's neutral root, so
`event.currentTarget` is not the native input.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccheckbox/snippets/controlled_states.py"
  title="Control, release, and reacquire checkedness"
/>

```citry-html
<c-CCheckbox
  $c-props="{ checked: selected }"
  @input="selected = $event.target.checked"
>
  Archive specimen
</c-CCheckbox>
```

Both `input` and `change` observe the browser-produced value before an
unchanged controlled prop is restored. Use `focusin` and `focusout` at the
component boundary. Observe native validation with `@invalid.capture`.

Do not drive state from root `click`: clicking label text produces the native
label click followed by the input click.

## Show a mixed aggregate

Indeterminate is visual state independent of checkedness and Form submission.
Use it for an aggregate whose descendants are partly selected.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccheckbox/snippets/indeterminate.py"
  title="Control a mixed habitat summary"
/>

HTML has no indeterminate content attribute. Citry's browser runtime sets the
native `indeterminate` property and the native accessibility mapping exposes
mixed state. Server-only output remains an ordinary two-state Checkbox.

Native activation clears indeterminate before `input` and `change`. Supply a
client `indeterminate` value when application state must restore or recompute
it.

## Use Field and Form state

Put Checkbox inside `CField` for an external label, Field description, error,
and shared required, disabled, or invalid state. Omit Checkbox's own label and
description slots in this composition.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccheckbox/snippets/field_states.py"
  title="Compose Checkbox with Field and Form"
/>

Native checkbox inputs do not support read-only. A standalone Checkbox ignores
Form read-only. A Field requesting read-only rejects Checkbox instead of
presenting an editable control as locked. Set `CField(readonly=False)` to opt
that Field out of an enclosing read-only Form.

A disabled Form always wins over local server or client `disabled=False`.
The same applies to a native disabled `fieldset`: browser-effective disabled
state drives the public mirror and styling even when the input's own
`disabled` property is false.

## Label long and compact choices

`label_pos="start"` moves the authored label and description to the logical
start. Direction-aware layout keeps that meaning in RTL. Long text wraps while
the control stays aligned with the first line.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccheckbox/snippets/label_and_description.py"
  title="Use labels, descriptions, and accessible-name-only controls"
/>

For a label-free standalone Checkbox, pass exactly one non-empty static
`aria-label` or `aria-labelledby` through `input_attrs`. Do not add ARIA naming
when a default label or Field label renders: hidden text must not replace the
visible accessible name.

## Choose variant and size

`solid` fills checked and mixed controls. `outline` keeps the surface and uses
the active color for the indicator and border. `sm`, `md`, and `lg` change
control geometry and associated text scale.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccheckbox/snippets/variants_and_sizes.py"
  title="Compare Checkbox variants and sizes"
/>

## Customize the theme

Override public variables on an ancestor or one Checkbox. Use stable part
selectors for targeted rules.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccheckbox/snippets/theme_customization.py"
  title="Theme two botanical checklists"
/>

`class_`, `style`, and `attrs` target the neutral root. `input_attrs` targets
the native input. Unlayered consumer CSS overrides the low-specificity Citry
UI defaults; named layers follow the site-wide layer-order contract.

`data-checked` and `data-indeterminate` are public runtime mirrors. No-runtime
checked styling uses native `:checked`, so it stays accurate without static
mirror attributes.

## Accessibility and trust

The native input owns role, keyboard behavior, focus, checkedness, required
validity, and mixed accessibility state. Checkbox does not author
`aria-checked`, simulate read-only, or add a focus proxy.

The visible label is an explicit `<label for="...">`. The description is its
sibling and is linked with `aria-describedby`, so supporting text does not also
enter the accessible name.

Direct string inputs render as plain text even when supplied through a trusted
string subclass. `attrs`, `input_attrs`, `class_`, and `style` remain trusted
authoring surfaces for unowned attributes. Checkbox rejects directives and
attributes that could replace its native input, label relationship, semantics,
state ownership, runtime markers, or accessibility exposure.
