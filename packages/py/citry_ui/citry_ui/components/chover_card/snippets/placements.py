# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class HoverCardPlacements(Component):
    template = """
      <c-CRow style="padding-block:8rem">
        <c-CHoverCard placement="top-start">
          <c-fill name="activator" data="{ activator_attrs }"><a href="#top" c-bind="activator_attrs">Top start</a></c-fill>
          <c-fill name="default">Collision-aware top preview.</c-fill>
        </c-CHoverCard>
        <c-CHoverCard placement="bottom-end">
          <c-fill name="activator" data="{ activator_attrs }"><a href="#bottom" c-bind="activator_attrs">Bottom end</a></c-fill>
          <c-fill name="default">Collision-aware bottom preview.</c-fill>
        </c-CHoverCard>
      </c-CRow>
    """


preview = HoverCardPlacements()
preview  # noqa: B018
