---
title: MultiSelect
description: Choose several fixed values from a compact, styled form control.
---

# MultiSelect

Use `CMultiSelect` when people choose several fixed values and the collection
should remain compact until opened. Selected values appear as noninteractive
chips. A native multiple Select preserves repeated-value form submission and
reset behavior.

## MultiSelect at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cmulti_select/snippets/at_a_glance.py" title="MultiSelect at a glance" />

## Submit repeated values

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cmulti_select/snippets/forms.py" title="Submit a MultiSelect" />

## Group related options

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cmulti_select/snippets/groups.py" title="Group options" />

## Control selection

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cmulti_select/snippets/controlled.py" title="Control selection" />

## Read-only and disabled states

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cmulti_select/snippets/states.py" title="MultiSelect states" />

## Close after each choice

By default the popup stays open so several values can be toggled efficiently.
Use `close_on_select` for workflows that should close after every change.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cmulti_select/snippets/close_on_select.py" title="Close after selection" />

## Variants and sizes

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cmulti_select/snippets/variants.py" title="MultiSelect variants and sizes" />

## Keyboard behavior

Enter, Space, Down, or Up opens the Listbox. Down and Up move the highlight;
Home and End jump to its edges; printable text performs buffered typeahead;
Enter or Space toggles the highlighted value; Escape closes; and Tab closes while ordinary
page navigation continues.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cmulti_select/snippets/keyboard.py" title="Navigate MultiSelect" />

## Customize MultiSelect

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cmulti_select/snippets/customization.py" title="Customize MultiSelect" />

## Accessibility and forms

The visible Button uses the select-only combobox pattern and keeps DOM focus
while `aria-activedescendant` identifies the highlighted Option. A native
multiple Select remains the repeated form value, validity, and reset truth. Before client
initialization, that native control is the visible fallback.

Use `CListbox(multiple=True)` for a persistent collection, `CSelect` for one
compact value, and `CCombobox` when users need text filtering or custom input.

<!-- UI_LIBRARY_API_REFERENCE -->
