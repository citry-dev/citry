# New in this step: every component uses the app's Citry instance.
from citry_setup import citry_app

from citry import Component


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

    template = """
      <section class="choice-picker" x-data="{ choice: 'Ocean' }">
        <p>
          Current choice:
          <output
            class="choice-picker__value"
            x-text="choice"
          ></output>
        </p>

        <c-ChoiceButton
          $c-props="{ label: choice }"
          @click="choice = choice === 'Ocean' ? 'Forest' : 'Ocean'"
        />
      </section>
    """


# New in this step: FastAPI will return this complete page.
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
