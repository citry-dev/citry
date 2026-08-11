import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MoonLabels(Component):
    template = """
      <section class="moon-labels">
        <c-CTooltip text="Inspect Europa's fractured water-ice crust">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Europa</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip text="Compare Ganymede's ancient grooved terrain">
          <c-fill name="activator" data="{ activator_attrs }">
            <a id="ganymede" class="moon-link" href="#ganymede" c-bind="activator_attrs">
              Ganymede
            </a>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip text="Filter observations recorded near Callisto">
          <c-fill name="activator" data="{ activator_attrs }">
            <button class="moon-icon" type="button" aria-label="Filter Callisto" c-bind="activator_attrs">
              ◌
            </button>
          </c-fill>
        </c-CTooltip>
      </section>
    """

    css = """
      :where(.moon-labels) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
        min-block-size: 10rem;
        padding-block: 2rem;
      }

      :where(.moon-link) {
        color: light-dark(#175cd3, #84adff);
        font-weight: 700;
      }

      :where(.moon-icon) {
        display: grid;
        place-items: center;
        inline-size: 2.75rem;
        block-size: 2.75rem;
        border: 1px solid color-mix(in srgb, CanvasText 24%, transparent);
        border-radius: 50%;
        background: Canvas;
        color: CanvasText;
        font-size: 1.5rem;
      }
    """


preview = MoonLabels()

preview  # noqa: B018
