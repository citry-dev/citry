---
title: Toolbar
description: Group persistent controls under one name and one page Tab stop.
---

# Toolbar

Use `CToolbar` for three or more persistent editor, map, table, or contextual
controls. Toolbar owns focus movement only: Buttons own actions, Toggles own
pressed state, and Menu or Popover owns its surface.

## Toolbar at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctoolbar/snippets/at_a_glance.py" title="Toolbar at a glance" />

## Group persistent commands

Give each Toolbar a concise label. One owned control participates in the page
Tab order; Left and Right move among controls in a horizontal Toolbar.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctoolbar/snippets/commands.py" title="Group persistent commands" />

```citry-html
<c-CToolbar label="Text formatting">
  <c-CButton>Undo</c-CButton>
  <c-CToggle>Bold</c-CToggle>
  <c-CToggle>Italic</c-CToggle>
</c-CToolbar>
```

Use `CButtonGroup` instead when related actions should remain separate page
Tab stops. Use `CToggleGroup` when a group owns one shared selection value.

## Compose groups, separators, links, and overlays

ButtonGroup and ToggleGroup may organize controls without becoming a second
focus owner. Divider stays noninteractive. Menu and Popover activators remain
Toolbar controls while their opened surfaces keep independent focus behavior.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctoolbar/snippets/composition.py" title="Compose Toolbar controls" />

## Choose orientation and boundaries

Vertical Toolbars use Up and Down. Home and End reach the first and last
available control. Set `loop=False` when arrow movement should stop at an edge.
Horizontal direction follows LTR or RTL.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctoolbar/snippets/orientation.py" title="Choose Toolbar orientation" />

## Compare variants and sizes

Plain adds no surface, soft adds a quiet background, and outline adds a
boundary. Toolbar does not change child Button or Toggle variants.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctoolbar/snippets/variants.py" title="Compare Toolbar variants and sizes" />

## Respect disabled ownership

Native disabled controls, `aria-disabled="true"`, hidden or inert controls,
disabled native fieldsets, and disabled `CForm` state are skipped. If the
focused control becomes unavailable, focus moves to the nearest available
Toolbar control only when focus had belonged to the Toolbar.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctoolbar/snippets/disabled.py" title="Toolbar disabled controls" />

## Customize Toolbar

Public variables control the Toolbar surface and spacing. Child controls keep
their own component variables and public parts.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctoolbar/snippets/customization.py" title="Customize Toolbar" />

## Accessibility and content rules

Toolbar requires at least three owned Buttons or links after browser
initialization. Do not place text inputs, selects, textareas, contenteditable
regions, nested Toolbars, or authored `tabindex` inside it. Their keyboard or
focus contracts conflict with Toolbar's roving focus. Icon-only controls still
need their own accessible name.

Native Buttons remain responsible for `type="button"` when they must not
submit a Form. Citry UI Button and Toggle already use form-safe Button roots.

<!-- UI_LIBRARY_API_REFERENCE -->
