from typing import Any

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RowsAndResize(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"survey_note": "Fern cover: dense\nSeedlings: abundant\nGround moisture: high"}

    template = """
      <section
        class="forest-resize"
        x-data
        x-init="Alpine.store('forestTextareaResize', {rows: 4, resize: 'vertical'})"
        @citry-ui-preview-controls.window="
          if ($event.detail.rows !== undefined) {
            $store.forestTextareaResize.rows = Number($event.detail.rows);
          }
          if ($event.detail.resize !== undefined) {
            $store.forestTextareaResize.resize = $event.detail.resize;
          }
        "
      >
        <c-CField>
          <c-fill name="label">Understory survey</c-fill>
          <c-fill name="default">
            <c-CTextarea
              name="understory"
              c-value="survey_note"
              $c-props="{
                rows: $store.forestTextareaResize.rows,
                resize: $store.forestTextareaResize.resize,
              }"
            />
          </c-fill>
          <c-fill name="description">
            Horizontal and both-direction resizing may exceed this bounded stage.
          </c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.forest-resize) {
        max-width: 34rem;
        overflow: auto;
        padding: 1rem;
        border: 1px dashed light-dark(#789f7f, #698d70);
        border-radius: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview_controls = (
    {
        "name": "rows",
        "label": "Visible rows",
        "type": "select",
        "default": "4",
        "options": (("2", "2"), ("4", "4"), ("7", "7")),
    },
    {
        "name": "resize",
        "label": "Resize",
        "type": "select",
        "default": "vertical",
        "options": (
            ("none", "None"),
            ("vertical", "Vertical"),
            ("horizontal", "Horizontal"),
            ("both", "Both"),
        ),
    },
)

preview = RowsAndResize()

preview  # noqa: B018
