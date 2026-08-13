# Citry UI Toolbar specification

**Status (2026-08-10):** implementation pass complete. Runtime, focused
server/browser evidence, public reference data, examples, quality scenario,
registration, and packaging wiring are checked in. Live assistive-technology
and release qualification remain human review work.

## 1. Purpose and product bar

`CToolbar` groups at least three persistent controls into one named composite
with one page Tab stop and arrow-key focus movement. It suits editor commands,
table tools, map controls, and contextual action strips.

Toolbar owns focus navigation only. Buttons own actions, Toggles own pressed
state, ToggleGroup owns selection, and Menu or Popover owns overlays. Use
`CButtonGroup` when related actions should remain ordinary Tab stops.

## 2. Prior art and complaints

Sources reviewed on 2026-08-10:

- WAI-ARIA APG Toolbar defines a named `toolbar`, one Tab stop, orientation
  aware arrow navigation, optional wrapping, Home/End, and last-focused entry.
- Radix Toolbar 1.1.16 composes Buttons, links, separators, ToggleGroups, and
  overlay triggers under roving focus.
- React Aria Toolbar composes Buttons, ToggleButtonGroups, Groups, Select
  triggers, and separators while owning only focus movement.
- Material UI Toolbar is primarily layout for application bars and does not
  supply APG roving focus, so Citry does not copy its layout-only semantics.
- existing Citry `CButtonGroup`, `CToggleGroup`, `CMenu`, `CPopover`, and
  `CDivider` already own actions, state, overlays, and separators.

Citry adopts the APG composite rather than a generic flex wrapper. Version 1
intentionally supports native Buttons and links as navigable controls. Native
text inputs, selects, textareas, contenteditable regions, and nested toolbars
are rejected because their directional-key contracts conflict with Toolbar.

## 3. Public composition and anatomy

`CToolbar` renders one `<div role="toolbar">` and its required default slot.
Controls may be direct children or descendants of presentational `group`
wrappers such as `CButtonGroup` and `CToggleGroup`. `CDivider` supplies visual
separator semantics and never enters the focus registry.

Nested Dialog, Menu, Listbox, Tree, Grid, Tablist, and popover surfaces remain
independent composites. Their descendants are not registered as Toolbar
controls. A Menu or Popover activator rendered in the Toolbar remains a normal
Toolbar Button.

## 4. Server inputs and client inputs

### Server inputs

| Input | Type | Default | Class | Effect |
|---|---|---|---|---|
| `label` | nonempty `str` | required | structural | accessible Toolbar name |
| `orientation` | `"horizontal" | "vertical"` | `"horizontal"` | reactive configuration | ARIA orientation, layout, and arrow axis |
| `loop` | `bool` | `True` | reactive configuration | wraps arrow navigation at boundaries |
| `variant` | `"plain" | "soft" | "outline"` | `"plain"` | reactive presentation | Toolbar surface treatment |
| `size` | `"sm" | "md" | "lg"` | `"md"` | reactive presentation | container gap, padding, and minimum height |
| `class_` | `CClassValue | None` | `None` | structural | root classes |
| `style` | `CStyleValue | None` | `None` | structural | root inline styles |
| `attrs` | `Mapping[str, object] | None` | `None` | structural | trusted root attrs after owned rejection |

### Client inputs

`orientation`, `loop`, `variant`, and `size` accept the same valid values.
Omission uses the server fallback. Invalid values keep the fallback and report
once per continuous invalid episode. Toolbar has no value and no callbacks.

## 5. State model

The only internal state is the current roving-focus control. Initial activation
chooses the first enabled control. Focus entering another registered control
makes it the remembered entry. Configuration changes never activate controls
or change their pressed, selected, open, or form state.

Native `:disabled`, `aria-disabled="true"`, hidden, and inert controls are
skipped. A currently remembered control becoming unavailable moves the single
Tab stop to the nearest following enabled control, then the nearest preceding
control. Focus moves only when it was already inside the Toolbar.

## 6. Slots and slot data

The required default slot receives `{}`. Settled enhanced content must contain
at least three Toolbar-owned Buttons or links. Noninteractive phrasing content,
groups, and `CDivider` are allowed. Native input, select, textarea,
contenteditable, nested Toolbar, and caller-authored tabindex are rejected.

## 7. Callbacks, native events, and methods

Toolbar defines no component callback, custom DOM event, or method. Native
click and keyboard activation remain on each control. The root owns keydown and
focusin in capture phase so an authored `stopPropagation()` handler does not
disable composite navigation.

## 8. Semantics, keyboard, focus, and assistive technology

The root has `role="toolbar"`, `aria-label`, and exact `aria-orientation`.
Exactly one enabled owned control has `tabindex="0"`; every other owned control
has `tabindex="-1"`.

- Tab and Shift+Tab enter or leave the Toolbar through the remembered control.
- Horizontal Left/Right and vertical Up/Down move focus. Horizontal direction
  follows computed LTR or RTL.
- Home and End focus the first and last enabled controls.
- `loop=True` wraps; `loop=False` stops at the boundary.
- Enter and Space remain native control activation.
- Perpendicular arrow keys remain available to the focused child.

Authors must avoid controls whose required arrow axis conflicts with the
Toolbar orientation. Icon-only controls still require their own accessible
names through CButton or native ARIA.

## 9. Native forms and validation

Toolbar is not a form control. Descendant Buttons and links retain native Form
ownership, submission, reset, and validation behavior. CButton and CToggle are
form-safe Buttons. Native authored Buttons remain responsible for explicit
`type="button"` when they are not intended to submit.

Native disabled fieldsets and `CForm.disabled` remain dominant. Toolbar reads
the settled native `:disabled` state and never rewrites it.

## 10. Styling and theme contract

Public variables are `--cui-toolbar-gap`, `--cui-toolbar-padding`,
`--cui-toolbar-min-height`, `--cui-toolbar-radius`,
`--cui-toolbar-background`, `--cui-toolbar-foreground`,
`--cui-toolbar-border-color`, and `--cui-toolbar-focus-color`.

The stable part is `toolbar`. Stable mirrors are `data-orientation`,
`data-loop`, `data-variant`, and `data-size`. Toolbar does not restyle child
Button or Toggle variants.

## 11. Environmental behavior

Horizontal Toolbar is a single logical row and may scroll inline rather than
wrap into an ambiguous two-dimensional composite. Vertical Toolbar uses one
column. Logical properties support RTL. Long labels may shrink and wrap inside
their owning controls without forcing page overflow. Forced colors preserve
the surface border and native control focus. Reduced motion removes the small
surface transition. Print retains boundary and orientation.

## 12. Overlay and layering behavior

Toolbar creates no overlay. Menu, Popover, Tooltip, Dialog, and AlertDialog
activators remain registered controls while their surfaces and descendants are
excluded from Toolbar ownership. Arrow handling belongs to the nearest active
composite: once focus enters an opened overlay, Toolbar does not receive it.

## 13. Collections, async data, and identity

Toolbar derives its bounded control registry from settled DOM. Browser-owned
membership insertion and removal are not a public collection API in version 1.
Within one initializer lifetime, disabled, hidden, inert, href, and relevant
structure changes reconcile the roving entry. Correlated server rerenders use
fresh settled membership and retain a physically preserved current control;
otherwise entry falls back to the prior index or first enabled control.

## 14. Server render, morph, and cleanup

Server HTML is a correctly named Toolbar with ordinary native focusability, so
it remains usable without JavaScript. Activation snapshots each owned
control's authored tabindex, installs roving focus, and marks readiness only
after valid settled reconciliation. Cleanup removes listeners and observers,
restores authored tabindex exactly, and prevents stale tasks from changing a
replacement generation.

## 15. Security and content trust

Direct strings are de-trusted. Root attrs reject role, name, orientation,
focus, children, public mirrors, runtime markers, hidden/inert ownership,
structural Alpine directives, and whole-object bindings. Settled validation
rejects controls that attempt to author their own tabindex or create a nested
focus owner. Native link URL trust remains the application's responsibility.

## 16. Assets and performance

One shared JS and CSS definition serves every instance. Each Toolbar has two
capture listeners, one root subtree observer, and observers only for native
ancestor fieldsets. Reconciliation is O(n) over owned controls and coalesces
same-batch mutations. Repository diagnostics record assets and bounded server
output at 1, 10, 100, 500, and 1,000 instances.

## 17. Acceptance matrix

Automated evidence covers server role/name/orientation and mirrors; attrs;
empty and invalid structure; native Buttons, links, ButtonGroup, ToggleGroup,
Divider, Menu and Popover activators; one Tab stop; LTR/RTL and both axes;
looping, Home/End, disabled and fieldset changes; perpendicular key release;
capture ownership; cleanup and retained reinitialization; variants, sizes,
public variables, narrow geometry, forced colors, reduced motion, print; three
engines; axe; docs previews; quality, assets, registration, wheel, and Ruff.

Manual release evidence covers VoiceOver/Safari, NVDA/Firefox or Chromium,
JAWS/Chromium, touch, browser zoom, and representative editor workflows.

## 18. Compatibility classification

Stable: inputs, role/name/orientation, keyboard behavior, focus boundary,
parts, mirrors, and variables. Private: registry selectors, readiness marker,
observers, scheduling, and classes. Deferred: wrapping multi-row navigation,
overflow collapsing, keyboard shortcuts, and child presentation ownership.

## 19. Public documentation contract

The guide contrasts Toolbar with ButtonGroup and ToggleGroup, then demonstrates
commands, Toggles, separators, links, Menu/Popover activators, orientation,
looping, variants/sizes, disabled behavior, and customization. It warns against
text fields and axis-conflicting child controls.

## 20. Open decisions and deferred work

Automatic overflow menus, multiple visual rows, global shortcuts, text-entry
controls, nested Toolbars, and Toolbar-owned selection remain deferred. None
blocks version 1 implementation.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
