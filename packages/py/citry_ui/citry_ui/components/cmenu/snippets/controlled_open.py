import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledMenu(Component):
    template = """
      <section
        class="archive-controlled-demo"
        x-data="{open: false, disabled: false, locked: false, size: 'md', lastReason: 'none'}"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <c-CButton size="sm" @click="open = !open">Toggle from owner</c-CButton>
        <c-CMenu
          $c-props="{
            open,
            disabled,
            size,
            onOpenChange: (nextOpen, detail) => {
              lastReason = detail.reason;
              if (!locked) open = nextOpen;
            },
          }"
        >
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Controlled grimoire</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="translate">Translate runes</c-CMenuItem>
            <c-CMenuItem value="restore">Restore missing page</c-CMenuItem>
          </c-fill>
        </c-CMenu>
        <output x-text="`Last request: ${lastReason}`">Last request: none</output>
      </section>
    """

    css = """
      :where(.archive-controlled-demo) {
        display: grid;
        gap: 1rem;
        min-block-size: 17rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

    """


preview_controls = (
    {
        "name": "size",
        "label": "Size",
        "type": "select",
        "default": "md",
        "options": (("sm", "Small"), ("md", "Medium"), ("lg", "Large")),
    },
    {
        "name": "disabled",
        "label": "Disabled",
        "type": "checkbox",
        "default": False,
    },
    {
        "name": "locked",
        "label": "Decline visibility requests",
        "type": "checkbox",
        "default": False,
    },
)


preview = ControlledMenu()

preview  # noqa: B018
