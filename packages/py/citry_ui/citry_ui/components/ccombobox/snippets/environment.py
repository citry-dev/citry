import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CelestialNamesEnvironment(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="celestial-environment">
        <div
          dir="rtl"
          style="color-scheme: dark"
        >
          <c-CField>
            <c-fill name="label">
              جرم سماوي
            </c-fill>
            <c-fill name="default">
              <c-CCombobox
                c-options="arabic_objects"
                value="thurayya"
                size="sm"
              />
            </c-fill>
          </c-CField>
        </div>
        <div
          class="celestial-environment__narrow"
          style="color-scheme: light"
        >
          <c-CField>
            <c-fill name="label">
              Long catalog name
            </c-fill>
            <c-fill name="default">
              <c-CCombobox
                c-options="long_names"
                open_on_focus
                placeholder="Search long names"
              />
            </c-fill>
          </c-CField>
        </div>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "arabic_objects": (
                citry_ui.CComboboxOption("thurayya", "الثريا", "عنقود نجمي مفتوح"),
                citry_ui.CComboboxOption("jauza", "الجوزاء", "كوكبة بارزة في سماء الشتاء"),
            ),
            "long_names": (
                citry_ui.CComboboxOption(
                    "andromeda-satellite",
                    "Andromeda Galaxy satellite candidate in the outer stellar halo",
                    "A deliberately long label that wraps instead of covering the action controls",
                ),
                citry_ui.CComboboxOption(
                    "magellanic-stream",
                    "Magellanic Stream high-velocity cloud observation",
                    "Supporting text also wraps inside a narrow popup",
                ),
            ),
        }

    css = """
      :where(.celestial-environment) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
        gap: 1rem;
        align-items: start;
        max-width: 48rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bfdbfe, #1e40af);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.celestial-environment__narrow) {
        max-width: 17rem;
      }
    """


preview = CelestialNamesEnvironment()

preview  # noqa: B018
