---
title: Tag and TagGroup
description: Present descriptive, selectable, actionable, and removable Tag collections.
---

# Tag and TagGroup

Use `CTagGroup` for a labelled collection of compact categories, filters, or
keywords. A descriptive group renders list semantics. Selection, actions, or
removal switch it to one keyboard-operable grid.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctag/snippets/at_a_glance.py" title="TagGroup at a glance" />

```citry-html
<c-CTagGroup label="Topics">
  <c-CTag value="css">CSS</c-CTag>
  <c-CTag value="html">HTML</c-CTag>
</c-CTagGroup>
```

## Select Tags

Choose a selection mode and give every Tag a unique value.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctag/snippets/selection.py" title="Select Tags" />

```citry-html
<c-CTagGroup
  label="Amenities"
  selection_mode="multiple"
  c-value="['wifi']"
  $c-props="{
    value: selectedAmenities,
    onValueChange: (value) => selectedAmenities = value
  }"
>
  <c-CTag value="wifi">Wi-Fi</c-CTag>
  <c-CTag value="parking">Parking</c-CTag>
  <c-CTag value="pool">Pool</c-CTag>
</c-CTagGroup>
```

A supplied client `value` is authoritative. The callback requests the next
selection; it does not mutate a controlled group. Omit the prop to release
control while preserving the last effective selection. `mandatory=True`
prevents user activation from clearing the final selection.

## Actions and removal

`actionable=True` reports enabled Tag activation through `onAction`.
`removable=True` adds one form-safe remove Button and enables Delete and
Backspace. Removal is a request: update your collection to remove the values.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctag/snippets/removal.py" title="Request Tag removal" />

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctag/snippets/actions.py" title="Run Tag actions" />

```citry-html
<c-CTagGroup
  label="Saved filters"
  removable
  $c-props="{
    onRemove: (values) => removeSavedFilters(values)
  }"
>
  <c-CTag value="open">Open</c-CTag>
  <c-CTag value="assigned">Assigned to me</c-CTag>
</c-CTagGroup>
```

When a selected Tag in multiple mode receives Delete, the request includes all
selected removable values. Focus follows retained values across reorder and
moves to the nearest following Tag after removal.

## Content

The default slot is the Tag label. `start` accepts decorative noninteractive
phrasing content such as an Icon or Avatar.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctag/snippets/content.py" title="Compose Tag content" />

```citry-html
<c-CTagGroup label="People">
  <c-CTag value="ava">
    <c-fill name="start"><c-CAvatar alt="Ava" size="sm">A</c-CAvatar></c-fill>
    <c-fill name="default">Ava</c-fill>
  </c-CTag>
</c-CTagGroup>
```

Tag content must not contain links, Buttons, form controls, focusable content,
or nested Tags. Use a native anchor outside TagGroup when the job is
navigation. Free-form entry and editing belong to `CTagsInput`.

## Keyboard behavior

- Arrow keys move through enabled Tags and wrap.
- Home and End move to the first and last enabled Tag.
- Typing moves to the next matching Tag label or `text_value`.
- Enter and Space activate selection and actions.
- Delete and Backspace request removal.
- Tab from a removable Tag reaches its remove Button; Shift+Tab returns.

The group has one page-tab entry. Descriptive groups remain ordinary lists and
do not add keyboard stops.

## Disabledness and forms

Group disabledness, item disabledness, `CForm.disabled`, and native disabled
fieldsets all dominate interaction. TagGroup is not a form control and adds no
FormData. Owned remove Buttons always use `type="button"`.

## Presentation and customization

Variants are `soft`, `solid`, and `outline`. Sizes are `sm`, `md`, and `lg`.
Customize through public variables or stable part selectors:

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctag/snippets/variants.py" title="Compare Tag variants and sizes" />

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctag/snippets/customization.py" title="Customize Tags" />

```css
.brand-tags {
  --cui-tag-selected-background: #176b4d;
  --cui-tag-selected-foreground: #fff;
  --cui-tag-radius: 0.5rem;
}
```

See [`api.yml`](api.yml) for the exhaustive inputs, callbacks, variables,
attributes, selectors, slots, and public interfaces.

<!-- UI_LIBRARY_API_REFERENCE -->
