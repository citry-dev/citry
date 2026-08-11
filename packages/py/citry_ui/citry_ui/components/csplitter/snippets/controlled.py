import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledSplitter(Component):
    template = """
      <section x-data="{ sizes: [25, 75], saved: '' }">
        <c-CSplitter
          c-sizes="[25, 75]"
          $c-props="{
            sizes,
            onResize: (next) => sizes = next,
            onResizeEnd: (next) => saved = next.map(value => value.toFixed(0)).join(' / ')
          }"
        >
          <c-CSplitterPanel id="filters" label="Filters">Filters</c-CSplitterPanel>
          <c-CSplitterPanel id="results" label="Results">Results</c-CSplitterPanel>
        </c-CSplitter>
        <output x-text="saved ? `Saved: ${saved}` : 'Resize to save the layout'"></output>
      </section>
    """


preview = ControlledSplitter()
preview  # noqa: B018
