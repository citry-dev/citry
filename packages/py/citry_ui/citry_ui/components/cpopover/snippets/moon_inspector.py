import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MoonInspector(Component):
    template = """
      <section class="moon-inspector">
        <p>Jovian system</p>
        <h2>Four worlds orbit a striped giant</h2>
        <c-CPopover>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Inspect Europa
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Europa
          </c-fill>
          <c-fill name="description">
            Jupiter II · mean radius 1,560.8 km
          </c-fill>
          <c-fill name="default">
            Its fractured water-ice crust may cover a global saltwater ocean.
          </c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.moon-inspector) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-inline-size: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.moon-inspector h2, .moon-inspector p) {
        margin: 0;
      }

      :where(.moon-inspector > p) {
        color: light-dark(#4338ca, #a5b4fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = MoonInspector()

preview  # noqa: B018
