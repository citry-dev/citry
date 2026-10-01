import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledPopover(Component):
    template = """
      <section
        class="controlled-popover"
      >
        <c-CPopover
          :open="open" :onOpenChange="(nextOpen, detail) => {
              lastReason = detail.reason;
              if (!locked) open = nextOpen;
            }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Mission controls
            </c-CButton>
          </c-fill>
          <c-fill name="title">Mission controls</c-fill>
          <c-fill name="default">
            The owner may accept or decline every visibility request.
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">Close panel</c-CButton>
          </c-fill>
        </c-CPopover>
        <label>
          <input type="checkbox" v-model="locked" />
          Decline visibility requests
        </label>
        <output v-text="`Last request: ${lastReason}`"></output>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            open: false, locked: false, lastReason: 'none'
          };
        },
      });
    """

    css = """
      :where(.controlled-popover) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }

      :where(.controlled-popover output) {
        flex-basis: 100%;
        color: color-mix(in srgb, CanvasText 70%, transparent);
      }
    """


preview = ControlledPopover()

preview  # noqa: B018
