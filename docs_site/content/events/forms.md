---
title: Handle and validate forms
description: Turn named form controls into typed Python data and show server validation without losing what the user entered.
---

# Handle and validate forms

When a user submits a form, you want its fields as typed Python values, and
when something is wrong, you want the error next to the field without losing
what the user typed. Citry does both: it turns the named controls into a
Python object for your handler, and shows the errors your handler raises.

Start with [Server events](/events/) if you have not called a Python handler
from a component yet.

## Receive typed form data

Write a class with the fields the form sends, and use it as the type of the
handler's `data` parameter:

```citry
from citry import Component
from citry.ext.events import EventError


class ContactIn:
    name: str = ""
    email: str = ""


class ContactForm(Component):
    citry = citry_app

    class Kwargs:
        sent: bool = False

    class Events:
        def submit(self, data: ContactIn):
            if "@" not in data.email:
                raise EventError(
                    "Please fix the errors.",
                    fields={
                        "email": "Enter a valid email address."
                    },
                )
            send_contact_email(data.name, data.email)
            return ContactForm(sent=True)

    def template_data(self, kwargs, slots):
        return {"sent": kwargs.sent}

    template = """
      <c-if cond="sent">
        <p>Thanks, we'll be in touch!</p>
      </c-if>
      <c-else>
        <form @c-submit.prevent="submit">
          <input name="name">
          <input name="email">
          <span
            v-text="$error('submit')?.fieldErrors?.email"
          ></span>
          <button
            type="submit"
            :disabled="$loading('submit')"
          >
            Send
          </button>
        </form>
      </c-else>
    """
```

`@c-submit.prevent` collects the form's named controls and calls `submit`
instead of letting the browser submit the form. The `name` attributes match
the fields of `ContactIn`. Citry checks each value against its type before
the handler runs. A value of the wrong type fails the call with an error for
that field, and `submit` does not run.

## Show validation errors

Raise [`EventError`][citry.ext.events.EventError] with a message and an error
per field. When a call fails, nothing re-renders, so the form keeps what the
user typed.

[`$error('submit')`][$error] returns the last error from the `submit` handler,
or `null`. Its `fieldErrors` uses the field names you passed to `EventError`:

```citry-html
<span v-text="$error('submit')?.fieldErrors?.email"></span>
```

A later successful `submit` call clears the error. Errors from other
handlers in the same component are separate, so two forms in one component
show their own errors. To show one banner for the whole component, call
`$error()` without a name: it returns the newest error from any handler.

## Disable the button while the form is sending

[`$loading('submit')`][$loading] is true from the moment the submit is queued
until the response arrives:

```citry-html
<button type="submit" :disabled="$loading('submit')">
  Send
</button>
```

## Related pages

- [Bind events in templates](/events/bindings/) covers the other modifiers
  and the loading and error helpers.
- [Use event routes directly](/events/http/#keep-a-form-working-without-javascript)
  shows how to make the same form work without JavaScript.

!!! note "Errors when you call a handler from JavaScript"

    An `@c-*` attribute handles a failed call for you: the error appears in
    `$error()` and nothing else happens. When your own code calls a handler
    with `$sendEvent(...)`, a failed call also rejects the returned Promise,
    so catch it with `try`/`catch` or `.catch(...)`.
