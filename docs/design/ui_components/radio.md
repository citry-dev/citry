# Citry UI Radio specification

**Status (2026-08-08): production implementation, public documentation,
focused server/browser evidence, reusable quality scenario, and diagnostic
scaling profile are complete. Human visual and assistive-technology release
review remains.**

## 1. Purpose and product bar

`CRadioGroup` and `CRadio` select exactly one value from a visible finite set.
The family preserves native fieldset, legend, radio, keyboard, form, validity,
and submission behavior before JavaScript loads.

```citry-html
<c-CRadioGroup name="destination" value="moon">
  <c-fill name="label">Destination</c-fill>
  <c-fill name="default">
    <c-CRadio value="moon">Moon</c-CRadio>
    <c-CRadio value="mars">Mars</c-CRadio>
  </c-fill>
</c-CRadioGroup>
```

Use Radio when every choice should remain visible. Use Native Select when the
list should collapse. Checkbox handles independent choices; Switch handles an
immediate Boolean setting. Radio Card and Segmented Control remain distinct
future families.

## 2. Prior art and complaints

| Source | Version or review date | Surface inspected | Decision |
|---|---|---|---|
| Citry UI | workspace reviewed 2026-08-08 | Field/Form capability, Checkbox ownership, Native Select value/reset, attrs and theme policy | Reuse Field-owned state, native FormData/reset, controlled value settlement, exact strings, diagnostics, and trusted destination maps. |
| Vuetify | 4.0.7 and current public docs reviewed 2026-08-08 | group value, mandatory selection, disabled, direction, density, color and label surfaces | Adopt group-owned value and concise presentation. Keep mandatory auto-selection deferred. |
| Material UI | 9.0.1 reviewed 2026-08-08 | RadioGroup native labels, standalone radios, size, placement, error and controlled state | Adopt native event value, explicit group label, size and label position. Require Citry Radio to stay under Group. |
| Mantine | 9.2.2 reviewed 2026-08-08 | native Radio, Group, controlled/uncontrolled, FormData, disabled, label/description, variants, root/input destinations | Adopt native form behavior, item description, group disabled, two destinations, and concise variants. |
| Chakra UI | 3.35 reviewed 2026-08-08 | Radio/Radio Card value, orientation, size, disabled, invalid, group labels and controlled callbacks | Adopt orientation and group state. Keep rich card anatomy separate. |

Common failures considered:

- unrelated `name` values break native mutual exclusion and FormData;
- custom ARIA radio widgets duplicate behavior browsers already implement;
- controlling `checked` per item allows contradictory multiple selections;
- group labels, item labels, and Field errors can overwrite each other;
- restoring controlled state before both native `input` and `change` handlers
  settle changes what consumer listeners observe;
- static and client state can disagree after reset or invalid recovery;
- putting arbitrary rich controls inside labels creates competing activation.

## 3. Public composition and anatomy

`CRadioGroup` renders a native `fieldset`. Standalone use requires a `label`
slot rendered as `legend`. Under `CField`, Field owns the group label,
description, error, required, disabled, and invalid state; Group supplies no
label slot and is named with Field's label ID.

Each `CRadio` renders one neutral item wrapper, one native
`input[type="radio"]`, a visible `label`, and optional description. It is valid
only under the nearest Group. Nested Groups establish their own name and value
scope. One Group may contain transparent layout components, but each Radio
belongs to exactly one nearest Group.

Public parts: `radio-group`, `legend`, `radio`, `input`, `body`, `label`, and
`description`.

## 4. Server inputs and client inputs

`CRadioGroup` server inputs:

| Input | Type | Default | Contract |
|---|---|---|---|
| `name` | `str` | required | Nonempty canonical native group/submission name. |
| `value` | `str | None` | `None` | Initial selected option or no selection. Must match one Radio value. |
| `form` | `str | None` | `None` | External native Form owner ID shared by every Radio. |
| `required` | `bool | None` | `None` | Native group validity; Field owns it when composed. |
| `disabled` | `bool | None` | `None` | Disables the fieldset; Field/Form dominates when composed. |
| `invalid` | `bool | None` | `None` | Visual/ARIA invalid state; Field owns it when composed. |
| `orientation` | `vertical | horizontal` | `vertical` | Layout reflection, not a replacement keyboard algorithm. |
| `variant` | `solid | outline` | `solid` | Selected control treatment. |
| `size` | `sm | md | lg` | `md` | Control and text scale. |
| `label_pos` | `start | end` | `end` | Places item label before or after its control. |
| `id`, `class_`, `style`, `attrs` | root values | `None` | Fieldset identity and customization. |

Group client `$c-props` support `value`, `required`, `disabled`, `invalid`,
`orientation`, `variant`, `size`, and `label_pos`. `value` accepts a canonical
known string or `null`. Omission releases browser ownership. Invalid values use
the documented server/Field fallback and report once per continuous episode.
Field-owned client state is ignored with one capability diagnostic.

`CRadio` server inputs: required canonical `value`, `disabled=False`,
`class_`, `style`, `attrs`, and `input_attrs`. Individual dynamic disabled
state is deferred; rerender the item or control the whole Group.

## 5. State model

The selected value has one owner at a time:

- server `value` sets initial/default checkedness;
- without client `value`, native browser selection is current authority;
- valid client `value` or `null` controls current checkedness;
- omission releases control without adding a second checked owner;
- reset restores native defaults when uncontrolled and the latest client value
  when controlled.

Native `input` and `change` expose the browser-produced selection before a
task applies the latest controlled value. Root `data-value` mirrors the current
selected canonical value and is absent when none is selected.

Required native invalid state joins explicit invalid state and informs Field.
Programmatic recovery clears an existing native-invalid episode only when the
settled group is valid; it never invents a native-invalid episode.

## 6. Slots and slot data

`CRadioGroup.label`: standalone group legend, no data. Forbidden under Field.
`CRadioGroup.default`: Group content, no data, required.
`CRadio.default`: visible item label, no data, required.
`CRadio.description`: optional description, no data.

Label content must be phrasing content without nested labels or interactive/
labelable descendants. Description may contain phrasing links but not form
controls that emit the Group-owned `input`/`change` event surface.

## 7. Callbacks, native events, and methods

No component-authored callback or method is needed. Native `input` and
`change` bubble from the selected input and fire once for a user selection.
On a Group component tag, `$event.target` is the native radio;
`$event.currentTarget` is the fieldset root. Use `target.value` and
`target.checked`. Native `focusin`/`focusout` observe focus at the group
boundary. `invalid` requires capture.

## 8. Semantics, keyboard, focus, and assistive technology

Native fieldset/legend and same-name radio semantics own grouping. Every item
has a visible associated label. Tab enters the group at the browser-selected
radio; arrow keys move and select among enabled same-name radios according to
native platform behavior. Space selects the focused radio. Disabled options
are skipped by native focus and selection.

No authored `radiogroup`/`radio` roles, tabindex roving algorithm, or
`aria-checked` exists. Native checkedness maps to the accessibility tree.
Orientation is visual and does not promise a custom directional algorithm.

## 9. Native forms and validation

All item inputs share the required `name` and optional `form`. The checked,
enabled radio contributes exactly one name/value entry to FormData. No
selection contributes none. `required` uses native same-name group validity.
Individual disabled options and disabled fieldsets are unsuccessful controls.

An enclosing `CForm(disabled=True)` remains dominant. Form readonly has no
native Radio meaning and is ignored standalone; inheriting
`CField(readonly=True)` rejects Radio capability, while explicit
`CField(readonly=False)` opts out. A conflicting external Form owner inside
`CForm` is rejected. The external owner must remain stable for one initializer
lifetime.

## 10. Styling and theme contract

Public variables:

| Variable | Purpose |
|---|---|
| `--cui-radio-group-gap` | item spacing |
| `--cui-radio-active-color` | checked border/fill/dot |
| `--cui-radio-border-color` | unchecked border |
| `--cui-radio-background` | control background |
| `--cui-radio-foreground` | labels |
| `--cui-radio-focus-color` | focus ring |
| `--cui-radio-invalid-color` | invalid border |
| `--cui-radio-control-size` | native control box |
| `--cui-radio-item-gap` | control/body spacing |
| `--cui-radio-label-gap` | label/description spacing |
| `--cui-radio-disabled-opacity` | disabled item opacity |

Stable group reflections are `aria-invalid`, `data-value`, `data-required`,
`data-disabled`, `data-invalid`, `data-orientation`, `data-variant`,
`data-size`, and `data-label-pos`. Native item inputs expose `name`, `value`,
`checked`, and `disabled`; item wrappers mirror `data-checked` and
`data-disabled`.

Every public part selector is stable. Public variables win over variant and
size fallbacks. Root class/style maps style the fieldset; item maps style one
Radio; `input_attrs` is a trusted escape path for nonconflicting native
metadata/listeners.

## 11. Environmental behavior

Logical ordering supports LTR and RTL. Horizontal groups wrap rather than
overflow. Long labels/descriptions break safely. Light/dark fallbacks follow
effective color scheme. Forced colors retains native radio recognition, focus,
and checked state. Print preserves a visible checked/unchecked boundary. No
animation means reduced motion needs no special behavior.

## 12. Overlay and layering behavior

No portal, popup, position, z-index, clipping, transform, overlay, or
containing-block ownership. Tooltip/popover composition must not replace the
native label activation or event ownership.

## 13. Collections, async data, and identity

Values are canonical identity and unique within the nearest Group. Empty
Groups, duplicates, and unknown server selection fail. Item order follows
rendered document order. Dynamic item addition/removal requires a correlated
Group rerender so the initializer snapshots one coherent set. Large searchable
or remotely loaded option sets should use Select/Combobox instead.

## 14. Server render, morph, and cleanup

Server output has complete checkedness, names, validity, labels, descriptions,
and styling. The Group initializer owns shared client state, native event
listeners, bounded reset/reconciliation tasks, and one marker. Cleanup removes
listeners/tasks, Field capability/native-invalid registration, and marker.
Correlated rerenders reinitialize from new server fallbacks and current props.

## 15. Security and content trust

Names, values, IDs, and choices become exact plain strings; CRLF/CR normalize
to LF and U+0000 is rejected before validation/rendering. Attr mappings are
copied. Each destination rejects owned semantics, checkedness, naming,
submission, Field/runtime markers, focus/editing, structural directives,
child replacement, whole-object binding, and dynamic aliases. Static
nonconflicting metadata, description relationships, classes/styles, and event
listeners remain allowed.

## 16. Assets and performance

One shared Group JS behavior and CSS asset; no icon catalog, SVG, observers,
global listeners, or animation. One Group listener set owns any number of
Radios. Diagnostic scaling records representative 1, 10, 100, 500, and 1,000
item groups without a timing gate.

## 17. Acceptance matrix

Focused evidence covers schemas; standalone/Field labels; one/many/disabled
items; duplicate/unknown/empty failures; exact values; native group/radio AX;
Tab/arrow/Space; input/change order and targets; uncontrolled/controlled/null/
omission; invalid episodes; required validity; Field capability/native error;
FormData, reset, external Form, disabled fieldset; every variant/size/
orientation/label position; public variables/selectors/destinations; long
content; LTR/RTL; nested schemes; forced colors; print; cleanup; docs/previews;
quality; scaling; registration; and wheel boundary.

Manual release review covers screen-reader group/item phrasing, platform arrow
behavior, zoom, touch target comfort, and visual selected/focus contrast.

## 18. Compatibility classification

Stable: components, nested schemas, aliases, native anatomy, inputs, slots,
events, value ownership, form behavior, capability boundary, public variables,
parts, attributes, diagnostics, and cleanup. Evolvable: exact colors, lengths,
and wrapping thresholds. Private: context key, registry, `.cui-*`,
`--_cui-*`, initializer marker, and JS helpers.

## 19. Public documentation contract

The page uses one botanical-garden theme. Planned previews: at a glance,
shortest composition, descriptions/disabled item, controlled selection,
validation/FormData, orientation, variants/sizes/label position, Field
composition, and theming. Examples use visible labels and real form jobs.

## 20. Open decisions and deferred work

Implementation blockers: none. Deferred: Radio Card, Segmented Control,
mandatory auto-selection, per-item client disabled state, rich item icons,
dynamic client-owned collection mutation, standalone CRadio, custom selection
callbacks, and roving-focus ARIA recreation.

Falsifier for native ownership: if supported browsers cannot preserve the
required controlled event order or style native radios without losing
checked/focus/forced-color semantics, stop and design a fully specified ARIA
radio widget rather than combining partial native and custom ownership.
