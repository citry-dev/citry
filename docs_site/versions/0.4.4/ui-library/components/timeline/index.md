---
title: Timeline
url: https://citry.dev/v/0.4.4/ui-library/components/timeline/
description: "Present histories, activity, milestones, and status sequences with Citry UI."
---
# Timeline

Use `CTimeline` and `CTimelineItem` for ordered histories, activity feeds,
roadmaps, and status sequences. Timeline is presentational: links, actions,
loading, and date formatting remain owned by your application.

## Timeline at a glance


### Timeline at a glance

[Open the rendered preview](/v/0.4.4/ui-library/components/timeline/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimelineAtAGlance(Component):
    template = """
      <c-CTimeline label="Shipment progress">
        <c-CTimelineItem state="complete">
          <c-fill name="opposite"><time datetime="2026-08-18">18 Aug</time></c-fill>
          <c-fill name="default"><strong>Order confirmed</strong><br />Payment received</c-fill>
        </c-CTimelineItem>
        <c-CTimelineItem state="current">
          <c-fill name="opposite"><time datetime="2026-08-21">Today</time></c-fill>
          <c-fill name="default"><strong>In transit</strong><br />Departed the regional hub</c-fill>
        </c-CTimelineItem>
        <c-CTimelineItem state="pending"><strong>Delivered</strong></c-CTimelineItem>
      </c-CTimeline>
    """


preview = TimelineAtAGlance()
preview  # noqa: B018
````


## Present an activity feed

Place semantic `<time>` elements, headings, descriptions, links, and actions
inside each Item. The authored DOM order remains the reading order.
When any Item has opposite metadata, the whole vertical Timeline reserves one
consistent metadata column so the track never jumps between Items. Content on
the logical start side—including opposite time labels—is aligned toward the
track rather than toward the outside edge.


### Present an activity feed

[Open the rendered preview](/v/0.4.4/ui-library/components/timeline/_previews/activity/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimelineActivity(Component):
    template = """
      <c-CTimeline label="Repository activity" density="compact">
        <c-CTimelineItem>
          <c-fill name="opposite"><time datetime="2026-08-21T09:15:00Z">09:15</time></c-fill>
          <c-fill name="default">
            <strong>Mina opened pull request #184</strong><p>Improve invoice import diagnostics.</p>
          </c-fill>
        </c-CTimelineItem>
        <c-CTimelineItem>
          <c-fill name="opposite"><time datetime="2026-08-21T10:04:00Z">10:04</time></c-fill>
          <c-fill name="default"><strong>Leo approved the changes</strong><p>All required checks passed.</p></c-fill>
        </c-CTimelineItem>
        <c-CTimelineItem state="current">
          <c-fill name="opposite"><time datetime="2026-08-21T10:12:00Z">10:12</time></c-fill>
          <c-fill name="default">
            <strong>Ready to merge</strong><p><a href="#review">Review the final diff</a></p>
          </c-fill>
        </c-CTimelineItem>
      </c-CTimeline>
    """
    css = ":where(.cui-timeline__content p){margin:.25rem 0 0}"


preview = TimelineActivity()
preview  # noqa: B018
````


## Communicate status in text

Item `state` styles the indicator. It never replaces a written status: the
indicator is decorative, and only one Item may be `current`.


### Present status history

[Open the rendered preview](/v/0.4.4/ui-library/components/timeline/_previews/status/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimelineStatus(Component):
    template = """
      <c-CTimeline label="Deployment status" line_style="dashed">
        <c-CTimelineItem state="complete">
          <strong>Build completed</strong><br />Artifacts signed successfully
        </c-CTimelineItem>
        <c-CTimelineItem state="error">
          <strong>Staging failed</strong><br />Health check timed out
        </c-CTimelineItem>
        <c-CTimelineItem state="current">
          <strong>Retry in progress</strong><br />Current attempt is running
        </c-CTimelineItem>
        <c-CTimelineItem state="pending">
          <strong>Production pending</strong><br />Waiting for staging approval
        </c-CTimelineItem>
      </c-CTimeline>
    """


preview = TimelineStatus()
preview  # noqa: B018
````


## Alternate content around the track

Use `side="alternate"` for a centered vertical track. An Item can override its
resolved side with `side="start"` or `side="end"`. All Items retain the same
three-column geometry even when only some of them provide opposite content.


### Build an alternating Timeline

[Open the rendered preview](/v/0.4.4/ui-library/components/timeline/_previews/alternating/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimelineAlternating(Component):
    template = """
      <c-CTimeline label="Product history" side="alternate">
        <c-CTimelineItem state="complete">
          <strong>Prototype</strong><p>The first field trial validated the core workflow.</p>
        </c-CTimelineItem>
        <c-CTimelineItem state="complete">
          <strong>Private beta</strong><p>Design partners shaped the collaboration model.</p>
        </c-CTimelineItem>
        <c-CTimelineItem state="current">
          <strong>Public beta</strong><p>The current release focuses on reliability and polish.</p>
        </c-CTimelineItem>
        <c-CTimelineItem state="pending">
          <strong>General availability</strong><p>Operational review and migration guidance remain.</p>
        </c-CTimelineItem>
      </c-CTimeline>
    """
    css = ":where(.cui-timeline__content p){margin:.25rem 0 0}"


preview = TimelineAlternating()
preview  # noqa: B018
````


## Build a horizontal roadmap

Horizontal Timelines preserve chronological DOM order, share one Grid Row for
the complete connector, and scroll within their own bounds at narrow widths.


### Build a horizontal roadmap

[Open the rendered preview](/v/0.4.4/ui-library/components/timeline/_previews/horizontal/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimelineHorizontal(Component):
    template = """
      <c-CTimeline label="2026 roadmap" orientation="horizontal" side="alternate" size="lg">
        <c-CTimelineItem state="complete"><strong>Q1</strong><br />Unified accounts</c-CTimelineItem>
        <c-CTimelineItem state="complete"><strong>Q2</strong><br />Regional storage</c-CTimelineItem>
        <c-CTimelineItem state="current"><strong>Q3</strong><br />Audit workspaces</c-CTimelineItem>
        <c-CTimelineItem state="pending"><strong>Q4</strong><br />Policy automation</c-CTimelineItem>
      </c-CTimeline>
    """


preview = TimelineHorizontal()
preview  # noqa: B018
````


## Customize indicators and the track

Use the `indicator` slot for an icon, avatar, or authored marker and public CSS
variables for geometry and color. Indicator content is hidden from assistive
technology, so repeat its meaning in the Item's visible content.


### Customize Timeline

[Open the rendered preview](/v/0.4.4/ui-library/components/timeline/_previews/customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimelineCustomization(Component):
    template = """
      <div class="custom-timeline">
        <c-CTimeline label="Team activity"
          c-style="{'--cui-timeline-indicator-size':'2rem','--cui-timeline-track-size':'2.75rem'}">
          <c-CTimelineItem>
            <c-fill name="indicator"><span class="avatar">AK</span></c-fill>
            <c-fill name="default">
              <strong>Ada assigned the issue</strong><br />Ownership moved to Platform.
            </c-fill>
          </c-CTimelineItem>
          <c-CTimelineItem state="current">
            <c-fill name="indicator"><span class="avatar">JM</span></c-fill>
            <c-fill name="default">
              <strong>Jules is investigating</strong><br />Current work is linked in the incident log.
            </c-fill>
          </c-CTimelineItem>
        </c-CTimeline>
      </div>
    """
    css = """
      :where(.custom-timeline) { --cui-timeline-current-color:#7c3aed; }
      :where(.custom-timeline .avatar) {
        display:grid;
        inline-size:100%;
        block-size:100%;
        place-items:center;
        border-radius:50%;
        background:currentcolor;
        color:Canvas;
        font-size:.65rem;
        font-weight:800;
      }
    """


preview = TimelineCustomization()
preview  # noqa: B018
````


## Timeline or Stepper?

Use Timeline to read events or history. Use Stepper when the user is moving
through a finite workflow and the component owns a current step or optional
step navigation.

## Accessibility and localization

Timeline renders one ordered list with one list item per event. It adds no
focus target or Arrow-key behavior. An Item with `state="current"` receives
`aria-current="true"`; all other state meaning must be written in content.

Timeline owns no text or date formatting and therefore has no catalog keys.
Author localized content with ordinary Citry `tr()` or `$c-tr`, render dates
with your application's locale profile, and add explicit `dir` boundaries when
mixing directional content.

<!-- UI_LIBRARY_API_REFERENCE -->

## API reference

### Inputs

#### CTimeline server inputs

Server inputs are passed in a template through `<c-CTimeline ... />` or in Python through
`CTimeline(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="timeline-input-ctimeline-server-inputs-orientation"></span>`orientation` | `CTimelineOrientation` ([`CTimelineOrientation`](#timeline-interface-orientation)) | `"vertical"` | Selects a vertical or horizontal track axis. |
| <span id="timeline-input-ctimeline-server-inputs-side"></span>`side` | `CTimelineSide` ([`CTimelineSide`](#timeline-interface-side)) | `"end"` | Places Item content at the logical end start or alternating sides of the track. |
| <span id="timeline-input-ctimeline-server-inputs-line-style"></span>`line_style` | `CTimelineLineStyle` ([`CTimelineLineStyle`](#timeline-interface-line-style)) | `"solid"` | Selects solid or dashed connectors. |
| <span id="timeline-input-ctimeline-server-inputs-density"></span>`density` | `CTimelineDensity` ([`CTimelineDensity`](#timeline-interface-density)) | `"comfortable"` | Selects comfortable or compact spacing. |
| <span id="timeline-input-ctimeline-server-inputs-size"></span>`size` | `CTimelineSize` ([`CTimelineSize`](#timeline-interface-size)) | `"md"` | Selects coordinated indicator and track geometry. |
| <span id="timeline-input-ctimeline-server-inputs-label"></span>`label` | `str | None` | `None` | Optionally supplies the ordered list accessible name. |
| <span id="timeline-input-ctimeline-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#timeline-interface-class-value)) | `None` | Adds classes to the root ordered list. |
| <span id="timeline-input-ctimeline-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#timeline-interface-style-value)) | `None` | Adds styles to the root ordered list. |
| <span id="timeline-input-ctimeline-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed attributes without replacing owned semantics or state. |

</div>

#### CTimelineItem server inputs

Server inputs are passed in a template through `<c-CTimelineItem ... />` or in Python
through `CTimelineItem(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="timeline-input-ctimeline-item-server-inputs-state"></span>`state` | `CTimelineState` ([`CTimelineState`](#timeline-interface-state)) | `"neutral"` | Styles authored neutral complete current pending or error status; current adds aria-current. |
| <span id="timeline-input-ctimeline-item-server-inputs-side"></span>`side` | `CTimelineItemSide` ([`CTimelineItemSide`](#timeline-interface-item-side)) | `"auto"` | Uses the root-resolved side or overrides one Item to logical start or end. |
| <span id="timeline-input-ctimeline-item-server-inputs-class"></span>`class_` | `CClassValue | None` ([`CClassValue`](#timeline-interface-class-value)) | `None` | Adds classes to the rendered list item. |
| <span id="timeline-input-ctimeline-item-server-inputs-style"></span>`style` | `CStyleValue | None` ([`CStyleValue`](#timeline-interface-style-value)) | `None` | Adds styles to the rendered list item. |
| <span id="timeline-input-ctimeline-item-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds copied allowed list-item attributes without replacing owned semantics or state. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CTimeline slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="timeline-slot-ctimeline-slots-default"></span>`default` | yes | `{}` ([`CTimelineDefaultSlotData`](#timeline-interface-ctimeline-default-slot-data)) | None; one or more CTimelineItem declarations are required. |

</div>

#### CTimelineItem slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="timeline-slot-ctimeline-item-slots-default"></span>`default` | yes | `{index, state, side, is_first, is_last}` ([`CTimelineItemDefaultSlotData`](#timeline-interface-ctimeline-item-default-slot-data)) | None. |
| <span id="timeline-slot-ctimeline-item-slots-opposite"></span>`opposite` | no | `{index, state, side, is_first, is_last}` ([`CTimelineItemOppositeSlotData`](#timeline-interface-opposite-slot-data)) | Omitted. |
| <span id="timeline-slot-ctimeline-item-slots-indicator"></span>`indicator` | no | `{index, state, side, is_first, is_last}` ([`CTimelineItemIndicatorSlotData`](#timeline-interface-indicator-slot-data)) | Decorative dot. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CTimeline CSS variables

Apply these variables to `CTimeline` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="timeline-css-ctimeline-css-variables-gap"></span>`--cui-timeline-gap` | `length` | Minimum space along the sequence axis. | `1.5rem; compact 0.75rem` |
| <span id="timeline-css-ctimeline-css-variables-item-gap"></span>`--cui-timeline-item-gap` | `length` | Space between the track and authored content. | `0.75rem; compact 0.5rem` |
| <span id="timeline-css-ctimeline-css-variables-track-size"></span>`--cui-timeline-track-size` | `length` | Cross-axis track lane size. | `sm 1.5rem; md 2rem; lg 2.5rem` |
| <span id="timeline-css-ctimeline-css-variables-indicator-size"></span>`--cui-timeline-indicator-size` | `length` | Indicator inline and block size. | `sm 0.5rem; md 0.75rem; lg 1rem` |
| <span id="timeline-css-ctimeline-css-variables-line-width"></span>`--cui-timeline-line-width` | `length` | Connector and indicator border thickness. | `0.125rem` |
| <span id="timeline-css-ctimeline-css-variables-line-color"></span>`--cui-timeline-line-color` | `color` | Connector color. | `Adaptive neutral` |
| <span id="timeline-css-ctimeline-css-variables-indicator-color"></span>`--cui-timeline-indicator-color` | `color` | Neutral indicator color. | `Adaptive neutral` |
| <span id="timeline-css-ctimeline-css-variables-current-color"></span>`--cui-timeline-current-color` | `color` | Current indicator color. | `Adaptive blue` |
| <span id="timeline-css-ctimeline-css-variables-complete-color"></span>`--cui-timeline-complete-color` | `color` | Complete indicator color. | `Adaptive green` |
| <span id="timeline-css-ctimeline-css-variables-pending-color"></span>`--cui-timeline-pending-color` | `color` | Pending indicator color. | `Adaptive muted neutral` |
| <span id="timeline-css-ctimeline-css-variables-error-color"></span>`--cui-timeline-error-color` | `color` | Error indicator color. | `Adaptive red` |
| <span id="timeline-css-ctimeline-css-variables-muted-color"></span>`--cui-timeline-muted-color` | `color` | Opposite metadata color. | `Adaptive neutral` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CTimeline attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="timeline-attribute-ctimeline-root-attributes-aria-label"></span>`aria-label` | Root ol | `string` | Optional accessible name. |
| <span id="timeline-attribute-ctimeline-root-attributes-data-orientation"></span>`data-orientation` | Root ol | `CTimelineOrientation` ([`CTimelineOrientation`](#timeline-interface-orientation)) | Mirrors the track axis. |
| <span id="timeline-attribute-ctimeline-root-attributes-data-side"></span>`data-side` | Root ol | `CTimelineSide` ([`CTimelineSide`](#timeline-interface-side)) | Mirrors root placement policy. |
| <span id="timeline-attribute-ctimeline-root-attributes-data-line-style"></span>`data-line-style` | Root ol | `CTimelineLineStyle` ([`CTimelineLineStyle`](#timeline-interface-line-style)) | Mirrors connector treatment. |
| <span id="timeline-attribute-ctimeline-root-attributes-data-density"></span>`data-density` | Root ol | `CTimelineDensity` ([`CTimelineDensity`](#timeline-interface-density)) | Mirrors spacing density. |
| <span id="timeline-attribute-ctimeline-root-attributes-data-size"></span>`data-size` | Root ol | `CTimelineSize` ([`CTimelineSize`](#timeline-interface-size)) | Mirrors geometry size. |
| <span id="timeline-attribute-ctimeline-root-attributes-data-has-opposite"></span>`data-has-opposite` | Root ol | `present | absent` | Reserves one consistent metadata column when any Item has opposite content. |

</div>

#### CTimelineItem attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="timeline-attribute-ctimeline-item-attributes-data-index"></span>`data-index` | Item li | `nonnegative-integer-string` | Exposes settled zero-based order. |
| <span id="timeline-attribute-ctimeline-item-attributes-data-state"></span>`data-state` | Item li | `CTimelineState` ([`CTimelineState`](#timeline-interface-state)) | Mirrors authored visual status. |
| <span id="timeline-attribute-ctimeline-item-attributes-data-side"></span>`data-side` | Item li | `start | end` | Mirrors resolved logical placement. |
| <span id="timeline-attribute-ctimeline-item-attributes-data-has-opposite"></span>`data-has-opposite` | Item li | `present | absent` | Marks an authored opposite slot. |
| <span id="timeline-attribute-ctimeline-item-attributes-aria-current"></span>`aria-current` | Current Item li | `true` | Identifies the one current event. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CTimeline selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="timeline-selector-ctimeline-selectors-timeline"></span>`[data-citry-ui-part="timeline"]` | Root ol | State reflections and root customization destination. |
| <span id="timeline-selector-ctimeline-selectors-item"></span>`[data-citry-ui-part="item"]` | Item li | Item attrs state and customization destination. |
| <span id="timeline-selector-ctimeline-selectors-opposite"></span>`[data-citry-ui-part="opposite"]` | Optional metadata div | Dates and other opposite content. |
| <span id="timeline-selector-ctimeline-selectors-track"></span>`[data-citry-ui-part="track"]` | Decorative div | Owns connector segments and indicator. |
| <span id="timeline-selector-ctimeline-selectors-before"></span>`[data-citry-ui-part="before"]` | Decorative span | Connector segment before the indicator. |
| <span id="timeline-selector-ctimeline-selectors-indicator"></span>`[data-citry-ui-part="indicator"]` | Decorative span | Default dot or custom indicator destination. |
| <span id="timeline-selector-ctimeline-selectors-after"></span>`[data-citry-ui-part="after"]` | Decorative span | Connector segment after the indicator. |
| <span id="timeline-selector-ctimeline-selectors-content"></span>`[data-citry-ui-part="content"]` | Content div | Authored event content destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="timeline-interface-orientation"></span>`CTimelineOrientation` | `Literal["vertical", "horizontal"]` |
| <span id="timeline-interface-side"></span>`CTimelineSide` | `Literal["start", "end", "alternate"]` |
| <span id="timeline-interface-item-side"></span>`CTimelineItemSide` | `Literal["auto", "start", "end"]` |
| <span id="timeline-interface-line-style"></span>`CTimelineLineStyle` | `Literal["solid", "dashed"]` |
| <span id="timeline-interface-density"></span>`CTimelineDensity` | `Literal["comfortable", "compact"]` |
| <span id="timeline-interface-size"></span>`CTimelineSize` | `Literal["sm", "md", "lg"]` |
| <span id="timeline-interface-state"></span>`CTimelineState` | `Literal["neutral", "complete", "current", "pending", "error"]` |
| <span id="timeline-interface-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="timeline-interface-style-value"></span>`CStyleValue` | `str | Mapping[str, object] | Sequence[CStyleValue]` |

</div>

<span id="timeline-interface-ctimeline-default-slot-data"></span>

#### `CTimelineDefaultSlotData`

Empty dataclass: `{}`.

<span id="timeline-interface-ctimeline-item-default-slot-data"></span>

#### `CTimelineItemDefaultSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="timeline-interface-ctimeline-item-default-slot-data-index"></span>`index` | `int` | - | Settled zero-based Item index. |
| <span id="timeline-interface-ctimeline-item-default-slot-data-state"></span>`state` | `CTimelineState` ([`CTimelineState`](#timeline-interface-state)) | - | Authored Item state. |
| <span id="timeline-interface-ctimeline-item-default-slot-data-side"></span>`side` | `start | end` | - | Resolved logical content side. |
| <span id="timeline-interface-ctimeline-item-default-slot-data-is-first"></span>`is_first` | `bool` | - | Whether this is the first Item. |
| <span id="timeline-interface-ctimeline-item-default-slot-data-is-last"></span>`is_last` | `bool` | - | Whether this is the last Item. |

</div>

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="timeline-interface-opposite-slot-data"></span>`CTimelineItemOppositeSlotData` | `CTimelineItemDefaultSlotData` |

</div>

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="timeline-interface-indicator-slot-data"></span>`CTimelineItemIndicatorSlotData` | `CTimelineItemDefaultSlotData` |

</div>

### Translation keys

-