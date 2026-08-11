---
title: Breadcrumbs
description: Show hierarchical page location with semantic Citry UI Breadcrumbs.
---

# Breadcrumbs

Use `CBreadcrumbs` to show the current page within a hierarchy and link back to
its ancestors.

## Breadcrumbs at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbreadcrumbs/snippets/at_a_glance.py" title="Breadcrumbs at a glance" />

## Build a trail from records

The final item is current. Give earlier items an `href`; leave the final href
empty for plain current-page text.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbreadcrumbs/snippets/basic.py" title="Build a Breadcrumb trail" />

```py
items = (
    CBreadcrumbItem("Home", "/"),
    CBreadcrumbItem("Library", "/library"),
    CBreadcrumbItem("The green room"),
)
```

## Keep the current page linked

A final item may retain its href. Citry adds `aria-current="page"`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbreadcrumbs/snippets/current_link.py" title="Link the current page" />

## Choose a separator

Use concise text directly or replace each separator through the scoped slot.
Separators stay hidden from assistive technology.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbreadcrumbs/snippets/separators.py" title="Choose Breadcrumb separators" />

## Choose size

Use `sm`, `md`, or `lg` to match the surrounding navigation density.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbreadcrumbs/snippets/sizes.py" title="Compare Breadcrumb sizes" />

## Wrap or scroll long trails

Wrapping is the default. Set `wrap=False` for one horizontal scroll row.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbreadcrumbs/snippets/overflow.py" title="Handle long Breadcrumb trails" />

## Customize item rendering

The `item` slot receives the record, index, current flag, and owned native attrs.
Bind `attrs` to preserve link and current-page semantics.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbreadcrumbs/snippets/item_slot.py" title="Customize Breadcrumb items" />

## Compose route-derived records

Route integration stays outside the component. Turn your router hierarchy into
`CBreadcrumbItem` records and pass the resulting tuple.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbreadcrumbs/snippets/route_records.py" title="Compose route-derived Breadcrumbs" />

## Customize Breadcrumbs

Override public link, current, separator, focus, and spacing variables or stable
parts.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cbreadcrumbs/snippets/customization.py" title="Customize Breadcrumbs with public CSS" />
