import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TreeMultipleSelection(Component):
    template = """
      <section >
        <c-CTree
          label="Specimens"
          selection_mode="multiple"
          c-selected="['alder']"
          :selected="selected" :onSelectionChange="(next) => selected = next"
        >
          <c-CTreeItem value="alder" label="Alder" />
          <c-CTreeItem value="birch" label="Birch" />
          <c-CTreeItem value="cedar" label="Cedar" />
        </c-CTree>
        <output v-text="selected.join(', ')"></output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            selected: ['alder']
          };
        },
      });
    """


preview = TreeMultipleSelection()
preview  # noqa: B018
