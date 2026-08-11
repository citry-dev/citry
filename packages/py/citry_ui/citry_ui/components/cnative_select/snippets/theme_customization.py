from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectOption

citry.register_library(citry_ui)


class NativeSelectThemes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "instruments": [
                CNativeSelectOption("ctd", "CTD profiler"),
                CNativeSelectOption("sonar", "Multibeam sonar"),
                CNativeSelectOption("rov", "Remotely operated vehicle"),
            ],
        }

    template = """
      <section class="ocean-themes">
        <div class="ocean-themes__lagoon">
          <c-CField>
            <c-fill name="label">Lagoon instrument</c-fill>
            <c-fill name="default">
              <c-CNativeSelect c-options="instruments" value="ctd" />
            </c-fill>
          </c-CField>
        </div>
        <div class="ocean-themes__trench" style="color-scheme: dark">
          <c-CField>
            <c-fill name="label">Trench instrument</c-fill>
            <c-fill name="default">
              <c-CNativeSelect
                c-options="instruments"
                value="rov"
                class_="ocean-themes__root"
              />
            </c-fill>
          </c-CField>
        </div>
      </section>
    """

    css = """
      :where(.ocean-themes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.ocean-themes > div) {
        padding: 1rem;
        border-radius: 1rem;
      }

      :where(.ocean-themes__lagoon) {
        --cui-native-select-background: #f3feff;
        --cui-native-select-foreground: #103f49;
        --cui-native-select-border-color: #5ca4b0;
        --cui-native-select-hover-border-color: #236b78;
        --cui-native-select-focus-color: #087e8b;
        --cui-native-select-placeholder-color: #52717a;
        --cui-native-select-radius: 1rem;
        --cui-native-select-indicator-size: 0.5rem;
        background: #dff4f6;
      }

      :where(.ocean-themes__trench) {
        --cui-native-select-background: #10262d;
        --cui-native-select-foreground: #e0f7fa;
        --cui-native-select-border-color: #527b86;
        --cui-native-select-hover-border-color: #83bbc6;
        --cui-native-select-focus-color: #76e4f7;
        --cui-native-select-placeholder-color: #a1bdc3;
        --cui-native-select-radius: 0.25rem;
        background: #08191e;
      }

      :where(.ocean-themes__root[data-citry-ui-part="native-select"]:focus-visible) {
        outline-style: double;
      }
    """


preview = NativeSelectThemes()

preview  # noqa: B018
