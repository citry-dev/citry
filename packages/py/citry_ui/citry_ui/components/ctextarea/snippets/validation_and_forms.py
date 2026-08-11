import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TextareaValidation(Component):
    template = """
      <section class="forest-report" x-data="{submitted: ''}">
        <c-CForm @submit.prevent="submitted = new FormData($event.target).get('habitat')">
          <c-CField required>
            <c-fill name="label">Habitat report</c-fill>
            <c-fill name="default">
              <c-CTextarea
                name="habitat"
                value="Moss"
                c-attrs="{'minlength': 12, 'maxlength': 180, 'spellcheck': True}"
              />
            </c-fill>
            <c-fill name="description">Use 12 to 180 characters.</c-fill>
            <c-fill name="error">Add a fuller habitat description.</c-fill>
          </c-CField>
          <div class="forest-report__actions">
            <c-CButton type="submit">Save report</c-CButton>
            <c-CButton type="reset" variant="outline">Reset</c-CButton>
          </div>
          <output x-show="submitted" x-text="submitted"></output>
        </c-CForm>
      </section>
    """

    css = """
      :where(.forest-report) {
        display: grid;
        gap: 1rem;
        max-width: 40rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.forest-report__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.forest-report output) {
        white-space: pre-wrap;
      }
    """


preview = TextareaValidation()

preview  # noqa: B018
