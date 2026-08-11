"""Shared Menu scenario used by Citry UI quality tools."""

from __future__ import annotations

from citry import Citry, Component


def menu_states_component(app: Citry) -> type[Component]:
    """Create the reusable Menu state catalog."""

    class CitryUiMenuStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack menu-quality"
            aria-labelledby="menu-states-title"
            x-data="{controlledOpen: false, formSubmits: 0}"
          >
            <h1 id="menu-states-title">Menu states</h1>
            <div class="menu-quality__grid">
              <form @submit.prevent="formSubmits += 1">
                <c-CMenu
                  id="quality-menu"
                  c-close_on_select="False"
                  c-attrs="{
                    'data-quality-states':
                      'closed open commands links choices groups separator submenu two-level danger form-safe'
                  }"
                >
                  <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                    <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Open archive index</c-CButton>
                  </c-fill>
                  <c-fill name="default">
                    <c-CMenuItem value="copy">Copy citation</c-CMenuItem>
                    <c-CMenuItem href="#quality-catalog">Open public catalog</c-CMenuItem>
                    <c-CMenuCheckboxItem value="glow" checked="mixed">
                      Illuminate marginalia
                    </c-CMenuCheckboxItem>
                    <c-CMenuRadioGroup value="elvish">
                      <c-fill name="label">Reading script</c-fill>
                      <c-fill name="default">
                        <c-CMenuRadioItem value="elvish">Elvish</c-CMenuRadioItem>
                        <c-CMenuRadioItem value="celestial">Celestial</c-CMenuRadioItem>
                      </c-fill>
                    </c-CMenuRadioGroup>
                    <c-CMenuSeparator />
                    <c-CMenuGroup>
                      <c-fill name="label">Restricted shelves</c-fill>
                      <c-fill name="default">
                        <c-CMenuItem value="sealed" disabled>Sealed prophecies</c-CMenuItem>
                        <c-CMenuSubmenu value="mythic">
                          <c-fill name="label">Mythic collections</c-fill>
                          <c-fill name="default">
                            <c-CMenuItem value="dragons">Dragon chronicles</c-CMenuItem>
                            <c-CMenuSubmenu value="moons">
                              <c-fill name="label">Moon records</c-fill>
                              <c-fill name="default">
                                <c-CMenuItem value="silver">Silver moon</c-CMenuItem>
                              </c-fill>
                            </c-CMenuSubmenu>
                          </c-fill>
                        </c-CMenuSubmenu>
                      </c-fill>
                    </c-CMenuGroup>
                    <c-CMenuItem value="banish" intent="danger">Banish record</c-CMenuItem>
                  </c-fill>
                </c-CMenu>
                <button type="submit">Submit native Form</button>
                <output x-text="`Submits: ${formSubmits}`">Submits: 0</output>
              </form>

              <c-CMenu
                id="quality-controlled-menu"
                c-loop="False"
                match_width
                size="sm"
                $c-props="{
                  open: controlledOpen,
                  onOpenChange: (open) => controlledOpen = open,
                }"
                c-attrs="{'data-quality-states': 'controlled loop-false match-width sm'}"
              >
                <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                  <c-CButton
                    size="sm"
                    c-disabled="activator_disabled"
                    c-attrs="activator_attrs"
                  >Controlled index</c-CButton>
                </c-fill>
                <c-fill name="default">
                  <c-CMenuItem value="stars">Star index</c-CMenuItem>
                  <c-CMenuItem value="tides">Tide index</c-CMenuItem>
                </c-fill>
              </c-CMenu>

              <fieldset disabled>
                <legend>Sealed desk</legend>
                <c-CMenu
                  id="quality-disabled-menu"
                  size="lg"
                  c-attrs="{'data-quality-states': 'disabled fieldset-disabled lg'}"
                >
                  <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                    <c-CButton
                      size="lg"
                      c-disabled="activator_disabled"
                      c-attrs="activator_attrs"
                    >Desk commands</c-CButton>
                  </c-fill>
                  <c-fill name="default">
                    <c-CMenuItem value="catalog">Catalog folio</c-CMenuItem>
                  </c-fill>
                </c-CMenu>
              </fieldset>

              <div class="menu-quality__moon">
                <c-CMenu c-attrs="{'data-quality-states': 'brand-moon md'}">
                  <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                    <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Moon archive</c-CButton>
                  </c-fill>
                  <c-fill name="default">
                    <c-CMenuItem value="phases">Moon phases</c-CMenuItem>
                    <c-CMenuItem value="eclipses">Eclipse records</c-CMenuItem>
                  </c-fill>
                </c-CMenu>
              </div>

              <div class="menu-quality__ember" dir="rtl">
                <c-CMenu
                  placement="top-end"
                  c-attrs="{'data-quality-states': 'brand-ember rtl placement'}"
                >
                  <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                    <c-CButton
                      variant="outline"
                      c-disabled="activator_disabled"
                      c-attrs="activator_attrs"
                    >Ember archive</c-CButton>
                  </c-fill>
                  <c-fill name="default">
                    <c-CMenuItem value="dragons">Dragon chronicles</c-CMenuItem>
                    <c-CMenuItem value="ashes" intent="danger">Destroy ash record</c-CMenuItem>
                  </c-fill>
                </c-CMenu>
              </div>
            </div>
          </section>
        """

        css = """
          :where(.menu-quality__grid) {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            align-items: start;
            min-block-size: 28rem;
          }

          :where(.menu-quality form, .menu-quality fieldset) {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            align-items: center;
          }

          :where(.menu-quality__moon) {
            --cui-menu-background: light-dark(#f4f2ff, #17142d);
            --cui-menu-foreground: light-dark(#261d53, #f1edff);
            --cui-menu-border-color: light-dark(#8f83c7, #7065aa);
            --cui-menu-focus-background: light-dark(#4c3e92, #b6a9ff);
            --cui-menu-focus-foreground: light-dark(#ffffff, #17142d);
          }

          :where(.menu-quality__ember) {
            --cui-menu-background: light-dark(#fff7ed, #2a1710);
            --cui-menu-foreground: light-dark(#57270d, #ffedd5);
            --cui-menu-border-color: light-dark(#d97706, #f59e0b);
            --cui-menu-focus-background: light-dark(#9a3412, #fdba74);
            --cui-menu-focus-foreground: light-dark(#ffffff, #2a1710);
          }
        """

    return CitryUiMenuStates
