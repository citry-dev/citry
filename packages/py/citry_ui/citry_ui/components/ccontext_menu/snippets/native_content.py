import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ContextMenuNativeContent(Component):
    template = """
      <section
        class="context-menu-native"
        x-data="{last:'No custom request yet'}"
      >
        <p>
          Select text or use the editing, link, image, media, embedded, and
          marked regions below. Their browser context menus stay available.
        </p>
        <c-CContextMenu
          aria_label="Document region actions"
          $c-props="{
            onOpenChange:(next,detail)=>
              last=`${next ? 'Open' : 'Close'}: ${detail.reason}`,
          }"
        >
          <c-fill name="target" data="{ target_attrs }">
            <div
              class="context-menu-native__target"
              tabindex="0"
              c-bind="target_attrs"
            >
              <p class="context-menu-native__selection">
                Select part of this paragraph before opening its browser menu.
              </p>
              <label>
                Editable title
                <input value="Quarterly report" />
              </label>
              <div contenteditable="true">Editable note</div>
              <a href="#native-content-destination">Open linked record</a>
              <img
                alt="Blue document thumbnail"
                width="72"
                height="48"
                src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
              />
              <video controls aria-label="Media preview"></video>
              <context-menu-native-card>Custom element host</context-menu-native-card>
              <div
                data-citry-context-menu-native
                x-init="const root=$el.attachShadow({mode:'closed'});root.textContent='Closed shadow fixture'"
              >
                Marked closed-shadow host
              </div>
              <div
                x-init="const root=$el.attachShadow({mode:'open'});root.textContent='Select open-shadow text'"
              >
                Open-shadow selection fixture
              </div>
              <iframe
                title="Embedded document boundary"
                srcdoc="<p>Child document keeps its own browser menu.</p>"
              ></iframe>
              <div class="context-menu-native__eligible" tabindex="0">
                Plain file row · Custom commands available here
              </div>
            </div>
          </c-fill>
          <c-fill name="menu">
            <c-CMenuItem value="rename">Rename file row</c-CMenuItem>
            <c-CMenuItem value="archive">Archive file row</c-CMenuItem>
          </c-fill>
        </c-CContextMenu>
        <output aria-live="polite" x-text="last">No custom request yet</output>
        <span id="native-content-destination">Linked record destination</span>
      </section>
    """

    css = """
      :where(.context-menu-native) {
        display: grid;
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-native > p) {
        max-inline-size: 62ch;
        margin: 0;
      }

      :where(.context-menu-native__target) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 0.75rem;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 22%, transparent);
        border-radius: 1rem;
      }

      :where(.context-menu-native__target > *) {
        min-inline-size: 0;
        padding: 0.625rem;
        border-radius: 0.5rem;
        background: color-mix(in srgb, Highlight 7%, Canvas);
      }

      :where(.context-menu-native__selection) {
        user-select: text;
      }

      :where(.context-menu-native__eligible:focus-visible,
        .context-menu-native__target:focus-visible) {
        outline: 2px solid Highlight;
        outline-offset: 2px;
      }

      :where(.context-menu-native iframe) {
        inline-size: 100%;
        min-block-size: 5rem;
        border: 1px solid color-mix(in srgb, CanvasText 22%, transparent);
      }
    """


preview = ContextMenuNativeContent()

preview  # noqa: B018
