# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RadioPresentation(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CCol gap="xl">
        <c-for each="variant in variants">
          <c-CRadioGroup #c-key="variant" c-name="f'variant-{variant}'" value="one" c-variant="variant" orientation="horizontal">
            <c-fill name="label">{{ variant }}</c-fill>
            <c-fill name="default"><c-CRadio #c-key="f'{variant}-one'" value="one">One</c-CRadio><c-CRadio #c-key="f'{variant}-two'" value="two">Two</c-CRadio></c-fill>
          </c-CRadioGroup>
        </c-for>
        <c-for each="size in sizes">
          <c-CRadioGroup #c-key="size" c-name="f'size-{size}'" value="leaf" c-size="size" label_pos="start" orientation="horizontal">
            <c-fill name="label">{{ size }}, labels first</c-fill>
            <c-fill name="default">
              <c-CRadio #c-key="f'{size}-leaf'" value="leaf">Leaf</c-CRadio>
              <c-CRadio #c-key="f'{size}-flower'" value="flower">Flower</c-CRadio>
            </c-fill>
          </c-CRadioGroup>
        </c-for>
      </c-CCol>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"variants": ("solid", "outline"), "sizes": ("sm", "md", "lg")}


preview = RadioPresentation()

preview  # noqa: B018
