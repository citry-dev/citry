import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListGlance(Component):
    template = """
      <c-CList label="Recent observations" variant="surface" c-divided="True">
        <c-CListItem href="/observations/aurora" c-current="True">Aurora over Tromsø</c-CListItem>
        <c-CListItem href="/observations/comet">Comet C/2026 Q2</c-CListItem>
        <c-CListItem href="/observations/eclipse">Lunar eclipse</c-CListItem>
      </c-CList>
    """


preview = ListGlance()
preview  # noqa: B018
