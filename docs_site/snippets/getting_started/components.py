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
