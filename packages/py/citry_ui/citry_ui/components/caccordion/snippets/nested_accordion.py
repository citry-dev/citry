import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NestedAccordion(Component):
    template = """
      <c-CAccordion value="trees" variant="separated">
        <c-CAccordionItem value="trees">
          <c-fill name="title">Trees</c-fill>
          <c-fill name="default">
            <p>Compare two trees found along the valley trail.</p>
            <c-CAccordion value="cedar" variant="plain" size="sm">
              <c-CAccordionItem value="cedar">
                <c-fill name="title">Western red cedar</c-fill>
                <c-fill name="default">A long-lived tree of moist lowland forests.</c-fill>
              </c-CAccordionItem>
              <c-CAccordionItem value="maple">
                <c-fill name="title">Bigleaf maple</c-fill>
                <c-fill name="default">Broad leaves support hanging gardens of moss.</c-fill>
              </c-CAccordionItem>
            </c-CAccordion>
          </c-fill>
        </c-CAccordionItem>
        <c-CAccordionItem value="wildflowers">
          <c-fill name="title">Wildflowers</c-fill>
          <c-fill name="default">Trillium and violets bloom before the canopy closes.</c-fill>
        </c-CAccordionItem>
      </c-CAccordion>
    """

    css = """
      :where([data-citry-ui-part="accordion-body"] > p:first-child) {
        margin-block-start: 0;
      }
    """


preview = NestedAccordion()

preview  # noqa: B018
