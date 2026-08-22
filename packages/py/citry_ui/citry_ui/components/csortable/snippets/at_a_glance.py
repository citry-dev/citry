import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SortableAtAGlance(Component):
    template = """
      <c-CSortable name="release-priority">
        <c-CSortableItem value="design" label="Design review">Design review</c-CSortableItem>
        <c-CSortableItem value="accessibility" label="Accessibility pass">Accessibility pass</c-CSortableItem>
        <c-CSortableItem value="implementation" label="Implementation">Implementation</c-CSortableItem>
        <c-CSortableItem value="release" label="Release">Release</c-CSortableItem>
      </c-CSortable>
    """


preview = SortableAtAGlance()
preview  # noqa: B018
