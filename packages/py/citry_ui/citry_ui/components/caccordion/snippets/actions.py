import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AccordionActions(Component):
    template = """
      <c-CAccordion value="trail" variant="separated">
        <c-CAccordionItem
          value="trail"
          actions_label="Trail actions"
        >
          <c-fill name="title">River trail</c-fill>
          <c-fill name="actions">
            <a href="#river-map">Map</a>
            <button type="button">Save</button>
          </c-fill>
          <c-fill name="default">
            A shaded six-kilometre route follows the river upstream.
          </c-fill>
        </c-CAccordionItem>
        <c-CAccordionItem
          value="ridge"
          actions_label="Ridge actions"
        >
          <c-fill name="title">Ridge trail</c-fill>
          <c-fill name="actions">
            <a href="#ridge-map">Map</a>
          </c-fill>
          <c-fill name="default">
            An exposed climb reaches the old fire lookout.
          </c-fill>
        </c-CAccordionItem>
      </c-CAccordion>
    """


preview = AccordionActions()

preview  # noqa: B018
