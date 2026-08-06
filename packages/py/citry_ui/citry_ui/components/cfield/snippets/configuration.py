import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FieldInputConfiguration(Component):
    template = """
      <section
        class="shore-configurator"
        x-data
        x-init="Alpine.store('shoreFieldConfig', {
          orientation: 'vertical',
          density: 'default',
          variant: 'outline',
          size: 'md',
          required: true,
          disabled: false,
          readonly: false,
          invalid: false,
        })"
        @citry-ui-preview-controls.window="Object.assign($store.shoreFieldConfig, $event.detail)"
      >
        <header>
          <p>Survey setup</p>
          <h2>Configure the observation field</h2>
        </header>

        <c-CField
          $c-props="{
            orientation: $store.shoreFieldConfig.orientation,
            density: $store.shoreFieldConfig.density,
            required: $store.shoreFieldConfig.required,
            disabled: $store.shoreFieldConfig.disabled,
            readonly: $store.shoreFieldConfig.readonly,
            invalid: $store.shoreFieldConfig.invalid,
          }"
        >
          <c-fill name="label">
            Shore condition
          </c-fill>
          <c-fill name="default">
            <c-CInput
              name="condition"
              value="Calm pools"
              $c-props="{
                variant: $store.shoreFieldConfig.variant,
                size: $store.shoreFieldConfig.size,
              }"
            />
          </c-fill>
          <c-fill name="description">
            Record the water state at the start of the survey.
          </c-fill>
          <c-fill name="error">
            Add the current shore condition.
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.shore-configurator) {
        max-width: 58rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.shore-configurator header) {
        margin-block-end: 1rem;
      }

      :where(.shore-configurator h2, .shore-configurator p) {
        margin-block: 0;
      }

      :where(.shore-configurator header p) {
        margin-block-end: 0.35rem;
        color: light-dark(#08758a, #69d4e8);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }
    """


preview_controls = (
    {
        "name": "orientation",
        "label": "Orientation",
        "type": "select",
        "default": "vertical",
        "options": (("vertical", "Vertical"), ("horizontal", "Horizontal")),
    },
    {
        "name": "density",
        "label": "Field density",
        "type": "select",
        "default": "default",
        "options": (("default", "Default"), ("comfortable", "Comfortable"), ("compact", "Compact")),
    },
    {
        "name": "variant",
        "label": "Input variant",
        "type": "select",
        "default": "outline",
        "options": (("outline", "Outline"), ("filled", "Filled"), ("plain", "Plain")),
    },
    {
        "name": "size",
        "label": "Input size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {"name": "required", "label": "Required", "type": "checkbox", "default": True},
    {"name": "disabled", "label": "Disabled", "type": "checkbox", "default": False},
    {"name": "readonly", "label": "Read-only", "type": "checkbox", "default": False},
    {"name": "invalid", "label": "Invalid", "type": "checkbox", "default": False},
)

preview = FieldInputConfiguration()

preview  # noqa: B018
