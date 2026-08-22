import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GroupWrapping(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="flow-wrapping" aria-label="Row wrapping">
        <c-CCol gap="xs">
          <strong>Wraps by default</strong>
          <c-CRow class_="flow-wrapping__group">
            <c-for each="label in labels"><span>{{ label }}</span></c-for>
          </c-CRow>
        </c-CCol>
        <c-CCol gap="xs">
          <strong>No wrap</strong>
          <div class="flow-wrapping__scroll">
            <c-CRow c-wrap="False" class_="flow-wrapping__group">
              <c-for each="label in labels"><span>{{ label }}</span></c-for>
            </c-CRow>
          </div>
        </c-CCol>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"labels": ("Wheel throwing", "Hand building", "Slip casting", "Raku firing")}

    css = """
      :where(.flow-wrapping) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
        gap: 1rem;
        max-inline-size: 46rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-wrapping__group) {
        inline-size: 100%;
        padding: 0.75rem;
        background: light-dark(#f1e0c7, #352b23);
      }

      :where(.flow-wrapping__group span) {
        padding: 0.35rem 0.55rem;
        border: 1px solid currentColor;
        border-radius: 999px;
        white-space: nowrap;
      }

      :where(.flow-wrapping__scroll) {
        overflow-x: auto;
      }
    """


preview = GroupWrapping()

preview  # noqa: B018
