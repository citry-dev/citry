# Citry UI List specification

Status: production implementation pass complete. Runtime, public documentation,
focused server/browser evidence, previews, quality and scaling scenarios, and
wheel qualification are wired. Human visual review, independent implementation
review, multi-browser checks, and final release qualification remain.

## 1. Purpose and product bar

`CList` and `CListItem` present semantic ordered/unordered collections, dense application indexes, navigation links, whole-row actions, media, descriptions, and secondary content without Menu or selection-widget keyboard behavior.

## 2. Prior art and complaints

Sources inspected 2026-08-09: current Vuetify List sources, MUI List family docs/source, Mantine List docs/source, Chakra List docs/source, HTML list/content-model rules, and WAI guidance for lists and current links. Vuetify/MUI expose large subcomponent families; Mantine emphasizes semantic list markers. Citry keeps two components and four item slots. Expansion, stateful selection, virtualization, sticky subheaders, and Menu semantics remain separate.

## 3. Public composition and anatomy

`CList` renders `ul` or `ol`. Direct `CListItem` renders `li`, then a static `div`, native `a`, or native `button type="button"` surface containing optional start, required default body, optional description under that body, and optional end content. Static Item bodies use flow-content wrappers so nested Lists are conforming; link and Button bodies remain phrasing-content wrappers. Nested Lists establish a new Item context.

## 4. Server inputs and client inputs

List server inputs: `ordered`, `start`, `reversed`, `marker`, `density`, `variant`, `divided`, `label`, `class_`, `style`, `attrs`. Item server inputs: `href`, `action`, `disabled`, `current`, `class_`, `style`, `attrs`, `surface_attrs`. Version 1 has no client inputs because changing `href`/action/static anatomy is structural; server rerender owns it.

## 5. State model

The family owns no selection. `current=True` is valid only for an enabled link and emits `aria-current="page"`. Action items are ordinary Buttons, not toggles. Disabled links render a noninteractive static surface; disabled action items use native disabled.

## 6. Slots and slot data

Item slots are `start {}`, required `default {}`, optional `description {}`, and optional `end {}`. Start is for CIcon/CAvatar. End is for metadata or a secondary control. Link and action Items require phrasing, noninteractive slot content. Static Items accept flow content and may contain a nested List or interactive end content, so interactive elements never nest.

## 7. Callbacks, native events, and methods

There are no component callbacks/methods. Native events may be placed on the link/Button surface through `surface_attrs`; component-tag events remain on the `li` root and may observe bubbling. Links navigate and action Buttons activate natively.

## 8. Semantics, keyboard, focus, and assistive technology

Native list/listitem semantics remain intact. Links and Buttons alone enter Tab order. Current navigation links expose `aria-current=page`. Static Items do not become focusable. Disabled link surfaces are not links. The family adds no arrows, roving focus, typeahead, or listbox/Menu roles.

## 9. Native forms and validation

Action items use `type="button"`; they never submit or validate. Secondary controls retain their own Form behavior. CList does not inherit CForm disabled state because content/navigation lists are not Form controls.

## 10. Styling and theme contract

Markers are `none`, `disc`, or `decimal`; ordered Lists default to decimal when marker is none only if the caller selects decimal explicitly, keeping application-list defaults compact. Densities are `comfortable` and `compact`; variants are `plain` and `surface`. Public parts are `list`, `list-item`, `surface`, `start`, `body`, `description`, and `end`. Public variables are `--cui-list-gap`, `--cui-list-padding`, `--cui-list-item-padding`, `--cui-list-radius`, `--cui-list-foreground`, `--cui-list-muted`, `--cui-list-background`, `--cui-list-hover-background`, `--cui-list-current-background`, `--cui-list-divider-color`, `--cui-list-marker-color`, and `--cui-list-focus-ring`. Stable reflections are `data-marker`, `data-density`, `data-variant`, `data-divided`, `data-current`, `data-disabled`, `data-interactive`, and `aria-current`.

## 11. Environmental behavior

Grid anatomy uses logical properties and supports RTL. Text and long URLs wrap. Narrow rows allow body shrink while start/end remain intrinsic. Forced colors preserves borders/current/focus. Print removes hover-only treatment. Nested schemes resolve inherited tokens locally.

## 12. Overlay and layering behavior

Lists create no overlay or stacking context. Inline secondary overlays may be clipped only by caller containers; CList itself keeps overflow visible.

## 13. Collections, async data, and identity

Identity and ordering belong to caller data and Citry morph keys. CList performs no filtering, fetching, selection, pagination, or virtualization. Large/windowed collections require a future VirtualList or project-owned windowing.

## 14. Server render, morph, and cleanup

Output is complete semantic HTML/CSS with zero family JavaScript. Server context requires every Item to belong to a List and nested Lists establish a new Item context. Direct-child placement is an authoring contract in version 1 rather than a spoof-resistant settled-DOM validator. No cleanup is required.

## 15. Security and content trust

href/label strings are de-trusted. Attribute maps are copied. Root attrs cannot replace list semantics/children/runtime fields. Surface attrs cannot replace element identity, href, disabled/current semantics, children, focus ownership, or runtime fields. Slot markup remains trusted author content under the documented content model.

## 16. Assets and performance

The family adds CSS only and O(n) server HTML. Diagnostics record assets and bounded 1/10/100/500/1,000 Item output without release timing thresholds.

## 17. Acceptance matrix

Checked-in server tests cover `ul`/`ol`, start/reversed, surface types, current/disabled rules, all slot wrappers, invalid combinations, Item-without-List rejection, and zero JavaScript. Focused Chromium tests cover native list/link/Button/static anatomy, disabled and current surfaces, native Tab order, and public variable/selector overrides. The shared quality scenario supplies automated axe evidence, and the docs harness exercises the public previews. Explicit AX count snapshots, direct-child misuse enforcement, narrow/RTL/nested layout, forced colors, print, nested color schemes, multi-browser behavior, and final visual judgment remain release qualification.

## 18. Compatibility classification

Stable: two components, inputs, slots, semantic surfaces, public selectors/variables, and no-selection boundary. Evolvable: private wrappers/classes. Deferred: selected item group, expansion, subheader component, virtualization, drag/reorder, Menu behavior, and client structural inputs.

## 19. Public documentation contract

The guide must show semantic content, ordered markers, navigation links/current page, whole-row actions, start/body/description/end anatomy, secondary controls, nesting, density/dividers, and customization. It must state when to use Menu, Tabs, or DataTable instead.

## 20. Open decisions and deferred work

Real projects will determine whether a dedicated Subheader, ListGroup, or selection model is warranted. Those features must not accrete onto `CListItem` without a fresh interaction contract.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
