import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonLoadingStates(Component):
    template = """
      <section
        class="button-loading"
        x-data="{ scanning: false }"
      >
        <article class="button-loading__interactive">
          <div>
            <p>Interactive pending state</p>
            <h2>Listen for woodland birds</h2>
          </div>
          <c-CButton
            $c-props="{ loading: scanning }"
            @click="scanning = true; setTimeout(() => { scanning = false }, 2400)"
          >
            Begin listening
          </c-CButton>
          <span aria-live="polite" x-text="scanning ? 'Listening…' : 'Ready'"></span>
        </article>

        <div class="button-loading__positions">
          <c-CButton loading loading_pos="start" variant="outline">
            <c-fill name="start">
              <span aria-hidden="true">✿</span>
            </c-fill>
            <c-fill name="default">
              Identifying spores
            </c-fill>
          </c-CButton>
          <c-CButton loading loading_pos="center">
            Mapping the trail
          </c-CButton>
          <c-CButton loading loading_pos="end" variant="outline">
            <c-fill name="default">
              Tracing migration
            </c-fill>
            <c-fill name="end">
              <span aria-hidden="true">→</span>
            </c-fill>
          </c-CButton>
          <c-CButton loading intent="success">
            <c-fill name="loading">
              <span aria-hidden="true">✺</span>
            </c-fill>
            <c-fill name="default">
              Pressing specimen
            </c-fill>
          </c-CButton>
          <c-CButton disabled intent="neutral" variant="outline">
            Trail unavailable
          </c-CButton>
        </div>
      </section>
    """

    css = """
      :where(.button-loading) {
        display: grid;
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-loading__interactive) {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 0.75rem 1rem;
        align-items: center;
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#bbd6c5, #355e48);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.button-loading__interactive h2, .button-loading__interactive p) {
        margin-block: 0;
      }

      :where(.button-loading__interactive p) {
        margin-block-end: 0.3rem;
        color: light-dark(#19704a, #74d9a3);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.button-loading__interactive > span) {
        grid-column: 1 / -1;
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.8125rem;
      }

      :where(.button-loading__positions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
        padding: 1rem;
        border: 1px solid light-dark(#d5ddd8, #40594b);
        border-radius: 0.75rem;
        background: Canvas;
      }

      @media (max-width: 34rem) {
        :where(.button-loading__interactive) {
          grid-template-columns: minmax(0, 1fr);
        }
      }
    """


preview = ButtonLoadingStates()

preview  # noqa: B018
