---
title: Field and Input
description: Build labelled native text controls with Citry UI Field and Input.
---

# Field and Input

Use `CField` to connect one visible label, one control, instructions, and an
error message. Use `CInput` for a styled native text input. The pair generates
stable IDs and keeps required, disabled, read-only, and invalid state aligned.

## Field and Input at a glance

The Input remains a native `<input>`. Browser editing, forms, validation,
selection, autocomplete, reset, and events continue to work normally.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cfield/snippets/at_a_glance.py"
  title="Field and Input at a glance"
/>

## Build a labelled Input

A Field requires `label` and `default` fills. Put exactly one `CInput`,
`CCombobox`, or custom text-entry primary control in the default fill. Compound
controls may contain their own auxiliary buttons.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cfield/snippets/labelled_input.py"
  title="Build a labelled Input"
/>

```citry-html
<c-CField>
  <c-fill name="label">
    Tidepool name
  </c-fill>
  <c-fill name="default">
    <c-CInput
      name="tidepool_name"
      placeholder="North shelf"
    />
  </c-fill>
  <c-fill name="description">
    Use the name printed on the observation marker.
  </c-fill>
</c-CField>
```

Explicit IDs are optional. Field creates the control, label, description, and
error IDs and passes the control ID to Input.

Compose the same pair in Python:

```python
from citry_ui import CField, CInput

tidepool_field = CField(
    slots={
        "label": "Tidepool name",
        "default": CInput(
            name="tidepool_name",
            placeholder="North shelf",
        ),
        "description": "Use the name printed on the observation marker.",
    },
)
```

Do not nest Field inside Field. Multiple controls would make the visible label,
invalid state, and relationship IDs ambiguous, so Field rejects them.

## Configure Field and Input

Server inputs are passed in Python through `<c-CField ... />`,
`<c-CInput ... />`, `CField(...)`, or `CInput(...)`. Client inputs are passed
in the browser through `$c-props="{...}"`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cfield/snippets/configuration.py"
  title="Configure Field and Input"
/>

A valid client input wins over its server value. Removing it restores the
server value. Invalid client values report one diagnostic per invalid episode
and retain the last valid value or documented fallback.

Field owns `required`, `disabled`, `readonly`, and `invalid` for a control
inside it. Set those inputs on Field, not on the nested Input. This keeps the
label marker, native properties, ARIA relationships, and visible error in one
state. A disabled `CForm` always wins because it uses a native disabled
fieldset.

Standalone Input accepts those state inputs directly. Its client inputs use the
same names through `$c-props`.

## Choose an Input variant

Use `outline` for the clearest boundary, `filled` for a quiet tinted surface,
and `plain` when the surrounding layout already defines the control region.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cfield/snippets/variants.py"
  title="Compare Input variants"
/>

## Set size, spacing, and layout

Input `size` accepts `sm`, `md`, and `lg`. Field `density` changes the space
between label, control, description, and error. Field `orientation` places the
label above or beside the control.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cfield/snippets/sizes_and_layout.py"
  title="Compare Input sizes and Field layout"
/>

The concise `size` input controls visual geometry. HTML's character-width
`size` attribute remains available through Input `attrs`, for example
`attrs={"size": 24}`. Horizontal Fields return to one column at the documented
narrow viewport breakpoint.

## Show Field states

Required adds the native constraint and a visual marker. Read-only keeps the
control focusable and submittable but prevents editing. Disabled removes the
control from focus and form submission. Invalid exposes the error relationship
without changing native constraint validity.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cfield/snippets/field_states.py"
  title="Compare Field states"
/>

Field combines two invalid sources:

- application invalid state from the Field `invalid` input;
- native invalid state after the browser reports a failed constraint.

Correcting a native value clears only the native source. Application code
decides when to clear a server or async error.

## Use native validation and forms

Input supports the text-like native types `text`, `email`, `password`,
`search`, `tel`, and `url`. Pass other native constraints such as `pattern`,
`minlength`, and `maxlength` through `attrs`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cfield/snippets/validation_and_forms.py"
  title="Use native validation and forms"
/>

`invalid=True` controls presentation and accessibility. It does not call
`setCustomValidity()` or make `checkValidity()` fail. Native submit, Enter
submission, reset, and `FormData` keep browser semantics.

`name` is optional. An enabled Input with a non-empty name contributes a form
entry; an unnamed Input works for client-only search and filtering without
submitting data.

Inside `CForm`, Input cannot redirect its native `form` attribute to a different
owner. A standalone Input may use a static external form ID through `attrs`.

## Control the browser value

Server `value` sets the initial and reset value. With no client `value`, the
browser owns later edits. Supplying a client string controls the current value.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cfield/snippets/controlled_values.py"
  title="Compare controlled and uncontrolled values"
/>

```citry-html
<c-CInput
  type="search"
  $c-props="{ value: query }"
  @input="query = $event.target.value"
/>
```

Use the native `input` event to update the supplied value. Removing the client
value preserves the current text and releases control to the browser. A
non-string or `null` client value is invalid and preserves the previous valid
ownership and value. Input defers restoration during IME composition.

## Use native text input types

Native types preserve mobile keyboard hints, autocomplete, password managers,
and type-specific validation. `autocomplete`, `inputmode`, and `placeholder`
have direct server inputs; less common native hints pass through `attrs`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cfield/snippets/native_input_types.py"
  title="Use native Input types"
/>

Placeholder text is never a substitute for an accessible name. A standalone
Input needs an external `<label>`, `aria-label`, or valid `aria-labelledby`.

## Render a custom control

The default slot receives `control_attrs`, which contains Field's generated ID,
server state, ARIA relationships, and private primary-control marker. Spread it
onto exactly one labelable control that should receive the Field label.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cfield/snippets/custom_control.py"
  title="Connect a custom control"
/>

```citry-html
<c-CField required>
  <c-fill name="label">
    Shore observation
  </c-fill>
  <c-fill
    name="default"
    data="{ control_attrs }"
  >
    <textarea c-bind="control_attrs"></textarea>
  </c-fill>
</c-CField>
```

This contract establishes server relationships. A custom control does not
automatically consume later reactive Field or Form state, register with
`CForm`, or report native invalidity. Use `CInput` or another Citry UI control
when those browser behaviors are required.

## Support long content and text direction

Field uses logical properties. Labels, descriptions, errors, placeholders,
and values support long translated text, LTR, RTL, narrow viewports, and zoom.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cfield/snippets/direction_and_content.py"
  title="Use long content and text direction"
/>

## Theme and customize Field and Input

Field and Input follow the surrounding `color-scheme`. Set documented
`--cui-field-*` and `--cui-input-*` variables on an ancestor or component root.
Use public `data-citry-ui-part` selectors for targeted element styling.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cfield/snippets/theme_customization.py"
  title="Theme Field and Input"
/>

```css
.moonlit-survey {
  --cui-field-label-color: #cffafe;
  --cui-field-error-color: #fda4af;
  --cui-input-background: #0f172a;
  --cui-input-foreground: #e2e8f0;
  --cui-input-focus-color: #22d3ee;
  --cui-input-placeholder-color: #94a3b8;

  color-scheme: dark;
}
```

Documented variables, selectors, and reflected attributes are public CSS API.
`.cui-*` classes, `--_cui-*` variables, context keys, and behavior markers are
private.

## Accessibility, events, and methods

Field renders one visible native label. Description and active error IDs merge
with consumer-authored relationships without duplicates. The error region
stays mounted as a polite live region. The required marker is hidden from
assistive technology.

Input adds no component callback or custom DOM event. Listen to native `input`,
`change`, `invalid`, `focus`, `blur`, and composition events with Alpine. The
native root exposes `focus()`, `blur()`, `select()`, selection-range methods,
`checkValidity()`, `reportValidity()`, and `setCustomValidity()` directly.

Focus-visible and forced-colors treatments remain visible. Final
`aria-errormessage`, description fallback, and live-region announcement order
is being verified across VoiceOver/Safari, NVDA/Firefox, and Chromium screen
readers before the v1 accessibility relationship is frozen.
