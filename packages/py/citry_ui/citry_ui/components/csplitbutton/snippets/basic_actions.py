from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CMenuItem, CSplitButton

citry.register_library(citry_ui)


class BasicSplitButtonActions(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return {
            "python_split_button": CSplitButton(
                label="Publish specimen actions",
                menu_label="More publish specimen actions",
                variant="outline",
                slots={
                    "default": "Publish specimen",
                    "menu": (
                        CMenuItem(
                            value="preview",
                            slots={"default": "Preview publication"},
                        ),
                        CMenuItem(
                            value="schedule",
                            slots={"default": "Schedule publication"},
                        ),
                    ),
                },
            )
        }

    template = """
      <section class="split-button-basic">
        <article>
          <p>Template composition</p>
          <c-CSplitButton
            label="Save specimen actions"
            menu_label="More save specimen actions"
          >
            <c-fill name="default">Save specimen</c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="save-copy">Save a copy</c-CMenuItem>
              <c-CMenuItem value="export">Export record</c-CMenuItem>
            </c-fill>
          </c-CSplitButton>
        </article>
        <article>
          <p>Python composition</p>
          {{ python_split_button }}
        </article>
      </section>
    """

    css = """
      :where(.split-button-basic) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        min-block-size: 17rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.split-button-basic article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, currentColor 20%, transparent);
        border-radius: 0.75rem;
      }

      :where(.split-button-basic p) {
        margin: 0;
        font-weight: 700;
      }
    """


preview = BasicSplitButtonActions()

preview  # noqa: B018
