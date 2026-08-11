import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListContent(Component):
    template = """
      <c-CList c-ordered="True" marker="decimal" c-start="3">
        <c-CListItem>Align the telescope</c-CListItem>
        <c-CListItem>Calibrate the camera</c-CListItem>
        <c-CListItem>Begin the exposure</c-CListItem>
      </c-CList>
    """


preview = ListContent()
preview  # noqa: B018
