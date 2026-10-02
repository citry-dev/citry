---
title: Handle and validate forms
description: Turn named form controls into typed Python data and show field errors with Vue.
---

# Handle and validate forms

Build an email form, reject the wrong domain in Python, and show the field
error without clearing what the visitor typed.

<c-include-file path="docs_site/snippets/getting_started/components_step11.py" language="citry" />

Submit `ada@elsewhere.test` to see the field error, then submit
`ada@example.com` to see the accepted address.

## Submit named controls

```citry-html
<form @c-submit.prevent="submit">
  <input name="email" type="email" required />
</form>
```

The `.prevent` modifier stops normal navigation. Citry collects named controls
and sends them to the typed handler input:

```python
class SignupIn:
    email: str

class Events:
    def submit(self, data: SignupIn):
        email = data.email.strip()
```

## Return field errors

```python
raise EventError(
    "Please fix the email address.",
    fields={"email": "Use an @example.com address."},
)
```

The field name matches both `SignupIn.email` and `name="email"`. Vue reads the
instance-scoped error and loading values directly:

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

A successful call clears that handler's retained error.

## Handle success in Vue

The handler dispatches the accepted email:

```python
return actions.Dispatch("SignupForm:sent", {"email": email})
```

As in the earlier steps, the event name starts with the component's name.

The component declares its local state with Vue Options:

```js
$component({
  data() {
    // Nothing is accepted until Python answers.
    return { acceptedEmail: '' };
  },
});
```

The [`onServerRender`][onServerRender] option runs after the component
mounts and again after each server render. It listens with
[`onEvent`][onEvent], which hears the events that this component's own
Python handlers dispatch:

```js
onServerRender({ component, onEvent }) {
  // Citry removes this listener before onServerRender
  // runs again and when the component unmounts.
  onEvent('SignupForm:sent', (detail) => {
    // Show the email that Python sent with the event.
    component.acceptedEmail = detail.email;
  });
}
```

`onEvent` hears only events from this component's own Python handlers, so
another form on the same page cannot change this one.

## Next steps

Next, [replace the calling component from Python](/getting-started/server-rendered-updates/).
