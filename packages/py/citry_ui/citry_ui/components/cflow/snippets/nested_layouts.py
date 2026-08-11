from dataclasses import dataclass

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


@dataclass(frozen=True, slots=True)
class FiringBatch:
    name: str
    clay: str
    cone: str


class NestedFlowLayouts(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CStack class_="flow-nested" gap="lg">
        <c-for each="batch in batches">
          <c-CGroup justify="between" class_="flow-nested__row">
            <c-CStack gap="0">
              <strong>{{ batch.name }}</strong>
              <span>{{ batch.clay }}</span>
            </c-CStack>
            <c-CGroup gap="xs">
              <span class="flow-nested__cone">{{ batch.cone }}</span>
              <c-CButton size="sm" variant="outline">Open log</c-CButton>
            </c-CGroup>
          </c-CGroup>
        </c-for>
      </c-CStack>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "batches": (
                FiringBatch("Sea mist bowls", "Porcelain", "Cone 10"),
                FiringBatch("Cedar cups", "Speckled stoneware", "Cone 6"),
                FiringBatch("Ember vases", "Red earthenware", "Cone 04"),
            )
        }

    css = """
      :where(.flow-nested) {
        max-inline-size: 42rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-nested__row) {
        padding: 0.8rem;
        border-block-end: 1px solid light-dark(#d6c4ad, #5f5247);
      }

      :where(.flow-nested__cone) {
        padding: 0.2rem 0.5rem;
        border-radius: 999px;
        background: light-dark(#ead7bd, #4b3b30);
        font-size: 0.75rem;
      }
    """


preview = NestedFlowLayouts()

preview  # noqa: B018
