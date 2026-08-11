import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class PopoverAtAGlance(Component):
    template = """
      <section class="popover-sampler">
        <c-CPopover placement="bottom-start">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">
              Europa
            </c-CButton>
          </c-fill>
          <c-fill name="title">Europa</c-fill>
          <c-fill name="default">An ocean world beneath fractured ice.</c-fill>
        </c-CPopover>
        <c-CPopover placement="top">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">
              Enceladus
            </c-CButton>
          </c-fill>
          <c-fill name="title">Enceladus</c-fill>
          <c-fill name="description">Saturn II</c-fill>
          <c-fill name="default">Bright plumes erupt above its south pole.</c-fill>
        </c-CPopover>
        <c-CPopover placement="bottom-end" match_width>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="ghost" c-attrs="activator_attrs">
              Titan atmosphere
            </c-CButton>
          </c-fill>
          <c-fill name="title">Titan</c-fill>
          <c-fill name="default">A dense nitrogen sky conceals methane lakes.</c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton size="sm" c-attrs="close_attrs">
              Mark explored
            </c-CButton>
          </c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.popover-sampler) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        min-block-size: 12rem;
        padding-block: 2rem;
      }
    """


preview = PopoverAtAGlance()

preview  # noqa: B018
