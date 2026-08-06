import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledDialog(Component):
    template = """
      <section
        class="controlled-dialog"
        x-data="{ open: false, accept: false, lastReason: 'none' }"
      >
        <p>Mission control</p>
        <h2>Own every visibility change</h2>
        <label class="controlled-dialog__toggle">
          <input type="checkbox" x-model="accept" />
          Accept Dialog requests
        </label>
        <c-CDialog
          $c-props="{
            open,
            onOpenChange: (nextOpen, detail) => {
              lastReason = detail.reason;
              if (accept) open = nextOpen;
            },
          }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Request flight plan
            </c-CButton>
          </c-fill>
          <c-fill name="title">
            Flight plan
          </c-fill>
          <c-fill name="default">
            Controlled owners may accept or decline this close request.
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">
              Request close
            </c-CButton>
          </c-fill>
        </c-CDialog>
        <p class="controlled-dialog__status" aria-live="polite">
          Last request: <strong x-text="lastReason">none</strong>
        </p>
      </section>
    """

    css = """
      :where(.controlled-dialog) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        max-width: 42rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#bae6fd, #0369a1);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.controlled-dialog h2, .controlled-dialog p) {
        margin: 0;
      }

      :where(.controlled-dialog > p:first-child) {
        color: light-dark(#0369a1, #7dd3fc);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.controlled-dialog__toggle) {
        display: flex;
        gap: 0.5rem;
        align-items: center;
      }

      :where(.controlled-dialog__status) {
        color: color-mix(in srgb, currentColor 72%, transparent);
        font-size: 0.875rem;
      }
    """


preview = ControlledDialog()

preview  # noqa: B018
