from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CButton, CContextMenu, CMenuItem, CMenuSeparator

citry.register_library(citry_ui)


class BasicContextMenu(Component):
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
            "python_menu": CContextMenu(
                aria_label="Invoice actions",
                slots={
                    "target": lambda data: CButton(
                        variant="outline",
                        attrs=data.target_attrs,
                        slots={"default": "Invoices"},
                    ),
                    "menu": (
                        CMenuItem(value="rename", slots={"default": "Rename"}),
                        CMenuItem(value="duplicate", slots={"default": "Duplicate"}),
                        CMenuSeparator(),
                        CMenuItem(
                            value="delete",
                            intent="danger",
                            slots={"default": "Delete"},
                        ),
                    ),
                },
            ),
        }

    template = """
      <section
        class="context-menu-basic"
        x-data
      >
        <article>
          <h3>Template file</h3>
          <c-CContextMenu
            aria_label="Document actions"
            $c-props="{onAction: onAction}"
          >
            <c-fill name="target" data="{ target_attrs }">
              <div
                class="context-menu-basic__file"
                tabindex="0"
                c-bind="target_attrs"
              >
                <strong>Quarterly report.pdf</strong>
                <span>2.4 MB · Updated today</span>
              </div>
            </c-fill>
            <c-fill name="menu">
              <c-CMenuItem value="rename">Rename</c-CMenuItem>
              <c-CMenuItem value="duplicate">Duplicate</c-CMenuItem>
              <c-CMenuSeparator />
              <c-CMenuItem value="delete" intent="danger">Delete</c-CMenuItem>
            </c-fill>
          </c-CContextMenu>
        </article>

        <article>
          <h3>Python composition</h3>
          {{ python_menu }}
        </article>

        <output aria-live="polite" x-text="lastActionLabel">
          Last action: No action yet
        </output>
      </section>
    """

    js = """
      $component(({ scope }) => {
        scope.lastActionLabel = "Last action: No action yet";
        scope.onAction = (value) => {
          scope.lastActionLabel = `Last action: ${value}`;
        };
      });
    """

    css = """
      :where(.context-menu-basic) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
        gap: 1rem;
        min-block-size: 20rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.context-menu-basic article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
      }

      :where(.context-menu-basic h3) {
        margin: 0;
      }

      :where(.context-menu-basic__file) {
        display: grid;
        gap: 0.25rem;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.context-menu-basic__file:focus-visible) {
        outline: 2px solid Highlight;
        outline-offset: 2px;
      }

      :where(.context-menu-basic output) {
        grid-column: 1 / -1;
      }
    """


preview = BasicContextMenu()

preview  # noqa: B018
