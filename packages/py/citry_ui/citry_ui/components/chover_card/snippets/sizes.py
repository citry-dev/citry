# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class HoverCardSizes(Component):
    template = """
      <c-CGroup>
        <c-CHoverCard size="sm">
          <c-fill name="activator" data="{ activator_attrs }"><a href="#small" c-bind="activator_attrs">Small</a></c-fill>
          <c-fill name="default">A compact preview card.</c-fill>
        </c-CHoverCard>
        <c-CHoverCard size="lg" c-arrow="False">
          <c-fill name="activator" data="{ activator_attrs }"><a href="#large" c-bind="activator_attrs">Large without arrow</a></c-fill>
          <c-fill name="default">A generous preview without a pointer arrow.</c-fill>
        </c-CHoverCard>
      </c-CGroup>
    """


preview = HoverCardSizes()
preview  # noqa: B018
