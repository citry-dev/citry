import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class LaunchDestinationForm(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section
        class="launch-form"
        x-data="{ result: 'No route submitted.' }"
      >
        <header>
          <p>Flight plan</p>
          <h2>Choose a launch destination</h2>
        </header>
        <c-CForm
          @submit.prevent="result = `Route: ${new FormData($el).get('destination_id')}`"
          @reset="result = 'Flight plan reset.'"
        >
          <c-CField required>
            <c-fill name="label">
              Destination
            </c-fill>
            <c-fill name="default">
              <c-CCombobox
                name="destination_id"
                c-options="destinations"
                value="luna"
              />
            </c-fill>
            <c-fill name="error">
              Choose a destination from the route catalog.
            </c-fill>
          </c-CField>
          <div class="launch-form__actions">
            <c-CButton type="submit">
              Submit route
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
        <p
          class="launch-form__result"
          aria-live="polite"
          x-text="result"
        >
          No route submitted.
        </p>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "destinations": (
                citry_ui.CComboboxOption("luna", "Lunar orbit", "Three-day transfer"),
                citry_ui.CComboboxOption("mars", "Mars transfer", "Hohmann transfer window"),
                citry_ui.CComboboxOption("europa", "Europa flyby", "Outer-system gravity assists"),
            )
        }

    css = """
      :where(.launch-form) {
        max-width: 36rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bae6fd, #0c4a6e);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.launch-form header) {
        margin-block-end: 1rem;
      }

      :where(.launch-form h2, .launch-form p) {
        margin: 0;
      }

      :where(.launch-form header p) {
        margin-block-end: 0.3rem;
        color: light-dark(#0369a1, #7dd3fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.launch-form__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
        margin-block-start: 1rem;
      }

      :where(.launch-form__result) {
        margin-block-start: 1rem;
        color: color-mix(in srgb, currentColor 70%, transparent);
        font-size: 0.875rem;
      }
    """


preview = LaunchDestinationForm()

preview  # noqa: B018
