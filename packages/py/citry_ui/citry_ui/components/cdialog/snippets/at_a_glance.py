import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DialogAtAGlance(Component):
    template = """
      <section class="dialog-glance">
        <article>
          <p class="dialog-glance__eyebrow">Lunar atlas</p>
          <h2>Mare Imbrium</h2>
          <p>A compact note for one clear decision.</p>
          <c-CDialog size="sm">
            <c-fill name="activator" data="{ activator_attrs }">
              <c-CButton c-attrs="activator_attrs">
                Open field note
              </c-CButton>
            </c-fill>
            <c-fill name="title">
              Mare Imbrium
            </c-fill>
            <c-fill name="default">
              The basin spans more than 1,100 kilometres.
            </c-fill>
          </c-CDialog>
        </article>

        <article>
          <p class="dialog-glance__eyebrow">Deep-sky catalog</p>
          <h2>Orion Nebula</h2>
          <p>A generous surface for richer observations.</p>
          <c-CDialog size="lg">
            <c-fill name="activator" data="{ activator_attrs }">
              <c-CButton variant="outline" c-attrs="activator_attrs">
                Inspect nebula
              </c-CButton>
            </c-fill>
            <c-fill name="title">
              Orion Nebula
            </c-fill>
            <c-fill name="description">
              A stellar nursery visible below Orion's belt.
            </c-fill>
            <c-fill name="default">
              New stars illuminate clouds of hydrogen, dust, and ionized gas.
            </c-fill>
          </c-CDialog>
        </article>
      </section>
    """

    css = """
      :where(.dialog-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.dialog-glance article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        padding: 1.25rem;
        border: 1px solid light-dark(#c4b5fd, #6d28d9);
        border-radius: 0.875rem;
        background: Canvas;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.dialog-glance h2, .dialog-glance p) {
        margin: 0;
      }

      :where(.dialog-glance__eyebrow) {
        color: light-dark(#6d28d9, #c4b5fd);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = DialogAtAGlance()

preview  # noqa: B018
