import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListNavigation(Component):
    template = """
      <nav aria-label="Observatory">
        <c-CList variant="surface">
          <c-CListItem href="/sky" c-current="True">Sky map</c-CListItem>
          <c-CListItem href="/sessions">Sessions</c-CListItem>
          <c-CListItem href="/equipment">Equipment</c-CListItem>
        </c-CList>
      </nav>
    """


preview = ListNavigation()
preview  # noqa: B018
