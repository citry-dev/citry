import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomBreadcrumbs(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CBreadcrumbItem("Archive", "/archive"),
                citry_ui.CBreadcrumbItem("Rare books"),
            )
        }

    template = '<c-CBreadcrumbs c-items="items" label="Archive location" class_="rare-trail" separator="✦" />'
    css = """
      :where(.rare-trail) {
        --cui-breadcrumbs-link-color: light-dark(#7c2d12, #fdba74);
        --cui-breadcrumbs-current-color: light-dark(#4c1d95, #c4b5fd);
        --cui-breadcrumbs-separator-color: light-dark(#9a3412, #fb923c);
        --cui-breadcrumbs-gap: 0.8rem;
        padding: 1rem;
        border-block: 1px solid color-mix(in srgb, CanvasText 24%, transparent);
      }
    """


preview = CustomBreadcrumbs()

preview  # noqa: B018
