# Timeline

**Status:** implementation contract accepted for the first production pass.
The family is intentionally server rendered and non-interactive; browser and
assistive-technology evidence still forms part of release qualification.

## 1. Purpose and product bar

`CTimeline` presents events, activity, milestones, and status history in an
ordered visual sequence. `CTimelineItem` declares one event. The family owns
the sequence, track, indicator placement, responsive layouts, and optional
visual state. It does not own event loading, selection, navigation, date
formatting, or application actions.

The shortest job is:

```html
<c-CTimeline>
  <c-CTimelineItem>Order placed</c-CTimelineItem>
  <c-CTimelineItem state="current">Preparing shipment</c-CTimelineItem>
</c-CTimeline>
```

Dates, headings, links, avatars, icons, logs, and actions are authored through
slots. Alternate and horizontal layouts are direct API. Pagination, streaming,
grouping, filtering, virtualisation, and an interactive value store are
composition or separate-family jobs. There is no headless Timeline API.

## 2. Prior art and complaints

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Vuetify `VTimeline` and `VTimelineItem` | current source reviewed 2026-08-21 | direction, side, alignment, line and dot styling, item slots, implementation measurement | Keep orientation, logical side, arbitrary indicator and opposite content; avoid JavaScript geometry measurement. |
| ReUI Timeline | current docs reviewed 2026-08-21 | anatomy, vertical/horizontal, roadmap, order, Git, alternating, logs, activity and leading-label examples | Cover the complex presentation jobs with a small root/item contract and slots. |
| Mantine Timeline | 9.5.1 docs reviewed 2026-08-21 | active prefix, alignment, bullets, opposite content, dashed lines, direct-child restriction | Keep explicit item state and line style; validate declarations instead of silently breaking through wrappers. |
| UI5 Web Components Timeline | nightly docs reviewed 2026-08-21 | read-only semantics, vertical/horizontal layout, items, groups, growing and loading | Keep the base family read-only; leave async growth and collection ownership to separate components. |
| W3C ordered-list technique H48 | current guidance reviewed 2026-08-21 | ordered and unordered list semantics | Render an `<ol>` because authored order carries meaning; do not invent a Timeline ARIA role. |

Vuetify remains the main styled-suite reference. Citry adopts its orientation,
logical-side layout, arbitrary opposite content, item indicator slot, and
customizable track. Citry rejects component-owned dot measurement and a
selection callback because Timeline is not a widget.

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `direction` | direct API | `orientation` | Adopt as `vertical` or `horizontal`. |
| `side` | direct API | root `side`; item override | Adopt and add `alternate`. |
| `align`, `justify` | CSS and stable parts | public variables and selectors | Omit dedicated inputs until a distinct semantic job appears. |
| `lineThickness`, `lineColor`, `lineInset` | CSS | public track variables | Prefer theme inputs over geometry props. |
| `truncateLine` | automatic anatomy | first/last item selectors | Omit; the track terminates at the outer indicators. |
| `dotColor`, `iconColor`, `fillDot`, `size` | direct state, slot, CSS | `state`, `indicator`, `size`, variables | Cover the jobs without color props. |
| `hideDot` | slot/CSS | public indicator part | Omit as a structural prop. |
| `hideOpposite` | slot omission | omit `opposite` | Native composition. |
| `icon`, `opposite`, default slots | slots | `indicator`, `opposite`, `default` | Adopt. |

## 3. Public composition and anatomy

```text
ol.cui-timeline
└─ li.cui-timeline__item × 1+
   ├─ div.cui-timeline__opposite?
   ├─ div.cui-timeline__track (aria-hidden)
   │  ├─ span.cui-timeline__before
   │  ├─ span.cui-timeline__indicator
   │  └─ span.cui-timeline__after
   └─ div.cui-timeline__content
```

`CTimelineItem` is declaration-only and must be rendered as a direct
declaration of one `CTimeline`; formatting whitespace and transparent
declaration helpers may surround declarations, but other output is rejected.
The owning Timeline renders each declaration as an `<li>`. One or more items
are required. Nested Timelines are valid inside an item's rendered slot, not
inside the declaration list.

Root `attrs`, `class_`, and `style` land on the `<ol>`. Item equivalents land
on the `<li>`. Owned semantics, state, part markers, and runtime attributes
cannot be replaced.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `CTimeline.orientation` | `"vertical" | "horizontal"` | `"vertical"` | structural | Selects the track axis. |
| `CTimeline.side` | `"start" | "end" | "alternate"` | `"end"` | structural | Places content on the logical end, start, or alternating sides of the track. |
| `CTimeline.line_style` | `"solid" | "dashed"` | `"solid"` | structural | Selects connector treatment. |
| `CTimeline.density` | `"comfortable" | "compact"` | `"comfortable"` | structural | Selects spacing. |
| `CTimeline.size` | `"sm" | "md" | "lg"` | `"md"` | structural | Selects indicator and track geometry. |
| `CTimeline.label` | `str | None` | `None` | structural | Optionally names the ordered list. |
| `CTimeline.class_`, `style`, `attrs` | structured values | `None` | structural | Extend the documented root without replacing owned state. |
| `CTimelineItem.state` | `"neutral" | "complete" | "current" | "pending" | "error"` | `"neutral"` | structural | Reflects authored visual status; `current` also sets `aria-current=true`. |
| `CTimelineItem.side` | `"auto" | "start" | "end"` | `"auto"` | structural | Overrides the root placement for one item. |
| `CTimelineItem.class_`, `style`, `attrs` | structured values | `None` | structural | Extend the rendered `<li>`. |

The family has no client inputs. All state is authored server data and changes
through an ordinary render or fragment update.

## 5. State model

Item state is declarative and has no transition owner. `neutral` is an
unclassified event, `complete` a completed milestone, `current` the event that
represents the present position, `pending` a future or waiting milestone, and
`error` a failed milestone. At most one item may be `current`. These names are
styling and semantic metadata, not workflow policy; they never disable links or
buttons in item content.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---:|---:|---|---|
| `CTimeline` | `default` | yes | one | `{}` | declarations only |
| `CTimelineItem` | `default` | yes | one | `index`, `state`, `side`, `is_first`, `is_last` | none |
| `CTimelineItem` | `opposite` | no | one | same | omitted |
| `CTimelineItem` | `indicator` | no | one | same | decorative dot |

Slot data is settled server data. `opposite` commonly contains a semantic
`<time datetime=...>` but may contain any authored metadata. The default slot
owns headings, descriptions, links, buttons, and actions. The indicator slot is
rendered inside an `aria-hidden` track; meaningful status must also be present
in authored text.

## 7. Callbacks, native events, and methods

There are no Timeline callbacks, custom events, or methods. Native events on
authored interactive descendants remain ordinary application events.

## 8. Semantics, keyboard, focus, and assistive technology

The root is an ordered list and every event is a list item. An optional
`aria-label` names the list without introducing a landmark. A current item has
`aria-current="true"`; no other state creates ARIA. Track and indicator visuals
are hidden from the accessibility tree.

Timeline adds no focus target or keyboard behavior. Links, Buttons, menus, and
other descendants retain native Tab and activation behavior. DOM order stays
chronological in every visual layout, including alternate and horizontal.

## 9. Native forms and validation

Timeline is not a form control and submits no value. Authored controls inside
item content keep their native form ownership and validation.

## 10. Styling and theme contract

Public parts are `timeline`, `item`, `opposite`, `track`, `before`, `indicator`,
`after`, and `content`. Public variables are `--cui-timeline-gap`,
`--cui-timeline-item-gap`, `--cui-timeline-track-size`,
`--cui-timeline-indicator-size`, `--cui-timeline-line-width`,
`--cui-timeline-line-color`, `--cui-timeline-indicator-color`,
`--cui-timeline-current-color`, `--cui-timeline-complete-color`,
`--cui-timeline-pending-color`, `--cui-timeline-error-color`, and
`--cui-timeline-muted-color`.

Root reflections are `data-orientation`, `data-side`, `data-line-style`,
`data-density`, and `data-size`. Item reflections are `data-index`,
`data-state`, `data-side`, and `data-has-opposite`; the last is present when
the optional opposite slot has authored content.

## 11. Environmental behavior

Logical properties preserve start/end meaning in RTL. Alternate placement is
derived from settled index while DOM order remains unchanged. Horizontal
layout scrolls within the component rather than widening the page. Long copy
wraps; compact mode remains readable at narrow widths. Forced colors retains
the indicator and line, reduced motion has no special path because the family
does not animate, and print uses current color instead of background-only
status.

All visible text and dates are application-authored slots. Timeline performs
no parsing, formatting, comparison, filtering, case conversion, or direction
guessing and owns no catalog messages. Slot content therefore retains its own
locale and bidi ownership. The structured Translation keys table is empty.

## 12. Overlay and layering behavior

Timeline never creates or controls an overlay. Overlays authored inside item
content retain their own logical ownership.

## 13. Collections, async data, and identity

Settled zero-based order is item identity for slot data and alternating layout.
The optional morph key is derived from that order; applications that need
stable state across reorder should wrap or rerender with their own keyed
collection before declaring items. Loading, empty, error, retry, pagination,
streaming, grouping, and virtualisation are application composition or future
specialist families. `state="error"` is presentation metadata, not an async
error store.

## 14. Server render, morph, and cleanup

The complete useful component is server-rendered HTML and CSS. There is no
initializer, listener, observer, timer, subscription, or cleanup. Fragment
insertion and morphing replace the settled list normally. A nested Timeline
receives an independent declaration registry.

## 15. Security and content trust

Slots use ordinary Citry escaping and trust rules; no raw-HTML shortcut is
added. General attrs reject owned roles, ARIA state, part/state markers,
visibility and child-replacement directives, and Citry runtime markers.
Indicator content is decorative by contract, preventing an icon-only status
from becoming the sole accessible output.

## 16. Assets and performance

The family contributes only one compact CSS asset. It adds no JavaScript,
icon, font, network request, measurement, or observer. Horizontal overflow is
native CSS scrolling.

## 17. Acceptance matrix

Focused evidence covers declaration placement and cardinality, exact ordered
list anatomy, state and current uniqueness, side resolution, slots and slot
data, root/item attrs, invalid inputs, nested isolation, no-JavaScript output,
RTL, narrow horizontal overflow, forced colors, print, axe, exports, typing,
API projection, snippets, quality routing, assets, and wheel inclusion.
Manual qualification includes visual review at supported zoom levels and
VoiceOver/Safari plus NVDA/Firefox review of list order and current state.

## 18. Compatibility classification

The two public classes, inputs, slot data, parts, reflected attributes, and CSS
variables are stable. Declaration registries, internal renderers, private CSS
variables, classes, and index-based morph keys are private.

## 19. Public documentation contract

The guide includes a basic activity history, status progression, opposite
dates, custom avatar/icon indicators, alternating layout, horizontal roadmap,
RTL/compact behavior, and styling. It explicitly compares Timeline with
Stepper and documents that indicator meaning must also appear in text. The API
reference ends with the structured empty Translation keys section.

## 20. Open decisions and deferred work

Date/group declarations, built-in growing/loading, record-driven rendering,
stable application keys, selection, collapsible items, and virtualisation are
deferred. They require separate collection or interaction evidence and are not
implied by this base family.

## 21. Internationalization

Timeline owns no messages. Application-authored date and content slots are
rendered unchanged, so applications may use Citry `tr()`, `$c-tr`, locale
formatters, and explicit `dir` boundaries as needed. No browser binding is
registered by the family.
