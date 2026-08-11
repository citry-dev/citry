import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedFiles(Component):
    css = """
      :where(.evidence-drop) {
        --cui-file-input-background: light-dark(#eef8f2, #10271d);
        --cui-file-input-border-color: light-dark(#28724d, #6ed59b);
        --cui-file-input-active-color: light-dark(#15623e, #82e8ad);
        --cui-file-input-radius: 1.25rem;
      }
    """
    template = """
      <c-CDropTarget label="Botanical records" class_="evidence-drop" size="lg">
        CSV, PDF, or field images
      </c-CDropTarget>
    """


preview = CustomizedFiles()

preview  # noqa: B018
