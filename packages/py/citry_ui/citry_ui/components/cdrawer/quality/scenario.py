"""Shared Drawer scenario used by Citry UI quality tools."""

from __future__ import annotations

from citry import Citry, Component


def drawer_states_component(app: Citry) -> type[Component]:
    """Create the reusable Drawer state catalog."""

    class CitryUiDrawerStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack drawer-quality"
            aria-labelledby="drawer-states-title"
            x-data="{ controlledOpen: false }"
          >
            <h1 id="drawer-states-title">Drawer states</h1>
            <div class="drawer-quality__grid">
              <c-CDrawer
                id="quality-drawer"
                c-attrs="{
                  'data-quality-states':
                    'closed open dismissible form nested inline-end md body'
                }"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton c-attrs="activator_attrs">Edit observatory note</c-CButton>
                </c-fill>
                <c-fill name="title">Observatory note</c-fill>
                <c-fill name="description">Update the shared observing log.</c-fill>
                <c-fill name="default">
                  <form id="quality-drawer-form">
                    <label for="quality-drawer-note">Note</label>
                    <input id="quality-drawer-note" name="note" value="Clear horizon" />
                  </form>
                  <c-CDrawer id="quality-nested-drawer" size="sm" placement="block-end">
                    <c-fill name="activator" data="{ activator_attrs }">
                      <c-CButton variant="outline" c-attrs="activator_attrs">
                        Review coordinates
                      </c-CButton>
                    </c-fill>
                    <c-fill name="title">Coordinates</c-fill>
                    <c-fill name="default">48.2082 N, 16.3738 E</c-fill>
                  </c-CDrawer>
                </c-fill>
                <c-fill name="actions" data="{ close_attrs }">
                  <c-CButton variant="outline" c-attrs="close_attrs">Cancel</c-CButton>
                  <c-CButton>Save note</c-CButton>
                </c-fill>
              </c-CDrawer>

              <c-CDrawer
                id="quality-sheet"
                placement="block-end"
                size="lg"
                scroll="drawer"
                c-dismissible="False"
                $c-props="{
                  open: controlledOpen,
                  onOpenChange: (open) => controlledOpen = open,
                }"
                c-attrs="{
                  'data-quality-states':
                    'controlled persistent block-end lg drawer-scroll long-content'
                }"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton variant="outline" c-attrs="activator_attrs">
                    Open observing protocol
                  </c-CButton>
                </c-fill>
                <c-fill name="title">Observing protocol</c-fill>
                <c-fill name="description">Explicit acknowledgement is required.</c-fill>
                <c-fill name="default">
                  <c-for each="paragraph in paragraphs">
                    <p>{{ paragraph }}</p>
                  </c-for>
                </c-fill>
                <c-fill name="actions" data="{ close_attrs }">
                  <c-CButton c-attrs="close_attrs">Acknowledge</c-CButton>
                </c-fill>
              </c-CDrawer>

              <div class="drawer-quality__aurora" dir="rtl">
                <c-CDrawer
                  id="quality-branded-drawer"
                  placement="inline-start"
                  size="sm"
                  c-attrs="{'data-quality-states': 'brand-aurora rtl inline-start sm'}"
                >
                  <c-fill name="activator" data="{ activator_attrs }">
                    <c-CButton variant="outline" c-attrs="activator_attrs">
                      Aurora settings
                    </c-CButton>
                  </c-fill>
                  <c-fill name="title">Aurora settings</c-fill>
                  <c-fill name="default">Tune the green-band exposure.</c-fill>
                </c-CDrawer>
              </div>
            </div>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
                "paragraphs": tuple(
                    f"Protocol {index}: Verify the instrument clock and record the horizon." for index in range(1, 9)
                )
            }

        css = """
          :where(.drawer-quality__grid) {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: center;
          }

          :where(.drawer-quality form) {
            display: grid;
            gap: 0.5rem;
          }

          :where(.drawer-quality__aurora) {
            --cui-drawer-background: light-dark(#ecfdf5, #052e2b);
            --cui-drawer-foreground: light-dark(#064e3b, #d1fae5);
            --cui-drawer-border-color: light-dark(#6ee7b7, #34d399);
          }
        """

    return CitryUiDrawerStates
