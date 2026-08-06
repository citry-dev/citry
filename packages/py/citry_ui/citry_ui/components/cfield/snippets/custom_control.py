import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomFieldControl(Component):
    template = """
      <section class="shore-custom-control">
        <c-CField required>
          <c-fill name="label">
            Shore observation
          </c-fill>
          <c-fill
            name="default"
            data="{ control_attrs }"
          >
            <textarea
              rows="5"
              placeholder="Describe the pool, weather, and visible species"
              c-bind="control_attrs"
            ></textarea>
          </c-fill>
          <c-fill name="description">
            The textarea receives Field IDs and server state from slot data.
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.shore-custom-control) {
        max-width: 40rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.shore-custom-control textarea) {
        box-sizing: border-box;
        inline-size: 100%;
        padding: 0.75rem;
        border: 1px solid color-mix(in srgb, CanvasText 38%, transparent);
        border-radius: 0.5rem;
        background: Canvas;
        color: CanvasText;
        font: inherit;
        resize: vertical;
      }
    """


preview = CustomFieldControl()

preview  # noqa: B018
