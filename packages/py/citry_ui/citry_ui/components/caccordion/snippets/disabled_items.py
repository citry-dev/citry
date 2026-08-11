import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisabledItems(Component):
    template = """
      <c-CAccordion value="open-trail">
        <c-CAccordionItem value="open-trail">
          <c-fill name="title">Fern loop</c-fill>
          <c-fill name="default">Open from dawn until dusk.</c-fill>
        </c-CAccordionItem>
        <c-CAccordionItem value="closed-trail" disabled>
          <c-fill name="title">Cedar crossing — temporarily closed</c-fill>
          <c-fill name="default">High water has covered the footbridge.</c-fill>
        </c-CAccordionItem>
        <c-CAccordionItem value="accessible-trail">
          <c-fill name="title">Wetland boardwalk</c-fill>
          <c-fill name="default">A level route through reeds and alder groves.</c-fill>
        </c-CAccordionItem>
      </c-CAccordion>
    """


preview = DisabledItems()

preview  # noqa: B018
