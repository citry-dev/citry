from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToastAtAGlance(Component):
    template = """
      <section class="toast-sampler">
        <p>These initial messages demonstrate presentation intent separately from urgency.</p>
        <c-CToastRegion c-items="items" c-duration_ms="0" c-limit="5" />
      </section>
    """

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": tuple(
                citry_ui.CToastMessage(id=intent, title=title, intent=intent)
                for intent, title in (
                    ("neutral", "Draft retained"),
                    ("info", "Sync started"),
                    ("success", "Field note saved"),
                    ("warn", "Connection is slow"),
                    ("error", "Upload failed"),
                )
            )
        }

    css = ":where(.toast-sampler) { min-block-size:20rem; padding:1rem; }"


preview = ToastAtAGlance()
preview  # noqa: B018
