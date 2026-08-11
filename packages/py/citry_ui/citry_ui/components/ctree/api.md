---
title: Tree
description: Explore and select hierarchical application data.
---

# Tree

Use `CTree` for compact hierarchical application data such as files or object
structures. Use disclosure navigation for ordinary site links.

## Tree at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctree/snippets/at_a_glance.py" title="Tree at a glance" />

## Control expansion

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctree/snippets/controlled_expansion.py" title="Control expanded branches" />

## Select one Item

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctree/snippets/single_selection.py" title="Select one Item" />

## Select multiple Items

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctree/snippets/multiple_selection.py" title="Select multiple Items" />

## Navigate with the keyboard

Down and Up move through visible Items. Right expands or enters a branch;
Left collapses or returns to its parent. Home, End, and buffered
typeahead follow the ARIA Tree pattern.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctree/snippets/keyboard.py" title="Navigate a Tree" />

## Disable Items

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctree/snippets/disabled.py" title="Disable Tree Items" />

## Customize Tree

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctree/snippets/customization.py" title="Customize Tree" />

## Accessibility and behavior

The named root uses `role="tree"`; Items use `role="treeitem"` and nested
children use `role="group"`. One visible Item is in the Tab order. Expansion,
selection, focus, and application action are separate states. Space selects,
Enter selects and invokes `onAction`, and double-click invokes the action.

<!-- UI_LIBRARY_API_REFERENCE -->
