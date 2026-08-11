# Tree

**Status:** implementation complete with focused server, browser, docs,
schema, scenario, asset, and package evidence. Manual assistive-technology,
touch-device, and visual review remains release qualification.

## 1. Purpose and product bar

`CTree` presents application data with parent and child relationships.
`CTreeItem` declares stable identity, a plain accessible label, optional
children, disabledness, and panel-independent application action identity.
Tree is appropriate for file explorers, object browsers, and similar compact
application widgets. Ordinary site navigation should usually use disclosure
and link patterns instead.

## 2. Prior art and complaints

| Source | Review date | Surface | Citry decision |
|---|---|---|---|
| WAI-ARIA APG Tree View | 2026-08-10 | tree/treeitem/group anatomy, roving focus, arrows, Home/End, typeahead, selection | Adopt the vertical DOM-focus pattern and distinguish focus, expansion, selection, and action. |
| MUI X Rich Tree View | 2026-08-10 | controlled expansion/selection, multi-select, disabled nodes, customization, paid advanced features | Adopt controlled vectors and multi-selection; defer editing, loading, virtualization, and reorder. |
| Chakra UI Tree View | 2026-08-10 | collection state, explicit expansion, async loading, links, checkbox trees, mutation | Adopt concise state callbacks; avoid requiring a client collection store for server templates. |
| PrimeVue Tree | 2026-08-10 | nested data, controlled expansion, selection, filtering, accessible keyboard model | Adopt simple nested declarations; leave filtering to application composition. |
| React Spectrum Tree View | 2026-08-10 | hierarchical collections, selection, actions, drag/drop and embedded controls | Adopt separate selection and action callbacks; defer embedded-control/grid and drag/drop models. |
| Vuetify 2 Treeview | 2026-08-10 | activatable nodes, child loading, selection propagation and slots | Preserve composable child declarations while avoiding implicit parent/child checkbox propagation. |

Ecosystem failures cluster around focus being confused with selection,
collapsed descendants remaining interactive, inaccessible mouse-only
expansion, and oversized APIs combining loading, filtering, editing, drag, and
checkbox propagation. Citry keeps the core tree state exact and composable.

## 3. Public composition and anatomy

```text
div role=tree
└─ div role=treeitem
   ├─ span row
   │  ├─ span indicator
   │  └─ span label
   └─ div role=group
      └─ div role=treeitem
```

`CTree` accepts one or more direct `CTreeItem` declarations. An Item's default
content accepts only child `CTreeItem` declarations. Values are unique across
the whole Tree and labels are nonempty plain strings. Nested `CTree` roots are
valid only inside separately authored application content, not inside an Item
declaration collection.

## 4. Server inputs and client inputs

Root server inputs: required `label`, `expanded: Sequence[str]=()`,
`selected: Sequence[str]=()`, `selection_mode: "none"|"single"|"multiple"`,
`disabled`, `variant: "plain"|"soft"|"outline"`, `size: "sm"|"md"|"lg"`,
`class_`, `style`, and `attrs`. Single mode accepts at most one selected value;
none mode accepts none.

Item server inputs: required `value`, required `label`, `disabled`, `class_`,
`style`, and `attrs`. Item identity and declaration shape are structural.

Client `expanded` and `selected` vectors are controlled while supplied;
`null` releases each state independently. `selectionMode`, root `disabled`,
`variant`, and `size` are reactive configuration. Invalid client values report
once per continuous episode and use the last valid state.

## 5. State model

Expansion and selection are separate ordered sets of canonical values. Only
branches may be expanded. Selection mode none emits no `aria-selected`; single
keeps zero or one value; multiple toggles independent values without modifier
keys. Focus is one active visible Item and does not imply selection. Disabled
Items remain in Arrow-key navigation but cannot expand, select, or act.

Uncontrolled requests commit immediately. Controlled requests notify and wait
for owner acceptance. Collapsing a branch whose descendant has focus moves
focus to the branch. Removing the focused Item moves focus to the next visible
Item, then previous, then first.

## 6. Slots and slot data

| Owner | Slot | Required | Data | Fallback |
|---|---|---:|---|---|
| `CTree` | `default` | yes | `{}` | Items only |
| `CTreeItem` | `default` | no | `{parent_value, level}` | leaf Item |

Item labels are string inputs so typeahead, accessible naming, and settled
structure have one canonical source. Rich row controls are intentionally not
accepted because interactive descendants change the pattern to a treegrid.

## 7. Callbacks, native events, and methods

`onExpandedChange(expanded, detail)`, `onSelectionChange(selected, detail)`,
and `onAction(value, detail)` are client callbacks. Detail includes the changed
value, prior state where relevant, controlled ownership, source, Item, and
native event. Selection uses click or Space; action uses Enter or double-click.
No custom DOM events or imperative methods are exposed.

## 8. Semantics, keyboard, focus, and assistive technology

The named root has `role="tree"`. Items have `role="treeitem"`, owned
`aria-label`, roving `tabindex`, and `aria-disabled`; selectable Items have
`aria-selected`. Branches alone have `aria-expanded` and contain a direct
`role="group"` child.

Down/Up move through visible Items. Right expands a closed branch or moves to
its first child. Left collapses an open branch or moves to its parent. Home/End
move to first/last visible Item. Printable keys perform normalized buffered
typeahead with repeated-character cycling. Tab
enters once and leaves normally. RTL does not reverse the conventional Tree
expansion keys.

## 9. Native forms and validation

Tree is not a form control and contributes no FormData. It renders no native
Buttons, so Enter and Space cannot submit a containing form. Native disabled
fieldsets dominate the entire Tree while preserving the first-Legend
exception. Controls are prohibited inside Item declarations.

## 10. Styling and theme contract

Variants: plain, soft, outline. Sizes control row height, indentation, and
indicator geometry. Stable parts: `tree`, `item`, `row`, `indicator`, `label`,
and `group`.

Public variables: `--cui-tree-indent`, `--cui-tree-row-gap`,
`--cui-tree-row-padding`, `--cui-tree-radius`, `--cui-tree-background`,
`--cui-tree-border-color`, `--cui-tree-hover-background`,
`--cui-tree-selected-background`, `--cui-tree-selected-color`,
`--cui-tree-muted-color`, and `--cui-tree-focus-color`.

Public root reflections: `data-selection-mode`, `data-disabled`,
`data-variant`, `data-size`. Items expose `data-value`, `data-level`,
`data-expanded`, `data-selected`, and `data-disabled`.

## 11. Environmental behavior

Logical indentation supports LTR and RTL. Labels wrap without horizontal
overflow. Reduced motion removes indicator transitions; forced colors keeps
focus and selection boundaries; print expands no extra branches and removes
interactive focus decoration. No library-authored visible string is added.

## 12. Overlay and layering behavior

Tree creates no overlay, inert region, focus trap, or scroll lock.

## 13. Collections, async data, and identity

Canonical Item values are stable unique identity. Server morphs may add,
remove, or reorder Items. Compatible retained roots preserve uncontrolled
expanded and selected values that still exist and recover focus by visible
order. Async loading is application-owned in v1; a loading branch should not
claim children until those Items exist.

## 14. Server render, morph, and cleanup

Server output contains full nested roles, initial collapsed visibility,
selection, expansion, and one roving Tab stop. Client activation installs
constant delegated click, double-click, key, and focus listeners plus bounded
root/fieldset observers. Cleanup removes all listeners, observers, timers, and
the private readiness marker while retaining only compatible semantic state.

## 15. Security and content trust

Values and labels are canonical plain strings rejecting U+0000; values also
reject ASCII whitespace. Slots use ordinary trusted-template boundaries.
Attrs cannot replace owned identity, roles, focus, visibility, selection,
expansion, children, or runtime attributes. Typeahead reads `textContent` and
never HTML. Callback values remain data.

## 16. Assets and performance

One CSS asset and one initializer are added. Each Tree has constant delegated
listeners and performs linear visible-order work only on state changes or
navigation. Closed descendants remain in the DOM but hidden and inert. There
is no icon, font, network, overlay, or storage dependency.

## 17. Acceptance matrix

Automated evidence covers declaration grammar, duplicate and unknown values,
server anatomy, expansion, selection modes, controlled rejection/acceptance
and release, full keyboard navigation, typeahead, disabled/fieldset behavior,
collapse and removal focus recovery, form safety, nested levels, CSS parts and
variables, RTL, narrow layout, reduced motion, forced colors, print, axe,
cleanup, exports, docs, API projection, assets, scenarios, and packaging in
Chromium, Firefox, and WebKit. Manual checks cover screen readers, coarse
touch, zoom, and visual polish.

## 18. Compatibility classification

Public components, inputs, callbacks, parts, attributes, and variables are
stable. Generated DOM IDs, classes, private readiness markers, normalization
tasks, observer strategy, and internal focus bookkeeping are private.

## 19. Public documentation contract

Examples cover a file tree, controlled expansion, single and multiple
selection, keyboard behavior, disabled Items, presentation, and
customization.

## 20. Open decisions and deferred work

Async child loading, virtualization, filtering, checkbox propagation, links,
inline rename, drag/drop reorder, embedded row controls/treegrid behavior,
horizontal trees, and imperative collection stores require separate design
and evidence.
