import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FormattedTooltip(Component):
    template = """
      <section class="formatted-tooltip">
        <c-CTooltip placement="bottom">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">
              Europa orbit
            </c-CButton>
          </c-fill>
          <c-fill name="default">
            Orbital period: <strong>3.55 Earth days</strong>
          </c-fill>
        </c-CTooltip>
      </section>
    """

    css = """
      :where(.formatted-tooltip) {
        display: grid;
        place-items: center;
        min-block-size: 12rem;
      }
    """


preview = FormattedTooltip()

preview  # noqa: B018
