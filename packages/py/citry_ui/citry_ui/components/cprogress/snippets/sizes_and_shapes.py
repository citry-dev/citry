import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ProgressSizesAndShapes(Component):
    template = """
      <c-CStack class_="progress-sizes">
        <c-CProgress label="Small square progress" c-value="35" size="sm" shape="square" />
        <c-CProgress label="Medium rounded progress" c-value="55" />
        <c-CProgress label="Large pill progress" c-value="75" size="lg" shape="pill" />
      </c-CStack>
    """
    css = """
      :where(.progress-sizes) {
        max-inline-size: 34rem;
        color: CanvasText;
      }
    """


preview = ProgressSizesAndShapes()

preview  # noqa: B018
