import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class LabelledInput(Component):
    template = """
      <section class="shore-example">
        <c-CField>
          <c-fill name="label">
            Tidepool name
          </c-fill>
          <c-fill name="default">
            <c-CInput
              name="tidepool_name"
              placeholder="North shelf"
              autocomplete="off"
            />
          </c-fill>
          <c-fill name="description">
            Use the name printed on the observation marker.
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.shore-example) {
        max-width: 34rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = LabelledInput()

preview  # noqa: B018
