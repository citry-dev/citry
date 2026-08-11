"""Shared Popover scenario used by Citry UI quality tools."""

from __future__ import annotations

from citry import Citry, Component


def popover_states_component(app: Citry) -> type[Component]:
    """Create the reusable Popover state catalog."""

    class CitryUiPopoverStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack popover-quality"
            aria-labelledby="popover-states-title"
            x-data="{ controlledOpen: false }"
          >
            <h1 id="popover-states-title">
              Popover states
            </h1>
            <div class="popover-quality__grid">
              <c-CPopover id="quality-popover">
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">
                    Inspect Europa
                  </c-CButton>
                </c-fill>
                <c-fill name="title">Europa</c-fill>
                <c-fill name="description">Jupiter II</c-fill>
                <c-fill name="default">
                  <form id="quality-popover-form">
                    <label for="quality-depth">Ocean depth</label>
                    <input id="quality-depth" name="depth" value="100 km" />
                  </form>
                  <c-CPopover id="quality-nested-popover" placement="bottom-end">
                    <c-fill name="activator" data="{ activator_attrs }">
                      <c-CButton size="sm" variant="outline" c-attrs="activator_attrs">
                        Inspect plume
                      </c-CButton>
                    </c-fill>
                    <c-fill name="title">Water plume</c-fill>
                    <c-fill name="default">Candidate vapor above the ice.</c-fill>
                  </c-CPopover>
                </c-fill>
                <c-fill name="actions" data="{ close_attrs }">
                  <c-CButton c-attrs="close_attrs">Close</c-CButton>
                </c-fill>
              </c-CPopover>
              <c-CPopover
                id="quality-controlled-popover"
                c-dismissible="False"
                placement="top"
                match_width
                $c-props="{
                  open: controlledOpen,
                  onOpenChange: (open) => controlledOpen = open,
                }"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton variant="outline" c-attrs="activator_attrs">
                    Mission protocol
                  </c-CButton>
                </c-fill>
                <c-fill name="title">Mission protocol</c-fill>
                <c-fill name="default">Explicit acknowledgment is required.</c-fill>
                <c-fill name="actions" data="{ close_attrs }">
                  <c-CButton c-attrs="close_attrs">Acknowledge</c-CButton>
                </c-fill>
              </c-CPopover>
              <c-CPopover class_="popover-quality__aurora" placement="top-start">
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Aurora brand</c-CButton>
                </c-fill>
                <c-fill name="title">Auroral oval</c-fill>
                <c-fill name="default">Green arcs above the magnetic pole.</c-fill>
              </c-CPopover>
              <c-CPopover class_="popover-quality__lunar" placement="bottom-end">
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton variant="outline" c-attrs="activator_attrs">
                    Lunar brand
                  </c-CButton>
                </c-fill>
                <c-fill name="title">Lunar highlands</c-fill>
                <c-fill name="default">Ancient pale terrain surrounds dark maria.</c-fill>
              </c-CPopover>
            </div>
          </section>
        """

        css = """
          :where(.popover-quality__grid) {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            align-items: center;
            min-block-size: 18rem;
            padding-block: 4rem;
          }

          :where(.popover-quality__aurora) {
            --cui-popover-background: light-dark(#ecfdf5, #052e2b);
            --cui-popover-foreground: light-dark(#064e3b, #d1fae5);
            --cui-popover-border-color: light-dark(#6ee7b7, #34d399);
          }

          :where(.popover-quality__lunar) {
            --cui-popover-background: light-dark(#f8fafc, #172033);
            --cui-popover-foreground: light-dark(#1e293b, #f1f5f9);
            --cui-popover-border-color: light-dark(#94a3b8, #64748b);
          }
        """

    return CitryUiPopoverStates
