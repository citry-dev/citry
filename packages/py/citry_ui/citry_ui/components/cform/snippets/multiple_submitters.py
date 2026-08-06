import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MultipleSubmitters(Component):
    template = """
      <section
        class="observation-draft"
        x-data="{ status: 'Choose how to save the observation.' }"
      >
        <header>
          <p>Observation log</p>
          <h2>Save a lunar transit</h2>
        </header>

        <c-CForm
          action="/observations"
          method="post"
          @submit.prevent="
            status = $event.submitter.value
              + ' via '
              + ($event.submitter.formMethod || $event.currentTarget.method).toUpperCase()
              + ' to '
              + ($event.submitter.formAction || $event.currentTarget.action)
          "
        >
          <c-CField required>
            <c-fill name="label">
              Summary
            </c-fill>
            <c-fill name="default">
              <c-CInput name="summary" value="Io crossed Jupiter at 02:14 UTC" />
            </c-fill>
          </c-CField>
          <div class="observation-draft__actions">
            <c-CButton
              type="submit"
              variant="outline"
              intent="neutral"
              c-attrs="{
                'name': 'intent',
                'value': 'draft',
                'formaction': '/observations/drafts',
                'formnovalidate': True,
              }"
            >
              Save draft
            </c-CButton>
            <c-CButton
              type="submit"
              c-attrs="{
                'name': 'intent',
                'value': 'publish',
                'formaction': '/observations/publish',
                'formmethod': 'post',
              }"
            >
              Publish
            </c-CButton>
          </div>
        </c-CForm>

        <p
          class="observation-draft__status"
          aria-live="polite"
          x-text="status"
        ></p>
      </section>
    """

    css = """
      :where(.observation-draft) {
        max-width: 46rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.observation-draft header) {
        margin-block-end: 1rem;
      }

      :where(.observation-draft h2, .observation-draft p) {
        margin-block: 0;
      }

      :where(.observation-draft header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.observation-draft__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
      }

      :where(.observation-draft__status) {
        margin-block-start: 1rem;
        color: light-dark(#175c43, #7be0b5);
      }
    """


preview = MultipleSubmitters()

preview  # noqa: B018
