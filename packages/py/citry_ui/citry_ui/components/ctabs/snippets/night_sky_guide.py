import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NightSkyGuide(Component):
    template = """
      <section
        class="night-sky-guide"
        x-data="{ selected: 'planets' }"
      >
        <header>
          <p class="night-sky-guide__eyebrow">Field guide</p>
          <h2>The night sky</h2>
          <p>
            Current topic:
            <output x-text="selected">planets</output>
          </p>
        </header>

        <c-CTabs
          default_value="planets"
          aria_label="Night sky topics"
          variant="pill"
          grow
          $c-props="{
            onValueChange: (value) => {
              selected = value;
            },
          }"
        >
          <c-CTab value="planets">
            Planets
          </c-CTab>
          <c-CTab value="nebulae">
            Nebulae
          </c-CTab>
          <c-CTab value="galaxies">
            Galaxies
          </c-CTab>

          <c-CTabPanel value="planets">
            <h3>Finding planets</h3>
            <p>Look for steady points of light. Planets usually twinkle less than stars.</p>
          </c-CTabPanel>
          <c-CTabPanel value="nebulae">
            <h3>Finding nebulae</h3>
            <p>Dark skies and a telescope reveal clouds of gas and dust.</p>
          </c-CTabPanel>
          <c-CTabPanel value="galaxies">
            <h3>Finding galaxies</h3>
            <p>From a dark site, the Andromeda Galaxy is visible without a telescope.</p>
          </c-CTabPanel>
        </c-CTabs>
      </section>
    """

    css = """
      :where(.night-sky-guide) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        --cui-tabs-active-background: light-dark(#eef2ff, #1e1b4b);
        max-width: 44rem;
        padding: 1.5rem;
        border: 1px solid light-dark(#a5b4fc, #4338ca);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
        box-shadow: 0 1rem 2.5rem rgb(15 23 42 / 12%);
      }

      :where(.night-sky-guide header) {
        margin-block-end: 1.25rem;
      }

      :where(.night-sky-guide h2, .night-sky-guide h3, .night-sky-guide p) {
        margin-block: 0 0.5rem;
      }

      :where(.night-sky-guide__eyebrow) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.night-sky-guide output) {
        font-weight: 700;
      }
    """


preview = NightSkyGuide()

preview  # noqa: B018
