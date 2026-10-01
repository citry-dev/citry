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
      <button class="choice-button" type="button" @click="$emit('select')">
        Choose
        <span
          class="choice-button__label"
          v-text="label"
        ></span>
      </button>
    """

    js = """
      $component({
        props: {
          label: { type: String, required: true },
        },
        emits: ['select'],
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
                },
            )

    template = """
      <section class="choice-picker">
        <button
          type="button"
          :disabled="$loading('load_choices')"
          @c-click="load_choices"
        >
          Load choices
        </button>
        <span v-show="$loading('load_choices')">Loading...</span>

        {# New in this step: show the counter from Python. #}
        <p>
          Sets loaded:
          <output v-text="$state.batches_loaded">
            {{ batches_loaded }}
          </output>
        </p>

        <p v-show="choices.length === 0">
          No choices loaded yet.
        </p>
        <div v-show="choices.length > 0">
          <p>
            Current choice:
            <output
              class="choice-picker__value"
              v-text="choice"
            ></output>
          </p>

          <c-ChoiceButton
            :label="choice"
            @select="setNextChoice"
          />
        </div>
      </section>
    """

    js = """
      $component({
        data() {
          return { choices: [], choice: '' };
        },
        methods: {
          loadChoices(newChoices) {
            this.choices = newChoices;
            this.choice = newChoices[0];
          },
          setNextChoice() {
            const oldChoiceIndex = this.choices.indexOf(this.choice);
            this.choice = this.choices[
              (oldChoiceIndex + 1) % this.choices.length
            ];
          },
        },
        onServerRender({ component }) {
          const receiveChoices = (event) => {
            component.loadChoices(event.detail.choices);
          };
          component.$el.addEventListener('choice-picker:loaded', receiveChoices);
          return () => {
            component.$el.removeEventListener('choice-picker:loaded', receiveChoices);
          };
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
