import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TreeAtAGlance(Component):
    template = """
      <c-CTree label="Project files" c-expanded="['src']" c-selected="['app']" variant="soft">
        <c-CTreeItem value="src" label="src">
          <c-CTreeItem value="app" label="app.py" />
          <c-CTreeItem value="styles" label="styles.css" />
        </c-CTreeItem>
        <c-CTreeItem value="tests" label="tests" />
        <c-CTreeItem value="readme" label="README.md" />
      </c-CTree>
    """


preview = TreeAtAGlance()
preview  # noqa: B018
