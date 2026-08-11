import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ExplicitCompletion(Component):
    template = """
      <section>
        <c-CDrawer c-dismissible="False" placement="block-start" size="sm">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Review coordinates</c-CButton>
          </c-fill>
          <c-fill name="title">Confirm coordinates</c-fill>
          <c-fill name="default">Check the latitude and longitude before continuing.</c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">Coordinates verified</c-CButton>
          </c-fill>
        </c-CDrawer>
      </section>
    """


preview = ExplicitCompletion()
preview  # noqa: B018
