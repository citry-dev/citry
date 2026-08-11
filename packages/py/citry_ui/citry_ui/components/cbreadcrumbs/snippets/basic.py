import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicBreadcrumbs(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CBreadcrumbItem("Library", "/library"),
                citry_ui.CBreadcrumbItem("Fiction", "/library/fiction"),
                citry_ui.CBreadcrumbItem("The left hand of darkness"),
            )
        }

    template = '<c-CBreadcrumbs c-items="items" label="Book location" />'


preview = BasicBreadcrumbs()

preview  # noqa: B018
