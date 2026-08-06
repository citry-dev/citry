import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormConfiguration(Component):
    template = """
      <section
        class="form-configurator"
        x-data="{
          disabled: false,
          readonly: false,
          submitting: false,
          gap: '1rem',
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
        :style="{'--cui-form-gap': gap}"
      >
        <header>
          <p>Deep-sky planner</p>
          <h2>Configure Form state</h2>
        </header>

        <c-CForm
          class_="form-configurator__form"
          $c-props="{
            disabled,
            readonly,
            submitting,
          }"
          @submit.prevent="void 0"
        >
          <c-CField>
            <c-fill name="label">
              Observation notes
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="notes"
                value="Track the nebula after moonset."
              />
            </c-fill>
          </c-CField>
          <c-CButton
            type="submit"
          >
            Save plan
          </c-CButton>
        </c-CForm>

        <p class="form-configurator__status" aria-live="polite">
          <span
            x-text="
              disabled
                ? 'disabled'
                : readonly
                  ? 'read-only'
                  : submitting
                    ? 'submitting'
                    : 'editable'
            "
          ></span>
        </p>
      </section>
    """

    css = """
      :where(.form-configurator) {
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.form-configurator header) {
        margin-block-end: 1rem;
      }

      :where(.form-configurator h2, .form-configurator p) {
        margin-block: 0;
      }

      :where(.form-configurator header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.form-configurator__form [data-citry-ui-part="button"]) {
        justify-self: start;
      }

      :where(.form-configurator__status) {
        margin-block-start: 0.85rem;
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.8125rem;
      }
    """


preview_controls = (
    {
        "name": "disabled",
        "label": "Disable Form",
        "type": "checkbox",
        "default": False,
    },
    {
        "name": "readonly",
        "label": "Use read-only defaults",
        "type": "checkbox",
        "default": False,
    },
    {
        "name": "submitting",
        "label": "Show submitting state",
        "type": "checkbox",
        "default": False,
    },
    {
        "name": "gap",
        "label": "Content spacing",
        "type": "select",
        "default": "1rem",
        "options": (("0.5rem", "Compact"), ("1rem", "Default"), ("1.5rem", "Spacious")),
    },
)

preview = FormConfiguration()

preview  # noqa: B018
