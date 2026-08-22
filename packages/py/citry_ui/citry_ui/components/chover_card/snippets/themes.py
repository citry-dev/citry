# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class HoverCardThemes(Component):
    template = """
      <c-CRow>
        <div style="color-scheme:light;background:Canvas;color:CanvasText;padding:2rem">
          <c-CHoverCard>
            <c-fill name="activator" data="{ activator_attrs }"><a href="#day" c-bind="activator_attrs">Day profile</a></c-fill>
            <c-fill name="default"><strong>Light scheme</strong><p>Follows its anchor context.</p></c-fill>
          </c-CHoverCard>
        </div>
        <div style="color-scheme:dark;background:Canvas;color:CanvasText;padding:2rem">
          <c-CHoverCard>
            <c-fill name="activator" data="{ activator_attrs }"><a href="#night" c-bind="activator_attrs">Night profile</a></c-fill>
            <c-fill name="default"><strong>Dark scheme</strong><p>Follows its anchor context.</p></c-fill>
          </c-CHoverCard>
        </div>
      </c-CRow>
    """


preview = HoverCardThemes()
preview  # noqa: B018
