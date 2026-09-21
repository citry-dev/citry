import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledExpansion(Component):
    template = """
      <section >
        <c-CTree
          label="Knowledge base"
          :expanded="expanded" :onExpandedChange="(next) => expanded = next"
        >
          <c-CTreeItem value="docs" label="Documentation">
            <c-CTreeItem value="guides" label="Guides" />
            <c-CTreeItem value="reference" label="Reference" />
          </c-CTreeItem>
          <c-CTreeItem value="examples" label="Examples" />
        </c-CTree>
        <output v-text="expanded.join(', ') || 'All branches collapsed'"></output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            expanded: ['docs']
          };
        },
      });
    """


preview = ControlledExpansion()
preview  # noqa: B018
