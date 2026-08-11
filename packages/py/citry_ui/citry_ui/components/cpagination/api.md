---
title: Pagination
description: Navigate finite page sequences with native links or client-owned controls.
---

# Pagination

Use `CPagination` to move through a finite sequence while preserving native URLs or browser-local state.

## Pagination at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpagination/snippets/at_a_glance.py" title="Pagination at a glance" />

## Navigate with links

Put `{page}` in `href`. Server output then works before JavaScript and remains shareable.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpagination/snippets/links.py" title="Navigate with page links" />

## Control the current page in the browser

Omit `href` for Button controls. Client inputs are passed with `$c-props="{...}"`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpagination/snippets/controlled.py" title="Control Pagination in the browser" />

## Compact long ranges

`siblings` keeps pages around the current page. `boundaries` keeps pages at both ends.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpagination/snippets/ranges.py" title="Compact long page ranges" />

## Add edge controls

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpagination/snippets/controls.py" title="Choose Pagination controls" />

## Choose presentation

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpagination/snippets/presentation.py" title="Compare Pagination variants and sizes" />

## Customize Pagination

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cpagination/snippets/customization.py" title="Customize Pagination" />

## Accessibility and behavior

Pagination is a named navigation landmark. Current page uses `aria-current="page"`. Links and Buttons keep native Tab and activation behavior; ellipses are inert.

<!-- UI_LIBRARY_API_REFERENCE -->
