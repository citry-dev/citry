import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class KeyboardTree(Component):
    template = """
      <c-CTree label="Keyboard explorer" c-expanded="['animals']" variant="outline">
        <c-CTreeItem value="animals" label="Animals">
          <c-CTreeItem value="badger" label="Badger" />
          <c-CTreeItem value="beaver" label="Beaver" />
        </c-CTreeItem>
        <c-CTreeItem value="minerals" label="Minerals" />
        <c-CTreeItem value="plants" label="Plants" />
      </c-CTree>
    """


preview = KeyboardTree()
preview  # noqa: B018
