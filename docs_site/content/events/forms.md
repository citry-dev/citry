---
title: Handle and validate forms
description: Turn named form controls into typed Python data and show server validation without losing what the user entered.
---

# Handle and validate forms

On a form submit, Citry can collect named controls into a typed Python object.
If validation fails, the form stays in place and Alpine can show the returned
errors beside the relevant fields.

Start with [Server events](/events/) if you have not called a Python handler
from a component yet.

## Receive typed form data

Declare the fields the handler accepts, then annotate its `data` parameter
with that class:

```citry
from citry import Component
from citry.ext.events import EventError


class ContactIn:
    name: str = ""
    email: str = ""


class ContactForm(Component):
    citry = citry_app

    class Kwargs:
        name: str = ""
        email: str = ""
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
            return ContactForm(
                name=data.name,
                email=data.email,
                sent=True,
            )

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
            x-text="$error('submit')?.fieldErrors?.email"
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

The control names match `ContactIn.name` and `ContactIn.email`. Citry converts
and validates those values before calling `submit`.

Raise [`EventError`][citry.ext.events.EventError] to return a human message and
per-field errors. A failed call does not render anything, so the browser keeps
what the user typed. This also avoids maintaining a second validation schema
in JavaScript.

## Show errors and loading state

[`$error('submit')`][$error] exposes this handler's retained error. Its
`fieldErrors` object uses the names passed to `EventError`:

```citry-html
<span x-text="$error('submit')?.fieldErrors?.email"></span>
```

[`$loading('submit')`][$loading] covers this handler's time waiting in the
queue as well as the network request, so it is suitable for disabling the
submit button:

```citry-html
<button type="submit" :disabled="$loading('submit')">
  Send
</button>
```

A successful `submit` call clears only its own error. Other handlers in the
same component keep their errors, so independent forms can show independent
feedback. Call `$error()` without a name when a component-wide banner should
show the newest retained error.

The [event bindings guide](/events/bindings/) covers submit modifiers and the
other loading and error helpers. [Use event routes directly](/events/http/)
when the same form must also work without JavaScript.
