from dataclasses import dataclass

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


@dataclass(frozen=True, slots=True)
class Mineral:
    name: str
    hardness: str


class GridIntrinsic(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="intrinsic-minerals" aria-labelledby="intrinsic-minerals-title">
        <h2 id="intrinsic-minerals-title">Mohs hardness field set</h2>
        <c-CGrid min_col="11rem" gap="sm">
          <c-for each="mineral in minerals">
            <article class="intrinsic-minerals__card">
              <strong>{{ mineral.name }}</strong>
              <span>{{ mineral.hardness }}</span>
            </article>
          </c-for>
        </c-CGrid>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "minerals": (
                Mineral("Talc", "1 · very soft"),
                Mineral("Calcite", "3 · copper scratch"),
                Mineral("Apatite", "5 · knife edge"),
                Mineral("Quartz", "7 · scratches glass"),
                Mineral("Corundum", "9 · near diamond"),
            )
        }

    css = """
      :where(.intrinsic-minerals) {
        max-inline-size: 50rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.intrinsic-minerals h2) {
        margin: 0 0 0.75rem;
        font-size: 0.95rem;
      }

      :where(.intrinsic-minerals__card) {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        padding: 0.75rem;
        border-block-start: 0.2rem solid #6f63a8;
        background: light-dark(#f5f1ff, #28243a);
        font-size: 0.76rem;
      }

      :where(.intrinsic-minerals__card span) {
        color: GrayText;
        text-align: end;
      }
    """


preview = GridIntrinsic()

preview  # noqa: B018
