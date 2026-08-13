import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ContextMenuChoicesAndSubmenus(Component):
    template = """
      <section
        class="context-menu-choices"
        dir="rtl"
        x-init="Alpine.store('contextMenuChoices', {showGrid:true, sort:'updated'})"
        x-data="{
          last:'No Menu action yet',
        }"
      >
        <h3>Canvas card</h3>
        <c-CContextMenu
          aria_label="Canvas card actions"
          c-close_on_select="False"
          $c-props="{
            onAction:(value,detail)=>
              last=`${detail.path.join(' / ') || 'root'}: ${value}`,
          }"
        >
          <c-fill name="target" data="{ target_attrs }">
            <article
              class="context-menu-choices__card"
              dir="ltr"
              tabindex="0"
              c-bind="target_attrs"
            >
              <strong>Release canvas</strong>
              <span>Four records · Updated today</span>
            </article>
          </c-fill>
          <c-fill name="menu">
            <c-CMenuCheckboxItem
              value="show-grid"
              c-checked="True"
              $c-props="{
                checked:$store.contextMenuChoices.showGrid,
                onCheckedChange:(next)=>$store.contextMenuChoices.showGrid=next,
              }"
            >
              Show grid
            </c-CMenuCheckboxItem>
            <c-CMenuSeparator />
            <c-CMenuRadioGroup
              value="updated"
              $c-props="{
                value:$store.contextMenuChoices.sort,
                onValueChange:(next)=>$store.contextMenuChoices.sort=next,
              }"
            >
              <c-fill name="label">Sort cards</c-fill>
              <c-fill name="default">
                <c-CMenuRadioItem value="updated">Recently updated</c-CMenuRadioItem>
                <c-CMenuRadioItem value="name">Name</c-CMenuRadioItem>
              </c-fill>
            </c-CMenuRadioGroup>
            <c-CMenuSeparator />
            <c-CMenuSubmenu value="export">
              <c-fill name="label">Export</c-fill>
              <c-fill name="default">
                <c-CMenuItem value="export-png">PNG image</c-CMenuItem>
                <c-CMenuSubmenu value="document">
                  <c-fill name="label">Document</c-fill>
                  <c-fill name="default">
                    <c-CMenuItem value="export-pdf">PDF</c-CMenuItem>
                    <c-CMenuItem value="export-svg">SVG</c-CMenuItem>
                  </c-fill>
                </c-CMenuSubmenu>
              </c-fill>
            </c-CMenuSubmenu>
          </c-fill>
        </c-CContextMenu>
        <div class="context-menu-choices__peer" dir="ltr">
          <c-CContextMenu
            aria_label="Canvas peer actions"
            $c-props="{
              onAction:(value,detail)=>
                last=`LTR ${detail.path.join(' / ') || 'root'}: ${value}`,
            }"
          >
            <c-fill name="target" data="{ target_attrs }">
              <button type="button" c-bind="target_attrs">LTR peer card</button>
            </c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="inspect-peer">Inspect peer</c-CMenuItem>
            </c-fill>
          </c-CContextMenu>
        </div>
        <output
          aria-live="polite"
          x-text="`${last}; grid ${$store.contextMenuChoices.showGrid}; sort ${$store.contextMenuChoices.sort}`"
        >No Menu action yet; grid true; sort updated</output>
      </section>
    """

    css = """
      :where(.context-menu-choices) {
        display: grid;
        gap: 0.875rem;
        justify-items: start;
        min-block-size: 24rem;
        max-inline-size: 22rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-choices h3) {
        margin: 0;
      }

      :where(.context-menu-choices__card) {
        display: grid;
        gap: 0.25rem;
        inline-size: min(18rem, 100%);
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 24%, transparent);
        border-radius: 0.75rem;
        background: color-mix(in srgb, Highlight 8%, Canvas);
      }

      :where(.context-menu-choices__card:focus-visible) {
        outline: 2px solid Highlight;
        outline-offset: 2px;
      }

      :where(.context-menu-choices__peer) {
        padding: 0.75rem;
        border: 1px dashed color-mix(in srgb, CanvasText 24%, transparent);
      }
    """


preview = ContextMenuChoicesAndSubmenus()

preview  # noqa: B018
