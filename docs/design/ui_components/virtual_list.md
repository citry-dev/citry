# Virtual List

**Status (2026-08-22):** production implementation, public docs, structured
reference, examples, quality scenario, and focused browser
coverage shipped in `citry-ui` 0.2.0. The family deliberately separates
browser render containment from true DOM windowing so server-rendered content
never acquires a hidden client renderer.

## 1. Purpose and product bar

`CVirtualList` and `CVirtualWindow` present long, ordered, non-selectable lists
while reducing off-screen rendering work. `CVirtualListItem` declares one
stable item for either owner. The family exposes the two jobs as separate
components so complete server HTML does not load a windowing runtime:

- `CVirtualList` keeps every server-rendered item in the DOM and uses
  browser containment to skip off-screen layout and paint; and
- `CVirtualWindow` renders only the contiguous range supplied by the application,
  reserves the missing space, and reports the next required range.

The shortest complete-DOM job is:

```html
<c-CVirtualList aria_label="Activity">
  <c-CVirtualListItem item_key="event-1">Created</c-CVirtualListItem>
  <c-CVirtualListItem item_key="event-2">Reviewed</c-CVirtualListItem>
</c-CVirtualList>
```

The shortest true-window job is:

```html
<c-CVirtualWindow
  c-total_count="10000"
  c-start_index="240"
  c-item_size="48"
  $c-props="{ onRangeChange: loadRange }"
>
  <c-for each="row in rows">
    <c-CVirtualListItem c-item_key="row.id">{{ row.label }}</c-CVirtualListItem>
  </c-for>
</c-CVirtualWindow>
```

The application loads, cancels, caches, and server-renders requested ranges.
Citry UI owns geometry, spacers, stable position metadata, keyboard scrolling,
pending reflection, and callback coalescing. It does not own selection,
listbox/grid keyboard behavior, infinite-loading transport, arbitrary client
templates, or pagination. There is no headless API.

## 2. Prior art and complaints

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Vuetify `VVirtualScroll` | current and v2 docs reviewed 2026-08-21 | dynamic vertical height, item reuse, bench/overscan, item data renderer | Keep vertical list geometry and overscan; reject framework-specific client item rehydration. |
| React Aria `Virtualizer` | current docs reviewed 2026-08-21 | visible DOM reuse, fixed and estimated variable layouts, collection render functions, orientation | Require stable keys and explicit size estimates; do not claim arbitrary layouts or client render functions. |
| TanStack Virtual | current docs reviewed 2026-08-21 | count, stable item keys, estimates, measurement, overscan, scrolling, SSR initial rect/offset, prepend anchoring | Adopt explicit count, estimate, overscan, stable identity, range callbacks, and deterministic initial output. |
| Blazor `Virtualize<TItem>` | ASP.NET Core 10 docs reviewed 2026-08-21 | fixed items or server `ItemsProvider`, spacer intersection, overscan, initial index, scroll API, focusable viewport | Use fixed-size rows for the first server-window contract and make the provider boundary application-owned. |
| Angular CDK virtual scroll | current available official docs reviewed 2026-08-21 | fixed-size strategy, buffers, track-by, view recycling, data source, orientation | Keep fixed-size geometry and stable keys; reject cached view recycling because Citry component ownership cannot be cloned or silently detached. |
| Vaadin Flow Grid | current docs reviewed 2026-08-21 | server data provider, lazy scrolling, client/server protocol, equal-height lazy columns | Confirm that automatic server virtualization requires a dedicated client/server data protocol, which this generic family does not invent. |
| CSS `content-visibility` | MDN and CSS containment guidance reviewed 2026-08-21 | `auto`, accessibility-tree retention, intrinsic size estimates, find/focus behavior | Use as the complete-DOM strategy and document that it reduces rendering, not transfer or DOM size. |
| WAI-ARIA feed pattern | current APG reviewed 2026-08-21 | `aria-posinset`, `aria-setsize`, `aria-busy`, loaded-range semantics | Apply position/set metadata to windowed list items and clear busy state after a supplied range commits. |

True windowing always needs either a browser-side item renderer or a server
range provider. React, Vue, and Angular libraries rerun client templates;
Blazor and Vaadin own a framework transport. Citry UI has neither a generic
client renderer nor a mandatory server connection. It therefore exposes the
range request without cloning HTML, evaluating trusted strings, or pretending
a browser callback is a Python data provider.

Vuetify remains the primary styled-suite reference:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `items` and item slot | application server rendering | `CVirtualListItem` declarations | Preserve arbitrary server content without serializing it. |
| `item-height` | direct API | `item_size` in window mode; `estimated_item_size` otherwise | Adopt with strategy-specific meaning. |
| `height`, `max-height` | CSS/direct API | `viewport_size`, public variable, root `style` | Provide a predictable default and ordinary CSS escape hatch. |
| `bench` | direct API | `overscan` | Adopt as item count. |
| dynamic heights | separate future strategy | none in `window` v1 | Complete-DOM content may vary; true windowing requires fixed size. |
| item rehydration/reuse | omitted | none | Citry never clones or rebinds arbitrary server components. |
| horizontal virtual scrolling | deferred | none | Vertical-only v1 keeps direction and scroll-offset rules bounded. |

## 3. Public composition and anatomy

```text
CVirtualList or CVirtualWindow → div[role=list].cui-virtual-list
└─ div.cui-virtual-list__track
   ├─ div.cui-virtual-list__spacer[aria-hidden]   (window only)
   ├─ div[role=listitem].cui-virtual-list__item × supplied range
   └─ div.cui-virtual-list__spacer[aria-hidden]   (window only)
```

`CVirtualListItem` is declaration-only and belongs directly to one
`CVirtualList` or `CVirtualWindow`. Formatting whitespace and transparent declaration helpers are
allowed; other sibling output is rejected. The root receives `attrs`,
`class_`, and `style`. Item equivalents land on the rendered list item.
Owned roles, position metadata, part markers, geometry styles, and runtime
attributes cannot be replaced.

The internal declaration collector and render components remain private. The
anatomy review split the original strategy input into two owners: this is what
keeps `$c-props` attached to the authored `CVirtualWindow` while preserving a
CSS-only `CVirtualList`. The public item component remains because it owns
stable key, item attributes, position metadata, and arbitrary server content.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `CVirtualList.aria_label` | `str | None` | `None` | structural | Names the complete-DOM list. |
| `CVirtualList.estimated_item_size` | positive `int` pixels | `48` | initial geometry | Supplies the intrinsic containment estimate. |
| `CVirtualList.viewport_size` | positive `int` pixels | `400` | initial geometry | Sets the initial block size; root style may override the public variable. |
| `CVirtualList.focusable` | `bool` | `True` | structural | Adds `tabindex=0` for keyboard scrolling. `False` requires a keyboard-reachable control inside an Item. |
| `CVirtualWindow.total_count` | nonnegative `int` | required | controlled collection state | Exact logical list size. |
| `CVirtualWindow.start_index` | nonnegative `int` | `0` | controlled collection state | Index of the first supplied item. |
| `CVirtualWindow.item_size` | positive `int` pixels | `48` | reactive geometry | Fixed item stride; total extent may not exceed 16,000,000 CSS pixels. |
| `CVirtualWindow.viewport_size` | positive `int` pixels | `400` | initial geometry | Sets the initial block size. |
| `CVirtualWindow.overscan` | `int` from `0` through `100` | `3` | reactive configuration | Adds requested items before and after the visible range. |
| `CVirtualWindow.initial_index` | nonnegative `int` | `0` | initial value | One-shot initial scroll target, clamped to the collection. |
| `CVirtualWindow.aria_label` | `str | None` | `None` | structural | Names the windowed list. |
| `CVirtualWindow.focusable` | `bool` | `True` | structural | Adds `tabindex=0` for keyboard scrolling. `False` requires a keyboard-reachable control inside an Item. |
| both owners: `class_`, `style`, `attrs` | structured values | `None` | structural | Extend the root without replacing owned behavior. |
| `CVirtualListItem.item_key` | nonempty `str` | required | identity | Unique stable identity within the logical collection. |
| `CVirtualListItem.class_`, `style`, `attrs` | structured values | `None` | structural | Extend the rendered list item. |

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `overscan` | integer `0..100` | server value | invalid, retain last valid | one diagnostic, retain last valid | requested range |
| `itemSize` | positive finite number | server value | invalid, retain last valid | one diagnostic, retain last valid | range geometry |
| `onRangeChange` | function | no callback | clears callback | one diagnostic, retain last valid callback | range requests |

Python supplies the committed `CVirtualWindow`. Client inputs tune requests but do not
alter `start_index`, `total_count`, or item content. A server morph is
authoritative and resets invalid-client diagnostics while preserving the
browser's scroll position when Citry preserves the keyed root.

## 5. State model

`CVirtualList` has `idle` only. `CVirtualWindow` has `settled` and `pending`.
Initialization, resize, scroll, overscan change, or item-size change computes a
desired range. If the committed window covers it, state stays settled. If not,
the component marks itself pending, sets `aria-busy=true`, and calls
`onRangeChange` once for the newest distinct desired range. A later server
render whose range covers the current desired range clears pending and
`aria-busy`.

Callbacks do not commit state and cannot be cancelled by the component.
Each detail includes a monotonically increasing `requestId`; applications use
it or their own abort controller to ignore stale work. Missing callbacks leave
the supplied range usable and log no error.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---:|---:|---|---|
| `CVirtualList` or `CVirtualWindow` | `default` | no | zero or one | `{}` | declarations only |
| `CVirtualListItem` | `default` | yes | one | `index`, `item_key`, `set_size`, `strategy` | none |

Slot data is settled server data. In complete-DOM mode `index` follows
declaration order. In window mode it is `start_index + declaration offset`.
There is no browser render callback, dynamic slot namespace, placeholder HTML,
or item template serialization.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onRangeChange` | one `CVirtualListRangeChangeDetail` | desired range is not covered by committed window | animation-frame-coalesced after geometry settles | request only; application supplies a new server range | no return-value cancellation; use `requestId` externally |

The detail contains `startIndex`, exclusive `endIndex`, `visibleStartIndex`,
exclusive `visibleEndIndex`, `requestId`, `reason`, and `sourceEvent`. Native
`scroll` remains available through root attrs only where the safe attrs policy
allows it. There are no public methods in v1; applications can control the
initial index or keep a root reference and use native `scrollTo`.

## 8. Semantics, keyboard, focus, and assistive technology

The root has `role=list`; items have `role=listitem`. In `CVirtualWindow` each item
has one-based `aria-posinset` and exact `aria-setsize`. Spacers have
`aria-hidden=true`, `role=presentation`, and cannot receive focus. The optional
label becomes `aria-label`.

The focusable root receives ordinary browser arrow, Page Up/Down, Home/End,
wheel, and touch scrolling. The component adds no roving focus or selection.
Interactive descendants keep native Tab order. A focused descendant pins the
desired range around its item; if the application nonetheless replaces that
item, normal Citry morph focus rules apply and the list does not synthesize a
different target.

When `focusable=False`, the supplied Items must contain a keyboard-reachable
control. That control gives keyboard users a way to enter the scrollable
region. A viewport with no root tab stop and no focusable descendant is not
keyboard accessible.

`CVirtualList` preserves every item in the DOM and accessibility tree.
`CVirtualWindow` exposes only the supplied range plus exact set position metadata;
it is unsuitable when assistive-technology users must browse every item
without requesting ranges. Documentation must show pagination or
complete-DOM mode as the accessible fallback for that product requirement.

## 9. Native forms and validation

The family is not a form control and submits no value. Authored controls
inside items keep their own form owner and validation. `CVirtualWindow` is a poor
fit for large editable forms because off-window controls are absent; the guide
warns against that composition.

## 10. Styling and theme contract

Public variables are `--cui-virtual-list-viewport-size`,
`--cui-virtual-list-item-size`, `--cui-virtual-list-gap`,
`--cui-virtual-list-padding`, `--cui-virtual-list-border`,
`--cui-virtual-list-radius`, `--cui-virtual-list-background`, and
`--cui-virtual-list-item-background`.

Public selectors are parts `virtual-list`, `track`, `item`, and `spacer`.
Root reflections are `data-strategy`, `data-pending`, `data-start-index`, and
`data-total-count`. Item reflections are `data-index` and `data-item-key`.

`CVirtualWindow` item block size is owned fixed geometry and cannot be replaced by
item style. `CVirtualList` items may grow naturally; their intrinsic estimate is
only a browser containment hint.

## 11. Environmental behavior

V1 is vertical and uses logical block properties, so RTL does not alter index
or scroll calculations. Reduced motion disables smooth-scroll examples;
runtime scrolling is always instant. Forced colors retains the viewport
border. At narrow widths content wraps in complete-DOM mode; window mode
requires callers to keep every row at the declared fixed block size, normally
through truncation or bounded internal layout. Print removes the viewport
height and overflow in complete-DOM mode. Window mode prints only the supplied
range and the guide recommends a separate non-windowed print rendering.

All visible content is application-authored. The family performs no parsing,
formatting, matching, sorting, case conversion, or announcements and owns no
catalog messages. Content keeps its locale and bidi ownership.

## 12. Overlay and layering behavior

The family creates no overlay. An overlay trigger inside a complete-DOM item
works normally. In window mode the application must keep an item supplied
while its logically owned overlay is open; otherwise the overlay family's
normal owner-removal cleanup applies.

## 13. Collections, async data, and identity

Every item has a nonempty stable key, and duplicate keys are rejected.
`CVirtualList` indexes are declaration order. `CVirtualWindow` declarations are a
contiguous range beginning at `start_index`; their count cannot exceed
`total_count - start_index`. Reorder is a server render and keys preserve
logical identity only when the owner keeps them stable.

The family does not fetch data. Applications own loading, cancellation,
supersession, retry, offline behavior, caching, total-count changes, and empty
or error presentation. Empty collections render an empty named list. A
windowed callback's request ID is evidence for newest-request-wins logic, not
a substitute for application cancellation.

## 14. Server render, morph, and cleanup

`CVirtualList` output is fully useful without JavaScript. `CVirtualWindow` output shows
the supplied range at the correct offset without JavaScript, but cannot request
another range. Initialization installs one passive scroll listener, one
`ResizeObserver`, one Alpine effect, and one animation-frame scheduler on the
root. Cleanup removes/releases all of them.

The runtime never removes, clones, caches, reparents, or writes item HTML.
Fragment insertion initializes from rendered geometry. Morph replacement
recomputes committed coverage and preserves scroll offset where the browser and
Citry keyed morph do so. Multiple and nested roots are isolated.

## 15. Security and content trust

Slots use ordinary Citry escaping and trust rules. Item keys and ARIA labels
reject U+0000 and whitespace-only values. Numeric geometry is finite and
bounded before it reaches CSS or JavaScript. General attrs reject owned roles,
geometry, visibility/child-replacement directives, and Citry runtime markers.
No `innerHTML`, client template evaluation, selector input, remote URL, or
serialized trusted markup exists.

## 16. Assets and performance

`CVirtualList` contributes CSS only. It reduces off-screen layout and paint
but not HTML transfer, DOM nodes, memory, Alpine roots, or Citry initialization.
`CVirtualWindow` contributes one family-local JavaScript asset with one listener,
one observer, and animation-frame-coalesced work per root. Runtime work is
constant in `total_count` and linear only in the supplied window.

The full-catalog frozen asset ceiling already has little remaining headroom.
This family must pass focused asset evidence and the integrated batch must
reduce or split catalog payload rather than silently raising the ceiling.

## 17. Acceptance matrix

Automated evidence covers schema and typing, declaration placement, key
uniqueness, complete-DOM anatomy, containment CSS, window spacers, exact
position metadata, empty and final partial ranges, invalid geometry, safe
attrs, client validation, range calculation, overscan, resize, scroll
coalescing, pending settlement, callback request IDs, focus pinning, cleanup,
fragment/morph initialization, nested roots, axe, three browsers, exports,
docs projection, snippets, quality routing, and asset/wheel inclusion.

Manual qualification covers VoiceOver/Safari and NVDA/Firefox range position,
keyboard scrolling, 400% zoom, long fixed-row content, forced colors, touch,
large totals, slow-server blank-space behavior, and visual review.

## 18. Compatibility classification

Component names, inputs, slots, callback shape, public variables/selectors,
reflected attributes, validation, and the two-owner split are stable API.
List/listitem semantics, complete-DOM retention, fixed-size window geometry,
request-only ownership, and the no-cloning rule are behavioral contracts.
Exact colors, spacing, borders, and private class names may evolve.

## 19. Public documentation contract

The guide begins with choosing `CVirtualList` or `CVirtualWindow`, then complete-DOM use, controlled
server windowing, callback cancellation, accessibility tradeoffs, fixed-height
rules, morph/focus behavior, styling, performance, and printing. `api.yml`
exhaustively documents both components and ends with an empty structured
Translation keys table.

Planned examples are:

| Module | Reader task | Visible evidence | Focused browser evidence |
|---|---|---|---|
| `at_a_glance.py` | render a long complete list | containment, stable rich server content | find, focus, axe |
| `windowed.py` | supply and replace a fixed server range | spacers, indexes, callback detail | scroll and range settlement |
| `controlled.py` | tune overscan and item size through `$c-props` | live request geometry | validation and newest request |
| `accessibility.py` | compare complete and windowed semantics | set position and fallback guidance | accessibility snapshot |
| `customization.py` | customize viewport and items | public variables/selectors | computed styles |

Static documentation cannot perform the application's server replacement.
Its window examples therefore use a small self-contained range with no omitted
leading or trailing Items. They must not expose scrollable blank space that the
static page cannot replace. Browser evidence for partial ranges separately
keeps both spacer directions and verifies the request/pending protocol.

## 20. Open decisions and deferred work

Variable-height true windowing, horizontal/RTL geometry, programmatic public
methods, prepend anchoring, infinite-loader transport, asynchronous placeholder
ownership, dynamic client render functions, selection, drag/reorder, grids,
trees, tables, and editable collections are deferred. DataGrid may reuse the
fixed range geometry privately, but it must not silently inherit list roles or
this family's application callback contract.

## 21. Internationalization

Virtual List owns no strings, messages, formatting, parsing, filtering,
sorting, comparison, or direction-sensitive symbols. `aria_label` and all item
content are application-localized inputs. No `$c-tr`, `i18n.bind()`, or
one-shot translation is registered. The component API's Translation keys
table is present and empty.
