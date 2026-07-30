---
title: Handle and validate a form
url: https://citry.dev/v/0.3.0/getting-started/forms/
description: "Turn named form controls into typed Python data and return a useful field error."
---
# Handle and validate a form

Buttons are only one way to call Python. A Citry event can also receive the
named values from a form.

You will add an email form, reject the wrong domain in Python, and show the
field error beside the input without clearing what the reader typed.

Continue from [Keep a value between
calls](/getting-started/state/). Keep `citry_setup.py` and `app.py` unchanged.

## Add the form

Replace `components.py` with this version:

The choice components are carried over unchanged. Follow the `New in this
step` comments from `SignupIn`, through `SignupForm`, to the line that places
the form on `TutorialPage`.

```citry
from citry_setup import citry_app

from citry import Component
from citry.ext.events import EventError, actions

CHOICE_BATCHES = (
    ("Ocean", "Forest"),
    ("History", "Science"),
)


def load_choices_from_database(batch: int) -> list[str]:
    choices = CHOICE_BATCHES[batch % len(CHOICE_BATCHES)]
    return list(choices)


class ChoiceButton(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <button class="choice-button" type="button">
        Choose
        <span
          class="choice-button__label"
          x-text="clientProps.label"
        ></span>
      </button>
    """

    js = """
      $component({
        props: {
          label: { type: String, required: true },
        },
        init: ({ props, scope }) => {
          scope.clientProps = props;
        },
      });
    """


class ChoicePicker(Component):
    citry = citry_app

    class Kwargs:
        batches_loaded: int = 0

    class Slots:
        pass

    class State(Kwargs):
        pass

    class Events:
        def load_choices(self, state):
            choices = load_choices_from_database(state.batches_loaded)
            state.batches_loaded += 1
            return actions.Dispatch(
                "choice-picker:loaded",
                {
                    "choices": choices,
                    "batches_loaded": state.batches_loaded,
                },
            )

    template = """
      <section
        class="choice-picker"
        c-x-data="{
          'choices': [],
          'choice': '',
          'batchesLoaded': batches_loaded,
        }"
        @choice-picker:loaded="
          choices = $event.detail.choices;
          choice = choices[0];
          batchesLoaded = $event.detail.batches_loaded;
        "
      >
        <button
          type="button"
          :disabled="$loading('load_choices')"
          @c-click="load_choices"
        >
          Load choices
        </button>
        <span x-show="$loading('load_choices')">Loading...</span>
        <p>
          Sets loaded:
          <output x-text="batchesLoaded">
            {{ batches_loaded }}
          </output>
        </p>

        <p x-show="choices.length === 0">
          No choices loaded yet.
        </p>
        <div x-show="choices.length > 0">
          <p>
            Current choice:
            <output
              class="choice-picker__value"
              x-text="choice"
            ></output>
          </p>

          <c-ChoiceButton
            $c-props="{ label: choice }"
            @click="
              choice = choices[
                (choices.indexOf(choice) + 1) % choices.length
              ]
            "
          />
        </div>
      </section>
    """


# New in this step: describe the named values sent by the form.
class SignupIn:
    email: str


# New in this step: validate the form and return field errors.
class SignupForm(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    class Events:
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
              x-show="$error?.fieldErrors?.email"
              x-text="$error?.fieldErrors?.email || ''"
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
          <title>Reading room</title>
        </head>
        <body>
          <main>
            <h1>Reading room</h1>
            <c-ChoicePicker />
            {# New in this step: place the form on the page. #}
            <c-SignupForm />
          </main>
        </body>
      </html>
    """

```

Open `http://127.0.0.1:8000/` and enter `ada@elsewhere.test`. The address is
valid enough for the browser, so the form reaches Python. Citry then shows
“Use an @example.com address.” below the input.

Change the value to `ada@example.com` and submit again. The page reports that
the address was accepted.

## Send named controls to Python

The form calls the `submit` handler instead of performing the browser's usual
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

## Describe the data Python receives

`SignupIn` names the fields expected by the handler:


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

## Reject input in Python

The handler checks the cleaned address and raises
[`EventError`](/v/0.3.0/reference/events/#citry-ext-events-eventerror) when the domain is wrong:


```python
if not email.endswith("@example.com"):
    raise EventError(
        "Please fix the email address.",
        fields={"email": "Use an @example.com address."},
    )
```


The first string is the overall error message, available as
[`$error.message`](/v/0.3.0/reference/browser-apis/#error) if you want a message for the whole form. The
[`fields`](/v/0.3.0/reference/events/#citry-ext-events-eventerror-fields) mapping adds messages for
specific inputs. Its `email` key matches both `SignupIn.email` and the input's
`name="email"`.

## Show the error beside the input

The span beside the input reads that field message from `$error`:


```citry-html
<span
  class="signup-form__error"
  role="alert"
  x-show="$error?.fieldErrors?.email"
  x-text="$error?.fieldErrors?.email || ''"
></span>
```


Before an error occurs, `$error` is empty and the span stays hidden. After the
failed call, `fieldErrors.email` contains “Use an @example.com address.” The
form itself remains in place, so the input keeps the address that needs fixing.

## Show while the request is running

The submit button reads the same handler name through
[`$loading('submit')`](/v/0.3.0/reference/browser-apis/#loading):


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


The success path updates Alpine data, so it does not need new HTML from
Python. The next lesson will keep the same form and change only that success
result.

Python type hints describe the expected input shape. Continue to validate
untrusted values and check permissions in the handler before changing data or
calling another service. The [Forms guide](/v/0.3.0/events/forms/) covers larger input
shapes and validation patterns.

## Return new HTML

An event does not have to stop at an error or browser event. Next, [replace
part of the page from Python](/getting-started/server-rendered-updates/).