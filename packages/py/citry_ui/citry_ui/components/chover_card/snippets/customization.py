# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedHoverCard(Component):
    template = """
      <c-CHoverCard
        style="--cui-hover-card-background:#fff8eb;--cui-hover-card-foreground:#7a2e0e;
               --cui-hover-card-border-color:#f79009;--cui-hover-card-radius:1.25rem"
      >
        <c-fill name="activator" data="{ activator_attrs }"><a href="#coral" c-bind="activator_attrs">Coral study</a></c-fill>
        <c-fill name="default"><strong>Coral study</strong><p>Warm brand adaptation.</p></c-fill>
      </c-CHoverCard>
    """


preview = CustomizedHoverCard()
preview  # noqa: B018
