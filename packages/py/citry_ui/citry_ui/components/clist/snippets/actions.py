import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListActions(Component):
    template = """
      <c-CList label="Observation queue" variant="surface">
        <c-CListItem c-action="True" @click="console.log('opened')">Open current session</c-CListItem>
        <c-CListItem>
          <c-fill name="default">Nightly calibration</c-fill>
          <c-fill name="description">Ready to archive</c-fill>
          <c-fill name="end"><c-CButton size="sm" variant="outline">Archive</c-CButton></c-fill>
        </c-CListItem>
      </c-CList>
    """


preview = ListActions()
preview  # noqa: B018
