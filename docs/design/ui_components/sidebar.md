# Sidebar

**Status:** implementation contract accepted for a persistent/collapsible
Sidebar. Responsive modal navigation deliberately composes `CDrawer` rather
than giving one DOM node conflicting landmark and modal-dialog semantics.

## 1. Purpose and product bar

`CSidebar` presents persistent application navigation or complementary tools
beside primary content. It owns a labelled landmark, fixed header/footer,
scrollable content, collapse control, rail/off-canvas collapse, logical side,
and controlled state. It does not own navigation items, routing, the page grid,
or a responsive modal overlay.

```html
<c-CSidebar id="workspace-sidebar" label="Workspace navigation">
  <c-fill name="header"><strong>Northstar</strong></c-fill>
  <c-fill name="default"><c-CList>...</c-CList></c-fill>
  <c-fill name="footer">Signed in as Ada</c-fill>
</c-CSidebar>
```

Use `CList`, `CDisclosure`, `CMenu`, and ordinary links inside it. Use
`CDrawer placement="inline-start"` for modal mobile navigation. A future
AppShell may choose between those surfaces without changing either contract.

## 2. Prior art and complaints

| Product or standard | Review date | Surface inspected | Decision supported |
|---|---|---|---|
| Vuetify `VNavigationDrawer` | 2026-08-21 | logical location, permanent/temporary, rail, width, floating, sticky, focus capture, mobile mode | Adopt logical side, rail, width profiles and sticky/floating styling; keep modal temporary behavior in Drawer. |
| shadcn/ui Sidebar | 2026-08-21 | provider, open state, offcanvas/icon/none collapse, header/content/footer, inset, trigger, shortcut, RTL changelog | Adopt a compact anatomy and controlled collapse; reject a global provider, implicit shortcut and bundled menu system. |
| PatternFly Navigation | 2026-08-21 | grouped/expandable/drilldown/flyout navigation, labelling, current and expanded state | Compose existing List/Disclosure/Menu families rather than duplicating navigation-item behavior. |
| WAI landmarks and Disclosure APG | 2026-08-21 | labelled navigation/complementary regions, native Button, `aria-expanded`, `aria-controls` | Render a labelled native landmark and native disclosure Button; add no menu role or Arrow-key model. |
| Citry UI Drawer and overlay foundations | current local source | native modal Dialog, focus containment, inertness, scroll lock, logical placement | Keep a persistent Sidebar out of the top layer and direct modal jobs to Drawer. |

Vuetify is the primary styled-suite reference. Citry covers permanent,
collapsible, rail, floating, sticky, size, logical side and authored content.

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `location` | direct API | `side=inline-start|inline-end` | Adopt logical values only. |
| `rail`, `rail-width` | direct API/CSS | `collapsible=rail`, public rail variable | Adopt without hover-only expansion. |
| model visibility | controlled state | `collapsed`, `onCollapsedChange` | Model collapse rather than ambiguous mobile visibility. |
| `permanent` | default behavior | expanded Sidebar | Adopt. |
| `temporary`, scrim, focus capture | separate component | `CDrawer` | Do not combine landmark and modal semantics. |
| `mobile`, breakpoint, touchless | AppShell/application policy | Sidebar plus Drawer | Defer responsive policy. |
| `floating`, width, sticky | direct API/CSS | `variant`, `size`, `sticky`, variables | Adopt. |
| image/theme/layout registration | composition/theme/AppShell | slots and ordinary layout | Omit. |

## 3. Public composition and anatomy

```text
aside|nav.cui-sidebar
├─ button.cui-sidebar__toggle
└─ div.cui-sidebar__panel
   ├─ header.cui-sidebar__header?
   ├─ div.cui-sidebar__content
   └─ footer.cui-sidebar__footer?
```

`class_`, `style`, and `attrs` target the native landmark. The toggle remains
available when off-canvas content is collapsed. Its optional slot replaces
only the decorative glyph; localized accessible text remains owned. The
panel/header/content/footer wrappers and relationships are stable parts.

## 4. Server inputs and client inputs

Server inputs are `id`, required nonempty `label`, `tag="aside"|"nav"`,
`collapsed=False`, `collapsible="rail"|"offcanvas"|"none"`,
`side="inline-start"|"inline-end"`, `variant="plain"|"floating"`,
`size="sm"|"md"|"lg"`, `sticky=False`, `expand_label`, `collapse_label`,
and root `class_`, `style`, `attrs`. `collapsed=True` is invalid with
`collapsible="none"`.

Client inputs mirror `collapsed`, `collapsible`, `side`, `variant`, `size`, and
`sticky`, plus `onCollapsedChange`. A supplied Boolean `collapsed` controls
state; omission releases to the last committed uncontrolled value. Invalid
client values report once and use the valid server/committed value.

## 5. State model

The effective state is expanded or collapsed. `none` always expands. A
collapsed `offcanvas` Sidebar keeps its toggle available and hides/inerts the
panel. A collapsed `rail` keeps panel controls available in a narrow rail;
Citry List labels remain visually clipped but accessible. A controlled
activation requests and notifies without committing. An uncontrolled
activation commits before notification. Configuration changes reconcile
without emitting callbacks.

## 6. Slots and slot data

| Slot | Required | Data | Fallback |
|---|---:|---|---|
| `default` | yes | `{}` | none |
| `header` | no | `{}` | omitted |
| `footer` | no | `{}` | omitted |
| `toggle` | no | `{collapsed}` at server render | neutral panel glyph |

Header and footer remain outside the owned scroll region. Slot content owns
its own interactivity. `data-citry-sidebar-expanded-only` and
`data-citry-sidebar-rail-only` are documented authored hooks; the latter must
carry an accessible equivalent when it replaces content.

## 7. Callbacks, native events, and methods

`onCollapsedChange(collapsed, detail)` receives `{collapsed,
previousCollapsed, controlled, source, sourceEvent}` for native toggle
activation. Return values do not cancel; controlled state is the acceptance
mechanism. The family adds no custom DOM event or imperative method.

## 8. Semantics, keyboard, focus, and assistive technology

The root is a labelled `<aside>` complementary landmark or `<nav>` navigation
landmark; its required name is emitted as `aria-label`. The toggle is a native `type=button` with `aria-controls` and
`aria-expanded`; localized visible-to-AT text changes between Expand and
Collapse. Enter and Space use native activation. Sidebar adds no roving focus
or Arrow keys. Collapsing off-canvas content while focus is inside moves focus
to the toggle before hiding it. Rail links retain accessible names.

## 9. Native forms and validation

Sidebar is not a Form control. Its toggle never submits. Authored controls
inside the panel retain Form ownership; collapsing an off-canvas panel makes
them unavailable through native `hidden` and `inert` behavior.

## 10. Styling and theme contract

Public parts are `sidebar`, `toggle`, `toggle-icon`, `toggle-label`, `panel`,
`header`, `content`, and `footer`. Public variables are
`--cui-sidebar-width`, `--cui-sidebar-rail-width`,
`--cui-sidebar-background`, `--cui-sidebar-foreground`,
`--cui-sidebar-border-color`, `--cui-sidebar-shadow`,
`--cui-sidebar-radius`, `--cui-sidebar-padding`, `--cui-sidebar-gap`,
`--cui-sidebar-toggle-size`, `--cui-sidebar-focus-color`, and
`--cui-sidebar-sticky-offset`.

Root mirrors are `data-collapsed`, `data-collapsible`, `data-side`,
`data-variant`, `data-size`, `data-sticky`, and `data-has-header`. The last
marker makes an authored header share its first Row with the owned toggle
instead of starting below it. Size sets the current default
expanded width; public variables override size through private fallbacks.

## 11. Environmental behavior

All edge geometry is logical and follows RTL/writing direction. The root clips
horizontal overflow only during a rail width transition while its inner panel
retains the full expanded width; labels therefore do not flash as one-character
columns. Once collapsed, the panel settles to the real rail width so List icon
surfaces retain their normal complete box geometry. Plain header/footer text is
hidden at rest in rail mode; authors can provide a rail-only replacement.
Arbitrary content-slot text uses a single clipped line at rest so an authored
paragraph cannot inflate the rail into one-character columns. Authors use
`data-citry-sidebar-expanded-only` when that content should disappear entirely.
Long content wraps inside the owned vertical scroll area. Sticky mode uses a
viewport-sized maximum rather than a forced block size, avoiding document or
iframe height feedback. Narrow containers may use off-canvas collapse but do
not automatically become modal. Reduced motion disables width
transitions, forced colors retains borders/focus, touch targets remain at least
44 CSS pixels, nested color schemes inherit, and print expands content while
omitting the toggle.

Expand and collapse labels are catalog messages with explicit prop overrides.
Stable label spans use server `tr()` plus `$c-tr`, so client locale changes
update both strings even while one is hidden. Application slot content retains
its own locale, formatting, matching, and bidi ownership.

## 12. Overlay and layering behavior

Sidebar is always in normal document/layout ancestry and never creates a
scrim, focus trap, inert page, top-layer entry, or scroll lock. Use Drawer for
those modal behaviors. Popovers and Menus inside Sidebar keep their own layer
ownership and close normally if the off-canvas panel becomes hidden.

## 13. Collections, async data, and identity

Sidebar owns no navigation collection, current route, loading, or async work.
Its stable `id` links toggle and panel identity. `CList`, `CDisclosure`, and
`CMenu` own their respective collection and interaction contracts.

## 14. Server render, morph, and cleanup

Server HTML reflects the initial collapsed state and remains meaningful when
expanded without JavaScript. Client activation adds one toggle listener and
one managed prop effect. Correlated rerenders use the current committed state
when the server baseline is unchanged. Cleanup removes the listener, marker,
and managed effect; no global state remains.

## 15. Security and content trust

Slots use ordinary Citry escaping. Root attrs cannot replace native landmark
identity/name, collapse state, parts, visibility, focus, or child-replacement
directives. Toggle/panel ownership is not exposed through attrs. Author hooks
are fixed data attributes, not selectors or expressions accepted as inputs.

## 16. Assets and performance

The family contributes compact CSS and one bounded initializer. There is no
observer, document listener, breakpoint listener, layout measurement, icon,
font, network request, overlay runtime, or duplicated slot tree.

## 17. Acceptance matrix

Evidence covers both native tags, label/ID relationships, all collapse modes,
controlled/uncontrolled requests, focus repair, prop removal/invalid episodes,
slots, CList rail names, attrs, RTL/logical sides, sticky/floating/sizes,
overflow, forced colors, reduced motion, print, localization override/live
switch, cleanup, axe, exports, typing, docs, quality routes, assets and wheel.

## 18. Compatibility classification

The public class, inputs, slot data, callback detail, parts, attributes,
messages and variables are stable. Private markers, classes, internal state,
CSS fallback variables and reconciliation order are private.

## 19. Public documentation contract

The guide includes persistent navigation, rail collapse with CList, off-canvas
collapse, controlled state, sticky/floating layout, header/footer, RTL,
customization, Drawer composition guidance, accessibility, and the final
structured Translation keys table.

## 20. Open decisions and deferred work

Remote triggers, resizable width, persisted preference, hover expansion,
global shortcuts, responsive mode selection, AppShell inset accounting,
mobile modal conversion, bundled navigation items and multi-Sidebar providers
are deferred. Each adds ownership or accessibility policy beyond this family.

## 21. Internationalization

`citry-ui-sidebar-expand` and `citry-ui-sidebar-collapse` name the toggle state.
`expand_label` and `collapse_label` override them per instance and suppress the
corresponding catalog binding. Both source messages live at the end of the
component class and use `messages_locale="en-US"`.
