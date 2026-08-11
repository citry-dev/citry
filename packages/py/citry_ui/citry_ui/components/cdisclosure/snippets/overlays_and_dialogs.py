import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DisclosureOverlaysAndDialogs(Component):
    template = """
      <section
        class="disclosure-overlay-demo"
        x-data="{dialogOpen:false}"
        @click="if ($event.target.closest('[data-open-credential-dialog]')) dialogOpen=true"
      >
        <c-CDisclosure open>
          <c-fill name="title">Credential help</c-fill>
          <c-fill name="default">
            <c-CStack gap="sm" align="start">
              <p>Review token scope before rotating a credential.</p>
              <c-CPopover>
                <c-fill name="activator" data="{ activator_attrs }">
                  <c-CButton size="sm" variant="outline" c-attrs="activator_attrs">Scope help</c-CButton>
                </c-fill>
                <c-fill name="title">Credential scope</c-fill>
                <c-fill name="default">Grant only the permissions this worker needs.</c-fill>
              </c-CPopover>
              <button
                type="button"
                class="disclosure-overlay-demo__dialog-trigger"
                data-open-credential-dialog
              >Rotate credential</button>
            </c-CStack>
          </c-fill>
        </c-CDisclosure>

        <c-CDialog
          size="sm"
          $c-props="{
            open: dialogOpen,
            onOpenChange: (next) => dialogOpen = next,
          }"
        >
          <c-fill name="title">Rotate credential</c-fill>
          <c-fill name="default">The old credential stops working immediately.</c-fill>
        </c-CDialog>
      </section>
    """

    css = """
      :where(.disclosure-overlay-demo) { display: grid; gap: 1rem; justify-items: start; }
      :where(.disclosure-overlay-demo > [data-citry-ui-part="disclosure"]) { inline-size: min(100%, 40rem); }
      :where(.disclosure-overlay-demo__dialog-trigger) {
        min-block-size: 2.25rem;
        padding-inline: 0.875rem;
        border: 1px solid color-mix(in srgb, currentColor 24%, transparent);
        border-radius: 0.5rem;
        background: Canvas;
        color: CanvasText;
        font: inherit;
      }
    """


preview = DisclosureOverlaysAndDialogs()
preview  # noqa: B018
