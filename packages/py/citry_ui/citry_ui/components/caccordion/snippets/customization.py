import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizeAccordion(Component):
    template = """
      <section
        class="accordion-configurator"
        x-data="{
          variant: 'separated',
          size: 'md',
          indicator: true,
          indicator_position: 'end',
        }"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <header>
          <p>Live configuration</p>
          <h2>Forest field guide</h2>
        </header>
        <c-CAccordion
          value="watershed"
          class_="accordion-configurator__group"
          $c-props="{
            variant,
            size,
            indicator,
            indicatorPosition: indicator_position,
          }"
        >
          <c-CAccordionItem value="watershed">
            <c-fill name="title">Watershed</c-fill>
            <c-fill name="default">Every hillside stream eventually meets the river.</c-fill>
          </c-CAccordionItem>
          <c-CAccordionItem value="wildlife">
            <c-fill name="title">Wildlife corridor</c-fill>
            <c-fill name="default">Connected forest lets animals move between habitats.</c-fill>
          </c-CAccordionItem>
        </c-CAccordion>
      </section>
    """

    css = """
      :where(.accordion-configurator) {
        display: grid;
        gap: 1rem;
        max-width: 48rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.accordion-configurator h2, .accordion-configurator p) {
        margin: 0;
      }

      :where(.accordion-configurator header > p) {
        color: light-dark(#39724e, #8fd4a6);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.accordion-configurator__group) {
        --cui-accordion-radius: 1rem;
        --cui-accordion-trigger-open-color: light-dark(#1f6b3c, #8fe0aa);
        --cui-accordion-focus-color: light-dark(#2f855a, #70d397);
      }
    """


preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "separated",
        "options": (
            ("outline", "Outline"),
            ("soft", "Soft"),
            ("separated", "Separated"),
            ("plain", "Plain"),
        ),
    },
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {
        "name": "indicator_position",
        "label": "Indicator position",
        "type": "select",
        "default": "end",
        "options": (("start", "Start"), ("end", "End")),
    },
    {
        "name": "indicator",
        "label": "Show indicator",
        "type": "checkbox",
        "default": True,
    },
)

preview = CustomizeAccordion()

preview  # noqa: B018
