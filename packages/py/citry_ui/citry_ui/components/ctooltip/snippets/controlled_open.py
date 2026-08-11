import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledTooltip(Component):
    template = """
      <section class="controlled-tooltip" x-data="{ open: false, locked: false, reason: 'none' }">
        <c-CTooltip
          text="Controlled description for the Europa archive"
          $c-props="{
            open,
            onOpenChange: (nextOpen, detail) => {
              reason = detail.reason;
              if (!locked) open = nextOpen;
            },
          }"
        >
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Europa archive</c-CButton>
          </c-fill>
        </c-CTooltip>
        <label>
          <input type="checkbox" x-model="locked" />
          Decline requests
        </label>
        <output x-text="`Last request: ${reason}`"></output>
      </section>
    """

    css = """
      :where(.controlled-tooltip) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }

      :where(.controlled-tooltip output) {
        flex-basis: 100%;
        color: color-mix(in srgb, CanvasText 72%, transparent);
      }
    """


preview = ControlledTooltip()

preview  # noqa: B018
