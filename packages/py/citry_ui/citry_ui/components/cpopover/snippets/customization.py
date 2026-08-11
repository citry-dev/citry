import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedPopover(Component):
    template = """
      <section class="custom-popovers">
        <c-CPopover class_="aurora-popover">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Aurora palette</c-CButton>
          </c-fill>
          <c-fill name="title">Auroral oval</c-fill>
          <c-fill name="default">Charged particles paint green arcs above the poles.</c-fill>
        </c-CPopover>
        <c-CPopover class_="lunar-popover">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">Lunar palette</c-CButton>
          </c-fill>
          <c-fill name="title">Lunar highlands</c-fill>
          <c-fill name="default">Ancient pale terrain surrounds younger dark maria.</c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.custom-popovers) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }

      :where(.aurora-popover) {
        --cui-popover-background: light-dark(#ecfdf5, #052e2b);
        --cui-popover-foreground: light-dark(#064e3b, #d1fae5);
        --cui-popover-border-color: light-dark(#6ee7b7, #34d399);
        --cui-popover-radius: 1.25rem;
      }

      :where(.lunar-popover) {
        --cui-popover-background: light-dark(#f8fafc, #172033);
        --cui-popover-foreground: light-dark(#1e293b, #f1f5f9);
        --cui-popover-border-color: light-dark(#94a3b8, #64748b);
        --cui-popover-shadow: 0 1.25rem 2.75rem rgb(15 23 42 / 30%);
      }
    """


preview = CustomizedPopover()

preview  # noqa: B018
