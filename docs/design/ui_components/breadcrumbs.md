# Citry UI Breadcrumbs specification

**Status (2026-08-09): production implementation, structured API, nine public
examples, quality route, scaling profile, wheel boundary, and focused server
and Chromium evidence are complete. Human visual and assistive-technology
release review remains.**

## 1. Purpose and product bar

`CBreadcrumbs` shows the current page within a hierarchical site structure and
links back to ancestors. It is a zero-JavaScript semantic `nav > ol > li`
component for finite server-owned trails.

## 2. Prior art and complaints

| Source | Reviewed | Surface and decision |
|---|---|---|
| Citry UI native collection policy | workspace, 2026-08-08 | Use copied record snapshots, exact strings, native navigation, scoped slots, public parts, and zero client runtime. |
| Vuetify Breadcrumbs | 4.0.7/current sources and Vuetify0, 2026-08-08 | Adopt item records, divider customization, item slot, size, current-page inference, and semantic navigation. Defer responsive collapse and route providers. |
| Material UI Breadcrumbs | 9.0.1, 2026-08-08 | Adopt ordered list, labelled nav, hidden separators, linked or plain current page. Defer max-items expansion until a menu/overflow owner exists. |
| Mantine Breadcrumbs | current, 2026-08-08 | Adopt concise separator and gap customization. Add stronger native semantics than an arbitrary child separator utility. |
| Chakra Breadcrumb | 3.35, 2026-08-08 | Adopt root/list/item/link/current/separator anatomy without requiring six public structural components. |
| WAI-ARIA APG Breadcrumb | current, 2026-08-08 | Navigation landmark label, ordered ancestor links, `aria-current="page"` on a linked current page, no custom keyboard model. |
| W3C WCAG technique G65 | current, 2026-08-08 | Preserve location hierarchy and native links as one way to meet location guidance. |

Frequent failures are unlabelled landmarks, separators announced as content,
unordered div soup, no current-page relationship, wrapping that becomes
unreadable, and hidden middle items with no discoverable expansion.

## 3. Public composition and anatomy

```py
items = (
    CBreadcrumbItem("Home", "/"),
    CBreadcrumbItem("Library", "/library"),
    CBreadcrumbItem("The green room"),
)
```

```citry-html
<c-CBreadcrumbs c-items="items" />
```

The root is a labelled `nav`; its direct child is an `ol`; each record owns one
`li`. Links are native anchors. The final item is current: a final link receives
`aria-current="page"`, while a final non-link is current by list position.
Separators live inside preceding items and are `aria-hidden`.

## 4. Server inputs and client inputs

Server inputs are required `items`, `label="Breadcrumbs"`, `separator="/"`,
`size="md"`, `wrap=True`, `class_`, `style`, `attrs`, and `list_attrs`.
`CBreadcrumbItem` fields are `label`, optional `href`, and optional `attrs`.
Sizes are `sm`, `md`, and `lg`.

There are no client inputs. Trails follow server routing and page hierarchy;
browser-side route derivation belongs to router integration or a future
extension.

## 5. State model

Breadcrumbs has no interactive component state. The final record is current.
`data-size` and `data-wrap` reflect presentation. Links retain native visited,
hover, active, and focus states without component-owned mirrors.

## 6. Slots and slot data

The optional `item` slot receives `{item: CBreadcrumbItem, index: int,
is_current: bool, attrs: Mapping[str, object]}`. It replaces one item body while
the component retains `li` ownership. Consumers must bind `attrs` to preserve
`href` and `aria-current`.

The optional `separator` slot receives `{index: int}` and replaces the visual
separator after one non-current item. Its wrapper remains `aria-hidden`.

## 7. Callbacks, native events, and methods

There are no callbacks or methods. Native anchor events and browser navigation
remain available through item attrs or scoped item content. Breadcrumbs adds no
custom DOM events.

## 8. Semantics, keyboard, focus, and assistive technology

The labelled nav is a navigation landmark; the ordered list exposes hierarchy;
native anchors use browser keyboard behavior. Separators never enter the
accessibility tree. A linked final item receives `aria-current="page"`; a plain
final item needs no redundant ARIA current marker but receives it on its span
for stable inspection and AT clarity.

## 9. Native forms and validation

Breadcrumbs does not participate in forms or constraint validation. Links may
contain ordinary query strings and fragments. Button-like actions and form
submission do not belong in the trail.

## 10. Styling and theme contract

Public variables are `--cui-breadcrumbs-foreground`,
`--cui-breadcrumbs-link-color`, `--cui-breadcrumbs-current-color`,
`--cui-breadcrumbs-separator-color`, `--cui-breadcrumbs-gap`, and
`--cui-breadcrumbs-focus-color`.

Stable parts are `breadcrumbs`, `list`, `item`, `link`, `current`, and
`separator`. Stable reflections are `aria-label`, `aria-current`, `href`,
`data-size`, and `data-wrap`. Each public variable resolves through a private
effective variable.

## 11. Environmental behavior

Default wrap permits multi-line trails at narrow widths and zoom. `wrap=False`
keeps one line and makes the ordered list a horizontal scroll container without
adding a forced tab stop. Layout, separator order, and scrolling follow RTL.
Forced colors keep separators visible; print makes links use current text color.

## 12. Overlay and layering behavior

Breadcrumbs creates no overlay or stacking context. Responsive ellipsis menus
are deferred until Menu/Popover supplies focus, dismissal, top-layer, and
disclosure ownership.

## 13. Collections, async data, and identity

Items are a finite server-owned sequence snapshotted once per render. Every
record and nested attrs mapping is copied and validated before output. Source
order is hierarchy order. Empty trails fail; duplicate labels and hrefs remain
valid because hierarchical paths can repeat names and destinations.

## 14. Server render, morph, and cleanup

Breadcrumbs renders entirely on the server, owns no JavaScript, listener,
timer, observer, or cleanup. A server rerender replaces trail records through
normal Citry identity and native anchor focus behavior.

## 15. Security and content trust

Labels, landmark label, separator, and href become exact plain strings,
normalize line endings, and reject U+0000. Labels and landmark names must be
nonempty; supplied href must be nonempty. Attribute maps are copied and reject
owned semantics, runtime namespaces, structural directives, object spreads,
visibility removal, href replacement, role replacement, and current-page
replacement. Href scheme policy remains application-owned trusted navigation
input.

## 16. Assets and performance

Breadcrumbs adds one shared CSS asset and zero JavaScript. DOM cost is one nav,
one list, and bounded item/link/separator nodes. Diagnostic scaling records 1,
10, 100, 500, and 1,000 items without a timing gate.

## 17. Acceptance matrix

Checked-in server tests cover schema, records, nav/list/item semantics, linked
and plain current pages, hidden separators, slots/data, exact strings, copied
attrs, trust boundaries, root/list destinations, wrapping, and public CSS.
Focused Chromium tests cover landmark/list/link/current semantics, Tab order,
public variables, horizontal overflow, and RTL.

Repository qualification must cover all previews, shared axe/Nu HTML and
screenshot profiles, host CSS, wheel contents, assets, and diagnostic scaling.
Human release review retains long translated trails, mobile/touch scrolling,
zoom, forced colors, print, and visual polish.

## 18. Compatibility classification

Stable: record shape, native anatomy/semantics, inputs, slots/data, public
variables, parts, and reflections. Evolvable: exact fallback colors, type
scale, gap, and underline treatment. Unsupported: automatic routes,
browser-reactive items, responsive ellipsis, menus, actions, multiple current
items, and arbitrary structural child components.

## 19. Public documentation contract

The public page teaches common hierarchy, linked/current records, custom
separators, sizes, wrapping/scrolling, item slots, routing composition,
customization, and accessibility. Nine component-owned previews use one
books-and-libraries theme and map every visual or structural contract to
rendered evidence.

## 20. Open decisions and deferred work

Responsive collapse, ellipsis disclosure, route-provider integration, icons,
and explicit current-item selection remain deferred. Revisit collapse only
after Menu/Popover exists; revisit a client route adapter only with one actual
router integration and a stable locale contract for the landmark/expand text.

## 21. Internationalization

The navigation landmark is the family-owned translatable output. The
structured [Translation keys table](../../../packages/py/citry_ui/citry_ui/components/cbreadcrumbs/api.yml)
is normative: the catalog default renders on the server and `$c-tr` keeps the
stable `aria-label` current in a client-enabled provider. An explicitly supplied
`label` remains caller-owned and registers no catalog binding.
