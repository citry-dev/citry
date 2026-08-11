import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledAccordion(Component):
    template = """
      <section
        class="controlled-accordion"
        x-data="{selected: 'lichen'}"
      >
        <p aria-live="polite">
          Open section: <strong x-text="selected ?? 'none'">lichen</strong>
        </p>
        <c-CAccordion
          value="lichen"
          $c-props="{
            value: selected,
            onValueChange: (value) => selected = value,
          }"
        >
          <c-CAccordionItem value="lichen">
            <c-fill name="title">Lichen</c-fill>
            <c-fill name="default">A partnership between fungi and algae.</c-fill>
          </c-CAccordionItem>
          <c-CAccordionItem value="mushrooms">
            <c-fill name="title">Mushrooms</c-fill>
            <c-fill name="default">Temporary fruiting bodies of hidden fungal networks.</c-fill>
          </c-CAccordionItem>
          <c-CAccordionItem value="ferns">
            <c-fill name="title">Ferns</c-fill>
            <c-fill name="default">Ancient plants that reproduce through spores.</c-fill>
          </c-CAccordionItem>
        </c-CAccordion>
      </section>
    """

    css = """
      :where(.controlled-accordion) {
        display: grid;
        gap: 0.75rem;
        max-width: 44rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.controlled-accordion > p) {
        margin: 0;
        color: light-dark(#356548, #8bcda0);
      }
    """


preview = ControlledAccordion()

preview  # noqa: B018
