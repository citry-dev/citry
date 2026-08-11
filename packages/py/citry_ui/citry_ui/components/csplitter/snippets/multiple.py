import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MultiplePanels(Component):
    template = """
      <c-CSplitter c-sizes="[20, 45, 35]" variant="soft">
        <c-CSplitterPanel id="outline" label="Document outline">Outline</c-CSplitterPanel>
        <c-CSplitterPanel id="editor" label="Document editor">Editor</c-CSplitterPanel>
        <c-CSplitterPanel id="preview" label="Document preview">Preview</c-CSplitterPanel>
      </c-CSplitter>
    """


preview = MultiplePanels()
preview  # noqa: B018
