import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NarrowDialog(Component):
    template = """
      <section class="narrow-dialog-demo">
        <p>Mobile star atlas</p>
        <h2>Fill a narrow viewport</h2>
        <c-CDialog size="full">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Open full atlas
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            The complete guide to circumpolar constellations
          </c-fill>
          <c-fill name="description">
            Full size uses the dynamic viewport and keeps actions reachable.
          </c-fill>
          <c-fill name="default">
            <p>
              Ursa Major, Ursa Minor, Cassiopeia, Cepheus, and Draco remain
              above the horizon throughout the year at northern latitudes.
            </p>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton variant="outline" c-attrs="close_attrs">
              Return to chart
            </c-CButton>
            <c-CButton>
              Mark visible stars
            </c-CButton>
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.narrow-dialog-demo) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 40rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bae6fd, #0369a1);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.narrow-dialog-demo h2, .narrow-dialog-demo p) {
        margin: 0;
      }

      :where(.narrow-dialog-demo > p) {
        color: light-dark(#0369a1, #7dd3fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = NarrowDialog()

preview  # noqa: B018
