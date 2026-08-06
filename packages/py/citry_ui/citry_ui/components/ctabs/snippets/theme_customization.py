import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsThemeCustomization(Component):
    template = """
      <section class="tabs-theme">
        <article class="tabs-theme__card tabs-theme__card--light">
          <header>
            <p class="tabs-eyebrow">Light surface</p>
            <h2>Lunar atlas</h2>
          </header>

          <c-CTabs
            default_value="maria"
            aria_label="Light lunar atlas"
            variant="pill"
          >
            <c-CTab value="maria">
              Maria
            </c-CTab>
            <c-CTab value="craters">
              Craters
            </c-CTab>
            <c-CTab value="highlands">
              Highlands
            </c-CTab>

            <c-CTabPanel value="maria">
              Dark plains formed by ancient volcanic flows.
            </c-CTabPanel>
            <c-CTabPanel value="craters">
              Impact basins record billions of years of history.
            </c-CTabPanel>
            <c-CTabPanel value="highlands">
              Bright, heavily cratered terrain covers much of the Moon.
            </c-CTabPanel>
          </c-CTabs>
        </article>

        <article class="tabs-theme__card tabs-theme__card--dark">
          <header>
            <p class="tabs-eyebrow">Dark surface</p>
            <h2>Lunar atlas</h2>
          </header>

          <c-CTabs
            default_value="maria"
            aria_label="Dark lunar atlas"
            variant="pill"
          >
            <c-CTab value="maria">
              Maria
            </c-CTab>
            <c-CTab value="craters">
              Craters
            </c-CTab>
            <c-CTab value="highlands">
              Highlands
            </c-CTab>

            <c-CTabPanel value="maria">
              Dark plains formed by ancient volcanic flows.
            </c-CTabPanel>
            <c-CTabPanel value="craters">
              Impact basins record billions of years of history.
            </c-CTabPanel>
            <c-CTabPanel value="highlands">
              Bright, heavily cratered terrain covers much of the Moon.
            </c-CTabPanel>
          </c-CTabs>
        </article>
      </section>
    """

    css = """
      :where(.tabs-theme) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-theme__card) {
        --cui-tabs-accent: #1d4ed8;
        --cui-tabs-border-color: #bfdbfe;
        --cui-tabs-muted-color: #475569;
        --cui-tabs-list-background: #eff6ff;
        --cui-tabs-active-background: #ffffff;
        --cui-tabs-hover-background: #dbeafe;
        --cui-tabs-focus-color: #7c3aed;
        --cui-tabs-radius: 0.75rem;
        --cui-tabs-gap: 0.75rem;
        --cui-tabs-panel-padding: 1rem 0.25rem 0.25rem;
        color-scheme: light;
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid #bfdbfe;
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
      }

      :where(.tabs-theme__card--dark) {
        --cui-tabs-accent: #67e8f9;
        --cui-tabs-border-color: #155e75;
        --cui-tabs-muted-color: #cbd5e1;
        --cui-tabs-list-background: #083344;
        --cui-tabs-active-background: #164e63;
        --cui-tabs-hover-background: #0e7490;
        --cui-tabs-focus-color: #f0abfc;
        color-scheme: dark;
        border-color: #155e75;
      }

      :where(.tabs-theme__card header) {
        margin-block-end: 0.75rem;
      }

      :where(.tabs-theme__card h2, .tabs-theme__card p) {
        margin-block: 0;
      }

      :where(.tabs-theme__card header p) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.tabs-eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
      }
    """


preview = TabsThemeCustomization()

preview  # noqa: B018
