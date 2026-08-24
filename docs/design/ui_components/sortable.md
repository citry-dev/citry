# Sortable

**Status (2026-08-22):** production implementation, public docs, structured
reference, examples, quality scenario, and focused browser
coverage shipped in `citry-ui` 0.2.0. Research refreshed 2026-08-21.

## 1. Purpose and product bar

`CSortable` reorders a finite server-rendered collection without making pointer
dragging the only interaction. `CSortableItem` declares one stable value, plain
accessible label, content, disabled state, and optional custom handle content.
The first release supports one vertical, horizontal, or grid container.

```html
<c-CSortable name="priority">
  <c-CSortableItem value="design" label="Design">Design</c-CSortableItem>
  <c-CSortableItem value="build" label="Build">Build</c-CSortableItem>
</c-CSortable>
```

The server order is useful without JavaScript. With JavaScript, a handle can be
dragged or operated with the keyboard. Native hidden inputs submit the accepted
order. Moving items between containers, moving tree nodes between parents,
free-positioned canvases, and application persistence are non-goals.

## 2. Prior art and complaints

| Product or standard | Surface inspected | Decision |
|---|---|---|
| ReUI Sortable, current 2026-08-21 | vertical, grid, nested, handles, overlays, dnd-kit integration | Adopt styled handles, vertical/horizontal/grid layouts, and clear moving state. Defer nested and multi-container movement. |
| dnd-kit Sortable and accessibility docs, current 2026-08-21 | stable IDs, DOM order, keyboard coordinates, activators, overlays | Require unique values, keep accepted DOM order authoritative, use a focusable handle, and preserve focus. |
| React Aria drag and drop, current 2026-08-21 | pointer, touch, keyboard, screen reader, drop positions | Provide equivalent keyboard operation and localized announcements. Do not expose a general data-transfer protocol. |
| Atlassian Pragmatic drag and drop accessibility guidelines, current 2026-08-21 | accessible alternatives, naming, announcements, focus | Make the handle a complete keyboard alternative and announce item label plus position. |
| HTML forms | repeated successful controls preserve tree order | Submit one hidden input per value in accepted order. |
| Vuetify 3, current 2026-08-21 | no first-class styled sortable family | Use Vuetify styling conventions only. Do not invent compatibility props. |

Complaints addressed include pointer-only ordering, drag gestures stealing
scroll, controls with no useful name, duplicated IDs in cloned previews,
controlled state that appears accepted before the owner responds, and focus
loss after DOM movement.

Vuetify disposition:

| Vuetify surface or job | Citry support path | Decision |
|---|---|---|
| List and card presentation | item content and CSS | Consumer content stays server-rendered and unrestricted except for the handle boundary. |
| density and theme | direct API and CSS variables | `size` plus public variables. |
| sortable state | new family behavior | `order` and `onOrderChange`. |
| cross-list and nested movement | omitted | Separate future contracts. |

## 3. Public composition and anatomy

```text
CSortable -> div state and styling root
|- ol named collection
|  `- CSortableItem -> li item
|     |- button handle
|     |- content
|     `- hidden input when name is present
|- hidden keyboard instructions
`- polite live region
```

Every layout renders one named ordered list inside the state and styling root;
grid presentation changes only CSS layout. Each Item renders one `li` with a
native Button handle. `CSortableItem` must be a direct logical child.
Duplicate values, unknown values in `order`, or non-declaration output fail.
The declaration component is retained because value, label, content, handle,
disabled state, form identity, and morph identity must stay one record.

## 4. Server inputs and client inputs

| Python input | Type/default | Class and effect |
|---|---|---|
| `id` | `str | None = None` | Structural; root ID and stable item IDs. |
| `order` | `Sequence[str] | None = None` | Initial state; declaration order when omitted. |
| `name`, `form` | `str | None = None` | Structural native form ownership. |
| `layout` | `"vertical" | "horizontal" | "grid" = "vertical"` | Reactive configuration. |
| `disabled` | `bool = False` | Reactive configuration. |
| `size` | `"sm" | "md" | "lg" = "md"` | Presentation. |
| message-label inputs | source English defaults | Explicit per-output localization override. |
| `class_`, `style`, `attrs` | structured values | Root customization without owned state replacement. |

Each Item requires `value` and `label`, accepts `disabled`, `class_`, `style`,
and `attrs`, and has default content plus an optional `handle` slot.

| Client input | Type | Omitted/null | Invalid | Effect |
|---|---|---|---|---|
| `order` | unique known `string[]` | uncontrolled/server order | diagnose, keep last valid | controlled accepted order |
| `layout` | string enum | server layout | diagnose | collision and key axes |
| `disabled` | boolean | server value | diagnose | disables every handle |
| `onOrderChange` | function | no callback | diagnose | receives requests and commits |

## 5. State model

The accepted order is one permutation of all declared values. In uncontrolled
mode a completed pointer or keyboard move commits immediately. In controlled
mode it emits a request, restores accepted order, and waits for `order`.
Repeated identical requests do nothing. Disabled roots and items cannot begin
or receive a move. Escape cancels an active move and restores origin. A server
morph supplies a new declaration set and server order unless a valid client
controlled order remains present.

## 6. Slots and slot data

`CSortable.default` accepts declarations only. `CSortableItem.default` receives
`{value, label, disabled, index}` and falls back to `label`.
`CSortableItem.handle` receives the same record and replaces only the visual
contents of the owned button; the button and its semantics remain owned.

## 7. Callbacks, native events, and methods

`onOrderChange(next, detail)` receives
`{order, previousOrder, value, fromIndex, toIndex, source, controlled,
sourceEvent}`. Source is `pointer`, `keyboard`, `reset`, or `client`.
Uncontrolled commits update form inputs and emit native `input` then `change`
from the root before the callback. Controlled moves are request-only.
No imperative method ships in v1.

## 8. Semantics, keyboard, focus, and assistive technology

Each handle is a native button named from the item label. Space or Enter picks
up and drops. Arrow keys move the proposed position along the layout axis;
Home and End move to the first and last valid position; Escape cancels. Tab
does not change order and handles remain in document order. Pointer and touch
start only on a handle. Touch activation waits long enough to preserve normal
scrolling and cancels on early scroll-like movement.

A polite atomic live region announces pickup, each new position, drop, and
cancel with the item label and one-based position. Focus remains on the moved
handle after a commit, rejection, or cancellation.

## 9. Native forms and validation

When `name` is present, one hidden input per item submits its value in accepted
order and may use external `form`. Disabled roots submit nothing. The family
has no required or constraint-validation contract. Form reset restores server
order in uncontrolled mode and requests it in controlled mode. Without
JavaScript, declaration order is submitted and remains readable.

## 10. Styling and theme contract

Public parts are `sortable`, `item`, `handle`, `content`, `placeholder`, and
`status`. Public variables are `--cui-sortable-gap`, `--cui-sortable-columns`,
`--cui-sortable-item-surface`, `--cui-sortable-item-border`,
`--cui-sortable-item-radius`, `--cui-sortable-item-shadow`,
`--cui-sortable-handle-size`, `--cui-sortable-focus`, and
`--cui-sortable-disabled-opacity`. Reflected attributes are `data-layout`,
`data-size`, `data-disabled`, `data-dragging`, `data-moving`, `data-value`, and
`data-placeholder`.

## 11. Environmental behavior

Logical CSS supports RTL. Horizontal arrow meaning follows visual inline
direction. Grid chooses the nearest item center. Forced colors preserve focus,
outline, and placeholder. Reduced motion removes lift and return transitions.
Long labels wrap without shrinking the handle. Coarse pointers receive a
larger handle. Print shows accepted content order and hides handles/status.
All source messages are under `CSortable.messages`, use `en-US`, and follow the
dormant, catalog-default, and explicit-override rules.

## 12. Overlay and layering behavior

The active original item becomes a fixed-position visual during pointer drag;
the runtime does not clone consumer content and therefore never duplicates
IDs. It is not a modal or Citry overlay. It uses pointer capture, stays below
application overlay categories, and is restored on cancel, removal, or error.

## 13. Collections, async data, and identity

Values are stable unique identity. The family owns no fetching, pagination,
virtualization, or cross-container transfer. Reordering a virtualized partial
window is unsupported because it cannot expose the complete accepted order.

## 14. Server render, morph, and cleanup

Repeated initialization is idempotent. Cleanup releases pointer capture,
listeners, prop effects, i18n bindings, active positioning, placeholders, and
form listeners. A morph during a move cancels first. A retained root preserves
accepted controlled order only when it remains a full valid permutation.

## 15. Security and content trust

Consumer content is escaped by Citry unless explicitly trusted by the
application. Values and labels are plain strings; values may not contain
U+0000, CR, or LF. General attributes cannot replace owned IDs, roles,
runtime markers, browser expressions, or handle semantics. The runtime never
uses `innerHTML`, `eval`, or serialized selectors containing raw values.

## 16. Assets and performance

The family owns one minified JavaScript runtime and one minified CSS asset.
It adds no document-global observer or permanent window listener. Pointer move
listeners exist only during a drag. Layout reads are cached at pickup and
refreshed after auto-scroll. Per-family raw, gzip, and Brotli sizes are recorded
after the built asset exists; catalog budget changes require measured evidence.

## 17. Acceptance matrix

Automated evidence covers schemas, registration, declaration validation,
server order, form order, controlled requests, pointer and keyboard moves,
cancel/rejection, disabled items, reset, i18n, fragments/morphs, cleanup, RTL,
reduced motion, forced colors, narrow/grid layout, axe, assets, snippets, docs,
wheel contents, and Chromium/Firefox/WebKit. Manual evidence covers keyboard,
VoiceOver/NVDA announcements, touch scrolling, long content, and visual polish.

Planned public examples are: basic priority list (`at_a_glance.py`), rich cards
and custom handles (`rich_items.py`), controlled order (`controlled.py`), grid
layout (`grid.py`), native form submission (`forms.py`), and disabled/keyboard
guidance (`accessibility.py`).

## 18. Compatibility classification

Names, input meanings, slots, callback detail, form output, message keys,
public CSS variables, parts, and reflected attributes are stable public API.
Keyboard behavior, accepted-order semantics, controlled requests, and useful
server output are behavioral contracts. Exact spacing, colors, easing, and
undocumented wrappers may evolve. Private classes and runtime markers are not
public API.

## 19. Public documentation contract

`csortable/api.md` owns the reader guide and the six examples.
`csortable/api.yml` exhaustively records Inputs, Slots, Events, CSS,
Attributes, Selectors, Interfaces, and the final Translation keys category.
Every example is shared with docs and quality tooling rather than copied.

## 20. Open decisions and deferred work

Moving between sibling containers, nested tree movement, virtualized reorder,
and application persistence are deferred separate contracts. They do not
block this family. An accessible action menu may be added later if manual
assistive-technology testing finds the handle interaction insufficient.

## 21. Internationalization

Keys cover handle name, instructions, pickup, moved position, drop, cancel,
and disabled-item feedback. Item label, position, and total are typed Fluent
variables. The stable handle uses `$c-tr`; browser-created live announcements
use one-shot `i18n.tr()`. Explicit label props remain fixed application text
and create no catalog binding. Direction changes update layout/key meaning;
application-authored item content keeps its own language and direction.
