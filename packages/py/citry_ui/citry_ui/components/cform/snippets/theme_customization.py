import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormThemeCustomization(Component):
    template = """
      <section
        class="night-checklist"
        x-data="{ gap: '0.75rem', scheme: 'light', compact: false }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
        :style="{ colorScheme: scheme, '--cui-form-gap': gap }"
        :data-compact="compact"
      >
        <header>
          <p>Night checklist</p>
          <h2>Prepare the observatory</h2>
        </header>

        <c-CForm
          class_="night-checklist__form"
          @submit.prevent="void 0"
        >
          <label>
            <input
              type="checkbox"
              name="task"
              value="dome"
            />
            Open the dome shutters
          </label>
          <label>
            <input
              type="checkbox"
              name="task"
              value="cooling"
            />
            Start detector cooling
          </label>
          <label>
            <input
              type="checkbox"
              name="task"
              value="weather"
            />
            Confirm weather limits
          </label>
          <c-CButton type="submit" size="sm">
            Begin session
          </c-CButton>
        </c-CForm>
      </section>
    """

    css = """
      :where(.night-checklist) {
        max-width: 40rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.night-checklist[data-compact]) {
        max-width: 28rem;
      }

      :where(.night-checklist header) {
        margin-block-end: 1rem;
      }

      :where(.night-checklist h2, .night-checklist p) {
        margin-block: 0;
      }

      :where(.night-checklist header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.night-checklist__form[data-citry-ui-part="form"]) {
        padding: 1rem;
        border: 1px solid light-dark(#d7d8ea, #3c3f63);
        border-radius: 0.625rem;
        background: light-dark(#fafaff, #1c1c2d);
      }

      :where(.night-checklist__form [data-citry-ui-part="fieldset"]) {
        align-items: start;
      }

      :where(.night-checklist__form label) {
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      :where(.night-checklist__form [data-citry-ui-part="button"]) {
        justify-self: start;
      }
    """


preview_controls = (
    {
        "name": "gap",
        "label": "Form spacing",
        "type": "select",
        "default": "0.75rem",
        "options": (("0.4rem", "Tight"), ("0.75rem", "Default"), ("1.25rem", "Open")),
    },
    {
        "name": "scheme",
        "label": "Color scheme",
        "type": "select",
        "default": "light",
        "options": (("light", "Light"), ("dark", "Dark")),
    },
    {
        "name": "compact",
        "label": "Narrow container",
        "type": "checkbox",
        "default": False,
    },
)

preview = FormThemeCustomization()

preview  # noqa: B018
