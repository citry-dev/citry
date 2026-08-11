---
title: Select
description: Choose one value from a compact, styled form control.
---

# Select

Use `CSelect` when people choose one value and the collection should remain
compact until opened. The component progressively enhances a native Select,
so form submission and reset retain native behavior.

## Select at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cselect/snippets/at_a_glance.py" title="Select at a glance" />

## Submit a value

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cselect/snippets/forms.py" title="Submit a Select" />

## Group related options

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cselect/snippets/groups.py" title="Group options" />

## Control selection

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cselect/snippets/controlled.py" title="Control selection" />

## Read-only and disabled states

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cselect/snippets/states.py" title="Select states" />

## Variants and sizes

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cselect/snippets/variants.py" title="Select variants and sizes" />

## Keyboard behavior

Enter, Space, Down, or Up opens the Listbox. Down and Up move the highlight;
Home and End jump to its edges; printable text performs buffered typeahead;
Enter or Space commits; Escape closes unchanged; and Tab closes while ordinary
page navigation continues.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cselect/snippets/keyboard.py" title="Navigate Select" />

## Customize Select

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cselect/snippets/customization.py" title="Customize Select" />

## Accessibility and forms

The visible Button uses the select-only combobox pattern and keeps DOM focus
while `aria-activedescendant` identifies the highlighted Option. A native
Select remains the form value, validity, and reset truth. Before client
initialization, that native control is the visible fallback.

Use `CListbox` for a persistent collection, `CMultiSelect` for several compact
values, and `CCombobox` when users need text filtering or custom input.

<!-- UI_LIBRARY_API_REFERENCE -->
