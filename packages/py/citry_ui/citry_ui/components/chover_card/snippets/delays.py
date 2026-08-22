# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class HoverCardDelays(Component):
    template = """
      <c-CRow>
        <c-CHoverCard c-delay="0" c-close_delay="0">
          <c-fill name="activator" data="{ activator_attrs }"><a href="#instant" c-bind="activator_attrs">Instant</a></c-fill>
          <c-fill name="default">No opening or closing delay.</c-fill>
        </c-CHoverCard>
        <c-CHoverCard c-delay="900" c-close_delay="500">
          <c-fill name="activator" data="{ activator_attrs }"><a href="#deliberate" c-bind="activator_attrs">Deliberate</a></c-fill>
          <c-fill name="default">A slower, forgiving preview.</c-fill>
        </c-CHoverCard>
      </c-CRow>
    """


preview = HoverCardDelays()
preview  # noqa: B018
