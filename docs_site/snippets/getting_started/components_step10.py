from citry_setup import citry_app

from citry import Component
from citry.ext.events import actions

# New in this step: simulate two database query results.
# Based on value from State, we return one of these two
# batches of choices.
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

    # New in this step: set the counter for the first render.
    class Kwargs:
        batches_loaded: int = 0

    class Slots:
        pass

    # New in this step: carry the counter between Python calls.
    class State:
        batches_loaded: int = 0

    class Events:
        def load_choices(self, state):
            # New in this step: read and advance the signed State.
            # NOTE: State is passed to the event handler.
            #       You can mutate the State, and it will be
            #       signed and sent back to the client.
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
      {# New in this step: pass Python `batches_loaded` to JS. #}
      {# `c-x-data` sets the first browser value. #}
      {# The listener applies later values returned by Python. #}
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

        {# New in this step: show the counter from Python. #}
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
          </main>
        </body>
      </html>
    """
