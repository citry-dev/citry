import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuPlacement(Component):
    template = """
      <section
        class="archive-placement-demo"
        x-data="{placement: 'bottom-start', rtl: false, match: true}"
        :dir="rtl ? 'rtl' : 'ltr'"
        @citry-ui-preview-controls.window="Object.assign($data, $event.detail)"
      >
        <c-CMenu $c-props="{placement, matchWidth: match}">
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton
              class_="archive-placement-demo__wide"
              c-disabled="activator_disabled"
              c-attrs="activator_attrs"
            >
              A deliberately wide enchanted-volume trigger
            </c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="north">Northern shelf</c-CMenuItem>
            <c-CMenuItem value="south">Southern shelf</c-CMenuItem>
            <c-CMenuSubmenu value="hidden-wing">
              <c-fill name="label">Hidden wing</c-fill>
              <c-fill name="default">
                <c-CMenuItem value="mirrors">Hall of mirrors</c-CMenuItem>
              </c-fill>
            </c-CMenuSubmenu>
          </c-fill>
        </c-CMenu>
      </section>
    """

    css = """
      :where(.archive-placement-demo) {
        display: grid;
        gap: 1rem;
        justify-items: center;
        min-block-size: 21rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-placement-demo__wide) {
        inline-size: min(34rem, 150dvi);
      }
    """


preview_controls = (
    {
        "name": "placement",
        "label": "Placement",
        "type": "select",
        "default": "bottom-start",
        "options": (
            ("bottom-start", "Bottom start"),
            ("bottom", "Bottom"),
            ("bottom-end", "Bottom end"),
            ("top-start", "Top start"),
            ("top", "Top"),
            ("top-end", "Top end"),
        ),
    },
    {
        "name": "match",
        "label": "Match activator width",
        "type": "checkbox",
        "default": True,
    },
    {
        "name": "rtl",
        "label": "Right-to-left",
        "type": "checkbox",
        "default": False,
    },
)


preview = MenuPlacement()

preview  # noqa: B018
