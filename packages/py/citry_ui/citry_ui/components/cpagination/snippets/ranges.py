import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PaginationRanges(Component):
    template = """
      <c-CStack gap="md">
        <c-CPagination c-pages="100" c-page="50" c-siblings="0" c-boundaries="1" />
        <c-CPagination c-pages="100" c-page="50" c-siblings="2" c-boundaries="2" />
      </c-CStack>
    """


preview = PaginationRanges()
preview  # noqa: B018
