import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TourCustomization(Component):
    template = """
      <c-CTour c-class_="['ocean-tour']">
        <c-fill name="activator" data="{ activator_attrs }">
          <c-CButton c-attrs="activator_attrs">Open custom tour</c-CButton>
        </c-fill>
        <c-fill name="close"><c-CIcon name="close" /></c-fill>
        <c-fill name="default">
          <c-CTourStep value="theme">
            <c-fill name="title">Ocean theme</c-fill>
            <c-fill name="default">Variables customize the stable Tour anatomy.</c-fill>
          </c-CTourStep>
        </c-fill>
      </c-CTour>
    """
    css = """
      :where(.ocean-tour) {
        --cui-tour-background: light-dark(#eff8ff, #102a43);
        --cui-tour-border-color: light-dark(#84caff, #2e90fa);
        --cui-tour-backdrop-color: rgb(2 32 71 / 62%);
        --cui-tour-radius: 1.25rem;
      }
    """


preview = TourCustomization()
preview  # noqa: B018
