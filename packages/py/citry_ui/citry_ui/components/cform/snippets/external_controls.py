import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ExternalControls(Component):
    template = """
      <section
        class="proposal-form"
        x-data="{ disabled: false, result: '' }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p>Time allocation</p>
          <h2>Submit a telescope proposal</h2>
        </header>

        <c-CForm
          id="proposal-form"
          $c-props="{ disabled }"
          @submit.prevent="
            result = JSON.stringify(
              Object.fromEntries(new FormData($el, $event.submitter))
            )
          "
        >
          <c-CField required>
            <c-fill name="label">
              Proposal title
            </c-fill>
            <c-fill name="default">
              <c-CInput name="title" value="Atmospheres of nearby super-Earths" />
            </c-fill>
          </c-CField>
          <c-CButton type="submit">
            Submit proposal
          </c-CButton>
        </c-CForm>

        <div class="proposal-form__external">
          <label for="allocation-code">External allocation code</label>
          <c-CInput
            id="allocation-code"
            name="allocation"
            value="Q4-NORTH"
            c-attrs="{'form': 'proposal-form'}"
          />
          <small>Owned by the Form, but outside its disabled fieldset.</small>
          <c-CButton
            type="submit"
            variant="outline"
            intent="neutral"
            c-attrs="{
              'form': 'proposal-form',
              'name': 'intent',
              'value': 'external',
            }"
          >
            Submit from outside
          </c-CButton>
        </div>

        <output
          aria-live="polite"
          x-show="result"
          x-text="result"
        ></output>
      </section>
    """

    css = """
      :where(.proposal-form) {
        display: grid;
        gap: 1rem;
        max-width: 46rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.proposal-form h2, .proposal-form p) {
        margin-block: 0;
      }

      :where(.proposal-form header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.proposal-form [data-citry-ui-part="button"]) {
        justify-self: start;
      }

      :where(.proposal-form__external) {
        display: grid;
        gap: 0.4rem;
        padding: 0.875rem;
        border-inline-start: 0.25rem solid light-dark(#6d5bd0, #a9a2ff);
        background: light-dark(#f7f6ff, #24233b);
      }

      :where(.proposal-form__external label) {
        font-weight: 650;
      }

      :where(.proposal-form__external small) {
        color: color-mix(in srgb, currentColor 68%, transparent);
      }

      :where(.proposal-form__external [data-citry-ui-part="button"]) {
        justify-self: start;
      }

      :where(.proposal-form output) {
        overflow-wrap: anywhere;
      }
    """


preview_controls = (
    {
        "name": "disabled",
        "label": "Disable internal controls",
        "type": "checkbox",
        "default": False,
    },
)

preview = ExternalControls()

preview  # noqa: B018
