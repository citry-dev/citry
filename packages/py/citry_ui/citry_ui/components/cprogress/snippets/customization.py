import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ProgressCustomization(Component):
    template = """
      <c-CStack class_="progress-themes">
        <div class="progress-themes__coral"><c-CProgress label="Coral lab" c-value="58" shape="pill" /></div>
        <div class="progress-themes__abyss"><c-CProgress label="Abyss lab" c-value="58" shape="pill" /></div>
      </c-CStack>
    """
    css = """
      :where(.progress-themes > div) {
        padding: 1.25rem;
        border-radius: 0.75rem;
      }

      :where(.progress-themes__coral) {
        --cui-progress-track-color: #f8ddd6;
        --cui-progress-range-color: #b9382f;
        --cui-progress-height: 0.75rem;
        background: #fff6f2;
      }

      :where(.progress-themes__abyss) {
        color-scheme: dark;
        --cui-progress-track-color: #1f3b48;
        --cui-progress-range-color: #63d4e8;
        --cui-progress-height: 0.75rem;
        background: #0b1b24;
      }
    """


preview = ProgressCustomization()

preview  # noqa: B018
