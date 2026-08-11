---
title: Popover
description: Place accessible interactive content beside a Button with Citry UI Popover.
---

# Popover

Use `CPopover` for compact interactive content that belongs beside one Button
without blocking the rest of the page. It enters the browser top layer, so it
escapes clipping while keeping its original DOM, theme, and Form relationships.

## Popover at a glance

Open each Button to compare concise content, a description, an explicit action,
and trigger-width matching.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cpopover/snippets/at_a_glance.py"
  title="Popover at a glance"
/>

## Build a Popover

Provide an activator, visible title, and body. Spread `activator_attrs` onto one
native Button. `CButton` renders the required Button when `href` is omitted.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cpopover/snippets/moon_inspector.py"
  title="Inspect a moon"
/>

```citry-html
<c-CPopover>
  <c-fill name="activator" data="{ activator_attrs }">
    <c-CButton c-attrs="activator_attrs">
      Inspect Europa
    </c-CButton>
  </c-fill>
  <c-fill name="title">
    Europa
  </c-fill>
  <c-fill name="description">
    Jupiter II · mean radius 1,560.8 km
  </c-fill>
  <c-fill name="default">
    Its fractured water-ice crust may cover a global ocean.
  </c-fill>
</c-CPopover>
```

The title becomes the accessible name. Keep `description` concise; place
structured or lengthy content in the body.

The activator must resolve to exactly one native Button. Do not use an anchor,
generic element, or several controls. Disable that Button itself when opening
is unavailable so native semantics, styling, and Popover behavior agree.

## Add interactive content and actions

The body accepts native controls and nested components. Content stays mounted,
so edits survive closing and reopening. Spread `close_attrs` only onto actions
that should request closure.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cpopover/snippets/interactive_form.py"
  title="Edit an orbit note"
/>

```citry-html
<c-fill name="actions" data="{ close_attrs }">
  <c-CButton variant="ghost" c-attrs="close_attrs">
    Cancel
  </c-CButton>
  <c-CButton c-attrs="close_attrs">
    Keep note
  </c-CButton>
</c-fill>
```

Popover never closes merely because body content was clicked. This keeps links,
inputs, selectors, and nested components predictable.

## Control visibility

Client inputs are passed in the browser through `$c-props="{...}"`. Supply a
Boolean `open` to control visibility. `onOpenChange` reports requests; update
the owner value to accept one or leave it unchanged to decline it.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cpopover/snippets/controlled_open.py"
  title="Control Popover visibility"
/>

```citry-html
<c-CPopover
  $c-props="{
    open,
    onOpenChange: (nextOpen, detail) => {
      if (mayApply(nextOpen, detail)) open = nextOpen;
    },
  }"
>
  ...
</c-CPopover>
```

Without a client `open`, Popover commits user requests itself and then notifies.
Removing the client value or passing `null` releases control without resetting
the current state. Owner commits do not call back.

The callback detail identifies `trigger`, `action`, `escape`, `outside`,
`focus-outside`, unavoidable external `native` changes, and safety closures
caused by an `ancestor` or `modal`. It also includes controlled ownership,
whether the close was forced, and the browser source.

## Choose dismissal behavior

`dismissible=True` allows Escape, outside pointer, and focus-outside requests.
The activator and controls carrying `close_attrs` always remain explicit paths.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cpopover/snippets/dismissal.py"
  title="Choose dismissal behavior"
/>

Use `dismissible=False` when the user must choose an explicit action. Always
provide a clear close path. In controlled mode, declining a passive request
keeps the surface open and prevents that request from closing an ancestor.

## Place the surface

Server inputs are passed in Python through `<c-CPopover ... />` attributes or a
`CPopover(...)` composition call. `placement` accepts `top-start`, `top`,
`top-end`, `bottom-start`, `bottom`, or `bottom-end`. The same client input can
change it in the browser. Use client `matchWidth` or server `match_width` when
the surface should be at least as wide as the Button.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cpopover/snippets/placements.py"
  title="Place a Popover"
/>

Placement is a preference. The browser may flip it near an edge. Start and end
are logical, so they follow text direction. Change the activator gap with
`--cui-popover-offset`; use `--cui-popover-inline-size` or `style` for width.

Popover uses native top-layer rendering and CSS anchors. It does not teleport
under `<body>`, start a JavaScript geometry loop, or publish a generic placement
engine.

## Nest Popovers

Nested Popovers are valid inside a body or action. Escape and outside
interaction affect only the top open layer.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cpopover/snippets/nested_popovers.py"
  title="Nest Popovers"
/>

Closing a child returns focus to its child activator and leaves the parent
open. Prefer shallow layers; a page section is clearer when content no longer
feels compact or locally related.

## Choose the right surface

Popover is a named, non-modal dialog with rich interactive content.

- Use `CDialog` when a task blocks the page or needs contained focus.
- Use the future `CMenu` for command/choice collection semantics and menu
  keyboard behavior.
- Use `CTooltip` for brief noninteractive text shown by hover and
  focus.
- Use `CAlert` for persistent status or feedback.

Adding a role to Popover content does not turn it into those components; each
has different activation, focus, dismissal, and assistive-technology rules.

## Theme and customize Popover

Set public `--cui-popover-*` variables on an ancestor or one surface. Use
public part selectors for targeted regions.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cpopover/snippets/customization.py"
  title="Theme Popovers"
/>

```css
.aurora-popover {
  --cui-popover-background: light-dark(#ecfdf5, #052e2b);
  --cui-popover-foreground: light-dark(#064e3b, #d1fae5);
  --cui-popover-border-color: light-dark(#6ee7b7, #34d399);
  --cui-popover-radius: 1.25rem;
}
```

`class_`, `style`, and `attrs` target the Popover surface. The activator remains
owned by its own component. Unlayered consumer CSS overrides Citry UI defaults;
named layers follow the site-wide layer-order contract.

The documented variables, selectors, and reflected attributes are public CSS
API. `.cui-*` classes, `--_cui-*` variables, host markup, initialization
markers, and anchor names are private.

## Keyboard, focus, and forms

Opening focuses `[autofocus]`, then the first tabbable descendant, then the
surface itself. Popover does not trap Tab: the rest of the page remains
available. Leaving a dismissible surface closes it after focus reaches the new
destination.

Escape closes only the top open layer. Trigger, action, and Escape closure
return focus to the activator when focus was inside. Outside closure preserves
the browser's new focus destination.

Controls inside Popover retain native Form owners, values, reset, validation,
and FormData behavior. Closing does not reset them because content stays in its
original DOM and remains mounted.

## Support narrow viewports and RTL

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cpopover/snippets/responsive_content.py"
  title="Use long RTL content"
/>

Logical dimensions, viewport maxima, wrapping, and body scrolling keep content
reachable at narrow widths and high zoom. The surface follows surrounding
light/dark scope even in the top layer. Forced colors preserve its boundary;
reduced-motion users receive immediate transitions.

Without JavaScript, an initially closed Popover stays hidden. An initially open
Popover renders readable content in document flow, then activation upgrades it
to the top layer.
