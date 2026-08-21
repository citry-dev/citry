import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TourTargets(Component):
    template = """
      <section class="tour-targets">
        <c-CButton c-attrs="{'id':'tour-filter'}" variant="outline">Filter</c-CButton>
        <c-CButton c-attrs="{'id':'tour-export'}">Export</c-CButton>
        <c-CTour>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Explain actions</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CTourStep value="filter" target_id="tour-filter" placement="bottom-start">
              <c-fill name="title">Narrow the results</c-fill>
              <c-fill name="default">Choose filters before exporting.</c-fill>
            </c-CTourStep>
            <c-CTourStep value="export" target_id="tour-export" placement="inline-end">
              <c-fill name="title">Export the current view</c-fill>
              <c-fill name="default">The export respects the active filters.</c-fill>
            </c-CTourStep>
          </c-fill>
        </c-CTour>
      </section>
    """
    css = ":where(.tour-targets){display:flex;flex-wrap:wrap;gap:1rem;align-items:center}"


preview = TourTargets()
preview  # noqa: B018
