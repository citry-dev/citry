import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SubmittingGuard(Component):
    template = """
      <section
        class="plate-solve"
        x-data="{ submitting: false, attempts: 0, snapshot: '' }"
      >
        <header>
          <p>Astrometry pipeline</p>
          <h2>Solve a star field</h2>
        </header>

        <c-CForm
          $c-props="{ submitting }"
          @submit.prevent="
            attempts += 1;
            snapshot = JSON.stringify(Object.fromEntries(new FormData($el)));
            submitting = true;
          "
        >
          <c-CField>
            <c-fill name="label">
              Frame ID
            </c-fill>
            <c-fill name="default">
              <c-CInput name="frame" value="M42-L-0084" />
            </c-fill>
          </c-CField>
          <div class="plate-solve__actions">
            <c-CButton
              type="submit"
              $c-props="{ loading: submitting }"
            >
              Solve frame
            </c-CButton>
            <c-CButton
              type="button"
              variant="outline"
              intent="neutral"
              @click="submitting = false"
            >
              Finish request
            </c-CButton>
          </div>
        </c-CForm>

        <p class="plate-solve__status" aria-live="polite">
          Accepted submits: <strong x-text="attempts"></strong>
          <span x-show="snapshot"> · FormData <code x-text="snapshot"></code></span>
        </p>
      </section>
    """

    css = """
      :where(.plate-solve) {
        max-width: 44rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.plate-solve header) {
        margin-block-end: 1rem;
      }

      :where(.plate-solve h2, .plate-solve p) {
        margin-block: 0;
      }

      :where(.plate-solve header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.plate-solve__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
      }

      :where(.plate-solve__status) {
        margin-block-start: 1rem;
        overflow-wrap: anywhere;
        color: color-mix(in srgb, currentColor 72%, transparent);
      }
    """


preview = SubmittingGuard()

preview  # noqa: B018
