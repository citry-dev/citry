import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SingleSelection(Component):
    template = """
      <section x-data="{ selected: ['mercury'] }">
        <c-CTree
          label="Planets"
          c-selected="['mercury']"
          $c-props="{ selected, onSelectionChange: (next) => selected = next }"
        >
          <c-CTreeItem value="mercury" label="Mercury" />
          <c-CTreeItem value="venus" label="Venus" />
          <c-CTreeItem value="earth" label="Earth" />
        </c-CTree>
        <output x-text="selected[0] ?? 'No selection'"></output>
      </section>
    """


preview = SingleSelection()
preview  # noqa: B018
