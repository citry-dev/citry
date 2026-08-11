import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledSwitch(Component):
    template = """
      <section class="switch-controlled" x-data="{enabled: true}">
        <c-CSwitch
          $c-props="{checked: enabled}"
          @input="enabled = $event.target.checked"
        >Reading mode</c-CSwitch>
        <output x-text="enabled ? 'Reading mode is on' : 'Reading mode is off'"></output>
      </section>
    """
    css = """
      :where(.switch-controlled) {
        display: grid;
        gap: 0.7rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.switch-controlled output) {
        color: light-dark(#3f6212, #bef264);
        font-size: 0.82rem;
      }
    """


preview = ControlledSwitch()

preview  # noqa: B018
