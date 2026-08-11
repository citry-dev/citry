---
title: HoverCard
description: Preview supplementary content behind a link or control.
---

# HoverCard

Use `CHoverCard` to preview supplementary profile, document, or destination
details on hover and keyboard focus. Essential information and actions must
remain available without the preview.

## HoverCard at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/chover_card/snippets/at_a_glance.py" title="HoverCard at a glance" />

## Preview a document

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/chover_card/snippets/document.py" title="Preview a document" />

## Control visibility

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/chover_card/snippets/controlled.py" title="Control HoverCard" />

## Tune delays

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/chover_card/snippets/delays.py" title="Tune HoverCard delays" />

## Choose placement

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/chover_card/snippets/placements.py" title="Place HoverCard" />

## Choose size and arrow

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/chover_card/snippets/sizes.py" title="HoverCard sizes" />

## Nested color schemes

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/chover_card/snippets/themes.py" title="HoverCard themes" />

## Customize HoverCard

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/chover_card/snippets/customization.py" title="Customize HoverCard" />

## Accessibility and interaction

The activator keeps its authored accessible name, navigation, and click
behavior. The preview is `aria-hidden` supplementary content and cannot contain
focusable or interactive descendants. Focus opens it visually; Escape and blur
close it without moving focus. Touch contact does not open it.

Use `CTooltip` for a concise accessible description and `CPopover` when people
must interact with the overlay.

<!-- UI_LIBRARY_API_REFERENCE -->
