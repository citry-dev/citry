import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledSwitch(Component):
    template = """
      <section class="switch-controlled" >
        <c-CSwitch
          :checked="enabled"
          @input="enabled = $event.target.checked"
        >Reading mode</c-CSwitch>
        <output v-text="enabled ? 'Reading mode is on' : 'Reading mode is off'"></output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            enabled: true
          };
        },
      });
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
