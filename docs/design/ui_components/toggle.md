# Citry UI Toggle specification

Status: production implementation pass complete. Runtime, public documentation,
focused server/browser evidence, previews, quality and scaling scenarios, and
wheel qualification are wired. Human visual review, independent implementation
review, multi-browser checks, and final release qualification remain.

## 1. Purpose and product bar

`CToggle` is a two-state pressed Button. `CToggleGroup` coordinates related single or multiple choices. Unlike `CSwitch`, a Toggle changes how content is presented or which tools are active rather than switching an immediate setting. Unlike `CButtonGroup`, the group owns persistent selection.

## 2. Prior art and complaints

Sources inspected 2026-08-09: current Vuetify BtnToggle sources, MUI ToggleButton/ToggleButtonGroup docs/source, Radix ToggleGroup 1.1.16 docs/source, React Spectrum ToggleButtonGroup docs/source, WAI-ARIA button guidance, and native Button behavior. MUI keeps every Toggle in Tab order; Radix adds roving focus. Citry v1 keeps ordinary native Button Tab order, which is simpler, discoverable, and consistent with `CButtonGroup`.

## 3. Public composition and anatomy

Standalone `CToggle` renders one native `button type="button"` with `aria-pressed`. Grouped Toggles are direct descendants of a named `CToggleGroup` root with `role="group"`. Nested groups are isolated by closest-root ownership.

## 4. Server inputs and client inputs

Toggle server inputs are `value`, `pressed`, `disabled`, optional standalone `variant` and `size`, `class_`, `style`, and `attrs`. Group server inputs are `label`, `value`, `multiple`, `mandatory`, `disabled`, `orientation`, `variant`, `size`, `grow`, `class_`, `style`, and `attrs`. Toggle client inputs are `pressed`, `disabled`, and standalone `variant`, `size`, and `onPressedChange`. Group client inputs are `value`, `disabled`, `orientation`, `variant`, `size`, and `onValueChange`. A group owns presentation for every grouped Toggle, so grouped children reject server `variant` or `size` and ignore those child client overrides. Server values provide initial HTML and client values win while supplied.

## 5. State model

Standalone Toggle is uncontrolled after activation until valid client `pressed` is supplied; omission releases ownership. A group value is `str | None` in single mode and a sequence of unique strings in multiple mode. `mandatory=True` prevents an activation from removing the final selected value. Invalid client values report once per continuous episode and retain the last valid controlled value.

## 6. Slots and slot data

Toggle requires a default `{}` slot containing its visible label. Group requires a default `{}` slot containing one or more direct Toggles. Interactive descendants inside a Toggle label are forbidden by author contract.

## 7. Callbacks, native events, and methods

`onPressedChange(pressed, detail)` runs for standalone accepted activation. `onValueChange(value, detail)` runs for grouped accepted activation. Detail includes `previousValue`, `value`, and `source="activation"`. Native `click` remains available on the actual Toggle button. Group ownership listens during capture, so an authored descendant `click.stop` handler does not disable selection behavior. No component methods are defined.

## 8. Semantics, keyboard, focus, and assistive technology

Each Toggle is a native Button with `aria-pressed=true|false`. Space and Enter use native activation. Every enabled Toggle remains one Tab stop in DOM order; arrow keys are not owned. Groups are named, while `data-orientation` exposes the visual axis because `aria-orientation` is not supported by the ARIA `group` role. Focus never moves merely because selection changes.

## 9. Native forms and validation

Toggle Buttons use `type="button"`, submit no value, do not validate, and do not reset. Use Radio/Checkbox for submitted choices. CForm disabled dominates local and client disabled state.

## 10. Styling and theme contract

Variants are `soft`, `outline`, and `plain`; sizes are `sm`, `md`, and `lg`. A group owns shared presentation for all grouped Toggles, while standalone Toggle inputs own standalone presentation. Public parts are `toggle-group` and `toggle`. Public variables are `--cui-toggle-foreground`, `--cui-toggle-background`, `--cui-toggle-border-color`, `--cui-toggle-pressed-background`, `--cui-toggle-pressed-foreground`, `--cui-toggle-radius`, `--cui-toggle-height`, `--cui-toggle-padding`, `--cui-toggle-focus-ring`, and `--cui-toggle-group-gap`. Stable reflections are `data-multiple`, `data-mandatory`, `data-disabled`, `data-orientation`, `data-variant`, `data-size`, `data-grow`, `data-value`, `data-pressed`, and `aria-pressed`.

## 11. Environmental behavior

Logical properties support RTL. Text wraps without horizontal overflow. Forced colors preserve pressed state through native ARIA and borders. Reduced motion removes transitions. Print keeps pressed distinctions without relying only on background.

## 12. Overlay and layering behavior

The family creates no overlay. A focused Toggle may receive local z-index above an adjacent attached edge.

## 13. Collections, async data, and identity

Grouped values are canonical nonempty strings with CRLF/CR normalized to LF and U+0000 rejected. Values are unique after normalization. Version 1 treats group membership as server-owned structure for an initializer lifetime; browser-side insertion and removal of Toggle roots are not a public collection API.

## 14. Server render, morph, and cleanup

Server context produces correct initial `aria-pressed`. Client ownership uses the closest group, one bounded group listener/effect, per-Toggle effects, and cleanup returned from every initializer. A server rerender derives fresh structure and initial selection from the new render; retained-root browser membership handoff is not promised in version 1.

## 15. Security and content trust

Named strings are de-trusted. Attribute maps are copied and cannot replace Button type, pressed/disabled state, group role/name/orientation, public reflections, children, focus ownership, or Citry runtime fields. Structural Alpine directives are rejected.

## 16. Assets and performance

One CSS and one shared JavaScript definition serve all instances. A group uses bounded root click handling and O(n) reconciliation. Diagnostics record assets and 1/10/100/500/1,000 server output; no timing threshold is claimed.

## 17. Acceptance matrix

Checked-in server tests cover initial standalone/group semantics, unique known values, single/multiple/mandatory configuration, grouped presentation ownership, Form-disabled precedence, hostile attrs, and invalid structures. Focused Chromium tests cover native click activation, controlled single and uncontrolled multiple selection, callback detail, dynamic item disabled state, group-owned variant/size changes, and Form-disabled dominance over client props. The shared quality scenario supplies automated axe evidence, and the docs harness exercises the public previews. Explicit keyboard-origin checks, retained rerender cleanup, RTL, public CSS override geometry, forced colors, reduced motion, multi-browser behavior, and final visual judgment remain release qualification.

## 18. Compatibility classification

Stable: classes, inputs, callbacks, value model, semantics, selectors, variables, and ordinary Tab order. Evolvable: private classes and reconciliation internals. Deferred: roving focus, toolbar semantics, Form submission, icon-only naming shorthand, and maximum selection count.

## 19. Public documentation contract

The guide must contrast Toggle with Switch and ButtonGroup, then show standalone, exclusive, multiple, mandatory, controlled, disabled, variants/sizes, and customization examples.

## 20. Open decisions and deferred work

Roving focus remains deferred for an ordinary ToggleGroup. `CToolbar` can own arrow navigation when Toggles participate in toolbar semantics without changing their pressed semantics. Browser-owned insertion/removal under a retained group, removal fallback, and semantic morph handoff require a separate collection lifecycle contract before becoming public behavior.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
