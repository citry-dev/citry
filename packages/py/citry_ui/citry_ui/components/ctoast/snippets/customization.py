from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedToast(Component):
    template = """
      <section class="toast-theme">
        <c-CToastRegion class_="polar-toast" c-items="items" c-duration_ms="0" />
      </section>
    """

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, object]:  # noqa: ARG002
        return {
            "items": (
                citry_ui.CToastMessage(
                    id="polar",
                    title="Polar archive synchronized",
                    description="A scheme-aware brand adaptation.",
                    intent="success",
                ),
            )
        }

    css = """
      :where(.toast-theme) { color-scheme:light dark; min-block-size:16rem; padding:1rem; }
      :where(.polar-toast) {
        --cui-toast-background: light-dark(#eef8fb, #102a34);
        --cui-toast-foreground: light-dark(#17343e, #e6f7fb);
        --cui-toast-border-color: light-dark(#76b7c7, #5ea5b6);
        --cui-toast-radius: 1.25rem;
      }
    """


preview = CustomizedToast()
preview  # noqa: B018
