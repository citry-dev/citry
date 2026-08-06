import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ComboboxAtAGlance(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="combo-glance">
        <header>
          <p>Celestial catalog</p>
          <h2>Choose a destination</h2>
        </header>
        <div class="combo-glance__grid">
          <c-CField>
            <c-fill name="label">
              Planet
            </c-fill>
            <c-fill name="default">
              <c-CCombobox
                c-options="planets"
                value="saturn"
                placeholder="Search planets"
              />
            </c-fill>
          </c-CField>
          <c-CField>
            <c-fill name="label">
              Observation target
            </c-fill>
            <c-fill name="default">
              <c-CCombobox
                c-options="targets"
                variant="filled"
                auto_highlight
                placeholder="Search targets"
              />
            </c-fill>
            <c-fill name="description">
              Arrow keys skip unavailable targets.
            </c-fill>
          </c-CField>
          <c-CField disabled>
            <c-fill name="label">
              Launch window
            </c-fill>
            <c-fill name="default">
              <c-CCombobox
                c-options="windows"
                value="aurora"
                variant="plain"
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
            "planets": (
                citry_ui.CComboboxOption("mars", "Mars", "Rocky planet with a thin atmosphere"),
                citry_ui.CComboboxOption("saturn", "Saturn", "Gas giant surrounded by bright rings"),
                citry_ui.CComboboxOption("neptune", "Neptune", "Windy blue world in the outer system"),
            ),
            "targets": (
                citry_ui.CComboboxOption("orion", "Orion Nebula", "A bright stellar nursery"),
                citry_ui.CComboboxOption("andromeda", "Andromeda Galaxy", "Nearest large spiral galaxy"),
                citry_ui.CComboboxOption("carina", "Carina Nebula", "Southern-sky emission nebula", disabled=True),
            ),
            "windows": (citry_ui.CComboboxOption("aurora", "Aurora window"),),
        }

    css = """
      :where(.combo-glance) {
        max-width: 62rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bfdbfe, #1e3a8a);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.combo-glance header) {
        margin-block-end: 1rem;
      }

      :where(.combo-glance h2, .combo-glance p) {
        margin: 0;
      }

      :where(.combo-glance header p) {
        margin-block-end: 0.3rem;
        color: light-dark(#1d4ed8, #93c5fd);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.combo-glance__grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        align-items: start;
      }
    """


preview = ComboboxAtAGlance()

preview  # noqa: B018
