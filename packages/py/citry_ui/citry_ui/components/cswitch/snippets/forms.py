import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SwitchForm(Component):
    template = """
      <form
        class="switch-form"

        @submit.prevent="save($event.target)"
      >
        <c-CSwitch name="quiet_hours" value="enabled" required>Quiet hours</c-CSwitch>
        <c-CRow>
          <c-CButton type="submit">Save home settings</c-CButton>
          <button type="reset">Reset</button>
        </c-CRow>
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
        methods: {
          // An unchecked switch leaves its name out of the form data.
          save(form) {
            const enabled = new window.FormData(form).has('quiet_hours');
            this.result = enabled ? 'Saved' : 'Enable quiet hours';
          },
        },
      });
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
