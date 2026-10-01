import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledPagination(Component):
    template = """
      <section >
        <p>Plate <strong v-text="page"></strong> of 18</p>
        <c-CPagination
          c-pages="18"
          c-page="3"
          :page="page" :onPageChange="(next) => page = next"
        />
      </section>
    """
    js = """
      $component({
        data() {
          return {
            page: 3
          };
        },
      });
    """


preview = ControlledPagination()
preview  # noqa: B018
