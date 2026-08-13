# Citry UI Button Group specification

Status: production implementation pass complete. Runtime, public documentation,
focused server/browser evidence, previews, quality and scaling scenarios, and
wheel qualification are wired. Human visual review, independent implementation
review, multi-browser checks, and final release qualification remain.

## 1. Purpose and product bar

`CButtonGroup` gives related actions one accessible name, one layout axis, and optional attached geometry. It never owns selection; use `CToggleGroup` when Buttons represent persistent choices. The bar is the small, predictable action-group surface found in Vuetify, MUI, Chakra, and React Spectrum without duplicating `CButton` inputs.

## 2. Prior art and complaints

Sources inspected 2026-08-09: current Vuetify Button/BtnToggle sources, MUI ButtonGroup docs/source, Chakra Button/Group docs/source, React Spectrum ButtonGroup docs, WAI-ARIA group guidance, and native Button semantics. MUI requires immediate Button children and exposes shared presentation. Chakra distinguishes ordinary and attached groups. Spectrum emphasizes related actions and responsive overflow. Citry keeps grouping and attachment, but leaves presentation on each Button so child reflections stay truthful and mixed actions remain possible.

## 3. Public composition and anatomy

The root is `<div role="group">` with `aria-label`, followed by the default slot. Direct `CButton` children receive attached geometry through public Button selectors. Other interactive descendants retain native semantics but do not receive joined-corner styling.

## 4. Server inputs and client inputs

Server inputs are `label`, `orientation`, `attached`, `grow`, `class_`, `style`, and `attrs`. There are no client inputs in v1. A changing group is rendered again by Python.

## 5. State model

The component has no selection, pressed, disabled, loading, or action state. Each Button remains authoritative for those states.

## 6. Slots and slot data

The required default slot receives `{}` and holds related actions. Authors should keep primary actions direct children when attached styling is expected.

## 7. Callbacks, native events, and methods

There are no component callbacks or methods. Native events originate from the authored Buttons or links; the group does not synthesize events.

## 8. Semantics, keyboard, focus, and assistive technology

The root uses `role="group"` and a required nonempty accessible label. Tab order and activation remain native. The group is never focusable and adds no roving focus. `data-orientation` exposes its visual axis because `aria-orientation` is not supported by the ARIA `group` role.

## 9. Native forms and validation

Buttons retain their own Form ownership, type, successful-control behavior, validation, and reset semantics. Group attrs cannot add disabled or Form ownership.

## 10. Styling and theme contract

Public variables are `--cui-button-group-gap`, `--cui-button-group-radius`, and `--cui-button-group-border-width`. `attached=True` joins direct Button roots and overlaps adjacent borders by one configurable width. `grow=True` gives each direct Button equal flexible width. The public parts are `button-group` and the direct child `button` part owned by `CButton`. Stable reflections are `data-orientation`, `data-attached`, and `data-grow`. Every declaration remains on its own line and uses logical properties.

## 11. Environmental behavior

Vertical and horizontal layouts work in LTR and RTL. Attached geometry uses logical first/last corners. Focus rings remain visible above neighboring Buttons. Narrow groups may wrap only when `attached=False`; attached groups scroll or shrink according to their container and Button content.

## 12. Overlay and layering behavior

The group creates no overlay or stacking context. Focused direct Buttons receive only a local z-index with positioned layout so their outline is not hidden by border overlap.

## 13. Collections, async data, and identity

Button identity belongs to the caller and Citry morph keys. The group performs no child registry, filtering, or async work.

## 14. Server render, morph, and cleanup

Output is complete server HTML and CSS with zero JavaScript. Morphing preserves child Button behavior under Citry’s normal ownership rules. No cleanup is required.

## 15. Security and content trust

`label` is de-trusted to an exact plain string and rejects empty/NUL values. `attrs` is copied and may add inert native, data, targeted Alpine, and event attributes, but cannot replace role, naming, orientation, public reflections, children, focus ownership, or Citry runtime fields.

## 16. Assets and performance

The family adds CSS only. Repository diagnostics record raw/gzip/Brotli assets and bounded server output at 1, 10, 100, 500, and 1,000 groups. No timing claim is a release threshold.

## 17. Acceptance matrix

Checked-in server tests cover schema/defaults, both orientations, attached/grow output, required naming, hostile attrs, slot presence, and zero JavaScript. Focused Chromium tests cover role/name, native Tab order, attached overlap, vertical/grow geometry, disabled child behavior, and a public selector override. The shared quality scenario supplies automated axe evidence, and the public previews are exercised by the docs harness. RTL geometry, nested color schemes, forced colors, narrow-content stress, multi-browser behavior, and final visual judgment remain release qualification rather than checked-in focused claims.

## 18. Compatibility classification

Stable: inputs, group semantics, public reflections, selectors, variables, and zero-selection boundary. Evolvable: private classes and exact internal CSS. Deferred: automatic responsive overflow, shared child presentation, split-menu behavior, and toolbar semantics.

## 19. Public documentation contract

The guide must show related actions, attached versus spaced groups, orientation, growth, mixed Button states, links/split-action composition, and public CSS customization. It must state that ButtonGroup does not select Buttons.

## 20. Open decisions and deferred work

Shared Button presentation remains deferred until Citry can preserve explicit-child precedence and truthful child reflections. `CToolbar` owns toolbar semantics; automatic overflow collapsing still needs a separate OverflowList design. Selection belongs to `CToggleGroup`.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
