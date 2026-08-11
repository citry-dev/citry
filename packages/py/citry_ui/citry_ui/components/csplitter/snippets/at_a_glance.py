import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SplitterAtAGlance(Component):
    template = """
      <c-CSplitter c-sizes="[30, 70]" variant="outline">
        <c-CSplitterPanel id="navigation" label="Navigation">
          <strong>Navigation</strong><p>Projects, files, and saved views.</p>
        </c-CSplitterPanel>
        <c-CSplitterPanel id="workspace" label="Workspace">
          <strong>Workspace</strong><p>Resize with the separator or its Arrow keys.</p>
        </c-CSplitterPanel>
      </c-CSplitter>
    """


preview = SplitterAtAGlance()
preview  # noqa: B018
