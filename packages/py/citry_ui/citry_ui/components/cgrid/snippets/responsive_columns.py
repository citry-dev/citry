import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GridResponsiveColumns(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="grid-columns" aria-labelledby="grid-columns-title">
        <h2 id="grid-columns-title">Crystal systems</h2>
        <p>Resize the preview to watch one column become two, then four.</p>
        <c-CGrid sm="2" lg="4" gap="sm">
          <c-for each="system in systems">
            <div class="grid-columns__cell">{{ system }}</div>
          </c-for>
        </c-CGrid>
        <h3>Fixed three-column index</h3>
        <c-CGrid cols="3" gap="sm">
          <c-for each="name in fixed_names">
            <div class="grid-columns__cell grid-columns__cell--quiet">{{ name }}</div>
          </c-for>
        </c-CGrid>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "systems": ("Cubic", "Hexagonal", "Monoclinic", "Trigonal"),
            "fixed_names": ("Quartz", "Calcite", "Galena"),
        }

    css = """
      :where(.grid-columns) {
        max-inline-size: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.grid-columns h2, .grid-columns h3, .grid-columns p) {
        margin: 0;
      }

      :where(.grid-columns h2) {
        font-size: 1rem;
      }

      :where(.grid-columns h3) {
        margin-block-start: 1.25rem;
        margin-block-end: 0.5rem;
        font-size: 0.82rem;
      }

      :where(.grid-columns p) {
        margin-block: 0.25rem 0.8rem;
        color: GrayText;
        font-size: 0.78rem;
      }

      :where(.grid-columns__cell) {
        min-block-size: 3.25rem;
        padding: 0.7rem;
        border-inline-start: 0.3rem solid #4b77be;
        border-radius: 0.35rem;
        background: light-dark(#edf4ff, #1c2b40);
        font-size: 0.78rem;
        font-weight: 700;
      }

      :where(.grid-columns__cell--quiet) {
        border-inline-start-color: #a55f38;
        background: light-dark(#faf0e9, #35241c);
      }
    """


preview = GridResponsiveColumns()

preview  # noqa: B018
