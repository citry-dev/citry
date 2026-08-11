import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RadioCustomization(Component):
    template = """
      <div class="radio-custom">
        <c-CRadioGroup name="collection" value="fern" orientation="horizontal">
          <c-fill name="label">Plant collection</c-fill>
          <c-fill name="default">
            <c-CRadio value="fern">Fern house</c-CRadio>
            <c-CRadio value="alpine">Alpine house</c-CRadio>
            <c-CRadio value="orchid">Orchid house</c-CRadio>
          </c-fill>
        </c-CRadioGroup>
      </div>
    """
    css = """
      :where(.radio-custom) {
        --cui-radio-active-color: light-dark(#7c3f00, #fbbf24);
        --cui-radio-border-color: light-dark(#a16207, #fde68a);
        --cui-radio-background: light-dark(#fffbeb, #2d2108);
        --cui-radio-control-size: 1.35rem;
        --cui-radio-group-gap: 1.25rem;
        padding: 1.25rem;
        border-radius: 0.8rem;
        background: light-dark(#f7f2df, #211d10);
      }
    """


preview = RadioCustomization()

preview  # noqa: B018
