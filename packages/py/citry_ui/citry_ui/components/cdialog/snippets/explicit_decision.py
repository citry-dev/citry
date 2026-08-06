import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ExplicitDecision(Component):
    template = """
      <section class="explicit-dialog">
        <p>Telescope alignment</p>
        <h2>Require an explicit decision</h2>
        <c-CDialog c-dismissible="False">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton intent="warn" c-attrs="activator_attrs">
              Recalibrate telescope
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Recalibrate telescope?
          </c-fill>
          <c-fill name="description">
            Observation pauses for about two minutes.
          </c-fill>
          <c-fill name="default">
            Escape, backdrop presses, and the built-in close control are unavailable.
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton variant="outline" c-attrs="close_attrs">
              Keep current alignment
            </c-CButton>
            <c-CButton c-attrs="close_attrs">
              Begin recalibration
            </c-CButton>
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.explicit-dialog) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 44rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#fde68a, #a16207);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.explicit-dialog h2, .explicit-dialog p) {
        margin: 0;
      }

      :where(.explicit-dialog > p) {
        color: light-dark(#a16207, #fde68a);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = ExplicitDecision()

preview  # noqa: B018
