import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsAlignmentAndOrientation(Component):
    template = """
      <section
        class="tabs-layout"
        x-data="{ align: 'start', orientation: 'horizontal' }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p class="tabs-eyebrow">Observatory catalog</p>
          <h2>Targets for tonight</h2>
        </header>

        <c-CTabs
          default_value="planets"
          aria_label="Observatory target categories"
          $c-props="{ align, orientation }"
        >
          <c-CTab value="stars">
            Stars
          </c-CTab>
          <c-CTab value="planets">
            Planets
          </c-CTab>
          <c-CTab value="nebulae">
            Nebulae
          </c-CTab>

          <c-CTabPanel value="stars">
            Compare color, brightness, and spectral class.
          </c-CTabPanel>
          <c-CTabPanel value="planets">
            Follow bright worlds as they move against the stars.
          </c-CTabPanel>
          <c-CTabPanel value="nebulae">
            Find emission and reflection clouds in dark skies.
          </c-CTabPanel>
        </c-CTabs>
      </section>
    """

    css = """
      :where(.tabs-layout) {
        --cui-tabs-accent: light-dark(#0f766e, #5eead4);
        --cui-tabs-focus-color: light-dark(#0d9488, #2dd4bf);
        max-width: 52rem;
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 46%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-layout header) {
        margin-block-end: 1rem;
      }

      :where(.tabs-layout h2, .tabs-layout p) {
        margin-block: 0;
      }

      :where(.tabs-layout header p) {
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
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
      }
    """


preview_controls = (
    {
        "name": "orientation",
        "label": "Orientation",
        "type": "select",
        "default": "horizontal",
        "options": (("horizontal", "Horizontal"), ("vertical", "Vertical")),
    },
    {
        "name": "align",
        "label": "Alignment",
        "type": "select",
        "default": "start",
        "options": (("start", "Start"), ("center", "Center"), ("end", "End")),
    },
)

preview = TabsAlignmentAndOrientation()

preview  # noqa: B018
