---
title: Handle and validate forms
url: https://citry.dev/v/0.4.0/getting-started/forms/
description: "Turn named form controls into typed Python data and return a useful field error."
---
# Handle and validate forms

Buttons are only one way to call Python. A Citry event can also receive the
named values from a form.

You will build an email form, reject the wrong domain in Python, and show the
field error beside the input without clearing what the reader typed.

Continue from [Keep a value between
calls](/getting-started/state/). Keep `citry_setup.py` and `app.py` unchanged.

## Add the form

Replace `components.py` with this version. Here we replace the ChoicePicker with a sign-in form:

```citry
from citry import Component
from citry.ext.events import EventError, actions

from citry_setup import citry_app


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
                "signup:sent",
                {"email": email},
            )

    template = """
      <section
        class="signup-form"
        x-data="{ acceptedEmail: '' }"
        @signup:sent="acceptedEmail = $event.detail.email"
      >
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
              x-show="$error('submit')?.fieldErrors?.email"
              x-text="$error('submit')?.fieldErrors?.email || ''"
            ></span>
          </label>
          <button
            type="submit"
            :disabled="$loading('submit')"
            x-text="$loading('submit') ? 'Sending' : 'Send request'"
          >
            Send request
          </button>
        </form>
        <p role="status" x-show="acceptedEmail">
          Accepted <output x-text="acceptedEmail"></output>.
        </p>
      </section>
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

Open `http://127.0.0.1:8000/` and enter `ada@elsewhere.test`. The address is
valid enough for the browser, so the form reaches Python. Citry then shows
“Use an `@example.com` address.” below the input.

Change the value to `ada@example.com` and submit again. The page reports that
the address was accepted.

## Submit form to event handler

The form calls the `submit` Python event handler instead of performing the browser's usual
full-page submission:


```citry-html
<form @c-submit.prevent="submit">
  <label>
    Work email
    <input
      name="email"
      type="email"
      autocomplete="email"
      required
    />
  </label>
  ...
</form>
```


The `.prevent` modifier stops the usual page navigation. Citry collects the
form's named controls and sends them to Python. Here, `name="email"` gives the
typed value its field name.

The browser checks that the input looks like an email address and is not empty.
The application-specific `@example.com` rule still belongs in Python.

## Declare form data

On the server, `SignupIn` names the fields expected by the handler:


```python
class SignupIn:
    email: str

class Events:
    def submit(self, data: SignupIn):
        email = data.email.strip()
```


The input's `name="email"` matches `SignupIn.email`, so the handler can read
`data.email`. A larger form can add more named controls and matching fields to
the input class.

The Python type hint `SignupIn` describes the expected input shape. The [Forms guide](/v/0.4.0/events/forms/) covers larger input
shapes and validation patterns.

## Reject input in Python

The handler checks the cleaned address and raises
[`EventError`](/v/0.4.0/reference/events/#citry-ext-events-eventerror) when the domain is wrong:


```python
if not email.endswith("@example.com"):
    raise EventError(
        "Please fix the email address.",
        fields={"email": "Use an @example.com address."},
    )
```


The first string is the overall error message, available as
[`$error('submit')?.message`](/v/0.4.0/reference/browser-apis/#error) if you want a message for the whole
form. The
[`fields`](/v/0.4.0/reference/events/#citry-ext-events-eventerror-fields) mapping adds messages for
specific inputs. Its `email` key matches both `SignupIn.email` and the input's
`name="email"`.

## Show handler error in UI

The span beside the input reads that field message from `$error('submit')`:


```citry-html
<span
  class="signup-form__error"
  role="alert"
  x-show="$error('submit')?.fieldErrors?.email"
  x-text="$error('submit')?.fieldErrors?.email || ''"
></span>
```


Before an error occurs, `$error('submit')` returns `null` and the span stays
hidden. After the failed call, `fieldErrors.email` contains `"Use an
@example.com address."` The form itself remains in place, so the input keeps
the address that needs fixing. Naming the handler matters when one component
contains several forms: a successful call clears only that handler's error.

## Show handler loading in UI

The submit button reads the same handler name through
[`$loading('submit')`](/v/0.4.0/reference/browser-apis/#loading):


```citry-html
<button
  type="submit"
  :disabled="$loading('submit')"
  x-text="$loading('submit') ? 'Sending' : 'Send request'"
>
  Send request
</button>
```


While `submit` is running, the button is disabled and its label changes to
“Sending.” This prevents an accidental second submission and tells the person
that the first one is still being handled.

## Handle success in the browser

A valid address returns another browser event:


```python
return actions.Dispatch(
    "signup:sent",
    {"email": email},
)
```


The form's root listens for that event and keeps the returned address in
Alpine:


```citry-html
<section
  x-data="{ acceptedEmail: '' }"
  @signup:sent="acceptedEmail = $event.detail.email"
>
  ...
  <p role="status" x-show="acceptedEmail">
    Accepted <output x-text="acceptedEmail"></output>.
  </p>
</section>
```


The listener is on the `SignupForm` root on purpose. [`Dispatch`](/v/0.4.0/reference/events/#citry-ext-events-actions-dispatch) fires the
bubbling event from that first root, so the root receives it. Moving
`@signup:sent` inside the `<form>` would not work because the event does not
bubble down into descendants. When root placement is awkward, use
[`$onEvent`](/v/0.4.0/reference/browser-apis/#on-event) or the `onEvent` member from
[`$component`](/v/0.4.0/reference/browser-apis/#component) to listen by component instance instead. The
[event actions guide](/v/0.4.0/events/actions/#choose-where-to-listen-for-dispatch)
explains the complete targeting rules.

Using `$component` would have looked like this:


```js
$component(({ onEvent, scope }) => {
  // Set initial Alpine state, replaces root x-data
  scope.acceptedEmail = '';

  // Update Alpine state on server event
  onEvent('signup:sent', (detail) => {
    scope.acceptedEmail = detail.email;
  });
});
```


The success path updates Alpine data, so it does not need new HTML from
Python. The next lesson will keep the same form and change only that success
result.

## Next steps

An event does not have to stop at an error or browser event. Next, [replace
part of the page from Python](/getting-started/server-rendered-updates/).