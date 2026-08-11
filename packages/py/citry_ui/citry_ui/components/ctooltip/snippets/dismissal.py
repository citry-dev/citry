import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TooltipDismissal(Component):
    template = """
      <section class="tooltip-dismissal">
        <p>Focus the Button, press Escape, then move focus away and return.</p>
        <c-CTooltip text="Escape closes this description without moving focus">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Europa telemetry</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CButton variant="outline">Next observation</c-CButton>
      </section>
    """

    css = """
      :where(.tooltip-dismissal) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }

      :where(.tooltip-dismissal p) {
        flex-basis: 100%;
        margin: 0;
      }
    """


preview = TooltipDismissal()

preview  # noqa: B018
