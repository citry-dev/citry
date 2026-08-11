---
title: NavigationMenu
description: Compose native website navigation with rich disclosure panels.
---

# NavigationMenu

Use `CNavigationMenu` for persistent site navigation whose top-level entries
are native links or Buttons that disclose richer link collections. It keeps
ordinary `nav`, list, link, and Tab behavior—application commands belong in
`CMenu`.

## NavigationMenu at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnavigation_menu/snippets/at_a_glance.py" title="NavigationMenu at a glance" />

## Link-only navigation

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnavigation_menu/snippets/links.py" title="Native navigation links" />

## Rich navigation panels

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnavigation_menu/snippets/panels.py" title="Rich navigation panels" />

## Control the open panel

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnavigation_menu/snippets/controlled.py" title="Controlled NavigationMenu" />

## Choose orientation

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnavigation_menu/snippets/orientation.py" title="NavigationMenu orientations" />

## Disabled states

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnavigation_menu/snippets/states.py" title="NavigationMenu states" />

## Variants and sizes

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnavigation_menu/snippets/variants.py" title="NavigationMenu variants and sizes" />

## Keyboard navigation

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnavigation_menu/snippets/keyboard.py" title="NavigationMenu keyboard behavior" />

## Customize NavigationMenu

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cnavigation_menu/snippets/customization.py" title="Customize NavigationMenu" />

## Accessibility and interaction

Give every root a concise `label`. Links remain native and all top-level links
and disclosure Buttons remain in ordinary Tab order. Arrow keys provide an
additional convenience between top-level controls; Escape closes an open panel
and returns focus to its Button. Panels can contain ordinary links, Buttons,
and forms, but nested NavigationMenu disclosures are intentionally deferred.

<!-- UI_LIBRARY_API_REFERENCE -->
