import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PaginationGlance(Component):
    template = '<c-CPagination c-pages="24" c-page="8" href="?page={page}" />'


preview = PaginationGlance()
preview  # noqa: B018
