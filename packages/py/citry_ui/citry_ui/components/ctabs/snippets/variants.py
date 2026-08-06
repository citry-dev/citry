import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsVariants(Component):
    template = """
      <section class="tabs-variants">
        <article class="tabs-variants__card">
          <header>
            <p class="tabs-eyebrow">Low-emphasis navigation</p>
            <h2>Underline</h2>
          </header>

          <c-CTabs
            default_value="surface"
            aria_label="Underline Mars topics"
            variant="underline"
          >
            <c-CTab value="orbit">
              Orbit
            </c-CTab>
            <c-CTab value="surface">
              Surface
            </c-CTab>
            <c-CTab value="weather">
              Weather
            </c-CTab>

            <c-CTabPanel value="orbit">
              Mars completes one orbit in roughly 687 Earth days.
            </c-CTabPanel>
            <c-CTabPanel value="surface">
              Iron minerals give the surface its familiar red color.
            </c-CTabPanel>
            <c-CTabPanel value="weather">
              Thin clouds and planet-wide dust storms shape the sky.
            </c-CTabPanel>
          </c-CTabs>
        </article>

        <article class="tabs-variants__card tabs-variants__card--pill">
          <header>
            <p>Contained choices</p>
            <h2>Pill</h2>
          </header>

          <c-CTabs
            default_value="surface"
            aria_label="Pill Mars topics"
            variant="pill"
          >
            <c-CTab value="orbit">
              Orbit
            </c-CTab>
            <c-CTab value="surface">
              Surface
            </c-CTab>
            <c-CTab value="weather">
              Weather
            </c-CTab>

            <c-CTabPanel value="orbit">
              Mars completes one orbit in roughly 687 Earth days.
            </c-CTabPanel>
            <c-CTabPanel value="surface">
              Iron minerals give the surface its familiar red color.
            </c-CTabPanel>
            <c-CTabPanel value="weather">
              Thin clouds and planet-wide dust storms shape the sky.
            </c-CTabPanel>
          </c-CTabs>
        </article>
      </section>
    """

    css = """
      :where(.tabs-variants) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-variants__card) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.tabs-variants__card--pill) {
        --cui-tabs-accent: light-dark(#0f766e, #5eead4);
        --cui-tabs-focus-color: light-dark(#0d9488, #2dd4bf);
        --cui-tabs-active-background: light-dark(#f0fdfa, #042f2e);
      }

      :where(.tabs-variants__card header) {
        margin-block-end: 0.75rem;
      }

      :where(.tabs-variants__card h2, .tabs-variants__card p) {
        margin-block: 0;
        margin-bottom: 0.5rem;
      }

      :where(.tabs-variants__card header p) {
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }
    """


preview = TabsVariants()

preview  # noqa: B018
