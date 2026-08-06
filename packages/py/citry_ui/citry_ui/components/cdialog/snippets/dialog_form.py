import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DialogForm(Component):
    template = """
      <section
        class="dialog-form-demo"
        x-data="{ result: 'No constellation selected' }"
      >
        <p>Star chart</p>
        <h2>Use a native Dialog Form</h2>
        <c-CDialog
          $c-props="{
            onOpenChange: (open, detail) => {
              if (!open && detail.returnValue) result = detail.returnValue;
            },
          }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Choose constellation
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Choose a constellation
          </c-fill>
          <c-fill name="description">
            Native submitter values become the Dialog return value.
          </c-fill>
          <c-fill name="default">
            <form method="dialog" class="dialog-form-demo__choices">
              <button value="Orion">Orion</button>
              <button value="Cassiopeia">Cassiopeia</button>
              <button value="Cygnus">Cygnus</button>
            </form>
          </c-fill>
        </c-CDialog>
        <p class="dialog-form-demo__result" aria-live="polite">
          Selected: <strong x-text="result">No constellation selected</strong>
        </p>
      </section>
    """

    css = """
      :where(.dialog-form-demo) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 44rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c4b5fd, #6d28d9);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.dialog-form-demo h2, .dialog-form-demo p) {
        margin: 0;
      }

      :where(.dialog-form-demo > p:first-child) {
        color: light-dark(#6d28d9, #c4b5fd);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.dialog-form-demo__choices) {
        display: grid;
        gap: 0.5rem;
      }

      :where(.dialog-form-demo__choices button) {
        padding: 0.75rem 1rem;
        border: 1px solid color-mix(in srgb, currentColor 24%, transparent);
        border-radius: 0.5rem;
        background: transparent;
        color: inherit;
        font: inherit;
        text-align: start;
        cursor: pointer;
      }

      :where(.dialog-form-demo__result) {
        color: color-mix(in srgb, currentColor 72%, transparent);
        font-size: 0.875rem;
      }
    """


preview = DialogForm()

preview  # noqa: B018
