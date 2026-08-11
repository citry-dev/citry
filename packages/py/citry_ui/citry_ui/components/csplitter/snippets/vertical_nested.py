import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class VerticalNested(Component):
    template = """
      <c-CSplitter orientation="vertical" c-sizes="[35, 65]" variant="outline">
        <c-CSplitterPanel id="header" label="Header preview">Header preview</c-CSplitterPanel>
        <c-CSplitterPanel id="workbench" label="Workbench">
          <c-CSplitter c-sizes="[40, 60]" size="sm">
            <c-CSplitterPanel id="source" label="Source">Source</c-CSplitterPanel>
            <c-CSplitterPanel id="result" label="Result">Result</c-CSplitterPanel>
          </c-CSplitter>
        </c-CSplitterPanel>
      </c-CSplitter>
    """


preview = VerticalNested()
preview  # noqa: B018
