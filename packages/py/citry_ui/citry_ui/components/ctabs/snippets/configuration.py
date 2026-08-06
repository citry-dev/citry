import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TabsConfiguration(Component):
    template = """
      <section
        class="tabs-configurator"
        x-data="{
          selected: 'mercury',
          accent: 'violet',
          accents: {
            violet: 'light-dark(#6d28d9, #c4b5fd)',
            coral: 'light-dark(#c2410c, #fdba74)',
            teal: 'light-dark(#0f766e, #5eead4)',
            pink: 'light-dark(#be185d, #f9a8d4)',
          },
          variant: 'underline',
          density: 'default',
          orientation: 'horizontal',
          align: 'start',
          grow: false,
          loop: true,
          disabled: false,
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
        :style="{
          '--cui-tabs-accent': accents[accent],
          '--cui-tabs-focus-color': accents[accent],
        }"
      >
        <header>
          <p class="tabs-configurator__eyebrow">Pocket reference</p>
          <h2>Solar system field guide</h2>
        </header>

        <div class="tabs-configurator__stage">
          <p class="tabs-configurator__status" aria-live="polite">
            Current world:
            <strong x-text="selected">mercury</strong>
          </p>

          <c-CTabs
            default_value="mercury"
            aria_label="Solar system chapters"
            $c-props="{
              variant,
              density,
              orientation,
              align,
              grow,
              loop,
              disabled,
              onValueChange: (value) => {
                selected = value;
              },
            }"
          >
            <c-CTab value="mercury">
              Mercury
            </c-CTab>
            <c-CTab value="europa">
              Europa
            </c-CTab>
            <c-CTab value="titan">
              Titan
            </c-CTab>

            <c-CTabPanel value="mercury">
              <h3>Mercury</h3>
              <p>A cratered world with sharp swings between day and night.</p>
            </c-CTabPanel>
            <c-CTabPanel value="europa">
              <h3>Europa</h3>
              <p>An icy moon with evidence of a vast ocean beneath its surface.</p>
            </c-CTabPanel>
            <c-CTabPanel value="titan">
              <h3>Titan</h3>
              <p>A hazy moon with rivers and lakes of liquid methane.</p>
            </c-CTabPanel>
          </c-CTabs>
        </div>
      </section>
    """

    css = """
      :where(.tabs-configurator) {
        max-width: 64rem;
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, var(--cui-tabs-accent) 54%, transparent);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.tabs-configurator > header) {
        margin-block-end: 1rem;
      }

      :where(.tabs-configurator h2, .tabs-configurator h3, .tabs-configurator p) {
        margin-block: 0 0.5rem;
      }

      :where(.tabs-configurator__eyebrow) {
        color: var(--cui-tabs-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.tabs-configurator__stage) {
        min-width: 0;
      }

      :where(.tabs-configurator__status) {
        color: color-mix(in srgb, currentColor 72%, transparent);
      }
    """


preview_controls = (
    {
        "name": "accent",
        "label": "Accent",
        "type": "select",
        "default": "violet",
        "options": (
            ("violet", "Violet"),
            ("coral", "Coral"),
            ("teal", "Teal"),
            ("pink", "Pink"),
        ),
    },
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "underline",
        "options": (("underline", "Underline"), ("pill", "Pill")),
    },
    {
        "name": "density",
        "label": "Density",
        "type": "select",
        "default": "default",
        "options": (
            ("default", "Default"),
            ("comfortable", "Comfortable"),
            ("compact", "Compact"),
        ),
    },
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
    {
        "name": "grow",
        "label": "Grow to fill space",
        "type": "checkbox",
        "default": False,
    },
    {
        "name": "loop",
        "label": "Loop keyboard focus",
        "type": "checkbox",
        "default": True,
    },
    {
        "name": "disabled",
        "label": "Disable all Tabs",
        "type": "checkbox",
        "default": False,
    },
)

preview = TabsConfiguration()

preview  # noqa: B018
