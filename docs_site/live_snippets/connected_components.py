from citry import Component


class ChoiceButton(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      {# 'x-text' shows current value, as given by parent #}
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
        // Declare the browser value ChoiceButton accepts
        // through '$c-props'.
        props: {
          label: { type: String, required: true },
        },
        init: ({ props, scope }) => {
          // Share the reactive prop with Alpine.
          scope.clientProps = props;
        },
      });
    """


class ChoicePicker(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      {# 'choice' lives in the parent's 'x-data'  #}
      <section class="choice-picker" x-data="{ choice: 'Ocean' }">
        <p>
          Current choice:
          <output
            class="choice-picker__value"
            x-text="choice"
          ></output>
        </p>

        {# `$c-props` passes 'choice' down as browser data. #}
        {# `@click` allows parent to react to child's click. #}
        <c-ChoiceButton
          $c-props="{ label: choice }"
          @click="choice = choice === 'Ocean' ? 'Forest' : 'Ocean'"
        />
      </section>
    """


class ChoicePage(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Connect components</title>
        </head>
        <body>
          <c-ChoicePicker />
        </body>
      </html>
    """


page = ChoicePage()

if __name__ == "__main__":
    print(page)

page
