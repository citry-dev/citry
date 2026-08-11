import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BreadcrumbItemSlot(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CBreadcrumbItem("Reading lists", "/lists"),
                citry_ui.CBreadcrumbItem("Summer shelf"),
            )
        }

    template = """
      <c-CBreadcrumbs c-items="items" label="Reading-list location">
        <c-fill name="item" data="{ item, index, is_current, attrs }">
          <c-if cond="item.href is not None">
            <a c-bind="attrs">
              <span aria-hidden="true">◌</span>
              {{ item.label }}
            </a>
          </c-if>
          <c-else>
            <span c-bind="attrs">
              {{ item.label }}
            </span>
          </c-else>
        </c-fill>
      </c-CBreadcrumbs>
    """


preview = BreadcrumbItemSlot()

preview  # noqa: B018
