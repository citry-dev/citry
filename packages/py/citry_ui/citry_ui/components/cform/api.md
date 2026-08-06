---
title: Form
description: Compose native submission, validation, reset, and shared control state with Citry UI Form.
---

# Form

Use `CForm` for native submission, validation, reset, and `FormData`. It renders
one `<form>` and an internal `<fieldset>`, shares disabled and read-only defaults
with supporting Citry UI controls, and can guard duplicate submits without
removing successful controls from the payload.

## Form at a glance

The Form owns coordination and layout. Field, Input, and Button keep their own
visual treatment.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cform/snippets/at_a_glance.py"
  title="Form at a glance"
/>

## Build a native Form

Set common native attributes directly on `CForm`. Named controls provide the
submission data.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cform/snippets/compose_form.py"
  title="Build a Form"
/>

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

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cform/snippets/configuration.py"
  title="Configure Form"
/>

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

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cform/snippets/native_submission.py"
  title="Read native FormData"
/>

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

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cform/snippets/validation.py"
  title="Use native validation"
/>

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

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cform/snippets/reset.py"
  title="Reset or cancel reset"
/>

If any reset listener calls `preventDefault()`, values and the attempted marker
remain unchanged. Application-owned server errors, dirty state, or request
state are separate and must be reset by their owner.

## Guard duplicate submission

Set the client `submitting` input after accepting the first submit. Later submit
events are canceled at CForm's capture listener while the value remains true.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cform/snippets/submitting.py"
  title="Guard duplicate submission"
/>

The first event already passed the guard and reaches the application handler.
Submitting does not disable controls, so `FormData` retains their values. The
application owns clearing the value after success or failure.

This is a client-side duplicate guard, not request idempotency. Earlier ancestor
capture listeners, same-node capture listeners registered first, and direct
`form.submit()` can still observe or bypass it.

## Use multiple submitters

Native submitter attributes let one Form expose different actions without a
component-specific callback.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cform/snippets/multiple_submitters.py"
  title="Use multiple submitters"
/>

Pass `name`, `value`, `formaction`, `formenctype`, `formmethod`,
`formnovalidate`, and `formtarget` through each action `CButton`'s server
`attrs`. Read the accepted control from `SubmitEvent.submitter`.

## Associate an external control

Give CForm a unique `id`, then set a standalone native control's `form`
attribute to that ID. The browser includes it in `form.elements`, validation,
reset, submission, and `FormData`.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cform/snippets/external_controls.py"
  title="Associate an external control"
/>

An external control is not a physical descendant of CForm's fieldset, so Form
`disabled` does not disable it and its non-bubbling `invalid` event does not set
CForm's attempted marker. Standalone `CInput` can receive `form` through
`attrs`. Compound controls such as `CCombobox` reject external redirection until
their visible validation and submitted-value elements can be associated
together.

## Show server errors

Render server feedback through Field. The application decides when a message
clears and whether it also sets custom native validity.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cform/snippets/server_errors.py"
  title="Show a server error"
/>

CForm does not own an error map, schema, touched state, or validation rules.
Those concerns can compose around the native Form without changing its browser
contract.

## Add and reorder controls

Use stable application keys when controls are repeated. The browser's live
`form.elements` and `FormData` define current membership and document order.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cform/snippets/dynamic_fields.py"
  title="Change repeated controls"
/>

CForm stores no participant registry, so removed controls cannot remain in a
parallel validity or submission list. Native repeated, bracketed, and dotted
names serialize exactly as authored; server code owns higher-level parsing.

## Theme and customize Form

CForm inherits typography, color, and `color-scheme`. Set
`--cui-form-gap` on an ancestor or Form root to change spacing between direct
children. Use the public Form and fieldset part selectors for targeted layout.

<c-ui-demo
  path="packages/py/citry_ui/citry_ui/components/cform/snippets/theme_customization.py"
  title="Theme Form"
/>

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
