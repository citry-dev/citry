import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RadioAtAGlance(Component):
    template = """
      <section class="radio-glance">
        <h2>Plan the garden path</h2>
        <p>Choose the habitat the path should pass through.</p>
        <c-CRadioGroup name="habitat" value="woodland" orientation="horizontal">
          <c-fill name="label">Habitat</c-fill>
          <c-fill name="default">
            <c-CRadio value="woodland">Woodland</c-CRadio>
            <c-CRadio value="meadow">Wildflower meadow</c-CRadio>
            <c-CRadio value="wetland">Wetland edge</c-CRadio>
          </c-fill>
        </c-CRadioGroup>
      </section>
    """
    css = """
      :where(.radio-glance) {
        display: grid;
        gap: 0.85rem;
        max-inline-size: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#a6b99b, #51664a);
        border-radius: 0.9rem;
        background: light-dark(#f4f8ef, #182219);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.radio-glance h2, .radio-glance p) {
        margin: 0;
      }

      :where(.radio-glance > p) {
        color: light-dark(#53634c, #b8c9b0);
        font-size: 0.82rem;
      }
    """


preview = RadioAtAGlance()

preview  # noqa: B018
