import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisclosureVariantsAndSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section
        class="disclosure-variants"
      >
        <div class="disclosure-variants__stage" style="color-scheme:dark">
          <c-CDisclosure
            open
            class_="disclosure-variants__subject"
            :variant="variant" :size="size" :indicator="indicator" :indicatorPosition="indicator_position"
          >
            <c-fill name="title">Deployment requirements for the observability gateway in restricted networks</c-fill>
            <c-fill name="default">The live subject reflects every external control.</c-fill>
          </c-CDisclosure>
        </div>
        <div class="disclosure-variants__matrix">
          <c-for each="variant in variants">
            <c-CDisclosure #c-key="variant" c-variant="variant" open>
              <c-fill name="title">{{ variant }} treatment</c-fill>
              <c-fill name="default">A concise operations handbook note.</c-fill>
            </c-CDisclosure>
          </c-for>
          <c-for each="size in sizes">
            <c-CDisclosure #c-key="size" c-size="size" indicator_pos="start">
              <c-fill name="title">{{ size }} geometry</c-fill>
              <c-fill name="default">Size changes the complete component geometry.</c-fill>
            </c-CDisclosure>
          </c-for>
        </div>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            variant:'outline',size:'md',indicator:true,indicator_position:'end'
          };
        },
        methods: {
          applyPreviewControls(event) {
            Object.assign(this, event.detail);
          },
        },
        mounted() {
          window.addEventListener("citry-ui-preview-controls", this.applyPreviewControls);
        },
        beforeUnmount() {
          window.removeEventListener("citry-ui-preview-controls", this.applyPreviewControls);
        },
      });
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {"variants": ("outline", "soft", "plain"), "sizes": ("sm", "md", "lg")}

    css = """
      :where(.disclosure-variants) {
        display: grid;
        gap: 1rem;
      }
      :where(.disclosure-variants__stage) {
        padding: 1rem;
        border-radius: 1rem;
        background: #111827;
      }
      :where(.disclosure-variants__matrix) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
        gap: 0.75rem;
      }
    """


preview_controls = (
    {
        "name": "variant",
        "label": "Variant",
        "type": "select",
        "default": "outline",
        "options": (("outline", "Outline"), ("soft", "Soft"), ("plain", "Plain")),
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
    {"name": "indicator", "label": "Show indicator", "type": "checkbox", "default": True},
)


preview = DisclosureVariantsAndSizes()
preview  # noqa: B018
