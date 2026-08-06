import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DialogThemeCustomization(Component):
    template = """
      <section class="moonlit-dialog">
        <p>Moonlit observatory</p>
        <h2>Customize tokens and parts</h2>
        <c-CDialog>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Open moon map
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Moon map
          </c-fill>
          <c-fill name="description">
            Public variables tune the surface; public selectors tune regions.
          </c-fill>
          <c-fill name="close">
            <span aria-hidden="true">✦</span>
          </c-fill>
          <c-fill name="default">
            The terminator currently crosses the eastern rim of Copernicus.
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.moonlit-dialog) {
        --cui-dialog-backdrop: rgb(15 23 42 / 78%);
        --cui-dialog-background: light-dark(#f5f3ff, #172033);
        --cui-dialog-foreground: light-dark(#2e1065, #e0e7ff);
        --cui-dialog-border-color: light-dark(#a78bfa, #818cf8);
        --cui-dialog-radius: 1.25rem;
        --cui-dialog-shadow: 0 1.75rem 5rem rgb(49 46 129 / 36%);

        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 44rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c4b5fd, #6d28d9);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.moonlit-dialog h2, .moonlit-dialog p) {
        margin: 0;
      }

      :where(.moonlit-dialog > p) {
        color: light-dark(#6d28d9, #c4b5fd);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.moonlit-dialog [data-citry-ui-part="title"]) {
        letter-spacing: 0.03em;
      }

      :where(.moonlit-dialog [data-citry-ui-part="close"]) {
        color: light-dark(#6d28d9, #c4b5fd);
      }
    """


preview = DialogThemeCustomization()

preview  # noqa: B018
