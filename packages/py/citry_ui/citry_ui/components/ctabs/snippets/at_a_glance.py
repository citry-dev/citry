import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsAtAGlance(Component):
    template = """
      <section class="tabs-sampler">
        <article class="tabs-sampler__card tabs-sampler__card--cosmic">
          <header>
            <p class="tabs-sampler__eyebrow">Deep-space radio</p>
            <h2>Europa Relay</h2>
          </header>

          <c-CTabs
            default_value="signals"
            aria_label="Europa Relay channels"
          >
            <c-CTab value="broadcast">
              Broadcast
            </c-CTab>
            <c-CTab value="signals">
              Signals
            </c-CTab>
            <c-CTab value="crew" disabled>
              Crew
            </c-CTab>

            <c-CTabPanel value="broadcast">
              <p>Now transmitting: a mixtape for whatever is out there.</p>
            </c-CTabPanel>
            <c-CTabPanel value="signals">
              <div class="tabs-sampler__metric">
                <strong>A repeating pulse crossed 1,200 light-years</strong>
                <span>Three notes, a pause, then whale song.</span>
              </div>
            </c-CTabPanel>
            <c-CTabPanel value="crew">
              <p>This relay is delightfully uncrewed.</p>
            </c-CTabPanel>
          </c-CTabs>
        </article>

        <article class="tabs-sampler__card tabs-sampler__card--greenhouse">
          <header>
            <p class="tabs-sampler__eyebrow">Lunar greenhouse</p>
            <h2>Habitat Seven</h2>
          </header>

          <c-CTabs
            default_value="crops"
            aria_label="Lunar greenhouse readings"
            variant="pill"
            density="comfortable"
            grow
          >
            <c-CTab value="crops">
              Crops
            </c-CTab>
            <c-CTab value="climate">
              Climate
            </c-CTab>
            <c-CTab value="supplies">
              Supplies
            </c-CTab>

            <c-CTabPanel value="crops">
              <div class="tabs-sampler__metric">
                <strong>Leafy greens are thriving</strong>
                <span>The blue-spectrum lamps run for six more hours.</span>
              </div>
            </c-CTabPanel>
            <c-CTabPanel value="climate">
              <p>Humidity is holding at 62% during the daylight cycle.</p>
            </c-CTabPanel>
            <c-CTabPanel value="supplies">
              <p>The next seed-vault delivery arrives in three orbits.</p>
            </c-CTabPanel>
          </c-CTabs>
        </article>
      </section>
    """

    css = """
      :where(.tabs-sampler) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-sampler__card) {
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid;
        border-radius: 0.875rem;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.tabs-sampler__card--cosmic) {
        --cui-tabs-accent: light-dark(#5b21b6, #ddd6fe);
        --cui-tabs-focus-color: light-dark(#6d28d9, #c4b5fd);
        --cui-tabs-active-background: light-dark(#ffffffb8, #2e1065b8);
        border-color: light-dark(#c4b5fd, #6d28d9);
        background: Canvas;
      }

      :where(.tabs-sampler__card--greenhouse) {
        --cui-tabs-accent: light-dark(#0f766e, #5eead4);
        --cui-tabs-focus-color: light-dark(#0d9488, #2dd4bf);
        --cui-tabs-active-background: light-dark(#f0fdf4cc, #042f2ecc);
        border-color: light-dark(#5eead4, #0f766e);
        background: Canvas;
      }

      :where(.tabs-sampler__card header) {
        margin-block-end: 1rem;
      }

      :where(.tabs-sampler__card h2, .tabs-sampler__card p) {
        margin-block: 0;
      }

      :where(.tabs-sampler__eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
      }

      :where(.tabs-sampler__metric) {
        display: grid;
        gap: 0.25rem;
      }

      :where(.tabs-sampler__metric span) {
        color: color-mix(in srgb, currentColor 72%, transparent);
      }
    """


preview = TabsAtAGlance()

preview  # noqa: B018
