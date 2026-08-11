import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BreadcrumbOverflow(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        labels = ("Library", "Collections", "Natural history", "Forests", "Temperate woodland", "Field notes")
        return {
            "items": tuple(
                citry_ui.CBreadcrumbItem(label, f"/shelf/{index}")
                if index < len(labels) - 1
                else citry_ui.CBreadcrumbItem(label)
                for index, label in enumerate(labels)
            )
        }

    template = """
      <c-CStack class_="breadcrumb-overflow">
        <c-CBreadcrumbs c-items="items" label="Wrapping book location" />
        <c-CBreadcrumbs c-items="items" label="Scrolling book location" c-wrap="False" />
      </c-CStack>
    """
    css = """
      :where(.breadcrumb-overflow) {
        inline-size: min(100%, 22rem);
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 24%, transparent);
      }
    """


preview = BreadcrumbOverflow()

preview  # noqa: B018
