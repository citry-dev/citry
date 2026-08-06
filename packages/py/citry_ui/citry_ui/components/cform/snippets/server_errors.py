import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ServerErrors(Component):
    template = """
      <section
        class="account-request"
        x-data="{
          error: 'That observer handle is already registered.',
        }"
      >
        <header>
          <p>Observer network</p>
          <h2>Request an observatory account</h2>
        </header>

        <c-CForm @submit.prevent="void 0">
          <c-CField
            $c-props="{
              invalid: Boolean(
                Alpine.$data($root.closest('.account-request')).error
              ),
            }"
          >
            <c-fill name="label">
              Observer handle
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="handle"
                value="night-heron"
                @input="Alpine.$data($root.closest('.account-request')).error = ''"
              />
            </c-fill>
            <c-fill name="error">
              <span
                x-text="Alpine.$data($root.closest('.account-request')).error"
              ></span>
            </c-fill>
          </c-CField>
          <c-CButton type="submit">
            Request account
          </c-CButton>
        </c-CForm>

        <p class="account-request__hint">
          The application clears this server message when the rejected field changes.
        </p>
      </section>
    """

    css = """
      :where(.account-request) {
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.account-request header) {
        margin-block-end: 1rem;
      }

      :where(.account-request h2, .account-request p) {
        margin-block: 0;
      }

      :where(.account-request header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.account-request [data-citry-ui-part="button"]) {
        justify-self: start;
      }

      :where(.account-request__hint) {
        margin-block-start: 1rem;
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.875rem;
      }
    """


preview = ServerErrors()

preview  # noqa: B018
