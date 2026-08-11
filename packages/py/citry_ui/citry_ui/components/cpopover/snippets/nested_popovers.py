import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NestedPopovers(Component):
    template = """
      <section class="nested-popovers">
        <c-CPopover>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Inspect Saturn</c-CButton>
          </c-fill>
          <c-fill name="title">Saturn</c-fill>
          <c-fill name="default">
            <p>Its rings contain countless ice-rich particles.</p>
            <c-CPopover placement="bottom-end">
              <c-fill name="activator" data="{ activator_attrs }">
                <c-CButton size="sm" variant="outline" c-attrs="activator_attrs">
                  Inspect ring gap
                </c-CButton>
              </c-fill>
              <c-fill name="title">Cassini Division</c-fill>
              <c-fill name="default">
                A broad region shaped by orbital resonance with Mimas.
              </c-fill>
            </c-CPopover>
          </c-fill>
        </c-CPopover>
      </section>
    """

    css = """
      :where(.nested-popovers) {
        min-block-size: 14rem;
        padding-block: 3rem;
      }
    """


preview = NestedPopovers()

preview  # noqa: B018
