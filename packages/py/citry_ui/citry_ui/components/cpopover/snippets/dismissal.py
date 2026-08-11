import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PopoverDismissal(Component):
    template = """
      <section class="dismissal-samples">
        <c-CPopover>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Dismissible</c-CButton>
          </c-fill>
          <c-fill name="title">Dismissible panel</c-fill>
          <c-fill name="default">Escape, outside pointer, or focus outside may close it.</c-fill>
        </c-CPopover>
        <c-CPopover c-dismissible="False">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">
              Explicit action only
            </c-CButton>
          </c-fill>
          <c-fill name="title">Protected observation</c-fill>
          <c-fill name="default">Outside interaction leaves this panel open.</c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton c-attrs="close_attrs">Acknowledge</c-CButton>
          </c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.dismissal-samples) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }
    """


preview = PopoverDismissal()

preview  # noqa: B018
