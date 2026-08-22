import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BreadcrumbSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CBreadcrumbItem("Essays", "/essays"),
                citry_ui.CBreadcrumbItem("On keeping a notebook"),
            ),
            "sizes": ("sm", "md", "lg"),
        }

    template = """
      <c-CCol>
        <c-for each="size in sizes">
          <c-CBreadcrumbs c-items="items" c-size="size" c-label="f'{size} book location'" />
        </c-for>
      </c-CCol>
    """


preview = BreadcrumbSizes()

preview  # noqa: B018
