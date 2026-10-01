import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ConfigureDrawer(Component):
    template = """
      <section
        >
        <c-CDrawer :placement="placement" :size="size" :scroll="scroll">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Preview geometry</c-CButton>
          </c-fill>
          <c-fill name="title">Configurable archive</c-fill>
          <c-fill name="default">Change the logical edge, extent, and scrolling policy.</c-fill>
        </c-CDrawer>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            placement:'inline-end', size:'md', scroll:'body'
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


preview_controls = (
    {
        "name": "placement",
        "label": "Placement",
        "type": "select",
        "default": "inline-end",
        "options": (
            ("inline-start", "Inline start"),
            ("inline-end", "Inline end"),
            ("block-start", "Block start"),
            ("block-end", "Block end"),
        ),
    },
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large"), ("full", "Full")),
    },
    {
        "name": "scroll",
        "label": "Scroll",
        "type": "select",
        "default": "body",
        "options": (("body", "Body"), ("drawer", "Complete Drawer")),
    },
)
preview = ConfigureDrawer()
preview  # noqa: B018
