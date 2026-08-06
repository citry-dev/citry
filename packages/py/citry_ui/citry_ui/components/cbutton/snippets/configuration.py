import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonConfiguration(Component):
    template = """
      <section
        class="button-configurator"
        x-data="{
          variant: 'solid',
          intent: 'primary',
          size: 'md',
          loading_pos: 'center',
          loading: false,
          disabled: false,
          block: false,
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p>Specimen catalog</p>
          <h2>Configure the action</h2>
        </header>

        <div class="button-configurator__stage">
          <c-CButton
            $c-props="{
              variant,
              intent,
              size,
              loadingPosition: loading_pos,
              loading,
              disabled,
              block,
            }"
          >
            <c-fill name="start">
              <span aria-hidden="true">✿</span>
            </c-fill>
            <c-fill name="default">
              Catalog specimen
            </c-fill>
            <c-fill name="end">
              <span aria-hidden="true">→</span>
            </c-fill>
          </c-CButton>

          <p class="button-configurator__status" aria-live="polite">
            <span x-text="variant">solid</span>
            ·
            <span x-text="intent">primary</span>
            ·
            <span x-text="size">md</span>
          </p>
        </div>
      </section>
    """

    css = """
      :where(.button-configurator) {
        max-width: 58rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bbd6c5, #355e48);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.button-configurator header) {
        margin-block-end: 1rem;
      }

      :where(.button-configurator h2, .button-configurator p) {
        margin-block: 0;
      }

      :where(.button-configurator header p) {
        margin-block-end: 0.35rem;
        color: light-dark(#19704a, #74d9a3);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.button-configurator__stage) {
        display: grid;
        gap: 0.75rem;
        min-width: 0;
      }

      :where(
        .button-configurator__stage > [data-citry-ui-part="button"]
      ) {
        justify-self: start;
      }

      :where(
        .button-configurator__stage > [data-citry-ui-part="button"][data-block]
      ) {
        justify-self: stretch;
      }

      :where(.button-configurator__status) {
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.8125rem;
      }
    """


preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "solid",
        "options": (("solid", "Solid"), ("outline", "Outline"), ("ghost", "Ghost")),
    },
    {
        "name": "intent",
        "label": "Intent",
        "type": "select",
        "default": "primary",
        "options": (
            ("primary", "Primary"),
            ("neutral", "Neutral"),
            ("success", "Success"),
            ("warn", "Warn"),
            ("danger", "Danger"),
        ),
    },
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {
        "name": "loading_pos",
        "label": "Loading position",
        "type": "select",
        "default": "center",
        "options": (("start", "Start"), ("center", "Center"), ("end", "End")),
    },
    {
        "name": "loading",
        "label": "Show loading state",
        "type": "checkbox",
        "default": False,
    },
    {
        "name": "disabled",
        "label": "Disable Button",
        "type": "checkbox",
        "default": False,
    },
    {
        "name": "block",
        "label": "Fill available width",
        "type": "checkbox",
        "default": False,
    },
)

preview = ButtonConfiguration()

preview  # noqa: B018
