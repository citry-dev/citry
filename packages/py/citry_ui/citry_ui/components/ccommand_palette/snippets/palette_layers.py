from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCommandPaletteCommand

citry.register_library(citry_ui)


class PaletteLayers(Component):
    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "commands": (
                CCommandPaletteCommand(
                    value="show-details",
                    label="Show deployment details",
                    close_on_action=False,
                ),
                CCommandPaletteCommand(value="close-workflow", label="Finish workflow"),
            )
        }

    template = """
      <section
        class="command-palette-layers"
      >
        <h2>Modal and anchored layers</h2>
        <c-CDialog>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open deployment workflow</c-CButton>
          </c-fill>
          <c-fill name="title">Deployment workflow</c-fill>
          <c-fill name="default">
            <div class="command-palette-layers__workflow">
              <div ref="paletteOwner">
                <c-CCommandPalette
                  label="Deployment workflow commands"
                  c-entries="commands"
                  :open="paletteOpen"
                  :onOpenChange="(value) => paletteOpen = value"
                  :onAction="handlePaletteAction"
                >
                  <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                    <c-CButton
                      c-disabled="activator_disabled"
                      c-attrs="activator_attrs"
                    >Open workflow commands</c-CButton>
                  </c-fill>
                </c-CCommandPalette>
              </div>

              <c-CPopover
                :open="popoverOpen"
                :onOpenChange="(value) => popoverOpen = value"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton variant="outline" c-attrs="activator_attrs">Details anchor</c-CButton>
                </c-fill>
                <c-fill name="title">Deployment details</c-fill>
                <c-fill name="default">The latest deployment passed its checks.</c-fill>
              </c-CPopover>
              <button
                type="button"
                @click="removePaletteOwner"
                v-show="!removed"
              >
                Remove palette owner
              </button>
              <output v-text="removed ? 'Palette owner removed' : 'Palette owner present'">
                Palette owner present
              </output>
            </div>
          </c-fill>
        </c-CDialog>
        <div ref="shadowHost" class="command-palette-layers__shadow-host">
          <div ref="shadowFixture">
            <c-CCommandPalette label="ShadowRoot commands" c-entries="commands">
              <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                <c-CButton
                  c-disabled="activator_disabled"
                  c-attrs="activator_attrs"
                >Open ShadowRoot fixture</c-CButton>
              </c-fill>
            </c-CCommandPalette>
          </div>
        </div>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            removed: false,
            paletteOpen: false,
            popoverOpen: false,
          };
        },
        methods: {
          handlePaletteAction(value) {
            if (value === 'show-details') this.popoverOpen = true;
          },
          removePaletteOwner() {
            this.$refs.paletteOwner.remove();
            this.removed = true;
          },
        },
        mounted() {
          this.$nextTick(() => {
            const host = this.$refs.shadowHost;
            const fixture = this.$refs.shadowFixture;
            if (!host.shadowRoot && fixture) {
              host.attachShadow({ mode: 'open' }).append(fixture);
            }
          });
        },
      });
    """

    css = """
      :where(.command-palette-layers) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
      :where(.command-palette-layers h2) { margin: 0; }
      :where(.command-palette-layers__workflow) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }
      :where(.command-palette-layers__shadow-host) {
        display: block;
        padding: 0.75rem;
        border: 1px solid currentColor;
      }
    """


preview = PaletteLayers()

preview  # noqa: B018
