# Scroll Area component design

**Status:** implemented and independently reviewed, 2026-08-11.

This specification follows the
[`Citry UI family workflow`](../../../packages/py/citry_ui/docs/component-authoring.md#requalify-one-component-family-at-a-time)
and the shared [component specification template](./_template.md).

## 1. Purpose and product bar

`CScrollArea` gives bounded content a durable, focusable, styled native
scrolling surface. A supplied naming input can promote it to a named region.
The browser viewport remains the only scrolling mechanism.
The component adds the behavior that repeated `overflow: auto` utility use does
not provide consistently: deterministic focus entry, optional region naming,
standard scrollbar and gutter policy, normalized RTL scroll notifications, and
lifecycle repair through direction change, Citry morph, and removal.

Use plain CSS when a page only needs `overflow: auto`, `scrollbar-width`, or
`scrollbar-color`. `CScrollArea` earns its additional JavaScript only when at
least one of its accessibility, normalized callback, RTL, or lifecycle
contracts is required.

Common jobs and shortest intended expressions are:

| Job | Template composition | Python composition | Support path |
|---|---|---|---|
| Bounded activity feed | `<c-CScrollArea aria_label="Recent activity">...</c-CScrollArea>` | `CScrollArea(aria_label="Recent activity", slots={"default": (...)})` | direct component API |
| Horizontal tag or metadata rail | `<c-CScrollArea aria_label="Applied filters" axis="inline">...</c-CScrollArea>` | `CScrollArea(aria_label="Applied filters", axis="inline", slots={"default": (...)})` | direct component API plus consumer layout CSS |
| Two-axis wide data surface | `<c-CScrollArea aria_labelledby="results-title" axis="both">...</c-CScrollArea>` | `CScrollArea(aria_labelledby="results-title", axis="both", slots={"default": (...)})` | direct component API; native table semantics stay in slot content |
| Reserve stable native scrollbar space | `<c-CScrollArea aria_label="Log" scrollbar_gutter="stable">...</c-CScrollArea>` | `CScrollArea(aria_label="Log", scrollbar_gutter="stable", slots={"default": (...)})` | direct component API |
| Limit native scroll chaining | `<c-CScrollArea aria_label="Inspector" overscroll="contain">...</c-CScrollArea>` | `CScrollArea(aria_label="Inspector", overscroll="contain", slots={"default": (...)})` | direct CSS policy API; no event-delivery guarantee |
| Brand the surface | `<c-CScrollArea class="audit-scroll">...</c-CScrollArea>` | `CScrollArea(aria_label="Audit", class_="audit-scroll", style={"--cui-scroll-area-radius": "0.25rem"}, slots={"default": (...)})` | public variables and selectors |
| Virtualized or remotely paged collection | compose a collection component that owns virtualization | same | separate collection component |
| App-specific previous/next controls | compose ordinary Buttons with application-owned viewport DOM access | same | composition, not built-in anatomy |
| Simple native overflow | `<div class="overflow-auto">...</div>` | ordinary HTML | CSS or utility class; do not use `CScrollArea` |

The closest native pattern is a focusable native-overflow `div`. When exactly
one of `aria_label` or `aria_labelledby` is supplied it becomes a named
`div[role="region"]`. When both are omitted it remains a generic focusable
element with neither role nor accessible-name attribute. There is no WAI-ARIA
Scroll Area widget pattern and no component-authored keyboard interaction
model.

Production completeness requires useful server output without JavaScript,
visible native scrollbars according to platform settings, deterministic focus
entry, light/dark and forced-colors behavior, print expansion, event-scoped
logical RTL measurements, nested-area isolation, correlated morph preservation,
complete cleanup, and 1/10/100-instance evidence.

Non-goals for v1 are custom scrollbar tracks, thumbs, or corners; hidden
native scrollbars; pointer dragging; custom wheel, touch, or key handling;
controlled or initial scroll positions; imperative public methods; built-in
scroll buttons; scroll snapping; virtualization; collection selection;
infinite loading; edge shadows or persistent overflow-edge state; rich text
editing; vertical writing modes; and headless parts. Horizontal writing mode
with LTR and RTL direction is the supported writing-mode boundary.

## 2. Prior art and complaints

The inventory classifies Scroll Area as native scrolling with durable visual
and RTL affordances. The taxonomy permits a component only where native CSS is
not enough and the extra behavior is explicit. Existing Citry consumers
already establish a native-first baseline:

- `CCarousel` uses a real overflow viewport, scroll snap, raw `scrollLeft`,
  focusability, and family-specific drag and index logic. Its hidden scrollbar
  policy is not copied. Its horizontal coordinate conversions must share the
  pure logical-offset helper introduced for Scroll Area, while snap targeting,
  drag, and selected-index settlement remain Carousel-specific.
- Tabs, Breadcrumbs, and Toolbar use thin native scrollbars.
- Menu, Listbox, Tree, Select, Combobox, Dialog, and Drawer use native overflow
  and, where appropriate, `overscroll-behavior: contain`. They continue to own
  their collection and overlay scrolling. Wrapping those internal viewports in
  a Scroll Area is not a replacement for their behavior.
- Bootstrap complaint BS-5 records overflow wrappers clipping ordinary
  overlays. Scroll Area must state that clipping boundary rather than imply
  that positioned descendants escape it.
- Radix issues [926](https://github.com/radix-ui/primitives/issues/926) and
  [2722](https://github.com/radix-ui/primitives/issues/2722) record width,
  ellipsis, and intrinsic sizing changes from its `display: table` content
  wrapper. The current source still contains that wrapper. Citry rejects it.
- Radix issues [2064](https://github.com/radix-ui/primitives/issues/2064) and
  [2888](https://github.com/radix-ui/primitives/issues/2888) show the cost of
  custom smooth-scroll and vertical-wheel remapping. Citry owns neither.
- Mantine issue [8844](https://github.com/mantinedev/mantine/issues/8844)
  records scrollbar-presence/offset state failing to converge. Persistent bar
  and edge state is outside v1.
- Web Awesome issue
  [1724](https://github.com/shoelace-style/webawesome/issues/1724) records a
  flex/grid sizing and fade regression. Citry uses one element and no fade.

Current official source record:

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| CSS Overflow Module Level 3 | editor draft, 2026-08-11 | [overflow model and scrollbar gutters](https://drafts.csswg.org/css-overflow/) | native overflow, overlay/classic distinction, and `scrollbar-gutter` are the base |
| CSS Scrollbars Styling Level 1 | editor draft, 2026-08-11 | [standard scrollbar styling](https://drafts.csswg.org/css-scrollbars/) | expose only `scrollbar-width` and `scrollbar-color`; precise internals are outside the standard |
| CSS Overscroll Behavior Level 1 | editor draft, 2026-08-11 | [logical overscroll policy](https://drafts.csswg.org/css-overscroll-1/) | expose auto, contain, and none as CSS policy without event interception |
| CSSOM View | editor draft, 2026-08-11 | [scroll geometry and events](https://drafts.csswg.org/cssom-view/) | raw browser geometry needs logical normalization for event detail and morph restoration |
| CSS Paged Media Module Level 3 | editor draft, 2026-08-11 | [content outside the page box](https://drafts.csswg.org/css-page-3/#content-outside-page-box) | removing component clipping does not guarantee that wide inline content fits a printed page |
| Media Queries Level 4 | editor draft, 2026-08-11 | [`overflow-inline` media feature](https://drafts.csswg.org/mediaqueries/#overflow-inline) | paged media has a finite inline area; the application owns print reflow, scaling, or an alternate representation |
| HTML | living standard, 2026-08-11 | [`tabindex` focus behavior](https://html.spec.whatwg.org/dev/interaction.html#the-tabindex-attribute) | explicit `tabindex="0"` requests deterministic sequential focus |
| WAI-ARIA | 1.2 Recommendation, reviewed 2026-08-11 | [`region` role](https://www.w3.org/TR/wai-aria-1.2/#region) | create a landmark only when a useful name is supplied; role and name are one conditional pair |
| WCAG 2.2 | W3C Recommendation, 2024-12-12 | [WCAG 2.2](https://www.w3.org/TR/WCAG22/), [G202](https://www.w3.org/WAI/WCAG22/Techniques/general/G202), [G225](https://www.w3.org/WAI/WCAG22/Techniques/general/G225), [C43](https://www.w3.org/WAI/WCAG22/Techniques/css/C43) | focusable scrolling, 400 percent zoom/reflow, visible focus, and spacing acceptance |
| Vuetify | 4.1.8, 2026-08-07 | [tagged component source](https://github.com/vuetifyjs/vuetify/tree/v4.1.8/packages/vuetify/src/components) | no general Scroll Area component; keep scope narrow and native rather than copying virtual/infinite collections |
| Mantine ScrollArea | 9.5.1, 2026-08-02 | [docs](https://mantine.dev/core/scroll-area/), [tagged source](https://github.com/mantinedev/mantine/tree/9.5.1/packages/%40mantine/core/src/components/ScrollArea) | adopt event-scoped position reporting; reject persistent edge state, custom scrollbar modes, and physical-side controls |
| Radix Scroll Area | 1.2.18 source snapshot, 2026-08-11 | [docs](https://www.radix-ui.com/primitives/docs/components/scroll-area), [source commit](https://github.com/radix-ui/primitives/tree/f7ecd5ab16f5e1e820eb5786a1419a98a2d594ae/packages/react/scroll-area) | reject replacement bars and the implicit table content wrapper; adopt native scrolling only |
| Ark UI Scroll Area | 5.38.1, 2026-08-11 | [docs](https://ark-ui.com/docs/components/scroll-area), [tagged source](https://github.com/chakra-ui/ark/tree/%40ark-ui/react%405.38.1/packages/react/src/components/scroll-area) | native viewport is sound; reject hidden native bars and replacement anatomy |
| Zag Scroll Area | 1.43.0, 2026-08-11 | [docs](https://zagjs.com/components/vue/scroll-area), [tagged machine source](https://github.com/chakra-ui/zag/tree/%40zag-js/scroll-area%401.43.0/packages/machines/scroll-area) | normalized position prior art is useful; persistent edge state and custom pointer machinery are outside v1 |
| Base UI Scroll Area | 1.7.0, 2026-08-11 | [docs](https://base-ui.com/react/components/scroll-area), [tagged source](https://github.com/mui/base-ui/tree/v1.7.0/packages/react/src/scroll-area) | custom track/thumb interaction cost supports the native-only boundary |
| Reka UI Scroll Area | 2.10.3, 2026-08-11 | [docs](https://reka-ui.com/docs/components/scroll-area), [tagged source](https://github.com/unovue/reka-ui/tree/v2.10.3/packages/core/src/ScrollArea) | native viewport plus styled replacement controls is possible but not necessary for Citry v1 |
| Web Awesome Scroller | docs 3.11.0; latest public source tag v3.10.0, reviewed 2026-08-11 | [current docs](https://webawesome.com/docs/components/scroller), [latest public tagged source](https://github.com/shoelace-style/webawesome/tree/v3.10.0/packages/webawesome/src/components/scroller) | adopt optional naming; reject hidden bars, edge fades, and custom Home/End behavior; no public v3.11.0 source tag was available at review |
| Vaadin Scroller | 25.2.7, 2026-08-11 | [docs](https://vaadin.com/docs/latest/components/scroller), [tagged source](https://github.com/vaadin/web-components/tree/v25.2.7/packages/scroller/src) | native directions and overflow indicators support the boundary; horizontal scrolling remains exceptional |

A disposable Playwright 1.62.0 probe used Chromium 151.0.7922.34,
Firefox 153.0, and WebKit 26.5 on 2026-08-11. No workspace file was retained.
All three used the negative RTL model: horizontal RTL begins at raw
`scrollLeft == 0`, positive values clamp to zero, and movement toward inline
end produces negative values. Explicit `tabindex="0"` was necessary for
deterministic WebKit sequential focus. Native key increments differed, so v1
does not promise pixels or intercept keys. A stable gutter reserved 15 CSS px,
and `stable both-edges` 30 CSS px, in the tested Chromium environment; both
could reserve zero in the tested overlay-scrollbar Firefox and WebKit
environments. Native `scrollend` syntax and one terminal smooth-scroll event
were present in all three, so no polyfill is justified. Nested automated wheel
chaining differed in Firefox, so `overscroll` is a CSS policy only, not a promise that a particular
wheel, trackpad, or touch event chains. `overflow-x: clip` paired with
perpendicular `auto` computed to `hidden` and remained programmatically
scrollable in all three engines. A generic scrollable element with only
`aria-label` was not a dependable named accessibility object, so Citry emits
the `region` role and name only as a pair. Print `overflow: visible` expanded
the viewport in all three.

A second disposable three-engine probe tested the owned-write suppression
boundary. With computed `scroll-behavior: auto`, a zero-delay timer could run
before the native `scroll` event, so timer-task expiry is invalid. Chromium,
Firefox, and WebKit all delivered the native event before the next requested
animation frame. A consumer class and earlier inline declaration using
`smooth !important` still computed to `auto` when the component's owned inline
`auto !important` declaration was appended last. These results ratify the
one-frame generation-owned expiry below, not a timer assumption.

Citry adopts the real native viewport, explicit focusability, optional named
region, event-scoped logical measurements, native standard styling, and narrow
lifecycle reconciliation. Citry rejects replacement scrollbars, hidden bars,
edge shadows and persistent edge state, vendor scrollbar selectors as public
API, arbitrary pixel keyboard behavior, event interception, controlled
offsets, and content layout hacks. Edge affordances are rejected because
stylesheet-only movement of absolute descendants can change scroll extents
without a reliable standard observer signal. Observing every descendant or
polling would violate the native-first cost boundary.

Vuetify receives the primary styled-suite disposition weight even though its
current tagged suite has no direct general-purpose counterpart:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| Native bounded overflow used by components | direct API or plain CSS | `CScrollArea` or ordinary `overflow` | adopt native mechanism |
| Virtual scrolling | separate component | existing/future virtual collection | omit from Scroll Area |
| Infinite loading | separate component | infinite collection pattern | omit from Scroll Area |
| Dense Menu/Listbox scrolling | existing component ownership | Menu/Listbox/Tree viewport | do not wrap or duplicate |
| Axis selection | direct API | `axis` | adopt logical block, inline, or both |
| Dimensions | CSS or utility classes | `style`, `class_`, public max-size variable | avoid dimension prop proliferation |
| Scrollbar styling | standard CSS | `scrollbar_width`, color variables | support auto/thin, never hidden |
| Edge affordance | application content/CSS | none | omit because reliable always-current overflow-edge state is not observable at bounded cost |
| Programmatic scrolling | native DOM composition | consumer-owned native viewport access | no public method in v1 |
| RTL | behavioral contract | normalized event detail and preserved morph/direction offset | stronger explicit contract |
| Controlled offset | omitted | none | browser owns scroll position |
| Slots | ordinary content | default slot | one transparent content boundary |

## 3. Public composition and anatomy

Minimal template composition:

```html
<c-CScrollArea aria_label="Recent activity">
  <ol>
    <li>Import completed</li>
    <li>Review requested</li>
    <li>Release approved</li>
  </ol>
</c-CScrollArea>
```

Minimal Python composition:

```python
from citry_ui.components.cscroll_area import CScrollArea

activity = CScrollArea(
    aria_label="Recent activity",
    slots={"default": ("Import completed", "Review requested", "Release approved")},
)
```

Public anatomy is one element and is exact:

```text
div#<id>[data-citry-ui-part="scroll-area"][tabindex="0"]
└── default slot
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CScrollArea` | native overflow `div` | `class_`, `style`, and `attrs` target this same element | root is explicitly focusable and is the only scroll viewport; one naming input adds `role="region"` with `aria-label` or `aria-labelledby` |

Generated and supplied root IDs follow the common Citry ID grammar and are
collision checked. A duplicate or replaced root ID, changed part marker,
tabindex, conditional role/name pair, or configuration reflection suspends
enhanced behavior until the immutable server anatomy is repaired.

Consumers retain semantic ownership and layout of direct slotted content. The
component adds no content wrapper and therefore cannot introduce
`display: table`, forced `max-content`, transforms, measurement clones, or a
new formatting context. Empty content is valid so asynchronous server
fragments can fill the surface later.

Only the elements and direct relationships shown above are stable. Native
scrollbar implementation nodes are user-agent UI, not public parts. No track,
thumb, corner, button, shadow, live-region, or focus-sentinel element exists.

## 4. Server inputs and client inputs

Server inputs are exact:

```python
CScrollAreaAxis = Literal["block", "inline", "both"]
CScrollAreaScrollbarWidth = Literal["auto", "thin"]
CScrollAreaScrollbarGutter = Literal["auto", "stable", "stable-both-edges"]
CScrollAreaOverscroll = Literal["auto", "contain", "none"]
```

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `id` | `str | None` | generated | structural | root ID base; nonempty, no ASCII whitespace or U+0000 |
| `aria_label` | `str | None` | `None` | structural | direct region name; non-whitespace and U+0000-free; exact text preserved; mutually exclusive with `aria_labelledby` |
| `aria_labelledby` | `str | None` | `None` | structural | ASCII-whitespace-separated IDREF list preserved exactly; each token follows the Citry HTML-ID grammar and is unique; mutually exclusive with `aria_label` |
| `axis` | `CScrollAreaAxis` | `"block"` | reactive configuration | logical `block`, `inline`, or `both` native overflow policy |
| `scrollbar_width` | `CScrollAreaScrollbarWidth` | `"auto"` | reactive configuration | standard `auto` or `thin`; no hidden value |
| `scrollbar_gutter` | `CScrollAreaScrollbarGutter` | `"auto"` | reactive configuration | `auto`, `stable`, or `stable-both-edges` |
| `overscroll` | `CScrollAreaOverscroll` | `"auto"` | reactive configuration | standard native `auto`, `contain`, or `none` policy on enabled logical axes |
| `class_` | `CClassValue | None` | `None` | structural | classes on native root viewport |
| `style` | `CStyleValue | None` | `None` | structural | styles on native root viewport; merges with allowed `attrs` style contributions |
| `attrs` | `Mapping[str, object] | None` | `None` | structural | allowed native-root attributes; class/style contributions merge with `class_`/`style` |

Naming inputs are deliberately server-only. Both omitted emits neither
`role` nor a naming attribute; exactly one valid input emits `role="region"`
and its corresponding naming attribute. Both supplied, an empty direct label,
an empty/duplicate/invalid IDREF token, ASCII-control whitespace inside a
token, or U+0000 is a server error. The consumer owns existence, uniqueness,
and useful text of external `aria_labelledby` targets; release examples prove
the final browser name. Targets must be in the root's own Document or open
ShadowRoot tree scope; cross-root IDREFs are unsupported. Changing region
identity is a server render. Dynamic
instructions or status belong in visible content and `aria-describedby`, not
a reactive naming prop. The component does not query future sibling DOM or
observe the document for external label changes. A missing target, duplicate
DOM ID, or target with no usable browser name is a consumer error surfaced by
AX/axe evidence, not component state.

Client inputs are exact:

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `axis` | `CScrollAreaAxis` | server fallback | server fallback | retain last valid effective client value and report once per invalid episode | overflow policy and reflection |
| `scrollbarWidth` | `CScrollAreaScrollbarWidth` | server fallback | server fallback | retain last valid effective client value and report once per invalid episode | `scrollbar-width`, reflection |
| `scrollbarGutter` | `CScrollAreaScrollbarGutter` | server fallback | server fallback | retain last valid effective client value and report once per invalid episode | `scrollbar-gutter`, reflection |
| `overscroll` | `CScrollAreaOverscroll` | server fallback | server fallback | retain last valid effective client value and report once per invalid episode | `overscroll-behavior`, reflection |
| `onScrollChange` | `function | null` | no component callback | no component callback | retain last valid callback; first invalid value means no callback; report once per episode | event-scoped normalized native scroll notification only |

Valid client values win field by field. Omission and `null` release only that
field to its latest server fallback. A server morph changes the fallback but
does not seize a still-valid client override. Invalidity in one client field
does not block reconciliation of another field. Public reflected attributes
are output only; mutation never changes configuration and is repaired.

The module and family/package `__all__` export exactly `CScrollArea`,
`CScrollAreaAxis`, `CScrollAreaScrollbarWidth`, `CScrollAreaScrollbarGutter`,
`CScrollAreaOverscroll`, and `CScrollAreaScrollDetail`. `Kwargs`, validators,
geometry records, observer registries, and client controller records remain
private.

## 5. State model

The browser owns the actual scroll offsets. The component owns effective
configuration, a cached logical offset used for direction/morph repair, and an
event-scoped normalized snapshot created only for `onScrollChange`. It does not
claim to hold always-current geometry between native scroll events. There is no
controlled or uncontrolled scroll-position axis.

There is no component `disabled`, `readonly`, `loading`, `pending`, `invalid`,
or error state. Empty content is valid native content. Consumer descendants
retain their own states and interaction.

For supported `writing-mode: horizontal-tb`:

```text
inlineMaximum     = max(0, scrollWidth - clientWidth)
blockMaximum      = max(0, scrollHeight - clientHeight)
inlineOffset      = clamp(direction == rtl ? -scrollLeft : scrollLeft,
                          0, inlineMaximum)
blockOffset       = clamp(scrollTop, 0, blockMaximum)
```

The maxima are private clamping inputs only. Raw overscroll and bounce never
appear as negative public offsets or offsets beyond the current range. No
maximum, progress, edge Boolean, or persistent overflow reflection is public.

`axis="block"` uses native block-axis `auto` and inline-axis `hidden`.
`axis="inline"` uses native inline-axis `auto` and block-axis `hidden`.
`axis="both"` uses native `auto` on both logical axes. Current engines may retain a
programmatic coordinate on an axis styled `hidden`; therefore init,
configuration, native-scroll settlement, and morph restoration reset a
disabled-axis coordinate to zero. Citry does not claim that the CSS value makes
that raw coordinate impossible.

The root always owns `scroll-behavior: auto !important`. The rendered inline
declaration is appended after consumer style contributions, and the property
is reserved from runtime mutation. This is not a motion preference: it makes
controller-owned disabled-axis, direction, and morph coordinate writes
instantaneous and therefore one transaction. Consumer classes or inline
styles that request smooth scrolling cannot change the root's computed
`scroll-behavior`. A consumer may still request smooth movement explicitly in
its own `scrollTo()` call; those resulting native events are ordinary external
scrolling and are not an owned write.

Meaningful states and transitions are:

| Trigger | Guard | Commit | DOM and visual effect | Callback |
|---|---|---|---|---|
| successful initialization | valid retained anatomy | cache the current logical offsets and reset a disabled axis through an owned-write token when necessary | set private readiness; public configuration reflections were already in SSR | silent |
| native scroll | initialized, horizontal writing mode, and current generation | synchronously cache logical offsets, then measure one normalized snapshot in an animation frame | repair disabled-axis coordinates; no public geometry DOM state | one `onScrollChange` callback for the latest coalesced native event |
| valid client configuration | current generation | apply field, reset newly disabled axis, and preserve still-enabled cached logical offset through one owned-write token | update CSS and configuration reflections | silent; a matching restoration event updates the cache only |
| ancestor or root direction change | current root and generation | preserve cached distance from the new inline start and clamp through one owned-write token | write converted raw coordinate | silent; a matching restoration event updates the cache only |
| invalid anatomy or writing mode | validation fails | suspend normalized callback and repair work without altering native scrollability | remove private readiness and diagnose once | none |
| repaired anatomy or writing mode | synchronous preflight and settled validation pass | activate a new generation and cache native position | restore owned identities and private readiness | silent |
| correlated morph | compatible handoff fingerprint | retain normalized offsets and valid client configuration, then restore and clamp through one owned-write token | no focus move and no geometry reflection | silent; a matching restoration event updates the cache only |
| cleanup | owner generation ends | cancel work and unregister | remove private readiness; leave native scroll/focus alone | none |

Configuration changes do not synthesize a scroll callback. Content, image,
font, viewport, or stylesheet changes do not create a component notification.
Controller-owned coordinate writes use a generation-owned suppression token
containing the exact expected logical inline/block offsets. A native `scroll`
event is silent only when the connected owner token is current and both
normalized offsets match that expectation within one CSS pixel. That event
updates the cache, clears the token, and never enters the public animation
frame. An unmatched event clears the token and follows the ordinary public
path. The controller's one generation-owned animation-frame slot expires an
unconsumed token after the proved native-event boundary; cleanup, reentrant
configuration, and a newer owned write cancel it. Thus a later user or
application scroll cannot be swallowed. Native listeners supplied through
`attrs` still observe every browser event, including a restoration event,
subject to Citry's isolated component-root expression scope described in
section 7.
Consumers needing current geometry outside a scroll callback read the native
viewport directly.

Direction detection samples `getComputedStyle(viewport).direction`. The scroll
listener updates the normalized cache synchronously before deferred writes.
When an observed root/composed-ancestor `dir`, `class`, or `style` mutation
changes direction, the
controller converts the cached logical value to the new raw model and clamps
it. This counters the tested browser behavior that resets raw `scrollLeft` to
zero on a direction change. Stylesheet-only direction changes are reconciled
at the next native scroll, configuration update, or explicit Citry morph
settlement; no global stylesheet observer exists.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---:|---:|---|---|
| `CScrollArea` | `default` | no | one fill | none | empty native root viewport |

The default slot accepts ordinary escaped text, standard HTML, and resolved
Citry components under the normal trusted slot boundary. It is not a
collection declaration surface, has no key or dynamic namespace, and exports
no reactive slot data. Nested `CScrollArea` roots are valid. If they are named,
their labels must be distinct and useful. A nested root is an opaque consumer
child for its ancestor.

Consumer content owns its own order, identity, loading, editing, focus, form,
and collection behavior. The root does not clone, wrap, or reorder slot nodes.

## 7. Callbacks, native events, and methods

| Callback | Arguments | Trigger | Timing | Controlled behavior | Cancellation |
|---|---|---|---|---|---|
| `onScrollChange` | `(CScrollAreaScrollDetail)` | one or more actual native `scroll` events on the root viewport | at most once per animation frame using the latest event and normalized offsets at callback time | not controlled; browser offset is already committed | no semantic cancellation; callback return is ignored |

`CScrollAreaScrollDetail` is an immutable fresh event-scoped record with:

```python
class CScrollAreaScrollDetail(TypedDict):
    inlineOffset: float
    blockOffset: float
    source: object
```

| Field | Type | Meaning |
|---|---|---|
| `inlineOffset` | `float` | logical horizontal distance from inline start |
| `blockOffset` | `float` | vertical distance from top |
| `source` | `Event` | latest native `scroll` event coalesced into this frame |

The record describes the callback instant only. It is not a persistent edge or
overflow-state claim. Each native event stores the latest event and current
callback revision for the pending frame. A callback change or removal before
the frame increments that revision and cancels the pending old notification;
it does not redirect the event to a new callback. Any effective axis,
direction, scrollbar-width, scrollbar-gutter, or overscroll revision also cancels that pending
notification rather than mixing old-event and new-configuration geometry.
Before invocation and after callback entry, generated DOM writes require the
same connected root and controller generation. Root removal, morph, or
reentrant configuration cannot let stale work mutate or notify the next
instance. A callback exception follows the common Citry callback reporter and
does not roll back native scrolling.

Native listeners such as `@scroll`, `@scrollend`, `@focus`, `@blur`, `@wheel`,
and `@touchstart` belong in `attrs` and observe native events on the scroll root.
Like every Citry component root, that destination has an intentionally isolated
Alpine data stack. An attrs expression may use event magics such as `$event`,
`$store`, `$dispatch`, or an explicit global, but it cannot capture an ancestor
component-local identifier. Owner-local state therefore uses `onScrollChange`,
or a native attrs listener dispatches an application event to the ancestor.
The component dispatches no custom DOM event of its own. It installs no wheel,
touch, or keyboard listener and calls neither `preventDefault()` nor
`stopPropagation()` for scrolling. Native `@scroll` runs in ordinary event
dispatch before the component's animation-frame callback. Current target
browsers expose native `scrollend`; Citry forwards it through `attrs` and does
not debounce or polyfill it.

There are no public methods. Consumers needing app-specific scroll controls
may compose ordinary Buttons and use the stable root selector or a native DOM
reference to call `scrollBy()`/`scrollTo()`. Citry does not define a step,
hold-repeat, disabled state, label, focus policy, or callback for those
application controls in v1.

## 8. Semantics, keyboard, focus, and assistive technology

The root viewport is always `div[tabindex="0"]` in server output and after
activation. One valid naming input adds `role="region"` and exactly one of
`aria-label` or `aria-labelledby`. Both omitted leaves neither role nor naming
attribute. The server validation in section 4 applies; browser AX and axe must
prove the resolved name for every released `aria_labelledby` example. No other
semantic wrapper exists and `aria-orientation` is never emitted on the region.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| Forward Tab before root | `Tab` | browser enters the native viewport | root receives focus before focusable descendants | never |
| Reverse Tab after root | `Shift+Tab` | browser enters in reverse order | last naturally preceding focus stop according to native order | never |
| Focused viewport | Arrow, Page Up/Down, Home/End, Space, or platform scrolling keys | browser-native scroll behavior | focus remains viewport | never by component |
| Focused descendant | native key/pointer action | descendant behavior and native scroll-into-view apply | browser owns focus | never by component |
| Pointer, touch, wheel, or trackpad | platform gesture | native viewport scroll and overscroll policy apply | no component focus move | never by component |
| Nested viewport | Tab or native scrolling | inner and outer viewports remain independent; named instances are separate regions | no trap; normal DOM order | never by component |

Exact key availability and pixel increments are browser and platform behavior,
not Citry API. The component does not add Home/End handling. Native scrollbars
remain available for pointer users according to system settings. Citry adds no
visual edge-state substitute for the native scrollbar.

The root remains a Tab stop even when the slot contains focusable descendants.
That extra stop is deliberate: the three-engine probe showed implicit
scroll-container reachability changes by engine and descendant composition.
Consumers who do not want this deterministic focus contract should use plain
native overflow CSS instead of `CScrollArea`.

The viewport has an ordinary `:focus-visible` ring and
`scroll-padding: var(--cui-scroll-area-scroll-padding)`. Automated and manual
evidence must prove focused descendants are not clipped beyond ordinary native
scroll positioning. There is no live-region announcement because scrolling and
position are continuous native interaction, not a discrete status task.

## 9. Native forms and validation

`CScrollArea` is not a form participant. It has no `name`, value, `required`,
`readonly`, `disabled`, validation proxy, reset callback, Enter-submit rule, or
external `form` association.

Native and Citry form controls inside the default slot retain their own names,
values, validation, form owners, resets, autocomplete, Citry Events behavior,
and focus. A form reset may change native scroll extents but creates no
component state. The root's own focus stop does not submit a form and no
key event is intercepted.

## 10. Styling and theme contract

There are no variants, sizes, densities, or intents. Dimensions remain normal
CSS. The default block maximum size is a variable so the component is
useful immediately without imposing a dimension prop vocabulary.

The root uses `display: block`, `box-sizing: border-box`, `inline-size: 100%`,
and `min-inline-size: 0`. Vertical and both-axis roots use
`max-block-size: var(--cui-scroll-area-max-block-size)`; inline-only roots use
`max-block-size: none` and expand in the block direction. The axis values map
to `overflow-block` and `overflow-inline` as specified in section 5.
`scrollbar_gutter` maps to
`scrollbar-gutter: auto | stable | stable both-edges`; `scrollbar_width` maps to
the standard `scrollbar-width`; `overscroll` maps only on enabled logical axes;
and the whole-value scrollbar color variable maps directly to standard
`scrollbar-color`.
The private owned `scroll-behavior: auto !important` declaration is merged
after consumer style contributions. It is deliberately not a public variable
or customization point.
Consumer content must create its own nonwrapping or wide inline layout for
inline overflow. The root uses a solid border with the public width/color,
padding and radius variables. `:focus-visible` uses a 3px solid public focus
color with 2px offset; forced colors maps it to `Highlight`.

Public variables are exact:

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-scroll-area-max-block-size` | length or `none` | maximum block/both viewport size | `20rem` |
| `--cui-scroll-area-background` | color | root viewport background | `Canvas` |
| `--cui-scroll-area-foreground` | color | inherited foreground | `CanvasText` |
| `--cui-scroll-area-border-color` | color | root border | `color-mix(in srgb, currentColor 24%, transparent)` |
| `--cui-scroll-area-border-width` | length | root border width | `1px` |
| `--cui-scroll-area-radius` | length | root corner radius | `0.75rem` |
| `--cui-scroll-area-padding` | length | root content inset | `0px` |
| `--cui-scroll-area-scrollbar-color` | complete `scrollbar-color` value | standard native thumb and track colors as one property value | `auto` |
| `--cui-scroll-area-focus-color` | color | viewport focus-visible ring | `#2563eb` |
| `--cui-scroll-area-scroll-padding` | length | native focus/anchor scroll padding | `0px` |

Defaults resolve in the documented Citry component cascade layer through
private effective variables. Root values override ancestor values. Consumer
rules on public selectors may override presentation, but must not replace
owned layout, overflow, positioning, pointer-events, semantics, or visibility
rules.

Public selectors are exact:

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="scroll-area"]` | native focusable overflow root, border, colors, radius, sizing, and padding destination | all | exactly one component element |

Vendor scrollbar pseudo-elements are not public selectors. Public scrollbar
styling uses only the standard `scrollbar-width` and `scrollbar-color`
properties. Native scrollbar shape, minimum thumb, button presence, overlay
behavior, and exact gutter pixels remain user-agent and platform behavior.

Public reflected attributes are exact:

| Public reflected attribute | Values | Meaning |
|---|---|---|
| `data-axis` | `block \| inline \| both` | effective logical axis policy |
| `data-scrollbar-width` | `auto \| thin` | effective standard width policy |
| `data-scrollbar-gutter` | `auto \| stable \| stable-both-edges` | effective gutter policy |
| `data-overscroll` | `auto \| contain \| none` | effective CSS overscroll policy |

The private readiness marker is
`[data-citry-scroll-area-initialized]`. It is not a public styling or API
surface.

## 11. Environmental behavior

- `Canvas` and `CanvasText` follow light, dark, and nested `color-scheme`
  scopes. Public variables support brand adaptation without fixed palette
  assumptions.
- LTR and RTL use the normalized negative RTL model proved in all three
  engines. Dynamic direction changes preserve the cached logical distance from
  the new inline start.
- Only `writing-mode: horizontal-tb` is supported. Other computed writing
  modes retain usable native overflow but suspend normalized callbacks and
  repair work, remove readiness, and issue one diagnostic until repaired.
- Reduced motion changes nothing because the component creates no animation.
  The owned root behavior is always `scroll-behavior: auto !important`.
- Forced colors sets `forced-color-adjust: auto`, restores
  `scrollbar-color: auto`, and uses system border/focus colors. Native
  scrollbars remain visible.
- At 200 and 400 percent zoom, block is the default. Inline and both
  are used only for content whose meaning requires two dimensions. A wide
  table example proves a 320 CSS px viewport can reach every cell without
  page-level two-dimensional scrolling.
- Text spacing, long unbroken content, narrow and wide containers, coarse
  pointers, touch, trackpads, virtual keyboards, overlay scrollbars, and
  classic scrollbars retain native behavior. No fixed scrollbar-gutter pixel
  value is asserted.
- `overscroll="contain"` and `"none"` map to the CSS property on enabled
  logical axes. Citry does not promise that `auto` always chains or that either
  restrictive value changes every
  synthetic automation event. Real hardware/browser manual evidence covers
  wheel, trackpad, and touch behavior.
- Print sets `block-size: auto`, `max-block-size: none`, and
  `overflow: visible !important`; it removes component clipping, scrollbar
  constraints, and any border that impedes content. It does not promise that
  inline-wide content fits the finite page box. The application owns a print
  reflow, scaling rule, landscape page choice, or alternate table
  representation. Conditional region semantics may remain.

The component authors no visible string. `aria_label`, external label text,
and all slot copy belong to the application and its locale layer.

## 12. Overlay and layering behavior

Scroll Area never creates, opens, owns, anchors, or closes an overlay. It does
not register in the anchored-layer system, create a stacking context, set a
global z-index, lock page scroll, make siblings inert, or move focus.

The native viewport clips ordinary positioned descendants at its padding box.
Consumers must not place a non-top-layer dropdown, tooltip, menu, or dialog
inside the slot and expect it to escape. Native top-layer `dialog`/popover and
Citry overlay components retain their own supported host, ownership, focus,
and layering contracts. Scroll Area adds no visual overlay child and never
becomes a layer owner or outside-interaction boundary.

Nested Scroll Areas are ordinary nested native scroll containers. Named nested
regions require distinct useful labels; generic nested viewports remain
unnamed. The component never arbitrates which area receives a gesture; hit
testing, enabled-axis overflow, and browser overscroll behavior decide.

## 13. Collections, async data, and identity

Scroll Area is not a collection owner. It assigns no item keys, active item,
selection, disabled-item state, ordering, pagination, or virtualization.
Content DOM order is the reading, focus, and layout order. Menu, Listbox, Tree,
Table, and application collection semantics remain with their owners.

The default slot may change through Citry Events, fragments, image/media load,
or consumer DOM updates. Native layout and overflow react without component
measurement. The controller does not fetch, cancel, retry, cache, or announce
remote work. Empty, loading, error, and retry presentation are application
content.

## 14. Server render, morph, and cleanup

Server output is already useful: one focusable native root viewport with native
scrollbars, standard axis/scrollbar-gutter/overscroll styling, and content. A supplied
naming input emits the region/name pair; omission emits neither. JavaScript adds only
client configuration, normalized native-scroll callbacks, direction/morph
offset preservation, and owned-anatomy lifecycle repair.

One private pure geometry module owns `maximum`, raw-to-logical horizontal
conversion, logical-to-raw horizontal conversion, and clamping.
Before Scroll Area implementation is accepted, `CCarousel` must consume the
same horizontal conversion functions wherever it reads or writes horizontal
positions. Existing Carousel server and browser suites, including LTR/RTL,
snap selection, drag, controlled index, and cleanup, must pass unchanged.
Carousel's selection, snapping, hidden-bar, and drag code remains
family-specific. This extraction prevents a second RTL model without turning
Scroll Area into Carousel infrastructure.

Per initialized root the intended budget is:

- one passive native `scroll` listener on the root;
- one `MutationObserver` instance registered on root owned attributes and on
  each current composed ancestor for `dir`, `class`, `style`, and direct
  child-list move correlation, never on slot descendants or with subtree
  observation; and
- at most one pending animation frame shared by public callback coalescing and
  owned-write expiry, and no timer during steady-state scroll.

There is no ResizeObserver, content observer, captured load/font listener,
document-wide style observer, polling loop, or scrollend polyfill. The
implementation records observed ancestor count at 1/10/100 roots and must
disconnect every registration during owner-token cleanup.

The scroll handler batches reads before writes. Mutation repair ignores controller-owned
writes through a generation-local suppression record, not a time-only latch.
The anatomy guard checks retained root object identity, not only a selector
count, so a same-marker clone cannot inherit a live controller.

The morph compatibility fingerprint includes retained root object identity,
root ID, and component kind. Server axis, scrollbar-width, scrollbar-gutter,
overscroll, and naming are separate incoming baselines. A compatible
retained-root handoff preserves each valid client override, cached logical
inline/block offsets, and focus on that root. Descendant focus follows the
owning content and common Citry morph contract; Scroll Area never redirects it.
After incoming content and direction settle, offsets are converted and
clamped. Changed server configuration becomes the new fallback while a
still-valid client override continues to win. Morph restoration uses the
exact owned-write suppression transaction in section 5. The matching native
event updates the cache but produces no component callback; an intervening
unmatched event is handled normally.
A different root object, even with the same authored ID, is a fresh instance
and receives browser-native initial state. V1 does not claim cross-node scroll
restoration.

Old and new controllers use an owner token on the retained root. Cleanup may
remove readiness or observer registrations only when its token is still
current. Repeated init is idempotent. Remove/restore cycles and
root moves between a Document and open ShadowRoot rebuild ancestor observation
without multiplying work.

Cleanup disconnects every observer and listener, cancels the pending frame,
invalidates callbacks, and removes private readiness. It does not reset native
offsets, move focus, or modify consumer content. Closed or opaque descendant
shadow roots are ordinary native content outside the lifecycle contract.

## 15. Security and content trust

`aria_label` is escaped text and `aria_labelledby` is a validated IDREF list.
The default slot follows Citry's trusted component content boundary; Scroll
Area performs no raw-HTML insertion, URL loading, remote fetch, or expression
evaluation. Generated IDs use the common validated ID mechanism.

Attribute mappings are copied before rendering and never mutated. Exact owned
destinations are:

| Destination | Allowed | Rejected or component-owned |
|---|---|---|
| `attrs` on native root viewport | `class` and `style` contributions except the reserved effective `scroll-behavior`, `aria-describedby`, `aria-details`, `aria-keyshortcuts`, `lang`, `dir`, `title`, `translate`, `spellcheck`, ordinary `data-*` outside `data-citry-*`, and safe native Alpine listeners such as `@scroll`, `@scrollend`, `@focus`, `@blur`, `@wheel`, and touch/pointer listeners; listener expressions use the isolated component-root scope and therefore reach owner state only through `$store`, `$dispatch`, event magics, or explicit globals | `id`, `role`, `tabindex`, `aria-label`, `aria-labelledby`, every other `aria-*`, `hidden`, `inert`, `popover`, `contenteditable`, `is`, `slot`, `data-citry-*`, all part/reflection/readiness attributes, effective `scroll-behavior`, lifecycle directives `x-data`, `x-init`, `x-effect`, `x-id`, `x-if`, `x-for`, `x-show`, `x-teleport`, `x-ignore`, and object-form binding |

`attrs` class/style contributions are copied and merged with `class_`/`style`;
the explicit inputs merge after the mapping, and the private owned
`scroll-behavior: auto !important` declaration merges last. Root overflow,
scrollbar policy, focusability, semantics, and owned
relationships cannot be replaced through attributes. Consumer CSS can still
break layout; support applies only while the required anatomy and owned
property contract remain intact.

Synchronous server preflight rejects invalid or simultaneous naming inputs,
invalid IDs, enum values, attribute destinations, and collisions. Settled client validation
suspends enhancement
for hostile mutation, diagnoses once per invalid episode, repairs immutable
server baselines, and reactivates only after exact validation. Native scrolling
remains the fail-safe.

## 16. Assets and performance

The family adds one deduplicated CSS asset and one initializer asset only when
`CScrollArea` is rendered. It uses the shared component lifecycle/diagnostic
substrate and the shared horizontal geometry helper. It adds no icon, font,
image, network request, global wheel/touch/key handler, overlay runtime, or
collection runtime.

Release ceilings are measured as unique payload after only the universal
shared lifecycle base. The Scroll Area total includes its complete share of
the required geometry helper:

| Asset | Raw ceiling | Gzip ceiling | Brotli ceiling |
|---|---:|---:|---:|
| incremental JavaScript | 12 KiB | 3 KiB | 2.75 KiB |
| incremental CSS | 6 KiB | 1.5 KiB | 1.25 KiB |

Actual raw, gzip, and Brotli sizes must replace provisional measurements in
the implementation evidence without raising these ceilings. Asset evidence
reports the ScrollArea-only catalog delta separately and proves that the
geometry helper occurs exactly once for Carousel-only, ScrollArea-only,
Carousel-plus-ScrollArea, and 1, 10, and 100 Scroll Area instances.

Steady-state scroll performs one synchronous offset snapshot, schedules at
most one animation frame, batches callback geometry reads before any disabled-
axis repair write, and performs no DOM rebuild. The 100-instance scroll scenario must show no
component-authored long task over 16 ms on the repository reference browser.
Server render gates cover 1/10/100/500/1000 instances. Browser gates cover
1/10/100 roots, native content growth/shrink, nested roots, direction changes, and
remove/restore cycles with exact listener/observer accounting.

## 17. Acceptance matrix

| Area | Automated evidence | Manual evidence |
|---|---|---|
| Render and typing | exact six exports; template and Python composition render; generated/supplied root ID; empty content; type checks; API schema parity | public names and shortest-path review |
| Native mechanism | the single component root is the element whose `scrollTop`/`scrollLeft` and native scrollbars change; zero wrapper/track/thumb/corner nodes; zero wheel/touch/key listeners | platform scrollbar visibility and interaction on macOS overlay, Windows classic, and Linux where available |
| Axis policy | block/inline/both computed logical overflow; root class and inline style attempts to set smooth scrolling still compute to auto; disabled axis repaired to zero atomically after init, programmatic write plus resulting scroll, morph, direction change, and client change | touch and trackpad behavior on each axis |
| Focus and keyboard | explicit viewport `tabindex=0`; forward/reverse Tab order; native Page/Home/End smoke without pixel assertions; focus descendants at four edges; no trap | keyboard-only pass in Chromium, Firefox, WebKit, Safari, and platform screen reader/browser pairs |
| Accessible semantics | naming omitted has no role/name; either valid naming input creates the region/name pair in browser AX; invalid/simultaneous naming rejected; missing/duplicate external ID and empty target prove the documented consumer error without observer/runtime recovery; morph atomically changes role/name; released fixtures are axe clean | VoiceOver, NVDA, and JAWS generic-scroll and named-region navigation check |
| RTL | three-engine negative raw model converted to common event detail; dynamic LTR/RTL preserves cached logical distance; one shared helper used by Carousel | native bar direction |
| Native scroll callback | every detail field and clamp; latest native source; one call per active frame; no resize/content/config synthetic call; retained-root nonzero LTR/RTL morph and direction writes produce exactly zero component callbacks while matching native events update cache; unmatched/user event is not swallowed; three-engine timer-before-scroll falsifier and scroll-before-next-frame proof; one-frame suppression expiry, callback removal/reentrancy, and cleanup; native `@scroll`/`@scrollend` forwarding through `$store`, `$dispatch`, `$event`, and an explicit global; ancestor-local identifier is absent in the isolated attrs expression scope; no polyfill or component custom DOM event | callback example comprehension |
| Resize/content | grow, shrink, image load, absolute descendant movement, empty/repopulate, and stylesheet changes create no persistent component state or synthetic callback; next actual scroll reports current normalized offsets | late font/image and responsive container visual pass |
| Nested and overscroll | distinct optional region labels, computed auto/contain/none, no event interception, inner focus order | real mouse wheel, precision trackpad, and touch chaining/containment without cross-browser delivery promise |
| Styling | every variable at ancestor/root, the one public selector, auto/thin computed standard property, stable/both-edge gutter, light/dark/nested scheme, long content | design sign-off for native bars |
| Environment | forced colors, reduced motion, 200/400 percent zoom, 320 CSS px reflow, text spacing, coarse pointer, RTL, print removes component clipping; the wide-table fixture supplies an application print rule and proves its final column is visibly inside the printed page box | Windows High Contrast, touch, virtual keyboard, and print preview |
| Overlay boundary | ordinary positioned descendant clips; supported native/Citry top-layer overlay follows its own contract; no overlay child exists | overlay composition visual review |
| Forms | slotted control FormData, validation, reset, and focus unchanged | no added form stop or submit surprise |
| Lifecycle | SSR/no-JS useful; invalid owned attributes suspend; clone substitution cannot inherit ownership; retained-root same-baseline and changed-content morph; a replacement root starts fresh; Document/open ShadowRoot moves; repeated same-node and replacement-node remove/restore; owner-token cleanup | no flicker or focus jump during real Citry Events retained-root morph |
| Security | exact root attr allowlist rejects `is`, lifecycle directives, owned ID/role/ARIA/part/reflections; hostile mutation repairs | trust-boundary review |
| Performance/assets | helper-inclusive ScrollArea-only unique raw/gzip/Brotli after only universal lifecycle base; separate catalog delta; exactly one helper for Carousel-only, ScrollArea-only, both families, and 1/10/100 roots; observer/listener counts; 1/10/100/500/1000 server; 100-root scroll trace | reference-device smoothness |
| Packaging/host | family and package exports, wheel/sdist assets, Starlette host, docs host, standalone route, fragment insertion | installation smoke |

Focused browser evidence runs Chromium, Firefox, and WebKit for RTL, focus,
axis suppression, event-scoped callback, nested scrolling, print, morph, ShadowRoot,
and cleanup. Safari and assistive-technology checks remain manual release
evidence. Synthetic wheel results are not treated as proof of real hardware
chaining. The Python-owned scenario catalog supplies docs previews, standalone
routes, Playwright, axe, screenshots, performance, and manual tasks.

## 18. Compatibility classification

1. **Stable public API:** the six exports; server and client input names,
   types, defaults, validation, precedence, and release behavior; default slot;
   callback name/detail; public variables, selectors, reflections; optional
   naming semantics; no-method/no-controlled-offset boundary; error behavior.
2. **Behavioral and structural contract:** real native viewport and visible
   native bars; conditional role/name and unconditional tabindex; one-element
   root/viewport relationship; native keyboard/wheel/touch ownership;
   event-scoped normalized RTL detail;
   direction preservation; no-JavaScript output; nested, print, morph, and
   cleanup behavior.
3. **Evolvable design:** exact default colors, border, radius,
   and max size may improve while public variable meanings, usable contrast,
   native bars, and acceptance remain. User-visible changes need release notes.
4. **Private implementation:** `.cui-*` classes, `--_cui-*` variables,
   readiness marker, owner tokens, observer organization, frame coalescer,
   helper module/file layout, diagnostics wording, and incidental CSS rules.

Changing a stable name, meaning, default, callback field, semantic
relationship, or native-first boundary follows semantic-versioning and
deprecation policy. Public examples and tests use only listed stable surfaces.

## 19. Public documentation contract

The reader-first `api.md` begins with the native-first decision and explicitly
says when ordinary CSS is the better choice. `api.yml` exhaustively records
Inputs, Slots, Events, Methods (`-`), CSS, Attributes, Selectors, and Interfaces
with stable kebab-case IDs. Callback inputs are component events; Alpine
listeners are documented as native events. Native scrollbar pseudo-elements
are never listed as selectors.

The public example catalog is frozen as follows:

| Source module | Reader task and fixture | Visible states and controls | Environment profiles | Contract and focused browser evidence |
|---|---|---|---|---|
| `at_a_glance.py` | compare block-axis activity, inline metadata, and both-axis results in one neutral operations dashboard | native bars, named and unnamed examples | light/dark, narrow/wide | native viewport, three logical axes, conditional AX region/name, no replacement anatomy, axe |
| `activity_and_focus.py` | navigate a long activity stream containing links and Buttons | focused viewport and descendants, live event detail | keyboard, 400 percent zoom, long copy | Tab order, native keys without pixel promises, no obscured focus, callback detail |
| `wide_table.py` | inspect a semantic quarterly table that cannot reflow to one dimension | both-axis overflow, header/cell focus, application-owned print representation | 320 CSS px, RTL, print | G225/reflow exception, reachable cells, component clipping removed; fixture print rule proves final column visibly inside the page box |
| `configuration.py` | change axis, scrollbar width, scrollbar gutter, and overscroll from controls outside the subject | every server default and reactive override/release, invalid diagnostic fixture | overlay/classic scrollbar profiles where available | client precedence, reflections, computed CSS, disabled-axis zero repair |
| `rtl_and_direction.py` | compare equal LTR/RTL inline rails and flip direction while scrolled | logical offset readout produced by actual scrolling | LTR/RTL, long unbroken labels | negative raw model normalization, shared helper, preserved logical distance, one callback per scroll frame |
| `nested_areas.py` | work in an inner inspector inside an outer document viewport | named and generic instances, auto, contain, and none policies | narrow, touch/coarse pointer, RTL | nested focus, no trap, computed overscroll, no component event interception; manual real-device gestures |
| `native_callback.py` | change content size and an absolute descendant, then scroll | no notice for non-scroll changes; next native scroll shows current normalized offsets | slow image, stylesheet toggle, open ShadowRoot | event-scoped promise, no broad observer/polling, callback coalescing |
| `customization.py` | apply two brand treatments using only variables and public selectors | auto/thin bars, stable gutter, customized border | light/dark nested scheme, forced colors | variable precedence, selector stability, contrast, forced native colors |
| `overlay_boundary.py` | understand clipping and open a supported sibling/top-layer overlay from slotted content | clipped ordinary positioned sample plus supported overlay | narrow, scrolled start/end | truthful clipping boundary, independent overlay ownership, focus unaffected |
| `lifecycle.py` | preserve position through retained-root Citry Events morph and prove replacement scope | same-baseline, changed-content clamp, fresh replacement state, invalid/repaired attrs, unsupported/repaired writing mode | Document/open ShadowRoot, LTR-to-RTL | retained owner-token handoff/focus, clone substitution isolation, exact observer/listener cleanup |

The guide explains that built-in scroll buttons, custom scrollbar anatomy,
hidden bars, controlled position, virtualization, and vertical writing modes
are absent. It links the native CSS standards and shows ordinary CSS before
specialized examples. It does not market `overscroll="contain"` or `"none"` as
a universal event-delivery guarantee.

## 20. Open decisions and deferred work

There are no unresolved implementation or release decisions for v1.

Deferred work is intentionally outside the stable v1 API:

| Deferred work | Evidence required before a later design | Current disposition |
|---|---|---|
| custom track/thumb/corner | product need that standard native bars cannot satisfy, cross-browser pointer/keyboard/AT design, forced-colors and target-size proof | rejected from v1 |
| hidden scrollbar mode | user-tested alternative affordance and full keyboard/touch/AT proof | rejected from v1 |
| built-in scroll buttons | repeated application need plus exact step, hold-repeat, labels, disabled state, focus, RTL, reduced-motion, and nested behavior | compose app-specific controls |
| controlled or initial position and public methods | application ownership case that cannot use native DOM and survives SSR/morph/history semantics | omitted from v1 |
| vertical writing modes | three-engine raw-coordinate probes and a logical block/inline state model | unsupported; native fallback remains usable |
| scroll snapping, carousel selection, virtualization, or infinite loading | collection-specific identity, focus, loading, and performance design | separate component families |

Implementation begins only after an independent reviewer returns PASS with no
high or medium semantic, focus, RTL, lifecycle, trust, feasibility, source, or
acceptance finding against these frozen bytes.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
