---
title: Handle and validate forms
description: Turn named form controls into typed Python data and show field errors with Vue.
---

# Handle and validate forms

When a user submits a form, you want the fields as typed Python values. When
a value is wrong, you want the error next to the field, without clearing what
the user typed. In this step you build an email form that Python checks: it
rejects addresses outside `@example.com` and shows the error under the
field.

Replace `components.py` with:

<c-include-file path="docs_site/snippets/getting_started/components_step11.py" language="citry" />

Submit `ada@elsewhere.test` to see the field error, then submit
`ada@example.com` to see the accepted address.

## Send the form to a Python handler

```citry-html
<form @c-submit.prevent="submit">
  <input name="email" type="email" required />
</form>
```

`@c-submit` calls the `submit` handler when the form is submitted, and
`.prevent` stops the browser from loading a new page. Citry collects every
control that has a `name` and passes the values to the handler as a typed
object:

```python
class SignupIn:
    email: str

class Events:
    def submit(self, data: SignupIn):
        email = data.email.strip()
```

The `data: SignupIn` annotation tells Citry which class to build from the
form.

## Reject a value with a field error

```python
raise EventError(
    "Please fix the email address.",
    fields={"email": "Use an @example.com address."},
)
```

Raising [`EventError`][citry.ext.events.EventError] stops the handler and
sends the errors to the browser. The key in `fields` is the field name: it
matches both `SignupIn.email` and `name="email"`.

## Show the error and progress in the form

The template reads the error with `$error('submit')` and the progress with
`$loading('submit')`. Both refer to this component's `submit` handler:

```citry-html
<span
  role="alert"
  v-show="$error('submit')?.fieldErrors?.email"
  v-text="$error('submit')?.fieldErrors?.email || ''"
></span>
<button
  type="submit"
  :disabled="$loading('submit')"
  v-text="$loading('submit') ? 'Sending' : 'Send request'"
>
  Send request
</button>
```

The error stays until the next call to `submit` succeeds. The page does not
reload, so the input keeps what the user typed.

## Show the accepted value

When the address is valid, the handler sends a browser event with it:

```python
return actions.Dispatch("SignupForm:sent", {"email": email})
```

As in the earlier steps, the event name starts with the component's name.

The component keeps the accepted address in its Vue data, and listens for
the event with [`onEvent`][onEvent] inside
[`onServerRender`][onServerRender]:

```js
$component({
  data() {
    // Nothing is accepted until Python answers.
    return { acceptedEmail: '' };
  },
  onServerRender({ component, onEvent }) {
    // Citry removes this listener before onServerRender
    // runs again and when the component unmounts.
    onEvent('SignupForm:sent', (detail) => {
      // Show the email that Python sent with the event.
      component.acceptedEmail = detail.email;
    });
  },
});
```

`onEvent` hears only events from this component's own Python handlers, so
another form on the same page cannot change this one.

[Handle and validate forms](/events/forms/) in the Events guide covers
more, such as which Python type each kind of input sends.

## Next steps

Next, [replace the form with new HTML from Python](/getting-started/server-rendered-updates/).
