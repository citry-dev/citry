---
title: Button Group
description: Arrange related Citry UI actions as one named group.
---

# Button Group

Use `CButtonGroup` when several Buttons perform closely related actions. It owns grouping and layout, not selection.

## Button Group at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbutton_group/snippets/at_a_glance.py" title="Button Group at a glance" />

## Group related actions

Give every group a concise accessible label. Buttons remain ordinary native actions.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbutton_group/snippets/related_actions.py" title="Group related actions" />

```citry-html
<c-CButtonGroup label="Map controls">
  <c-CButton variant="outline">Zoom in</c-CButton>
  <c-CButton variant="outline">Zoom out</c-CButton>
</c-CButtonGroup>
```

## Attach or space Buttons

Attached groups share outer geometry. Set `attached=False` for separate Buttons that still belong to one named action set.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbutton_group/snippets/attachment.py" title="Compare attached and spaced groups" />

## Choose orientation and growth

Vertical groups describe stacked actions. `grow=True` gives direct Buttons equal width.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbutton_group/snippets/layout.py" title="Choose Button Group layout" />

## Compose mixed actions

Each Button keeps its own variant, intent, loading, disabled, and link behavior. Use `CToggleGroup` instead when the Buttons represent selected choices.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbutton_group/snippets/composition.py" title="Compose mixed Button actions" />

## Customize Button Group

Public variables control spacing, outer radius, and border overlap.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbutton_group/snippets/customization.py" title="Customize Button Group" />

## Accessibility and behavior

The root is a named `group`. Tab order, activation, Form behavior, loading, and disabled state belong to each Button. Button Group adds no JavaScript or roving focus.

<!-- UI_LIBRARY_API_REFERENCE -->
