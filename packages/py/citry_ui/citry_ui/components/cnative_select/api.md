---
title: Native Select
description: Choose one value with native keyboard, touch, forms, validation, and an optional controlled browser value.
---

# Native Select

Use `CNativeSelect` for one choice from a finite server-owned list. It renders
one native Select element, so keyboards, touch pickers, autofill, forms,
validation, and reset keep their browser behavior.

## Native Select at a glance

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cnative_select/snippets/at_a_glance.py"
  title="Native Select at a glance"
/>

## Compose a labelled Select

Put Native Select inside `CField` when it needs a label, description, error,
or composed state. Pass options as `CNativeSelectOption` and
`CNativeSelectGroup` records.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cnative_select/snippets/compose_select.py"
  title="Compose Native Select in templates and Python"
/>

Outside `CField`, provide a native label or accessible name yourself.
`CNativeSelect` has no slots or child content.

## Build options and groups

Option values are stable form and morph identities. They must be unique and
nonempty. Groups preserve order, cannot nest, and may disable all their
options.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cnative_select/snippets/options_and_groups.py"
  title="Use flat options, groups, and disabled choices"
/>

Labels are plain text. Put rich rows, search, remote data, or virtualization
in a future custom Select rather than native options.

## Prompt and require a choice

`placeholder` inserts the first empty-value option. It is also required for a
conforming required single Select.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cnative_select/snippets/placeholder_and_required.py"
  title="Compare optional and required destinations"
/>

An empty string selects an existing placeholder. Without a placeholder,
`None` leaves native initial selection to the first enabled option.

## Choose a variant

`outline`, `filled`, and `plain` change the closed-control treatment without
changing the native picker.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cnative_select/snippets/variants.py"
  title="Compare Native Select variants"
/>

## Choose a size

`sm`, `md`, and `lg` adjust visual padding and text size. This `size` is not
the native listbox-size attribute, which the component rejects.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cnative_select/snippets/sizes.py"
  title="Compare Native Select sizes"
/>

## Use Field and Form states

Required, disabled, and invalid keep their native differences. Native Select
does not simulate read-only behavior: a Field requesting read-only rejects
this control instead of presenting an editable control as locked.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cnative_select/snippets/field_states.py"
  title="Compare survey states"
/>

## Control browser selection

Supply client `value` through `$c-props` to control current selection. Mirror
the native `input` event to accept user choices. Omit the prop to release
control without replacing a valid browser-owned selection.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cnative_select/snippets/controlled_selection.py"
  title="Control and release a vessel assignment"
/>

Client `null` selects the placeholder when present, otherwise it means no
selection. Invalid or disabled controlled values report once and follow the
documented fallback. Native Select adds no value-change callback or custom
DOM event.

## Keep the platform picker

Citry UI styles the closed root. The browser or operating system owns the
open picker, including its layout, scrolling, dismissal, touch behavior, and
assistive-technology presentation.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cnative_select/snippets/native_picker.py"
  title="Use native focus, events, and external Form ownership"
/>

Listen to native `input`, `change`, focus, and invalid events directly.
Consumers may call native methods such as `focus()` and, where supported,
`showPicker()` on the root ref. The component does not promise the open
picker's DOM or styling.

## Customize the theme

Override public variables on an ancestor or one Select. Use the stable part
selector for targeted rules.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cnative_select/snippets/theme_customization.py"
  title="Theme two expedition controls"
/>

`class_` and `style` target the native root. Unlayered consumer CSS overrides
the low-specificity defaults; named layers follow the site-wide Citry UI
layer ordering contract.

## Accessibility and trust

Keep a visible label even when placeholder text is present. Native Select
adds no role, focus proxy, or keyboard handler. Labels, values, names, IDs,
and autocomplete hints render as plain text, including trusted-string
subclasses. `attrs`, `class_`, `style`, and option/group `attrs` remain trusted
code surfaces for unowned native, ARIA, data, and Alpine attributes.

Use `attrs={"form": "survey"}` for an external native Form owner. That Form
element and ID must remain stable for one Select initialization; rerender the
Select when ownership changes. Dynamic `form` bindings and duplicate
case-insensitive spellings are rejected.
