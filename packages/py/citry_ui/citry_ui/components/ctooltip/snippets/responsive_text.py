import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ResponsiveTooltipText(Component):
    template = """
      <section class="responsive-tooltips" dir="rtl">
        <c-CTooltip
          text="أوروبا قمر جليدي يخفي محيطًا عالميًا تحت قشرته المتشققة"
          placement="bottom-start"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">أوروبا</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip
          text="Averylongunbrokenastronomicalcatalogidentifierwrapswithoutwideningthepage"
          placement="bottom-end"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">Catalog ID</c-CButton>
          </c-fill>
        </c-CTooltip>
      </section>
    """

    css = """
      :where(.responsive-tooltips) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }

      :where(.responsive-tooltips [data-citry-ui-part="tooltip"]) {
        --cui-tooltip-max-inline-size: 13rem;
      }
    """


preview = ResponsiveTooltipText()

preview  # noqa: B018
