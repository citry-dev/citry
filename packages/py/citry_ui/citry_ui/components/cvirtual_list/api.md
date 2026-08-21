---
title: Virtual List
description: Defer off-screen rendering or supply a true server-rendered collection window with Citry UI.
---

# Virtual List

Use `CVirtualList` when you can server-render the complete collection and want
the browser to skip off-screen layout and paint. Use `CVirtualWindow` when DOM
size is the bottleneck and your application can supply each requested
fixed-size server range. Both use `CVirtualListItem` for stable identity and
arbitrary server-rendered content.

## Keep complete server HTML

`CVirtualList` preserves every Item in the DOM and accessibility tree. It uses
`content-visibility: auto` plus an intrinsic-size estimate, so it reduces
rendering cost without reducing HTML transfer, DOM nodes, memory, Alpine roots,
or Citry initialization.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cvirtual_list/snippets/at_a_glance.py" title="Keep a complete virtualized list" />

Choose an `estimated_item_size` close to the average rendered block size. It
is a browser layout hint, not a fixed height; rich Items may still wrap and
grow. Stable `item_key` values preserve logical identity across server renders.

## Supply a true DOM window

`CVirtualWindow` renders only the contiguous range supplied by the current
server output. `total_count`, `start_index`, and `item_size` reserve the full
scroll extent. The direct `CVirtualListItem` declarations are the committed
range beginning at `start_index`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cvirtual_list/snippets/windowed.py" title="Supply a fixed server window" />

Pass `onRangeChange` through `$c-props`. The callback receives the desired
overscanned half-open range, visible range, request ID, reason, and source
event. It requests state; it never mutates or renders Item HTML. Fetch or
render the new range, cancel superseded work in the application, and replace
the component with the new `start_index` and Items.

The runtime marks the root `aria-busy="true"` and `data-pending` until the
committed server range covers the current desired range. A missing callback
leaves the current range usable. Callback failures are isolated and logged.

## Keep window rows fixed

Every `CVirtualWindow` Item must occupy exactly `item_size` CSS pixels in the
block axis. The component clips overflow to keep spacer geometry correct.
Use bounded internal layout, truncation, or a larger row size; do not use a
window for variable-height articles. The total scroll extent is limited to
16,000,000 CSS pixels because browser element-size limits are not portable.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cvirtual_list/snippets/controlled.py" title="Tune range geometry" />

`overscan` and `itemSize` are reactive client inputs. A valid Alpine change
recomputes the requested range immediately. Invalid values log one diagnostic
per episode and retain the previous valid value. Use a server render when the
committed range or total count changes.

## Accessibility and focus

Both owners render `role="list"` and `CVirtualListItem` renders
`role="listitem"`. A Window Item also receives exact `aria-posinset` and
`aria-setsize`; spacers are hidden from assistive technology. `focusable=True`
adds one viewport tab stop so keyboard users can scroll even when Items contain
no controls.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cvirtual_list/snippets/accessibility.py" title="Compare complete and windowed semantics" />

Use `CVirtualList` or ordinary pagination when assistive-technology users must
browse the entire collection without application range requests. Windowing
necessarily exposes only the supplied Items. Avoid windowing a long editable
form. If a focused Item or the logical owner of an open overlay leaves the
supplied range, ordinary Citry morph and owner-removal cleanup applies.

## Server rendering and JavaScript

`CVirtualList` is CSS-only and remains fully useful without JavaScript.
`CVirtualWindow` displays the supplied range at its correct offset without
JavaScript but needs JavaScript to request another range. The runtime never
clones, reparents, caches, or writes Item HTML and adds no generic client
renderer.

Server morphs are authoritative. Stable Item keys preserve the Item/component
relationship, and a retained root hands off its scroll offset across runtime
replacement. The application still owns stale-request cancellation, loading,
errors, retry, caching, and total-count changes.

## Customize the viewport and Items

Use root `class_`, `style`, and `attrs`, Item equivalents, public variables,
and documented part selectors. Window Item block size is owned geometry.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cvirtual_list/snippets/customization.py" title="Customize Virtual List" />

For print, `CVirtualList` expands and makes all Items visible. A
`CVirtualWindow` can print only its supplied range; render a separate complete
or paginated print view when the full collection matters.

## Localization

The family owns no visible or accessibility text, announcements, parsing,
formatting, filtering, sorting, or comparison. Localize `aria_label` and Item
content in the application. The family therefore has no Citry UI catalog keys.

<!-- UI_LIBRARY_API_REFERENCE -->
