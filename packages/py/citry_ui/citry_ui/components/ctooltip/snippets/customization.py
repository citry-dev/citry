import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedTooltip(Component):
    template = """
      <section class="custom-tooltips">
        <c-CTooltip text="Charged particles paint green arcs" class_="aurora-tooltip">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Auroral oval</c-CButton>
          </c-fill>
        </c-CTooltip>
        <c-CTooltip text="Ancient pale terrain surrounds dark maria" class_="lunar-tooltip">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">Lunar highlands</c-CButton>
          </c-fill>
        </c-CTooltip>
      </section>
    """

    css = """
      :where(.custom-tooltips) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }

      :where(.aurora-tooltip) {
        --cui-tooltip-background: light-dark(#064e3b, #d1fae5);
        --cui-tooltip-foreground: light-dark(#ecfdf5, #052e2b);
        --cui-tooltip-border-color: light-dark(#34d399, #6ee7b7);
        --cui-tooltip-radius: 1rem;
      }

      :where(.lunar-tooltip) {
        --cui-tooltip-background: light-dark(#334155, #e2e8f0);
        --cui-tooltip-foreground: light-dark(#f8fafc, #172033);
        --cui-tooltip-border-color: light-dark(#94a3b8, #64748b);
        --cui-tooltip-shadow: 0 0.75rem 2rem rgb(15 23 42 / 30%);
      }
    """


preview = CustomizedTooltip()

preview  # noqa: B018
