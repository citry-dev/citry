import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledContextMenu(Component):
    template = """
      <section
        class="context-menu-controlled"
        x-data="{
          open:false,
          controlled:true,
          accept:true,
          breakClaim:false,
          lastReason:'none',
          candidate:'none',
        }"
      >
        <c-CContextMenu
          aria_label="Diagram actions"
          $c-props="{
            open:controlled ? open : null,
            onOpenChange:(nextOpen,detail)=>{
              lastReason=detail.reason;
              candidate=`${Math.round(detail.clientX)}, ${Math.round(detail.clientY)}`;
              if (!controlled) return;
              if (!nextOpen) {
                open=false;
                return;
              }
              if (!accept) return false;
              if (!breakClaim) open=true;
              return true;
            },
          }"
        >
          <c-fill name="target" data="{ target_attrs }">
            <div
              class="context-menu-controlled__target"
              tabindex="0"
              c-bind="target_attrs"
            >
              <strong>Controlled diagram</strong>
              <span>Right click or press Shift+F10</span>
            </div>
          </c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="inspect">Inspect layers</c-CMenuItem>
            <c-CMenuItem value="duplicate">Duplicate diagram</c-CMenuItem>
          </c-fill>
        </c-CContextMenu>

        <div role="group" aria-label="Controlled visibility settings">
          <label><input type="checkbox" x-model="accept" /> Claim requests</label>
          <label><input type="checkbox" x-model="breakClaim" /> Break the claim</label>
          <button type="button" @click="controlled=true;open=true">
            Open from owner
          </button>
          <button type="button" @click="controlled=true;open=false">
            Close from owner
          </button>
          <button type="button" @click="controlled=false">
            Release control
          </button>
        </div>

        <output>
          State:
          <span x-text="controlled ? (open ? 'controlled open' : 'controlled closed') : 'uncontrolled'">
            controlled closed
          </span>;
          request: <span x-text="lastReason">none</span>;
          candidate: <span x-text="candidate">none</span>
        </output>
      </section>
    """

    css = """
      :where(.context-menu-controlled) {
        display: grid;
        gap: 1rem;
        min-block-size: 22rem;
        padding: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-controlled__target) {
        display: grid;
        gap: 0.25rem;
        padding: 1.25rem;
        border-radius: 1rem;
        background: light-dark(#eef4ff, #182230);
      }

      :where(.context-menu-controlled__target:focus-visible) {
        outline: 2px solid Highlight;
        outline-offset: 2px;
      }

      :where(.context-menu-controlled [role="group"]) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
        align-items: center;
      }

      :where(.context-menu-controlled label) {
        display: inline-flex;
        gap: 0.375rem;
        align-items: center;
      }
    """


preview = ControlledContextMenu()

preview  # noqa: B018
