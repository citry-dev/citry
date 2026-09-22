import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RadioForm(Component):
    template = """
      <form
        class="radio-form"

        @submit.prevent="result = new window.FormData($event.target).get('plot') || 'Choose a plot'"
      >
        <c-CRadioGroup name="plot" required>
          <c-fill name="label">Planting plot</c-fill>
          <c-fill name="default">
            <c-CRadio value="north">North wall</c-CRadio>
            <c-CRadio value="orchard">Old orchard</c-CRadio>
            <c-CRadio value="pond">Pond margin</c-CRadio>
          </c-fill>
        </c-CRadioGroup>
        <c-CRow><c-CButton type="submit">Reserve plot</c-CButton><button type="reset">Reset</button></c-CRow>
        <output v-text="result"></output>
      </form>
    """
    js = """
      $component({
        data() {
          return {
            result: ''
          };
        },
      });
    """
    css = """
      :where(.radio-form) {
        display: grid;
        gap: 1rem;
        max-inline-size: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = RadioForm()

preview  # noqa: B018
