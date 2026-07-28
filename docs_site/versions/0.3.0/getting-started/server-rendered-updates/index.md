---
title: Replace part of the page from Python
url: https://citry.dev/v/0.3.0/getting-started/server-rendered-updates/
description: "Render a new component into one chosen part of the page, including the component's JavaScript and CSS."
---
# Replace part of the page from Python

The form currently reports success by changing a line of text in the browser.
For the final step, Python will render a new `Confirmation` component into the
result area.

The form itself will stay where it is. Only the chosen part of the page will
change.

Continue from [Handle and validate a
form](/getting-started/forms/). Keep `citry_setup.py` and `app.py` unchanged.

## Return a rendered update

Replace `components.py` with the finished version:

The `New in this step` comments mark the complete change: the new
`Confirmation` component, the form's new success action and result area, and
the two places where the page collects component CSS and JavaScript.

```citry
"""The completed Getting started server application."""

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


# New in this step: render this component after a valid form.
class Confirmation(Component):
    citry = citry_app

    class Kwargs:
        email: str

    class Slots:
        pass

    class JsData:
        email: str

    def js_data(self, kwargs: Kwargs, slots: Slots) -> JsData:
        return self.JsData(email=kwargs.email)

    template = """
      <section class="confirmation">
        <strong>Request received</strong>
        <p>We will write to {{ email }}.</p>
        <p class="confirmation__status">
          Preparing confirmation...
        </p>
      </section>
    """

    js = """
      $component(({ els, data }) => {
        els[0].querySelector(".confirmation__status").textContent =
          `Confirmation ready for ${data.email}`;
      });
    """

    css = """
      .confirmation {
        border: 2px solid #2f855a;
        border-radius: 0.5rem;
        padding: 1rem;
      }
    """


class SignupIn:
    email: str


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
            # New in this step: replace the result area's contents.
            return actions.Render(
                Confirmation(email=email),
                target="#signup-result",
                swap="inner",
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
        {# New in this step: give Render a stable target. #}
        <div id="signup-result" aria-live="polite">
          <p>Your confirmation will appear here.</p>
        </div>
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
          {# New in this step: place collected component CSS. #}
          <c-css />
        </head>
        <body>
          <main>
            <h1>Reading room</h1>
            <c-ChoicePicker />
            <c-SignupForm />
          </main>
          {# New in this step: place collected component JS. #}
          <c-js />
        </body>
      </html>
    """

```

Open `http://127.0.0.1:8000/`. Try `ada@elsewhere.test` once more to confirm
that the field error still works. Then submit `ada@example.com`.

The placeholder inside the result area becomes a bordered confirmation. Its
status changes to “Confirmation ready for ada@example.com.” The email form
remains above it.

## Build the component Python will return

`Confirmation` is an ordinary component. Focusing only on its input and
visible HTML, it looks like this:


```citry
class Confirmation(Component):
    class Kwargs:
        email: str

    template = """
      <section class="confirmation">
        <strong>Request received</strong>
        <p>We will write to {{ email }}.</p>
        <p class="confirmation__status">
          Preparing confirmation...
        </p>
      </section>
    """
```


The complete class above also includes its Citry instance, `Slots`, browser
data, JavaScript, and CSS. This smaller excerpt shows the first connection:
`Confirmation(email=email)` supplies the value that `{{ email }}` prints.

## Return the component from the handler

The successful handler now returns an
[`actions.Render`](/v/0.3.0/reference/events/#citry-ext-events-actions-render) action:


```python
return actions.Render(
    Confirmation(email=email),
    target="#signup-result",
    swap="inner",
)
```


`Confirmation(email=email)` builds a fresh component for this response. Citry
renders it as a browser update, including the information needed for that
component's CSS and JavaScript. The validation path still raises the same
`EventError`; only a successful submission reaches this return statement.

## Choose the part of the page to update

The form contains a stable result area:


```citry-html
<div id="signup-result" aria-live="polite">
  <p>Your confirmation will appear here.</p>
</div>
```


[`target="#signup-result"`](/v/0.3.0/reference/events/#citry-ext-events-actions-render-target) points to
that element with a CSS selector.
[`swap="inner"`](/v/0.3.0/reference/events/#citry-ext-events-actions-render-swap) replaces its contents
while keeping the `<div id="signup-result">` itself. The form, input, and
button remain where they are. `aria-live="polite"` also lets assistive
technology announce the new confirmation without moving keyboard focus.

Use a selector that identifies the intended area without matching unrelated
elements.

## Give the new component browser data

The confirmation sends its email address to browser code through
[`js_data()`](/v/0.3.0/reference/component/#citry-component-js-data):


```python
class JsData:
    email: str


def js_data(self, kwargs: Kwargs, slots: Slots) -> JsData:
    return self.JsData(email=kwargs.email)
```


The [`$component`](/v/0.3.0/reference/browser-apis/#component) callback receives that value as `data.email`:


```javascript
$component(({ els, data }) => {
  els[0].querySelector(".confirmation__status").textContent =
    `Confirmation ready for ${data.email}`;
});
```


When the new component starts, this changes “Preparing confirmation...” to the
finished status. As with the browser data from the earlier lesson, the value
returned by `js_data()` must be JSON-serializable.

## Bring the component's styles and script

`Confirmation` also owns the border that makes the new result visible:


```css
.confirmation {
  border: 2px solid #2f855a;
  border-radius: 0.5rem;
  padding: 1rem;
}
```


The full page provides places for component CSS and JavaScript:


```citry-html
<head>
  ...
  <c-css />
</head>
<body>
  ...
  <c-js />
</body>
```


[`<c-css />`](/v/0.3.0/reference/builtins/#c-css) and [`<c-js />`](/v/0.3.0/reference/builtins/#c-js) place the assets needed by
components in the first response. Earlier pages worked without these tags
because Citry can choose the usual document positions automatically. Adding
the tags makes the positions explicit.

`Confirmation` is created later, so its assets arrive with the rendered
update, not through the two tags in the first response. Citry loads them before
the new component starts. That is why the green border appears and the status
changes after the confirmation enters the page.

See [Event actions](/v/0.3.0/events/actions/) for the other results a handler can
return, and [HTML fragments](/v/0.3.0/advanced/html-fragments/) for a deeper look at
rendering and inserting partial HTML.

## Keep building

You have now used Citry from both sides of the connection. Python rendered the
first page, browser data handled instant changes, server events called typed
Python handlers, State continued across calls, form errors came back beside
their fields, and a final handler replaced one part of the page with a new
component.

From here:

- use [Examples](/v/0.3.0/examples/) when you want working code for a specific task;
- read [Docs](/v/0.3.0/getting-started/installation/) when you want a concept or guided
  workflow; or
- open [Reference](/v/0.3.0/reference/) when you need the exact API for a class,
  method, or return action.