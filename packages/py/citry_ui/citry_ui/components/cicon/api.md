---
title: Icon
description: Render a consistent, accessible set of local SVG symbols with Citry UI Icon.
---

# Icon

Use `CIcon` for a bundled symbol that follows the surrounding text color and
size. It renders inline SVG from Citry UI itself, so it needs no font, network
request, client runtime, or JavaScript icon package.

## Icon at a glance

Icons are decorative by default. Put them beside visible text and let that
text carry the meaning.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cicon/snippets/at_a_glance.py"
  title="Icon at a glance"
/>

```citry-html
<p>
  <c-CIcon name="leaf" />
  Silver fern
</p>
```

Compose the same Icon in Python:

```python
from citry_ui import CIcon

leaf = CIcon(name="leaf")
```

## Browse the catalog

The initial catalog favors common actions, navigation, status, and objects.
Semantic aliases such as `success`, `warn`, and `close` keep application code
about meaning rather than one particular drawing.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cicon/snippets/catalog.py"
  title="Browse bundled Icons"
/>

Names are a versioned public contract. Unknown names fail during server render
instead of leaving a blank placeholder.

## Match size and color

`sm`, `md`, and `lg` scale with nearby type. Icons inherit `currentColor`, so
ordinary text color utilities and component intent colors work without an
Icon-specific color input.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cicon/snippets/size_and_color.py"
  title="Set Icon size and color"
/>

Set `--cui-icon-size` for an exact local size. Use `class_` and `style` directly
for routine root styling.

## Give standalone Icons meaning

Pass `label` only when the Icon must communicate without nearby text. It adds
`role="img"` and `aria-label`. Without `label`, the Icon has
`aria-hidden="true"`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cicon/snippets/meaning.py"
  title="Choose decorative or meaningful semantics"
/>

Do not repeat visible text in `label`. An Icon never enters the focus order and
does not own a click action.

## Compose Icons with controls

Put Icons inside the decoration slots of the component that owns the action.
The Button keeps the accessible name, focus, keyboard behavior, loading state,
and target size.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cicon/snippets/composition.py"
  title="Compose Icons with Buttons"
/>

For an icon-only action, name the Button through its `attrs`. Do not attach an
event listener or `tabindex` to `CIcon`.

## Use physical and logical direction

Physical names such as `arrow-left` always point the same way. Logical names
`back`, `forward`, `prev`, and `next` mirror automatically in right-to-left
content.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cicon/snippets/direction.py"
  title="Compare physical and logical direction"
/>

Choose a logical name for reading or navigation order. Choose a physical name
when the direction itself is the content, such as a compass or diagram.

## Theme and customize Icon

Icon follows the surrounding `color-scheme`. Override the two documented CSS
variables on an ancestor or one Icon; use the public part selector for targeted
root styling.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cicon/snippets/customization.py"
  title="Customize Icon"
/>

```css
.field-key {
  --cui-icon-size: 1.4rem;
  --cui-icon-stroke-width: 1.6;
}

.field-key [data-citry-ui-part="icon"] {
  color: #15803d;
}
```

The documented variables, part, and reflected attributes are public CSS API.
`.cui-*` classes and `--_cui-*` variables are private.

## Accessibility and security

Decorative and meaningful semantics are decided on the server and work without
JavaScript. The SVG is non-interactive, ignores pointer events, and contains
only reviewed package-owned geometry.

`attrs` accepts inert metadata but rejects executable Alpine and Citry
directives, event attributes, geometry, focus controls, and accessible-name
overrides. Citry runtime data namespaces are reserved. Trusted
`Markup`/`__html__` values are rejected across every input, including nested
class, style, and attribute structures. `CIcon` is not a raw SVG escape hatch.
