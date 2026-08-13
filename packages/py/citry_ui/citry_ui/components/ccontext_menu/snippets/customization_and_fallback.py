import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ContextMenuCustomizationAndFallback(Component):
    template = """
      <section
        class="context-menu-customization"
        x-data="{orchardEnhanced:false,harborEnhanced:true}"
      >
        <div class="context-menu-customization__controls">
          <button type="button" @click="orchardEnhanced=!orchardEnhanced">
            Toggle server-disabled Orchard enhancement
          </button>
          <button type="button" @click="harborEnhanced=!harborEnhanced">
            Disable or restore ready Harbor enhancement
          </button>
          <output
            aria-live="polite"
            x-text="`Orchard ${orchardEnhanced ? 'enhanced' : 'native'};
              Harbor ${harborEnhanced ? 'enhanced' : 'native'}`"
          >Orchard native; Harbor enhanced</output>
        </div>

        <div class="context-menu-customization__brands">
          <article class="context-menu-customization__orchard">
            <h3>Orchard</h3>
            <c-CContextMenu
              class_="brand-context-menu"
              aria_label="Orchard file actions"
              c-open="True"
              c-disabled="True"
              c-style="{
                '--cui-menu-radius':'1rem',
                '--cui-menu-focus-background':'#315f37',
              }"
              c-attrs="{'data-quality-brand':'orchard'}"
              $c-props="{disabled:!orchardEnhanced}"
            >
              <c-fill name="target" data="{ target_attrs }">
                <div
                  class="context-menu-customization__file"
                  tabindex="0"
                  c-bind="target_attrs"
                >
                  <strong>Harvest plan.pdf</strong>
                  <span>Server-open fallback</span>
                </div>
              </c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="open">Open file</c-CMenuItem>
                <c-CMenuItem value="archive">Archive file</c-CMenuItem>
              </c-fill>
            </c-CContextMenu>
          </article>

          <article
            class="context-menu-customization__harbor"
            style="color-scheme:dark"
          >
            <h3>Harbor</h3>
            <c-CContextMenu
              class_="brand-context-menu"
              aria_label="Harbor file actions"
              size="lg"
              c-style="{
                '--cui-menu-background':'#173c4c',
                '--cui-menu-foreground':'#eefaff',
                '--cui-menu-border-color':'#72b5ce',
              }"
              c-attrs="{'data-quality-brand':'harbor'}"
              $c-props="{disabled:!harborEnhanced}"
            >
              <c-fill name="target" data="{ target_attrs }">
                <div
                  class="context-menu-customization__file"
                  tabindex="0"
                  c-bind="target_attrs"
                >
                  <strong>Dock schedule.csv</strong>
                  <span>Server-closed fallback</span>
                </div>
              </c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="open">Open file</c-CMenuItem>
                <c-CMenuItem value="remove" intent="danger">Remove file</c-CMenuItem>
              </c-fill>
            </c-CContextMenu>
          </article>
        </div>

        <p>
          Without JavaScript, targets remain ordinary native content. A
          server-closed Menu stays hidden and a server-open Menu remains readable
          in document flow. The browser context menu remains available until a
          valid enhanced request is accepted.
        </p>
      </section>
    """

    css = """
      :where(.context-menu-customization) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-customization__brands) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
      }

      :where(.context-menu-customization__controls) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }

      :where(.context-menu-customization article) {
        display: grid;
        gap: 0.75rem;
        padding: 1rem;
        border-radius: 1rem;
      }

      :where(.context-menu-customization h3,
        .context-menu-customization p) {
        margin: 0;
      }

      :where(.context-menu-customization__orchard) {
        background: #f5f0df;
        color: #203422;
        --cui-menu-background: #fffdf5;
        --cui-menu-foreground: #203422;
        --cui-menu-border-color: #78916d;
      }

      :where(.context-menu-customization__harbor) {
        background: #102b38;
        color: #eefaff;
      }

      :where(.context-menu-customization__file) {
        display: grid;
        gap: 0.25rem;
        padding: 1rem;
        border: 1px solid currentColor;
        border-radius: 0.75rem;
      }

      :where(.context-menu-customization__file:focus-visible) {
        outline: 2px solid Highlight;
        outline-offset: 2px;
      }

      .context-menu-customization
      .brand-context-menu[data-citry-ui-part="context-menu"]
      [data-citry-ui-part="menu"] {
        border-width: 2px;
      }

      @media (forced-colors: active) {
        :where(.context-menu-customization article) {
          border: 1px solid CanvasText;
        }
      }

      @media (prefers-reduced-motion: reduce) {
        :where(.context-menu-customization) {
          scroll-behavior: auto;
        }
      }

      @media print {
        :where(.context-menu-customization article) {
          background: transparent;
          color: black;
        }
      }
    """


preview = ContextMenuCustomizationAndFallback()

preview  # noqa: B018
