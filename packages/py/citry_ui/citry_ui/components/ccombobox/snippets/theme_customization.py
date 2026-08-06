import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DeepSkyTheme(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="deep-sky-theme">
        <header>
          <p>Deep-sky palette</p>
          <h2>Search the Messier catalog</h2>
        </header>
        <c-CField>
          <c-fill name="label">
            Messier object
          </c-fill>
          <c-fill name="default">
            <c-CCombobox
              c-options="objects"
              value="m51"
              class_="deep-sky-theme__picker"
            />
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
            "objects": (
                citry_ui.CComboboxOption("m1", "Crab Nebula", "Supernova remnant in Taurus"),
                citry_ui.CComboboxOption("m42", "Orion Nebula", "Stellar nursery in Orion"),
                citry_ui.CComboboxOption("m51", "Whirlpool Galaxy", "Interacting spiral galaxies"),
                citry_ui.CComboboxOption("m104", "Sombrero Galaxy", "Galaxy with a bright central bulge"),
            )
        }

    css = """
      :where(.deep-sky-theme) {
        --cui-combobox-background: #11142b;
        --cui-combobox-foreground: #f5f3ff;
        --cui-combobox-border-color: #6d5bd0;
        --cui-combobox-focus-color: #f0abfc;
        --cui-combobox-popup-background: #171a35;
        --cui-combobox-popup-border-color: #8171d8;
        --cui-combobox-highlighted-background: #312e81;
        --cui-combobox-selected-background: #4c1d95;
        --cui-combobox-option-description-color: #c4b5fd;

        max-width: 34rem;
        padding: 1.25rem;
        border: 1px solid #5145a6;
        border-radius: 0.875rem;
        background: #0b1024;
        color: #f5f3ff;
        color-scheme: dark;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.deep-sky-theme header) {
        margin-block-end: 1rem;
      }

      :where(.deep-sky-theme h2, .deep-sky-theme p) {
        margin: 0;
      }

      :where(.deep-sky-theme header p) {
        margin-block-end: 0.3rem;
        color: #f0abfc;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.deep-sky-theme__picker) {
        --cui-combobox-radius: 0.75rem;
        --cui-combobox-popup-shadow: 0 1rem 3rem rgb(0 0 0 / 45%);
      }
    """


preview = DeepSkyTheme()

preview  # noqa: B018
