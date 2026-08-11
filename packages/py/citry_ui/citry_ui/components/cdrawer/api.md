---
title: Drawer
description: Build accessible modal side Drawers and Sheets with Citry UI.
---

# Drawer

Use `CDrawer` for a modal task that enters from a viewport edge. It renders a
native modal Dialog, so focus containment, background inertness, top-layer
ordering, native Forms, and restoration remain platform semantics.

Persistent navigation is not a Drawer mode. Build that later with the layout
and AppShell vocabulary so it can reserve space without trapping focus.

## Drawer at a glance

Logical placement works in LTR, RTL, and other writing modes. `block-end` is
the bottom-Sheet path in ordinary horizontal writing.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdrawer/snippets/at_a_glance.py"
  title="Drawer at a glance"
/>

## Build a Drawer

Provide a visible title and body. Spread `activator_attrs` on one `CButton`.
Spread `close_attrs` on explicit completion or cancel actions.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdrawer/snippets/edit_field_note.py"
  title="Edit a field note"
/>

```citry-html
<c-CDrawer placement="inline-end">
  <c-fill name="activator" data="{ activator_attrs }">
    <c-CButton c-attrs="activator_attrs">Edit note</c-CButton>
  </c-fill>
  <c-fill name="title">Field note</c-fill>
  <c-fill name="description">Update the selected observation.</c-fill>
  <c-fill name="default">...</c-fill>
  <c-fill name="actions" data="{ close_attrs }">
    <c-CButton c-attrs="close_attrs">Done</c-CButton>
  </c-fill>
</c-CDrawer>
```

The activator must settle to exactly one native Button with `type="button"`.
`CButton` already has that safe default. Set the type explicitly when using a
native `<button>`.

## Build a bottom Sheet

Use the same semantic family with `placement="block-end"`; there is no second
`CSheet` alias or mini-language.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdrawer/snippets/bottom_sheet.py"
  title="Open a bottom Sheet"
/>

## Configure placement and size

Placement accepts `inline-start`, `inline-end`, `block-start`, or `block-end`.
Size accepts `sm`, `md`, `lg`, or `full`. The viewport-safe maximum wins over
an oversized requested extent.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdrawer/snippets/configuration.py"
  title="Configure Drawer geometry"
/>

Every server configuration input has a matching client input except identity,
text, class, style, and attrs. Use `initialFocus`, `placement`, `size`, and
`scroll` through `$c-props` for live changes.

## Control visibility

Pass Boolean `open` and `onOpenChange` through `$c-props`. Controlled requests
wait for the owner; retaining `open` declines an ordinary request. Forced
ancestor/native safety closure happens first and reports `forced: true`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdrawer/snippets/controlled_drawer.py"
  title="Control Drawer visibility"
/>

Callback reasons are `trigger`, `close-button`, `action`, `escape`, `outside`,
`native`, and `ancestor`. Detail also carries `controlled`, `forced`, `source`,
and `returnValue`. Removing `open` or passing `null` releases ownership from
the current committed state.

## Place focus and scroll content

`initial_focus="auto"` preserves native autofocus/focus steps.
`initial_focus="title"` starts reading at the visible title. `scroll="body"`
keeps header/actions fixed; `scroll="drawer"` scrolls the whole surface.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdrawer/snippets/long_content.py"
  title="Read long Drawer content"
/>

Tab and Shift+Tab remain inside the nearest modal. Closing returns focus to
the deep active element recorded before opening when it is still usable.

## Use native Forms

Forms retain validation, reset, FormData, and Citry Events. A
`method="dialog"` Form reports its submitter through callback `returnValue`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdrawer/snippets/drawer_form.py"
  title="Submit a Drawer Form"
/>

## Compose anchored layers

Menu, Popover, and Tooltip may open inside a Drawer. Opening a modal suppresses
ineligible anchored layers outside it; closing a parent closes descendants.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdrawer/snippets/nested_layers.py"
  title="Use a Menu inside a Drawer"
/>

## Require explicit completion

Set `dismissible=False` to remove the built-in close control and reject Escape
and backdrop dismissal. Explicit controls using `close_attrs` still work.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdrawer/snippets/explicit_completion.py"
  title="Require explicit completion"
/>

## Customize the Drawer

Use the documented `--cui-drawer-*` variables and part selectors. Defaults use
low-specificity rules, so unlayered application CSS wins. Safe-area insets,
logical placement, forced colors, and reduced motion remain component-owned.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cdrawer/snippets/customization.py"
  title="Customize the Drawer"
/>

`class_`, `style`, and allowed `attrs` merge onto the native Dialog. They may
not replace modality, relationships, visibility, parts, or structure.

## Composition boundaries

Drawer is modal and task-oriented. It does not reserve application layout
space, become permanent at a breakpoint, teleport, expose z-index, or support
swipe/drag. Use `CDialog` for centered work and a later AppShell navigation
surface for persistent navigation.
