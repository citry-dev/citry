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

## Receive form data

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

The form's fields are sent only when the binding names the handler alone,
as in `submit` or `submit()`. Arguments you write, as in
`submit({draft: true})`, are sent instead of the fields.

A `name` that the data class does not declare fails each submit that
sends the control. With your application loaded, `citry check` and the
editor report such a `name`, and a required field that no control in the
form sends ([form fields](/ide/template-linting/#check-form-fields)).

### Form field types

Every control sends its text, and Citry converts the text to the field's
type the same way as for a form posted without JavaScript:

| Control | Text sent | Declare the field as |
|---|---|---|
| `<input type="number">`, `<input type="range">` | `"3"` or `"2.5"` | `int` or `float` |
| A checked checkbox without a `value` | `"on"` | `bool = False` |
| An unchecked checkbox | nothing | `bool = False` |
| A `<select>` whose options are numbers | `"2"` | `int` |
| Other inputs, `<select>`, `<textarea>` | the text | `str` |

An unchecked checkbox sends nothing at all, so give a `bool` field a default
of `False`, or a form with the box unchecked fails because the field is
missing. A checkbox with its own `value` sends that text, so for a `bool`
field leave `value` out or use `"true"` or `"1"`.

An empty input sends empty text, which an `int`, `float`, or `bool` field
rejects, even one declared as `int | None`. Add `required` to the input, or
declare the field as `str` and convert it in the handler.

The submit button that sent the form adds its own `name` and `value`, if
it has a `name`, so `<button name="action" value="save">` sends
`action="save"`. An image button, `<input type="image">`, sends where it
was clicked as `x` and `y` instead, which a data class does not declare,
so use a `<button>` with an image inside it.

The form's fields are sent only when the binding names the handler alone,
as in `submit` or `submit()`. Arguments you write, as in
`submit({draft: true})`, are sent instead of the fields.

## `EventError` field errors

Raise [`EventError`][citry.ext.events.EventError] with a message and an error
per field. When a call fails, nothing re-renders, so the form keeps what the
user typed.

[`$error('submit')`][$error] returns the last error from the `submit` handler,
or `null`. Its `fieldErrors` uses the field names you passed to `EventError`:

```citry-html
<span v-text="$error('submit')?.fieldErrors?.email"></span>
```

When a call sends fields the `data` class does not declare, `fieldErrors`
lists at most 20 of them, and `message` ends with how many more there
were. Errors for declared fields are always listed in full.

A later successful `submit` call clears the error. Errors from other
handlers in the same component are separate, so two forms in one component
show their own errors. To show one banner for the whole component, call
`$error()` without a name: it returns the newest error from any handler.

## `$loading` while sending

[`$loading('submit')`][$loading] is true from the moment the user submits
until the response arrives, including any time spent waiting behind other
calls:

```citry-html
<button type="submit" :disabled="$loading('submit')">
  Send
</button>
```

## Related pages

- [Bind events in templates](/events/bindings/) covers the other modifiers
  and the loading and error helpers.
- [Event routes](/events/routes/#keep-a-form-working-without-javascript)
  shows how to make the same form work without JavaScript.

!!! note "Errors when you call a handler from JavaScript"

    When the server returns an error for an `@c-*` call, the error appears
    in `$error()` and nothing else happens. When your own code calls a
    handler with `$sendEvent(...)`, a failed call also rejects the returned
    Promise, so catch it with `try`/`catch` or `.catch(...)`.
