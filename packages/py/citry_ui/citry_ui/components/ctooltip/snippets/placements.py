import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TooltipPlacements(Component):
    template = """
      <section
        class="tooltip-placement"
      >
        <c-CTooltip
          text="The browser may flip this surface near an edge"
          :placement="placement"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Place orbital note</c-CButton>
          </c-fill>
        </c-CTooltip>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            placement: 'top'
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

    css = """
      :where(.tooltip-placement) {
        display: grid;
        place-items: center;
        min-block-size: 20rem;
      }
    """


preview_controls = (
    {
        "name": "placement",
        "label": "Placement",
        "type": "select",
        "default": "top",
        "options": (
            ("top-start", "Top start"),
            ("top", "Top"),
            ("top-end", "Top end"),
            ("bottom-start", "Bottom start"),
            ("bottom", "Bottom"),
            ("bottom-end", "Bottom end"),
        ),
    },
)

preview = TooltipPlacements()

preview  # noqa: B018
