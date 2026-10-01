from citry import Component


class ChoiceButton(Component):
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
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="choice-picker">
        <p>
          Current choice:
          <output
            class="choice-picker__value"
            v-text="choice"
          ></output>
        </p>

        <c-ChoiceButton
          :label="choice"
          @select="toggleChoice"
        />
      </section>
    """

    js = """
      $component({
        data() {
          return { choice: 'Ocean' };
        },
        methods: {
          toggleChoice() {
            this.choice = this.choice === 'Ocean' ? 'Forest' : 'Ocean';
          },
        },
      });
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
