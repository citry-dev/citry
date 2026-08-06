from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableColumn, CTableRow

citry.register_library(citry_ui)


class StickyOverflowTable(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="sticky-tables">
        <article>
          <h2>Bounded catalog</h2>
          <p>Scroll this region in either direction.</p>
          <c-CTable
            c-columns="columns"
            c-rows="rows"
            sticky_header
            layout="fixed"
            style="max-block-size: 16rem; --cui-table-min-width: 54rem"
          >
            <c-fill name="caption">
              Confirmed exoplanets
            </c-fill>
          </c-CTable>
        </article>
        <article>
          <h2>Page-sticky mode</h2>
          <p>The header follows page scroll instead of an inner scroller.</p>
          <c-CTable
                c-columns="columns"
            c-rows="rows"
            sticky_header
            overflow="visible"
          >
            <c-fill name="caption">
              Nearby exoplanets
            </c-fill>
          </c-CTable>
        </article>
      </section>
    """

    css = """
      :where(.sticky-tables) {
        display: grid;
        gap: 1.25rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.sticky-tables article) {
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#bae6fd, #075985);
        border-radius: 0.875rem;
        background: Canvas;
      }

      :where(.sticky-tables h2, .sticky-tables p) {
        margin: 0;
      }

      :where(.sticky-tables p) {
        margin-block: 0.25rem 0.75rem;
        color: color-mix(in srgb, currentColor 68%, transparent);
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        columns = (
            CTableColumn("planet", "Planet", row_header=True, cell_attrs={"style": {"width": "12rem"}}),
            CTableColumn("system", "System", cell_attrs={"style": {"width": "14rem"}}),
            CTableColumn("distance", "Distance", align="end", cell_attrs={"style": {"width": "10rem"}}),
            CTableColumn("period", "Orbital period", align="end", cell_attrs={"style": {"width": "10rem"}}),
        )
        rows = tuple(
            CTableRow(
                key,
                {"planet": planet, "system": system, "distance": distance, "period": period},
            )
            for key, planet, system, distance, period in (
                ("proxima-b", "Proxima Centauri b", "Proxima Centauri", "4.2 ly", "11.2 days"),
                ("barnard-b", "Barnard's Star b", "Barnard's Star", "6.0 ly", "233 days"),
                ("ross-128-b", "Ross 128 b", "Ross 128", "11.0 ly", "9.9 days"),
                ("tau-ceti-e", "Tau Ceti e", "Tau Ceti", "11.9 ly", "163 days"),
                ("gj-1061-d", "GJ 1061 d", "GJ 1061", "12.0 ly", "13.0 days"),
                ("teegarden-b", "Teegarden's Star b", "Teegarden's Star", "12.5 ly", "4.9 days"),
                ("wolf-1061-c", "Wolf 1061 c", "Wolf 1061", "14.1 ly", "17.9 days"),
                ("gliese-667-cc", "Gliese 667 Cc", "Gliese 667 C", "23.6 ly", "28.1 days"),
            )
        )
        return {"columns": columns, "rows": rows}


preview = StickyOverflowTable()

preview  # noqa: B018
