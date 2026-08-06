import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ChooseAMoon(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="moon-picker">
        <c-CField required>
          <c-fill name="label">
            Moon
          </c-fill>
          <c-fill name="default">
            <c-CCombobox
              name="moon_id"
              c-options="moons"
              placeholder="Search moons"
            />
          </c-fill>
          <c-fill name="description">
            Search by name, then choose one destination.
          </c-fill>
          <c-fill name="error">
            Choose a destination from the catalog.
          </c-fill>
        </c-CField>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "moons": (
                citry_ui.CComboboxOption("europa", "Europa", "Icy moon of Jupiter"),
                citry_ui.CComboboxOption("titan", "Titan", "Moon with a dense atmosphere"),
                citry_ui.CComboboxOption("triton", "Triton", "Retrograde moon of Neptune"),
                citry_ui.CComboboxOption("enceladus", "Enceladus", "Bright moon with water plumes"),
            )
        }

    css = """
      :where(.moon-picker) {
        max-width: 28rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7d2fe, #3730a3);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = ChooseAMoon()

preview  # noqa: B018
