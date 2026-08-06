import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NativeSubmission(Component):
    template = """
      <section
        class="transient-report"
        x-data="{ submitted: '', submitter: '' }"
      >
        <header>
          <p>Transient watch</p>
          <h2>Report a changing object</h2>
        </header>

        <c-CForm
          action="/transients"
          method="post"
          @submit.prevent="
            submitted = JSON.stringify(
              Object.fromEntries(new FormData($el, $event.submitter))
            );
            submitter = $event.submitter?.value ?? '';
          "
        >
          <c-CField required>
            <c-fill name="label">
              Object
            </c-fill>
            <c-fill name="default">
              <c-CInput name="object" value="AT 2026lmn" />
            </c-fill>
          </c-CField>
          <c-CField>
            <c-fill name="label">
              Brightness
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="magnitude"
                value="17.4"
                inputmode="decimal"
              />
            </c-fill>
          </c-CField>
          <div class="transient-report__actions">
            <c-CButton
              type="submit"
              c-attrs="{'name': 'intent', 'value': 'report'}"
            >
              Report object
            </c-CButton>
            <c-CButton
              type="reset"
              variant="ghost"
              intent="neutral"
            >
              Reset
            </c-CButton>
          </div>
        </c-CForm>

        <output aria-live="polite" x-show="submitted">
          Submitter: <strong x-text="submitter"></strong><br />
          FormData: <code x-text="submitted"></code>
        </output>
      </section>
    """

    css = """
      :where(.transient-report) {
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.transient-report header) {
        margin-block-end: 1rem;
      }

      :where(.transient-report h2, .transient-report p) {
        margin-block: 0;
      }

      :where(.transient-report header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.transient-report__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
      }

      :where(.transient-report output) {
        display: block;
        margin-block-start: 1rem;
        padding: 0.75rem;
        border-radius: 0.5rem;
        background: light-dark(#f3f1ff, #25243d);
        overflow-wrap: anywhere;
      }
    """


preview = NativeSubmission()

preview  # noqa: B018
