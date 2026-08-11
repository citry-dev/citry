import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicAccordion(Component):
    template = """
      <c-CAccordion value="moss">
        <c-CAccordionItem value="moss">
          <c-fill name="title">Moss gardens</c-fill>
          <c-fill name="default">
            Moss retains moisture around roots and fallen logs.
          </c-fill>
        </c-CAccordionItem>
        <c-CAccordionItem value="streams">
          <c-fill name="title">Cold streams</c-fill>
          <c-fill name="default">
            Shaded water stays cool enough for salmon and stoneflies.
          </c-fill>
        </c-CAccordionItem>
        <c-CAccordionItem value="nurse-logs">
          <c-fill name="title">Nurse logs</c-fill>
          <c-fill name="default">
            Seedlings use decaying trunks as raised, nutrient-rich beds.
          </c-fill>
        </c-CAccordionItem>
      </c-CAccordion>
    """


preview = BasicAccordion()

preview  # noqa: B018
