import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ConstrainedSplitter(Component):
    template = """
      <c-CSplitter c-sizes="[35, 65]" c-keyboard_step="5" variant="outline">
        <c-CSplitterPanel id="tools" label="Tools" c-min_size="20" c-max_size="50">
          Focus the separator. Arrow keys move 5%; Shift moves 20%; Home and End use the limits.
        </c-CSplitterPanel>
        <c-CSplitterPanel id="canvas" label="Canvas" c-min_size="40">Canvas</c-CSplitterPanel>
      </c-CSplitter>
    """


preview = ConstrainedSplitter()
preview  # noqa: B018
