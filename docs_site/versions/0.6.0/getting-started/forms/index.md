---
title: Handle and validate forms
url: https://citry.dev/v/0.6.0/getting-started/forms/
description: "Turn named form controls into typed Python data and show field errors with Vue."
---
# Handle and validate forms

When a user submits a form, you want the fields as typed Python values. When
a value is wrong, you want the error next to the field, without clearing what
the user typed. In this step you build an email form that Python checks: it
rejects addresses outside `@example.com` and shows the error under the
field.

Replace `components.py` with this version. The signup form takes the
choice picker's place on the page; keep `citry_setup.py` and `app.py` as
they are:

```citry
from citry_setup import citry_app

from citry import Component
from citry.ext.events import EventError, actions


# New in this step: describe the named values sent by the form.
class SignupIn:
    email: str


# New in this step: Sign up form with server-side validation
class SignupForm(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    class Events:
        # Validate the form and return field errors
        def submit(self, data: SignupIn):
            email = data.email.strip()
            if not email.endswith("@example.com"):
                raise EventError(
                    "Please fix the email address.",
                    fields={"email": "Use an @example.com address."},
                )
            return actions.Dispatch(
                "SignupForm:sent",
                {"email": email},
            )

    template = """
      <section class="signup-form">
        <form @c-submit.prevent="submit">
          <label>
            Work email
            <input
              name="email"
              type="email"
              autocomplete="email"
              required
            />
            <span
              class="signup-form__error"
              role="alert"
              v-show="$error('submit')?.fieldErrors?.email"
              v-text="$error('submit')?.fieldErrors?.email || ''"
            ></span>
          </label>
          <button
            type="submit"
            :disabled="$loading('submit')"
            v-text="$loading('submit') ? 'Sending' : 'Send request'"
          >
            Send request
          </button>
        </form>
        <p role="status" v-show="acceptedEmail">
          Accepted <output v-text="acceptedEmail"></output>.
        </p>
      </section>
    """

    js = """
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
    """


class TutorialPage(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Join the reading room</title>
        </head>
        <body>
          <main>
            <h1>Join the reading room</h1>
            {# New in this step: place the form on the page. #}
            <c-SignupForm />
          </main>
        </body>
      </html>
    """

```

Submit `ada@elsewhere.test` to see the field error, then submit
`ada@example.com` to see the accepted address.

## Send the form


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

## Reject a value


```python
raise EventError(
    "Please fix the email address.",
    fields={"email": "Use an @example.com address."},
)
```


Raising [`EventError`](/v/0.6.0/reference/events/#citry-ext-events-eventerror) stops the handler and
sends the errors to the browser. The key in `fields` is the field name: it
matches both `SignupIn.email` and `name="email"`.

## Show error and progress

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

## Show the valid address

When the address is valid, the handler sends a browser event with it:


```python
return actions.Dispatch("SignupForm:sent", {"email": email})
```


As in the earlier steps, the event name starts with the component's name.

The component keeps the accepted address in its Vue data, and listens for
the event with [`onEvent`](/v/0.6.0/reference/browser-apis/#on-server-render-on-event) inside
[`onServerRender`](/v/0.6.0/reference/browser-apis/#on-server-render):


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

[Handle and validate forms](/v/0.6.0/events/forms/) in the Events guide covers
more, such as which Python type each kind of input sends.

## Next steps

Next, [replace the form with new HTML from Python](/v/0.6.0/getting-started/server-rendered-updates/).