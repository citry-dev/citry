import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DescribedRadios(Component):
    template = """
      <c-CRadioGroup name="soil" value="loam" class_="radio-described">
        <c-fill name="label">Soil blend</c-fill>
        <c-fill name="default">
          <c-CRadio value="loam">
            <c-fill name="default">Woodland loam</c-fill>
            <c-fill name="description">Balanced drainage for ferns and woodland flowers.</c-fill>
          </c-CRadio>
          <c-CRadio value="grit">
            <c-fill name="default">Alpine grit</c-fill>
            <c-fill name="description">Fast drainage for rock-garden plants.</c-fill>
          </c-CRadio>
          <c-CRadio value="peat" disabled>
            <c-fill name="default">Bog peat</c-fill>
            <c-fill name="description">Unavailable while the bog bed recovers.</c-fill>
          </c-CRadio>
        </c-fill>
      </c-CRadioGroup>
    """
    css = """
      :where(.radio-described) {
        max-inline-size: 34rem;
      }
    """


preview = DescribedRadios()

preview  # noqa: B018
