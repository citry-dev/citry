import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonNativeForms(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section
        class="button-form"
        x-data="{ result: 'No sighting recorded yet.' }"
      >
        <header>
          <p>Field journal</p>
          <h2>Record a woodland sighting</h2>
        </header>

        <form
          @submit.prevent="result = `Recorded with ${$event.submitter.value}.`"
          @reset="result = 'Journal reset.'"
        >
          <label for="button-form-species">Species</label>
          <input
            id="button-form-species"
            name="species"
            value="Silver-washed fritillary"
          />
          <div>
            <c-CButton
              type="submit"
              intent="success"
              c-attrs="submit_attrs"
            >
              Record sighting
            </c-CButton>
            <c-CButton type="reset" variant="ghost" intent="neutral">
              Reset journal
            </c-CButton>
          </div>
        </form>

        <p class="button-form__result" aria-live="polite" x-text="result">
          No sighting recorded yet.
        </p>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "submit_attrs": {
                "name": "observation_action",
                "value": "field journal",
            }
        }

    css = """
      :where(.button-form) {
        max-width: 34rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bbd6c5, #355e48);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-form header) {
        margin-block-end: 1rem;
      }

      :where(.button-form h2, .button-form p) {
        margin-block: 0;
      }

      :where(.button-form header p) {
        margin-block-end: 0.35rem;
        color: light-dark(#19704a, #74d9a3);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.button-form form) {
        display: grid;
        gap: 0.65rem;
      }

      :where(.button-form label) {
        font-weight: 650;
      }

      :where(.button-form input) {
        box-sizing: border-box;
        inline-size: 100%;
        min-block-size: 2.5rem;
        padding: 0.55rem 0.7rem;
        border: 1px solid color-mix(in srgb, currentColor 32%, transparent);
        border-radius: 0.5rem;
        background: Field;
        color: FieldText;
        font: inherit;
      }

      :where(.button-form form > div) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.65rem;
        margin-block-start: 0.35rem;
      }

      :where(.button-form__result) {
        margin-block-start: 1rem;
        color: color-mix(in srgb, currentColor 72%, transparent);
      }
    """


preview = ButtonNativeForms()

preview  # noqa: B018
