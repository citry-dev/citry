import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IconDirection(Component):
    template = """
      <section class="icon-direction">
        <article dir="ltr">
          <h2>Left to right</h2>
          <dl>
            <div><dt>Physical left</dt><dd><c-CIcon name="arrow-left" size="lg" /></dd></div>
            <div><dt>Back</dt><dd><c-CIcon name="back" size="lg" /></dd></div>
            <div><dt>Forward</dt><dd><c-CIcon name="forward" size="lg" /></dd></div>
            <div><dt>Next</dt><dd><c-CIcon name="next" size="lg" /></dd></div>
          </dl>
        </article>
        <article dir="rtl">
          <h2>Right to left</h2>
          <dl>
            <div><dt>Physical left</dt><dd><c-CIcon name="arrow-left" size="lg" /></dd></div>
            <div><dt>Back</dt><dd><c-CIcon name="back" size="lg" /></dd></div>
            <div><dt>Forward</dt><dd><c-CIcon name="forward" size="lg" /></dd></div>
            <div><dt>Next</dt><dd><c-CIcon name="next" size="lg" /></dd></div>
          </dl>
        </article>
      </section>
    """

    css = """
      :where(.icon-direction) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.icon-direction article) {
        padding: 1rem;
        border: 1px solid light-dark(#d4ddce, #40533e);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.icon-direction h2) {
        margin: 0 0 0.8rem;
        font-size: 0.95rem;
      }

      :where(.icon-direction dl) {
        display: grid;
        gap: 0.45rem;
        margin: 0;
      }

      :where(.icon-direction dl div) {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.4rem 0.55rem;
        border-radius: 0.4rem;
        background: light-dark(#f1f6ee, #233526);
      }

      :where(.icon-direction dt) {
        font-size: 0.85rem;
      }

      :where(.icon-direction dd) {
        margin: 0;
        color: light-dark(#236538, #7bd596);
      }
    """


preview = IconDirection()

preview  # noqa: B018
