from citry_setup import citry_app

from citry import Component
from citry.ext.events import actions


# New in this step: stand in for a database query.
def load_choices_from_database() -> list[str]:
    return ["Ocean", "Forest"]


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

    class Kwargs:
        pass

    class Slots:
        pass

    # New in this step: handle the button click in Python.
    class Events:
        # Method name matches @c-click.
        def load_choices(self):
            choices = load_choices_from_database()
            # Tell the client to dispatch a custom browser event
            # with the loaded choices.
            return actions.Dispatch(
                "choice-picker:loaded",
                {"choices": choices},
            )

    template = """
      <section class="choice-picker">
        {# New in this step: ask Python for the choices. #}
        <button
          type="button"
          :disabled="$loading('load_choices')"
          @c-click="load_choices"
        >
          Load choices
        </button>
        <span v-show="$loading('load_choices')">Loading...</span>

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

          {# New in this step: cycle through the loaded choices. #}
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
          setNextChoice() {
            const oldChoiceIndex = this.choices.indexOf(this.choice);
            this.choice = this.choices[
              (oldChoiceIndex + 1) % this.choices.length
            ];
          },
          loadChoices(newChoices) {
            this.choices = newChoices;
            this.choice = newChoices[0];
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
