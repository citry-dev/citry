import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IconSizeAndColor(Component):
    template = """
      <section class="icon-scale">
        <article>
          <h2>Preset sizes</h2>
          <p><c-CIcon name="leaf" size="sm" /> Small seedling</p>
          <p><c-CIcon name="leaf" /> Mature frond</p>
          <p><c-CIcon name="leaf" size="lg" /> Canopy specimen</p>
        </article>
        <article class="icon-scale__seasons">
          <h2>Inherited color</h2>
          <p class="icon-scale__spring"><c-CIcon name="leaf" /> Spring</p>
          <p class="icon-scale__summer"><c-CIcon name="leaf" /> Summer</p>
          <p class="icon-scale__autumn"><c-CIcon name="leaf" /> Autumn</p>
        </article>
        <article>
          <h2>Exact local override</h2>
          <p><c-CIcon name="leaf" style="--cui-icon-size: 2rem" /> Alpine frond</p>
        </article>
      </section>
    """

    css = """
      :where(.icon-scale) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.icon-scale article) {
        padding: 1rem;
        border: 1px solid light-dark(#d4ddce, #40533e);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.icon-scale h2) {
        margin: 0 0 0.75rem;
        font-size: 0.9rem;
      }

      :where(.icon-scale p) {
        display: flex;
        gap: 0.55rem;
        align-items: center;
        margin: 0.6rem 0;
      }

      :where(.icon-scale__spring) {
        color: #16a34a;
      }

      :where(.icon-scale__summer) {
        color: #15803d;
      }

      :where(.icon-scale__autumn) {
        color: #c2410c;
      }
    """


preview = IconSizeAndColor()

preview  # noqa: B018
