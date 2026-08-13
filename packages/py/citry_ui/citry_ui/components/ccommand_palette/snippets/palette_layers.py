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
        x-data="{removed:false}"
        x-init="
          Alpine.store('commandPaletteLayers', {paletteOpen:false,popoverOpen:false});
          $nextTick(() => {
          const host=$refs.shadowHost;
          const fixture=$refs.shadowFixture;
          if (!host.shadowRoot && fixture) {
            Alpine.destroyTree(fixture);
            host.attachShadow({mode:'open'}).append(fixture);
            Alpine.initTree(fixture);
          }
          })
        "
      >
        <h2>Modal and anchored layers</h2>
        <c-CDialog>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open deployment workflow</c-CButton>
          </c-fill>
          <c-fill name="title">Deployment workflow</c-fill>
          <c-fill name="default">
            <div class="command-palette-layers__workflow">
              <div x-ref="paletteOwner">
                <c-CCommandPalette
                  label="Deployment workflow commands"
                c-entries="commands"
                $c-props="{
                  open:$store.commandPaletteLayers.paletteOpen,
                  onOpenChange:(value)=>$store.commandPaletteLayers.paletteOpen=value,
                  onAction:(value)=>{
                    if (value==='show-details') $store.commandPaletteLayers.popoverOpen=true;
                  },
                    }"
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
                $c-props="{
                  open:$store.commandPaletteLayers.popoverOpen,
                  onOpenChange:(value)=>$store.commandPaletteLayers.popoverOpen=value,
                }"
              >
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton variant="outline" c-attrs="activator_attrs">Details anchor</c-CButton>
                </c-fill>
                <c-fill name="title">Deployment details</c-fill>
                <c-fill name="default">The latest deployment passed its checks.</c-fill>
              </c-CPopover>
              <button
                type="button"
                @click="$refs.paletteOwner.remove(); removed=true"
                x-show="!removed"
              >Remove palette owner</button>
              <output x-text="removed ? 'Palette owner removed' : 'Palette owner present'">
                Palette owner present
              </output>
            </div>
          </c-fill>
        </c-CDialog>
        <div x-ref="shadowHost" class="command-palette-layers__shadow-host">
          <div x-ref="shadowFixture">
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
