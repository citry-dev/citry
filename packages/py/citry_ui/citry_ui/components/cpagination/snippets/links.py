import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class LinkPagination(Component):
    template = '<c-CPagination c-pages="12" c-page="4" href="/field-notes?page={page}" />'


preview = LinkPagination()
preview  # noqa: B018
