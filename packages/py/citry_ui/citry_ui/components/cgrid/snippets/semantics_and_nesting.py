import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GridSemanticsAndNesting(Component):
    template = """
      <c-CContainer
        tag="section"
        class_="mineral-catalog"
        size="md"
        c-attrs="{'aria-labelledby': 'mineral-catalog-title'}"
      >
        <h2 id="mineral-catalog-title">Mineral families</h2>
        <c-CGrid tag="ul" sm="2" class_="mineral-catalog__list">
          <c-CGridItem tag="li">
            <strong>Silicates</strong>
            <c-CGrid cols="2" gap="xs" class_="mineral-catalog__nested">
              <span>Quartz</span><span>Feldspar</span>
            </c-CGrid>
          </c-CGridItem>
          <c-CGridItem tag="li">
            <strong>Carbonates</strong>
            <c-CGrid cols="2" gap="xs" class_="mineral-catalog__nested">
              <span>Calcite</span><span>Dolomite</span>
            </c-CGrid>
          </c-CGridItem>
        </c-CGrid>
      </c-CContainer>
    """

    css = """
      :where(.mineral-catalog) {
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.mineral-catalog h2) {
        margin: 0 0 0.75rem;
        font-size: 0.95rem;
      }

      :where(.mineral-catalog__list) {
        margin: 0;
        padding: 0;
        list-style: none;
      }

      :where(.mineral-catalog__list > li) {
        padding: 0.85rem;
        border: 1px solid light-dark(#d7cfbe, #5e574c);
        border-radius: 0.55rem;
        background: light-dark(#fffaf0, #29251f);
        font-size: 0.78rem;
      }

      :where(.mineral-catalog__nested) {
        margin-block-start: 0.6rem;
      }

      :where(.mineral-catalog__nested span) {
        padding: 0.35rem;
        border-radius: 0.25rem;
        background: light-dark(#e5eee9, #263a32);
        text-align: center;
      }
    """


preview = GridSemanticsAndNesting()

preview  # noqa: B018
