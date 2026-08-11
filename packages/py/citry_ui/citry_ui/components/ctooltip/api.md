---
title: Tooltip
description: Add accessible, noninteractive descriptions to focusable controls with Citry UI Tooltip.
---

# Tooltip

Use `CTooltip` for brief descriptions that appear on keyboard focus or
fine-pointer hover. It keeps focus on the activator, crosses the pointer gap,
and enters the browser top layer without moving its DOM.

## Tooltip at a glance

Focus or hover each Button. The first hover waits briefly; nearby Tooltips then
open immediately.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctooltip/snippets/at_a_glance.py"
  title="Tooltip at a glance"
/>

## Describe one activator

Provide concise `text` and spread `activator_attrs` onto exactly one enabled,
focusable element.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctooltip/snippets/moon_labels.py"
  title="Describe moon controls"
/>

```citry-html
<c-CTooltip text="Inspect Europa's fractured ice">
  <c-fill name="activator" data="{ activator_attrs }">
    <c-CButton c-attrs="activator_attrs">
      Europa
    </c-CButton>
  </c-fill>
</c-CTooltip>
```

`text` supplements the activator's accessible name. It does not replace one.
An icon-only Button still needs its own accessible name.

The activator may be a Button, link with `href`, form control, or another
element with a real keyboard focus path. Tooltip rejects disabled and
nonfocusable activators; persistent text is clearer for unavailable controls.

## Add simple formatting

Omit `text` and supply the default fill for static, noninteractive formatting.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctooltip/snippets/formatted_description.py"
  title="Format a description"
/>

```citry-html
<c-fill name="default">
  Orbital period: <strong>3.55 Earth days</strong>
</c-fill>
```

Do not put links, Buttons, form controls, editable content, widgets, or nested
Tooltips in the surface. Use `CPopover` for interactive content. Keep essential
instructions and validation feedback persistently visible.

## Update text in the browser

Client inputs are passed through `$c-props="{...}"`. Client `text` safely
updates a Tooltip authored with the server `text` input.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctooltip/snippets/live_text.py"
  title="Update Tooltip text"
/>

Use the default fill for server-authored formatting; client text does not
replace arbitrary slotted markup.

## Tune hover timing

Focus always opens immediately. `delay` affects only the first fine-pointer
hover. `close_delay` keeps a bridge open while the pointer moves from the
activator onto the Tooltip.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctooltip/snippets/timing.py"
  title="Compare hover timing"
/>

Once one Tooltip opens, nearby Tooltips skip the first-hover delay until a
short cooldown ends. No provider or group component is required.

## Control visibility

Supply a client Boolean `open` to control visual visibility. `onOpenChange`
reports requests; update the owner value to accept one or leave it unchanged
to decline it.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctooltip/snippets/controlled_open.py"
  title="Control Tooltip visibility"
/>

```citry-html
<c-CTooltip
  text="Europa has a hidden ocean"
  $c-props="{
    open,
    onOpenChange: (nextOpen) => open = nextOpen,
  }"
>
  ...
</c-CTooltip>
```

Without client `open`, Tooltip commits requests itself and then notifies.
Passing `null` or omitting the client value releases control without resetting
the current state. Owner commits do not notify. Callback detail reports the
interaction reason, controlled ownership, browser source, and whether an
ancestor or modal safety rule forced the Tooltip closed.

## Place the surface

Server inputs are passed through `<c-CTooltip ... />` attributes or a
`CTooltip(...)` composition call. `placement` accepts logical top and bottom
start, center, and end positions. The browser may flip the surface near an
edge.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctooltip/snippets/placements.py"
  title="Place a Tooltip"
/>

Start and end follow text direction. Change the activator gap with
`--cui-tooltip-offset`; change line length with
`--cui-tooltip-max-inline-size`.

## Dismiss and revisit

Escape closes only the top Tooltip and leaves focus on the activator. Pressing
an open activator also dismisses its Tooltip without canceling the native
action. It stays closed until focus and pointer both leave, so it does not
immediately reopen.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctooltip/snippets/dismissal.py"
  title="Dismiss a Tooltip"
/>

Touch activation does not show a visual Tooltip. The interface must remain
understandable without one.

## Theme Tooltip

Set public `--cui-tooltip-*` variables on an ancestor or one surface.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctooltip/snippets/customization.py"
  title="Theme Tooltips"
/>

```css
.aurora-tooltip {
  --cui-tooltip-background: light-dark(#064e3b, #d1fae5);
  --cui-tooltip-foreground: light-dark(#ecfdf5, #052e2b);
  --cui-tooltip-border-color: light-dark(#34d399, #6ee7b7);
  --cui-tooltip-radius: 1rem;
}
```

`class_`, `style`, and `attrs` target the Tooltip surface. The activator stays
owned by its authored component. Unlayered consumer CSS overrides Citry UI
defaults; named layers follow the site-wide layer-order contract.

The documented variables, selector, and reflected attributes are public CSS
API. `.cui-*` classes, `--_cui-*` variables, host markup, initialization
markers, and anchor names are private.

## Support long text, RTL, and zoom

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ctooltip/snippets/responsive_text.py"
  title="Use long RTL descriptions"
/>

Logical placement, a viewport-safe maximum, and aggressive wrapping keep text
reachable at narrow widths and high zoom. The surface follows surrounding
light/dark scope even in the top layer. Forced colors preserve its boundary;
reduced motion removes transitions; print omits visual Tooltips.

Without JavaScript, an initially closed Tooltip remains hidden. An initially
open Tooltip renders readable text in document flow, then activation upgrades
it to the top layer.

## Choose the right surface

- Use `CPopover` for links, controls, forms, or other interactive content.
- Use `CAlert` for persistent status or feedback.
- Use a Field description for instructions tied to a form control.
- Use visible prose when the information is essential to completing a task.
