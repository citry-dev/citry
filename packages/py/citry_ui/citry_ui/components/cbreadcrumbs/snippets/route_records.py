import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RouteBreadcrumbs(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        route = (("Authors", "/authors"), ("Ursula K. Le Guin", "/authors/le-guin"), ("Books", None))
        return {"items": tuple(citry_ui.CBreadcrumbItem(label, href) for label, href in route)}

    template = '<c-CBreadcrumbs c-items="items" label="Author location" />'


preview = RouteBreadcrumbs()

preview  # noqa: B018
