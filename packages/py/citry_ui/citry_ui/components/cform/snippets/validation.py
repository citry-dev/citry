import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NativeValidation(Component):
    template = """
      <section
        class="instrument-booking"
        x-data="{ accepted: false }"
      >
        <header>
          <p>Instrument desk</p>
          <h2>Book the spectrograph</h2>
        </header>

        <c-CForm
          @submit.prevent="accepted = true"
          @input="accepted = false"
        >
          <c-CField required>
            <c-fill name="label">
              Contact email
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="email"
                type="email"
                placeholder="observer@example.org"
              />
            </c-fill>
            <c-fill name="description">
              The browser checks the address before submission.
            </c-fill>
          </c-CField>
          <c-CField required>
            <c-fill name="label">
              Observation date
            </c-fill>
            <c-fill name="default" data="{ control_attrs }">
              <input
                class="instrument-booking__date"
                type="date"
                name="date"
                c-bind="control_attrs"
              />
            </c-fill>
          </c-CField>
          <c-CButton type="submit">
            Check availability
          </c-CButton>
        </c-CForm>

        <p
          class="instrument-booking__success"
          aria-live="polite"
          x-show="accepted"
        >
          The request is ready to send.
        </p>
      </section>
    """

    css = """
      :where(.instrument-booking) {
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.instrument-booking header) {
        margin-block-end: 1rem;
      }

      :where(.instrument-booking h2, .instrument-booking p) {
        margin-block: 0;
      }

      :where(.instrument-booking header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.instrument-booking__date) {
        inline-size: 100%;
        box-sizing: border-box;
        padding: 0.625rem 0.75rem;
        border: 1px solid light-dark(#9498bd, #686c96);
        border-radius: 0.5rem;
        background: Canvas;
        color: CanvasText;
        font: inherit;
      }

      :where(.instrument-booking form[data-validation-attempted] :invalid) {
        border-color: light-dark(#b42318, #ff8a80);
      }

      :where(.instrument-booking [data-citry-ui-part="button"]) {
        justify-self: start;
      }

      :where(.instrument-booking__success) {
        margin-block-start: 1rem;
        color: light-dark(#175c43, #7be0b5);
      }
    """


preview = NativeValidation()

preview  # noqa: B018
