from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToastPlacementRtl(Component):
    template = """
      <section class="toast-example" dir="rtl">
        <p>Logical start follows this RTL context.</p>
        <c-CToastRegion c-items="items" placement="block-end-start" c-duration_ms="0" />
      </section>
    """

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {"items": (citry_ui.CToastMessage(id="rtl", title="Logical start placement"),)}

    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = ToastPlacementRtl()
preview  # noqa: B018
