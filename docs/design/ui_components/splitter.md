# Splitter

**Status:** implementation complete with focused server, browser, docs,
schema, scenario, asset, and package evidence. Manual assistive-technology,
touch-device, and visual review remains release qualification.

## 1. Purpose and product bar

`CSplitter` lets people resize two or more adjacent application panels.
`CSplitterPanel` declares stable panel identity, accessible name, content, and
percentage constraints. The family supports side-by-side and stacked layouts,
nested Splitters, pointer/touch dragging, precise keyboard resizing, and
controlled or uncontrolled sizes.

```html
<c-CSplitter c-sizes="[30, 70]">
  <c-CSplitterPanel id="navigation" label="Navigation">…</c-CSplitterPanel>
  <c-CSplitterPanel id="content" label="Content">…</c-CSplitterPanel>
</c-CSplitter>
```

Persistence is application composition through `onResizeEnd`. Non-goals are
automatic storage, CSS-unit constraints, panel collapse/expand state,
imperative stores, grid authoring, and window-management behavior.

## 2. Prior art and complaints

| Source | Review date | Surface | Citry decision |
|---|---|---|---|
| Vuetify | 2026-08-10 | current component catalog; no stable first-party Splitter surface found | Do not invent Vuetify parity where none exists; use Citry theme conventions. |
| Chakra UI 3.30+ Splitter | 2026-08-10 | multi-panel, controlled sizes, CSS units, constraints, collapse, nested layouts, keyboard and storage | Adopt multi-panel, controlled state, constraints, nesting and keyboard; defer CSS units, store and collapse. |
| PrimeVue Splitter | 2026-08-10 | percentage sizes, minimums, horizontal/vertical, nesting, separator semantics | Adopt concise percentage-based declaration and nested layouts. |
| WAI-ARIA/MDN separator | 2026-08-10 | focusable separator, value range, orientation, accessible naming | Implement exact range attributes and native focus/keyboard behavior. |

The main ecosystem complaints are inaccessible drag-only handles, lost panel
constraints, hydration shifts from CSS units, and libraries that silently own
localStorage. Citry uses percentages for stable server output, makes every
handle keyboard accessible, and leaves persistence explicit.

## 3. Public composition and anatomy

```text
div.cui-splitter
├─ div.cui-splitter__panel role=group
├─ div.cui-splitter__handle role=separator tabindex=0
├─ div.cui-splitter__panel role=group
└─ …
```

`CSplitter` accepts only two or more direct `CSplitterPanel` declarations.
Panels require unique nonempty `id` and `label`. A handle is generated between
each pair and controls exactly those panel IDs. A nested Splitter is valid
inside panel content because the panel removes the outer declaration context.

## 4. Server inputs and client inputs

Root server inputs: `sizes: Sequence[int|float] | None`, `orientation:
"horizontal"|"vertical"`, `disabled`, `keyboard_step` percentage points,
`variant: "plain"|"soft"|"outline"`, `size: "sm"|"md"|"lg"`, `class_`,
`style`, and `attrs`. Omitted sizes divide 100 equally. Supplied sizes must
match panel count, total 100 within 0.01, and satisfy every constraint.

Panel server inputs: required `id`, required `label`, `min_size=10`,
`max_size=100`, plus `class_`, `style`, and `attrs` on the concrete panel.

Client `sizes` is controlled while supplied; `null` releases to the last
effective sizes. `orientation`, `disabled`, `keyboardStep`, `variant`, and
`size` are reactive configuration. Invalid values report once per continuous
episode and retain the prior valid state.

## 5. State model

Every layout owns one ordered percentage vector totaling 100. A handle changes
only its adjacent pair and preserves their combined size. Pair limits are the
intersection of both panels' min/max constraints. Pointerdown begins one
resize transaction; pointermove requests sizes; pointerup/cancel ends it.
Keyboard Arrow keys move by `keyboard_step`, Shift uses four times the step,
and Home/End move to the pair minimum/maximum.

Uncontrolled requests commit immediately. Controlled requests notify and wait
for owner acceptance. Disabled root or native disabled fieldset disables all
handles and cancels an active drag without changing sizes.

## 6. Slots and slot data

| Owner | Slot | Required | Data | Fallback |
|---|---|---:|---|---|
| `CSplitter` | `default` | yes | `{}` | declarations only |
| `CSplitterPanel` | `default` | yes | `id`, `index`, `size`, `is_first`, `is_last` | none |

Panel content may contain ordinary interactive descendants and nested
Splitters. It cannot contain another direct outer `CSplitterPanel` declaration.

## 7. Callbacks, native events, and methods

`onResizeStart(detail)`, `onResize(sizes, detail)`, and
`onResizeEnd(sizes, detail)` are client callback inputs. Detail carries
`sizes`, `previousSizes`, `handleIndex`, `controlled`, `source`, and
`sourceEvent`. Source is `pointer` or `keyboard`. No custom DOM events or
imperative methods are exposed.

## 8. Semantics, keyboard, focus, and assistive technology

Panels are named `role=group` elements. Handles use `role=separator`,
`tabindex=0`, `aria-controls` for their two panels, an accessible name formed
from the adjacent panel labels, `aria-valuenow`, `aria-valuemin`,
`aria-valuemax`, and physical separator orientation. Side-by-side panels have
a vertical separator and Left/Right keys; stacked panels have a horizontal
separator and Up/Down keys. Tab order contains one stop per handle. RTL flips
the percentage effect of physical Left/Right movement.

The concrete panel and separator carry owned `aria-label` values. Disabled
handles expose `aria-disabled="true"` and `tabindex="-1"`; enabled handles use
`aria-disabled="false"` and `tabindex="0"`. The separator's
`aria-orientation` is `vertical` for horizontal layout and `horizontal` for
vertical layout.

## 9. Native forms and validation

Splitter is not a form control and contributes no FormData. Handles are divs,
not Buttons, and cannot submit a form. Controls authored inside panels retain
their native form behavior. Native disabled fieldsets dominate handles.

## 10. Styling and theme contract

Variants: plain, soft, outline. Sizes control handle hit area and visual line.
Stable parts: `splitter`, `panel`, `handle`, `handle-line`, `handle-grip`.

Public variables: `--cui-splitter-min-block-size`, `--cui-splitter-radius`,
`--cui-splitter-background`, `--cui-splitter-border-color`,
`--cui-splitter-handle-size`, `--cui-splitter-handle-color`,
`--cui-splitter-handle-active-color`, `--cui-splitter-focus-color`.

Public root reflections: `data-orientation`, `data-disabled`, `data-resizing`,
`data-variant`, `data-size`. Panels expose `data-panel-id`, `data-index`, and
`data-size-percent`, plus constraint reflections `data-min-size` and
`data-max-size`; handles expose `data-handle-index`, `data-disabled`, and
`data-active`. The stable semantic values are `role="group"` on panels and
`role="separator"` on handles.

## 11. Environmental behavior

Logical layout and physical pointer geometry support LTR/RTL. Panels use
`min-inline-size:0`, `min-block-size:0`, and overflow auto. Touch uses Pointer
Events and `touch-action:none` only on the handle. Reduced motion removes
transitions; forced colors preserves handle and focus boundaries; print
renders the settled layout without interactive grips. No library-authored
visible string is added.

## 12. Overlay and layering behavior

Splitter creates no overlay. Pointer capture stays on the active handle and is
released on completion, cancellation, disability, morph, or removal.

## 13. Collections, async data, and identity

Panel `id` is stable identity and unique per Splitter. Order defines adjacency.
Adding/removing/reordering panels is a server morph and resets uncontrolled
sizes unless the server size baseline and ordered IDs are unchanged. Async
content inside panels is application-owned.

## 14. Server render, morph, and cleanup

Server output contains complete percentage flex ratios and ARIA values. Client
activation installs delegated key/pointer listeners plus bounded root and
fieldset observers. Cleanup cancels drag, releases pointer capture, removes
listeners/observers/readiness, and stores only semantic uncontrolled sizes for
a compatible retained root.

## 15. Security and content trust

IDs and labels are canonical plain strings; IDs reject whitespace and U+0000.
Slots use normal trusted-template boundaries. Attrs cannot replace owned role,
identity, sizing, value, focus, visibility, children, or runtime attributes.
No size expression is evaluated as CSS or code.

## 16. Assets and performance

One CSS asset and one initializer are added. One root owns constant delegated
listeners and observers regardless of panel count. Pointermove work updates
only the adjacent pair and public ARIA values. No icon, font, overlay, storage,
or network dependency is added.

## 17. Acceptance matrix

Automated evidence covers declaration grammar, size/constraint validation,
server anatomy, pointer capture, controlled/uncontrolled drag, keyboard and
RTL directions, Home/End, callback phases, disabled/fieldset cancellation,
nested Splitters, form safety, public CSS, narrow/overflow geometry, reduced
motion, forced colors, print, axe, cleanup, exports, docs, API projection,
assets, scenarios, and packaging across Chromium, Firefox, and WebKit. Manual
release checks cover screen readers, coarse touch, zoom, and visual polish.

## 18. Compatibility classification

Public components, inputs, callback detail, parts, attributes, and variables
are stable. Internal collectors, generated handle/panel IDs, classes, runtime
markers, pointer bookkeeping, and observer strategy are private.

## 19. Public documentation contract

Examples cover two panels, multiple panels, vertical and nested layout,
constraints and keyboard, controlled persistence composition, disabled state,
and public customization.

## 20. Open decisions and deferred work

Collapsible panels, collapse callbacks, imperative reset/store APIs, CSS-unit
sizes, responsive orientation shortcuts, automatic persistence, and grid-like
two-axis resizing are deferred for separate design evidence.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
