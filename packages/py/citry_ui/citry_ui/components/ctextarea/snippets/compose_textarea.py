import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ComposeTextarea(Component):
    template = """
      <section class="forest-compose">
        <c-CField>
          <c-fill name="label">Trail condition</c-fill>
          <c-fill name="default">
            <c-CTextarea name="trail_condition" placeholder="Roots, mud, fallen limbs…" />
          </c-fill>
          <c-fill name="description">Shared with the next ranger patrol.</c-fill>
        </c-CField>

        <div>
          <label for="quick-sketch">Quick sketch notes</label>
          <c-CTextarea id="quick-sketch" name="quick_sketch" rows="3" />
        </div>
      </section>
    """

    css = """
      :where(.forest-compose) {
        display: grid;
        gap: 1.25rem;
        max-width: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.forest-compose > div) {
        display: grid;
        gap: 0.5rem;
      }

      :where(.forest-compose > div > label) {
        font-weight: 600;
      }
    """


preview = ComposeTextarea()

preview  # noqa: B018
