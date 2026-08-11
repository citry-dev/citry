import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DividerLabels(Component):
    template = """
      <section class="divider-labels">
        <c-CDivider label_pos="start">Inner planets</c-CDivider>
        <c-CDivider>Asteroid belt</c-CDivider>
        <c-CDivider label_pos="end">Outer planets</c-CDivider>
      </section>
    """
    css = """
      :where(.divider-labels) {
        display: grid;
        gap: 1.5rem;
        max-inline-size: 40rem;
        padding: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = DividerLabels()

preview  # noqa: B018
