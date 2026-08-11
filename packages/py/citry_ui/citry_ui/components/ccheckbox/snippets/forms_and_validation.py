import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CheckboxForms(Component):
    template = """
      <section
        class="checkbox-form-demo"
        x-data="{result: 'Submit the form to inspect its native values.'}"
      >
        <c-CForm
          id="botanical-survey"
          @submit.prevent="result = JSON.stringify(
            Array.from(new FormData($event.target).entries())
          )"
          @reset="result = 'The browser restored the server defaults.'"
        >
          <fieldset>
            <legend>Habitats observed</legend>
            <c-CCheckbox name="habitat" value="meadow" checked>
              Meadow edge
            </c-CCheckbox>
            <c-CCheckbox name="habitat" value="woodland" checked>
              Ancient woodland
            </c-CCheckbox>
            <c-CCheckbox name="habitat" value="wetland">
              Wetland margin
            </c-CCheckbox>
          </fieldset>
          <c-CCheckbox name="confirmed" value="yes" required>
            I checked the location against the field map
          </c-CCheckbox>
          <div class="checkbox-form-demo__actions">
            <c-CButton type="submit">Record survey</c-CButton>
            <c-CButton type="reset" variant="outline" intent="neutral">Reset</c-CButton>
          </div>
        </c-CForm>
        <output x-text="result" aria-live="polite"></output>
      </section>
    """

    css = """
      :where(.checkbox-form-demo) {
        display: grid;
        gap: 1rem;
        max-width: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.checkbox-form-demo fieldset) {
        display: grid;
        gap: 0.75rem;
        margin: 0;
        padding: 1rem;
        border: 1px solid light-dark(#bfd1ba, #415943);
        border-radius: 0.75rem;
      }

      :where(.checkbox-form-demo legend) {
        padding-inline: 0.35rem;
        font-weight: 700;
      }

      :where(.checkbox-form-demo__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.checkbox-form-demo output) {
        padding: 0.75rem;
        border-radius: 0.625rem;
        background: light-dark(#f1f7ef, #18271a);
        font-family: ui-monospace, monospace;
        font-size: 0.875rem;
      }
    """


preview = CheckboxForms()

preview  # noqa: B018
