import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardNestedContent(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "rooms": (
                citry_ui.CComboboxOption("sunroom", "Sunroom"),
                citry_ui.CComboboxOption("library", "Library"),
                citry_ui.CComboboxOption("studio", "Studio"),
            )
        }

    template = """
      <section class="card-nested">
        <c-CCard variant="outline">
          <c-fill name="header"><h2>Place the reading chair</h2></c-fill>
          <c-fill name="default">
            <c-CField>
              <c-fill name="label">Room</c-fill>
              <c-fill name="default">
                <c-CCombobox
                  c-options="rooms"
                  value="sunroom"
                  placeholder="Choose a room"
                />
              </c-fill>
            </c-CField>
          </c-fill>
          <c-fill name="actions">
            <c-CDialog>
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton variant="outline" c-attrs="activator_attrs">
                  Check dimensions
                </c-CButton>
              </c-fill>
              <c-fill name="title">Reading chair dimensions</c-fill>
              <c-fill name="description">
                Measure doorways and the chosen corner before delivery.
              </c-fill>
              <c-fill name="default">
                The chair is 76 cm wide, 84 cm deep, and 92 cm tall.
              </c-fill>
            </c-CDialog>
          </c-fill>
        </c-CCard>
      </section>
    """

    css = """
      :where(.card-nested) {
        max-width: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-nested h2) {
        margin: 0;
        font-size: 1.05rem;
      }
    """


preview = CardNestedContent()

preview  # noqa: B018
