# Citry UI Pagination specification

Status: production implementation pass complete. Runtime, public documentation,
focused server/browser evidence, previews, quality and scaling scenarios, and
wheel qualification are wired. Human visual review, independent implementation
review, multi-browser checks, and final release qualification remain.

## 1. Purpose and product bar

`CPagination` navigates a finite sequence of numbered pages with native links or browser-owned Buttons. It must stay useful under server rendering, long page counts, narrow layouts, RTL, keyboard access, and client-controlled page changes.

## 2. Prior art and complaints

Sources inspected 2026-08-09: current Vuetify Pagination sources, MUI Pagination/usePagination docs/source, Mantine Pagination docs/source, React Aria navigation guidance, native `nav`/link/Button semantics, and WAI landmark guidance. Common APIs expose count/current page, sibling and boundary counts, previous/next and optional first/last controls, responsive compaction, links, callbacks, size, and variants. Citry keeps deterministic range configuration and native URLs; compound anatomy and automatic container-query labels remain deferred.

## 3. Public composition and anatomy

The root is a named `nav`, containing one `ul`. Each control is one `li` with an `a`, `button type="button"`, or inert ellipsis span. Current page uses `aria-current="page"`. Previous/next and optional first/last controls share the same stable control surface.

## 4. Server inputs and client inputs

Server inputs: `pages`, `page`, `href`, `siblings`, `boundaries`, `show_controls`, `show_edges`, `disabled`, `variant`, `size`, accessible labels, `class_`, `style`, `attrs`. Client inputs: `page`, `disabled`, `variant`, `size`, `onPageChange`. `href` is a server string containing `{page}` and produces native links.

## 5. State model

Page numbering starts at 1. `1 <= page <= pages`. Omitted client page releases ownership to browser-local state initialized by Python. Valid supplied client page wins. Invalid values report once per continuous episode and retain the prior valid state. Structure is rebuilt deterministically after a client page change so the compact range stays correct.

## 6. Slots and slot data

Version 1 has no slots. Labels are plain inputs so JS rebuilds and server output remain identical. Rich/custom item rendering is deferred to a compound Pagination family after real usage.

## 7. Callbacks, native events, and methods

`onPageChange(page, detail)` runs for an enabled noncurrent control. Detail includes `previousPage`, `page`, `kind`, and `sourceEvent`. For native links, navigation continues unless the callback prevents the source event. For Button mode, uncontrolled state updates after the callback.

## 8. Semantics, keyboard, focus, and assistive technology

Native links/Buttons provide activation and focus. The named `nav` is a landmark. Current page exposes `aria-current=page`. Disabled Button controls use native disabled; unavailable link controls render Buttons so no fake disabled link is emitted. Ellipses are hidden from assistive technology. No arrow-key or roving-focus behavior is added.

## 9. Native forms and validation

Button controls use `type="button"` and never submit or validate. Pagination ignores Form state; it is navigation, not a Form control.

## 10. Styling and theme contract

Variants are `soft`, `outline`, and `plain`; sizes are `sm`, `md`, and `lg`. Public parts are `pagination`, `list`, `control`, and `ellipsis`. Public variables are `--cui-pagination-gap`, `--cui-pagination-control-size`, `--cui-pagination-radius`, `--cui-pagination-foreground`, `--cui-pagination-background`, `--cui-pagination-border-color`, `--cui-pagination-current-background`, `--cui-pagination-current-foreground`, `--cui-pagination-disabled-opacity`, and `--cui-pagination-focus-ring`. Stable reflections are `aria-current`, `data-current`, `data-page`, `data-kind`, `data-disabled`, `data-variant`, and `data-size`.

## 11. Environmental behavior

The list wraps rather than overflowing. Logical arrow glyphs mirror in RTL through the component stylesheet. Forced colors preserves current and focus distinctions. Reduced motion removes transitions. Print retains page/current borders.

## 12. Overlay and layering behavior

Pagination creates no overlay or stacking context.

## 13. Collections, async data, and identity

The compact range always includes configured boundaries, current-page siblings, and gap ellipses. Gaps of one page expand to that page rather than an ellipsis. Buttons are keyed by semantic kind/page during JS rebuild. Remote loading belongs to the page owner.

## 14. Server render, morph, and cleanup

Server output is complete and link mode works without JS. Client initialization binds one root click listener and one effect, rebuilding only the bounded visible range. Cleanup removes listener/effect. Server rerender remains authoritative and reinitializes from fresh data.

## 15. Security and content trust

Labels and href pattern are de-trusted exact strings. `{page}` substitution does not evaluate format expressions. `attrs` cannot replace nav role/name, children, public fields, focus ownership, or Citry runtime fields. Generated JS uses DOM APIs and `textContent`, never HTML strings.

## 16. Assets and performance

The visible DOM is O(boundaries + siblings), independent of total pages. One shared CSS/JS definition serves all instances. Repository tools record assets and bounded server output; no benchmark threshold is claimed.

## 17. Acceptance matrix

Checked-in server tests cover compact-range expansion, URL substitution, native link and Button output, current semantics, controls/edges, invalid inputs, hostile attrs, and stable reflections. Focused Chromium tests cover native URLs/current-page semantics, controlled and uncontrolled Button updates, callback details, visible-range rebuilding, and one-diagnostic-per-invalid-client episode with last-valid retention. The shared quality scenario supplies automated axe evidence, and the docs harness exercises the public previews. Prevented-link behavior, explicit focus retention, RTL glyphs, narrow wrapping, public CSS overrides, forced colors, cleanup, multi-browser behavior, and final visual judgment remain release qualification.

## 18. Compatibility classification

Stable: inputs, callback, range rules, link/Button boundary, semantics, selectors, and variables. Evolvable: private classes and rebuild internals. Deferred: slots/compound controls, automatic responsive label, start values, page-size selection, cursor pagination, and localization provider integration.

## 19. Public documentation contract

The guide must lead with native URL pagination, then Button-controlled pagination, long ranges, controls/edges, sizing/variants, disabled/current behavior, and customization. It must distinguish Pagination from Table pagination policy.

## 20. Open decisions and deferred work

A later compound API may expose Items/Previous/Next/Label if projects need custom anatomy. Cursor-based pagination belongs to a separate component because it has no finite page count.
