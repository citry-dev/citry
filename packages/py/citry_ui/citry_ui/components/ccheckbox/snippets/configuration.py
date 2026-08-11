import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CheckboxConfiguration(Component):
    template = """
      <section
        class="checkbox-configurator"
        x-data="{
          variant: 'solid',
          size: 'md',
          label_pos: 'end',
          checked: true,
          indeterminate: false,
          required: false,
          disabled: false,
          invalid: false,
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p>Living collection</p>
          <h2>Configure the record marker</h2>
        </header>
        <c-CCheckbox
          $c-props="{
            variant,
            size,
            label_pos,
            checked,
            indeterminate,
            required,
            disabled,
            invalid,
          }"
          @input="checked = $event.target.checked; indeterminate = false"
        >
          <c-fill name="default">Verified against the herbarium sheet</c-fill>
          <c-fill name="description">
            Match leaf shape, vein pattern, and collection date.
          </c-fill>
        </c-CCheckbox>
      </section>
    """

    css = """
      :where(.checkbox-configurator) {
        display: grid;
        gap: 1.25rem;
        max-width: 50rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b7cfba, #3a5940);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.checkbox-configurator h2, .checkbox-configurator p) {
        margin: 0;
      }

      :where(.checkbox-configurator header p) {
        color: light-dark(#287047, #7ed6a0);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "solid",
        "options": (("solid", "Solid"), ("outline", "Outline")),
    },
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {
        "name": "label_pos",
        "label": "Label position",
        "type": "select",
        "default": "end",
        "options": (("end", "End"), ("start", "Start")),
    },
    {"name": "checked", "label": "Checked", "type": "checkbox", "default": True},
    {"name": "indeterminate", "label": "Indeterminate", "type": "checkbox", "default": False},
    {"name": "required", "label": "Required", "type": "checkbox", "default": False},
    {"name": "disabled", "label": "Disabled", "type": "checkbox", "default": False},
    {"name": "invalid", "label": "Invalid", "type": "checkbox", "default": False},
)

preview = CheckboxConfiguration()

preview  # noqa: B018
