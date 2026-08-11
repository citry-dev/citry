# Citry UI Checkbox component specification

**Status (2026-08-08): production runtime, public documentation, focused
server and browser evidence, and reusable quality scenario complete. Final
cross-family qualification and human visual and assistive-technology review
remain.**

## 1. Purpose and product bar

`CCheckbox` lets an application author choose one independent Boolean option,
submit one native name/value pair when that option is checked, or represent a
partial aggregate selection without replacing native checkbox semantics.

The production bar is a styled, useful-by-default native checkbox that works in
server-only HTML and gains controlled checked and indeterminate state when
Citry's browser runtime is present. Server-only output remains an ordinary
two-state checkbox because HTML has no indeterminate content attribute. It
supports ordinary forms, Citry Form and Field ownership, descriptions,
validation, reset, narrow layouts, RTL, forced colors, print, and public
runtime theming.

Common jobs and their shortest intended surfaces:

| Job | Template | Python composition | Support path |
|---|---|---|---|
| Choose one Boolean preference | `<c-CCheckbox name="digest">Weekly digest</c-CCheckbox>` | `CCheckbox(name="digest", slots={"default": "Weekly digest"})` | direct API and native form behavior |
| Submit a specific token | `<c-CCheckbox name="format" value="epub">EPUB</c-CCheckbox>` | `CCheckbox(name="format", value="epub", slots={"default": "EPUB"})` | direct API |
| Explain a choice | `description` fill | `slots={"description": ...}` | direct slot |
| Require one agreement | `required` | `CCheckbox(required=True, ...)` | native constraint validation |
| Control checked state in the browser | `$c-props="{ checked: selected }"` | same rendered component | client input plus native `input` event |
| Show a partial aggregate | `$c-props="{ indeterminate: partial }"` | initial `indeterminate=True` | direct initial and client input |
| Select several independent values | several Checkboxes with the same `name` | several `CCheckbox(...)` values | native HTML composition |
| Give a set a visible group name | native `<fieldset>` and `<legend>` | ordinary component composition | native HTML composition |
| Label a row-selection checkbox without visible text | `c-input_attrs="{'aria-label': ...}"` | `input_attrs={"aria-label": ...}` | trusted native attributes |
| Show Field description and error state | bare Checkbox inside `CField` | `CField(... CCheckbox(...))` | composition; Field owns its text and state |
| Reverse label position | `label_pos="start"` | `label_pos="start"` | direct API |
| Change geometry or appearance | `size`, `variant`, `class_`, `style` | same | direct API, public CSS, or utility classes |

Non-goals:

- `CCheckboxGroup` is not part of this pass. A future group must own set-valued
  controlled state, `fieldset` and `legend` relationships, and group-level
  validation. Merely arranging children does not justify a component.
- Radio and Switch remain separate families because they express different
  choices and assistive-technology semantics.
- A checkbox card, button-like toggle, tree selection model, and table
  selection model remain composition or separate components.
- The component does not submit a hidden false value. An unchecked native
  checkbox contributes no form entry.
- No headless variant ships in this pass.
- No simulated read-only state ships. Native checkbox `readonly` does not
  apply, and blocking activation would create a second, non-native contract.

## 2. Prior art and complaints

The shared taxonomy reports Checkbox, Radio, and Switch coverage in 12 of 12
surveyed suites. The active inventory asks this pass to qualify `CCheckbox`
first and add a group only if it owns real aggregate behavior.

### Current-source record

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| HTML Living Standard | 2026-07-20 snapshot, reviewed 2026-08-08 | Checkbox state, dirty checkedness, activation, reset, required validity, form submission, and indeterminateness | Keep a real `input[type="checkbox"]`; preserve checked/defaultChecked, reset, native events, and independent indeterminate semantics. |
| MDN | reviewed 2026-08-08 | Checkbox input and `HTMLInputElement.indeterminate` | Treat indeterminate as a JavaScript property that does not determine form submission. |
| WAI-ARIA APG | reviewed 2026-08-08 | Checkbox pattern and mixed-state example | Use native keyboard behavior; expose mixed state; require a usable accessible name; use native fieldset composition for groups. |
| Vuetify | 4.0.7 source, reviewed 2026-08-08 | `VCheckbox`, `VCheckboxBtn`, `VSelectionControl`, and `VSelectionControlGroup` source | Weight the full styled control, label slot, model ownership, indeterminate, density, color, errors, and group context most heavily. Reject generic true/false model values in the single native Checkbox. |
| Material UI | 7.3.11 source and current docs, reviewed 2026-08-08 | Checkbox, FormControlLabel, indeterminate docs, and Checkbox source | Keep label composition explicit, distinguish checked from visual indeterminate, and expose small/medium/large through Citry's shared size vocabulary. |
| Mantine | 8.3.14 source and current docs, reviewed 2026-08-08 | Checkbox, Group, Indicator, Card, label position, descriptions, errors, forms, and indeterminate | Own a useful label and description surface, use the native indeterminate property, and leave Card and Group as separate jobs. |
| Chakra UI and Ark | current docs, reviewed 2026-08-08 | Checkbox anatomy, closed composition, group guidance, controlled state, description, and indeterminate | Preserve a concise closed component while keeping native input access and explicit Field relationships. |
| React Spectrum and React Aria | current V3/Spectrum docs, reviewed 2026-08-08 | Checkbox, CheckboxGroup, controlled selection, form values, validation, read-only, and indeterminate | Keep group ownership separate; use visible children as the label; treat persistent client indeterminate as controlled configuration. |
| Bootstrap | 5.3.8 docs, reviewed 2026-08-08 | checks/radios, indeterminate, reverse, no-label, toggle-button, and CSS variables | Support reverse label position and label-free accessible controls without copying sibling-only markup or toggle-button styling. |
| Web Awesome | 3.11.0 docs, reviewed 2026-08-08 | Checkbox label and hint slots, checked/defaultChecked, indeterminate, forms, validation, events, states, variables, and parts | Keep label and description in the closed component, preserve native initial/current distinction, and expose stable selectors and variables. |

### Material complaints and consequences

| Complaint | Status and evidence | Citry consequence |
|---|---|---|
| Indeterminate MUI Checkbox was announced as checked or unchecked instead of mixed. | MUI issue 20476 opened 2020 and closed by merged PR 48147 in 2026. | Set the native `indeterminate` property and assert the accessibility tree exposes mixed. Never author forbidden `aria-checked` on a native checkbox. |
| Checkbox and Switch inside Ark Field could point `aria-labelledby` at a label that did not exist. | Ark issue 3824 opened 2026-03-17 and closed not planned. The report identifies unconditional generated ID references. | Never invent a label ID unless the corresponding label renders. Merge only concrete Field, description, error, and consumer relationships. |
| Vuetify Checkbox lacks a concise secondary text surface distinct from its hint. | Vuetify issue 21773 opened 2025-07-17 and remains open for the 4.x milestone. | Give standalone Checkbox a `description` slot directly below its label. |
| Bootstrap checked colors cannot be changed through the same runtime CSS variable used by unchecked state. | Bootstrap issue 41652, reported against 5.3.7, closed not planned. | Resolve every visual state through inherited public variables instead of compiled state colors. |

### Patterns adopted and rejected

Citry adopts a label-owning native checkbox, an optional description, direct
size and variant inputs, controlled browser checked and indeterminate inputs,
native events, and Field/Form relationships. It rejects a generic selection
control abstraction, arbitrary true/false values, a built-in ripple, hidden
false submission, simulated read-only, and a layout-only group.

### Vuetify disposition

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| `modelValue` and `update:modelValue` | direct API and native event | client `checked`; native `input`/`change` | Use Boolean checkedness, not arbitrary values. |
| initial selection | direct API | server `checked` | Seeds native default and current checkedness. |
| `indeterminate` and `update:indeterminate` | direct API and native event | server/client `indeterminate`; native `input` | Client control persists only while the client prop remains supplied. |
| `label` and label slot | direct slot | default slot | Label may contain authored inline content. |
| additional explanatory text | direct slot | `description` | Addresses issue 21773 without another string prop. |
| `disabled` | direct API | server/client `disabled` | Native property and Form inheritance. |
| `readonly` | omitted | rejected attribute and unsupported Field capability | Native checkbox has no read-only state. |
| `error`, messages, hint, rules, validation | composition and native validation | `invalid`, `description`, `CField`, native `required`, Citry Events | One owner controls Field state and visible errors. |
| `name`, `id`, and submitted value | direct API | `name`, `id`, `value` | Preserve native form output. |
| true/false values, `multiple`, and comparator | native composition or future group | repeated names and future `CCheckboxGroup` | Omit generic model comparison from a Boolean native control. |
| color, theme, density, inline | direct API, CSS, or composition | public variables, `size`, ordinary layout | Do not copy broad color props or layout wrappers. |
| true, false, and indeterminate icons | public CSS | input selector and indicator pseudo-element variables | No client-reactive indicator slot in the first pass. |
| ripple | omitted | none | Avoid client work that is not needed for checkbox semantics. |
| default, label, and input slots | slot, attrs, and CSS | default slot, `input_attrs`, selectors | Do not replace the native input. |
| prepend, append, details, and message slots | composition | surrounding content or `CField` | Keep finite Checkbox anatomy small. |
| focus/blur state and methods | native HTML | refs, `focus()`, native focus/blur events | No wrapper method API. |
| class and style | direct API | `class_`, `style` | Land on the neutral root. |

## 3. Public composition and anatomy

Smallest visible-label template:

```citry-html
<c-CCheckbox name="field_notes">
  Include field notes
</c-CCheckbox>
```

Python composition:

```python
from citry_ui import CCheckbox

include_notes = CCheckbox(
    name="field_notes",
    slots={"default": "Include field notes"},
)
```

Stable anatomy:

```text
span[data-citry-ui-part="checkbox"]
├── input[type="checkbox"][data-citry-ui-part="input"]
└── span
    ├── label[for][data-citry-ui-part="label"]?
    └── span[data-citry-ui-part="description"]?
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CCheckbox` | neutral `<span>` | `class_`, `style`, and `attrs` land on the root; `input_attrs` lands on the native input | An authored default fill renders in an explicit internal label whose `for` targets the input ID. Description is the label's sibling and is referenced through `aria-describedby`, so it does not also enter the accessible name. Field IDREFs target elements that actually render. |

The internal label renders only when visible default content is supplied. When
it is omitted, the input must receive a non-empty `aria-label` or valid
`aria-labelledby` through `input_attrs`, unless an enclosing `CField` supplies
its external label. Static ARIA naming is accepted only for a label-free,
standalone Checkbox. It is rejected when a default fill or Field label exists,
so hidden text cannot replace the visible label in the accessible name.

Inside `CField`, Checkbox must omit its default and description fills. Field
owns the visible label, description, error, and the shared required, disabled,
read-only, and invalid state. Checkbox registers support for required and lack
of support for read-only. Supplying Checkbox-owned label or description in a
Field raises because two visible label systems would be ambiguous.

A standalone Checkbox ignores `CForm(readonly=True)` because native Checkbox
has no read-only state. Checkbox inside a Field that inherits Form read-only
fails the server capability check and resolves false with one client
capability diagnostic. `CField(readonly=False)` explicitly opts that Field and
its Checkbox out of the Form's read-only state.

Outside Field, default and description each accept at most one fill. Unknown or
duplicate fills raise through Citry's slot contract.

Repeated Checkboxes with a shared name submit one entry for each checked
control. A related set uses native `fieldset` and `legend`; CCheckbox adds no
administrative container.

Post-implementation anatomy review must try to remove the anonymous body span.
It is retained only if label plus description alignment, label reversal, and
narrow wrapping cannot be expressed without it. It is not public API.

## 4. Server inputs and client inputs

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `name` | `str | None` | `None` | structural | Non-empty plain string when supplied; native form name. |
| `value` | `str` | `"on"` | reactive configuration | Plain string; CRLF and CR normalize to LF; U+0000 rejected; submitted only while checked and enabled. |
| `id` | `str | None` | `None` | structural | Non-empty with no ASCII whitespace; generated when omitted. Must match enclosing Field control ID when both are explicit. |
| `checked` | `bool` | `False` | initial value | Sets the native `checked` content attribute, defaultChecked, initial current checkedness, and reset destination. |
| `indeterminate` | `bool` | `False` | initial value | Seeds visual mixed state and native property during client activation; independent of submitted checkedness. |
| `required` | `bool | None` | `None` | reactive configuration | Standalone false when omitted; Field owns when composed. Native validity requires checkedness. |
| `disabled` | `bool | None` | `None` | reactive configuration | Standalone false when omitted; enclosing Form disabled dominates; Field owns when composed. |
| `invalid` | `bool | None` | `None` | reactive configuration | External presentation and ARIA source; does not set custom validity; Field owns when composed. |
| `variant` | `Literal["solid", "outline"]` | `"solid"` | reactive presentation | Checked/mixed fill treatment. |
| `size` | `Literal["sm", "md", "lg"]` | `"md"` | reactive presentation | Control geometry and text scale. |
| `label_pos` | `Literal["start", "end"]` | `"end"` | reactive presentation | Logical position of authored label text relative to the control. |
| `class_` | `CClassValue | None` | `None` | server presentation | Merges onto the neutral root. |
| `style` | `CStyleValue | None` | `None` | server presentation | Merges onto the neutral root. |
| `attrs` | `Mapping[str, object] | None` | `None` | trusted root attributes | Copied per render; lands on the neutral root; cannot set static or dynamic `for` or `aria-hidden` because internal label and accessibility ownership are fixed; cannot replace owned public/runtime attributes. |
| `input_attrs` | `Mapping[str, object] | None` | `None` | trusted native attributes | Copied per render; lands on input; may supply static Form owner and, only for label-free standalone usage, one non-empty static `aria-label` or `aria-labelledby`; dynamic ARIA naming and dynamic `aria-describedby`/`aria-errormessage` aliases are rejected; cannot set static or dynamic `role`, `aria-hidden`, `aria-checked`, `aria-required`, `aria-disabled`, `aria-readonly`, or `aria-invalid`; cannot replace owned state or add dynamic ownership. |

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `checked` | Boolean | release to browser ownership and preserve current checkedness | invalid | report once; before valid control leave browser value, after control retain last valid value | native checkedness, mirrors, form output |
| `indeterminate` | Boolean | release to browser ownership and preserve current indeterminateness | invalid | same ownership rule | native property, native accessible mixed state, mirrors |
| `value` | string | reapply the private server fallback | invalid | report once and reapply the private server fallback | native value property/content attribute and FormData token |
| `required` | Boolean | Field or server fallback | invalid | report once and use fallback | native validity and mirrors |
| `disabled` | Boolean | Field or local server fallback | invalid | report once and use fallback; enclosing Form disabled is always ORed afterward | native mutability, focus, submission, mirrors |
| `invalid` | Boolean | Field or server fallback | invalid | report once and use fallback | ARIA, Field error relationship, mirrors |
| `variant` | enum | server fallback | invalid | report once and use server fallback | root reflected attribute and CSS |
| `size` | enum | server fallback | invalid | same | root reflected attribute and CSS |
| `label_pos` | enum | server fallback | invalid | same | root reflected attribute and layout |

A valid client value wins within its documented ownership boundary. Removing
client `checked` or `indeterminate` releases that property immediately without
a DOM assignment. Other omitted client inputs use the Field, Form, or server
fallback. For standalone Checkbox, effective disabled is always
`Form.disabled OR local client/server disabled`; client false cannot re-enable
a control under a disabled Form. Inside Field, Field state is authoritative.
A client `value` updates the native value property and its reflected content
attribute. The component retains the server value privately, and omission or
invalid client input reapplies that fallback without pretending the DOM
attribute stayed unchanged.

Inside Field, client `required`, `disabled`, and `invalid` are ignored with one
diagnostic per invalid episode. Field client state is authoritative. Checkbox
has no `readonly` client input and reports unsupported Field read-only through
the capability registry.

## 5. State model

Checkedness and indeterminateness are independent:

| Transition | Trigger | Result |
|---|---|---|
| initialize unchecked or checked | server render | `checked` seeds both default and current native state |
| initialize mixed | server `indeterminate=True` plus Citry's browser runtime | activation sets the native property and root reflection together; the native property exposes mixed to accessibility APIs; server-only output remains two-state |
| user activation | pointer, touch, or Space while enabled | browser toggles checkedness, clears native indeterminate, then fires native `input` and `change` |
| uncontrolled activation | no corresponding client input | preserve browser checkedness and cleared indeterminate state |
| controlled activation | valid client `checked` and/or `indeterminate` | native event fires first; after consumer reactive updates settle, restore only supplied properties that still differ |
| acquire control | valid client Boolean | assign only if current semantic state differs |
| release control | client input becomes omitted | keep current state and let the browser own later changes |
| invalid client input | non-Boolean or null | report once; preserve prior valid controlled state, otherwise leave current browser state |
| external invalid | Field or standalone input | set presentation and ARIA without changing native validity |
| native invalid | uncanceled constraint validation failure | record a native-invalid episode in Field and show invalid presentation |
| validity recovery | settled input, config update, rerender, or reset leaves validity valid | clear native-invalid only; external invalid may remain |
| native reset | uncanceled Form reset | browser restores checkedness to server default; indeterminate remains native-current; controlled properties restore after reset |
| disabled | effective disabled true | native input leaves tab order, cannot activate, and submits no value |

If both controlled props remain unchanged after a native activation, checked
and mixed visuals return to those controlled values. A consumer mirroring
`event.target.checked` and clearing its mixed value incurs no redundant
assignment. Native listeners authored on the component tag run on the neutral
root, so they read Checkbox state from `event.target`, not
`event.currentTarget`.

The direct input listener marks native activation reconciliation pending before
the bubbling consumer `input` handler runs. While pending, reactive prop effects
record the latest supplied checked and indeterminate values but never assign
either native property. Both consumer `input` and `change` handlers therefore
observe the browser-produced checkedness and cleared indeterminate state. A
task after `change` reads the latest props, releases omitted properties, and
assigns only supplied properties that still differ. Prop changes outside a
native activation may reconcile immediately.

An uncontrolled valid input clears an existing native-invalid episode
immediately. When `checked` is controlled, the input handler defers that
decision until the latest prop has been reconciled. It clears the episode only
if the final controlled native validity is valid. Restoring an unchanged false
prop therefore keeps the required-invalid episode; a consumer update to true
clears it. Programmatic configuration and controlled assignments may clear an
existing episode after validity recovers, but never create one without a native
`invalid` event.

The component does not infer aggregate state from neighboring checkboxes.
Application code computes select-all checked and indeterminate values.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CCheckbox` | `default` | no when externally named; otherwise yes | zero or one | `{}` via `CCheckboxDefaultSlotData` | no visible label |
| `CCheckbox` | `description` | no | zero or one | `{}` via `CCheckboxDescriptionSlotData` | no description element |

Both slots are lazy server content. They receive no browser-reactive data.
Checked and indeterminate visuals must use reflected attributes or CSS rather
than expecting a slot rerender.

Both slots accept phrasing content only because their stable wrappers are
spans. The default slot additionally forbids nested labels and any other
interactive or labelable descendant. Put links, buttons, and richer flow
content outside CCheckbox rather than inside its label. The description may
contain ordinary phrasing links because it is a sibling of the internal label,
but it forbids form controls, editable content, and custom descendants that
emit bubbling `input` or `change`. Those events belong to the direct Checkbox
input at the component boundary. Public examples and Nu HTML fixtures lock
this content-model boundary.

Inside Field, both slots are forbidden because Field owns the visible label
and description. There are no dynamic keyed slots and no indicator slot.
Custom indicators use the stable input selector and public CSS variables.

## 7. Callbacks, native events, and methods

The family adds no component callback and no custom DOM event.

Use native Alpine listeners:

```citry-html
<c-CCheckbox
  $c-props="{ checked: selected }"
  @input="selected = $event.target.checked"
>
  Archive specimen
</c-CCheckbox>
```

Native `input` and `change` fire after the browser has toggled checkedness and
cleared indeterminate. A controlled restoration occurs only after those
listeners and their reactive updates settle. Prop effects do not assign native
checked or indeterminate properties while that activation is pending, even if
Alpine flushes between input and change. These bubbling events fire once
per native state change and are the component-boundary state-change surface.
Citry carries a listener authored on `<c-CCheckbox>` to the neutral root, so
`event.currentTarget` is the root and `event.target` is the internal
native input for Checkbox input/change events.

At the component boundary, use `focusin` and `focusout` because native `focus`
and `blur` do not bubble from the input. Observe native validation with
`@invalid.capture`, or place a listener directly on the input through trusted
`input_attrs`. A description link can also produce focusin/focusout, so a
focus-specific handler inspects `event.target`. Do not drive state from a root
`click`: activating label text causes the label-origin click followed by the
input's synthetic click bubbling through the root.

There is no public method layer. Consumers that need imperative focus use a
reference to `[data-citry-ui-part="input"]` and call the native `focus()`.

## 8. Semantics, keyboard, focus, and assistive technology

The control is a native `input[type="checkbox"]`. The default slot renders in
an explicit internal label that supplies the visible name. The description is
outside that label and linked through `aria-describedby`. Label-free usage
requires `aria-label` or `aria-labelledby` on the input. A Field label is an
explicit external label for the generated input ID. Consumer ARIA naming is
rejected on the visible-label and Field paths, so the rendered label remains
the computed accessible name.

| Context | Input | Result | Focus result | Prevent default |
|---|---|---|---|---|
| document | Tab | enter enabled Checkbox in document order | native input focused | no |
| focused Checkbox | Space | toggle checkedness and clear mixed state | focus stays on input | browser behavior |
| pointer or touch on input or internal label | activation | toggle checkedness and clear mixed state | browser-dependent focus remains native | no |
| disabled Checkbox | Tab, Space, pointer, touch | no activation | omitted from normal tab order | native behavior |

The component adds no arrow-key group model. A native fieldset of independent
checkboxes keeps each enabled input in sequential Tab order.

While indeterminate, the native property exposes the partial state to
accessibility APIs. `aria-checked` is forbidden on this native element and is
never authored or mutated. Description, Field error, and consumer IDREFs merge
without duplicates. `aria-invalid` appears only while effective external or
native invalid state is active.

## 9. Native forms and validation

An enabled, checked Checkbox with a non-empty name contributes its current
value. Unchecked, disabled, or unnamed Checkbox contributes no entry. Repeated
checked Checkboxes may contribute repeated entries with the same name. The
default value is the native `"on"` token.

`required=True` makes one Checkbox valid only while checked. It does not mean
"at least one in this set". Group-level minimum selection remains future
`CCheckboxGroup` work or application validation.

`invalid=True` changes presentation and accessibility only. It does not call
`setCustomValidity()` and does not make `checkValidity()` fail. A browser
`invalid` event starts the native-invalid episode used by Field.

Native reset restores checkedness to the latest server-rendered checked
attribute and clears the browser's user-validity state. The standard does not
reset `indeterminate` or restore a Checkbox's value token. Uncontrolled mixed
state therefore remains whatever it was immediately before reset. After each
uncanceled reset, an independent bounded task reapplies the current valid
client value or private server value fallback and restores supplied client
checked or indeterminate values.

Inside `CForm`, the input cannot redirect static native `form` ownership to a
different form. Standalone Checkbox may use static `input_attrs={"form": id}`.
Dynamic `form` bindings are rejected because reset listening is attached for
one initializer lifetime. The external Form element and ID must remain stable
until Checkbox reinitializes.

Citry Events submit, cancellation, server failure, and retry keep native
checkedness as the transport source. The component adds no hidden false entry
and no synthetic serialization.

## 10. Styling and theme contract

`solid` fills the control in checked and mixed states. `outline` retains the
surface and uses the active color for border and indicator. `sm`, `md`, and
`lg` change control geometry and associated type scale. `label_pos` is logical
and mirrors under RTL.

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-checkbox-background` | color | unchecked control surface | `Canvas` |
| `--cui-checkbox-foreground` | color | label text | `CanvasText` |
| `--cui-checkbox-border-color` | color | unchecked border | mixed CanvasText |
| `--cui-checkbox-hover-border-color` | color | enabled hover border | stronger CanvasText mix |
| `--cui-checkbox-active-color` | color | checked or mixed fill/border | scheme-aware blue |
| `--cui-checkbox-indicator-color` | color | check and mixed indicator | scheme-aware high-contrast color, or active color in outline variant |
| `--cui-checkbox-focus-color` | color | focus-visible outline | `Highlight` |
| `--cui-checkbox-invalid-color` | color | invalid border and outline accent | scheme-aware danger |
| `--cui-checkbox-disabled-opacity` | number | disabled root opacity | `0.55` |
| `--cui-checkbox-control-size` | length | control inline/block size | size-dependent fallback |
| `--cui-checkbox-radius` | length | control corner radius | `0.3rem` |
| `--cui-checkbox-gap` | length | control-to-text gap | `0.625rem` |
| `--cui-checkbox-description-color` | color | description text | muted CanvasText mix |
| `--cui-checkbox-description-gap` | length | label-to-description gap | `0.2rem` |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="checkbox"]` | neutral root | variant, size, label position, checked, mixed, required, disabled, invalid | root |
| `[data-citry-ui-part="input"]` | native visible checkbox | checked, indeterminate, required, disabled, invalid, focus-visible | direct child of root |
| `[data-citry-ui-part="label"]` | authored visible label | present only with default fill | descendant of root body |
| `[data-citry-ui-part="description"]` | authored description | present only with description fill | descendant of root body |

| Public runtime-reflected attribute | Values | Meaning |
|---|---|---|
| root `data-checked` | present or absent | current native checkedness |
| root `data-indeterminate` | present or absent | current native indeterminateness |
| root `data-required` | present or absent | effective required configuration |
| root `data-disabled` | present or absent | effective disabled configuration |
| root `data-invalid` | present or absent | effective external or native invalid state |
| root `data-variant` | `solid`, `outline` | effective presentation |
| root `data-size` | `sm`, `md`, `lg` | effective geometry |
| root `data-label-pos` | `start`, `end` | logical label position |

Defaults live in `@layer citry-ui.theme`. Every public variable is inherited
and resolved through a private fallback variable. Unlayered consumer CSS wins
regardless of source order. Named consumer layers require the application's
documented layer order.

The checked indicator uses the native input's `:checked` pseudo-class, so it
remains accurate without JavaScript. Root `data-checked` and
`data-indeterminate` are browser-runtime mirrors, not static HTML fallbacks.
Client initialization and native activation update each mirror together with
its native property.

## 11. Environmental behavior

Light and dark schemes use `light-dark()` and system colors. Nested scheme
scopes resolve independently. Logical flex direction and spacing support RTL;
`label_pos` names logical positions rather than left and right.

Forced colors keeps the control border, indicator, invalid distinction, and
focus outline visible using system colors. The custom appearance does not
disable forced-color adjustment for the control. Reduced motion removes the
brief indicator transition. The component has no essential animation.

At 200 and 400 percent zoom, long label and description text wrap while the
control remains aligned with the first text line. The internal label provides
a touch target larger than the visible control. Narrow layouts must not create
horizontal overflow. Print preserves checked and mixed marks, label,
description, border, and disabled distinction without relying on background
color alone.

Visible library-authored strings: none. Labels, descriptions, accessible
names, and application errors are caller content. Localization remains a
separate follow-up.

## 12. Overlay and layering behavior

Checkbox never creates or controls an overlay. It adds no z-index, portal,
scroll lock, inert state, focus trap, or top-layer element. Consumer links or
other interactive content must not be placed in the default fill because
nested activation targets compete with native label activation.

## 13. Collections, async data, and identity

One Checkbox is not a collection. Repeated instances own independent native
checkedness even when they share a name. Citry render identity is private; the
component exposes no item key.

Select-all logic, group arrays, minimum selection, async option loading, and
aggregate error messages remain application composition or future
`CCheckboxGroup` work. A mixed Checkbox does not own or discover descendants.

## 14. Server render, morph, and cleanup

No-JavaScript output remains a usable styled two-state checkbox. Server
`indeterminate=True` is runtime-enhanced state: static HTML does not emit a
mixed ARIA value or mixed reflection that could become stale after native
activation. Client initialization sets the native IDL property and
`data-indeterminate` together. The native property supplies accessible mixed
semantics. Native form submission still depends on checkedness.

Client initialization sets current mirrors, the native indeterminate property,
Field capabilities, native invalid handling, controlled reconciliation, and
one reset listener on the resolved Form owner. Repeated initialization must not
duplicate listeners, Field registrations, diagnostics, or timers.

On correlated rerender, cleanup records current checkedness and
indeterminateness. A retained uncontrolled Checkbox restores both current
states after the new server HTML sets the next reset defaults. Controlled
client props then win. A fresh insertion uses server initial state.

Every uncanceled reset event owns an independent bounded task. A later canceled
reset cannot cancel restoration for an earlier uncanceled reset. Cleanup
cancels all pending tasks and any scheduled controlled reconciliation, removes
listeners and capability registration, clears a native-invalid Field source,
and removes the initialization marker.

Changing static external Form ownership requires Checkbox reinitialization.
Direct client mutation or dynamic binding of `form` is unsupported and
rejected.

## 15. Security and content trust

`name`, `value`, and `id` accept only plain-string semantics. The implementation
unwraps Citry constants, copies into an exact base `str` without honoring
`__html__`, normalizes line endings where applicable, validates, and only then
renders. Safe-string subclasses and arbitrary `__html__` objects cannot inject
attributes.

Default and description fills follow Citry's ordinary escaped/trusted template
rules. `attrs`, `input_attrs`, `class_`, and `style` are explicit trusted
authoring boundaries.

The component rejects:

- case-insensitive duplicates of singleton native attributes;
- static or dynamic `for`, `role`, `tabindex`, and `contenteditable` on the root;
- static or dynamic `aria-hidden` on either destination;
- static or dynamic `role`, `aria-checked`, `aria-required`, `aria-disabled`,
  `aria-readonly`, and `aria-invalid` on the native input;
- dynamic `aria-label` or `aria-labelledby`, and static ARIA naming when a
  default fill or Field label owns the visible name;
- replacement of `type`, checked, value, name, ID, required, disabled, Field
  markers, public reflected attributes, part markers, and Citry or Events
  runtime attributes;
- static or dynamic `readonly`;
- `x-model`, `x-modelable`, whole-object `x-bind`, `x-html`, and `x-text` on
  both the neutral root and native input;
- dynamic bindings targeting any owned native or public attribute, including
  shorthand, longhand, property, and case variants; and
- dynamic Form ownership.

Native event listeners and unrelated Alpine attributes remain allowed in
`input_attrs`. Consumer ARIA description and error IDREFs merge with concrete
Field relationships and never point at an element the component omitted.
Case-insensitive static `aria-describedby` and `aria-errormessage` values are
copied and merged once into browser data. Duplicate case spellings and every
dynamic/property binding alias for those two runtime-maintained IDREF
attributes are rejected.

## 16. Assets and performance

The family adds one component CSS block and one small client behavior block.
It uses no icon asset, font, global listener, overlay, or third-party runtime.
The check and mixed indicators are CSS on the native input.

The behavior adds native `input`, `change`, and `invalid` listeners per
instance plus one reset listener when a Form owner exists. It observes only
actual ancestor fieldsets so a dynamic native `disabled` attribute keeps the
public mirror aligned with the browser's effective state. Static no-runtime
output remains useful. Asset reports record raw, gzip, and Brotli size.
Diagnostic scaling records 1, 10, 100, and 1,000 Checkboxes without a release
timing gate. Human review decides whether repeated-instance cost is acceptable
before release.

## 17. Acceptance matrix

Required server evidence:

- defaults, every valid enum, every invalid enum/type, plain strings,
  Const strings, safe-string subclasses, hostile `__html__`, line ending and
  U+0000 handling;
- label, description, accessible-name-only, Field-composed, repeated-name,
  required, disabled, invalid, checked, mixed, and all variant/size/position
  render paths;
- phrasing-only public examples, no nested label/interactive default content,
  no description form controls/editable input emitters, and zero Nu HTML errors
  for the stable wrappers;
- exact anatomy, slot cardinality, Field slot/state conflicts, Field capability
  rejection, CForm owner conflicts, case-insensitive attributes, dynamic
  ownership rejection, uppercase static ARIA IDREF merging, dynamic IDREF alias
  rejection, visible-label and Field naming conflicts, label-free static naming,
  root/input object-spread and structural-content directive rejection, targeted
  unrelated binding acceptance, root/input `aria-hidden` rejection, merge
  precedence, and public outputs;
- Python composition, exports, library registration, structured reference, and
  exact wheel contents.

Required focused browser evidence:

- pointer, label, touch-equivalent click, Tab, Shift+Tab, and Space behavior;
- one bubbling input/change delivery and ordering, checked/mixed state at
  both handler times, a prop-effect flush between input and change without early
  restoration, focusin/focusout, captured invalid, the two-click native label
  sequence, controlled mirroring, unchanged control restoration,
  omission/reacquisition, invalid supply recovery, and no redundant same-value
  assignment;
- native `indeterminate` mapping to accessibility-tree mixed state with no
  authored `aria-checked` attribute;
- a focusable native input present in the accessibility tree, with static and
  dynamic `aria-hidden` rejected on both root and input;
- FormData checked/unchecked/repeated/disabled/unnamed/value cases, required
  validity, invalid episode entry/recovery, controlled false episode retention,
  consumer-updated true clearing, no programmatic episode creation, external
  invalid, reset, canceled reset ordering, external owner, Form-disabled
  dominance over local server and client false, reactive Form toggles,
  omission/invalid recovery, and cleanup;
- real correlated rerender preserving uncontrolled checked and mixed state,
  changing reset defaults, applying controlled props, and removing the root;
- visible-label, label-free, and Field accessible-name computation; Field
  descriptions, errors, external IDREF merging, generated-ID existence,
  standalone Form read-only ignoring, inherited Field read-only rejection,
  explicit Field opt-out, and one client capability diagnostic;
- computed variable and selector overrides, unlayered class rules before and
  after Citry CSS, both variants, all sizes, label positions, light/dark nested
  schemes, RTL, narrow wrapping, long text, zoom, forced colors, reduced
  motion, print, and host CSS coexistence;
- no serious or critical axe findings, no console/page errors, and zero Nu HTML
  errors across public examples.

Shared infrastructure records preview routes, screenshot profiles, assets,
diagnostic scaling, Lighthouse/manual tasks, and exact wheel qualification.
Automated presence does not replace manual keyboard, VoiceOver, NVDA, JAWS,
touch-device, 400 percent zoom, forced-colors, print, and visual-design review.

## 18. Compatibility classification

Stable public API:

- `CCheckbox`, input names and meanings, slots and data records;
- native event and FormData behavior;
- public variables, selectors, reflected attributes, validation errors, and
  Field/Form error behavior.

Behavioral and structural contract:

- native input plus an explicit internal label when default content exists;
- documented label, sibling description, and Field relationships;
- controlled ownership, reset, morph, keyboard, focus, and no-JS behavior.

Evolvable design:

- exact colors, spacing, radius, typography, and transition timing;
- anonymous body wrapper and internal pseudo-element drawing.

Private implementation:

- `.cui-*` classes, `--_cui-*` variables, handoff symbols, initialization and
  Field capability markers, JavaScript organization, and incidental markup.

## 19. Public documentation contract

The Checkbox page uses a coherent botanical field-guide theme. It begins with
visible, interactive results and then moves from shortest composition to forms,
control, mixed state, Field integration, environment, and customization.

| Source module | Reader task | Visible result and interaction | Controls or profiles | Contract coverage |
|---|---|---|---|---|
| `at_a_glance.py` | Recognize Checkbox appearance and purpose. | Three seed-catalog choices show unchecked, checked, and described states. | light/dark and narrow profile | first impression, labels, description, native toggling |
| `compose_checkbox.py` | Write the shortest template and Python forms. | One herbarium-label preference from each authoring surface. | none | template and composition parity, default slot |
| `configuration.py` | Compare presentation in one place. | One specimen checkbox updates variant, size, label position, checked, mixed, disabled, required, and invalid. | selects and checkboxes in docs controls | every client presentation/state input, no console errors |
| `forms_and_validation.py` | Submit and reset native checkbox values. | A seed-packet form shows required consent, repeated habitat values, FormData output, validation, and reset. | native submit/reset | successful controls, repeated names, required, reset, no hidden false value |
| `controlled_states.py` | Understand browser-owned and client-owned state. | Controlled, uncontrolled, release, and reacquire specimens. | in-preview action buttons and native listeners | checked ownership, event timing, release/reacquisition, same-value behavior |
| `indeterminate.py` | Build a select-all summary. | One mixed habitat summary controls three ordinary Checkboxes. | select all, clear, and individual toggles | checked versus indeterminate, aggregate app ownership, native mixed semantics |
| `field_states.py` | Compose Checkbox with Field and Form. | Required, invalid, disabled, and unsupported read-only cases are explained with valid runnable states. | Form-disabled and invalid toggles | Field ownership, labels, description/error IDREFs, capabilities |
| `label_and_description.py` | Use long labels, descriptions, external naming, and label position. | Botanical permissions wrap at narrow widths; a row-selection checkbox uses an ARIA label. | label position control | slots, accessible-name-only path, RTL, narrow text |
| `variants_and_sizes.py` | Compare the visual matrix. | Solid and outline in sm/md/lg, including checked, mixed, disabled, and invalid states. | none | geometry, state distinctions, token fallbacks |
| `theme_customization.py` | Apply two branded schemes. | Sunlit conservatory and moonlit field station scopes use variables plus public selectors. | theme switch and forced-colors profile | ancestor/root variables, selector override, nested color scheme, contrast |

Every snippet lives under `components/ccheckbox/snippets/` and is excluded from
the wheel. Configurator controls are collapsible docs chrome above the rendered
stage. Source is collapsed by default. Focused docs tests scroll each preview
into view, await the exact initialized controls, exercise representative
interaction, and assert no console errors. The shared Checkbox quality route
checks initial and active states with axe.
Invalid client-supply diagnostics remain focused E2E coverage rather than a
public example that intentionally logs an error.

`api.yml` exhaustively lists Inputs, Slots, Events, Methods, CSS, Attributes,
Selectors, and Interfaces. Empty Events and Methods sections use `-`. Native
events are taught in the guide, not mislabeled as component events.

## 20. Open decisions and deferred work

No design blocker is intentionally left open before independent review.

Deferred work:

- `CCheckboxGroup` needs its own evidence and specification for set-valued
  control, fieldset/legend, minimum selection, disabled descendants, group
  errors, reset, morph, and aggregate callbacks.
- Checkbox Card and a non-semantic Indicator may be considered after real
  application use proves the jobs cannot remain composition.
- Custom indicator slots wait for a proven client-reactive slot contract.
- Locale and translation integration remains the library-wide follow-up.
- Publication and released-artifact compatibility wait for the next Citry and
  Citry Core releases.
