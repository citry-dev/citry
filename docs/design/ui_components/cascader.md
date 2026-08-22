# Cascader

**Status:** accepted implementation contract for the first production pass.
Research refreshed 2026-08-21.

## 1. Purpose

`CCascader` selects one path through a finite, server-rendered hierarchy.
`CCascaderOption` declares one stable value, plain label, disabled state, and
optional child Options. The popup presents one visible level per column so a
province, category, organization, or other taxonomy can be resolved without
flattening every path into one long list.

Ant Design's current Cascader establishes the product distinction among path
selection, optional parent selection, search, multiple selection, and lazy
loading. Citry v1 supports one path and optional parent selection. Search,
multiple paths, and lazy child loading are separate future contracts because
they add different result, async, and selection state machines.

## 2. Composition and anatomy

```text
CCascader -> div root
|- button trigger
|  |- selected path or placeholder
|  `- disclosure indicator
|- div popup
|  |- root tree column
|  `- sibling group columns linked to branch treeitems with aria-owns
|- repeated hidden inputs for selected path when name exists
`- polite status
```

Option values are unique across the hierarchy. `value` is the complete path
from root through the selected Option. Unknown, discontinuous, disabled, or
nonselectable parent paths fail on the server and are rejected as client props.
Without JavaScript, the selected path remains visible and form-submittable.

## 3. Semantics and keyboard

The trigger is a native button with `aria-haspopup=tree`, `aria-expanded`, and
`aria-controls`. The popup uses a single-select tree model, following the WAI
APG distinction between focus and selection. Each Option is a treeitem. Its
child list is a logically owned group and becomes the next visible column only
while that branch is active. Visual columns are DOM siblings so one column
cannot become another column's horizontal scroll container. Explicit
`aria-level`, `aria-posinset`, `aria-setsize`, and `aria-owns` preserve the
hierarchy exposed to assistive technology.

Arrow Down and Up move within a column; Home and End reach its boundaries;
Arrow Right opens a branch and enters its first child; Arrow Left returns to
the parent and collapses the departed child column. Arrow Left on an expanded
branch collapses it in place. Enter, Space, or pointer activation opens a
collapsed branch and collapses an expanded branch; activating a leaf selects
it. Collapsing affects only the browsing path and does not change an accepted
leaf. Escape closes and restores trigger focus. Printable text performs bounded
typeahead in the active column. Tab closes without trapping focus.

## 4. Inputs, state, and callbacks

Server inputs include `value`, `name`, `form`, `aria_label`,
`aria_labelledby`, `placeholder`, `separator`, `change_on_select`, `open`,
`disabled`, `size`, `variant`, catalog label overrides, and root
customization. Client props are `value`, `open`,
`disabled`, `onValueChange`, and `onOpenChange`.

Uncontrolled selection commits immediately. Controlled `value` emits a request
and restores the accepted path until the owner supplies it. Controlled `open`
works the same way. `onValueChange(path, detail)` includes labels,
`previousValue`, selected Option element, controlled flag, and source event.
`onOpenChange(open, detail)` includes reason and source event.
An invalid controlled `value` or `open` value is diagnosed once and leaves the
last valid effective state unchanged. Omitting `value` returns to the retained
uncontrolled path; omitting `open` releases control at its current state.

## 5. Forms and localization

When `name` exists, one hidden input per selected path segment uses that name
in root-to-leaf order. Disabled roots submit none. Form reset restores the
server path. The visible selected label joins application-authored Option
labels with `separator`; those labels remain in their own locale.

Catalog messages cover the placeholder, selected path summary, and empty-hierarchy
status. The stateful trigger value uses `i18n.bind()`: locale changes update the
placeholder only while the path is empty and never overwrite an accepted
application path. The stable empty status uses `$c-tr`. Browser-created
summaries use one-shot `i18n.tr()` with the live joined path. Explicit overrides
remain fixed.

## 6. Styling, lifecycle, and limits

Public parts are `cascader`, `trigger`, `value`, `indicator`, `popup`, `tree`,
`group`, `option`, `option-row`, `option-label`, `option-indicator`, `empty`,
`inputs`, and `status`. Public variables cover width, column width, max height,
surface, border, radius, shadow, active surface, and focus. Columns sit side by
side and scroll vertically within the maximum height when the preferred width of
up to three visible columns fits the physical viewport. The runtime measures that
fit after path changes and viewport resizing, including custom column widths. If
the preferred row does not fit, the visible columns stack at the trigger width
and the popup becomes the vertical scroll owner without adding horizontal
scrolling. Deeper row layouts retain the three-column inline cap and use the
popup as their horizontal scroll owner. Popup height follows the tallest visible
row-layout column instead of reserving a fixed empty area.
Open-state placement shifts the popup inside the physical viewport at either
inline edge. Logical properties support RTL, including reversed column
progression and a mirrored branch indicator.
Forced colors preserve selected/focused states, reduced motion removes popup
transition, and print retains the accepted path but hides controls.

Initialization is idempotent. Cleanup removes listeners, prop effects, pending
typeahead, and runtime state. The component installs its
outside-pointer and viewport-resize listeners only while open; reset listeners
stay scoped to the owning forms. It performs no network access. Labels and values are
plain strings; the runtime uses no `innerHTML`, `eval`, or raw-value selectors.

## 7. Acceptance and public docs

Evidence covers nesting validation, an empty hierarchy, useful server output,
native path order,
controlled and uncontrolled selection, parent selection policy, pointer and
keyboard branch toggling, all keyboard keys, typeahead, disabled Options, reset,
RTL, measured side-by-side geometry, fit-triggered vertical stacking, visually
authoritative closing, stateful placeholder localization,
morph cleanup, axe, assets, API schema, six snippets, and Chromium, Firefox,
and WebKit. Public API documentation ends with every translation key.

Deferred work is multiple path selection, catalog-aware search, async child
loading, custom Option rendering, and virtualized levels.
