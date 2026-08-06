import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsLongList(Component):
    template = """
      <section class="tabs-overflow">
        <header>
          <p class="tabs-eyebrow">Seven survey programs</p>
          <h2>Planetary observation queue</h2>
        </header>

        <p class="tabs-overflow__hint">Scroll the Tab row to reach every survey.</p>

        <c-CTabs
          default_value="mercury"
          aria_label="Planetary observation programs"
          density="compact"
        >
          <c-CTab value="mercury">
            Mercury geology
          </c-CTab>
          <c-CTab value="venus">
            Venus cloud layers
          </c-CTab>
          <c-CTab value="earth">
            Earth magnetosphere
          </c-CTab>
          <c-CTab value="mars">
            Mars surface weather
          </c-CTab>
          <c-CTab value="jupiter">
            Jupiter storm systems
          </c-CTab>
          <c-CTab value="saturn">
            Saturn ring survey
          </c-CTab>
          <c-CTab value="outer-system">
            Outer-system objects
          </c-CTab>

          <c-CTabPanel value="mercury">
            Map fresh impact craters near Mercury's equator.
          </c-CTabPanel>
          <c-CTabPanel value="venus">
            Compare ultraviolet images of Venusian clouds.
          </c-CTabPanel>
          <c-CTabPanel value="earth">
            Follow changes in Earth's magnetic environment.
          </c-CTabPanel>
          <c-CTabPanel value="mars">
            Track dust and frost across the Martian surface.
          </c-CTabPanel>
          <c-CTabPanel value="jupiter">
            Measure wind patterns around Jupiter's largest storms.
          </c-CTabPanel>
          <c-CTabPanel value="saturn">
            Resolve fine structure within Saturn's rings.
          </c-CTabPanel>
          <c-CTabPanel value="outer-system">
            Search for faint objects beyond Neptune.
          </c-CTabPanel>
        </c-CTabs>
      </section>
    """

    css = """
      :where(.tabs-overflow) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        width: min(100%, 28rem);
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-overflow header) {
        margin-block-end: 1rem;
      }

      :where(.tabs-overflow h2, .tabs-overflow p) {
        margin-block: 0;
      }

      :where(.tabs-overflow header p) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      :where(.tabs-overflow__hint) {
        margin-block: 0 0.5rem;
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.8125rem;
      }

      :where(.tabs-eyebrow) {
        color: var(--cui-tabs-accent, LinkText);
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
      }
    """


preview = TabsLongList()

preview  # noqa: B018
