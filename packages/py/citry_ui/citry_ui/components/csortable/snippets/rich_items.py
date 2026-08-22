# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SortableRichItems(Component):
    template = """
      <c-CSortable label="Reorder sprint tasks">
        <c-CSortableItem value="audit" label="Audit keyboard paths">
          <c-fill name="handle"><span aria-hidden="true">↕</span></c-fill>
          <c-fill name="default"><strong>Audit keyboard paths</strong><br /><small>Accessibility · 3 points</small></c-fill>
        </c-CSortableItem>
        <c-CSortableItem value="tokens" label="Refine theme tokens">
          <c-fill name="handle"><span aria-hidden="true">↕</span></c-fill>
          <c-fill name="default"><strong>Refine theme tokens</strong><br /><small>Design system · 2 points</small></c-fill>
        </c-CSortableItem>
        <c-CSortableItem value="locked" label="Publish release" c-disabled="True">
          <strong>Publish release</strong><br /><small>Fixed until approval</small>
        </c-CSortableItem>
      </c-CSortable>
    """


preview = SortableRichItems()
preview  # noqa: B018
