---
title: Card
description: Group related content, media, metadata, and actions in a flexible Citry UI surface.
---

# Card

Use `CCard` to present one subject as a contained visual unit. Its sections are
optional, so a Card can be a short note, a media object, or a complete summary
with header and footer actions.

## Card at a glance

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccard/snippets/at_a_glance.py"
  title="Card at a glance"
/>

The smallest Card needs only content:

```citry-html
<c-CCard>
  A quiet place to read beside the window.
</c-CCard>
```

Compose the same result in Python:

```python
from citry_ui import CCard

reading_note = CCard(slots={"default": "A quiet place to read beside the window."})
```

## Compose the sections you need

Every slot is optional, but a Card must supply at least one. Omitted sections
produce no empty wrapper.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccard/snippets/basic_card.py"
  title="Compose optional Card sections"
/>

Use `header_actions` for controls beside a heading. Use `footer` for metadata
and `actions` for controls at the end. Card supplies the alignment; your slot
content supplies headings, landmarks, links, and accessible names.

## Choose visual emphasis

`elevated` lifts a Card with shadow, `outline` draws a boundary, and `subtle`
adds a quiet system-color tint.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccard/snippets/variants.py"
  title="Compare Card variants"
/>

Variants describe surface emphasis, not meaning. Use semantic HTML for
success, warning, or error feedback instead of assigning semantic color to
Card.

## Choose spacing

`sm`, `md`, and `lg` adjust section padding and action gaps. Typography remains
owned by your content.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccard/snippets/sizes.py"
  title="Compare Card sizes"
/>

## Add media

Media appears first and clips to the Card's top edge, or to every edge when it
is the only section. Card makes direct images, pictures, and videos block-level
and prevents intrinsic overflow. It does not choose an aspect ratio, crop, or
`object-fit`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccard/snippets/media.py"
  title="Add consumer-owned media"
/>

Keep menus and popups outside `media`: clipping is intentional there. Place
escaping interactive content in the header, body, or footer.

## Align metadata and actions

Header and footer action slots keep direct controls together and wrap when
space runs out. The companion content stays in its own flexible column.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccard/snippets/actions.py"
  title="Compose header and footer actions"
/>

Pass `header_actions_attrs` or `actions_attrs` when the control cluster needs
group semantics, an accessible label, data, or a trusted Alpine binding. A
nonempty part mapping fails if its destination slot is absent.

## Put interactive content inside Card

Card has no client state and does not intercept nested controls. Its root,
header, body, and footer stay unclipped and create no stacking context.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccard/snippets/nested_content.py"
  title="Use interactive content inside Card"
/>

Card itself is not one large action. Use real links and Buttons inside it. A
whole-Card link needs its own focus, layering, and nested-control contract and
is not supported by `CCard`.

## Customize layout and theme

Override public variables on an ancestor or one Card. Stable part selectors
support responsive layouts without turning orientation into a server input.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccard/snippets/customization.py"
  title="Customize Card with public CSS"
/>

The example shows two independent brand treatments and a horizontal layout
that returns to vertical at narrow width. `.cui-*` classes and `--_cui-*`
variables are private.

## Choose root semantics

The default `div` makes no document-structure claim. Choose `article` for an
independently reusable composition, `section` for a named document section, or
`li` inside a list.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/ccard/snippets/semantics.py"
  title="Choose native Card semantics"
/>

`CCard` adds no role, focus stop, keyboard behavior, or accessible name. The
selected native root and your content own those semantics.

## Accessibility, trust, and server rendering

Card renders completely without JavaScript. Slot text uses ordinary Citry
escaping. Attribute maps accept native, ARIA, data, and trusted Alpine
attributes, but reserve Card's reflected fields, part markers, and Citry's
runtime ownership namespace.

Card follows nested `color-scheme`, keeps a visible forced-colors boundary,
removes decorative shadow in print, and uses logical layout for right-to-left
content.
