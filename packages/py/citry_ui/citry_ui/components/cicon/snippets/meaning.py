import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IconMeaning(Component):
    template = """
      <section class="icon-meaning">
        <article>
          <h2>Visible text carries meaning</h2>
          <p class="icon-meaning__notice">
            <c-CIcon name="warn" size="lg" />
            Frost is expected above the tree line.
          </p>
          <code>aria-hidden="true"</code>
        </article>
        <article>
          <h2>Icon stands alone</h2>
          <div class="icon-meaning__weather">
            <c-CIcon name="leaf" size="lg" label="Good growing conditions" />
          </div>
          <code>role="img" aria-label="Good growing conditions"</code>
        </article>
      </section>
    """

    css = """
      :where(.icon-meaning) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 58rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.icon-meaning article) {
        padding: 1rem;
        border: 1px solid light-dark(#d8dac7, #55563a);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.icon-meaning h2) {
        margin: 0 0 0.75rem;
        font-size: 0.95rem;
      }

      :where(.icon-meaning__notice) {
        display: flex;
        gap: 0.6rem;
        align-items: center;
        color: light-dark(#9a3412, #fdba74);
      }

      :where(.icon-meaning__weather) {
        display: grid;
        place-items: center;
        min-block-size: 4rem;
        color: light-dark(#15803d, #86efac);
        font-size: 2rem;
      }

      :where(.icon-meaning code) {
        font-size: 0.72rem;
        overflow-wrap: anywhere;
      }
    """


preview = IconMeaning()

preview  # noqa: B018
