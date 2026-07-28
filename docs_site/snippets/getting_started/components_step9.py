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
      <section
        class="choice-picker"
        x-data="{
          choices: [],
          choice: '',
          setNextChoice() {
            const choices = this.choices;
            const oldChoiceIndex = choices.indexOf(this.choice);
            const nextChoiceIndex =
              (oldChoiceIndex + 1) % choices.length;
            this.choice = choices[nextChoiceIndex];
          },
          loadChoices(newChoices) {
            this.choices = newChoices;
            this.choice = newChoices[0];
          },
        }"
        @choice-picker:loaded="loadChoices($event.detail.choices)"
      >
        {# New in this step: ask Python for the choices. #}
        <button
          type="button"
          :disabled="$loading('load_choices')"
          @c-click="load_choices"
        >
          Load choices
        </button>
        <span x-show="$loading('load_choices')">Loading...</span>

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

          {# New in this step: cycle through the loaded choices. #}
          <c-ChoiceButton
            $c-props="{ label: choice }"
            @click="setNextChoice"
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
