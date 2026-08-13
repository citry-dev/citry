import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ContextMenuFocusAndKeyboard(Component):
    template = """
      <section
        class="context-menu-focus"
        x-data="{disableInvoker:false,last:'No close yet'}"
      >
        <p>
          Focus the row or nested Button, then press the Context Menu key or
          Shift+F10. A linked path keeps the browser's native context menu.
        </p>
        <c-CContextMenu
          aria_label="Focusable row actions"
          $c-props="{
            onOpenChange:(next,detail)=>last=
              `${next ? 'opened' : 'closed'} by ${detail.reason}`,
            onAction:(value)=>{
              if (value === 'disable-invoker') disableInvoker=true;
              if (value === 'remove-invoker') {
                document.querySelector('[data-context-menu-return-target]')?.remove();
              }
            },
          }"
        >
          <c-fill name="target" data="{ target_attrs }">
            <div
              class="context-menu-focus__row"
              tabindex="0"
              c-bind="target_attrs"
            >
              <span>
                <strong>Focusable report row</strong>
                <small>The row is the stable fallback target.</small>
              </span>
              <c-CButton
                size="sm"
                variant="outline"
                c-attrs="{'data-context-menu-return-target':''}"
                $c-props="{disabled:disableInvoker}"
              >Nested action</c-CButton>
              <a href="#focus-linked-record">Linked record</a>
            </div>
          </c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="rename">Rename</c-CMenuItem>
            <c-CMenuItem value="disable-invoker">
              Disable nested return target
            </c-CMenuItem>
            <c-CMenuItem value="remove-invoker">
              Remove nested return target
            </c-CMenuItem>
            <c-CMenuItem href="#focus-linked-record">Open linked record</c-CMenuItem>
          </c-fill>
        </c-CContextMenu>

        <div class="context-menu-focus__fallbacks">
          <button type="button" @click="location.reload()">Reload nested Button</button>
          <button type="button" disabled>Disabled fallback</button>
          <span tabindex="-1">Programmatic fallback</span>
        </div>

        <c-CDialog>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">
              Open composed modal fixture
            </c-CButton>
          </c-fill>
          <c-fill name="title">Modal focus ancestry</c-fill>
          <c-fill name="default">
            <p>
              This target and its private point stay inside the current modal.
            </p>
            <c-CContextMenu
              aria_label="Modal row actions"
              $c-props="{
                onOpenChange:(next,detail)=>last=
                  `modal ${next ? 'opened' : 'closed'} by ${detail.reason}`,
              }"
            >
              <c-fill name="target" data="{ target_attrs }">
                <button
                  class="context-menu-focus__modal-target"
                  type="button"
                  c-bind="target_attrs"
                >Modal report row</button>
              </c-fill>
              <c-fill name="menu">
                <c-CMenuItem value="review-modal-row">Review modal row</c-CMenuItem>
              </c-fill>
            </c-CContextMenu>
          </c-fill>
        </c-CDialog>
        <output aria-live="polite" x-text="last">No close yet</output>
        <span id="focus-linked-record">Linked destination</span>
      </section>
    """

    css = """
      :where(.context-menu-focus) {
        display: grid;
        gap: 1rem;
        min-block-size: 22rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-focus > p) {
        max-inline-size: 62ch;
        margin: 0;
      }

      :where(.context-menu-focus__row) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
        justify-content: space-between;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 22%, transparent);
        border-radius: 0.75rem;
      }

      :where(.context-menu-focus__row > span:first-child) {
        display: grid;
        gap: 0.25rem;
      }

      :where(.context-menu-focus__row:focus-visible) {
        outline: 2px solid Highlight;
        outline-offset: 2px;
      }

      :where(.context-menu-focus__fallbacks) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
      }

      :where(.context-menu-focus__modal-target) {
        padding: 0.75rem;
        border: 1px solid color-mix(in srgb, CanvasText 22%, transparent);
        border-radius: 0.5rem;
        background: Canvas;
        color: CanvasText;
      }
    """


preview = ContextMenuFocusAndKeyboard()

preview  # noqa: B018
