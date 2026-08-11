import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PaginationCustomization(Component):
    template = '<c-CPagination class_="lunar-pages" c-pages="9" c-page="5" />'
    css = """
      :where(.lunar-pages) {
        --cui-pagination-current-background: light-dark(#6d28d9, #c4b5fd);
        --cui-pagination-current-foreground: light-dark(white, #2e1065);
        --cui-pagination-radius: 999px;
      }
    """


preview = PaginationCustomization()
preview  # noqa: B018
