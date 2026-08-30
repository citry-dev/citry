---
title: Form
url: https://citry.dev/v/0.4.6/ui-library/components/form/
description: "Compose native submission, validation, reset, and shared control state with Citry UI Form."
---
# Form

Use `CForm` for native submission, validation, reset, and `FormData`. It renders
one `<form>` and an internal `<fieldset>`, shares disabled and read-only defaults
with supporting Citry UI controls, and can guard duplicate submits without
removing successful controls from the payload.

## Form at a glance

The Form owns coordination and layout. Field, Input, and Button keep their own
visual treatment.


### Form at a glance

[Open the rendered preview](/v/0.4.6/ui-library/components/form/_previews/at-a-glance/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormAtAGlance(Component):
    template = """
      <section class="form-glance">
        <article class="form-glance__card">
          <header>
            <p>Night observation</p>
            <h2>Reserve telescope time</h2>
          </header>

          <c-CForm @submit.prevent="void 0">
            <c-CField required>
              <c-fill name="label">
                Target name
              </c-fill>
              <c-fill name="default">
                <c-CInput
                  name="target"
                  value="Andromeda Galaxy"
                />
              </c-fill>
              <c-fill name="description">
                Use a catalog or common name.
              </c-fill>
            </c-CField>
            <c-CButton type="submit">
              Request a window
            </c-CButton>
          </c-CForm>
        </article>

        <article class="form-glance__card">
          <header>
            <p>Calibration queue</p>
            <h2>Exposure sequence</h2>
          </header>

          <c-CForm submitting @submit.prevent="void 0">
            <c-CField readonly>
              <c-fill name="label">
                Filter sequence
              </c-fill>
              <c-fill name="default">
                <c-CInput
                  name="filters"
                  value="L · R · G · B"
                />
              </c-fill>
            </c-CField>
            <c-CButton type="submit" loading>
              Sending sequence
            </c-CButton>
          </c-CForm>
        </article>
      </section>
    """

    css = """
      :where(.form-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.form-glance__card) {
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.form-glance__card header) {
        margin-block-end: 1rem;
      }

      :where(.form-glance__card h2, .form-glance__card p) {
        margin-block: 0;
      }

      :where(.form-glance__card header p) {
        margin-block-end: 0.35rem;
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.form-glance__card [data-citry-ui-part="button"]) {
        justify-self: start;
      }
    """


preview = FormAtAGlance()

preview  # noqa: B018
````


## Build a native Form

Set common native attributes directly on `CForm`. Named controls provide the
submission data.


### Build a Form

[Open the rendered preview](/v/0.4.6/ui-library/components/form/_previews/compose-form/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ComposeForm(Component):
    template = """
      <section class="orbit-request" x-data="{ saved: '' }">
        <header>
          <p>Orbital survey</p>
          <h2>Queue a tracking request</h2>
        </header>

        <c-CForm
          id="orbit-request-form"
          action="/tracking-requests"
          method="post"
          autocomplete="off"
          @submit.prevent="saved = new FormData($el).get('object')"
        >
          <c-CField required>
            <c-fill name="label">
              Object designation
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="object"
                value="2024 YR4"
              />
            </c-fill>
          </c-CField>
          <c-CButton type="submit">
            Queue tracking
          </c-CButton>
        </c-CForm>

        <p aria-live="polite" x-show="saved">
          Queued <strong x-text="saved"></strong>
        </p>
      </section>
    """

    css = """
      :where(.orbit-request) {
        max-width: 38rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.orbit-request header) {
        margin-block-end: 1rem;
      }

      :where(.orbit-request h2, .orbit-request p) {
        margin-block: 0;
      }

      :where(.orbit-request header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.orbit-request form > fieldset > [data-citry-ui-part="button"]) {
        justify-self: start;
      }

      :where(.orbit-request > p) {
        margin-block-start: 1rem;
        color: light-dark(#175c43, #7be0b5);
      }
    """


preview = ComposeForm()

preview  # noqa: B018
````



```citry-html
<c-CForm
  action="/tracking-requests"
  method="post"
  @submit="queueTracking($event)"
>
  <c-CField required>
    <c-fill name="label">
      Object designation
    </c-fill>
    <c-fill name="default">
      <c-CInput name="object" />
    </c-fill>
  </c-CField>

  <c-CButton type="submit">
    Queue tracking
  </c-CButton>
</c-CForm>
```


Compose the same Form in Python:


```python
from citry_ui import CForm

tracking_form = CForm(
    action="/tracking-requests",
    method="post",
    slots={"default": fields},
)
```


Use `method="post"` and `enctype="multipart/form-data"` for file uploads.
`target`, `autocomplete`, and `novalidate` map directly to their native Form
attributes. `method="dialog"` retains native Dialog submission behavior.

Less-common native, ARIA, `data-*`, and Alpine attributes go through `attrs`.
Common native attributes have direct inputs and cannot also be supplied through
`attrs`. Prefer top-level `class_` and `style`; class and style values retained
in `attrs` merge with them.

## Configure shared behavior

Server inputs are passed in Python through `<c-CForm ... />` attributes or a
`CForm(...)` composition call. Client inputs are passed in the browser through
the `$c-props="{...}"` attribute.


### Configure Form

[Open the rendered preview](/v/0.4.6/ui-library/components/form/_previews/configuration/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormConfiguration(Component):
    template = """
      <section
        class="form-configurator"
        x-data="{
          disabled: false,
          readonly: false,
          submitting: false,
          gap: '1rem',
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
        :style="{'--cui-form-gap': gap}"
      >
        <header>
          <p>Deep-sky planner</p>
          <h2>Configure Form state</h2>
        </header>

        <c-CForm
          class_="form-configurator__form"
          $c-props="{
            disabled,
            readonly,
            submitting,
          }"
          @submit.prevent="void 0"
        >
          <c-CField>
            <c-fill name="label">
              Observation notes
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="notes"
                value="Track the nebula after moonset."
              />
            </c-fill>
          </c-CField>
          <c-CButton
            type="submit"
          >
            Save plan
          </c-CButton>
        </c-CForm>

        <p class="form-configurator__status" aria-live="polite">
          <span
            x-text="
              disabled
                ? 'disabled'
                : readonly
                  ? 'read-only'
                  : submitting
                    ? 'submitting'
                    : 'editable'
            "
          ></span>
        </p>
      </section>
    """

    css = """
      :where(.form-configurator) {
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.form-configurator header) {
        margin-block-end: 1rem;
      }

      :where(.form-configurator h2, .form-configurator p) {
        margin-block: 0;
      }

      :where(.form-configurator header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.form-configurator__form [data-citry-ui-part="button"]) {
        justify-self: start;
      }

      :where(.form-configurator__status) {
        margin-block-start: 0.85rem;
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.8125rem;
      }
    """


preview_controls = (
    {
        "name": "disabled",
        "label": "Disable Form",
        "type": "checkbox",
        "default": False,
    },
    {
        "name": "readonly",
        "label": "Use read-only defaults",
        "type": "checkbox",
        "default": False,
    },
    {
        "name": "submitting",
        "label": "Show submitting state",
        "type": "checkbox",
        "default": False,
    },
    {
        "name": "gap",
        "label": "Content spacing",
        "type": "select",
        "default": "1rem",
        "options": (("0.5rem", "Compact"), ("1rem", "Default"), ("1.5rem", "Spacious")),
    },
)

preview = FormConfiguration()

preview  # noqa: B018
````



```citry-html
<c-CForm
  $c-props="{
    disabled: accessClosed,
    readonly: reviewMode,
    submitting: requestPending,
  }"
>
  ...
</c-CForm>
```


A valid client Boolean wins over its server input. Removing it restores the
server value. Invalid client values report one diagnostic per invalid episode
and use that field's server value.

`disabled` uses the internal native fieldset. Physical descendant controls are
disabled and excluded from submission, even when a child requests
`disabled=False`. `readonly` is a default for supporting Citry UI controls;
ordinary native controls are unchanged. `submitting` affects only the Form's
busy marker and submit guard, so controls stay focusable and successful.

## Read native submission data

Handle the native `submit` event. Call `preventDefault()` only when browser
code or Citry Events owns transport.


### Read native FormData

[Open the rendered preview](/v/0.4.6/ui-library/components/form/_previews/native-submission/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NativeSubmission(Component):
    template = """
      <section
        class="transient-report"
        x-data="{ submitted: '', submitter: '' }"
      >
        <header>
          <p>Transient watch</p>
          <h2>Report a changing object</h2>
        </header>

        <c-CForm
          action="/transients"
          method="post"
          @submit.prevent="
            submitted = JSON.stringify(
              Object.fromEntries(new FormData($el, $event.submitter))
            );
            submitter = $event.submitter?.value ?? '';
          "
        >
          <c-CField required>
            <c-fill name="label">
              Object
            </c-fill>
            <c-fill name="default">
              <c-CInput name="object" value="AT 2026lmn" />
            </c-fill>
          </c-CField>
          <c-CField>
            <c-fill name="label">
              Brightness
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="magnitude"
                value="17.4"
                inputmode="decimal"
              />
            </c-fill>
          </c-CField>
          <div class="transient-report__actions">
            <c-CButton
              type="submit"
              c-attrs="{'name': 'intent', 'value': 'report'}"
            >
              Report object
            </c-CButton>
            <c-CButton
              type="reset"
              variant="ghost"
              intent="neutral"
            >
              Reset
            </c-CButton>
          </div>
        </c-CForm>

        <output aria-live="polite" x-show="submitted">
          Submitter: <strong x-text="submitter"></strong><br />
          FormData: <code x-text="submitted"></code>
        </output>
      </section>
    """

    css = """
      :where(.transient-report) {
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.transient-report header) {
        margin-block-end: 1rem;
      }

      :where(.transient-report h2, .transient-report p) {
        margin-block: 0;
      }

      :where(.transient-report header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.transient-report__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
      }

      :where(.transient-report output) {
        display: block;
        margin-block-start: 1rem;
        padding: 0.75rem;
        border-radius: 0.5rem;
        background: light-dark(#f3f1ff, #25243d);
        overflow-wrap: anywhere;
      }
    """


preview = NativeSubmission()

preview  # noqa: B018
````



```javascript
const data = new FormData(event.currentTarget, event.submitter)
const submitter = event.submitter
```


Submit, reset, Enter submission, constraint validation, successful-control
rules, and submitter selection remain browser-native. `requestSubmit()` follows
validation and dispatches submit. Direct `form.submit()` bypasses both.

Controls named `submit`, `reset`, or another Form property can shadow that
property. Choose a different name or call the method from `HTMLFormElement`'s
prototype.

## Use browser validation

Put native constraints on controls. The browser owns complete Form validity,
invalid focus, and submission blocking.


### Use native validation

[Open the rendered preview](/v/0.4.6/ui-library/components/form/_previews/validation/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NativeValidation(Component):
    template = """
      <section
        class="instrument-booking"
        x-data="{ accepted: false }"
      >
        <header>
          <p>Instrument desk</p>
          <h2>Book the spectrograph</h2>
        </header>

        <c-CForm
          @submit.prevent="accepted = true"
          @input="accepted = false"
        >
          <c-CField required>
            <c-fill name="label">
              Contact email
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="email"
                type="email"
                placeholder="observer@example.org"
              />
            </c-fill>
            <c-fill name="description">
              The browser checks the address before submission.
            </c-fill>
          </c-CField>
          <c-CField required>
            <c-fill name="label">
              Observation date
            </c-fill>
            <c-fill name="default" data="{ control_attrs }">
              <input
                class="instrument-booking__date"
                type="date"
                name="date"
                c-bind="control_attrs"
              />
            </c-fill>
          </c-CField>
          <c-CButton type="submit">
            Check availability
          </c-CButton>
        </c-CForm>

        <p
          class="instrument-booking__success"
          aria-live="polite"
          x-show="accepted"
        >
          The request is ready to send.
        </p>
      </section>
    """

    css = """
      :where(.instrument-booking) {
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.instrument-booking header) {
        margin-block-end: 1rem;
      }

      :where(.instrument-booking h2, .instrument-booking p) {
        margin-block: 0;
      }

      :where(.instrument-booking header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.instrument-booking__date) {
        inline-size: 100%;
        box-sizing: border-box;
        padding: 0.625rem 0.75rem;
        border: 1px solid light-dark(#9498bd, #686c96);
        border-radius: 0.5rem;
        background: Canvas;
        color: CanvasText;
        font: inherit;
      }

      :where(.instrument-booking form[data-validation-attempted] :invalid) {
        border-color: light-dark(#b42318, #ff8a80);
      }

      :where(.instrument-booking [data-citry-ui-part="button"]) {
        justify-self: start;
      }

      :where(.instrument-booking__success) {
        margin-block-start: 1rem;
        color: light-dark(#175c43, #7be0b5);
      }
    """


preview = NativeValidation()

preview  # noqa: B018
````


After a physical descendant dispatches `invalid`, CForm exposes
`data-validation-attempted` for application styling. This includes invalid
events caused by `checkValidity()` or `reportValidity()`.

CForm does not expose a parallel validity callback or `valid` attribute. Native
controls, external `form=id` controls, third-party controls, and programmatic
changes must all agree on whether the Form can submit; the browser is the one
complete authority.

Server validation remains authoritative. Error text does not change native
validity by itself. Use native constraints or `setCustomValidity()` when a
server condition must block a later native submission.

## Reset values

A native reset Button restores each control's authored default. CForm clears
`data-validation-attempted` only after the reset event finishes uncanceled.


### Reset or cancel reset

[Open the rendered preview](/v/0.4.6/ui-library/components/form/_previews/reset/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormReset(Component):
    template = """
      <section
        class="exposure-reset"
        x-data="{ cancel_reset: false, status: 'Edit either value, then reset.' }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p>Exposure plan</p>
          <h2>Restore authored defaults</h2>
        </header>

        <c-CForm
          @submit.prevent="void 0"
          @reset="
            if (cancel_reset) {
              $event.preventDefault();
              status = 'Reset canceled; edits preserved.';
            } else {
              setTimeout(() => status = 'Defaults restored.', 0);
            }
          "
        >
          <c-CField>
            <c-fill name="label">
              Exposure
            </c-fill>
            <c-fill name="default">
              <c-CInput name="exposure" value="120 seconds" />
            </c-fill>
          </c-CField>
          <c-CField>
            <c-fill name="label">
              Frames
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="frames"
                value="24"
                inputmode="numeric"
              />
            </c-fill>
          </c-CField>
          <c-CButton
            type="reset"
            variant="outline"
            intent="neutral"
          >
            Restore defaults
          </c-CButton>
        </c-CForm>

        <p
          class="exposure-reset__status"
          aria-live="polite"
          x-text="status"
        ></p>
      </section>
    """

    css = """
      :where(.exposure-reset) {
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.exposure-reset header) {
        margin-block-end: 1rem;
      }

      :where(.exposure-reset h2, .exposure-reset p) {
        margin-block: 0;
      }

      :where(.exposure-reset header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.exposure-reset [data-citry-ui-part="button"]) {
        justify-self: start;
      }

      :where(.exposure-reset__status) {
        margin-block-start: 1rem;
        color: color-mix(in srgb, currentColor 68%, transparent);
      }
    """


preview_controls = (
    {
        "name": "cancel_reset",
        "label": "Cancel the reset event",
        "type": "checkbox",
        "default": False,
    },
)

preview = FormReset()

preview  # noqa: B018
````


If any reset listener calls `preventDefault()`, values and the attempted marker
remain unchanged. Application-owned server errors, dirty state, or request
state are separate and must be reset by their owner.

## Guard duplicate submission

Set the client `submitting` input after accepting the first submit. Later submit
events are canceled at CForm's capture listener while the value remains true.


### Guard duplicate submission

[Open the rendered preview](/v/0.4.6/ui-library/components/form/_previews/submitting/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SubmittingGuard(Component):
    template = """
      <section
        class="plate-solve"
        x-data="{ submitting: false, attempts: 0, snapshot: '' }"
      >
        <header>
          <p>Astrometry pipeline</p>
          <h2>Solve a star field</h2>
        </header>

        <c-CForm
          $c-props="{ submitting }"
          @submit.prevent="
            attempts += 1;
            snapshot = JSON.stringify(Object.fromEntries(new FormData($el)));
            submitting = true;
          "
        >
          <c-CField>
            <c-fill name="label">
              Frame ID
            </c-fill>
            <c-fill name="default">
              <c-CInput name="frame" value="M42-L-0084" />
            </c-fill>
          </c-CField>
          <div class="plate-solve__actions">
            <c-CButton
              type="submit"
              $c-props="{ loading: submitting }"
            >
              Solve frame
            </c-CButton>
            <c-CButton
              type="button"
              variant="outline"
              intent="neutral"
              @click="submitting = false"
            >
              Finish request
            </c-CButton>
          </div>
        </c-CForm>

        <p class="plate-solve__status" aria-live="polite">
          Accepted submits: <strong x-text="attempts"></strong>
          <span x-show="snapshot"> · FormData <code x-text="snapshot"></code></span>
        </p>
      </section>
    """

    css = """
      :where(.plate-solve) {
        max-width: 44rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.plate-solve header) {
        margin-block-end: 1rem;
      }

      :where(.plate-solve h2, .plate-solve p) {
        margin-block: 0;
      }

      :where(.plate-solve header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.plate-solve__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
      }

      :where(.plate-solve__status) {
        margin-block-start: 1rem;
        overflow-wrap: anywhere;
        color: color-mix(in srgb, currentColor 72%, transparent);
      }
    """


preview = SubmittingGuard()

preview  # noqa: B018
````


The first event already passed the guard and reaches the application handler.
Submitting does not disable controls, so `FormData` retains their values. The
application owns clearing the value after success or failure.

This is a client-side duplicate guard, not request idempotency. Earlier ancestor
capture listeners, same-node capture listeners registered first, and direct
`form.submit()` can still observe or bypass it.

## Use multiple submitters

Native submitter attributes let one Form expose different actions without a
component-specific callback.


### Use multiple submitters

[Open the rendered preview](/v/0.4.6/ui-library/components/form/_previews/multiple-submitters/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MultipleSubmitters(Component):
    template = """
      <section
        class="observation-draft"
        x-data="{ status: 'Choose how to save the observation.' }"
      >
        <header>
          <p>Observation log</p>
          <h2>Save a lunar transit</h2>
        </header>

        <c-CForm
          action="/observations"
          method="post"
          @submit.prevent="
            status = $event.submitter.value
              + ' via '
              + ($event.submitter.formMethod || $event.currentTarget.method).toUpperCase()
              + ' to '
              + ($event.submitter.formAction || $event.currentTarget.action)
          "
        >
          <c-CField required>
            <c-fill name="label">
              Summary
            </c-fill>
            <c-fill name="default">
              <c-CInput name="summary" value="Io crossed Jupiter at 02:14 UTC" />
            </c-fill>
          </c-CField>
          <div class="observation-draft__actions">
            <c-CButton
              type="submit"
              variant="outline"
              intent="neutral"
              c-attrs="{
                'name': 'intent',
                'value': 'draft',
                'formaction': '/observations/drafts',
                'formnovalidate': True,
              }"
            >
              Save draft
            </c-CButton>
            <c-CButton
              type="submit"
              c-attrs="{
                'name': 'intent',
                'value': 'publish',
                'formaction': '/observations/publish',
                'formmethod': 'post',
              }"
            >
              Publish
            </c-CButton>
          </div>
        </c-CForm>

        <p
          class="observation-draft__status"
          aria-live="polite"
          x-text="status"
        ></p>
      </section>
    """

    css = """
      :where(.observation-draft) {
        max-width: 46rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.observation-draft header) {
        margin-block-end: 1rem;
      }

      :where(.observation-draft h2, .observation-draft p) {
        margin-block: 0;
      }

      :where(.observation-draft header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.observation-draft__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
      }

      :where(.observation-draft__status) {
        margin-block-start: 1rem;
        color: light-dark(#175c43, #7be0b5);
      }
    """


preview = MultipleSubmitters()

preview  # noqa: B018
````


Pass `name`, `value`, `formaction`, `formenctype`, `formmethod`,
`formnovalidate`, and `formtarget` through each action `CButton`'s server
`attrs`. Read the accepted control from `SubmitEvent.submitter`.

## Associate an external control

Give CForm a unique `id`, then set a standalone native control's `form`
attribute to that ID. The browser includes it in `form.elements`, validation,
reset, submission, and `FormData`.


### Associate an external control

[Open the rendered preview](/v/0.4.6/ui-library/components/form/_previews/external-controls/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ExternalControls(Component):
    template = """
      <section
        class="proposal-form"
        x-data="{ disabled: false, result: '' }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p>Time allocation</p>
          <h2>Submit a telescope proposal</h2>
        </header>

        <c-CForm
          id="proposal-form"
          $c-props="{ disabled }"
          @submit.prevent="
            result = JSON.stringify(
              Object.fromEntries(new FormData($el, $event.submitter))
            )
          "
        >
          <c-CField required>
            <c-fill name="label">
              Proposal title
            </c-fill>
            <c-fill name="default">
              <c-CInput name="title" value="Atmospheres of nearby super-Earths" />
            </c-fill>
          </c-CField>
          <c-CButton type="submit">
            Submit proposal
          </c-CButton>
        </c-CForm>

        <div class="proposal-form__external">
          <label for="allocation-code">External allocation code</label>
          <c-CInput
            id="allocation-code"
            name="allocation"
            value="Q4-NORTH"
            c-attrs="{'form': 'proposal-form'}"
          />
          <small>Owned by the Form, but outside its disabled fieldset.</small>
          <c-CButton
            type="submit"
            variant="outline"
            intent="neutral"
            c-attrs="{
              'form': 'proposal-form',
              'name': 'intent',
              'value': 'external',
            }"
          >
            Submit from outside
          </c-CButton>
        </div>

        <output
          aria-live="polite"
          x-show="result"
          x-text="result"
        ></output>
      </section>
    """

    css = """
      :where(.proposal-form) {
        display: grid;
        gap: 1rem;
        max-width: 46rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.proposal-form h2, .proposal-form p) {
        margin-block: 0;
      }

      :where(.proposal-form header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.proposal-form [data-citry-ui-part="button"]) {
        justify-self: start;
      }

      :where(.proposal-form__external) {
        display: grid;
        gap: 0.4rem;
        padding: 0.875rem;
        border-inline-start: 0.25rem solid light-dark(#6d5bd0, #a9a2ff);
        background: light-dark(#f7f6ff, #24233b);
      }

      :where(.proposal-form__external label) {
        font-weight: 650;
      }

      :where(.proposal-form__external small) {
        color: color-mix(in srgb, currentColor 68%, transparent);
      }

      :where(.proposal-form__external [data-citry-ui-part="button"]) {
        justify-self: start;
      }

      :where(.proposal-form output) {
        overflow-wrap: anywhere;
      }
    """


preview_controls = (
    {
        "name": "disabled",
        "label": "Disable internal controls",
        "type": "checkbox",
        "default": False,
    },
)

preview = ExternalControls()

preview  # noqa: B018
````


An external control is not a physical descendant of CForm's fieldset, so Form
`disabled` does not disable it and its non-bubbling `invalid` event does not set
CForm's attempted marker. Standalone `CInput` can receive `form` through
`attrs`. Compound controls such as `CCombobox` reject external redirection until
their visible validation and submitted-value elements can be associated
together.

## Show server errors

Render server feedback through Field. The application decides when a message
clears and whether it also sets custom native validity.


### Show a server error

[Open the rendered preview](/v/0.4.6/ui-library/components/form/_previews/server-errors/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ServerErrors(Component):
    template = """
      <section
        class="account-request"
        x-data="{
          error: 'That observer handle is already registered.',
        }"
      >
        <header>
          <p>Observer network</p>
          <h2>Request an observatory account</h2>
        </header>

        <c-CForm @submit.prevent="void 0">
          <c-CField
            $c-props="{
              invalid: Boolean(
                Alpine.$data($root.closest('.account-request')).error
              ),
            }"
          >
            <c-fill name="label">
              Observer handle
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="handle"
                value="night-heron"
                @input="Alpine.$data($root.closest('.account-request')).error = ''"
              />
            </c-fill>
            <c-fill name="error">
              <span
                x-text="Alpine.$data($root.closest('.account-request')).error"
              ></span>
            </c-fill>
          </c-CField>
          <c-CButton type="submit">
            Request account
          </c-CButton>
        </c-CForm>

        <p class="account-request__hint">
          The application clears this server message when the rejected field changes.
        </p>
      </section>
    """

    css = """
      :where(.account-request) {
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.account-request header) {
        margin-block-end: 1rem;
      }

      :where(.account-request h2, .account-request p) {
        margin-block: 0;
      }

      :where(.account-request header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.account-request [data-citry-ui-part="button"]) {
        justify-self: start;
      }

      :where(.account-request__hint) {
        margin-block-start: 1rem;
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.875rem;
      }
    """


preview = ServerErrors()

preview  # noqa: B018
````


CForm does not own an error map, schema, touched state, or validation rules.
Those concerns can compose around the native Form without changing its browser
contract.

## Add and reorder controls

Use stable application keys when controls are repeated. The browser's live
`form.elements` and `FormData` define current membership and document order.


### Change repeated controls

[Open the rendered preview](/v/0.4.6/ui-library/components/form/_previews/dynamic-fields/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DynamicFields(Component):
    template = """
      <section
        class="filter-sequence"
        x-data="{
          rows: [
            { id: 1, value: 'Luminance' },
            { id: 2, value: 'Hydrogen-alpha' },
            { id: 3, value: 'Oxygen III' },
          ],
          nextId: 4,
          result: '',
        }"
      >
        <header>
          <p>Filter wheel</p>
          <h2>Build an exposure sequence</h2>
        </header>

        <c-CForm @submit.prevent="result = JSON.stringify(new FormData($el).getAll('filter'))">
          <div class="filter-sequence__rows">
            <template x-for="(row, index) in rows" :key="row.id">
              <div class="filter-sequence__row">
                <label
                  :for="`filter-${row.id}`"
                  x-text="`Exposure ${index + 1}`"
                ></label>
                <input
                  :id="`filter-${row.id}`"
                  name="filter"
                  x-model="row.value"
                />
                <button type="button" @click="rows.splice(index, 1)">Remove</button>
              </div>
            </template>
          </div>
          <div class="filter-sequence__actions">
            <c-CButton
              type="button"
              variant="outline"
              intent="neutral"
              @click="rows.push({ id: nextId++, value: 'New filter' })"
            >
              Add exposure
            </c-CButton>
            <c-CButton
              type="button"
              variant="ghost"
              intent="neutral"
              @click="rows.length > 1 && rows.unshift(rows.pop())"
            >
              Rotate order
            </c-CButton>
            <c-CButton type="submit">
              Read FormData
            </c-CButton>
          </div>
        </c-CForm>

        <output
          aria-live="polite"
          x-show="result"
          x-text="result"
        ></output>
      </section>
    """

    css = """
      :where(.filter-sequence) {
        max-width: 48rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.filter-sequence header) {
        margin-block-end: 1rem;
      }

      :where(.filter-sequence h2, .filter-sequence p) {
        margin-block: 0;
      }

      :where(.filter-sequence header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.filter-sequence__rows) {
        display: grid;
        gap: 0.625rem;
      }

      :where(.filter-sequence__row) {
        display: grid;
        grid-template-columns: minmax(6rem, 0.45fr) minmax(0, 1fr) auto;
        align-items: center;
        gap: 0.625rem;
      }

      :where(.filter-sequence__row input) {
        min-width: 0;
        padding: 0.55rem 0.7rem;
        border: 1px solid light-dark(#9498bd, #686c96);
        border-radius: 0.45rem;
        background: Canvas;
        color: CanvasText;
        font: inherit;
      }

      :where(.filter-sequence__row button) {
        border: 0;
        background: transparent;
        color: light-dark(#9b2c24, #ff9d94);
        cursor: pointer;
      }

      :where(.filter-sequence__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
      }

      :where(.filter-sequence output) {
        display: block;
        margin-block-start: 1rem;
        overflow-wrap: anywhere;
      }

      @media (max-width: 34rem) {
        :where(.filter-sequence__row) {
          grid-template-columns: minmax(0, 1fr) auto;
        }

        :where(.filter-sequence__row label) {
          grid-column: 1 / -1;
        }
      }
    """


preview = DynamicFields()

preview  # noqa: B018
````


CForm stores no participant registry, so removed controls cannot remain in a
parallel validity or submission list. Native repeated, bracketed, and dotted
names serialize exactly as authored; server code owns higher-level parsing.

## Theme and customize Form

CForm inherits typography, color, and `color-scheme`. Set
`--cui-form-gap` on an ancestor or Form root to change spacing between direct
children. Use the public Form and fieldset part selectors for targeted layout.


### Theme Form

[Open the rendered preview](/v/0.4.6/ui-library/components/form/_previews/theme-customization/)

````citry
import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormThemeCustomization(Component):
    template = """
      <section
        class="night-checklist"
        x-data="{ gap: '0.75rem', scheme: 'light', compact: false }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
        :style="{ colorScheme: scheme, '--cui-form-gap': gap }"
        :data-compact="compact"
      >
        <header>
          <p>Night checklist</p>
          <h2>Prepare the observatory</h2>
        </header>

        <c-CForm
          class_="night-checklist__form"
          @submit.prevent="void 0"
        >
          <label>
            <input
              type="checkbox"
              name="task"
              value="dome"
            />
            Open the dome shutters
          </label>
          <label>
            <input
              type="checkbox"
              name="task"
              value="cooling"
            />
            Start detector cooling
          </label>
          <label>
            <input
              type="checkbox"
              name="task"
              value="weather"
            />
            Confirm weather limits
          </label>
          <c-CButton type="submit" size="sm">
            Begin session
          </c-CButton>
        </c-CForm>
      </section>
    """

    css = """
      :where(.night-checklist) {
        max-width: 40rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.night-checklist[data-compact]) {
        max-width: 28rem;
      }

      :where(.night-checklist header) {
        margin-block-end: 1rem;
      }

      :where(.night-checklist h2, .night-checklist p) {
        margin-block: 0;
      }

      :where(.night-checklist header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.night-checklist__form[data-citry-ui-part="form"]) {
        padding: 1rem;
        border: 1px solid light-dark(#d7d8ea, #3c3f63);
        border-radius: 0.625rem;
        background: light-dark(#fafaff, #1c1c2d);
      }

      :where(.night-checklist__form [data-citry-ui-part="fieldset"]) {
        align-items: start;
      }

      :where(.night-checklist__form label) {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      :where(.night-checklist__form [data-citry-ui-part="button"]) {
        justify-self: start;
      }
    """


preview_controls = (
    {
        "name": "gap",
        "label": "Form spacing",
        "type": "select",
        "default": "0.75rem",
        "options": (("0.4rem", "Tight"), ("0.75rem", "Default"), ("1.25rem", "Open")),
    },
    {
        "name": "scheme",
        "label": "Color scheme",
        "type": "select",
        "default": "light",
        "options": (("light", "Light"), ("dark", "Dark")),
    },
    {
        "name": "compact",
        "label": "Narrow container",
        "type": "checkbox",
        "default": False,
    },
)

preview = FormThemeCustomization()

preview  # noqa: B018
````



```css
.compact-observation {
  --cui-form-gap: 0.625rem;
}

.compact-observation [data-citry-ui-part="fieldset"] {
  align-items: start;
}
```


The documented variable, parts, and reflected attributes are public CSS API.
`.cui-*` classes and `--_cui-*` variables are private.

## Accessibility and native boundaries

CForm adds no role. The native Form supplies submission, validation, reset,
keyboard, focus, autofill, and assistive-technology behavior. Keep source order
aligned with visual order and use a visible heading or `aria-labelledby` when
the surrounding page needs an accessible Form name.

The internal fieldset begins with a private hidden legend. It reserves HTML's
first-legend disabled exemption so user controls cannot accidentally remain
enabled. Put visible group legends inside their own nested fieldsets; do not
place a direct legend in CForm's default slot.

Controls outside the Form may associate through `form=id`, but they do not
inherit the physical fieldset's disabled behavior. A Form inside `CDialog` may
use `method="dialog"`; never nest one native Form inside another.

## API reference

### Inputs

#### CForm server inputs

Server inputs are passed in a template through `<c-CForm ... />` or in Python through
`CForm(...)`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 13rem; --ui-api-column-3-width: 7rem">

| Input | Type | Default | Effect |
|---|---|---|---|
| <span id="form-input-cform-server-inputs-id"></span>`id` | `str | None` | generated | Sets unique native Form identity and an external control ownership target. |
| <span id="form-input-cform-server-inputs-action"></span>`action` | `str | None` | `None` | Sets the native submission destination; omission preserves browser current-URL behavior. |
| <span id="form-input-cform-server-inputs-method"></span>`method` | `"get" | "post" | "dialog" | None` ([`CFormMethod`](#form-interface-input-type-aliases-cform-method)) | `None` | Sets the native submission method; omission uses the browser default. |
| <span id="form-input-cform-server-inputs-enctype"></span>`enctype` | `"application/x-www-form-urlencoded" | "multipart/form-data" | "text/plain" | None` ([`CFormEnctype`](#form-interface-input-type-aliases-cform-enctype)) | `None` | Sets native submission encoding. |
| <span id="form-input-cform-server-inputs-target"></span>`target` | `str | None` | `None` | Sets the native browsing-context target. |
| <span id="form-input-cform-server-inputs-autocomplete"></span>`autocomplete` | `"on" | "off" | None` ([`CFormAutocomplete`](#form-interface-input-type-aliases-cform-autocomplete)) | `None` | Sets the native Form autocomplete hint. |
| <span id="form-input-cform-server-inputs-disabled"></span>`disabled` | `bool` | `False` | Disables physical descendant controls through the internal fieldset and supplies inherited Citry disabled state. |
| <span id="form-input-cform-server-inputs-readonly"></span>`readonly` | `bool` | `False` | Supplies a read-only default to supporting Citry controls; ordinary native controls are unaffected. |
| <span id="form-input-cform-server-inputs-submitting"></span>`submitting` | `bool` | `False` | Exposes Form busy state and stops later submit handlers reached after CForm's capture listener; it is not inherited by descendants. |
| <span id="form-input-cform-server-inputs-novalidate"></span>`novalidate` | `bool` | `False` | Maps to native `novalidate`. |
| <span id="form-input-cform-server-inputs-class"></span>`class_` | `str | Mapping[str, bool] | Sequence[CClassValue] | None` ([`CClassValue`](#form-interface-input-type-aliases-class-value)) | `None` | Adds native Form classes from a string, conditional mapping, or nested sequence and merges them with `attrs`. |
| <span id="form-input-cform-server-inputs-style"></span>`style` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue] | None` ([`CStyleValue`](#form-interface-input-type-aliases-style-value)) | `None` | Adds native Form inline styles from CSS text, a property mapping, or nested sequence and merges them with `attrs`. |
| <span id="form-input-cform-server-inputs-attrs"></span>`attrs` | `Mapping[str, object] | None` | `None` | Adds allowed less-common native Form, ARIA, Alpine, and data attributes; direct native inputs, public parts, and reflected attributes cannot also be supplied here. Class and style values merge with the top-level inputs. |

</div>

#### CForm client inputs

Client inputs are passed in the browser through the `$c-props="{ ... }"` attribute on
`<c-CForm />`.

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 9rem; --ui-api-column-3-width: 11rem">

| Input | Type | Omitted behavior | Effect |
|---|---|---|---|
| <span id="form-input-cform-client-inputs-disabled"></span>`disabled` | `boolean` | Uses the server input. | Controls the fieldset, inherited Citry disabled state, and `data-disabled`. |
| <span id="form-input-cform-client-inputs-readonly"></span>`readonly` | `boolean` | Uses the server input. | Controls inherited Citry read-only state and `data-readonly`. |
| <span id="form-input-cform-client-inputs-submitting"></span>`submitting` | `boolean` | Uses the server input. | Controls Form busy state, its submit guard, and `data-submitting`; descendants remain enabled unless disabled separately. |

</div>

### Slots

Slots are passed as nested content or `<c-fill>` tags in a template, or through the
`slots={...}` argument in Python.

#### CForm slots

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 6rem; --ui-api-column-3-width: 14rem">

| Slot | Required | Data | Fallback |
|---|---|---|---|
| <span id="form-slot-cform-slots-default"></span>`default` | yes | `{}` ([`CFormDefaultSlotData`](#form-interface-cform-default-slot-data)) | none |

</div>

### Events

-

### Methods

-

### CSS

CSS variables to theme the components. Set them on an ancestor or the component itself.

#### CForm CSS variables

Apply these variables to `CForm` or one of its ancestors.

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2 ui-api-table--width-column-4" markdown="1" style="--ui-api-column-1-width: 17rem; --ui-api-column-2-width: 8rem; --ui-api-column-4-width: 11rem">

| Variable | Type | Purpose | Default |
|---|---|---|---|
| <span id="form-css-cform-css-variables-cui-form-gap"></span>`--cui-form-gap` | `length` | Spacing between direct children of the internal fieldset. | `1rem` |

</div>

### Attributes

HTML attributes defined on the components that you can refer to for CSS, inspection, and
testing. Read-only.

#### CForm attributes

<div class="ui-api-table ui-api-table--fit-column-1 ui-api-table--width-column-2 ui-api-table--width-column-3" markdown="1" style="--ui-api-column-2-width: 10rem; --ui-api-column-3-width: 13rem">

| Attribute | Element | Type | Meaning |
|---|---|---|---|
| <span id="form-attribute-cform-attributes-data-disabled"></span>`data-disabled` | Native Form | `present | absent` | Mirrors effective disabled state. |
| <span id="form-attribute-cform-attributes-data-readonly"></span>`data-readonly` | Native Form | `present | absent` | Mirrors effective read-only state. |
| <span id="form-attribute-cform-attributes-data-submitting"></span>`data-submitting` | Native Form | `present | absent` | Mirrors effective submitting state. |
| <span id="form-attribute-cform-attributes-data-validation-attempted"></span>`data-validation-attempted` | Native Form | `present | absent` | Appears after a physical descendant dispatches native invalid, including through validation methods, and clears after an uncanceled reset. |

</div>

### Selectors

Selectors for the DOM nodes in the components that you can use for CSS, inspection, and
testing.

#### CForm selectors

<div class="ui-api-table ui-api-table--width-column-1 ui-api-table--width-column-2" markdown="1" style="--ui-api-column-1-width: 15rem; --ui-api-column-2-width: 10rem">

| Selector | Element | Purpose |
|---|---|---|
| <span id="form-selector-cform-selectors-data-citry-ui-part-form"></span>`[data-citry-ui-part="form"]` | Native Form | Root and `attrs` destination. |
| <span id="form-selector-cform-selectors-data-citry-ui-part-fieldset"></span>`[data-citry-ui-part="fieldset"]` | Native fieldset | Native disabled-group and direct-child layout boundary. |

</div>

### Interfaces

Aliases and data shapes referenced above.

#### Input type aliases

<div class="ui-api-table ui-api-table--fit-column-1" markdown="1">

| Interface | Definition |
|---|---|
| <span id="form-interface-input-type-aliases-class-value"></span>`CClassValue` | `str | Mapping[str, bool] | Sequence[CClassValue]` |
| <span id="form-interface-input-type-aliases-style-value"></span>`CStyleValue` | `str | Mapping[str, str | int | float | bool | None] | Sequence[CStyleValue]` |
| <span id="form-interface-input-type-aliases-cform-method"></span>`CFormMethod` | `Literal["get", "post", "dialog"]` |
| <span id="form-interface-input-type-aliases-cform-enctype"></span>`CFormEnctype` | `Literal["application/x-www-form-urlencoded", "multipart/form-data", "text/plain"]` |
| <span id="form-interface-input-type-aliases-cform-autocomplete"></span>`CFormAutocomplete` | `Literal["on", "off"]` |

</div>

<span id="form-interface-cform-default-slot-data"></span>

#### `CFormDefaultSlotData`

Empty dataclass: `{}`.

### Translation keys

-