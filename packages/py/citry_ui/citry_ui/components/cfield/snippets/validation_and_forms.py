import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ValidationAndForms(Component):
    template = """
      <section
        class="shore-form-card"
        x-data
        x-init="Alpine.store('shoreValidation', {
          submitted: '',
          serverInvalid: true,
        })"
      >
        <header>
          <p>Tide alert</p>
          <h2>Register a survey contact</h2>
        </header>

        <c-CForm
          @submit.prevent="$store.shoreValidation.submitted = new FormData($el).get('email')"
          @reset="
            $store.shoreValidation.submitted = '';
            $store.shoreValidation.serverInvalid = false;
          "
        >
          <c-CField required>
            <c-fill name="label">
              Observer email
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="email"
                type="email"
                autocomplete="email"
                placeholder="observer@example.com"
              />
            </c-fill>
            <c-fill name="description">
              Native email validation runs before submission.
            </c-fill>
          </c-CField>

          <c-CField $c-props="{ invalid: $store.shoreValidation.serverInvalid }">
            <c-fill name="label">
              Permit code
            </c-fill>
            <c-fill name="default">
              <c-CInput
                name="permit"
                value="OLD-14"
                @input="$store.shoreValidation.serverInvalid = false"
              />
            </c-fill>
            <c-fill name="error">
              This permit expired at the previous tide cycle.
            </c-fill>
          </c-CField>

          <div class="shore-form-card__actions">
            <button type="submit">Register observer</button>
            <button type="reset">Reset</button>
          </div>
        </c-CForm>

        <p aria-live="polite" x-show="$store.shoreValidation.submitted">
          Registered <strong x-text="$store.shoreValidation.submitted"></strong>
        </p>
      </section>
    """

    css = """
      :where(.shore-form-card) {
        max-width: 38rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.shore-form-card header) {
        margin-block-end: 1rem;
      }

      :where(.shore-form-card h2, .shore-form-card p) {
        margin-block: 0;
      }

      :where(.shore-form-card header p) {
        color: light-dark(#08758a, #69d4e8);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.shore-form-card__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }

      :where(.shore-form-card__actions button) {
        min-height: 2.5rem;
        padding-inline: 0.875rem;
      }
    """


preview = ValidationAndForms()

preview  # noqa: B018
