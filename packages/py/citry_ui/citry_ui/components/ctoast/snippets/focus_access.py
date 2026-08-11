from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToastFocusAccess(Component):
    template = """
      <section class="toast-example">
        <p>Focus this page, then press F6 to enter the notification and F6 again to return.</p>
        <c-CButton>Focus before F6</c-CButton>
        <c-CToastRegion c-items="items" c-duration_ms="0" />
      </section>
    """

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {"items": (citry_ui.CToastMessage(id="f6", title="F6 reaches this message"),)}

    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = ToastFocusAccess()
preview  # noqa: B018
