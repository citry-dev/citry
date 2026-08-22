import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SwitchForm(Component):
    template = """
      <form
        class="switch-form"
        x-data="{result: ''}"
        @submit.prevent="result = new FormData($event.target).has('quiet_hours') ? 'Saved' : 'Enable quiet hours'"
      >
        <c-CSwitch name="quiet_hours" value="enabled" required>Quiet hours</c-CSwitch>
        <c-CRow>
          <c-CButton type="submit">Save home settings</c-CButton>
          <button type="reset">Reset</button>
        </c-CRow>
        <output x-text="result"></output>
      </form>
    """
    css = """
      :where(.switch-form) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = SwitchForm()

preview  # noqa: B018
