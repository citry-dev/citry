import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormAtAGlance(Component):
    template = """
      <section class="form-glance">
        <article class="form-glance__card">
          <header>
            <p>Night observation</p>
            <h2>Reserve telescope time</h2>
          </header>

          <c-CForm @submit.prevent="void 0">
            <c-CField required>
              <c-fill name="label">
                Target name
              </c-fill>
              <c-fill name="default">
                <c-CInput
                  name="target"
                  value="Andromeda Galaxy"
                />
              </c-fill>
              <c-fill name="description">
                Use a catalog or common name.
              </c-fill>
            </c-CField>
            <c-CButton type="submit">
              Request a window
            </c-CButton>
          </c-CForm>
        </article>

        <article class="form-glance__card">
          <header>
            <p>Calibration queue</p>
            <h2>Exposure sequence</h2>
          </header>

          <c-CForm submitting @submit.prevent="void 0">
            <c-CField readonly>
              <c-fill name="label">
                Filter sequence
              </c-fill>
              <c-fill name="default">
                <c-CInput
                  name="filters"
                  value="L · R · G · B"
                />
              </c-fill>
            </c-CField>
            <c-CButton type="submit" loading>
              Sending sequence
            </c-CButton>
          </c-CForm>
        </article>
      </section>
    """

    css = """
      :where(.form-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.form-glance__card) {
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.form-glance__card header) {
        margin-block-end: 1rem;
      }

      :where(.form-glance__card h2, .form-glance__card p) {
        margin-block: 0;
      }

      :where(.form-glance__card header p) {
        margin-block-end: 0.35rem;
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.form-glance__card [data-citry-ui-part="button"]) {
        justify-self: start;
      }
    """


preview = FormAtAGlance()

preview  # noqa: B018
