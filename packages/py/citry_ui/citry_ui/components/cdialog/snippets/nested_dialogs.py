import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NestedDialogs(Component):
    template = """
      <section class="nested-dialog-demo">
        <p>Observatory archive</p>
        <h2>Open a chart inside a report</h2>
        <c-CDialog>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Open transit report
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Europa transit report
          </c-fill>
          <c-fill name="default">
            <p>The moon crossed Jupiter's face shortly after midnight.</p>
            <c-CDialog size="sm">
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton variant="outline" c-attrs="activator_attrs">
                  Open transit chart
                </c-CButton>
              </c-fill>
              <c-fill name="title">
                Transit chart
              </c-fill>
              <c-fill name="default">
                Europa entered the western limb at 00:14 and cleared it at 02:37.
              </c-fill>
              <c-fill name="actions" data="{ close_attrs }">
                <c-CButton c-attrs="close_attrs">
                  Return to report
                </c-CButton>
              </c-fill>
            </c-CDialog>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">
              Close report
            </c-CButton>
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.nested-dialog-demo) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 46rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bae6fd, #0369a1);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.nested-dialog-demo h2, .nested-dialog-demo p) {
        margin: 0;
      }

      :where(.nested-dialog-demo > p) {
        color: light-dark(#0369a1, #7dd3fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = NestedDialogs()

preview  # noqa: B018
