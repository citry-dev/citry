import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DividerOrientations(Component):
    template = """
      <section class="divider-orientations">
        <div class="divider-orientations__horizontal">
          <span>First quarter</span>
          <c-CDivider variant="dashed" c-decorative="True" />
          <span>Full moon</span>
        </div>
        <div class="divider-orientations__vertical">
          <span>Rise 20:14</span>
          <c-CDivider orientation="vertical" c-decorative="True" />
          <span>Transit 01:36</span>
          <c-CDivider orientation="vertical" c-decorative="True" />
          <span>Set 06:51</span>
        </div>
      </section>
    """
    css = """
      :where(.divider-orientations) {
        display: grid;
        gap: 1.25rem;
        max-inline-size: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.divider-orientations__horizontal) {
        display: grid;
        gap: 0.75rem;
      }

      :where(.divider-orientations__vertical) {
        display: flex;
        min-block-size: 2.5rem;
        flex-wrap: wrap;
        align-items: stretch;
        gap: 0.75rem;
        padding: 0.75rem;
        border-radius: 0.6rem;
        background: light-dark(#eef2ff, #1e2744);
      }
    """


preview = DividerOrientations()

preview  # noqa: B018
