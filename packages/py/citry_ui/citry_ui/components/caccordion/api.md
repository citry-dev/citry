---
title: Accordion
description: Organize related sections with native headings, controlled expansion, stable panel content, and nested groups.
---

# Accordion

Use `CAccordion` for a finite group of related sections. Each
`CAccordionItem` renders a native heading and button. Panel content stays in
the document when closed, preserving forms, browser-owned values, and nested
component state.

## Accordion at a glance

Open the field-guide sections to see the complete item pattern in a compact
group.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/caccordion/snippets/at_a_glance.py"
  title="Accordion at a glance"
/>

## Compose Accordion items

Give every item a stable `value`, a `title` fill, and a default panel fill.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/caccordion/snippets/basic_accordion.py"
  title="Compose an Accordion"
/>

```citry-html
<c-CAccordion value="canopy">
  <c-CAccordionItem value="canopy">
    <c-fill name="title">
      Forest canopy
    </c-fill>
    <c-fill name="default">
      The canopy captures most incoming sunlight.
    </c-fill>
  </c-CAccordionItem>
  <c-CAccordionItem value="understory">
    <c-fill name="title">
      Understory
    </c-fill>
    <c-fill name="default">
      Shade-tolerant plants grow beneath the canopy.
    </c-fill>
  </c-CAccordionItem>
</c-CAccordion>
```

For Python composition, supply one component whose output contains the direct
items. This preserves item registration without introducing a DOM wrapper.

```python
from citry import Component
from citry_ui import CAccordion


class FieldGuideItems(Component):
    template = """
      <c-CAccordionItem value="canopy">
        <c-fill name="title">Forest canopy</c-fill>
        <c-fill name="default">Upper forest layer</c-fill>
      </c-CAccordionItem>
    """


field_guide = CAccordion(
    value="canopy",
    slots={"default": FieldGuideItems()},
)
```

`CAccordionItem` is not standalone. Put it directly inside the nearest
Accordion. Transparent components may generate items when they add no wrapper
or other output.

## Control expansion in the browser

Server inputs are passed in Python through `<c-CAccordion ... />` attributes
or a `CAccordion(...)` composition call. Client inputs are passed in the
browser through `$c-props="{...}"`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/caccordion/snippets/controlled_value.py"
  title="Control Accordion value"
/>

Single mode uses `string | null`; multiple mode uses `string[] | null`.
`onValueChange` receives requests before an uncontrolled commit. When `value`
is supplied, update it in the callback to accept the request. Omit the client
value to release control without resetting the current valid browser state.

## Choose an expansion policy

The default single mode keeps at most one panel open. Set `multiple=True` to
open several. Set `collapsible=False` in single mode when an open item should
stay open.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/caccordion/snippets/expansion_modes.py"
  title="Compare expansion modes"
/>

`collapsible=False` does not force an initial selection. After a section opens,
its trigger remains focusable and exposes `aria-disabled="true"` while it is
the item that cannot close.

## Add adjacent actions

Put related Buttons, links, or menus in the `actions` slot. They render beside
the heading, never inside its trigger. `actions_label` creates one named
`group` for the controls.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/caccordion/snippets/actions.py"
  title="Add item actions"
/>

Title content is inside a native button. Keep it to noninteractive phrasing
content. Links, form controls, nested headings, and another Accordion belong in
the panel or actions slot.

## Disable groups or items

Group `disabled` blocks every trigger. Item `disabled` blocks only that item.
An open disabled item stays open.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/caccordion/snippets/disabled_items.py"
  title="Disable Accordion items"
/>

An enclosing disabled native `fieldset`, including CForm's fieldset, remains
authoritative. Client `disabled=False` cannot re-enable its descendant
buttons.

## Nest Accordion

Put a nested `CAccordion` in a panel. Do not place it in a title or action
area. The nested root becomes a new registration and keyboard boundary.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/caccordion/snippets/nested_accordion.py"
  title="Nest Accordion groups"
/>

## Choose variant and size

`outline`, `soft`, `separated`, and `plain` cover connected and independent
surfaces. `sm`, `md`, and `lg` change trigger, action, indicator, and panel
geometry.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/caccordion/snippets/variants.py"
  title="Compare variants and sizes"
/>

## Customize Accordion

Override public variables on an ancestor or one root. Stable part selectors
target item anatomy. Browser inputs can change `variant`, `size`, `indicator`,
and `indicatorPosition` without a server render.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/caccordion/snippets/customization.py"
  title="Theme a field guide"
/>

`class_`, `style`, and `attrs` target the Accordion root. An item has its own
`class_`, `style`, and `attrs`, plus exact maps for its native heading,
trigger, panel, and optional actions wrapper. Unlayered consumer CSS overrides
Citry UI defaults; named layers follow the site-wide layer-order contract.

## Keyboard and accessibility

Every enabled trigger remains in normal Tab order. Enter and Space use native
button activation. Arrow Up, Arrow Down, Home, and End move focus among enabled
triggers without opening them; `loop` controls wrapping.

Choose `heading_level` to fit the page outline. Panels are neutral by default.
Set `region=True` only when the panels benefit from landmarks; this adds
`role="region"` and trigger-based naming as one pair.

Closing a panel that contains focus moves focus to its trigger before the panel
becomes inert. A structural update that removes the focused item moves focus to
the nearest enabled surviving trigger. If none survives, the update owner must
choose an external destination.

## Forms, animation, and content lifetime

Closed panel content remains mounted. Uncontrolled edits, successful controls,
and nested component state survive close and reopen. Closed controls still
belong to `FormData` and native constraint validation. A hidden required
control can therefore block submission; applications must open the relevant
panel before moving focus to it.

Rapid expansion requests replace the active animation instead of being
ignored. Reduced-motion users receive an immediate commit. Settled panels do
not clip overlays; a panel clips its contents only during the bounded height
transition. Print shows every panel.

## Trust boundaries

Item values and generated IDs are plain text. Raw values appear only in the
public `data-value`; generated trigger/panel IDs use a stable hash. Title and
panel content use ordinary Citry escaping. The chevron comes from the packaged
icon allowlist.

Attribute maps are trusted authoring surfaces for unowned values. Accordion
rejects attributes and Alpine directives that could replace native semantics,
children, expansion visibility, focus ownership, a second popover/command
activation owner, public mirrors, or Citry runtime markers.
