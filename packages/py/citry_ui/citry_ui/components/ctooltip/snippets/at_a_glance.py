import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TooltipAtAGlance(Component):
    template = """
      <section class="tooltip-sampler">
        <c-CTooltip text="Ocean world beneath fractured ice" placement="top-start">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Europa</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip text="Bright plumes rise above the south pole" placement="top">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">Enceladus</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip text="Dense nitrogen skies conceal methane lakes" placement="top-end">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="ghost" c-attrs="activator_attrs">Titan</c-CButton>
          </c-fill>
        </c-CTooltip>
      </section>
    """

    css = """
      :where(.tooltip-sampler) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }
    """


preview = TooltipAtAGlance()

preview  # noqa: B018
