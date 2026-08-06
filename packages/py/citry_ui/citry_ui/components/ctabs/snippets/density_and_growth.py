import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsDensityAndGrowth(Component):
    template = """
      <section
        class="tabs-density"
        x-data="{ grow: false }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <div class="tabs-density__row">
          <h2>Default</h2>
          <c-CTabs
            default_value="orbit"
            aria_label="Default-density telescope views"
            density="default"
            $c-props="{ grow }"
          >
            <c-CTab value="orbit">
              Orbit
            </c-CTab>
            <c-CTab value="surface">
              Surface
            </c-CTab>
            <c-CTab value="signals">
              Signals
            </c-CTab>

            <c-CTabPanel value="orbit">
              Track the object's path across the sky.
            </c-CTabPanel>
            <c-CTabPanel value="surface">
              Compare reflected-light surface features.
            </c-CTabPanel>
            <c-CTabPanel value="signals">
              Review the latest radio observations.
            </c-CTabPanel>
          </c-CTabs>
        </div>

        <div class="tabs-density__row">
          <h2>Comfortable</h2>
          <c-CTabs
            default_value="orbit"
            aria_label="Comfortable-density telescope views"
            density="comfortable"
            $c-props="{ grow }"
          >
            <c-CTab value="orbit">
              Orbit
            </c-CTab>
            <c-CTab value="surface">
              Surface
            </c-CTab>
            <c-CTab value="signals">
              Signals
            </c-CTab>

            <c-CTabPanel value="orbit">
              Track the object's path across the sky.
            </c-CTabPanel>
            <c-CTabPanel value="surface">
              Compare reflected-light surface features.
            </c-CTabPanel>
            <c-CTabPanel value="signals">
              Review the latest radio observations.
            </c-CTabPanel>
          </c-CTabs>
        </div>

        <div class="tabs-density__row">
          <h2>Compact</h2>
          <c-CTabs
            default_value="orbit"
            aria_label="Compact-density telescope views"
            density="compact"
            $c-props="{ grow }"
          >
            <c-CTab value="orbit">
              Orbit
            </c-CTab>
            <c-CTab value="surface">
              Surface
            </c-CTab>
            <c-CTab value="signals">
              Signals
            </c-CTab>

            <c-CTabPanel value="orbit">
              Track the object's path across the sky.
            </c-CTabPanel>
            <c-CTabPanel value="surface">
              Compare reflected-light surface features.
            </c-CTabPanel>
            <c-CTabPanel value="signals">
              Review the latest radio observations.
            </c-CTabPanel>
          </c-CTabs>
        </div>
      </section>
    """

    css = """
      :where(.tabs-density) {
        --cui-tabs-accent: light-dark(#4338ca, #a5b4fc);
        --cui-tabs-focus-color: light-dark(#4f46e5, #818cf8);
        display: grid;
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tabs-density__row) {
        display: grid;
        grid-template-columns: 7rem minmax(0, 1fr);
        gap: 1rem;
        align-items: start;
        min-width: 0;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, currentColor 16%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.tabs-density__row h2) {
        margin-block: 0.65rem 0;
        color: color-mix(in srgb, currentColor 72%, transparent);
        font-size: 0.875rem;
      }

      @media (max-width: 34rem) {
        :where(.tabs-density__row) {
          grid-template-columns: minmax(0, 1fr);
        }

        :where(.tabs-density__row h2) {
          margin-block: 0;
        }
      }
    """


preview_controls = (
    {
        "name": "grow",
        "label": "Make Tabs equal width",
        "type": "checkbox",
        "default": False,
    },
)

preview = TabsDensityAndGrowth()

preview  # noqa: B018
