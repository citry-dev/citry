import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsNested(Component):
    template = """
      <section class="tabs-nested">
        <header>
          <p class="tabs-eyebrow">Outer and inner selection</p>
          <h2>Giant planets</h2>
        </header>

        <c-CTabs
          default_value="jupiter"
          aria_label="Giant planets"
        >
          <c-CTab value="jupiter">
            Jupiter
          </c-CTab>
          <c-CTab value="saturn">
            Saturn
          </c-CTab>

          <c-CTabPanel value="jupiter">
            <div class="tabs-nested__inner">
              <c-CTabs
                default_value="moons"
                aria_label="Jupiter topics"
                variant="pill"
                density="compact"
              >
                <c-CTab value="moons">
                  Moons
                </c-CTab>
                <c-CTab value="atmosphere">
                  Atmosphere
                </c-CTab>
                <c-CTab value="rings">
                  Rings
                </c-CTab>

                <c-CTabPanel value="moons">
                  Io, Europa, Ganymede, and Callisto are the largest moons.
                </c-CTabPanel>
                <c-CTabPanel value="atmosphere">
                  Bands of clouds circle a deep hydrogen-rich atmosphere.
                </c-CTabPanel>
                <c-CTabPanel value="rings">
                  Jupiter has a faint ring system made mostly of dust.
                </c-CTabPanel>
              </c-CTabs>
            </div>
          </c-CTabPanel>
          <c-CTabPanel value="saturn">
            Saturn's bright rings contain countless pieces of ice and rock.
          </c-CTabPanel>
        </c-CTabs>
      </section>
    """

    css = """
      :where(.tabs-nested) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        max-width: 52rem;
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-nested > header) {
        margin-block-end: 1rem;
      }

      :where(.tabs-nested h2, .tabs-nested p) {
        margin-block: 0;
      }

      :where(.tabs-nested > header p) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.tabs-nested__inner) {
        --cui-tabs-accent: light-dark(#0f766e, #5eead4);
        --cui-tabs-focus-color: light-dark(#0d9488, #2dd4bf);
        --cui-tabs-active-background: light-dark(#f0fdfa, #042f2e);
        padding: 0.75rem;
        border: 1px solid color-mix(in srgb, currentColor 14%, transparent);
        border-radius: 0.625rem;
      }

      :where(.tabs-eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
      }
    """


preview = TabsNested()

preview  # noqa: B018
