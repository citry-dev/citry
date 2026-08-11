import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SpinnerBusyRegion(Component):
    template = """
      <section class="spinner-busy" aria-busy="true" aria-describedby="star-chart-status">
        <c-CGroup>
          <c-CSpinner label="Updating star chart" c-attrs="{'id': 'star-chart-status'}" />
          <strong>Updating the star chart</strong>
        </c-CGroup>
        <div class="spinner-busy__chart" aria-hidden="true">
          ✦&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;✧<br />
          &nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;✦&nbsp;&nbsp;·
        </div>
      </section>
    """
    css = """
      :where(.spinner-busy) {
        display: grid;
        gap: 1rem;
        max-inline-size: 30rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.spinner-busy__chart) {
        min-block-size: 5rem;
        padding: 1rem;
        border-radius: 0.7rem;
        background: light-dark(#ecebff, #1d1d35);
        color: light-dark(#5148a0, #c4b5fd);
        letter-spacing: 0.7rem;
        line-height: 2;
      }
    """


preview = SpinnerBusyRegion()

preview  # noqa: B018
