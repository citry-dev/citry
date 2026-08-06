import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DialogInitialFocus(Component):
    template = """
      <section class="dialog-focus-grid" x-data>
        <article>
          <p>Quick observation</p>
          <h2>Focus a control</h2>
          <c-CDialog initial_focus="auto">
            <c-fill name="activator" data="{ activator_attrs }">
              <c-CButton
                c-attrs="activator_attrs"
                @click="$refs.cometName.setAttribute('autofocus', '')"
              >
                Name a comet
              </c-CButton>
            </c-fill>
            <c-fill name="title">
              Name a comet
            </c-fill>
            <c-fill name="default">
              <label for="comet-name">Catalog name</label>
              <input id="comet-name" x-ref="cometName" />
            </c-fill>
          </c-CDialog>
        </article>

        <article>
          <p>Long report</p>
          <h2>Focus the title</h2>
          <c-CDialog initial_focus="title">
            <c-fill name="activator" data="{ activator_attrs }">
              <c-CButton variant="outline" c-attrs="activator_attrs">
                Read eclipse report
              </c-CButton>
            </c-fill>
            <c-fill name="title">
              Total eclipse report
            </c-fill>
            <c-fill name="default">
              <p>
                Focusing the title starts reading at the top without jumping
                past structured content.
              </p>
              <button type="button">Continue reading</button>
            </c-fill>
          </c-CDialog>
        </article>
      </section>
    """

    css = """
      :where(.dialog-focus-grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 60rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.dialog-focus-grid article) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        padding: 1.25rem;
        border: 1px solid light-dark(#c4b5fd, #6d28d9);
        border-radius: 0.875rem;
        background: Canvas;
      }

      :where(.dialog-focus-grid h2, .dialog-focus-grid p) {
        margin: 0;
      }

      :where(.dialog-focus-grid article > p) {
        color: light-dark(#6d28d9, #c4b5fd);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = DialogInitialFocus()

preview  # noqa: B018
