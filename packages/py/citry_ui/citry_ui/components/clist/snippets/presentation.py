import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListPresentation(Component):
    template = """
      <c-CCol gap="lg">
        <c-CList label="Comfortable list" variant="surface">
          <c-CListItem>Andromeda Galaxy</c-CListItem>
          <c-CListItem>Triangulum Galaxy</c-CListItem>
        </c-CList>
        <c-CList label="Compact divided list" density="compact" c-divided="True">
          <c-CListItem>Whirlpool Galaxy</c-CListItem>
          <c-CListItem>Sombrero Galaxy</c-CListItem>
        </c-CList>
      </c-CCol>
    """


preview = ListPresentation()
preview  # noqa: B018
