---
title: Alert
description: Present persistent feedback with clear intent, optional actions, and deliberate announcement urgency.
---

# Alert

Use `CAlert` for persistent feedback about a page, section, action, or system
condition. Alert owns presentation and optional announcement semantics. Your
application owns visibility, dismissal, focus recovery, and retry behavior.

## Alert at a glance

Intent changes both color and icon shape, so meaning never depends on color
alone.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/calert/snippets/at_a_glance.py"
  title="Alert at a glance"
/>

## Compose an Alert

Write a message in the default slot. Add `title` when a condition needs a
short summary.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/calert/snippets/basic_alert.py"
  title="Compose Alert content"
/>

```citry-html
<c-CAlert intent="warn">
  <c-fill name="title">
    Cloud cover approaching
  </c-fill>
  <c-fill name="default">
    The western ridge may disappear after midnight.
  </c-fill>
</c-CAlert>
```

Compose the same Alert in Python:

```python
from citry_ui import CAlert

forecast = CAlert(
    intent="warn",
    slots={
        "title": "Cloud cover approaching",
        "default": "The western ridge may disappear after midnight.",
    },
)
```

At least one of `title` or `default` is required. Alert does not choose a
heading rank; put the appropriate native heading in the title slot when the
Alert introduces a document section.

## Choose visual meaning

Use `info` for neutral context, `success` for completion, `warn` for a
condition that needs attention, and `error` for failure.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/calert/snippets/intents.py"
  title="Compare Alert intents"
/>

`intent` is visual meaning, not urgency. Configure announcements separately.

## Choose emphasis

`soft` is the quiet default. Use `solid` for stronger prominence and `outline`
when the surrounding surface should remain visible.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/calert/snippets/variants.py"
  title="Compare Alert variants"
/>

## Choose size

`sm`, `md`, and `lg` change spacing, text scale, icon geometry, and action gap.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/calert/snippets/sizes.py"
  title="Compare Alert sizes"
/>

## Configure icons

The default icon follows intent. Set `icon=False` to hide it or pass a
registered `icon_name` for a fixed decorative glyph.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/calert/snippets/icons.py"
  title="Use automatic, hidden, and fixed icons"
/>

Icons are hidden from the accessibility tree. Put essential meaning in the
title or message.

## Add actions

Use the `actions` slot for links, Buttons, menus, or other related controls.
`actions_label` gives the controls a named group without adding another layout
wrapper.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/calert/snippets/actions.py"
  title="Add actions and own dismissal"
/>

Alert has no close input or callback. The state owner hides or removes it and
chooses where focus goes when a focused action disappears. The example retains
the Alert with `x-show`; use a server rerender when dismissal must remove it.

## Configure Alert in the browser

Server inputs are passed in Python through `<c-CAlert ... />` attributes or a
`CAlert(...)` composition call. Client inputs are passed in the browser through
`$c-props="{...}"`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/calert/snippets/configure.py"
  title="Configure Alert"
/>

Client `intent`, `variant`, `size`, `announce`, and `icon` values override the
server fallback. Omit a value to return to that fallback. Invalid values never
acquire ownership.

## Choose announcement urgency

The default `announce="off"` adds no live-region role. Use `polite` for a
nonblocking update and `assertive` only when attention is immediate.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/calert/snippets/announcements.py"
  title="Compare announcement modes"
/>

Alert applies `status` or `alert` to the content wrapper, never the action
group. It does not guarantee that a populated Alert inserted in one operation
will be announced by every browser and assistive-technology pair. A queued,
reliable announcer needs a persistent owner.

## Customize the theme

Override public variables on an ancestor or one Alert. Use stable part
selectors for targeted rules.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/calert/snippets/customization.py"
  title="Theme observatory Alerts"
/>

`class_`, `style`, and `attrs` target the root. `actions_attrs` targets the
optional action wrapper. Unlayered consumer CSS overrides Citry UI defaults;
named layers follow the site-wide layer-order contract.

## Accessibility and trust

Alert never moves focus, adds a Tab stop, traps keyboard input, or handles
Escape. Authored actions keep native DOM and Tab order. Visual intent changes
icon shape as well as color.

Title and message content use ordinary Citry escaping. `actions_label` is
converted to plain text before attribute rendering. Registered icon names use
the packaged allowlist. `attrs`, `actions_attrs`, `class_`, and `style` remain
trusted authoring surfaces for unowned values; Alert rejects attributes and
directives that could replace its children, semantics, focus ownership,
public mirrors, or runtime markers.
