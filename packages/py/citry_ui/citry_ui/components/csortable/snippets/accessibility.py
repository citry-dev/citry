import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SortableAccessibility(Component):
    template = """
      <c-CSortable label="Arrange deployment checks">
        <c-CSortableItem value="backup" label="Verify backup" />
        <c-CSortableItem value="approval" label="Security approval" c-disabled="True" />
        <c-CSortableItem value="deploy" label="Deploy application" />
        <c-CSortableItem value="observe" label="Observe health metrics" />
      </c-CSortable>
    """


preview = SortableAccessibility()
preview  # noqa: B018
