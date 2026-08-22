---
title: Field and Input
url: https://citry.dev/v/0.4.3/ui-library/components/field-input/
description: "Build labelled native text controls with Citry UI Field and Input."
---
# Field and Input

Use `CField` to connect one visible label, one control, instructions, and an
error message. Use `CInput` for a styled native text input. The pair generates
stable IDs and keeps required, disabled, read-only, and invalid state aligned.

## Field and Input at a glance

The Input remains a native `<input>`. Browser editing, forms, validation,
selection, autocomplete, reset, and events continue to work normally.


### Field and Input at a glance

[Open the rendered preview](/v/0.4.3/ui-library/components/field-input/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FieldInputAtAGlance(Component):
    template = """
      <section class="shore-glance">
        <article class="shore-glance__card">
          <header>
            <p>Morning survey</p>
            <h2>Log a tidepool sighting</h2>
          </header>

          <c-CField required>
            <c-fill name="label">
              Species
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="species"
                value="Ochre sea star"
                autocomplete="off"
              />
            </c-fill>
            <c-fill name="description">
              Use the common name from the shore guide.
            </c-fill>
          </c-CField>
        </article>

        <article class="shore-glance__card">
          <header>
            <p>Tide alert</p>
            <h2>Check the observation code</h2>
          </header>

          <c-CField invalid>
            <c-fill name="label">
              Observation code
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="observation_code"
                value="LOW-7"
                variant="filled"
              />
            </c-fill>
            <c-fill name="error">
              Codes contain three letters and three digits.
            </c-fill>
          </c-CField>
        </article>
      </section>
    """

    css = """
      :where(.shore-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        max-width: 62rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.shore-glance__card) {
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.shore-glance__card header) {
        margin-block-end: 1rem;
      }

      :where(.shore-glance__card h2, .shore-glance__card p) {
        margin-block: 0;
      }

      :where(.shore-glance__card header p) {
        margin-block-end: 0.35rem;
        color: light-dark(#08758a, #69d4e8);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }
    """


preview = FieldInputAtAGlance()

preview  # noqa: B018
````


## Build a labelled Input

A Field requires `label` and `default` fills. Put exactly one `CInput`,
`CCombobox`, or custom text-entry primary control in the default fill. Compound
controls may contain their own auxiliary buttons.


### Build a labelled Input

[Open the rendered preview](/v/0.4.3/ui-library/components/field-input/_previews/labelled-input/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class LabelledInput(Component):
    template = """
      <section class="shore-example">
        <c-CField>
          <c-fill name="label">
            Tidepool name
          </c-fill>
          <c-fill name="default">
            <c-CInput
              name="tidepool_name"
              placeholder="North shelf"
              autocomplete="off"
            />
          </c-fill>
          <c-fill name="description">
            Use the name printed on the observation marker.
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.shore-example) {
        max-width: 34rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = LabelledInput()

preview  # noqa: B018
````



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


### Configure Field and Input

[Open the rendered preview](/v/0.4.3/ui-library/components/field-input/_previews/configuration/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FieldInputConfiguration(Component):
    template = """
      <section
        class="shore-configurator"
        x-data
        x-init="Alpine.store('shoreFieldConfig', {
          orientation: 'vertical',
          density: 'default',
          variant: 'outline',
          size: 'md',
          required: true,
          disabled: false,
          readonly: false,
          invalid: false,
        })"
        @citry-ui-preview-controls.window="Object.assign($store.shoreFieldConfig, $event.detail)"
      >
        <header>
          <p>Survey setup</p>
          <h2>Configure the observation field</h2>
        </header>

        <c-CField
          $c-props="{
            orientation: $store.shoreFieldConfig.orientation,
            density: $store.shoreFieldConfig.density,
            required: $store.shoreFieldConfig.required,
            disabled: $store.shoreFieldConfig.disabled,
            readonly: $store.shoreFieldConfig.readonly,
            invalid: $store.shoreFieldConfig.invalid,
          }"
        >
          <c-fill name="label">
            Shore condition
          </c-fill>
          <c-fill name="default">
            <c-CInput
              name="condition"
              value="Calm pools"
              $c-props="{
                variant: $store.shoreFieldConfig.variant,
                size: $store.shoreFieldConfig.size,
              }"
            />
          </c-fill>
          <c-fill name="description">
            Record the water state at the start of the survey.
          </c-fill>
          <c-fill name="error">
            Add the current shore condition.
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.shore-configurator) {
        max-width: 58rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.shore-configurator header) {
        margin-block-end: 1rem;
      }

      :where(.shore-configurator h2, .shore-configurator p) {
        margin-block: 0;
      }

      :where(.shore-configurator header p) {
        margin-block-end: 0.35rem;
        color: light-dark(#08758a, #69d4e8);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }
    """


preview_controls = (
    {
        "name": "orientation",
        "label": "Orientation",
        "type": "select",
        "default": "vertical",
        "options": (("vertical", "Vertical"), ("horizontal", "Horizontal")),
    },
    {
        "name": "density",
        "label": "Field density",
        "type": "select",
        "default": "default",
        "options": (("default", "Default"), ("comfortable", "Comfortable"), ("compact", "Compact")),
    },
    {
        "name": "variant",
        "label": "Input variant",
        "type": "select",
        "default": "outline",
        "options": (("outline", "Outline"), ("filled", "Filled"), ("plain", "Plain")),
    },
    {
        "name": "size",
        "label": "Input size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {"name": "required", "label": "Required", "type": "checkbox", "default": True},
    {"name": "disabled", "label": "Disabled", "type": "checkbox", "default": False},
    {"name": "readonly", "label": "Read-only", "type": "checkbox", "default": False},
    {"name": "invalid", "label": "Invalid", "type": "checkbox", "default": False},
)

preview = FieldInputConfiguration()

preview  # noqa: B018
````


A valid client input wins over its server value. Removing it restores the
server value. Invalid client values report one diagnostic per invalid episode
and retain the last valid value or documented fallback.

Field owns `required`, `disabled`, `readonly`, and `invalid` for a control
inside it. Set those inputs on Field, not on the nested Input. This keeps the
label marker, native properties, ARIA relationships, and visible error in one
state. Required and read-only each require a control that supports that state.
An unsupported server value raises; an unsupported browser value resolves to
`false` and reports once. A disabled `CForm` always wins because it uses a native disabled
fieldset.

Standalone Input accepts those state inputs directly. Its client inputs use the
same names through `$c-props`.

## Choose an Input variant

Use `outline` for the clearest boundary, `filled` for a quiet tinted surface,
and `plain` when the surrounding layout already defines the control region.


### Compare Input variants

[Open the rendered preview](/v/0.4.3/ui-library/components/field-input/_previews/variants/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InputVariants(Component):
    template = """
      <section class="shore-grid">
        <c-CField>
          <c-fill name="label">
            Outline
          </c-fill>
          <c-fill name="default">
            <c-CInput name="outline" value="Rocky shelf" variant="outline" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">
            Filled
          </c-fill>
          <c-fill name="default">
            <c-CInput name="filled" value="Kelp channel" variant="filled" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">
            Plain
          </c-fill>
          <c-fill name="default">
            <c-CInput name="plain" value="Sand basin" variant="plain" />
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.shore-grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 1rem;
        max-width: 62rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = InputVariants()

preview  # noqa: B018
````


## Set size, spacing, and layout

Input `size` accepts `sm`, `md`, and `lg`. Field `density` changes the space
between label, control, description, and error. Field `orientation` places the
label above or beside the control.


### Compare Input sizes and Field layout

[Open the rendered preview](/v/0.4.3/ui-library/components/field-input/_previews/sizes-and-layout/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InputSizesAndLayout(Component):
    template = """
      <section class="shore-layout">
        <c-CField density="compact">
          <c-fill name="label">
            Small marker code
          </c-fill>
          <c-fill name="default">
            <c-CInput name="small" value="A-14" size="sm" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">
            Medium marker code
          </c-fill>
          <c-fill name="default">
            <c-CInput name="medium" value="B-27" size="md" />
          </c-fill>
        </c-CField>
        <c-CField density="comfortable">
          <c-fill name="label">
            Large marker code
          </c-fill>
          <c-fill name="default">
            <c-CInput name="large" value="C-08" size="lg" />
          </c-fill>
        </c-CField>
        <c-CField orientation="horizontal">
          <c-fill name="label">
            Long observation label
          </c-fill>
          <c-fill name="default">
            <c-CInput name="long" placeholder="Describe the waterline" />
          </c-fill>
          <c-fill name="description">
            Horizontal Fields return to one column on narrow viewports.
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.shore-layout) {
        display: grid;
        gap: 1.25rem;
        max-width: 58rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = InputSizesAndLayout()

preview  # noqa: B018
````


The concise `size` input controls visual geometry. HTML's character-width
`size` attribute remains available through Input `attrs`, for example
`attrs={"size": 24}`. Horizontal Fields return to one column at the documented
narrow viewport breakpoint.

## Show Field states

Required adds the native constraint and a visual marker. Read-only keeps the
control focusable and submittable but prevents editing. Disabled removes the
control from focus and form submission. Invalid exposes the error relationship
without changing native constraint validity.


### Compare Field states

[Open the rendered preview](/v/0.4.3/ui-library/components/field-input/_previews/field-states/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FieldStates(Component):
    template = """
      <section class="shore-states">
        <c-CField required>
          <c-fill name="label">
            Required site
          </c-fill>
          <c-fill name="default">
            <c-CInput name="site" placeholder="Choose a survey site" />
          </c-fill>
        </c-CField>
        <c-CField readonly>
          <c-fill name="label">
            Read-only permit
          </c-fill>
          <c-fill name="default">
            <c-CInput name="permit" value="SHORE-204" />
          </c-fill>
        </c-CField>
        <c-CField disabled>
          <c-fill name="label">
            Disabled trail
          </c-fill>
          <c-fill name="default">
            <c-CInput name="trail" value="Cliff descent" />
          </c-fill>
        </c-CField>
        <c-CField invalid>
          <c-fill name="label">
            Invalid tide code
          </c-fill>
          <c-fill name="default">
            <c-CInput name="tide_code" value="LOW" />
          </c-fill>
          <c-fill name="error">
            Add the hour after the tide code.
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.shore-states) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1.25rem;
        max-width: 62rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = FieldStates()

preview  # noqa: B018
````


Field combines two invalid sources:

- application invalid state from the Field `invalid` input;
- native invalid state after the browser reports a failed constraint.

Correcting a native value clears only the native source. Application code
decides when to clear a server or async error.

## Use native validation and forms

Input supports the text-like native types `text`, `email`, `password`,
`search`, `tel`, and `url`. Pass other native constraints such as `pattern`,
`minlength`, and `maxlength` through `attrs`.


### Use native validation and forms

[Open the rendered preview](/v/0.4.3/ui-library/components/field-input/_previews/validation-and-forms/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ValidationAndForms(Component):
    template = """
      <section
        class="shore-form-card"
        x-data
        x-init="Alpine.store('shoreValidation', {
          submitted: '',
          serverInvalid: true,
        })"
      >
        <header>
          <p>Tide alert</p>
          <h2>Register a survey contact</h2>
        </header>

        <c-CForm
          @submit.prevent="$store.shoreValidation.submitted = new FormData($el).get('email')"
          @reset="
            $store.shoreValidation.submitted = '';
            $store.shoreValidation.serverInvalid = false;
          "
        >
          <c-CField required>
            <c-fill name="label">
              Observer email
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="email"
                type="email"
                autocomplete="email"
                placeholder="observer@example.com"
              />
            </c-fill>
            <c-fill name="description">
              Native email validation runs before submission.
            </c-fill>
          </c-CField>

          <c-CField $c-props="{ invalid: $store.shoreValidation.serverInvalid }">
            <c-fill name="label">
              Permit code
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="permit"
                value="OLD-14"
                @input="$store.shoreValidation.serverInvalid = false"
              />
            </c-fill>
            <c-fill name="error">
              This permit expired at the previous tide cycle.
            </c-fill>
          </c-CField>

          <div class="shore-form-card__actions">
            <button type="submit">Register observer</button>
            <button type="reset">Reset</button>
          </div>
        </c-CForm>

        <p aria-live="polite" x-show="$store.shoreValidation.submitted">
          Registered <strong x-text="$store.shoreValidation.submitted"></strong>
        </p>
      </section>
    """

    css = """
      :where(.shore-form-card) {
        max-width: 38rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.shore-form-card header) {
        margin-block-end: 1rem;
      }

      :where(.shore-form-card h2, .shore-form-card p) {
        margin-block: 0;
      }

      :where(.shore-form-card header p) {
        color: light-dark(#08758a, #69d4e8);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.shore-form-card__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.shore-form-card__actions button) {
        min-height: 2.5rem;
        padding-inline: 0.875rem;
      }
    """


preview = ValidationAndForms()

preview  # noqa: B018
````


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


### Compare controlled and uncontrolled values

[Open the rendered preview](/v/0.4.3/ui-library/components/field-input/_previews/controlled-values/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledValues(Component):
    template = """
      <section
        class="shore-values"
        x-data
        x-init="Alpine.store('shoreValues', {
          controlled: true,
          value: 'Ochre sea star',
        })"
      >
        <c-CField>
          <c-fill name="label">
            Browser-owned note
          </c-fill>
          <c-fill name="default">
            <c-CInput name="uncontrolled" value="Calm water" />
          </c-fill>
          <c-fill name="description">
            Edit freely, then use native reset.
          </c-fill>
        </c-CField>

        <c-CField>
          <c-fill name="label">
            Application-owned species
          </c-fill>
          <c-fill name="default">
            <c-CInput
              name="controlled"
              $c-props="{
                value: $store.shoreValues.controlled
                  ? $store.shoreValues.value
                  : undefined,
              }"
              @input="$store.shoreValues.value = $event.target.value"
            />
          </c-fill>
          <c-fill name="description">
            The native input event updates the supplied value.
          </c-fill>
        </c-CField>

        <div class="shore-values__actions">
          <button
            type="button"
            @click="$store.shoreValues.controlled = false"
          >
            Release control
          </button>
          <button
            type="button"
            @click="
              $store.shoreValues.value = 'Giant green anemone';
              $store.shoreValues.controlled = true;
            "
          >
            Set controlled value
          </button>
        </div>
      </section>
    """

    css = """
      :where(.shore-values) {
        display: grid;
        gap: 1.25rem;
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.shore-values__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.shore-values__actions button) {
        min-height: 2.5rem;
      }
    """


preview = ControlledValues()

preview  # noqa: B018
````



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


### Use native Input types

[Open the rendered preview](/v/0.4.3/ui-library/components/field-input/_previews/native-input-types/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NativeInputTypes(Component):
    template = """
      <section class="shore-native-grid">
        <c-CField>
          <c-fill name="label">
            Observer email
          </c-fill>
          <c-fill name="default">
            <c-CInput name="email" type="email" autocomplete="email" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">
            Ranger telephone
          </c-fill>
          <c-fill name="default">
            <c-CInput name="telephone" type="tel" inputmode="tel" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">
            Field guide URL
          </c-fill>
          <c-fill name="default">
            <c-CInput name="guide" type="url" inputmode="url" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">
            Survey passphrase
          </c-fill>
          <c-fill name="default">
            <c-CInput name="passphrase" type="password" autocomplete="current-password" />
          </c-fill>
        </c-CField>
        <label class="shore-native-grid__standalone">
          Filter observations
          <c-CInput
            type="search"
            placeholder="Search species"
            c-attrs="{'aria-label': 'Filter observations'}"
          />
        </label>
      </section>
    """

    css = """
      :where(.shore-native-grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1.25rem;
        max-width: 62rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.shore-native-grid__standalone) {
        display: grid;
        gap: 0.5rem;
        font-weight: 600;
      }
    """


preview = NativeInputTypes()

preview  # noqa: B018
````


Placeholder text is never a substitute for an accessible name. A standalone
Input needs an external `<label>`, `aria-label`, or valid `aria-labelledby`.

## Render a custom control

The default slot receives `control_attrs`, which contains Field's generated ID,
server state, ARIA relationships, and private primary-control marker. Spread it
onto exactly one labelable control that should receive the Field label.


### Connect a custom control

[Open the rendered preview](/v/0.4.3/ui-library/components/field-input/_previews/custom-control/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomFieldControl(Component):
    template = """
      <section class="shore-custom-control">
        <c-CField required>
          <c-fill name="label">
            Shore observation
          </c-fill>
          <c-fill
            name="default"
            data="{ control_attrs }"
          >
            <textarea
              rows="5"
              placeholder="Describe the pool, weather, and visible species"
              c-bind="control_attrs"
            ></textarea>
          </c-fill>
          <c-fill name="description">
            The textarea receives Field IDs and server state from slot data.
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.shore-custom-control) {
        max-width: 40rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.shore-custom-control textarea) {
        box-sizing: border-box;
        inline-size: 100%;
        padding: 0.75rem;
        border: 1px solid color-mix(in srgb, CanvasText 38%, transparent);
        border-radius: 0.5rem;
        background: Canvas;
        color: CanvasText;
        font: inherit;
        resize: vertical;
      }
    """


preview = CustomFieldControl()

preview  # noqa: B018
````



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


### Use long content and text direction

[Open the rendered preview](/v/0.4.3/ui-library/components/field-input/_previews/direction-and-content/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DirectionAndContent(Component):
    template = """
      <section class="shore-direction-grid">
        <article dir="ltr">
          <c-CField orientation="horizontal" invalid>
            <c-fill name="label">
              Detailed shoreline observation recorded during the lowest tide
            </c-fill>
            <c-fill name="default">
              <c-CInput name="english_note" value="Waves reaching the upper marker" />
            </c-fill>
            <c-fill name="error">
              Add whether the water crossed the protected nesting area.
            </c-fill>
          </c-CField>
        </article>

        <article dir="rtl" lang="ar">
          <c-CField orientation="horizontal">
            <c-fill name="label">
              ملاحظة مفصلة عن الشاطئ أثناء أدنى مستوى للمد
            </c-fill>
            <c-fill name="default">
              <c-CInput name="arabic_note" value="المياه هادئة حول الصخور" />
            </c-fill>
            <c-fill name="description">
              اذكر الأنواع التي ظهرت قرب خط الماء.
            </c-fill>
          </c-CField>
        </article>
      </section>
    """

    css = """
      :where(.shore-direction-grid) {
        display: grid;
        gap: 1.5rem;
        max-width: 62rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.shore-direction-grid article) {
        min-width: 0;
      }
    """


preview = DirectionAndContent()

preview  # noqa: B018
````


## Theme and customize Field and Input

Field and Input follow the surrounding `color-scheme`. Set documented
`--cui-field-*` and `--cui-input-*` variables on an ancestor or component root.
Use public `data-citry-ui-part` selectors for targeted element styling.


### Theme Field and Input

[Open the rendered preview](/v/0.4.3/ui-library/components/field-input/_previews/theme-customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FieldThemeCustomization(Component):
    template = """
      <section class="shore-themes">
        <article class="shore-theme shore-theme--sunlit">
          <p>Sunlit survey</p>
          <c-CField required>
            <c-fill name="label">
              Water clarity
            </c-fill>
            <c-fill name="default">
              <c-CInput name="day_clarity" value="Clear" />
            </c-fill>
          </c-CField>
        </article>

        <article class="shore-theme shore-theme--moonlit">
          <p>Moonlit survey</p>
          <c-CField invalid>
            <c-fill name="label">
              Lantern marker
            </c-fill>
            <c-fill name="default">
              <c-CInput name="night_marker" value="Missing" variant="filled" />
            </c-fill>
            <c-fill name="error">
              Mark the nearest visible lantern.
            </c-fill>
          </c-CField>
        </article>
      </section>
    """

    css = """
      :where(.shore-themes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 62rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.shore-theme) {
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid var(--shore-border);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
      }

      :where(.shore-theme > p) {
        margin-block: 0 1rem;
        color: var(--shore-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.shore-theme--sunlit) {
        --shore-border: #91c7d2;
        --shore-accent: #086b7d;
        --cui-field-label-color: #164e63;
        --cui-input-focus-color: #0891b2;
        --cui-input-radius: 0.8rem;

        color-scheme: light;
      }

      :where(.shore-theme--moonlit) {
        --shore-border: #475569;
        --shore-accent: #67e8f9;
        --cui-field-label-color: #cffafe;
        --cui-field-error-color: #fda4af;
        --cui-input-background: #0f172a;
        --cui-input-foreground: #e2e8f0;
        --cui-input-border-color: #64748b;
        --cui-input-focus-color: #22d3ee;
        --cui-input-placeholder-color: #94a3b8;

        color-scheme: dark;
      }

      :where(.shore-theme [data-citry-ui-part="description"]) {
        max-inline-size: 38ch;
      }
    """


preview = FieldThemeCustomization()

preview  # noqa: B018
````



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

## API reference

### Inputs

#### CField server inputs

Server inputs are passed in a template through `<c-CField ... />` or in Python through
`CField(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 8rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="field-input-input-cfield-server-inputs-control-id"></span>`control_id` | `str | None` | generated | Sets the control ID and related label, description, and error IDs. |
| <span id="field-input-input-cfield-server-inputs-required"></span>`required` | `bool` | `False` | Supplies required state to a supporting control; an unsupported true value raises after server control registration. |
| <span id="field-input-input-cfield-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Sets local disabled state; an enclosing disabled `CForm` always wins. |
| <span id="field-input-input-cfield-server-inputs-readonly"></span>`readonly` | `bool | None` | Inherits `CForm`. | Supplies read-only state to a supporting control; an unsupported true value raises after server control registration. |
| <span id="field-input-input-cfield-server-inputs-invalid"></span>`invalid` | `bool` | `False` | Supplies application-owned invalid state. |
| <span id="field-input-input-cfield-server-inputs-orientation"></span>`orientation` | `"vertical" | "horizontal"` ([`CFieldOrientation`](#field-input-interface-input-type-aliases-cfield-orientation)) | `"vertical"` | Selects label and control layout. |
| <span id="field-input-input-cfield-server-inputs-density"></span>`density` | `"default" | "comfortable" | "compact"` ([`CFieldDensity`](#field-input-interface-input-type-aliases-cfield-density)) | `"default"` | Selects spacing. |
| <span id="field-input-input-cfield-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#field-input-interface-input-type-aliases-class-value)) | `None` | Adds Field-root classes from a string, conditional mapping, or nested sequence and merges them with `attrs`. |
| <span id="field-input-input-cfield-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#field-input-interface-input-type-aliases-style-value)) | `None` | Adds Field-root inline styles from CSS text, a property mapping, or a nested sequence and merges them with `attrs`. |
| <span id="field-input-input-cfield-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed attributes to the Field root; prefer the top-level inputs for class and style. |

</div>

#### CField client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CField />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="field-input-input-cfield-client-inputs-required"></span>`required` | `boolean` | Uses the server input. | Controls required state for supporting controls; an unsupported true value resolves to false and reports once. |
| <span id="field-input-input-cfield-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls local disabled state; an enclosing disabled `CForm` always wins. |
| <span id="field-input-input-cfield-client-inputs-readonly"></span>`readonly` | `boolean` | Uses the server input or reactive Form value. | Controls read-only state for supporting controls; an unsupported true value resolves to false and reports once. |
| <span id="field-input-input-cfield-client-inputs-invalid"></span>`invalid` | `boolean` | Uses the server input. | Controls application invalid state; native invalid state still combines with it. |
| <span id="field-input-input-cfield-client-inputs-orientation"></span>`orientation` | `"vertical" | "horizontal"` ([`CFieldOrientation`](#field-input-interface-input-type-aliases-cfield-orientation)) | Uses the server input. | Controls label and control layout. |
| <span id="field-input-input-cfield-client-inputs-density"></span>`density` | `"default" | "comfortable" | "compact"` ([`CFieldDensity`](#field-input-interface-input-type-aliases-cfield-density)) | Uses the server input. | Controls spacing. |

</div>

#### CInput server inputs

Server inputs are passed in a template through `<c-CInput ... />` or in Python through
`CInput(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 9rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="field-input-input-cinput-server-inputs-name"></span>`name` | `non-empty str | None` | `None` | Sets the native submitted name; an unnamed Input contributes no `FormData` entry. |
| <span id="field-input-input-cinput-server-inputs-type"></span>`type` | `"text" | "email" | "password" | "search" | "tel" | "url"` ([`CInputType`](#field-input-interface-input-type-aliases-cinput-type)) | `"text"` | Sets the native input type. |
| <span id="field-input-input-cinput-server-inputs-id"></span>`id` | `str | None` | generated | Uses the Field control ID when composed, otherwise sets or generates native identity. |
| <span id="field-input-input-cinput-server-inputs-value"></span>`value` | `str | None` | `None` | Sets the server initial and default value. |
| <span id="field-input-input-cinput-server-inputs-required"></span>`required` | `bool | None` | `None` | Sets native required state when standalone; omit it inside `CField`, which owns the state. |
| <span id="field-input-input-cinput-server-inputs-disabled"></span>`disabled` | `bool | None` | `None` | Sets local native disabled state when standalone; omit it inside `CField`, and note that disabled `CForm` always wins. |
| <span id="field-input-input-cinput-server-inputs-readonly"></span>`readonly` | `bool | None` | Inherits `CForm` when standalone. | Sets native read-only state when standalone; omit it inside `CField`. |
| <span id="field-input-input-cinput-server-inputs-invalid"></span>`invalid` | `bool | None` | `None` | Sets application invalid state when standalone; omit it inside `CField`. |
| <span id="field-input-input-cinput-server-inputs-autocomplete"></span>`autocomplete` | `str | None` | `None` | Sets the native autocomplete hint. |
| <span id="field-input-input-cinput-server-inputs-inputmode"></span>`inputmode` | `str | None` | `None` | Sets the virtual keyboard hint. |
| <span id="field-input-input-cinput-server-inputs-placeholder"></span>`placeholder` | `str | None` | `None` | Sets placeholder text; do not use it instead of a label. |
| <span id="field-input-input-cinput-server-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CInputVariant`](#field-input-interface-input-type-aliases-cinput-variant)) | `"outline"` | Selects presentation. |
| <span id="field-input-input-cinput-server-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CInputSize`](#field-input-interface-input-type-aliases-cinput-size)) | `"md"` | Selects visual height, padding, and text size; use `attrs["size"]` for native character width. |
| <span id="field-input-input-cinput-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#field-input-interface-input-type-aliases-class-value)) | `None` | Adds native Input classes from a string, conditional mapping, or nested sequence and merges them with `attrs`. |
| <span id="field-input-input-cinput-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#field-input-interface-input-type-aliases-style-value)) | `None` | Adds native Input inline styles from CSS text, a property mapping, or a nested sequence and merges them with `attrs`. |
| <span id="field-input-input-cinput-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed native constraints, ARIA, Alpine, and data attributes; prefer the top-level inputs for class and style. |

</div>

#### CInput client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CInput />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 12rem; --ui-api-column-3-width: 12rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="field-input-input-cinput-client-inputs-value"></span>`value` | `string` | Continues uncontrolled from the current value. | Controls the native value while supplied. |
| <span id="field-input-input-cinput-client-inputs-required"></span>`required` | `boolean` | Uses the server value. | Controls native required state only when standalone; `CField` owns it when composed. |
| <span id="field-input-input-cinput-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server value. | Controls local disabled state only when standalone; disabled `CForm` always wins and `CField` owns it when composed. |
| <span id="field-input-input-cinput-client-inputs-readonly"></span>`readonly` | `boolean` | Uses the server or reactive Form value. | Controls native read-only state only when standalone; `CField` owns it when composed. |
| <span id="field-input-input-cinput-client-inputs-invalid"></span>`invalid` | `boolean` | Uses the server value. | Controls application invalid state only when standalone; `CField` owns it when composed. |
| <span id="field-input-input-cinput-client-inputs-variant"></span>`variant` | `"outline" | "filled" | "plain"` ([`CInputVariant`](#field-input-interface-input-type-aliases-cinput-variant)) | Uses the server input. | Controls presentation. |
| <span id="field-input-input-cinput-client-inputs-size"></span>`size` | `"sm" | "md" | "lg"` ([`CInputSize`](#field-input-interface-input-type-aliases-cinput-size)) | Uses the server input. | Controls geometry. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CField slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="field-input-slot-cfield-slots-label"></span>`label` | yes | `{}` ([`CFieldLabelSlotData`](#field-input-interface-cfield-label-slot-data)) | none |
| <span id="field-input-slot-cfield-slots-default"></span>`default` | yes | `{control_attrs: dict[str, object], control_id: str, label_id: str, description_id: str, error_id: str, is_required: bool, is_disabled: bool, is_readonly: bool, is_invalid: bool}` ([`CFieldDefaultSlotData`](#field-input-interface-cfield-default-slot-data)) | none |
| <span id="field-input-slot-cfield-slots-description"></span>`description` | no | `{}` ([`CFieldDescriptionSlotData`](#field-input-interface-cfield-description-slot-data)) | omitted |
| <span id="field-input-slot-cfield-slots-error"></span>`error` | no | `{}` ([`CFieldErrorSlotData`](#field-input-interface-cfield-error-slot-data)) | Mounted empty live region. |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CField CSS variables

Apply these variables to `CField` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="field-input-css-cfield-css-variables-cui-field-gap"></span>`--cui-field-gap` | `length` | Gap between Field regions. | `0.5rem, density adjusted` |
| <span id="field-input-css-cfield-css-variables-cui-field-label-color"></span>`--cui-field-label-color` | `color` | Label color. | `CanvasText` |
| <span id="field-input-css-cfield-css-variables-cui-field-label-weight"></span>`--cui-field-label-weight` | `number | keyword` | Label font weight. | `600` |
| <span id="field-input-css-cfield-css-variables-cui-field-description-color"></span>`--cui-field-description-color` | `color` | Description color. | `Muted CanvasText mix.` |
| <span id="field-input-css-cfield-css-variables-cui-field-error-color"></span>`--cui-field-error-color` | `color` | Error color. | `Scheme-aware negative color.` |
| <span id="field-input-css-cfield-css-variables-cui-field-required-color"></span>`--cui-field-required-color` | `color` | Required-indicator color. | `Effective Field error color.` |

</div>

#### CInput CSS variables

Apply these variables to `CInput` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="field-input-css-cinput-css-variables-cui-input-background"></span>`--cui-input-background` | `color` | Control background. | `Canvas, variant adjusted` |
| <span id="field-input-css-cinput-css-variables-cui-input-foreground"></span>`--cui-input-foreground` | `color` | Input text. | `CanvasText` |
| <span id="field-input-css-cinput-css-variables-cui-input-border-color"></span>`--cui-input-border-color` | `color` | Resting border. | `Subtle CanvasText mix, variant adjusted` |
| <span id="field-input-css-cinput-css-variables-cui-input-hover-border-color"></span>`--cui-input-hover-border-color` | `color` | Hover border. | `Stronger CanvasText mix.` |
| <span id="field-input-css-cinput-css-variables-cui-input-focus-color"></span>`--cui-input-focus-color` | `color` | Focus outline and border. | `Highlight` |
| <span id="field-input-css-cinput-css-variables-cui-input-invalid-border-color"></span>`--cui-input-invalid-border-color` | `color` | Invalid border. | `Scheme-aware negative color.` |
| <span id="field-input-css-cinput-css-variables-cui-input-disabled-background"></span>`--cui-input-disabled-background` | `color` | Disabled background. | `Subtle CanvasText/Canvas mix.` |
| <span id="field-input-css-cinput-css-variables-cui-input-placeholder-color"></span>`--cui-input-placeholder-color` | `color` | Placeholder text color. | `Muted CanvasText mix.` |
| <span id="field-input-css-cinput-css-variables-cui-input-radius"></span>`--cui-input-radius` | `length` | Corner radius. | `0.5rem; 0 for plain` |
| <span id="field-input-css-cinput-css-variables-cui-input-height"></span>`--cui-input-height` | `length` | Minimum control height. | `Size-derived length.` |
| <span id="field-input-css-cinput-css-variables-cui-input-inline-padding"></span>`--cui-input-inline-padding` | `length` | Logical inline padding. | `Size-derived length.` |
| <span id="field-input-css-cinput-css-variables-cui-input-block-padding"></span>`--cui-input-block-padding` | `length` | Logical block padding. | `Size-derived length.` |
| <span id="field-input-css-cinput-css-variables-cui-input-font-size"></span>`--cui-input-font-size` | `length` | Input text size. | `Size-derived length.` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CField attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="field-input-attribute-cfield-data-required"></span>`data-required` | Field root | `present | absent` | Mirrors effective required state. |
| <span id="field-input-attribute-cfield-data-disabled"></span>`data-disabled` | Field root | `present | absent` | Mirrors effective disabled state. |
| <span id="field-input-attribute-cfield-data-readonly"></span>`data-readonly` | Field root | `present | absent` | Mirrors effective read-only state. |
| <span id="field-input-attribute-cfield-data-invalid"></span>`data-invalid` | Field root | `present | absent` | Mirrors effective invalid state. |
| <span id="field-input-attribute-cfield-data-orientation"></span>`data-orientation` | Field root | `"vertical" | "horizontal"` | Mirrors effective orientation. |
| <span id="field-input-attribute-cfield-data-density"></span>`data-density` | Field root | `"default" | "comfortable" | "compact"` | Mirrors effective density. |

</div>

#### CInput attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="field-input-attribute-cinput-data-required"></span>`data-required` | Native Input | `present | absent` | Mirrors effective required state. |
| <span id="field-input-attribute-cinput-data-disabled"></span>`data-disabled` | Native Input | `present | absent` | Mirrors effective disabled state. |
| <span id="field-input-attribute-cinput-data-readonly"></span>`data-readonly` | Native Input | `present | absent` | Mirrors effective read-only state. |
| <span id="field-input-attribute-cinput-data-invalid"></span>`data-invalid` | Native Input | `present | absent` | Mirrors combined application and native invalid state. |
| <span id="field-input-attribute-cinput-data-variant"></span>`data-variant` | Native Input | `"outline" | "filled" | "plain"` | Mirrors effective presentation variant. |
| <span id="field-input-attribute-cinput-data-size"></span>`data-size` | Native Input | `"sm" | "md" | "lg"` | Mirrors effective visual size. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CField selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="field-input-selector-cfield-field"></span>`[data-citry-ui-part="field"]` | Field root | Root and `attrs` destination. |
| <span id="field-input-selector-cfield-label"></span>`[data-citry-ui-part="label"]` | Native label | Generated relationship owner. |
| <span id="field-input-selector-cfield-required-indicator"></span>`[data-citry-ui-part="required-indicator"]` | Required marker | Visual required-state hook. |
| <span id="field-input-selector-cfield-control"></span>`[data-citry-ui-part="control"]` | Control wrapper | Control-slot hook. |
| <span id="field-input-selector-cfield-description"></span>`[data-citry-ui-part="description"]` | Description region | Optional description hook. |
| <span id="field-input-selector-cfield-error"></span>`[data-citry-ui-part="error"]` | Error region | Stable validation-message live region. |

</div>

#### CInput selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="field-input-selector-cinput-input"></span>`[data-citry-ui-part="input"]` | Native Input | Root and `attrs` destination. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="field-input-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="field-input-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="field-input-interface-input-type-aliases-cfield-orientation"></span>`CFieldOrientation` | `Literal["vertical", "horizontal"]` |
| <span id="field-input-interface-input-type-aliases-cfield-density"></span>`CFieldDensity` | `Literal["default", "comfortable", "compact"]` |
| <span id="field-input-interface-input-type-aliases-cinput-type"></span>`CInputType` | `Literal["text", "email", "password", "search", "tel", "url"]` |
| <span id="field-input-interface-input-type-aliases-cinput-variant"></span>`CInputVariant` | `Literal["outline", "filled", "plain"]` |
| <span id="field-input-interface-input-type-aliases-cinput-size"></span>`CInputSize` | `Literal["sm", "md", "lg"]` |

</div>

<span id="field-input-interface-cfield-default-slot-data"></span>

#### `CFieldDefaultSlotData`

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 8rem">

| Field | Type | Default | Meaning |
|---|---|---|---|
| <span id="field-input-interface-cfield-default-slot-data-control-attrs"></span>`control_attrs` | `dict[str, object]` | - | Attributes for the slotted native control. |
| <span id="field-input-interface-cfield-default-slot-data-control-id"></span>`control_id` | `str` | - | Generated or supplied control ID. |
| <span id="field-input-interface-cfield-default-slot-data-label-id"></span>`label_id` | `str` | - | Generated label ID. |
| <span id="field-input-interface-cfield-default-slot-data-description-id"></span>`description_id` | `str` | - | Generated description ID. |
| <span id="field-input-interface-cfield-default-slot-data-error-id"></span>`error_id` | `str` | - | Generated error-region ID. |
| <span id="field-input-interface-cfield-default-slot-data-is-required"></span>`is_required` | `bool` | - | Effective server required state. |
| <span id="field-input-interface-cfield-default-slot-data-is-disabled"></span>`is_disabled` | `bool` | - | Effective server disabled state. |
| <span id="field-input-interface-cfield-default-slot-data-is-readonly"></span>`is_readonly` | `bool` | - | Effective server read-only state. |
| <span id="field-input-interface-cfield-default-slot-data-is-invalid"></span>`is_invalid` | `bool` | - | Effective server invalid state. |

</div>

<span id="field-input-interface-cfield-label-slot-data"></span>

#### `CFieldLabelSlotData`

Empty dataclass: `{}`.

<span id="field-input-interface-cfield-description-slot-data"></span>

#### `CFieldDescriptionSlotData`

Empty dataclass: `{}`.

<span id="field-input-interface-cfield-error-slot-data"></span>

#### `CFieldErrorSlotData`

Empty dataclass: `{}`.

### Translation keys

-