import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledExpansion(Component):
    template = """
      <section x-data="{ expanded: ['docs'] }">
        <c-CTree
          label="Knowledge base"
          $c-props="{ expanded, onExpandedChange: (next) => expanded = next }"
        >
          <c-CTreeItem value="docs" label="Documentation">
            <c-CTreeItem value="guides" label="Guides" />
            <c-CTreeItem value="reference" label="Reference" />
          </c-CTreeItem>
          <c-CTreeItem value="examples" label="Examples" />
        </c-CTree>
        <output x-text="expanded.join(', ') || 'All branches collapsed'"></output>
      </section>
    """


preview = ControlledExpansion()
preview  # noqa: B018
