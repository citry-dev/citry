# Citry UI Field and Input specification

**Status (2026-08-05): production contract, runtime, structured reference,
public example catalog, and focused automated evidence aligned. Human visual,
assistive-technology, mobile, autofill, and password-manager review remain
release evidence.** This family defines one styled relationship
owner, `CField`, and one styled native text control, `CInput`. A convenience
`CTextField`, input adornment shell, clear action, password reveal, and counter
remain separate product decisions.

## 1. Purpose and product bar

`CField` connects one visible label, one control, persistent instructions, and
an error message. It owns generated relationship IDs, required indication,
layout, and the effective required, disabled, read-only, and external-invalid
state for a control composed inside it.

`CInput` renders a native text-like `<input>`. It works inside or outside a
Field and preserves native editing, form submission, reset, constraints,
selection, focus, autocomplete, browser restoration, and events. Inside a
Field it consumes the Field state rather than defining a contradictory second
state. Outside a Field it owns the corresponding state itself.

Production-complete means:

- a label, description, and visible error always point to the intended primary
  control without duplicate IDs within one generated Field relationship;
- an enclosing Field and its control expose one coherent required, disabled,
  read-only, and invalid result;
- server HTML is labelled, editable, validatable, and submittable without
  JavaScript;
- controlled browser values, uncontrolled edits, native reset, IME
  composition, and server morphs do not corrupt text or caret ownership;
- native constraints and external/server errors remain distinct and compose
  predictably;
- variants, sizes, layouts, public variables, selectors, and meaningful
  states work in light and dark schemes; and
- consumer attributes and server-wired custom controls remain available
  without allowing replacement of component-owned relationships.

The common jobs and their shortest supported paths are:

| Job | Contract |
|---|---|
| Build a labelled text input | `CField` with `label` and `default` fills, with `CInput` inside the default fill |
| Add instructions or an error | `description` and `error` fills on `CField` |
| Submit or reset without JavaScript | optional native `name`, initial `value`, constraints through typed inputs or `attrs`, and native Form controls |
| Build a client-only search or filter | unnamed standalone `CInput` with an external accessible name |
| Start editable and later control the value | server `value`; optional browser `value` through `$c-props` |
| Show application or server invalid state | set `invalid` on `CField`, or on a standalone `CInput` |
| Use browser validation | native `required`, type, pattern, length, and other attributes |
| Change presentation | `variant`, visual `size`, Field `density`, Field `orientation`, and CSS variables |
| Use a textarea or another custom text-entry control | spread `CField` default-slot `control_attrs` onto one primary label target that supports the supplied native state attributes |
| Add icons, units, clear, password reveal, or a counter | application composition now; later purpose-built components after their behavior contracts are specified |

The family does not cover multiline editing, number parsing, masks, files,
selection controls, clear actions, password visibility, counters, input-local
rules, async validation, or arbitrary in-control content. Those jobs have
different value, caret, focus, event, accessibility, or form contracts.
Headless components remain parked.

## 2. Prior art and complaints

The family was re-audited from its runtime, render and browser tests, shared
quality route, composed uses, public guide, and structured reference before
the external comparison. Existing behavior remained provisional where those
artifacts disagreed.

| Product or standard | Version or review date | Docs, source, or issue inspected | Decision supported |
|---|---|---|---|
| Citry UI prototype | 2026-08-05 | `cfield.py`, Field/Input/Form browser tests, repeatable workflow, `field-input.states`, `api.md`, and `api.yml` | Retain native input, server IDs, Field/Form context, native constraints, persistent error region, public variables, and native events. Repair state disagreement, quality-route drift, controlled recovery, IME handling, nested selectors, and evidence claims. |
| HTML Living Standard | reviewed 2026-08-05 | [Input](https://html.spec.whatwg.org/multipage/input.html) and [forms](https://html.spec.whatwg.org/multipage/forms.html) | Native value/default value, successful-control, reset, constraints, form ownership, selection, and text-like type behavior. |
| WAI and WAI-ARIA 1.2 | reviewed 2026-08-05 | [Labels](https://www.w3.org/WAI/tutorials/forms/labels/), [instructions](https://www.w3.org/WAI/tutorials/forms/instructions/), [validation](https://www.w3.org/WAI/tutorials/forms/validation/), and [`aria-errormessage`](https://www.w3.org/TR/wai-aria-1.2/#aria-errormessage) | One visible explicit label, persistent instructions, textual errors, invalid relationships, and real assistive-technology verification. |
| Vuetify | 4.1.7 source and docs reviewed 2026-08-05 | [`VTextField`](https://github.com/vuetifyjs/vuetify/blob/v4.1.7/packages/vuetify/src/components/VTextField/VTextField.tsx), [`VField`](https://github.com/vuetifyjs/vuetify/blob/v4.1.7/packages/vuetify/src/components/VField/VField.tsx), [`VInput`](https://github.com/vuetifyjs/vuetify/blob/v4.1.7/packages/vuetify/src/components/VInput/VInput.tsx), [Text fields page](https://github.com/vuetifyjs/vuetify/blob/v4.1.7/packages/docs/src/pages/en/components/text-fields.md), [duplicate-label report #21914](https://github.com/vuetifyjs/vuetify/issues/21914), and [custom composition report #22036](https://github.com/vuetifyjs/vuetify/issues/22036) | Use Vuetify's job breadth as the primary styled-suite reference. Retain separate Field and control responsibilities, one label node, simple variants/density, and native attributes. Reject the three-layer aggregate API, floating labels, input-local rules, fake focus/dirty props, and ambiguous custom composition. |
| React and React Aria Components | React 19.2 docs and React Aria 1.20.0 reviewed 2026-08-05 | [Native Input](https://react.dev/reference/react-dom/components/input), [TextField](https://react-aria.adobe.com/TextField), [Forms](https://react-aria.adobe.com/forms), and [controlled validation report #8659](https://github.com/adobe/react-spectrum/issues/8659) | Compound Field/Label/Input/Error anatomy, synchronous controlled updates, native forms, and explicit controlled-validation tests. |
| React Spectrum | 3.47.3 docs reviewed 2026-08-05 | [TextField](https://react-spectrum.adobe.com/v3/TextField.html) and [Forms](https://react-spectrum.adobe.com/v3/forms.html) | Separate default and controlled value, validation behavior, label, help, and error responsibilities. |
| Material UI | 9.3.0 docs and source reviewed 2026-08-05 | [TextField](https://mui.com/material-ui/react-text-field/), [API](https://mui.com/material-ui/api/text-field/), [source](https://github.com/mui/material-ui/blob/v9.3.0/packages/mui-material/src/TextField/TextField.js), [Input props complaint #1578](https://github.com/mui/material-ui/issues/1578), and [error-message request #38929](https://github.com/mui/material-ui/issues/38929) | A convenience wrapper can cover common use, but wrapper versus native-input props and helper-text layout create lasting confusion. Keep the native root and defer `CTextField` until forwarding and state ownership are proven. |
| Chakra UI and Ark UI | 3.36.1 and 5.38.0 reviewed 2026-08-05 | [Chakra Field](https://chakra-ui.com/docs/components/field), [Chakra Input](https://chakra-ui.com/docs/components/input), [Ark Field](https://ark-ui.com/docs/components/field), and [broken relationship report #3824](https://github.com/chakra-ui/ark/issues/3824) | Separate relationship owner and native control; verify optional-part IDREFs and keep adornments as composition. |
| PrimeVue | 5.0.0 reviewed 2026-08-05 | [InputText](https://primevue.dev/inputtext/), [FloatLabel](https://primevue.org/floatlabel/), [Forms](https://primevue.dev/forms/), and [InputGroup](https://primevue.dev/inputgroup/) | Keep a native-style Input small and move labels, groups, icons, and form coordination into explicit owners. |
| Web Awesome | 3.11.0 reviewed 2026-08-05 | [Input](https://webawesome.com/docs/components/input/), [form controls](https://webawesome.com/docs/form-controls/), and [validity synchronization report #1205](https://github.com/shoelace-style/webawesome/issues/1205) | Native-like value, reset, and validation are valuable but subtle to recreate behind a wrapper. A real native Input is the safer Citry baseline. |

Vuetify carries roughly 30 percent of product-comparison weight. Standards are
acceptance gates rather than scored products. Every relevant Vuetify job has
an explicit Citry disposition:

| Vuetify surface or job | Citry support path | Citry surface | Decision |
|---|---|---|---|
| value, ID, name, type, autocomplete, placeholder | direct API and native HTML | `CInput` inputs and `attrs` | Adopt the common native subset; make `name` optional. |
| visible label, hint, messages, errors | direct slots | `CField.label`, `description`, and `error` | Use one visible label and two message roles instead of an arbitrary message collection. |
| disabled, read-only, required, external invalid | direct Field state and inheritance | `CField`; standalone `CInput` only outside a Field | One owner prevents contradictory marker, native, and ARIA state. |
| rules, validation timing, `maxErrors`, reset-validation methods | native HTML or application/Form layer | native constraints and external error content | Omit the input-local rules engine and duplicated methods. |
| controlled focus, active, dirty, arbitrary role | omitted | native DOM | Native focus and value are authoritative; incompatible roles are not supported. |
| variants and density | direct API | three Input variants, visual `size`, Field density and orientation | Keep a small stable vocabulary. |
| color, dimensions, rounding, theme, full width | CSS or utility classes | `class_`, `style`, `attrs`, and public variables | Do not grow the frequent constructor with styling props. |
| prefix, suffix, prepend/append inner and outer content | composition or later component | application wrapper; future input group | A native Input cannot contain children. |
| clearable and clear slot/event | deferred | future purpose-built clear action | Requires controlled-request, read-only, focus, Tab-order, accessible-name, and reset decisions. |
| password reveal | separate component | future password field | Security and action behavior are not ordinary Input presentation. |
| counter | composition or deferred helper | native `maxlength` now | Unicode count, announcement, and layout semantics need their own contract. |
| loading and loader slot | composition | Form/action/status owner | Async ownership does not belong to a text Input. |
| native events and methods | native HTML | native root | Keep `input`, `change`, `invalid`, focus, selection, validity, and custom-validity APIs directly available. |

The adopted pattern is one Field relationship owner plus one real native
control, persistent help and error regions, optional native form identity,
native constraints, controlled and uncontrolled values, a small visual
vocabulary, and CSS customization. Citry rejects floating labels, arbitrary
root polymorphism, an input-local form store, duplicated callbacks for native
events, and one monolithic prop union for adornments and specialist behaviors.

## 3. Public composition and anatomy

The common template path omits explicit IDs:

```citry-html
<c-CField required>
  <c-fill name="label">
    Tidepool name
  </c-fill>
  <c-fill name="default">
    <c-CInput
      name="tidepool_name"
      autocomplete="off"
    />
  </c-fill>
  <c-fill name="description">
    Use the name printed on the observation marker.
  </c-fill>
</c-CField>
```

Python composition stays explicit about slots:

```python
from citry_ui import CField, CInput

name_field = CField(
    required=True,
    slots={
        "label": "Tidepool name",
        "default": CInput(name="tidepool_name"),
        "description": "Use the name printed on the observation marker.",
    },
)
```

| Component | Semantic root | Attribute destination | Required relationships |
|---|---|---|---|
| `CField` | `<div>` group | `class_`, `style`, and `attrs` merge onto the Field root | one required visible label and exactly one registered or marked primary control in the default slot |
| `CInput` | native `<input>` | `class_`, `style`, and `attrs` merge onto the native Input | inherits the nearest Field when present; otherwise its accessible name is consumer-owned |

`CField` owns direct root children for `label`, `control`, optional
`description`, and persistent `error`. The required indicator is a child of
the label. `CInput` owns one native Input and no wrapper. The public selectors
document those elements; no private `.cui-*` class is public.

An explicit `CField.control_id` fixes the control and related ID base. A
`CInput.id` inside that Field must be omitted or match. Outside a Field,
`CInput` generates an ID when none is supplied. Generated IDs are unique per
render and stable only while the component identity is retained.
Consumers remain responsible for keeping explicit `control_id` and standalone
`id` values unique across sibling component instances.

Nested Fields are invalid. A Field accepts exactly one registered or marked
primary control. Citry UI controls register during server rendering, so two
Input or Combobox controls fail before output. Every primary control receives
a private marker through Field bindings; client initialization rejects zero or
multiple marked controls, including malformed custom-control content. A
compound control such as Combobox may still contain auxiliary buttons. A
custom control must spread `control_attrs` onto its one primary label target.

`class_` and `style` are direct root inputs accepting Citry's structured
values. `attrs` accepts other allowed native, ARIA, `data-*`, and Alpine
attributes. It may still contribute class and style, which merge with the
direct inputs. Owned IDs, relationships, state/configuration attributes,
part markers, and private initialization markers cannot be replaced.

The post-implementation anatomy review retains both public components:
`CField` is reusable by Input, Combobox, textarea, and custom controls;
`CInput` is useful standalone and preserves a native root. Neither exists only
to group declarations. A convenience wrapper would add a distinct frequent
authoring path rather than replace either primitive.

## 4. Server inputs and client inputs

`CField` Python inputs:

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `control_id` | `str | None` | generated | structural server-only | fixes the control ID and derives Field, label, description, and error IDs |
| `required` | `bool` | `False` | reactive configuration fallback | owns native required state and the visual indicator when the registered control supports required |
| `disabled` | `bool | None` | inherit Form | reactive configuration fallback | disables the Field control; an enclosing disabled Form always wins |
| `readonly` | `bool | None` | inherit Form | reactive configuration fallback | makes a supporting Field control read-only; an unsupported true value raises after server control registration |
| `invalid` | `bool` | `False` | reactive external-invalid fallback | combines with native invalid state without changing native validity |
| `orientation` | `vertical | horizontal` | `vertical` | reactive layout fallback | selects stacked or side-by-side layout |
| `density` | `default | comfortable | compact` | `default` | reactive spacing fallback | changes Field-region spacing, not native Input character width |
| `class_` | Citry class value or `None` | `None` | structural server-only | merges classes onto the Field root |
| `style` | Citry style value or `None` | `None` | structural server-only | merges inline styles onto the Field root |
| `attrs` | mapping or `None` | `None` | structural server-only | merges allowed attributes onto the Field root |

`CField` client inputs:

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `required` | Boolean | server fallback | invalid, server fallback | unsupported true resolves to false with one diagnostic | required marker, Field context, native control, reflected attribute |
| `disabled` | Boolean | server/Form fallback | invalid, fallback | same | Field context, native control, reflected attribute; disabled Form still wins |
| `readonly` | Boolean | server/Form fallback | invalid, fallback | unsupported true resolves to false with one diagnostic | Field context, supporting native control, reflected attribute |
| `invalid` | Boolean | server fallback | invalid, fallback | same | external-invalid source, Field context, error visibility, Input ARIA, reflected attribute |
| `orientation` | enum | server fallback | invalid, fallback | same | layout and reflected attribute |
| `density` | enum | server fallback | invalid, fallback | same | spacing and reflected attribute |

`CInput` Python inputs:

| Python input | Type | Default | Class | Validation and effect |
|---|---|---|---|---|
| `name` | `str | None` | `None` | structural server-only | gives the native successful control a submitted name; `None` creates a client-only or unnamed control |
| `type` | `text | email | password | search | tel | url` | `text` | structural server-only | selects a text-like native Input type |
| `id` | `str | None` | Field ID or generated | structural server-only | fixes native identity without breaking an enclosing Field relationship |
| `value` | `str | None` | `None` | initial value | sets the server value and native reset default |
| `required` | `bool | None` | Field value or `False` | standalone reactive fallback | valid only outside `CField`; inside a Field configure `CField.required` |
| `disabled` | `bool | None` | Field/Form value or `False` | standalone reactive fallback | valid only outside `CField`; a disabled Form always wins |
| `readonly` | `bool | None` | Field/Form value or `False` | standalone reactive fallback | valid only outside `CField` |
| `invalid` | `bool | None` | Field value or `False` | standalone external-invalid fallback | valid only outside `CField`; does not create native invalidity |
| `autocomplete` | `str | None` | `None` | structural server-only | sets the native autocomplete hint |
| `inputmode` | `str | None` | `None` | structural server-only | sets the virtual-keyboard hint |
| `placeholder` | `str | None` | `None` | structural server-only | sets placeholder text; never substitutes for an accessible name |
| `variant` | `outline | filled | plain` | `outline` | reactive presentation fallback | selects native Input presentation |
| `size` | `sm | md | lg` | `md` | reactive presentation fallback | selects target height, padding, and text size |
| `class_` | Citry class value or `None` | `None` | structural server-only | merges classes onto the native Input |
| `style` | Citry style value or `None` | `None` | structural server-only | merges inline styles onto the native Input |
| `attrs` | mapping or `None` | `None` | structural server-only | merges allowed native constraints, ARIA, Alpine, and `data-*` attributes |

The visual `size` input uses the concise `sm`, `md`, and `lg` vocabulary.
HTML's separate character-width `size` attribute remains
available through `attrs={"size": 24}`. The API reference calls out this
destination explicitly.

`CInput` client inputs:

| Client input | Type | Omitted | `null` | Invalid value | Affected surfaces |
|---|---|---|---|---|---|
| `value` | string | uncontrolled from current DOM value | invalid | log once and retain the previous valid ownership/value | native current value; not the reset default |
| `required` | Boolean | inherited or server fallback | invalid | fallback outside Field; diagnostic and Field value inside Field | native property, validity, reflected attribute |
| `disabled` | Boolean | inherited or server fallback | invalid | same; disabled Form still wins | native property, focus/submission, reflected attribute |
| `readonly` | Boolean | inherited or server fallback | invalid | same | native property, editing, reflected attribute |
| `invalid` | Boolean | inherited or server fallback | invalid | same | external-invalid source, ARIA, reflected attribute |
| `variant` | enum | server fallback | invalid | log once and use server fallback | presentation and reflected attribute |
| `size` | enum | server fallback | invalid | same | geometry and reflected attribute |

A valid supplied client value wins. Removing `value` releases control while
preserving the last controlled DOM value. An invalid value never silently
switches ownership or erases the last valid value. Removing another client
input returns only that field to its inherited or server fallback.

Inside a Field, any non-`None` Python value for Input `required`, `disabled`,
`readonly`, or `invalid` raises, even when it equals the Field value. Any
supplied client value for one of those names is ignored and reports one
diagnostic per distinct episode. Configure the Field instead.

## 5. State model

Field effective state is:

- `required`: the current Field configuration, then false when the registered
  control does not support required;
- `disabled`: enclosing native Form disabled OR current Field configuration;
- `readonly`: explicit Field configuration, otherwise inherited Form value,
  then false when the registered control does not support read-only;
- `external invalid`: current Field invalid configuration; and
- `effective invalid`: external invalid OR the one control's native invalid
  episode.

Inside a Field, a library control consumes those values and cannot override
them. Controls register whether they support required and read-only. An
effective server true value raises after an unsupported capability registers.
In the browser, an unsupported true request reports once and resolves to false
before Field context, the required indicator, and reflected attributes update.
`CInput` supports both capabilities, so its existing behavior is unchanged.
Outside a Field, Input resolves its own server and client values, with an
enclosing Form's disabled state still dominant.

Client capability registration is reactive and generation-scoped. A control
initialization registers its current required/read-only support through the
private Field context and cleanup unregisters only that generation. A child
replacement may change capabilities while Field is retained; the new
registration becomes authoritative in the same lifecycle turn before Field
effects settle. Stale cleanup cannot erase a newer registration.

| Transition | Trigger and guard | Native, ARIA, visual, and form result |
|---|---|---|
| enter native-invalid episode | native `invalid` from the one control | native validity is unchanged; Field and Input gain invalid presentation; error relationships and visible error activate; a physical enclosing Form records attempted validation |
| clear native-invalid episode | `input`, `change`, reset, or reactive constraint change leaves `validity.valid` true | remove only native-invalid source; external invalid may keep the Field invalid |
| set or clear external invalid | valid Field or standalone Input client configuration | update ARIA, error visibility, reflected attributes, and Field context; never call `setCustomValidity()` |
| acquire controlled value | valid supplied client string | set DOM current value; keep server/default value for reset semantics |
| controlled user edit | native input event while controlled and not composing | consumer receives the native event; a microtask restores the latest supplied value |
| controlled IME composition | `compositionstart`, input events, optional client value changes, then `compositionend` | browser composition text remains untouched during composition; supplied value updates are remembered but not written; a microtask after `compositionend` restores the latest valid supplied value |
| release controlled value | client value becomes omitted | preserve current value and return editing ownership to browser |
| invalid controlled supply | non-string or `null` | report once; preserve prior valid control mode and value |
| native reset | enclosing native form resets | uncontrolled current value returns to native default; controlled current value returns to latest controlled value after reset completes; native-invalid episode clears |

Disabled removes the Input from successful form controls and editing. Read-only
keeps it focusable and successful but prevents user edits. Neither state erases
configured values or external error content. Form disabled cannot be
overridden because its native fieldset already disables descendants.

## 6. Slots and slot data

| Owner | Slot | Required | Cardinality | Slot data | Fallback |
|---|---|---|---|---|---|
| `CField` | `label` | yes | one | empty `CFieldLabelSlotData` | none |
| `CField` | `default` | yes | one | `CFieldDefaultSlotData` with bindings, IDs, and effective server state | none |
| `CField` | `description` | no | one | empty `CFieldDescriptionSlotData` | omitted |
| `CField` | `error` | no | one | empty `CFieldErrorSlotData` | mounted empty polite region |

`CFieldDefaultSlotData` contains `control_attrs`, `control_id`, `label_id`,
`description_id`, `error_id`, `is_required`, `is_disabled`, `is_readonly`,
and `is_invalid`. Its values are the server-render snapshot. Spreading
`control_attrs` applies the owned ID, native state, relationship attributes,
and private one-control marker.

A custom control receives correct server relationships but does not
automatically consume later reactive Field/Form context, report native
invalidity, or register with `CForm`. A component implementing those browser
behaviors may use Citry UI's private integration internally, but no public
custom-control client protocol is frozen in this family. Public docs must not
imply otherwise.

`CInput` defines an empty Slots schema. A native Input cannot contain slot
content. Dynamic slots do not apply.

## 7. Callbacks, native events, and methods

The family adds no component-authored callback or custom DOM event. Consumers
listen to native `input`, `change`, `invalid`, `focus`, `blur`, and composition
events with Alpine `@...` handlers. Controlled examples synchronize through
native `@input`; `onValueChange` is not a supported Input prop.

The native root exposes `focus()`, `blur()`, `select()`, selection-range,
`checkValidity()`, `reportValidity()`, and `setCustomValidity()` directly. No
proxy method is necessary.

## 8. Semantics, keyboard, focus, and assistive technology

The visible native label points at the one marked primary control. Persistent
description text is included in `aria-describedby`. While invalid, the error
is included in the error relationship and description fallback. Consumer
IDREFs merge in first-seen order without duplicates.

The error region remains mounted with `aria-live="polite"`, even when no error
fill exists, so later text can be announced without creating a new live
region. Whether simultaneously using `aria-errormessage`, an
`aria-describedby` fallback, and the mounted live region causes repeated
announcements remains a named release-evidence question. VoiceOver/Safari,
NVDA/Firefox, and a Chromium screen-reader combination must settle it before
the relationship is frozen for v1.

The required indicator is visual and hidden from assistive technology. A
visible label is mandatory for `CField`. Required-slot validation proves the
fill exists, not that its consumer content is visibly rendered; empty or
visually hidden label content is a consumer error. A standalone Input may use an
external `<label for>`, `aria-label`, or a valid `aria-labelledby`
relationship. Placeholder text is never its accessible name.

Editing, selection, clipboard, undo, mobile keyboard, password manager,
autofill, pointer, touch, and keyboard behavior remain native. Citry UI
intercepts no editing key. Focus uses the native Input and a visible
`:focus-visible` treatment.

## 9. Native forms and validation

An Input with a non-empty `name` that is not disabled is a successful native
control. An unnamed Input remains editable and validatable but contributes no
entry to `FormData`. Native `required`, type, pattern, minimum/maximum length,
and other constraints supplied through typed fields or `attrs` participate in
normal form validation.

`invalid=True` changes presentation and accessibility state but does not make
`checkValidity()` fail. Server validation remains authoritative; application
code decides when an edit clears a server error. Custom validity remains a
native method owned by the consumer.

Native submit, Enter submission, multiple submitters, reset, autocomplete,
autofill, virtual keyboards, password managers, and no-JavaScript behavior
remain intact. `attrs["form"]` may associate a standalone Input with a static
external form. Inside `CForm`, redirecting the Input to another native form is
an error because Citry Form registration and native ownership would disagree.

An enclosing disabled `CForm` uses a native disabled fieldset. That native
state always wins over descendant configuration and removes controls from
submission. Read-only Form context remains a Citry fallback and may be
overridden at the Field or standalone Input.

## 10. Styling and theme contract

The family follows [`../ui_theme.md`](../ui_theme.md). `CInput` variants are
`outline`, `filled`, and `plain`; visual sizes are `sm`, `md`, and `lg`.
`CField` density changes spacing between its regions, while orientation changes
label/control layout.

`CField` public variables:

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-field-gap` | length | gap between Field regions | density-derived, starting at `0.5rem` |
| `--cui-field-label-color` | color | label foreground | `CanvasText` |
| `--cui-field-label-weight` | number or keyword | label weight | `600` |
| `--cui-field-description-color` | color | description foreground | muted `CanvasText` mix |
| `--cui-field-error-color` | color | error foreground | scheme-aware danger color |
| `--cui-field-required-color` | color | required-indicator foreground | effective Field error color |

`CInput` public variables:

| Public variable | Value type | Purpose | Current default |
|---|---|---|---|
| `--cui-input-background` | color | resting surface | `Canvas`, variant adjusted |
| `--cui-input-foreground` | color | entered text | `CanvasText` |
| `--cui-input-border-color` | color | resting border | subtle `CanvasText` mix, variant adjusted |
| `--cui-input-hover-border-color` | color | enabled hover border | stronger `CanvasText` mix |
| `--cui-input-focus-color` | color | focus border and outline | `Highlight` |
| `--cui-input-invalid-border-color` | color | invalid border | scheme-aware danger color |
| `--cui-input-disabled-background` | color | disabled surface | subtle Canvas mix |
| `--cui-input-placeholder-color` | color | placeholder foreground | muted `CanvasText` mix |
| `--cui-input-radius` | length | corner radius | `0.5rem`, or `0` for plain |
| `--cui-input-height` | length | minimum target height | visual-size derived |
| `--cui-input-inline-padding` | length | logical inline padding | visual-size derived |
| `--cui-input-block-padding` | length | logical block padding | visual-size derived |
| `--cui-input-font-size` | length | entered-text size | visual-size derived |

| Public selector | Element and purpose | Supported conditions | Stable relationship |
|---|---|---|---|
| `[data-citry-ui-part="field"]` | Field root and attribute destination | all | root |
| `[data-citry-ui-part="label"]` | native visible label | all | direct child of Field root |
| `[data-citry-ui-part="required-indicator"]` | visual required mark | required or hidden | child of label |
| `[data-citry-ui-part="control"]` | default-slot wrapper | all | direct child of Field root |
| `[data-citry-ui-part="description"]` | persistent instructions | when supplied | direct child of Field root |
| `[data-citry-ui-part="error"]` | persistent polite error region | hidden or invalid | direct child of Field root |
| `[data-citry-ui-part="input"]` | native Input and attribute destination | all | Input root |

| Public reflected attribute | Values | Meaning |
|---|---|---|
| Field `data-required` | present or absent | effective required state |
| Field `data-disabled` | present or absent | effective disabled state |
| Field `data-readonly` | present or absent | effective read-only state |
| Field `data-invalid` | present or absent | effective external or native invalid state |
| Field `data-orientation` | `vertical | horizontal` | effective layout |
| Field `data-density` | `default | comfortable | compact` | effective spacing |
| Input `data-required` | present or absent | effective native required state |
| Input `data-disabled` | present or absent | effective native disabled state |
| Input `data-readonly` | present or absent | effective native read-only state |
| Input `data-invalid` | present or absent | effective external or native invalid state |
| Input `data-variant` | `outline | filled | plain` | effective presentation |
| Input `data-size` | `sm | md | lg` | effective visual size |

Public variables are inherited inputs resolved through private effective
variables. Default rules use the `citry-ui.theme` layer and low specificity.
Field CSS targets its direct owned parts so a nested Combobox or other
component with an `error` part cannot inherit Field-internal styling by name.
Private classes, behavior markers, and private variables are not public API.

## 11. Environmental behavior

Every state, variant, and size must work in light and dark, including nested
opposite `color-scheme` scopes. Logical properties and authored text direction
support LTR and RTL. Horizontal Fields collapse to vertical at the documented
narrow viewport breakpoint; the component does not claim container-query
behavior in this version.

Long labels, descriptions, errors, placeholders, and values wrap or scroll
without clipping at 200 and 400 percent zoom. Forced colors retains the native
border, invalid distinction, and focus outline. The family has no animation,
so reduced motion requires no alternate state. Autofill remains legible and
browser-owned. Print output keeps labels, values, descriptions, and visible
errors readable without relying on background color.

The family-authored visible glyph is the required indicator. All words come
from consumer slots or native browser UI. Placeholder, description, and error
translation plus direction remain application-owned until the localization
follow-up defines a broader contract.

## 12. Overlay and layering behavior

The family creates no overlay and owns no stacking behavior. Browser autofill,
password-manager, datalist, and picker UI remain platform-owned.

## 13. Collections, async data, and identity

The family owns no collection or request. Each control's stable Citry identity,
native ID, and optional name identify it. Repeatable workflows keep those
values stable while reordering. Server or async validation must associate a
result with the current logical field and must not overwrite a newer edit.

## 14. Server render, morph, and cleanup

Server output is labelled, editable, constrained, and submittable. Field
context is provided before descendant client initialization. Input registers
with the nearest Citry Form, listens to its native form reset, and removes all
listeners and registration on cleanup.

Morphing retained identity preserves uncontrolled current value, selection,
focus, and active IME composition. A new server `value` updates the native
default without silently overwriting an uncontrolled current edit. Controlled
browser value remains authoritative while supplied. Reinitialization must not
duplicate listeners, registrations, invalid sources, or diagnostics.

Static external-form association is resolved at initialization. A morph that
changes native form ownership must reinitialize registration and reset
listening; silently retaining the old owner is invalid.

Every native reset event owns an independent bounded deferred task. A later
reset cannot cancel an earlier task because either event may be canceled
independently. Each task checks its event's final `defaultPrevented` state and
reads the latest controlled value. Cleanup cancels every outstanding task.

## 15. Security and content trust

Label, description, error, placeholder, and values follow Citry's ordinary
escaping. Trusted HTML remains an explicit application decision. `attrs`
cannot replace owned identity, state, ARIA, part, or browser-expression
attributes. Pattern strings and native constraints are consumer input, not
server-side validation or sanitization.

Password values must never be copied into reflected attributes, diagnostics,
slot data, or quality records. Autofill and password-manager behavior remains
browser-owned. Generated IDs are escaped at the HTML boundary and validated
against whitespace.

## 16. Assets and performance

The family adds one shared Field CSS/initializer and one shared Input
CSS/initializer only when used. It adds no icon, font, request, observer,
timer, or document-level listener. The combined target remains below 8 KiB
gzip. One hundred paired Fields must release every listener and Form
registration after removal. Measurements stay bounded to the representative
state route and do not gate reversible visual tuning.

## 17. Acceptance matrix

Automated evidence must cover:

- every Python schema value and invalid type, optional `name`, generated and
  explicit IDs, owned-attribute rejection, direct classes/styles, all slots,
  and Python composition;
- one-control enforcement, nested Field rejection, Input and Combobox Field
  registration, required/read-only capability registration, unsupported
  server/client fallback, unchanged Input behavior, and Field-owned state
  agreement;
- retained-Field child replacement with changing capabilities, generation-safe
  unregister, and no stale or transient reflected Field state;
- Form disabled dominance, read-only fallback, native successful-control and
  reset behavior, external form ownership, and dynamic cleanup;
- same-turn uncanceled then canceled reset and canceled then uncanceled reset,
  plus cleanup of every pending reset task;
- all client omitted, valid, `null`, invalid, removal, and recovery paths;
- native invalid entry and clearing, external plus native invalid sources,
  consumer IDREF merging, and persistent error-region behavior;
- controlled and uncontrolled values, IME, caret/selection, reset, morph,
  fragment insertion, repeated initialization, and removal;
- variants, visual sizes, densities, orientations, public variables,
  selectors, nested part isolation, two brands, light/dark, RTL, forced
  colors, narrow width, long content, and zoom;
- axe, HTML validity, clean-wheel rendering, compressed assets, and bounded
  repeated-instance evidence; and
- reusable Field/Input/Form/Combobox compositions without duplicated state or
  styling.

Manual evidence must cover VoiceOver/Safari, NVDA/Firefox, one Chromium screen
reader, label/error announcement order, keyboard editing, IME, autofill,
password managers, mobile virtual keyboards, touch, 400 percent zoom, forced
colors, and final visual hierarchy. Automated axe or Lighthouse results do not
replace those sessions.

## 18. Compatibility classification

Stable public API includes component and schema names, server and client input
names and meanings, slots and slot data, state ownership, native event policy,
form output, controlled transitions, public variables, selectors, reflected
attributes, and validation errors. The native Input root, visible label, one
primary-control relationship, persistent error region, and useful
server-rendered behavior are structural contracts. The exact combination of
`aria-errormessage`, error inclusion in `aria-describedby`, and polite live
region behavior remains provisional until the named assistive-technology
matrix is complete.

Exact colors, spacing, radius, narrow viewport breakpoint, and focus-ring
drawing are evolvable design. Private `.cui-*` classes, private variables,
browser-initialization markers, one-control marker, context keys, and
JavaScript organization are private implementation.

## 19. Public documentation contract

[`cfield/api.md`](../../../packages/py/citry_ui/citry_ui/components/cfield/api.md)
is the family-owned reader-first guide. Its sibling `api.yml` is the exhaustive
structured reference. The guide teaches the ordinary labelled Input first,
then presentation and states, forms and controlled values, custom controls,
environmental behavior, and customization.

The page uses one coastal tidepool field-journal theme. Copy stays concrete:
observation sites, shore conditions, species notes, tide alerts, and day/night
shore surveys. It does not mix themes or use generic workplace fixtures.

| Order and module | Reader task and fixture | Visible states and interaction | Controls and environmental cases | Contract coverage and focused evidence |
|---|---|---|---|---|
| 1. `at_a_glance.py` | Recognize a complete tidepool sighting Field and observer-email Field. | Label, description, required marker, entered text, focus, and visible invalid/error state. | Responsive wrapping; inherited light/dark. | First impression, anatomy, native editing, required/invalid distinction; load, label activation, typing, console, and narrow-overflow smoke. |
| 2. `labelled_input.py` | Compose the smallest complete labelled Input without explicit IDs. | Ordinary generated relationships and editable value. | No controls. | Template and Python composition, optional `name`, type, autocomplete, and required named fills. |
| 3. `configuration.py` | Configure one tidepool-site Field. | Orientation, density, variant, visual size, required, disabled, read-only, and invalid update immediately. | Four selects and four checkboxes in docs controls. | Every visual client input and Field-to-Input state; focused control-to-DOM check with no console errors. |
| 4. `variants.py` | Choose Input presentation. | Outline, filled, and plain with identical content. | Narrow wrapping and operable focus/hover. | Variant hierarchy and native root. |
| 5. `sizes_and_layout.py` | Choose visual size, Field spacing, and label layout. | `sm`, `md`, `lg`; three densities; vertical and horizontal Fields. | Long label/description and narrow viewport. | Geometry, target height, wrapping, and documented viewport fallback. |
| 6. `field_states.py` | Compare required, disabled, read-only, external-invalid, and Form-disabled states. | Coherent Field/control states shown side by side. | One Form-disabled toggle; standalone Input state example. | State ownership, required indicator, disabled dominance, read-only submission, and persistent error region. |
| 7. `validation_and_forms.py` | Validate, submit, and reset a native tide-alert form. | Native email failure, visible error, correction, submitted FormData, and reset. | Real native submit/reset interaction. | Constraints, native-invalid lifecycle, ARIA, successful controls, Enter, reset; focused Chromium/Firefox/WebKit journey. |
| 8. `controlled_values.py` | Compare uncontrolled editing with a client-controlled species filter. | Replace, release, reacquire, edit, and reset value ownership. | In-preview native-event owner controls. | Controlled phases, invalid-supply recovery, composition-safe restoration, and no invented callback. |
| 9. `native_input_types.py` | Use browser-native email, search, telephone, URL, and password behavior. | Text-like types plus an unnamed standalone search Input. | Narrow layout; mobile, autofill, and password-manager manual profiles. | Type allowlist, optional name, accessible standalone Input, autocomplete, inputmode, and native attrs. |
| 10. `custom_control.py` | Connect a multiline shore observation control. | Native textarea spreads exact Field bindings. | No controls. | Slot-data shape, one-control marker, server relationships, and explicit reactive limitation. |
| 11. `direction_and_content.py` | Support long content and text direction. | English LTR and Arabic RTL Fields with long labels/messages. | Narrow viewport; zoom profiles. | Logical CSS, wrapping, direction, and focus order. |
| 12. `theme_customization.py` | Theme a sunlit shore and moonlit low-tide survey. | Public variable and selector overrides with focused and invalid controls. | Explicit light/dark scopes; forced-colors profile. | Ancestor/root variables, exact public selectors, nested scheme, contrast, and computed-style check. |

The reusable `field-input.states` route covers a bounded pairwise set rather
than duplicating every component test. It must initialize every expected
component, contain a real Form for reset, use native `@input` for controlled
state, assert the representative action changed the intended state before axe,
and fail on console errors.

The structured reference lists every server and client input, slot and exact
slot-data shape, native event policy, public variable, reflected attribute,
selector, and named interface with stable anchors. Examples use no private
class, variable, context key, or behavior marker.

## 20. Open decisions and deferred work

- `aria-errormessage`, `aria-describedby`, and the polite region remain a
  release-blocking assistive-technology disposition. The implementation may
  change before v1 if the named matrix finds duplicate or missing
  announcements.
- `CTextField` remains deferred until independent applications demonstrate a
  dominant composition and a forwarding table can preserve Field/Input state,
  slots, attributes, client props, native root behavior, and asset cost.
- Input groups, prefix/suffix content, clear actions, password reveal,
  counters, textarea, number, masking, and file inputs require separate
  specifications.
- A public custom-control browser registration protocol remains deferred. The
  current slot contract guarantees server relationships only.
- A container-query layout may replace the viewport fallback after the stable
  Field anatomy can support it without an administrative public wrapper.
- Full manual assistive-technology, autofill, password-manager, mobile, and
  visual sign-off blocks release, not implementation of the automated slice.
