import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ConstellationKeyboardPicker(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="constellation-keys">
        <header>
          <p>Keyboard chart</p>
          <h2>Navigate constellations</h2>
        </header>
        <c-CField>
          <c-fill name="label">
            Constellation
          </c-fill>
          <c-fill name="default">
            <c-CCombobox
              c-options="constellations"
              open_on_focus
              auto_highlight
              placeholder="Search constellations"
            />
          </c-fill>
          <c-fill name="description">
            Try Arrow keys, Home, End, Enter, Escape, and Tab.
          </c-fill>
        </c-CField>
        <p class="constellation-keys__note">
          Cetus is unavailable and is skipped by keyboard navigation.
        </p>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "constellations": (
                citry_ui.CComboboxOption("andromeda", "Andromeda", "Northern constellation"),
                citry_ui.CComboboxOption("cetus", "Cetus", "Sea-monster constellation", disabled=True),
                citry_ui.CComboboxOption("cygnus", "Cygnus", "Northern Cross"),
                citry_ui.CComboboxOption("lyra", "Lyra", "Home of Vega"),
                citry_ui.CComboboxOption("orion", "Orion", "Prominent winter constellation"),
            )
        }

    css = """
      :where(.constellation-keys) {
        max-width: 32rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c4b5fd, #5b21b6);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.constellation-keys header) {
        margin-block-end: 1rem;
      }

      :where(.constellation-keys h2, .constellation-keys p) {
        margin: 0;
      }

      :where(.constellation-keys header p) {
        margin-block-end: 0.3rem;
        color: light-dark(#6d28d9, #c4b5fd);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.constellation-keys__note) {
        margin-block-start: 1rem;
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.8125rem;
      }
    """


preview = ConstellationKeyboardPicker()

preview  # noqa: B018
