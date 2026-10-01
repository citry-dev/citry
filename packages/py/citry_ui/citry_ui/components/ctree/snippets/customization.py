import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedTree(Component):
    template = """
      <div class="brand-tree">
        <c-CTree label="Branded catalog" c-selected="['ferns']" variant="outline" size="lg">
          <c-CTreeItem value="mosses" label="Mosses" />
          <c-CTreeItem value="ferns" label="Ferns" />
          <c-CTreeItem value="orchids" label="Orchids" />
        </c-CTree>
      </div>
    """
    css = """
      :where(.brand-tree) {
        --cui-tree-indent: 1.75rem;
        --cui-tree-radius: 1rem;
        --cui-tree-selected-background: rebeccapurple;
        --cui-tree-selected-color: white;
      }
    """


preview = CustomizedTree()
preview  # noqa: B018
