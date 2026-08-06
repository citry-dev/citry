import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FieldInputAtAGlance(Component):
    template = """
      <section class="shore-glance">
        <article class="shore-glance__card">
          <header>
            <p>Morning survey</p>
            <h2>Log a tidepool sighting</h2>
          </header>

          <c-CField required>
            <c-fill name="label">
              Species
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="species"
                value="Ochre sea star"
                autocomplete="off"
              />
            </c-fill>
            <c-fill name="description">
              Use the common name from the shore guide.
            </c-fill>
          </c-CField>
        </article>

        <article class="shore-glance__card">
          <header>
            <p>Tide alert</p>
            <h2>Check the observation code</h2>
          </header>

          <c-CField invalid>
            <c-fill name="label">
              Observation code
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="observation_code"
                value="LOW-7"
                variant="filled"
              />
            </c-fill>
            <c-fill name="error">
              Codes contain three letters and three digits.
            </c-fill>
          </c-CField>
        </article>
      </section>
    """

    css = """
      :where(.shore-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        max-width: 62rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.shore-glance__card) {
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.shore-glance__card header) {
        margin-block-end: 1rem;
      }

      :where(.shore-glance__card h2, .shore-glance__card p) {
        margin-block: 0;
      }

      :where(.shore-glance__card header p) {
        margin-block-end: 0.35rem;
        color: light-dark(#08758a, #69d4e8);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }
    """


preview = FieldInputAtAGlance()

preview  # noqa: B018
