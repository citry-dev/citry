import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SpinnerAtAGlance(Component):
    template = """
      <section class="spinner-glance">
        <div class="spinner-glance__sky" aria-hidden="true">✦ · ✧ · ✦</div>
        <c-CGroup justify="center">
          <c-CSpinner label="Calibrating deep-sky camera" size="lg" />
          <div><h2>Calibrating the camera</h2><p>Reading dark frames from the observatory sensor.</p></div>
        </c-CGroup>
      </section>
    """
    css = """
      :where(.spinner-glance) {
        display: grid;
        gap: 1rem;
        max-inline-size: 34rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b8b8dd, #4b4a78);
        border-radius: 0.9rem;
        background: light-dark(#f7f6ff, #17172a);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.spinner-glance__sky) {
        color: light-dark(#5b4bb7, #c4b5fd);
        font-size: 1.3rem;
        letter-spacing: 0.6rem;
        text-align: center;
      }

      :where(.spinner-glance h2, .spinner-glance p) {
        margin: 0;
      }

      :where(.spinner-glance p) {
        margin-block-start: 0.25rem;
        color: light-dark(#55546f, #c6c4de);
        font-size: 0.8rem;
      }
    """


preview = SpinnerAtAGlance()

preview  # noqa: B018
