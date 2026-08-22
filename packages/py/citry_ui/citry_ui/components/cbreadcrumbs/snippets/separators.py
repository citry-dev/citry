import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BreadcrumbSeparators(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CBreadcrumbItem("Poetry", "/poetry"),
                citry_ui.CBreadcrumbItem("Mary Oliver"),
            )
        }

    template = """
      <c-CCol>
        <c-CBreadcrumbs c-items="items" separator="/" label="Slash trail" />
        <c-CBreadcrumbs c-items="items" separator="»" label="Chevron trail" />
        <c-CBreadcrumbs c-items="items" label="Arrow trail">
          <c-fill name="separator" data="{ index }">
            →
          </c-fill>
        </c-CBreadcrumbs>
      </c-CCol>
    """


preview = BreadcrumbSeparators()

preview  # noqa: B018
