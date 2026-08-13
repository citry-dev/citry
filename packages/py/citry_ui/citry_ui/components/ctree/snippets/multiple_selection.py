import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TreeMultipleSelection(Component):
    template = """
      <section x-data="{ selected: ['alder'] }">
        <c-CTree
          label="Specimens"
          selection_mode="multiple"
          c-selected="['alder']"
          $c-props="{ selected, onSelectionChange: (next) => selected = next }"
        >
          <c-CTreeItem value="alder" label="Alder" />
          <c-CTreeItem value="birch" label="Birch" />
          <c-CTreeItem value="cedar" label="Cedar" />
        </c-CTree>
        <output x-text="selected.join(', ')"></output>
      </section>
    """


preview = TreeMultipleSelection()
preview  # noqa: B018
