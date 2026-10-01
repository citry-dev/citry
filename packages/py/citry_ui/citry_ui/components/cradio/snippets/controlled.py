import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledRadios(Component):
    template = """
      <section class="radio-controlled" >
        <c-CRadioGroup
          name="groundcover"
          :value="value"
          @input="value = $event.target.value"
          orientation="horizontal"
        >
          <c-fill name="label">Ground cover</c-fill>
          <c-fill name="default">
            <c-CRadio value="moss">Moss</c-CRadio>
            <c-CRadio value="thyme">Creeping thyme</c-CRadio>
            <c-CRadio value="clover">Microclover</c-CRadio>
          </c-fill>
        </c-CRadioGroup>
        <output v-text="`Selected: ${value}`"></output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            value: 'moss'
          };
        },
      });
    """
    css = """
      :where(.radio-controlled) {
        display: grid;
        gap: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.radio-controlled output) {
        color: light-dark(#3f6212, #bef264);
        font-size: 0.8rem;
      }
    """


preview = ControlledRadios()

preview  # noqa: B018
