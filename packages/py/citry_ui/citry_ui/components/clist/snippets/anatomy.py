import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ListAnatomy(Component):
    template = """
      <c-CList label="Specimens" c-divided="True">
        <c-CListItem>
          <c-fill name="start"><c-CAvatar alt="Mare Imbrium" /></c-fill>
          <c-fill name="default">Mare Imbrium basalt</c-fill>
          <c-fill name="description">Apollo 15 · sample 15555</c-fill>
          <c-fill name="end"><c-CBadge variant="outline">Lunar</c-CBadge></c-fill>
        </c-CListItem>
        <c-CListItem>
          <c-fill name="start"><c-CIcon name="star" /></c-fill>
          <c-fill name="default">Murchison meteorite</c-fill>
          <c-fill name="description">Carbonaceous chondrite · 1969</c-fill>
          <c-fill name="end">12.4 g</c-fill>
        </c-CListItem>
      </c-CList>
    """


preview = ListAnatomy()
preview  # noqa: B018
