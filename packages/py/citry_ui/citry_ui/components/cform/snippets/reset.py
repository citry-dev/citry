import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormReset(Component):
    template = """
      <section
        class="exposure-reset"
        x-data="{ cancel_reset: false, status: 'Edit either value, then reset.' }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p>Exposure plan</p>
          <h2>Restore authored defaults</h2>
        </header>

        <c-CForm
          @submit.prevent="void 0"
          @reset="
            if (cancel_reset) {
              $event.preventDefault();
              status = 'Reset canceled; edits preserved.';
            } else {
              setTimeout(() => status = 'Defaults restored.', 0);
            }
          "
        >
          <c-CField>
            <c-fill name="label">
              Exposure
            </c-fill>
            <c-fill name="default">
              <c-CInput name="exposure" value="120 seconds" />
            </c-fill>
          </c-CField>
          <c-CField>
            <c-fill name="label">
              Frames
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="frames"
                value="24"
                inputmode="numeric"
              />
            </c-fill>
          </c-CField>
          <c-CButton
            type="reset"
            variant="outline"
            intent="neutral"
          >
            Restore defaults
          </c-CButton>
        </c-CForm>

        <p
          class="exposure-reset__status"
          aria-live="polite"
          x-text="status"
        ></p>
      </section>
    """

    css = """
      :where(.exposure-reset) {
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.exposure-reset header) {
        margin-block-end: 1rem;
      }

      :where(.exposure-reset h2, .exposure-reset p) {
        margin-block: 0;
      }

      :where(.exposure-reset header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.exposure-reset [data-citry-ui-part="button"]) {
        justify-self: start;
      }

      :where(.exposure-reset__status) {
        margin-block-start: 1rem;
        color: color-mix(in srgb, currentColor 68%, transparent);
      }
    """


preview_controls = (
    {
        "name": "cancel_reset",
        "label": "Cancel the reset event",
        "type": "checkbox",
        "default": False,
    },
)

preview = FormReset()

preview  # noqa: B018
