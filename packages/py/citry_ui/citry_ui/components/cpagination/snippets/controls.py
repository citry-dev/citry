import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PaginationControls(Component):
    template = """
      <c-CStack gap="md">
        <c-CPagination c-pages="14" c-page="7" c-show_edges="True" />
        <c-CPagination c-pages="14" c-page="7" c-show_controls="False" />
      </c-CStack>
    """


preview = PaginationControls()
preview  # noqa: B018
