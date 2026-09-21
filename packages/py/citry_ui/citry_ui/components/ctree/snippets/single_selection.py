import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TreeSingleSelection(Component):
    template = """
      <section >
        <c-CTree
          label="Planets"
          c-selected="['mercury']"
          :selected="selected" :onSelectionChange="(next) => selected = next"
        >
          <c-CTreeItem value="mercury" label="Mercury" />
          <c-CTreeItem value="venus" label="Venus" />
          <c-CTreeItem value="earth" label="Earth" />
        </c-CTree>
        <output v-text="selected[0] ?? 'No selection'"></output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            selected: ['mercury']
          };
        },
      });
    """


preview = TreeSingleSelection()
preview  # noqa: B018
