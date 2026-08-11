import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NestedList(Component):
    template = """
      <c-CList label="Solar system" marker="disc">
        <c-CListItem>
          <c-fill name="default">
            Inner planets
            <c-CList marker="disc">
              <c-CListItem>Mercury</c-CListItem>
              <c-CListItem>Venus</c-CListItem>
              <c-CListItem>Earth</c-CListItem>
            </c-CList>
          </c-fill>
        </c-CListItem>
        <c-CListItem>Outer planets</c-CListItem>
      </c-CList>
    """


preview = NestedList()
preview  # noqa: B018
