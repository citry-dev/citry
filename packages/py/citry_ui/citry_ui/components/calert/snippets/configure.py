import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ConfigureAlert(Component):
    template = """
      <section
        class="alert-configurator"
        x-data="{
          intent: 'info',
          variant: 'soft',
          size: 'md',
          announce: 'off',
          icon: true,
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p>Live configuration</p>
          <h2>Observation status</h2>
        </header>
        <c-CAlert
          $c-props="{
            intent,
            variant,
            size,
            announce,
            icon,
          }"
        >
          <c-fill name="title">Tracking update</c-fill>
          <c-fill name="default">
            The guide camera is following the selected star.
          </c-fill>
        </c-CAlert>
      </section>
    """

    css = """
      :where(.alert-configurator) {
        display: grid;
        gap: 1.25rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.alert-configurator h2, .alert-configurator p) {
        margin: 0;
      }

      :where(.alert-configurator header p) {
        color: light-dark(#3758a6, #9db7ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview_controls = (
    {
        "name": "intent",
        "label": "Intent",
        "type": "select",
        "default": "info",
        "options": (
            ("info", "Info"),
            ("success", "Success"),
            ("warn", "Warn"),
            ("error", "Error"),
        ),
    },
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "soft",
        "options": (("soft", "Soft"), ("solid", "Solid"), ("outline", "Outline")),
    },
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {
        "name": "announce",
        "label": "Announcement",
        "type": "select",
        "default": "off",
        "options": (("off", "Off"), ("polite", "Polite"), ("assertive", "Assertive")),
    },
    {"name": "icon", "label": "Show icon", "type": "checkbox", "default": True},
)

preview = ConfigureAlert()

preview  # noqa: B018
