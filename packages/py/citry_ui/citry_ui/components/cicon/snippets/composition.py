import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class IconComposition(Component):
    template = """
      <section class="icon-composition">
        <div class="icon-composition__actions">
          <c-CButton variant="outline" intent="neutral">
            <c-fill name="start">
              <c-CIcon name="search" />
            </c-fill>
            <c-fill name="default">
              Search specimens
            </c-fill>
          </c-CButton>
          <c-CButton intent="success">
            <c-fill name="start">
              <c-CIcon name="success" />
            </c-fill>
            <c-fill name="default">
              Save field note
            </c-fill>
          </c-CButton>
          <c-CButton variant="ghost">
            <c-fill name="default">
              Next trail
            </c-fill>
            <c-fill name="end">
              <c-CIcon name="next" />
            </c-fill>
          </c-CButton>
          <c-CButton
            variant="outline"
            intent="neutral"
            c-attrs="{'aria-label': 'Open field settings'}"
          >
            <c-CIcon name="settings" />
          </c-CButton>
        </div>
        <p class="icon-composition__warning">
          <c-CIcon name="warn" />
          The western footbridge is closed after rain.
        </p>
      </section>
    """

    css = """
      :where(.icon-composition) {
        display: grid;
        gap: 1rem;
        max-width: 62rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.icon-composition__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.65rem;
        align-items: center;
      }

      :where(.icon-composition__warning) {
        display: flex;
        gap: 0.55rem;
        align-items: center;
        width: fit-content;
        margin: 0;
        padding: 0.75rem 0.9rem;
        border-inline-start: 0.25rem solid light-dark(#d97706, #fbbf24);
        color: light-dark(#78350f, #fde68a);
        background: light-dark(#fffbeb, #451a03);
      }
    """


preview = IconComposition()

preview  # noqa: B018
