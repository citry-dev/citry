import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PaginationPresentation(Component):
    template = """
      <c-CStack gap="md">
        <c-CPagination c-pages="8" c-page="3" variant="soft" size="sm" />
        <c-CPagination c-pages="8" c-page="3" variant="outline" />
        <c-CPagination c-pages="8" c-page="3" variant="plain" size="lg" />
      </c-CStack>
    """


preview = PaginationPresentation()
preview  # noqa: B018
