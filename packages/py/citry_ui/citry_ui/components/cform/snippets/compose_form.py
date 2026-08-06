import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ComposeForm(Component):
    template = """
      <section class="orbit-request" x-data="{ saved: '' }">
        <header>
          <p>Orbital survey</p>
          <h2>Queue a tracking request</h2>
        </header>

        <c-CForm
          id="orbit-request-form"
          action="/tracking-requests"
          method="post"
          autocomplete="off"
          @submit.prevent="saved = new FormData($el).get('object')"
        >
          <c-CField required>
            <c-fill name="label">
              Object designation
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="object"
                value="2024 YR4"
              />
            </c-fill>
          </c-CField>
          <c-CButton type="submit">
            Queue tracking
          </c-CButton>
        </c-CForm>

        <p aria-live="polite" x-show="saved">
          Queued <strong x-text="saved"></strong>
        </p>
      </section>
    """

    css = """
      :where(.orbit-request) {
        max-width: 38rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.orbit-request header) {
        margin-block-end: 1rem;
      }

      :where(.orbit-request h2, .orbit-request p) {
        margin-block: 0;
      }

      :where(.orbit-request header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.orbit-request form > fieldset > [data-citry-ui-part="button"]) {
        justify-self: start;
      }

      :where(.orbit-request > p) {
        margin-block-start: 1rem;
        color: light-dark(#175c43, #7be0b5);
      }
    """


preview = ComposeForm()

preview  # noqa: B018
