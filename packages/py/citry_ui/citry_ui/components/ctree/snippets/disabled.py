import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TreeDisabledItems(Component):
    template = """
      <c-CTree label="Deployment targets" c-expanded="['regions']">
        <c-CTreeItem value="regions" label="Regions">
          <c-CTreeItem value="eu" label="Europe" />
          <c-CTreeItem value="us" label="United States" disabled />
        </c-CTreeItem>
        <c-CTreeItem value="archive" label="Archived targets" disabled />
      </c-CTree>
    """


preview = TreeDisabledItems()
preview  # noqa: B018
