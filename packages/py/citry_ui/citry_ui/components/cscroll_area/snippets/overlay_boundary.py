import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaOverlayBoundary(Component):
    template = """
      <section class="scroll-area-overlay-boundary">
        <h2>Credential review</h2>
        <p>
          The red sample is ordinary positioned content and clips at the
          viewport. The Popover follows its own anchored-layer contract.
        </p>
        <c-CScrollArea
          aria_label="Credential review notes"
          style="--cui-scroll-area-max-block-size: 12rem"
        >
          <div class="scroll-area-overlay-boundary__content">
            <span class="scroll-area-overlay-boundary__clipped">
              Ordinary positioned note
            </span>
            <p>Confirm the token owner and intended service boundary.</p>
            <p>Review the current scopes before granting another permission.</p>
            <c-CPopover>
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton
                  size="sm"
                  variant="outline"
                  c-attrs="activator_attrs"
                >Open scope help</c-CButton>
              </c-fill>
              <c-fill name="title">Credential scope</c-fill>
              <c-fill name="default">
                Grant only the permissions this worker needs.
              </c-fill>
            </c-CPopover>
            <p>Record the approval before rotating the credential.</p>
            <p>Archive the previous key after the overlap window closes.</p>
          </div>
        </c-CScrollArea>
      </section>
    """

    css = """
      :where(.scroll-area-overlay-boundary) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-overlay-boundary h2,
        .scroll-area-overlay-boundary p) {
        margin: 0;
      }

      :where(.scroll-area-overlay-boundary__content) {
        position: relative;
        display: grid;
        gap: 1rem;
        min-block-size: 22rem;
        padding: 1rem;
      }

      :where(.scroll-area-overlay-boundary__clipped) {
        position: absolute;
        inset-block-start: 1rem;
        inset-inline-end: -5rem;
        inline-size: 8rem;
        padding: 0.5rem;
        border: 2px solid #b42318;
        background: Canvas;
        color: #b42318;
      }
    """


preview = ScrollAreaOverlayBoundary()

preview  # noqa: B018
