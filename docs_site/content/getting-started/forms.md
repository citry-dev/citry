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
return actions.Dispatch("signup:sent", {"email": email})
```

The component declares its local state with Vue Options:

```js
$component({
  data() {
    return { acceptedEmail: '' };
  },
});
```

`onServerRender` listens on the component root and returns the matching
cleanup:

```js
onServerRender({ component }) {
  const receiveSignup = (event) => {
    component.acceptedEmail = event.detail.email;
  };
  component.$el.addEventListener('signup:sent', receiveSignup);
  return () => component.$el.removeEventListener('signup:sent', receiveSignup);
}
```

[`Dispatch`][citry.ext.events.actions.Dispatch] starts at the calling
component's first live root. Cleanup prevents duplicate listeners after a
server render and removes the listener on unmount.

## Next steps

Next, [replace the calling component from Python](/getting-started/server-rendered-updates/).
