import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IndeterminateProgress(Component):
    template = """
      <section class="progress-unknown">
        <h2>Contacting the deep-sea relay</h2>
        <c-CProgress label="Contacting the deep-sea relay" shape="pill" />
        <p>The operation is active, but its remaining duration is unknown.</p>
      </section>
    """
    css = """
      :where(.progress-unknown) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 32rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.progress-unknown h2, .progress-unknown p) {
        margin: 0;
      }

      :where(.progress-unknown p) {
        color: GrayText;
        font-size: 0.8rem;
      }
    """


preview = IndeterminateProgress()

preview  # noqa: B018
