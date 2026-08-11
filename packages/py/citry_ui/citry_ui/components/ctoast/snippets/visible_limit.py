from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToastVisibleLimit(Component):
    template = """
      <section class="toast-example">
        <p>Dismiss a visible message to promote the queued third item.</p>
        <c-CToastRegion c-items="items" c-limit="2" c-duration_ms="0" />
      </section>
    """

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": tuple(
                citry_ui.CToastMessage(id=f"queue-{index}", title=f"Queue item {index}") for index in range(1, 4)
            )
        }

    css = ":where(.toast-example) { min-block-size:16rem; padding:1rem; }"


preview = ToastVisibleLimit()
preview  # noqa: B018
