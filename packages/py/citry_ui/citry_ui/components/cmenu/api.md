---
title: Menu
description: Present commands, links, application choices, and nested command collections from one Button.
---

# Menu

Use `CMenu` for a temporary application-command collection. It supports native
links, grouped commands, check/radio choices, and nested submenus with direct
focus, typeahead, touch-safe activation, and logical placement.

Use `CPopover` for arbitrary controls, forms, or explanatory content. Menu
items accept text and decorative content, not nested interactive controls.

## Menu at a glance

Open the archive menu to see commands, navigation, a submenu, a separator, and
destructive emphasis together.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cmenu/snippets/at_a_glance.py"
  title="Menu at a glance"
/>

## Compose a Menu

Provide exactly one native Button through `activator`. Put Menu-family
declarations directly in the default slot.

```citry-html
<c-CMenu>
  <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
    <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Open archive</c-CButton>
  </c-fill>
  <c-fill name="default">
    <c-CMenuItem value="rename">Rename folio</c-CMenuItem>
    <c-CMenuItem href="/catalog">Open catalog</c-CMenuItem>
    <c-CMenuSeparator />
    <c-CMenuItem value="delete" intent="danger">Delete folio</c-CMenuItem>
  </c-fill>
</c-CMenu>
```

Forward both activator fields. `activator_attrs` carries relationships and the
anchor; `activator_disabled` goes through CButton's `disabled` input. A native
`button` also sets `type="button"` directly.

For Python composition, supply one component whose output contains the direct
declarations. Transparent components may generate declarations when they add
no wrapper or other output.

`CMenuItem`, `CMenuCheckboxItem`, `CMenuRadioGroup`, `CMenuRadioItem`,
`CMenuGroup`, `CMenuSeparator`, and `CMenuSubmenu` are not standalone.

## Run commands and follow links

Give a command `value` when the root `onAction` callback should identify it.
Anonymous commands use native `@click`. Supplying `href` renders a real anchor
and preserves navigation, link context menus, and browser behavior.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cmenu/snippets/commands_and_links.py"
  title="Commands and links"
/>

Links do not call `onAction`. Disabled links temporarily omit `href` and never
navigate.

## Add item content

Use `start`, default, `description`, and `end` for icons, the visible label,
supporting text, and shortcuts. Only the default label names the item; the
description is exposed separately.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cmenu/snippets/item_content.py"
  title="Item content"
/>

Keep every item region to noninteractive phrasing content. Set `text_value`
when the visible label does not produce concise typeahead text.

## Control visibility and configuration

Server inputs are passed in Python through `<c-CMenu ... />` attributes or a
`CMenu(...)` composition call. Client inputs are passed in the browser through
`$c-props="{...}"`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cmenu/snippets/controlled_open.py"
  title="Control Menu visibility"
/>

A Boolean client `open` owns visibility. Omit it or pass `null` to release
control from the current committed state. `onOpenChange` reports requests;
forced ancestor/modal/disabled closes cannot be rejected.

## Add application choices

Checkbox and radio items model application preferences, not native Form
controls. They contribute no `FormData` and emit no native input/change event.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cmenu/snippets/choices.py"
  title="Menu choices"
/>

Checkboxes support `false`, `true`, and `"mixed"`; activating mixed requests
true. A radio group owns one value. Set `close_on_select=False` when readers
should make several choices before leaving the Menu.

## Group commands

`CMenuGroup` owns a visible accessible label. `CMenuSeparator` divides adjacent
command families. Radio groups have their own optional label.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cmenu/snippets/groups_and_separators.py"
  title="Groups and separators"
/>

Do not put separators first, last, or consecutively. Generic groups cannot be
nested inside generic groups.

## Nest submenus

`CMenuSubmenu` is one item plus another Menu surface. Give it a stable `value`,
a `label` fill, and direct declarations in its default fill.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cmenu/snippets/submenus.py"
  title="Nested command menus"
/>

Arrow direction follows text direction. Pointer intent uses the submenu's
actual collision-resolved geometry. Deep nesting works, but one level is
usually easier to scan and operate.

## Keyboard and typeahead

Arrow Down/Up moves direct focus, Home/End reaches the edges, and printable
characters perform buffered prefix matching. Repeating one character cycles
matching labels. `loop` controls wrapping.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cmenu/snippets/keyboard_and_typeahead.py"
  title="Keyboard and typeahead"
/>

Escape closes one submenu or the root. Tab closes the whole tree and continues
normal page order. Disabled items remain discoverable by Menu navigation but
never activate.

## Disable Menu safely

Menu `disabled` and native disabled `fieldset` ancestry are authoritative.
Buttons inside the Menu always use `type=button`, so commands never submit an
enclosing Form.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cmenu/snippets/disabled_and_forms.py"
  title="Disabled Menu and native Forms"
/>

## Place the surface

Choose one of six logical block placements. `match_width` follows the activator
only up to the viewport-safe maximum. Submenus prefer logical inline-end, flip
inline, then use a centered block fallback when neither side is usable.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cmenu/snippets/placement_and_rtl.py"
  title="Placement, width, and RTL"
/>

## Choose a size

`sm`, `md`, and `lg` change the whole family’s item geometry.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cmenu/snippets/sizes.py"
  title="Menu sizes"
/>

## Customize Menu

Override public variables on an ancestor or one wrapper. Stable part selectors
target the surface, item regions, groups, indicators, separators, and submenus.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cmenu/snippets/customization.py"
  title="Theme archive menus"
/>

Every styled family member exposes top-level `class_` and `style` on its
documented root. Unlayered consumer CSS overrides Citry UI defaults; named
layers follow the site-wide layer-order contract.

## Compose with other overlays

Menu, Popover, Tooltip, and Dialog share one logical layer coordinator. Closing
an ancestor closes descendant submenus first. Opening an unrelated modal Dialog
suppresses outside anchored layers and gives the Dialog Escape/focus ownership.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cmenu/snippets/lifecycle.py"
  title="Overlay ownership and cleanup"
/>

## Trust boundary

Text is escaped. Values are plain, nonempty canonical strings; generated IDs
do not expose raw values. `href` remains a trusted application URL boundary.
Attribute maps reject owned semantics, focus, visibility, anchoring, structural
Alpine directives, and Citry runtime namespaces. Use Popover when item content
needs links, Buttons, inputs, editing, or independent Tab stops.
