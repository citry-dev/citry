# Citry UI Switch specification

**Status (2026-08-08): production implementation, public documentation,
focused server/browser evidence, reusable quality scenario, and diagnostic
scaling profile are complete. Human visual and assistive-technology release
review remains.**

## 1. Purpose and product bar

`CSwitch` changes one immediate on/off setting. It keeps native checkbox form,
validity, reset, focus, and keyboard behavior while exposing switch semantics
and a styled track/thumb.

Use Checkbox for independent selections, acknowledgements, and multi-choice
forms. A Switch label must describe the setting and must not change with state.

## 2. Prior art and complaints

| Source | Reviewed | Surface and decision |
|---|---|---|
| Citry UI Checkbox, Field, and Form | workspace, 2026-08-08 | Reuse exact strings, native forms, Field-owned state, controlled settlement, attrs protection, and theme contracts without mixed state. |
| Vuetify VSwitch | current source/docs, 2026-08-08 | Give Switch a dedicated family, concise density/color styling, loading deferred, and normal input event ownership. |
| Material UI Switch | 9.0.1, 2026-08-08 | Adopt controlled/native change, small/medium precedent, native input value, and stable internal slots without copying IconButton inheritance. |
| Mantine Switch | current docs, 2026-08-08 | Adopt visible label, description, label placement, sizes, native FormData, and public track/thumb parts. Defer inner labels and thumb icons. |
| Chakra Switch | 3.35, 2026-08-08 | Adopt checked, disabled, invalid, required, value, size, track/thumb anatomy. Keep read-only unsupported because native checkbox has no read-only behavior. |
| WAI-ARIA APG Switch | current, 2026-08-08 | Native checkbox with `role="switch"`; checked property supplies on/off state; Space activates; stable label required; no mixed state. |
| HTML/ARIA in HTML | current, 2026-08-08 | Preserve native checkbox submission/reset/validation. Do not author `aria-checked`; checked state maps natively. |

Common failure patterns are dynamic labels that change from “Enable” to
“Disable”, visual-only div switches, mixed state, independent checked writers,
and switches used for actions that should be Buttons.

## 3. Public composition and anatomy

```citry-html
<c-CSwitch name="night_lighting" value="enabled" checked>
  Night lighting
</c-CSwitch>
```

Stable anatomy is a neutral root span, direct native checkbox input with
`role="switch"`, presentation surface, decorative track and thumb, and
optional body, native label, and description spans. The transparent native
input owns the track hit area; the visible label owns text activation. The
track and thumb are never independent controls.

## 4. Server inputs and client inputs

Server inputs are `name`, `value`, `id`, `checked`, `required`, `disabled`,
`invalid`, `size`, `label_pos`, `class_`, `style`, `attrs`, and `input_attrs`.
Sizes are `sm`, `md`, and `lg`; label positions are `start` and `end`.

Client `$c-props` supports `checked`, `value`, `required`, `disabled`,
`invalid`, `size`, and `label_pos`. Valid client checkedness controls current
state; omission releases control. Field owns required/disabled/invalid when
composed. Form disabled remains dominant.

## 5. State model

Server `checked` sets default checkedness. Without a client checked prop, the
browser owns current state. A valid client Boolean controls it; omission
releases it; an invalid value retains the last valid controlled state or uses
the server fallback before control begins. Native input and change handlers see
the browser-produced state before a task applies the latest controlled value.

There is no indeterminate state. Root `data-checked`, `data-required`,
`data-disabled`, and `data-invalid` mirror effective state. `data-size` and
`data-label-pos` mirror effective presentation. The native input exposes
`role`, `checked`, `required`, and `disabled`.

## 6. Slots and slot data

The optional default slot renders the visible label. The optional
`description` slot renders guidance and is connected through
`aria-describedby`. Both receive `{}`. Inside CField both slots are forbidden
because Field owns label, description, and error. Label-free standalone use
requires one static input `aria-label` or `aria-labelledby`.

Label content stays stable across on/off state. Default content must not contain
interactive descendants. Description content must not contain form controls or
other emitters of the owned input/change event surface.

## 7. Callbacks, native events, and methods

There is no component callback or public method. Native `input` and `change`
bubble from the internal input; use `$event.target.checked`. `focusin` and
`focusout` observe boundary focus. Use `@invalid.capture` at the component
boundary. Root `click` can fire more than once through label activation and is
not the state-change API.

## 8. Semantics, keyboard, focus, and assistive technology

The native input has `type="checkbox"` and `role="switch"`. Its checked
property maps to on/off; `aria-checked` is neither authored nor mutated. Space
toggles the focused Switch. Enter remains browser-defined. The visible label
or explicit ARIA name identifies it; the label text does not change with state.

## 9. Native forms and validation

A checked enabled named Switch contributes its exact `name=value` pair;
unchecked contributes nothing. `value` defaults to `"on"`. Native required
means the Switch must be on. Native Form reset restores server default when
uncontrolled and the latest controlled checkedness when controlled. External
form ownership uses static `input_attrs.form` and must remain stable for an
initializer lifetime.

## 10. Styling and theme contract

Public variables are `--cui-switch-off-color`, `--cui-switch-on-color`,
`--cui-switch-thumb-color`, `--cui-switch-foreground`,
`--cui-switch-focus-color`, `--cui-switch-invalid-color`,
`--cui-switch-disabled-opacity`, `--cui-switch-width`,
`--cui-switch-height`, `--cui-switch-padding`, `--cui-switch-gap`, and
`--cui-switch-duration`. Each resolves through one private effective variable.

Stable parts are `switch`, `input`, `surface`, `track`, `thumb`, `body`,
`label`, and `description`. Unlayered consumer CSS and declared later layers
may override theme defaults.

## 11. Environmental behavior

Logical layout and the checked thumb movement support LTR and RTL. Long labels
and descriptions wrap at narrow widths and zoom. Reduced motion shortens track
and thumb transitions. Forced colors preserve track, thumb, focus, and checked
state; print preserves an outlined track and visible checked treatment.

## 12. Overlay and layering behavior

Switch creates no overlay or stacking context. The native input uses a local
z-index only to own the track hit area. Consumer overlays remain separate.

## 13. Collections, async data, and identity

Switch is one native control. Repeated settings are composed through ordinary
markup and semantic fieldsets when a visible group label is needed. Server
identity remains Citry-owned. Async persistence and optimistic rollback belong
to application state, not Switch.

## 14. Server render, morph, and cleanup

Server output is usable before JavaScript. Client initialization restores a
retained root's current browser checkedness, installs bounded input/change,
invalid, and form-reset listeners, and registers Field capabilities. Cleanup
records checked handoff, removes listeners, timers, capability registration,
and the initialized marker.

## 15. Security and content trust

Named strings become exact plain strings, normalize CRLF/CR to LF, and reject
U+0000. IDs reject emptiness and ASCII whitespace. Attribute mappings are
copied. Root and input maps reject Citry/runtime namespaces, structural Alpine
directives, object binding, semantic replacement, visibility/focus ownership,
native checkedness, switch role, Field markers, and dynamic bindings to owned
relationships. Static trusted event handlers and unrelated metadata remain.

## 16. Assets and performance

Switch adds one shared CSS asset and one shared client behavior per class, not
per instance. Instance DOM is one input plus bounded presentation/text spans.
Diagnostic scaling records 1, 10, 100, 500, and 1,000 instances without a
timing gate.

## 17. Acceptance matrix

Checked-in server tests cover schemas, native output, naming, slots, Field
ownership, form values, direct styling, exact strings, invalid types, attrs
boundaries, public variables, and environments. Focused Chromium tests cover
role/name, Space activation, native FormData, controlled restoration, Field
relationships/validity, reset, CSS variables, RTL, and reduced motion.

Repository qualification must also cover all public previews, shared axe/Nu
HTML and screenshot profiles, host CSS, wheel contents, assets, and diagnostic
scaling. Human release review retains screen-reader switch announcements,
mobile/touch, zoom, forced colors, and visual polish.

## 18. Compatibility classification

Stable: native semantics/forms, listed inputs/slots, Field boundary, public
variables, parts, and reflections. Evolvable: exact fallback colors, geometry,
motion curve, and diagnostics wording. Unsupported: mixed state, read-only,
inner on/off labels, thumb icons, loading, grouped aggregate state, and
imperative actions.

## 19. Public documentation contract

The public page teaches at-a-glance use, native semantics, controlled state,
forms/validation, descriptions, Field composition, sizes/label placement,
customization, and when Checkbox or Button is the correct control. Nine
component-owned previews use one home-and-living theme and map every visual or
interactive contract to rendered evidence.

## 20. Open decisions and deferred work

Defer inner labels, thumb icons, loading, read-only simulation, and group
components until real application jobs justify their API and accessibility
cost. Revisit the emerging native `switch` content attribute only after the
supported browser floor and Nu HTML evidence make it a reliable replacement
for explicit `role="switch"`.

## 21. Internationalization

This family has not yet completed its localization audit. Before adding any
catalog output, apply the Citry UI component-authoring i18n checklist and make
the structured **Translation keys** table in the family API reference the
authoritative inventory. Record dormant fallback behavior, explicit override
precedence, typed variables, formatting and direction claims, and the exact
browser update path for every library-owned string.
