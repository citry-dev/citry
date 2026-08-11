import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TooltipTiming(Component):
    template = """
      <section class="tooltip-timing">
        <c-CTooltip text="Opens after the standard 600 ms hover delay">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Standard delay</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip text="Opens without an initial hover delay" c-delay="0">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">Immediate</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip text="A longer bridge makes the surface easier to reach" c-close_delay="500">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="ghost" c-attrs="activator_attrs">Long bridge</c-CButton>
          </c-fill>
        </c-CTooltip>
      </section>
    """

    css = """
      :where(.tooltip-timing) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }
    """


preview = TooltipTiming()

preview  # noqa: B018
