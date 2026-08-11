"""Shared Tooltip scenario used by Citry UI quality tools."""

from __future__ import annotations

from citry import Citry, Component


def tooltip_states_component(app: Citry) -> type[Component]:
    """Create the reusable Tooltip state catalog."""

    class CitryUiTooltipStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack tooltip-quality"
            aria-labelledby="tooltip-states-title"
            x-data="{ controlledOpen: false, liveText: 'Ocean world' }"
          >
            <h1 id="tooltip-states-title">Tooltip states</h1>
            <div class="tooltip-quality__grid">
              <c-CTooltip id="quality-tooltip" text="Ocean world beneath fractured ice">
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Europa</c-CButton>
                </c-fill>
              </c-CTooltip>
              <c-CTooltip
                id="quality-controlled-tooltip"
                text="Controlled visibility"
                placement="bottom-start"
                $c-props="{
                  open: controlledOpen,
                  text: liveText,
                  onOpenChange: (open) => controlledOpen = open,
                }"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton variant="outline" c-attrs="activator_attrs">Ganymede</c-CButton>
                </c-fill>
              </c-CTooltip>
              <c-CTooltip text="Unavailable visual description" disabled>
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton variant="ghost" c-attrs="activator_attrs">Callisto</c-CButton>
                </c-fill>
              </c-CTooltip>
              <c-CTooltip class_="tooltip-quality__aurora" placement="top-end">
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Aurora brand</c-CButton>
                </c-fill>
                <c-fill name="default">Charged particles paint <strong>green arcs</strong>.</c-fill>
              </c-CTooltip>
              <c-CTooltip
                class_="tooltip-quality__lunar"
                text="Averylongunbrokenastronomicalcatalogidentifierwraps"
                placement="bottom-end"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton variant="outline" c-attrs="activator_attrs">Lunar brand</c-CButton>
                </c-fill>
              </c-CTooltip>
            </div>
          </section>
        """

        css = """
          :where(.tooltip-quality__grid) {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: center;
            min-block-size: 18rem;
            padding-block: 4rem;
          }

          :where(.tooltip-quality__aurora) {
            --cui-tooltip-background: light-dark(#064e3b, #d1fae5);
            --cui-tooltip-foreground: light-dark(#ecfdf5, #052e2b);
            --cui-tooltip-border-color: light-dark(#34d399, #6ee7b7);
          }

          :where(.tooltip-quality__lunar) {
            --cui-tooltip-background: light-dark(#334155, #e2e8f0);
            --cui-tooltip-foreground: light-dark(#f8fafc, #172033);
            --cui-tooltip-border-color: light-dark(#94a3b8, #64748b);
            --cui-tooltip-max-inline-size: 12rem;
          }
        """

    return CitryUiTooltipStates
