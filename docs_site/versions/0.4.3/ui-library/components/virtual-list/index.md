---
title: Virtual List
url: https://citry.dev/v/0.4.3/ui-library/components/virtual-list/
description: "Defer off-screen rendering or supply a true server-rendered collection window with Citry UI."
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


### Keep a complete virtualized list

[Open the rendered preview](/v/0.4.3/ui-library/components/virtual-list/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class VirtualListAtAGlance(Component):
    template = """
      <c-CVirtualList aria_label="Build activity" c-estimated_item_size="64">
        <c-for each="entry in entries">
          <c-CVirtualListItem c-item_key="entry['key']">
            <article>
              <strong>{{ entry['title'] }}</strong><br />
              <small>{{ entry['detail'] }}</small>
            </article>
          </c-CVirtualListItem>
        </c-for>
      </c-CVirtualList>
    """
    css = """
      :where([data-citry-ui-part="virtual-list"] article) {
        padding: 0.75rem 1rem;
        border-block-end: 1px solid color-mix(in srgb, currentColor 14%, transparent);
      }
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "entries": [
                {"key": f"build-{index}", "title": f"Build {2400 + index}", "detail": "Checks passed"}
                for index in range(80)
            ]
        }


preview = VirtualListAtAGlance()
preview  # noqa: B018
````


Choose an `estimated_item_size` close to the average rendered block size. It
is a browser layout hint, not a fixed height; rich Items may still wrap and
grow. Stable `item_key` values preserve logical identity across server renders.

## Supply a true DOM window

`CVirtualWindow` renders only the contiguous range supplied by the current
server output. `total_count`, `start_index`, and `item_size` reserve the full
scroll extent. The direct `CVirtualListItem` declarations are the committed
range beginning at `start_index`.


### Supply a fixed server window

[Open the rendered preview](/v/0.4.3/ui-library/components/virtual-list/_previews/windowed/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class VirtualWindowExample(Component):
    template = """
      <section x-data="{last:'This static preview supplies one complete window'}">
        <output x-text="last">This static preview supplies one complete window</output>
        <c-CVirtualWindow
          aria_label="Audit records"
          c-total_count="16"
          c-item_size="48"
          $c-props="{onRangeChange:(detail)=>last=`Requested ${detail.startIndex}-${detail.endIndex - 1}`}"
        >
          <c-for each="record in records">
            <c-CVirtualListItem c-item_key="record['key']">
              <span>{{ record['number'] }}</span> {{ record['label'] }}
            </c-CVirtualListItem>
          </c-for>
        </c-CVirtualWindow>
      </section>
    """
    css = """
      :where([data-citry-ui-part="item"]) {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding-inline: 1rem;
        border-block-end: 1px solid color-mix(in srgb, currentColor 12%, transparent);
      }
      :where([data-citry-ui-part="item"] > span) { color: GrayText; font-variant-numeric: tabular-nums; }
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "records": [
                {"key": f"audit-{index}", "number": f"#{index + 1:05d}", "label": "Signed deployment record"}
                for index in range(16)
            ]
        }


preview = VirtualWindowExample()
preview  # noqa: B018
````


Pass `onRangeChange` through `$c-props`. The callback receives the desired
overscanned half-open range, visible range, request ID, reason, and source
event. It requests state; it never mutates or renders Item HTML. Fetch or
render the new range, cancel superseded work in the application, and replace
the component with the new `start_index` and Items.

The static documentation examples use a small self-contained range with no
omitted leading or trailing Items. They therefore never expose scrollable
blank space that a static page cannot replace. A real partial range reserves
blank geometry only while the server request is pending; the owner must replace
it when `onRangeChange` fires.

The runtime marks the root `aria-busy="true"` and `data-pending` until the
committed server range covers the current desired range. A missing callback
leaves the current range usable. Callback failures are isolated and logged.

## Keep window rows fixed

Every `CVirtualWindow` Item must occupy exactly `item_size` CSS pixels in the
block axis. The component clips overflow to keep spacer geometry correct.
Use bounded internal layout, truncation, or a larger row size; do not use a
window for variable-height articles. The total scroll extent is limited to
16,000,000 CSS pixels because browser element-size limits are not portable.


### Tune range geometry

[Open the rendered preview](/v/0.4.3/ui-library/components/virtual-list/_previews/controlled/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class VirtualWindowControlled(Component):
    template = """
      <section x-data="{itemSize:56,overscan:2,last:'No request'}">
        <label>Row size <input type="range" min="40" max="72" x-model.number="itemSize" /></label>
        <label>Overscan <input type="range" min="0" max="8" x-model.number="overscan" /></label>
        <output x-text="last">No request</output>
        <c-CVirtualWindow
          aria_label="Controlled geometry"
          c-total_count="12"
          c-item_size="56"
          c-viewport_size="280"
          $c-props="{
            itemSize,
            overscan,
            onRangeChange:(detail)=>last=`${detail.reason}: ${detail.startIndex}-${detail.endIndex - 1}`,
          }"
        >
          <c-for each="index in indexes">
            <c-CVirtualListItem c-item_key="f'controlled-{index}'">Record {{ index + 1 }}</c-CVirtualListItem>
          </c-for>
        </c-CVirtualWindow>
      </section>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"indexes": list(range(12))}

    css = """
      :where([data-citry-ui-part="item"]) { display:flex;align-items:center;padding-inline:1rem; }
      :where(label) { display:inline-flex;gap:0.5rem;margin-inline-end:1rem; }
      :where(output) { display:block;margin-block:0.5rem; }
    """


preview = VirtualWindowControlled()
preview  # noqa: B018
````


`overscan` and `itemSize` are reactive client inputs. A valid Alpine change
recomputes the requested range immediately. Invalid values log one diagnostic
per episode and retain the previous valid value. Use a server render when the
committed range or total count changes.

## Accessibility and focus

Both owners render `role="list"` and `CVirtualListItem` renders
`role="listitem"`. A Window Item also receives exact `aria-posinset` and
`aria-setsize`; spacers are hidden from assistive technology. `focusable=True`
adds one viewport tab stop so keyboard users can scroll even when Items contain
no controls. Use `focusable=False` only when the supplied Items contain a
keyboard-reachable control that lets keyboard users enter and scroll the
viewport. A scrollable region with neither a root tab stop nor a focusable
descendant is not keyboard accessible.


### Compare complete and windowed semantics

[Open the rendered preview](/v/0.4.3/ui-library/components/virtual-list/_previews/accessibility/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class VirtualListAccessibility(Component):
    template = """
      <c-CCol>
        <section>
          <h2>Complete collection</h2>
          <c-CVirtualList aria_label="All release notes" c-viewport_size="220">
            <c-for each="index in complete_indexes">
              <c-CVirtualListItem c-item_key="f'complete-{index}'">
                <a c-href="f'#release-{index + 1}'">Release {{ index + 1 }}</a>
              </c-CVirtualListItem>
            </c-for>
          </c-CVirtualList>
        </section>
        <section>
          <h2>Supplied range</h2>
          <c-CVirtualWindow
            aria_label="Windowed release notes"
            c-total_count="8"
            c-item_size="44"
            c-viewport_size="220"
          >
            <c-for each="index in window_indexes">
              <c-CVirtualListItem c-item_key="f'window-{index}'">Release {{ index + 1 }}</c-CVirtualListItem>
            </c-for>
          </c-CVirtualWindow>
        </section>
      </c-CCol>
    """
    css = """
      :where([data-citry-ui-part="item"]) {
        display:flex;align-items:center;padding-inline:0.75rem;min-block-size:44px;
      }
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"complete_indexes": list(range(16)), "window_indexes": list(range(8))}


preview = VirtualListAccessibility()
preview  # noqa: B018
````


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


### Customize Virtual List

[Open the rendered preview](/v/0.4.3/ui-library/components/virtual-list/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class VirtualListCustomization(Component):
    template = """
      <c-CVirtualList aria_label="Pinned environments" class_="environment-list" c-viewport_size="260">
        <c-for each="environment in environments">
          <c-CVirtualListItem c-item_key="environment['key']">
            <strong>{{ environment['name'] }}</strong>
            <span>{{ environment['region'] }}</span>
          </c-CVirtualListItem>
        </c-for>
      </c-CVirtualList>
    """
    css = """
      :where(.environment-list) {
        --cui-virtual-list-border: 2px solid #7c3aed;
        --cui-virtual-list-radius: 1rem;
        --cui-virtual-list-background: light-dark(#faf5ff, #2e1065);
        --cui-virtual-list-item-background: light-dark(#fff, #1e1b4b);
      }
      :where(.environment-list [data-citry-ui-part="item"]) {
        display:grid;
        grid-template-columns:1fr auto;
        gap:1rem;
        padding:0.875rem 1rem;
        margin:0.5rem;
        border-radius:0.625rem;
      }
      :where(.environment-list [data-citry-ui-part="item"] span) { color:GrayText; }
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "environments": [
                {"key": f"environment-{index}", "name": f"Service {index + 1}", "region": "eu-central"}
                for index in range(24)
            ]
        }


preview = VirtualListCustomization()
preview  # noqa: B018
````


For print, `CVirtualList` expands and makes all Items visible. A
`CVirtualWindow` can print only its supplied range; render a separate complete
or paginated print view when the full collection matters.

## Localization

The family owns no visible or accessibility text, announcements, parsing,
formatting, filtering, sorting, or comparison. Localize `aria_label` and Item
content in the application. The family therefore has no Citry UI catalog keys.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CVirtualList server inputs

Server inputs are passed in a template through `<c-CVirtualList ... />` or in Python through
`CVirtualList(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="virtual-list-input-cvirtual-list-server-inputs-aria-label"></span>`aria_label` | `str | None` | `None` | Optionally names the complete-DOM list. |
| <span id="virtual-list-input-cvirtual-list-server-inputs-estimated-item-size"></span>`estimated_item_size` | `int` | `48` | Sets the positive pixel intrinsic-size estimate used while off-screen Item rendering is skipped. |
| <span id="virtual-list-input-cvirtual-list-server-inputs-viewport-size"></span>`viewport_size` | `int` | `400` | Sets the positive initial viewport block size in CSS pixels. |
| <span id="virtual-list-input-cvirtual-list-server-inputs-focusable"></span>`focusable` | `bool` | `True` | Adds or removes the root tabindex=0 keyboard-scroll stop. False requires a keyboard-reachable control inside the supplied Items. |
| <span id="virtual-list-input-cvirtual-list-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#virtual-list-interface-class-value)) | `None` | Adds classes to the list viewport. |
| <span id="virtual-list-input-cvirtual-list-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#virtual-list-interface-style-value)) | `None` | Adds styles before owned viewport geometry variables. |
| <span id="virtual-list-input-cvirtual-list-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed viewport attributes without replacing owned roles geometry state or runtime markers. |

</div>

#### CVirtualWindow server inputs

Server inputs are passed in a template through `<c-CVirtualWindow ... />` or in Python
through `CVirtualWindow(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="virtual-list-input-cvirtual-window-server-inputs-total-count"></span>`total_count` | `int` | required | Sets the exact nonnegative logical collection size. |
| <span id="virtual-list-input-cvirtual-window-server-inputs-start-index"></span>`start_index` | `int` | `0` | Sets the nonnegative logical index of the first supplied Item. |
| <span id="virtual-list-input-cvirtual-window-server-inputs-item-size"></span>`item_size` | `int` | `48` | Sets the positive fixed Item stride in CSS pixels; total extent cannot exceed 16000000 pixels. |
| <span id="virtual-list-input-cvirtual-window-server-inputs-viewport-size"></span>`viewport_size` | `int` | `400` | Sets the positive initial viewport block size in CSS pixels. |
| <span id="virtual-list-input-cvirtual-window-server-inputs-overscan"></span>`overscan` | `int` | `3` | Requests zero through one hundred Items before and after the visible range. |
| <span id="virtual-list-input-cvirtual-window-server-inputs-initial-index"></span>`initial_index` | `int` | `0` | Sets the one-shot nonnegative initial scroll index and clamps it to the collection. |
| <span id="virtual-list-input-cvirtual-window-server-inputs-aria-label"></span>`aria_label` | `str | None` | `None` | Optionally names the windowed list. |
| <span id="virtual-list-input-cvirtual-window-server-inputs-focusable"></span>`focusable` | `bool` | `True` | Adds or removes the root tabindex=0 keyboard-scroll stop. False requires a keyboard-reachable control inside the supplied Items. |
| <span id="virtual-list-input-cvirtual-window-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#virtual-list-interface-class-value)) | `None` | Adds classes to the Window viewport. |
| <span id="virtual-list-input-cvirtual-window-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#virtual-list-interface-style-value)) | `None` | Adds styles before owned viewport geometry variables. |
| <span id="virtual-list-input-cvirtual-window-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed viewport attributes without replacing owned roles geometry state or runtime markers. |

</div>

#### CVirtualWindow client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CVirtualWindow />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 10rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="virtual-list-input-cvirtual-window-client-inputs-overscan"></span>`overscan` | `int` | Uses the server value; null is invalid and retains the last valid value. | Reactively changes the requested buffer from zero through one hundred Items. |
| <span id="virtual-list-input-cvirtual-window-client-inputs-item-size"></span>`itemSize` | `number` | Uses the server value; null is invalid and retains the last valid value. | Reactively changes fixed pixel geometry while the resulting total extent stays within the family limit. |
| <span id="virtual-list-input-cvirtual-window-client-inputs-on-range-change"></span>`onRangeChange` | `function` | Omission or null selects no component callback. | Receives newest distinct range requests without committing server state. |

</div>

#### CVirtualListItem server inputs

Server inputs are passed in a template through `<c-CVirtualListItem ... />` or in Python
through `CVirtualListItem(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="virtual-list-input-cvirtual-list-item-server-inputs-item-key"></span>`item_key` | `str` | required | Supplies nonempty stable identity unique within the owning logical collection or supplied range. |
| <span id="virtual-list-input-cvirtual-list-item-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#virtual-list-interface-class-value)) | `None` | Adds classes to the rendered list Item. |
| <span id="virtual-list-input-cvirtual-list-item-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#virtual-list-interface-style-value)) | `None` | Adds styles to the Item; Window fixed block size remains owned. |
| <span id="virtual-list-input-cvirtual-list-item-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed Item attributes without replacing owned roles positions identity or runtime markers. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CVirtualList slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="virtual-list-slot-cvirtual-list-slots-default"></span>`default` | no | `{}` ([`CVirtualListDefaultSlotData`](#virtual-list-interface-cvirtual-list-default-slot-data)) | Empty list; accepts only CVirtualListItem declarations. |

</div>

#### CVirtualWindow slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="virtual-list-slot-cvirtual-window-slots-default"></span>`default` | no | `{}` ([`CVirtualListDefaultSlotData`](#virtual-list-interface-cvirtual-list-default-slot-data)) | Empty supplied range; accepts only CVirtualListItem declarations. |

</div>

#### CVirtualListItem slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="virtual-list-slot-cvirtual-list-item-slots-default"></span>`default` | yes | `{index, item_key, set_size, strategy}` ([`CVirtualListItemDefaultSlotData`](#virtual-list-interface-cvirtual-list-item-default-slot-data)) | None. |

</div>

### Events

Component events are callback inputs supplied through `$c-props`. Native browser events
remain available through Alpine `@...` attributes.

#### CVirtualWindow events

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 13rem; --ui-api-column-4-width: 11rem">

| Event | Signature | Trigger and timing | Detail | Controlled and cancellation behavior |
|---|---|---|---|---|
| <span id="virtual-list-event-cvirtual-window-events-range-change"></span>`onRangeChange` | `(detail: CVirtualListRangeChangeDetail) => void` ([`CVirtualListRangeChangeDetail`](#virtual-list-interface-cvirtual-list-range-change-detail)) | The visible overscanned range is not covered by the committed server range. | `{startIndex, endIndex, visibleStartIndex, visibleEndIndex, requestId, reason, sourceEvent}` ([`CVirtualListRangeChangeDetail`](#virtual-list-interface-cvirtual-list-range-change-detail)) | Animation-frame-coalesced request only. The application supplies a new server range and owns cancellation supersession loading error and retry. |

</div>

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CVirtualList CSS variables

Apply these variables to `CVirtualList` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="virtual-list-css-cvirtual-list-css-variables-viewport-size"></span>`--cui-virtual-list-viewport-size` | `length` | Viewport block size read by both root owners. | `Server viewport_size; 400px` |
| <span id="virtual-list-css-cvirtual-list-css-variables-item-size"></span>`--cui-virtual-list-item-size` | `length` | Complete-DOM intrinsic estimate or owned Window Item stride. | `Server estimate or item_size; 48px` |
| <span id="virtual-list-css-cvirtual-list-css-variables-border"></span>`--cui-virtual-list-border` | `complete border value` | Viewport border. | `Adaptive 1px solid neutral` |
| <span id="virtual-list-css-cvirtual-list-css-variables-radius"></span>`--cui-virtual-list-radius` | `length` | Viewport corner radius. | `0.625rem` |
| <span id="virtual-list-css-cvirtual-list-css-variables-background"></span>`--cui-virtual-list-background` | `color` | Viewport background. | `Canvas` |
| <span id="virtual-list-css-cvirtual-list-css-variables-item-background"></span>`--cui-virtual-list-item-background` | `color` | Item background. | `transparent` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CVirtualList attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="virtual-list-attribute-cvirtual-list-root-attributes-role"></span>`role` | Root viewport div | `list` | Exposes noninteractive list semantics. |
| <span id="virtual-list-attribute-cvirtual-list-root-attributes-aria-label"></span>`aria-label` | Root viewport div | `string | absent` | Optional application-localized list name. |
| <span id="virtual-list-attribute-cvirtual-list-root-attributes-tabindex"></span>`tabindex` | Root viewport div | `0 | absent` | Adds keyboard-scroll focus when focusable is true. |
| <span id="virtual-list-attribute-cvirtual-list-root-attributes-data-strategy"></span>`data-strategy` | Root viewport div | `content-visibility` | Identifies complete-DOM containment behavior. |

</div>

#### CVirtualWindow attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="virtual-list-attribute-cvirtual-window-root-attributes-role"></span>`role` | Root viewport div | `list` | Exposes noninteractive list semantics. |
| <span id="virtual-list-attribute-cvirtual-window-root-attributes-aria-label"></span>`aria-label` | Root viewport div | `string | absent` | Optional application-localized list name. |
| <span id="virtual-list-attribute-cvirtual-window-root-attributes-aria-busy"></span>`aria-busy` | Root viewport div | `true | absent` | Present while the current desired range is not covered. |
| <span id="virtual-list-attribute-cvirtual-window-root-attributes-tabindex"></span>`tabindex` | Root viewport div | `0 | absent` | Adds keyboard-scroll focus when focusable is true. |
| <span id="virtual-list-attribute-cvirtual-window-root-attributes-data-strategy"></span>`data-strategy` | Root viewport div | `window` | Identifies true controlled window behavior. |
| <span id="virtual-list-attribute-cvirtual-window-root-attributes-data-pending"></span>`data-pending` | Root viewport div | `present | absent` | Mirrors an uncovered desired range. |
| <span id="virtual-list-attribute-cvirtual-window-root-attributes-data-start-index"></span>`data-start-index` | Root viewport div | `nonnegative-integer-string` | Mirrors the committed server range start. |
| <span id="virtual-list-attribute-cvirtual-window-root-attributes-data-total-count"></span>`data-total-count` | Root viewport div | `nonnegative-integer-string` | Mirrors logical collection size. |

</div>

#### CVirtualListItem attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="virtual-list-attribute-cvirtual-list-item-attributes-role"></span>`role` | Item div | `listitem` | Exposes one noninteractive list item. |
| <span id="virtual-list-attribute-cvirtual-list-item-attributes-data-index"></span>`data-index` | Item div | `nonnegative-integer-string` | Exposes settled logical zero-based position. |
| <span id="virtual-list-attribute-cvirtual-list-item-attributes-data-item-key"></span>`data-item-key` | Item div | `string` | Exposes stable server identity. |
| <span id="virtual-list-attribute-cvirtual-list-item-attributes-aria-posinset"></span>`aria-posinset` | Window Item div | `positive-integer-string | absent` | Exposes one-based logical position only in CVirtualWindow. |
| <span id="virtual-list-attribute-cvirtual-list-item-attributes-aria-setsize"></span>`aria-setsize` | Window Item div | `nonnegative-integer-string | absent` | Exposes total logical size only in CVirtualWindow. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CVirtualList selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="virtual-list-selector-cvirtual-list-selectors-virtual-list"></span>`[data-citry-ui-part="virtual-list"]` | Root viewport div | Root attrs and viewport customization destination for both owners. |
| <span id="virtual-list-selector-cvirtual-list-selectors-track"></span>`[data-citry-ui-part="track"]` | Direct track div | Contains spacers and supplied Items. |
| <span id="virtual-list-selector-cvirtual-list-selectors-item"></span>`[data-citry-ui-part="item"]` | Item div | Stable Item attrs content and customization destination. |
| <span id="virtual-list-selector-cvirtual-list-selectors-spacer"></span>`[data-citry-ui-part="spacer"]` | Window-only aria-hidden div | Reserves omitted range space; geometry is owned. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="virtual-list-interface-strategy"></span>`CVirtualListStrategy` | `Literal["content-visibility", "window"]` |
| <span id="virtual-list-interface-range-reason"></span>`CVirtualListRangeReason` | `Literal["initial", "scroll", "resize", "configuration"]` |
| <span id="virtual-list-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="virtual-list-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="virtual-list-interface-cvirtual-list-default-slot-data"></span>

#### `CVirtualListDefaultSlotData`

Empty dataclass: `{}`.

<span id="virtual-list-interface-cvirtual-list-item-default-slot-data"></span>

#### `CVirtualListItemDefaultSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="virtual-list-interface-cvirtual-list-item-default-slot-data-index"></span>`index` | `int` | - | Settled logical zero-based Item position. |
| <span id="virtual-list-interface-cvirtual-list-item-default-slot-data-item-key"></span>`item_key` | `str` | - | Stable authored Item identity. |
| <span id="virtual-list-interface-cvirtual-list-item-default-slot-data-set-size"></span>`set_size` | `int` | - | Complete declaration count or Window total_count. |
| <span id="virtual-list-interface-cvirtual-list-item-default-slot-data-strategy"></span>`strategy` | `CVirtualListStrategy` ([`CVirtualListStrategy`](#virtual-list-interface-strategy)) | - | Identifies the owning complete-DOM or Window behavior. |

</div>

<span id="virtual-list-interface-cvirtual-list-range-change-detail"></span>

#### `CVirtualListRangeChangeDetail`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="virtual-list-interface-cvirtual-list-range-change-detail-start-index"></span>`startIndex` | `int` | - | Inclusive requested overscanned range start. |
| <span id="virtual-list-interface-cvirtual-list-range-change-detail-end-index"></span>`endIndex` | `int` | - | Exclusive requested overscanned range end. |
| <span id="virtual-list-interface-cvirtual-list-range-change-detail-visible-start-index"></span>`visibleStartIndex` | `int` | - | Inclusive geometrically visible range start. |
| <span id="virtual-list-interface-cvirtual-list-range-change-detail-visible-end-index"></span>`visibleEndIndex` | `int` | - | Exclusive geometrically visible range end. |
| <span id="virtual-list-interface-cvirtual-list-range-change-detail-request-id"></span>`requestId` | `int` | - | Monotonically increasing instance-local request identifier. |
| <span id="virtual-list-interface-cvirtual-list-range-change-detail-reason"></span>`reason` | `CVirtualListRangeReason` ([`CVirtualListRangeReason`](#virtual-list-interface-range-reason)) | - | Geometry trigger that scheduled the latest request frame. |
| <span id="virtual-list-interface-cvirtual-list-range-change-detail-source-event"></span>`sourceEvent` | `Event | null` | - | Latest native scroll event when reason is scroll; otherwise null. |

</div>

### Translation keys

-