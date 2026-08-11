import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BusyRegionProgress(Component):
    template = """
      <section class="progress-busy" aria-busy="true" aria-describedby="reef-progress">
        <h2>Reconstructing the reef map</h2>
        <p>Existing survey results remain visible while the new contour layer loads.</p>
        <c-CProgress
          label="Reconstructing the reef map"
          c-value="74"
          c-attrs="{'id': 'reef-progress'}"
        />
      </section>
    """
    css = """
      :where(.progress-busy) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 34rem;
        padding: 1rem;
        border: 1px solid light-dark(#b5d0d9, #436571);
        border-radius: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.progress-busy h2, .progress-busy p) {
        margin: 0;
      }
    """


preview = BusyRegionProgress()

preview  # noqa: B018
