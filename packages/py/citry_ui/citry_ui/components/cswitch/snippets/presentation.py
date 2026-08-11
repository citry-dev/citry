import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SwitchPresentation(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CStack>
        <c-for each="size in sizes">
          <c-CSwitch c-size="size" checked>{{ size }} switch</c-CSwitch>
        </c-for>
        <c-CSwitch label_pos="start" checked>Label before track</c-CSwitch>
      </c-CStack>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"sizes": ("sm", "md", "lg")}


preview = SwitchPresentation()

preview  # noqa: B018
