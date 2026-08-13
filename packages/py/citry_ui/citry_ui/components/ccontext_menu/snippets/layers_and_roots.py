import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ContextMenuLayersAndRoots(Component):
    template = """
      <section
        class="context-menu-layers"
        x-data="{
          last:'No layer request yet',
          counterTick:0,
        }"
      >
        <article>
          <h3>Deepest target wins</h3>
          <c-CContextMenu
            aria_label="Outer card actions"
            $c-props="{
              onOpenChange:(next,detail)=>last=
                `outer ${next ? 'open' : 'close'} ${detail.reason}`,
            }"
          >
            <c-fill name="target" data="{ target_attrs }">
              <div
                class="context-menu-layers__outer"
                tabindex="0"
                c-bind="target_attrs"
              >
                Outer card
                <c-CContextMenu
                  aria_label="Inner badge actions"
                  $c-props="{
                    onOpenChange:(next,detail)=>last=
                      `inner ${next ? 'open' : 'close'} ${detail.reason}`,
                  }"
                >
                  <c-fill name="target" data="{ target_attrs as inner_target_attrs }">
                    <span
                      class="context-menu-layers__inner"
                      tabindex="0"
                      c-bind="inner_target_attrs"
                    >Inner badge</span>
                  </c-fill>
                  <c-fill name="menu">
                    <c-CMenuItem value="inspect-badge">Inspect badge</c-CMenuItem>
                  </c-fill>
                </c-CContextMenu>
              </div>
            </c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="inspect-card">Inspect card</c-CMenuItem>
            </c-fill>
          </c-CContextMenu>
        </article>

        <article>
          <h3>Inside another anchored layer</h3>
          <c-CPopover>
            <c-fill name="activator" data="{ activator_attrs }">
              <c-CButton c-attrs="activator_attrs">Open inspector</c-CButton>
            </c-fill>
            <c-fill name="title">Record inspector</c-fill>
            <c-fill name="default">
              <c-CContextMenu
                aria_label="Inspector row actions"
                c-attrs="{'data-context-menu-removable':''}"
              >
                <c-fill name="target" data="{ target_attrs }">
                  <div
                    class="context-menu-layers__popover-target"
                    tabindex="0"
                    c-bind="target_attrs"
                  >Row inside Popover</div>
                </c-fill>
                <c-fill name="menu">
                  <c-CMenuItem value="open-row">Open row</c-CMenuItem>
                  <c-CMenuItem value="archive-row">Archive row</c-CMenuItem>
                </c-fill>
              </c-CContextMenu>
            </c-fill>
          </c-CPopover>
          <button
            type="button"
            @click="
              document.querySelector('[data-context-menu-removable]')?.remove();
              last='nested ContextMenu removed'
            "
          >Remove nested ContextMenu</button>
          <button type="button" @click="location.reload()">
            Restore the fixture, then repeat the cycle
          </button>

          <c-CContextMenu aria_label="Tooltip target actions">
            <c-fill name="target" data="{ target_attrs }">
              <div class="context-menu-layers__popover-target" c-bind="target_attrs">
                <c-CTooltip text="This descendant shares Tooltip layer ancestry">
                  <c-fill name="activator" data="{ activator_attrs }">
                    <c-CButton
                      size="sm"
                      variant="outline"
                      c-attrs="activator_attrs"
                    >Tooltip-bound target</c-CButton>
                  </c-fill>
                </c-CTooltip>
              </div>
            </c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="inspect-tooltip-target">
                Inspect Tooltip target
              </c-CMenuItem>
            </c-fill>
          </c-CContextMenu>

          <c-CMenu>
            <c-fill name="activator" data="{ activator_attrs }">
              <c-CButton size="sm" variant="outline" c-attrs="activator_attrs">
                Open sibling Menu
              </c-CButton>
            </c-fill>
            <c-fill name="default">
              <c-CMenuItem value="ordinary-menu-command">
                Ordinary Menu command
              </c-CMenuItem>
              <c-CMenuItem href="#context-menu-menu-native-link">
                Native link in Menu
              </c-CMenuItem>
            </c-fill>
          </c-CMenu>
          <p id="context-menu-menu-native-link">
            Right click inside the open Menu to keep the browser path rather
            than reinvoking ContextMenu.
          </p>
        </article>

        <article
          x-data
          x-init="$nextTick(()=>{
            const shadow=$refs.shadowHost.attachShadow({mode:'open'});
            document.querySelectorAll('style').forEach(
              (style)=>shadow.append(style.cloneNode(true))
            );
            shadow.append($refs.shadowFixture);
          })"
        >
          <h3>Open ShadowRoot scope</h3>
          <div x-ref="shadowFixture">
            <c-CContextMenu aria_label="Shadow record actions">
              <c-fill name="target" data="{ target_attrs }">
                <button
                  class="context-menu-layers__shadow-target"
                  type="button"
                  c-bind="target_attrs"
                >ShadowRoot target</button>
              </c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="inspect-shadow">Inspect shadow record</c-CMenuItem>
              </c-fill>
            </c-CContextMenu>
          </div>
          <div x-ref="shadowHost" data-context-menu-shadow-host></div>
        </article>

        <article>
          <h3>Later modal owns the top layer</h3>
          <c-CDialog>
            <c-fill name="activator" data="{ activator_attrs }">
              <c-CButton variant="outline" c-attrs="activator_attrs">
                Open sibling Dialog
              </c-CButton>
            </c-fill>
            <c-fill name="title">Layer review</c-fill>
            <c-fill name="default">
              A later modal outside a ContextMenu ancestry force-closes it.
            </c-fill>
            <c-fill name="actions" data="{ close_attrs }">
              <c-CButton c-attrs="close_attrs">Close review</c-CButton>
            </c-fill>
          </c-CDialog>
          <iframe
            title="Separate document context boundary"
            srcdoc="<p>A child document needs its own Citry instance.</p>"
          ></iframe>
        </article>

        <div class="context-menu-layers__diagnostics">
          <button type="button" @click="counterTick += 1">
            Refresh layer counters
          </button>
          <output
            aria-live="polite"
            x-text="`${last}; layers ${counterTick >= 0
              ? (globalThis[Symbol.for('citry-ui:anchored-layer-runtime')]?.layers.length ?? 0)
              : 0}; registrations ${globalThis[Symbol.for('citry-ui:anchored-layer-runtime')]
                ?.stats?.activeCoordinators ?? 0}`"
          >No layer request yet; layers 0; registrations 0</output>
        </div>
      </section>
    """

    css = """
      :where(.context-menu-layers) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        min-block-size: 28rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-layers article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        min-inline-size: 0;
      }

      :where(.context-menu-layers h3) {
        margin: 0;
      }

      :where(.context-menu-layers__outer,
        .context-menu-layers__popover-target) {
        display: grid;
        gap: 0.75rem;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 22%, transparent);
        border-radius: 0.75rem;
      }

      :where(.context-menu-layers__inner) {
        display: inline-block;
        inline-size: fit-content;
        padding: 0.375rem 0.625rem;
        border-radius: 999px;
        background: color-mix(in srgb, Highlight 14%, Canvas);
      }

      :where(.context-menu-layers__shadow-target) {
        padding: 0.75rem;
        border: 1px solid currentColor;
        border-radius: 0.5rem;
        background: Canvas;
        color: CanvasText;
      }

      :where(.context-menu-layers iframe) {
        inline-size: 100%;
        min-block-size: 6rem;
      }

      :where(.context-menu-layers__diagnostics) {
        grid-column: 1 / -1;
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }
    """


preview = ContextMenuLayersAndRoots()

preview  # noqa: B018
