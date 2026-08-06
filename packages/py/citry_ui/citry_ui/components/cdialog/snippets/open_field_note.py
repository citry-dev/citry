import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class OpenFieldNote(Component):
    template = """
      <section class="field-note">
        <p>Tonight's observation</p>
        <h2>Aurora over the northern ridge</h2>
        <c-CDialog>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Read field note
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Aurora over the northern ridge
          </c-fill>
          <c-fill name="description">
            Recorded at 01:42 under a clear sky.
          </c-fill>
          <c-fill name="default">
            <p>
              Green ribbons appeared low on the horizon, then climbed toward
              the zenith in three bright arcs.
            </p>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton variant="ghost" c-attrs="close_attrs">
              Close note
            </c-CButton>
            <c-CButton>
              Add to atlas
            </c-CButton>
          </c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.field-note) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bae6fd, #0369a1);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.field-note h2, .field-note p) {
        margin: 0;
      }

      :where(.field-note > p) {
        color: light-dark(#0369a1, #7dd3fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = OpenFieldNote()

preview  # noqa: B018
