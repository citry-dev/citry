import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuKeyboard(Component):
    template = """
      <section
        class="archive-keyboard-demo"
        x-data="{loop: true, close: false}"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <c-CMenu
          c-close_on_select="False"
          $c-props="{loop, closeOnSelect: close}"
        >
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Browse spell index</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="aegis">Aegis</c-CMenuItem>
            <c-CMenuItem value="alchemy">Alchemy</c-CMenuItem>
            <c-CMenuItem value="astral">Astral projection</c-CMenuItem>
            <c-CMenuItem value="binding">Binding</c-CMenuItem>
            <c-CMenuItem value="blessing">Blessing</c-CMenuItem>
            <c-CMenuItem value="conjuring">Conjuring</c-CMenuItem>
            <c-CMenuItem value="divination">Divination</c-CMenuItem>
            <c-CMenuItem value="enchantment">Enchantment</c-CMenuItem>
            <c-CMenuItem value="illusion">Illusion</c-CMenuItem>
            <c-CMenuItem value="restoration">Restoration</c-CMenuItem>
            <c-CMenuItem value="warding">Warding</c-CMenuItem>
          </c-fill>
        </c-CMenu>
      </section>
    """

    css = """
      :where(.archive-keyboard-demo) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
        min-block-size: 20rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-keyboard-demo) {
        --cui-menu-max-block-size: 13rem;
      }
    """


preview_controls = (
    {
        "name": "loop",
        "label": "Loop navigation",
        "type": "checkbox",
        "default": True,
    },
    {
        "name": "close",
        "label": "Close on action",
        "type": "checkbox",
        "default": False,
    },
)


preview = MenuKeyboard()

preview  # noqa: B018
