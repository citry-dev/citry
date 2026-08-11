---
title: Disclosure
description: Reveal one independent block of supporting content.
---

# Disclosure

Use `CDisclosure` for one independently expandable note, setting group, or
supporting section. Use `CAccordion` when several items share selection,
expansion policy, or collection keyboard behavior.

## Disclosure at a glance

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdisclosure/snippets/at_a_glance.py" title="Disclosure at a glance" />

## Write the shortest Disclosure

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdisclosure/snippets/basic_disclosure.py" title="Basic Disclosure" />

The title becomes the native Button name. Choose `heading_level` to fit the
document outline. Add `region` only when the expanded panel deserves a
landmark.

Python composition uses the same two required slots:

```python
from citry_ui import CDisclosure

requirements = CDisclosure(
    slots={
        "title": "System requirements",
        "default": "Python 3.13 or newer",
    },
)
```

## Control expansion

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdisclosure/snippets/controlled_open.py" title="Control Disclosure" />

A Boolean client `open` owns expansion. Omit it or supply `null` to release
control and commit the retained uncontrolled/server baseline, which may differ
from the visible controlled state.

`onOpenChange` is a component callback, not a DOM event. Native listeners such
as `@click` and `@focus` still receive their ordinary browser events;
Disclosure dispatches no custom toggle, show, or hide event.

## Add actions and disabled state

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdisclosure/snippets/actions_and_disabled.py" title="Disclosure actions and disabled state" />

Actions stay beside the heading rather than inside its Button. Disabledness
blocks activation without erasing an already-open panel.

## Choose treatment and geometry

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdisclosure/snippets/variants_and_sizes.py" title="Disclosure variants and sizes" />

## Nest independent and grouped content

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdisclosure/snippets/nested_disclosures.py" title="Nested Disclosure and Accordion" />

Nested Disclosure and Accordion roots belong in the panel, never in the title
or adjacent actions.

## Compose overlays and Dialogs safely

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdisclosure/snippets/overlays_and_dialogs.py" title="Disclosure overlays and sibling Dialog" />

Citry anchored layers may live in an open panel and close structurally with
it. Render `CDialog` and `CDrawer` as siblings outside Disclosure, then open
them from a panel or action control. Native `dialog` elements, `CDialog`, and
`CDrawer` are rejected as panel or actions descendants regardless of their
current open state. Raw native popovers, unresolved web components, customized
built-ins, and authored shadow hosts are also outside that slot contract.

## Keep title content structural

The title accepts text and only these native elements: `abbr`, `b`, `bdi`,
`bdo`, `br`, `cite`, `code`, `data`, `del`, `dfn`, `em`, `i`, `img`, `ins`,
`kbd`, `mark`, `picture`, `q`, `rp`, `rt`, `ruby`, `s`, `samp`, `small`,
`source`, `span`, `strong`, `sub`, `sup`, `svg`, `time`, `u`, `var`, and
`wbr`. Images must have empty `alt`. Decorative SVG must use
`aria-hidden="true"` and `focusable="false"`, and may contain only `g`, `path`,
`polyline`, `line`, `circle`, `rect`, `ellipse`, and `polygon`. The title must
still contain non-whitespace text outside decorative content. Links, controls,
custom elements, and other HTML do not belong inside the trigger. Every title
descendant rejects `role`, `tabindex`, `contenteditable`, `autofocus`, `href`,
`xlink:href`, `controls`, `usemap`, `form`, `popover`, `is`, `hidden`, `inert`,
ARIA naming or description attributes, inline or Alpine event listeners, and
Alpine structural or ownership directives.

The default panel accepts normal flow content and nested Disclosure or
Accordion roots within the overlay boundary above. Actions follow the same
boundary but do not accept nested Disclosure or Accordion roots.

## Preserve forms and focus

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdisclosure/snippets/forms_and_focus.py" title="Disclosure forms and focus" />

Panels stay mounted, so closing preserves edits and FormData participation.
It does not exempt a required closed control from constraint validation. Keep
required content open or open it from captured validation handling.

## Customize Disclosure

<c-ui-demo path="packages/py/citry_ui/citry_ui/components/cdisclosure/snippets/customization.py" title="Customize Disclosure" />

## Accessibility and interaction

The trigger is a native `button type="button"` with `aria-expanded` and
`aria-controls`. Enter and Space use native activation. Disclosure does not
add Arrow, Home, or End behavior. When accepted closing would hide focused
panel content, focus moves to the trigger or a safe modal/document fallback
before the panel becomes inert.

For a plain no-JavaScript reveal, use native
[`details`](https://html.spec.whatwg.org/multipage/interactive-elements.html#the-details-element)
and `summary`. Citry's authored pattern exists for controlled ownership,
disabled fieldsets, adjacent actions, focus safety, and reversible animation.

<!-- UI_LIBRARY_API_REFERENCE -->
