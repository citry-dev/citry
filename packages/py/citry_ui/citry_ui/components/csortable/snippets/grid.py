# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SortableGrid(Component):
    template = """
      <c-CSortable layout="grid" label="Arrange dashboard cards" c-style="{'--cui-sortable-columns':'repeat(2,minmax(0,1fr))'}">
        <c-CSortableItem value="revenue" label="Revenue"><strong>Revenue</strong><br />€42,800</c-CSortableItem>
        <c-CSortableItem value="orders" label="Orders"><strong>Orders</strong><br />318</c-CSortableItem>
        <c-CSortableItem value="retention" label="Retention"><strong>Retention</strong><br />91%</c-CSortableItem>
        <c-CSortableItem value="alerts" label="Alerts"><strong>Alerts</strong><br />4 open</c-CSortableItem>
      </c-CSortable>
    """


preview = SortableGrid()
preview  # noqa: B018
