import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FieldStates(Component):
    template = """
      <section class="shore-states">
        <c-CField required>
          <c-fill name="label">
            Required site
          </c-fill>
          <c-fill name="default">
            <c-CInput name="site" placeholder="Choose a survey site" />
          </c-fill>
        </c-CField>
        <c-CField readonly>
          <c-fill name="label">
            Read-only permit
          </c-fill>
          <c-fill name="default">
            <c-CInput name="permit" value="SHORE-204" />
          </c-fill>
        </c-CField>
        <c-CField disabled>
          <c-fill name="label">
            Disabled trail
          </c-fill>
          <c-fill name="default">
            <c-CInput name="trail" value="Cliff descent" />
          </c-fill>
        </c-CField>
        <c-CField invalid>
          <c-fill name="label">
            Invalid tide code
          </c-fill>
          <c-fill name="default">
            <c-CInput name="tide_code" value="LOW" />
          </c-fill>
          <c-fill name="error">
            Add the hour after the tide code.
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.shore-states) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1.25rem;
        max-width: 62rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = FieldStates()

preview  # noqa: B018
