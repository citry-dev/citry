import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarComposition(Component):
    template = """
      <c-CToolbar label="Map tools" variant="soft">
        <c-CButtonGroup label="Zoom">
          <c-CButton variant="outline">Zoom in</c-CButton>
          <c-CButton variant="outline">Zoom out</c-CButton>
        </c-CButtonGroup>
        <c-CDivider orientation="vertical" decorative />
        <c-CToggleGroup label="Map layer" value="terrain">
          <c-CToggle value="terrain">Terrain</c-CToggle>
          <c-CToggle value="satellite">Satellite</c-CToggle>
        </c-CToggleGroup>
        <c-CPopover>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Details</c-CButton>
          </c-fill>
          <c-fill name="title">Map details</c-fill>
          <c-fill name="default"><p>Projection and data source information.</p></c-fill>
        </c-CPopover>
      </c-CToolbar>
    """


preview = ToolbarComposition()

preview  # noqa: B018
