import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CheckboxAtAGlance(Component):
    template = """
      <section class="botanical-checklist" aria-label="Botanical field checklist">
        <header>
          <p>Morning survey</p>
          <h2>Woodland observations</h2>
        </header>
        <div class="botanical-checklist__grid">
          <c-CCheckbox name="observed" value="fern" checked>
            Lady fern unfurled
          </c-CCheckbox>
          <c-CCheckbox name="observed" value="moss">
            <c-fill name="default">Cushion moss fruiting</c-fill>
            <c-fill name="description">
              Check the shaded side of fallen trunks.
            </c-fill>
          </c-CCheckbox>
          <c-CCheckbox name="observed" value="lichen" variant="outline">
            Reindeer lichen present
          </c-CCheckbox>
          <c-CCheckbox disabled>
            <c-fill name="default">Alpine saxifrage</c-fill>
            <c-fill name="description">
              Outside this survey's elevation range.
            </c-fill>
          </c-CCheckbox>
        </div>
      </section>
    """

    css = """
      :where(.botanical-checklist) {
        display: grid;
        gap: 1rem;
        max-width: 48rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b8d2bd, #365c42);
        border-radius: 1rem;
        background: light-dark(#f6fbf5, #12251a);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.botanical-checklist h2, .botanical-checklist p) {
        margin: 0;
      }

      :where(.botanical-checklist header p) {
        color: light-dark(#286b43, #7bd9a0);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.botanical-checklist__grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
      }
    """


preview = CheckboxAtAGlance()

preview  # noqa: B018
