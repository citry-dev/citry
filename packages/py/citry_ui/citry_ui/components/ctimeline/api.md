---
title: Timeline
description: Present histories, activity, milestones, and status sequences with Citry UI.
---

# Timeline

Use `CTimeline` and `CTimelineItem` for ordered histories, activity feeds,
roadmaps, and status sequences. Timeline is presentational: links, actions,
loading, and date formatting remain owned by your application.

## Timeline at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctimeline/snippets/at_a_glance.py" title="Timeline at a glance" />

## Present an activity feed

Place semantic `<time>` elements, headings, descriptions, links, and actions
inside each Item. The authored DOM order remains the reading order.
When any Item has opposite metadata, the whole vertical Timeline reserves one
consistent metadata column so the track never jumps between Items. Content on
the logical start side—including opposite time labels—is aligned toward the
track rather than toward the outside edge.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctimeline/snippets/activity.py" title="Present an activity feed" />

## Communicate status in text

Item `state` styles the indicator. It never replaces a written status: the
indicator is decorative, and only one Item may be `current`.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctimeline/snippets/status.py" title="Present status history" />

## Alternate content around the track

Use `side="alternate"` for a centered vertical track. An Item can override its
resolved side with `side="start"` or `side="end"`. All Items retain the same
three-column geometry even when only some of them provide opposite content.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctimeline/snippets/alternating.py" title="Build an alternating Timeline" />

## Build a horizontal roadmap

Horizontal Timelines preserve chronological DOM order, share one Grid Row for
the complete connector, and scroll within their own bounds at narrow widths.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctimeline/snippets/horizontal.py" title="Build a horizontal roadmap" />

## Customize indicators and the track

Use the `indicator` slot for an icon, avatar, or authored marker and public CSS
variables for geometry and color. Indicator content is hidden from assistive
technology, so repeat its meaning in the Item's visible content.

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/ctimeline/snippets/customization.py" title="Customize Timeline" />

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
