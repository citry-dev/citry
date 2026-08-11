import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuLifecycle(Component):
    template = """
      <section class="archive-lifecycle-demo" x-data>
        <c-CPopover>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open reading room</c-CButton>
          </c-fill>
          <c-fill name="title">Reading room</c-fill>
          <c-fill name="default">
            <c-CMenu>
              <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Nested folio menu</c-CButton>
              </c-fill>
              <c-fill name="default">
                <c-CMenuItem value="inspect">Inspect binding</c-CMenuItem>
                <c-CMenuSubmenu value="editions">
                  <c-fill name="label">Other editions</c-fill>
                  <c-fill name="default">
                    <c-CMenuItem value="first">First edition</c-CMenuItem>
                  </c-fill>
                </c-CMenuSubmenu>
              </c-fill>
            </c-CMenu>
          </c-fill>
        </c-CPopover>
        <c-CButton @click="$refs.vault.showModal()">Open modal vault</c-CButton>
        <dialog x-ref="vault" aria-labelledby="vault-title">
          <h2 id="vault-title">Royal vault</h2>
          <p>Opening this modal closes unrelated anchored layers.</p>
          <button type="button" @click="$refs.vault.close()">Close vault</button>
        </dialog>
      </section>
    """

    css = """
      :where(.archive-lifecycle-demo) {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        min-block-size: 20rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-lifecycle-demo dialog) {
        max-inline-size: min(26rem, calc(100dvi - 2rem));
        padding: 1.25rem;
        border: 1px solid color-mix(in srgb, CanvasText 24%, transparent);
        border-radius: 0.85rem;
        background: Canvas;
        color: CanvasText;
      }

      :where(.archive-lifecycle-demo dialog::backdrop) {
        background: rgb(15 23 42 / 45%);
      }
    """


preview = MenuLifecycle()

preview  # noqa: B018
