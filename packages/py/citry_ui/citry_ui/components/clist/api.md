---
title: List
description: Compose semantic content, navigation, and action lists with Citry UI.
---

# List

Use `CList` and `CListItem` for concise semantic collections. Items can stay static, navigate, or act as native Buttons.

## List at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clist/snippets/at_a_glance.py" title="List at a glance" />

## Present semantic content

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clist/snippets/content.py" title="Present semantic list content" />

## Build navigation

Set `href` on an Item for a whole-row link. `current=True` adds `aria-current="page"`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clist/snippets/navigation.py" title="Build list navigation" />

## Add media, descriptions, and trailing content

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clist/snippets/anatomy.py" title="Compose List Item anatomy" />

## Add whole-row and secondary actions

Use `action=True` for one whole-row Button. Keep an Item static when its end slot contains a separate control.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clist/snippets/actions.py" title="Compose List actions" />

## Nest Lists

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clist/snippets/nested.py" title="Nest semantic Lists" />

## Choose density and dividers

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clist/snippets/presentation.py" title="Choose List presentation" />

## Customize List

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/clist/snippets/customization.py" title="Customize List" />

## Accessibility and behavior

Lists retain native `ul`/`ol` and `li` semantics. Only links, whole-row Buttons, and authored secondary controls enter Tab order. Use Menu for command popovers, Tabs for view switching, and DataTable for two-dimensional records.

<!-- UI_LIBRARY_API_REFERENCE -->
