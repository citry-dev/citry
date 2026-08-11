import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class LinkedCurrentBreadcrumb(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CBreadcrumbItem("Library", "/library"),
                citry_ui.CBreadcrumbItem("New arrivals", "/library/new"),
            )
        }

    template = '<c-CBreadcrumbs c-items="items" label="Collection location" />'


preview = LinkedCurrentBreadcrumb()

preview  # noqa: B018
