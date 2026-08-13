---
title: ScrollArea
description: Keep bounded content reachable through native scrolling.
---

# ScrollArea

Use `CScrollArea` when bounded content needs a consistent focus stop, optional
region name, logical-axis policy, normalized scroll callback, or retained-root
lifecycle behavior. The component renders one native scrolling `div`. The
browser still owns its scrollbar, wheel, touch, trackpad, and keyboard behavior.

Use ordinary CSS when `overflow: auto` is enough. ScrollArea does not replace
native scrollbars or add track, thumb, corner, edge-shadow, or scroll-button
elements.

## Start with one native viewport

The default slot is transparent. It adds no content wrapper and does not change
the semantics, focus order, or layout of its children.

```citry-html
<c-CScrollArea aria_label="Recent activity">
  <ol>
    <li>Import completed</li>
    <li>Review requested</li>
    <li>Release approved</li>
  </ol>
</c-CScrollArea>
```

When `aria_label` or `aria_labelledby` is supplied, the viewport becomes a
named region. Omit both for a generic focusable viewport. The two inputs are
mutually exclusive.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cscroll_area/snippets/at_a_glance.py" title="Block, inline, and two-axis native scrolling" />

## Enter the viewport with the keyboard

The viewport always has `tabindex="0"` and a visible focus ring. Native Page,
Home, End, Space, arrow, wheel, and touch behavior stays with the browser, so
exact keys and pixel increments can differ by platform. Focusable children keep
their ordinary Tab order. ScrollArea never traps or moves focus.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cscroll_area/snippets/activity_and_focus.py" title="Viewport and descendant focus" />

Do not attach a root key handler to reproduce native scrolling. It can consume
Home, End, or arrow keys intended for an input or another interactive child.

## Keep wide data semantic

Use `axis="both"` for a table or other surface whose meaning requires two
dimensions. The slotted Table keeps its own caption, headers, cells, and focus
behavior. ScrollArea only supplies the bounded native viewport.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cscroll_area/snippets/wide_table.py" title="A semantic table at narrow width" />

At 400 percent zoom, prefer block flow unless two-dimensional content is
essential. In print, ScrollArea removes its own maximum size, border, and
overflow clipping. An application must still reflow, scale, rotate, or replace
content that is wider than the physical page.

## Change native overflow policy

`axis` accepts logical `block`, `inline`, or `both`. `scrollbar_width` accepts
`auto` or `thin`. `scrollbar_gutter` accepts `auto`, `stable`, or
`stable-both-edges`. Native scrollbar thickness, overlay behavior, and gutter
pixels remain browser and operating-system choices.

`overscroll="contain"` limits native scroll chaining on enabled axes, while
`none` also requests suppression of local boundary effects. These are CSS
policies, not promises that every browser, device, or synthetic event delivers
the same gesture behavior.

The policies follow [CSS Overflow](https://drafts.csswg.org/css-overflow/),
[CSS Scrollbars](https://drafts.csswg.org/css-scrollbars/), and
[CSS Overscroll Behavior](https://drafts.csswg.org/css-overscroll-1/).

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cscroll_area/snippets/configuration.py" title="Reactive axis and scrollbar policy" />

Client `axis`, `scrollbarWidth`, `scrollbarGutter`, and `overscroll` values win
field by field. `null` or omission releases one field to its latest server
fallback. An invalid value keeps the last valid effective value and reports one
diagnostic for that invalid episode.

The root owns instantaneous `scroll-behavior: auto` for direction, disabled-axis,
and morph repair. An application can still request a smooth native movement in
an explicit `scrollTo()` call, but it cannot replace the root's computed CSS
policy.

## Read logical RTL offsets

`onScrollChange` receives logical distance from inline start and block distance
from the top. RTL callers do not need to interpret a negative browser
`scrollLeft`. The detail describes the callback instant only and does not claim
persistent edge or progress state.

Raw viewport geometry and native events follow
[CSSOM View](https://drafts.csswg.org/cssom-view/).

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cscroll_area/snippets/rtl_and_direction.py" title="LTR and RTL logical offsets" />

A direction change preserves the last cached logical distance when the same
root remains connected. Stylesheet-only direction changes are reconciled at
the next native scroll, configuration update, or Citry morph settlement.
Vertical writing modes keep usable native overflow but suspend normalized
callbacks and lifecycle repair.

## Nest independent scrolling regions

Nested ScrollAreas remain ordinary nested native scroll containers. The
browser decides which area receives a gesture. Give nested named regions
distinct useful names, and leave incidental regions unnamed.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cscroll_area/snippets/nested_areas.py" title="Nested regions and overscroll policy" />

## Distinguish the component callback from native events

`onScrollChange` is a semantic component callback supplied through `$c-props`.
It runs at most once per animation frame after one or more actual native
`scroll` events. It receives the latest native event as `detail.source`.
Content resize, image load, configuration changes, and component-owned repairs
do not create this callback.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cscroll_area/snippets/native_callback.py" title="Event-scoped logical scroll details" />

Native root events remain Alpine listeners in `attrs`:

```citry-html
<section
  x-data="{nativeCount:0,settled:false,last:0}"
  @build-log-scroll="nativeCount += 1"
  @build-log-settled="settled = true"
>
  <c-CScrollArea
    aria_label="Build log"
    c-attrs="{
      '@scroll':'$dispatch(`build-log-scroll`)',
      '@scrollend':'$dispatch(`build-log-settled`)',
    }"
    $c-props="{onScrollChange:(detail)=>last=detail.blockOffset}"
  >
    ...
  </c-CScrollArea>
</section>
```

Native listeners observe every browser event, including an event produced by
component-owned coordinate repair. ScrollArea dispatches no custom DOM event
and exposes no public method. A listener on a component root has Citry's
isolated component scope, so it cannot read ancestor-local `x-data` identifiers
directly. Use `$event`, `$dispatch`, `$store`, or another explicit global bridge;
use `onScrollChange` for owner-local callback state. Application controls can
use an ordinary DOM ref and the native `scrollTo()` or `scrollBy()` method.

## Customize standards-based styling

Public variables control the viewport's size, colors, border, radius, padding,
focus ring, scroll padding, and complete standard `scrollbar-color` value. The
one stable selector targets the same native viewport.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cscroll_area/snippets/customization.py" title="Public variables and the viewport selector" />

Citry uses `scrollbar-width`, `scrollbar-color`, and `scrollbar-gutter`. Vendor
scrollbar pseudo-elements are not public API. Forced colors restore platform
scrollbar, border, and focus colors. Unlayered application rules override the
Citry UI theme layer whether loaded before or after the component stylesheet.
A named application layer must be ordered after `citry-ui.theme`.

## Respect the clipping boundary

Native overflow clips ordinary positioned descendants. A dropdown, tooltip,
or menu cannot escape merely because it appears in the default slot. Compose a
supported Citry overlay or native top-layer element whose own contract defines
its host, focus, and layering.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cscroll_area/snippets/overlay_boundary.py" title="Clipped content and an independently owned overlay" />

ScrollArea does not register as an overlay owner, lock page scroll, make
siblings inert, or create a stacking context.

## Preserve only a retained root

A correlated Citry morph that retains the same root preserves valid client
configuration, cached logical position, and focus on that root. Incoming
server values become new fallbacks for fields without client ownership.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cscroll_area/snippets/lifecycle.py" title="Retained-root morph and replacement scope" />

A replacement root, even with the same authored ID, starts with native browser
position. Removal cancels pending callbacks and lifecycle work. Restoring a new
root does not inherit the removed instance's offsets or focus.

## Keep the native fallback useful

Without JavaScript, server output is already one focusable native viewport
with its configured axis, standard scrollbar, gutter, overscroll, colors, and
slot content. A supplied name already emits the region and naming attribute.
Client enhancement only adds reactive configuration, normalized callbacks,
direction repair, and retained-root lifecycle behavior.

## Treat root attributes as trusted configuration

`class_`, `style`, and `attrs` all target the native viewport. `attrs` accepts
ordinary descriptive attributes, `dir`, language hints, nonreserved `data-*`,
and native Alpine event listeners that respect the isolated scope boundary. It
rejects values that replace the root ID, role, focusability, region name, part
marker, reflected state, lifecycle, or owned scrolling policy.

Slotted text and components follow Citry's normal trusted content boundary.
ScrollArea does not evaluate content as HTML, URLs, selectors, or Alpine
expressions.

<!-- UI_LIBRARY_API_REFERENCE -->
