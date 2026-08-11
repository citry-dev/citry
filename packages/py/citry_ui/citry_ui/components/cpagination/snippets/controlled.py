import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledPagination(Component):
    template = """
      <section x-data="{ page: 3 }">
        <p>Plate <strong x-text="page"></strong> of 18</p>
        <c-CPagination
          c-pages="18"
          c-page="3"
          $c-props="{ page, onPageChange: (next) => page = next }"
        />
      </section>
    """


preview = ControlledPagination()
preview  # noqa: B018
