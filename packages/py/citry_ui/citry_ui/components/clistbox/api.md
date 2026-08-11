---
title: Listbox
description: Choose one or more values from a persistent collection.
---

# Listbox

Use `CListbox` when the choices should remain visible while people compare and
select them. Use Select or MultiSelect when the choices should open from a
compact form control.

## Listbox at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clistbox/snippets/at_a_glance.py" title="Listbox at a glance" />

## Select one value

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clistbox/snippets/single_selection.py" title="Select one value" />

## Select several values

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clistbox/snippets/multiple_selection.py" title="Select several values" />

## Group related options

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clistbox/snippets/groups.py" title="Group options" />

## Control selection

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clistbox/snippets/controlled.py" title="Control selection" />

## Disabled collections and options

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clistbox/snippets/disabled.py" title="Disable Listboxes and Options" />

## Keyboard navigation

Down and Up move between enabled Options. Home and End jump to the collection
edges, printable text performs buffered typeahead, Enter or Space selects, and
Escape clears a non-mandatory selection.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clistbox/snippets/keyboard.py" title="Navigate a Listbox" />

## Customize Listbox

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clistbox/snippets/customization.py" title="Customize Listbox" />

## Accessibility and behavior

The named collection uses `role="listbox"`; Options use `role="option"`, and
visible group labels name `role="group"` collections. One enabled Option is in
the Tab order. Focus and selection remain separate, and disabled Options are
skipped by keyboard navigation.

`CListbox` is a persistent application selection surface, not a form control.
Use Select or MultiSelect when native form submission, reset, validity, or a
compact popup is required.

<!-- UI_LIBRARY_API_REFERENCE -->
