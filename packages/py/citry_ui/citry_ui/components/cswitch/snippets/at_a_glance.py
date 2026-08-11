import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SwitchAtAGlance(Component):
    template = """
      <section class="switch-room">
        <h2>Evening room</h2>
        <c-CSwitch checked>Reading lamp</c-CSwitch>
        <c-CSwitch>Window shades</c-CSwitch>
        <c-CSwitch checked>
          <c-fill name="default">Quiet ventilation</c-fill>
          <c-fill name="description">Keep air moving below the bedroom.</c-fill>
        </c-CSwitch>
      </section>
    """
    css = """
      :where(.switch-room) {
        display: grid;
        gap: 0.9rem;
        max-inline-size: 28rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c8bda8, #665d50);
        border-radius: 0.9rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.switch-room h2) {
        margin: 0;
      }
    """


preview = SwitchAtAGlance()

preview  # noqa: B018
